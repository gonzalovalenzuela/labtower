"""Script labtower-ct (crea el CT de Proxmox) y su guía / script that creates the Proxmox CT, and its guide."""
import re, shutil, subprocess, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "labtower-ct"

def run(*args):
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True)

@unittest.skipUnless(shutil.which("bash"), "bash no está instalado")
class Ct(unittest.TestCase):
    def test_dry_run_builds_the_expected_commands(self):
        r = run("--dry-run", "--version", "2.1.5", "--id", "321", "--hostname", "lt", "--ip", "192.0.2.50/24", "--gw", "192.0.2.1", "--dns", "192.0.2.2", "--vlan", "20", "--bridge", "vmbr1")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("pct create 321 local:vztmpl/debian-12-standard", out)
        self.assertIn("--unprivileged 1 --features nesting=1", out)
        self.assertIn("--net0 name=eth0,bridge=vmbr1,firewall=0,tag=20,ip=192.0.2.50/24,gw=192.0.2.1", out)
        self.assertIn("--nameserver 192.0.2.2", out)
        self.assertIn("--onboot 1", out)
        self.assertIn("deb-builds/labtower_2.1.5_all.deb", out)
        self.assertIn("pct start 321", out)

    def test_defaults_use_dhcp(self):
        r = run("--dry-run", "--version", "2.1.5")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ip=dhcp", r.stdout); self.assertIn("--rootfs local-lvm:8", r.stdout); self.assertIn("--memory 1024", r.stdout)

    def test_rejects_bad_input(self):
        for bad in (["--hostname", "a b"], ["--hostname", "-x"], ["--memory", "1g"], ["--id", "1;reboot"], ["--vlan", "x"], ["--ip", "192.0.2.5"],
                    ["--ip", "1.2.3.4/24;id"], ["--storage", "a b"], ["--url", "http://x/y.deb"], ["--version", "1;2"], ["--nope"]):
            with self.subTest(bad=bad):
                r = run("--dry-run", "--version", "2.1.5", *bad) if "--version" not in bad else run("--dry-run", *bad)
                self.assertNotEqual(r.returncode, 0, r.stdout)

    def test_url_is_used_as_given(self):
        r = run("--dry-run", "--url", "https://example.org/labtower_9_all.deb")
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("https://example.org/labtower_9_all.deb", r.stdout)

    def test_guide_exists_and_matches_the_options(self):
        g = (ROOT / "docs" / "CT.md").read_text()
        for opt in re.findall(r"^\s+--([a-z-]+)\)", SCRIPT.read_text(), re.M):
            if opt in ("help",): continue
            self.assertIn("--" + opt, g, f"la guía no documenta --{opt}")
        self.assertIn("labtower-ct", (ROOT / "README.md").read_text())
        self.assertIn("labtower-ct", (ROOT / "README.en.md").read_text())

if __name__ == "__main__": unittest.main()
