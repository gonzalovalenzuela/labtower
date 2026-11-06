"""NAS Monitor: certificados TLS (puertos por defecto y validación, lectura real con openssl, niveles, alertas, eventos y textos).
EN: NAS Monitor: TLS certificates (default ports and validation, real read with openssl, levels, alerts, events and texts)."""
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from tests import support

m = support.load("nas-monitor/server.py")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "auth"))
import certinfo

SYN = {"type": "synology", "name": "NAS", "host": "192.0.2.20", "version": "2c", "community": "public"}
TN = {"type": "truenas", "name": "TN", "host": "192.0.2.21", "user": "ro", "api_key": "k" * 20}
OMV = {"type": "omv", "name": "OMV", "host": "192.0.2.22", "user": "admin", "password": "secret", "https": False, "port": 80}


class Options(unittest.TestCase):
    def test_defaults_per_type(self):
        c = m.validate(dict(SYN)); self.assertEqual((c["cert_ports"], c["cert_warn"], c["cert_crit"]), ([5001], 14, 3))
        self.assertEqual(m.validate(dict(TN))["cert_ports"], [443])
        self.assertEqual(m.validate(dict(OMV))["cert_ports"], [])
        self.assertEqual(m.cert_ports({"type": "synology"}), [5001])           # a NAS saved before this change
        self.assertEqual(m.public({"id": "x", "type": "truenas", "port": 8443, "https": True})["cert_ports"], [8443])

    def test_parse_keep_and_reject(self):
        c = m.validate({**SYN, "cert_ports": "5001, 443 443", "cert_warn": "30", "cert_crit": 7})
        self.assertEqual((c["cert_ports"], c["cert_warn"], c["cert_crit"]), ([5001, 443], 30, 7))
        self.assertEqual(m.validate({**SYN, "cert_ports": ""})["cert_ports"], [])
        kept = m.validate({"name": "NAS2"}, current=c)
        self.assertEqual((kept["cert_ports"], kept["cert_warn"], kept["cert_crit"]), ([5001, 443], 30, 7))
        self.assertEqual(m.cert_thr({"cert_warn": 3, "cert_crit": 5}), (14, 3))                # broken stored values fall back
        for bad in ({"cert_ports": "0"}, {"cert_ports": "70000"}, {"cert_ports": "abc"}, {"cert_ports": [True]},
                    {"cert_ports": list(range(1, 10))}, {"cert_warn": 0}, {"cert_warn": 91}, {"cert_crit": True}, {"cert_warn": 5, "cert_crit": 5}, {"cert_crit": 20}, {"cert_ports": {"a": 1}}):
            with self.assertRaises(ValueError, msg=bad): m.validate({**SYN, **bad})


