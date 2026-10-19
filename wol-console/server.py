#!/usr/bin/env python3
"""WOL Console — Backend con auth compartido."""
# WOL Console (puerto 8080): lista de equipos y envío de «magic packets» Wake-on-LAN.
#
# Cómo funciona un magic packet: un datagrama UDP de broadcast con 6 bytes 0xFF seguidos de la MAC
# del equipo repetida 16 veces. La tarjeta de red del equipo apagado lo reconoce y enciende la placa.
#
# Estructura del archivo:
#   · utilidades (límite de tasa, validación de MAC, broadcast, ping)
#   · envío del paquete y registro de encendidos (wake_log.json)
#   · lista de equipos (devices.json) y datos compartidos con Net Monitor
#   · salud (/api/health) y manejador HTTP (GET, POST, DELETE)
# EN: WOL Console (port 8080): device list and sending Wake-on-LAN "magic packets".
#
#     How a magic packet works: a broadcast UDP datagram with 6 bytes of 0xFF followed by the device's
#     MAC repeated 16 times. The network card of the powered-off device recognises it and switches the board on.
#
#     File structure:
#       · utilities (rate limit, MAC validation, broadcast, ping)
#       · packet sending and wake log (wake_log.json)
#       · device list (devices.json) and data shared with Net Monitor
#       · health (/api/health) and HTTP handler (GET, POST, DELETE)
import json, os, socket, re, sys, time, logging, hashlib, hmac, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128      # default is 5: a burst of simultaneous connections got reset
from urllib.parse import urlparse
from pathlib import Path

# El módulo compartido de autenticación está en la carpeta hermana /auth.
# EN: The shared authentication module is in the sibling folder /auth.
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

# Configuración y rutas de datos. HOST es solo loopback: el acceso desde la red pasa por nginx.
# EN: Configuration and data paths. HOST is loopback only: network access goes through nginx.
PORT       = 8080
HOST       = "127.0.0.1"
# Los datos viven en /var/lib/pi-console/wol-console (el código de /opt es de solo lectura para el servicio).
# EN: The data lives in /var/lib/pi-console/wol-console (the code in /opt is read-only for the service).
DATA_DIR   = auth.module_data("wol-console")
auth.adopt_legacy(Path(__file__).parent, DATA_DIR, ("devices.json", "wake_log.json"))
DATA_FILE  = DATA_DIR / "devices.json"
LOG_FILE   = DATA_DIR / "wake_log.json"
# Net Monitor host table (shared info: MAC, IP, name, type). Read-only here.
# Tabla de hosts de Net Monitor (solo lectura aquí): permite autocompletar equipos y mostrar si están en línea.
# EN: Net Monitor host table (read-only here): lets devices be autocompleted and shows whether they are online.
NET_HOSTS_FILE = Path(os.environ.get("NET_HOSTS_FILE", str(auth.DATA_ROOT / "net-monitor" / "hosts.json")))
STATIC_DIR = Path(__file__).parent / "static"
# Máximo de encendidos por minuto y por IP (evita que un cliente descontrolado inunde la red con paquetes).
# EN: Maximum wake-ups per minute and per IP (stops a runaway client from flooding the network with packets).
RATE_LIMIT  = 10

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("wol")

# ─── Rate limiting ────────────────────────────────────────────────────────────
# Contadores de encendidos recientes por IP.
# EN: Counters of recent wake-ups per IP.
_rate: dict = {}
_rate_lock = threading.Lock()
# True si la IP aún puede encender equipos este minuto. Registra el intento y limpia clientes viejos para que la tabla no crezca.
# EN: True if the IP can still wake devices this minute. Records the attempt and cleans old clients so the table does not grow.
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

# ─── MAC validation ───────────────────────────────────────────────────────────
# MAC válida: 6 pares hexadecimales separados por «:» o «-».
# EN: Valid MAC: 6 hexadecimal pairs separated by ":" or "-".
_MAC = re.compile(r'^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$')
# Normaliza a MAYÚSCULAS con «:»; devuelve None si no es una MAC válida.
# EN: Normalise to UPPERCASE with ":"; returns None if it is not a valid MAC.
def norm_mac(raw):
    raw = raw.strip()
    return raw.upper().replace("-",":") if _MAC.match(raw) else None

# ─── Broadcast IP ─────────────────────────────────────────────────────────────
# IP de este equipo en la LAN: se abre un socket UDP hacia afuera (sin enviar nada) y se lee la IP de origen que eligió el sistema.
# EN: This machine's LAN IP: a UDP socket is opened outwards (nothing is sent) and the source IP chosen by the system is read.
def _local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except OSError: return "127.0.0.1"

