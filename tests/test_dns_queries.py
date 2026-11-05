"""2.1.7f: consultas por hora y por día en DNS Monitor (Pi-hole v6, AdGuard y respaldo propio) / Queries per hour and per day in DNS Monitor (Pi-hole v6, AdGuard and own fallback)."""
import time
import unittest

from tests import support

dns = support.load("dns-monitor/server.py")
NOW = 1_700_000_000          # a fixed instant: 2023-11-14 22:13 UTC


class HourRows(unittest.TestCase):
    def test_groups_by_clock_hour_and_drops_the_cut_hour(self):
        rows = [(NOW - 5 * 3600 + 10, 5, 1), (NOW - 5 * 3600 + 700, 2, 0), (NOW - 100, 7, 2), (NOW - 86400 - 10, 9, 9), (NOW - 86400 + 5, 4, 4)]
        out = dns.hour_rows(rows, NOW)
        self.assertEqual(sum(t for _, t, _ in out), 5 + 2 + 7)                 # the two oldest rows belong to the hour the window cuts in half
        self.assertTrue(all(h % 3600 == 0 for h, _, _ in out))
        self.assertEqual(out[0][1:], (7, 1))

    def test_ignores_bad_rows(self):
        self.assertEqual(dns.hour_rows([(None, 1, 1), ("x", 1, 1)], NOW), [])


class Bars(unittest.TestCase):
    def test_hour_bars_fill_gaps_and_cut_leading_zeros(self):
        bars = dns.build_bars([(NOW - 3 * 3600, 4, 1), (NOW - 3600, 6, 2)], NOW - 7 * 3600, NOW, "hour")
        self.assertEqual(bars[0]["total"], 4)                                    # leading empty hours are cut
        self.assertEqual([b["total"] for b in bars], [4, 0, 6, 0])
        self.assertTrue(all(b["t"] % 3600 == 0 for b in bars))

    def test_day_bars_sum_the_hours_of_each_local_day(self):
        d0 = dns._bucket(NOW - 2 * 86400, "day")
        bars = dns.build_bars([(d0 + 3600, 4, 1), (d0 + 7200, 6, 2), (NOW, 1, 0)], NOW - 30 * 86400, NOW, "day")
        self.assertEqual((bars[0]["t"], bars[0]["total"], bars[0]["blocked"]), (d0, 10, 3))
        self.assertEqual(bars[-1]["total"], 1)

    def test_never_more_than_800_bars(self):
        self.assertLessEqual(len(dns.build_bars([(NOW, 1, 0)], NOW - 3000 * 86400, NOW, "hour")), 800)


class Sources(unittest.TestCase):
    def setUp(self):
        dns._QCACHE.clear()
        self._ph6, self._ag, self._rr = dns._ph6, dns._ag, dns._remote_rows

    def tearDown(self):
        dns._ph6, dns._ag, dns._remote_rows = self._ph6, self._ag, self._rr
        dns._QCACHE.clear()

    def test_pihole_v6_is_read_in_chunks(self):
        calls = []
        def fake(cfg, st, path, params=None, **kw):
            calls.append((path, params))
            return 200, {"history": [{"timestamp": params["from"] + 600, "total": 10, "blocked": 3}]}
        dns._ph6 = fake
        rows = dns._remote_rows({"type": "pihole"}, {"api": "v6"}, 365)
        self.assertGreaterEqual(len(calls), 12)
        self.assertTrue(all(c[0] == "/api/history/database" and c[1]["until"] - c[1]["from"] <= 31 * 86400 for c in calls))
        self.assertEqual(len(rows), len(calls))

    def test_pihole_v6_error_gives_nothing(self):
        dns._ph6 = lambda *a, **k: (404, {})
        self.assertIsNone(dns._remote_rows({"type": "pihole"}, {"api": "v6"}, 7))
        self.assertIsNone(dns._remote_rows({"type": "pihole"}, {"api": "v5"}, 7))      # v5 has no long-term answer here: own counts are used

    def test_adguard_needs_day_retention(self):
        dns._ag = lambda cfg, m, p, body=None: (200, {"time_units": "hours", "dns_queries": [1] * 24})
        self.assertIsNone(dns._remote_rows({"type": "adguard"}, {}, 7))
        dns._ag = lambda cfg, m, p, body=None: (200, {"time_units": "days", "dns_queries": [10, 20, 30], "blocked_filtering": [1, 2, 3]})
        rows = dns._remote_rows({"type": "adguard"}, {}, 7)
        self.assertEqual([r[1] for r in rows], [10, 20, 30])
        self.assertEqual([r[2] for r in rows], [1, 2, 3])
        self.assertLess(rows[0][0], rows[-1][0])

    def test_falls_back_to_the_stored_hours(self):
        sid = "t-queries"
        dns._remote_rows = lambda *a: None
        h = int(time.time()) // 3600 * 3600
        dns.push_hours(sid, [(h - 7200, 11, 2), (h - 3600, 5, 1)])
        try:
            out = dns.queries_range({"type": "adguard"}, {}, sid, "1w")
        finally:
            dns.forget_history(sid)
        self.assertEqual(out["source"], "local")
        self.assertEqual(out["unit"], "hour")
        self.assertEqual([b["total"] for b in out["bars"]][:2], [11, 5])

    def test_remote_source_is_named_and_cached(self):
        n = []
        def rows(*a): n.append(1); return [(int(time.time()) - 3600, 8, 2)]
        dns._remote_rows = rows
        try:
            a = dns.queries_range({"type": "pihole"}, {"api": "v6"}, "t-q2", "1mo"); dns.queries_range({"type": "pihole"}, {"api": "v6"}, "t-q2", "1mo")
        finally:
            pass
        self.assertEqual((a["source"], a["unit"]), ("pihole", "day"))
        self.assertEqual(len(n), 1, "the answer is kept for a few minutes")

    def test_only_known_ranges(self):
        self.assertEqual(set(dns.QRANGES), {"1w", "1mo", "all"})


class Page(unittest.TestCase):
    def test_the_card_has_the_range_buttons_and_the_handler(self):
        js = (support.ROOT / "dns-monitor/static/app.js").read_text()
        self.assertIn('data-on-click="setQRange"', js)
        self.assertRegex(js, r"cspRegister\(\{[^}]*\bsetQRange\b")
        self.assertIn("api/dns/'+encodeURIComponent(id)+'/queries?range=", js)


if __name__ == "__main__":
    unittest.main()
