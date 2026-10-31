"""Proxmox Monitor: último respaldo por VM/CT, antigüedad, tareas vzdump fallidas y ajustes / last backup per guest, age, failed vzdump tasks and settings."""
import json, tempfile, unittest
from pathlib import Path
from tests import support
from tests.support import ADMIN, READONLY

m = support.load("proxmox-monitor/server.py")
bk = m.backups
NOW = 2_000_000_000

def item(vmid, age_h, size=100, ver=None, volid=None):
    d = {"vmid": vmid, "ctime": NOW - int(age_h * 3600), "size": size, "volid": volid or f"s:backup/vzdump-{vmid}"}
    if ver: d["verification"] = {"state": ver}
    return d

class Pure(unittest.TestCase):
    def test_newest_wins_and_counts(self):
        n = bk.newest_by_vmid([{"storage": "pbs", "node": "a", "items": [item(100, 30), item(100, 5, ver="ok"), item("101", 70)]},
                               {"storage": "nfs", "node": "b", "items": [item(100, 50)]}])
        self.assertEqual((n[100]["count"], n[100]["ctime"], n[100]["storage"], n[100]["verify"]), (3, NOW - 5 * 3600, "pbs", "ok"))
        self.assertEqual(n[101]["count"], 1)

    def test_garbage_is_ignored(self):
        junk = [None, 5, {"items": None}, {"items": [None, 3, {"vmid": 0, "ctime": 5}, {"vmid": "x", "ctime": 5}, {"vmid": 100, "ctime": -1},
                                                      {"vmid": True, "ctime": 9}, {"vmid": 100, "ctime": float("nan")}]}]
        self.assertEqual(bk.newest_by_vmid(junk), {})
        self.assertEqual(bk.newest_by_vmid("x"), {})

    def test_evaluate_states_and_order(self):
        guests = [{"vmid": 100, "name": "web", "type": "qemu", "node": "a"}, {"vmid": 101, "name": "db", "type": "lxc", "node": "b"},
                  {"vmid": 102, "name": "test", "type": "qemu", "node": "a"}, {"vmid": 103, "name": "tpl", "type": "qemu", "template": 1},
                  {"vmid": 104, "name": "old", "type": "qemu"}, None, {"vmid": 0}]
        newest = bk.newest_by_vmid([{"storage": "s", "node": "a", "items": [item(100, 3), item(101, 40), item(104, 100)]}])
        rows = bk.evaluate(guests, newest, 36, [102], NOW)
        self.assertEqual([(r["vmid"], r["status"]) for r in rows], [(101, "old"), (104, "old"), (100, "ok"), (102, "ignored")])
        self.assertEqual(rows[0]["type"], "ct")
        rows = bk.evaluate(guests, {}, 36, [], NOW)
        self.assertEqual({r["status"] for r in rows}, {"never"})                       # templates are never listed
        self.assertNotIn(103, [r["vmid"] for r in rows])

    def test_age_limit_is_respected(self):
        g = [{"vmid": 100, "name": "w", "type": "qemu"}]
        n = bk.newest_by_vmid([{"storage": "s", "node": "a", "items": [item(100, 40)]}])
        self.assertEqual(bk.evaluate(g, n, 36, [], NOW)[0]["status"], "old")
        self.assertEqual(bk.evaluate(g, n, 48, [], NOW)[0]["status"], "ok")
        self.assertEqual(bk.evaluate(g, n, "junk", None, NOW)[0]["status"], "ok")       # falls back to 7 days

    def test_tasks(self):
        tasks = [{"type": "vzdump", "upid": "U1", "node": "a", "starttime": NOW - 100, "endtime": NOW - 50, "status": "OK", "id": "100"},
                 {"type": "vzdump", "upid": "U2", "node": "a", "starttime": NOW - 200, "endtime": NOW - 150, "status": "job errors"},
                 {"type": "vzdump", "upid": "U3", "node": "b", "starttime": NOW - 10},
                 {"type": "vzdump", "upid": "U4", "node": "b", "starttime": NOW - 300, "endtime": NOW - 250, "status": "WARNINGS: 1"},
                 {"type": "vzdump", "upid": "U5", "starttime": NOW - 10 * 86400, "status": "OK", "endtime": 1},
                 {"type": "qmstart", "upid": "U6", "starttime": NOW - 10, "status": "OK"}, None, {"type": "vzdump", "starttime": "x"}]
        t = bk.parse_tasks(tasks, NOW)
        self.assertEqual([x["upid"] for x in t], ["U3", "U1", "U2", "U4"])
        self.assertEqual([x["ok"] for x in t], [None, True, False, True])
        self.assertEqual(t[1]["vmid"], 100); self.assertIsNone(t[2]["vmid"])

    def test_failures_baseline_then_new(self):
        t = lambda u, ok: {"upid": u, "ok": ok}
        seen, new = bk.new_failures(None, [t("A", False), t("B", True)])
        self.assertEqual(new, [])
        seen, new = bk.new_failures(seen, [t("A", False), t("C", False)])
        self.assertEqual([x["upid"] for x in new], ["C"])
        seen, new = bk.new_failures(seen, [t("A", False), t("C", False)])
        self.assertEqual(new, [])

    def test_config_validation(self):
        self.assertEqual(bk.clean_config({"max_age_h": 24, "ignore": [105, 101, 105]}), {"max_age_h": 24, "ignore": [101, 105]})
        self.assertEqual(bk.clean_config({}), {"max_age_h": 168, "ignore": []})
        for bad in (None, [], {"max_age_h": 0}, {"max_age_h": 9000}, {"max_age_h": True}, {"max_age_h": "9"}, {"max_age_h": float("nan")},
                    {"ignore": "x"}, {"ignore": [True]}, {"ignore": [5]}, {"ignore": ["101"]}, {"ignore": list(range(100, 400))}):
            with self.assertRaises(ValueError, msg=bad): bk.clean_config(bad)

