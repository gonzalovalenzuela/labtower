"""Pausa en todos los módulos con equipos vigilados: servidores NUT (UPS Monitor), clusters (Proxmox), servidores DNS, VPN, monitores de
Uptime y switches (botón en la tarjeta). Pausado no se consulta, no avisa en el estado ni en el Resumen y la página lo muestra «Pausado».
La pausa va por su propia ruta, solo admin, y no toca secretos ni huellas fijadas.
EN: Pause in every module with watched devices: NUT servers (UPS Monitor), clusters (Proxmox), DNS servers, VPNs, Uptime monitors and
switches (button on the card). Paused, it is not polled, raises no warning in the status or the Overview and the page shows "Paused".
The pause has its own route, admin only, and leaves secrets and pinned fingerprints alone."""
import json
import unittest
from pathlib import Path

from tests import support
from tests.support import ADMIN, READONLY, auth

ROOT = Path(__file__).resolve().parents[1]
UID = "0f8e7d6c-5b4a-4938-8271-605f4e3d2c1b"

# módulo, archivo, guardar/leer, ruta de la lista y su clave, ruta de pausa, clave de la respuesta, entrada de prueba, secretos que no deben salir
# EN: module, file, save/load, list route and its key, pause route, response key, test entry, secrets that must not leak
CASES = {
    "nut": ("nut-monitor/server.py", "save_servers", "load_servers", "/api/servers?range=none", "servers", "/api/servers/{}/pause", "server",
            {"id": "s-p1", "name": "ups1", "host": "192.0.2.30", "port": 3493}, ()),
    "pve": ("proxmox-monitor/server.py", "save_clusters", "load_clusters", "/api/clusters?hist=0", "clusters", "/api/clusters/{}/pause", "cluster",
            {"id": "c-p1", "name": "pve1", "host": "192.0.2.31", "port": 8006, "user": "ro@pve", "token_name": "t", "token_value": "tok-secret-1",
             "fingerprint": "AB:" * 31 + "AB"}, ("tok-secret-1",)),
    "dns": ("dns-monitor/server.py", "save_servers", "load_servers", "/api/dns?hist=0", "servers", "/api/dns/{}/pause", "dns",
            {"id": "d-p1", "name": "dns1", "type": "pihole", "url": "http://192.0.2.32", "username": "", "password": "dns-secret-1", "timeout": 5,
             "verify_tls": True}, ("dns-secret-1",)),
    "vpn": ("vpn-monitor/server.py", "save_vpn", "load_vpn", "/api/vpn?hist=0", "vpn", "/api/vpn/{}/pause", "vpn",
            {"id": "v-p1", "name": "vpn1", "type": "wireguard", "host": "192.0.2.33", "port": 22, "ssh_user": "ro", "aliases": {}}, ()),
    "uptime": ("uptime-monitor/server.py", "save_monitors", "load_monitors", "/api/monitors?beats=0", "monitors", "/api/monitors/{}/pause", "monitor",
               {"id": UID, "name": "web", "type": "tcp", "host": "192.0.2.34", "port": 443, "interval": 60, "timeout": 10, "down_after": 3}, ()),
}


class Helpers(unittest.TestCase):
    def test_paused_and_set_paused(self):
        self.assertFalse(auth.paused({})); self.assertFalse(auth.paused(None)); self.assertFalse(auth.paused({"enabled": True}))
        d = {"name": "x"}; auth.set_paused(d, True); self.assertIs(d["enabled"], False); self.assertTrue(auth.paused(d))
        auth.set_paused(d, False); self.assertNotIn("enabled", d)


class Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adm = support.make_user("pause_all_adm", ADMIN)
        cls.ro = support.make_user("pause_all_ro", READONLY)

    def each(self):
        for key, (rel, save, load, lst, lkey, route, rkey, entry, secrets) in CASES.items():
            with self.subTest(module=key):
                m = support.load(rel)
                m.DATA_DIR.mkdir(parents=True, exist_ok=True)
                ens = "ensure_monitor" if key == "uptime" else "ensure_poller"
                old_items, old_ens = getattr(m, load)(), getattr(m, ens)
                setattr(m, ens, lambda *a: None)
                getattr(m, save)([json.loads(json.dumps(entry))])
                srv = support.Server(m.H)
                try: yield key, m, srv, getattr(m, load), lst, lkey, route.format(entry["id"]), rkey, entry, secrets
                finally: srv.close(); setattr(m, ens, old_ens); getattr(m, save)(old_items)

    def test_pause_and_resume_everywhere(self):
        for key, m, srv, load, lst, lkey, route, rkey, entry, secrets in self.each():
            st, d = srv.call("POST", route, {"paused": True}, token=self.adm)
            self.assertEqual((st, d[rkey]["paused"]), (200, True), key)
            for sec in secrets: self.assertNotIn(sec, json.dumps(d), key)
            saved = load()[0]
            self.assertIs(saved["enabled"], False)
            self.assertEqual({k: v for k, v in saved.items() if k != "enabled"}, entry, key)       # nothing else changes (token, fingerprint)
            st, d = srv.call("GET", lst, token=self.adm); self.assertEqual(st, 200)
            self.assertTrue(d[lkey][0]["paused"], key)
            st, d = srv.call("POST", route, {"paused": False}, token=self.adm)
            self.assertEqual((st, d[rkey]["paused"]), (200, False), key)
            self.assertNotIn("enabled", load()[0])
            self.assertFalse(srv.call("GET", lst, token=self.adm)[1][lkey][0]["paused"], key)

    def test_only_admin_and_only_true_or_false(self):
        for key, _m, srv, load, _l, _k, route, _r, _e, _s in self.each():
            self.assertEqual(srv.call("POST", route, {"paused": True}, token=self.ro)[0], 403, key)
            self.assertEqual(srv.call("POST", route, {"paused": True})[0], 401, key)
            for bad in ({}, {"paused": "yes"}, {"paused": 1}):
                self.assertEqual(srv.call("POST", route, bad, token=self.adm)[0], 400, (key, bad))
            self.assertEqual(srv.call("POST", route.replace(route.split("/")[3], UID.replace("0", "9")), {"paused": True}, token=self.adm)[0], 404, key)
            self.assertNotIn("enabled", load()[0], key)

    def test_health_skips_paused(self):
        for key, m, srv, load, _l, _k, route, _r, _e, _s in self.each():
            srv.call("POST", route, {"paused": True}, token=self.adm)
            checks = m.health_report(True)[1]["checks"]
            self.assertTrue(any("1 paused" in str(c.get("detail")) for c in checks.values()), (key, checks))
            self.assertFalse(any(c.get("level") != auth.OK and entry_name(key) in str(c.get("detail")) for c in checks.values()), (key, checks))


    def test_editing_keeps_the_pause_and_the_form_cannot_set_it(self):
        # Editar (solo el nombre) un equipo pausado lo deja pausado; «enabled» en el formulario no pausa. / EN: Editing a paused device keeps it paused.
        edits = {"nut": ("PUT", {"name": "nuevo", "host": "192.0.2.30", "port": 3493}),
                 "pve": ("POST", {"name": "nuevo", "host": "192.0.2.31", "port": 8006, "user": "ro@pve", "token_name": "t"}),
                 "dns": ("POST", {"name": "nuevo"}), "vpn": ("POST", {"name": "nuevo"}), "uptime": ("POST", {"name": "nuevo"})}
        for key, _m, srv, load, _l, _k, route, _r, _e, _s in self.each():
            meth, body = edits[key]; url = route.rsplit("/", 1)[0]
            st, d = srv.call(meth, url, {**body, "enabled": False}, token=self.adm)
            self.assertEqual(st, 200, (key, d)); self.assertNotIn("enabled", load()[0], key)
            srv.call("POST", route, {"paused": True}, token=self.adm)
            st, d = srv.call(meth, url, {**body, "name": "otro"}, token=self.adm)
            self.assertEqual(st, 200, (key, d)); self.assertIs(load()[0].get("enabled"), False, key); self.assertEqual(load()[0]["name"], "otro", key)

    def test_dns_tools_answer_404_before_409(self):
        # Un id que no existe es 404 aunque traiga cuerpo; uno pausado es 409. / EN: An unknown id is 404; a paused one is 409.
        for key, _m, srv, _load, _l, _k, route, _r, _e, _s in self.each():
            if key != "dns": continue
            self.assertEqual(srv.call("POST", "/api/dns/nope/resolve", {"name": "example.com"}, token=self.adm)[0], 404)
            srv.call("POST", route, {"paused": True}, token=self.adm)
            self.assertEqual(srv.call("POST", route.replace("/pause", "/resolve"), {"name": "example.com"}, token=self.adm)[0], 409)


def entry_name(key): return CASES[key][7]["name"]


