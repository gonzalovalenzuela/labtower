#!/usr/bin/env python3
"""
Switch Monitor — monitoreo de switches administrables para Net Monitor (solo biblioteca estándar de Python 3).

Drivers: zx (ZX310S-8T2XS), hc (HC-SWTGW218AS) y snmp (cualquier switch con IF-MIB / BRIDGE-MIB, p. ej. TP-Link).
Los tres entregan el mismo snapshot normalizado:
  {"switch", "driver", "host", "timestamp", "scrape_seconds",
   "system": {model, description, mac, ipv4, fw, hw, temperature_c, stp_enabled, ...},
   "ports": [{port, admin_up, link_up, link, speed_mbps, speed_cfg, flow_ctrl, tx_good_pkts, tx_bad_pkts,
              rx_good_pkts, rx_bad_pkts, loop_detected, stp_state, [rx_bytes, tx_bytes, rx_discards, tx_discards]}],
   "macs": [{mac, port, vlan, ...}]}
Los campos que un modelo no soporta quedan en None.

Seguridad: SOLO LECTURA. Las rutas con efectos sobre el equipo están bloqueadas en el código (en el ZX,
clear_statistics.json es un GET que borra los contadores; en el HC, cualquier POST a mac.cgi sin cmd=nextpage borra la
tabla MAC).

EN: Switch Monitor — monitoring of managed switches for Net Monitor (Python 3 standard library only).
    Drivers: zx (ZX310S-8T2XS), hc (HC-SWTGW218AS) and snmp (any switch with IF-MIB / BRIDGE-MIB, e.g. TP-Link).
    All three return the same normalised snapshot (above); fields a model does not support stay None.
    Security: READ ONLY. Routes that change the device are blocked in code (on the ZX, clear_statistics.json is a GET that
    wipes the counters; on the HC any POST to mac.cgi without cmd=nextpage wipes the MAC table).

Uso de diagnóstico / Diagnostics:  python3 switches.py --config switches.json --once
"""
import hashlib
import http.cookiejar
import json
import os
import re
import socket
import sqlite3
import sys
import threading
import time
import urllib.parse
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


class SessionExpired(Exception):
    pass


def md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def speed_mbps(link):
    """'2500MbpsFull', '2500Full', '10GbpsFull', '10GFull', '100Full' -> Mbps"""
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*(G|M)?", link or "")
    if not m or "down" in (link or "").lower():
        return 0
    n = float(m.group(1))
    return int(n * 1000) if m.group(2) == "G" else int(n)


def _num(v):
    """First number inside a value like '74', '74.5', '74 C' (None if there is none)."""
    m = re.search(r"-?\d+(?:\.\d+)?", str(v)) if v not in (None, "") else None
    return float(m.group(0)) if m else None


class BaseDriver:
    FORBIDDEN = set()

    def __init__(self, name, host, user, password, timeout=8, gap=0.3):
        self.name, self.host = name, host
        self.base = f"http://{host}/"
        self.user, self.password = user, password
        self.timeout, self.gap = timeout, gap
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.lock = threading.Lock()  # estos httpd no toleran peticiones concurrentes / these httpd cannot take parallel requests
        self.logged_in = False

    def _check(self, path):
        clean = path.split("?")[0]
        if path in self.FORBIDDEN or clean in self.FORBIDDEN:
            raise ValueError(f"{path} bloqueado: tiene efectos sobre el switch")

    def _open(self, path, data=None):
        self._check(path)
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        try:
            with self.opener.open(self.base + path, data=body, timeout=self.timeout) as r:
                text = r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            # Indica qué petición falló (sin la consulta: lleva las credenciales en MD5). / EN: Says which request failed (no query string: it carries the MD5 credentials).
            raise OSError(f"el switch respondió HTTP {e.code} a {'POST' if body is not None else 'GET'} /{path.split('?')[0]}") from None
        time.sleep(self.gap)
        return text

    def fetch(self, path, data=None):
        with self.lock:
            if not self.logged_in:
                self.login()
            try:
                return self._fetch(path, data)
            except SessionExpired:
                self.login()
                return self._fetch(path, data)

    def snapshot(self, with_macs=True):
        ts = time.time()
        snap = self._collect(with_macs)
        snap.update(switch=self.name, driver=self.DRIVER, host=self.host, timestamp=ts,
                    scrape_seconds=round(time.time() - ts, 3))
        snap["ports"].sort(key=lambda p: p["port"])
        return snap


# --------------------------------------------------------------------------- ZX310S
class ZXDriver(BaseDriver):
    DRIVER = "zx"
    FORBIDDEN = {"clear_statistics.json", "system_reboot.json", "factory_reset.json",
                 "mac_clear_dynamic_mac_entries.json", "config/download", "firmware/download"}
    # índice del JSON -> puerto del frontal (los SFP+ vienen cruzados) / JSON index -> front-panel port (SFP+ are crossed)
    JSON_TO_FRONT = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 10, 10: 9}
    MAC_TO_FRONT = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 10, 13: 9}

    def login(self):
        q = urllib.parse.urlencode({"loginusr": md5(self.user), "loginpwd": md5(self.password)})
        if "login.html" in self._open("authorize?" + q):
            raise RuntimeError(f"{self.name}: login rechazado")
        self.logged_in = True

    def _fetch(self, path, data=None):
        text = self._open(path, data)
        if "login.html" in text and not text.lstrip().startswith("{"):
            raise SessionExpired()
        return json.loads(text)

    def _macs(self, max_pages=40):
        out, seen = [], set()
        page = self.fetch("mac_get_dynamic_mac_entries.json")
        for _ in range(max_pages):
            n, new = int(page.get("total_entries", 0)), 0
            for i in range(n):
                e = page.get(f"Idx_{i}")
                if not e or e["Dynamic_mac_addr"] in seen:
                    continue
                seen.add(e["Dynamic_mac_addr"])
                new += 1
                raw = int(e["Dynamic_portid"])
                out.append({"mac": e["Dynamic_mac_addr"], "port": self.MAC_TO_FRONT.get(raw, raw),
                            "vlan": int(e["Dynamic_fid"]), "age": int(e["Dynamic_age_timer"])})
            if n < 50 or new == 0:
                break
            page = self.fetch("mac_get_next_dynamic_mac_entries.json")
        return out

    def _collect(self, with_macs):
        st = self.fetch("status.json")
        stats = self.fetch("port_statistics.json")
        cfg = self.fetch("port_setting_load.json")
        loop = self.fetch("port_loop_status.json")
        stp = self.fetch("stp.json")
        ports = []
        for j in range(1, int(stats["PortNum"]) + 1):
            s, c = stats[f"Port_{j}"], cfg[f"Port_{j}"]
            link = s["Link_Status"]
            ports.append({
                "port": self.JSON_TO_FRONT.get(j, j),
                "admin_up": s["Port_Status"] == "Enabled",
                "link_up": link != "Link Down", "link": link, "speed_mbps": speed_mbps(link),
                "speed_cfg": c["Spd_Duplex_Cfg"],
                "flow_ctrl": c["Flow_Ctrl_Actual"],
                "tx_good_pkts": int(s["TxGoodPkt"]), "tx_bad_pkts": int(s["TxBadPkt"]),
                "rx_good_pkts": int(s["RxGoodPkt"]), "rx_bad_pkts": int(s["RxBadPkt"]),
                "loop_detected": loop.get(f"Violdetd_{j}") == "1",
                "stp_state": stp.get(f"Port_{j}", {}).get(f"Stp_Status_{j}"),
            })
        return {
            "system": {"model": st.get("modle"), "description": st.get("des"),
                       "mac": st.get("sys_macaddr"), "ipv4": st.get("sys_ipv4"),
                       "fw": st.get("fw_ver"), "hw": st.get("hw_ver"),
                       "temperature_c": _num(st.get("temperature")),
                       "stp_enabled": stp.get("stp_enable") == "1"},
            "ports": ports,
            "macs": self._macs() if with_macs else None,
        }


