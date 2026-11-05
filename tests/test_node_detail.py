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

    def test_pve_mod_fields_are_short_and_never_show_the_serial(self):
        st = {"PveMod_JsonSensorInfo": {"temp_unit": "C", "cpu": True, "hdd": False, "data": "PVE MOD lm-sensors Enhanced", "other": True, "fans": True, "nvme": True},
              "PveMod_Version": "1.0.6",
              "PveMod_systemInfo": {"serial_number": "2TQVWP3", "manufacturer": "Dell Inc.", "display_string": "Manufacturer: Dell Inc. | Serial Number: 2TQVWP3", "product_name": "OptiPlex 7090"},
              "PveMod_upsInfo": {"disabled": True}}
        d = extra.node_detail(st, None, None, None, None, None, None, None, None)
        self.assertEqual({o["k"]: o["v"] for o in d["other"]}, {"PveMod_Version": "1.0.6", "PveMod_systemInfo": "Manufacturer: Dell Inc. | Product Name: OptiPlex 7090"})
        self.assertNotIn("2TQVWP3", repr(d))
        st["PveMod_upsInfo"] = {"disabled": False, "model": "APC"}
        self.assertIn("model: APC", {o["k"]: o["v"] for o in extra.node_detail(st, None, None, None, None, None, None, None, None)["other"]}["PveMod_upsInfo"])

    def test_a_service_off_on_purpose_is_not_a_problem(self):
        sv = [{"service": "pveproxy", "state": "running", "unit-state": "enabled"},
              {"service": "syslog", "state": "dead", "unit-state": "disabled"}, {"service": "systemd-timesyncd", "state": "dead", "unit-state": "masked"},
              {"service": "pvedaemon", "state": "dead", "unit-state": "enabled"}, {"service": "x", "state": "dead", "unit-state": "static", "active-state": "failed"}]
        d = extra.node_detail(None, None, None, None, None, None, None, sv, None)
        self.assertEqual({s["name"]: s["bad"] for s in d["services"]}, {"pveproxy": False, "syslog": False, "systemd-timesyncd": False, "pvedaemon": True, "x": True})

    def test_old_proxmox_without_unit_state_only_flags_the_core_services(self):
        d = extra.node_detail(None, None, None, None, None, None, None, [{"service": "syslog", "state": "dead"}, {"service": "pveproxy", "state": "dead"},
                                                                      {"service": "pvestatd", "state": "running"}], None)
        self.assertEqual({s["name"]: s["bad"] for s in d["services"]}, {"syslog": False, "pveproxy": True, "pvestatd": False})

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


class PveModSensors(unittest.TestCase):
    DATA = {"PVE MOD lm-sensors Enhanced": {  # noqa: RUF012
        "coretemp-isa-0000": {"Adapter": "ISA adapter", "Core 0": {"temp2_crit": 100, "temp2_input": 55, "temp2_max": 84},
                              "Package id 0": {"temp1_crit": 100, "temp1_input": 65, "temp1_max": 84}, "cpu_model": "Intel(R) Core(TM) i5-10500", "cpu_package": "0"},
        "dell_smm-virtual-0": {"Adapter": "Virtual device", "fan1": {"fan1_input": 1823, "fan1_max": 4000}, "pwm1": {"pwm1": 64},
                               "temp1": {"temp1_input": 55}, "temp3": {"temp3_input": 0}},
        "nvme-pci-0200": {"Adapter": "PCI adapter", "Composite": {"temp1_crit": 84.85, "temp1_input": 45.85, "temp1_max": 82.85},
                          "device_path": "/dev/nvme0n1", "model": "Asgard AN1TNVMe-M.2/80", "serial": "SERIAL-123"},
        "ucsi_source_psy_USBC000:001-isa-0000": {"Adapter": "ISA adapter", "in0": {"in0_input": 5}}}}

    def test_groups_cpu_nvme_other_and_fans_from_the_real_format(self):
        s = extra.sensors({"data": self.DATA})
        self.assertEqual([(x["g"], x["l"], x["v"], x.get("mx"), x.get("cr")) for x in s], [
            ("cpu", "Core 0", 55, 84, 100), ("cpu", "Package id 0", 65, 84, 100), ("fans", "fan1", 1823, 4000, None),
            ("other", "dell_smm-virtual-0 · temp1", 55, None, None), ("nvme", "Asgard AN1TNVMe-M.2/80", 45.9, 82.8, 84.8)])

    def test_the_drive_serial_never_leaves(self):
        self.assertNotIn("SERIAL-123", str(extra.sensors({"data": self.DATA})))

    def test_data_as_a_json_string_also_works(self):
        import json
        self.assertEqual(len(extra.sensors({"data": json.dumps(self.DATA)})), 5)

    def test_unreadable_data_gives_nothing(self):
        for bad in (None, {}, {"data": "PVE MOD lm-sensors Enhanced:"}, {"data": "x {not json"}, {"data": 5}, "text"):
            self.assertEqual(extra.sensors(bad), [])

    def test_node_detail_carries_them(self):
        d = extra.node_detail({"PveMod_JsonSensorInfo": {"temp_unit": "C", "data": self.DATA}}, {}, {}, {}, [], {}, [], [], [])
        self.assertEqual(len(d["sensors"]), 5)
        self.assertEqual(d["temp_unit"], "C")
