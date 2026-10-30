"""Switch Monitor: errores CRC/FCS por SNMP, aviso CRC, enlaces que rebotan y vigilancia de enlace por puerto."""
import tempfile, unittest
from tests import support
from tests.test_switches import FakeSNMP, snmp_data, mk_snap, mk_port, sw

DOT3 = "1.3.6.1.2.1.10.7.2.1"

class Snmp(unittest.TestCase):
    def test_crc_and_alignment_are_read_when_the_device_has_etherlike_mib(self):
        d = snmp_data(); d[f"{DOT3}.3.1"], d[f"{DOT3}.2.1"], d[f"{DOT3}.3.2"], d[f"{DOT3}.2.2"] = 7, 2, 0, 0
        drv = sw.SNMPDriver("t", "192.0.2.3", "public"); drv.snmp = FakeSNMP(d)
        ps = drv.snapshot()["ports"]
        self.assertEqual((ps[0]["crc_errors"], ps[0]["align_errors"], ps[1]["crc_errors"]), (7, 2, 0))

    def test_missing_etherlike_mib_leaves_none_and_is_not_asked_again(self):
        drv = sw.SNMPDriver("t", "192.0.2.3", "public"); fake = FakeSNMP(snmp_data()); drv.snmp = fake
        asked = []
        orig = fake.walk
        fake.walk = lambda base, max_rep=20: (asked.append(base), orig(base, max_rep))[1]
        ps = drv.snapshot()["ports"]
        self.assertTrue(all(p["crc_errors"] is None and p["align_errors"] is None for p in ps))
        n1 = sum(1 for b in asked if b.startswith(DOT3))
        drv.snapshot()
        self.assertEqual(sum(1 for b in asked if b.startswith(DOT3)), n1)       # not asked again

    def test_snmp_error_on_etherlike_is_contained(self):
        drv = sw.SNMPDriver("t", "192.0.2.3", "public"); fake = FakeSNMP(snmp_data()); drv.snmp = fake
        orig = fake.walk
        def walk(base, max_rep=20):
            if base.startswith(DOT3): raise sw.SNMPError("noSuchName")
            return orig(base, max_rep)
        fake.walk = walk
        self.assertIsNone(drv.snapshot()["ports"][0]["crc_errors"])

class Mgr(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.events, self.seen = [], {}
        def changed(k, st):
            old = self.seen.get(k); self.seen[k] = st
            return None if old is None or old == st else (old, st)
        self.m = sw.Manager(self.d, hooks={"event": lambda mod, lv, tx, k=None, **p: self.events.append((lv, k, p)), "changed": changed, "hosts": lambda: {}})
        self.m.reconcile = lambda: None; self.m._db_init()
        self.sid = self.m.save_switch({"name": "tp", "driver": "snmp", "host": "192.0.2.3", "community": "public"})["id"]
    def feed(self, ts, ports): self.m._ingest(self.sid, self.m._find(self.sid), mk_snap("tp", ts, ports), False)
    def kinds(self): return [e[1] for e in self.events]
    def port(self): return self.m.state()["switches"][0]["ports"][0]

    def test_crc_increase_gives_a_crc_notice_not_the_generic_one(self):
        t = 2_000_000.0
        def p(crc, rxe): q = mk_port(1, rxe=rxe); q["crc_errors"] = crc; q["align_errors"] = 0; return q
        self.feed(t, [p(10, 10)]); self.feed(t + 60, [p(10, 10)])
        self.assertEqual(self.kinds(), [])
        self.feed(t + 120, [p(15, 15)])
        self.assertEqual(self.kinds(), ["sw_crc"]); self.assertEqual(self.events[0][2]["d"], 5)
        s = self.m.state()["switches"][0]
        self.assertEqual((self.port()["crc"], self.port()["crc_1h"]), (15, 5))
        self.assertIn({"lv": "warn", "k": "crc", "p": 1, "d": 5}, s["alerts"])

    def test_errors_without_crc_support_still_use_the_generic_notice(self):
        t = 3_000_000.0
        self.feed(t, [mk_port(1, rxe=1)]); self.feed(t + 60, [mk_port(1, rxe=4)])
        self.assertEqual(self.kinds(), ["sw_err"]); self.assertIsNone(self.port()["crc"])

    def test_flapping_link_is_reported_once_and_flagged(self):
        t = 4_000_000.0
        self.feed(t, [mk_port(1)])
        for i in range(1, 5):
            self.feed(t + i * 30, [mk_port(1, up=(i % 2 == 0))])
        self.assertEqual(self.kinds().count("sw_flap"), 1)
        self.assertEqual(self.events[-1][2]["c"], 4)
        self.feed(t + 150, [mk_port(1, up=True)]); self.feed(t + 160, [mk_port(1, up=False)])
        self.assertEqual(self.kinds().count("sw_flap"), 1)                         # gap: no repeat for 30 min
        self.assertGreaterEqual(self.port()["flaps_1h"], 4)

    def test_slow_changes_are_not_flapping(self):
        t = 5_000_000.0
        self.feed(t, [mk_port(1)])
        for i in range(1, 6): self.feed(t + i * 400, [mk_port(1, up=(i % 2 == 0))])
        self.assertNotIn("sw_flap", self.kinds())

    def test_watch_alerts_on_link_change_for_any_port_and_persists(self):
        t = 6_000_000.0
        self.feed(t, [mk_port(1), mk_port(2)])
        self.feed(t + 60, [mk_port(1, up=False), mk_port(2, up=False)])
        self.assertEqual(self.kinds(), [])                                         # not watched: silent
        self.m.set_port_meta(self.sid, 2, "", False, True)
        self.assertTrue(self.m.state()["switches"][0]["ports"][1]["watch"])
        self.feed(t + 120, [mk_port(1, up=True), mk_port(2, up=True)])
        ev = [e for e in self.events if e[1] == "sw_link"]
        self.assertEqual([(e[2]["p"], e[2]["st"]) for e in ev], [(2, "up")])
        self.m.set_port_meta(self.sid, 2, "", False, False)                         # nothing left to keep → entry removed
        self.assertNotIn("2", self.m._find(self.sid).get("ports", {}))

if __name__ == "__main__":
    unittest.main()
