"""Uptime Monitor: validación, certificados (DER), DNS, revisiones HTTP/TCP/DNS reales contra servidores locales, reintentos, eventos, historial y permisos.
EN: Uptime Monitor: validation, certificates (DER), DNS, real HTTP/TCP/DNS checks against local servers, failures before down, events, history and permissions."""
import calendar
import shutil
import socket
import ssl
import struct
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from tests import support
from tests.support import ADMIN, NONE, READONLY

m = support.load("uptime-monitor/server.py")


def tlv(tag, body: bytes) -> bytes:
    n = len(body)
    ln = bytes([n]) if n < 0x80 else bytes([0x80 | 2]) + n.to_bytes(2, "big")
    return bytes([tag]) + ln + body


def fake_cert(not_after: bytes, tag=0x17, version=True) -> bytes:
    """Minimal DER certificate: version, serial, signature, issuer, validity and subject (enough for certinfo.parse)."""
    name = lambda cn: tlv(0x30, tlv(0x31, tlv(0x30, tlv(0x06, bytes.fromhex("550403")) + tlv(0x0C, cn))))
    tbs = (tlv(0xA0, tlv(0x02, b"\x02")) if version else b"") + tlv(0x02, b"\x01") + tlv(0x30, b"") + name(b"Issuer " + b"x" * 200) \
        + tlv(0x30, tlv(0x17, b"240101000000Z") + tlv(tag, not_after)) + name(b"nas.example.lan")
    return tlv(0x30, tlv(0x30, tbs) + tlv(0x30, b"") + tlv(0x03, b"\x00"))


class Validate(unittest.TestCase):
    def test_http_defaults_and_tls_fields(self):
        h = m.validate({"type": "http", "name": "web", "url": "http://nas.example.lan/"})
        self.assertEqual((h["interval"], h["timeout"], h["down_after"], h["expect"], h["keyword"]), (60, 10, 3, "200-399", ""))
        self.assertNotIn("insecure", h); self.assertNotIn("cert_days", h)
        s = m.validate({"type": "http", "name": "pve", "url": "https://192.0.2.10:8006/", "insecure": True, "cert_days": 30, "expect": "200, 301"})
        self.assertEqual((s["insecure"], s["cert_days"], s["expect"]), (True, 30, "200,301"))

    def test_rejects_bad_input(self):
        bad = ({"type": "ping", "name": "x"}, {"type": "http", "name": "", "url": "http://a.example/"},
               {"type": "http", "name": "x", "url": "ftp://a.example/"}, {"type": "http", "name": "x", "url": "http://u:p@a.example/"},
               {"type": "http", "name": "x", "url": "http://a.example/\nx"}, {"type": "http", "name": "x", "url": "http://a.example/", "expect": "2xx"},
               {"type": "http", "name": "x", "url": "http://a.example/", "expect": "600"}, {"type": "http", "name": "x", "url": "http://a.example:99999/"},
               {"type": "http", "name": "x", "url": "http://a.example/", "interval": 10}, {"type": "http", "name": "x", "url": "http://a.example/", "interval": 20, "timeout": 20},
               {"type": "http", "name": "x", "url": "http://a.example/", "down_after": 0}, {"type": "http", "name": "x", "url": "http://a.example/", "down_after": 7}, {"type": "tcp", "name": "x", "host": "192.0.2.9"},
               {"type": "tcp", "name": "x", "host": "-oProxy", "port": 22}, {"type": "dns", "name": "x", "qname": "a b"},
               {"type": "dns", "name": "x", "qname": "a.example", "rtype": "MX"}, {"type": "dns", "name": "x", "qname": "a.example", "expect_ip": "999.1.1.1"},
               {"type": "dns", "name": "x", "qname": "a.example", "server": "-x"})
        for b in bad:
            with self.subTest(b=b), self.assertRaises(ValueError): m.validate(b)

    def test_changing_type_drops_the_old_fields(self):
        cur = m.validate({"type": "http", "name": "x", "url": "https://a.example/", "keyword": "ok"}); cur["id"] = "i"
        t = m.validate({"type": "tcp", "host": "192.0.2.9", "port": 22}, cur)
        self.assertEqual((t["name"], t["host"], t["port"], t["id"]), ("x", "192.0.2.9", 22, "i"))
        for k in ("url", "keyword", "insecure", "cert_days", "expect"): self.assertNotIn(k, t)

    def test_http_refuses_this_machine_tcp_and_dns_allow_it(self):
        with mock.patch.object(m.auth, "valid_target", support.real_valid_target):
            for u in ("http://127.0.0.1/", "https://localhost/", "http://169.254.169.254/latest", "http://[::1]:8082/"):
                with self.subTest(u=u), self.assertRaises(ValueError): m.validate({"type": "http", "name": "x", "url": u})
            self.assertEqual(m.validate({"type": "tcp", "name": "x", "host": "127.0.0.1", "port": 22})["host"], "127.0.0.1")
            self.assertEqual(m.validate({"type": "dns", "name": "x", "qname": "a.example", "server": "127.0.0.53"})["server"], "127.0.0.53")
            with self.assertRaises(ValueError): m.validate({"type": "tcp", "name": "x", "host": "169.254.169.254", "port": 80})
            with self.assertRaises(m.CheckError): m._connect_addr("127.0.0.1", 80, allow_loopback=False)      # checked again on connect

    def test_reorder_keeps_unlisted_at_the_end(self):
        items = [{"id": k} for k in "abcd"]
        self.assertEqual([x["id"] for x in m.reorder(items, ["c", "zz", "a", "c"])], ["c", "a", "b", "d"])
        self.assertEqual([x["id"] for x in m.reorder(items, [])], list("abcd"))

    def test_expect_and_target(self):
        self.assertEqual(m.parse_expect("200-299,301"), [(200, 299), (301, 301)])
        self.assertTrue(m._code_ok(301, "200-299,301")); self.assertFalse(m._code_ok(302, "200-299,301"))
        self.assertEqual(m.target_of({"type": "tcp", "host": "2001:db8::1", "port": 22}), "[2001:db8::1]:22")
        self.assertEqual(m.target_of({"type": "dns", "qname": "a.example", "rtype": "A", "server": "192.0.2.53"}), "a.example A @192.0.2.53")


