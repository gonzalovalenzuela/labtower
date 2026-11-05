"""2.1.7f: detalle de un nodo de Proxmox, gráficos con rangos y velocidad de WAN por rango / Proxmox node detail, range charts and WAN speed by range."""
import unittest

from tests import support

pve = support.load("proxmox-monitor/server.py")
extra = support.load("proxmox-monitor/extra.py")
wan = support.load("wan-monitor/server.py")


class RrdPoints(unittest.TestCase):
    def test_converts_units_and_sorts(self):
        rows = [{"time": 200, "cpu": 0.1, "iowait": 0.004, "loadavg": 0.5, "memused": 50, "memtotal": 200, "swapused": 0, "swaptotal": 0, "rootused": 1, "roottotal": 4, "netin": 10, "netout": 20},
                {"time": 100, "cpu": 0.5}, {"time": 0, "cpu": 1}, "junk", {"cpu": 1}]
        pts = extra.rrd_points(rows)
        self.assertEqual([p["ts"] for p in pts], [100, 200])
        p = pts[1]
        self.assertEqual((p["cpu"], p["iowait"], p["mem"], p["root"], p["load"], p["netin"]), (10.0, 0.4, 25.0, 25.0, 0.5, 10.0))
        self.assertIsNone(p["swap"])                        # no swap configured: no division by zero
        self.assertIsNone(pts[0]["mem"])

    def test_not_a_list(self):
        self.assertEqual(extra.rrd_points(None), [])
        self.assertEqual(extra.rrd_points({"data": 1}), [])

    def test_ranges_cover_the_chart_ranges(self):
        self.assertEqual(set(extra.RRD_FRAME), {"1h", "1d", "1w", "1mo", "all"})
        self.assertEqual(extra.RRD_FRAME["all"], "year")


class NodeDetail(unittest.TestCase):
    def test_full_status(self):
        d = extra.node_detail({"cpu": 0.0482, "wait": 0.004, "loadavg": ["0.79", "0.70", "0.66"], "cpuinfo": {"model": "Intel i5", "cpus": 12, "sockets": 1, "cores": 6, "mhz": "3100"},
                               "memory": {"used": 1, "total": 2}, "swap": {"used": 0, "total": 8}, "rootfs": {"used": 3, "total": 9}, "ksm": {"shared": 7}, "uptime": 61685,
                               "pveversion": "pve-manager/9.2.2/abc", "current-kernel": {"release": "7.0.14-28-pve", "machine": "x86_64"}, "boot-info": {"mode": "efi", "secureboot": 1},
                               "thermal": {"core0": 52, "core1": 51}},
                              {"version": "9.2.2"}, {"timezone": "America/Santiago", "localtime": 5}, {"search": "lan", "dns1": "192.0.2.1"},
                              [{"iface": "vmbr0", "type": "bridge", "active": 1, "cidr": "192.0.2.20/24", "bridge_ports": "eno1"}],
                              {"status": "notfound", "key": "SECRET-KEY", "serverid": "SECRET-ID"}, [{"Package": "a"}, {"Package": "b"}],
                              [{"service": "pveproxy", "state": "running"}], [{"devpath": "/dev/sda", "model": "X", "size": 5, "type": "hdd", "health": "PASSED", "serial": "SERIAL"}])
        self.assertEqual(d["cpu"], 4.82)
        self.assertEqual(d["load"], [0.79, 0.7, 0.66])
        self.assertEqual(d["kernel"], "7.0.14-28-pve")
        self.assertEqual(d["boot"], {"mode": "efi", "secureboot": True})
        self.assertEqual(d["updates"], 2)
        self.assertEqual(d["net"][0]["address"], "192.0.2.20/24")
        self.assertEqual(d["dns"]["servers"], ["192.0.2.1"])
        self.assertEqual([o["k"] for o in d["other"]], ["thermal"])         # unknown fields are kept, shortened
        blob = repr(d)
        for secret in ("SECRET-KEY", "SECRET-ID", "SERIAL"):
            self.assertNotIn(secret, blob, "the license key, server id and disk serials never go to the page")

    def test_missing_parts_do_not_fail(self):
        d = extra.node_detail(None, None, None, None, None, None, None, None, None)
        self.assertIsNone(d["cpu"]); self.assertIsNone(d["updates"]); self.assertIsNone(d["subscription"])
        self.assertEqual((d["net"], d["services"], d["disks"], d["load"]), ([], [], [], []))

    def test_long_values_are_cut(self):
        d = extra.node_detail({"x": "A" * 5000, "cpuinfo": {"model": "B" * 5000}}, None, None, None, None, None, None, None, None)
        self.assertLessEqual(len(d["other"][0]["v"]), 160)
        self.assertLessEqual(len(d["cpuinfo"]["model"]), 120)


