#!/usr/bin/env python3
"""Panel de administración de usuarios — corre en puerto 8082."""
# Admin Panel (puerto 8082): gestión de usuarios y permisos, respaldos (teleporter) y vista de salud
# de todos los módulos. Solo entran usuarios con nivel «admin» en WOL o UPS.
#
# Estructura del archivo:
#   · helpers de salud  → consulta /api/health de cada módulo y arma el resumen
#   · clase H           → manejador HTTP: do_GET, do_POST, do_PUT y do_DELETE
#   · bloque final      → migración de permisos y arranque del servidor
# EN: Admin Panel (port 8082): user and permission management, backups (teleporter) and the health view
#     of every module. Only users with the "admin" level in WOL or UPS can enter.
#
#     File structure:
#       · health helpers  → queries each module's /api/health and builds the summary
#       · class H         → HTTP handler: do_GET, do_POST, do_PUT and do_DELETE
#       · final block     → permission migration and server startup
import json, sys, time, logging, re
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128      # default is 5: a burst of simultaneous connections got reset
from urllib.parse import urlparse
from pathlib import Path

# El módulo auth vive en la misma carpeta; se agrega al path para poder importarlo al ejecutar el script directamente.
# EN: The auth module lives in the same folder; it is added to the path so it can be imported when the script is run directly.
sys.path.insert(0, str(Path(__file__).parent))
import auth
import teleporter_api as tp

# Solo escucha en loopback: el acceso desde la red pasa por nginx (puerto 80), que es quien aplica cabeceras de seguridad.
# EN: Listens on loopback only: network access goes through nginx (port 80), which applies the security headers.
HOST = "127.0.0.1"
PORT = 8082
STATIC_DIR = Path(__file__).parent / "static"

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("admin")

# Niveles de permiso aceptados al crear o editar usuarios («none» = sin acceso al módulo).
# EN: Permission levels accepted when creating or editing users ("none" = no access to the module).
VALID_PERMS = ("readonly", "execute", "admin", "none")
PERM_KEYS = ("wol", "nut", "net", "pve")          # one explicit level per module

# ─── Health (aggregate of every module) ───────────────────────────────────────
# Puertos de los otros servicios, usados para consultar su /api/health.
# EN: Ports of the other services, used to query their /api/health.
MODULES = {"wol": 8080, "nut": 8081, "net": 8083, "pve": 8084}

# Pregunta a un módulo cómo está. Devuelve su informe JSON o None si no responde. Un 503 también trae
# informe (significa «hay un fallo grave»), por eso se lee igual.
# EN: Ask a module how it is doing. Returns its JSON report or None if it does not answer. A 503 also carries a
#     report (it means "there is a serious failure"), so it is read as well.
def _module_health(name, port, tok):
    import urllib.request, urllib.error
    hdr = {"Authorization": f"Bearer {tok}"} if tok else {}
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/health", headers=hdr)
        with urllib.request.urlopen(req, timeout=4) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:              # 503 still carries the report
        try: return json.loads(e.read())
        except Exception: return None
    except Exception:
        return None

# Resumen de salud del sistema: chequeos propios (usuarios, sesiones, disco, respaldo, fuente de la Pi)
# más el estado de cada módulo. Sin sesión de admin solo se devuelven niveles, sin detalle.
# EN: System health summary: own checks (users, sessions, disk, backup, Pi power supply) plus the status of each
#     module. Without an admin session only levels are returned, without details.
def health_report(tok, detailed=False):
    c = auth.check_common()
    c["teleporter"] = (auth.chk(auth.OK) if tp.available()
                       else auth.chk(auth.WARN, "teleporter.sh not installed"))
    pw = auth.check_power()                       # Raspberry Pi only: absent on VMs and other hardware
    if pw: c["power"] = pw
    modules = {}
    for name, port in MODULES.items():
        h = _module_health(name, port, tok)
        if h is None:
            c[name] = auth.chk(auth.FAIL, f"service on :{port} not answering")
        else:
            lvl = {"ok": auth.OK, "degraded": auth.WARN}.get(h.get("status"), auth.FAIL)
            bad = [k for k, v in h.get("checks", {}).items() if v.get("level") != auth.OK]
            c[name] = auth.chk(lvl, ", ".join(bad) if bad else "")
            modules[name] = h
    code, body = auth.health_reply("admin", c, detailed, extra={"modules": modules})
    if not detailed: body["modules"] = {k: {"status": v.get("status")} for k, v in modules.items()}
    return code, body

