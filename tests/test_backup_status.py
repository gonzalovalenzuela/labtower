"""Estado del último respaldo SFTP para la tarjeta «LabTower Server» del Resumen."""
import os, tempfile, unittest, pathlib
from tests import support

auth = support.load("auth/auth.py")

class BackupStatus(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.st, self.cf = os.path.join(self.d, "status"), os.path.join(self.d, "conf")
        os.environ["LABTOWER_BACKUP_STATUS"], os.environ["LABTOWER_BACKUP_CONF"] = self.st, self.cf
        self.addCleanup(lambda: [os.environ.pop(k, None) for k in ("LABTOWER_BACKUP_STATUS", "LABTOWER_BACKUP_CONF")])

    def test_not_configured(self):
        self.assertEqual(auth.backup_status()["state"], "off")
        pathlib.Path(self.cf).write_text("SFTP_HOST=h\nSFTP_USER=\n")
        self.assertEqual(auth.backup_status()["state"], "off")

    def test_configured_but_never_run(self):
        pathlib.Path(self.cf).write_text("SFTP_USER=bob\n")
        self.assertEqual(auth.backup_status()["state"], "pending")

    def test_ok_and_failed(self):
        pathlib.Path(self.st).write_text('{"time": 1700000000, "ok": true, "file": "a.gpg", "size": 5, "message": "ok"}')
        r = auth.backup_status(); self.assertEqual((r["state"], r["time"], r["file"]), ("ok", 1700000000, "a.gpg"))
        pathlib.Path(self.st).write_text('{"time": 1700000000, "ok": false, "file": "", "size": 0, "message": "SSH key not found"}')
        r = auth.backup_status(); self.assertEqual((r["state"], r["message"]), ("fail", "SSH key not found"))

    def test_empty_or_corrupt_file_is_not_an_error(self):
        for txt in ("", "{", "[1]"):
            pathlib.Path(self.st).write_text(txt)
            self.assertEqual(auth.backup_status(), {"state": "unknown"})

    def test_included_in_system_stats(self):
        self.assertIn("backup", auth.system_stats())

if __name__ == "__main__":
    unittest.main()
