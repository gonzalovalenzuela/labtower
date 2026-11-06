#!/usr/bin/env python3
"""
VPN Monitor — clientes conectados a Tailscale, OpenVPN y WireGuard / connected clients of Tailscale, OpenVPN and WireGuard
"""
# VPN Monitor (puerto 8089): muestra quién está conectado a cada VPN, desde cuándo y cuánto tráfico lleva. Es solo lectura.
#
# Fuentes (cada una es un «servidor VPN» de la lista):
#   tailscale  API de Tailscale (clave de API de solo lectura): dispositivos de la tailnet, usuario, si están en línea y su último contacto.
#   openvpn    el archivo de estado del servidor OpenVPN, leído por SSH: nombre (CN), IP real y virtual, bytes y «conectado desde».
#   wireguard  «wg show all dump», leído por SSH: peers, último handshake, endpoint y bytes. WireGuard no tiene usuarios: se muestra un alias
#              que se define aquí (clave pública → nombre). Un peer cuenta como conectado si su último handshake tiene menos de 3 minutos.
#
# SSH: LabTower genera una llave propia (ed25519, solo para este módulo) que se instala en el servidor VPN. Lo recomendable es restringirla
# con «command="…"» en authorized_keys para que solo pueda leer ese dato. El comando que se ejecuta es fijo (nunca viene del navegador).
# La huella del servidor se acepta la primera vez y después se exige (known_hosts propio).
#
# Sesiones: este módulo anota cuándo se vio conectado a cada cliente y cuándo dejó de estarlo (vpn.json guarda los servidores, state.json las
# sesiones). Los eventos «conectó / se desconectó» salen en la línea de tiempo del Resumen.
# EN: VPN Monitor (port 8089): shows who is connected to each VPN, since when and how much traffic. Read-only.
#     Sources: tailscale (API, read-only key), openvpn (server status file over SSH), wireguard ("wg show all dump" over SSH; peers get an alias
#     defined here; connected = last handshake under 3 minutes). SSH uses an own ed25519 key for this module, ideally restricted with command="…"
#     in authorized_keys; the command is fixed (never from the browser); the server host key is accepted once and then enforced.
#     Sessions: the module records when each client was seen connected / gone (vpn.json = servers, state.json = sessions); connect / disconnect
#     events go to the Overview timeline.
import json, os, re, subprocess, sys, time, logging, threading, urllib.request, urllib.error, urllib.parse, shutil
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128
from urllib.parse import urlparse, parse_qs
from collections import deque as _deque
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

HOST       = "127.0.0.1"
PORT       = 8089
STATIC_DIR = Path(__file__).parent / "static"
DATA_DIR   = auth.module_dir("vpn-monitor")
LEGACY_FILES = ()
DATA_FILE  = DATA_DIR / "vpn.json"
STATE_FILE = DATA_DIR / "state.json"
LAST_FILE  = DATA_DIR / "last.json"      # last reading of each server: shown right after a restart, marked as stale
SSH_DIR    = DATA_DIR / "ssh"
SSH_KEY    = SSH_DIR / "id_ed25519"
KNOWN      = SSH_DIR / "known_hosts"
POLL_ACTIVE = float(os.environ.get("VPN_POLL_ACTIVE", 20))
POLL_IDLE   = float(os.environ.get("VPN_POLL_IDLE", 60))
VIEW_GRACE  = 30
WG_FRESH    = 180            # s: a WireGuard peer with a handshake newer than this is connected
TS_FRESH    = 300            # s: Tailscale fallback when the API does not say connectedToControl
LOG_KEEP    = 40             # recent sessions kept per server
_HIST_MAX   = 720            # ~4 h at 20 s
_last_view  = 0.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("vpn")

TYPES    = ("tailscale", "openvpn", "wireguard")
SECRETS  = ("api_key",)
_vpn_lock = threading.RLock()
_state_lock = threading.RLock()

# Los comandos remotos son fijos. / The remote commands are fixed.
CMD_WG = "wg show all dump"
DEFAULT_OVPN_STATUS = "/run/openvpn-server/status-server.log"

