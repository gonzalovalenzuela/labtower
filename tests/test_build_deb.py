"""scripts/build-deb: arma el .deb desde HEAD con dpkg-deb, con el contenido, los permisos y los conffiles esperados, y de forma repetible.
EN: scripts/build-deb: builds the .deb from HEAD with dpkg-deb, with the expected contents, permissions and conffiles, and repeatably."""
import hashlib, shutil, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build-deb"


def head_version():
    r = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:VERSION"], capture_output=True, text=True, check=False)
    return r.stdout.strip() if r.returncode == 0 else None


@unittest.skipUnless(shutil.which("dpkg-deb") and shutil.which("git"), "dpkg-deb or git not installed")
class BuildDeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ver = (ROOT / "VERSION").read_text().strip()
        if head_version() != cls.ver:
            raise unittest.SkipTest("VERSION is not committed yet (build-deb builds from HEAD)")
        cls.out = Path(tempfile.mkdtemp())
        r = subprocess.run(["bash", str(SCRIPT), str(cls.out)], capture_output=True, text=True, timeout=300, check=False)
        if r.returncode != 0: raise AssertionError(r.stderr)
        cls.deb = cls.out / f"labtower_{cls.ver}_all.deb"
        cls.listing = subprocess.run(["dpkg-deb", "-c", str(cls.deb)], capture_output=True, text=True, check=True).stdout.splitlines()
        cls.names = {ln.split()[-1] if " -> " not in ln else ln.split(" -> ")[0].split()[-1]: ln.split()[0] for ln in cls.listing}
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.out, ignore_errors=True)

    def test_version_and_control(self):
        f = lambda k: subprocess.run(["dpkg-deb", "-f", str(self.deb), k], capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual((f("Package"), f("Version"), f("Architecture")), ("labtower", self.ver, "all"))

    def test_contents(self):
        n = self.names
        for want in ("./opt/labtower/VERSION", "./opt/labtower/uptime-monitor/server.py", "./opt/labtower/home/icons/uptime.png",
                     "./etc/nginx/snippets/labtower-site.conf", "./usr/local/bin/teleporter.sh", "./usr/local/bin/teleporter",
                     "./usr/share/doc/labtower/copyright", "./usr/share/doc/labtower/CHANGELOG.md", "./etc/systemd/system/"):
            self.assertIn(want, n, want)
        for bad in ("tests/", "docs/", "assets/", "debian/", "scripts/", "README", "CLAUDE.md", ".github", "__pycache__"):
            self.assertFalse([x for x in n if x.startswith("./opt/labtower/") and bad in x], bad)
        self.assertTrue(n["./usr/local/bin/teleporter"].startswith("l"))

    def test_permissions(self):
        for name, mode in self.names.items():
            if mode.startswith("l"): continue
            want = "drwxr-xr-x" if name.endswith("/") else "-rwxr-xr-x" if name.startswith("./usr/local/bin/") or name == "./opt/labtower/auth/resetpw.py" else "-rw-r--r--"
            self.assertEqual(mode, want, name)
        self.assertTrue(all(" root/root " in ln for ln in self.listing))

    def test_conffiles_are_every_file_in_etc(self):
        conf = subprocess.run(["dpkg-deb", "-I", str(self.deb), "conffiles"], capture_output=True, text=True, check=True).stdout.split()
        etc = sorted(x[1:] for x, m in self.names.items() if x.startswith("./etc/") and m.startswith("-"))
        self.assertEqual(conf, etc); self.assertEqual(len(conf), 5)

    def test_repeatable(self):
        out = Path(tempfile.mkdtemp())
        try:
            subprocess.run(["bash", str(SCRIPT), str(out)], capture_output=True, text=True, timeout=300, check=True)
            sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(sha(out / self.deb.name), sha(self.deb))
        finally: shutil.rmtree(out, ignore_errors=True)


class Guards(unittest.TestCase):
    def test_script_checks_the_three_versions_and_builds_from_head(self):
        s = SCRIPT.read_text()
        for k in ("VERSION", "debian/control", "CHANGELOG.md", "git -C \"$ROOT\" archive --format=tar HEAD", "--root-owner-group", "SOURCE_DATE_EPOCH"):
            self.assertIn(k, s, k)
        self.assertEqual(subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
