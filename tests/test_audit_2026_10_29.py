"""Correcciones de la revisión de seguridad del 2026-10-29 / Fixes from the 2026-10-29 security review."""
import json, os, re, shutil, ssl, subprocess, tempfile, threading, time, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tests import support
from tests.support import ADMIN, READONLY
auth = support.auth
ROOT = Path(__file__).resolve().parent.parent


class FakeHandler:
    def __init__(self, ip="198.51.100.9"): self.client_address = ("127.0.0.1", 1); self.headers = {"X-Real-IP": ip}


class Throttle(unittest.TestCase):
    def test_successful_login_does_not_reset_the_ip_counter(self):
        support.make_user("guest1", READONLY, password="Guest-pass-12345")
        h = FakeHandler("203.0.113.77")
        for _ in range(3): auth.login(h, "guest1", "bad")
        u, err = auth.login(h, "guest1", "Guest-pass-12345")          # a valid login in between…
        self.assertIsNotNone(u)
        for _ in range(2): auth.login(h, "nobody-here", "bad")        # …must not give the IP a fresh set of attempts
        self.assertGreater(auth.throttle_wait("ip:203.0.113.77"), 0)
        auth.throttle_clear("ip:203.0.113.77")


class SessionCap(unittest.TestCase):
    def test_absolute_lifetime(self):
        tok = support.make_user("capuser", READONLY)
        self.assertIsNotNone(auth.get_session(tok))
        with auth._sessions_lock:
            ss = auth._load_sessions(); s = ss[auth._tkey(tok)]
            s["created"] = time.time() - 15 * 24 * 3600               # older than the 14-day cap of a normal session
            s["expires"] = time.time() + 3600                         # still "active" by the sliding window
            auth._save_sessions(ss)
        self.assertIsNone(auth.get_session(tok))


class UsersSanitized(unittest.TestCase):
    def test_unknown_levels_and_bad_entries_are_dropped(self):
        out = auth._sanitize_users({"a": {"password_hash": "x", "permissions": {"wol": "admin", "net": "<img onerror=1>", 5: "admin"}},
                                    "b": "notadict", "c": {"password_hash": "y", "permissions": ["x"]}})
        self.assertEqual(out["a"]["permissions"], {"wol": "admin", "net": "none"})
        self.assertNotIn("b", out)
        self.assertEqual(out["c"]["permissions"], {})


class TargetCheck(unittest.TestCase):
    def test_real_valid_target(self):
        v = support.real_valid_target
        for bad in ("127.0.0.1", "localhost", "foo.localhost", "::1", "0.0.0.0", "169.254.169.254", "[::1]", "::ffff:127.0.0.1", "127.1.2.3", "-x"):
            with self.subTest(bad=bad): self.assertFalse(v(bad))
        for good in ("192.0.2.5", "10.1.2.3", "2001:db8::1", "no-such-host.invalid"):
            with self.subTest(good=good): self.assertTrue(v(good))


class BodyMustBeObject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = support.Server(support.load("wol-console/server.py").H)
        cls.tok = support.make_user("bodyadm", ADMIN)
    @classmethod
    def tearDownClass(cls): cls.s.close()
    def test_non_object_bodies_are_400(self):
        import http.client
        for raw in (b"[]", b"1", b"null", b'"x"', b"[" * 5000):
            c = http.client.HTTPConnection("127.0.0.1", self.s.port, timeout=10)
            c.request("POST", "/api/wake", raw, {"Content-Type": "application/json", "Cookie": "session=" + self.tok, "Content-Length": str(len(raw))})
            r = c.getresponse(); r.read(); c.close()
            self.assertEqual(r.status, 400, raw[:10])


