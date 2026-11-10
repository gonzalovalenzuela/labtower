"""El aviso «Atención» sigue a la página: cuando el módulo rearma su contenido con una lectura nueva, o al volver a la pestaña, nav.js
vuelve a pedir el estado si tiene más de 15 s. Antes solo se pedía cada 60 s (y Safari detiene ese temporizador en segundo plano), así que
el aviso seguía aunque la página ya mostraba el problema resuelto.
EN: The "Attention" notice follows the page: when the module rebuilds its content with a new reading, or when the tab comes back, nav.js
fetches the status again if it is older than 15 s. It used to be fetched only every 60 s (and Safari stops that timer in the background),
so the notice stayed although the page already showed the problem solved."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAV = (ROOT / "assets/nav.js").read_text(encoding="utf-8")


class WarnSync(unittest.TestCase):
    def test_refetched_when_the_module_redraws(self):
        self.assertIn("}).observe(document.body, { childList: true, subtree: true });", NAV)
        self.assertIn("if (!hWait) hWait = setTimeout(function () { hWait = null; healthSoon(); }, 1000);", NAV)   # not restarted by a ticking clock
        self.assertIn("if (r.target.closest && r.target.closest('#gwarn, .gbar')) continue;", NAV)      # its own drawing does not loop

    def test_at_most_every_15_seconds(self):
        self.assertIn("if (!st || Date.now() - hAt < 15000) return;", NAV)
        self.assertIn("hAt = Date.now();\n    fetch('/admin/api/health'", NAV)
        self.assertIn("health = c.m; hAt = c.t; paint(); return;", NAV)

    def test_when_the_tab_comes_back(self):
        self.assertIn("document.addEventListener('visibilitychange', function () { if (!document.hidden) healthSoon(); });", NAV)
        self.assertIn("window.addEventListener('pageshow', function (e) { if (e.persisted) healthSoon(); });", NAV)

    def test_armed_once(self):
        self.assertEqual(NAV.count("healthSync();"), 1)
        self.assertIn("if (!timer) { timer = setInterval(", NAV)


if __name__ == "__main__":
    unittest.main()
