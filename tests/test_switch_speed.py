"""Switch Monitor: aviso cuando un puerto queda bajo su velocidad habitual (p. ej. 1G → 100M por un cable o un puerto trabado). La habitual es la
más alta de los últimos 7 días; el aviso necesita dos lecturas seguidas, sobrevive a un reinicio y se apaga solo al volver a la habitual.
EN: Switch Monitor: warning when a port stays below its usual speed (e.g. 1G → 100M from a cable or a stuck port). The usual one is the highest
of the last 7 days; the warning needs two readings in a row, survives a restart and clears by itself when back at the usual speed."""
import json
import unittest
from pathlib import Path

from tests import test_switches as ts

ROOT = Path(__file__).resolve().parents[1]
T0 = 3_000_000.0


def port(n, mbps, up=True):
    p = ts.mk_port(n, up=up)
    p["speed_mbps"] = mbps if up else 0
    return p


class Speed(unittest.TestCase):
    setUp, add, feed = ts.ManagerTests.setUp, ts.ManagerTests.add, ts.ManagerTests.feed

    def readings(self, sid, speeds, start=T0, step=60):
        for i, sp in enumerate(speeds):
            self.feed(sid, ts.mk_snap("zx310s", start + i * step, [port(1, sp), port(2, 1000)]))

    def port1(self):
        return next(p for p in self.m.state()["switches"][0]["ports"] if p["port"] == 1)

    def kinds(self): return [e[1] for e in self.events]

    def test_drop_needs_two_readings_then_warns_and_recovers(self):
        sid = self.add()["id"]
        self.readings(sid, [1000, 1000, 100])
        self.assertFalse(self.port1()["slow"]); self.assertNotIn("sw_speed", self.kinds())           # one reading is not enough
        self.readings(sid, [100], start=T0 + 180)
        p = self.port1()
        self.assertEqual((p["slow"], p["usual_mbps"]), (True, 1000))
        self.assertEqual(self.kinds().count("sw_speed"), 1)
        ev = next(e for e in self.events if e[1] == "sw_speed")
        self.assertEqual((ev[0], ev[2]["d"], ev[2]["b"], ev[2]["p"]), ("warn", 100, 1000, 1))
        alerts = self.m.state()["switches"][0]["alerts"]
        self.assertIn({"lv": "warn", "k": "speed", "p": 1, "d": 100, "b": 1000}, alerts)
        self.readings(sid, [100, 100], start=T0 + 240)
        self.assertEqual(self.kinds().count("sw_speed"), 1)                                          # no repeat while it stays low
        self.readings(sid, [1000], start=T0 + 360)
        self.assertFalse(self.port1()["slow"]); self.assertIn("sw_speed_ok", self.kinds())
        self.assertEqual(self.m.state()["switches"][0]["alerts"], [])

    def test_link_down_is_not_a_speed_drop(self):
        sid = self.add()["id"]
        self.readings(sid, [1000, 1000])
        for i in range(3):
            self.feed(sid, ts.mk_snap("zx310s", T0 + 200 + i * 60, [port(1, 0, up=False), port(2, 1000)]))
        self.assertFalse(self.port1()["slow"]); self.assertNotIn("sw_speed", self.kinds())

    def test_a_slower_device_becomes_usual_after_seven_days(self):
        sid = self.add()["id"]
        self.readings(sid, [1000])
        later = T0 + 8 * 86400
        self.readings(sid, [100, 100, 100], start=later)
        self.assertFalse(self.port1()["slow"])                                                       # 1000 was seen more than 7 days ago

    def test_usual_speed_survives_a_restart_and_deleted_switches_are_dropped(self):
        sid = self.add()["id"]
        self.readings(sid, [1000])
        f = Path(self.d) / "switch_speeds.json"
        self.assertEqual(json.loads(f.read_text())[sid]["1"], {"1000": T0})
        m2 = ts.sw.Manager(self.d, hooks={"event": lambda *a, **k: None, "changed": lambda k, st: None, "hosts": dict})
        self.assertEqual(m2._usual_speed(sid, 1, T0 + 60), 1000)
        other = self.add("otro")["id"]
        self.m.delete_switch(sid)
        self.readings(other, [1000])
        self.assertNotIn(sid, json.loads(f.read_text()))

    def test_paused_switch_has_no_speed_alert(self):
        sid = self.add()["id"]
        self.readings(sid, [1000, 100, 100])
        self.m.save_switch({"id": sid, "enabled": False})
        self.assertEqual(self.m.state()["switches"][0]["alerts"], [])

    def test_pages_show_it(self):
        js = (ROOT / "net-monitor/static/switches.js").read_text(encoding="utf-8")
        self.assertIn("${p.slow ? ' slow' : ''}", js); self.assertEqual(js.count("swSlow:"), 2)
        self.assertIn(".spd-pill.slow{--spd:var(--orange);background:var(--orange-dim)}", (ROOT / "net-monitor/static/app.css").read_text(encoding="utf-8"))
        ov = (ROOT / "overview/static/app.js").read_text(encoding="utf-8")
        self.assertIn("else if(a.k==='speed')", ov)
        for k in ("swspeed:", "swusual:", "sw_speed:", "sw_speed_ok:"): self.assertEqual(ov.count(k), 2, k)


if __name__ == "__main__":
    unittest.main()
