"""Al refrescar, la vista no salta: nav.js (en todos los módulos) mantiene en su lugar el elemento que está bajo la barra
superior cuando el contenido se rearma. El scroll anchoring del navegador no basta: falta en Safari antiguo y se pierde
cuando el elemento se reemplaza (cada refresco); donde existe, se revisa un cuadro después para no corregir dos veces.
EN: On refresh the view does not jump: nav.js (in every module) keeps the element under the top bar in place when the
content is rebuilt. Browser scroll anchoring is not enough: older Safari lacks it and it is lost when the element is
replaced (every refresh); where it exists, it is checked one frame later so the correction is not applied twice."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAV = (ROOT / "assets/nav.js").read_text(encoding="utf-8")


class KeepView(unittest.TestCase):
    def test_works_with_and_without_native_anchoring(self):
        self.assertIn("var native = !!(window.CSS && CSS.supports && CSS.supports('overflow-anchor', 'auto'));", NAV)
        self.assertIn("if (native && a.el.isConnected) {", NAV)
        self.assertIn("requestAnimationFrame(function () { later = false; fix(); });", NAV)
        self.assertIn("if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', keepView); else keepView();", NAV)

    def test_follows_element_changes_in_the_whole_page(self):
        self.assertIn("mo.observe(root, { childList: true, subtree: true });", NAV)
        self.assertIn("var root = document.body, a = null, busy = false, later = false;", NAV)
        self.assertIn("el = r.addedNodes[k].nodeType === 1;", NAV)          # clock text alone does not count

    def test_finds_the_same_element_and_corrects(self):
        for k in ("if (a.el.isConnected) return a.el;", "var n = a.id ? document.getElementById(a.id) : root;",
                  "if (n && n.getClientRects().length) {", "window.scrollBy(0, d);",
                  "if (window.scrollY < 1) return null;"):
            self.assertIn(k, NAV, k)

    def test_every_module_loads_it(self):
        pages = sorted(ROOT.glob("*/static/index.html"))
        self.assertGreaterEqual(len(pages), 11)
        for p in pages:
            self.assertIn('<script src="nav.js"></script>', p.read_text(encoding="utf-8"), p)
            self.assertEqual((p.parent / "nav.js").read_text(encoding="utf-8"), NAV, p)

    def test_syntax(self):
        try:
            r = subprocess.run(["node", "--check", str(ROOT / "assets/nav.js")], capture_output=True, text=True, timeout=30, check=False)
        except FileNotFoundError:
            self.skipTest("node not installed")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
