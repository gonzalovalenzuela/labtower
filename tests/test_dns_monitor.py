"""DNS Monitor: Pi-hole v6 y v5 y AdGuard Home contra servidores simulados, validación, secretos, permisos, pausa del bloqueo y alertas."""
import json, os, stat, threading, time, unittest
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from tests import support
from tests.support import ADMIN, READONLY, NONE

m = support.load("dns-monitor/server.py")

NOW = int(time.time())

# ── Servidores simulados: responden con el formato documentado de cada API y anotan las peticiones ──
class Fake:
    """kind: ph6 | ph5 | agh. password/token se comprueba; el estado del bloqueo se puede cambiar con las rutas de pausa."""
    def __init__(self, kind, password="secret", user="admin"):
        self.kind, self.password, self.user = kind, password, user
        self.log, self.blocking, self.timer, self.sessions = [], True, None, set()
        fake = self
        class Hd(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def _send(self, code, obj):
                b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            def _body(self):
                n = int(self.headers.get("Content-Length", 0)); return json.loads(self.rfile.read(n)) if n else {}
            def do_GET(self): fake.handle(self, "GET")
            def do_POST(self): fake.handle(self, "POST")
            def do_DELETE(self): fake.handle(self, "DELETE")
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Hd); self.srv.daemon_threads = True
        self.port = self.srv.server_address[1]; self.url = f"http://127.0.0.1:{self.port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
    def close(self): self.srv.shutdown(); self.srv.server_close()

    def handle(self, h, method):
        u = urlparse(h.path); q = {k: v[0] for k, v in parse_qs(u.query, keep_blank_values=True).items()}
        body = h._body() if method == "POST" else {}
        self.log.append((method, u.path, q, body, dict(h.headers)))
        getattr(self, "_" + self.kind)(h, method, u.path, q, body)

    # Pi-hole v6
    def _ph6(self, h, method, path, q, body):
        if path == "/api/auth":
            if method == "DELETE": self.sessions.discard(h.headers.get("X-FTL-SID")); return h._send(204, {})
            if body.get("password") != self.password: return h._send(401, {"session": {"valid": False}, "error": {"key": "unauthorized"}})
            sid = "sid%d" % len(self.sessions); self.sessions.add(sid)
            return h._send(200, {"session": {"valid": True, "sid": sid, "validity": 300}})
        if h.headers.get("X-FTL-SID") not in self.sessions: return h._send(401, {"error": {"key": "unauthorized"}})
        if path == "/api/stats/summary":
            return h._send(200, {"queries": {"total": 1000, "blocked": 250, "percent_blocked": 25.0, "cached": 400, "forwarded": 350, "unique_domains": 120},
                                 "clients": {"active": 7, "total": 9}, "gravity": {"domains_being_blocked": 99000, "last_update": NOW - 3600}})
        if path == "/api/dns/blocking":
            if method == "POST":
                self.blocking = bool(body["blocking"]); self.timer = body.get("timer"); return h._send(200, {"blocking": "enabled" if self.blocking else "disabled", "timer": self.timer})
            return h._send(200, {"blocking": "enabled" if self.blocking else "disabled", "timer": self.timer})
        if path == "/api/stats/top_domains":
            if q.get("blocked") == "true": return h._send(200, {"domains": [{"domain": "ads.example", "count": 90}, {"domain": "track.example", "count": 40}]})
            return h._send(200, {"domains": [{"domain": "good.example", "count": 300}]})
        if path == "/api/stats/top_clients": return h._send(200, {"clients": [{"ip": "192.0.2.10", "name": "pc", "count": 500}, {"ip": "192.0.2.11", "name": "", "count": 100}]})
        if path == "/api/stats/upstreams":
            return h._send(200, {"upstreams": [{"ip": "1.1.1.1", "name": "one.one.one.one", "port": 53, "count": 300, "statistics": {"response": 0.020, "variance": 0}},
                                               {"ip": "9.9.9.9", "name": None, "port": 53, "count": 100, "statistics": {"response": 0.060, "variance": 0}}]})
        if path == "/api/history":
            return h._send(200, {"history": [{"timestamp": NOW - 600 * i, "total": 10, "cached": 4, "blocked": 2, "forwarded": 4} for i in range(1, 30)]})
        if path == "/api/info/version": return h._send(200, {"version": {"core": {"local": {"version": "v6.1"}}}})
        h._send(404, {"error": "nope"})

    # Pi-hole v5 (no tiene /api/auth)
    def _ph5(self, h, method, path, q, body):
        if path != "/admin/api.php": return h._send(404, {})
        if q.get("auth") != self.password: return h._send(200, [])           # v5 answers 200 with [] for a wrong token
        if "summaryRaw" in q:
            return h._send(200, {"domains_being_blocked": 80000, "dns_queries_today": 500, "ads_blocked_today": 100, "ads_percentage_today": 20.0, "unique_domains": 50,
                                 "queries_forwarded": 300, "queries_cached": 100, "unique_clients": 4, "status": "enabled" if self.blocking else "disabled",
                                 "gravity_last_updated": {"absolute": NOW - 7200}})
        if "topItems" in q: return h._send(200, {"top_queries": {"a.example": 50, "b.example": 70}, "top_ads": {"ad.example": 30}})
        if "getQuerySources" in q: return h._send(200, {"top_sources": {"pc|192.0.2.10": 200, "192.0.2.12|192.0.2.12": 20}})
        if "overTimeData10mins" in q:
            return h._send(200, {"domains_over_time": {str(NOW - 600 * i): 10 for i in range(1, 20)}, "ads_over_time": {str(NOW - 600 * i): 2 for i in range(1, 20)}})
        if "disable" in q: self.blocking = False; return h._send(200, {"status": "disabled"})
        if "enable" in q: self.blocking = True; return h._send(200, {"status": "enabled"})
        h._send(200, {})

    # AdGuard Home
    def _agh(self, h, method, path, q, body):
        import base64
        if h.headers.get("Authorization") != "Basic " + base64.b64encode(f"{self.user}:{self.password}".encode()).decode(): return h._send(401, {})
        if path == "/control/status":
            return h._send(200, {"running": True, "version": "v0.107.50", "protection_enabled": self.blocking, "protection_disabled_duration": 0 if self.blocking else 120000})
        if path == "/control/stats":
            return h._send(200, {"time_units": "hours", "num_dns_queries": 2000, "num_blocked_filtering": 300, "num_replaced_safebrowsing": 10, "num_replaced_parental": 0,
                                 "avg_processing_time": 0.0123, "dns_queries": [10] * 24, "blocked_filtering": [2] * 24,
                                 "top_queried_domains": [{"a.example": 90}, {"b.example": 10}], "top_blocked_domains": [{"ad.example": 50}],
                                 "top_clients": [{"192.0.2.10": 1500}], "top_upstreams_responses": [{"1.1.1.1:53": 900}], "top_upstreams_avg_time": [{"1.1.1.1:53": 0.015}]})
        if path == "/control/filtering/status": return h._send(200, {"enabled": True, "filters": [{"enabled": True, "rules_count": 5000}, {"enabled": False, "rules_count": 9999}]})
        if path == "/control/protection" and method == "POST":
            self.blocking = bool(body["enabled"]); return h._send(200, {})
        h._send(404, {})


