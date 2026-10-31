"""2.1.4d: última conexión, nombres de Net Monitor en UPS, aviso de cambio de IP pública, lista de switches en la barra lateral, días de respaldo."""
import json, os, tempfile, time, unittest
from tests import support
from tests.support import auth, ADMIN, READONLY, NONE

class LastLogin(unittest.TestCase):
    def test_login_records_last_connection(self):
        support.make_user("lastlog", READONLY)
        self.assertGreater(auth.load_users()["lastlog"]["last_login"], time.time() - 5)
    def test_users_endpoint_returns_it(self):
        ap = support.load("auth/admin_panel.py"); srv = support.Server(ap.H)
        try:
            tok = support.make_user("lastadm", ADMIN)
            st, d = srv.call("GET", "/api/users", None, token=tok)
            row = next(u for u in d["users"] if u["username"] == "lastadm")
            self.assertEqual(st, 200); self.assertGreater(row["last_login"], time.time() - 5)
        finally:
            srv.close()

class UpsNames(unittest.TestCase):
    def test_names_from_net_monitor(self):
        m = support.load("nut-monitor/server.py")
        d = tempfile.mkdtemp(); f = os.path.join(d, "hosts.json")
        json.dump({"192.0.2.10": {"ip": "192.0.2.10", "alias": "pve1", "hostname": "x.lan"}, "192.0.2.11": {"hostname": "nas\x01main"},
                   "192.0.2.12": {"alias": "", "hostname": ""}, "192.0.2.13": "junk"}, open(f, "w"))
        old = (m.NET_HOSTS_FILE, list(m._names_cache)); m.NET_HOSTS_FILE = m.Path(f); m._names_cache[0] = 0
        try:
            self.assertEqual(m.net_names(), {"192.0.2.10": "pve1", "192.0.2.11": "nasmain"})
        finally:
            m.NET_HOSTS_FILE = old[0]; m._names_cache[0], m._names_cache[1] = old[1]
    def test_missing_file_gives_nothing(self):
        m = support.load("nut-monitor/server.py"); old = (m.NET_HOSTS_FILE, list(m._names_cache))
        m.NET_HOSTS_FILE = m.Path("/nonexistent/hosts.json"); m._names_cache[0] = 0
        try: self.assertEqual(m.net_names(), {})
        finally: m.NET_HOSTS_FILE = old[0]; m._names_cache[0], m._names_cache[1] = old[1]
    def test_names_only_for_users_who_may_see_net(self):
        m = support.load("nut-monitor/server.py"); srv = support.Server(m.H)
        old = list(m._names_cache); m._names_cache[0], m._names_cache[1] = time.time(), {"192.0.2.10": "pve1"}
        try:
            ok = support.make_user("nn_ok", {**NONE, "nut": "readonly", "net": "readonly"}); no = support.make_user("nn_no", {**NONE, "nut": "readonly"})
            self.assertEqual(srv.call("GET", "/api/servers", None, token=ok)[1]["names"], {"192.0.2.10": "pve1"})
            self.assertEqual(srv.call("GET", "/api/servers", None, token=no)[1]["names"], {})
        finally:
            m._names_cache[0], m._names_cache[1] = old; srv.close()

class PublicIp(unittest.TestCase):
    def test_change_keeps_previous_and_notice_lasts_a_day(self):
        w = support.load("wan-monitor/server.py")
        evs = []; rec = w.auth.record_event; w.auth.record_event = lambda *a, **k: evs.append((a, k))
        old = (w.fetch_public_ip, w.STATE_FILE, w.S.ip, w.S.ip_changed, w.S.ip_prev)
        w.STATE_FILE = w.Path(tempfile.mkdtemp()) / "state.json"
        try:
            w.S.ip, w.S.ip_changed, w.S.ip_prev = None, None, None
            w.fetch_public_ip = lambda u: "203.0.113.4"; w.check_ip({"ip_url": "x"})
            self.assertEqual(evs, [])                                        # first reading is not a change
            w.fetch_public_ip = lambda u: "203.0.113.9"; w.check_ip({"ip_url": "x"})
            self.assertEqual((w.S.ip, w.S.ip_prev), ("203.0.113.9", "203.0.113.4"))
            self.assertEqual(evs[0][0][1], "warn"); self.assertEqual(evs[0][1]["prev"], "203.0.113.4")
            self.assertEqual(json.load(open(w.STATE_FILE))["prev"], "203.0.113.4")
            snap = {"public_ip": "203.0.113.9", "ip_changed": int(time.time()) - 20 * 3600, "ip_prev": "203.0.113.4"}
            a = [x for x in w.compute_alerts(snap) if x["type"] == "ip_changed"]
            self.assertEqual((a[0]["value"], a[0]["prev"]), ("203.0.113.9", "203.0.113.4"))
            snap["ip_changed"] = int(time.time()) - 26 * 3600
            self.assertEqual([x for x in w.compute_alerts(snap) if x["type"] == "ip_changed"], [])
        finally:
            w.auth.record_event = rec; w.fetch_public_ip, w.STATE_FILE, w.S.ip, w.S.ip_changed, w.S.ip_prev = old

class Front(unittest.TestCase):
    def read(self, p): return open(p, encoding="utf-8").read()
    def test_switch_list_in_sidebar(self):
        h, j, c = self.read("net-monitor/static/index.html"), self.read("net-monitor/static/switches.js"), self.read("net-monitor/static/app.css")
        self.assertIn('id="sw-side-list"', h); self.assertEqual(h.count("sb-hosts"), 2)
        self.assertIn("body.view-sw .sb-hosts", c); self.assertIn("data-sw-only", j); self.assertIn("SW.only", j)
        self.assertEqual(j.count("swAllSwitches:"), 2); self.assertEqual(j.count("swSideTitle:"), 2)
    def test_wan_sidebar_ip(self):
        h, j = self.read("wan-monitor/static/index.html"), self.read("wan-monitor/static/app.js")
        self.assertIn('id="sb-ip"', h); self.assertIn("sb-ip-body", j); self.assertEqual(j.count('"ip_changed_from"'), 2)
    def test_proxmox_days_setting(self):
        a = self.read("proxmox-monitor/static/app.js")
        self.assertRegex(a, r"cspRegister\(\{[^}]*bkSetDays"); self.assertEqual(a.count("bkApply:"), 2)

if __name__ == "__main__":
    unittest.main()