# Dirección de broadcast de la subred, suponiendo /24 (x.x.x.255). Se puede forzar con WOL_BROADCAST.
# EN: Broadcast address of the subnet, assuming /24 (x.x.x.255). Can be forced with WOL_BROADCAST.
def _broadcast():
    return _local_ip().rsplit(".",1)[0] + ".255"

# ─── Ping (para verificar si ya está online) ──────────────────────────────────
# Host permitido para hacer ping: debe empezar con letra o número, así nunca se interpreta como opción de línea de comandos.
# EN: Host allowed for ping: must start with a letter or digit, so it is never interpreted as a command-line option.
_HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]{0,252}$")
# True si el texto es una IP o nombre de host razonable.
# EN: True if the text is a reasonable IP or host name.
def valid_host(h) -> bool:
    """IPv4 or hostname; never something that could be read as a command-line option."""
    return isinstance(h, str) and bool(_HOST_RE.match(h))

# Un solo ping con tiempo límite. Se usa para saber si un equipo ya está encendido antes de despertarlo.
# EN: A single ping with a timeout. Used to know whether a device is already on before waking it.
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
# Arma y envía el magic packet sin dependencias externas. Se manda al broadcast de la subred y a 255.255.255.255 por el
# puerto UDP del equipo (normalmente 9). Falla solo si NO se pudo enviar a ningún destino.
# EN: Build and send the magic packet with no external dependencies. It goes to the subnet broadcast and to 255.255.255.255 on
#     the device's UDP port (normally 9). Fails only if it could NOT be sent to any destination.
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
# El registro de encendidos guarda las últimas 500 entradas; el candado evita que dos hilos lo escriban a la vez.
# EN: The wake log keeps the last 500 entries; the lock stops two threads from writing it at once.
_log_lock = threading.Lock()

# Lee wake_log.json (con la red de seguridad de auth.read_json).
# EN: Read wake_log.json (with the safety net of auth.read_json).
def load_wake_log() -> list:
    return auth.read_json(LOG_FILE, [], list)

# Agrega una entrada y conserva solo las últimas 500.
# EN: Add an entry and keep only the last 500.
def append_wake_log(entry: dict):
    with _log_lock:
        entries = load_wake_log()
        entries.append(entry)
        entries = entries[-500:]   # máx 500 entradas
        auth.write_json(LOG_FILE, entries, mode=0o644)

# ─── Devices ──────────────────────────────────────────────────────────────────
# Candado de la lista de equipos. Regla: cargar → modificar → guardar siempre dentro de este candado.
# EN: Lock of the device list. Rule: load → modify → save always inside this lock.
_dev_lock = threading.RLock()     # hold around load_devices() → modify → save_devices()

# Lee devices.json (lista vacía si no existe).
# EN: Read devices.json (empty list if missing).
def load_devices():
    return auth.read_json(DATA_FILE, [], list)

# Guarda la lista de equipos de forma atómica.
# EN: Save the device list atomically.
def save_devices(devs):
    with _dev_lock:
        auth.write_json(DATA_FILE, devs, mode=0o644)

# ─── Net Monitor (shared host info) ───────────────────────────────────────────
# MAC reducida a 12 dígitos hexadecimales en minúscula, sirve de clave para cruzar equipos con hosts de Net Monitor.
# EN: MAC reduced to 12 lowercase hex digits; used as the key to match devices with Net Monitor hosts.
def mac_key(raw):
    h = re.sub(r"[^0-9a-fA-F]", "", raw or "").lower()
    return h if len(h) == 12 else ""

# Hosts de Net Monitor que tienen MAC, indexados por mac_key, con nombre, IP, fabricante, tipo y si están en línea.
# Devuelve None si el archivo no está disponible (Net Monitor es opcional).
# EN: Net Monitor hosts that have a MAC, indexed by mac_key, with name, IP, vendor, type and whether they are online.
#     Returns None if the file is not available (Net Monitor is optional).
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

# Valida un equipo nuevo: nombre no vacío, MAC válida, puerto 1-65535 y categoría conocida. Devuelve (ok, mensaje).
# EN: Validate a new device: non-empty name, valid MAC, port 1-65535 and known category. Returns (ok, message).
def validate_device(d):
    if not isinstance(d.get("name"), str) or not d["name"].strip() or re.search(r"[\x00-\x1f\x7f]", d["name"]):
        return False, "Invalid name"
    if d.get("notes") not in (None, "") and (not isinstance(d["notes"], str) or re.search(r"[\x00-\x1f\x7f]", d["notes"])):
        return False, "Invalid notes"
    if not isinstance(d.get("mac"), str) or not norm_mac(d["mac"]):
        return False, "Invalid MAC address"
    p = d.get("port", 9)
    if not isinstance(p, int) or not (1 <= p <= 65535):
        return False, "Invalid port"
    if d.get("tag","PC") not in ("PC","SERVER","NAS","VM","OTHER"):
        return False, "Invalid category"
    ip = d.get("ip")
    if ip not in (None, "") and not (isinstance(ip, str) and valid_host(ip.strip())):
        return False, "Invalid IP or host"
    return True, ""