def _num(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x

# ─── Configuración / Configuration ──────────────────────────────────────────────
def load_vpn() -> list:
    return auth.read_json(DATA_FILE, [], list)

def save_vpn(items: list):
    with _vpn_lock:
        auth.write_json(DATA_FILE, items)        # contiene la clave de API: 0600 / EN: holds the API key: 0600

_PUB = re.compile(r"[A-Za-z0-9+/]{42}[AEIMQUYcgkosw480]=")           # WireGuard public key (base64, 44 chars)
def parse_aliases(text) -> dict:
    """'<public key> <name>' per line → {key: name}. Raises ValueError on a malformed line."""
    out = {}
    for ln in str(text or "").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"): continue
        k, _, nm = ln.partition(" ")
        nm = nm.strip()
        if not _PUB.fullmatch(k) or not nm or len(nm) > 60 or re.search(r"[\x00-\x1f\x7f<>]", nm): raise ValueError("Invalid alias line (use: <public key> <name>)")
        out[k] = nm
    if len(out) > 200: raise ValueError("Too many aliases")
    return out

def aliases_text(d) -> str:
    return "\n".join(f"{k} {v}" for k, v in (d or {}).items())

def validate(body: dict, current=None) -> dict:
    typ = (current.get("type") if current is not None else body.get("type")) or ""
    if typ not in TYPES: raise ValueError("Invalid VPN type")
    if current is not None and body.get("type") not in (None, "", typ): raise ValueError("The VPN type cannot be changed")
    cfg = {"type": typ}
    if current: cfg.update({k: v for k, v in current.items() if k != "type"})
    name = str(body.get("name", cfg.get("name", "")) or "").strip()
    if not name or len(name) > 60 or re.search(r"[\x00-\x1f\x7f]", name): raise ValueError("Invalid name")
    cfg["name"] = name
    def _to(default):
        try: v = int(body.get("timeout", cfg.get("timeout", default)))
        except (TypeError, ValueError): raise ValueError("Invalid timeout")
        if not 2 <= v <= 30: raise ValueError("Timeout must be 2-30 seconds")
        return v
    if typ == "tailscale":
        tn = str(body.get("tailnet", cfg.get("tailnet", "-")) or "-").strip()
        if not re.fullmatch(r"-|[A-Za-z0-9][A-Za-z0-9._@-]{0,100}", tn): raise ValueError("Invalid tailnet")
        cfg["tailnet"] = tn
        k = body.get("api_key")
        if k not in (None, ""):
            k = str(k).strip()
            if not re.fullmatch(r"[A-Za-z0-9_.\-]{8,300}", k): raise ValueError("Invalid API key")
            cfg["api_key"] = k
        if not cfg.get("api_key"): raise ValueError("API key required")
        cfg["timeout"] = _to(10)
        for k in ("host", "port", "ssh_user", "use_sudo", "status_path", "aliases"): cfg.pop(k, None)
        return cfg
    host = str(body.get("host", cfg.get("host", "")) or "").strip()
    if not host or host.startswith("-") or not auth.valid_target(host): raise ValueError("Invalid host (this machine and link-local addresses are not allowed)")
    cfg["host"] = host
    try: port = int(body.get("port", cfg.get("port", 22)))
    except (TypeError, ValueError): raise ValueError("Invalid port")
    if not 1 <= port <= 65535: raise ValueError("Invalid port")
    cfg["port"] = port
    user = str(body.get("ssh_user", cfg.get("ssh_user", "")) or "").strip()
    if not re.fullmatch(r"[a-z_][a-z0-9_.-]{0,31}", user): raise ValueError("Invalid SSH user")
    cfg["ssh_user"] = user
    cfg["use_sudo"] = bool(body.get("use_sudo", cfg.get("use_sudo", False)))
    cfg["timeout"] = _to(10)
    if typ == "openvpn":
        sp = str(body.get("status_path", cfg.get("status_path", DEFAULT_OVPN_STATUS)) or DEFAULT_OVPN_STATUS).strip()
        if not re.fullmatch(r"/[A-Za-z0-9_./-]{1,200}", sp) or ".." in sp: raise ValueError("Invalid status file path")
        cfg["status_path"] = sp
        cfg.pop("aliases", None)
    else:
        if "aliases" in body:
            if not isinstance(body["aliases"], str): raise ValueError("Invalid aliases")
            cfg["aliases"] = parse_aliases(body["aliases"])
        cfg.setdefault("aliases", {})
        cfg.pop("status_path", None)
    cfg.pop("tailnet", None); cfg.pop("api_key", None)
    return cfg

def public(n: dict) -> dict:
    out = {k: v for k, v in n.items() if k not in SECRETS}
    for k in SECRETS: out["has_" + k] = bool(n.get(k))
    if "aliases" in out: out["aliases_text"] = aliases_text(out.pop("aliases"))
    return out

# ─── Llave SSH / SSH key ───────────────────────────────────────────────────────
def ssh_pub():
    try: return (SSH_KEY.with_suffix(".pub")).read_text().strip()
    except OSError: return ""

def ssh_keygen() -> str:
    """Create the module's SSH key if it does not exist and return the public key."""
    if not SSH_KEY.exists():
        if not shutil.which("ssh-keygen"): raise RuntimeError("ssh-keygen is not installed (apt install openssh-client)")
        SSH_DIR.mkdir(parents=True, exist_ok=True); os.chmod(SSH_DIR, 0o700)
        r = subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "labtower-vpn", "-f", str(SSH_KEY)], capture_output=True, text=True, timeout=20)
        if r.returncode != 0: raise RuntimeError("Could not create the SSH key")
        os.chmod(SSH_KEY, 0o600)
    if not SSH_KEY.with_suffix(".pub").exists():
        r = subprocess.run(["ssh-keygen", "-y", "-f", str(SSH_KEY)], capture_output=True, text=True, timeout=20)
        if r.returncode == 0: SSH_KEY.with_suffix(".pub").write_text(r.stdout)
    return ssh_pub()

