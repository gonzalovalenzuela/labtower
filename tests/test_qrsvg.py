"""2.1.3i: generador de QR propio (sin librerías) para el 2FA."""
import re, sys, unittest
from tests.support import ROOT
sys.path.insert(0, str(ROOT / "auth"))
import qrsvg  # noqa: E402

URI = "otpauth://totp/LabTower:admin?secret=JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP&issuer=LabTower"

class Qr(unittest.TestCase):
    def test_size_and_finders(self):
        m = qrsvg.encode(URI); n = len(m)
        self.assertEqual((n - 17) % 4, 0); self.assertTrue(21 <= n <= 57)
        for ox, oy in ((0, 0), (n - 7, 0), (0, n - 7)):                     # 7x7 finder: dark ring, light ring, dark 3x3
            self.assertTrue(all(m[oy][ox + i] and m[oy + 6][ox + i] and m[oy + i][ox] and m[oy + i][ox + 6] for i in range(7)))
            self.assertTrue(all(m[oy + 2 + a][ox + 2 + b] for a in range(3) for b in range(3)))
        self.assertTrue(all(m[6][i] == (i % 2 == 0) for i in range(8, n - 8)))   # timing row
        self.assertTrue(m[n - 8][8])                                              # the always-dark module

    def test_version_grows_and_limit(self):
        self.assertEqual(len(qrsvg.encode("a")), 21)
        self.assertGreater(len(qrsvg.encode("x" * 100)), len(qrsvg.encode("x" * 20)))
        with self.assertRaises(ValueError): qrsvg.encode("x" * 500)

    def test_svg_is_plain_and_safe(self):
        s = qrsvg.svg(URI)
        self.assertRegex(s, r'^<svg xmlns="http://www.w3.org/2000/svg"[^<]*><rect[^<]*/><path d="[MhvzL0-9, .\-]*" fill="#000"/></svg>$')
        self.assertNotIn("script", s.lower()); self.assertNotIn("<style", s.lower())

    def test_decodes_with_a_real_reader_when_available(self):
        try: import cv2, numpy as np
        except ImportError: self.skipTest("opencv not installed")
        m = qrsvg.encode(URI); n, s, b = len(m), 8, 4
        img = np.full(((n + 2 * b) * s,) * 2, 255, np.uint8)
        for y in range(n):
            for x in range(n):
                if m[y][x]: img[(y + b) * s:(y + b + 1) * s, (x + b) * s:(x + b + 1) * s] = 0
        self.assertEqual(cv2.QRCodeDetector().detectAndDecode(img)[0], URI)

if __name__ == "__main__":
    unittest.main()
