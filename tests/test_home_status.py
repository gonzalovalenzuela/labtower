"""La portada muestra el estado de cada módulo, junto a la flecha de su tarjeta, con su /api/health público."""
import re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class HomeStatus(unittest.TestCase):
    def test_every_module_is_listed_and_has_a_public_health_route(self):
        js = (ROOT / "home" / "home.js").read_text()
        ids = re.findall(r"'([a-z]+)'", js.split("const SERVICES = ")[1].split("\n")[0])
        html = (ROOT / "home" / "index.html").read_text()
        for i in ids: self.assertIn(f'class="app-card" href="/{i}/"', html, i)       # every status sits on its own card
        self.assertEqual(sorted(ids), sorted(["overview", "wol", "nut", "net", "pve", "nas", "dns", "wan", "vpn", "uptime", "admin"]))
        site = (ROOT / "etc/nginx/snippets/labtower-site.conf").read_text()
        for i in ids: self.assertIn(f"location /{i}/ {{", site, i)
        for srv in ("overview/server.py", "wol-console/server.py", "nut-monitor/server.py", "net-monitor/server.py", "proxmox-monitor/server.py",
                    "nas-monitor/server.py", "dns-monitor/server.py", "wan-monitor/server.py", "vpn-monitor/server.py", "uptime-monitor/server.py", "auth/admin_panel.py"):
            self.assertIn('"/api/health"', (ROOT / srv).read_text(), srv)
    def test_levels_and_colours(self):
        js = (ROOT / "home" / "home.js").read_text(); css = (ROOT / "home" / "home.css").read_text()
        for k in ("'ok'", "'degraded'", "'fail'", "503"): self.assertIn(k, js)
        for c in (".dot.green", ".dot.yellow", ".dot.red", ".dot.gray"): self.assertIn(c, css)
        self.assertNotIn("innerHTML", js.split("const SERVICES")[1]); self.assertIn(".app-state", css)

if __name__ == "__main__":
    unittest.main()
