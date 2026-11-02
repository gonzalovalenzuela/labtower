"""Disabling unused modules: root helper, auth.disabled_modules(), API contract, installer and UI wiring."""
import os, re, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "scripts" / "labtower-modules"
IDS = ("wol", "nut", "net", "pve", "nas", "dns", "wan", "vpn")

def helper(f, *args):
    env = {**{k: v for k, v in os.environ.items() if not k.startswith("LABTOWER_")},
           "LABTOWER_DISABLED_FILE": str(f), "LABTOWER_MODULES_DRY": "1"}
    return subprocess.run(["bash", str(HELPER), *args], capture_output=True, text=True, env=env, timeout=30)

class Helper(unittest.TestCase):
    def setUp(self): self.f = Path(tempfile.mkdtemp()) / "modules.disabled"
    def off(self): return self.f.read_text().split() if self.f.exists() else []

    def test_disable_enable_roundtrip_no_duplicates(self):
        for m in ("vpn", "wol", "vpn"): self.assertEqual(helper(self.f, "disable", m).returncode, 0)
        self.assertEqual(self.off(), ["vpn", "wol"])
        self.assertEqual(helper(self.f, "enable", "vpn").returncode, 0)
        self.assertEqual(self.off(), ["wol"])
        self.assertEqual(helper(self.f, "enable", "wol").returncode, 0)
        self.assertEqual(self.off(), [])

    def test_only_allowlisted_modules(self):
        for bad in ("admin", "overview", "x;reboot", "../etc", "", "WOL"):
            r = helper(self.f, "disable", bad)
            self.assertEqual(r.returncode, 2, bad)
        self.assertFalse(self.f.exists())

    def test_list_shows_state(self):
        helper(self.f, "disable", "dns")
        out = helper(self.f, "list").stdout
        self.assertRegex(out, r"dns\s+dns-monitor\s+disabled")
        self.assertRegex(out, r"vpn\s+vpn-monitor\s+enabled")

class AuthApi(unittest.TestCase):
    def test_disabled_modules_reads_file_and_ignores_garbage(self):
        f = Path(tempfile.mkdtemp()) / "m"; f.write_text("vpn\nbogus\nadmin\nwol\n")
        code = ("import sys; sys.path.insert(0, %r); import auth; print(auth.disabled_modules())" % str(ROOT / "auth"))
        env = {**{k: v for k, v in os.environ.items() if not k.startswith("LABTOWER_")}, "LABTOWER_DISABLED_FILE": str(f)}
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(r.stdout.strip(), "['wol', 'vpn']", r.stderr)
        f.unlink()
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(r.stdout.strip(), "[]")

class Wiring(unittest.TestCase):
    def test_every_module_reports_disabled_in_api_me_and_hides_nav(self):
        for d in ("overview", "wol-console", "dns-monitor", "net-monitor", "proxmox-monitor", "vpn-monitor", "wan-monitor", "nas-monitor", "nut-monitor"):
            self.assertIn("auth.disabled_modules()", (ROOT / d / "server.py").read_text(), d)
        for d in ("wol-console", "dns-monitor", "net-monitor", "proxmox-monitor", "vpn-monitor", "wan-monitor", "nas-monitor", "nut-monitor", "auth", "overview"):
            self.assertIn("me.disabled", (ROOT / d / "static" / "nav.js").read_text(), d)       # the shared menu hides disabled modules

    def test_admin_api_requires_full_admin_and_audits(self):
        s = (ROOT / "auth" / "admin_panel.py").read_text()
        blk = s[s.index('if path == "/api/modules":'):]
        blk = blk[:blk.index("return self._json(200 if ok")]
        self.assertIn("_is_full_admin", blk)
        self.assertIn("module_disabled", blk)
        self.assertIn("isinstance(en, bool)", blk)

    def test_installer_sudoers_per_module_and_off_modules_not_started(self):
        p = (ROOT / "debian" / "postinst").read_text()
        self.assertIn("labtower-modules disable %s, /usr/local/bin/labtower-modules enable %s", p)
        self.assertIn("modules.disabled", p)
        self.assertNotIn("labtower-modules *", p)                       # no wildcard rule
        t = (ROOT / "scripts" / "teleporter.sh").read_text()
        self.assertIn("service_is_off", t)
        svc = re.search(r'SERVICES="([^"]+)"', t).group(1).split()
        for s in svc:                                                    # every optional service is mapped by the helper and the installer
            if s in ("admin-panel", "labtower-overview"): continue
            self.assertIn(s, HELPER.read_text()); self.assertIn(s + ")", p)

    def test_health_skips_disabled_and_home_hides_cards(self):
        self.assertIn("if name in off: continue", (ROOT / "auth" / "admin_panel.py").read_text())
        self.assertIn("/admin/api/disabled", (ROOT / "home" / "home.js").read_text())

    def test_ui_i18n_keys_in_both_languages(self):
        js = (ROOT / "auth" / "static" / "app.js").read_text()
        self.assertEqual(len(re.findall(r"\bmdTitle:", js)), 2)
        self.assertIn("mdToggle", js[js.index("cspRegister({"):])

if __name__ == "__main__":
    unittest.main()
