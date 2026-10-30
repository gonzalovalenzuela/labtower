"""WAN Monitor + router: prueba de los adaptadores contra routers simulados (Huawei, OpenWrt, DD-WRT, TP-Link), la clasificación LAN/WAN/internet, la configuración sin filtrar la clave y el endpoint de prueba."""
import base64, json, tempfile, threading, time, unittest
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from tests import support
from tests.support import ADMIN, READONLY

m = support.load("wan-monitor/server.py")
rtr = m.rtr

PASS = "Router-pass-1"

class FakeRouter:
    """Un router de mentira: `kind` elige el protocolo; `wan` es el estado que informa."""
    def __init__(self, kind, wan=True, password=PASS):
        self.kind, self.wan, self.password, self.log = kind, wan, password, []
        outer = self
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def send(self, code, body, ctype="text/html", headers=()):
                b = body.encode() if isinstance(body, str) else body
                self.send_response(code)
                for k, v in headers: self.send_header(k, v)
                self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            def body(self):
                n = int(self.headers.get("Content-Length", 0)); return self.rfile.read(n).decode() if n else ""
            def basic_ok(self):
                a = self.headers.get("Authorization", "")
                return a.startswith("Basic ") and base64.b64decode(a[6:]).decode() == "admin:" + outer.password
            def do_GET(self): outer.log.append(("GET", self.path)); getattr(outer, "get_" + outer.kind)(self)
            def do_POST(self):
                t = self.body(); outer.log.append(("POST", self.path)); getattr(outer, "post_" + outer.kind)(self, t)
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H); self.srv.daemon_threads = True
        self.port = self.srv.server_address[1]; threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.sessions, self.nonce = set(), {}
    def close(self): self.srv.shutdown(); self.srv.server_close()
    def cfg(self, **kw): return {"type": self.kind, "port": self.port, "https": False, "user": "admin", "password": PASS, "interface": "wan", **kw}

    # Huawei
    def get_huawei(self, h):
        if h.path == "/html/index.html":
            h.send(200, '<meta name="csrf_param" content="cp"><meta name="csrf_token" content="t0">', headers=[("Set-Cookie", "SessionID_R3=abc; Path=/")])
        elif h.path == "/api/ntwk/wandetect":
            if "SessionID_R3=abc" not in h.headers.get("Cookie", "") or "ok" not in self.sessions: return h.send(403, "{}")
            h.send(200, json.dumps({"Status": "Connected" if self.wan else "Disconnected", "ExternalIPAddress": "203.0.113.9" if self.wan else "", "Uptime": 4321}))
        else: h.send(404, "")
    def post_huawei(self, h, t):
        d = json.loads(t)["data"]
        if h.path == "/api/system/user_login_nonce":
            self.nonce = {"first": d["firstnonce"], "server": d["firstnonce"] + "ab" * 8}
            h.send(200, json.dumps({"salt": "a1b2c3d4e5f60718293a4b5c6d7e8f90", "iterations": 1000, "servernonce": self.nonce["server"], "csrf_param": "cp", "csrf_token": "t1"}))
        elif h.path == "/api/system/user_login_proof":
            want = rtr.huawei_proof(self.password, "a1b2c3d4e5f60718293a4b5c6d7e8f90", 1000, self.nonce["first"], self.nonce["server"])
            if d["clientproof"] != want: return h.send(200, json.dumps({"err": 1, "errorCategory": "user_pass_err"}))
            self.sessions.add("ok"); h.send(200, json.dumps({"csrf_param": "cp", "csrf_token": "t2"}))
        elif h.path == "/api/system/user_logout": self.sessions.discard("ok"); h.send(200, "{}")
        else: h.send(404, "")

    # OpenWrt
    def post_openwrt(self, h, t):
        p = json.loads(t)["params"]; sid, obj, meth, args = p
        def res(*r): h.send(200, json.dumps({"jsonrpc": "2.0", "id": 1, "result": list(r)}), "application/json")
        if obj == "session" and meth == "login":
            return res(0, {"ubus_rpc_session": "S" * 32}) if args["password"] == self.password else res(6)
        if sid != "S" * 32: return res(6)
        if obj == "session" and meth == "destroy": return res(0, {})
        if obj == "network.interface.wan" and meth == "status":
            return res(0, {"up": self.wan, "proto": "dhcp", "uptime": 77, "ipv4-address": [{"address": "203.0.113.5", "mask": 24}] if self.wan else []})
        res(4)
    def get_openwrt(self, h): h.send(404, "")

    # DD-WRT
    def get_ddwrt(self, h):
        if not h.basic_ok(): return h.send(401, "", headers=[("WWW-Authenticate", 'Basic realm="x"')])
        if h.path == "/Status_Router.live.asp":
            h.send(200, "{wan_status::%s}{wan_ipaddr::%s}{wan_uptime:: 1 day, 02:03:04}" % ("Connected" if self.wan else "Disconnected", "203.0.113.7" if self.wan else "0.0.0.0"))
        else: h.send(404, "")
    def post_ddwrt(self, h, t): h.send(404, "")

    # TP-Link clásico
    def get_tplink(self, h):
        if not h.basic_ok(): return h.send(401, "")
        if h.path == "/userRpm/StatusRpm.htm":
            ip = "203.0.113.11" if self.wan else "0.0.0.0"
            h.send(200, 'var wanPara = new Array(\n1, "00-11-22-33-44-55", "%s", 1, "255.255.255.0", "203.0.113.1", "8.8.8.8 , 1.1.1.1", 0);\n' % ip)
        else: h.send(404, "")
    def post_tplink(self, h, t): h.send(404, "")


