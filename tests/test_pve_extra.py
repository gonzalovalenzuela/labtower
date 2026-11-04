"""Proxmox Monitor: información adicional (tendencias, estados, bloqueos, capacidad, HA, replicación, tareas, nodos) /
extra information (trends, states, locks, capacity, HA, replication, tasks, nodes)."""
import unittest
from tests import support

m = support.load("proxmox-monitor/server.py")
ex = m.extra
NOW = 2_000_000_000
GIB = 1024 ** 3

def node(name, vms=(), cts=(), maxmem=64 * GIB, status="online", storage=()):
    return {"name": name, "status": status, "maxcpu": 16, "maxmem": maxmem, "vms": list(vms), "cts": list(cts), "storage": list(storage)}

def vm(vmid, st="running", mem=8 * GIB, cpus=4, lock="", tags="", name=None):
    return {"vmid": vmid, "name": name or f"vm{vmid}", "status": st, "maxmem": mem, "cpus": cpus, "lock": lock, "tags": tags}

class Trends(unittest.TestCase):
    def pts(self, days, per_day, start, rate):
        return [(NOW - int((days - i / per_day) * 86400), start + rate * (i / per_day)) for i in range(int(days * per_day))]

    def test_days_why_tells_missing_history_from_flat(self):
        self.assertEqual(ex.days_why(self.pts(1, 20, 100 * GIB, 0))[0], "history")
        w = ex.days_why(self.pts(5, 96, 100 * GIB, 0)); self.assertEqual(w[0], "flat"); self.assertGreaterEqual(w[1], 2)
        self.assertEqual(ex.days_why([]), ("history", 0))

    def test_days_to_full_and_guards(self):
        p = self.pts(5, 96, 100 * GIB, 2 * GIB)
        d = ex.days_to_full(p, 20 * GIB)
        self.assertTrue(9 <= d <= 11, d)
        self.assertIsNone(ex.days_to_full(p[:10], 20 * GIB))                       # little history
        self.assertIsNone(ex.days_to_full(self.pts(5, 96, 100 * GIB, 0), 20 * GIB))  # flat
        self.assertIsNone(ex.days_to_full(p, 10000 * GIB))                         # > 1 year
        self.assertIsNone(ex.days_to_full(p, float("nan")))

    def test_series_points_dedup_shared_and_ceph(self):
        sto = lambda n, sh: {"storage": n, "active": 1, "shared": sh, "total": 100, "used": 40}
        rows = ex.series_points([node("a", storage=[sto("nfs", 1), sto("local", 0)]), node("b", storage=[sto("nfs", 1), sto("local", 0)])],
                                {"pgmap": {"bytes_total": 1000, "bytes_used": 10}})
        self.assertEqual(sorted(rows), ["ceph", "s:a/local", "s:b/local", "s:nfs"])

    def test_days_alerts_levels(self):
        al = ex.days_alerts({"s:a": 2.0, "s:b": 10.0, "s:c": 30.0, "s:d": None, "ceph": 5.0})
        self.assertEqual({(a["type"], a["lv"]) for a in al}, {("sto_days", "crit"), ("sto_days", "warn"), ("ceph_days", "warn")})

class Guests(unittest.TestCase):
    def test_changes(self):
        a = ex.guest_state([node("n1", [vm(100), vm(101, "stopped"), vm(102, tags="labtower-ignore")])])
        self.assertNotIn(102, a)
        self.assertEqual(ex.guest_changes(None, a), [])                           # first pass only memorizes
        b = ex.guest_state([node("n1", [vm(100, "stopped"), vm(101)]), node("n2", [vm(103)])])
        ch = {c["vmid"]: c["what"] for c in ex.guest_changes(a, b)}
        self.assertEqual(ch, {100: "stop", 101: "start", 103: "new"})
        c = ex.guest_state([node("n2", [vm(100, "stopped")]), node("n1", [vm(101)])])
        self.assertEqual({x["vmid"]: x["what"] for x in ex.guest_changes(b, c)}, {100: "moved"})

    def test_paused_or_garbage_do_not_crash(self):
        cur = ex.guest_state([None, {"status": "online", "vms": [None, {"vmid": "x"}, {"vmid": 0}, vm(100, "paused")]}])
        self.assertEqual(list(cur), [100])
        self.assertEqual(ex.guest_changes({100: dict(cur[100], st="running")}, cur), [])