def _sudo(cfg: dict) -> str:
    """"sudo -n " (never asks for a password) when the server is set to use sudo."""
    return "sudo -n " if cfg.get("use_sudo") else ""

def ssh_run(cfg: dict, command: str) -> str:
    if not SSH_KEY.exists(): raise RuntimeError("No SSH key yet: create it in the VPN Monitor settings and install it on the VPN server")
    if not shutil.which("ssh"): raise RuntimeError("ssh is not installed (apt install openssh-client)")
    t = int(cfg.get("timeout", 10))
    cmd = ["ssh", "-F", "/dev/null", "-i", str(SSH_KEY), "-p", str(cfg["port"]), "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
           "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={KNOWN}", "-o", f"ConnectTimeout={t}",
           "-o", "LogLevel=ERROR", "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=2", "-o", "PasswordAuthentication=no",
           f"{cfg['ssh_user']}@{cfg['host']}", command]
    try: r = subprocess.run(cmd, capture_output=True, text=True, timeout=t + 8, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(DATA_DIR)})
    except subprocess.TimeoutExpired: raise RuntimeError("SSH timed out")
    if r.returncode != 0:
        e = (r.stderr or "").strip().splitlines()
        raise RuntimeError("SSH: " + (e[-1][:160] if e else f"exit {r.returncode}"))
    return r.stdout

def forget_host(host: str, port: int):
    """Drop the stored host key (used when a server's address changes)."""
    if KNOWN.exists() and shutil.which("ssh-keygen"):
        subprocess.run(["ssh-keygen", "-q", "-f", str(KNOWN), "-R", host if port == 22 else f"[{host}]:{port}"], capture_output=True, timeout=10)

# ─── Lectura de cada fuente / Reading each source ─────────────────────────────
def parse_wireguard(text: str, aliases: dict, now: float) -> list:
    """`wg show all dump` → clients. Interface lines have 5 fields, peer lines 9 (the first one is the interface name)."""
    out = []
    for ln in text.splitlines():
        f = ln.split("\t")
        if len(f) < 9: continue
        iface, key, endpoint, allowed, hs, rx, tx = f[0], f[1], f[3], f[4], f[5], f[6], f[7]
        try: hs, rx, tx = int(hs), int(rx), int(tx)
        except ValueError: continue
        ip = endpoint.rsplit(":", 1)[0].strip("[]") if endpoint and endpoint != "(none)" else None
        out.append({"key": f"{iface}:{key}", "name": aliases.get(key) or key[:8] + "…", "alias": key in aliases, "id": key, "iface": iface,
                    "ip": ip, "virtual": allowed if allowed != "(none)" else None, "rx": rx, "tx": tx,
                    "last": hs or None, "online": bool(hs) and now - hs <= WG_FRESH, "since": None})
    return out

def _hms_epoch(s: str):
    try: return int(time.mktime(time.strptime(re.sub(r"\s+", " ", s.strip()), "%a %b %d %H:%M:%S %Y")))
    except ValueError: return None