class Adapters(unittest.TestCase):
    def run_check(self, kind, wan=True, **kw):
        fr = FakeRouter(kind, wan=wan)
        try: return rtr.check({**fr.cfg(), **kw}, "127.0.0.1"), fr
        finally: fr.close()

    def test_huawei_proof_matches_the_reference_vector(self):
        self.assertEqual(rtr.huawei_proof("MyPass123", "a1b2c3d4e5f60718293a4b5c6d7e8f90", 1000, "11" * 32, "22" * 32),
                         "785370629cf925e307faa66e7a1d0af16a099bc8f08ba8f191747994fb040a25")

    def test_each_type_reports_wan_up_and_down(self):
        for kind, ip in (("huawei", "203.0.113.9"), ("openwrt", "203.0.113.5"), ("ddwrt", "203.0.113.7"), ("tplink", "203.0.113.11")):
            with self.subTest(kind=kind, wan=True):
                r, _ = self.run_check(kind, True); self.assertTrue(r["ok"], r); self.assertIs(r["wan_up"], True); self.assertEqual(r["ip"], ip); self.assertEqual(r["error"], "")
            with self.subTest(kind=kind, wan=False):
                r, _ = self.run_check(kind, False); self.assertTrue(r["ok"], r); self.assertIs(r["wan_up"], False); self.assertIsNone(r["ip"])

    def test_extra_fields(self):
        r, _ = self.run_check("huawei"); self.assertEqual(r["uptime"], 4321)
        r, _ = self.run_check("ddwrt"); self.assertEqual(r["uptime"], 86400 + 2 * 3600 + 3 * 60 + 4)
        r, _ = self.run_check("openwrt"); self.assertEqual(r["uptime"], 77)

    def test_huawei_logs_out_and_only_reads(self):
        r, fr = self.run_check("huawei")
        self.assertIn(("POST", "/api/system/user_logout"), fr.log); self.assertEqual(fr.sessions, set())
    def test_openwrt_other_interface(self):
        r, _ = self.run_check("openwrt", interface="wan6"); self.assertFalse(r["ok"]); self.assertIn("ubus", r["error"])

    def test_wrong_password_is_reported_for_every_type(self):
        for kind in ("huawei", "openwrt", "ddwrt", "tplink"):
            with self.subTest(kind=kind):
                r, _ = self.run_check(kind, password="nope"); self.assertFalse(r["ok"]); self.assertIsNone(r["wan_up"]); self.assertIn("password", r["error"])

    def test_no_connection_never_raises(self):
        r = rtr.check({"type": "huawei", "port": 9, "https": False, "user": "a", "password": "b", "interface": "wan"}, "127.0.0.1")
        self.assertFalse(r["ok"]); self.assertIn("no connection", r["error"])
        self.assertIn("no router address", rtr.check({"type": "huawei", "port": 80, "user": "a", "password": "b"}, "")["error"])
        self.assertIn("unknown", rtr.check({"type": "zzz"}, "x")["error"])

    def test_not_a_huawei(self):
        fr = FakeRouter("ddwrt")
        try: r = rtr.check({**fr.cfg(), "type": "huawei"}, "127.0.0.1")
        finally: fr.close()
        self.assertFalse(r["ok"]); self.assertIn("Huawei", r["error"])

    def test_parsers(self):
        self.assertEqual(rtr.parse_ddwrt("{wan_status::Disconnected}{wan_ipaddr::0.0.0.0}")[:2], (False, None))
        self.assertEqual(rtr.parse_ddwrt("{wan_ipaddr::198.51.100.4}")[:2], (True, "198.51.100.4"))
        self.assertEqual(rtr.parse_ddwrt("nothing")[0], None)
        self.assertEqual(rtr.parse_tplink('var wanPara = new Array(1,"aa","198.51.100.8",1);'), (True, "198.51.100.8"))
        self.assertEqual(rtr.parse_tplink("<html>login</html>"), (None, None))

    def test_classify_scope(self):
        up, down, bad = {"ok": True, "wan_up": True}, {"ok": True, "wan_up": False}, {"ok": False, "wan_up": None}
        self.assertEqual(rtr.classify_scope(False, down), "lan"); self.assertEqual(rtr.classify_scope(False, None), "lan")
        self.assertEqual(rtr.classify_scope(True, down), "wan")
        for r in (up, bad, None): self.assertEqual(rtr.classify_scope(True, r), "internet")