class Levels(unittest.TestCase):
    def setUp(self): m._CERTS.clear()
    def tearDown(self): m._CERTS.clear()

    def test_level_days_and_alerts(self):
        now = 1_700_000_000
        n = {"id": "a", "name": "NAS", "type": "synology", "cert_ports": [5001, 443, 6690, 8443], "cert_warn": 14, "cert_crit": 3}
        m._CERTS["a"] = {"ts": now, "sig": None, "list": [
            {"port": 5001, "cn": "nas.example.lan", "issuer": "Example CA", "not_after": now + 10 * 86400 + 60, "self_signed": False},
            {"port": 443, "cn": "nas.example.lan", "issuer": "Example CA", "not_after": now - 3600, "self_signed": False},
            {"port": 6690, "error": "timed out"},
            {"port": 8443, "cn": "nas.example.lan", "issuer": "Example CA", "not_after": now + 3 * 86400 + 60, "self_signed": False}]}
        certs, al = m.cert_view(n, now)
        self.assertEqual([(c["lv"], c["days"]) for c in certs], [("warn", 10), ("exp", -1), ("err", None), ("crit", 3)])
        self.assertEqual([(a["lv"], a["type"], a["item"]) for a in al],
                         [("warn", "cert", "TLS :5001"), ("crit", "cert_exp", "TLS :443"), ("warn", "cert_err", "TLS :6690"), ("crit", "cert", "TLS :8443")])
        self.assertEqual(m.cert_level({"not_after": now + 40 * 86400}, (14, 3), now), ("ok", 40))
        self.assertEqual(m.cert_view({"id": "none"}), ([], []))

    def test_events_on_change_only(self):
        seen, states = [], {}
        def changed(k, v):
            old = states.get(k); states[k] = v
            return None if old is None or old == v else (old, v)
        n = {"id": "a", "name": "NAS", "type": "synology"}
        with mock.patch.object(m.auth, "record_event", lambda mod, lv, tx, kind, **kw: seen.append((lv, kind, kw))), \
             mock.patch.object(m.auth, "state_changed", changed):
            now = 1_700_000_000
            for exp in (now + 40 * 86400, now + 40 * 86400, now + 5 * 86400, now + 2 * 86400, now - 60, now + 90 * 86400):
                m._CERTS["a"] = {"ts": now, "sig": None, "list": [{"port": 5001, "not_after": exp}]}
                m._cert_events(n, m.cert_view(n, now)[0])
            m._CERTS["a"] = {"ts": now, "sig": None, "list": [{"port": 5001, "error": "refused"}]}
            m._cert_events(n, m.cert_view(n, now)[0])                           # an error raises nothing
        self.assertEqual([(lv, k) for lv, k, _ in seen], [("warn", "nas_cert"), ("crit", "nas_cert"), ("crit", "nas_certexp"), ("info", "nas_cert_ok")])
        self.assertEqual((seen[0][2], seen[1][2]["d"]), ({"n": "NAS", "p": 5001, "d": 5}, 2))

    def test_due_once_a_day(self):
        n = {"id": "b", "name": "NAS", "type": "synology", "host": "192.0.2.20", "cert_ports": [5001]}
        calls = []
        with mock.patch.object(m, "read_cert", lambda h, p, t: calls.append(p) or {"port": p, "error": "refused"}):
            now = 1_700_000_000
            self.assertTrue(m.check_certs_due(n, now))
            self.assertFalse(m.check_certs_due(n, now + 3599))                                  # a failed port waits an hour
            self.assertTrue(m.check_certs_due(n, now + 3600))
            self.assertTrue(m.check_certs_due({**n, "cert_ports": [443]}, now + 3601))          # ports changed: at once
            self.assertFalse(m.check_certs_due({**n, "cert_ports": [443]}, now + 3605, force=True))   # forced, but checked 4 s ago
            self.assertTrue(m.check_certs_due({**n, "cert_ports": [443]}, now + 3612, force=True))
        with mock.patch.object(m, "read_cert", lambda h, p, t: calls.append(p) or {"port": p, "not_after": now + 99 * 86400}):
            m.check_certs_due(n, now + 7300)
            self.assertFalse(m.check_certs_due(n, now + 7300 + 86399))                          # all fine: once a day
            self.assertTrue(m.check_certs_due(n, now + 7300 + 86400))
        self.assertEqual((calls, m.CERT_EVERY, m.CERT_RETRY), ([5001, 5001, 443, 443, 5001, 5001], 86400, 3600))


