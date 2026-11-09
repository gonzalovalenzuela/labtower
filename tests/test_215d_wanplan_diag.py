"""2.1.5d: velocidad contratada en WAN Monitor (% entregado) y «Expandir todo» en el diagnóstico del cluster de Proxmox."""
import unittest
from pathlib import Path

from tests import support

w = support.load("wan-monitor/server.py")
ROOT = Path(__file__).resolve().parents[1]

class WanPlan(unittest.TestCase):
    def test_default_and_validation(self):
        c = w.validate({}); self.assertEqual((c["speed"]["plan_down"], c["speed"]["plan_up"]), (0, 0))
        c = w.validate({"speed": {"plan_down": 300, "plan_up": 150}}); self.assertEqual((c["speed"]["plan_down"], c["speed"]["plan_up"]), (300, 150))
        for bad in (-1, 100001, "x"):
            with self.assertRaises(ValueError): w.validate({"speed": {"plan_down": bad}})
    def test_ui(self):
        a = (ROOT / "wan-monitor/static/app.js").read_text(); h = (ROOT / "wan-monitor/static/index.html").read_text()
        for k in ("plan_down", "plan_up", "planRows", "setPlanDown"): self.assertIn(k, a)
        self.assertIn('id="s-sp-pdown"', h); self.assertIn('id="s-sp-pup"', h)
        self.assertEqual(a.count('"setPlanDown"'), 2)

class DiagExpandAll(unittest.TestCase):
    def test_button_and_registration(self):
        a = (ROOT / "proxmox-monitor/static/app.js").read_text()
        self.assertIn("function toggleDiagAll", a); self.assertIn("toggleDiag, toggleDiagAll", a)
        self.assertIn("diagExpand:'Expand all'", a); self.assertIn("diagExpand:'Expandir todo'", a)
        for k in ("reboots", "backups", "smart"): self.assertIn(f"sect('{k}'", a); self.assertIn(f"'{k}'", a.split("const DIAG_KEYS=")[1].split(";")[0])

if __name__ == "__main__": unittest.main()
