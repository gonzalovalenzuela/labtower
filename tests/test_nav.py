"""Shared navigation: one menu (nav.js) in every module and in the Overview, same order as the home page."""
import re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIDE = {"wol-console": "wol", "nut-monitor": "nut", "net-monitor": "net", "proxmox-monitor": "pve", "nas-monitor": "nas",
        "dns-monitor": "dns", "wan-monitor": "wan", "vpn-monitor": "vpn", "auth": "admin"}

class Nav(unittest.TestCase):
    def test_every_page_loads_the_shared_menu(self):
        for d in (*SIDE, "overview"):
            h = (ROOT / d / "static" / "index.html").read_text()
            self.assertIn('src="nav.js"', h, d); self.assertIn('href="nav.css"', h, d)
            self.assertLess(h.index('src="nav.js"'), h.index('src="app.js"') if 'src="app.js"' in h else 10**9, d)

    def test_modules_use_it_and_keep_no_private_menu(self):
        for d, sid in SIDE.items():
            js = (ROOT / d / "static" / "app.js").read_text()
            self.assertIn(f"const _NAV_SELF='{sid}'", js, d)
            self.assertIn("labNav.render(", js, d)
            for old in ("_NAV_ITEMS", "_navDragSrc", "pi-nav-order"): self.assertNotIn(old, js, d)
        ov = (ROOT / "overview" / "static" / "app.js").read_text()
        self.assertIn("self:'overview',mode:'strip'", ov)
        self.assertIn('id="navstrip"', (ROOT / "overview" / "static" / "index.html").read_text())
        self.assertNotIn('href="/" data-i="home"', (ROOT / "overview" / "static" / "index.html").read_text())

    def test_home_cards_follow_the_menu_order(self):
        nav = (ROOT / "assets" / "nav.js").read_text()
        groups = re.search(r"var G = \[(.*?)\n  \];", nav, re.S).group(1)
        want = re.findall(r"'(\w+)'", " ".join(re.findall(r"items: \[([^\]]*)\]", groups)))
        want = [x for x in want if x != "home"]
        home = re.findall(r'class="app-card" href="/(\w+)/"', (ROOT / "home" / "index.html").read_text())
        self.assertEqual(home, want)
        hj = (ROOT / "home" / "home.js").read_text()
        for k in ("gPower", "gNet", "gTools", "gSys"): self.assertEqual(hj.count(k + ":"), 2, k)

    def test_menu_permissions_and_disabled_rules(self):
        nav = (ROOT / "assets" / "nav.js").read_text()
        self.assertIn("me.disabled", nav); self.assertIn("LV[me.permissions[id]]", nav)
        self.assertIn("/admin/api/health", nav)                       # one public call for every status dot

if __name__ == "__main__":
    unittest.main()