class Locks(unittest.TestCase):
    def test_stuck_after_limit_and_cleared(self):
        st = {}
        ns = [node("n1", [vm(100, lock="snapshot")])]
        self.assertEqual(ex.lock_alerts(st, ns, NOW), [])
        al = ex.lock_alerts(st, ns, NOW + 61 * 60)
        self.assertEqual((al[0]["type"], al[0]["vmid"], al[0]["mins"]), ("lock", 100, 61))
        self.assertEqual(ex.lock_alerts(st, [node("n1", [vm(100)])], NOW + 7200), [])
        self.assertEqual(st, {})

    def test_backup_lock_has_longer_limit_and_offline_node_keeps_state(self):
        st = {}
        ns = [node("n1", [vm(100, lock="backup")])]
        ex.lock_alerts(st, ns, NOW)
        self.assertEqual(ex.lock_alerts(st, ns, NOW + 2 * 3600), [])
        self.assertEqual(len(ex.lock_alerts(st, ns, NOW + 7 * 3600)), 1)
        ex.lock_alerts(st, [node("n1", status="offline")], NOW + 8 * 3600)
        self.assertIn(100, st)

class Capacity(unittest.TestCase):
    def test_overcommit_and_n1(self):
        ns = [node("a", [vm(1, mem=30 * GIB), vm(2, mem=30 * GIB)]), node("b", [vm(3, mem=30 * GIB)])]
        cap = ex.capacity(ns)
        self.assertEqual(cap["nodes"][0]["vcpu"], 8)
        self.assertFalse(cap["n1"]["ok"])                                          # 90 GiB > 64 * 0.9
        self.assertEqual([a["type"] for a in ex.capacity_alerts(cap)], ["n1"])
        ok = ex.capacity([node("a", [vm(1, mem=8 * GIB)]), node("b", [vm(2, mem=8 * GIB)])])
        self.assertTrue(ok["n1"]["ok"]); self.assertEqual(ex.capacity_alerts(ok), [])
        self.assertIsNone(ex.capacity([node("a")])["n1"])
        over = ex.capacity([node("a", [vm(1, mem=80 * GIB)])])
        self.assertEqual([a["type"] for a in ex.capacity_alerts(over)], ["overcommit"])

class Cluster(unittest.TestCase):
    def test_ha(self):
        s = ex.ha_summary([{"type": "quorum"}, {"type": "service", "sid": "vm:100", "state": "error", "node": "a", "status": "vm:100, node a, state error"},
                           {"type": "service", "sid": "vm:101", "state": "started", "node": "a", "status": "ok"},
                           {"type": "lrm", "node": "b", "status": "old timestamp - dead?"}, None, "x"])
        self.assertEqual([(b["type"], b["lv"]) for b in s["bad"]], [("ha", "crit"), ("ha_lrm", "warn")])
        self.assertEqual(len(s["services"]), 2)
        self.assertEqual(ex.ha_summary(None), {"services": [], "bad": []})

    def test_replication(self):
        s = ex.repl_summary({"a": [{"id": "100-0", "guest": 100, "target": "b", "fail_count": 3, "error": "no route"}, {"id": "101-0", "guest": 101, "target": "b"}, None]})
        self.assertEqual(len(s["jobs"]), 2); self.assertEqual(s["bad"][0]["vmid"], 100)

    def test_failed_tasks_skip_vzdump_noise_and_ok(self):
        t = lambda ty, st, u="U": {"upid": u + ty + st, "type": ty, "status": st, "starttime": NOW - 100, "node": "a", "id": "100"}
        got = ex.failed_tasks([t("qmstart", "start failed: no memory"), t("vzdump", "ERROR"), t("vncproxy", "ERROR"), t("qmstop", "OK"), t("srvstart", "WARNINGS: 1"),
                               t("qmigrate", ""), {"type": "qmstart", "status": "x", "starttime": NOW - 10 ** 7}, None], NOW)
        self.assertEqual([g["type"] for g in got], ["qmstart"])
        seen, new = ex.new_task_failures(None, got); self.assertEqual(new, [])
        seen, new = ex.new_task_failures(seen, got + [dict(got[0], upid="N")]); self.assertEqual([n["upid"] for n in new], ["N"])

    def test_ceph_io_and_pg_alert(self):
        io = ex.ceph_io({"pgmap": {"num_pgs": 100, "read_bytes_sec": 5, "write_bytes_sec": 7, "recovering_bytes_per_sec": 9,
                                   "pgs_by_state": [{"state_name": "active+clean", "count": 90}, {"state_name": "active+undersized+degraded", "count": 10}]}})
        self.assertEqual((io["clean"], io["states"][0]["n"]), (90, 10))
        self.assertEqual(ex.ceph_alerts(io)[0]["value"], 10)
        scrub = ex.ceph_io({"pgmap": {"num_pgs": 10, "pgs_by_state": [{"state_name": "active+clean", "count": 8}, {"state_name": "active+clean+scrubbing", "count": 2}]}})
        self.assertEqual(ex.ceph_alerts(scrub), [])
        self.assertIsNone(ex.ceph_io(None))

    def test_node_info_cert_drift_and_alerts(self):
        st = {"pveversion": "pve-manager/8.2.4/abc", "kversion": "Linux 6.8.4-2-pve", "loadavg": ["0.1", "0.2", "0.3"], "wait": 0.5,
              "swap": {"used": 3, "total": 4}, "cpuinfo": {"cpus": 8}}
        ni = ex.node_info(st, [{"filename": "pve-ssl.pem", "notafter": NOW + 5 * 86400}, {"filename": "pve-root-ca.pem", "notafter": NOW + 86400}], NOW)
        self.assertEqual((ni["version"], ni["cert_days"], ni["load"]), ("8.2.4", 5.0, [0.1, 0.2, 0.3]))
        self.assertEqual({a["type"] for a in ex.node_alerts({"a": ni})}, {"cert", "iowait", "swap"})
        self.assertEqual([a["lv"] for a in ex.node_alerts({"a": ni}) if a["type"] == "cert"], ["crit"])
        self.assertEqual(ex.version_drift({"a": {"version": "8.2.4"}, "b": {"version": "8.1.0"}}), ["8.1.0", "8.2.4"])
        self.assertEqual(ex.version_drift({"a": {"version": "8.2.4"}, "b": {"version": "8.2.4"}}), [])
        self.assertEqual(ex.node_info(None, None, NOW)["version"], "")

