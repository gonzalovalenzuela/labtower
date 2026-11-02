"""VPN Monitor: validación, lectores (WireGuard, OpenVPN v1/v2/v3, Tailscale), sesiones y eventos, SSH con el comando fijo, secretos y permisos."""
import json, os, tempfile, time, unittest
from pathlib import Path
from unittest import mock
from tests import support
from tests.support import ADMIN, READONLY, NONE

m = support.load("vpn-monitor/server.py")
K1, K2 = "A" * 43 + "=", "B" * 43 + "="

class Validate(unittest.TestCase):
    def test_types_and_required(self):
        t = m.validate({"type": "tailscale", "name": "ts", "api_key": "tskey-api-abc12345"})
        self.assertEqual((t["tailnet"], t["timeout"]), ("-", 10))
        w = m.validate({"type": "wireguard", "name": "wg", "host": "192.0.2.9", "ssh_user": "root", "aliases": K1 + " Gonzalo"})
        self.assertEqual((w["port"], w["aliases"]), (22, {K1: "Gonzalo"}))
        o = m.validate({"type": "openvpn", "name": "ov", "host": "192.0.2.9", "ssh_user": "vpnread"})
        self.assertEqual(o["status_path"], m.DEFAULT_OVPN_STATUS)
        for bad in ({"type": "ipsec", "name": "x"}, {"type": "tailscale", "name": "x"}, {"type": "tailscale", "name": "x", "api_key": "short"},
                    {"type": "tailscale", "name": "", "api_key": "tskey-api-abc12345"}, {"type": "tailscale", "name": "x", "api_key": "tskey-api-abc12345", "tailnet": "a b"},
                    {"type": "wireguard", "name": "x", "host": "-oProxyCommand=x", "ssh_user": "root"}, {"type": "wireguard", "name": "x", "host": "192.0.2.9", "ssh_user": "-x"},
                    {"type": "wireguard", "name": "x", "host": "192.0.2.9", "ssh_user": "a b"}, {"type": "wireguard", "name": "x", "host": "192.0.2.9", "ssh_user": "root", "port": 0},
                    {"type": "wireguard", "name": "x", "host": "192.0.2.9", "ssh_user": "root", "aliases": "nokey Name"},
                    {"type": "openvpn", "name": "x", "host": "192.0.2.9", "ssh_user": "root", "status_path": "/etc/../shadow"},
                    {"type": "openvpn", "name": "x", "host": "192.0.2.9", "ssh_user": "root", "status_path": "/tmp/a b; reboot"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError): m.validate(bad)
    def test_type_fixed_and_secret_kept(self):
        cur = m.validate({"type": "tailscale", "name": "ts", "api_key": "tskey-api-abc12345"}); cur["id"] = "a"
        c = m.validate({"name": "ts2"}, cur); self.assertEqual((c["api_key"], c["name"]), ("tskey-api-abc12345", "ts2"))
        with self.assertRaises(ValueError): m.validate({"type": "openvpn", "name": "x"}, cur)
    def test_public_hides_secret(self):
        p = m.public(m.validate({"type": "tailscale", "name": "ts", "api_key": "tskey-api-abc12345"}))
        self.assertNotIn("api_key", p); self.assertTrue(p["has_api_key"])
        w = m.public(m.validate({"type": "wireguard", "name": "wg", "host": "192.0.2.9", "ssh_user": "root", "aliases": K1 + " G"}))
        self.assertEqual(w["aliases_text"], K1 + " G")

class Parsers(unittest.TestCase):
    def test_wireguard(self):
        now = time.time()
        dump = f"wg0\tPRIV\tPUB\t51820\toff\nwg0\t{K1}\t(none)\t203.0.113.5:4000\t10.8.0.2/32\t{int(now) - 30}\t1000\t2000\toff\nwg0\t{K2}\t(none)\t(none)\t10.8.0.3/32\t0\t0\t0\toff\n"
        a, b = m.parse_wireguard(dump, {K1: "Gonzalo"}, now)
        self.assertEqual((a["name"], a["online"], a["ip"], a["rx"], a["tx"]), ("Gonzalo", True, "203.0.113.5", 1000, 2000))
        self.assertEqual((b["online"], b["ip"], b["last"]), (False, None, None))
        old = m.parse_wireguard(dump.replace(str(int(now) - 30), str(int(now) - 400)), {}, now)[0]
        self.assertFalse(old["online"])                                   # handshake older than 3 minutes
    def test_openvpn_v3_v2_v1(self):
        v3 = "CLIENT_LIST\tbob\t198.51.100.7:5555\t10.9.0.6\t\t100\t200\tMon Nov  2 10:00:00 2026\t1793000000\tbob\t1\t0\tAES\n"
        c = m.parse_openvpn(v3)[0]; self.assertEqual((c["name"], c["ip"], c["virtual"], c["rx"], c["since"]), ("bob", "198.51.100.7", "10.9.0.6", 100, 1793000000))
        v2 = "CLIENT_LIST,alice,198.51.100.8:1,10.9.0.7,,1,2,Mon Nov  2 10:00:00 2026,1793000001,UNDEF,2,0,AES\n"
        self.assertEqual(m.parse_openvpn(v2)[0]["name"], "alice")
        v1 = "OpenVPN CLIENT LIST\nUpdated,x\nCommon Name,Real Address,Bytes Received,Bytes Sent,Connected Since\nal,1.2.3.4:55,10,20,Mon Nov  2 10:00:00 2026\nROUTING TABLE\nx,y\nEND\n"
        c = m.parse_openvpn(v1); self.assertEqual((len(c), c[0]["name"], c[0]["ip"], c[0]["tx"]), (1, "al", "1.2.3.4", 20))
        self.assertEqual(m.parse_openvpn("garbage\nCLIENT_LIST,short\n"), [])
    def test_tailscale(self):
        now = time.time()
        d = [{"hostname": "nas", "addresses": ["100.64.0.1"], "lastSeen": "2026-11-02T18:00:00Z", "connectedToControl": True, "user": "g@x.cl", "os": "linux"},
             {"hostname": "old", "addresses": [], "lastSeen": "2020-01-01T00:00:00Z"}, "junk"]
        a, b = m.parse_tailscale(d, now); self.assertTrue(a["online"]); self.assertFalse(b["online"]); self.assertEqual(a["ip"], "100.64.0.1")

class Ssh(unittest.TestCase):
    def test_fixed_command_and_hardening(self):
        cfg = m.validate({"type": "wireguard", "name": "wg", "host": "192.0.2.9", "ssh_user": "root"})
        d = Path(tempfile.mkdtemp()); (d / "k").write_text("x")
        with mock.patch.object(m, "SSH_KEY", d / "k"), mock.patch.object(m, "KNOWN", d / "kh"), mock.patch.object(m, "DATA_DIR", d), \
             mock.patch.object(m.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="ok", stderr="")
            m.ssh_run(cfg, m.CMD_WG)
            argv = run.call_args[0][0]
        self.assertEqual(argv[-1], "wg show all dump"); self.assertEqual(argv[-2], "root@192.0.2.9")
        for o in ("BatchMode=yes", "StrictHostKeyChecking=accept-new", "PasswordAuthentication=no"): self.assertIn(o, argv)
        self.assertIn("-F", argv); self.assertNotIn("shell", run.call_args[1])
    def test_openvpn_reads_only_the_configured_file(self):
        cfg = m.validate({"type": "openvpn", "name": "ov", "host": "192.0.2.9", "ssh_user": "root", "status_path": "/var/log/openvpn/status.log"})
        with mock.patch.object(m, "ssh_run", return_value="") as r:
            m.collect(cfg)
        self.assertEqual(r.call_args[0][1], "cat /var/log/openvpn/status.log")
    def test_openvpn_real_address_forms(self):
        for raw, want in (("1.2.3.4:5000", "1.2.3.4"), ("[2001:db8::1]:5000", "2001:db8::1"), ("::ffff:190.1.2.3", "190.1.2.3"),
                          ("::ffff:190.1.2.3:44444", "190.1.2.3"), ("udp6:[::ffff:190.1.2.3]:1194", "190.1.2.3"), ("2001:db8::1", "2001:db8::1")):
            self.assertEqual(m._ovpn_ip(raw), want, raw)
    def test_sudo_option_prefixes_only_the_fixed_command(self):
        for typ, extra, want in (("openvpn", {"status_path": "/tmp/ovpn_status_2_result"}, "sudo -n cat /tmp/ovpn_status_2_result"),
                                 ("wireguard", {}, "sudo -n " + m.CMD_WG)):
            cfg = m.validate({"type": typ, "name": "x", "host": "192.0.2.9", "ssh_user": "gonzalo", "use_sudo": True, **extra})
            self.assertTrue(cfg["use_sudo"])
            with mock.patch.object(m, "ssh_run", return_value="") as r:
                m.collect(cfg)
            self.assertEqual(r.call_args[0][1], want)
        cfg = m.validate({"type": "openvpn", "name": "x", "host": "192.0.2.9", "ssh_user": "gonzalo"})
        self.assertFalse(cfg["use_sudo"])
    def test_missing_key_is_explained(self):
        with mock.patch.object(m, "SSH_KEY", Path(tempfile.mkdtemp(), "nokey")):
            with self.assertRaises(RuntimeError) as e: m.ssh_run({"port": 22, "ssh_user": "root", "host": "192.0.2.9"}, "x")
        self.assertIn("SSH key", str(e.exception))

class Sessions(unittest.TestCase):
    def setUp(self):
        self.ev = []
        self.p = [mock.patch.object(m.auth, "record_event", lambda *a, **k: self.ev.append((a[2], a[3]))), mock.patch.object(m, "save_state", lambda: None)]
        for p in self.p: p.start()
        m._state.clear()
    def tearDown(self):
        for p in self.p: p.stop()
    def snap(self, *online): return {"clients": [{"key": k, "name": k, "online": True, "since": None} for k in online]}
    def test_connect_disconnect_and_duration(self):
        n = {"id": "x", "name": "VPN"}
        s = self.snap("a"); m.track(n, s, 1000)                      # first reading: nothing is announced
        self.assertEqual(self.ev, []); self.assertEqual(s["clients"][0]["since"], 1000)
        s = self.snap("a", "b"); m.track(n, s, 1100)
        self.assertEqual([e[1] for e in self.ev], ["vpn_up"]); self.assertEqual(s["clients"][0]["since"], 1000)
        s = self.snap("b"); m.track(n, s, 1200)
        self.assertEqual([e[1] for e in self.ev], ["vpn_up", "vpn_down"])
        self.assertEqual(s["log"][0], {"name": "a", "start": 1000, "end": 1200})
    def test_openvpn_since_is_trusted(self):
        n = {"id": "y", "name": "VPN"}
        s = {"clients": [{"key": "k", "name": "bob", "online": True, "since": 500}]}; m.track(n, s, 1000)
        self.assertEqual(s["clients"][0]["since"], 500)

class Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.patch = [mock.patch.object(m, "DATA_FILE", Path(cls.tmp, "vpn.json")), mock.patch.object(m, "ensure_poller", lambda n: None)]
        for p in cls.patch: p.start()
        cls.srv = support.Server(m.H)
        cls.admin, cls.ro, cls.none = (support.make_user(u, p) for u, p in (("vadmin", ADMIN), ("vro", READONLY), ("vnone", NONE)))
    @classmethod
    def tearDownClass(cls):
        cls.srv.close()
        for p in cls.patch: p.stop()
    def test_permissions_and_no_secret_leak(self):
        body = {"type": "tailscale", "name": "ts", "api_key": "tskey-api-abc12345"}
        self.assertEqual(self.srv.call("GET", "/api/vpn")[0], 401)
        self.assertEqual(self.srv.call("GET", "/api/vpn", token=self.none)[0], 401)
        self.assertEqual(self.srv.call("POST", "/api/vpn", body, token=self.ro)[0], 403)
        st, j = self.srv.call("POST", "/api/vpn", body, token=self.admin); self.assertEqual(st, 201)
        self.assertNotIn("tskey", json.dumps(j))
        st, j = self.srv.call("GET", "/api/vpn", token=self.ro); self.assertEqual(st, 200)
        self.assertNotIn("tskey", json.dumps(j)); self.assertTrue(j["vpn"][0]["has_api_key"])
        self.assertEqual(self.srv.call("GET", "/api/ssh-key", token=self.ro)[0], 403)
        vid = j["vpn"][0]["id"]
        self.assertEqual(self.srv.call("DELETE", "/api/vpn/" + vid, token=self.ro)[0], 403)
        self.assertEqual(self.srv.call("DELETE", "/api/vpn/" + vid, token=self.admin)[0], 200)

class Wiring(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    def test_installer_nginx_and_permissions_know_the_module(self):
        r = lambda p: (self.ROOT / p).read_text()
        for f, needles in (("debian/postinst", ('install_service "vpn-monitor"', "labtower-vpn", "vpn-monitor:vpn")), ("debian/preinst", ("labtower-vpn",)),
                           ("debian/postrm", ("vpn-monitor.service",)), ("etc/nginx/snippets/labtower-site.conf", ("location /vpn/", "/vpn/api/login", "8089")),
                           ("scripts/teleporter.sh", ("vpn-monitor",)), ("auth/admin_panel.py", ('"vpn"',)), ("overview/server.py", ('"vpn"',)), ("auth/auth.py", ('"vpn": "admin"',))):
            for n in needles:
                with self.subTest(file=f, needle=n): self.assertIn(n, r(f))
    def test_no_inline_handlers(self):
        h = (self.ROOT / "vpn-monitor/static/index.html").read_text(); self.assertNotIn("onclick=", h)

if __name__ == "__main__": unittest.main()
