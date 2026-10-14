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
import json, os, sys, logging
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
    log.info(f"Overview en http://{HOST}:{PORT}")
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
