"""UPS Monitor: autonomía estimada, envejecimiento de la batería y registro de autotests / estimated runtime, ageing and self-test log."""
import datetime, time, unittest
from tests import support

b = support.load("nut-monitor/battery.py")

class Pure(unittest.TestCase):
    def test_runtime_estimate_projects_to_full_battery(self):
        e = b.runtime_estimate({"battery.runtime": "900", "battery.charge": "50", "ups.load": "20"})
        self.assertEqual((e["now_s"], e["full_s"]), (900, 1800))
        self.assertEqual(e["plus50_s"], 1200)                         # 30 % load → 1800 × 20/30

    def test_runtime_estimate_edge_cases(self):
        self.assertIsNone(b.runtime_estimate({"battery.runtime": "0", "battery.charge": "100"}))
        self.assertIsNone(b.runtime_estimate({"battery.runtime": "900", "battery.charge": "5"}))     # too low to project
        self.assertIsNone(b.runtime_estimate({"battery.runtime": "x", "battery.charge": "100"}))
        self.assertIsNone(b.runtime_estimate(None)); self.assertIsNone(b.runtime_estimate({}))
        e = b.runtime_estimate({"battery.runtime": "600", "battery.charge": "100", "ups.load": "80"})
        self.assertIsNone(e["plus50_s"])                              # 120 % does not exist
        e = b.runtime_estimate({"battery.runtime": "600", "battery.charge": "100"})
        self.assertNotIn("plus50_s", e)
        e = b.runtime_estimate({"battery.runtime": "600", "battery.charge": "140", "ups.load": "nan"})
        self.assertEqual(e["full_s"], 600)

    def test_battery_date(self):
        today = datetime.date(2026, 10, 30)
        self.assertEqual(b.battery_age_years("2023/04/30", today), 3.5)
        self.assertEqual(b.battery_age_years("2023-04-30", today), 3.5)
        self.assertEqual(b.battery_age_years("04/30/2023", today), 3.5)
        for bad in ("00/00/00", "", None, 5, "2027/01/01", "1980/01/01", "garbage"):
            self.assertIsNone(b.battery_age_years(bad, today), bad)

    def test_aging_needs_enough_history(self):
        self.assertIsNone(b.aging_trend([]))
        self.assertIsNone(b.aging_trend([(1, 3000, 500), (2, 3000, 500)]))
        self.assertIsNone(b.aging_trend([(1, 3000, 5), (2, 3000, 5), (3, 3000, 5), (4, 3000, 5)]))     # too few samples
        self.assertIsNone(b.aging_trend("x")); self.assertIsNone(b.aging_trend([(1, "a", 500)] * 6))

    def test_aging_detects_decline_and_stability(self):
        steady = [(w, 3000, 900) for w in range(100, 108)]
        self.assertEqual(b.aging_trend(steady)["change_pct"], 0.0); self.assertFalse(b.aging_trend(steady)["warn"])
        falling = [(100 + i, 3000 - i * 150, 900) for i in range(8)]
        t = b.aging_trend(falling)
        self.assertLess(t["change_pct"], -20); self.assertTrue(t["warn"]); self.assertEqual(t["weeks"], 8)

    def test_gaps_in_weeks_still_count_the_span(self):
        t = b.aging_trend([(100, 3000, 900), (101, 3000, 900), (104, 2900, 900), (110, 2800, 900)])
        self.assertEqual(t["weeks"], 11)

    def test_classify_test(self):
        for txt, k in (("Done and passed", "passed"), ("In progress", "running"), ("No test initiated", "none"), ("Done and error", "failed"),
                       ("Done and warning", "failed"), ("Aborted", "failed"), ("", "none"), (None, "none"), ("Something odd", "other"), ("OK", "passed")):
            self.assertEqual(b.classify_test(txt), k, txt)