class AdminReauth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = support.Server(support.load("auth/admin_panel.py").H)
        cls.pw = "Admin-pass-12345"
        cls.tok = support.make_user("reauthadm", ADMIN, password=cls.pw)
    @classmethod
    def tearDownClass(cls): cls.s.close()
    def test_create_user_needs_the_account_password(self):
        body = {"username": "newone", "password": "Another-pass-123"}
        self.assertEqual(self.s.call("POST", "/api/users", body, self.tok)[0], 401)
        self.assertEqual(self.s.call("POST", "/api/users", {**body, "current_password": "wrong"}, self.tok)[0], 403)
        self.assertEqual(self.s.call("POST", "/api/users", {**body, "current_password": self.pw}, self.tok)[0], 201)
    def test_reset_of_another_account_needs_the_password(self):
        support.make_user("victim", READONLY)
        body = {"username": "victim", "new_password": "Brand-new-pass-1"}
        self.assertEqual(self.s.call("POST", "/api/change_password", body, self.tok)[0], 401)
        self.assertEqual(self.s.call("POST", "/api/change_password", {**body, "current_password": self.pw}, self.tok)[0], 200)
    def test_restore_needs_the_password(self):
        code, _ = self.s.call("POST", "/api/teleporter/restore", {"name": "labtower-x.tar.gz", "confirm": True}, self.tok)
        self.assertIn(code, (401, 503))                                # 503 if teleporter.sh is not installed here; never 200
    def test_old_plain_download_route_is_gone(self):
        self.assertEqual(self.s.call("GET", "/api/teleporter/download/labtower-x.tar.gz", None, self.tok)[0], 404)
    def test_wrong_json_types_are_400_not_500(self):
        self.assertEqual(self.s.call("POST", "/api/users", {"username": ["a"], "password": 5, "current_password": self.pw}, self.tok)[0], 400)


@unittest.skipUnless(shutil.which("gpg"), "gpg not installed")
class BackupEncryption(unittest.TestCase):
    def test_encrypt_and_decrypt_roundtrip(self):
        import teleporter_api as tp
        with tempfile.TemporaryDirectory() as d:
            old = tp.SPOOL; tp.SPOOL = Path(d)
            try:
                import gzip
                (Path(d) / "labtower-t.tar.gz").write_bytes(gzip.compress(b"secret data"))
                self.assertIsNone(tp.encrypt_backup("labtower-t.tar.gz", "short")[0])
                out, err = tp.encrypt_backup("labtower-t.tar.gz", "a long passphrase 123")
                self.assertIsNone(err); data = out.read_bytes(); out.unlink()
                self.assertNotIn(b"secret data", data); self.assertIn(data[0], tp.GPG_MAGIC)
                import io
                self.assertEqual(tp.save_upload(io.BytesIO(data), len(data))[0], None)                    # no passphrase
                self.assertIn("Could not decrypt", tp.save_upload(io.BytesIO(data), len(data), "wrong passphrase!!")[1])
                name, err = tp.save_upload(io.BytesIO(data), len(data), "a long passphrase 123")
                self.assertIsNone(err); self.assertEqual(gzip.decompress((Path(d) / name).read_bytes()), b"secret data")
                self.assertEqual(sorted(p.name for p in Path(d).iterdir() if p.name.startswith(".")), [], "temporary files left behind")
            finally: tp.SPOOL = old


class CspBinding(unittest.TestCase):
    NAME = re.compile(r'data-on-(?:click|change|keydown|mousemove|mouseleave|mouseover|mouseout)=\\?["\']([A-Za-z_][\w]*)')
    def test_copies_are_identical_and_use_no_window_lookup(self):
        files = sorted(ROOT.glob("*/static/csp-bind.js")); self.assertEqual(len(files), 8)
        ref = files[0].read_text()
        for f in files:
            self.assertEqual(f.read_text(), ref, f)
        self.assertNotRegex(ref, r"window\s*\[")
        self.assertIn("cspRegister", ref)
    def test_every_handler_used_in_a_module_is_registered_there(self):
        for d in sorted(ROOT.glob("*/static")):
            js = [f for f in d.glob("*.js") if f.name != "csp-bind.js"]
            used = set()
            for f in list(d.glob("*.html")) + js: used |= set(self.NAME.findall(f.read_text()))
            if not used: continue
            reg = ",".join(m for f in js for m in re.findall(r"cspRegister\(\{([^}]*)\}\)", f.read_text()))
            names = {n.strip() for n in reg.split(",") if n.strip()}
            self.assertFalse(used - names, f"{d.parent.name}: handlers not registered: {sorted(used - names)}")