# Manejador HTTP del panel. Cada petición corre en su propio hilo (ThreadingHTTPServer).
# EN: HTTP handler of the panel. Each request runs in its own thread (ThreadingHTTPServer).
class H(BaseHTTPRequestHandler):
    timeout = 60      # a stalled client must not hold a thread forever

    # Solo se registran las respuestas de error (código ≥ 400) para no llenar el journal.
    # EN: Only error responses (code ≥ 400) are logged, so the journal does not fill up.
    def log_message(self, fmt, *a):
        if int(a[1]) >= 400: log.warning(f"{self.client_address[0]} {a[1]}")

    # Responde JSON con el código dado; Cache-Control: no-store evita que el navegador guarde datos sensibles.
    # EN: Reply with JSON and the given code; Cache-Control: no-store keeps the browser from storing sensitive data.
    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(body)

    # Lee y parsea el cuerpo JSON. Devuelve None si es inválido o pesa más de 8 KB (protección contra abusos).
    # EN: Read and parse the JSON body. Returns None if invalid or larger than 8 KB (abuse protection).
    def _body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > 8192: return None
            return json.loads(self.rfile.read(n))
        except: return None

    # Token de sesión de la petición, desde la cabecera Authorization o la cookie.
    # EN: Session token of the request, from the Authorization header or the cookie.
    def _tok(self):
        return auth.token_from_request(dict(self.headers),
                                       self.headers.get("Cookie",""))

    # Sirve un archivo estático sin caché, para que el navegador siempre cargue la versión instalada.
    # EN: Serve a static file without caching, so the browser always loads the installed version.
    def _file(self, path, mime):
        try:
            c = Path(path).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(c)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.end_headers(); self.wfile.write(c)
        except FileNotFoundError:
            self._json(404, {"error": "Not found"})

    # ¿La sesión es administradora de WOL o de UPS? Es el criterio de acceso a todo el panel.
    # EN: Is the session an admin of WOL or UPS? This is the access criterion for the whole panel.
    def _is_admin(self, tok):
        return auth.check_permission(tok, "wol", "admin") or auth.check_permission(tok, "nut", "admin")

    # Nombre del usuario de la sesión (cadena vacía si no hay sesión).
    # EN: Username of the session (empty string if there is no session).
    def _me(self, tok):
        sess = auth.get_session(tok)
        return sess["username"] if sess else ""

    # Descarga de un respaldo: se envía por bloques de 1 MB para no cargar el archivo completo en memoria.
    # EN: Backup download: sent in 1 MB blocks so the whole file is never loaded into memory.
    def _tp_download(self, name):
        p = tp.path_of(name)
        if not p: return self._json(404, {"error": "Backup not found"})
        size = p.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", "application/gzip")
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition", f'attachment; filename="{name}"')
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with open(p, "rb") as f:
            while True:
                chunk = f.read(1 << 20)
                if not chunk: break
                self.wfile.write(chunk)

    # Subida de un respaldo: valida el tamaño máximo antes de leer y delega el guardado seguro a teleporter_api.
    # EN: Backup upload: checks the maximum size before reading and delegates the safe saving to teleporter_api.
    def _tp_upload(self, tok):
        if not self._is_admin(tok): return self._json(401, {"error": "Unauthorized"})
        try: length = int(self.headers.get("Content-Length", 0))
        except ValueError: length = 0
        if length > tp.MAX_UPLOAD:
            return self._json(413, {"error": f"File too large (limit {tp.MAX_UPLOAD // (1024*1024)} MB)"})
        name, err = tp.save_upload(self.rfile, length)
        if err: return self._json(400, {"error": err})
        log.info(f"Backup uploaded: {name} by {self._me(tok)}")
        self._json(201, {"ok": True, "name": name})

    # GET: página, versión y salud son públicas (la salud sin detalle). Todo lo demás exige ser admin.
    # Rutas: /api/teleporter, /api/teleporter/download/<archivo>, /api/users, /api/me.
    # EN: GET: page, version and health are public (health without details). Everything else requires admin.
    #     Routes: /api/teleporter, /api/teleporter/download/<file>, /api/users, /api/me.
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        tok  = self._tok()

        # La página de administración es pública; los datos no (se piden con la sesión).
        # EN: The admin page is public; the data is not (it is requested with the session).
        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")

        # Pantalla de cambio obligatorio de contraseña: pública (la sesión pendiente no es válida para nada más).
        # EN: Mandatory password-change screen: public (a pending session is not valid for anything else).
        if path in ("/change-password", "/change-password.html"):
            return self._file(STATIC_DIR / "change-password.html", "text/html; charset=utf-8")

        # Quién es la sesión pendiente de cambiar contraseña (la página lo usa para saludar o volver al login).
        # EN: Who the session pending a password change is (the page uses it to greet or go back to the login).
        if path == "/api/self":
            sess = auth.get_session(tok, allow_pending=True)
            return self._json(200, {"username": sess["username"],
                                    "must_change_password": sess["must_change_password"]} if sess else {})

        if path == "/api/version":     # public: shown in the page footer
            return self._json(200, {"version": auth.version()})
        if path == "/api/health":      # public: levels only; details need a valid session
            code, body = health_report(tok, auth.get_session(tok) is not None)
            return self._json(code, body)

        if not auth.check_permission(tok, "wol", "admin") and \
           not auth.check_permission(tok, "nut", "admin"):
            return self._json(401, {"error": "Unauthorized"})

        if path == "/api/teleporter":
            return self._json(200, {"available": tp.available(), "backups": tp.list_backups(),
                                    "restore": tp.restore_status(),
                                    "max_upload": tp.MAX_UPLOAD})
        m = re.match(r"^/api/teleporter/download/([A-Za-z0-9._-]+)$", path)
        if m: return self._tp_download(m.group(1))

        if path == "/api/users":
            users = auth.load_users()
            out   = [{"username": u, "permissions": d["permissions"],
                      "must_change_password": d.get("must_change_password", False),
                      "created": d.get("created")}
                     for u, d in users.items()]
            self._json(200, {"users": out})
        elif path == "/api/me":
            sess = auth.get_session(tok)
            self._json(200, {"username": sess["username"],
                              "permissions": sess["permissions"]} if sess else {})
        else:
            self._json(404, {"error": "Not found"})

    # POST: login, logout, respaldos (crear / verificar / restaurar), alta de usuarios y cambio de contraseña.
    # Orden: rutas públicas (login) → exigir admin → rutas protegidas.
    # EN: POST: login, logout, backups (create / verify / restore), user creation and password change.
    #     Order: public routes (login) → require admin → protected routes.
    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        if path == "/api/teleporter/upload": return self._tp_upload(tok)
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})

        # Login público
        # Login: pasa por auth.login (con límite de intentos). Solo se acepta a admins. La cookie es HttpOnly y
        # SameSite=Strict para que el JavaScript de la página y otros sitios no puedan leer ni enviar el token.
        # EN: Login: goes through auth.login (with attempt limiting). Only admins are accepted. The cookie is HttpOnly and
        #     SameSite=Strict so the page's JavaScript and other sites can neither read nor send the token.
        if path == "/api/login":
            u, err = auth.login(self, body.get("username",""), body.get("password",""))
            if not u: return self._json(err[0], {"error": err[1]})
            # Solo admins pueden acceder al panel
            if auth.LEVELS.get(u["permissions"].get("wol",""),0) < 3 and \
               auth.LEVELS.get(u["permissions"].get("nut",""),0) < 3:
                return self._json(403, {"error": "Administrator access required"})
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

        # Cambio de la propia contraseña, disponible para cualquier usuario con sesión (también la pendiente de cambio obligatorio, que no sirve para nada más). Pide la contraseña actual y exige una distinta.
        # EN: Change of one's own password, available to any user with a session (including the one pending a mandatory change, which is valid for nothing else). It asks for the current password and requires a different one.
        if path == "/api/self_password":
            sess = auth.get_session(tok, allow_pending=True)
            if not sess: return self._json(401, {"error": "Unauthorized"})
            me_  = sess["username"]
            cur  = body.get("current_password")
            new_ = body.get("new_password")
            if not isinstance(cur, str) or not isinstance(new_, str):
                return self._json(400, {"error": "Invalid request body"})
            if len(new_.strip()) < 6:
                return self._json(400, {"error": "Password must be at least 6 characters"})
            if new_ == cur:
                return self._json(400, {"error": "The new password must be different from the current one"})
            if auth.authenticate(me_, cur) is None:
                return self._json(403, {"error": "Current password is incorrect"})
            with auth.users_lock():
                users = auth.load_users()
                if me_ not in users: return self._json(404, {"error": "User not found"})
                users[me_]["password_hash"] = auth._hash(new_.strip())
                users[me_]["must_change_password"] = False
                auth.save_users(users)
            auth.delete_user_sessions(me_, keep=tok)
            log.info(f"Password changed by the user themselves: {me_}")
            return self._json(200, {"ok": True})

        if not auth.check_permission(tok, "wol", "admin") and \
           not auth.check_permission(tok, "nut", "admin"):
            return self._json(401, {"error": "Unauthorized"})

        sess = auth.get_session(tok)
        me   = sess["username"] if sess else ""

        # Respaldos: backup (crear), check (verificar sin cambiar nada) y restore (requiere confirm=true).
        # La restauración desde el panel nunca toca /etc/nut ni nginx; eso solo se hace por consola.
        # EN: Backups: backup (create), check (verify without changing anything) and restore (requires confirm=true).
        #     Restoring from the panel never touches /etc/nut or nginx; that is done only from the command line.
        if path.startswith("/api/teleporter/"):
            if not tp.available(): return self._json(503, {"error": "teleporter.sh is not installed"})
            action = path.rsplit("/", 1)[1]
            if action == "backup":
                ok, name, out = tp.create_backup()
                log.info(f"Backup created by {me}: {name if ok else 'FAILED'}")
                return self._json(200 if ok else 500, {"ok": ok, "name": name, "output": out,
                                  **({} if ok else {"error": "Backup failed"})})
            name = body.get("name")
            if action == "check":
                ok, out = tp.verify(name)
                return self._json(200, {"ok": ok, "output": out})
            if action == "restore":
                if body.get("confirm") is not True:
                    return self._json(400, {"error": "Confirmation required"})
                ok, out = tp.start_restore(name)
                log.warning(f"Restore started by {me}: {name} -> {'ok' if ok else 'FAILED'}")
                return self._json(200 if ok else 500, {"ok": ok, "output": out,
                                  **({} if ok else {"error": "Could not start the restore"})})
            return self._json(404, {"error": "Not found"})

        # Alta de usuario: valida nombre (2-32 caracteres seguros) y niveles; por defecto WOL/UPS de solo lectura
        # y Net/Proxmox sin acceso. Todo bajo users_lock para no pisar otros cambios.
        # EN: User creation: validates the name (2-32 safe characters) and levels; by default WOL/UPS read-only
        #     and Net/Proxmox no access. All under users_lock so other changes are not overwritten.
        if path == "/api/users":
            # Crear usuario
            uname = (body.get("username") or "").strip()
            pwd   = (body.get("password") or "").strip()
            perms = {k: body.get(k + "_permission", "readonly" if k in ("wol", "nut") else "none")
                     for k in PERM_KEYS}
            if not uname or not pwd:
                return self._json(400, {"error": "Username and password are required"})
            if not re.match(r'^[a-zA-Z0-9_\-]{2,32}$', uname):
                return self._json(400, {"error": "Invalid username (2-32 alphanumeric chars)"})
            if any(v not in VALID_PERMS for v in perms.values()):
                return self._json(400, {"error": "Invalid permission"})
            with auth.users_lock():
                users = auth.load_users()
                if uname in users:
                    return self._json(409, {"error": "User already exists"})
                users[uname] = {
                    "password_hash": auth._hash(pwd),
                    "permissions": perms,
                    "created": int(time.time()),
                    "must_change_password": body.get("must_change_password", False),
                }
                auth.save_users(users)
            log.info(f"Usuario creado: {uname} por {me}")
            self._json(201, {"ok": True})

        # Cambio de contraseña: cada usuario cambia la suya y solo un admin de WOL cambia la de otros. Al cambiarla
        # se cierran todas las demás sesiones de esa cuenta.
        # EN: Password change: each user changes their own and only a WOL admin changes others'. Changing it
        #     closes every other session of that account.
        elif path == "/api/change_password":
            # Cambiar propia contraseña o la de cualquiera (admin)
            target = (body.get("username") or me).strip()
            new_pw = (body.get("new_password") or "").strip()
            if not new_pw or len(new_pw) < 6:
                return self._json(400, {"error": "Password must be at least 6 characters"})
            # No-admin solo puede cambiar la suya
            if target != me and not auth.check_permission(tok, "wol", "admin"):
                return self._json(403, {"error": "You can only change your own password"})
            with auth.users_lock():
                users = auth.load_users()
                if target not in users:
                    return self._json(404, {"error": "User not found"})
                users[target]["password_hash"] = auth._hash(new_pw)
                users[target]["must_change_password"] = False
                auth.save_users(users)
            # every other session of that account is closed (the current one stays open)
            auth.delete_user_sessions(target, keep=tok if target == me else None)
            log.info(f"Password changed: {target} by {me}")
            self._json(200, {"ok": True})

        else:
            self._json(404, {"error": "Not found"})

    # PUT /api/users/<nombre>: actualiza niveles de permiso (WOL, UPS, Net, Proxmox). Solo admins.
    # EN: PUT /api/users/<name>: updates permission levels (WOL, UPS, Net, Proxmox). Admins only.
    def do_PUT(self):
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})

        if not auth.check_permission(tok, "wol", "admin") and \
           not auth.check_permission(tok, "nut", "admin"):
            return self._json(401, {"error": "Unauthorized"})

        sess = auth.get_session(tok)
        me   = sess["username"] if sess else ""

        m = re.match(r'^/api/users/([a-zA-Z0-9_\-]+)$', path)
        if m:
            uname = m.group(1)
            new = {k: body.get(k + "_permission") for k in PERM_KEYS if body.get(k + "_permission")}
            if any(v not in VALID_PERMS for v in new.values()):
                return self._json(400, {"error": "Invalid permission"})
            # Don't let admins lock themselves out of the panel
            # Un admin no puede quitarse a sí mismo el acceso al panel (se quedaría fuera).
            # EN: An admin cannot remove their own access to the panel (they would lock themselves out).
            if uname == me and (new.get("wol") == "none" or new.get("nut") == "none"):
                return self._json(400, {"error": "You cannot remove your own admin permissions"})
            with auth.users_lock():
                users = auth.load_users()
                if uname not in users:
                    return self._json(404, {"error": "User not found"})
                users[uname].setdefault("permissions", {}).update(new)
                auth.save_users(users)
            log.info(f"Permissions updated: {uname} by {me}")
            self._json(200, {"ok": True})
        else:
            self._json(404, {"error": "Not found"})

    # DELETE: borrar un respaldo o un usuario. Un usuario no puede eliminarse a sí mismo; al borrar se cierran sus sesiones.
    # EN: DELETE: remove a backup or a user. A user cannot delete themselves; deleting closes their sessions.
    def do_DELETE(self):
        path = urlparse(self.path).path
        tok  = self._tok()
        if not auth.check_permission(tok, "wol", "admin") and \
           not auth.check_permission(tok, "nut", "admin"):
            return self._json(401, {"error": "Unauthorized"})
        sess = auth.get_session(tok)
        me   = sess["username"] if sess else ""
        mt = re.match(r"^/api/teleporter/([A-Za-z0-9._-]+)$", path)
        if mt:
            if tp.delete(mt.group(1)):
                log.info(f"Backup deleted: {mt.group(1)} by {me}")
                return self._json(200, {"ok": True})
            return self._json(404, {"error": "Backup not found"})
        m = re.match(r'^/api/users/([a-zA-Z0-9_\-]+)$', path)
        if not m: return self._json(400, {"error": "Invalid user"})
        uname = m.group(1)
        if uname == me: return self._json(400, {"error": "You cannot delete yourself"})
        with auth.users_lock():
            users = auth.load_users()
            if uname not in users: return self._json(404, {"error": "Not found"})
            del users[uname]; auth.save_users(users)
        auth.delete_user_sessions(uname)
        log.info(f"Usuario eliminado: {uname} por {me}")
        self._json(200, {"ok": True})

# Arranque: crea la carpeta estática, completa los permisos net/pve de usuarios antiguos (una sola vez)
# y sirve en loopback hasta que el proceso termine.
# EN: Startup: creates the static folder, fills in net/pve permissions for old users (once)
#     and serves on loopback until the process ends.
if __name__ == "__main__":
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if auth.ensure_permissions(): log.info("'net'/'pve' permissions filled in")
    except Exception as e:
        log.warning(f"Permissions: {e}")
    log.info(f"Admin Panel en http://{HOST}:{PORT}")
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H); srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
