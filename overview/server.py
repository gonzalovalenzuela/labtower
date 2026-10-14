#!/usr/bin/env python3
"""
Overview — resumen de UPS, Proxmox, red y la Pi / Overview of UPS, Proxmox, network and the Pi
"""
# Resumen (puerto 8085): una sola página con lo más importante de UPS Monitor, Proxmox Monitor y Net Monitor,
# más el estado de la Raspberry Pi y una línea de tiempo de eventos. La página consulta directamente las APIs de
# los otros módulos (con la misma sesión); este servicio solo aporta lo que ellos no tienen:
#   /api/system  → temperatura, CPU, memoria, disco y tiempo encendido de la Pi
#   /api/events  → línea de tiempo (los módulos anotan sus cambios de estado con auth.record_event)
# Estructura: salud · HTTP (GET/POST) · arranque.
# EN: Overview (port 8085): a single page with the key points of UPS Monitor, Proxmox Monitor and Net Monitor,
#     plus the Raspberry Pi status and an event timeline. The page queries the other modules' APIs directly (with
#     the same session); this service only adds what they do not have:
#       /api/system  → temperature, CPU, memory, disk and uptime of the Pi
#       /api/events  → timeline (modules record their state changes with auth.record_event)
#     Structure: health · HTTP (GET/POST) · startup.
import json, os, sys, logging, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Módulo compartido de autenticación (carpeta hermana /auth).
# EN: Shared authentication module (sibling folder /auth).
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

logging.basicConfig(level=logging.INFO, format="%(asctime)s [overview] %(message)s")
log = logging.getLogger("overview")

# Solo loopback; el acceso desde la red pasa por nginx.
# EN: Loopback only; network access goes through nginx.
HOST       = "127.0.0.1"
PORT       = 8085
STATIC_DIR = Path(__file__).parent / "static"

# Qué permiso hace falta para ver los eventos de cada módulo.
# EN: Which permission is needed to see each module's events.
EVENT_MODULES = ("nut", "net", "pve")


# ─── Historial de la Pi (temperatura y bajo voltaje) ─────────────────────────────────────
# Solo en una Raspberry Pi: cada PI_EVERY segundos se anota la temperatura y los bits de «get_throttled».
# Cada muestra es [hora, temperatura, banderas]; banderas: 1 = subtensión ahora, 2 = limitada ahora,
# 4 = límite de temperatura ahora, 8 = hubo subtensión desde la muestra anterior (aunque ya no esté).
# Se guardan 24 h y se escriben a disco cada PI_SAVE_EVERY muestras (y al cerrar) para no gastar la SD;
# al reiniciar el servicio se retoma lo guardado. En otros equipos no se crea hilo ni archivo.
# EN: ─── Pi history (temperature and under-voltage) ─────────────────────────────────────
#     Raspberry Pi only: every PI_EVERY seconds the temperature and the "get_throttled" bits are recorded.
#     Each sample is [time, temperature, flags]; flags: 1 = under-voltage now, 2 = throttled now,
#     4 = temperature limit now, 8 = there was under-voltage since the previous sample (even if gone now).
#     24 h are kept and written to disk every PI_SAVE_EVERY samples (and on exit) to spare the SD card;
#     when the service restarts it resumes from what was saved. On other machines no thread or file is created.
PI_EVERY      = int(os.environ.get("PICONSOLE_PI_EVERY", "60"))
PI_KEEP       = 24 * 3600
PI_SAVE_EVERY = 10
PI_FILE       = Path(os.environ.get("PICONSOLE_PI_HISTORY", str(auth.EVENTS_FILE.with_name("pi-history.json"))))
_pi_samples   = []
_pi_lock      = threading.Lock()

def pi_enabled():
    return auth._is_raspberry_pi()

def pi_load():
    data = auth.read_json(PI_FILE, [], list)
    now = time.time()
    ok = []
    for s in data:
        if isinstance(s, list) and len(s) == 3 and all(isinstance(x, (int, float)) or x is None for x in s) \
                and s[0] and now - PI_KEEP < s[0] <= now + 60:
            ok.append(s)
    with _pi_lock: _pi_samples[:] = ok

def pi_save():
    with _pi_lock: snap = list(_pi_samples)
    try: auth.write_json(PI_FILE, snap, indent=None)
    except Exception as e: log.warning(f"could not save the Pi history: {e}")

# Una muestra: temperatura y banderas de alimentación.
# EN: One sample: temperature and power flags.
def pi_sample(prev_since):
    st = auth.system_stats()
    bits = auth._read_throttled()
    flags, since = 0, prev_since
    if bits is not None:
        if bits & 0x1: flags |= 1
        if bits & 0x4: flags |= 2
        if bits & 0x8: flags |= 4
        since = bool(bits & 0x10000)
        if since and prev_since is False and not (bits & 0x1): flags |= 8      # new under-voltage between two samples
    return [int(time.time()), st.get("temp"), flags], since