class Pollers(unittest.TestCase):
    """Los hilos no consultan mientras está pausado y no dejan datos viejos. / EN: Threads do not poll while paused and leave no stale data."""
    def run_poll(self, rel, load_name, fn, cache, entry, *args):
        m = support.load(rel)
        cfgs = iter([{**entry, "enabled": False}, None])
        saved = {k: getattr(m, k) for k in (load_name, "collect", "POLL_IDLE", "POLL_ACTIVE") if hasattr(m, k)}
        calls = []
        m.collect = lambda *a: calls.append(a)
        setattr(m, load_name, lambda: [x for x in [next(cfgs, None)] if x])
        m.POLL_IDLE = m.POLL_ACTIVE = 0.01
        try: getattr(m, fn)(*args)
        finally:
            for k, v in saved.items(): setattr(m, k, v)
        self.assertEqual(calls, [])
        return cache.snap()

    def test_dns(self):
        m = support.load("dns-monitor/server.py")
        cc = m.DnsCache("d-p1"); cc.update({"queries": 5}); m._cache["d-p1"] = cc
        try: sn = self.run_poll("dns-monitor/server.py", "load_servers", "_poll", cc, CASES["dns"][7], "d-p1")
        finally: m._cache.pop("d-p1", None)
        self.assertEqual((sn["data"], sn["ts"]), ({}, None))

    def test_vpn(self):
        m = support.load("vpn-monitor/server.py")
        cc = m.Cache("v-p1"); cc.update({"ts": 1, "online": 1, "clients": []}); m._cache["v-p1"] = cc
        try: sn = self.run_poll("vpn-monitor/server.py", "load_vpn", "_poll", cc, CASES["vpn"][7], "v-p1")
        finally: m._cache.pop("v-p1", None)
        self.assertEqual((sn["data"], sn["ts"]), ({}, None)); self.assertEqual(cc.history(), [])

    def test_nut(self):
        m = support.load("nut-monitor/server.py")
        entry = CASES["nut"][7]; cfgs = iter([{**entry, "enabled": False}])
        cc = m.SCache("s-p1"); cc._ups = {"u": {"ups.status": "OL"}}; cc._last_ok = 1; m._caches["s-p1"] = cc
        old = m.load_servers, m._safe_servers, m.POLL_SEC, m.NUTClient
        m.load_servers = lambda: [x for x in [next(cfgs, None)] if x]
        m._safe_servers = list
        m.POLL_SEC = 0.01
        calls = []
        class NoNut:                                                                         # notes any query (the loop swallows errors)
            def __init__(s, *a, **k): pass
            def __getattr__(s, name): calls.append(name); raise OSError("no")
        m.NUTClient = NoNut
        sid = entry["id"]; m.db_init()
        m.outage_track(sid, "u", "OB", 80, 1000)                                             # UPS on battery when it is paused
        m.outage_track("otro", "u", "OB", 80, 1000)                                          # another server's outage stays open
        try: m._poll(entry)
        finally: m.load_servers, m._safe_servers, m.POLL_SEC, m.NUTClient = old; m._caches.pop("s-p1", None)
        self.assertEqual(calls, []); self.assertEqual(cc.snap("none")["ups"], {})
        c = m.db_connect()
        try: rows = dict(c.execute("SELECT srv_id, t_end FROM outages WHERE t_start = 1000 AND srv_id IN (?, 'otro')", (sid,)).fetchall())
        finally: c.execute("DELETE FROM outages WHERE t_start = 1000"); c.commit(); c.close()
        self.assertIsNotNone(rows[sid]); self.assertGreater(rows[sid], 1000)                 # closed at the pause
        self.assertIsNone(rows["otro"])
        self.assertIsNone(m._open_out[(sid, "u")])                                           # the next battery reading opens a new one

    def test_uptime(self):
        m = support.load("uptime-monitor/server.py")
        entry = CASES["uptime"][7]; mon = m.Mon(UID); m._mons[UID] = mon; mon.status = "down"
        cfgs = iter([{**entry, "enabled": False}])
        def load():
            mon.wake.set(); return [x for x in [next(cfgs, None)] if x]
        old = m.load_monitors, m.run_check
        m.load_monitors, m.run_check = load, lambda *a: self.fail("checked while paused")
        mon.wake.set()
        try: m._loop(UID)
        finally: m.load_monitors, m.run_check = old; m._mons.pop(UID, None)
        self.assertIsNone(mon.status)

    def test_proxmox_side_threads_and_data(self):
        m = support.load("proxmox-monitor/server.py")
        src = (ROOT / "proxmox-monitor/server.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("if off: _drop_side(cid)"), 4)                            # SMART, backups, extra, guests
        for every in ("SMART_EVERY", "BACKUP_EVERY", "EXTRA_EVERY", "GUEST_EVERY"):
            self.assertIn(f"time.sleep(_side_wait(off, {every}))", src)                     # resumed: they read within PAUSED_EVERY s
        self.assertEqual(m._side_wait(True, 900), m.PAUSED_EVERY); self.assertEqual(m._side_wait(False, 900), 900)
        self.assertEqual(m._side_wait(True, 5), 5)
        self.assertIn("cache.clear(); _drop_side(cid); client.close()", src)
        for d in (m._smart, m._backups, m._extra, m._live, m._gnets): d["c-x"] = {"x": 1}
        m._drop_side("c-x")
        self.assertFalse(any("c-x" in d for d in (m._smart, m._backups, m._extra, m._live, m._gnets)))


class Pages(unittest.TestCase):
    def read(self, p): return (ROOT / p).read_text(encoding="utf-8")

    def test_buttons_routes_and_both_languages(self):
        for page, fn, route, keys in (
                ("nut-monitor/static/app.js", "pauseServer", "'api/servers/'+encodeURIComponent(sid)+'/pause'", ("pause:", "resume:", "paused:", "pausedOk:", "resumedOk:")),
                ("proxmox-monitor/static/app.js", "pauseCluster", "'api/clusters/'+encodeURIComponent(id)+'/pause'", ("pause:", "resume:", "paused:", "pausedMsg:", "clusterDeleted:")),
                ("dns-monitor/static/app.js", "pauseMonitor", "'api/dns/'+encodeURIComponent(id)+'/pause'", ('"monPause":', '"monResume":', '"monPaused":', '"monPausedMsg":')),
                ("vpn-monitor/static/app.js", "pauseVpn", "'api/vpn/'+encodeURIComponent(id)+'/pause'", ('"pause":', '"resume":', '"paused":', '"pausedMsg":')),
                ("uptime-monitor/static/app.js", "pauseMon", "'api/monitors/'+encodeURIComponent(id)+'/pause'", ('"st_paused":', '"pause":', '"resume":', '"pausedMsg":'))):
            js = self.read(page)
            with self.subTest(page=page):
                self.assertIn(f'data-on-click="{fn}"', js); self.assertIn(f" {fn},", js); self.assertIn(route, js)
                for k in keys: self.assertEqual(js.count(k), 2, k)
                self.assertIn(".paused{", self.read(page.replace("app.js", "app.css")))

    def test_paused_is_never_counted_online(self):
        self.assertIn("const d=n.snap?.data;if(n.paused||!d||n.snap.error)return;on++;", self.read("nas-monitor/static/app.js"))
        self.assertIn("const d=n.snap?.data;if(n.paused||!d||n.snap.error)return;on++;q+=d.queries||0;", self.read("dns-monitor/static/app.js"))
        self.assertIn("d=!n.paused&&sn.data&&sn.data.queries!=null?sn.data:null", self.read("dns-monitor/static/app.js"))

    def test_switch_card_button(self):
        js = self.read("net-monitor/static/switches.js")
        self.assertIn('data-act="pause"', js); self.assertIn("await post('api/switches/save', { id, enabled: resume });", js)
        for k in ("swPause:", "swResume:", "swPausedOk:", "swResumedOk:"): self.assertEqual(js.count(k), 2, k)
        self.assertIn("swActive:", js)                                                       # the checkbox in Edit stays

    def test_vpn_admin_buttons_even_without_data(self):
        js = self.read("vpn-monitor/static/app.js")
        self.assertIn("if(!d||!d.clients){return (h||`<div class=\"nas-empty\">${esc(t('connecting'))}</div>`)+tools;}", js)

    def test_overview_and_rules_skip_paused(self):
        ov, rules = self.read("overview/static/app.js"), self.read("overview/static/rules.js")
        for k in ("(d.servers||[]).filter(x=>!x.paused)", "(d.clusters||[]).filter(c=>!c.paused)", "(d.servers||[]).filter(n=>!n.paused)",
                  "(d.vpn||[]).filter(n=>!n.paused)", "(d.monitors||[]).filter(n=>!n.paused)", "(R.nut.value.servers||[]).filter(x=>!x.paused)"):
            self.assertIn(k, ov)
        # Todo pausado: la tarjeta lo dice en vez de «sin configurar». / EN: All paused: the card says so instead of "none configured".
        self.assertIn("function idle(all,k){all=all||[];return all.length&&all.every(x=>x.paused)?T('allpaused').replace('{n}',all.length):T(k)}", ov)
        for a, k in (("d.servers", "noups"), ("d.clusters", "nopve"), ("d.nas", "nonas"), ("d.servers", "nodns"), ("d.vpn", "vpnnone"), ("d.monitors", "uptnone")):
            self.assertIn(f"esc(idle({a},'{k}'))", ov)
        self.assertEqual(ov.count("allpaused:"), 2)
        for k in ("((ok('nut') || {}).servers || []).filter(sv => !sv.paused)", "((ok('pve') || {}).clusters || []).filter(c => !c.paused)",
                  "((ok('dns') || {}).servers || []).filter(n => !n.paused)"):
            self.assertIn(k, rules)


if __name__ == "__main__":
    unittest.main()