class Db(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = support.load("nut-monitor/server.py"); cls.m.DATA_DIR.mkdir(parents=True, exist_ok=True)
    def setUp(self):
        m = self.m; m.db_init()
        c = m.db_connect(); c.execute("DELETE FROM history"); c.execute("DELETE FROM selftests"); c.commit(); c.close()
        m._test_last.clear(); m._aging_cache.clear()
        self.ev = []; self._rec = m.auth.record_event
        m.auth.record_event = lambda mod, lv, tx, k=None, **p: self.ev.append((lv, k, p))
    def tearDown(self): self.m.auth.record_event = self._rec

    def test_selftest_log_baseline_changes_and_events(self):
        m = self.m; v = lambda r: {"ups.test.result": r}
        m.selftest_track("s", "u", v("No test initiated"), 1000)
        self.assertEqual(m.selftest_log("s", "u"), [])                     # first reading: baseline only
        m.selftest_track("s", "u", v("No test initiated"), 1010)
        m.selftest_track("s", "u", v("In progress"), 1020)
        m.selftest_track("s", "u", v("Done and passed"), 1030)
        m.selftest_track("s", "u", v("Done and error"), 2000)
        log = m.selftest_log("s", "u")
        self.assertEqual([(x["result"], x["kind"]) for x in log], [("Done and error", "failed"), ("Done and passed", "passed"), ("In progress", "running")])
        self.assertEqual([e[1] for e in self.ev], ["ups_test_ok", "ups_test_fail"])
        m.selftest_track("s", "u", {}, 3000); m.selftest_track("s", "u", None, 3000); m.selftest_track("s", "u", {"ups.test.result": 5}, 3000)
        self.assertEqual(len(m.selftest_log("s", "u")), 3)

    def test_selftest_log_is_capped(self):
        m = self.m
        for i in range(260): m.selftest_track("s", "u", {"ups.test.result": f"r{i}"}, 1000 + i)
        c = m.db_connect(); n = c.execute("SELECT COUNT(*) FROM selftests").fetchone()[0]; c.close()
        self.assertEqual(n, 200)

    def _fill(self, ups, weeks, runtime_of, load=20, per_week=300, now=None):
        now = now or int(time.time()); rows = []
        for w in range(weeks):
            base = now - (weeks - w) * 604800
            for i in range(per_week): rows.append(("s", ups, base + i * 60, 100, runtime_of(w), load, 230, 230, 0, 0))
        c = self.m.db_connect()
        c.executemany("INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp) VALUES (?,?,?,?,?,?,?,?,?,?)", rows); c.commit(); c.close()

    def test_aging_from_history_detects_a_weakening_battery(self):
        self._fill("old", 10, lambda w: 3000 - w * 150)
        t = self.m.aging("s", "old")
        self.assertTrue(t["warn"]); self.assertLess(t["change_pct"], -20)

    def test_aging_stable_and_ignores_other_loads_and_low_charge(self):
        self._fill("ok", 10, lambda w: 3000)
        self._fill("ok", 10, lambda w: 100, load=90)                       # a different load must not pollute the trend
        c = self.m.db_connect(); c.execute("INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp) VALUES ('s','ok',?,40,10,20,230,230,0,0)", (int(time.time()),)); c.commit(); c.close()
        t = self.m.aging("s", "ok")
        self.assertFalse(t["warn"]); self.assertLess(abs(t["change_pct"]), 5)

    def test_aging_without_data_is_none_and_cached(self):
        self.assertIsNone(self.m.aging("s", "empty"))
        self._fill("empty", 10, lambda w: 3000)
        self.assertIsNone(self.m.aging("s", "empty"))                       # cached for hours
        self.m._aging_cache.clear()
        self.assertIsNotNone(self.m.aging("s", "empty"))

    def test_battery_info_and_stats_integration(self):
        m = self.m
        info = m.battery_info("s", "u", {"battery.runtime": "900", "battery.charge": "100", "ups.load": "20", "battery.date": "2024/01/01", "ups.test.result": "Done and passed"})
        self.assertEqual(info["runtime"]["full_s"], 900); self.assertEqual(info["test_now"]["kind"], "passed"); self.assertIsNotNone(info["age_years"])
        c = m.SCache("s"); c._ups = {"u": {"battery.runtime": "900", "battery.charge": "100"}}
        st = c._stats(c._ups)
        self.assertIn("battery", st["u"]); self.assertIn("avail", st["u"])

if __name__ == "__main__":
    unittest.main()