def _ovpn_ip(real: str) -> str:
    """Address part of OpenVPN's "Real Address": "1.2.3.4:5", "[v6]:5", "::ffff:1.2.3.4[:5]" or a bare IPv6 (no port)."""
    a = re.sub(r"^(udp|tcp)[46]?:", "", real.strip())
    m = re.fullmatch(r"\[([^\]]+)\](?::\d+)?", a)
    if m: a = m.group(1)
    else:
        m = re.fullmatch(r"(\d+\.\d+\.\d+\.\d+):\d+", a)
        if m: return m.group(1)
        if a.count(":") == 1: a = a.rsplit(":", 1)[0]
    m = re.fullmatch(r"::ffff:(\d+\.\d+\.\d+\.\d+)(?::\d+)?", a, re.I)
    return m.group(1) if m else a

def parse_openvpn(text: str) -> list:
    """OpenVPN status file, versions 1, 2 and 3."""
    out, v1 = [], False
    for ln in text.splitlines():
        ln = ln.rstrip("\r")
        sep = "\t" if ln.startswith("CLIENT_LIST\t") else "," if ln.startswith("CLIENT_LIST,") else None
        if sep:
            f = ln.split(sep)
            if len(f) < 9: continue
            name = f[1]
            if len(f) > 9 and f[9] and f[9] != "UNDEF": name = f"{f[9]} ({f[1]})" if f[9] != f[1] else f[1]
            try: rx, tx, since = int(f[5]), int(f[6]), int(f[8])
            except ValueError: continue
            ip = _ovpn_ip(f[2]) if f[2] else None
            out.append({"key": f[1] + "@" + f[2], "name": name, "id": f[1], "ip": ip, "virtual": f[3] or None, "rx": rx, "tx": tx,
                        "last": None, "online": True, "since": since})
            continue
        if ln.startswith("Common Name,Real Address,Bytes Received"): v1 = True; continue
        if v1:
            if ln.startswith(("ROUTING TABLE", "GLOBAL STATS", "END")): v1 = False; continue
            f = ln.split(",")
            if len(f) < 5: continue
            try: rx, tx = int(f[2]), int(f[3])
            except ValueError: continue
            out.append({"key": f[0] + "@" + f[1], "name": f[0], "id": f[0], "ip": _ovpn_ip(f[1]), "virtual": None, "rx": rx, "tx": tx,
                        "last": None, "online": True, "since": _hms_epoch(f[4])})
    return out

def _iso(s):
    try: return int(datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except (TypeError, ValueError): return None

def parse_tailscale(devs: list, now: float) -> list:
    out = []
    for d in devs if isinstance(devs, list) else []:
        if not isinstance(d, dict): continue
        last = _iso(d.get("lastSeen"))
        on = d.get("connectedToControl")
        if not isinstance(on, bool): on = bool(last) and now - last <= TS_FRESH
        addrs = [a for a in (d.get("addresses") or []) if isinstance(a, str)]
        name = str(d.get("hostname") or d.get("name") or "?")[:80]
        out.append({"key": str(d.get("nodeId") or d.get("id") or name), "name": name, "id": name, "ip": addrs[0] if addrs else None, "virtual": None,
                    "user": str(d.get("user") or "")[:80], "os": str(d.get("os") or "")[:30], "version": str(d.get("clientVersion") or "").split("-")[0][:20],
                    "update": bool(d.get("updateAvailable")), "tags": [str(x)[:40] for x in (d.get("tags") or [])[:6] if isinstance(x, str)],
                    "rx": None, "tx": None, "last": last, "online": bool(on), "since": None})
    return out

def fetch_tailscale(cfg: dict, now: float) -> list:
    url = "https://api.tailscale.com/api/v2/tailnet/%s/devices?fields=all" % urllib.parse.quote(cfg.get("tailnet") or "-", safe="")
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + cfg["api_key"], "Accept": "application/json", "User-Agent": "labtower-vpn"})
    try:
        with urllib.request.urlopen(req, timeout=int(cfg.get("timeout", 10))) as r:  # constant https://api.tailscale.com URL  # nosec B310
            j = json.loads(r.read(4_000_000))
    except urllib.error.HTTPError as e:
        raise RuntimeError({401: "Tailscale: invalid or expired API key", 403: "Tailscale: the key cannot read this tailnet", 404: "Tailscale: tailnet not found"}.get(e.code, f"Tailscale: HTTP {e.code}"))
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise RuntimeError("Tailscale: " + str(getattr(e, "reason", e))[:120])
    return parse_tailscale(j.get("devices") if isinstance(j, dict) else None, now)

