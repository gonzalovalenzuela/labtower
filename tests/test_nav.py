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
        self.assertIn("self:'overview'", ov); self.assertIn("labNav.render(", ov)
        self.assertNotIn('id="navstrip"', (ROOT / "overview" / "static" / "index.html").read_text())
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

    def test_top_bar_switcher_and_bottom_bar(self):
        nav = (ROOT / "assets" / "nav.js").read_text(); css = (ROOT / "assets" / "nav.css").read_text()
        for k in ("gbar", "gsw", "gpanel", "gtab", 'aria-haspopup', 'aria-controls'): self.assertIn(k, nav, k)
        self.assertIn("Escape", nav)                                  # panel closes with Esc
        self.assertIn("max-width:767px", css)                         # bottom bar below 768 px
        self.assertIn("body.kiosk .gbar", css)                        # hidden in kiosk mode
        for s in ("up", "mid", "down"): self.assertIn("'" + s + "'", nav, s)   # status = shape + text, not only colour

    def test_original_logo_warning_notice_and_menu_wizard(self):
        nav = (ROOT / "assets" / "nav.js").read_text(); css = (ROOT / "assets" / "nav.css").read_text()
        self.assertIn("'/logo.png'", nav); self.assertNotIn("'LT'", nav)             # the original icon, not text
        self.assertIn("function warnStrip", nav); self.assertIn("document.querySelector('.main')", nav)
        self.assertIn("host.insertBefore(box, at)", nav)                                 # notice under the module bar (top of the content when there is none)
        self.assertIn("=== 'overview' ? null", nav)                                 # the Overview has its own notice
        for k in ("lt-nav-mode", "function wizard", "function classic", "aria-modal", "menuType", "function placeBtn", "function sideLayout", "function barRight"): self.assertIn(k, nav, k)
        for k in (".gwiz", ".gwarn", ".nav-chip", ".gmt", "body.gtb-none .topbar", "body.gside-none .sidebar", "body:not(.has-gbar) .gbar"): self.assertIn(k, css, k)

    def test_overview_strip_fits_on_one_line(self):
        # ES: la tira del Resumen (menú clásico) usa nombres cortos y el completo en title/aria-label; con 13 px midió 999 de 1288 px.
        # EN: the Overview strip (classic menu) uses short names with the full one in title/aria-label; at 13 px it measured 999 of 1288 px.
        nav = (ROOT / "assets" / "nav.js").read_text(); css = (ROOT / "assets" / "nav.css").read_text()
        self.assertIn("strip ? name.replace(/ (Monitor|Console|Panel)$/, '') : name", nav)
        self.assertIn("a.title = name; a.setAttribute('aria-label', name);", nav)
        self.assertIn(".navstrip{display:flex;flex-wrap:wrap;gap:8px 12px;", css)
        self.assertIn(".nav-grp{display:inline-flex;flex-wrap:wrap;gap:4px;", css)
        self.assertIn("gap:5px;padding:5px 10px;", css)

    def test_overview_vpn_card_shows_only_the_count(self):
        ov = (ROOT / "overview" / "static" / "app.js").read_text()
        fn = ov[ov.index("function renderVPN"):ov.index("return sev;", ov.index("function renderVPN"))]
        self.assertNotIn("clients", fn); self.assertIn("x.online", fn); self.assertNotIn("x.total", fn)

    def test_top_bar_mode_keeps_the_module_buttons(self):
        """En el modo de barra superior #tb-sub se oculta (solo texto): los botones de cada módulo no pueden vivir ahí, y la barra del módulo
        se vuelve a evaluar cuando le aparecen botones después de cargar los datos."""
        nav = (ROOT / "assets" / "nav.js").read_text()
        self.assertIn("gbar-act", nav); self.assertIn(".gbar-act", (ROOT / "assets" / "nav.css").read_text())      # action buttons go up to the top bar
        self.assertIn("tb.gobs = new MutationObserver", nav); self.assertIn("function ownControls", nav)
        for d in SIDE:
            app = ROOT / d / "static" / "app.js"
            if not app.exists(): continue
            lines = app.read_text().splitlines()
            for i, l in enumerate(lines):
                if "tb-sub" in l:
                    self.assertIsNone(re.search(r"\bsub\.appendChild\(b\w*\)", " ".join(lines[i:i + 3])), f"{d}: botón dentro de #tb-sub (línea {i + 1})")
        self.assertIn("button.lt-btn", (ROOT / "assets" / "nav.css").read_text())                 # one look for every module action button
        self.assertIn("lt-btn", (ROOT / "wan-monitor" / "static" / "app.js").read_text()); self.assertIn('class="lt-btn"', (ROOT / "net-monitor" / "static" / "index.html").read_text())
        wan = (ROOT / "wan-monitor" / "static")
        self.assertIn('id="tb-actions"', (wan / "index.html").read_text())
        self.assertIn("act.appendChild(b)", (wan / "app.js").read_text())

    def test_overview_uses_the_common_bar_without_module_chips(self):
        """El Resumen tiene la misma barra común que los demás módulos (idioma, tema, reloj, usuario, salir); ya no tiene la fila de chips de módulos, solo el filtro «solo con problemas»."""
        ov = ROOT / "overview" / "static"
        html, js = (ov / "index.html").read_text(), (ov / "app.js").read_text()
        for needle in ('class="lang-btns"', 'class="theme-btns"', 'id="clock"', 'class="topbar-user"', 'class="btn-logout"', 'id="only-prob"'):
            self.assertIn(needle, html)
        top = html[html.index('<div class="top">'):html.index('id="attn"')]
        for old in ('id="bl"', "data-theme-toggle", 'id="bo"'):
            self.assertNotIn(old, top)                                  # no duplicated controls in the page header
        self.assertNotIn('id="chips"', html); self.assertNotIn("renderChips", js)
        self.assertIn("function applySeverity", js); self.assertEqual(js.count("modSev(mods,"), 9)

    def test_phone_bar_has_a_sign_out_tab_that_uses_the_modules_own_button(self):
        """ES: En el móvil toda sección tiene «Salir» en la barra inferior (la barra del módulo se oculta); usa el .btn-logout propio. EN: every section has Sign out in the phone bottom bar."""
        js = (ROOT / "assets" / "nav.js").read_text()
        self.assertIn("tabItem('out', tr.out", js)
        self.assertIn("document.querySelector('.btn-logout')", js)
        self.assertIn("out: 'Salir'", js); self.assertIn("out: 'Sign out'", js)

    def test_every_page_has_a_favicon(self):
        for d in (*SIDE, "overview"):
            self.assertIn('rel="icon"', (ROOT / d / "static" / "index.html").read_text(), d)
        self.assertIn('rel="icon"', (ROOT / "home" / "index.html").read_text())

if __name__ == "__main__":
    unittest.main()


class TopBarLayout(unittest.TestCase):
    def test_overview_bar_is_full_width_and_net_actions_sit_by_the_title(self):
        ov = (ROOT / "overview" / "static" / "app.css").read_text(); css = (ROOT / "assets" / "nav.css").read_text()
        self.assertIn(".ov-in{max-width:1320px", ov); self.assertIn("position:sticky;top:0", ov.split(".topbar{")[1].split("}")[0])
        self.assertIn("body:not(.kiosk) .top h1{display:none}", ov)
        self.assertIn(".topbar>.tb-actions{", css); self.assertIn(".nav-grp{", css)

