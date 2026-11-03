"""WAN Monitor: percentiles, calidad por destino, velocidad contra el plan, disponibilidad / MTBF y eventos sostenidos."""
import time, unittest
from tests import support

m = support.load("wan-monitor/server.py")
st = m.wst
NOW = 2_000_000_000

class Pure(unittest.TestCase):
    def test_percentiles(self):
        v = list(range(1, 101))
        self.assertAlmostEqual(st.percentile(v, 50), 50.5); self.assertAlmostEqual(st.percentile(v, 99), 99.01)
        self.assertIsNone(st.percentile([], 50)); self.assertIsNone(st.percentile([None, "x", float("nan")], 50))
        s = st.latency_stats([10] * 98 + [200, 400])
        self.assertEqual((s["n"], s["p50"], s["max"]), (100, 10.0, 400.0)); self.assertGreater(s["p99"], s["p95"])
        self.assertEqual(st.latency_stats([])["n"], 0)

    def test_targets(self):
        rows = [("1.1.1.1", 10, 0, 1)] * 9 + [("1.1.1.1", None, 100, 0)] + [("8.8.8.8", 30, 0, 1)] * 5
        r = {x["host"]: x for x in st.target_stats(rows)}
        self.assertEqual((r["1.1.1.1"]["n"], r["1.1.1.1"]["fail_pct"], r["1.1.1.1"]["loss"]), (10, 10.0, 10.0))
        self.assertEqual((r["8.8.8.8"]["rtt"], r["8.8.8.8"]["fail_pct"]), (30.0, 0.0))

    def rows(self, vals, step=43200):
        return [(NOW - (len(vals) - i) * step, d, u, None) for i, (d, u) in enumerate(vals)]

    def test_speed_plan_hours_trend_and_streak(self):
        rows = self.rows([(100, 20)] * 6 + [(60, 20), (50, 20), (40, 20)])
        r = st.speed_stats(rows, 100, 20, NOW, lambda t: (t // 3600) % 24)
        self.assertEqual(r["last"]["down"], 40); self.assertEqual(r["low_streak"], 3)
        self.assertEqual(r["avg30"]["down"], 83); self.assertEqual(r["avg30"]["up"], 100)
        self.assertTrue(r["hours"] and r["trend"])
        r2 = st.speed_stats(rows + [(NOW - 10, 90, 20, None)], 100, 20, NOW, lambda t: 0)
        self.assertEqual(r2["low_streak"], 0)                                  # a good test breaks the streak
        self.assertEqual(st.speed_stats(rows, 0, 0, NOW, lambda t: 0)["low_streak"], 0)   # no plan, no judgement
        self.assertEqual(st.speed_stats([(NOW, None, None, "err")], 100, 20, NOW, lambda t: 0)["n"], 0)

    def test_outages_and_mtbf(self):
        w = 7 * 86400
        outs = [(NOW - 5 * 86400, NOW - 5 * 86400 + 600, "wan"), (NOW - 86400, NOW - 86400 + 1800, "lan"), (NOW - 20 * 86400, NOW - 20 * 86400 + 60, "internet"), (NOW - 100, None, "internet")]
        r = st.outage_stats(outs, NOW, w, NOW - 30 * 86400)
        self.assertEqual((r["count"], r["longest"], r["scopes"]), (3, 1800, {"lan": 1, "wan": 1, "internet": 1}))
        self.assertEqual(r["down"], 600 + 1800 + 100); self.assertTrue(r["mtbf"] > 0)
        new = st.outage_stats([], NOW, w, NOW - 600)                           # 10 min of history: not judged
        self.assertEqual((new["count"], new["pct"], new["mtbf"]), (0, None, None))
        self.assertEqual(st.outage_stats([], NOW, w, NOW - 3 * 86400)["pct"], 100.0)

    def test_sustain(self):
        s = st.Sustain(3)
        self.assertEqual([s.update("a", b) for b in (1, 1, 0, 1, 1, 1)], [None, None, None, None, None, "on"])
        self.assertEqual([s.update("a", b) for b in (1, 0, 0, 0)], [None, None, None, "off"])
        self.assertIsNone(s.update("a", 0))

class Server(unittest.TestCase):
    def setUp(self):
        self.ev = []
        self._rec = m.auth.record_event
        m.auth.record_event = lambda mod, lv, tx, k=None, **p: self.ev.append((lv, k, p))
        m.S.speed_low = 0
        m._sus.on.clear(); m._sus.c.clear()
        m._db("DELETE FROM wan_speed"); m._db("DELETE FROM wan_targets"); m._stats_cache[1] = None
    def tearDown(self): m.auth.record_event = self._rec

    def r(self, up=True, loss=0.0, rtt=20.0): return {"up": up, "loss": loss, "rtt": rtt}

    def test_sustained_loss_and_latency_events(self):
        for _ in range(2): m.sustained_events(self.r(loss=10))
        self.assertEqual(self.ev, [])                                           # not yet
        m.sustained_events(self.r(loss=10, rtt=300)); 
        self.assertEqual([e[1] for e in self.ev], ["wan_loss"])
        m.sustained_events(self.r(loss=10, rtt=300)); m.sustained_events(self.r(loss=10, rtt=300))
        self.assertEqual([e[1] for e in self.ev], ["wan_loss", "wan_lat"])
        for _ in range(3): m.sustained_events(self.r())
        self.assertEqual(sorted(e[1] for e in self.ev[2:]), ["wan_lat_ok", "wan_loss_ok"])
        n = len(self.ev); m.sustained_events(self.r(up=False, loss=100))        # outages have their own events
        self.assertEqual(len(self.ev), n)

    def test_speed_low_event_and_alert(self):
        cfg = m.load_config(); cfg["speed"]["plan_down"] = 100; cfg["speed"]["plan_up"] = 0
        now = int(time.time())
        for i, d in enumerate((50, 55, 60)):
            m._db("INSERT INTO wan_speed (ts,down,up,ping,server,error) VALUES (?,?,?,?,?,?)", (now - 3600 * (3 - i), d, 10, 5, "x", None))
        m.speed_events(cfg)
        self.assertEqual([e[1] for e in self.ev], ["wan_speed_low"])
        self.assertTrue(any(a["type"] == "speed_low" for a in m.compute_alerts({})))
        m._db("INSERT INTO wan_speed (ts,down,up,ping,server,error) VALUES (?,?,?,?,?,?)", (now, 95, 10, 5, "x", None))
        m.speed_events(cfg)
        self.assertEqual([e[1] for e in self.ev], ["wan_speed_low", "wan_speed_ok"])
        self.assertFalse(any(a["type"] == "speed_low" for a in m.compute_alerts({})))

    def test_target_samples_and_stats(self):
        now = int(time.time())
        for i in range(5):
            m.store_targets({"ts": now - i * 30, "targets": [{"host": "1.1.1.1", "kind": "ping", "rtt": 10 + i, "loss": 0, "ok": True},
                                                              {"host": "9.9.9.9", "kind": "tcp", "port": 443, "rtt": None, "loss": 100, "ok": False}]})
        s = m.wan_stats(m.load_config())
        t = {x["host"]: x for x in s["targets"]["24h"]}
        self.assertEqual(t["1.1.1.1"]["n"], 5); self.assertEqual(t["tcp:9.9.9.9:443"]["fail_pct"], 100.0)
        self.assertEqual(set(s["avail"]), {"24h", "7d", "30d"})

if __name__ == "__main__":
    unittest.main()
