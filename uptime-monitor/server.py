#!/usr/bin/env python3
"""
Uptime Monitor — disponibilidad de servicios por HTTP(S), TCP y DNS / service availability over HTTP(S), TCP and DNS
"""
# Uptime Monitor (puerto 8090): revisa cada servicio de la lista cada cierto intervalo y guarda el resultado. Es solo lectura hacia los equipos.
#
# Tipos de monitor:
#   http  GET a una URL http:// o https://. Arriba si el código de respuesta está en la lista esperada (200-399 por defecto) y, si se pide,
#         la página contiene una palabra (sin distinguir mayúsculas). No se siguen redirecciones. En https se lee la fecha de vencimiento del
#         certificado; «no verificar» acepta un certificado autofirmado pero igual avisa su vencimiento.
#   tcp   abre una conexión al puerto (SSH, SMB, MQTT, una base de datos…).
#   dns   resuelve un nombre (A o AAAA) con el resolvedor del sistema o con un servidor dado; opcionalmente exige una IP.
#
# Fallos seguidos: un monitor pasa a «caído» después de N fallos seguidos (3 por defecto); mientras tanto queda «pendiente» (cuenta como arriba).
# Historial (metrics.db del módulo): cada revisión 2 días (barra, gráficos de 1 hora y 1 día) y un resumen por hora 365 días (disponibilidad
# 7 y 30 días y gráficos de 1 semana, 1 mes y todo). Los gráficos son los de charts.js, con los mismos rangos y la comparación con el periodo anterior.
# Eventos para el Resumen: caído, recuperado, certificado por vencer o vencido. state.json guarda el último estado para no repetirlos al reiniciar.
# Seguridad: solo un administrador del módulo crea monitores. HTTP no puede apuntar a esta máquina ni a direcciones de enlace local (se comprueba
# al guardar y otra vez al conectar, con la IP ya resuelta); TCP y DNS sí pueden mirar la propia máquina, como el ping de Net Monitor.
# EN: Uptime Monitor (port 8090): checks every service in the list at its interval and stores the result. It only reads from the targets.
#     Types: http (GET; up when the status code is in the expected list, 200-399 by default, and the page contains the keyword if one is set,
#     case-insensitive; redirects are not followed; https reads the certificate expiry, and "do not verify" accepts a self-signed certificate
#     but still warns about its expiry), tcp (opens a connection to the port), dns (resolves A or AAAA with the system resolver or a given
#     server; optionally requires an IP). Down after N failures in a row (3 by default); meanwhile "pending" (counted as up).
#     History (module metrics.db): every check for 2 days (bar, 1 hour and 1 day charts) and an hourly summary for 365 days (7 and 30 day
#     uptime, 1 week, 1 month and all charts). Charts use charts.js, with the same ranges and the previous-period comparison.
#     Overview events: down, recovered, certificate expiring or expired; state.json keeps the last state so a restart does not repeat them.
#     Security: only a module administrator creates monitors. HTTP cannot target this machine or link-local addresses (checked on save and
#     again on connect, with the resolved IP); TCP and DNS may look at the own machine, like Net Monitor's ping.
# permite «X | None» en Python 3.9 / allows «X | None» on Python 3.9
from __future__ import annotations

import http.client
import ipaddress
import json
import logging
import queue
import random
import re
import secrets
import socket
import sqlite3
import ssl
import struct
import sys
import threading
import time
import uuid
from collections import deque as _deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlsplit

ThreadingHTTPServer.request_queue_size = 128

sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import certinfo

import auth

HOST        = "127.0.0.1"
PORT        = 8090
STATIC_DIR  = Path(__file__).parent / "static"
DATA_DIR    = auth.module_dir("uptime-monitor")
DATA_FILE   = DATA_DIR / "uptime.json"
STATE_FILE  = DATA_DIR / "state.json"
TYPES       = ("http", "tcp", "dns")
MAX_MON     = 100
BAR_BEATS   = 50                 # revisiones en la barra / checks in the bar
BEATS_KEEP  = 2 * 86400          # s: cada revisión / every check
HOURLY_KEEP = auth.keep_days("UPTIME_KEEP_DAYS", 365) * 86400   # s: resumen por hora, como DNS Monitor / hourly summary, like DNS Monitor
# Rango del gráfico → (duración, tamaño de cada punto en s, tabla); «all» no tiene duración ni periodo anterior. Máximo ~600 puntos, como los demás.
# EN: Chart range → (span, bucket size in s, table); "all" has no span and no previous period. At most ~600 points, like the others.
RANGES      = {"1h": (3600, 1, "beats"), "1d": (86400, 300, "beats"), "1w": (7 * 86400, 3600, "hourly"),
               "1mo": (30 * 86400, 2 * 3600, "hourly"), "all": (None, 86400, "hourly")}
MAX_BODY    = 512 * 1024         # bytes leídos para buscar la palabra / bytes read to look for the keyword
UA          = "LabTower-Uptime"
FLUSH_EVERY = 5.0                # s: escritura de revisiones en lote / batched writes of checks
STATS_TTL   = 30.0               # s: caché de los porcentajes / cache of the percentages

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("uptime")