@unittest.skipUnless(shutil.which("openssl"), "openssl not installed")
class RealTls(unittest.TestCase):
    """A real self-signed certificate served on 127.0.0.1: read without validating it."""
    @classmethod
    def setUpClass(cls):
        d = Path(tempfile.mkdtemp()); cls.dir = d; key, crt = d / "k.pem", d / "c.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "20", "-subj", "/O=Example/CN=nas.example.lan",
                        "-keyout", str(key), "-out", str(crt)], check=True, capture_output=True, timeout=60)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(str(crt), str(key))
        cls.sock = socket.socket(); cls.sock.bind(("127.0.0.1", 0)); cls.sock.listen(4); cls.port = cls.sock.getsockname()[1]
        def serve():
            while True:
                try: c, _ = cls.sock.accept()
                except OSError: return
                try:
                    with ctx.wrap_socket(c, server_side=True): pass
                except (OSError, ssl.SSLError): pass
        threading.Thread(target=serve, daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.sock.close(); shutil.rmtree(cls.dir, ignore_errors=True)

    def test_read(self):
        with mock.patch.object(m.auth, "valid_target", lambda h, **k: True):
            c = m.read_cert("127.0.0.1", self.port, 5)
        self.assertNotIn("error", c, c)
        self.assertEqual((c["cn"], c["issuer"], c["self_signed"]), ("nas.example.lan", "Example", True))
        self.assertAlmostEqual(c["not_after"], time.time() + 20 * 86400, delta=2 * 86400)

    def test_loopback_refused_and_closed_port(self):
        with mock.patch.object(m.auth, "valid_target", lambda h, **k: not h.startswith("127.")):     # support.py relaxes it for every test
            self.assertEqual(m.read_cert("127.0.0.1", self.port, 3)["error"], "address not allowed")
        s = socket.socket(); s.bind(("127.0.0.1", 0)); closed = s.getsockname()[1]; s.close()
        with mock.patch.object(m.auth, "valid_target", lambda h, **k: True):
            self.assertTrue(m.read_cert("127.0.0.1", closed, 3)["error"])


class CheckNow(unittest.TestCase):
    """POST /api/nas/<id>/certs: execute permission, 404 for an unknown NAS, and it returns the certificates read."""
    @classmethod
    def setUpClass(cls):
        m.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.ex, cls.ro = support.make_user("cex", {"nas": "execute"}), support.make_user("cro", {"nas": "readonly"})
        cls.srv = support.Server(m.H)
    @classmethod
    def tearDownClass(cls): cls.srv.close(); m.save_nas([]); m._CERTS.clear()

    def test_check_now(self):
        m.save_nas([{**m.validate(dict(SYN)), "id": "n1"}]); m._CERTS.clear()
        c = self.srv.call
        self.assertEqual(c("POST", "/api/nas/n1/certs", {})[0], 401)
        self.assertEqual(c("POST", "/api/nas/n1/certs", {}, token=self.ro)[0], 403)
        self.assertEqual(c("POST", "/api/nas/zz/certs", {}, token=self.ex)[0], 404)
        far = int(time.time()) + 2 * 86400
        with mock.patch.object(m, "read_cert", lambda h, p, t: {"port": p, "cn": "nas.example.lan", "issuer": "Example CA", "not_after": far, "self_signed": False}):
            s, j = c("POST", "/api/nas/n1/certs", {}, token=self.ex)
        self.assertEqual(s, 200, j)
        self.assertEqual([(x["port"], x["lv"]) for x in j["certs"]], [(5001, "crit")])
        self.assertEqual([a["type"] for a in j["alerts"]], ["cert"])


class Parser(unittest.TestCase):
    def test_junk(self):
        for junk in (b"", b"\x30", b"\x30\x84\xff\xff\xff\xff", b"\x30\x03\x02\x01\x01"):
            self.assertIsNone(certinfo.parse(junk)); self.assertIsNone(certinfo.not_after(junk))


class Texts(unittest.TestCase):
    def test_alert_and_event_texts(self):
        nas = (ROOT / "nas-monitor/static/app.js").read_text()
        ov = (ROOT / "overview/static/app.js").read_text()
        for k in ("cert:(i,v)=>", "cert_exp:i=>", "cert_err:(i,v)=>"): self.assertEqual(nas.count(k), 2, k)
        for k in ("cert:'certificate expires soon'", "cert:'el certificado vence pronto'", "cert:' d'"): self.assertIn(k, ov)
        for k in ("cert_exp:'", "cert_err:'", "nas_cert:'", "nas_certexp:'", "nas_cert_ok:'"): self.assertEqual(ov.count(k), 2, k)
        html = (ROOT / "nas-monitor/static/index.html").read_text()
        self.assertIn('id="f-cert-ports"', html); self.assertIn('id="f-cert-warn"', html); self.assertIn('id="f-cert-crit"', html)


if __name__ == "__main__":
    unittest.main()
