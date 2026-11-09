"""Revisión de seguridad: cuerpo vacío en POST, URLs https de WAN que no pueden apuntar a esta máquina, y esc() con comilla simple."""
import io
import re
import unittest
from pathlib import Path

from tests import support

ROOT = Path(__file__).resolve().parent.parent
wan = support.load("wan-monitor/server.py")
SERVERS = ["nas-monitor/server.py", "net-monitor/server.py", "nut-monitor/server.py", "overview/server.py",
           "proxmox-monitor/server.py", "vpn-monitor/server.py", "uptime-monitor/server.py", "wol-console/server.py", "auth/admin_panel.py"]


class EmptyBody(unittest.TestCase):
    def test_post_without_body_is_an_empty_object_everywhere(self):
        for rel in SERVERS:
            src = (ROOT / rel).read_text()
            self.assertIn("json.loads(self.rfile.read(n)) if n else {}", src, rel)

    def test_logout_style_post_gets_a_dict(self):
        m = support.load("net-monitor/server.py")
        h = m.H.__new__(m.H)
        class Hd(dict):
            def get(self, k, d=None): return super().get(k, d)
        h.headers = Hd({"Content-Length": "0"}); h.rfile = io.BytesIO(b"")
        self.assertEqual(h._body(), {})
        h.headers = Hd({"Content-Length": "9"}); h.rfile = io.BytesIO(b"not json!!")
        self.assertIsNone(h._body())


class UnsupportedMethod(unittest.TestCase):
    """HEAD (u otro método sin manejador) recibe 501; antes log_message lanzaba ValueError y la conexión se cortaba sin respuesta.
    EN: HEAD (or any method without a handler) gets 501; log_message used to raise ValueError and the connection was dropped."""
    def test_head_gets_501_everywhere(self):
        import http.client
        for rel in SERVERS + ["dns-monitor/server.py", "wan-monitor/server.py"]:
            with self.subTest(module=rel):
                srv = support.Server(support.load(rel).H)
                try:
                    c = http.client.HTTPConnection("127.0.0.1", srv.port, timeout=10); c.request("HEAD", "/")
                    self.assertEqual(c.getresponse().status, 501); c.close()
                finally: srv.close()

class WanUrls(unittest.TestCase):
    def setUp(self):                      # the harness relaxes valid_target for its local fake servers: use the real one here
        self._vt = wan.auth.valid_target; wan.auth.valid_target = support.real_valid_target
    def tearDown(self): wan.auth.valid_target = self._vt

    def test_https_url_refuses_this_machine_and_link_local(self):
        for bad in ("https://127.0.0.1/x", "https://localhost/x", "https://169.254.169.254/x", "https://[::1]/x", "http://example.com/x"):
            with self.assertRaises(ValueError, msg=bad): wan._https_url(bad, "url")
        self.assertEqual(wan._https_url("https://speed.cloudflare.com/__down", "url"), "https://speed.cloudflare.com/__down")


class NutTarget(unittest.TestCase):
    def test_loopback_allowed_only_when_asked(self):
        v = support.real_valid_target
        self.assertFalse(v("127.0.0.1")); self.assertTrue(v("127.0.0.1", allow_loopback=True)); self.assertTrue(v("localhost", allow_loopback=True))
        for bad in ("0.0.0.0", "169.254.169.254", "-x"):  # nosec B104 - test data
            self.assertFalse(v(bad, allow_loopback=True), bad)


class RpcBudget(unittest.TestCase):
    def test_a_module_cannot_flood_events_and_audit(self):
        authrpc = support.load("auth/authrpc.py")
        svc = authrpc.Service(support.auth, identify=lambda uid: "wol")
        got = [svc._budget("wol") for _ in range(authrpc.WRITE_LIMIT + 5)]
        self.assertTrue(all(got[:authrpc.WRITE_LIMIT])); self.assertFalse(any(got[authrpc.WRITE_LIMIT:]))
        self.assertTrue(svc._budget("nut"))                          # each module has its own budget


class Escape(unittest.TestCase):
    def test_esc_escapes_single_quotes(self):
        for rel in ("auth/static/app.js", "net-monitor/static/app.js", "wol-console/static/app.js"):
            m = re.search(r"function esc\(s\)[^\n]*", (ROOT / rel).read_text())
            self.assertIn("&#39;", m.group(0), rel)


if __name__ == "__main__":
    unittest.main()