class Fake:
    def __init__(self): self.deny = set()
    def get(self, path):
        for d in self.deny:
            if path.startswith(d): raise m.PVEHTTPError(403, "Forbidden")
        if path.endswith("/status"): return {"data": {"pveversion": "pve-manager/8.2.4/x", "kversion": "Linux 6.8", "loadavg": ["1", "1", "1"], "wait": 0.01}}
        if path.endswith("/certificates/info"): return {"data": [{"filename": "pve-ssl.pem", "notafter": NOW + 86400 * 400}]}
        if path.endswith("/replication"): return {"data": []}
        if path == "/cluster/ha/status/current": return {"data": [{"type": "service", "sid": "vm:100", "state": "error", "node": "n1", "status": "e"}]}
        if path == "/cluster/tasks": return {"data": []}
        raise RuntimeError("unexpected " + path)

class Cache:
    def __init__(self, nodes): self.n = nodes
    def snap(self): return {"data": {"nodes": self.n, "ceph": None}}

class Round(unittest.TestCase):
    def setUp(self):
        self.ev = []
        self._rec = m.auth.record_event
        m.auth.record_event = lambda mod, lv, tx, k=None, **p: self.ev.append((lv, k, p))
        for d in (m._extra, m._live, m._guest_prev, m._lock_state, m._task_seen, m._al_on, m._ser_last): d.clear()
        self.cl = {"id": "c1", "name": "Pen"}
        self.real_now = m.time.time; m.time.time = lambda: NOW
        self._store = m._series_store; m._series_store = lambda *a: None
        self._days = m._series_days; m._series_days = lambda *a: ({}, {})
    def tearDown(self):
        m.auth.record_event = self._rec; m.time.time = self.real_now; m._series_store = self._store; m._series_days = self._days
    def kinds(self): return [e[1] for e in self.ev]

    def test_first_round_memorizes_then_new_alerts_make_events(self):
        ns = [node("n1", [vm(100)]), node("n2")]
        m._live_pass(self.cl, ns)
        self.assertEqual(self.ev, [])
        m._extra_round(self.cl, Fake(), Cache(ns))
        self.assertEqual(self.ev, [])                                              # HA error already existed: baseline
        self.assertEqual(m._extra["c1"]["ha"]["bad"][0]["sid"], "vm:100")
        self.assertTrue(any(a["type"] == "ha" for a in m.all_alerts("c1")))
        m._live_pass(self.cl, [node("n1", [vm(100, "stopped")]), node("n2")])
        self.assertEqual(self.kinds(), ["pve_guest_stop"])
        m._live_pass(self.cl, [node("n1", [vm(100, "stopped"), vm(101, mem=70 * GIB)]), node("n2")])
        self.assertIn("pve_al_n1", self.kinds())
        self.assertIn("pve_guest_new", self.kinds())

    def test_many_changes_make_one_summary(self):
        m._live_pass(self.cl, [node("n1", [vm(100 + i) for i in range(10)])])
        m._extra["c1"] = {"alerts": []}
        m._live_pass(self.cl, [node("n1", [vm(100 + i, "stopped") for i in range(10)])])
        self.assertEqual(self.kinds(), ["pve_guest_many"])

    def test_missing_permission_is_noted_not_fatal(self):
        f = Fake(); f.deny = {"/cluster/ha", "/nodes/n1/replication"}
        m._extra_round(self.cl, f, Cache([node("n1")]))
        r = m._extra["c1"]
        self.assertEqual((r["errors"]["ha"], r["errors"]["repl"]), ("perm", "perm"))
        self.assertEqual(r["ha"]["bad"], [])
        self.assertEqual(r["nodes"]["n1"]["version"], "8.2.4")

if __name__ == "__main__":
    unittest.main()