def pi_loop():
    pi_load()
    since, n = None, 0
    while True:
        try:
            s, since = pi_sample(since)
            cut = time.time() - PI_KEEP
            with _pi_lock:
                _pi_samples.append(s)
                while _pi_samples and _pi_samples[0][0] < cut: _pi_samples.pop(0)
            n += 1
            if n % PI_SAVE_EVERY == 0: pi_save()
        except Exception as e:
            log.warning(f"Pi sample failed: {e}")
        time.sleep(PI_EVERY)

def pi_history(hours=24):
    cut = time.time() - max(1, min(24, hours)) * 3600
    with _pi_lock: s = [x for x in _pi_samples if x[0] >= cut]
    return {"pi": True, "every": PI_EVERY, "samples": s}


# ─── Salud ───────────────────────────────────────────────────────────────────
# Chequeos comunes (usuarios, sesiones, disco) y que el archivo de eventos se pueda leer y escribir.
# EN: ─── Health ──────────────────────────────────────────────────────────────
#     Common checks (users, sessions, disk) and that the events file is readable and writable.
def health_report(detailed=False):
    c = auth.check_common()
    c["events"] = auth.check_file(auth.EVENTS_FILE)
    return auth.health_reply("overview", c, detailed)


# ─── HTTP Handler ────────────────────────────────────────────────────────────
# Manejador HTTP. Cada petición se atiende en su propio hilo.
# EN: HTTP handler. Each request is served in its own thread.
class H(BaseHTTPRequestHandler):
    timeout = 30
    def log_message(self, fmt, *a):
        if int(a[1]) >= 400: log.warning(f"{self.client_address[0]} {a[1]}")

    def _json(self, code, payload, extra_headers=()):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra_headers: self.send_header(k, v)
        self.end_headers(); self.wfile.write(body)

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > 8192: return None
            return json.loads(self.rfile.read(n))
        except Exception: return None

    def _tok(self):
        return auth.token_from_request(dict(self.headers), self.headers.get("Cookie", ""))

    def _file(self, path, mime):
        try:
            c = Path(path).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(c)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.end_headers(); self.wfile.write(c)
        except FileNotFoundError: self._json(404, {"error": "Not found"})

    # GET: página, versión y salud son públicos; /api/system, /api/events y /api/me piden sesión.
    # EN: GET: page, version and health are public; /api/system, /api/events and /api/me need a session.
    def do_GET(self):
        u = urlparse(self.path); path = u.path.rstrip("/") or "/"
        tok = self._tok()
        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if path == "/api/version":
            return self._json(200, {"version": auth.version()})
        if path == "/api/health":
            code, body = health_report(auth.get_session(tok) is not None)
            return self._json(code, body)
        sess = auth.get_session(tok)
        if path == "/api/me":
            return self._json(200, {"username": sess["username"], "permissions": sess["permissions"]} if sess else {})
        if not sess:
            return self._json(401, {"error": "Unauthorized"})

        if path == "/api/system":
            return self._json(200, auth.system_stats())

        # Historial de temperatura y subtensión: solo existe en una Raspberry Pi.
        # EN: Temperature and under-voltage history: it exists only on a Raspberry Pi.
        if path == "/api/pihistory":
            if not pi_enabled(): return self._json(200, {"pi": False, "samples": []})
            try: hours = int(parse_qs(u.query).get("hours", ["24"])[0])
            except ValueError: hours = 24
            return self._json(200, pi_history(hours))

        # Eventos: solo los de módulos sobre los que el usuario tiene al menos «solo lectura».
        # EN: Events: only those of modules where the user has at least "readonly".
        if path == "/api/events":
            try: limit = max(1, min(200, int(parse_qs(u.query).get("limit", ["60"])[0])))
            except ValueError: limit = 60
            allowed = [m for m in EVENT_MODULES if auth.LEVELS.get(sess["permissions"].get(m, ""), 0) >= auth.LEVELS["readonly"]]
            return self._json(200, {"events": auth.read_events(allowed, limit)})
        self._json(404, {"error": "Not found"})

    # POST: login y logout (mismo comportamiento que en los otros módulos).
    # EN: POST: login and logout (same behaviour as in the other modules).
    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})
        if path == "/api/login":
            u, err = auth.login(self, body.get("username", ""), body.get("password", ""))
            if not u: return self._json(err[0], {"error": err[1]})
            token = auth.create_session(body["username"], u["permissions"])
            must  = auth.load_users().get(body["username"], {}).get("must_change_password", False)
            return self._json(200, {"ok": True, "token": token, "username": body["username"],
                                    "permissions": u["permissions"], "must_change_password": must},
                              [("Set-Cookie", auth.session_cookie(token))])
        if path == "/api/logout":
            auth.delete_session(tok); return self._json(200, {"ok": True})
        self._json(404, {"error": "Not found"})


# Arranque: sirve en loopback.
# EN: Startup: serves on loopback.
if __name__ == "__main__":
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    auth.system_stats()           # primes the CPU counter so the first reading is meaningful
    if pi_enabled():
        threading.Thread(target=pi_loop, daemon=True, name="pi-history").start()
    log.info(f"Overview en http://{HOST}:{PORT}")
    import signal
    def _bye(*_):
        if pi_enabled(): pi_save()
        os._exit(0)
    signal.signal(signal.SIGTERM, _bye)
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: _bye()