_cfg_lock = threading.RLock()
_state_lock = threading.RLock()
UP, DOWN, PENDING = 1, 0, 2      # valor guardado por revisión / value stored per check
# En Python 3.9 socket.timeout todavía no es TimeoutError: se captura con este nombre. / EN: on Python 3.9 socket.timeout is not TimeoutError yet.
SOCK_TIMEOUT = socket.timeout
DB_ERRORS = (sqlite3.Error, OSError)

# ─── Configuración / Configuration ──────────────────────────────────────────────
def load_monitors() -> list:
    return auth.read_json(DATA_FILE, [], list)

def save_monitors(items: list):
    with _cfg_lock:
        auth.write_json(DATA_FILE, items)

_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_EXPECT = re.compile(r"\d{3}(-\d{3})?(,\d{3}(-\d{3})?)*")

def _int(body, cfg, key, default, lo, hi, what):
    try: v = int(body.get(key, cfg.get(key, default)))
    except (TypeError, ValueError): raise ValueError(f"Invalid {what}")
    if not lo <= v <= hi: raise ValueError(f"{what[0].upper() + what[1:]} must be {lo}-{hi}")
    return v

def parse_expect(s: str) -> list:
    """'200-299,301' → [(200, 299), (301, 301)]. Raises ValueError."""
    s = re.sub(r"\s+", "", str(s or ""))
    if not s or len(s) > 60 or not _EXPECT.fullmatch(s): raise ValueError("Invalid expected status codes (example: 200-399)")
    out = []
    for part in s.split(","):
        a, _, b = part.partition("-")
        lo, hi = int(a), int(b or a)
        if not 100 <= lo <= hi <= 599: raise ValueError("Invalid expected status codes (example: 200-399)")
        out.append((lo, hi))
    return out

def validate(body: dict, current: dict | None = None) -> dict:
    """Checked copy of a monitor from the browser. `current` is the stored one when editing."""
    cfg = dict(current or {})
    typ = str(body.get("type", cfg.get("type", "")) or "")
    if typ not in TYPES: raise ValueError("Invalid monitor type")
    cfg["type"] = typ
    name = str(body.get("name", cfg.get("name", "")) or "").strip()
    if not name or len(name) > 60 or _CTRL.search(name): raise ValueError("Invalid name")
    cfg["name"] = name
    cfg["interval"] = _int(body, cfg, "interval", 60, 20, 3600, "interval")
    cfg["timeout"] = _int(body, cfg, "timeout", 10, 2, 30, "timeout")
    if cfg["timeout"] >= cfg["interval"]: raise ValueError("The timeout must be shorter than the interval")
    cfg["down_after"] = _int(body, cfg, "down_after", 3, 1, 6, "failures before down")
    cfg.pop("retries", None)
    for k in ("url", "expect", "keyword", "insecure", "cert_days", "host", "port", "qname", "rtype", "server", "expect_ip"): cfg.pop(k, None)
    if typ == "http":
        url = str(body.get("url", (current or {}).get("url", "")) or "").strip()
        if not url or len(url) > 2000 or _CTRL.search(url) or " " in url: raise ValueError("Invalid URL")
        try: u = urlsplit(url); port = u.port
        except ValueError: raise ValueError("Invalid URL")
        if u.scheme not in ("http", "https") or not u.hostname: raise ValueError("The URL must start with http:// or https://")
        if u.username is not None or u.password is not None: raise ValueError("Credentials are not allowed in the URL")
        if port is not None and not 1 <= port <= 65535: raise ValueError("Invalid port")
        if not auth.valid_target(u.hostname): raise ValueError("Invalid host (this machine and link-local addresses are not allowed)")
        cfg["url"] = url
        ex = str(body.get("expect", (current or {}).get("expect", "200-399")) or "200-399")
        parse_expect(ex); cfg["expect"] = re.sub(r"\s+", "", ex)
        kw = str(body.get("keyword", (current or {}).get("keyword", "")) or "").strip()
        if len(kw) > 100 or _CTRL.search(kw): raise ValueError("Invalid keyword")
        cfg["keyword"] = kw
        if u.scheme == "https":
            cfg["insecure"] = bool(body.get("insecure", (current or {}).get("insecure", False)))
            cfg["cert_days"] = _int(body, current or {}, "cert_days", 14, 1, 90, "certificate warning days")
    elif typ == "tcp":
        host = str(body.get("host", (current or {}).get("host", "")) or "").strip()
        if not host or host.startswith("-") or not auth.valid_target(host, allow_loopback=True): raise ValueError("Invalid host")
        cfg["host"] = host
        cfg["port"] = _int(body, current or {}, "port", 0, 1, 65535, "port")
    else:
        qn = str(body.get("qname", (current or {}).get("qname", "")) or "").strip().rstrip(".").lower()
        if not qn or not auth.valid_host(qn) or ":" in qn: raise ValueError("Invalid name to resolve")
        cfg["qname"] = qn
        rt = str(body.get("rtype", (current or {}).get("rtype", "A")) or "A").upper()
        if rt not in ("A", "AAAA"): raise ValueError("Invalid record type")
        cfg["rtype"] = rt
        srv = str(body.get("server", (current or {}).get("server", "")) or "").strip()
        if srv and (srv.startswith("-") or not auth.valid_target(srv, allow_loopback=True)): raise ValueError("Invalid DNS server")
        cfg["server"] = srv
        ip = str(body.get("expect_ip", (current or {}).get("expect_ip", "")) or "").strip()
        if ip:
            try: ip = str(ipaddress.ip_address(ip))
            except ValueError: raise ValueError("Invalid expected IP")
        cfg["expect_ip"] = ip
    return cfg