class Config(unittest.TestCase):
    def test_defaults_off(self):
        c = m.validate({}); self.assertFalse(c["router"]["enabled"]); self.assertEqual(c["router"]["type"], "huawei")

    def test_password_kept_replaced_and_cleared(self):
        base = m.validate({"router": {"enabled": True, "type": "openwrt", "host": "192.168.1.1", "password": "one"}})
        self.assertEqual(base["router"]["password"], "one")
        kept = m.validate({"router": {"password": ""}}, base); self.assertEqual(kept["router"]["password"], "one")
        self.assertEqual(m.validate({"router": {"password": "two"}}, base)["router"]["password"], "two")
        off = m.validate({"router": {"enabled": False, "clear_password": True}}, base); self.assertEqual(off["router"]["password"], "")

    def test_rules(self):
        base = m.validate({})
        for bad in ({"type": "cisco"}, {"host": "-x"}, {"port": 0}, {"port": 70000}, {"every": 5}, {"every": 999},
                    {"interface": "a b"}, {"user": "a\nb"}, {"enabled": True}, {"password": "x" * 200}):
            with self.subTest(bad=bad), self.assertRaises(ValueError): m.validate({"router": bad}, base)
        ok = m.validate({"router": {"type": "tplink", "host": "192.168.0.1", "port": 8080, "https": True, "password": "p", "enabled": True, "every": 60}}, base)["router"]
        self.assertEqual((ok["type"], ok["port"], ok["https"], ok["every"]), ("tplink", 8080, True, 60))

    def test_public_config_hides_the_password(self):
        c = m.validate({"router": {"enabled": True, "password": "secret-xyz"}})
        p = m.public_config(c); self.assertNotIn("password", p["router"]); self.assertTrue(p["router"]["has_password"]); self.assertNotIn("secret-xyz", json.dumps(p))
        self.assertFalse(m.public_config(m.validate({}))["router"]["has_password"])


class Outages(unittest.TestCase):
    def setUp(self):
        self.s0 = (m.S.fails, m.S.down_since, m.S.scope, m.S.router, m.S.last); m.S.fails, m.S.down_since, m.S.scope, m.S.router = 0, None, None, None
        c = support.auth.metrics_conn(); c.execute("DELETE FROM wan_outages"); c.commit(); c.close()
    def tearDown(self): m.S.fails, m.S.down_since, m.S.scope, m.S.router, m.S.last = self.s0

    @staticmethod
    def rnd(ts, up, gw_ok=True): return {"ts": ts, "up": up, "gateway": {"ok": gw_ok, "host": "g"}}

    def test_scope_wan_when_router_says_its_link_is_down(self):
        t = int(time.time()); m.S.router = {"ok": True, "wan_up": False, "ts": t}
        m.track_outage(self.rnd(t, False), t); m.track_outage(self.rnd(t + 30, False), t)
        self.assertEqual(m.S.scope, "wan"); self.assertEqual(m.recent_outages()[0]["scope"], "wan")

    def test_scope_lan_wins_over_router_and_stale_reading_is_ignored(self):
        t = int(time.time()); m.S.router = {"ok": True, "wan_up": False, "ts": t}
        m.track_outage(self.rnd(t, False, False), t); m.track_outage(self.rnd(t + 30, False, False), t)
        self.assertEqual(m.S.scope, "lan")
        m.S.fails, m.S.down_since, m.S.scope = 0, None, None
        m.S.router = {"ok": True, "wan_up": False, "ts": t - 3600}
        m.track_outage(self.rnd(t, False), t); m.track_outage(self.rnd(t + 30, False), t); self.assertEqual(m.S.scope, "internet")

    def test_open_outage_is_refined_by_a_later_router_answer(self):
        t = int(time.time()); m.track_outage(self.rnd(t, False), t); m.track_outage(self.rnd(t + 30, False), t)
        self.assertEqual(m.S.scope, "internet"); m.S.last = self.rnd(t + 30, False)
        orig = m.rtr.check; m.rtr.check = lambda c, h: {"ok": True, "wan_up": False, "ip": None, "uptime": None, "detail": "", "error": "", "type": "huawei", "host": h, "ts": int(time.time())}
        try: m.router_round(m.validate({"router": {"enabled": True, "password": "p", "host": "192.168.1.1"}}))
        finally: m.rtr.check = orig
        self.assertEqual(m.S.scope, "wan"); self.assertEqual(m.recent_outages()[0]["scope"], "wan")


