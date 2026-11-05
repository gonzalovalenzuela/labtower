"""WAN Monitor: período de las pruebas de velocidad en minutos u horas (antes solo horas)."""
import re
import unittest
from pathlib import Path

from tests import support

m = support.load("wan-monitor/server.py")
ROOT = Path(__file__).resolve().parents[1]


class Period(unittest.TestCase):
    def v(self, sp, cur=None):
        return m.validate({"speed": sp}, cur, resolve=False)["speed"]

    def test_default_is_12_hours_in_minutes(self):
        self.assertEqual(m.validate({}, resolve=False)["speed"]["every_minutes"], 720)
        self.assertNotIn("every_hours", m.validate({}, resolve=False)["speed"])

    def test_minutes_are_accepted(self):
        self.assertEqual(self.v({"every_minutes": 45})["every_minutes"], 45)
        self.assertEqual(self.v({"every_minutes": 5})["every_minutes"], 5)

    def test_old_hours_are_converted_and_never_kept(self):
        sp = self.v({"every_hours": 6})
        self.assertEqual(sp["every_minutes"], 360); self.assertNotIn("every_hours", sp)

    def test_a_stored_config_in_hours_keeps_its_value(self):
        cur = {"speed": {"every_hours": 1}}                       # what wan.json looked like before
        self.assertEqual(m.validate(cur, resolve=False)["speed"]["every_minutes"], 60)

    def test_minutes_win_when_both_come(self):
        self.assertEqual(self.v({"every_hours": 6, "every_minutes": 90})["every_minutes"], 90)

    def test_hours_in_the_body_replace_minutes_already_saved(self):
        cur = m.validate({"speed": {"every_minutes": 45}}, resolve=False)
        self.assertEqual(m.validate({"speed": {"every_hours": 2}}, cur, resolve=False)["speed"]["every_minutes"], 120)

    def test_zero_means_never_and_the_minimum_is_five_minutes(self):
        self.assertIsNone(m.next_speedtest(m.validate({"speed": {"every_minutes": 0}}, resolve=False)))
        for bad in (1, 4, -1, 43201, "x"):
            with self.assertRaises(ValueError, msg=bad): self.v({"every_minutes": bad})

    def test_next_test_uses_minutes(self):
        cfg = m.validate({"speed": {"every_minutes": 30}}, resolve=False)
        m.S.speed_last = 1000
        try: self.assertEqual(m.next_speedtest(cfg), 1000 + 1800)
        finally: m.S.speed_last = 0


class Page(unittest.TestCase):
    def test_the_page_has_the_unit_selector_and_the_warning(self):
        html = (ROOT / "wan-monitor/static/index.html").read_text(); js = (ROOT / "wan-monitor/static/app.js").read_text()
        self.assertIn('id="s-sp-unit"', html); self.assertIn('id="s-sp-warn"', html)
        self.assertRegex(js, r"every_minutes:.*s-sp-unit")
        self.assertEqual(len(re.findall(r'"setEveryWarn"', js)), 2)            # English and Spanish
        self.assertIn("m>0&&m<30", js)


if __name__ == "__main__":
    unittest.main()
