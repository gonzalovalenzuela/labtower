"""UPS Monitor: cortes de energía, racha en línea y disponibilidad (nut-monitor/server.py)."""
import time
import unittest

from tests import support


class UpsOutages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = support.load("nut-monitor/server.py")
        cls.m.DATA_DIR.mkdir(parents=True, exist_ok=True)
    def setUp(self):
        self.m.db_init()
        c = self.m.db_connect(); c.execute("DELETE FROM outages"); c.execute("DELETE FROM history"); c.commit(); c.close()
        self.m._open_out.clear(); self.m._out_min.clear(); self.m._stats_cache.clear()
        self.now = int(time.time())
    def _history(self, ups, start, end, outs, step=60, vin_ok=230.0):
        rows = []
        for ts in range(start, end, step):
            out = any(a <= ts < b for a, b in outs)
            rows.append(("s", ups, ts, 50 if out else 100, 0, 10, 0 if out else vin_ok, 230, 0, 0))
        c = self.m.db_connect()
        c.executemany("INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        c.commit(); self.m._outages_backfill(c); c.close()
    def _outages(self):
        c = self.m.db_connect(); r = [tuple(x) for x in c.execute("SELECT t_start,t_end,min_charge,src FROM outages ORDER BY t_start")]; c.close(); return r

    def test_backfill_rebuilds_past_outages_from_input_voltage(self):
        n = self.now
        self._history("u", n - 10 * 86400, n, [(n - 3 * 86400, n - 3 * 86400 + 1200), (n - 7200, n - 7200 + 300)])
        o = self._outages()
        self.assertEqual(len(o), 2)
        self.assertAlmostEqual(o[0][1] - o[0][0], 1140, delta=60)
        self.assertEqual((o[0][2], o[0][3]), (50.0, "hist"))

    def test_backfill_ignores_ups_without_input_voltage(self):
        self._history("novin", self.now - 3600, self.now, [], vin_ok=0.0)
        self.assertEqual(self._outages(), [])

    def test_stats_streak_count_and_availability(self):
        n = self.now
        self._history("u", n - 10 * 86400, n, [(n - 3 * 86400, n - 3 * 86400 + 1200), (n - 7200, n - 7200 + 300)])
        st = self.m.ups_stats("s", "u")
        self.assertEqual(st["count30"], 2); self.assertFalse(st["on_battery"])
        self.assertEqual(st["last"]["dur"], 300)
        self.assertTrue(6600 <= st["streak"] <= 7000, st["streak"])
        a = st["avail"]
        self.assertTrue(99.0 < a["24h"] < 100 and 99.0 < a["7d"] < 100 and a["30d"] >= a["7d"] - 0.5, a)

    def test_availability_needs_one_hour_of_data(self):
        self._history("u", self.now - 1800, self.now, [])
        st = self.m.ups_stats("s", "u")
        self.assertEqual(st["avail"], {"24h": None, "7d": None, "30d": None})

    def test_live_outage_opens_updates_and_closes(self):
        m, n = self.m, self.now
        m.outage_track("s", "u", "OB DISCHRG", 80, n); m.outage_track("s", "u", "OB DISCHRG", 60, n + 10); m.outage_track("s", "u", "OB LB", 20, n + 20)
        m._stats_cache.clear(); st = m.ups_stats("s", "u")
        self.assertTrue(st["on_battery"]); self.assertEqual(st["streak"], 0)
        m.outage_track("s", "u", "OL CHRG", 25, n + 100)
        o = self._outages(); self.assertEqual(o, [(n, n + 100, 20.0, "live")])

    def test_open_outage_survives_a_restart_without_duplicating(self):
        m, n = self.m, self.now
        m.outage_track("s", "u", "OB", 70, n)
        m._open_out.clear(); m._out_min.clear()                 # el servicio se reinició
        m.outage_track("s", "u", "OB", 65, n + 10)
        c = m.db_connect(); open_n = c.execute("SELECT COUNT(*) FROM outages WHERE t_end IS NULL").fetchone()[0]; c.close()
        self.assertEqual(open_n, 1)

    def test_prune_keeps_at_most_2000_outages_per_ups(self):
        n = self.now; c = self.m.db_connect()
        c.executemany("INSERT INTO outages (srv_id,ups,t_start,t_end,min_charge) VALUES (?,?,?,?,?)",
                      [("s", "flap", n - 5000 + i, n - 5000 + i + 1, 50) for i in range(2600)] + [("s", "other", n - 100, n - 90, 50)])
        c.execute("INSERT INTO outages (srv_id,ups,t_start) VALUES ('s','flap',?)", (n - 3,)); c.commit(); c.close()
        self.m.db_prune()
        c = self.m.db_connect()
        flap = c.execute("SELECT COUNT(*) FROM outages WHERE ups='flap'").fetchone()[0]
        other = c.execute("SELECT COUNT(*) FROM outages WHERE ups='other'").fetchone()[0]
        opened = c.execute("SELECT COUNT(*) FROM outages WHERE t_end IS NULL").fetchone()[0]; c.close()
        self.assertLessEqual(flap, 2000); self.assertEqual((other, opened), (1, 1))
if __name__ == "__main__": unittest.main()


class UpsEnergy(unittest.TestCase):
    """Cortes por mes, últimos cortes y consumo en kWh. / Outages per month, latest outages and kWh used."""
    @classmethod
    def setUpClass(cls):
        cls.m = support.load("nut-monitor/server.py")
        cls.m.DATA_DIR.mkdir(parents=True, exist_ok=True)
    def setUp(self):
        m = self.m; m.db_init()
        c = m.db_connect(); c.execute("DELETE FROM outages"); c.execute("DELETE FROM history"); c.commit(); c.close()
        m._energy_cache.clear(); m.auth.write_json(m.ENERGY_FILE, {})
    tearDown = setUp

    def test_kwh_and_outages(self):
        m, now = self.m, int(time.time())
        lt = time.localtime(now); today0 = int(time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1)))
        rows = [("s", "u", ts, 100, 0, 10, 230, 230, 500, 0) for ts in range(today0, today0 + 7200 + 1, 60)]                 # 2 h at 500 W = 1 kWh
        rows += [("s", "u", ts, 100, 0, 10, 230, 230, 500, 0) for ts in range(today0 + 4 * 3600, today0 + 5 * 3600, 3600)]  # gaps > OUT_GAP do not count
        c = m.db_connect()
        c.executemany("INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        c.executemany("INSERT INTO outages (srv_id,ups,t_start,t_end,min_charge) VALUES (?,?,?,?,?)",
                      [("s", "u", today0 + 600, today0 + 900, 80), ("s", "u", today0 + 1200, today0 + 2400, 60), ("s", "u", now - 400 * 86400, now - 400 * 86400 + 60, 90)])
        c.commit(); c.close()
        r = m.energy_report("s", "u", max(today0 + 7200, now))
        self.assertAlmostEqual(r["kwh_today"], 1.0, places=2); self.assertAlmostEqual(r["kwh_30"], 1.0, places=2)
        cur = r["months"][-1]
        self.assertEqual((cur["n"], cur["avg"], cur["max"]), (2, 750, 1200))
        self.assertEqual(len(r["months"]), 12); self.assertEqual([o["dur"] for o in r["outages"]], [1200, 300])    # the 400-day-old one is left out
        self.assertIsNone(r["price"])
        m.auth.write_json(m.ENERGY_FILE, {"price": 150}); self.assertEqual(m.energy_report("s", "u")["price"], 150.0)

    def test_no_power_reported(self):
        m, now = self.m, int(time.time())
        c = m.db_connect()
        c.executemany("INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      [("s", "w", ts, 100, 0, 0, 230, 230, 0, 0) for ts in range(now - 3600, now, 60)])
        c.commit(); c.close()
        r = m.energy_report("s", "w")
        self.assertIsNone(r["kwh_30"]); self.assertIsNone(r["months"][-1]["kwh"])

    def test_api(self):
        m = self.m
        old = m.load_servers
        m.load_servers = lambda: [{"id": "s", "name": "S", "host": "192.0.2.9", "port": 3493}]
        srv = support.Server(m.H)
        try:
            adm, ro = support.make_user("en_adm", support.ADMIN), support.make_user("en_ro", support.READONLY)
            code, d = srv.call("GET", "/api/energy?srv=s&ups=u", token=ro)
            self.assertEqual((code, d["can_edit"]), (200, False))
            self.assertEqual(srv.call("GET", "/api/energy?srv=x&ups=u", token=ro)[0], 404)
            self.assertEqual(srv.call("POST", "/api/energy-price", {"price": 150}, token=ro)[0], 403)
            for bad in (0, -1, "150", True, 1e7): self.assertEqual(srv.call("POST", "/api/energy-price", {"price": bad}, token=adm)[0], 400, bad)
            self.assertEqual(srv.call("POST", "/api/energy-price", {"price": 172.5}, token=adm)[0], 200)
            self.assertEqual(m.energy_price(), 172.5)
            self.assertEqual(srv.call("POST", "/api/energy-price", {"price": None}, token=adm)[0], 200); self.assertIsNone(m.energy_price())
        finally: srv.close(); m.load_servers = old
