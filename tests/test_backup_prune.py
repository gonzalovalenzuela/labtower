"""Limpieza de /var/backups/labtower: preinst y prerm conservan las 5 copias más nuevas de cada archivo (y la history.db más grande);
prerm copia solo al desinstalar; el Teleporter conserva las 5 copias previas a restaurar más nuevas.
EN: /var/backups/labtower cleanup: preinst and prerm keep the 5 newest copies of each file (and the largest history.db); prerm copies only on
    uninstall; the Teleporter keeps the 5 newest pre-restore copies."""
import os
import re
import shutil
import subprocess  # nosec B404 - runs the package's own shell function on a temporary folder
import tempfile
import unittest

from tests import support


def func(path):
    s = (support.ROOT / path).read_text(encoding="utf-8")
    m = re.search(r"(?ms)^KEEP_BAK=5\nprune_bak\(\) \{.*?^\}\n", s)
    return m.group(0) if m else None


@unittest.skipUnless(shutil.which("sh") and subprocess.run(["find", "/", "-maxdepth", "0", "-printf", ""], capture_output=True, check=False).returncode == 0,
                     "needs GNU find (-printf)")
class Prune(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)
    def touch(self, name, size=1):
        with open(os.path.join(self.d, name), "wb") as f:
            f.write(b"x" * size)

    def test_keeps_five_newest_per_file_and_largest_history(self):
        for i in range(1, 9):
            self.touch(f"switches.db.20261030_2034{i:02d}.bak")
            self.touch(f"history.db.20261030_2034{i:02d}.bak", 5000 if i == 1 else 10)
        self.touch("users.json.20261030_203401.bak")
        self.touch("metrics.db.pre-isolation.20250101_000000")          # other names are not touched
        self.touch("pre-restore-20261030_203401.tar.gz")
        subprocess.run(["sh", "-c", func("debian/preinst") + 'prune_bak "$1"', "sh", self.d], check=True)  # nosec B603 B607
        left = sorted(os.listdir(self.d))
        self.assertEqual([f for f in left if f.startswith("switches.db")], [f"switches.db.20261030_2034{i:02d}.bak" for i in range(4, 9)])
        self.assertEqual([f for f in left if f.startswith("history.db")],
                         ["history.db.20261030_203401.bak"] + [f"history.db.20261030_2034{i:02d}.bak" for i in range(4, 9)])
        for f in ("users.json.20261030_203401.bak", "metrics.db.pre-isolation.20250101_000000", "pre-restore-20261030_203401.tar.gz"):
            self.assertIn(f, left)

    def test_missing_folder_is_fine(self):
        subprocess.run(["sh", "-c", func("debian/preinst") + 'prune_bak "$1"', "sh", os.path.join(self.d, "nope")], check=True)  # nosec B603 B607


class Scripts(unittest.TestCase):
    def test_same_cleanup_in_preinst_and_prerm(self):
        self.assertIsNotNone(func("debian/preinst"))
        self.assertEqual(func("debian/preinst"), func("debian/prerm"))
        for f in ("debian/preinst", "debian/prerm"):
            self.assertRegex((support.ROOT / f).read_text(encoding="utf-8"), r'(?m)^prune_bak "\$BACKUP_DIR"$')

    def test_prerm_copies_only_on_remove(self):
        self.assertIn('if [ "$1" = remove ] && command -v runuser', (support.ROOT / "debian/prerm").read_text(encoding="utf-8"))

    def test_teleporter_keeps_five_pre_restore_copies(self):
        s = (support.ROOT / "scripts/teleporter.sh").read_text(encoding="utf-8")
        self.assertIn("-name 'pre-restore-[0-9]*_[0-9]*.tar.gz' -printf '%f\\n' 2>/dev/null | sort -r | tail -n +6", s)