class Fake:
    def __init__(self, fail_storage=False): self.fail = fail_storage; self.calls = []; self.tasks = []; self.age = {100: 3, 101: 50}
    def get(self, path):
        self.calls.append(path)
        if path.startswith("/nodes/n1/storage/pbs/content"):
            if self.fail: raise RuntimeError("storage offline")
            return {"data": [item(v, a) for v, a in self.age.items()]}
        if path == "/cluster/tasks": return {"data": self.tasks}
        raise RuntimeError("unexpected " + path)

class Cache:
    def snap(self):
        n1 = {"name": "n1", "status": "online", "vms": [{"vmid": 100, "name": "web"}, {"vmid": 101, "name": "db"}, {"vmid": 102, "name": "dev"}], "cts": [],
              "storage": [{"storage": "pbs", "content": "backup", "active": 1, "shared": 1}, {"storage": "local-lvm", "content": "images", "active": 1}]}
        n2 = {"name": "n2", "status": "online", "vms": [], "cts": [], "storage": [{"storage": "pbs", "content": "backup", "active": 1, "shared": 1}]}
        return {"data": {"nodes": [n1, n2]}}

class Round(unittest.TestCase):
    def setUp(self):
        self.ev = []
        self._rec = m.auth.record_event
        m.auth.record_event = lambda mod, lv, tx, k=None, **p: self.ev.append((lv, k, p))
        m.auth._state_seen.clear(); m._bk_seen.clear(); m._backups.clear()
        self.cl = {"id": "c1", "name": "Pen", "backup": {"max_age_h": 24, "ignore": []}}
        self.real_now = m.time.time
        m.time.time = lambda: NOW
    def tearDown(self):
        m.auth.record_event = self._rec; m.time.time = self.real_now
    def kinds(self): return [e[1] for e in self.ev]

    def test_round_reads_shared_storage_once_and_reports(self):
        f = Fake()
        m._backup_round(self.cl, f, Cache())
        self.assertEqual(sum(1 for c in f.calls if "/storage/" in c), 1)                # shared: asked once; local-lvm has no backup
        b = m._backups["c1"]
        self.assertEqual({r["vmid"]: r["status"] for r in b["rows"]}, {100: "ok", 101: "old", 102: "never"})
        self.assertEqual(self.ev, [])                                                  # first reading: baseline only

    def test_transitions_make_events(self):
        f = Fake(); m._backup_round(self.cl, f, Cache())
        f.age = {100: 40, 101: 2}
        m._backup_round(self.cl, f, Cache())
        self.assertEqual(sorted(self.kinds()), ["pve_backup_ok", "pve_backup_old"])
        old = next(e for e in self.ev if e[1] == "pve_backup_old"); self.assertEqual((old[2]["v"], old[2]["h"]), (100, 40))
        m._backup_round(self.cl, f, Cache())
        self.assertEqual(len(self.ev), 2)                                              # nothing repeated

    def test_old_default_moves_to_seven_days(self):
        self.assertEqual(bk.migrate_config({"max_age_h": 36, "ignore": [101]}), {"max_age_h": 168, "ignore": [101]})
        self.assertEqual(bk.migrate_config({"max_age_h": 48, "ignore": []})["max_age_h"], 48)
        self.cl["backup"]["max_age_h"] = 36
        m._backup_round(self.cl, Fake(), Cache())
        self.assertEqual(m._backups["c1"]["max_age_h"], 168)
        self.assertEqual({r["vmid"]: r["status"] for r in m._backups["c1"]["rows"]}, {100: "ok", 101: "ok", 102: "never"})   # 50 h is fine under 7 days

    def test_ignored_guest_never_alerts(self):
        f = Fake(); self.cl["backup"]["ignore"] = [102]
        m._backup_round(self.cl, f, Cache())
        self.assertEqual(next(r for r in m._backups["c1"]["rows"] if r["vmid"] == 102)["status"], "ignored")

    def test_unreadable_storage_is_not_reported_as_missing(self):
        f = Fake(); m._backup_round(self.cl, f, Cache()); f.fail = True
        m._backup_round(self.cl, f, Cache())
        b = m._backups["c1"]
        self.assertTrue(all(r["status"] in ("unknown", "ignored") for r in b["rows"]))
        self.assertIn("offline", b["storages"][0]["error"]); self.assertEqual(self.ev, [])

    def test_failed_task_event_once(self):
        f = Fake(); m._backup_round(self.cl, f, Cache())
        f.tasks = [{"type": "vzdump", "upid": "UX", "node": "n1", "starttime": NOW - 100, "endtime": NOW - 50, "status": "job errors", "id": "100"}]
        m._backup_round(self.cl, f, Cache()); m._backup_round(self.cl, f, Cache())
        ev = [e for e in self.ev if e[1] == "pve_backup_fail"]
        self.assertEqual(len(ev), 1); self.assertEqual(ev[0][0], "crit"); self.assertEqual(ev[0][2]["w"], "VM 100")

