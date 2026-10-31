"""2.1.4b: edad de batería en meses, purga de equipos sin conexión, color por velocidad, pausa de Pi-hole en el Resumen."""
import datetime, json, re, subprocess, unittest
from tests import support
from tests.support import ADMIN

bat = support.load("nut-monitor/battery.py")

class Months(unittest.TestCase):
    def test_age_months(self):
        t = datetime.date(2026, 10, 31)
        self.assertEqual(bat.age_months(datetime.date(2026, 10, 1), t), 0)
        self.assertEqual(bat.age_months(datetime.date(2026, 9, 30), t), 1)
        self.assertEqual(bat.age_months(datetime.date(2026, 9, 15), t), 1)
        self.assertEqual(bat.age_months(datetime.date(2025, 11, 30), t), 11)
        self.assertEqual(bat.age_months(datetime.date(2025, 11, 1), t), 11)
        self.assertIsNone(bat.age_months(datetime.date(2027, 1, 1), t))
        self.assertIsNone(bat.age_months(None, t))
    def test_best_date_ignores_implausible(self):
        t = datetime.date(2026, 10, 31)
        self.assertEqual(bat.best_battery_date({"battery.date": "2001/09/25", "battery.mfr.date": "2026/09/30"}, t), datetime.date(2026, 9, 30))
        self.assertIsNone(bat.best_battery_date({"battery.date": "2001/09/25"}, t))

class Purge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.net = support.load("net-monitor/server.py")
    def test_purge_offline(self):
        now = 1_000_000_000
        h = {"a": {"online": False, "last_seen": now - 40 * 86400}, "b": {"online": False, "last_seen": now - 5 * 86400},
             "c": {"online": True, "last_seen": now - 90 * 86400}, "d": {"online": False}}
        gone = self.net.purge_offline(h, 30, now)
        self.assertEqual(gone, ["a"]); self.assertEqual(sorted(h), ["b", "c", "d"])
        self.assertEqual(self.net.purge_offline(h, 0, now), [])
    def test_endpoint(self):
        srv = support.Server(self.net.H)
        try:
            tok = support.make_user("purgeadm", ADMIN)
            hd = {"Origin": "http://127.0.0.1"}
            for bad in (-1, "x", 99999, None):
                st, _ = srv.call("POST", "/api/hosts/purge", {"days": bad}, token=tok, headers=hd)
                self.assertEqual(st, 400, bad)
            st, d = srv.call("POST", "/api/hosts/purge", {"days": 30}, token=tok, headers=hd)
            self.assertEqual(st, 200); self.assertEqual(d["days"], 30)
            st, d = srv.call("GET", "/api/config", None, token=tok)
            self.assertEqual(d["purge_days"], 30)
            st, _ = srv.call("POST", "/api/hosts/purge", {"days": 0}, token=tok, headers=hd)
            self.assertEqual(st, 200)
        finally:
            srv.close()

class Front(unittest.TestCase):
    def run_js(self, src, expr):
        out = subprocess.run(["node", "-e", src + f"console.log(JSON.stringify({expr}))"], capture_output=True, text=True, check=True)
        return json.loads(out.stdout)
    def test_speed_classes(self):
        s = open("net-monitor/static/switches.js", encoding="utf-8").read()
        fn = re.search(r"const SPD_CLS = .*?;\n", s).group(0)
        self.assertEqual([self.run_js(fn, f"SPD_CLS({m})") for m in (0, 10, 100, 1000, 2500, 10000)],
                         ["", "s10m", "s100m", "s1g", "s25g", "s10g"])
    def test_overview_pause_button_registered(self):
        s = open("overview/static/app.js", encoding="utf-8").read()
        self.assertIn("document.addEventListener('click',dnsAct)", s)
        self.assertIn("'/dns/api/dns/'", s); self.assertIn("/blocking", s)
        self.assertEqual(s.count("dnsPause:"), 2)
    def test_proxmox_toggle(self):
        a = open("proxmox-monitor/static/app.js", encoding="utf-8").read(); h = open("proxmox-monitor/static/index.html", encoding="utf-8").read()
        self.assertIn("toggleStopped", a); self.assertIn('data-on-click="toggleStopped"', h)
        self.assertEqual(a.count("hideStopped:"), 2)

if __name__ == "__main__":
    unittest.main()