# --------------------------------------------------------------------------- HC-SWTGW218AS
class _Tables(HTMLParser):
    """Extrae todas las <table> como listas de filas de texto. / Extracts every <table> as lists of text rows."""

    def __init__(self):
        super().__init__()
        self.tables, self._stack, self._row, self._cell = [], [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._stack.append([])
        elif tag == "tr" and self._stack:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._stack:
            if any(self._row):
                self._stack[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._stack:
            self.tables.append(self._stack.pop())

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def tables(html):
    p = _Tables()
    p.feed(html)
    return p.tables


def find_table(html, first_cell):
    for t in tables(html):
        if t and t[0] and t[0][0] == first_cell and len(t) > 1:
            return t
    return []


class HCDriver(BaseDriver):
    DRIVER = "hc"
    FORBIDDEN = {"reset.cgi", "save.cgi", "reboot.cgi", "logout.cgi", "fwug.cgi", "config_back.cgi"}

    def __init__(self, *a, mac_paginate=False, **kw):
        super().__init__(*a, **kw)
        self.mac_paginate = mac_paginate

    def login(self):
        token = md5(self.user + self.password)
        self.jar.set_cookie(http.cookiejar.Cookie(
            0, "admin", token, None, False, self.host.split(":")[0], False, False,
            "/", True, False, None, False, None, None, {}))
        # El POST a login.cgi es «de cortesía»: en el equipo real puede responder 400 aunque la cookie ya baste. Lo que decide es info.cgi.
        # EN: The login.cgi POST is best-effort: the real unit may answer 400 even when the cookie is enough. info.cgi decides.
        post_err = None
        try:
            self._open("login.cgi", {"username": self.user, "password": self.password,
                                     "language": "EN", "Response": token})
        except OSError as e:
            post_err = str(e)
        if self._is_login(self._open("info.cgi")):
            raise RuntimeError(f"{self.name}: login rechazado" + (f" ({post_err})" if post_err else ""))
        self.logged_in = True

    @staticmethod
    def _is_login(text):
        return "login.cgi" in text and len(text) < 600

    def _fetch(self, path, data=None):
        if data is not None and path.startswith("mac.cgi") and data.get("cmd") != "nextpage":
            raise ValueError("POST a mac.cgi sin cmd=nextpage borraría la tabla MAC")
        if data is not None and not path.startswith("mac.cgi"):
            raise ValueError("el driver HC solo hace POST para paginar la tabla MAC")
        text = self._open(path, data)
        if self._is_login(text):
            raise SessionExpired()
        return text

    def _macs(self, paginate):
        rows = find_table(self.fetch("mac.cgi?page=fwd_tbl"), "No.")[1:]
        if paginate:  # opcional: la paginación no fue probada contra el equipo real / optional: pagination was never tried on the real unit
            seen = {r[1] for r in rows}
            for _ in range(20):
                more = find_table(self.fetch("mac.cgi?page=fwd_tbl", {"cmd": "nextpage"}), "No.")[1:]
                new = [r for r in more if r[1] not in seen]
                if not new:
                    break
                rows += new
                seen.update(r[1] for r in new)
        return [{"mac": r[1], "vlan": int(r[2]), "type": r[3], "port": int(r[4])}
                for r in rows if len(r) >= 5 and r[2].isdigit() and r[4].isdigit()]

    def _collect(self, with_macs):
        info = {r[0]: r[1] for r in find_table(self.fetch("info.cgi"), "Device Model")
                if len(r) >= 2}
        stats = find_table(self.fetch("port.cgi?page=stats"), "Port")
        cfg = {}
        for t in tables(self.fetch("port.cgi")):
            for r in t:
                if len(r) == 6 and r[0].startswith("Port "):
                    cfg[int(r[0].split()[1])] = r
        stp = {}
        for t in tables(self.fetch("loop.cgi?page=stp_port")):
            for r in t:
                if len(r) >= 3 and r[0].startswith("Port ") and r[1] in (
                        "Forwarding", "Blocking", "Learning", "Listening", "Disabled", "Discarding"):
                    stp[int(r[0].split()[1])] = r[1]
        # Algunos firmwares añaden columnas de bytes (TxBytes / RxBytes) a la tabla de estadísticas; se detectan por el nombre del encabezado.
        # EN: Some firmwares add byte columns (TxBytes / RxBytes) to the statistics table; they are found by header name.
        hdr = [h.lower().replace(" ", "") for h in (stats[0] if stats else [])]
        ix_tx = next((i for i, h in enumerate(hdr) if "tx" in h and "byte" in h), None)
        ix_rx = next((i for i, h in enumerate(hdr) if "rx" in h and "byte" in h), None)
        count = lambda r, i: (_num(r[i].replace(",", "")) if i is not None and i < len(r) else None)  # noqa: E731
        ports = []
        for r in stats[1:]:
            if len(r) < 7 or not r[0].startswith("Port "):
                continue
            n = int(r[0].split()[1])
            c = cfg.get(n, [""] * 6)
            link = c[3] or r[2]  # port.cgi trae la velocidad real; stats solo Up/Down / port.cgi has the real speed; stats only Up/Down
            ports.append({
                "port": n,
                "admin_up": r[1] == "Enable",
                "link_up": r[2] == "Link Up", "link": link,
                "speed_mbps": speed_mbps(link) if r[2] == "Link Up" else 0,
                "speed_cfg": c[2] or None, "flow_ctrl": c[5] or None,
                "tx_good_pkts": int(r[3]), "tx_bad_pkts": int(r[4]),
                "rx_good_pkts": int(r[5]), "rx_bad_pkts": int(r[6]),
                **({"rx_bytes": int(count(r, ix_rx)), "tx_bytes": int(count(r, ix_tx))}
                   if count(r, ix_rx) is not None and count(r, ix_tx) is not None else {}),
                "loop_detected": None,  # este firmware no reporta loop por puerto / this firmware has no per-port loop flag
                "stp_state": stp.get(n),
            })
        return {
            "system": {"model": info.get("Device Model"), "description": None,
                       "mac": info.get("MAC Address"), "ipv4": info.get("IP Address"),
                       "fw": info.get("Firmware Version"), "hw": info.get("Hardware Version"),
                       "temperature_c": None, "stp_enabled": None},
            "ports": ports,
            "macs": self._macs(self.mac_paginate) if with_macs else None,
        }


# --------------------------------------------------------------------------- SNMP (stdlib)
class SNMPError(Exception):
    pass


def _ber_len(n):
    if n < 0x80:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(b)]) + b


def _tlv(tag, payload):
    return bytes([tag]) + _ber_len(len(payload)) + payload