class Api(unittest.TestCase):
    def test_config_endpoint_and_diag_payload(self):
        admin, ro = support.make_user("bk_admin", ADMIN), support.make_user("bk_ro", READONLY)
        srv = support.Server(m.H)
        tmp = Path(tempfile.mkdtemp()) / "clusters.json"
        orig_file, orig_load, orig_save = m.DATA_FILE, m.load_clusters, m.save_clusters
        store = [{"id": "c1", "name": "X", "host": "h", "user": "u", "token_name": "t", "token_value": "v"}]
        m.load_clusters = lambda: [dict(c) for c in store]
        m.save_clusters = lambda cl: (store.clear(), store.extend(cl))
        try:
            url = "/api/clusters/c1/backup"
            self.assertIn(srv.call("POST", url, {"max_age_h": 24})[0], (401, 403))
            self.assertEqual(srv.call("POST", url, {"max_age_h": 24}, token=ro)[0], 403)
            self.assertEqual(srv.call("POST", url, {"max_age_h": 0}, token=admin)[0], 400)
            code, j = srv.call("POST", url, {"max_age_h": 24, "ignore": [105, 101]}, token=admin)
            self.assertEqual((code, j["ignore"]), (200, [101, 105]))
            self.assertEqual(store[0]["backup"], {"max_age_h": 24, "ignore": [101, 105]})
            self.assertEqual(srv.call("POST", "/api/clusters/nope/backup", {}, token=admin)[0], 404)
            m._backups["c1"] = {"ts": 1, "rows": [], "tasks": [], "storages": [], "max_age_h": 24, "ignore": []}
            m._diag_state = {"boots": {}, "reboots": [], "unsafe": {}}
            code, j = srv.call("GET", "/api/diag?id=c1", token=ro)
            self.assertEqual(code, 200); self.assertEqual(j["backups"]["max_age_h"], 24)
            # saving new settings updates what the page reads back right away (no waiting for the next storage read)
            rows = [{"vmid": 101, "last": None, "age": None, "status": "never"}, {"vmid": 102, "last": 1, "age": 100 * 3600, "status": "old"},
                    {"vmid": 103, "last": 1, "age": 3600, "status": "ok"}, {"vmid": 104, "last": None, "age": None, "status": "unknown"}]
            m._backups["c1"] = {"ts": 1, "rows": rows, "tasks": [], "storages": [], "max_age_h": 24, "ignore": []}
            self.assertEqual(srv.call("POST", url, {"max_age_h": 24, "ignore": [101, 102, 104]}, token=admin)[0], 200)
            got = {r["vmid"]: r["status"] for r in srv.call("GET", "/api/diag?id=c1", token=ro)[1]["backups"]["rows"]}
            self.assertEqual(got, {101: "ignored", 102: "ignored", 103: "ok", 104: "unknown"})
            srv.call("POST", url, {"max_age_h": 24, "ignore": [103]}, token=admin)
            j = srv.call("GET", "/api/diag?id=c1", token=ro)[1]["backups"]
            self.assertEqual({r["vmid"]: r["status"] for r in j["rows"]}, {101: "never", 102: "old", 103: "ignored", 104: "unknown"})
            self.assertEqual(j["ignore"], [103])
        finally:
            m.load_clusters, m.save_clusters = orig_load, orig_save; m._backups.clear(); m._diag_state = None; srv.close()

if __name__ == "__main__":
    unittest.main()