class Certificates(unittest.TestCase):
    def test_not_after_utc_and_generalized(self):
        self.assertEqual(m.cert_not_after(fake_cert(b"300615120000Z")), calendar.timegm((2030, 6, 15, 12, 0, 0)))
        self.assertEqual(m.cert_not_after(fake_cert(b"20510101000000Z", tag=0x18)), calendar.timegm((2051, 1, 1, 0, 0, 0)))
        self.assertEqual(m.cert_not_after(fake_cert(b"491231235959Z", version=False)), calendar.timegm((2049, 12, 31, 23, 59, 59)))
        for junk in (b"", b"\x30", b"\x30\x84\xff\xff\xff\xff", fake_cert(b"nonsense")):
            self.assertIsNone(m.cert_not_after(junk))

    def test_state(self):
        now = 1_000_000_000
        self.assertIsNone(m.cert_state(None, 14, now))
        self.assertEqual(m.cert_state(now - 1, 14, now), "expired")
        self.assertEqual(m.cert_state(now + 5 * 86400, 14, now), "warn")
        self.assertEqual(m.cert_state(now + 60 * 86400, 14, now), "ok")


def dns_answer(qid, ips, rcode=0, flags=0x8180):
    q = m.dns_query_packet("nas.example.lan", "A", qid)[12:]
    ans = b"".join(b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 60, 4) + socket.inet_aton(ip) for ip in ips)
    return struct.pack(">HHHHHH", qid, flags | rcode, 1, len(ips), 0, 0) + q + ans


