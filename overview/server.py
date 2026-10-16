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
# Solo en una Raspberry Pi: cada PI_EVERY segundos se guarda en metrics.db (tabla pi_samples) la temperatura y los
# bits de «get_throttled». Banderas: 1 = subtensión ahora, 2 = limitada ahora, 4 = límite de temperatura ahora,
# 8 = hubo subtensión desde la muestra anterior (aunque ya no esté). Se conservan PICONSOLE_PI_KEEP_DAYS días (7 por
# defecto). En otros equipos no se crea hilo ni se escribe nada. Si queda un pi-history.json de la versión 1.2.0m/o,
# se importa una vez y se renombra a .migrated.
# EN: ─── Pi history (temperature and under-voltage) ─────────────────────────────────────
#     Raspberry Pi only: every PI_EVERY seconds the temperature and the "get_throttled" bits are stored in
#     metrics.db (table pi_samples). Flags: 1 = under-voltage now, 2 = throttled now, 4 = temperature limit now,
#     8 = there was under-voltage since the previous sample (even if gone now). PICONSOLE_PI_KEEP_DAYS days are kept
#     (7 by default). On other machines no thread is created and nothing is written. A leftover pi-history.json from
#     version 1.2.0m/o is imported once and renamed to .migrated.
PI_EVERY    = int(os.environ.get("PICONSOLE_PI_EVERY", "60"))
PI_KEEP     = auth.keep_days("PICONSOLE_PI_KEEP_DAYS", 7) * 86400
PI_LEGACY   = Path(os.environ.get("PICONSOLE_PI_HISTORY", str(auth.EVENTS_FILE.with_name("pi-history.json"))))

def pi_enabled():
    return auth._is_raspberry_pi()

def _ok_row(s, now):
    return isinstance(s, list) and len(s) == 3 and isinstance(s[0], (int, float)) and now - PI_KEEP < s[0] <= now + 60 \
        and (s[1] is None or isinstance(s[1], (int, float))) and isinstance(s[2], (int, float))

# Importa el JSON antiguo si la tabla está vacía.
# EN: Import the old JSON if the table is empty.
def pi_migrate(c):
    if not PI_LEGACY.is_file(): return
    try:
        if c.execute("SELECT 1 FROM pi_samples LIMIT 1").fetchone() is None:
            now = time.time()
            rows = [(int(s[0]), s[1], int(s[2])) for s in auth.read_json(PI_LEGACY, [], list) if _ok_row(s, now)]
            c.executemany("INSERT OR IGNORE INTO pi_samples (ts,temp,flags) VALUES (?,?,?)", rows); c.commit()
            log.info(f"Pi history: imported {len(rows)} samples from {PI_LEGACY.name}")
        PI_LEGACY.rename(PI_LEGACY.with_name(PI_LEGACY.name + ".migrated"))
    except Exception as e:
        log.warning(f"could not import the old Pi history: {e}")

# Una muestra: [hora, temperatura, banderas].
# EN: One sample: [time, temperature, flags].
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

def pi_store(s):
    c = auth.metrics_conn()
    try:
        c.execute("INSERT OR REPLACE INTO pi_samples (ts,temp,flags) VALUES (?,?,?)", tuple(s))
        c.commit()
    finally: c.close()

def pi_prune():
    c = auth.metrics_conn()
    try:
        c.execute("DELETE FROM pi_samples WHERE ts < ?", (int(time.time()) - PI_KEEP,)); c.commit()
    finally: c.close()

def pi_loop():
    since, n = None, 0
    try:
        c = auth.metrics_conn()
        try: pi_migrate(c)
        finally: c.close()
        pi_prune()
    except Exception as e:
        log.warning(f"Pi history unavailable: {e}")
    while True:
        try:
            s, since = pi_sample(since)
            pi_store(s)
            n += 1
            if n % 360 == 0: pi_prune()
        except Exception as e:
            log.warning(f"Pi sample failed: {e}")
        time.sleep(PI_EVERY)

def pi_history(hours=24):
    cut = int(time.time()) - max(1, min(PI_KEEP // 3600, hours)) * 3600
    c = auth.metrics_conn()
    try: rows = [list(r) for r in c.execute("SELECT ts,temp,flags FROM pi_samples WHERE ts >= ? ORDER BY ts", (cut,))]
    finally: c.close()
    return {"pi": True, "every": PI_EVERY, "samples": rows}


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
            if n < 0 or n > 8192: return None
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
        if auth.serve_asset(self, STATIC_DIR, path): return   # .js / .css de la página

        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if path == "/api/version":
            return self._json(200, {"version": auth.version()} if (auth.get_session(tok) or auth.is_local_request(self)) else {})
        if path == "/api/health":
            code, body = health_report(auth.health_mode(self, tok))
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
            try: return self._json(200, pi_history(hours))
            except Exception as e:
                log.warning(f"Pi history unavailable: {e}"); return self._json(200, {"pi": True, "every": PI_EVERY, "samples": []})

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
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})
        if path == "/api/login":
            u, err = auth.login(self, body.get("username", ""), body.get("password", ""))
            if not u: return self._json(err[0], {"error": err[1]})
            token = auth.create_session(body["username"], u["permissions"])
            must  = auth.load_users().get(body["username"], {}).get("must_change_password", False)
            return self._json(200, {"ok": True, "username": body["username"],
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
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