def reorder(items: list, order: list) -> list:
    """Monitors in the given id order; unknown ids are ignored and monitors not listed keep their order at the end."""
    pos = {mid: i for i, mid in enumerate(dict.fromkeys(order))}
    return sorted(items, key=lambda m: pos.get(m.get("id"), len(pos)))        # sorted() is stable

def target_of(m: dict) -> str:
    """Short description of what a monitor checks."""
    if m["type"] == "http": return m.get("url", "")
    if m["type"] == "tcp":
        h = m.get("host", "")
        return f"[{h}]:{m.get('port')}" if ":" in h else f"{h}:{m.get('port')}"
    return f"{m.get('qname')} {m.get('rtype')}" + (f" @{m['server']}" if m.get("server") else "")

# ─── Certificados / Certificates ────────────────────────────────────────────────
# El DER se lee con auth/certinfo.py (compartido con NAS Monitor). / The DER is read by auth/certinfo.py (shared with NAS Monitor).
cert_not_after = certinfo.not_after

# ─── Revisiones / Checks ────────────────────────────────────────────────────────
class CheckError(Exception):
    pass

def _connect_addr(host: str, port: int, allow_loopback: bool, kind=socket.SOCK_STREAM):
    """Resolve once and return the first address that is allowed (the same check as on save, now on the IP actually used)."""
    try: infos = socket.getaddrinfo(host, port, type=kind)
    except OSError as e: raise CheckError(f"cannot resolve {host}: {e.strerror or e}")
    for fam, _, _, _, sa in infos:
        if auth.valid_target(sa[0].split("%")[0], allow_loopback=allow_loopback): return fam, sa
    raise CheckError("address not allowed")

def _code_ok(code: int, expect: str) -> bool:
    try: return any(lo <= code <= hi for lo, hi in parse_expect(expect))
    except ValueError: return 200 <= code <= 399

def check_http(m: dict) -> dict:
    u = urlsplit(m["url"]); host = u.hostname; https = u.scheme == "https"
    port = u.port or (443 if https else 80); to = m.get("timeout", 10)
    path = (u.path or "/") + ("?" + u.query if u.query else "")
    fam, sa = _connect_addr(host, port, allow_loopback=False)
    t0 = time.monotonic(); exp = None
    sock = socket.socket(fam, socket.SOCK_STREAM); sock.settimeout(to)
    try:
        sock.connect(sa)
        if https:
            ctx = ssl.create_default_context()
            if m.get("insecure"): ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE  # nosec B501 - optional, chosen per monitor by its administrator
            try: sock = ctx.wrap_socket(sock, server_hostname=host)
            except ssl.SSLCertVerificationError as e: raise CheckError("certificate: " + str(e.verify_message or e)[:120])
            exp = cert_not_after(sock.getpeercert(True) or b"")
        conn = http.client.HTTPConnection(host, port, timeout=to)
        conn.sock = sock                                              # already connected (and wrapped) to the checked address
        hh = f"[{host}]" if ":" in host else host
        if u.port: hh += f":{u.port}"
        conn.request("GET", path, headers={"Host": hh, "User-Agent": UA, "Accept": "*/*", "Connection": "close"})
        r = conn.getresponse()
        body = r.read(MAX_BODY) if m.get("keyword") else b""
        ms = (time.monotonic() - t0) * 1000
        if not _code_ok(r.status, m.get("expect") or "200-399"): raise CheckError(f"HTTP {r.status}")
        if m.get("keyword") and m["keyword"].lower() not in body.decode("utf-8", "replace").lower(): raise CheckError("keyword not found")
        return {"ms": ms, "code": r.status, "cert_exp": exp}
    except CheckError as e:
        e.cert_exp = exp; raise
    except SOCK_TIMEOUT: raise CheckError("timed out")
    except ssl.SSLError as e: raise CheckError("TLS: " + str(e.reason or e)[:120])
    except (OSError, http.client.HTTPException) as e: raise CheckError(str(getattr(e, "strerror", None) or e)[:120] or type(e).__name__)
    finally:
        try: sock.close()
        except OSError: pass

def check_tcp(m: dict) -> dict:
    fam, sa = _connect_addr(m["host"], m["port"], allow_loopback=True)
    t0 = time.monotonic()
    s = socket.socket(fam, socket.SOCK_STREAM); s.settimeout(m.get("timeout", 10))
    try: s.connect(sa)
    except SOCK_TIMEOUT: raise CheckError("timed out")
    except OSError as e: raise CheckError(str(e.strerror or e)[:120])
    finally: s.close()
    return {"ms": (time.monotonic() - t0) * 1000}