def _ber_int(v):
    return _tlv(0x02, v.to_bytes(max(1, (v.bit_length() + 8) // 8), "big", signed=True))


def _ber_oid(oid):
    parts = [int(x) for x in oid.strip(".").split(".")]
    out = bytearray([parts[0] * 40 + parts[1]])
    for p in parts[2:]:
        chunk = [p & 0x7F]
        p >>= 7
        while p:
            chunk.insert(0, 0x80 | (p & 0x7F))
            p >>= 7
        out += bytes(chunk)
    return _tlv(0x06, bytes(out))


def _ber_read(buf, i):
    tag = buf[i]
    ln = buf[i + 1]
    i += 2
    if ln & 0x80:
        n = ln & 0x7F
        ln = int.from_bytes(buf[i:i + n], "big")
        i += n
    return tag, buf[i:i + ln], i + ln


def _ber_seq(payload):
    items, i = [], 0
    while i < len(payload):
        tag, val, i = _ber_read(payload, i)
        items.append((tag, val))
    return items


def _dec_oid(b):
    parts = [b[0] // 40, b[0] % 40]
    v = 0
    for x in b[1:]:
        v = (v << 7) | (x & 0x7F)
        if not x & 0x80:
            parts.append(v)
            v = 0
    return ".".join(map(str, parts))


_END = object()  # noSuchObject / noSuchInstance / endOfMibView


def _dec_value(tag, val):
    if tag == 0x02:
        return int.from_bytes(val, "big", signed=True)
    if tag in (0x41, 0x42, 0x43, 0x46):  # Counter32, Gauge32, TimeTicks, Counter64
        return int.from_bytes(val, "big")
    if tag == 0x04:
        return val
    if tag == 0x06:
        return _dec_oid(val)
    if tag == 0x40:
        return ".".join(map(str, val))
    if tag in (0x80, 0x81, 0x82):
        return _END
    return None


class SNMPClient:
    """SNMPv2c mínimo: GET y walk con GETBULK. Solo lectura. / Minimal SNMPv2c: GET and GETBULK walk. Read only."""

    def __init__(self, host, community, port=161, timeout=2.0, retries=2):
        self.addr = (host, port)
        self.community = community.encode()
        self.timeout, self.retries = timeout, retries
        self._rid = int(time.time()) & 0x3FFFFFFF

    def _request(self, pdu_tag, oids, non_rep=0, max_rep=0):
        self._rid = (self._rid + 1) & 0x3FFFFFFF
        vbs = b"".join(_tlv(0x30, _ber_oid(o) + b"\x05\x00") for o in oids)
        pdu = _tlv(pdu_tag, _ber_int(self._rid) + _ber_int(non_rep) + _ber_int(max_rep)
                   + _tlv(0x30, vbs))
        msg = _tlv(0x30, _ber_int(1) + _tlv(0x04, self.community) + pdu)  # version 1 = v2c
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self.timeout)
        try:
            for _ in range(self.retries + 1):
                s.sendto(msg, self.addr)
                try:
                    while True:
                        data, _ = s.recvfrom(65535)
                        out = self._parse(data)
                        if out is not None:
                            return out
                except OSError:
                    continue
            raise SNMPError(f"sin respuesta SNMP de {self.addr[0]} (¿community o ACL?)")
        finally:
            s.close()

    def _parse(self, data):
        _, msg, _ = _ber_read(data, 0)
        _ver, _comm, (ptag, pdu) = _ber_seq(msg)[:3]
        f = _ber_seq(pdu)
        if int.from_bytes(f[0][1], "big") != self._rid:
            return None  # respuesta de otra petición / reply to another request
        err = int.from_bytes(f[1][1], "big")
        if err:
            raise SNMPError(f"error SNMP {err} (index {int.from_bytes(f[2][1], 'big')})")
        out = []
        for _, vb in _ber_seq(f[3][1]):
            (_, oid), (vtag, val) = _ber_seq(vb)
            out.append((_dec_oid(oid), _dec_value(vtag, val)))
        return out

    def get(self, oids):
        return {o: v for o, v in self._request(0xA0, oids) if v is not _END}

    def walk(self, base, max_rep=20):
        base = base.strip(".")
        prefix, cur, out = base + ".", base, {}
        for _ in range(5000):
            rows = self._request(0xA5, [cur], 0, max_rep)
            done = False
            for oid, val in rows:
                if val is _END or not oid.startswith(prefix):
                    done = True
                    break
                out[oid[len(prefix):]] = val
                cur = oid
            if done or not rows:
                break
        return out


def _s(v):
    return v.decode("utf-8", "replace").strip("\x00 ") if isinstance(v, bytes) else v


def _mac_str(v):
    return ":".join(f"{b:02X}" for b in v) if isinstance(v, bytes) and len(v) == 6 else None


class SNMPDriver(BaseDriver):
    """Cualquier switch con IF-MIB / BRIDGE-MIB (pensado para TP-Link). / Any switch with IF-MIB / BRIDGE-MIB (made for TP-Link)."""
    DRIVER = "snmp"
    SYS = "1.3.6.1.2.1.1"
    IF = "1.3.6.1.2.1.2.2.1"
    IFX = "1.3.6.1.2.1.31.1.1.1"
    BRIDGE_ADDR = "1.3.6.1.2.1.17.1.1.0"           # dot1dBaseBridgeAddress
    BASE_PORT_IFINDEX = "1.3.6.1.2.1.17.1.4.1.2"
    Q_FDB_PORT = "1.3.6.1.2.1.17.7.1.2.2.1.2"   # dot1qTpFdbPort (fdbId.mac)
    D_FDB_PORT = "1.3.6.1.2.1.17.4.3.1.2"       # dot1dTpFdbPort (mac)
    VIRTUAL = re.compile(r"^(vlan|loopback|null|port-?channel|link.?aggregation|tunnel|lo\d*$)", re.I)
    PORT_NAME = re.compile(r"\d+/\d+/(\d+)")

    def __init__(self, name, host, community, port=161, **kw):
        super().__init__(name, host, "", "")
        self.snmp = SNMPClient(host, community, port=port, **kw)

    def login(self):
        self.logged_in = True

    def _macs(self, bp_to_port):
        rows = self.snmp.walk(self.Q_FDB_PORT)
        out = []
        if rows:
            for idx, bp in rows.items():
                p = idx.split(".")
                vlan, mac = int(p[0]), ":".join(f"{int(x):02X}" for x in p[1:7])
                out.append({"mac": mac, "vlan": vlan, "port": bp_to_port.get(bp, bp)})
        else:
            for idx, bp in self.snmp.walk(self.D_FDB_PORT).items():
                mac = ":".join(f"{int(x):02X}" for x in idx.split(".")[:6])
                out.append({"mac": mac, "vlan": None, "port": bp_to_port.get(bp, bp)})
        return [e for e in out if e["port"] not in (0, None)]

    def _collect(self, with_macs):
        with self.lock:
            sysv = self.snmp.get([f"{self.SYS}.{n}.0" for n in (1, 3, 5)] + [self.BRIDGE_ADDR])
            col = lambda base, c: self.snmp.walk(f"{base}.{c}")  # noqa: E731
            if_type, if_descr = col(self.IF, 3), col(self.IF, 2)
            admin, oper = col(self.IF, 7), col(self.IF, 8)
            in_err, out_err = col(self.IF, 14), col(self.IF, 20)
            in_disc, out_disc = col(self.IF, 13), col(self.IF, 19)
            if_speed = col(self.IF, 5)
            x = {c: col(self.IFX, c) for c in (1, 6, 7, 8, 9, 10, 11, 12, 13, 15, 18)}
            bp = {str(v): k for k, v in self.snmp.walk(self.BASE_PORT_IFINDEX).items()}

            # puertos físicos: ifType 6 (ethernetCsmacd); numerados por puerto de bridge
            # EN: physical ports: ifType 6 (ethernetCsmacd); numbered by bridge port
            # Se descartan las interfaces virtuales que algunos equipos declaran como ethernet (p. ej. «Vlan-interface1» del TP-Link).
            # EN: Virtual interfaces some devices declare as ethernet (e.g. the TP-Link's "Vlan-interface1") are skipped.
            pname = lambda i: _s(x[1].get(str(i))) or _s(if_descr.get(str(i))) or ""  # noqa: E731
            phys = sorted(int(i) for i, t in if_type.items() if t == 6 and not self.VIRTUAL.match(pname(i)))
            port_no = {i: int(bp[str(i)]) if str(i) in bp else n
                       for n, i in enumerate(phys, 1)}
            # Con nombres tipo «gigabitEthernet 1/0/12» el número del puerto es el último (el índice puede ser 49164 y la tabla MAC usa 12).
            # EN: With names like "gigabitEthernet 1/0/12" the port number is the last one (the ifIndex may be 49164 while the MAC table uses 12).
            named = {i: int(m.group(1)) for i in phys for m in [self.PORT_NAME.search(pname(i))] if m}
            if len(named) == len(phys) and len(set(named.values())) == len(phys):
                port_no = named
            ports = []
            for i in phys:
                k = str(i)
                g = lambda c: x[c].get(k)  # noqa: E731
                up = oper.get(k) == 1
                spd = g(15) or (if_speed.get(k) or 0) // 1_000_000
                hc = all(g(c) is not None for c in (6, 10))
                ports.append({
                    "port": port_no[i], "ifindex": i,
                    "name": _s(g(1)) or _s(if_descr.get(k)), "alias": _s(g(18)) or None,
                    "admin_up": admin.get(k) == 1, "link_up": up,
                    "link": f"{spd}Mbps" if up else "Link Down",
                    "speed_mbps": spd if up else 0,
                    "speed_cfg": None, "flow_ctrl": None,
                    "rx_bytes": g(6) if hc else None, "tx_bytes": g(10) if hc else None,
                    "rx_good_pkts": sum(g(c) or 0 for c in (7, 8, 9)),
                    "tx_good_pkts": sum(g(c) or 0 for c in (11, 12, 13)),
                    "rx_bad_pkts": in_err.get(k, 0), "tx_bad_pkts": out_err.get(k, 0),
                    "rx_discards": in_disc.get(k), "tx_discards": out_disc.get(k),
                    "loop_detected": None, "stp_state": None,
                })
            bp_to_port = {int(b): port_no.get(int(i), int(b)) for i, b in bp.items()}
        macs = None
        if with_macs:
            with self.lock:
                macs = self._macs(bp_to_port)
        descr = _s(sysv.get(f"{self.SYS}.1.0")) or ""
        return {
            "system": {"model": descr.split(",")[0][:60] or None, "description": descr,
                       "name": _s(sysv.get(f"{self.SYS}.5.0")),
                       "uptime_s": (sysv.get(f"{self.SYS}.3.0") or 0) / 100,
                       "mac": _mac_str(sysv.get(self.BRIDGE_ADDR)), "ipv4": self.host, "fw": None, "hw": None,
                       "temperature_c": None, "stp_enabled": None},
            "ports": ports,
            "macs": macs,
        }


DRIVERS = {"zx": ZXDriver, "hc": HCDriver, "snmp": SNMPDriver}


def build_driver(cfg):
    """Driver a partir de una entrada de configuración. / Driver from a configuration entry."""
    d = cfg.get("driver")
    if d == "snmp":
        return SNMPDriver(cfg["name"], cfg["host"], cfg.get("community") or "", port=int(cfg.get("port") or 161))
    if d in ("zx", "hc"):
        kw = {"mac_paginate": bool(cfg.get("mac_paginate"))} if d == "hc" else {}
        return DRIVERS[d](cfg["name"], cfg["host"], cfg.get("user") or "admin", cfg.get("password") or "", **kw)
    raise ValueError(f"driver desconocido: {d}")


# =========================================================================== Gestor / Manager
# ES: El gestor guarda los switches en switches.json (modo 600), consulta cada uno en su propio hilo cada POLL segundos,
#     calcula tasas entre muestras, detecta cambios (eventos), guarda historial en SQLite (switches.db) y arma la respuesta
#     que muestra la pestaña «Switch Monitor». Nada aquí escribe en los switches.
# EN: The manager stores the switches in switches.json (mode 600), polls each one in its own thread every POLL seconds,
#     computes rates between samples, detects changes (events), keeps history in SQLite (switches.db) and builds the
#     response the "Switch Monitor" tab shows. Nothing here writes to the switches.
TEMP_WARN = float(os.environ.get("SWITCH_TEMP_WARN", 70))
TEMP_CRIT = float(os.environ.get("SWITCH_TEMP_CRIT", 80))
POLL_DEFAULT, POLL_MIN, POLL_MAX = 60, 30, 3600
MAC_EVERY = 300                    # la tabla MAC pesa más: se lee cada 5 min / the MAC table is heavier: read every 5 min
FAILS_FOR_DOWN = 2                 # fallos seguidos para dar el switch por caído / consecutive failures before "down"
ERR_EVENT_GAP = 600                # un aviso de errores nuevos por puerto cada 10 min como máximo / at most one new-errors notice per port per 10 min
RAW_KEEP = 48 * 3600               # muestras de 1 min durante 48 h; después se resumen cada 15 min / 1-min samples for 48 h, then 15-min summaries
AGG_STEP = 900
KEEP = 365 * 86400                 # el historial resumido se conserva 1 año, como UPS Monitor / summaries kept 1 year, like UPS Monitor
RANGE_SECS = {"1h": 3600, "1d": 86400, "1w": 604800, "1mo": 2592000}
RANGE_LIMIT = {"1h": 720, "1d": 1440, "1w": 2016, "1mo": 2880, "all": 4320}
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,31}$")
HOST_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?(:\d{1,5})?$")


def _mkey(mac):
    return re.sub(r"[^0-9a-f]", "", str(mac or "").lower())


def _same_device(a, b):
    """Dos MAC del mismo equipo: los switches usan MAC base + n por puerto, así que se comparan los primeros 5 bytes.
    EN: Two MACs of the same device: switches use base MAC + n per port, so the first 5 bytes are compared."""
    a, b = _mkey(a), _mkey(b)
    return len(a) == 12 and len(b) == 12 and a[:10] == b[:10]


def _delta(new, old):
    return new - old if isinstance(new, (int, float)) and isinstance(old, (int, float)) and new >= old else None


def _clean_text(s, n):
    return "".join(ch for ch in str(s or "") if ch.isprintable())[:n].strip()


def redact(cfg):
    """Config sin secretos para la API. / Config without secrets for the API."""
    out = {k: v for k, v in cfg.items() if k not in ("password", "community")}
    out["has_password"] = bool(cfg.get("password"))
    out["has_community"] = bool(cfg.get("community"))
    return out


def validate(body, current=None):
    """Valida el cuerpo de «guardar» o «probar» y devuelve la entrada de configuración. Una contraseña o community vacía
    al editar conserva la guardada. EN: Validate the "save" / "test" body and return the config entry. An empty password or
    community while editing keeps the stored one."""
    cur = current or {}
    name = _clean_text(body.get("name", cur.get("name", "")), 32)
    if not NAME_RE.match(name):
        raise ValueError("Invalid name (letters, digits, space . _ - ; up to 32)")
    driver = body.get("driver", cur.get("driver"))
    if driver not in DRIVERS:
        raise ValueError("Invalid driver (zx, hc or snmp)")
    host = _clean_text(body.get("host", cur.get("host", "")), 255)
    if not HOST_RE.match(host) or (driver == "snmp" and ":" in host):
        raise ValueError("Invalid host (IP or name" + ("" if driver == "snmp" else ", optional :port") + ")")
    cfg = {"id": cur.get("id", ""), "name": name, "driver": driver, "host": host,
           "enabled": bool(body.get("enabled", cur.get("enabled", True))), "ports": dict(cur.get("ports") or {})}
    # Distribución del panel frontal: una fila, o dos filas alternadas (1 arriba, 2 abajo, 3 arriba…). / EN: front-panel layout: one row, or two alternating rows.
    layout = body.get("layout", cur.get("layout", "auto"))
    if layout not in ("auto", "row", "alt"):
        raise ValueError("Invalid layout (auto, row or alt)")
    cfg["layout"] = layout
    if driver == "snmp":
        comm = body.get("community") or cur.get("community") or ""
        if not comm or len(comm) > 64 or not comm.isprintable():
            raise ValueError("SNMP community required (up to 64 characters)")
        try:
            port = int(body.get("port", cur.get("port") or 161))
        except (TypeError, ValueError):
            raise ValueError("Invalid SNMP port")
        if not 1 <= port <= 65535:
            raise ValueError("Invalid SNMP port")
        cfg.update(community=comm, port=port)
    else:
        user = _clean_text(body.get("user", cur.get("user", "admin")), 64) or "admin"
        pw = body.get("password") or cur.get("password") or ""
        if not pw or len(pw) > 128 or not pw.isprintable():
            raise ValueError("Password required (up to 128 characters)")
        cfg.update(user=user, password=pw)
        if driver == "hc":
            cfg["mac_paginate"] = bool(body.get("mac_paginate", cur.get("mac_paginate", False)))
    return cfg


def _atomic_json(path, data):
    path = str(path)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


class _Worker:
    def __init__(self, thread=None):
        self.stop, self.ev, self.thread = False, threading.Event(), thread


class Manager:
    """hooks (todos opcionales / all optional):
       event(module, level, text, key, **params)  → anota un evento / records an event
       changed(key, state)                        → (viejo, nuevo) si el estado cambió / (old, new) if the state changed
       hosts()                                    → {mac_sin_separadores: {"ip", "name"}} / {mac_without_separators: {...}}"""

    def __init__(self, data_dir, hooks=None, log=None):
        self.dir = Path(data_dir)
        self.conf_file, self.db_file = self.dir / "switches.json", self.dir / "switches.db"
        self.hooks = hooks or {}
        self.log = log
        self.lock = threading.RLock()
        self.db_lock = threading.Lock()
        self.rec, self.workers = {}, {}
        self.cfg = {"poll_seconds": POLL_DEFAULT, "switches": []}
        self._maint = None
        self._stopped = False
        self.load()

    # ---- configuración / configuration
    def _say(self, level, msg):
        if self.log:
            getattr(self.log, level)(msg)

    def load(self):
        try:
            d = json.loads(self.conf_file.read_text())
            if isinstance(d, dict) and isinstance(d.get("switches"), list):
                d["switches"] = [s for s in d["switches"] if isinstance(s, dict) and s.get("id") and s.get("driver") in DRIVERS]
                d["poll_seconds"] = min(POLL_MAX, max(POLL_MIN, int(d.get("poll_seconds") or POLL_DEFAULT)))
                self.cfg = d
        except FileNotFoundError:
            pass
        except Exception as e:
            self._say("warning", f"switches.json unreadable: {e}")

    def _save(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        _atomic_json(self.conf_file, self.cfg)

    def poll_seconds(self):
        return self.cfg.get("poll_seconds", POLL_DEFAULT)

    def _find(self, sid):
        return next((s for s in self.cfg["switches"] if s["id"] == sid), None)

    def list_config(self):
        with self.lock:
            return {"poll_seconds": self.poll_seconds(), "switches": [redact(s) for s in self.cfg["switches"]]}

    def set_poll(self, seconds):
        try:
            seconds = int(seconds)
        except (TypeError, ValueError):
            raise ValueError("Invalid interval")
        if not POLL_MIN <= seconds <= POLL_MAX:
            raise ValueError(f"Interval must be between {POLL_MIN} and {POLL_MAX} seconds")
        with self.lock:
            self.cfg["poll_seconds"] = seconds
            self._save()
        for w in list(self.workers.values()):
            w.ev.set()

    def save_switch(self, body):
        """Agrega o edita (si trae id). Devuelve la entrada sin secretos. / Add or edit (when it has an id)."""
        with self.lock:
            cur = self._find(body.get("id")) if body.get("id") else None
            if body.get("id") and not cur:
                raise ValueError("Switch not found")
            cfg = validate(body, cur)
            for s in self.cfg["switches"]:
                if s["name"].lower() == cfg["name"].lower() and s["id"] != cfg["id"]:
                    raise ValueError("A switch with that name already exists")
            if cur:
                cur.clear()
                cur.update(cfg)
            else:
                base = re.sub(r"[^a-z0-9]+", "-", cfg["name"].lower()).strip("-") or "switch"
                sid, n = base, 1
                while self._find(sid):
                    n += 1
                    sid = f"{base}-{n}"
                cfg["id"] = sid
                self.cfg["switches"].append(cfg)
            self._save()
            out = redact(cfg)
        self.reconcile()
        return out

    def delete_switch(self, sid):
        with self.lock:
            cur = self._find(sid)
            if not cur:
                raise ValueError("Switch not found")
            self.cfg["switches"].remove(cur)
            self.rec.pop(sid, None)
            self._save()
        self.reconcile()
        with self.db_lock:
            conn = self._db()
            try:
                for t in ("sw_sys", "sw_port", "sw_sys_agg", "sw_port_agg", "sw_total"):
                    conn.execute(f"DELETE FROM {t} WHERE sw=?", (sid,))
                conn.commit()
            finally:
                conn.close()

    def set_port_meta(self, sid, port, label, uplink):
        with self.lock:
            cur = self._find(sid)
            if not cur:
                raise ValueError("Switch not found")
            try:
                port = str(int(port))
            except (TypeError, ValueError):
                raise ValueError("Invalid port")
            label = _clean_text(label, 32)
            meta = cur.setdefault("ports", {})
            if label or uplink:
                meta[port] = {"label": label, "uplink": bool(uplink)}
            else:
                meta.pop(port, None)
            self._save()

    def test(self, body):
        """Una lectura de prueba (sin tabla MAC) con los datos del formulario. / One test read (no MAC table) with the form data."""
        with self.lock:
            cur = self._find(body.get("id")) if body.get("id") else None
        cfg = validate(body, cur)
        snap = build_driver(cfg).snapshot(with_macs=False)
        sy = snap["system"]
        return {"ok": True, "model": sy.get("model"), "fw": sy.get("fw"), "ports": len(snap["ports"]),
                "ports_up": sum(1 for p in snap["ports"] if p["link_up"]), "temperature_c": sy.get("temperature_c"),
                "has_bytes": any(p.get("rx_bytes") is not None for p in snap["ports"]), "seconds": snap["scrape_seconds"]}

    # ---- hilos / threads
    def start(self):
        self._db_init()
        self.reconcile()
        if not self._maint or not self._maint.is_alive():
            self._maint = threading.Thread(target=self._maintenance, daemon=True, name="sw-maint")
            self._maint.start()

    def stop(self):
        self._stopped = True
        for w in self.workers.values():
            w.stop = True
            w.ev.set()

    def reconcile(self):
        """Un hilo por switch activo; reinicia el de los que cambiaron. / One thread per active switch; restart changed ones."""
        with self.lock:
            # La firma ignora las etiquetas de puertos: cambiarlas no reinicia el hilo. / The signature ignores port labels: changing them does not restart the thread.
            want = {s["id"]: json.dumps({k: v for k, v in s.items() if k != "ports"}, sort_keys=True)
                    for s in self.cfg["switches"] if s.get("enabled", True)}
            for sid in list(self.workers):
                w = self.workers[sid]
                if sid not in want or getattr(w, "sig", None) != want[sid]:
                    w.stop = True
                    w.ev.set()
                    del self.workers[sid]
            for i, (sid, sig) in enumerate(want.items()):
                if sid in self.workers:
                    continue
                w = _Worker()
                w.sig = sig
                w.thread = threading.Thread(target=self._loop, args=(sid, json.loads(sig), w, 2 + 3 * i), daemon=True, name=f"sw-{sid}")
                self.workers[sid] = w
                w.thread.start()

    def refresh(self, sid=None):
        """«Actualizar ahora»: respeta 30 s entre lecturas del mismo switch. / "Refresh now": at least 30 s between reads of a switch."""
        n = 0
        with self.lock:
            for s, w in self.workers.items():
                if sid and s != sid:
                    continue
                r = self.rec.get(s)
                if not r or time.time() - r.get("try_ts", 0) >= POLL_MIN:
                    w.ev.set()
                    n += 1
        return n

    def _new_rec(self):
        return {"snap": None, "macs": [], "macs_ts": 0, "ok_ts": 0, "err": None, "try_ts": 0, "fails": 0,
                "prev": None, "rates": {}, "errq": {}, "err_ev": {}}

    def _loop(self, sid, cfg, w, delay):
        if delay and w.ev.wait(delay) and w.stop:
            return
        w.ev.clear()
        drv = None
        while not w.stop and not self._stopped:
            with self.lock:
                rec = self.rec.setdefault(sid, self._new_rec())
                rec["try_ts"] = time.time()
                want_macs = time.time() - rec["macs_ts"] >= MAC_EVERY
            try:
                if drv is None:
                    drv = build_driver(cfg)
                snap = drv.snapshot(with_macs=want_macs)
                self._ingest(sid, cfg, snap, want_macs)
            except Exception as e:  # noqa: BLE001
                if drv is not None:
                    drv.logged_in = False
                self._fail(sid, cfg, e)
            w.ev.wait(self.poll_seconds())
            w.ev.clear()

    # ---- ingestión / ingestion
    def _event(self, level, text, key, **params):
        fn = self.hooks.get("event")
        if fn:
            try:
                fn("net", level, text, key, **params)
            except Exception as e:  # noqa: BLE001
                self._say("debug", f"event hook: {e}")

    def _changed(self, key, state):
        fn = self.hooks.get("changed")
        return fn(key, state) if fn else None

    def _fail(self, sid, cfg, err):
        msg = f"{type(err).__name__}: {err}"[:200]
        with self.lock:
            rec = self.rec.setdefault(sid, self._new_rec())
            rec["err"], rec["fails"] = msg, rec["fails"] + 1
            fails = rec["fails"]
        self._say("warning", f"[{cfg['name']}] {msg}")
        if fails >= FAILS_FOR_DOWN:
            if self._changed(f"sw-dn:{sid}", "down"):
                self._event("crit", f"{cfg['name']}: switch unreachable", "sw_down", n=cfg["name"])
            self._db_write(sid, time.time(), None, {})

    def _ingest(self, sid, cfg, snap, had_macs):
        now = snap["timestamp"]
        ports = snap["ports"]
        events = []
        with self.lock:
            rec = self.rec.setdefault(sid, self._new_rec())
            if had_macs and snap.get("macs") is not None:
                rec["macs"], rec["macs_ts"] = snap["macs"], now
            prev, rates = rec["prev"], {}
            if prev and 0 < now - prev["ts"] < 600:
                dt = now - prev["ts"]
                for p in ports:
                    q = prev["ports"].get(p["port"])
                    if not q:
                        continue
                    r = {}
                    for k, src in (("rx_pps", "rx_good_pkts"), ("tx_pps", "tx_good_pkts")):
                        d = _delta(p.get(src), q.get(src))
                        r[k] = d / dt if d is not None else None       # contador que baja = reinicio: sin tasa / a falling counter = reset: no rate
                    for k, src in (("rx_bps", "rx_bytes"), ("tx_bps", "tx_bytes")):
                        d = _delta(p.get(src), q.get(src))
                        r[k] = d * 8 / dt if d is not None else None
                    rates[p["port"]] = r
            rec["prev"] = {"ts": now, "ports": {p["port"]: p for p in ports}}
            rec["rates"], rec["snap"], rec["ok_ts"], rec["err"], rec["fails"] = rates, snap, now, None, 0
            meta = (self._find(sid) or {}).get("ports") or {}     # copia vigente (se edita sin reiniciar el hilo) / current copy
            links = self._links_locked()
            for p in ports:
                n = p["port"]
                total = (p.get("rx_bad_pkts") or 0) + (p.get("tx_bad_pkts") or 0)
                dq = rec["errq"].setdefault(n, [])
                dq.append((now, total))
                del dq[:-80]
                watched = bool((meta.get(str(n)) or {}).get("uplink")) or (sid, n) in links
                if len(dq) >= 2 and total > dq[-2][1] and now - rec["err_ev"].get(n, 0) >= ERR_EVENT_GAP:
                    rec["err_ev"][n] = now
                    events.append(("warn", f"{cfg['name']}/{n}: {total - dq[-2][1]} new errors", "sw_err", dict(n=cfg["name"], p=n, d=total - dq[-2][1])))
                st = "up" if p["link_up"] else "down"
                ch = self._changed(f"sw-link:{sid}:{n}", st)
                if ch and watched:
                    events.append(("info" if st == "up" else "warn", f"{cfg['name']}/{n}: link {st}", "sw_link", dict(n=cfg["name"], p=n, st=st)))
                if p.get("loop_detected") is not None and not watched:
                    ch = self._changed(f"sw-loop:{sid}:{n}", "loop" if p["loop_detected"] else "ok")
                    if ch and ch[1] == "loop":
                        events.append(("warn", f"{cfg['name']}/{n}: loop detected", "sw_loop", dict(n=cfg["name"], p=n)))
        if self._changed(f"sw-dn:{sid}", "up"):
            events.append(("info", f"{cfg['name']}: switch reachable again", "sw_up", dict(n=cfg["name"])))
        t = snap["system"].get("temperature_c")
        if t is not None:
            lv = "crit" if t >= TEMP_CRIT else "warn" if t >= TEMP_WARN else "ok"
            ch = self._changed(f"sw-temp:{sid}", lv)
            if ch:
                events.append(("info" if lv == "ok" else lv, f"{cfg['name']}: temperature {t:g} °C", "sw_temp" if lv != "ok" else "sw_temp_ok", dict(n=cfg["name"], t=round(t))))
        for lv, text, key, params in events:
            self._event(lv, text, key, **params)
        self._db_write(sid, now, snap, rates)

    # ---- topología / topology
    def _links_locked(self):
        """{(switch_id, puerto): otro_switch_id}: un puerto cuya tabla MAC contiene la MAC de otro switch es un enlace entre ambos.
        EN: A port whose MAC table holds another switch's MAC is a link between the two."""
        sysmac = {}
        for sid, r in self.rec.items():
            s = r.get("snap")
            if s and s["system"].get("mac"):
                sysmac[sid] = s["system"]["mac"]
        out = {}
        for sid, r in self.rec.items():
            for m in r.get("macs") or []:
                for other, om in sysmac.items():
                    if other != sid and _same_device(m["mac"], om):
                        out[(sid, m["port"])] = other
        return out

    # ---- respuesta para la página / page response
    def _err_1h(self, rec, n):
        dq = rec["errq"].get(n) or []
        if len(dq) < 2:
            return 0
        cutoff = dq[-1][0] - 3600
        first = next((v for t, v in dq if t >= cutoff), dq[0][1])
        return max(0, dq[-1][1] - first)

    def state(self):
        hosts = {}
        try:
            hosts = self.hooks["hosts"]() if self.hooks.get("hosts") else {}
        except Exception as e:  # noqa: BLE001
            self._say("debug", f"hosts hook: {e}")
        now = time.time()
        with self.lock:
            links = self._links_locked()
            names = {s["id"]: s["name"] for s in self.cfg["switches"]}
            out = []
            for cfg in self.cfg["switches"]:
                sid = cfg["id"]
                rec = self.rec.get(sid) or self._new_rec()
                snap = rec["snap"]
                meta = cfg.get("ports") or {}
                online = bool(snap) and rec["fails"] < FAILS_FOR_DOWN
                by_port = {}
                for m in rec["macs"] or []:
                    by_port.setdefault(m["port"], []).append(m)
                ports = []
                for p in (snap["ports"] if snap else []):
                    n = p["port"]
                    pm = meta.get(str(n)) or {}
                    link_to = names.get(links.get((sid, n)))
                    uplink = bool(pm.get("uplink")) or bool(link_to)
                    macs = by_port.get(n, [])
                    nb = []
                    for m in macs[:8]:
                        h = hosts.get(_mkey(m["mac"])) or {}
                        nb.append({"mac": m["mac"], "vlan": m.get("vlan"), "ip": h.get("ip"), "name": h.get("name")})
                    e1h = self._err_1h(rec, n)
                    loop = bool(p.get("loop_detected"))
                    if not p["admin_up"]:
                        flag = "off"
                    elif not p["link_up"]:
                        flag = "down"
                    elif loop and not uplink:
                        flag = "loop"
                    elif e1h > 0:
                        flag = "warn"
                    else:
                        flag = "uplink" if uplink else "up"
                    r = rec["rates"].get(n) or {}
                    ports.append({
                        "port": n, "name": p.get("name"), "alias": p.get("alias"), "label": pm.get("label", ""),
                        "uplink": uplink, "uplink_manual": bool(pm.get("uplink")), "link_to": link_to, "flag": flag,
                        "admin_up": p["admin_up"], "link_up": p["link_up"], "link": p["link"], "speed_mbps": p["speed_mbps"],
                        "speed_cfg": p.get("speed_cfg"), "flow_ctrl": p.get("flow_ctrl"), "stp_state": p.get("stp_state"),
                        "loop": loop if p.get("loop_detected") is not None else None,
                        "rx_err": p.get("rx_bad_pkts"), "tx_err": p.get("tx_bad_pkts"), "err_1h": e1h,
                        "rx_discards": p.get("rx_discards"), "tx_discards": p.get("tx_discards"),
                        "rx_bytes": p.get("rx_bytes"), "tx_bytes": p.get("tx_bytes"),
                        "rx_pps": r.get("rx_pps"), "tx_pps": r.get("tx_pps"), "rx_bps": r.get("rx_bps"), "tx_bps": r.get("tx_bps"),
                        "mac_count": len(macs), "neighbors": nb,
                    })
                sy = (snap or {}).get("system") or {}
                t = sy.get("temperature_c")
                tlv = None if t is None else "crit" if t >= TEMP_CRIT else "warn" if t >= TEMP_WARN else "ok"
                alerts = []
                if not online and rec["fails"] >= FAILS_FOR_DOWN:
                    alerts.append({"lv": "crit", "k": "down"})
                if tlv in ("warn", "crit"):
                    alerts.append({"lv": tlv, "k": "temp", "t": t})
                for p in ports:
                    if p["flag"] == "loop":
                        alerts.append({"lv": "warn", "k": "loop", "p": p["port"]})
                    elif p["flag"] == "warn":
                        alerts.append({"lv": "warn", "k": "err", "p": p["port"], "d": p["err_1h"]})
                out.append({
                    "id": sid, "name": cfg["name"], "driver": cfg["driver"], "host": cfg["host"], "enabled": cfg.get("enabled", True),
                    "online": online, "error": rec["err"], "updated": rec["ok_ts"] or None,
                    "age": int(now - rec["ok_ts"]) if rec["ok_ts"] else None, "scrape": (snap or {}).get("scrape_seconds"),
                    "system": sy, "temp_level": tlv, "ports": ports,
                    "layout": cfg.get("layout") if cfg.get("layout") in ("row", "alt") else ("alt" if cfg["driver"] == "snmp" and len(ports) >= 16 else "row"),
                    "has_bytes": any(q.get("rx_bytes") is not None for q in ((snap or {}).get("ports") or [])),
                    "ports_up": sum(1 for p in ports if p["link_up"]), "ports_total": len(ports),
                    "macs_total": len(rec["macs"] or []), "alerts": alerts,
                })
            edges, seen = [], {}
            for (sid, port), other in links.items():
                a, b = names.get(sid), names.get(other)
                if not a or not b:
                    continue
                key = frozenset((sid, other))
                bport = None
                om = (self.rec.get(sid, {}).get("snap") or {}).get("system", {}).get("mac")
                for m in self.rec.get(other, {}).get("macs") or []:
                    if om and _same_device(m["mac"], om):
                        bport = m["port"]
                        break
                e = {"a": a, "a_port": port, "b": b, "b_port": bport}
                if key not in seen:
                    seen[key] = e
                    edges.append(e)
                elif bport is not None and seen[key]["b_port"] is None:
                    seen[key].update(e)
        return {"switches": out, "edges": edges, "poll_seconds": self.poll_seconds(), "now": int(now),
                "temp_warn": TEMP_WARN, "temp_crit": TEMP_CRIT}

    def summary(self):
        """Resumen corto para la tarjeta de Net Monitor del Resumen. / Short summary for the Overview's Net Monitor card."""
        st = self.state()
        sw = []
        for s in st["switches"]:
            lv = "ok"
            for a in s["alerts"]:
                lv = "crit" if a["lv"] == "crit" or lv == "crit" else "warn"
            sw.append({"id": s["id"], "name": s["name"], "online": s["online"], "temp": (s["system"] or {}).get("temperature_c"),
                       "ports_up": s["ports_up"], "ports_total": s["ports_total"], "lv": lv, "alerts": s["alerts"]})
        lv = "ok"
        for s in sw:
            lv = "crit" if s["lv"] == "crit" or lv == "crit" else "warn" if s["lv"] == "warn" else lv
        return {"switches": sw, "lv": lv}

    # ---- historial / history
    def _db(self):
        conn = sqlite3.connect(str(self.db_file), timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _db_init(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        with self.db_lock:
            conn = self._db()
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                for suf in ("", "_agg"):
                    conn.execute(f"""CREATE TABLE IF NOT EXISTS sw_sys{suf} (
                        ts INTEGER NOT NULL, sw TEXT NOT NULL, up REAL, temp REAL, scrape REAL, ports_up REAL,
                        PRIMARY KEY (sw, ts))""")
                    conn.execute(f"""CREATE TABLE IF NOT EXISTS sw_port{suf} (
                        ts INTEGER NOT NULL, sw TEXT NOT NULL, port INTEGER NOT NULL, link INTEGER, speed INTEGER,
                        rxp REAL, txp REAL, rxb REAL, txb REAL, err INTEGER,
                        PRIMARY KEY (sw, port, ts))""")
                # Totales acumulados por puerto: suman las diferencias entre lecturas y sobreviven a reinicios del switch y de LabTower.
                # EN: Cumulative per-port totals: they add up the differences between reads and survive switch and LabTower restarts.
                conn.execute("""CREATE TABLE IF NOT EXISTS sw_total (
                    sw TEXT NOT NULL, port INTEGER NOT NULL, rxb INTEGER, txb INTEGER, rxp INTEGER, txp INTEGER,
                    lrxb INTEGER, ltxb INTEGER, lrxp INTEGER, ltxp INTEGER, since INTEGER, updated INTEGER, resets INTEGER DEFAULT 0,
                    PRIMARY KEY (sw, port))""")
                conn.commit()
            finally:
                conn.close()

    @staticmethod
    def _totals_update(conn, sid, t, ports):
        """Suma al total de cada puerto lo que avanzó su contador desde la lectura anterior. Si el contador bajó (reinicio o borrado)
        se suma el valor actual, porque el contador volvió a empezar de cero. Un puerto nuevo parte del valor que ya traía el switch.
        EN: Adds to each port's total how far its counter advanced since the previous read. If the counter went down (reboot or clear)
        the current value is added, since the counter restarted from zero. A new port starts from the value the switch already had."""
        for p in ports:
            cur = (p.get("rx_bytes"), p.get("tx_bytes"), p.get("rx_good_pkts"), p.get("tx_good_pkts"))
            row = conn.execute("SELECT rxb,txb,rxp,txp,lrxb,ltxb,lrxp,ltxp,resets FROM sw_total WHERE sw=? AND port=?", (sid, p["port"])).fetchone()
            if row is None:
                conn.execute("INSERT INTO sw_total VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0)",
                             (sid, p["port"], *cur, *cur, t, t))
                continue
            tot, last, resets = list(row[0:4]), list(row[4:8]), row[8] or 0
            dropped = False
            for i, v in enumerate(cur):
                if v is None:
                    continue
                if last[i] is None or tot[i] is None:
                    tot[i] = v
                elif v >= last[i]:
                    tot[i] += v - last[i]
                else:
                    tot[i] += v
                    dropped = True
                last[i] = v
            conn.execute("UPDATE sw_total SET rxb=?,txb=?,rxp=?,txp=?,lrxb=?,ltxb=?,lrxp=?,ltxp=?,updated=?,resets=? WHERE sw=? AND port=?",
                         (*tot, *last, t, resets + (1 if dropped else 0), sid, p["port"]))

    def totals(self):
        """Totales acumulados de todos los switches para la pestaña «Historial». / Cumulative totals for the "History" tab."""
        out = []
        with self.db_lock:
            conn = self._db()
            try:
                rows = conn.execute("SELECT sw,port,rxb,txb,rxp,txp,since,updated,resets FROM sw_total ORDER BY sw,port").fetchall()
            finally:
                conn.close()
        by = {}
        for sid, port, rxb, txb, rxp, txp, since, upd, resets in rows:
            by.setdefault(sid, []).append({"port": port, "rx_bytes": rxb, "tx_bytes": txb, "rx_pkts": rxp, "tx_pkts": txp,
                                           "since": since, "updated": upd, "resets": resets or 0})
        with self.lock:
            cfgs = [dict(c) for c in self.cfg["switches"]]
        for c in cfgs:
            ports = by.get(c["id"], [])
            for p in ports:
                p["label"] = str((c.get("ports") or {}).get(str(p["port"]), {}).get("label") or "")
            out.append({"id": c["id"], "name": c["name"], "driver": c["driver"],
                        "has_bytes": any(p["rx_bytes"] is not None for p in ports), "ports": ports,
                        "since": min((p["since"] for p in ports if p["since"]), default=None),
                        "resets": sum(p["resets"] for p in ports)})
        return {"switches": out, "now": int(time.time())}

    def _db_write(self, sid, ts, snap, rates):
        """Una fila por switch y una por puerto con enlace (o que acaba de caer). / One row per switch and one per linked port."""
        try:
            with self.db_lock:
                conn = self._db()
                try:
                    t = int(ts)
                    if not snap:
                        conn.execute("INSERT OR REPLACE INTO sw_sys VALUES (?,?,?,?,?,?)", (t, sid, 0, None, None, None))
                    else:
                        ports = snap["ports"]
                        conn.execute("INSERT OR REPLACE INTO sw_sys VALUES (?,?,?,?,?,?)",
                                     (t, sid, 1, snap["system"].get("temperature_c"), snap.get("scrape_seconds"),
                                      sum(1 for p in ports if p["link_up"])))
                        for p in ports:
                            r = rates.get(p["port"]) or {}
                            if not p["link_up"] and not any(v for v in r.values() if v):
                                continue
                            conn.execute("INSERT OR REPLACE INTO sw_port VALUES (?,?,?,?,?,?,?,?,?,?)",
                                         (t, sid, p["port"], int(p["link_up"]), p["speed_mbps"], r.get("rx_pps"), r.get("tx_pps"),
                                          r.get("rx_bps"), r.get("tx_bps"), (p.get("rx_bad_pkts") or 0) + (p.get("tx_bad_pkts") or 0)))
                        self._totals_update(conn, sid, t, ports)
                    conn.commit()
                finally:
                    conn.close()
        except Exception as e:  # noqa: BLE001
            self._say("warning", f"history write: {e}")

    def _maintenance(self):
        time.sleep(60)
        while not self._stopped:
            try:
                self.rollup()
            except Exception as e:  # noqa: BLE001
                self._say("warning", f"history maintenance: {e}")
            time.sleep(3600)

    def rollup(self, now=None):
        """Resume en bloques de 15 min lo que pasó de 48 h y borra lo de más de 1 año. / Sum up (15-min blocks) what is older than 48 h; drop what is older than 1 year."""
        now = int(now or time.time())
        cutoff = (now - RAW_KEEP) // AGG_STEP * AGG_STEP
        with self.db_lock:
            conn = self._db()
            try:
                st = int(AGG_STEP)          # constante, no viene de la red / a constant, not from the network
                conn.execute(f"""INSERT OR REPLACE INTO sw_sys_agg
                    SELECT (ts/{st})*{st}, sw, AVG(up), AVG(temp), AVG(scrape), AVG(ports_up) FROM sw_sys WHERE ts<? GROUP BY ts/{st}, sw""", (cutoff,))
                conn.execute(f"""INSERT OR REPLACE INTO sw_port_agg
                    SELECT (ts/{st})*{st}, sw, port, MAX(link), MAX(speed), AVG(rxp), AVG(txp), AVG(rxb), AVG(txb), MAX(err)
                    FROM sw_port WHERE ts<? GROUP BY ts/{st}, sw, port""", (cutoff,))
                conn.execute("DELETE FROM sw_sys WHERE ts<?", (cutoff,))
                conn.execute("DELETE FROM sw_port WHERE ts<?", (cutoff,))
                conn.execute("DELETE FROM sw_sys_agg WHERE ts<?", (now - KEEP,))
                conn.execute("DELETE FROM sw_port_agg WHERE ts<?", (now - KEEP,))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            finally:
                conn.close()

    @staticmethod
    def _reduce(rows, fields, limit):
        """Reduce a ~limit puntos promediando intervalos iguales (el último punto conserva su hora real).
        EN: Reduce to ~limit points by averaging equal intervals (the last point keeps its real time)."""
        if len(rows) <= limit:
            return rows
        lo, hi = rows[0]["ts"], rows[-1]["ts"]
        step = max(1, -(-(hi - lo) // max(1, limit - 1)))
        out, cur, key = [], None, None
        def flush():
            if cur:
                o = {"ts": cur["ts"]}
                for f in fields:
                    vals = [v for v in cur[f] if v is not None]
                    o[f] = sum(vals) / len(vals) if vals else None
                out.append(o)
        for r in rows:
            k = (r["ts"] - lo) // step
            if k != key:
                flush()
                cur, key = {"ts": r["ts"], **{f: [] for f in fields}}, k
            cur["ts"] = r["ts"]
            for f in fields:
                cur[f].append(r.get(f))
        flush()
        return out

    def history(self, sid, rng="1d", port=None, now=None):
        now = int(now or time.time())
        since = now - RANGE_SECS[rng] if rng in RANGE_SECS else 0
        limit = RANGE_LIMIT.get(rng, 4320)
        edge = (now - RAW_KEEP) // AGG_STEP * AGG_STEP
        sys_f, port_f = ("up", "temp", "scrape", "ports_up"), ("link", "speed", "rxp", "txp", "rxb", "txb", "err")
        with self.db_lock:
            conn = self._db()
            try:
                def q(table, cols, extra, args, lo, hi):
                    sql = f"SELECT ts, {', '.join(cols)} FROM {table} WHERE sw=? {extra} AND ts>=?" + (" AND ts<?" if hi else "") + " ORDER BY ts"
                    return [dict(r) for r in conn.execute(sql, (*args, lo, *((hi,) if hi else ())))]
                sysr = q("sw_sys_agg", sys_f, "", (sid,), since, edge) + q("sw_sys", sys_f, "", (sid,), since, 0)
                portr = (q("sw_port_agg", port_f, "AND port=?", (sid, int(port)), since, edge) +
                         q("sw_port", port_f, "AND port=?", (sid, int(port)), since, 0)) if port is not None else []
            finally:
                conn.close()
        return {"range": rng, "sys": self._reduce(sysr, sys_f, limit), "port": self._reduce(portr, port_f, limit)}


# =========================================================================== Diagnóstico / Diagnostics
def _cli(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Lee una vez los switches de un switches.json y muestra los snapshots (solo lectura). "
                                             "Contraseñas: pass_env / pass_file; SNMP: community_env.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--no-macs", action="store_true")
    a = ap.parse_args(argv)
    res = {}
    data = json.load(open(a.config))
    # Acepta el formato de LabTower ({"switches":[…]}) y una lista simple. / EN: Accepts LabTower's format ({"switches":[…]}) and a plain list.
    for s in (data.get("switches", []) if isinstance(data, dict) else data):
        pw = os.environ.get(s.get("pass_env", ""), "") or (open(s["pass_file"]).read().strip() if s.get("pass_file") else "")
        cfg = {"name": s["name"], "driver": s["driver"], "host": s["host"], "user": s.get("user", "admin"), "password": pw,
               "community": os.environ.get(s.get("community_env", ""), "") or s.get("community", ""), "port": s.get("port", 161),
               "mac_paginate": s.get("mac_paginate", False)}
        try:
            res[s["name"]] = {"error": None, "data": build_driver(cfg).snapshot(with_macs=not a.no_macs)}
        except Exception as e:  # noqa: BLE001
            res[s["name"]] = {"error": f"{type(e).__name__}: {e}", "data": None}
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    _cli(sys.argv[1:])
