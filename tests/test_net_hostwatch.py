"""Net Monitor: cambio de MAC, puertos nuevos, equipos conocidos, conectividad y vigilancia / MAC change, new ports, known devices, connectivity and watch."""
import time
import unittest

from tests import support

m = support.load("net-monitor/server.py")
hw = m.hw
NOW = 2_000_000_000

class Pure(unittest.TestCase):
    def test_mac_change_only_when_it_was_online(self):
        ex = {"online": True, "mac": "AA:BB:CC:00:00:01"}
        self.assertEqual(hw.mac_change(ex, {"mac": "aa:bb:cc:00:00:02"})["new"], "aa:bb:cc:00:00:02")
        self.assertIsNone(hw.mac_change(ex, {"mac": "aa-bb-cc-00-00-01"}))                 # same MAC, other format
        self.assertIsNone(hw.mac_change(dict(ex, online=False), {"mac": "aa:bb:cc:00:00:02"}))   # DHCP gave the IP to another device
        self.assertIsNone(hw.mac_change(ex, {"mac": ""})); self.assertIsNone(hw.mac_change({}, {"mac": "aa:bb:cc:00:00:02"})); self.assertIsNone(hw.mac_change(None, None))

    def test_port_news_memorizes_and_ignores_flapping(self):
        p = lambda *n: [{"port": x, "service": ""} for x in n]
        seen, new = hw.port_news({}, {"ports": p(22, 80)})
        self.assertEqual((seen, new), ([22, 80], []))                                   # no previous reading: only memorize
        seen, new = hw.port_news({"ports": p(22, 80)}, {"ports": p(22)})                  # 80 closed (timeout): nothing
        self.assertEqual(new, []); self.assertEqual(seen, [22, 80])
        ex = {"ports": p(22), "ports_seen": [22, 80]}
        self.assertEqual(hw.port_news(ex, {"ports": p(22, 80)})[1], [])                  # 80 reopened: seen before
        self.assertEqual(hw.port_news(ex, {"ports": p(22, 80, 3389)})[1], [3389])
        self.assertEqual(hw.port_news({"ports": p(22)}, {"ports": p(22, 23)})[1], [23])  # legacy host without ports_seen: its ports are the baseline
        self.assertEqual(hw.port_news(None, None), ([], []))

    def test_known_uses_baseline(self):
        self.assertTrue(hw.known({"first_seen": 100}, 500)); self.assertFalse(hw.known({"first_seen": 900}, 500))
        self.assertTrue(hw.known({"first_seen": 900, "known": True}, 500)); self.assertFalse(hw.known({"first_seen": 900}, None)); self.assertFalse(hw.known(None, 5))

    def test_conn_stats_and_week_bar(self):
        d = 86400
        ev = [{"ts": NOW - 5 * d, "event": "down"}, {"ts": NOW - 5 * d + 6 * 3600, "event": "up"}, {"ts": NOW - d, "event": "down"}, {"ts": NOW - d + 3600, "event": "up"}]
        c = hw.conn_stats(ev, NOW - 10 * d, True, NOW)
        self.assertEqual(c["7d"]["drops"], 2)
        self.assertAlmostEqual(c["7d"]["pct"], 100 * (7 * d - 7 * 3600) / (7 * d), places=1)
        self.assertLess(c["30d"]["observed"], 11 * d)                                     # not judged over time it did not observe
        wb = hw.week_bar(ev, NOW - 10 * d, True, NOW)
        self.assertEqual(len(wb), 42); self.assertTrue(min(x for x in wb if x is not None) < 1)
        self.assertEqual(hw.conn_stats([], NOW - 60, True, NOW)["7d"]["pct"], None)         # a minute of history says nothing

    def test_trimmed_log_deduces_the_initial_state(self):
        ev = [{"ts": NOW - 1000 + i * 2, "event": "down" if i % 2 == 0 else "up"} for i in range(200)]
        seg = hw.timeline(ev, NOW - 10 * 86400, True, NOW)
        self.assertEqual(seg[0][0], ev[0]["ts"]); self.assertTrue(seg[-1][2])

    def test_latency_summary(self):
        s = hw.latency_summary([(i, 10.0 + i, 1) for i in range(20)] + [(30, None, 0)])
        self.assertEqual((s["n"], s["loss"]), (21, 4.76)); self.assertEqual(s["max"], 29.0)
        self.assertEqual(hw.latency_summary([])["n"], 0)

class Server(unittest.TestCase):
    def setUp(self):
        self.ev = []
        self._rec = m.auth.record_event
        m.auth.record_event = lambda mod, lv, tx, k=None, **p: self.ev.append((lv, k, p))
        m.auth._state_seen.clear(); m._watch.clear()
        self._lh, self._pt = m.load_hosts, m.ping_ttl
        c = m.auth.metrics_conn(); c.execute("DELETE FROM net_latency"); c.commit(); c.close()
    def tearDown(self): m.auth.record_event = self._rec; m.load_hosts, m.ping_ttl = self._lh, self._pt

    def test_security_events(self):
        h = {"alias": "nas", "hostname": ""}
        m._record_security_events([("mac", "10.0.0.5", h, {"old": "aa:aa:aa:aa:aa:01", "new": "aa:aa:aa:aa:aa:02"}), ("port", "10.0.0.6", h, [3389, 8080])])
        self.assertEqual([(e[0], e[1]) for e in self.ev], [("warn", "net_mac_changed"), ("warn", "net_port_new")])
        self.ev.clear(); m._record_security_events([("port", "10.0.0.6", h, [8080])])
        self.assertEqual(self.ev[0][0], "info")                                           # not a risky port

    def test_flaky_event_once(self):
        now = int(time.time())
        h = {"uptime_history": [{"ts": now - 100 * i, "event": "down" if i % 2 else "up"} for i in range(1, 12)]}
        m._flaky_check("10.0.0.7", {"uptime_history": []})                                 # baseline
        m._flaky_check("10.0.0.7", h); m._flaky_check("10.0.0.7", h)
        self.assertEqual([e[1] for e in self.ev], ["net_flaky"])

    def test_watch_round_events_and_latency(self):
        hosts = {"10.0.0.9": {"ip": "10.0.0.9", "watch": True, "alias": "srv"}, "10.0.0.10": {"ip": "10.0.0.10"}}
        m.load_hosts = lambda: hosts
        answers = {"v": (True, 64, 1.5)}
        m.ping_ttl = lambda ip: answers["v"]
        m._watch_round()
        self.assertEqual(self.ev, [])                                                      # first reading only memorizes
        answers["v"] = (False, 0, 0.0)
        m._watch_round(); self.assertEqual(self.ev, [])                                    # one failure is not enough
        m._watch_round(); self.assertEqual([e[1] for e in self.ev], ["net_watch_down"]); self.assertTrue(m._watch["10.0.0.9"]["down"])
        answers["v"] = (True, 64, 2.0)
        m._watch_round(); self.assertEqual([e[1] for e in self.ev], ["net_watch_down", "net_watch_up"])
        pts = m.latency_points("10.0.0.9", 3600)
        self.assertEqual(len(pts), 1)                                                      # same-second samples collapse on the primary key
        self.assertNotIn("10.0.0.10", m._watch)

if __name__ == "__main__":
    unittest.main()
