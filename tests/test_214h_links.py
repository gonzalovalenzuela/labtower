"""2.1.4h: marcadores del Resumen y búsqueda global / Overview bookmarks and global search."""
import json, re, shutil, subprocess, unittest
from pathlib import Path
from tests import support
from tests.support import ADMIN, READONLY

ROOT = Path(__file__).resolve().parent.parent
ov = support.load("overview/server.py")

class Clean(unittest.TestCase):
    def test_accepts_http_https_and_internal_paths(self):
        out, err = ov.clean_bookmarks([{"g": "Red", "n": "Router", "u": "http://192.0.2.1/"}, {"g": "", "n": "DNS", "u": "/dns/"},
                                       {"g": "Red", "n": "Panel", "u": "https://example.com/a?b=1"}])
        self.assertEqual(err, ""); self.assertEqual(len(out), 3)
    def test_rejects_dangerous_or_wrong_links(self):
        for u in ("javascript:alert(1)", "data:text/html,x", "//evil.example/x", "ftp://x/", "http://", "http://user:pw@host/", "/a\\b", " http://x/", "http://x/\n", "", None, 5, "h" * 600):
            out, err = ov.clean_bookmarks([{"n": "x", "u": u}])
            self.assertIsNone(out, u)
    def test_rejects_bad_shapes_and_limits(self):
        for bad in ("x", {"a": 1}, [1], [{"n": 5, "u": "/x"}], [{"n": "", "u": "/x"}], [{"n": "a" * 41, "u": "/x"}], [{"g": "g" * 31, "n": "a", "u": "/x"}], [{"n": "a\x00", "u": "/x"}]):
            self.assertIsNone(ov.clean_bookmarks(bad)[0], bad)
        self.assertIsNone(ov.clean_bookmarks([{"n": "a", "u": "/x"}] * (ov.BM_MAX + 1))[0])
        self.assertIsNone(ov.clean_bookmarks([{"g": str(i), "n": "a", "u": "/x"} for i in range(ov.BM_MAX_GROUPS + 1)])[0])

class Endpoints(unittest.TestCase):
    def setUp(self):
        self.srv = support.Server(ov.H); self.hd = {"Origin": "http://127.0.0.1"}
        ov.BOOKMARKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if ov.BOOKMARKS_FILE.exists(): ov.BOOKMARKS_FILE.unlink()
    def tearDown(self): self.srv.close()
    def test_roundtrip_and_permissions(self):
        adm, ro = support.make_user("bmadm", ADMIN), support.make_user("bmro", READONLY)
        st, d = self.srv.call("GET", "/api/bookmarks", None, token=ro)
        self.assertEqual(st, 200); self.assertEqual(d, {"bookmarks": [], "can_edit": False})
        items = [{"g": "Red", "n": "Router", "u": "http://192.0.2.1/"}]
        st, _ = self.srv.call("POST", "/api/bookmarks", {"bookmarks": items}, token=ro, headers=self.hd)
        self.assertEqual(st, 403)
        st, d = self.srv.call("POST", "/api/bookmarks", {"bookmarks": items}, token=adm, headers=self.hd)
        self.assertEqual(st, 200); self.assertEqual(d["bookmarks"], items)
        st, d = self.srv.call("GET", "/api/bookmarks", None, token=ro)
        self.assertEqual(d["bookmarks"], items); self.assertFalse(d["can_edit"])
        st, d = self.srv.call("GET", "/api/bookmarks", None, token=adm)
        self.assertTrue(d["can_edit"])
    def test_invalid_is_rejected_and_nothing_is_saved(self):
        adm = support.make_user("bmadm2", ADMIN)
        st, d = self.srv.call("POST", "/api/bookmarks", {"bookmarks": [{"n": "x", "u": "javascript:alert(1)"}]}, token=adm, headers=self.hd)
        self.assertEqual(st, 400); self.assertFalse(ov.BOOKMARKS_FILE.exists())
    def test_needs_a_session_and_blocks_cross_origin(self):
        st, _ = self.srv.call("GET", "/api/bookmarks", None); self.assertEqual(st, 401)
        adm = support.make_user("bmadm3", ADMIN)
        st, _ = self.srv.call("POST", "/api/bookmarks", {"bookmarks": []}, token=adm, headers={"Origin": "http://evil.example"})
        self.assertEqual(st, 403)
    def test_corrupt_file_is_ignored(self):
        ov.BOOKMARKS_FILE.write_text('[{"n":"x","u":"javascript:1"}]')
        self.assertEqual(ov.load_bookmarks(), [])

class Front(unittest.TestCase):
    def test_page_loads_links_after_app_and_has_search(self):
        h = (ROOT / "overview/static/index.html").read_text()
        self.assertLess(h.index('src="app.js"'), h.index('src="links.js"'))
        for i in ('id="gs"', 'id="gsr"', 'id="c-bm"'): self.assertIn(i, h)
    def test_no_inline_handlers_and_hooks_exist(self):
        js = (ROOT / "overview/static/links.js").read_text()
        self.assertNotRegex(js, r"\bon(click|input|change)=")
        app = (ROOT / "overview/static/app.js").read_text()
        self.assertIn("linksUpdate(R)", app); self.assertIn("linksLang()", app)
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_same_keys_in_both_languages(self):
        js = (ROOT / "overview/static/links.js").read_text()
        code = "const s=%s;const m=s.match(/en: \\{(.*?)\\},\\n\\s+es: \\{(.*?)\\}\\n  \\};/s);" % json.dumps(js) + \
               "const k=t=>[...t.matchAll(/(\\w+): '/g)].map(x=>x[1]).sort();console.log(JSON.stringify([k(m[1]),k(m[2])]))"
        out = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        en, es = json.loads(out.stdout); self.assertEqual(en, es); self.assertGreater(len(en), 20)

if __name__ == "__main__": unittest.main()