QTYPE = {"A": 1, "AAAA": 28}

def dns_query_packet(qname: str, rtype: str, qid: int) -> bytes:
    q = b"".join(bytes([len(p)]) + p.encode("ascii") for p in qname.split(".") if p) + b"\0"
    return struct.pack(">HHHHHH", qid, 0x0100, 1, 0, 0, 0) + q + struct.pack(">HH", QTYPE[rtype], 1)

def _skip_name(b: bytes, i: int) -> int:
    for _ in range(128):
        n = b[i]
        if n == 0: return i + 1
        if n & 0xC0 == 0xC0: return i + 2
        i += n + 1
    raise ValueError("name too long")

def dns_parse(b: bytes, qid: int, rtype: str) -> list:
    """Addresses of the requested type in a DNS answer. Raises CheckError on an error reply."""
    try:
        rid, flags, qd, an, _, _ = struct.unpack(">HHHHHH", b[:12])
        if rid != qid or not flags & 0x8000: raise CheckError("unexpected DNS reply")
        rc = flags & 0xF
        if rc: raise CheckError({2: "SERVFAIL", 3: "NXDOMAIN (name not found)", 5: "REFUSED"}.get(rc, f"DNS error {rc}"))
        i = 12
        for _ in range(qd): i = _skip_name(b, i) + 4
        out, want = [], QTYPE[rtype]
        for _ in range(an):
            i = _skip_name(b, i)
            t, _c, _ttl, n = struct.unpack(">HHIH", b[i:i + 10]); i += 10
            rd = b[i:i + n]; i += n
            if len(rd) != n: raise ValueError("truncated")
            if t == want and len(rd) == (4 if want == 1 else 16): out.append(str(ipaddress.ip_address(rd)))
        return out
    except (struct.error, IndexError, ValueError): raise CheckError("malformed DNS reply")

def check_dns(m: dict) -> dict:
    to = m.get("timeout", 10); rt = m.get("rtype", "A"); t0 = time.monotonic()
    if not m.get("server"):
        try: infos = socket.getaddrinfo(m["qname"], None, socket.AF_INET if rt == "A" else socket.AF_INET6, socket.SOCK_STREAM)
        except OSError as e: raise CheckError(f"cannot resolve: {e.strerror or e}")
        ips = sorted({i[4][0] for i in infos})
    else:
        fam, sa = _connect_addr(m["server"], 53, allow_loopback=True, kind=socket.SOCK_DGRAM)
        qid = secrets.randbits(16)
        s = socket.socket(fam, socket.SOCK_DGRAM); s.settimeout(to)
        try:
            s.connect(sa); s.send(dns_query_packet(m["qname"], rt, qid))
            end = time.monotonic() + to
            while True:                                               # ignore stray datagrams with another id
                b = s.recv(4096)
                try: ips = dns_parse(b, qid, rt); break
                except CheckError as e:
                    if str(e) != "unexpected DNS reply" or time.monotonic() > end: raise
        except SOCK_TIMEOUT: raise CheckError("timed out")
        except OSError as e: raise CheckError(str(e.strerror or e)[:120])
        finally: s.close()
    ms = (time.monotonic() - t0) * 1000
    if not ips: raise CheckError(f"no {rt} record")
    if m.get("expect_ip") and m["expect_ip"] not in ips: raise CheckError("resolved to " + ", ".join(ips[:3]))
    return {"ms": ms, "ips": ips[:8]}

CHECKS = {"http": check_http, "tcp": check_tcp, "dns": check_dns}

def run_check(m: dict) -> dict:
    """{'ok': bool, 'ms', 'error', 'cert_exp', …} for one check; never raises."""
    try: r = CHECKS[m["type"]](m); r["ok"] = True; r["error"] = None
    except CheckError as e: r = {"ok": False, "ms": None, "error": str(e), "cert_exp": getattr(e, "cert_exp", None)}
    except Exception as e:  # noqa: BLE001 - un error en una revisión no puede detener el monitor / a bug in a check must not stop the monitor
        log.warning(f"[{m.get('name')}] check failed: {e!r}"); r = {"ok": False, "ms": None, "error": "internal error"}
    if r.get("ms") is not None: r["ms"] = round(r["ms"], 1)
    return r

def cert_state(exp, days: int, now: float) -> str | None:
    if not exp: return None
    if exp <= now: return "expired"
    return "warn" if exp - now <= days * 86400 else "ok"

# ─── Historial (metrics.db) / History ───────────────────────────────────────────
_wq: queue.Queue = queue.Queue()
_stats_cache = {"ts": 0.0, "data": {}}
_stats_lock = threading.Lock()

def _db(sql, args=(), many=False, fetch=False):
    c = auth.metrics_conn()
    try:
        cur = c.executemany(sql, args) if many else c.execute(sql, args)
        rows = cur.fetchall() if fetch else None
        c.commit(); return rows
    finally: c.close()

