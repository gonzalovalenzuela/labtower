"""2.1.4h: búsqueda global del Resumen (la tarjeta «Enlaces» se quitó en 2.1.4r) / Overview global search (the "Links" card was removed in 2.1.4r)."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from tests import support
from tests.support import ADMIN

ROOT = Path(__file__).resolve().parent.parent
ov = support.load("overview/server.py")

class Removed(unittest.TestCase):
    def test_bookmarks_are_gone(self):
        s = support.Server(ov.H); tok = support.make_user("srchadm", ADMIN)
        self.assertEqual(s.call("GET", "/api/bookmarks", None, token=tok)[0], 404)
        self.assertEqual(s.call("POST", "/api/bookmarks", {"bookmarks": []}, token=tok)[0], 404)
        self.assertFalse((ROOT / "overview/static/links.js").exists())
        self.assertFalse(any(hasattr(ov, n) for n in ("load_bookmarks", "clean_bookmarks", "BOOKMARKS_FILE")))

class Front(unittest.TestCase):
    def test_page_loads_search_after_app(self):
        h = (ROOT / "overview/static/index.html").read_text()
        self.assertLess(h.index('src="app.js"'), h.index('src="search.js"'))
        for i in ('id="gs"', 'id="gsr"'): self.assertIn(i, h)
        self.assertNotIn('id="c-bm"', h)
    def test_no_inline_handlers_and_hooks_exist(self):
        js = (ROOT / "overview/static/search.js").read_text()
        self.assertNotRegex(js, r"\bon(click|input|change)=")
        app = (ROOT / "overview/static/app.js").read_text()
        self.assertIn("searchUpdate(R)", app); self.assertIn("searchLang()", app)
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_same_keys_in_both_languages(self):
        js = (ROOT / "overview/static/search.js").read_text()
        code = f"const s={json.dumps(js)};const m=s.match(/en: \\{{(.*?)\\}},\\n\\s+es: \\{{(.*?)\\}}\\n  \\}};/s);" + \
               "const k=t=>[...t.matchAll(/(\\w+): '/g)].map(x=>x[1]).sort();console.log(JSON.stringify([k(m[1]),k(m[2])]))"
        out = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(out.returncode, 0, out.stderr)
        en, es = json.loads(out.stdout); self.assertEqual(en, es); self.assertGreater(len(en), 6)

if __name__ == "__main__": unittest.main()
