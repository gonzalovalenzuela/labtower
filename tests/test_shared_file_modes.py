"""2.1.3i: los archivos que un módulo publica para otro (modo 0640) no pueden quedar 0600 por el umask 077 de los servicios."""
import os, stat, tempfile, unittest
from pathlib import Path
from tests.support import auth

class Modes(unittest.TestCase):
    def test_640_survives_umask_077(self):
        d = Path(tempfile.mkdtemp()); old = os.umask(0o077)
        try:
            p = d / "hosts.json"
            auth.write_json(p, {"a": 1}, mode=0o640)
            auth.write_json(p, {"a": 2}, mode=0o640)                 # second write also leaves the .bak
            self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o640)
            self.assertEqual(stat.S_IMODE((d / "hosts.json.bak").stat().st_mode), 0o640)
            auth.write_json(d / "users.json", {}, mode=0o600)
            self.assertEqual(stat.S_IMODE((d / "users.json").stat().st_mode), 0o600)
        finally: os.umask(old)

    def test_default_stays_private(self):
        d = Path(tempfile.mkdtemp()); old = os.umask(0o022)
        try:
            auth.atomic_write(d / "x", "1")
            self.assertEqual(stat.S_IMODE((d / "x").stat().st_mode), 0o600)
        finally: os.umask(old)

if __name__ == "__main__":
    unittest.main()
