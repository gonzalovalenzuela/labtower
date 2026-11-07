"""Presentación en todas las resoluciones: la cabecera de los gráficos y las columnas de las tablas se adaptan al ancho de su tarjeta (no de la
ventana, porque la barra lateral también ocupa), los textos largos saltan de línea en vez de montarse o cortarse, y la barra superior deja
margen cuando pasa a dos filas.
EN: Layout at every resolution: the chart header and the table columns adapt to the width of their card (not the window, since the sidebar
takes room too), long texts wrap instead of overlapping or being cut, and the top bar keeps a margin when it wraps to two rows."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = ["wol-console", "nut-monitor", "net-monitor", "proxmox-monitor", "nas-monitor", "dns-monitor", "wan-monitor", "vpn-monitor", "uptime-monitor", "overview", "auth"]
TABLES = {"nas-monitor": "nas-table", "dns-monitor": "dns-table", "wan-monitor": "wan-table", "vpn-monitor": "nas-table", "uptime-monitor": "nas-table"}
css = lambda m: (ROOT / m / "static/app.css").read_text()
js = lambda m: (ROOT / m / "static/app.js").read_text()


class Charts(unittest.TestCase):
    def test_chart_header_follows_its_card(self):
        th = (ROOT / "assets/theme/theme.css").read_text()
        self.assertIn(".vchart-section{container-type:inline-size}", th)
        self.assertIn('@container (max-width:600px){.vchart-header{grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"title filters" "legend legend"}', th)
        self.assertIn('@container (max-width:380px){.vchart-header{grid-template-columns:minmax(0,1fr);grid-template-areas:"title" "filters" "legend"}', th)
        for m in MODULES:                                    # the old window-based rule is gone everywhere
            self.assertNotRegex(css(m), r"@media[^{]*\{[^}]*\.vchart-header\{grid-template-columns:1fr auto", m)

    def test_proxmox_node_charts_four_two_or_one_per_row(self):
        c = css("proxmox-monitor")
        for k in (".nd{container-type:inline-size}", ".nd-charts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}",
                  "@container (min-width:1240px){.nd-charts{grid-template-columns:repeat(4,minmax(0,1fr))}}",
                  "@container (max-width:620px){.nd-charts{grid-template-columns:minmax(0,1fr)}}", ".nd-ch>.vchart-section{flex:1}",
                  ".cluster-nav-host{font-size:10px;color:var(--text-dim);font-family:var(--mono);overflow-wrap:anywhere}"):
            self.assertIn(k, c, k)

    def test_axis_labels_stay_inside_the_chart(self):
        src = (ROOT / "nut-monitor/static/charts.js").read_text()
        self.assertIn("ctx.fillText(tx, Math.max(hw + 1, Math.min(W - hw - 1, xOf(i))), H - 3);", src)


class Tables(unittest.TestCase):
    def test_columns_hide_by_card_width(self):
        for m, cls in TABLES.items():
            c = css(m)
            self.assertIn(".tbl-wrap{container-type:inline-size}", c, m)
            self.assertIn(f"@container (max-width:1100px){{.{cls} .c-spark,.{cls} .c-model{{display:none}}}}", c, m)
            self.assertIn(f"@container (max-width:760px){{.{cls} .c-model,.{cls} .c-temp{{display:none}}", c, m)
            self.assertNotIn(f"@media(max-width:1180px){{.{cls} .c-spark", c, m)
            self.assertIn(f".{cls} .sum-name,.{cls} .sum-sub{{white-space:normal;overflow-wrap:anywhere;min-width:16ch}}", c, m)
        self.assertIn("@container (max-width:760px){.nas-table .c-beats{display:none}}", css("uptime-monitor"))

    def test_wol_panel_moves_below_by_content_width(self):
        c = css("wol-console")
        self.assertIn(".content{container-type:inline-size}", c)
        self.assertIn("@container (max-width:1080px){.main-grid{grid-template-columns:minmax(0,1fr)}}", c)

    def test_admin_user_and_dates_on_one_line(self):
        c = css("auth")
        self.assertIn("#users-table .uname,#users-table .ucreated{white-space:nowrap}", c)
        self.assertIn("#users-table .uname{white-space:normal;overflow-wrap:anywhere}", c)


class Texts(unittest.TestCase):
    def test_label_and_value_cells_wrap_instead_of_squashing(self):
        self.assertIn("display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;align-content:center", css("nut-monitor"))
        self.assertIn(".nd-row{display:flex;flex-wrap:wrap;", css("proxmox-monitor"))
        self.assertIn(".disk-row .dm{color:var(--text-mid);min-width:0;overflow-wrap:anywhere}", css("nas-monitor"))
        self.assertIn(".row:not(:has(.bar)) .l{width:auto;flex:1 1 auto;min-width:0}", css("overview"))

    def test_long_ring_text_uses_a_smaller_font(self):
        for m in ("wan-monitor", "dns-monitor"):
            self.assertIn("<div class=\"circle-val${String(txt==null?(pct==null?'—':Math.round(pct)+'%'):txt).length>5?' sm':''}\">", js(m), m)
            self.assertIn(".circle-val.sm{font-size:9.5px;letter-spacing:-.04em}", css(m), m)

    def test_speed_ping_is_rounded(self):
        self.assertIn("bigNum(t('speedPing'),last.ping==null?'—':fmtNum(Math.round(last.ping*10)/10)", js("wan-monitor"))

    def test_overview_vpn_without_a_reading(self):
        self.assertIn("${x&&x.online!=null?`${esc(x.online)} ${T('vpnconn')}`:T(sn.error?'vpnoff':'vpnwait')}", js("overview"))


class TopBar(unittest.TestCase):
    def test_margin_and_right_group_when_wrapped(self):
        for m in MODULES:
            self.assertRegex(css(m), r"\.topbar\{background:var\(--surface\);border-bottom:1px solid var\(--border\);padding:6px ", m)
        self.assertIn(".topbar>:last-child:not(:first-child){margin-left:auto}", (ROOT / "assets/theme/theme.css").read_text())

    def test_ups_count_on_one_line(self):
        self.assertTrue(re.search(r"\.card-meta\{[^}]*white-space:nowrap", css("nut-monitor")))


if __name__ == "__main__":
    unittest.main()
