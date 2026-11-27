"""DNS Monitor: sondeo de DNS de salida cifrados (DoT y DoH) contra servidores TLS locales con un certificado propio.
EN: DNS Monitor: probing encrypted upstreams (DoT and DoH) against local TLS servers with their own certificate."""
import shutil
import socket
import ssl
import struct
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from tests import support

m = support.load("dns-monitor/server.py")
dnsq = m.dnsq
HOST = "dns.example.lan"


def answer(q, ip="192.0.2.7"):
    """A response to query `q` with one A record."""
    return q[:2] + struct.pack(">HHHHH", 0x8180, 1, 1, 0, 0) + q[12:] + b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 60, 4) + socket.inet_aton(ip)


@unittest.skipUnless(shutil.which("openssl"), "openssl not installed")
class Encrypted(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = Path(tempfile.mkdtemp()); cls.crt, key, conf = d / "c.pem", d / "k.pem", d / "x.cnf"
        conf.write_text(f"[req]\ndistinguished_name=dn\nx509_extensions=v3\nprompt=no\n[dn]\nCN={HOST}\n[v3]\nsubjectAltName=DNS:{HOST}\n")
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2", "-config", str(conf),
                        "-keyout", str(key), "-out", str(cls.crt)], check=True, capture_output=True, timeout=60)
        srv_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); srv_ctx.load_cert_chain(str(cls.crt), str(key))
        # DoT: a 2-byte length, then the message. / DoT: 2-byte length, then the message.
        cls.dot = socket.socket(); cls.dot.bind(("127.0.0.1", 0)); cls.dot.listen(4); cls.dot_port = cls.dot.getsockname()[1]
        def serve():
            while True:
                try: c, _ = cls.dot.accept()
                except OSError: return
                try:
                    with srv_ctx.wrap_socket(c, server_side=True) as s:
                        n = struct.unpack(">H", s.recv(2))[0]; q = s.recv(n); a = answer(q); s.sendall(struct.pack(">H", len(a)) + a)
                except (OSError, ssl.SSLError, struct.error): pass
        threading.Thread(target=serve, daemon=True).start()
        # DoH: POST application/dns-message.
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_POST(self):
                q = self.rfile.read(int(self.headers["Content-Length"]))
                if self.path != "/dns-query" or self.headers["Content-Type"] != "application/dns-message": self.send_response(415); self.end_headers(); return
                a = answer(q); self.send_response(200); self.send_header("Content-Type", "application/dns-message"); self.send_header("Content-Length", str(len(a)))
                self.end_headers(); self.wfile.write(a)
        cls.doh = ThreadingHTTPServer(("127.0.0.1", 0), H); cls.doh.socket = srv_ctx.wrap_socket(cls.doh.socket, server_side=True)
        cls.doh_port = cls.doh.server_address[1]
        threading.Thread(target=cls.doh.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls): cls.dot.close(); cls.doh.shutdown()

    def trusted(self):
        return mock.patch.object(dnsq, "_tls_ctx", lambda: ssl.create_default_context(cafile=str(self.crt)))

    def test_dot(self):
        with self.trusted(): r = dnsq.query_tls("127.0.0.1", HOST, self.dot_port, "example.com")
        self.assertTrue(r["ok"], r); self.assertEqual(r["answers"], [{"type": "A", "value": "192.0.2.7"}]); self.assertIn("hs", r)
        r = dnsq.query_tls("127.0.0.1", HOST, self.dot_port, "example.com")                        # not trusted by the system CAs
        self.assertFalse(r["ok"]); self.assertTrue(r["error"].startswith(("certificate", "TLS")), r)
        with self.trusted(): r = dnsq.query_tls("127.0.0.1", "other.example.lan", self.dot_port, "example.com")   # wrong name
        self.assertFalse(r["ok"])

    def test_doh(self):
        with self.trusted(): r = dnsq.query_https("127.0.0.1", HOST, self.doh_port, "/dns-query", "example.com")
        self.assertTrue(r["ok"], r); self.assertEqual(r["answers"][0]["value"], "192.0.2.7")
        with self.trusted(): r = dnsq.query_https("127.0.0.1", HOST, self.doh_port, "/other", "example.com")
        self.assertEqual(r, {"ok": False, "error": "HTTP 415"})

    def test_unreachable(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        self.assertFalse(dnsq.query_tls("127.0.0.1", HOST, port, "example.com", timeout=1)["ok"])


class Targets(unittest.TestCase):
    def test_probe_target(self):
        res = lambda h: "192.0.2.53"
        t = lambda ip, port=None, **k: m.probe_target({"ip": ip, "port": port, **k}, res)
        self.assertEqual(t("https://dns10.quad9.net:443/dns-query"), ("https", "192.0.2.53", "dns10.quad9.net", 443, "/dns-query"))
        self.assertEqual(t("tls://dns.google"), ("tls", "192.0.2.53", "dns.google", 853, ""))
        self.assertEqual(t("1.1.1.1:53"), ("udp", "192.0.2.53", "1.1.1.1", 53, ""))
        self.assertEqual(t("127.0.0.1", 5335)[3], 5335)                                         # high UDP port allowed
        for bad in ("quic://dns.adguard-dns.com", "h3://dns.google/dns-query", "sdns://AQcAAAAAAAAA", "tls://dns.google:80", "1.1.1.1:99"):
            self.assertIsNone(t(bad), bad)
        self.assertIsNone(t("tls://dns.google", old=True))                                     # removed from the configuration
        self.assertIsNone(m.probe_target({"ip": "tls://dns.google"}, lambda h: None))           # not resolvable or not allowed
        with mock.patch.object(m.auth, "valid_target", lambda h, **k: h != "192.0.2.9"):                # the address must pass valid_target
            self.assertIsNone(m._probe_ip("192.0.2.9")); self.assertEqual(m._probe_ip("192.0.2.1"), "192.0.2.1")


if __name__ == "__main__":
    unittest.main()
