"""Pausa de alarmas por módulo: el admin del módulo lo pausa 1 h, 4 h, 24 h o hasta reanudar. El módulo sigue leyendo, pero no anota eventos,
cuenta como OK en /api/health (los chequeos conservan su nivel) y el Resumen no muestra sus avisos. Botón en la tarjeta del Resumen y en la
página del módulo (nav.js compartido).
EN: Per-module alarm pause: the module's admin pauses it for 1 h, 4 h, 24 h or until resumed. The module keeps reading, but records no events,
counts as OK in /api/health (the checks keep their level) and the Overview shows none of its warnings. Button on the Overview card and on the
module page (shared nav.js)."""
import time
import unittest
from pathlib import Path

from tests import support
from tests.support import ADMIN, READONLY

ROOT = Path(__file__).resolve().parents[1]
auth = support.auth
panel = support.load("auth/admin_panel.py")


class Store(unittest.TestCase):
    def setUp(self): auth.write_json(auth.MUTES_FILE, {})
    tearDown = setUp

    def test_pause_resume_and_expiry(self):
        now = int(time.time())
        self.assertEqual(auth.mutes(), {})
        auth.set_mute("nas", 3600)
        self.assertAlmostEqual(auth.mute_until("nas"), now + 3600, delta=5)
        auth.set_mute("dns", 0)
        self.assertEqual(auth.mute_until("dns"), 0)                      # until resumed
        auth.set_mute("nas", None)
        self.assertEqual(auth.mutes(), {"dns": 0})
        auth.write_json(auth.MUTES_FILE, {"wan": now - 1, "vpn": now + 60, "bogus": 0, "net": "x", "pve": True})
        self.assertEqual(auth.mutes(), {"vpn": now + 60})                # expired, unknown and malformed entries are left out

    def test_only_known_modules_and_durations(self):
        for mod, f in (("wol", 3600), ("overview", 0), ("admin", 0), ("nas", 60), ("nas", True), ("nas", "3600"), ("nas", -1)):
            with self.assertRaises(ValueError, msg=(mod, f)): auth.set_mute(mod, f)
        self.assertEqual(auth.mutes(), {})

    def test_no_events_while_paused(self):
        tag = f"pause-test-{time.time()}"
        auth.set_mute("nas", 3600)
        auth.record_event("nas", "crit", tag + " a")
        auth.record_event("dns", "warn", tag + " b")
        auth.set_mute("nas", None)
        auth.record_event("nas", "info", tag + " c")
        got = [e["tx"] for e in auth.read_events(None, 300) if e.get("tx", "").startswith(tag)]
        self.assertEqual(sorted(got), [tag + " b", tag + " c"])

    def test_health_counts_ok_but_keeps_the_checks(self):
        checks = {"poll": auth.chk(auth.FAIL, "down"), "disk": auth.chk(auth.OK)}
        self.assertEqual(auth.health_reply("nas", checks, True)[0], 503)
        auth.set_mute("nas", 0)
        code, body = auth.health_reply("nas", checks, True)
        self.assertEqual((code, body["status"], body["muted"], body["checks"]["poll"]["level"]), (200, "ok", 0, auth.FAIL))
        self.assertEqual(auth.health_reply("nas", checks, None), (200, {"status": "ok", "muted": True}))
        self.assertNotIn("muted", auth.health_reply("dns", checks, True)[1])


class Rpc(unittest.TestCase):
    def test_modules_read_the_pauses(self):
        authrpc = support.load("auth/authrpc.py")
        auth.write_json(auth.MUTES_FILE, {})
        auth.set_mute("wan", 0)
        try:
            self.assertEqual(authrpc.Service(auth, identify=lambda uid: "wan").handle("wan", {"op": "mutes"}), {"mutes": {"wan": 0}})
            self.assertEqual(authrpc.Service(auth).handle("someone", {"op": "mutes"}), {"error": "forbidden"})
        finally: auth.write_json(auth.MUTES_FILE, {})