def collect(cfg: dict) -> dict:
    now = time.time(); typ = cfg["type"]
    if typ == "tailscale": cl = fetch_tailscale(cfg, now)
    elif typ == "openvpn": cl = parse_openvpn(ssh_run(cfg, _sudo(cfg) + "cat " + cfg["status_path"]))
    else: cl = parse_wireguard(ssh_run(cfg, _sudo(cfg) + CMD_WG), cfg.get("aliases") or {}, now)
    return {"ts": int(now), "clients": cl, "online": sum(1 for c in cl if c["online"]), "total": len(cl),
            "rx": sum(c["rx"] for c in cl if c.get("rx") and c["online"]) if typ != "tailscale" else None,
            "tx": sum(c["tx"] for c in cl if c.get("tx") and c["online"]) if typ != "tailscale" else None}

def test_connection(cfg: dict) -> dict:
    s = collect(cfg)
    return {"online": s["online"], "total": s["total"]}

# ─── Sesiones / Sessions ───────────────────────────────────────────────────────
# state.json: {"<id>": {"cur": {<key>: {"since": ts, "name": str}}, "log": [{"name","start","end"}], "init": bool}}
_state: dict = {}

def load_state():
    global _state
    with _state_lock: _state = auth.read_json(STATE_FILE, {}, dict)

def save_state():
    with _state_lock: auth.write_json(STATE_FILE, _state)

def track(n: dict, snap: dict, now: float):
    """Detect connects / disconnects, fill each client's `since`, keep the recent-sessions log and emit events."""
    with _state_lock:
        st = _state.setdefault(n["id"], {"cur": {}, "log": [], "init": False})
        cur, changed, first = st["cur"], False, not st.get("init")
        seen = set()
        for c in snap["clients"]:
            if not c["online"]: continue
            seen.add(c["key"])
            k = cur.get(c["key"])
            if k is None:
                cur[c["key"]] = k = {"since": int(c["since"] or now), "name": c["name"]}; changed = True
                if not first: auth.record_event("vpn", "info", f"{n['name']}: {c['name']} connected", "vpn_up", n=n["name"], c=c["name"])
            c["since"] = k["since"]
        for key in [x for x in cur if x not in seen]:
            k = cur.pop(key); changed = True
            st["log"].insert(0, {"name": k["name"], "start": k["since"], "end": int(now)})
            auth.record_event("vpn", "info", f"{n['name']}: {k['name']} disconnected", "vpn_down", n=n["name"], c=k["name"])
        st["log"] = st["log"][:LOG_KEEP]
        if first: st["init"] = changed = True
        snap["log"] = list(st["log"])
    if changed: save_state()

def drop_state(nid: str):
    with _state_lock:
        if _state.pop(nid, None) is not None: save_state()

# ─── Caché, historial y poller / Cache, history and poller ─────────────────────
class Cache:
    def __init__(self, nid):
        self.id, self._lock, self._data, self._err, self._ts, self._stale = nid, threading.RLock(), {}, None, None, False
        self.hist = _deque(maxlen=_HIST_MAX)
        self.wake = threading.Event()
    def update(self, data):
        with self._lock:
            self._data, self._err, self._ts, self._stale = data, None, time.time(), False
            self.hist.append([data["ts"], data["online"]])
    def preload(self, data, ts):
        """Last reading stored before the restart: shown (stale) until the first fresh one arrives."""
        with self._lock:
            if not self._data: self._data, self._ts, self._stale = data, ts, True
    def set_error(self, e):
        with self._lock: self._err = e
    def snap(self):
        with self._lock: return {"id": self.id, "data": dict(self._data), "error": self._err, "ts": self._ts, "stale": self._stale}
    def history(self):
        with self._lock: return list(self.hist)

_cache: dict = {}
_last: dict = {}
_last_lock = threading.Lock()
SLOW_READ = 5.0                  # seconds: slower reads are logged so a slow server can be found

def load_last():
    global _last
    with _last_lock: _last = auth.read_json(LAST_FILE, {}, dict)

def save_last(nid, snap):
    with _last_lock:
        _last[nid] = {"ts": time.time(), "snap": snap}
        for k in [k for k in _last if k not in _cache]: _last.pop(k, None)
        try: auth.write_json(LAST_FILE, _last)
        except OSError as e: log.warning(f"last reading not saved: {e}")