class Validate(unittest.TestCase):
    def test_url_is_reduced_and_checked(self):
        self.assertEqual(m.norm_url("192.0.2.5"), "http://192.0.2.5")
        self.assertEqual(m.norm_url("https://pihole.lan:8443/admin/"), "https://pihole.lan:8443")
        self.assertEqual(m.norm_url("http://[2001:db8::1]:80"), "http://[2001:db8::1]:80")
        for bad in ("ftp://x", "http://u:p@host", "http://", "http://-x", "http://host:99999", "http://ho st"):
            with self.subTest(bad=bad), self.assertRaises(ValueError): m.norm_url(bad)

    def test_validate_rules_and_secret_kept(self):
        ok = m.validate({"name": "Pi", "url": "192.0.2.5", "type": "pihole", "password": "pw"})
        self.assertEqual((ok["url"], ok["verify_tls"], ok["timeout"]), ("http://192.0.2.5", True, 8))
        kept = m.validate({"name": "Pi2", "password": ""}, ok); self.assertEqual((kept["name"], kept["password"]), ("Pi2", "pw"))
        for bad in ({"name": "", "url": "h"}, {"name": "a", "url": "h", "type": "bind"}, {"name": "a", "url": "h", "timeout": 99},
                    {"name": "a", "url": "h", "type": "adguard"}, {"name": "a\nb", "url": "h"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError): m.validate(bad)
        self.assertEqual(m.validate({"name": "AG", "url": "h", "type": "adguard", "username": "u"})["type"], "adguard")

    def test_public_hides_password(self):
        p = m.public({"id": "1", "name": "n", "password": "x"}); self.assertNotIn("password", p); self.assertTrue(p["has_password"])


class Collect(unittest.TestCase):
    def cfg(self, f, **kw): return m.validate({"name": "T", "url": f.url, "type": "adguard" if f.kind == "agh" else "pihole", "password": f.password, "username": f.user, **kw})

    def test_pihole_v6(self):
        f = Fake("ph6")
        try:
            st = {}; s = m.collect(self.cfg(f), st)
            self.assertEqual((s["api"], s["queries"], s["blocked"], s["pct"], s["blocking"], s["clients"], s["domains_blocked"], s["version"]), ("v6", 1000, 250, 25.0, "enabled", 7, 99000, "v6.1"))
            self.assertEqual([x["name"] for x in s["top_blocked"]], ["ads.example", "track.example"])
            self.assertEqual(s["top_clients"][0]["name"], "pc"); self.assertEqual(s["top_clients"][1]["name"], "192.0.2.11")
            self.assertEqual(s["ms"], 30.0)                                             # (20 ms · 300 + 60 ms · 100) / 400
            self.assertEqual(sum(s["hourly"]["total"]), 290); self.assertEqual(len(s["hourly"]["total"]), 24)
            self.assertEqual(s["alerts"], [])
            logins = len([1 for x in f.log if x[1] == "/api/auth" and x[0] == "POST"]); m.collect(self.cfg(f), st)       # second reading reuses the session
            self.assertEqual(len([1 for x in f.log if x[1] == "/api/auth" and x[0] == "POST"]), logins)
            self.assertTrue(all(x[4].get("X-FTL-SID") for x in f.log if x[1].startswith("/api/stats")))
        finally: f.close()

    def test_pihole_v6_wrong_password_and_expired_session(self):
        f = Fake("ph6")
        try:
            with self.assertRaisesRegex(m.DnsError, "Wrong password"): m.collect(self.cfg(f, password="nope"), {})
            st = {}; m.collect(self.cfg(f), st); f.sessions.clear()                      # the Pi-hole forgot the session
            self.assertEqual(m.collect(self.cfg(f), st)["queries"], 1000)
        finally: f.close()

    def test_pihole_v5_is_detected(self):
        f = Fake("ph5")
        try:
            st = {}; s = m.collect(self.cfg(f), st)
            self.assertEqual((s["api"], s["queries"], s["blocked"], s["pct"], s["blocking"], s["clients"]), ("v5", 500, 100, 20.0, "enabled", 4))
            self.assertEqual(s["top_domains"][0], {"name": "b.example", "count": 70}); self.assertEqual(s["top_clients"][0]["name"], "pc")
            self.assertEqual(s["top_clients"][1]["name"], "192.0.2.12"); self.assertEqual(s["domains_blocked"], 80000)
            with self.assertRaises(m.DnsError): m.collect(self.cfg(f, password="bad"), {})
        finally: f.close()

    def test_adguard(self):
        f = Fake("agh")
        try:
            s = m.collect(self.cfg(f), {})
            self.assertEqual((s["queries"], s["blocked"], s["pct"], s["blocking"], s["ms"], s["domains_blocked"], s["version"]), (2000, 310, 15.5, "enabled", 12.3, 5000, "v0.107.50"))
            self.assertEqual(s["top_domains"][0], {"name": "a.example", "count": 90}); self.assertEqual(s["upstreams"][0]["ms"], 15.0)
            self.assertEqual(sum(s["hourly"]["total"]), 240)
            with self.assertRaisesRegex(m.DnsError, "Wrong username or password"): m.collect(self.cfg(f, password="bad"), {})
        finally: f.close()

    def test_unreachable_server_is_an_error(self):
        with self.assertRaises(m.DnsError): m.collect(m.validate({"name": "x", "url": "http://127.0.0.1:9", "timeout": 1}), {})

    def test_set_blocking_everywhere(self):
        for kind in ("ph6", "ph5", "agh"):
            f = Fake(kind)
            try:
                cfg, st = self.cfg(f), {}
                m.collect(cfg, st)
                m.set_blocking(cfg, st, False, 300); self.assertFalse(f.blocking, kind)
                s = m.collect(cfg, st); self.assertEqual(s["blocking"], "disabled", kind); self.assertEqual([a["type"] for a in s["alerts"]], ["blocking_off"])
                m.set_blocking(cfg, st, True, None); self.assertTrue(f.blocking, kind)
            finally: f.close()

    def test_pause_sends_the_duration(self):
        f = Fake("ph6"); g = Fake("agh")
        try:
            c, st = self.cfg(f), {}; m.collect(c, st); m.set_blocking(c, st, False, 120)
            self.assertEqual(f.timer, 120); self.assertEqual(m.collect(c, st)["timer"], 120)
            c2 = self.cfg(g); m.set_blocking(c2, {}, False, 90)
            self.assertEqual([x[3] for x in g.log if x[1] == "/control/protection"][0], {"enabled": False, "duration": 90000})
        finally: f.close(); g.close()

    def test_test_connection_frees_the_pihole_session(self):
        f = Fake("ph6")
        try:
            r = m.test_connection(self.cfg(f)); self.assertEqual((r["api"], r["queries"]), ("v6", 1000)); self.assertEqual(f.sessions, set())
        finally: f.close()


class Alerts(unittest.TestCase):
    def test_rules(self):
        base = {"blocking": "enabled", "domains_blocked": 10, "upstreams": []}
        self.assertEqual(m.compute_alerts(base), [])
        self.assertEqual([a["type"] for a in m.compute_alerts({**base, "blocking": "disabled", "timer": 60})], ["blocking_off"])
        self.assertEqual(m.compute_alerts({**base, "blocking": "failed"})[0]["lv"], "crit")
        self.assertEqual([a["type"] for a in m.compute_alerts({**base, "domains_blocked": 0})], ["no_lists"])
        self.assertEqual([a["type"] for a in m.compute_alerts({**base, "upstreams": [{"ms": 800}]})], ["slow_upstream"])
        self.assertEqual(m.compute_alerts({**base, "blocking": "disabled", "domains_blocked": 0}), [{"lv": "warn", "type": "blocking_off", "value": None}])

    def test_bin24(self):
        now = 1_000_000.0
        b = m.bin24([(now - 100, 5, 1), (now - 3700, 7, 2), (now - 90000, 9, 9)], now)
        self.assertEqual((b["total"][23], b["total"][22], sum(b["total"])), (5, 7, 12)); self.assertEqual(sum(b["blocked"]), 3)


class Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        m.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.started = []; cls._ep, m.ensure_poller = m.ensure_poller, lambda n: cls.started.append(n["id"])
        cls.admin, cls.exe, cls.ro, cls.none = (support.make_user("dadm", {**ADMIN}), support.make_user("dexe", {**READONLY, "dns": "execute"}),
                                                support.make_user("dro", READONLY), support.make_user("dnone", NONE))
        cls.srv = support.Server(m.H)
    @classmethod
    def tearDownClass(cls): m.ensure_poller = cls._ep; cls.srv.close()
    def setUp(self): m.save_servers([]); m._cache.clear()

    def test_permissions(self):
        c = self.srv.call
        self.assertEqual(c("GET", "/api/dns")[0], 401); self.assertEqual(c("GET", "/api/dns", token=self.none)[0], 401); self.assertEqual(c("GET", "/api/dns", token=self.ro)[0], 200)
        body = {"name": "a", "url": "192.0.2.9", "password": "x"}
        for path in ("/api/dns", "/api/test"):
            self.assertEqual(c("POST", path, body, token=self.ro)[0], 403, path); self.assertEqual(c("POST", path, body, token=self.exe)[0], 403, path)
            self.assertEqual(c("POST", path, body)[0], 401, path)
        self.assertEqual(c("DELETE", "/api/dns/abc", token=self.exe)[0], 403)

    def test_create_edit_delete_and_password_stays_server_side(self):
        c = self.srv.call; body = {"name": "Main", "url": "192.0.2.9", "type": "pihole", "password": "TopSecret99"}
        s, j = c("POST", "/api/dns", body, token=self.admin); self.assertEqual(s, 201, j)
        sid = j["server"]["id"]; self.assertIn(sid, self.started); self.assertNotIn("TopSecret99", json.dumps(j))
        self.assertEqual(c("POST", "/api/dns", {**body, "name": "Dup"}, token=self.admin)[0], 409)
        s, j = c("GET", "/api/dns", token=self.ro); self.assertEqual(len(j["servers"]), 1)
        self.assertNotIn("TopSecret99", json.dumps(j)); self.assertTrue(j["servers"][0]["has_password"])
        s, j = c("POST", "/api/dns/" + sid, {"name": "Renamed", "password": ""}, token=self.admin); self.assertEqual(s, 200, j)
        st = m.load_servers()[0]; self.assertEqual((st["name"], st["password"]), ("Renamed", "TopSecret99"))
        self.assertEqual(oct(stat.S_IMODE(os.stat(m.DATA_FILE).st_mode)), "0o600")
        self.assertEqual(c("POST", "/api/dns/nope", {"name": "x"}, token=self.admin)[0], 404)
        self.assertEqual(c("DELETE", "/api/dns/" + sid, token=self.admin)[0], 200); self.assertEqual(m.load_servers(), [])
        self.assertEqual(c("DELETE", "/api/dns/" + sid, token=self.admin)[0], 404)

    def test_invalid_bodies(self):
        c = self.srv.call
        for bad in ({}, {"name": "a", "url": "ftp://x"}, {"name": "a", "url": "http://u:p@h"}, {"name": "a", "url": "h", "type": "adguard"}, {"name": "a", "url": "h", "timeout": 0}):
            self.assertEqual(c("POST", "/api/dns", bad, token=self.admin)[0], 400, bad)

    def test_connection_test_uses_stored_password_when_empty(self):
        f = Fake("ph6")
        try:
            s, j = self.srv.call("POST", "/api/dns", {"name": "T", "url": f.url, "type": "pihole", "password": "secret"}, token=self.admin); sid = j["server"]["id"]
            s, r = self.srv.call("POST", "/api/test", {"id": sid, "name": "T", "url": f.url, "type": "pihole", "password": ""}, token=self.admin)
            self.assertTrue(r["ok"], r); self.assertEqual(r["api"], "v6")
            s, r = self.srv.call("POST", "/api/test", {"name": "T", "url": f.url, "type": "pihole", "password": "wrong"}, token=self.admin)
            self.assertFalse(r["ok"]); self.assertIn("Wrong password", r["error"])
        finally: f.close()

    def test_pause_needs_execute_and_validates(self):
        f = Fake("ph6")
        try:
            s, j = self.srv.call("POST", "/api/dns", {"name": "T", "url": f.url, "type": "pihole", "password": "secret"}, token=self.admin); sid = j["server"]["id"]
            url = f"/api/dns/{sid}/blocking"
            self.assertEqual(self.srv.call("POST", url, {"enabled": False}, token=self.ro)[0], 403)
            self.assertEqual(self.srv.call("POST", url, {"enabled": False})[0], 401)
            self.assertEqual(self.srv.call("POST", url, {"enabled": "no"}, token=self.exe)[0], 400)
            self.assertEqual(self.srv.call("POST", url, {"enabled": False, "seconds": 0}, token=self.exe)[0], 400)
            self.assertEqual(self.srv.call("POST", url, {"enabled": False, "seconds": 300}, token=self.exe)[0], 200)
            self.assertFalse(f.blocking); self.assertEqual(f.timer, 300)
            self.assertEqual(self.srv.call("POST", url, {"enabled": True}, token=self.exe)[0], 200); self.assertTrue(f.blocking)
            self.assertEqual(self.srv.call("POST", "/api/dns/nope/blocking", {"enabled": True}, token=self.exe)[0], 404)
        finally: f.close()

    def test_history_endpoint(self):
        s, j = self.srv.call("POST", "/api/dns", {"name": "H", "url": "192.0.2.50", "password": "x"}, token=self.admin); sid = j["server"]["id"]
        now = int(time.time()); cn = support.auth.metrics_conn()
        try:
            for i in range(5): cn.execute("INSERT OR REPLACE INTO dns_samples VALUES (?,?,?,?,?,?)", (sid, now - 60 * i, 100 + i, 20, 20.0, 10.0 + i))
            cn.commit()
        finally: cn.close()
        s, j = self.srv.call("GET", f"/api/dns/{sid}/history?range=1h", token=self.ro); self.assertEqual(s, 200); self.assertEqual(len(j["history"]), 5)
        self.assertEqual(self.srv.call("GET", f"/api/dns/{sid}/history?range=zz", token=self.ro)[0], 400)
        self.assertEqual(self.srv.call("GET", "/api/dns/nope/history", token=self.ro)[0], 404)
        m.forget_history(sid)


class Poller(unittest.TestCase):
    def test_poll_updates_cache_and_history(self):
        f = Fake("ph6"); old = (m.POLL_ACTIVE, m.POLL_IDLE)
        try:
            n = m.validate({"name": "P", "url": f.url, "type": "pihole", "password": "secret"}); n["id"] = "test-poll-1"
            m.save_servers([n]); m._cache["test-poll-1"] = m.DnsCache("test-poll-1")
            m.POLL_ACTIVE = m.POLL_IDLE = 0.05
            t = threading.Thread(target=m._poll, args=("test-poll-1",), daemon=True); t.start()
            for _ in range(60):
                if m._cache["test-poll-1"].snap()["ts"]: break
                time.sleep(0.05)
            sn = m._cache["test-poll-1"].snap(); self.assertEqual(sn["data"]["queries"], 1000); self.assertIsNone(sn["error"])
            self.assertTrue(m.get_history("test-poll-1"))
            m.save_servers([])                                  # deleted → the thread ends by itself
            t.join(3); self.assertFalse(t.is_alive())
        finally:
            m.POLL_ACTIVE, m.POLL_IDLE = old; m.save_servers([]); m.forget_history("test-poll-1"); f.close()

if __name__ == "__main__": unittest.main()