class Schedules(unittest.TestCase):
    """Pausas programadas semanales en la hora local del servidor. / Weekly scheduled pauses in the server's local time."""
    def setUp(self): auth.write_json(auth.MUTES_FILE, {}); auth.write_json(auth.SCHED_FILE, {})
    tearDown = setUp

    @staticmethod
    def at(wday_hm, base=None):
        """Epoch of the next local time with that weekday (0 = Monday), hour and minute."""
        wd, h, mi = wday_hm
        lt = time.localtime(base or time.time())
        t = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, h, mi, 0, 0, 0, -1))
        return int(t + ((wd - lt.tm_wday) % 7) * 86400)

    def test_validation(self):
        ok = {"d": [6, 6, 0], "s": 180, "dur": 120}
        self.assertEqual(auth.sched_clean([ok]), [{"d": [0, 6], "s": 180, "dur": 120}])
        for bad in ({**ok, "d": []}, {**ok, "d": [7]}, {**ok, "d": [True]}, {**ok, "s": 1440}, {**ok, "s": "3"}, {**ok, "dur": 45}, {**ok, "dur": 0}, "x"):
            self.assertIsNone(auth.sched_clean([bad]), bad)
        self.assertIsNone(auth.sched_clean([ok] * 8)); self.assertIsNone(auth.sched_clean("x"))

    def test_window_and_midnight(self):
        w = [{"d": [6], "s": 23 * 60, "dur": 120}]                       # Sunday 23:00 for 2 h: crosses into Monday
        start = self.at((6, 23, 0))
        self.assertEqual(auth.sched_end(w, start + 30 * 60), start + 7200)
        self.assertEqual(auth.sched_end(w, start + 90 * 60), start + 7200)   # Monday 00:30, still inside
        self.assertIsNone(auth.sched_end(w, start - 60)); self.assertIsNone(auth.sched_end(w, start + 7200))

    def test_scheduled_pause_and_manual_resume(self):
        now = int(time.time()); lt = time.localtime(now)
        auth.set_schedule("dns", [{"d": [lt.tm_wday], "s": lt.tm_hour * 60 + lt.tm_min, "dur": 60}])
        end = auth.mute_until("dns"); self.assertTrue(end and now < end <= now + 3600)
        self.assertEqual(auth.mute_schedules()["dns"][0]["dur"], 60)
        auth.set_mute("dns", 0); self.assertEqual(auth.mute_until("dns"), 0)          # "until resumed" wins over the window
        auth.set_mute("dns", None); self.assertIsNone(auth.mute_until("dns"))         # resumed by hand: the rest of the window is skipped
        auth.set_schedule("dns", []); self.assertEqual(auth.mute_schedules(), {})
        with self.assertRaises(ValueError): auth.set_schedule("dns", [{"d": [1], "s": 0, "dur": 7}])
        with self.assertRaises(ValueError): auth.set_schedule("admin", [])

    def test_backups_and_nav(self):
        for f in ("debian/preinst", "debian/prerm", "scripts/teleporter.sh"):
            self.assertIn("mute_schedules.json", (ROOT / f).read_text(encoding="utf-8"), f)
        nav = (ROOT / "assets/nav.js").read_text(encoding="utf-8")
        self.assertIn("function schedEdit(m, mod, done)", nav); self.assertIn("{module: mod, schedule: sched}", nav)


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.srv = support.Server(panel.H)
    @classmethod
    def tearDownClass(cls): cls.srv.close()
    def setUp(self):
        auth.write_json(auth.MUTES_FILE, {})
        self.adm = support.make_user("mute_admin", ADMIN)
        self.ro = support.make_user("mute_ro", READONLY)
        self.nas_adm = support.make_user("mute_nas", {**READONLY, "nas": "admin"})
    def tearDown(self): auth.write_json(auth.MUTES_FILE, {})

    def test_read_needs_a_session_and_lists_what_it_can_pause(self):
        self.assertEqual(self.srv.call("GET", "/api/mutes")[0], 401)
        code, d = self.srv.call("GET", "/api/mutes", token=self.ro)
        self.assertEqual((code, d["mutes"], d["can"]), (200, {}, []))
        self.assertEqual(self.srv.call("GET", "/api/mutes", token=self.nas_adm)[1]["can"], ["nas"])
        self.assertEqual(self.srv.call("GET", "/api/mutes", token=self.adm)[1]["can"], list(auth.MUTABLE))

    def test_only_the_module_admin_pauses_it(self):
        self.assertEqual(self.srv.call("POST", "/api/mutes", {"module": "nas", "for": 3600})[0], 401)
        self.assertEqual(self.srv.call("POST", "/api/mutes", {"module": "nas", "for": 3600}, token=self.ro)[0], 403)
        self.assertEqual(self.srv.call("POST", "/api/mutes", {"module": "dns", "for": 3600}, token=self.nas_adm)[0], 403)
        code, d = self.srv.call("POST", "/api/mutes", {"module": "nas", "for": 14400}, token=self.nas_adm)
        self.assertEqual((code, list(d["mutes"])), (200, ["nas"]))
        self.assertEqual(auth.read_audit(5, "mute_nas", "alarms_paused")[0]["d"], "4 h")
        code, d = self.srv.call("POST", "/api/mutes", {"module": "nas", "for": None}, token=self.nas_adm)
        self.assertEqual((code, d["mutes"]), (200, {}))
        self.assertTrue(auth.read_audit(5, "mute_nas", "alarms_resumed"))

    def test_schedule_api(self):
        auth.write_json(auth.SCHED_FILE, {})
        w = [{"d": [6], "s": 180, "dur": 120}]
        self.assertEqual(self.srv.call("POST", "/api/mutes", {"module": "nas", "schedule": w}, token=self.ro)[0], 403)
        self.assertEqual(self.srv.call("POST", "/api/mutes", {"module": "nas", "schedule": [{"d": [], "s": 0, "dur": 60}]}, token=self.nas_adm)[0], 400)
        code, d = self.srv.call("POST", "/api/mutes", {"module": "nas", "schedule": w}, token=self.nas_adm)
        self.assertEqual((code, d["schedules"]), (200, {"nas": w}))
        self.assertEqual(self.srv.call("GET", "/api/mutes", token=self.ro)[1]["schedules"], {"nas": w})
        self.assertEqual(auth.read_audit(5, "mute_nas", "alarm_schedule_saved")[0]["d"], "1")
        auth.write_json(auth.SCHED_FILE, {})

    def test_rejects_bad_input(self):
        for body in ({"module": "wol", "for": 0}, {"module": "x", "for": 0}, {"module": "nas", "for": 60}, {"module": "nas", "for": "0"}, {"module": "nas", "for": False}):
            self.assertEqual(self.srv.call("POST", "/api/mutes", body, token=self.adm)[0], 400, body)
        self.assertEqual(self.srv.call("POST", "/api/mutes", {"module": "nas", "for": 3600}, token=self.adm,
                                       headers={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(auth.mutes(), {})


class Aggregate(unittest.TestCase):
    def setUp(self):
        auth.write_json(auth.MUTES_FILE, {})
        self.old = panel._module_health
        bad = {"status": "fail", "checks": {"poll": {"level": "fail", "detail": "down"}}}
        panel._module_health = lambda name, port, tok: None if name == "dns" else dict(bad) if name == "nas" else {"status": "ok", "checks": {}}
    def tearDown(self):
        panel._module_health = self.old; auth.write_json(auth.MUTES_FILE, {})

    def test_paused_modules_count_as_ok(self):
        c = panel.health_report(None, True)[1]["checks"]
        self.assertEqual((c["nas"]["level"], c["dns"]["level"]), (auth.FAIL, auth.FAIL))
        auth.set_mute("nas", 0); auth.set_mute("dns", 3600)
        code, body = panel.health_report(None, True)
        self.assertEqual((code, body["checks"]["nas"]["level"], body["checks"]["dns"]["level"]), (200, auth.OK, auth.OK))
        self.assertEqual((body["modules"]["nas"]["status"], body["modules"]["nas"]["muted"]), ("ok", 0))
        self.assertEqual(panel.health_report(None, False)[1]["modules"]["nas"], {"status": "ok", "muted": 0})

    def test_a_stale_pause_from_the_module_is_dropped(self):
        panel._module_health = lambda name, port, tok: {"status": "ok", "muted": 0, "checks": {"poll": {"level": "warn"}}}
        body = panel.health_report(None, True)[1]
        self.assertEqual((body["modules"]["nas"]["status"], "muted" in body["modules"]["nas"]), ("degraded", False))


class Pages(unittest.TestCase):
    def test_shared_nav_has_the_button_and_the_paused_state(self):
        js = (ROOT / "assets/nav.js").read_text(encoding="utf-8")
        for k in ("var STD = '#gmute, #gmt,", "me.permissions[self] === 'admin'", "fetch('/admin/api/mutes'", "[[tr.mH1, 3600], [tr.mH4, 14400], [tr.mH24, 86400], [tr.mInf, 0]]",
                  "if (h && h.muted != null) return 'pause';", "window.labMute = {", "placeMute();"):
            self.assertIn(k, js, k)
        self.assertIn(".gmute-menu{", (ROOT / "assets/nav.css").read_text(encoding="utf-8"))

    def test_overview_drops_the_warnings_of_a_paused_module(self):
        js = (ROOT / "overview/static/app.js").read_text(encoding="utf-8")
        for k in ("if(muted(CARD_MOD[id])){issues.length=n0;sev='ok'}", "jobs.mu=jget('/admin/api/mutes').catch(()=>null)",
                  "filter(i=>!muted(RULE_MOD[i.m]))", "muteDecor(mods)", "MUT.can.includes(mod)"):
            self.assertIn(k, js, k)
        self.assertEqual(js.count(",issues.length,"), 9)                   # every card records where its warnings start

    def test_home_and_cli_show_the_pause(self):
        self.assertIn("level = d.muted ? 'paused'", (ROOT / "home/home.js").read_text(encoding="utf-8"))
        self.assertIn('alarms paused', (ROOT / "scripts/labtower-health").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
