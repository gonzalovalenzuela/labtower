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
import base64, http.client, json, os, re, ssl, sys, time, logging, threading, uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128
from urllib.parse import urlparse, parse_qs, urlencode
from collections import deque as _deque
from pathlib import Path

# Módulo compartido de autenticación (carpeta hermana /auth).
# EN: Shared authentication module (sibling folder /auth).
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

# Solo loopback; el acceso desde la red pasa por nginx.
# EN: Loopback only; network access goes through nginx.
HOST       = "127.0.0.1"
PORT       = 8087
STATIC_DIR = Path(__file__).parent / "static"
DATA_DIR   = auth.module_dir("dns-monitor")          # solo la ruta; la carpeta se crea al arrancar / EN: path only, created at startup
LEGACY_FILES = ()
DATA_FILE  = DATA_DIR / "dns.json"
POLL_ACTIVE = float(os.environ.get("DNS_POLL_ACTIVE", 15))   # seconds, while someone is watching
POLL_IDLE   = float(os.environ.get("DNS_POLL_IDLE", 60))     # seconds, when nobody has the page open
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

def _num(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x

# Reparte (marca de tiempo, total, bloqueadas) en 24 tramos de una hora que terminan ahora; para el gráfico de barras.
# EN: Spread (timestamp, total, blocked) into 24 one-hour bins ending now; for the bar chart.
def bin24(rows, now=None):
    now = now or time.time(); tot, blk = [0] * 24, [0] * 24
    for ts, t, b in rows:
        i = int((ts - (now - 86400)) // 3600)
        if 0 <= i < 24: tot[i] += int(t or 0); blk[i] += int(b or 0)
    return {"total": tot, "blocked": blk}

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
        snap["hourly"] = bin24([(x.get("timestamp"), x.get("total"), x.get("blocked")) for x in (_g(hh, "history", default=[]) or []) if isinstance(x, dict) and _num(x.get("timestamp"))])
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
            except DnsError as e: warnings.append(f"{list(params)[0]}: {e}"); return None
        ti = get5({"topItems": 10})
        snap["top_domains"] = [{"name": k, "count": v} for k, v in sorted((_g(ti, "top_queries", default={}) or {}).items(), key=lambda kv: -kv[1])][:10]
        snap["top_blocked"] = [{"name": k, "count": v} for k, v in sorted((_g(ti, "top_ads", default={}) or {}).items(), key=lambda kv: -kv[1])][:10]
        src = get5({"getQuerySources": 10})
        snap["top_clients"] = []
        for k, v in sorted((_g(src, "top_sources", default={}) or {}).items(), key=lambda kv: -kv[1])[:10]:
            nm, _, ip = k.partition("|"); snap["top_clients"].append({"name": nm, "ip": ip or nm, "count": v})
        ot = get5({"overTimeData10mins": ""})
        dom, ads = _g(ot, "domains_over_time", default={}) or {}, _g(ot, "ads_over_time", default={}) or {}
        snap["hourly"] = bin24([(int(k), v, ads.get(k, 0)) for k, v in dom.items() if str(k).isdigit()])
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
def collect(cfg: dict, st: dict) -> dict:
    snap = pihole_collect(cfg, st) if cfg["type"] == "pihole" else adguard_collect(cfg, st)
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
    except Exception as e:
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
    except Exception as e:
        log.warning(f"could not load the history: {e}")
    return n

RANGE_SECS = {"1h": 3600, "1d": 86400, "1w": 604800, "1mo": 2592000}
RANGE_POINTS = 600

def history_range(sid: str, range_: str) -> list:
    since = int(time.time()) - RANGE_SECS[range_] if range_ in RANGE_SECS else 0
    c = auth.metrics_conn()
    try:
        rows = c.execute("SELECT ts,total,blocked,pct,ms FROM dns_samples WHERE sid = ? AND ts >= ? ORDER BY ts", (sid, since)).fetchall()
    finally: c.close()
    step = 1 if len(rows) <= RANGE_POINTS else -(-len(rows) // RANGE_POINTS)
    out = []
    for i in range(0, len(rows), step):
        grp = rows[i:i + step]
        def avg(k):
            v = [r[k] for r in grp if r[k] is not None]
            return round(sum(v) / len(v), 2) if v else None
        out.append({"ts": grp[len(grp) // 2][0], "total": avg(1), "blocked": avg(2), "pct": avg(3), "ms": avg(4)})
    return out

def forget_history(sid: str):
    with _hist_lock: _HISTORY.pop(sid, None)
    try:
        c = auth.metrics_conn()
        try: c.execute("DELETE FROM dns_samples WHERE sid = ?", (sid,)); c.commit()
        finally: c.close()
    except Exception as e: log.warning(f"could not delete the history: {e}")

def _history_pruner():
    while True:
        time.sleep(3600)
        try:
            c = auth.metrics_conn()
            try: c.execute("DELETE FROM dns_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,)); c.commit()
            finally: c.close()
        except Exception as e: log.warning(f"could not prune the history: {e}")

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

def _poll(sid: str):
    cache = _cache.get(sid)
    if not cache: return
    while True:
        try:
            n = next((x for x in load_servers() if x["id"] == sid), None)
        except Exception as e:
            log.error(f"[{sid}] config read: {e}"); n = False
        if n is None: return
        if n:
            t0 = time.time()
            try:
                snap = collect(n, cache.state)
                snap["name"] = n["name"]
                push_history(sid, snap)
                cache.update(snap)
                _events(n, snap)
                if auth.state_changed(f"dns-dn:{sid}", "up"):
                    auth.record_event("dns", "info", f"{n['name']}: reachable again", "dns_up", n=n["name"])
                log.debug(f"[{n['name']}] read in {time.time() - t0:.2f}s")
            except Exception as e:
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
    for n in items:
        t = _pollers.get(n["id"])
        if t is None or not t.is_alive(): dead.append(n["name"]); continue
        cc = _cache.get(n["id"])
        if cc is None: continue
        sn = cc.snap()
        if sn["error"]: bad.append(f'{n["name"]}: {sn["error"]}')
        elif sn["ts"] and now - sn["ts"] > max(3 * POLL_IDLE, 180): bad.append(f'{n["name"]}: data {int(now - sn["ts"])} s old')
    if not items: c["pollers"] = auth.chk(auth.OK, "no DNS server configured")
    elif dead:    c["pollers"] = auth.chk(auth.FAIL, "poller stopped: " + ", ".join(dead))
    else:         c["pollers"] = auth.chk(auth.OK, f"{len(items)} running")
    c["dns_servers"] = auth.chk(auth.WARN, "; ".join(bad)) if bad else auth.chk(auth.OK, "all DNS servers answering")
    return auth.health_reply("dns", c, detailed)

# ─── HTTP ─────────────────────────────────────────────────────────────────────
_test_gate = threading.Semaphore(2)

class H(BaseHTTPRequestHandler):
    timeout = 30
    def log_message(self, fmt, *a):
        if int(a[1]) >= 400: log.warning(f"{self.client_address[0]} {a[1]}")
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
            return self._json(200, {"username": sess["username"], "permissions": sess["permissions"]} if sess else {})
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
                snap = _cache.get(n["id"], DnsCache(n["id"])).snap()
                out.append({**public(n), "snap": snap, "history": get_history(n["id"]) if with_hist else []})
            return self._json(200, {"servers": out})
        mh = re.fullmatch(r"/api/dns/([A-Za-z0-9_-]{1,40})/history", path)
        if mh:
            if not any(n.get("id") == mh.group(1) for n in load_servers()): return self._json(404, {"error": "Server not found"})
            rng = parse_qs(urlparse(self.path).query).get("range", ["1d"])[0]
            if rng not in RANGE_SECS and rng != "all": return self._json(400, {"error": "Invalid range"})
            try: return self._json(200, {"range": rng, "history": history_range(mh.group(1), rng)})
            except Exception as e:
                log.warning(f"history query failed: {e}"); return self._json(500, {"error": "Could not read the history"})
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
            r, err = auth.login_session(self, body.get("username", ""), body.get("password", ""), body.get("remember"))   # the service checks the password and opens the session
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
            if not isinstance(body.get("enabled"), bool): return self._json(400, {"error": "enabled must be true or false"})
            secs = body.get("seconds")
            if secs is not None and (not isinstance(secs, int) or isinstance(secs, bool) or not 1 <= secs <= 86400): return self._json(400, {"error": "seconds must be 1-86400"})
            cc = _cache.get(n["id"])
            try:
                set_blocking(n, cc.state if cc else {}, body["enabled"], secs)
            except Exception as e:
                return self._json(502, {"error": str(e)[:200]})
            who = (auth.get_session(tok) or {}).get("username", "?")
            log.info(f"{who}: {'resume' if body['enabled'] else 'pause'} blocking on {n['name']}")
            if cc: cc.wake.set()
            return self._json(200, {"ok": True})

        if not auth.check_permission(tok, "dns", "admin"):
            return self._json(403 if auth.check_permission(tok, "dns", "readonly") else 401, {"error": "Admin permission required"})

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
            except Exception as e:
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
    except Exception as e:
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
