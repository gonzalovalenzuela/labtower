#!/usr/bin/env python3
"""
DNS Monitor — estado de uno o varios Pi-hole (v6 y v5) o AdGuard Home / status of one or more Pi-hole (v6 and v5) or AdGuard Home servers
"""
# DNS Monitor (puerto 8087): muestra el estado de uno o varios servidores DNS con bloqueo de anuncios: consultas, bloqueadas, % bloqueado, dominios
# y clientes más activos, DNS de salida (upstreams), tiempo de respuesta y estado de la protección. Pi-hole v6 (API REST con sesión), Pi-hole v5
# (api.php con token) y AdGuard Home (API con usuario y clave). Lee por HTTP(S) con la biblioteca estándar; no instala nada en el servidor DNS.
# Los usuarios con nivel «execute» pueden pausar el bloqueo unos minutos y reanudarlo.
#
# Flujo de datos:
#   un hilo «poller» por servidor → collect() pide las rutas de la API → DnsCache guarda la última lectura → la página la pide a /api/dns.
#   El hilo consulta rápido (15 s) mientras alguien mira la página y lento (60 s) si nadie la tiene abierta.
#
# Seguridad: la clave (o el token) nunca se devuelve al navegador (solo «has_password»), el archivo dns.json es privado (0600), las redirecciones HTTP
# no se siguen (no se envían credenciales a otro sitio) y la dirección se reduce a esquema://host[:puerto].
#
# Estructura: validación · cliente HTTP · Pi-hole · AdGuard · lectura de un servidor · caché e historial · poller · salud · HTTP.
# EN: DNS Monitor (port 8087): shows the status of one or more ad-blocking DNS servers: queries, blocked, % blocked, top domains and clients,
#     upstreams, response time and protection state. Pi-hole v6 (REST API with a session), Pi-hole v5 (api.php with a token) and AdGuard Home
#     (API with user and password). It reads over HTTP(S) with the standard library; nothing is installed on the DNS server.
#     Users with the "execute" level can pause blocking for a few minutes and resume it.
#
#     Data flow:
#       one "poller" thread per server → collect() requests the API routes → DnsCache keeps the last reading → the page requests it from /api/dns.
#       The thread polls fast (15 s) while someone is looking at the page and slowly (60 s) if nobody has it open.
#
#     Security: the password (or token) is never returned to the browser (only "has_password"), dns.json is private (0600), HTTP redirects are not
#     followed (credentials never go to another site) and the address is reduced to scheme://host[:port].
#
#     Structure: validation · HTTP client · Pi-hole · AdGuard · reading one server · cache and history · poller · health · HTTP.
import base64
import http.client
import json
import logging
import math
import os
import re
import socket
import sqlite3
import ssl
import sys
import threading
import time
import uuid
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ThreadingHTTPServer.request_queue_size = 128
from collections import deque as _deque
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

# Módulo compartido de autenticación (carpeta hermana /auth).
# EN: Shared authentication module (sibling folder /auth).
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

sys.path.insert(0, str(Path(__file__).parent))
import dnsq

# Solo loopback; el acceso desde la red pasa por nginx.
# EN: Loopback only; network access goes through nginx.
HOST       = "127.0.0.1"
PORT       = 8087
STATIC_DIR = Path(__file__).parent / "static"
DATA_DIR   = auth.module_dir("dns-monitor")          # solo la ruta; la carpeta se crea al arrancar / EN: path only, created at startup
LEGACY_FILES = ()
DATA_FILE  = DATA_DIR / "dns.json"
POLL_ACTIVE = float(os.environ.get("DNS_POLL_ACTIVE", "15"))   # seconds, while someone is watching
POLL_IDLE   = float(os.environ.get("DNS_POLL_IDLE", "60"))     # seconds, when nobody has the page open
VIEW_GRACE  = 30
HIST_EVERY  = 60                                              # history sampling period (s)
_HIST_MAX   = 720                                             # ~12 h at 60 s
HIST_KEEP   = auth.keep_days("DNS_KEEP_DAYS", 30) * 86400
MAX_BODY    = 1 << 22                                         # largest API answer read (4 MB)
_last_view  = 0.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("dns")

TYPES    = ("pihole", "adguard")
FIELDS   = ("type", "url", "username", "password", "verify_tls", "timeout")
SECRETS  = ("password",)
DEFAULTS = {"type": "pihole", "url": "", "username": "", "password": "", "verify_tls": True, "timeout": 8}

class DnsError(RuntimeError):
    pass

# ─── Validación y configuración ───────────────────────────────────────────────
_dns_lock = threading.RLock()

def load_servers() -> list:
    return auth.read_json(DATA_FILE, [], list)

def save_servers(items: list):
    with _dns_lock:
        auth.write_json(DATA_FILE, items)            # holds passwords: 0600

# Reduce la dirección a esquema://host[:puerto]. Rechaza usuario en la URL, esquemas distintos de http/https y hosts raros.
# EN: Reduce the address to scheme://host[:port]. Rejects a user in the URL, schemes other than http/https and odd hosts.
def norm_url(u) -> str:
    u = str(u or "").strip()
    if "://" not in u: u = "http://" + u
    p = urlparse(u)
    if p.scheme not in ("http", "https"): raise ValueError("Address must start with http:// or https://")
    if p.username or p.password: raise ValueError("Do not put credentials in the address")
    try: port = p.port
    except ValueError: raise ValueError("Invalid port")
    h = p.hostname or ""
    if not auth.valid_target(h): raise ValueError("Invalid host (this machine and link-local addresses are not allowed)")
    if port is not None and not 1 <= port <= 65535: raise ValueError("Invalid port")
    host = f"[{h}]" if ":" in h else h
    return f"{p.scheme}://{host}" + (f":{port}" if port else "")

# Combina la petición con lo guardado y valida cada campo. Una clave vacía significa «conservar la actual».
# EN: Merge the request with what is stored and validate every field. An empty password means "keep the current one".
def validate(body: dict, current=None) -> dict:
    cfg = dict(DEFAULTS); cfg.update({k: v for k, v in (current or {}).items() if k in FIELDS or k in ("name", "id")})
    for k in ("name",) + FIELDS:
        if k not in body: continue
        v = body[k]
        if k in SECRETS and (v is None or v == ""): continue
        cfg[k] = v
    cfg["name"] = str(cfg.get("name") or "").strip()
    if not cfg["name"] or len(cfg["name"]) > 60 or re.search(r"[\x00-\x1f\x7f]", cfg["name"]): raise ValueError("Invalid name")
    if cfg["type"] not in TYPES: raise ValueError("Invalid server type")
    cfg["url"] = norm_url(cfg["url"])
    cfg["verify_tls"] = bool(cfg.get("verify_tls", True))
    # La huella fijada (tls_pin) la aprende el servidor y nunca se acepta del formulario. Guardar el servidor otra vez la borra (se vuelve a aprender en la
    # siguiente conexión): es la forma de aceptar un certificado nuevo a propósito.
    # EN: The pinned fingerprint (tls_pin) is learned by the server and never accepted from the form. Saving the server again clears it (it is learned again
    #     on the next connection): that is how a new certificate is accepted on purpose.
    cfg["tls_pin"] = ""
    try:    cfg["timeout"] = int(cfg["timeout"])
    except (TypeError, ValueError): raise ValueError("Invalid timeout")
    if not 1 <= cfg["timeout"] <= 30: raise ValueError("Timeout must be 1-30 seconds")
    for k in ("username", "password"):
        cfg[k] = str(cfg.get(k) or "")
        if re.search(r"[\x00-\x1f\x7f]", cfg[k]) or len(cfg[k]) > 256: raise ValueError(f"Invalid {k}")
    if cfg["type"] == "adguard" and not cfg["username"]: raise ValueError("AdGuard Home needs a username")
    # La pausa del monitoreo solo cambia por /pause: editar la conserva. / EN: The monitoring pause only changes through /pause: editing keeps it.
    if auth.paused(current): cfg["enabled"] = False
    return cfg

# Vista para el navegador: sin la clave, solo «has_password».
# EN: View for the browser: no password, only "has_password".
def public(n: dict) -> dict:
    out = {k: v for k, v in n.items() if k not in SECRETS}
    for k in SECRETS: out["has_" + k] = bool(n.get(k))
    return out