_pollers: dict = {}
_glock = threading.Lock()

def _poll(nid: str):
    cache = _cache.get(nid)
    if not cache: return
    while True:
        try: n = next((x for x in load_vpn() if x["id"] == nid), None)
        except Exception as e:
            log.error(f"[{nid}] config read: {e}"); n = False
        if n is None: return
        if n:
            try:
                t0 = time.time()
                snap = collect(n)
                if time.time() - t0 > SLOW_READ: log.info(f"[{n['name']}] slow read: {time.time() - t0:.1f}s")
                track(n, snap, time.time())
                cache.update(snap)
                save_last(nid, snap)
                if auth.state_changed(f"vpn-dn:{nid}", "up"):
                    auth.record_event("vpn", "info", f"{n['name']}: reachable again", "vpn_reach", n=n["name"])
            except Exception as e:
                cache.set_error(str(e)[:200])
                log.error(f"[{n['name']}] poll error: {e}")
                if auth.state_changed(f"vpn-dn:{nid}", "down"):
                    auth.record_event("vpn", "warn", f"{n['name']}: cannot read the VPN status ({str(e)[:80]})", "vpn_unreach", n=n["name"])
        active = (time.time() - _last_view) < VIEW_GRACE
        cache.wake.wait(POLL_ACTIVE if active else POLL_IDLE)
        cache.wake.clear()

def ensure_poller(n: dict):
    nid = n["id"]
    with _glock:
        if nid not in _cache:
            _cache[nid] = Cache(nid)
            old = _last.get(nid)
            if isinstance(old, dict) and isinstance(old.get("snap"), dict) and isinstance(old.get("snap", {}).get("clients"), list):
                _cache[nid].preload(old["snap"], float(old.get("ts") or 0))
        if nid not in _pollers or not _pollers[nid].is_alive():
            t = threading.Thread(target=_poll, args=(nid,), daemon=True, name=f"vpn-{nid[:8]}")
            _pollers[nid] = t; t.start()
            log.info(f"Poller → {n['name']} ({n['type']})")

def remove_poller(nid: str):
    with _glock:
        c = _cache.pop(nid, None); _pollers.pop(nid, None)
    if c: c.wake.set()
    drop_state(nid)

def start_all():
    load_state()
    load_last()
    for n in load_vpn(): ensure_poller(n)

def health_report(detailed=False):
    c = auth.check_common()
    c["vpn_file"] = auth.check_file(DATA_FILE)
    now = time.time(); items = load_vpn(); dead, bad = [], []
    need_ssh = any(x["type"] != "tailscale" for x in items)
    c["ssh_tools"] = auth.chk(auth.OK, "ssh found") if shutil.which("ssh") else auth.chk(auth.FAIL if need_ssh else auth.WARN, "ssh not installed (apt install openssh-client)")
    for n in items:
        t = _pollers.get(n["id"])
        if t is None or not t.is_alive(): dead.append(n["name"]); continue
        cc = _cache.get(n["id"])
        if cc is None: continue
        sn = cc.snap()
        if sn["error"]: bad.append(f'{n["name"]}: {sn["error"]}')
        elif sn["ts"] and now - sn["ts"] > max(3 * POLL_IDLE, 180): bad.append(f'{n["name"]}: data {int(now - sn["ts"])} s old')
    if not items: c["pollers"] = auth.chk(auth.OK, "no VPN configured")
    elif dead:    c["pollers"] = auth.chk(auth.FAIL, "poller stopped: " + ", ".join(dead))
    else:         c["pollers"] = auth.chk(auth.OK, f"{len(items)} running")
    c["vpn_sources"] = auth.chk(auth.WARN, "; ".join(bad)) if bad else auth.chk(auth.OK, "all VPN sources answering")
    return auth.health_reply("vpn", c, detailed)

