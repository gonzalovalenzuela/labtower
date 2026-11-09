"""UPS Monitor: banderas de estado, alarmas, margen de apagado y calidad de la red / status flags, alarms, shutdown margin and mains quality."""
import time
import unittest

from tests import support


class Pure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = support.load("nut-monitor/server.py"); cls.p = cls.m.power

    def test_flags(self):
        self.assertEqual([f["f"] for f in self.p.flags("OL CHRG RB")], ["RB"])
        self.assertEqual({f["f"]: f["lv"] for f in self.p.flags("OB DISCHRG OVER FSD TRIM")}, {"OVER": "warn", "FSD": "crit", "TRIM": "info"})
        self.assertEqual(self.p.flags("OL"), []); self.assertEqual(self.p.flags(None), [])

    def test_alarm_and_beeper(self):
        self.assertEqual(self.p.alarm({"ups.alarm": "Overload!"}), "Overload!")
        for none in ("", "None", "no alarms", None): self.assertEqual(self.p.alarm({"ups.alarm": none}), "")
        self.assertEqual(self.p.beeper({"ups.beeper.status": "Muted"}), "muted"); self.assertEqual(self.p.beeper({"ups.beeper.status": "x"}), "")

    def test_margin_on_mains_uses_full_charge_projection(self):
        v = {"ups.status": "OL", "battery.runtime": "600", "battery.charge": "50", "battery.runtime.low": "120"}
        m = self.p.margin(v, 300)
        self.assertEqual((m["basis"], m["margin_s"], m["ok"]), ("full", 1080, True))
        v2 = dict(v, **{"battery.runtime": "100", "battery.charge": "100", "battery.runtime.low": "30"})
        self.assertFalse(self.p.margin(v2, 300)["ok"])

    def test_margin_on_battery_uses_runtime_now(self):
        m = self.p.margin({"ups.status": "OB DISCHRG", "battery.runtime": "400", "battery.charge": "40"}, 300)
        self.assertEqual((m["basis"], m["margin_s"], m["ok"]), ("now", 400, True))
        self.assertFalse(self.p.margin({"ups.status": "OB", "battery.runtime": "250", "battery.charge": "40"}, 300)["ok"])
        self.assertIsNone(self.p.margin({"ups.status": "OL"}, 300)); self.assertIsNone(self.p.margin({"battery.runtime": "x"}, 300)); self.assertIsNone(self.p.margin(None, 300))

    def test_quality_counts_runs_not_samples_and_ignores_outage_and_noise(self):
        now = 10 ** 9; rows = []
        for i in range(2000):
            t = now - 86400 + i * 40; v = 230.0
            if 100 <= i < 110: v = 190.0            # sag (10 samples)
            if 500 == i: v = 260.0                  # single stray reading: noise
            if 800 <= i < 806: v = 0.0              # outage (counted elsewhere)
            if 1200 <= i < 1203: v = 255.0          # surge
            rows.append((t, v))
        q = self.p.quality(rows, 230, now)
        w = q["w"]["24h"]
        self.assertEqual((q["lo"], q["hi"]), (207, 253))
        self.assertEqual((w["low"], w["high"]), (1, 1))
        self.assertEqual(w["min"], 190.0)

    def test_quality_gap_splits_runs_and_estimates_nominal(self):
        now = 10 ** 9
        rows = [(now - 5000 + i * 10, 230.0) for i in range(100)]
        rows += [(now - 3000 + i * 10, 150.0) for i in range(3)] + [(now - 1000 + i * 10, 150.0) for i in range(3)]
        q = self.p.quality(rows, None, now)
        self.assertEqual((q["nominal"], q["w"]["24h"]["low"]), (230, 2))
        self.assertEqual(self.p.quality([], None, now)["w"], {})

class Server(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = support.load("nut-monitor/server.py"); cls.m.DATA_DIR.mkdir(parents=True, exist_ok=True)
    def setUp(self):
        self.m.db_init()
        c = self.m.db_connect(); c.execute("DELETE FROM outages"); c.execute("DELETE FROM history"); c.commit(); c.close()
        self.m._power_cache.clear(); self.ev = []
        self._rec = self.m.auth.record_event
        self.m.auth.record_event = lambda mod, lv, tx, k=None, **p: self.ev.append((lv, k, p))
        self.m.auth._state_seen.clear()
    def tearDown(self): self.m.auth.record_event = self._rec

    def test_events_first_reading_memorizes_then_changes_report(self):
        base = {"ups.status": "OL CHRG", "battery.runtime": "3000", "battery.charge": "100"}
        self.m._power_events("s", "u", base)
        self.assertEqual(self.ev, [])
        self.m._power_events("s", "u", dict(base, **{"ups.status": "OL RB", "ups.alarm": "Replace battery"}))
        self.assertEqual(sorted(e[1] for e in self.ev), ["ups_alarm", "ups_flag"])
        self.m._power_events("s", "u", dict(base, **{"ups.status": "OL RB", "ups.alarm": "Replace battery"}))
        self.assertEqual(len(self.ev), 2)                                                   # nothing repeated
        self.m._power_events("s", "u", base)
        self.assertEqual(sorted(e[1] for e in self.ev[2:]), ["ups_alarm_ok", "ups_flag_off"])

    def test_margin_event_only_on_change(self):
        ok = {"ups.status": "OL", "battery.runtime": "3000", "battery.charge": "100"}
        bad = dict(ok, **{"battery.runtime": "200"})
        self.m._power_events("s", "u", ok); self.m._power_events("s", "u", bad); self.m._power_events("s", "u", bad)
        self.assertEqual([e[1] for e in self.ev], ["ups_margin"]); self.assertEqual(self.ev[0][2]["need"], 5)
        self.m._power_events("s", "u", ok)
        self.assertEqual([e[1] for e in self.ev], ["ups_margin", "ups_margin_ok"])

    def test_power_info_reads_history_and_transfers(self):
        now = int(time.time()); c = self.m.db_connect()
        c.executemany("INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      [("s", "u", now - 3600 + i * 10, 100, 0, 10, 190.0 if 100 <= i < 110 else 230.0, 230, 0, 0) for i in range(300)])
        c.execute("INSERT INTO outages (srv_id,ups,t_start,t_end,min_charge) VALUES ('s','u',?,?,90)", (now - 7200, now - 7000)); c.commit(); c.close()
        p = self.m.power_info("s", "u", {"input.voltage.nominal": "230", "ups.status": "OL CHRG"})
        w = p["quality"]["w"]
        self.assertEqual((w["24h"]["low"], w["24h"]["transfers"], w["7d"]["transfers"]), (1, 1, 1))
        self.assertEqual(p["flags"], []); self.assertEqual(p["alarm"], "")

if __name__ == "__main__":
    unittest.main()
