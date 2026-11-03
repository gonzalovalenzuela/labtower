"""Revisión de seguridad: cuerpo vacío en POST, URLs https de WAN que no pueden apuntar a esta máquina, y esc() con comilla simple."""
import io, re, unittest
from pathlib import Path
from tests import support

ROOT = Path(__file__).resolve().parent.parent
wan = support.load("wan-monitor/server.py")
SERVERS = ["nas-monitor/server.py", "net-monitor/server.py", "nut-monitor/server.py", "overview/server.py",
           "proxmox-monitor/server.py", "vpn-monitor/server.py", "wol-console/server.py", "auth/admin_panel.py"]


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


class WanUrls(unittest.TestCase):
    def setUp(self):                      # the harness relaxes valid_target for its local fake servers: use the real one here
        self._vt = wan.auth.valid_target; wan.auth.valid_target = support.real_valid_target
    def tearDown(self): wan.auth.valid_target = self._vt

    def test_https_url_refuses_this_machine_and_link_local(self):
        for bad in ("https://127.0.0.1/x", "https://localhost/x", "https://169.254.169.254/x", "https://[::1]/x", "http://example.com/x"):
            with self.assertRaises(ValueError, msg=bad): wan._https_url(bad, "url")
        self.assertEqual(wan._https_url("https://speed.cloudflare.com/__down", "url"), "https://speed.cloudflare.com/__down")


class Escape(unittest.TestCase):
    def test_esc_escapes_single_quotes(self):
        for rel in ("auth/static/app.js", "net-monitor/static/app.js", "wol-console/static/app.js"):
            m = re.search(r"function esc\(s\)[^\n]*", (ROOT / rel).read_text())
            self.assertIn("&#39;", m.group(0), rel)


if __name__ == "__main__":
    unittest.main()
