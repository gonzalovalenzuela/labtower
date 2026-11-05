"""Permiso «ver números de serie»: migración, panel de usuarios y filtrado en UPS, NAS y Proxmox."""
import unittest

from tests import support
from tests.support import ADMIN, READONLY, auth


class Auth(unittest.TestCase):
    def test_without_serials_drops_every_serial_variable_and_keeps_the_rest(self):
        v = {"ups.serial": "A1", "device.serial": "B2", "battery.serial": "C3", "_serial": "A1", "ups.status": "OL", "ups.model": "X", "ups.serialnumber": "keep"}
        self.assertEqual(auth.without_serials(v), {"ups.status": "OL", "ups.model": "X", "ups.serialnumber": "keep"})

    def test_can_see_serials_follows_the_permission(self):
        yes = support.make_user("serial_yes", {**READONLY, "serials": "readonly"})
        no = support.make_user("serial_no", {**READONLY, "serials": "none"})
        missing = support.make_user("serial_missing", READONLY)
        self.assertTrue(auth.can_see_serials(yes))
        self.assertFalse(auth.can_see_serials(no)); self.assertFalse(auth.can_see_serials(missing)); self.assertFalse(auth.can_see_serials(""))

    def test_migration_keeps_it_only_for_admins_of_wol_or_ups(self):
        with auth.users_lock():
            us = auth.load_users()
            for name, p in (("mig_wol", {**READONLY, "wol": "admin"}), ("mig_nut", {**READONLY, "nut": "admin"}), ("mig_ro", READONLY),
                            ("mig_set", {**READONLY, "serials": "none", "wol": "admin"})):
                us[name] = {"password_hash": "x", "permissions": dict(p), "created": 1}
            auth.save_users(us)
        auth.ensure_permissions()
        us = auth.load_users()
        got = {n: us[n]["permissions"].get("serials") for n in ("mig_wol", "mig_nut", "mig_ro", "mig_set")}
        self.assertEqual(got, {"mig_wol": "readonly", "mig_nut": "readonly", "mig_ro": "none", "mig_set": "none"})   # an explicit value is never overwritten


class AdminPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = support.Server(support.load("auth/admin_panel.py").H)
        cls.pw = "Admin-pass-12345"
        cls.tok = support.make_user("serialadm", {**ADMIN, "serials": "readonly"}, password=cls.pw)
        cls.tok_noser = support.make_user("serialadm2", ADMIN, password=cls.pw)
    @classmethod
    def tearDownClass(cls): cls.s.close()

    def _create(self, name, tok=None, **extra):
        return self.s.call("POST", "/api/users", {"username": name, "password": "Another-pass-123", "current_password": self.pw, **extra}, tok or self.tok)

    def test_new_users_do_not_get_it_by_default(self):
        self.assertEqual(self._create("ser_def")[0], 201)
        self.assertEqual(auth.load_users()["ser_def"]["permissions"]["serials"], "none")

    def test_it_can_be_granted_when_creating(self):
        self.assertEqual(self._create("ser_yes", serials_permission="readonly")[0], 201)
        self.assertEqual(auth.load_users()["ser_yes"]["permissions"]["serials"], "readonly")

    def test_only_yes_or_no_are_accepted(self):
        self.assertEqual(self._create("ser_bad", serials_permission="admin")[0], 400)
        self.assertEqual(self.s.call("PUT", "/api/users/ser_def", {"serials_permission": "execute"}, self.tok)[0], 400)

    def test_you_cannot_grant_what_you_do_not_have(self):
        self.assertEqual(self._create("ser_nogrant", self.tok_noser, serials_permission="readonly")[0], 403)

    def test_it_can_be_changed_later_and_listed(self):
        support.make_user("ser_edit", {**READONLY, "serials": "none"})
        r = self.s.call("PUT", "/api/users/ser_edit", {"serials_permission": "readonly", "current_password": self.pw}, self.tok)
        self.assertEqual(r[0], 200, r)
        _, d = self.s.call("GET", "/api/users", token=self.tok)
        self.assertEqual(next(u for u in d["users"] if u["username"] == "ser_edit")["permissions"]["serials"], "readonly")


class Modules(unittest.TestCase):
    def test_ups_snapshot_loses_the_serials_unless_allowed(self):
        m = support.load("nut-monitor/server.py")
        snap = {"id": "s1", "ups": {"ups1": {"ups.serial": "A1", "_serial": "A1", "ups.status": "OL"}}}
        self.assertEqual(m._no_serials(snap, True), snap)
        self.assertEqual(m._no_serials(snap, False)["ups"]["ups1"], {"ups.status": "OL"})
        self.assertEqual(snap["ups"]["ups1"]["ups.serial"], "A1")        # the cached copy is not touched

    def test_nas_serial_is_hidden_unless_allowed(self):
        m = support.load("nas-monitor/server.py")
        snap = {"id": "n1", "data": {"system": {"model": "DS", "serial": "S9"}, "cpu": {}}, "error": None, "ts": 1}
        self.assertEqual(m._snap_no_serial(snap)["data"]["system"], {"model": "DS", "serial": ""})
        self.assertEqual(snap["data"]["system"]["serial"], "S9")
        self.assertEqual(m._snap_no_serial({"id": "n2", "data": {}, "error": "x"}), {"id": "n2", "data": {}, "error": "x"})

    def test_proxmox_drive_serials_are_hidden_unless_allowed(self):
        m = support.load("proxmox-monitor/server.py")
        sm = {"ts": 1, "nodes": {"n1": {"disks": [{"dev": "/dev/sda", "serial": "S1"}], "error": None}}}
        self.assertEqual(m._smart_view(sm, True), sm)
        self.assertEqual(m._smart_view(sm, False)["nodes"]["n1"]["disks"], [{"dev": "/dev/sda", "serial": ""}])
        self.assertEqual(sm["nodes"]["n1"]["disks"][0]["serial"], "S1")
        self.assertIsNone(m._smart_view(None, False))

    def test_proxmox_machine_serial_is_apart_from_the_visible_text(self):
        ex = support.load("proxmox-monitor/extra.py")
        st = {"PveMod_systemInfo": {"serial_number": "SN-123", "manufacturer": "Dell Inc.", "product_name": "OptiPlex"}}
        d = ex.node_detail(st, {}, {}, {}, [], {}, [], [], [])
        self.assertEqual(d["serial"], "SN-123")
        self.assertNotIn("SN-123", str(d["other"]))


if __name__ == "__main__":
    unittest.main()