# ─── HTTP ───────────────────────────────────────────────────────────────────
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

    # GET: página, versión y salud son públicos; el resto exige sesión con VPN «readonly». Rutas: /api/vpn, /api/ssh-key (admin), /api/me.
    # EN: GET: page, version and health are public; the rest requires a session with VPN "readonly". Routes: /api/vpn, /api/ssh-key (admin), /api/me.
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
        if not auth.check_permission(tok, "vpn", "readonly"):
            return self._json(401, {"error": "Unauthorized"})
        if path == "/api/vpn":
            was_idle = (time.time() - _last_view) >= VIEW_GRACE
            _last_view = time.time()
            if was_idle:
                for cc in list(_cache.values()): cc.wake.set()
            with_hist = parse_qs(urlparse(self.path).query).get("hist", ["1"])[0] != "0"
            out = []
            for n in load_vpn():
                if n["id"] not in _pollers or not _pollers[n["id"]].is_alive(): ensure_poller(n)
                cc = _cache.get(n["id"]) or Cache(n["id"])
                out.append({**public(n), "snap": cc.snap(), "history": cc.history() if with_hist else []})
            return self._json(200, {"vpn": out})
        if path == "/api/ssh-key":
            if not auth.check_permission(tok, "vpn", "admin"): return self._json(403, {"error": "Admin permission required"})
            return self._json(200, {"public_key": ssh_pub()})
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
        if not auth.check_permission(tok, "vpn", "admin"):
            return self._json(403 if auth.check_permission(tok, "vpn", "readonly") else 401, {"error": "Admin permission required"})

        # Crea la llave SSH del módulo (si no existe) y devuelve la pública para instalarla en el servidor VPN.
        # EN: Create the module's SSH key (if missing) and return the public key to install on the VPN server.
        if path == "/api/ssh-key":
            try: return self._json(200, {"public_key": ssh_keygen()})
            except (RuntimeError, OSError, subprocess.SubprocessError) as e: return self._json(500, {"error": str(e)[:160]})

        if path == "/api/vpn":
            try: cfg = validate(body)
            except ValueError as e: return self._json(400, {"error": str(e)})
            import uuid
            cfg["id"] = str(uuid.uuid4())
            with _vpn_lock:
                items = load_vpn()
                if len(items) >= 16: return self._json(400, {"error": "Too many VPN servers"})
                items.append(cfg); save_vpn(items)
            ensure_poller(cfg)
            return self._json(201, {"vpn": public(cfg)})

        if path == "/api/test":
            cur = next((x for x in load_vpn() if x["id"] == body.get("id")), None) if body.get("id") else None
            try: cfg = validate(body, cur) if cur else validate(body)
            except ValueError as e: return self._json(400, {"error": str(e)})
            if not _test_gate.acquire(blocking=False): return self._json(429, {"error": "Too many tests at once"})
            try: return self._json(200, {"ok": True, **test_connection(cfg)})
            except Exception as e: return self._json(200, {"ok": False, "error": str(e)[:200]})
            finally: _test_gate.release()

        m = re.fullmatch(r"/api/vpn/([a-zA-Z0-9\-]+)", path)
        if m:
            with _vpn_lock:
                items = load_vpn()
                cur = next((x for x in items if x["id"] == m.group(1)), None)
                if not cur: return self._json(404, {"error": "Not found"})
                try: cfg = validate(body, cur)
                except ValueError as e: return self._json(400, {"error": str(e)})
                cfg["id"] = cur["id"]
                if cur.get("host") and (cur.get("host"), cur.get("port")) != (cfg.get("host"), cfg.get("port")):
                    try: forget_host(cur["host"], cur.get("port", 22))
                    except (OSError, subprocess.SubprocessError): pass
                items[items.index(cur)] = cfg; save_vpn(items)
            c = _cache.get(cfg["id"])
            if c: c.wake.set()
            return self._json(200, {"vpn": public(cfg)})
        self._json(404, {"error": "Not found"})

    def do_DELETE(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        tok = self._tok()
        if not auth.check_permission(tok, "vpn", "admin"):
            return self._json(403, {"error": "Admin permission required"})
        m = re.fullmatch(r"/api/vpn/([a-zA-Z0-9\-]+)", urlparse(self.path).path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        with _vpn_lock:
            items = load_vpn()
            new = [x for x in items if x["id"] != m.group(1)]
            if len(new) == len(items): return self._json(404, {"error": "Not found"})
            save_vpn(new)
        remove_poller(m.group(1))
        self._json(200, {"ok": True})

if __name__ == "__main__":
    auth.prepare_module(DATA_DIR, Path(__file__).parent, LEGACY_FILES)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if auth.ensure_permissions(("vpn",)): log.info("'vpn' permissions updated")
    except Exception as e:
        log.warning(f"Permissions: {e}")
    log.info(f"VPN Monitor en http://{HOST}:{PORT} — poll {POLL_ACTIVE:g}s active / {POLL_IDLE:g}s idle")
    start_all()
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
