"""Proxmox Monitor: reinicios, quórum de corosync, OSD de Ceph y SMART / reboots, corosync quorum, Ceph OSDs and SMART."""
import json, os, tempfile, unittest
from pathlib import Path
from tests import support
from tests.support import ADMIN, READONLY

m = support.load("proxmox-monitor/server.py")
diag = m.diag

NVME_TEXT = """smartctl 7.3
SMART/Health Information (NVMe Log 0x02)
Critical Warning:                   0x00
Temperature:                        41 Celsius
Available Spare:                    100%
Available Spare Threshold:          10%
Percentage Used:                    3%
Power Cycles:                       55
Power On Hours:                     8,123
Unsafe Shutdowns:                   17
Media and Data Integrity Errors:    0
Warning  Comp. Temperature Time:    0
"""

def nodes(**up):
    return [{"name": n, "status": "online", "uptime": u} for n, u in up.items()]

class Boots(unittest.TestCase):
    def test_first_sight_is_not_a_reboot(self):
        st = {}
        self.assertEqual(diag.observe_boots(st, "c", "C", nodes(a=1000), 10000), [])
        self.assertEqual(st["boots"]["c:a"], 9000)

    def test_jitter_is_not_a_reboot_and_boot_does_not_creep(self):
        st = {}
        diag.observe_boots(st, "c", "C", nodes(a=1000), 10000)
        for k in range(1, 50):
            self.assertEqual(diag.observe_boots(st, "c", "C", nodes(a=1000 + k * 5 + (k % 3)), 10000 + k * 5), [])
        self.assertLessEqual(abs(st["boots"]["c:a"] - 9000), 3)

    def test_reboot_detected_even_if_module_was_stopped(self):
        st = {}
        diag.observe_boots(st, "c", "C", nodes(a=500000), 1000000)
        new = diag.observe_boots(st, "c", "C", nodes(a=120), 1003600)          # an hour later, uptime 2 min
        self.assertEqual(len(new), 1)
        self.assertEqual(new[0]["boot"], 1003600 - 120)
        self.assertEqual(diag.observe_boots(st, "c", "C", nodes(a=125), 1003605), [])

    def test_offline_and_garbage_nodes_are_ignored(self):
        st = {}
        junk = [None, 5, {"name": "x"}, {"name": "b", "status": "online", "uptime": "abc"},
                {"name": "c", "status": "online", "uptime": True}, {"name": "d", "status": "offline", "uptime": 10},
                {"name": "e", "status": "online", "uptime": float("nan")}, {"name": "f", "status": "online", "uptime": [1]}]
        self.assertEqual(diag.observe_boots(st, "c", "C", junk, 10000), [])
        self.assertEqual(st["boots"], {})

    def test_log_is_capped(self):
        st = {}
        diag.observe_boots(st, "c", "C", nodes(a=10), 100000)
        for i in range(1, 400):
            diag.observe_boots(st, "c", "C", nodes(a=10), 100000 + i * 1000)
        self.assertEqual(len(st["reboots"]), diag.KEEP_REBOOTS)

class Waves(unittest.TestCase):
    def r(self, n, boot, cid="c"): return {"cid": cid, "c": "C", "n": n, "boot": boot, "seen": boot}
    def test_near_simultaneous_reboots_form_a_wave(self):
        w = diag.with_waves([self.r("a", 1000), self.r("b", 1100), self.r("c", 1200), self.r("a", 90000)])
        by = {(x["n"], x["boot"]): x["wave"] for x in w}
        self.assertEqual({by[("a", 1000)], by[("b", 1100)], by[("c", 1200)]}, {1})
        self.assertEqual(by[("a", 90000)], 0)
        self.assertEqual(w[0]["boot"], 90000)                                 # newest first

    def test_same_node_twice_is_not_a_wave(self):
        self.assertTrue(all(x["wave"] == 0 for x in diag.with_waves([self.r("a", 1000), self.r("a", 1200)])))

    def test_other_cluster_is_never_mixed(self):
        self.assertTrue(all(x["wave"] == 0 for x in diag.with_waves([self.r("a", 1000), self.r("b", 1010, "other")])))

    def test_garbage(self):
        self.assertEqual(diag.with_waves([None, 3, "x"]), [])

class Corosync(unittest.TestCase):
    def test_summary(self):
        s = diag.corosync_summary([
            {"type": "cluster", "name": "pen", "quorate": 1, "nodes": 3, "version": 7},
            {"type": "node", "name": "n2", "nodeid": 2, "online": 0, "ip": "10.0.0.2"},
            {"type": "node", "name": "n1", "nodeid": 1, "online": 1, "ip": "10.0.0.1", "local": 1}])
        self.assertTrue(s["quorate"]); self.assertEqual((s["online"], s["expected"]), (1, 3))
        self.assertEqual([x["name"] for x in s["members"]], ["n1", "n2"])

    def test_standalone_and_garbage(self):
        self.assertIsNone(diag.corosync_summary([{"type": "node", "name": "x", "online": 1}]))
        self.assertIsNone(diag.corosync_summary(None)); self.assertIsNone(diag.corosync_summary("x"))
        self.assertIsNotNone(diag.corosync_summary([{"type": "cluster", "quorate": "0", "nodes": "x"}, None]))

