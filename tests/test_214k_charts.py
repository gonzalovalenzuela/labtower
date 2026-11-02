"""2.1.4k: gráficos unificados (charts.js) — periodo anterior en el backend, filtro de eventos y copias idénticas del motor.
EN: unified charts (charts.js) — previous period in the backend, event filter and identical copies of the engine."""
import re, time, unittest
from pathlib import Path
from tests import support

ROOT = Path(__file__).resolve().parent.parent
dns = support.load("dns-monitor/server.py"); nas = support.load("nas-monitor/server.py"); wan = support.load("wan-monitor/server.py")
nut = support.load("nut-monitor/server.py"); ov = support.load("overview/server.py")

class Windows(unittest.TestCase):
    def test_prev_window_is_the_period_just_before(self):
        for m in (dns, nas, wan):
            span = m.RANGE_SECS["1d"]
            a, b = m.history_window("1d", prev=True)
            self.assertEqual(b - a, span)
            self.assertAlmostEqual(b, time.time() - span, delta=3)
            cur = m.history_window("1d")
            self.assertAlmostEqual(cur[0], time.time() - span, delta=3)
    def test_all_has_no_previous_period(self):
        for m in (dns, nas, wan):
            self.assertIsNone(m.history_window("all", prev=True))
    def test_week_range_exists(self):
        for m in (dns, nas, wan):
            self.assertEqual(m.RANGE_SECS["1w"], 7 * 86400)

class NutUntil(unittest.TestCase):
    def test_db_query_until(self):
        nut.DATA_DIR.mkdir(parents=True, exist_ok=True); nut.db_init()
        now = int(time.time())
        with nut._db_lock:
            c = nut.db_connect()
            for i in range(10):
                c.execute("INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp) VALUES ('k','u',?,100,900,10,230,230,100,30)", (now - 1000 + i * 100,))
            c.commit(); c.close()
        allr = nut.db_query("k", "u", since_ts=now - 2000)
        old = nut.db_query("k", "u", since_ts=now - 2000, until_ts=now - 500)
        self.assertEqual(len(allr), 10)
        self.assertTrue(0 < len(old) < 10)
        self.assertTrue(all(p["ts"] < now - 500 for p in old))

class Events(unittest.TestCase):
    def test_events_filter_by_module(self):
        tok = support.make_user("k214adm", support.ADMIN)
        support.auth.record_event("wan", "warn", "w", "wan_ipc")
        support.auth.record_event("nut", "warn", "n", "ups_srv_up")
        s = support.Server(ov.H)
        mods = lambda q: {e["m"] for e in s.call("GET", "/api/events" + q, None, token=tok)[1]["events"]}
        self.assertEqual(mods("?m=wan"), {"wan"})
        self.assertEqual(mods("?m=nut"), {"nut"})
        self.assertTrue({"wan", "nut"} <= mods(""))

class Engine(unittest.TestCase):
    MODS = ["dns-monitor", "nas-monitor", "wan-monitor", "nut-monitor", "net-monitor"]
    def test_identical_copies_and_loaded(self):
        ref = (ROOT / "dns-monitor/static/charts.js").read_text()
        for m in self.MODS:
            self.assertEqual((ROOT / m / "static/charts.js").read_text(), ref, m)
            self.assertIn('<script src="charts.js"></script>', (ROOT / m / "static/index.html").read_text(), m)
    def test_no_module_draws_its_own_line_charts(self):
        for m, f in (("nut-monitor", "app.js"), ("dns-monitor", "app.js"), ("nas-monitor", "app.js"), ("wan-monitor", "app.js"), ("net-monitor", "switches.js")):
            src = (ROOT / m / "static" / f).read_text()
            self.assertIn("VC.draw(", src, m)
            self.assertNotIn("createLinearGradient", src, m)
    def test_nut_range_week(self):
        src = (ROOT / "nut-monitor/static/app.js").read_text()
        self.assertIn("'1w':604800", src)
        self.assertIn("toggleVCmp", src)

if __name__ == "__main__":
    unittest.main()