class Crosscheck(unittest.TestCase):
    def setUp(self):
        c = support.auth.metrics_conn(); c.execute("DELETE FROM wan_outages"); c.commit(); c.close()
    def test_counts_only_outages_inside_the_routers_connection_time(self):
        now = int(time.time()); r = {"ok": True, "wan_up": True, "uptime": 20 * 86400}
        self.assertEqual(m.router_crosscheck(r)["outages"], 0)
        c = support.auth.metrics_conn()
        c.execute("INSERT INTO wan_outages(start,end,scope) VALUES (?,?,?)", (now - 30 * 86400, now - 29 * 86400, "internet"))     # before the router connected
        c.execute("INSERT INTO wan_outages(start,end,scope) VALUES (?,?,?)", (now - 5 * 86400, now - 5 * 86400 + 600, "internet"))
        c.execute("INSERT INTO wan_outages(start,end,scope) VALUES (?,?,?)", (now - 2 * 86400, now - 2 * 86400 + 600, "wan")); c.commit(); c.close()
        x = m.router_crosscheck(r); self.assertEqual((x["outages"], x["wan_outages"], x["uptime"]), (2, 1, 20 * 86400))
        for bad in (None, {"ok": False}, {"ok": True, "wan_up": False, "uptime": 5}, {"ok": True, "wan_up": True, "uptime": None}): self.assertIsNone(m.router_crosscheck(bad))


class Endpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin, cls.ro = support.make_user("wradm", {**ADMIN}), support.make_user("wrro", READONLY)
        cls.srv = support.Server(m.H); cls.old = (m.DATA_FILE, m.rtr.check)
        m.DATA_FILE = Path(tempfile.mkdtemp(), "wan.json")
    @classmethod
    def tearDownClass(cls): m.DATA_FILE, m.rtr.check = cls.old; cls.srv.close()
    def setUp(self): m.S.router_test = 0

    def test_password_is_stored_but_never_returned(self):
        st, j = self.srv.call("POST", "/api/wan/config", {"router": {"enabled": True, "type": "huawei", "host": "192.168.1.1", "password": "top-secret-77"}}, self.admin)
        self.assertEqual(st, 200, j); self.assertNotIn("top-secret-77", json.dumps(j)); self.assertTrue(j["config"]["router"]["has_password"])
        self.assertEqual(m.load_config()["router"]["password"], "top-secret-77")
        for tok in (self.admin, self.ro):
            st, j = self.srv.call("GET", "/api/wan", token=tok); self.assertEqual(st, 200); self.assertNotIn("top-secret-77", json.dumps(j))
        st, j = self.srv.call("POST", "/api/wan/config", {"router": {"enabled": True, "type": "huawei"}}, self.admin); self.assertEqual(st, 200)
        self.assertEqual(m.load_config()["router"]["password"], "top-secret-77")

    def test_test_endpoint(self):
        seen = {}
        def fake(c, host): seen.update(c=dict(c), host=host); return {"ok": True, "wan_up": True, "ip": "203.0.113.1", "uptime": 5, "detail": "d", "error": "", "type": c["type"], "host": host, "ts": 1}
        m.rtr.check = fake
        st, j = self.srv.call("POST", "/api/wan/router/test", {"router": {"type": "openwrt", "host": "192.168.1.1", "password": "typed"}}, self.admin)
        self.assertEqual(st, 200, j); self.assertEqual(j["result"]["wan_up"], True); self.assertEqual(seen["c"]["password"], "typed"); self.assertNotIn("password", json.dumps(j))
        self.assertEqual(self.srv.call("POST", "/api/wan/router/test", {"router": {}}, self.admin)[0], 429)
        m.S.router_test = 0
        st, j = self.srv.call("POST", "/api/wan/router/test", {"router": {"type": "openwrt", "host": "192.168.1.1"}}, self.admin)
        self.assertEqual(st, 200); self.assertEqual(seen["c"]["password"], m.load_config()["router"]["password"])
        m.S.router_test = 0
        self.assertEqual(self.srv.call("POST", "/api/wan/router/test", {"router": {"type": "nope"}}, self.admin)[0], 400)
        m.S.router_test = 0
        self.assertEqual(self.srv.call("POST", "/api/wan/router/test", {"router": {}}, self.ro)[0], 403)
        self.assertEqual(self.srv.call("POST", "/api/wan/router/test", {"router": {}})[0], 401)


if __name__ == "__main__":
    unittest.main()