class Ceph(unittest.TestCase):
    def test_summary(self):
        s = diag.ceph_summary({"health": {"status": "HEALTH_WARN", "checks": {
            "OSD_DOWN": {"severity": "HEALTH_WARN", "summary": {"message": "1 osds down"}},
            "PG_DEGRADED": {"severity": "HEALTH_ERR", "summary": {"message": "degraded"}}}},
            "osdmap": {"num_osds": 6, "num_up_osds": 5, "num_in_osds": 6}})
        self.assertEqual((s["osds"], s["up"], s["in"], s["down"], s["out"]), (6, 5, 6, 1, 0))
        self.assertEqual(s["checks"][0]["code"], "PG_DEGRADED")                # errors first

    def test_nested_osdmap_and_garbage(self):
        s = diag.ceph_summary({"health": {"status": "HEALTH_OK"}, "osdmap": {"osdmap": {"num_osds": 3, "num_up_osds": 3, "num_in_osds": 3}}})
        self.assertEqual(s["down"], 0)
        for bad in (None, 5, [], {"error": "x"}, {"health": 3, "osdmap": "x"}, {"health": {"checks": {"A": 1, "B": {"summary": 5}}}}):
            diag.ceph_summary(bad)

class Smart(unittest.TestCase):
    def test_nvme_parse(self):
        p = diag.parse_nvme_text(NVME_TEXT)
        self.assertEqual((p["unsafe"], p["media_err"], p["used_pct"], p["spare"], p["spare_thr"], p["temp"], p["poh"], p["cycles"], p["crit"]),
                         (17, 0, 3, 100, 10, 41, 8123, 55, 0))
        self.assertEqual(diag.parse_nvme_text(None), {})

    def test_nvme_summary_ok_and_bad(self):
        row = {"devpath": "/dev/nvme0n1", "model": "Samsung", "serial": "S1", "type": "nvme", "size": 5, "wearout": 97, "health": "PASSED"}
        d = diag.summarize_disk(row, {"health": "PASSED", "type": "text", "text": NVME_TEXT})
        self.assertEqual(d["warns"], []); self.assertEqual(d["unsafe"], 17)
        bad = diag.summarize_disk(row, {"health": "FAILED", "text": NVME_TEXT.replace("Integrity Errors:    0", "Integrity Errors:    4").replace("Used:                    3%", "Used:                    95%")})
        self.assertEqual(set(bad["warns"]), {"health", "media", "wear"})

    def test_ata(self):
        row = {"devpath": "/dev/sda", "serial": "X", "type": "hdd", "wearout": "N/A", "health": "PASSED"}
        sm = {"health": "PASSED", "attributes": [{"id": 5, "raw": "8"}, {"id": 197, "raw": "0"}, {"id": 194, "raw": "35 (Min/Max 20/50)"}, {"id": 9, "raw": "100"}, None, {"id": "x"}]}
        d = diag.summarize_disk(row, sm)
        self.assertEqual((d["realloc"], d["pending"], d["temp"]), (8, 0, 35)); self.assertEqual(d["warns"], ["realloc"])
        self.assertIsNone(d["wearout"])

    def test_garbage(self):
        for a in (None, 3, "x", []): diag.summarize_disk(a, a)

    def test_unsafe_increase_is_tracked_by_serial(self):
        st = {}
        d = [{"dev": "/dev/nvme0n1", "model": "M", "serial": "S1", "unsafe": 10}]
        self.assertEqual(diag.unsafe_increases(st, "c", "n", d), [])
        self.assertEqual(diag.unsafe_increases(st, "c", "n", d), [])
        d[0]["unsafe"] = 11
        up = diag.unsafe_increases(st, "c", "n", d)
        self.assertEqual((up[0]["was"], up[0]["now"]), (10, 11))

class Fake:
    """Cliente de la API simulado / simulated API client."""
    def __init__(self, nvme_unsafe=10): self.unsafe = nvme_unsafe; self.calls = []
    def get(self, path):
        self.calls.append(path)
        if path == "/nodes/n1/disks/list":
            return {"data": [{"devpath": "/dev/nvme0n1", "model": "M", "serial": "S1", "type": "nvme", "size": 1, "wearout": 99, "health": "PASSED"},
                             {"devpath": "/dev/../etc/passwd; rm", "model": "evil"}, {"devpath": "/dev/sdb", "serial": "S2", "type": "hdd", "health": "PASSED"}]}
        if path.startswith("/nodes/n1/disks/smart?disk=/dev/nvme0n1"):
            return {"data": {"health": "PASSED", "text": NVME_TEXT.replace("Unsafe Shutdowns:                   17", f"Unsafe Shutdowns:                   {self.unsafe}")}}
        if path.startswith("/nodes/n1/disks/smart?disk=/dev/sdb"):
            raise RuntimeError("smartctl failed")
        raise RuntimeError("unexpected " + path)