class Dns(unittest.TestCase):
    def test_packet_and_parse(self):
        p = m.dns_query_packet("nas.example.lan", "AAAA", 0x1234)
        self.assertEqual(p[:2], b"\x12\x34"); self.assertTrue(p.endswith(b"\x03lan\x00\x00\x1c\x00\x01"))
        self.assertEqual(m.dns_parse(dns_answer(7, ["192.0.2.7", "192.0.2.8"]), 7, "A"), ["192.0.2.7", "192.0.2.8"])
        with self.assertRaisesRegex(m.CheckError, "NXDOMAIN"): m.dns_parse(dns_answer(7, [], rcode=3), 7, "A")
        with self.assertRaisesRegex(m.CheckError, "unexpected"): m.dns_parse(dns_answer(8, ["192.0.2.7"]), 7, "A")
        with self.assertRaisesRegex(m.CheckError, "malformed"): m.dns_parse(dns_answer(7, ["192.0.2.7"])[:-3], 7, "A")

    def test_check_against_a_local_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
        def serve():
            for _ in range(2):
                data, addr = s.recvfrom(512)
                s.sendto(dns_answer(struct.unpack(">H", data[:2])[0], ["192.0.2.7"]), addr)
        threading.Thread(target=serve, daemon=True).start()
        real = m._connect_addr
        with mock.patch.object(m, "_connect_addr", lambda h, p, allow_loopback, kind: real(h, port, allow_loopback, kind)):
            ok = m.run_check({"type": "dns", "name": "d", "qname": "nas.example.lan", "rtype": "A", "server": "127.0.0.1", "expect_ip": "192.0.2.7", "timeout": 3})
            self.assertTrue(ok["ok"], ok); self.assertEqual(ok["ips"], ["192.0.2.7"])
            bad = m.run_check({"type": "dns", "name": "d", "qname": "nas.example.lan", "rtype": "A", "server": "127.0.0.1", "expect_ip": "192.0.2.9", "timeout": 3})
            self.assertFalse(bad["ok"]); self.assertIn("192.0.2.7", bad["error"])
        s.close()


class Page(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        code = 500 if self.path == "/fail" else 200
        body = b"<html>Welcome to the NAS</html>"
        self.send_response(code); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Page); cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close()

    def http(self, path="/", **kw):
        return m.run_check({"type": "http", "name": "w", "url": f"http://127.0.0.1:{self.port}{path}", "timeout": 3, "expect": "200-399", **kw})

    def test_http_status_and_keyword(self):
        r = self.http(); self.assertTrue(r["ok"], r); self.assertEqual(r["code"], 200); self.assertIsInstance(r["ms"], float)
        self.assertTrue(self.http(keyword="welcome")["ok"])                       # case-insensitive
        self.assertEqual(self.http(keyword="Login")["error"], "keyword not found")
        self.assertEqual(self.http("/fail")["error"], "HTTP 500")
        self.assertTrue(self.http("/fail", expect="500")["ok"])

    def test_tcp_open_and_closed(self):
        self.assertTrue(m.run_check({"type": "tcp", "name": "t", "host": "127.0.0.1", "port": self.port, "timeout": 3})["ok"])
        s = socket.socket(); s.bind(("127.0.0.1", 0)); closed = s.getsockname()[1]; s.close()
        r = m.run_check({"type": "tcp", "name": "t", "host": "127.0.0.1", "port": closed, "timeout": 3})
        self.assertFalse(r["ok"]); self.assertTrue(r["error"])


@unittest.skipUnless(shutil.which("openssl"), "openssl not installed")
class Https(unittest.TestCase):
    """A real self-signed certificate: refused when verified, accepted with «do not verify», and its expiry is read either way."""
    @classmethod
    def setUpClass(cls):
        d = Path(tempfile.mkdtemp()); key, crt = d / "k.pem", d / "c.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30", "-subj", "/CN=uptime.test",
                        "-keyout", str(key), "-out", str(crt)], check=True, capture_output=True, timeout=60)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(str(crt), str(key))
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Page); cls.srv.socket = ctx.wrap_socket(cls.srv.socket, server_side=True)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close()

    def test_self_signed(self):
        url = f"https://127.0.0.1:{self.port}/"
        r = m.run_check({"type": "http", "name": "s", "url": url, "timeout": 5})
        self.assertFalse(r["ok"]); self.assertTrue(r["error"].startswith("certificate:"), r)
        r = m.run_check({"type": "http", "name": "s", "url": url, "timeout": 5, "insecure": True})
        self.assertTrue(r["ok"], r); self.assertAlmostEqual(r["cert_exp"], time.time() + 30 * 86400, delta=2 * 86400)