# ─── Health ───────────────────────────────────────────────────────────────────
# Chequeos de salud de WOL: archivos de datos, tabla de Net Monitor (opcional) y que la máquina tenga una IP de LAN.
# EN: WOL health checks: data files, Net Monitor table (optional) and that the machine has a LAN IP.
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
# Manejador HTTP. Cada petición se atiende en su propio hilo.
# EN: HTTP handler. Each request is served in its own thread.
class H(BaseHTTPRequestHandler):
    timeout = 30      # a stalled client must not hold a thread forever

    def log_message(self, fmt, *a):
        if int(a[1]) >= 400: log.warning(f"{self.client_address[0]} {a[1]}")

    # IP del cliente para el límite de encendidos. Usa auth.client_ip (X-Real-IP de nginx, solo si la conexión es local): X-Forwarded-For lo puede falsear el cliente.
    # EN: Client IP for the wake-up limit. Uses auth.client_ip (nginx's X-Real-IP, only if the connection is local): X-Forwarded-For can be forged by the client.
    def _ip(self):
        return auth.client_ip(self)

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
            return json.loads(self.rfile.read(n))
        except (ValueError, TypeError, OSError): return None

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

    # GET: la página es pública (versión y salud solo con sesión o desde esta máquina); el resto exige sesión con WOL «readonly».
    # Rutas: /api/devices, /api/netmonitor/hosts, /api/wake_log, /api/config, /api/me.
    # EN: GET: the page is public (version and health only with a session or from this machine); the rest requires a session with WOL "readonly".
    #     Routes: /api/devices, /api/netmonitor/hosts, /api/wake_log, /api/config, /api/me.
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        tok  = self._tok()
        if auth.serve_asset(self, STATIC_DIR, path): return   # .js / .css de la página

        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")

        if path == "/api/version":     # shown in the page footer; only with a session (or from this machine)
            return self._json(200, {"version": auth.version()} if (auth.get_session(tok) or auth.is_local_request(self)) else {})
        if path == "/api/health":      # public: levels only; details need a valid session
            code, body = health_report(auth.health_mode(self, tok))
            return self._json(code, body)

        if not auth.check_permission(tok, "wol", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        # Lista de equipos. A cada uno se le agrega cuándo y quién lo despertó por última vez (desde wake_log) y,
        # si el usuario tiene permiso de Net Monitor, su estado de red.
        # EN: Device list. Each one gets when and by whom it was last woken (from wake_log) and,
        #     if the user has Net Monitor permission, its network state.
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

        # Hosts de Net Monitor para agregarlos como equipos WOL; marca cuáles ya están en la lista.
        # EN: Net Monitor hosts to add them as WOL devices; marks which are already in the list.
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

        # Últimos 100 encendidos, del más reciente al más antiguo.
        # EN: Last 100 wake-ups, newest first.
        elif path == "/api/wake_log":
            entries = load_wake_log()
            self._json(200, {"log": list(reversed(entries[-100:]))})

        # Datos que la página muestra en el instructivo (IP y puerto del servidor).
        # EN: Data the page shows in the help section (server IP and port).
        elif path == "/api/config":
            self._json(200, {"server_host": _local_ip(), "port": PORT})

        elif path == "/api/me":
            sess = auth.get_session(tok)
            self._json(200, {"username": sess["username"],
                              "permissions": sess["permissions"]} if sess else {})
        else:
            self._json(404, {"error": "Not found"})

    # POST: login/logout, alta de equipos, ping, encendido de uno y encendido de todos.
    # Orden: login (público) → exigir sesión → rutas protegidas según el nivel necesario.
    # EN: POST: login/logout, add device, ping, wake one and wake all.
    #     Order: login (public) → require a session → protected routes according to the level needed.
    def do_POST(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})

        # Login con límite de intentos (auth.login); la cookie es HttpOnly y SameSite=Strict.
        # EN: Login with attempt limiting (auth.login); the cookie is HttpOnly and SameSite=Strict.
        if path == "/api/login":
            u, err = auth.login(self, body.get("username",""), body.get("password",""))
            if not u: return self._json(err[0], {"error": err[1]})
            ttl = auth.remember_ttl(body.get("remember"))     # «Recordarme»: solo valores de la lista blanca / EN: only whitelisted values
            token = auth.create_session(body["username"], u["permissions"], ttl, self)
            users = auth.load_users()
            must  = users.get(body["username"],{}).get("must_change_password", False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie",
                auth.session_cookie(token, ttl))
            br = json.dumps({"ok": True, "username": body["username"],
                             "permissions": u["permissions"],
                             "must_change_password": must}).encode()
            self.send_header("Content-Length", str(len(br)))
            self.end_headers(); self.wfile.write(br); return

        if path == "/api/logout":
            auth.delete_session(tok); return self._json(200, {"ok": True})

        if not auth.check_permission(tok, "wol", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        # Alta de equipo (solo admin): valida, normaliza la MAC y rechaza duplicados. Bajo el candado para no pisar cambios.
        # EN: Add a device (admin only): validates, normalises the MAC and rejects duplicates. Under the lock so changes are not overwritten.
        if path == "/api/devices":
            if not auth.check_permission(tok, "wol", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            ok2, msg = validate_device(body)
            if not ok2: return self._json(400, {"error": msg})
            mac  = norm_mac(body["mac"])
            import uuid
            with _dev_lock:                       # load → modify → save must not interleave
                devs = load_devices()
                if any(d["mac"] == mac for d in devs):
                    return self._json(409, {"error": "Duplicate MAC"})
                dev = {"id": str(uuid.uuid4()), "name": body["name"].strip()[:40],
                       "mac": mac, "ip": (body.get("ip") or "").strip() or None,
                       "port": int(body.get("port",9)),
                       "tag": body.get("tag","PC"), "added": int(time.time())}
                devs.append(dev); save_devices(devs)
            self._json(201, {"device": dev})

        # Comprueba si un equipo ya está en línea (cualquier usuario con acceso a WOL).
        # EN: Check whether a device is already online (any user with WOL access).
        elif path == "/api/ping":
            # Verificar si un equipo ya está online antes de despertar
            if not auth.check_permission(tok, "wol", "readonly"):
                return self._json(403, {"error": "Unauthorized"})
            ip = (body.get("ip") or "").strip()
            if not ip:
                return self._json(400, {"error": "IP required"})
            if not valid_host(ip):
                return self._json(400, {"error": "Invalid IP or host"})
            online = ping_host(ip)
            self._json(200, {"online": online, "ip": ip})

        # Despierta un equipo (permiso «execute», con límite por IP). Si ya responde a ping avisa y no envía, salvo que
        # llegue force=true. La IP de Net Monitor tiene prioridad porque es la más reciente. Cada envío queda en el registro.
        # EN: Wake a device ("execute" permission, with a per-IP limit). If it already answers ping it warns and does not send, unless
        #     force=true arrives. The Net Monitor IP takes priority because it is the most recent. Every send is logged.
        elif path == "/api/wake":
            if not auth.check_permission(tok, "wol", "execute"):
                return self._json(403, {"error": "Execute permission required"})
            if not check_rate(self._ip()):
                return self._json(429, {"error": "Rate limit"})
            devs = load_devices()
            dev  = next((d for d in devs if d["id"] == body.get("id")), None)
            if not dev: return self._json(404, {"error": "Device not found"})

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
                                 "message": f"Magic packet sent to {dev['name']}",
                                 "already_online": already_online})
            except Exception as e:
                log.error(f"WOL error: {e}"); self._json(500, {"error": str(e)})

        # Despierta todos los equipos de la lista; devuelve cuántos se enviaron y los errores por equipo.
        # EN: Wake every device in the list; returns how many were sent and the errors per device.
        elif path == "/api/wake_all":
            if not auth.check_permission(tok, "wol", "execute"):
                return self._json(403, {"error": "Execute permission required"})
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

    # DELETE /api/devices/<id>: elimina un equipo (solo admin). El id debe ser un UUID.
    # EN: DELETE /api/devices/<id>: remove a device (admin only). The id must be a UUID.
    def do_DELETE(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path
        tok  = self._tok()
        if not auth.check_permission(tok, "wol", "admin"):
            return self._json(403, {"error": "Admin permission required"})
        m = re.match(r'^/api/devices/([0-9a-f\-]{36})$', path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        with _dev_lock:
            devs = load_devices()
            new  = [d for d in devs if d["id"] != m.group(1)]
            if len(new) == len(devs): return self._json(404, {"error": "Not found"})
            save_devices(new)
        self._json(200, {"ok": True})

# Arranque del servidor en loopback, un hilo por petición; Ctrl-C termina limpio.
# EN: Start the server on loopback, one thread per request; Ctrl-C ends cleanly.
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
