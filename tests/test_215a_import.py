"""2.1.5a: el selector de «Subir respaldo» del Admin Panel acepta también los .gpg (los respaldos descargados salen cifrados)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class ImportPicker(unittest.TestCase):
    def test_file_picker_accepts_gpg(self):
        html = (ROOT / "auth/static/index.html").read_text()
        accept = re.search(r'id="tp-file" accept="([^"]*)"', html).group(1).split(",")
        for ext in (".gz", ".tgz", ".gpg"):
            self.assertIn(ext, accept)
    def test_gpg_files_ask_for_the_passphrase(self):
        js = (ROOT / "auth/static/app.js").read_text()
        self.assertIn(r"/\.gpg$/i.test(file.name)", js)

if __name__ == "__main__": unittest.main()