class Results(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.p = mock.patch.object(m, "STATE_FILE", Path(self.tmp) / "state.json"); self.p.start()
        self.ev = []; self.r = mock.patch.object(m.auth, "record_event", lambda mod, lv, tx, k=None, **p: self.ev.append((k, lv, p))); self.r.start()
        m._state.clear(); m._db("DELETE FROM uptime_beats"); m._db("DELETE FROM uptime_hourly"); m._flush()
    def tearDown(self): self.p.stop(); self.r.stop(); m._state.clear()

    def test_three_failures_pending_then_down_then_up_with_events(self):
        cfg = {"id": "a", "name": "NAS", "type": "tcp", "host": "192.0.2.9", "port": 22}            # down_after missing = 3
        mon = m.Mon("a"); now = 1_700_000_000
        m.apply_result(cfg, mon, {"ok": True, "ms": 2.0}, now)
        self.assertEqual((mon.status, self.ev), ("up", []))                        # the first state is not an event
        for i in (1, 2):
            m.apply_result(cfg, mon, {"ok": False, "ms": None, "error": "timed out"}, now + 60 * i)
            self.assertEqual((mon.status, mon.beats[-1][1], self.ev), ("up", m.PENDING, []))    # 1st and 2nd failure: pending
        m.apply_result(cfg, mon, {"ok": False, "ms": None, "error": "timed out"}, now + 180)
        self.assertEqual(mon.status, "down"); self.assertEqual(self.ev[-1][:2], ("uptime_down", "crit")); self.assertEqual(self.ev[-1][2]["e"], "timed out")
        m.apply_result(cfg, mon, {"ok": True, "ms": 3.0}, now + 240)
        self.assertEqual((mon.status, self.ev[-1][0]), ("up", "uptime_up"))
        self.assertEqual(m._state["a"], {"st": "up", "since": now + 240})
        self.assertTrue((Path(self.tmp) / "state.json").exists())

    def test_certificate_events_once(self):
        now = time.time()
        cfg = {"id": "c", "name": "Web", "type": "http", "url": "https://a.example/", "cert_days": 14, "down_after": 1}
        mon = m.Mon("c")
        for i in range(3): m.apply_result(cfg, mon, {"ok": True, "ms": 1.0, "cert_exp": now + 5 * 86400}, now + i)
        self.assertEqual([e[0] for e in self.ev], ["uptime_cert"]); self.assertEqual(self.ev[0][2]["d"], 5)
        m.apply_result(cfg, mon, {"ok": False, "ms": None, "error": "certificate: certificate has expired", "cert_exp": now - 10}, now + 10)
        self.assertIn("uptime_certexp", [e[0] for e in self.ev])

    def test_history_and_percentages(self):
        cfg = {"id": "h", "name": "H", "type": "tcp", "host": "192.0.2.9", "port": 22, "down_after": 1}
        mon = m.Mon("h"); now = int(time.time()) - 3000
        for i in range(10): m.apply_result(cfg, mon, {"ok": i != 3, "ms": 10.0 if i != 3 else None, "error": "x"}, now + i * 60)
        m._stats_cache["ts"] = 0
        st = m.uptime_stats()["h"]
        self.assertEqual((st["24h"], st["7d"], st["30d"], st["avg"]), (90.0, 90.0, 90.0, 10.0))
        h1 = m.history("h", "1h"); self.assertEqual(len(h1), 10); self.assertEqual((h1[3]["up"], h1[3]["ms"], h1[0]["ms"]), (0, None, 10.0))
        d = m.history("h", "1d"); self.assertTrue(1 <= len(d) <= 3); self.assertTrue(all(p["ts"] % 300 == 0 for p in d))
        self.assertEqual(sum(p["up"] == 0 for p in d), 1)                          # the bucket with the down check is red
        for r in ("1w", "1mo", "all"):
            pts = m.history("h", r); self.assertTrue(pts, r); self.assertEqual(sum(p["ms"] is not None for p in pts), len(pts), r)
            self.assertAlmostEqual(sum(p["pct"] for p in pts) / len(pts), 90.0, delta=10, msg=r)
        self.assertEqual(m.history("h", "1d", prev=True), []); self.assertEqual(m.history("h", "all", prev=True), [])
        self.assertEqual(len(m.history("h", "1d", prev=True, now=time.time() + 86400)), len(d))     # one day later, today is "previous"
        m.prune(now + 10 * 86400); self.assertEqual(m.history("h", "1h"), [])
        m.drop_history("h"); m._stats_cache["ts"] = 0; self.assertNotIn("h", m.uptime_stats())


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.patches = [mock.patch.object(m, "DATA_FILE", Path(cls.tmp) / "uptime.json"), mock.patch.object(m, "STATE_FILE", Path(cls.tmp) / "state.json"),
                       mock.patch.object(m, "ensure_monitor", lambda mon: m._mons.setdefault(mon["id"], m.Mon(mon["id"])))]
        for p in cls.patches: p.start()
        cls.srv = support.Server(m.H)
        cls.admin = support.make_user("upadm", ADMIN); cls.ro = support.make_user("upro", READONLY); cls.no = support.make_user("upno", NONE)
        cls.ex = support.make_user("upex", {**READONLY, "uptime": "execute"})
    @classmethod
    def tearDownClass(cls):
        cls.srv.close()
        for p in cls.patches: p.stop()
        m._mons.clear()

    def test_crud_permissions_and_check_now(self):
        body = {"type": "tcp", "name": "SSH", "host": "192.0.2.9", "port": 22}
        self.assertEqual(self.srv.call("GET", "/api/monitors", token=self.no)[0], 401)
        self.assertEqual(self.srv.call("POST", "/api/monitors", body, token=self.ro)[0], 403)
        s, j = self.srv.call("POST", "/api/monitors", body, token=self.admin); self.assertEqual(s, 201, j)
        mid = j["monitor"]["id"]
        s, j = self.srv.call("GET", "/api/monitors", token=self.ro); self.assertEqual(s, 200)
        got = next(x for x in j["monitors"] if x["id"] == mid)
        self.assertEqual((got["target"], got["status"], got["beats"]), ("192.0.2.9:22", None, []))
        self.assertNotIn("beats", self.srv.call("GET", "/api/monitors?beats=0", token=self.ro)[1]["monitors"][0])
        self.assertEqual(self.srv.call("GET", f"/api/monitors/{mid}/history?range=1w", token=self.ro)[1], {"range": "1w", "prev": False, "history": []})
        self.assertEqual(self.srv.call("GET", f"/api/monitors/{mid}/history?range=5y", token=self.ro)[0], 400)
        self.assertEqual(self.srv.call("POST", f"/api/monitors/{mid}/check", {}, token=self.ro)[0], 403)
        self.assertEqual(self.srv.call("POST", f"/api/monitors/{mid}/check", {}, token=self.ex)[0], 200)
        self.assertEqual(self.srv.call("POST", f"/api/monitors/{mid}", {"name": "x"}, token=self.ex)[0], 403)
        s, j = self.srv.call("POST", f"/api/monitors/{mid}", {"type": "tcp", "name": "SSH 2", "host": "192.0.2.9", "port": 2222}, token=self.admin)
        self.assertEqual((s, j["monitor"]["port"]), (200, 2222))
        self.assertEqual(self.srv.call("POST", f"/api/monitors/{mid}", {"type": "tcp", "name": "x", "port": 0}, token=self.admin)[0], 400)
        self.assertEqual(self.srv.call("DELETE", f"/api/monitors/{mid}", token=self.ro)[0], 403)
        self.assertEqual(self.srv.call("DELETE", f"/api/monitors/{mid}", token=self.admin)[0], 200)
        self.assertEqual(self.srv.call("GET", f"/api/monitors/{mid}/history", token=self.ro)[0], 404)

    def test_order_is_saved_by_admins_only(self):
        ids = []
        for nm in ("A", "B", "C"):
            _, j = self.srv.call("POST", "/api/monitors", {"type": "tcp", "name": nm, "host": "192.0.2.9", "port": 22}, token=self.admin); ids.append(j["monitor"]["id"])
        try:
            names = lambda: [x["name"] for x in self.srv.call("GET", "/api/monitors", token=self.ro)[1]["monitors"]]
            self.assertEqual(names(), ["A", "B", "C"])
            self.assertEqual(self.srv.call("POST", "/api/order", {"order": [ids[2], ids[0], ids[1]]}, token=self.ro)[0], 403)
            self.assertEqual(self.srv.call("POST", "/api/order", {"order": [ids[2], ids[0], ids[1]]}, token=self.ex)[0], 403)
            self.assertEqual(self.srv.call("POST", "/api/order", {"order": [ids[2], ids[0], ids[1]]}, token=self.admin)[0], 200)
            self.assertEqual(names(), ["C", "A", "B"])
            self.assertEqual(self.srv.call("POST", "/api/order", {"order": [ids[1]]}, token=self.admin)[0], 200)
            self.assertEqual(names(), ["B", "C", "A"])                                  # the rest keeps its order at the end
            for bad in ({"order": "x"}, {"order": ["../x"]}, {"order": [1]}, {}):
                self.assertEqual(self.srv.call("POST", "/api/order", bad, token=self.admin)[0], 400, bad)
            self.assertEqual(self.srv.call("POST", "/api/order", {"order": [ids[0]]}, token=self.admin, headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        finally:
            for i in ids: self.srv.call("DELETE", f"/api/monitors/{i}", token=self.admin)

    def test_test_endpoint_runs_one_check(self):
        with mock.patch.object(m, "run_check", return_value={"ok": False, "ms": None, "error": "timed out"}):
            s, j = self.srv.call("POST", "/api/test", {"type": "tcp", "name": "x", "host": "192.0.2.9", "port": 22}, token=self.admin)
        self.assertEqual((s, j["ok"], j["error"]), (200, False, "timed out"))
        self.assertEqual(self.srv.call("POST", "/api/test", {"type": "tcp", "name": "x"}, token=self.admin)[0], 400)

    def test_health_warns_when_a_service_is_down(self):
        m.save_monitors([{"id": "z" * 8 + "-0000-0000-0000-000000000000", "name": "Z", "type": "tcp", "host": "192.0.2.9", "port": 1, "interval": 60, "timeout": 10, "down_after": 3}])
        try:
            mon = m._mons.setdefault("z" * 8 + "-0000-0000-0000-000000000000", m.Mon("z"))
            mon.status = "down"
            c = m.health_report(True)[1]["checks"]
            self.assertEqual(c["uptime_services"]["level"], "warn")
        finally:
            m.save_monitors([]); m._mons.clear()


class Wiring(unittest.TestCase):
    def test_module_is_registered_everywhere(self):
        r = lambda p: (support.ROOT / p).read_text()
        self.assertIn('"uptime": 8090', r("auth/admin_panel.py")); self.assertIn('"uptime"', r("auth/authrpc.py"))
        self.assertIn("uptime_beats", r("auth/auth.py")); self.assertIn('"uptime"', r("overview/server.py"))
        self.assertIn("location /uptime/ {", r("etc/nginx/snippets/labtower-site.conf")); self.assertIn("127.0.0.1:8090", r("etc/nginx/snippets/labtower-site.conf"))
        self.assertIn("data/uptime-monitor/uptime.json", r("scripts/teleporter.sh")); self.assertIn("data/uptime-monitor/metrics.db", r("scripts/teleporter.sh"))
        self.assertIn("uptime-monitor/uptime.json:uptime.json", r("debian/postinst"))
        self.assertIn("function renderUptime", r("overview/static/app.js")); self.assertIn('id="c-upt"', r("overview/static/index.html"))
        self.assertIn('id="d-uptime"', r("auth/static/index.html"))


if __name__ == "__main__":
    unittest.main()