class Integration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pvediag-")
        m.DIAG_FILE = Path(self.tmp) / "diag.json"; m._diag_state = None; m._diag_dump = ""; m._waves_sent.clear()
        self.ev = []
        self._rec, self._sc = m.auth.record_event, m.auth.state_changed
        m.auth.record_event = lambda mod, lv, tx, k=None, **p: self.ev.append((lv, k, tx, p))
        m.auth._state_seen.clear()
        self.cl = {"id": "cid1", "name": "Pen"}
    def tearDown(self):
        m.auth.record_event = self._rec

    def kinds(self): return [e[1] for e in self.ev]

    def test_reboot_event_wave_and_persistence(self):
        t = 1_000_000
        import time as _t
        real = _t.time
        try:
            m.time.time = lambda: t
            m._observe_reboots(self.cl, nodes(a=5000, b=5000, c=5000))
            self.assertEqual(self.ev, [])
            m.time.time = lambda: t + 3600
            m._observe_reboots(self.cl, nodes(a=60, b=5000 + 3600, c=5000 + 3600))
            self.assertEqual(self.kinds(), ["pve_reboot"])
            m.time.time = lambda: t + 3700
            m._observe_reboots(self.cl, nodes(a=160, b=100, c=5000 + 3700))
            self.assertEqual(self.kinds(), ["pve_reboot", "pve_reboot", "pve_reboot_multi"])
            self.assertEqual(self.ev[-1][3]["cnt"], 2)
            m.time.time = lambda: t + 3800
            m._observe_reboots(self.cl, nodes(a=260, b=200, c=5000 + 3800))
            self.assertEqual(len(self.ev), 3)                                  # nothing repeated
        finally:
            m.time.time = real
        saved = json.loads(m.DIAG_FILE.read_text())
        self.assertEqual(len(saved["reboots"]), 2)
        self.assertEqual(oct(m.DIAG_FILE.stat().st_mode & 0o777), "0o600")
        m._diag_state = None                                                   # restart: state comes back from disk
        self.assertEqual(len(m._diag_load()["reboots"]), 2)

    def test_quorum_and_osd_events(self):
        ok = {"quorate": True}; lost = {"quorate": False}
        cp = lambda down: {"down": down, "up": 6 - down, "osds": 6}
        m._diag_events(self.cl, ok, cp(0)); self.assertEqual(self.ev, [])
        m._diag_events(self.cl, lost, cp(1))
        m._diag_events(self.cl, lost, cp(1))
        m._diag_events(self.cl, ok, cp(0))
        self.assertEqual(self.kinds(), ["pve_quorum_lost", "pve_osd_down", "pve_quorum_ok", "pve_osd_ok"])

    def test_smart_round_unsafe_and_path_safety(self):
        class C:
            def snap(s): return {"data": {"nodes": [{"name": "n1", "status": "online"}, {"name": "n2", "status": "offline"}]}}
        f = Fake(10)
        m._smart_round(self.cl, f, C())
        r = m._smart["cid1"]["nodes"]
        self.assertEqual(list(r), ["n1"]); self.assertEqual([d["dev"] for d in r["n1"]["disks"]], ["/dev/nvme0n1", "/dev/sdb"])
        self.assertFalse(any("passwd" in c for c in f.calls))
        self.assertEqual(self.ev, [])
        f.unsafe = 12
        m._smart_round(self.cl, f, C())
        self.assertEqual(self.kinds(), ["pve_unsafe"]); self.assertEqual((self.ev[0][3]["a"], self.ev[0][3]["b"]), (10, 12))

    def test_smart_round_node_error_is_contained(self):
        class C:
            def snap(s): return {"data": {"nodes": [{"name": "n9", "status": "online"}]}}
        m._smart_round(self.cl, Fake(), C())
        self.assertIn("unexpected", m._smart["cid1"]["nodes"]["n9"]["error"])

class Api(unittest.TestCase):
    def test_diag_endpoint(self):
        tok, ro = support.make_user("pvd_admin", ADMIN), support.make_user("pvd_none", {"pve": "none"})
        srv = support.Server(m.H)
        try:
            orig = m.load_clusters
            m.load_clusters = lambda: [{"id": "cX", "name": "X", "host": "h", "user": "u", "token_name": "t", "token_value": "v"}]
            m._diag_state = {"boots": {}, "reboots": [{"cid": "cX", "c": "X", "n": "a", "boot": 5, "seen": 6},
                                                      {"cid": "other", "c": "O", "n": "z", "boot": 5, "seen": 6}], "unsafe": {}}
            self.assertEqual(srv.call("GET", "/api/diag?id=cX")[0], 401)
            self.assertEqual(srv.call("GET", "/api/diag?id=cX", token=ro)[0], 401)
            code, j = srv.call("GET", "/api/diag?id=cX", token=tok)
            self.assertEqual(code, 200); self.assertEqual([r["n"] for r in j["reboots"]], ["a"])
            self.assertEqual(srv.call("GET", "/api/diag?id=nope", token=tok)[0], 404)
            self.assertEqual(srv.call("GET", "/api/diag", token=tok)[0], 404)
        finally:
            m.load_clusters = orig; srv.close(); m._diag_state = None

if __name__ == "__main__":
    unittest.main()