# ─── Cliente HTTP (biblioteca estándar, sin seguir redirecciones) ─────────────
# Con «verificar TLS» activo se valida contra las CA del sistema. Sin él NO se acepta cualquier certificado: se FIJA la huella SHA-256 la primera vez
# (TOFU, como Net Monitor y Proxmox) y, si luego cambia, la conexión se corta antes de enviar la contraseña.
# EN: With "verify TLS" on, the certificate is validated against the system CAs. Without it, ANY certificate is NOT accepted: the SHA-256 fingerprint
#     is PINNED the first time (TOFU, like Net Monitor and Proxmox) and, if it later changes, the connection is dropped before the password is sent.
def _ctx(cfg):
    if cfg["url"].startswith("https") and not cfg.get("verify_tls", True):
        c = ssl.create_default_context(); c.check_hostname = False; c.verify_mode = ssl.CERT_NONE; return c
    return ssl.create_default_context()

def _learn_pin(cfg, fp):
    cfg["tls_pin"] = fp
    sid = cfg.get("id")
    if not sid: return                                   # connection test of an unsaved server: kept in memory only
    with _dns_lock:
        items = load_servers()
        for x in items:
            if x.get("id") == sid and not x.get("tls_pin") and x.get("url") == cfg.get("url"):
                x["tls_pin"] = fp; save_servers(items)
                log.info(f"DNS server {x.get('name')!r}: certificate fingerprint pinned ({fp[:16]}…)")
                break

def _check_pin(cfg, conn):
    import hashlib
    fp = hashlib.sha256(conn.sock.getpeercert(True)).hexdigest()
    pin = cfg.get("tls_pin") or ""
    if not pin: _learn_pin(cfg, fp)
    elif pin != fp: raise DnsError("The server's certificate changed (pinned fingerprint mismatch); nothing was sent. Edit and save the server to learn it again")

# Una petición. Devuelve (código, JSON o None). Falla (DnsError) solo si no hay conexión; un 4xx/5xx se devuelve para que quien llama decida.
# EN: One request. Returns (code, JSON or None). It raises (DnsError) only when there is no connection; a 4xx/5xx is returned so the caller decides.
def _req(cfg, method, path, params=None, body=None, headers=None):
    p = urlparse(cfg["url"]); https = p.scheme == "https"
    host, port = p.hostname, p.port or (443 if https else 80)
    q = ("?" + urlencode(params)) if params else ""
    h = {"Accept": "application/json", "User-Agent": "LabTower-DNS", "Connection": "close"}; h.update(headers or {})
    data = None
    if body is not None: data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    try:
        conn = http.client.HTTPSConnection(host, port, timeout=cfg["timeout"], context=_ctx(cfg)) if https else http.client.HTTPConnection(host, port, timeout=cfg["timeout"])
        try:
            if https and not cfg.get("verify_tls", True):
                conn.connect(); _check_pin(cfg, conn)
            conn.request(method, path + q, data, h)
            r = conn.getresponse()
            raw = r.read(MAX_BODY + 1)
        finally:
            conn.close()
    except ssl.SSLError as e:
        raise DnsError(f"TLS error: {getattr(e, 'reason', None) or e}"[:200])
    except (OSError, http.client.HTTPException) as e:
        raise DnsError(f"{type(e).__name__}: {e}"[:200])
    if len(raw) > MAX_BODY: raise DnsError("Answer too large")
    try:    j = json.loads(raw) if raw.strip() else None
    except ValueError: j = None
    return r.status, j

def _g(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict): return default
        d = d.get(k)
    return default if d is None else d