class NginxSnippet(unittest.TestCase):
    CONF = (ROOT / "etc/nginx/snippets/labtower-site.conf").read_text()
    def test_no_third_party_sources_in_csp(self):
        csp = re.search(r'Content-Security-Policy "([^"]*)"', self.CONF).group(1)
        self.assertNotIn("googleapis", csp); self.assertNotIn("gstatic", csp)
    def test_big_bodies_only_on_the_upload_route(self):
        blocks = re.findall(r"location ([^{]*)\{(.*?)\n\}", self.CONF, re.S)
        big = [loc.strip() for loc, body in blocks if "200m" in body]
        self.assertEqual(big, ["= /admin/api/teleporter/upload"])
    def test_every_module_login_is_rate_limited(self):
        for m in ("wol", "nut", "admin", "net", "pve", "nas", "dns", "wan", "overview"):
            with self.subTest(module=m): self.assertRegex(self.CONF, r"location = /%s/api/login \{[^}]*zone=labtower_login" % m)


class DnsPinning(unittest.TestCase):
    """verify_tls=false pins the certificate fingerprint on first use and refuses a different one."""
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.m = support.load("dns-monitor/server.py")
        cls.srvs = []
    @classmethod
    def tearDownClass(cls):
        for s in cls.srvs: s.shutdown(); s.server_close()
        shutil.rmtree(cls.d, ignore_errors=True)
    def _serve(self, tag):
        crt, key = f"{self.d}/{tag}.crt", f"{self.d}/{tag}.key"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", crt, "-days", "2", "-subj", f"/CN={tag}"], check=True, capture_output=True)
        class H(BaseHTTPRequestHandler):
            def do_GET(s):
                b = b'{"ok":1}'; s.send_response(200); s.send_header("Content-Length", str(len(b))); s.end_headers(); s.wfile.write(b)
            def log_message(s, *a): pass
        srv = HTTPServer(("127.0.0.1", 0), H)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(crt, key)
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        threading.Thread(target=srv.serve_forever, daemon=True).start(); self.srvs.append(srv)
        return srv.server_address[1]
    @unittest.skipUnless(shutil.which("openssl"), "openssl not installed")
    def test_pin_is_learned_then_enforced(self):
        m = self.m
        port = self._serve("a")
        m.DATA_FILE = Path(self.d) / "dns.json"
        cfg = m.validate({"name": "n", "url": f"https://127.0.0.1:{port}", "verify_tls": False, "password": "p"})
        cfg["id"] = "id1"; m.save_servers([dict(cfg)])
        self.assertEqual(m._req(cfg, "GET", "/")[0], 200)
        pin = m.load_servers()[0]["tls_pin"]; self.assertRegex(pin, r"^[0-9a-f]{64}$")
        port2 = self._serve("b")                                              # another certificate at the "same" server
        cfg2 = dict(m.load_servers()[0]); cfg2["url"] = f"https://127.0.0.1:{port2}"
        with self.assertRaises(m.DnsError) as cm: m._req(cfg2, "GET", "/")
        self.assertIn("changed", str(cm.exception))
        again = m.validate({"name": "n", "url": cfg["url"], "verify_tls": False}, m.load_servers()[0])
        self.assertEqual(again["tls_pin"], "", "saving the server again forgets the pin")
    def test_form_cannot_set_the_pin(self):
        cfg = self.m.validate({"name": "n", "url": "https://192.0.2.1", "verify_tls": False, "tls_pin": "a" * 64})
        self.assertEqual(cfg["tls_pin"], "")


class TeleporterScript(unittest.TestCase):
    SRC = (ROOT / "scripts/teleporter.sh").read_text()
    def test_untrusted_archive_is_opened_as_the_service_user(self):
        self.assertIn('as_service tar -xzf -', self.SRC)
        self.assertIn("in_dir_as_service", self.SRC)
        self.assertNotRegex(self.SRC, r"\n\s*tar -xzf \"\$1\"")
        self.assertNotRegex(self.SRC, r"python3 -I - \"\$1\" <<")
    def test_bash_syntax(self):
        self.assertEqual(subprocess.run(["bash", "-n", str(ROOT / "scripts/teleporter.sh")]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