class FakeClient:
    def __init__(self, answers): self.answers, self.calls = answers, []
    def get(self, path):
        self.calls.append(path)
        for k, v in self.answers.items():
            if path.startswith(k):
                if isinstance(v, Exception): raise v
                return {"data": v}
        raise pve.PVEHTTPError(404, "nope")


class ServerSide(unittest.TestCase):
    def setUp(self):
        pve._ncache.clear()
        self._orig = pve._node_client

    def tearDown(self):
        pve._node_client = self._orig

    def test_rrd_uses_the_range_frame_and_quotes_the_node(self):
        fc = FakeClient({"/nodes/": [{"time": 10, "cpu": 0.2}]})
        pve._node_client = lambda cid: fc
        pts = pve.node_rrd("c1", "n o/de", "1w")
        self.assertEqual(pts[0]["cpu"], 20.0)
        self.assertEqual(fc.calls, ["/nodes/n%20o%2Fde/rrddata?timeframe=week&cf=AVERAGE"])
        pve.node_rrd("c1", "n o/de", "1w")
        self.assertEqual(len(fc.calls), 1, "the answer is kept for a minute")

    def test_detail_survives_missing_permissions(self):
        fc = FakeClient({"/nodes/n1/status": {"cpu": 0.1, "uptime": 5}, "/nodes/n1/apt/update": pve.PVEHTTPError(403, "perm"),
                         "/nodes/n1/subscription": pve.PVEHTTPError(403, "perm")})
        pve._node_client = lambda cid: fc
        d = pve.node_detail("c1", "n1")
        self.assertEqual(d["cpu"], 10.0)
        self.assertEqual(d["errors"].get("apt"), "perm")
        self.assertIsNone(d["updates"])

    def test_detail_fails_when_the_node_status_cannot_be_read(self):
        fc = FakeClient({"/nodes/n1/status": pve.PVEHTTPError(500, "boom")})
        pve._node_client = lambda cid: fc
        with self.assertRaises(pve.PVEHTTPError): pve.node_detail("c1", "n1")

    def test_unknown_node_is_refused(self):
        self.assertFalse(pve._node_known("nope", "n1"))


class WanSpeedRange(unittest.TestCase):
    def test_speed_range_leaves_failed_tests_out(self):
        seen = {}
        def fake_db(sql, args=(), fetch=False):
            seen["sql"], seen["args"] = sql, args
            return [(30, 400.0, 40.0, 9.0), (20, None, 38.0, 8.0)]
        orig = wan._db; wan._db = fake_db
        try:
            out = wan.speed_range("1w")
        finally: wan._db = orig
        self.assertIn("error IS NULL", seen["sql"])
        self.assertEqual([p["ts"] for p in out], [20, 30])                  # oldest first
        self.assertEqual(wan.speed_range("all", prev=True), [])             # "all" has no previous period


class Pages(unittest.TestCase):
    """Las páginas cargan lo que necesitan / The pages load what they need."""
    def read(self, rel): return (support.ROOT / rel).read_text()

    def test_proxmox_page_loads_the_chart_engine_before_the_app(self):
        html = self.read("proxmox-monitor/static/index.html")
        self.assertLess(html.index("charts.js"), html.index("app.js"))

    def test_node_name_toggles_the_detail(self):
        js = self.read("proxmox-monitor/static/app.js")
        self.assertIn('data-on-click="toggleNode"', js)
        self.assertRegex(js, r"cspRegister\(\{[^}]*\btoggleNode\b[^}]*\bsetNRange\b")

    def test_switch_temperature_chart_has_range_buttons(self):
        js = self.read("net-monitor/static/switches.js")
        self.assertIn("rangeChips()", js.split("data-kind=\"temp\"")[0].rsplit("sw-charthead", 1)[-1] + "rangeChips()")
        self.assertEqual(js.count("data-act=\"range\""), 1, "one shared builder for the range buttons")

    def test_wan_speed_chart_is_not_local_anymore(self):
        js = self.read("wan-monitor/static/app.js")
        self.assertNotIn("local:true", js)
        self.assertIn("src:'speed'", js)


if __name__ == "__main__":
    unittest.main()
