"""Every systemd service is called labtower-<module>; the installer, the scripts and the docs agree on the names."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW = ["labtower-wol", "labtower-ups", "labtower-auth", "labtower-net", "labtower-pve", "labtower-nas", "labtower-dns", "labtower-wan", "labtower-vpn", "labtower-overview"]
OLD = ["wol-console", "admin-panel", "net-monitor", "proxmox-monitor", "nas-monitor", "dns-monitor", "wan-monitor", "vpn-monitor"]
r = lambda p: (ROOT / p).read_text()


class ServiceNames(unittest.TestCase):
    def test_installer_names_follow_the_pattern(self):
        names = re.findall(r'(?m)^install_service "([^"]+)"', r("debian/postinst"))
        self.assertEqual(names, NEW)

    def test_the_service_lists_are_the_same_everywhere(self):
        self.assertIn(" ".join(NEW), r("debian/postinst"))
        for f in ("scripts/teleporter.sh", "scripts/labtower-https"):
            with self.subTest(file=f):
                self.assertEqual(re.search(r'(?m)^SERVICES="([^"]+)"', r(f)).group(1).split(), NEW)
        self.assertTrue(r("debian/prerm").split("for svc in ")[1].startswith(" ".join(NEW)))

    def test_every_module_maps_to_its_labtower_service(self):
        for m, svc in (("wol", "labtower-wol"), ("nut", "labtower-ups"), ("net", "labtower-net"), ("pve", "labtower-pve"),
                       ("nas", "labtower-nas"), ("dns", "labtower-dns"), ("wan", "labtower-wan"), ("vpn", "labtower-vpn")):
            with self.subTest(module=m):
                self.assertRegex(r("scripts/labtower-modules"), rf"{m}\) echo {svc};;")
                self.assertIn(f"{svc}) m={m};;", r("debian/postinst"))
                self.assertIn(f"{svc}) m={m};;", r("scripts/teleporter.sh"))

    def test_upgrade_removes_the_old_names(self):
        p = r("debian/postinst")
        body = p[p.index("migrate_legacy_unit_names() {"):]
        body = body[:body.index("\n}\n")]
        for o in OLD: self.assertIn(o, body)
        self.assertIn('grep -qE "Pi Console|LabTower"', body)                 # only a LabTower file is touched
        self.assertIn("\nmigrate_legacy_unit_names\n", p)
        for o in OLD:                                                          # purge and remove also clean the old names
            self.assertIn(o, r("debian/postrm")); self.assertIn(o, r("debian/prerm"))

    def test_no_old_name_is_used_as_a_service_in_the_scripts_or_docs(self):
        for f in ("scripts/teleporter.sh", "scripts/labtower-https", "scripts/labtower-modules", "README.md", "README.en.md", "docs/CT.md"):
            t = r(f)
            for o in OLD:
                with self.subTest(file=f, name=o):
                    self.assertNotRegex(t, rf"(systemctl|journalctl)[^\n]*(?<![/\w-]){re.escape(o)}(?![/\w.-])")
                    self.assertNotRegex(t, rf"`{re.escape(o)}` \|")

    def test_shell_syntax_of_the_installer_scripts(self):
        for f in ("debian/postinst", "debian/prerm", "debian/postrm", "scripts/teleporter.sh", "scripts/labtower-modules", "scripts/labtower-https"):
            with self.subTest(file=f):
                self.assertEqual(subprocess.run(["bash", "-n", str(ROOT / f)], capture_output=True, text=True, check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
