"""La tarjeta de IP (ipcard.js) no se ofrece para esta misma máquina: 127.x, ::1 y localhost no están en Net Monitor."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class IpCardLocal(unittest.TestCase):
    def test_every_copy_skips_loopback_targets(self):
        copies = sorted(ROOT.glob("*/static/ipcard.js"))
        self.assertGreaterEqual(len(copies), 8)
        for p in copies:
            js = p.read_text()
            self.assertIn("function isLocal(q)", js, p)
            self.assertIn("!isLocal(t.getAttribute('data-nethost'))", js, p)       # tgt() returns nothing for them: no hover card, no click-through
        self.assertEqual(len({p.read_text() for p in copies}), 1, "the copies must stay identical")


if __name__ == "__main__":
    unittest.main()
