"""Net Monitor: cambio de MAC, puertos nuevos, equipos conocidos, conectividad y vigilancia / MAC change, new ports, known devices, connectivity and watch."""
import time
import unittest

from tests import support
from tests.support import ADMIN, READONLY

m = support.load("net-monitor/server.py")
hw = m.hw
NOW = 2_000_000_000

class Pure(unittest.TestCase):
    def test_mac_change_only_when_it_was_online(self):
        ex = {"online": True, "mac": "AA:BB:CC:00:00:01"}
        self.assertEqual(hw.mac_change(ex, {"mac": "aa:bb:cc:00:00:02"})["new"], "aa:bb:cc:00:00:02")
        self.assertIsNone(hw.mac_change(ex, {"mac": "aa-bb-cc-00-00-01"}))                 # same MAC, other format
        self.assertIsNone(hw.mac_change(dict(ex, online=False), {"mac": "aa:bb:cc:00:00:02"}))   # DHCP gave the IP to another device
        self.assertIsNone(hw.mac_change(ex, {"mac": ""})); self.assertIsNone(hw.mac_change({}, {"mac": "aa:bb:cc:00:00:02"})); self.assertIsNone(hw.mac_change(None, None))

    def test_mac_already_seen_on_the_ip_is_not_a_change(self):
        # Equipo con dos tarjetas en la misma red (ARP flux): alterna entre nic0 y nic1. / EN: Two cards on one network: alternates nic0/nic1.
        nic0, nic1, other = "00:e0:4c:00:00:01", "90:8d:6e:00:00:02", "aa:bb:cc:00:00:03"
        ex = {"online": True, "mac": nic1, "mac_prev": nic0}
        self.assertIsNone(hw.mac_change(ex, {"mac": nic0.upper()}))                    # back to nic0: known (mac_prev)
        ex = {"online": True, "mac": nic0, "macs_seen": [nic0, nic1]}
        self.assertIsNone(hw.mac_change(ex, {"mac": nic1}))
        self.assertEqual(hw.mac_change(ex, {"mac": other})["new"], other)              # a MAC never seen here still warns
        self.assertTrue(hw.same_mac("AA-BB-CC-00-00-03", other)); self.assertFalse(hw.same_mac("", ""))

    def test_macs_seen_keeps_recent_unique_macs(self):
        self.assertEqual(hw.macs_seen({"mac": "AA:BB:CC:00:00:01"}, {"mac": "aa-bb-cc-00-00-02"}), ["aa:bb:cc:00:00:01", "aa:bb:cc:00:00:02"])
        self.assertEqual(hw.macs_seen({"mac": "aa:bb:cc:00:00:01", "macs_seen": ["aa:bb:cc:00:00:01"]}, {"mac": "AA:BB:CC:00:00:01"}),
                         ["aa:bb:cc:00:00:01"])
        many = [f"aa:bb:cc:00:00:{i:02x}" for i in range(20)]
        out = hw.macs_seen({"macs_seen": many}, {"mac": "aa:bb:cc:00:00:00"})
        self.assertEqual((len(out), out[-1]), (hw.MACS_MAX, "aa:bb:cc:00:00:00"))         # the latest one goes last
        self.assertEqual(hw.macs_seen(None, None), []); self.assertEqual(hw.macs_seen({"macs_seen": "x"}, {}), [])

    def test_scan_prefers_the_arp_mac_over_pihole(self):
        old = m.ping_ttl, m.pihole_lookup, m.resolve_name, m.scan_ports, m.arp_mac, m.oui_vendor
        m.ping_ttl = lambda ip: (True, 64, 1.0)
        m.pihole_lookup = lambda ip: {"hostname": "nodo", "mac": "00:e0:4c:00:00:01", "vendor": "Realtek"}
        m.resolve_name = lambda ip: ""; m.scan_ports = lambda ip, ports: []; m.oui_vendor = lambda mac: "Dell" if mac.startswith("90:") else "?"
        try:
            m.arp_mac = lambda ip: "90:8d:6e:00:00:02"
            r = m.scan_host("192.0.2.40")
            self.assertEqual((r["mac"], r["vendor"], r["hostname"]), ("90:8d:6e:00:00:02", "Dell", "nodo"))   # Pi-hole vendor is of the other MAC
            m.arp_mac = lambda ip: ""
            r = m.scan_host("192.0.2.40")
            self.assertEqual((r["mac"], r["vendor"]), ("00:e0:4c:00:00:01", "Realtek"))                      # no ARP: Pi-hole as fallback
        finally: m.ping_ttl, m.pihole_lookup, m.resolve_name, m.scan_ports, m.arp_mac, m.oui_vendor = old

    def test_port_news_memorizes_and_ignores_flapping(self):
        p = lambda *n: [{"port": x, "service": ""} for x in n]
        seen, new = hw.port_news({}, {"ports": p(22, 80)})
        self.assertEqual((seen, new), ([22, 80], []))                                   # no previous reading: only memorize
        seen, new = hw.port_news({"ports": p(22, 80)}, {"ports": p(22)})                  # 80 closed (timeout): nothing
        self.assertEqual(new, []); self.assertEqual(seen, [22, 80])
        ex = {"ports": p(22), "ports_seen": [22, 80]}
        self.assertEqual(hw.port_news(ex, {"ports": p(22, 80)})[1], [])                  # 80 reopened: seen before
        self.assertEqual(hw.port_news(ex, {"ports": p(22, 80, 3389)})[1], [3389])
        self.assertEqual(hw.port_news({"ports": p(22)}, {"ports": p(22, 23)})[1], [23])  # legacy host without ports_seen: its ports are the baseline
        self.assertEqual(hw.port_news(None, None), ([], []))

    def test_known_uses_baseline(self):
        self.assertTrue(hw.known({"first_seen": 100}, 500)); self.assertFalse(hw.known({"first_seen": 900}, 500))
        self.assertTrue(hw.known({"first_seen": 900, "known": True}, 500)); self.assertFalse(hw.known({"first_seen": 900}, None)); self.assertFalse(hw.known(None, 5))

    def test_conn_stats_and_week_bar(self):
        d = 86400
        ev = [{"ts": NOW - 5 * d, "event": "down"}, {"ts": NOW - 5 * d + 6 * 3600, "event": "up"}, {"ts": NOW - d, "event": "down"}, {"ts": NOW - d + 3600, "event": "up"}]
        c = hw.conn_stats(ev, NOW - 10 * d, True, NOW)
        self.assertEqual(c["7d"]["drops"], 2)
        self.assertAlmostEqual(c["7d"]["pct"], 100 * (7 * d - 7 * 3600) / (7 * d), places=1)
        self.assertLess(c["30d"]["observed"], 11 * d)                                     # not judged over time it did not observe
        wb = hw.week_bar(ev, NOW - 10 * d, True, NOW)
        self.assertEqual(len(wb), 42); self.assertTrue(min(x for x in wb if x is not None) < 1)
        self.assertEqual(hw.conn_stats([], NOW - 60, True, NOW)["7d"]["pct"], None)         # a minute of history says nothing

    def test_trimmed_log_deduces_the_initial_state(self):
        ev = [{"ts": NOW - 1000 + i * 2, "event": "down" if i % 2 == 0 else "up"} for i in range(200)]
        seg = hw.timeline(ev, NOW - 10 * 86400, True, NOW)
        self.assertEqual(seg[0][0], ev[0]["ts"]); self.assertTrue(seg[-1][2])

    def test_latency_summary(self):
        s = hw.latency_summary([(i, 10.0 + i, 1) for i in range(20)] + [(30, None, 0)])
        self.assertEqual((s["n"], s["loss"]), (21, 4.76)); self.assertEqual(s["max"], 29.0)
        self.assertEqual(hw.latency_summary([])["n"], 0)

