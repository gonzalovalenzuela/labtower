"""2.1.3g: aviso de versión nueva a partir de las versiones publicadas."""
import json, os, tempfile, threading, time, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from tests.support import auth, load, make_user, Server, ADMIN

class Gh(BaseHTTPRequestHandler):
    body = {}; status = 200; hits = 0
    def do_GET(self):
        Gh.hits += 1
        self.send_response(Gh.status); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps(Gh.body).encode())
    def log_message(self, *a): pass

class Versions(unittest.TestCase):
    def test_ordering(self):
        k = auth.version_key
        self.assertTrue(k("2.1") < k("2.1.3") < k("2.1.3a") < k("2.1.3e") < k("2.1.3f") < k("v2.2"))
        self.assertIsNone(k("latest")); self.assertIsNone(k("")); self.assertIsNone(k("2.1.3-rc1"))

class Update(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gh = HTTPServer(("127.0.0.1", 0), Gh); threading.Thread(target=cls.gh.serve_forever, daemon=True).start()
        cls.saved = (auth.UPDATE_URL, auth.UPDATE_FILE)
        auth.UPDATE_URL = f"http://127.0.0.1:{cls.gh.server_address[1]}/x"
    @classmethod
    def tearDownClass(cls):
        cls.gh.shutdown(); auth.UPDATE_URL, auth.UPDATE_FILE = cls.saved
    def setUp(self):
        d = tempfile.mkdtemp(); auth.UPDATE_FILE = auth.Path(d) / "update.json"
        Gh.status = 200; Gh.hits = 0
        os.environ["LABTOWER_VERSION"] = "2.1.3e"
        self.addCleanup(lambda: os.environ.pop("LABTOWER_VERSION", None))
    def wait(self):
        for _ in range(100):
            if not auth._update_busy[0]: return
            time.sleep(0.05)
    def test_newer_release_is_reported(self):
        Gh.body = {"tag_name": "2.1.3f", "html_url": "https://github.com/gonzalovalenzuela/labtower/releases/tag/2.1.3f", "published_at": "2026-10-30T10:00:00Z", "name": "x"}
        auth.update_info(); self.wait()
        i = auth.update_info()
        self.assertTrue(i["newer"]); self.assertEqual(i["latest"], "2.1.3f"); self.assertEqual(i["published"], "2026-10-30"); self.assertEqual(i["error"], "")
        self.assertEqual(Gh.hits, 1)                                   # second call used the cache

    def test_same_or_older_is_not_newer(self):
        for tag in ("2.1.3e", "2.1.3", "2.1"):
            Gh.body = {"tag_name": tag, "html_url": "https://github.com/gonzalovalenzuela/labtower/releases/tag/x"}
            auth.UPDATE_FILE.unlink(missing_ok=True)
            auth.update_info(); self.wait()
            self.assertFalse(auth.update_info()["newer"], tag)

    def test_prerelease_draft_bad_tag_and_foreign_url(self):
        for b in ({"tag_name": "2.9", "prerelease": True}, {"tag_name": "2.9", "draft": True}, {"tag_name": "nightly"}):
            Gh.body = b; auth.UPDATE_FILE.unlink(missing_ok=True)
            auth.update_info(); self.wait()
            i = auth.update_info(); self.assertFalse(i["newer"]); self.assertTrue(i["error"])
        Gh.body = {"tag_name": "2.9", "html_url": "https://evil.example/x"}; auth.UPDATE_FILE.unlink(missing_ok=True)
        auth.update_info(); self.wait()
        self.assertTrue(auth.update_info()["url"].startswith(auth.RELEASE_PREFIX))

    def test_failure_keeps_last_answer_and_retries_later(self):
        Gh.body = {"tag_name": "2.1.3f", "html_url": auth.RELEASE_PREFIX + "releases/tag/2.1.3f"}
        auth.update_info(); self.wait()
        Gh.status = 500
        auth.update_info(force=True)                                   # within 30 s of the last check: ignored
        self.wait(); self.assertEqual(Gh.hits, 1)
        cur = json.loads(auth.UPDATE_FILE.read_text()); cur["checked"] -= 100; auth.UPDATE_FILE.write_text(json.dumps(cur))
        auth.update_info(force=True); self.wait()
        i = auth.update_info()
        self.assertTrue(i["error"]); self.assertEqual(i["latest"], "2.1.3f"); self.assertTrue(i["newer"])

    def test_can_be_turned_off(self):
        os.environ["LABTOWER_UPDATE_CHECK"] = "0"
        try:
            i = auth.update_info(force=True); self.wait()
            self.assertFalse(i["enabled"]); self.assertEqual(Gh.hits, 0)
        finally: os.environ.pop("LABTOWER_UPDATE_CHECK")

    def test_admin_routes(self):
        srv = Server(load("auth/admin_panel.py").H)
        try:
            self.assertEqual(srv.call("GET", "/api/update")[0], 401)
            tok = make_user("upadm", ADMIN)
            Gh.body = {"tag_name": "2.1.3f", "html_url": auth.RELEASE_PREFIX + "releases/tag/2.1.3f"}
            st, b = srv.call("POST", "/api/update/check", {}, tok); self.assertEqual(st, 200)
            self.wait()
            st, b = srv.call("GET", "/api/update", token=tok)
            self.assertEqual(st, 200); self.assertTrue(b["newer"])
            self.assertEqual(srv.call("POST", "/api/update/check", {})[0], 401)
        finally: srv.close()

if __name__ == "__main__":
    unittest.main()