def _flush():
    rows = []
    while True:
        try: rows.append(_wq.get_nowait())
        except queue.Empty: break
    if not rows: return
    hourly = [(mid, ts - ts % 3600, 1 if st == DOWN else 0, ms or 0.0, 1 if ms is not None else 0) for mid, ts, st, ms in rows]
    c = auth.metrics_conn()
    try:
        c.executemany("INSERT OR REPLACE INTO uptime_beats (mid,ts,st,ms) VALUES (?,?,?,?)", rows)
        c.executemany("INSERT INTO uptime_hourly (mid,hour,n,down,ms_sum,ms_n) VALUES (?,?,1,?,?,?) "
                      "ON CONFLICT(mid,hour) DO UPDATE SET n=n+1, down=down+excluded.down, ms_sum=ms_sum+excluded.ms_sum, ms_n=ms_n+excluded.ms_n", hourly)
        c.commit()
    finally: c.close()

def prune(now=None):
    now = int(now or time.time())
    _db("DELETE FROM uptime_beats WHERE ts < ?", (now - BEATS_KEEP,))
    _db("DELETE FROM uptime_hourly WHERE hour < ?", (now - HOURLY_KEEP,))

def _writer():
    n = 0
    while True:
        time.sleep(FLUSH_EVERY)
        try:
            _flush(); n += 1
            if n % int(3600 / FLUSH_EVERY) == 1: prune()
        except Exception as e: log.warning(f"history not saved: {e}")  # noqa: BLE001 - el hilo de escritura no puede morir / the writer thread must not die

def drop_history(mid: str):
    _db("DELETE FROM uptime_beats WHERE mid = ?", (mid,)); _db("DELETE FROM uptime_hourly WHERE mid = ?", (mid,))

def uptime_stats(now=None) -> dict:
    """{mid: {'24h': %, '7d': %, '30d': %, 'avg': ms 24 h}} — pending counts as up. Cached STATS_TTL seconds."""
    now = int(now or time.time())
    with _stats_lock:
        if time.time() - _stats_cache["ts"] < STATS_TTL: return _stats_cache["data"]
        try: _flush()
        except DB_ERRORS as e: log.warning(f"history not saved: {e}")
        out: dict = {}
        for mid, n, dn, ms_s, ms_n in _db("SELECT mid, COUNT(*), SUM(st=0), SUM(COALESCE(ms,0)), COUNT(ms) FROM uptime_beats WHERE ts >= ? GROUP BY mid", (now - 86400,), fetch=True):
            out.setdefault(mid, {})["24h"] = round(100 * (n - dn) / n, 2) if n else None
            out[mid]["avg"] = round(ms_s / ms_n, 1) if ms_n else None
        for key, secs in (("7d", 7 * 86400), ("30d", 30 * 86400)):
            for mid, n, dn in _db("SELECT mid, SUM(n), SUM(down) FROM uptime_hourly WHERE hour >= ? GROUP BY mid", (now - now % 3600 - secs + 3600,), fetch=True):
                out.setdefault(mid, {})[key] = round(100 * (n - dn) / n, 2) if n else None
        _stats_cache.update(ts=time.time(), data=out)
        return out

def history_window(range_: str, prev: bool = False, now=None):
    """(since, until) of a range; prev=True gives the period just before it, with the same length ("all" has none: None)."""
    span = RANGES[range_][0]; now = int(now or time.time())
    if not span: return None if prev else (0, now)
    return (now - 2 * span, now - span) if prev else (now - span, now)

# Puntos del gráfico: tiempo de respuesta promedio y disponibilidad de cada tramo; «up» = 0 si hubo alguna revisión caída (franja roja).
# EN: Chart points: average response time and uptime of each bucket; "up" = 0 when any check in it was down (red band).
def history(mid: str, range_: str, prev: bool = False, now=None) -> list:
    try: _flush()
    except DB_ERRORS as e: log.warning(f"history not saved: {e}")
    _, size, table = RANGES[range_]; win = history_window(range_, prev, now)
    if win is None: return []
    a, b = win
    if table == "beats":
        sql = ("SELECT ts - ts % ? AS t, COUNT(*), SUM(st = 0), SUM(COALESCE(ms, 0)), COUNT(ms) FROM uptime_beats "
               "WHERE mid = ? AND ts >= ? AND ts < ? GROUP BY t ORDER BY t")
    else:
        sql = ("SELECT hour - hour % ? AS t, SUM(n), SUM(down), SUM(ms_sum), SUM(ms_n) FROM uptime_hourly "
               "WHERE mid = ? AND hour >= ? AND hour < ? GROUP BY t ORDER BY t")
    out = []
    for t, n, dn, ms_s, ms_n in _db(sql, (size, mid, a - a % size, b), fetch=True):
        out.append({"ts": int(t), "ms": round(ms_s / ms_n, 1) if ms_n else None, "pct": round(100 * (n - dn) / n, 2) if n else None, "up": 0 if dn else 1})
    return out

# ─── Estado persistente / Persistent state ──────────────────────────────────────
# state.json: {"<id>": {"st": "up"|"down", "since": ts, "cert": "ok"|"warn"|"expired"|None}}
_state: dict = {}

def load_state():
    global _state
    with _state_lock: _state = auth.read_json(STATE_FILE, {}, dict)

