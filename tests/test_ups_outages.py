"""UPS Monitor: cortes de energía, racha en línea y disponibilidad (nut-monitor/server.py)."""
import time, unittest
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
