"""Endurecimiento tras la auditoría del 2026-10-26: defensa CSRF de respaldo (esquema y puerto) y escape de datos remotos de Proxmox (Ceph)."""
import json, subprocess, textwrap, unittest
from pathlib import Path
from tests import support
auth = support.auth
ROOT = Path(__file__).resolve().parent.parent

def co(**h): return auth.cross_origin(h)

class CsrfFallback(unittest.TestCase):
    """Sin Sec-Fetch-Site (Safari antiguo) se compara Origin con Host y, si nginx los envía, con esquema y puerto."""
    def test_sec_fetch_site_decides(self):
        self.assertFalse(co(**{"Sec-Fetch-Site": "same-origin"}))
        self.assertFalse(co(**{"Sec-Fetch-Site": "none"}))
        self.assertTrue(co(**{"Sec-Fetch-Site": "same-site"}))
        self.assertTrue(co(**{"Sec-Fetch-Site": "cross-site", "Origin": "http://pi.lan", "Host": "pi.lan"}))

    def test_no_origin_is_allowed(self):             # curl / scripts: sin cookie ambiente que abusar
        self.assertFalse(co(Host="pi.lan"))

    def test_same_host_default_port(self):
        self.assertFalse(co(Origin="http://pi.lan", Host="pi.lan", **{"X-Forwarded-Proto": "http", "X-Forwarded-Port": "80"}))
        self.assertFalse(co(Origin="https://pi.lan", Host="pi.lan", **{"X-Forwarded-Proto": "https", "X-Forwarded-Port": "443"}))

    def test_other_port_same_host_is_blocked(self):
        self.assertTrue(co(Origin="http://pi.lan:8000", Host="pi.lan", **{"X-Forwarded-Proto": "http", "X-Forwarded-Port": "80"}))
        self.assertTrue(co(Origin="http://pi.lan:81", Host="pi.lan", **{"X-Forwarded-Port": "80"}))

    def test_other_scheme_same_host_is_blocked(self):
        self.assertTrue(co(Origin="https://pi.lan", Host="pi.lan", **{"X-Forwarded-Proto": "http", "X-Forwarded-Port": "80"}))
        self.assertTrue(co(Origin="http://pi.lan", Host="pi.lan", **{"X-Forwarded-Proto": "https"}))

    def test_other_host_subdomain_and_null_are_blocked(self):
        for origin in ("http://evil.example", "http://sub.pi.lan", "null", "", "http://"):
            self.assertTrue(co(Origin=origin, Host="pi.lan"), origin)

    def test_ipv6(self):
        self.assertFalse(co(Origin="http://[fd00::5]", Host="[fd00::5]", **{"X-Forwarded-Proto": "http", "X-Forwarded-Port": "80"}))
        self.assertTrue(co(Origin="http://[fd00::5]:8080", Host="[fd00::5]", **{"X-Forwarded-Port": "80"}))
        self.assertTrue(co(Origin="http://[fd00::6]", Host="[fd00::5]"))

    def test_without_forwarded_headers_behaves_as_before(self):    # llamada directa al servicio (127.0.0.1): solo host
        self.assertFalse(co(Origin="http://pi.lan:8080", Host="pi.lan"))

    def test_nginx_sends_forwarded_headers_in_every_location(self):
        conf = (ROOT / "etc/nginx/snippets/labtower-site.conf").read_text()
        hosts = conf.count("proxy_set_header   Host")
        self.assertGreater(hosts, 0)
        self.assertEqual(conf.count("X-Forwarded-Proto $scheme"), hosts)
        self.assertEqual(conf.count("X-Forwarded-Port  $server_port"), hosts)

class CephRendering(unittest.TestCase):
    """Los datos que llegan de un Proxmox remoto no pueden meter marcado en la página."""
    SRC = (ROOT / "proxmox-monitor/static/app.js").read_text()

    def test_status_is_whitelisted(self):
        self.assertIn("['HEALTH_OK','HEALTH_WARN','HEALTH_ERR'].includes(ceph.health?.status)", self.SRC)

    def test_node_maxcpu_is_escaped(self):
        self.assertIn("${esc(node.maxcpu??'?')}", self.SRC)
        self.assertNotIn("${node.maxcpu}", self.SRC)

    def test_helpers_coerce_to_number(self):
        script = textwrap.dedent("""
            const src = require('fs').readFileSync(process.argv[1], 'utf8');
            const get = n => src.match(new RegExp('function ' + n + '\\\\([^)]*\\\\)\\\\{.*'))[0];
            eval(get('fmtBytes') + get('fmtUptime'));
            console.log(JSON.stringify([fmtBytes('<img src=x onerror=1>'), fmtBytes('2048'), fmtUptime('<b>'), fmtUptime(90061)]));
        """)
        out = subprocess.run(["node", "-e", script, str(ROOT / "proxmox-monitor/static/app.js")], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout), ["0B", "2.0 KB", "—", "1d 1h"])

if __name__ == "__main__":
    unittest.main()
