"""labtower-sftp-backup verify: comprueba en el storage (simulado con un `sftp` falso) que hay una copia reciente / checks on the (fake) storage."""
import json, os, shutil, stat, subprocess, tempfile, time, unittest
from pathlib import Path
from tests import support

ROOT = support.ROOT
SCRIPT = ROOT / "scripts" / "labtower-sftp-backup"
HOST = "pibox"

def stamp(hours_ago):
    return time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time() - hours_ago * 3600))

@unittest.skipUnless(os.geteuid() == 0 and shutil.which("bash"), "needs root and bash")
class Verify(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="sftpv-"))
        (self.d / "bin").mkdir()
        self.listing = self.d / "listing.txt"; self.rc = self.d / "rc"
        fake = self.d / "bin" / "sftp"
        fake.write_text(f'#!/bin/bash\ncat > /dev/null\nif [ -f "{self.rc}" ]; then echo "Permission denied (publickey)."; exit 255; fi\ncat "{self.listing}"\n')
        fake.chmod(0o755)
        (self.d / "bin" / "hostname").write_text(f'#!/bin/bash\necho {HOST}\n'); (self.d / "bin" / "hostname").chmod(0o755)
        (self.d / "key").write_text("k"); 
        self.conf = self.d / "backup.conf"; self.out = self.d / "backup.verify"
        self.write_conf()

    def write_conf(self, extra=""):
        self.conf.write_text(f"SFTP_HOST=nas.lan\nSFTP_USER=bob\nSFTP_DIR=bk\nSFTP_KEY={self.d/'key'}\nKNOWN_HOSTS={self.d/'kh'}\n"
                             f"VERIFY_FILE={self.out}\nSTATUS_FILE={self.d/'status'}\n{extra}")

    def files(self, *rows):
        self.listing.write_text("sftp> ls -l bk\n" + "".join(f"-rw-r--r--    1 bob      users    {size:>9} Oct 30 03:17 {name}\n" for name, size in rows))

    def run_verify(self):
        env = dict(os.environ, PATH=f"{self.d/'bin'}:{os.environ['PATH']}", LABTOWER_BACKUP_CONF=str(self.conf))
        r = subprocess.run(["bash", str(SCRIPT), "verify"], env=env, capture_output=True, text=True, timeout=60)
        res = json.loads(self.out.read_text()) if self.out.exists() else None
        return r.returncode, res, r.stdout + r.stderr

    def name(self, h, ext=".tar.gz.gpg"): return f"labtower-auto-{HOST}-{stamp(h)}{ext}"

    def test_recent_copy_is_ok(self):
        self.files((self.name(30), 500), (self.name(6), 700), (self.name(54), 400), (".labtower-sftp-backup-test-1", 5), (self.name(2) + ".part", 9))
        rc, res, _ = self.run_verify()
        self.assertEqual(rc, 0); self.assertTrue(res["ok"]); self.assertEqual((res["count"], res["size"], res["age_h"]), (3, 700, 6))
        self.assertEqual(stat.S_IMODE(self.out.stat().st_mode), 0o644)

    def test_old_copy_fails(self):
        self.files((self.name(60), 500))
        rc, res, _ = self.run_verify()
        self.assertEqual(rc, 1); self.assertFalse(res["ok"]); self.assertIn("60 h old", res["message"])

    def test_limit_is_configurable(self):
        self.files((self.name(60), 500)); self.write_conf("VERIFY_MAX_AGE=72\n")
        self.assertEqual(self.run_verify()[0], 0)

    def test_empty_copy_fails(self):
        self.files((self.name(1), 0))
        rc, res, _ = self.run_verify(); self.assertEqual(rc, 1); self.assertIn("empty", res["message"])

    def test_no_copies_and_other_hosts_files_do_not_count(self):
        self.files(("labtower-auto-otherhost-" + stamp(1) + ".tar.gz.gpg", 500), ("notes.txt", 5))
        rc, res, _ = self.run_verify(); self.assertEqual(rc, 1); self.assertIn("no copy", res["message"])

    def test_unreachable_storage_fails_and_says_so(self):
        self.files((self.name(1), 500)); self.rc.write_text("x")
        rc, res, _ = self.run_verify(); self.assertEqual(rc, 1); self.assertIn("cannot list", res["message"])

    def test_not_configured_does_nothing(self):
        self.write_conf(); self.conf.write_text(self.conf.read_text().replace("SFTP_USER=bob", "SFTP_USER="))
        rc, res, _ = self.run_verify(); self.assertEqual(rc, 0); self.assertIsNone(res)

    def test_bad_config_value_is_rejected(self):
        self.files((self.name(1), 500)); self.write_conf("VERIFY_MAX_AGE=abc\n")
        rc, res, _ = self.run_verify(); self.assertEqual(rc, 1); self.assertIn("VERIFY_MAX_AGE", res["message"])

if __name__ == "__main__":
    unittest.main()
