#!/usr/bin/env python3
"""WOL Console — Backend con auth compartido."""
import json, os, socket, re, sys, time, logging, hashlib, hmac, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128      # default is 5: a burst of simultaneous connections got reset
from urllib.parse import urlparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

PORT       = 8080
HOST       = "0.0.0.0"
DATA_FILE  = Path(__file__).parent / "devices.json"
LOG_FILE   = Path(__file__).parent / "wake_log.json"
# Net Monitor host table (shared info: MAC, IP, name, type). Read-only here.
NET_HOSTS_FILE = Path(os.environ.get("NET_HOSTS_FILE", str(Path(__file__).parent.parent / "net-monitor" / "hosts.json")))
STATIC_DIR = Path(__file__).parent / "static"
WOL_SECRET = os.environ.get("WOL_SECRET", "cambiar-esta-clave")
RATE_LIMIT  = 10

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("wol")

# ─── Rate limiting ────────────────────────────────────────────────────────────
_rate: dict = {}
_rate_lock = threading.Lock()
def check_rate(ip):
    now = time.time()
    with _rate_lock:
        hits = [t for t in _rate.get(ip, []) if now-t < 60]
        if len(hits) >= RATE_LIMIT: return False
        hits.append(now); _rate[ip] = hits
        if len(_rate) > 1000:                       # drop stale clients so the table cannot grow forever
            for k in [k for k, v in _rate.items() if not v or now - v[-1] >= 60]:
                _rate.pop(k, None)
        return True