def save_state():
    with _state_lock:
        try: auth.write_json(STATE_FILE, _state)
        except OSError as e: log.warning(f"state not saved: {e}")

# ─── Monitores en ejecución / Running monitors ──────────────────────────────────
class Mon:
    def __init__(self, mid):
        self.id, self.lock, self.wake = mid, threading.RLock(), threading.Event()
        self.beats = _deque(maxlen=BAR_BEATS)                           # [ts, st, ms]
        self.fails, self.status, self.last, self.cert_exp = 0, None, None, None
    def snap(self):
        with self.lock:
            st = _state.get(self.id) or {}
            return {"status": self.status or ({1: "up", 0: "down"}.get(self.beats[-1][1]) if self.beats else None) or st.get("st"),
                    "since": st.get("since"), "last": dict(self.last) if self.last else None, "fails": self.fails,
                    "cert_exp": self.cert_exp, "beats": list(self.beats)}

_mons: dict = {}
_threads: dict = {}
_glock = threading.Lock()

def apply_result(m: dict, mon: Mon, r: dict, now: float):
    """Update a monitor with one check: status after N failures in a row, beat, state.json and events."""
    name = m["name"]
    with mon.lock:
        mon.fails = 0 if r["ok"] else mon.fails + 1
        st = UP if r["ok"] else DOWN if mon.fails >= m.get("down_after", 3) else PENDING
        if st != PENDING: mon.status = "up" if st == UP else "down"
        elif mon.status is None: mon.status = "pending"
        mon.last = {"ts": int(now), "ok": r["ok"], "ms": r.get("ms"), "error": r.get("error"), "code": r.get("code")}
        if r.get("cert_exp"): mon.cert_exp = r["cert_exp"]
        mon.beats.append([int(now), st, r.get("ms")])
    _wq.put((m["id"], int(now), st, r.get("ms")))
    changed = False
    with _state_lock:
        s = _state.setdefault(m["id"], {})
        if st != PENDING:
            new = "up" if st == UP else "down"
            if s.get("st") != new:
                if s.get("st") == "down" and new == "up":
                    auth.record_event("uptime", "info", f"{name}: up again", "uptime_up", n=name)
                elif new == "down":
                    auth.record_event("uptime", "crit", f"{name}: down ({r.get('error') or '?'})", "uptime_down", n=name, e=str(r.get("error") or "?")[:80])
                s["st"], s["since"] = new, int(now); changed = True
        if m["type"] == "http" and m["url"].startswith("https://") and r.get("cert_exp"):
            cs = cert_state(r["cert_exp"], m.get("cert_days", 14), now)
            if cs != s.get("cert"):
                d = max(0, int((r["cert_exp"] - now) // 86400))
                if cs == "warn": auth.record_event("uptime", "warn", f"{name}: certificate expires in {d} days", "uptime_cert", n=name, d=d)
                elif cs == "expired": auth.record_event("uptime", "crit", f"{name}: certificate expired", "uptime_certexp", n=name)
                s["cert"] = cs; changed = True
    if changed: save_state()

def _loop(mid: str):
    mon = _mons.get(mid)
    if not mon: return
    mon.wake.wait(random.uniform(0.5, 5.0))                           # spread the first checks  # nosec B311 - not security related
    mon.wake.clear()
    while True:
        with _glock:
            if _mons.get(mid) is not mon: return                    # deleted
        m = next((x for x in load_monitors() if x.get("id") == mid), None)
        if m is None: return
        t0 = time.time()
        r = run_check(m)
        with _glock:
            if _mons.get(mid) is not mon: return
        apply_result(m, mon, r, t0)
        mon.wake.wait(max(1.0, m["interval"] - (time.time() - t0)))
        mon.wake.clear()

def _preload(mon: Mon, now: float):
    try: rows = _db("SELECT ts, st, ms FROM uptime_beats WHERE mid = ? AND ts >= ? ORDER BY ts DESC LIMIT ?", (mon.id, int(now) - BEATS_KEEP, BAR_BEATS), fetch=True)
    except DB_ERRORS as e: log.warning(f"history not read: {e}"); rows = []
    for r in reversed(rows): mon.beats.append(list(r))

def ensure_monitor(m: dict):
    mid = m["id"]
    with _glock:
        if mid not in _mons:
            _mons[mid] = Mon(mid); _preload(_mons[mid], time.time())
        if mid not in _threads or not _threads[mid].is_alive():
            t = threading.Thread(target=_loop, args=(mid,), daemon=True, name=f"up-{mid[:8]}")
            _threads[mid] = t; t.start()

def remove_monitor(mid: str):
    with _glock:
        mon = _mons.pop(mid, None); _threads.pop(mid, None)
    if mon: mon.wake.set()
    with _state_lock:
        if _state.pop(mid, None) is not None: save_state()
    try: drop_history(mid)
    except DB_ERRORS as e: log.warning(f"history not deleted: {e}")
    with _stats_lock: _stats_cache["ts"] = 0.0

def start_all():
    load_state()
    try: prune()
    except DB_ERRORS as e: log.warning(f"history not pruned: {e}")
    threading.Thread(target=_writer, daemon=True, name="up-writer").start()
    for m in load_monitors(): ensure_monitor(m)

def public(m: dict, mon: Mon | None, stats: dict, with_beats=True) -> dict:
    sn = mon.snap() if mon else {"status": None, "since": None, "last": None, "fails": 0, "cert_exp": None, "beats": []}
    out = {**m, "target": target_of(m), **{k: v for k, v in sn.items() if k != "beats"}, "uptime": stats.get(m["id"], {})}
    if with_beats: out["beats"] = sn["beats"]
    out["cert"] = cert_state(sn["cert_exp"], m.get("cert_days", 14), time.time()) if m["type"] == "http" and m.get("url", "").startswith("https://") else None
    return out

def health_report(detailed=False):
    c = auth.check_common()
    c["uptime_file"] = auth.check_file(DATA_FILE)
    items = load_monitors(); dead = [m["name"] for m in items if not (_threads.get(m["id"]) and _threads[m["id"]].is_alive())]
    down = [m["name"] for m in items if _mons.get(m["id"]) and _mons[m["id"]].snap()["status"] == "down"]
    if not items: c["uptime_monitors"] = auth.chk(auth.OK, "no monitors configured")
    elif dead:    c["uptime_monitors"] = auth.chk(auth.FAIL, "monitor stopped: " + ", ".join(dead[:10]))
    else:         c["uptime_monitors"] = auth.chk(auth.OK, f"{len(items)} running")
    c["uptime_services"] = auth.chk(auth.WARN, "down: " + ", ".join(down[:10])) if down else auth.chk(auth.OK, "every service is up")
    return auth.health_reply("uptime", c, detailed)

# ─── HTTP ───────────────────────────────────────────────────────────────────
_test_gate = threading.Semaphore(2)
_ID = r"([a-f0-9\-]{36})"

class H(BaseHTTPRequestHandler):
    timeout = 30
    def log_message(self, fmt, *a):
        # send_error() llega aquí con (código, mensaje) y un 501 de HEAD trae el mensaje en a[1]: solo se registra un código numérico.
        # EN: send_error() arrives here with (code, message) and a HEAD 501 carries the message in a[1]: only a numeric code is logged.
        c = str(a[1]) if len(a) > 1 else ""
        if c.isdigit() and int(c) >= 400: log.warning(f"{self.client_address[0]} {c}")
    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(body)
    def _body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n < 0 or n > 16384: return None
            d = json.loads(self.rfile.read(n)) if n else {}
            return d if isinstance(d, dict) else None
        except (ValueError, TypeError, OSError, RecursionError): return None
    def _tok(self):
        return auth.token_from_request(dict(self.headers), self.headers.get("Cookie", ""))
    def _file(self, path, mime):
        try:
            c = Path(path).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime); self.send_header("Content-Length", str(len(c)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"); self.send_header("Pragma", "no-cache")
            self.end_headers(); self.wfile.write(c)
        except FileNotFoundError: self._json(404, {"error": "Not found"})

    # GET: página, versión y salud son públicos; el resto exige sesión con Uptime «readonly». Rutas: /api/monitors, /api/monitors/<id>/history?range=1h|1d|1w|1mo|all[&prev=1], /api/me.
    # EN: GET: page, version and health are public; the rest requires a session with Uptime "readonly". Routes: /api/monitors, /api/monitors/<id>/history?range=1h|1d|1w|1mo|all[&prev=1], /api/me.
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        tok  = self._tok()
        if auth.serve_asset(self, STATIC_DIR, path): return
        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if path == "/api/version":
            return self._json(200, {"version": auth.version()} if (auth.get_session(tok) or auth.is_local_request(self)) else {})
        if path == "/api/health":
            code, body = health_report(auth.health_mode(self, tok))
            return self._json(code, body)
        if path == "/api/me":
            sess = auth.get_session(tok)
            return self._json(200, {"username": sess["username"], "permissions": sess["permissions"],
                      "disabled": auth.disabled_modules()} if sess else {})
        if not auth.check_permission(tok, "uptime", "readonly"):
            return self._json(401, {"error": "Unauthorized"})
        if path == "/api/monitors":
            with_beats = parse_qs(urlparse(self.path).query).get("beats", ["1"])[0] != "0"
            try: stats = uptime_stats()
            except DB_ERRORS as e: log.warning(f"stats: {e}"); stats = {}
            out = []
            for m in load_monitors():
                if m["id"] not in _threads or not _threads[m["id"]].is_alive(): ensure_monitor(m)
                out.append(public(m, _mons.get(m["id"]), stats, with_beats))
            return self._json(200, {"monitors": out})
        mt = re.fullmatch(r"/api/monitors/" + _ID + r"/history", path)
        if mt:
            if not any(x.get("id") == mt.group(1) for x in load_monitors()): return self._json(404, {"error": "Not found"})
            q = parse_qs(urlparse(self.path).query); rng = q.get("range", ["1d"])[0]; prev = q.get("prev", ["0"])[0] == "1"
            if rng not in RANGES: return self._json(400, {"error": "Invalid range"})
            return self._json(200, {"range": rng, "prev": prev, "history": history(mt.group(1), rng, prev)})
        self._json(404, {"error": "Not found"})

    def do_POST(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})
        if path == "/api/login":
            r, err = auth.login_session(self, body.get("username", ""), body.get("password", ""), body.get("remember"), body.get("code"))
            if not r: return self._json(err[0], {"error": err[1]})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", auth.session_cookie(r["token"], r["ttl"]))
            br = json.dumps({"ok": True, "username": r["username"], "permissions": r["permissions"], "must_change_password": r["must_change_password"]}).encode()
            self.send_header("Content-Length", str(len(br)))
            self.end_headers(); self.wfile.write(br); return
        if path == "/api/logout":
            auth.delete_session(tok); return self._json(200, {"ok": True})

        # Revisar ahora: basta el nivel «ejecutar». / Check now: the "execute" level is enough.
        mc = re.fullmatch(r"/api/monitors/" + _ID + r"/check", path)
        if mc:
            if not auth.check_permission(tok, "uptime", "execute"):
                return self._json(403 if auth.check_permission(tok, "uptime", "readonly") else 401, {"error": "Execute permission required"})
            mon = _mons.get(mc.group(1))
            if not mon: return self._json(404, {"error": "Not found"})
            mon.wake.set(); return self._json(200, {"ok": True})

        if not auth.check_permission(tok, "uptime", "admin"):
            return self._json(403 if auth.check_permission(tok, "uptime", "readonly") else 401, {"error": "Admin permission required"})

        if path == "/api/monitors":
            try: cfg = validate(body)
            except ValueError as e: return self._json(400, {"error": str(e)})
            cfg["id"] = str(uuid.uuid4())
            with _cfg_lock:
                items = load_monitors()
                if len(items) >= MAX_MON: return self._json(400, {"error": f"At most {MAX_MON} monitors"})
                items.append(cfg); save_monitors(items)
            ensure_monitor(cfg)
            return self._json(201, {"monitor": public(cfg, _mons.get(cfg["id"]), {})})

        if path == "/api/test":
            cur = next((x for x in load_monitors() if x.get("id") == body.get("id")), None) if body.get("id") else None
            try: cfg = validate(body, cur)
            except ValueError as e: return self._json(400, {"error": str(e)})
            if not _test_gate.acquire(blocking=False): return self._json(429, {"error": "Too many tests at once"})
            try: r = run_check(cfg)
            finally: _test_gate.release()
            return self._json(200, {"ok": r["ok"], "ms": r.get("ms"), "error": r.get("error"), "code": r.get("code"), "ips": r.get("ips"),
                                    "cert_exp": r.get("cert_exp")})

        # Orden manual de los monitores (arrastrar y soltar): se guarda en uptime.json, así todos los navegadores ven el mismo.
        # Los ids que no vengan quedan al final, en su orden actual. / EN: Manual monitor order (drag and drop), stored in uptime.json
        # so every browser sees the same; ids not sent stay at the end, in their current order.
        if path == "/api/order":
            order = body.get("order")
            if not (isinstance(order, list) and len(order) <= MAX_MON and all(isinstance(x, str) and re.fullmatch(_ID, x) for x in order)):
                return self._json(400, {"error": "Invalid order"})
            with _cfg_lock:
                items = load_monitors()
                save_monitors(reorder(items, order))
            return self._json(200, {"ok": True})

        m = re.fullmatch(r"/api/monitors/" + _ID, path)
        if m:
            with _cfg_lock:
                items = load_monitors()
                cur = next((x for x in items if x.get("id") == m.group(1)), None)
                if not cur: return self._json(404, {"error": "Not found"})
                try: cfg = validate(body, cur)
                except ValueError as e: return self._json(400, {"error": str(e)})
                cfg["id"] = cur["id"]
                items[items.index(cur)] = cfg; save_monitors(items)
            mon = _mons.get(cfg["id"])
            if mon:
                with mon.lock: mon.fails = 0
                if (cur.get("type"), target_of(cur)) != (cfg["type"], target_of(cfg)):
                    with mon.lock: mon.cert_exp = None
                mon.wake.set()
            return self._json(200, {"monitor": public(cfg, mon, {})})
        self._json(404, {"error": "Not found"})

    def do_DELETE(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        tok = self._tok()
        if not auth.check_permission(tok, "uptime", "admin"):
            return self._json(403, {"error": "Admin permission required"})
        m = re.fullmatch(r"/api/monitors/" + _ID, urlparse(self.path).path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        with _cfg_lock:
            items = load_monitors()
            new = [x for x in items if x.get("id") != m.group(1)]
            if len(new) == len(items): return self._json(404, {"error": "Not found"})
            save_monitors(new)
        remove_monitor(m.group(1))
        self._json(200, {"ok": True})

if __name__ == "__main__":
    auth.prepare_module(DATA_DIR, Path(__file__).parent, ())
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if auth.ensure_permissions(("uptime",)): log.info("'uptime' permissions updated")
    except (OSError, ValueError, RuntimeError) as e:
        log.warning(f"Permissions: {e}")
    log.info(f"Uptime Monitor en http://{HOST}:{PORT}")
    start_all()
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