def _num(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and not math.isnan(x)

# Reparte (marca de tiempo, total, bloqueadas) en 24 tramos de una hora que terminan ahora; para el gráfico de barras.
# EN: Spread (timestamp, total, blocked) into 24 one-hour bins ending now; for the bar chart.
def bin24(rows, now=None):
    now = now or time.time(); tot, blk = [0] * 24, [0] * 24
    for ts, t, b in rows:
        i = int((ts - (now - 86400)) // 3600)
        if 0 <= i < 24: tot[i] += int(t or 0); blk[i] += int(b or 0)
    return {"total": tot, "blocked": blk}


# Filas por hora de reloj (inicio de la hora, total, bloqueadas) de las últimas 24 h. La hora más antigua queda fuera porque la ventana la corta a medias.
# Se guardan en metrics.db para poder dibujar semanas y meses aunque el DNS solo entregue 24 h.
# EN: Clock-hour rows (hour start, total, blocked) for the last 24 h. The oldest hour is left out because the window cuts it in half.
#     They are stored in metrics.db so weeks and months can be drawn even when the DNS only gives 24 h.
def hour_rows(rows, now=None):
    now = now or time.time(); first = -(-int(now - 86400) // 3600) * 3600; acc = {}
    for ts, t, b in rows:
        if not _num(ts): continue
        h = int(ts) // 3600 * 3600
        if h < first: continue
        a = acc.setdefault(h, [0, 0]); a[0] += int(t or 0); a[1] += int(b or 0)
    return [(h, a[0], a[1]) for h, a in sorted(acc.items())]

# ─── Pi-hole ──────────────────────────────────────────────────────────────────
# v6: POST /api/auth da un «sid» que se manda en la cabecera X-FTL-SID (dura unos minutos y se renueva al usarlo).
# v5: /admin/api.php con ?auth=<token>; el token es el que muestra Ajustes → API.
# EN: v6: POST /api/auth gives a "sid" sent in the X-FTL-SID header (lasts a few minutes, renewed on use).
#     v5: /admin/api.php with ?auth=<token>; the token is the one shown in Settings → API.
def _ph6_login(cfg, st) -> bool:
    code, j = _req(cfg, "POST", "/api/auth", body={"password": cfg.get("password", "")})
    if code == 404 or (code == 200 and not isinstance(j, dict)): return False            # not v6
    if code in (401, 403) or (isinstance(j, dict) and _g(j, "session", "valid") is False):
        raise DnsError("Wrong password")
    if code == 429: raise DnsError("Pi-hole refused the login (too many attempts)")
    if code != 200: raise DnsError(f"Pi-hole answered HTTP {code}")
    st["api"], st["sid"] = "v6", _g(j, "session", "sid")
    return True

def _ph6(cfg, st, path, params=None, method="GET", body=None):
    for attempt in (0, 1):
        if "sid" not in st and not _ph6_login(cfg, st): raise DnsError("Pi-hole API v6 not found")
        hdr = {"X-FTL-SID": st["sid"]} if st.get("sid") else {}
        code, j = _req(cfg, method, path, params, body, hdr)
        if code == 401 and attempt == 0:
            st.pop("sid", None); continue
        return code, j
    raise DnsError("Session rejected")

def _ph5(cfg, params):
    p = dict(params)
    if cfg.get("password"): p["auth"] = cfg["password"]
    code, j = _req(cfg, "GET", "/admin/api.php", p)
    if code == 404: raise DnsError("No Pi-hole API at this address (tried /api/auth and /admin/api.php). Check the port; if Pi-hole only listens on 443, use https:// and turn off the certificate check")
    if code != 200: raise DnsError(f"Pi-hole answered HTTP {code}")
    return j

def pihole_collect(cfg, st):
    warnings = []
    api = st.get("api")
    if api is None:
        api = st["api"] = "v6" if _ph6_login(cfg, st) else "v5"
    if api == "v6":
        code, summ = _ph6(cfg, st, "/api/stats/summary")
        if code != 200 or not isinstance(summ, dict): raise DnsError(f"Pi-hole answered HTTP {code}")
        q = _g(summ, "queries", default={})
        total, blocked = int(q.get("total") or 0), int(q.get("blocked") or 0)
        snap = {"type": "pihole", "api": "v6", "queries": total, "blocked": blocked,
                "pct": round(float(q.get("percent_blocked")), 1) if _num(q.get("percent_blocked")) else (round(blocked / total * 100, 1) if total else 0.0),
                "cached": q.get("cached"), "forwarded": q.get("forwarded"), "unique_domains": q.get("unique_domains"),
                "clients": _g(summ, "clients", "active"), "domains_blocked": _g(summ, "gravity", "domains_being_blocked"),
                "gravity_updated": _g(summ, "gravity", "last_update")}
        def get(path, params=None):
            try:
                c, j = _ph6(cfg, st, path, params)
                return j if c == 200 and isinstance(j, dict) else None
            except DnsError as e: warnings.append(f"{path}: {e}"); return None
        b = get("/api/dns/blocking")
        snap["blocking"] = {"enabled": "enabled", "disabled": "disabled", "failed": "failed"}.get(str(_g(b, "blocking", default="")).lower(), "unknown") if b else "unknown"
        snap["timer"] = _g(b, "timer") if _num(_g(b, "timer")) else None
        td, tb, tc = get("/api/stats/top_domains", {"count": 10}), get("/api/stats/top_domains", {"count": 10, "blocked": "true"}), get("/api/stats/top_clients", {"count": 10})
        snap["top_domains"] = [{"name": x.get("domain"), "count": x.get("count")} for x in (_g(td, "domains", default=[]) or []) if isinstance(x, dict)]
        snap["top_blocked"] = [{"name": x.get("domain"), "count": x.get("count")} for x in (_g(tb, "domains", default=[]) or []) if isinstance(x, dict)]
        snap["top_clients"] = [{"name": x.get("name") or x.get("ip"), "ip": x.get("ip"), "count": x.get("count")} for x in (_g(tc, "clients", default=[]) or []) if isinstance(x, dict)]
        up = get("/api/stats/upstreams")
        ups, wsum, wcnt = [], 0.0, 0
        for x in (_g(up, "upstreams", default=[]) or []):
            if not isinstance(x, dict): continue
            ms = _g(x, "statistics", "response"); ms = round(ms * 1000, 1) if _num(ms) and ms > 0 else None
            cnt = x.get("count") or 0
            ups.append({"name": x.get("name") or x.get("ip"), "ip": x.get("ip"), "port": x.get("port"), "count": cnt, "ms": ms})
            if ms is not None and cnt: wsum += ms * cnt; wcnt += cnt
        snap["upstreams"], snap["ms"] = ups, (round(wsum / wcnt, 1) if wcnt else None)
        hh = get("/api/history")
        h6 = [(x.get("timestamp"), x.get("total"), x.get("blocked")) for x in (_g(hh, "history", default=[]) or []) if isinstance(x, dict) and _num(x.get("timestamp"))]
        snap["hourly"] = bin24(h6); snap["hours"] = hour_rows(h6)
        if not st.get("version") or time.time() - st.get("vts", 0) > 3600:
            v = get("/api/info/version")
            st["version"] = _g(v, "version", "core", "local", "version", default=st.get("version") or ""); st["vts"] = time.time()
        snap["version"] = st.get("version") or ""
    else:
        summ = _ph5(cfg, {"summaryRaw": ""})
        if not isinstance(summ, dict) or "dns_queries_today" not in summ:
            raise DnsError("Wrong token or not a Pi-hole" if not cfg.get("password") else "Unexpected answer (wrong token?)")
        total, blocked = int(summ.get("dns_queries_today") or 0), int(summ.get("ads_blocked_today") or 0)
        snap = {"type": "pihole", "api": "v5", "queries": total, "blocked": blocked,
                "pct": round(float(summ.get("ads_percentage_today") or 0), 1), "cached": summ.get("queries_cached"),
                "forwarded": summ.get("queries_forwarded"), "unique_domains": summ.get("unique_domains"), "clients": summ.get("unique_clients"),
                "domains_blocked": summ.get("domains_being_blocked"), "gravity_updated": _g(summ, "gravity_last_updated", "absolute"),
                "blocking": "enabled" if summ.get("status") == "enabled" else "disabled" if summ.get("status") == "disabled" else "unknown",
                "timer": None, "ms": None, "upstreams": [], "version": "v5"}
        def get5(params):
            try:
                j = _ph5(cfg, params); return j if isinstance(j, dict) else None
            except DnsError as e: warnings.append(f"{next(iter(params))}: {e}"); return None
        ti = get5({"topItems": 10})
        snap["top_domains"] = [{"name": k, "count": v} for k, v in sorted((_g(ti, "top_queries", default={}) or {}).items(), key=lambda kv: -kv[1])][:10]
        snap["top_blocked"] = [{"name": k, "count": v} for k, v in sorted((_g(ti, "top_ads", default={}) or {}).items(), key=lambda kv: -kv[1])][:10]
        src = get5({"getQuerySources": 10})
        snap["top_clients"] = []
        for k, v in sorted((_g(src, "top_sources", default={}) or {}).items(), key=lambda kv: -kv[1])[:10]:
            nm, _, ip = k.partition("|"); snap["top_clients"].append({"name": nm, "ip": ip or nm, "count": v})
        ot = get5({"overTimeData10mins": ""})
        dom, ads = _g(ot, "domains_over_time", default={}) or {}, _g(ot, "ads_over_time", default={}) or {}
        h5 = [(int(k), v, ads.get(k, 0)) for k, v in dom.items() if str(k).isdigit()]
        snap["hourly"] = bin24(h5); snap["hours"] = hour_rows(h5)
    snap["warnings"] = warnings
    return snap

# Pausa o reanuda el bloqueo. seconds=None → hasta que se reanude.
# EN: Pause or resume blocking. seconds=None → until resumed.
def pihole_set_blocking(cfg, st, enabled, seconds):
    if st.get("api") is None: pihole_collect(cfg, st)
    if st.get("api") == "v6":
        body = {"blocking": bool(enabled)}
        if not enabled and seconds: body["timer"] = int(seconds)
        code, _ = _ph6(cfg, st, "/api/dns/blocking", method="POST", body=body)
        if code != 200: raise DnsError(f"Pi-hole answered HTTP {code}")
    else:
        _ph5(cfg, {"enable": ""} if enabled else ({"disable": int(seconds)} if seconds else {"disable": ""}))

# ─── AdGuard Home ─────────────────────────────────────────────────────────────
def _ag(cfg, method, path, body=None):
    tok = base64.b64encode(f"{cfg['username']}:{cfg.get('password', '')}".encode()).decode()
    code, j = _req(cfg, method, path, body=body, headers={"Authorization": "Basic " + tok})
    if code in (401, 403): raise DnsError("Wrong username or password")
    return code, j

def _pairs(lst):          # AdGuard: [{"name": count}, ...] → [(name, count)]
    out = []
    for it in lst or []:
        if isinstance(it, dict):
            for k, v in it.items(): out.append((k, v))
    return out

def adguard_collect(cfg, st):
    warnings = []
    code, s = _ag(cfg, "GET", "/control/status")
    if code != 200 or not isinstance(s, dict): raise DnsError(f"AdGuard Home answered HTTP {code}")
    code, stt = _ag(cfg, "GET", "/control/stats")
    if code != 200 or not isinstance(stt, dict): raise DnsError(f"AdGuard Home answered HTTP {code} for the statistics")
    total = int(stt.get("num_dns_queries") or 0)
    blocked = int(stt.get("num_blocked_filtering") or 0) + int(stt.get("num_replaced_safebrowsing") or 0) + int(stt.get("num_replaced_parental") or 0)
    dur = s.get("protection_disabled_duration")
    snap = {"type": "adguard", "api": "agh", "queries": total, "blocked": blocked, "pct": round(blocked / total * 100, 1) if total else 0.0,
            "cached": None, "forwarded": None, "unique_domains": None, "clients": None, "gravity_updated": None,
            "blocking": "enabled" if s.get("protection_enabled") else "disabled",
            "timer": round(dur / 1000) if _num(dur) and dur > 0 else None,
            "ms": round(float(stt["avg_processing_time"]) * 1000, 1) if _num(stt.get("avg_processing_time")) and stt["avg_processing_time"] > 0 else None,
            "version": s.get("version") or "",
            "top_domains": [{"name": k, "count": v} for k, v in _pairs(stt.get("top_queried_domains"))[:10]],
            "top_blocked": [{"name": k, "count": v} for k, v in _pairs(stt.get("top_blocked_domains"))[:10]],
            "top_clients": [{"name": k, "ip": k, "count": v} for k, v in _pairs(stt.get("top_clients"))[:10]]}
    times = dict(_pairs(stt.get("top_upstreams_avg_time")))
    snap["upstreams"] = [{"name": k, "ip": k, "port": None, "count": v, "ms": round(times[k] * 1000, 1) if _num(times.get(k)) and times[k] > 0 else None}
                         for k, v in _pairs(stt.get("top_upstreams_responses"))[:6]]
    dq, bf = stt.get("dns_queries") or [], stt.get("blocked_filtering") or []
    if stt.get("time_units") == "hours" and len(dq) <= 24 and dq:
        pad = 24 - len(dq)
        snap["hourly"] = {"total": [0] * pad + [int(x or 0) for x in dq], "blocked": [0] * pad + [int(x or 0) for x in (bf + [0] * len(dq))[:len(dq)]]}
        top = int(time.time()) // 3600 * 3600                           # the last value is the current hour
        bl = (bf + [0] * len(dq))[:len(dq)]
        snap["hours"] = [(top - (len(dq) - 1 - i) * 3600, int(v or 0), int(bl[i] or 0)) for i, v in enumerate(dq)]
    else:
        snap["hourly"] = {"total": [], "blocked": []}
    try:
        c, f = _ag(cfg, "GET", "/control/filtering/status")
        snap["domains_blocked"] = sum(int(x.get("rules_count") or 0) for x in (f or {}).get("filters", []) if isinstance(x, dict) and x.get("enabled")) if c == 200 and isinstance(f, dict) else None
    except DnsError as e:
        warnings.append(f"filtering: {e}"); snap["domains_blocked"] = None
    snap["warnings"] = warnings
    return snap

def adguard_set_blocking(cfg, st, enabled, seconds):
    body = {"enabled": bool(enabled)}
    if not enabled and seconds: body["duration"] = int(seconds) * 1000
    code, _ = _ag(cfg, "POST", "/control/protection", body)
    if code != 200: raise DnsError(f"AdGuard Home answered HTTP {code}")

# ─── Lectura de un servidor ───────────────────────────────────────────────────
# Lee todo un servidor. «st» guarda la sesión de Pi-hole entre lecturas.
# EN: Read a whole server. "st" keeps the Pi-hole session between readings.
# ─── Salud de los DNS de salida (upstreams) ───────────────────────────────────
PROBE_EVERY = 60                         # seconds between active checks of each upstream
PROBE_NAME  = "example.com"
BLOCK_ANSWERS = ("0.0.0." + "0", "::")                       # addresses a DNS blocker answers with (a comparison, not a bind)
COMPARE_DNS = os.environ.get("DNS_COMPARE", "1.1.1.1")     # outside resolver used by the resolution test

# Pregunta «example.com» directamente a cada DNS de salida (cada 60 s) y anota si responde y en cuánto. Solo se sondean direcciones IP
# permitidas (no esta máquina ni enlace local, y solo el puerto 53 o puertos altos) y nunca DoH/DoT, que no se pueden consultar por UDP.
# EN: Ask "example.com" directly to each upstream (every 60 s) and note whether it answers and how fast. Only allowed IP addresses
#     are probed (not this machine or link-local, and only port 53 or high ports) and never DoH/DoT, which cannot be queried over UDP.
def probe_upstreams(snap: dict, st: dict):
    ups = snap.get("upstreams") or []
    pr = st.setdefault("probe", {"ts": 0.0, "res": {}})
    def target(u):            # (address, port) of an upstream that may be probed, else None
        hp = dnsq.split_upstream(u.get("ip") or u.get("name"), u.get("port"))
        return hp if hp and (hp[1] == 53 or hp[1] >= 1024) and auth.valid_target(hp[0]) else None
    if time.time() - pr["ts"] >= PROBE_EVERY:
        res, threads = {}, []
        def work(hp):
            r = dnsq.query(hp[0], hp[1], PROBE_NAME, "A", 2.0)
            res[hp] = {"ok": bool(r.get("ok")), "ms": r.get("ms"), "error": r.get("error")}
        for hp in list(dict.fromkeys(h for h in map(target, ups) if h))[:8]:
            th = threading.Thread(target=work, args=(hp,), daemon=True); th.start(); threads.append(th)
        for th in threads: th.join(4)
        pr["res"], pr["ts"] = res, time.time()
    for u in ups:
        hp = target(u)
        if hp and hp in pr["res"]: u["probe"] = pr["res"][hp]

# Prueba de resolución: pregunta el mismo nombre a este servidor DNS y a un resolutor externo, y compara.
# EN: Resolution test: ask the same name to this DNS server and to an outside resolver, and compare.
def resolve_compare(cfg: dict, name: str, qtype: str) -> dict:
    host = urlparse(cfg["url"]).hostname or ""
    if not auth.valid_target(host): raise ValueError("Invalid DNS server address")
    try: ip = socket.getaddrinfo(host, None, type=socket.SOCK_DGRAM)[0][4][0]
    except OSError: raise ValueError("Could not resolve the DNS server address")
    if not auth.valid_target(ip): raise ValueError("Invalid DNS server address")
    mine, outside = {}, {}
    def a(): mine.update(dnsq.query(ip, 53, name, qtype, 3.0))
    def b(): outside.update(dnsq.query(COMPARE_DNS, 53, name, qtype, 3.0))
    ts = [threading.Thread(target=f, daemon=True) for f in (a, b)]
    for x in ts: x.start()
    for x in ts: x.join(5)
    def sinkhole(r):          # Pi-hole / AdGuard answer 0.0.0.0 or :: for a blocked name
        addr = [x["value"] for x in r.get("answers") or [] if x["type"] in ("A", "AAAA")]
        return bool(addr) and all(a in BLOCK_ANSWERS for a in addr)
    blocked = bool(outside.get("answers")) and (sinkhole(mine) or mine.get("rcode") in (3, 5) or (mine.get("ok") and not mine.get("answers")))
    verdict = "blocked" if blocked else "failed" if not mine.get("ok") else "ok"
    return {"name": name, "type": qtype, "server": {"addr": ip, **mine}, "outside": {"addr": COMPARE_DNS, **outside}, "verdict": verdict}

def collect(cfg: dict, st: dict) -> dict:
    snap = pihole_collect(cfg, st) if cfg["type"] == "pihole" else adguard_collect(cfg, st)
    try: probe_upstreams(snap, st)
    except Exception as e: log.warning(f"upstream probe: {e}")  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
    snap["alerts"] = compute_alerts(snap)
    return snap

# Alertas de una lectura: la página y el Resumen las traducen por «type».
# EN: Alerts of a reading: the page and the Overview translate them by "type".
def compute_alerts(s: dict) -> list:
    a = []
    if s.get("blocking") == "disabled": a.append({"lv": "warn", "type": "blocking_off", "value": s.get("timer")})
    elif s.get("blocking") == "failed": a.append({"lv": "crit", "type": "blocking_failed"})
    if _num(s.get("domains_blocked")) and s["domains_blocked"] == 0 and s.get("blocking") == "enabled": a.append({"lv": "warn", "type": "no_lists"})
    ups = s.get("upstreams") or []
    probed = [u for u in ups if u.get("probe")]
    down = [u for u in probed if not u["probe"]["ok"]]
    if down: a.append({"lv": "crit" if len(down) == len(probed) else "warn", "type": "upstream_down", "value": ", ".join(str(u.get("name") or u.get("ip")) for u in down)[:80]})
    if any(u.get("ms") and u["ms"] >= 500 for u in ups): a.append({"lv": "warn", "type": "slow_upstream", "value": max(u["ms"] for u in ups if u.get("ms"))})
    return a

def set_blocking(cfg: dict, st: dict, enabled: bool, seconds):
    (pihole_set_blocking if cfg["type"] == "pihole" else adguard_set_blocking)(cfg, st, enabled, seconds)

# Prueba de conexión con lo escrito en el formulario, sin guardar nada.
# EN: Connection test with what is typed in the form, saving nothing.
def test_connection(cfg: dict) -> dict:
    st = {}
    snap = collect(cfg, st)
    if st.get("api") == "v6" and st.get("sid"):                     # free the session seat on the Pi-hole
        try: _req(cfg, "DELETE", "/api/auth", headers={"X-FTL-SID": st["sid"]})
        except DnsError: pass
    return {"type": snap["type"], "api": snap["api"], "version": snap.get("version", ""), "queries": snap["queries"], "blocking": snap["blocking"]}


# ─── Consultas por hora y por día (gráfico «Consultas por hora» con rangos) ─────────────
# Fuentes, en este orden: la base de largo plazo del DNS (Pi-hole v6 → /api/history/database; AdGuard con retención de días) y, si no hay o no alcanza,
# las horas que LabTower guarda desde que lee el DNS (tabla dns_hourly de metrics.db, un año por defecto).
# EN: Queries per hour and per day (the "Queries per hour" chart with ranges). Sources, in this order: the DNS's own long-term database (Pi-hole v6 →
#     /api/history/database; AdGuard with day retention) and, if it has none or not enough, the hours LabTower stores since it reads the DNS
#     (table dns_hourly in metrics.db, one year by default).
HOURS_KEEP = auth.keep_days("DNS_QUERIES_KEEP_DAYS", 365) * 86400
QRANGES = {"1w": (7, "hour"), "1mo": (30, "day"), "all": (365, "day")}      # range → (days, bar unit)
_QCACHE: dict = {}
_QTTL = {"1w": 120, "1mo": 300, "all": 900}

def push_hours(sid: str, rows):
    if not rows: return
    try:
        c = auth.metrics_conn()
        try:
            c.executemany("INSERT OR REPLACE INTO dns_hourly (sid,hour,total,blocked) VALUES (?,?,?,?)", [(sid, int(h), int(t), int(b)) for h, t, b in rows])
            c.execute("DELETE FROM dns_hourly WHERE sid = ? AND hour < ?", (sid, int(time.time()) - HOURS_KEEP)); c.commit()
        finally: c.close()
    except (sqlite3.Error, OSError) as e:
        log.warning(f"could not store the hourly counts: {e}")

def _bucket(ts, unit):
    if unit == "hour": return int(ts) // 3600 * 3600
    d = time.localtime(ts)
    return int(time.mktime((d.tm_year, d.tm_mon, d.tm_mday, 0, 0, 0, 0, 0, -1)))

def _next_bucket(cur, unit):
    if unit == "hour": return cur + 3600
    d = date(*time.localtime(cur)[:3]) + timedelta(days=1)
    return int(time.mktime(d.timetuple()))

def build_bars(rows, start, end, unit):
    """(timestamp, total, blocked) rows → one bar per hour or local day from start to end; empty hours are zero. Leading empty bars are cut."""
    acc = {}
    for ts, t, b in rows:
        if not _num(ts): continue
        a = acc.setdefault(_bucket(ts, unit), [0, 0]); a[0] += int(t or 0); a[1] += int(b or 0)
    bars, cur = [], _bucket(start, unit)
    while cur <= end and len(bars) < 800:
        a = acc.get(cur, [0, 0]); bars.append({"t": cur, "total": a[0], "blocked": a[1]}); cur = _next_bucket(cur, unit)
    while len(bars) > 1 and not bars[0]["total"]: bars.pop(0)
    return bars

def _remote_rows(cfg, st, days):
    """History rows from the DNS itself, or None when it has none (older Pi-hole, AdGuard with 1-day retention, errors)."""
    now = int(time.time())
    if cfg["type"] == "pihole" and st.get("api") == "v6":
        rows = []
        for a in range(now - days * 86400, now, 31 * 86400):                 # 31-day chunks keep every answer small
            code, j = _ph6(cfg, st, "/api/history/database", {"from": a, "until": min(now, a + 31 * 86400)})
            if code != 200 or not isinstance(j, dict): return None
            rows += [(x.get("timestamp"), x.get("total"), x.get("blocked")) for x in (j.get("history") or []) if isinstance(x, dict)]
        return rows or None
    if cfg["type"] == "adguard":
        code, stt = _ag(cfg, "GET", "/control/stats")
        if code != 200 or not isinstance(stt, dict) or stt.get("time_units") != "days": return None
        dq, bf = stt.get("dns_queries") or [], stt.get("blocked_filtering") or []
        today = _bucket(now, "day"); out = []
        for i, v in enumerate(dq):
            d = date(*time.localtime(today)[:3]) - timedelta(days=len(dq) - 1 - i)
            out.append((int(time.mktime(d.timetuple())) + 43200, v, bf[i] if i < len(bf) else 0))
        return out or None
    return None

def _local_rows(sid, days):
    c = auth.metrics_conn()
    try: return c.execute("SELECT hour,total,blocked FROM dns_hourly WHERE sid = ? AND hour >= ? ORDER BY hour", (sid, int(time.time()) - days * 86400)).fetchall()
    finally: c.close()

def queries_range(cfg, st, sid, rng):
    days, unit = QRANGES[rng]
    key, now = (sid, rng), time.time()
    hit = _QCACHE.get(key)
    if hit and now - hit[0] < _QTTL[rng]: return hit[1]
    src, rows = "local", None
    try: rows = _remote_rows(cfg, st, days)
    except (DnsError, OSError, ValueError, TypeError) as e: log.warning(f"remote history unavailable: {e}")
    if rows: src = cfg["type"]
    else: rows = _local_rows(sid, days)
    start = int(now) - days * 86400
    out = {"range": rng, "unit": unit, "source": src, "bars": build_bars(rows, start, int(now), unit)}
    if len(_QCACHE) > 100: _QCACHE.clear()
    _QCACHE[key] = (now, out)
    return out


# ─── Actividad de clientes (consultas por cliente en el tiempo) ─────────────────────
# Pi-hole v6: /api/history/clients (24 h) y /api/history/database/clients (más tiempo); Pi-hole v5: getClientsOverTime (24 h). AdGuard Home no entrega
# una serie por cliente, así que ahí el gráfico no está disponible. Se muestran los 6 clientes con más consultas y el resto como «otros».
# EN: Client activity (queries per client over time). Pi-hole v6: /api/history/clients (24 h) and /api/history/database/clients (longer); Pi-hole v5:
#     getClientsOverTime (24 h). AdGuard Home gives no per-client series, so the chart is not available there. The 6 busiest clients are shown, the rest as "other".
CLIENT_TOP = 6
CRANGES = {"1d": (1, "hour"), "1w": (7, "hour"), "1mo": (30, "day"), "all": (365, "day")}
_CCACHE: dict = {}
_CTTL = {"1d": 60, "1w": 120, "1mo": 300, "all": 900}

def _client_names(raw):
    """Pi-hole 'clients' (object keyed by address, or a list) → {key: display name}."""
    out = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            out[str(k)] = str((v.get("name") if isinstance(v, dict) else "") or k)[:80]
    elif isinstance(raw, list):
        for v in raw:
            if isinstance(v, dict) and (v.get("ip") or v.get("name")): out[str(v.get("ip") or v.get("name"))] = str(v.get("name") or v.get("ip"))[:80]
    return out

def build_client_bars(points, names, start, end, unit):
    """points: [(timestamp, {client: count})] → {"clients": [{key, name, total}] (top CLIENT_TOP, busiest first), "bars": [{t, v: [per client…, other]}]}."""
    totals = {}
    for ts, data in points:
        if _num(ts) and isinstance(data, dict):
            for k, v in data.items():
                if _num(v): totals[str(k)] = totals.get(str(k), 0) + int(v)
    top = [k for k, _ in sorted(totals.items(), key=lambda kv: -kv[1])[:CLIENT_TOP] if totals[k] > 0]
    idx, acc = {k: i for i, k in enumerate(top)}, {}
    for ts, data in points:
        if not _num(ts) or not isinstance(data, dict): continue
        row = acc.setdefault(_bucket(ts, unit), [0] * (len(top) + 1))
        for k, v in data.items():
            if _num(v): row[idx.get(str(k), len(top))] += int(v)
    bars, cur = [], _bucket(start, unit)
    while cur <= end and len(bars) < 800:
        bars.append({"t": cur, "v": acc.get(cur, [0] * (len(top) + 1))}); cur = _next_bucket(cur, unit)
    while len(bars) > 1 and not any(bars[0]["v"]): bars.pop(0)
    return {"clients": [{"key": k, "name": names.get(k, k), "total": totals[k]} for k in top], "bars": bars}

def _client_points(cfg, st, rng, days):
    """(points, names) from the DNS, or None when this DNS cannot give a per-client series for the range."""
    now = int(time.time())
    if cfg["type"] != "pihole": return None
    if st.get("api") == "v6":
        pts, names = [], {}
        chunks = [(None, None)] if rng == "1d" else [(a, min(now, a + 31 * 86400)) for a in range(now - days * 86400, now, 31 * 86400)]
        for a, b in chunks:
            path, params = ("/api/history/clients", {"N": 20}) if a is None else ("/api/history/database/clients", {"from": a, "until": b, "N": 20})
            code, j = _ph6(cfg, st, path, params)
            if code != 200 or not isinstance(j, dict): return None
            names.update(_client_names(j.get("clients")))
            pts += [(x.get("timestamp"), x.get("data")) for x in (j.get("history") or []) if isinstance(x, dict)]
        return (pts, names) if pts else None
    if st.get("api") == "v5" and rng == "1d":
        j = _ph5(cfg, {"getClientsOverTime": ""})
        cl = (j or {}).get("clients") if isinstance(j, dict) else None
        ot = (j or {}).get("over_time") if isinstance(j, dict) else None
        if not isinstance(cl, list) or not isinstance(ot, dict): return None
        keys = [str(c.get("ip") or c.get("name")) for c in cl if isinstance(c, dict)]
        pts = [(int(ts), {keys[i]: v for i, v in enumerate(vals) if i < len(keys)}) for ts, vals in ot.items() if str(ts).isdigit() and isinstance(vals, list)]
        return (pts, _client_names(cl)) if pts else None
    return None

def clients_range(cfg, st, sid, rng):
    key, now = (sid, rng), time.time()
    hit = _CCACHE.get(key)
    if hit and now - hit[0] < _CTTL[rng]: return hit[1]
    days, unit = CRANGES[rng]
    out = {"range": rng, "unit": unit, "supported": False, "clients": [], "bars": []}
    try: got = _client_points(cfg, st, rng, days)
    except (DnsError, OSError, ValueError, TypeError) as e:
        log.warning(f"client history unavailable: {e}"); got = None
    if got:
        out.update(build_client_bars(got[0], got[1], int(now) - days * 86400, int(now), unit)); out["supported"] = True
    if len(_CCACHE) > 100: _CCACHE.clear()
    _CCACHE[key] = (now, out)
    return out

# ─── Historial (% bloqueado, consultas y tiempo de respuesta por servidor) ────
# Un buffer circular de ~12 h por servidor; cada muestra se guarda al instante en metrics.db (tabla dns_samples) y al arrancar se recargan las últimas ~12 h.
# EN: A ~12 h circular buffer per server; every sample is stored at once in metrics.db (table dns_samples) and the last ~12 h are reloaded at startup.
_HISTORY: dict = {}
_hist_lock = threading.Lock()

def push_history(sid: str, snap: dict):
    pt = {"ts": int(time.time()), "total": snap["queries"], "blocked": snap["blocked"], "pct": snap["pct"], "ms": snap.get("ms")}
    with _hist_lock:
        dq = _HISTORY.setdefault(sid, _deque(maxlen=_HIST_MAX))
        if dq and pt["ts"] - dq[-1]["ts"] < HIST_EVERY - 1: return
        dq.append(pt)
    try:
        c = auth.metrics_conn()
        try:
            c.execute("INSERT OR REPLACE INTO dns_samples (sid,ts,total,blocked,pct,ms) VALUES (?,?,?,?,?,?)", (sid, pt["ts"], pt["total"], pt["blocked"], pt["pct"], pt["ms"]))
            c.commit()
        finally: c.close()
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not store the history sample: {e}")

def get_history(sid: str) -> list:
    with _hist_lock: return list(_HISTORY.get(sid, []))

def load_history() -> int:
    n = 0
    try:
        c = auth.metrics_conn()
        try:
            c.execute("DELETE FROM dns_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,)); c.commit()
            keep = {x.get("id") for x in load_servers()}
            cut = int(time.time()) - _HIST_MAX * HIST_EVERY
            rows = c.execute("SELECT sid,ts,total,blocked,pct,ms FROM dns_samples WHERE ts >= ? ORDER BY ts", (cut,)).fetchall()
        finally: c.close()
        with _hist_lock:
            for sid, ts, total, blocked, pct, ms in rows:
                if sid not in keep: continue
                _HISTORY.setdefault(sid, _deque(maxlen=_HIST_MAX)).append({"ts": ts, "total": total, "blocked": blocked, "pct": pct, "ms": ms}); n += 1
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not load the history: {e}")
    return n

RANGE_SECS = {"1h": 3600, "1d": 86400, "1w": 604800, "1mo": 2592000}
RANGE_POINTS = 600

def history_window(range_: str, prev: bool = False):
    """(since, until) of a range. prev=True gives the period just before it (same length) so charts can compare the two; "all" has none."""
    now, span = int(time.time()), RANGE_SECS.get(range_)
    if prev: return ((now - 2 * span, now - span) if span else None)
    return (now - span if span else 0, now + 1)

def history_range(sid: str, range_: str, prev: bool = False) -> list:
    win = history_window(range_, prev)
    if win is None: return []
    c = auth.metrics_conn()
    try:
        rows = c.execute("SELECT ts,total,blocked,pct,ms FROM dns_samples WHERE sid = ? AND ts >= ? AND ts < ? ORDER BY ts", (sid, win[0], win[1])).fetchall()
    finally: c.close()
    step = 1 if len(rows) <= RANGE_POINTS else -(-len(rows) // RANGE_POINTS)
    def avg(grp, k):
        v = [r[k] for r in grp if r[k] is not None]
        return round(sum(v) / len(v), 2) if v else None
    out = []
    for i in range(0, len(rows), step):
        grp = rows[i:i + step]
        out.append({"ts": grp[len(grp) // 2][0], "total": avg(grp, 1), "blocked": avg(grp, 2), "pct": avg(grp, 3), "ms": avg(grp, 4)})
    return out

def forget_history(sid: str):
    with _hist_lock: _HISTORY.pop(sid, None)
    for c in (_QCACHE, _CCACHE):
        for k in [k for k in c if k[0] == sid]: c.pop(k, None)
    try:
        c = auth.metrics_conn()
        try: c.execute("DELETE FROM dns_samples WHERE sid = ?", (sid,)); c.execute("DELETE FROM dns_hourly WHERE sid = ?", (sid,)); c.commit()
        finally: c.close()
    except Exception as e: log.warning(f"could not delete the history: {e}")  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running

def _history_pruner():
    while True:
        time.sleep(3600)
        try:
            c = auth.metrics_conn()
            try: c.execute("DELETE FROM dns_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,)); c.commit()
            finally: c.close()
        except Exception as e: log.warning(f"could not prune the history: {e}")  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running

# ─── Caché y hilos de consulta ────────────────────────────────────────────────
class DnsCache:
    def __init__(self, sid):
        self.id, self._lock, self._data, self._err, self._ts = sid, threading.RLock(), {}, None, None
        self.state = {}                 # Pi-hole session (sid / api version), used only by this server's thread and by set_blocking
        self.wake = threading.Event()
    def update(self, data):
        with self._lock: self._data, self._err, self._ts = data, None, time.time()
    def set_error(self, e):
        with self._lock: self._err = e
    def snap(self):
        with self._lock: return {"id": self.id, "data": dict(self._data), "error": self._err, "ts": self._ts}
    def clear(self):
        with self._lock: self._data, self._err, self._ts = {}, None, None

_cache: dict = {}
_pollers: dict = {}
_glock = threading.Lock()

# Eventos en la línea de tiempo del Resumen cuando cambia el estado de algo importante.
# EN: Events on the Overview timeline when something important changes state.
def _events(n: dict, snap: dict):
    ch = auth.state_changed(f"dns-bl:{n['id']}", snap["blocking"])
    if ch:
        if snap["blocking"] == "disabled": auth.record_event("dns", "warn", f"{n['name']}: blocking paused", "dns_off", n=n["name"])
        elif ch[1] == "enabled": auth.record_event("dns", "info", f"{n['name']}: blocking active", "dns_on", n=n["name"])
        elif snap["blocking"] == "failed": auth.record_event("dns", "crit", f"{n['name']}: blocking failed", "dns_fail", n=n["name"])

    for u in snap.get("upstreams") or []:
        p = u.get("probe")
        if not p: continue
        nm = str(u.get("name") or u.get("ip"))
        ch = auth.state_changed(f"dns-up:{n['id']}:{nm}", "up" if p["ok"] else "down")
        if ch and not p["ok"]: auth.record_event("dns", "warn", f"{n['name']}: upstream {nm} not answering", "dns_upstream_down", n=n["name"], u=nm)
        elif ch: auth.record_event("dns", "info", f"{n['name']}: upstream {nm} answering again", "dns_upstream_up", n=n["name"], u=nm)

def _poll(sid: str):
    cache = _cache.get(sid)
    if not cache: return
    while True:
        try:
            n = next((x for x in load_servers() if x["id"] == sid), None)
        except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
            log.error(f"[{sid}] config read: {e}"); n = False
        if n is None: return
        if n and auth.paused(n):
            cache.clear()                 # paused: no queries or events, nothing stale when resumed / pausado: sin consultas
        elif n:
            t0 = time.time()
            try:
                snap = collect(n, cache.state)
                snap["name"] = n["name"]
                push_hours(sid, snap.pop("hours", None))
                push_history(sid, snap)
                cache.update(snap)
                _events(n, snap)
                if auth.state_changed(f"dns-dn:{sid}", "up"):
                    auth.record_event("dns", "info", f"{n['name']}: reachable again", "dns_up", n=n["name"])
                log.debug(f"[{n['name']}] read in {time.time() - t0:.2f}s")
            except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
                cache.set_error(str(e)[:200])
                log.error(f"[{n['name']}] poll error: {e}")
                if auth.state_changed(f"dns-dn:{sid}", "down"):
                    auth.record_event("dns", "crit", f"{n['name']}: unreachable", "dns_down", n=n["name"])
        active = (time.time() - _last_view) < VIEW_GRACE
        cache.wake.wait(POLL_ACTIVE if active else POLL_IDLE)
        cache.wake.clear()

def ensure_poller(n: dict):
    sid = n["id"]
    with _glock:
        if sid not in _cache: _cache[sid] = DnsCache(sid)
        if sid not in _pollers or not _pollers[sid].is_alive():
            t = threading.Thread(target=_poll, args=(sid,), daemon=True, name=f"dns-{sid[:8]}")
            _pollers[sid] = t; t.start()
            log.info(f"Poller → {n['name']} ({n['url']})")

def remove_poller(sid: str):
    with _glock:
        c = _cache.pop(sid, None); _pollers.pop(sid, None)
    if c: c.wake.set()
    forget_history(sid)

def start_all():
    for n in load_servers(): ensure_poller(n)

# ─── Health ───────────────────────────────────────────────────────────────────
def health_report(detailed=False):
    c = auth.check_common()
    c["dns_file"] = auth.check_file(DATA_FILE)
    now = time.time(); items = load_servers(); dead, bad = [], []
    paused = [n for n in items if auth.paused(n)]
    for n in items:
        if auth.paused(n): continue                  # not checked, so it raises no warning
        t = _pollers.get(n["id"])
        if t is None or not t.is_alive(): dead.append(n["name"]); continue
        cc = _cache.get(n["id"])
        if cc is None: continue
        sn = cc.snap()
        if sn["error"]: bad.append(f'{n["name"]}: {sn["error"]}')
        elif sn["ts"] and now - sn["ts"] > max(3 * POLL_IDLE, 180): bad.append(f'{n["name"]}: data {int(now - sn["ts"])} s old')
    if not items: c["pollers"] = auth.chk(auth.OK, "no DNS server configured")
    elif dead:    c["pollers"] = auth.chk(auth.FAIL, "poller stopped: " + ", ".join(dead))
    else:         c["pollers"] = auth.chk(auth.OK, f"{len(items) - len(paused)} running" + (f", {len(paused)} paused" if paused else ""))
    c["dns_servers"] = auth.chk(auth.WARN, "; ".join(bad)) if bad else auth.chk(auth.OK, "all DNS servers answering")
    return auth.health_reply("dns", c, detailed)

# ─── HTTP ─────────────────────────────────────────────────────────────────────
_test_gate = threading.Semaphore(2)

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
            if n < 0 or n > 8192: return None
            d = json.loads(self.rfile.read(n)) if n else {}
            return d if isinstance(d, dict) else None      # EN: a list/number would crash the handlers (500); reject it (400)
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

    # GET: página, versión y salud son públicos; el resto exige sesión con DNS «readonly».
    # Rutas: /api/dns, /api/dns/<id>/history, /api/me.
    # EN: GET: page, version and health are public; the rest requires a session with DNS "readonly".
    def do_GET(self):
        global _last_view
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
        if not auth.check_permission(tok, "dns", "readonly"):
            return self._json(401, {"error": "Unauthorized"})
        if path == "/api/dns":
            was_idle = (time.time() - _last_view) >= VIEW_GRACE
            _last_view = time.time()
            if was_idle:
                for cc in list(_cache.values()): cc.wake.set()
            with_hist = parse_qs(urlparse(self.path).query).get("hist", ["1"])[0] != "0"
            out = []
            for n in load_servers():
                if n["id"] not in _pollers or not _pollers[n["id"]].is_alive(): ensure_poller(n)
                snap = (DnsCache(n["id"]) if auth.paused(n) else _cache.get(n["id"], DnsCache(n["id"]))).snap()
                out.append({**public(n), "paused": auth.paused(n), "snap": snap, "history": get_history(n["id"]) if with_hist else []})
            return self._json(200, {"servers": out})
        mh = re.fullmatch(r"/api/dns/([A-Za-z0-9_-]{1,40})/history", path)
        if mh:
            if not any(n.get("id") == mh.group(1) for n in load_servers()): return self._json(404, {"error": "Server not found"})
            rng = parse_qs(urlparse(self.path).query).get("range", ["1d"])[0]
            if rng not in RANGE_SECS and rng != "all": return self._json(400, {"error": "Invalid range"})
            prev = parse_qs(urlparse(self.path).query).get("prev", ["0"])[0] == "1"
            try: return self._json(200, {"range": rng, "prev": prev, "history": history_range(mh.group(1), rng, prev)})
            except Exception as e:  # noqa: BLE001 - error de la petición: se responde sin caer / request error: answered without crashing
                log.warning(f"history query failed: {e}"); return self._json(500, {"error": "Could not read the history"})
        mc = re.fullmatch(r"/api/dns/([A-Za-z0-9_-]{1,40})/clients", path)
        if mc:
            cfg = next((n for n in load_servers() if n.get("id") == mc.group(1)), None)
            if cfg is None: return self._json(404, {"error": "Server not found"})
            if auth.paused(cfg): return self._json(409, {"error": "Monitoring of this server is paused"})
            rng = parse_qs(urlparse(self.path).query).get("range", ["1d"])[0]
            if rng not in CRANGES: return self._json(400, {"error": "Invalid range"})
            cache = _cache.get(cfg["id"])
            return self._json(200, clients_range(cfg, cache.state if cache else {}, cfg["id"], rng))
        mq = re.fullmatch(r"/api/dns/([A-Za-z0-9_-]{1,40})/queries", path)
        if mq:
            cfg = next((n for n in load_servers() if n.get("id") == mq.group(1)), None)
            if cfg is None: return self._json(404, {"error": "Server not found"})
            if auth.paused(cfg): return self._json(409, {"error": "Monitoring of this server is paused"})
            rng = parse_qs(urlparse(self.path).query).get("range", ["1w"])[0]
            if rng not in QRANGES: return self._json(400, {"error": "Invalid range"})
            cache = _cache.get(cfg["id"])
            try: return self._json(200, queries_range(cfg, cache.state if cache else {}, cfg["id"], rng))
            except (sqlite3.Error, OSError, DnsError, ValueError) as e:
                log.warning(f"queries query failed: {e}"); return self._json(500, {"error": "Could not read the history"})
        self._json(404, {"error": "Not found"})

    # POST: login/logout; «execute»: pausar o reanudar el bloqueo; solo admin: alta, edición y prueba.
    # EN: POST: login/logout; "execute": pause or resume blocking; admin only: add, edit and test.
    def do_POST(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})
        if path == "/api/login":
            r, err = auth.login_session(self, body.get("username", ""), body.get("password", ""), body.get("remember"), body.get("code"))   # the service checks the password and opens the session
            if not r: return self._json(err[0], {"error": err[1]})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", auth.session_cookie(r["token"], r["ttl"]))
            br = json.dumps({"ok": True, "username": r["username"], "permissions": r["permissions"], "must_change_password": r["must_change_password"]}).encode()
            self.send_header("Content-Length", str(len(br)))
            self.end_headers(); self.wfile.write(br); return
        if path == "/api/logout":
            auth.delete_session(tok); return self._json(200, {"ok": True})

        # POST /api/dns/<id>/blocking {"enabled": bool, "seconds": int|null}: pausa o reanuda el bloqueo (nivel «execute»).
        # EN: POST /api/dns/<id>/blocking: pause or resume blocking ("execute" level).
        mb = re.fullmatch(r"/api/dns/([a-zA-Z0-9\-]+)/blocking", path)
        if mb:
            if not auth.check_permission(tok, "dns", "execute"):
                return self._json(403 if auth.check_permission(tok, "dns", "readonly") else 401, {"error": "Execute permission required"})
            n = next((x for x in load_servers() if x["id"] == mb.group(1)), None)
            if not n: return self._json(404, {"error": "Not found"})
            if auth.paused(n): return self._json(409, {"error": "Monitoring of this server is paused"})
            if not isinstance(body.get("enabled"), bool): return self._json(400, {"error": "enabled must be true or false"})
            secs = body.get("seconds")
            if secs is not None and (not isinstance(secs, int) or isinstance(secs, bool) or not 1 <= secs <= 86400): return self._json(400, {"error": "seconds must be 1-86400"})
            cc = _cache.get(n["id"])
            try:
                set_blocking(n, cc.state if cc else {}, body["enabled"], secs)
            except Exception as e:  # noqa: BLE001 - error de la petición: se responde sin caer / request error: answered without crashing
                return self._json(502, {"error": str(e)[:200]})
            who = (auth.get_session(tok) or {}).get("username", "?")
            log.info(f"{who}: {'resume' if body['enabled'] else 'pause'} blocking on {n['name']}")
            if cc: cc.wake.set()
            return self._json(200, {"ok": True})

        # POST /api/dns/<id>/resolve {"name": "example.com", "type": "A"|"AAAA"}: qué responde este DNS frente a un resolutor externo (nivel «execute»).
        # EN: POST /api/dns/<id>/resolve: what this DNS answers compared with an outside resolver ("execute" level).
        mr = re.fullmatch(r"/api/dns/([a-zA-Z0-9\-]+)/resolve", path)
        if mr:
            if not auth.check_permission(tok, "dns", "execute"):
                return self._json(403 if auth.check_permission(tok, "dns", "readonly") else 401, {"error": "Execute permission required"})
            n = next((x for x in load_servers() if x["id"] == mr.group(1)), None)
            if auth.paused(n): return self._json(409, {"error": "Monitoring of this server is paused"})
            if not n: return self._json(404, {"error": "Not found"})
            name, qt = str(body.get("name") or "").strip(), str(body.get("type") or "A").upper()
            if not dnsq.valid_name(name) or qt not in ("A", "AAAA"): return self._json(400, {"error": "Invalid name or type"})
            if not _test_gate.acquire(blocking=False): return self._json(429, {"error": "Too many tests at once"})
            try: return self._json(200, resolve_compare(n, name, qt))
            except ValueError as e: return self._json(400, {"error": str(e)})
            finally: _test_gate.release()

        if not auth.check_permission(tok, "dns", "admin"):
            return self._json(403 if auth.check_permission(tok, "dns", "readonly") else 401, {"error": "Admin permission required"})

        # Pausar o reanudar el monitoreo de un servidor: {"paused": true|false}. No es el bloqueo de anuncios (eso es /blocking).
        # EN: Pause or resume monitoring a server. Not the ad blocking (that is /blocking).
        mp = re.fullmatch(r"/api/dns/([a-zA-Z0-9\-]+)/pause", path)
        if mp:
            if not isinstance(body.get("paused"), bool): return self._json(400, {"error": "paused must be true or false"})
            with _dns_lock:
                items = load_servers()
                cur = next((x for x in items if x["id"] == mp.group(1)), None)
                if not cur: return self._json(404, {"error": "Not found"})
                auth.set_paused(cur, body["paused"]); save_servers(items)
            log.info(f"[{cur['name']}] monitoring " + ("paused" if body["paused"] else "resumed"))
            ensure_poller(cur)
            cc = _cache.get(cur["id"])
            if cc: cc.wake.set()
            return self._json(200, {"dns": {**public(cur), "paused": auth.paused(cur)}})

        if path == "/api/dns":
            try: cfg = validate(body)
            except ValueError as e: return self._json(400, {"error": str(e)})
            cfg["id"] = str(uuid.uuid4())
            with _dns_lock:
                items = load_servers()
                if len(items) >= 16: return self._json(400, {"error": "Too many servers"})
                if any(x["url"] == cfg["url"] and x["type"] == cfg["type"] for x in items):
                    return self._json(409, {"error": "That server already exists"})
                items.append(cfg); save_servers(items)
            ensure_poller(cfg)
            return self._json(201, {"server": public(cfg)})

        if path == "/api/test":
            cur = next((x for x in load_servers() if x["id"] == body.get("id")), None) if body.get("id") else None
            try: cfg = validate(body, cur)
            except ValueError as e: return self._json(400, {"error": str(e)})
            if not _test_gate.acquire(blocking=False): return self._json(429, {"error": "Too many tests at once"})
            try:
                return self._json(200, {"ok": True, **test_connection(cfg)})
            except Exception as e:  # noqa: BLE001 - error de la petición: se responde sin caer / request error: answered without crashing
                return self._json(200, {"ok": False, "error": str(e)[:200]})
            finally: _test_gate.release()

        m = re.fullmatch(r"/api/dns/([a-zA-Z0-9\-]+)", path)
        if m:
            with _dns_lock:
                items = load_servers()
                cur = next((x for x in items if x["id"] == m.group(1)), None)
                if not cur: return self._json(404, {"error": "Not found"})
                try: cfg = validate(body, cur)
                except ValueError as e: return self._json(400, {"error": str(e)})
                cfg["id"] = cur["id"]
                if any(x["id"] != cur["id"] and x["url"] == cfg["url"] and x["type"] == cfg["type"] for x in items):
                    return self._json(409, {"error": "That server already exists"})
                items[items.index(cur)] = cfg; save_servers(items)
            c = _cache.get(cfg["id"])
            if c: c.state.clear(); c.wake.set()
            return self._json(200, {"server": public(cfg)})
        self._json(404, {"error": "Not found"})

    def do_DELETE(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        tok = self._tok()
        if not auth.check_permission(tok, "dns", "admin"):
            return self._json(403, {"error": "Admin permission required"})
        m = re.fullmatch(r"/api/dns/([a-zA-Z0-9\-]+)", urlparse(self.path).path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        with _dns_lock:
            items = load_servers()
            new = [x for x in items if x["id"] != m.group(1)]
            if len(new) == len(items): return self._json(404, {"error": "Not found"})
            save_servers(new)
        remove_poller(m.group(1))
        self._json(200, {"ok": True})

# Arranque: permiso «dns» para usuarios antiguos (una vez), hilos de consulta y servidor en loopback.
# EN: Startup: "dns" permission for old users (once), polling threads and the loopback server.
if __name__ == "__main__":
    auth.prepare_module(DATA_DIR, Path(__file__).parent, LEGACY_FILES)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if auth.ensure_permissions(("dns",)): log.info("'dns' permissions updated")
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"Permissions: {e}")
    log.info(f"DNS Monitor en http://{HOST}:{PORT} — poll {POLL_ACTIVE:g}s active / {POLL_IDLE:g}s idle")
    n = load_history()
    if n: log.info(f"History restored: {n} samples")
    start_all()
    threading.Thread(target=_history_pruner, daemon=True, name="history-pruner").start()
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
