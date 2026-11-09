"""WAN Monitor: el certificado del router se fija (TOFU, como NAS, DNS, Net y Proxmox). La primera conexión HTTPS aprende la huella;
si luego cambia, se corta antes de enviar usuario o contraseña. La huella nunca viene del formulario ni se devuelve al navegador, y guardar
los ajustes del router la borra para volver a aprenderla.
EN: WAN Monitor: the router certificate is pinned (TOFU, like NAS, DNS, Net and Proxmox). The first HTTPS connection learns the fingerprint;
if it later changes, the connection is dropped before the user or password is sent. The fingerprint never comes from the form nor goes back
to the browser, and saving the router settings clears it so it is learned again."""
import hashlib
import http.server
import json
import shutil
import ssl
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from tests import support

m = support.load("wan-monitor/server.py")
rtr = m.rtr
FP = "ab" * 32


@unittest.skipUnless(shutil.which("openssl"), "openssl not installed")
class Pinning(unittest.TestCase):
    """De punta a punta sobre TLS con un certificado autofirmado. / EN: End to end over TLS with a self-signed certificate."""
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", f"{cls.dir}/k", "-out", f"{cls.dir}/c.pem",
                        "-days", "2", "-subj", "/CN=router"], capture_output=True, check=True)
        der = subprocess.run(["openssl", "x509", "-in", f"{cls.dir}/c.pem", "-outform", "DER"], capture_output=True, check=True).stdout
        cls.fp = hashlib.sha256(der).hexdigest()
        cls.hits = []
        hits = cls.hits
        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(h):
                hits.append((h.path, h.headers.get("Authorization")))
                h.send_response(200); h.send_header("Content-Type", "text/plain"); h.end_headers(); h.wfile.write(b"ok")
            log_message = lambda *a: None
        cls.srv = http.server.HTTPServer(("127.0.0.1", 0), H); cls.srv.handle_error = lambda *a: None
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(f"{cls.dir}/c.pem", f"{cls.dir}/k")
        cls.srv.socket = ctx.wrap_socket(cls.srv.socket, server_side=True)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"https://127.0.0.1:{cls.srv.server_address[1]}"
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); shutil.rmtree(cls.dir, ignore_errors=True)
    def setUp(self): self.hits.clear()

    def test_first_connection_learns(self):
        got = []
        st, body = rtr.Http(self.base, basic=("admin", "secret"), learn=got.append).request("/x")
        self.assertEqual((st, body, got), (200, "ok", [self.fp]))
        self.assertEqual(len(self.hits), 1)

    def test_same_fingerprint_works(self):
        self.assertEqual(rtr.Http(self.base, pin=self.fp).request("/y")[0], 200)

    def test_changed_certificate_sends_nothing(self):
        with self.assertRaises(rtr.RouterError) as e:
            rtr.Http(self.base, basic=("admin", "secret"), pin=FP).request("/login")
        self.assertIn("certificate changed", str(e.exception))
        self.assertEqual(self.hits, [])                                           # neither the path nor the password reached the server


class Config(unittest.TestCase):
    def setUp(self):
        self.old = m.DATA_FILE
        m.DATA_FILE = Path(tempfile.mkdtemp()) / "config.json"
        cfg = m.validate({"router": {"enabled": True, "password": "p", "host": "192.0.2.1", "https": True, "port": 443}}, resolve=False)
        m.save_config(cfg)
    def tearDown(self): m.DATA_FILE = self.old

    def test_learned_kept_and_hidden(self):
        m.learn_router_pin({"addr": "192.0.2.1:443", "fp": FP})
        cfg = m.load_config()
        self.assertEqual(cfg["router"]["tls_pin"], {"addr": "192.0.2.1:443", "fp": FP})
        self.assertNotIn("tls_pin", json.dumps(m.public_config(cfg)))
        self.assertEqual(rtr.pin_for(cfg["router"], "192.0.2.1"), FP)
        self.assertIsNone(rtr.pin_for(cfg["router"], "192.0.2.9"))              # another address learns its own

    def test_never_from_the_form_and_saving_clears_it(self):
        m.learn_router_pin({"addr": "192.0.2.1:443", "fp": FP})
        cfg = m.validate({"router": {"tls_pin": {"addr": "192.0.2.1:443", "fp": "cd" * 32}}}, m.load_config(), resolve=False)
        self.assertNotIn("tls_pin", cfg["router"])
        m.save_config(cfg)
        self.assertNotIn("tls_pin", m.load_config()["router"])

    def test_bad_pins_are_ignored(self):
        for bad in (None, "x", {"addr": "a", "fp": "zz"}, {"addr": "", "fp": FP}, {"addr": "a" * 400, "fp": FP}):
            m.learn_router_pin(bad)
        self.assertNotIn("tls_pin", m.load_config()["router"])

    def test_learning_does_not_replace_a_pin(self):
        m.learn_router_pin({"addr": "192.0.2.1:443", "fp": FP})
        m.learn_router_pin({"addr": "192.0.2.1:443", "fp": "cd" * 32})
        self.assertEqual(m.load_config()["router"]["tls_pin"]["fp"], FP)


class Code(unittest.TestCase):
    def test_router_thread_learns_and_test_checks(self):
        src = (Path(m.__file__).parent / "server.py").read_text(encoding="utf-8")
        self.assertIn("res = rtr.check(rc, host, learn=learn_router_pin)", src)
        self.assertIn('if pin: rc["tls_pin"] = pin', src)
        self.assertNotIn("verify=False", (Path(m.__file__).parent / "router.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
