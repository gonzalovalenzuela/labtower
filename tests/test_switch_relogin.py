"""Switch Monitor: un inicio de sesión nuevo parte sin cookies viejas. Si el switch entrega la sesión con otro nombre o ruta, la cookie anterior
(también la guardada en disco) viajaba junto a la nueva y el switch volvía a responder con su página de login («SessionExpired»).
EN: Switch Monitor: a new login starts without old cookies. If the switch hands out the session under another name or path, the previous
cookie (also the one stored on disk) travelled with the new one and the switch answered with its login page again ("SessionExpired")."""
import http.cookiejar
import json
import os
import tempfile
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

    def test_forget_drops_cookies_and_the_stored_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "s.cookies")
            d = sw.ZXDriver("zx", self.host, "admin", "pw", gap=0, session_file=f)
            d.snapshot(with_macs=False); self.assertTrue(os.path.exists(f))
            d.forget()
            self.assertEqual((len(d.jar), d.logged_in, os.path.exists(f)), (0, False, False))
            d.forget()                                                          # no file: no error

    def test_message_explains_the_single_session(self):
        self.assertIn("another LabTower or a browser", str(sw.SessionExpired()))


class LoopStartsOver(unittest.TestCase):
    """El monitoreo, ante un SessionExpired que su propio reinicio de sesión no arregló, vuelve a leer con un driver nuevo (como «Probar»).
    EN: On a SessionExpired its own relogin did not fix, polling reads again with a new driver (like "Test")."""
    def test_session_expired_builds_a_new_driver(self):
        tmp = tempfile.mkdtemp()
        m = sw.Manager(tmp, hooks={})
        m.poll_seconds = lambda: 0
        built, forgot, ingested = [], [], []
        w = sw._Worker()

        class Stuck:                                                            # the first driver keeps getting the login page
            def snapshot(self, with_macs): raise sw.SessionExpired()
            def forget(self): forgot.append(1)
        class Good:
            def snapshot(self, with_macs): w.stop = True; return {"ok": 1}
        def build(cfg, d):
            built.append(d); return Stuck() if len(built) == 1 else Good()
        old = sw.build_driver
        sw.build_driver = build
        m._ingest = lambda sid, cfg, snap, macs: ingested.append(snap)
        try: m._loop("s1", {"name": "zx", "driver": "zx"}, w, 0)
        finally: sw.build_driver = old
        self.assertEqual((len(built), forgot, ingested), (2, [1], [{"ok": 1}]))
        self.assertIn("SessionExpired", m.rec["s1"]["err"])

    def test_other_errors_keep_the_driver(self):
        m = sw.Manager(tempfile.mkdtemp(), hooks={})
        m.poll_seconds = lambda: 0
        built, w, n = [], sw._Worker(), [0]

        class Flaky:
            logged_in = True
            def snapshot(self, with_macs):
                n[0] += 1
                if n[0] == 1: raise OSError("timeout")
                w.stop = True; return {"ok": 1}
        def build(cfg, d):
            built.append(d); return Flaky()
        old = sw.build_driver
        sw.build_driver = build
        m._ingest = lambda *a: None
        try: m._loop("s1", {"name": "zx", "driver": "zx"}, w, 0)
        finally: sw.build_driver = old
        self.assertEqual(len(built), 1)


if __name__ == "__main__":
    unittest.main()