# ─── CSRF token ───────────────────────────────────────────────────────────────
def gen_token():
    ts = str(int(time.time()//300))
    return hmac.new(WOL_SECRET.encode(), ts.encode(), hashlib.sha256).hexdigest()[:32]

def valid_token(t):
    for d in (0,-1):
        ts = str(int(time.time()//300)+d)
        exp = hmac.new(WOL_SECRET.encode(), ts.encode(), hashlib.sha256).hexdigest()[:32]
        if hmac.compare_digest(exp, t or ""): return True
    return False

# ─── MAC validation ───────────────────────────────────────────────────────────
_MAC = re.compile(r'^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$')
def norm_mac(raw):
    raw = raw.strip()
    return raw.upper().replace("-",":") if _MAC.match(raw) else None

# ─── Broadcast IP ─────────────────────────────────────────────────────────────
def _local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except: return "127.0.0.1"

def _broadcast():
    return _local_ip().rsplit(".",1)[0] + ".255"

# ─── Ping (para verificar si ya está online) ──────────────────────────────────
_HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]{0,252}$")
def valid_host(h) -> bool:
    """IPv4 or hostname; never something that could be read as a command-line option."""
    return isinstance(h, str) and bool(_HOST_RE.match(h))

def ping_host(ip: str, timeout: float = 1.0) -> bool:
    """Retorna True si el host responde a ping."""
    if not valid_host(ip): return False
    try:
        import subprocess
        r = subprocess.run(["ping", "-c1", f"-W{int(timeout)}", "--", ip],
                           capture_output=True, timeout=timeout+1)
        return r.returncode == 0
    except Exception:
        return False

# ─── WOL ──────────────────────────────────────────────────────────────────────
def send_wol(mac, port):
    """Send a magic packet natively (no external `wakeonlan` package needed).

    It goes to the subnet broadcast of this host (assumed /24, or WOL_BROADCAST) and to
    255.255.255.255, on the device's configured UDP port.
    """
    hexmac = re.sub(r"[^0-9A-Fa-f]", "", mac)
    if len(hexmac) != 12:
        raise RuntimeError("Invalid MAC address")
    packet = b"\xff" * 6 + bytes.fromhex(hexmac) * 16
    port = int(port or 9)
    targets = [t.strip() for t in os.environ.get("WOL_BROADCAST", "").split(",") if t.strip()]
    if not targets:
        targets = [_broadcast(), "255.255.255.255"]
    sent, last_err = 0, None
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(3)
        for t in dict.fromkeys(targets):
            try:
                s.sendto(packet, (t, port)); sent += 1
            except OSError as e:
                last_err = e
    if not sent:
        raise RuntimeError(f"Could not send the magic packet: {last_err}")
    log.info(f"Magic packet → MAC={hexmac} {','.join(dict.fromkeys(targets))}:{port}")

# ─── Wake log ─────────────────────────────────────────────────────────────────
_log_lock = threading.Lock()

def load_wake_log() -> list:
    return auth.read_json(LOG_FILE, [], list)

def append_wake_log(entry: dict):
    with _log_lock:
        entries = load_wake_log()
        entries.append(entry)
        entries = entries[-500:]   # máx 500 entradas
        auth.write_json(LOG_FILE, entries, mode=0o644)

# ─── Devices ──────────────────────────────────────────────────────────────────
_dev_lock = threading.RLock()     # hold around load_devices() → modify → save_devices()

def load_devices():
    return auth.read_json(DATA_FILE, [], list)

def save_devices(devs):
    with _dev_lock:
        auth.write_json(DATA_FILE, devs, mode=0o644)

# ─── Net Monitor (shared host info) ───────────────────────────────────────────
def mac_key(raw):
    h = re.sub(r"[^0-9a-fA-F]", "", raw or "").lower()
    return h if len(h) == 12 else ""

def load_net_hosts():
    """Hosts known to Net Monitor that have a MAC, as {mac_key: info}. Empty if unavailable."""
    try:
        data = json.loads(NET_HOSTS_FILE.read_text())
    except Exception:
        return None
    if not isinstance(data, dict): return None
    out = {}
    for ip, h in data.items():
        if not isinstance(h, dict): continue
        k = mac_key(h.get("mac"))
        if not k: continue
        out[k] = {"ip": h.get("ip") or ip, "mac": norm_mac(":".join(k[i:i+2] for i in range(0, 12, 2))),
                  "name": (h.get("alias") or h.get("hostname") or "").strip(),
                  "vendor": h.get("vendor") or "", "device_type": h.get("device_type") or "other",
                  "online": bool(h.get("online"))}
    return out

def validate_device(d):
    if not isinstance(d.get("name"), str) or not d["name"].strip():
        return False, "Invalid name"
    if not isinstance(d.get("mac"), str) or not norm_mac(d["mac"]):
        return False, "Invalid MAC address"
    p = d.get("port", 9)
    if not isinstance(p, int) or not (1 <= p <= 65535):
        return False, "Invalid port"
    if d.get("tag","PC") not in ("PC","SERVER","NAS","VM","OTHER"):
        return False, "Invalid category"
    return True, ""

# ─── Health ───────────────────────────────────────────────────────────────────
def health_report(detailed=False):
    c = auth.check_common()
    c["devices"]  = auth.check_file(DATA_FILE)
    c["wake_log"] = auth.check_file(LOG_FILE)
    n = load_net_hosts()
    c["net_monitor"] = (auth.chk(auth.OK, f"{len(n)} hosts with MAC") if n is not None
                        else auth.chk(auth.WARN, "Net Monitor hosts file not readable (optional)"))
    ip = _local_ip()
    c["network"] = auth.chk(auth.OK, ip) if ip != "127.0.0.1" else auth.chk(auth.WARN, "no LAN address: magic packets will not reach the network")
    return auth.health_reply("wol", c, detailed)

# ─── HTTP Handler ─────────────────────────────────────────────────────────────
class H(BaseHTTPRequestHandler):
    timeout = 30      # a stalled client must not hold a thread forever

    def log_message(self, fmt, *a):
        if int(a[1]) >= 400: log.warning(f"{self.client_address[0]} {a[1]}")

    def _ip(self):
        fwd = self.headers.get("X-Forwarded-For")
        return fwd.split(",")[0].strip() if fwd else self.client_address[0]

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
            if n > 8192: return None
            return json.loads(self.rfile.read(n))
        except: return None

    def _tok(self):
        return auth.token_from_request(dict(self.headers),
                                       self.headers.get("Cookie",""))

    def _file(self, path, mime):
        try:
            c = Path(path).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(c)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.end_headers(); self.wfile.write(c)
        except FileNotFoundError: self._json(404, {"error": "Not found"})

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        tok  = self._tok()

        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")

        if path == "/api/version":     # public: shown in the page footer
            return self._json(200, {"version": auth.version()})
        if path == "/api/token":
            return self._json(200, {"token": gen_token()})

        if path == "/api/health":      # public: levels only; details need a valid session
            code, body = health_report(auth.get_session(tok) is not None)
            return self._json(code, body)

        if not auth.check_permission(tok, "wol", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        if path == "/api/devices":
            devs = load_devices()
            wake_log = load_wake_log()
            # Anotar last_wake por device id
            last_wake = {}
            for entry in wake_log:
                did = entry.get("device_id")
                if did and (did not in last_wake or entry["ts"] > last_wake[did]["ts"]):
                    last_wake[did] = entry
            for d in devs:
                lw = last_wake.get(d["id"])
                d["last_wake"] = lw["ts"] if lw else None
                d["last_wake_user"] = lw["user"] if lw else None
            if auth.check_permission(tok, "net", "readonly"):
                net = load_net_hosts() or {}
                for d in devs:
                    n = net.get(mac_key(d.get("mac")))
                    if n: d["net"] = {k: n[k] for k in ("ip", "name", "online", "device_type", "vendor")}
            self._json(200, {"devices": devs})

        elif path == "/api/netmonitor/hosts":
            if not auth.check_permission(tok, "net", "readonly"):
                return self._json(403, {"error": "Net Monitor permission required"})
            net = load_net_hosts()
            if net is None:
                return self._json(200, {"available": False, "hosts": []})
            have = {mac_key(d.get("mac")) for d in load_devices()}
            hosts = [{**h, "in_wol": k in have} for k, h in net.items()]
            hosts.sort(key=lambda h: (h["in_wol"], (h["name"] or h["ip"]).lower()))
            self._json(200, {"available": True, "hosts": hosts})

        elif path == "/api/wake_log":
            entries = load_wake_log()
            self._json(200, {"log": list(reversed(entries[-100:]))})

        elif path == "/api/config":
            self._json(200, {"server_host": _local_ip(), "port": PORT})

        elif path == "/api/me":
            sess = auth.get_session(tok)
            self._json(200, {"username": sess["username"],
                              "permissions": sess["permissions"]} if sess else {})
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})

        if path == "/api/login":
            u, err = auth.login(self, body.get("username",""), body.get("password",""))
            if not u: return self._json(err[0], {"error": err[1]})
            token = auth.create_session(body["username"], u["permissions"])
            users = auth.load_users()
            must  = users.get(body["username"],{}).get("must_change_password", False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie",
                f"session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400")
            br = json.dumps({"ok": True, "token": token, "username": body["username"],
                             "permissions": u["permissions"],
                             "must_change_password": must}).encode()
            self.send_header("Content-Length", str(len(br)))
            self.end_headers(); self.wfile.write(br); return

        if path == "/api/logout":
            auth.delete_session(tok); return self._json(200, {"ok": True})

        if not auth.check_permission(tok, "wol", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        if path == "/api/devices":
            if not auth.check_permission(tok, "wol", "admin"):
                return self._json(403, {"error": "Requiere permiso admin"})
            ok2, msg = validate_device(body)
            if not ok2: return self._json(400, {"error": msg})
            mac  = norm_mac(body["mac"])
            import uuid
            with _dev_lock:                       # load → modify → save must not interleave
                devs = load_devices()
                if any(d["mac"] == mac for d in devs):
                    return self._json(409, {"error": "MAC duplicada"})
                dev = {"id": str(uuid.uuid4()), "name": body["name"].strip()[:40],
                       "mac": mac, "ip": (body.get("ip") or "").strip() or None,
                       "port": int(body.get("port",9)),
                       "tag": body.get("tag","PC"), "added": int(time.time())}
                devs.append(dev); save_devices(devs)
            self._json(201, {"device": dev})

        elif path == "/api/ping":
            # Verificar si un equipo ya está online antes de despertar
            if not auth.check_permission(tok, "wol", "readonly"):
                return self._json(403, {"error": "Unauthorized"})
            ip = (body.get("ip") or "").strip()
            if not ip:
                return self._json(400, {"error": "IP requerida"})
            if not valid_host(ip):
                return self._json(400, {"error": "Invalid IP or host"})
            online = ping_host(ip)
            self._json(200, {"online": online, "ip": ip})

        elif path == "/api/wake":
            if not auth.check_permission(tok, "wol", "execute"):
                return self._json(403, {"error": "Requiere permiso execute"})
            if not check_rate(self._ip()):
                return self._json(429, {"error": "Rate limit"})
            devs = load_devices()
            dev  = next((d for d in devs if d["id"] == body.get("id")), None)
            if not dev: return self._json(404, {"error": "Dispositivo no encontrado"})

            # Verificar si ya está online
            net_h = (load_net_hosts() or {}).get(mac_key(dev.get("mac")))
            ping_ip = (net_h or {}).get("ip") or dev.get("ip") or ""   # Net Monitor IP is the freshest
            already_online = ping_host(ping_ip) if ping_ip else False
            if already_online and not body.get("force"):
                return self._json(200, {"ok": False, "already_online": True,
                                        "message": f"{dev['name']} is already on"})
            try:
                send_wol(dev["mac"], dev.get("port",9))
                sess = auth.get_session(tok)
                username = sess["username"] if sess else "?"
                # Registrar en log
                append_wake_log({
                    "ts": int(time.time()),
                    "device_id": dev["id"],
                    "device_name": dev["name"],
                    "mac": dev["mac"],
                    "user": username,
                    "already_online": already_online,
                })
                self._json(200, {"ok": True,
                                 "message": f"Paquete enviado a {dev['name']}",
                                 "already_online": already_online})
            except Exception as e:
                log.error(f"WOL error: {e}"); self._json(500, {"error": str(e)})

        elif path == "/api/wake_all":
            if not auth.check_permission(tok, "wol", "execute"):
                return self._json(403, {"error": "Requiere permiso execute"})
            devs = load_devices()
            sess = auth.get_session(tok)
            username = sess["username"] if sess else "?"
            sent = 0
            errors = []
            for dev in devs:
                try:
                    send_wol(dev["mac"], dev.get("port", 9))
                    append_wake_log({
                        "ts": int(time.time()),
                        "device_id": dev["id"],
                        "device_name": dev["name"],
                        "mac": dev["mac"],
                        "user": username,
                        "already_online": False,
                        "bulk": True,
                    })
                    sent += 1
                except Exception as e:
                    errors.append({"name": dev["name"], "error": str(e)})
            self._json(200, {"ok": True, "sent": sent, "errors": errors})

        else:
            self._json(404, {"error": "Not found"})

    def do_DELETE(self):
        path = urlparse(self.path).path
        tok  = self._tok()
        if not auth.check_permission(tok, "wol", "admin"):
            return self._json(403, {"error": "Requiere permiso admin"})
        m = re.match(r'^/api/devices/([0-9a-f\-]{36})$', path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        with _dev_lock:
            devs = load_devices()
            new  = [d for d in devs if d["id"] != m.group(1)]
            if len(new) == len(devs): return self._json(404, {"error": "No encontrado"})
            save_devices(new)
        self._json(200, {"ok": True})

if __name__ == "__main__":
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    log.info(f"WOL Console en http://{HOST}:{PORT}")
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
    except PermissionError:
        log.error(f"Sin permisos para puerto {PORT}"); sys.exit(1)
