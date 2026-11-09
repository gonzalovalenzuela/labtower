"""Switch Monitor: un inicio de sesión nuevo parte sin cookies viejas. Si el switch entrega la sesión con otro nombre o ruta, la cookie anterior
(también la guardada en disco) viajaba junto a la nueva y el switch volvía a responder con su página de login («SessionExpired»).
EN: Switch Monitor: a new login starts without old cookies. If the switch hands out the session under another name or path, the previous
cookie (also the one stored on disk) travelled with the new one and the switch answered with its login page again ("SessionExpired")."""
import http.cookiejar
import json
import unittest
from http.server import BaseHTTPRequestHandler

from tests import support
from tests.test_switches import serve, zx_site

sw = support.load("net-monitor/switches.py")
STATE = {"tick": 0, "temp": 60, "new_err": 0, "expire_once": False, "hits": []}


class OneSession(BaseHTTPRequestHandler):
    """Switch que da la sesión «s2» al iniciar sesión y lee la PRIMERA cookie que recibe. / EN: Hands out "s2" on login and reads the FIRST cookie."""
    def log_message(self, *a): pass
    def do_GET(self):
        path = self.path.lstrip("/").split("?")[0]; STATE["hits"].append(path)
        ck = None
        if path == "authorize": body, ck = "ok", "SID=s2; Path=/"
        else:
            first = (self.headers.get("Cookie") or "").split(";")[0].strip()
            body = json.dumps(zx_site(STATE).get(path, {})) if first == "SID=s2" else "<script>location='login.html'</script>"
        b = body.encode(); self.send_response(200); self.send_header("Content-Length", str(len(b)))
        if ck: self.send_header("Set-Cookie", ck)
        self.end_headers(); self.wfile.write(b)


class Relogin(unittest.TestCase):
    def setUp(self):
        STATE["hits"].clear()
        self.srv, self.host = serve(OneSession)
    def tearDown(self): self.srv.shutdown(); self.srv.server_close()

    def stale(self, d):
        # Cookie vieja de otra ruta que el cliente envía primero. / EN: Old cookie under another path, sent first by the client.
        d.jar.set_cookie(http.cookiejar.Cookie(0, "SID", "old", None, False, self.host.split(":")[0], False, False, "/status.json", True,
                                               False, None, False, None, None, {}))
        d.logged_in = True

    def test_old_cookie_does_not_break_the_new_session(self):
        d = sw.ZXDriver("zx", self.host, "admin", "pw", gap=0)
        self.stale(d)
        snap = d.snapshot(with_macs=False)                                     # used to raise SessionExpired
        self.assertEqual(snap["system"]["model"], "ZX310S-8T2XS")
        self.assertEqual(STATE["hits"].count("authorize"), 1)
        self.assertEqual([c.value for c in d.jar], ["s2"])

    def test_message_explains_the_single_session(self):
        self.assertIn("another LabTower or a browser", str(sw.SessionExpired()))


if __name__ == "__main__":
    unittest.main()