class Server(unittest.TestCase):
    def setUp(self):
        self.ev = []
        self._rec = m.auth.record_event
        m.auth.record_event = lambda mod, lv, tx, k=None, **p: self.ev.append((lv, k, p))
        m.auth._state_seen.clear(); m._watch.clear()
        self._lh, self._pt = m.load_hosts, m.ping_ttl
        c = m.auth.metrics_conn(); c.execute("DELETE FROM net_latency"); c.commit(); c.close()
    def tearDown(self): m.auth.record_event = self._rec; m.load_hosts, m.ping_ttl = self._lh, self._pt

    def test_scan_merge_keeps_and_updates_macs_seen(self):
        src = (support.ROOT / "net-monitor/server.py").read_text(encoding="utf-8")
        self.assertIn('for k in ("group", "known", "watch", "mac_prev", "mac_changed", "macs_seen"):', src)
        self.assertIn('result["macs_seen"] = hw.macs_seen(existing, result)', src)
        self.assertLess(src.index("mc = hw.mac_change(existing, result)"), src.index('result["macs_seen"] = hw.macs_seen(existing, result)'))   # compared before memorizing

    def test_admin_can_acknowledge_a_mac_change(self):
        m.DATA_DIR.mkdir(parents=True, exist_ok=True)
        old = m.load_hosts()
        m.save_hosts({"192.0.2.52": {"ip": "192.0.2.52", "online": True, "mac": "90:8d:6e:00:00:02", "mac_prev": "00:e0:4c:00:00:01",
                                     "mac_changed": NOW}})
        srv = support.Server(m.H); hdr = {"Origin": "http://127.0.0.1"}
        try:
            ro, adm = support.make_user("macack_ro", READONLY), support.make_user("macack_adm", ADMIN)
            st, _ = srv.call("POST", "/api/hosts/update", {"ip": "192.0.2.52", "mac_ack": True}, token=ro, headers=hdr)
            self.assertEqual(st, 403); self.assertIn("mac_changed", m.load_hosts()["192.0.2.52"])
            st, _ = srv.call("POST", "/api/hosts/update", {"ip": "192.0.2.52", "mac_ack": "yes"}, token=adm, headers=hdr)
            self.assertEqual(st, 200); self.assertIn("mac_changed", m.load_hosts()["192.0.2.52"])           # only a real true acknowledges
            st, _ = srv.call("POST", "/api/hosts/update", {"ip": "192.0.2.52", "mac_ack": True}, token=adm, headers=hdr)
            h = m.load_hosts()["192.0.2.52"]
            self.assertEqual(st, 200); self.assertNotIn("mac_changed", h)
            self.assertEqual(h["macs_seen"], ["00:e0:4c:00:00:01", "90:8d:6e:00:00:02"])
            self.assertIsNone(hw.mac_change(h, {"mac": "00:e0:4c:00:00:01"}))                               # flipping back no longer warns
        finally:
            srv.close(); m.save_hosts(old)

    def test_badge_shows_both_macs_and_acknowledges(self):
        js = (support.ROOT / "net-monitor/static/app.js").read_text(encoding="utf-8")
        for k in ('data-on-click="ackMac" data-on-click-args="${jsargs([h.ip])}" data-on-click-stop="1"', "if(!canAdmin()){alert(info);return;}",
                  "body:JSON.stringify({ip,mac_ack:true})", "cspRegister({ ackMac,"):
            self.assertIn(k, js, k)
        for k in ("macInfo:", "macAckQ:", "macAckDone:"):
            self.assertEqual(js.count(k), 2, k)                                                              # English and Spanish

    def test_security_events(self):
        h = {"alias": "nas", "hostname": ""}
        m._record_security_events([("mac", "10.0.0.5", h, {"old": "aa:aa:aa:aa:aa:01", "new": "aa:aa:aa:aa:aa:02"}), ("port", "10.0.0.6", h, [3389, 8080])])
        self.assertEqual([(e[0], e[1]) for e in self.ev], [("warn", "net_mac_changed"), ("warn", "net_port_new")])
        self.ev.clear(); m._record_security_events([("port", "10.0.0.6", h, [8080])])
        self.assertEqual(self.ev[0][0], "info")                                           # not a risky port

    def test_flaky_event_once(self):
        now = int(time.time())
        h = {"uptime_history": [{"ts": now - 100 * i, "event": "down" if i % 2 else "up"} for i in range(1, 12)]}
        m._flaky_check("10.0.0.7", {"uptime_history": []})                                 # baseline
        m._flaky_check("10.0.0.7", h); m._flaky_check("10.0.0.7", h)
        self.assertEqual([e[1] for e in self.ev], ["net_flaky"])

    def test_watch_round_events_and_latency(self):
        hosts = {"10.0.0.9": {"ip": "10.0.0.9", "watch": True, "alias": "srv"}, "10.0.0.10": {"ip": "10.0.0.10"}}
        m.load_hosts = lambda: hosts
        answers = {"v": (True, 64, 1.5)}
        m.ping_ttl = lambda ip: answers["v"]
        m._watch_round()
        self.assertEqual(self.ev, [])                                                      # first reading only memorizes
        answers["v"] = (False, 0, 0.0)
        m._watch_round(); self.assertEqual(self.ev, [])                                    # one failure is not enough
        m._watch_round(); self.assertEqual([e[1] for e in self.ev], ["net_watch_down"]); self.assertTrue(m._watch["10.0.0.9"]["down"])
        answers["v"] = (True, 64, 2.0)
        m._watch_round(); self.assertEqual([e[1] for e in self.ev], ["net_watch_down", "net_watch_up"])
        pts = m.latency_points("10.0.0.9", 3600)
        self.assertEqual(len(pts), 1)                                                      # same-second samples collapse on the primary key
        self.assertNotIn("10.0.0.10", m._watch)

if __name__ == "__main__":
    unittest.main()
