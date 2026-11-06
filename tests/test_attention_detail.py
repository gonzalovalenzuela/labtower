"""Cada aviso tiene su detalle: el aviso «Atención» muestra el texto de los chequeos que fallan, y Proxmox Monitor muestra el error
de lectura (con la antigüedad de los datos) y, si el certificado cambió, el botón para volver a fijarlo.
EN: Every warning has its detail: the "Attention" notice shows the text of the failing checks, and Proxmox Monitor shows the read error
(with the age of the data) and, when the certificate changed, the button to pin it again."""
import unittest
from pathlib import Path

from tests import support

m = support.load("proxmox-monitor/server.py")
ROOT = Path(__file__).resolve().parents[1]


class ClusterError(unittest.TestCase):
    def test_error_kind(self):
        c = m.ClusterCache("x")
        self.assertIsNone(c.snap()["error_kind"])
        c.update({"nodes": []}); c.set_error("Certificate fingerprint mismatch", "cert")
        s = c.snap(); self.assertEqual((s["error"], s["error_kind"]), ("Certificate fingerprint mismatch", "cert"))
        self.assertTrue(s["ts"])                                         # the older data stays
        c.set_error("timed out"); self.assertIsNone(c.snap()["error_kind"])
        c.update({"nodes": []}); s = c.snap(); self.assertEqual((s["error"], s["error_kind"]), (None, None))

    def test_poller_marks_certificate_errors(self):
        src = (ROOT / "proxmox-monitor/server.py").read_text()
        self.assertIn('cache.set_error(str(e), "cert" if isinstance(e, PVECertError) else None)', src)


class Page(unittest.TestCase):
    def test_proxmox_page_shows_the_error_and_repin(self):
        js = (ROOT / "proxmox-monitor/static/app.js").read_text()
        for k in ("if(snap.error){", "snap.error_kind==='cert'", 'data-on-click="pinCluster"', "stale-banner"):
            self.assertIn(k, js, k)
        for k in ("staleTitle:", "staleAge:", "certChanged:", "certChangedDesc:", "repin:"): self.assertEqual(js.count(k), 2, k)

    def test_attention_notice_shows_check_details(self):
        nav = (ROOT / "assets/nav.js").read_text()
        self.assertIn("function detail(id)", nav); self.assertIn("'gwarn-d'", nav)
        self.assertIn(".gwarn-d{", (ROOT / "assets/nav.css").read_text())


class Overview(unittest.TestCase):
    """El Resumen marca una lectura fallida con datos anteriores y cada aviso de conexión lleva el texto del error.
    EN: The Overview flags a failed reading with older data and every connection issue carries the error text."""
    def setUp(self): self.js = (ROOT / "overview/static/app.js").read_text()

    def test_proxmox_stale_and_certificate(self):
        self.assertIn("else if(sn.error){s=worst(s,'warn');issues.push({lv:'warn',m:'pve',t:`${c.name}: ${T(sn.error_kind==='cert'?'issue_cert':'issue_stale')}${why(sn.error)}`", self.js)
        for k in ("issue_stale:'", "issue_cert:'"): self.assertEqual(self.js.count(k), 2, k)

    def test_connection_issues_carry_the_error(self):
        for k in ("T('issue_cl')}${why(sn.error)}", "T('issue_nasdown')}${why(sn.error)}", "T('issue_dnsdown')}${why(sn.error)}",
                  "T('vpnoff')}${why(sn.error)}", "T('uptdown')}${why(n.last&&n.last.error)}", "T('unreach')}${why(e)}"):
            self.assertIn(k, self.js, k)
        self.assertEqual(self.js.count(":fail('c-"), 8); self.assertNotRegex(self.js, r":fail\('c-[\w-]+',T\('\w+'\)\)")


class ModulePages(unittest.TestCase):
    def test_ups_and_net_show_their_errors(self):
        ups = (ROOT / "nut-monitor/static/app.js").read_text()
        self.assertIn("const bad=servers.filter(sv=>allData[sv.id]?.error);", ups); self.assertEqual(ups.count("srvErrSince:"), 2)
        self.assertIn('id="srv-errs"', (ROOT / "nut-monitor/static/index.html").read_text())
        net = (ROOT / "net-monitor/static/app.js").read_text()
        self.assertIn("t('scanFailed')+': '+scan.error", net); self.assertEqual(net.count("scanFailed:"), 2)
        self.assertIn('id="st-scan-err"', (ROOT / "net-monitor/static/index.html").read_text())


if __name__ == "__main__":
    unittest.main()
