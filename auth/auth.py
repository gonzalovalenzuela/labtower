#!/usr/bin/env python3
"""
Pi Console — Auth Module
Gestión de usuarios, sesiones y permisos compartido por todos los módulos.

Los módulos son procesos distintos que comparten users.json y sessions.json, así que
toda lectura-modificación-escritura se hace bajo un bloqueo de archivo (flock) además
del bloqueo entre hilos, y todo se escribe de forma atómica (archivo temporal propio,
fsync y rename) para no perder ni corromper datos ante cortes de energía.

EN: User, session and permission management shared by all the modules. The modules are separate
processes that share users.json and sessions.json, so every read-modify-write happens under a
file lock (flock) in addition to the thread lock, and everything is written atomically (own temp
file, fsync and rename) so no data is lost or corrupted by power cuts.
"""
# ─── Mapa del archivo ────────────────────────────────────────────────────────────────
# Este módulo lo importan los 5 servicios (WOL, UPS, Net, Proxmox y Admin). Cada servicio es
# un proceso distinto, pero todos comparten dos archivos en /var/lib/pi-console:
#   users.json     usuarios, hash de contraseña y nivel de permiso por módulo
#   sessions.json  sesiones abiertas (un solo inicio de sesión sirve para todos los módulos)
#
# Secciones, en orden:
#   1. Escritura atómica y bloqueo entre procesos (atomic_write, read_json, FileLock)
#   2. Hash de contraseñas (scrypt; SHA-256 antiguo solo para migrar)
#   3. Usuarios (cargar, guardar, usuario inicial, migración de permisos)
#   4. Sesiones (crear, validar, renovar, cerrar)
#   5. Autenticación, límite de intentos y permisos
#   6. Versión y chequeos de salud (/api/health)
#
# Convención: los comentarios van primero en español y después en inglés (marcados con «EN:»).
# Los docstrings en inglés describen qué hace cada función; los comentarios explican el porqué.
# EN: ─── File map ───────────────────────────────────────────────────────────────────────
#     Imported by all 5 services (WOL, UPS, Net, Proxmox and Admin). Each service is a separate
#     process, but they all share two files in /var/lib/pi-console:
#       users.json     users, password hashes and the permission level for each module
#       sessions.json  open sessions (a single login works for every module)
#
#     Sections, in order:
#       1. Atomic writes and cross-process locking (atomic_write, read_json, FileLock)
#       2. Password hashing (scrypt; the old SHA-256 only to migrate)
#       3. Users (load, save, initial user, permission migration)
#       4. Sessions (create, validate, renew, close)
#       5. Authentication, login throttling and permissions
#       6. Version and health checks (/api/health)
#
#     Convention: comments are written in Spanish first and then in English (marked "EN:"). The
#     English docstrings describe what each function does; the comments explain why.
import copy, json, os, hashlib, hmac, secrets, time, logging, threading, glob, shutil, subprocess
from pathlib import Path

try:
    import fcntl
except ImportError:          # pragma: no cover - solo Linux/macOS
    fcntl = None

# Registro de mensajes; cada servicio decide el formato y el destino (journalctl).
# EN: Message log; each service decides the format and destination (journalctl).
log = logging.getLogger("auth")

# Rutas de los archivos compartidos. Las variables PICONSOLE_* permiten cambiarlas en las pruebas
# sin tocar /var/lib/pi-console.
# EN: Paths of the shared files. The PICONSOLE_* variables let tests move them
#     without touching /var/lib/pi-console.
USERS_FILE    = Path(os.environ.get("PICONSOLE_USERS",    "/var/lib/pi-console/users.json"))
# Duración de una sesión sin actividad.
# EN: How long a session lasts without activity.
SESSION_TTL = 24 * 3600   # 24 horas
# La ventana deslizante se renueva como máximo cada RENEW_EVERY segundos: renovar en
# cada request reescribiría sessions.json (y la SD) varias veces por segundo.
RENEW_EVERY = 600
SESSIONS_FILE = Path(os.environ.get("PICONSOLE_SESSIONS", "/var/lib/pi-console/sessions.json"))


# ─── Escritura atómica y bloqueo entre procesos ───────────────────────────────
# Escribir un archivo sin dejarlo nunca a medias: se escribe en un temporal propio, se fuerza a disco
# (fsync) y se renombra encima del destino. El rename es atómico, así que un corte de energía
# deja el archivo viejo completo o el nuevo completo, nunca uno corrupto (la Pi usa tarjeta SD).
# EN: Write a file without ever leaving it half-written: write to a private temp file, force it to
#     disk (fsync) and rename it over the target. The rename is atomic, so a power cut leaves either
#     the complete old file or the complete new one, never a corrupt one (the Pi uses an SD card).
def atomic_write(path, data, mode=0o600):
    """Write `data` (str or bytes) to `path` atomically: private temp file, fsync, rename.

    Each writer uses its own temp name, so concurrent writers (other threads or the other
    Pi Console services) can never interleave their bytes. Files are created with `mode`
    (0600 by default: they hold password hashes, API tokens and SNMP/Pi-hole credentials).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode()
    # El nombre del temporal incluye el PID y el hilo: dos escritores a la vez nunca comparten archivo.
    # EN: The temp name includes the PID and the thread: two simultaneous writers never share a file.
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try: os.unlink(tmp)
        except OSError: pass
        raise
    try:                                   # persist the rename itself (best effort)
        dfd = os.open(str(path.parent), os.O_RDONLY)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    except OSError:
        pass


# Leer un JSON de datos con red de seguridad: si el archivo falta o está dañado se intenta la copia
# .bak que deja write_json; si tampoco sirve, se devuelve el valor por defecto.
# EN: Read a JSON data file with a safety net: if it is missing or damaged, try the .bak copy that
#     write_json leaves; if that is not usable either, return the default value.
def read_json(path, default, kind=None):
    """Load a JSON data file. If it is missing or damaged, fall back to its last good copy
    (<name>.bak, kept by write_json) and, failing that, to `default` (a value or a callable)."""
    path = Path(path)
    for p in (path, path.with_name(path.name + ".bak")):
        try:
            if not p.exists():
                continue
            data = json.loads(p.read_text())
            if kind is None or isinstance(data, kind):
                if p is not path:
                    log.error(f"{path} is unreadable; using {p.name}")
                return data
            log.error(f"{p}: unexpected content")
        except Exception as e:
            log.error(f"{p}: {e}")
    return default() if callable(default) else copy.deepcopy(default)


# Guardar un JSON de datos conservando la versión anterior buena como .bak (solo si era JSON válido).
# EN: Save a JSON data file keeping the previous good version as .bak (only if it was valid JSON).
def write_json(path, obj, indent=2, mode=0o600):
    """Atomically write a JSON data file, keeping the previous good version as <name>.bak."""
    path = Path(path)
    if path.exists():
        try:
            raw = path.read_bytes()
            json.loads(raw)
            atomic_write(path.with_name(path.name + ".bak"), raw, mode)
        except Exception:
            pass                      # the current file is already damaged: keep the older .bak
    atomic_write(path, json.dumps(obj, indent=indent), mode)


# Candado reentrante que protege a los hilos de ESTE proceso (RLock) y a los OTROS procesos (flock
# sobre un archivo .lock). Hace falta porque los 5 servicios modifican users.json y sessions.json.
# EN: Re-entrant lock that protects the threads of THIS process (RLock) and OTHER processes (flock on
#     a .lock file). It is needed because the 5 services modify users.json and sessions.json.
class FileLock:
    """Re-entrant lock for threads of this process *and* for other processes (flock)."""
    def __init__(self, path):
        self.path = Path(path)
        self._t = threading.RLock()
        self._depth = 0
        self._fd = None

    def __enter__(self):
        self._t.acquire()
        try:
            if self._depth == 0 and fcntl is not None:
                try:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    fd = os.open(str(self.path), os.O_CREAT | os.O_RDWR, 0o600)
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX)
                    except OSError:
                        os.close(fd); raise
                    self._fd = fd
                except OSError as e:       # without the lock, concurrent writers could corrupt data
                    log.error(f"file lock unavailable ({self.path}): {e}")
                    raise RuntimeError(f"cannot acquire file lock {self.path}: {e}") from e
            self._depth += 1
        except BaseException:
            self._t.release(); raise
        return self

    def __exit__(self, *exc):
        self._depth -= 1
        if self._depth == 0 and self._fd is not None:
            try: fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd); self._fd = None
        self._t.release()
        return False


# Un candado por archivo compartido, con su archivo .lock al lado.
# EN: One lock per shared file, with its .lock file next to it.
_users_lock    = FileLock(USERS_FILE.with_name(USERS_FILE.name + ".lock"))
_sessions_lock = FileLock(SESSIONS_FILE.with_name(SESSIONS_FILE.name + ".lock"))

# Uso: «with auth.users_lock():» alrededor de cargar → modificar → guardar usuarios, para no pisar cambios ajenos.
# EN: Usage: "with auth.users_lock():" around load → modify → save of users, so other changes are not overwritten.
def users_lock():
    """Hold this around any load_users() → modify → save_users() sequence."""
    return _users_lock


# ─── Contraseñas ─────────────────────────────────────────────────────────────────────
# Formato actual: scrypt con sal aleatoria por contraseña. El formato antiguo (SHA-256 con sal fija)
# se sigue reconociendo solo para que los usuarios viejos puedan entrar y migrar.
# EN: ─── Passwords ───────────────────────────────────────────────────────────────────────
#     Current format: scrypt with a random salt per password. The old format (SHA-256 with a fixed salt)
#     is still recognised only so that old users can log in and be migrated.
def _salt() -> str:
    """Salt of the LEGACY sha256 hashes (kept only to verify and migrate old users.json files)."""
    return os.environ.get("PICONSOLE_SALT", "pi-console-salt-change-me")

# Parámetros de scrypt: N=2^14 usa ~16 MB y tarda ~0,1-0,3 s en una Pi 3 (suficiente freno contra fuerza bruta sin ahogar la Pi).
# EN: scrypt parameters: N=2^14 uses ~16 MB and takes ~0.1-0.3 s on a Pi 3 (enough brake against brute force without choking the Pi).
_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2 ** 14, 8, 1      # ~16 MB, ~0.1-0.3 s on a Pi 3

def _hash(password: str) -> str:
    """Salted scrypt hash, stored as  scrypt$N$r$p$<salt hex>$<hash hex>  (random salt per password)."""
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32)
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${dk.hex()}"

# Hash del formato antiguo; existe únicamente para comparar y migrar.
# EN: Hash of the old format; it exists only to compare and migrate.
def _legacy_hash(password: str) -> str:
    return hashlib.sha256(f"{_salt()}:{password}".encode()).hexdigest()

# Todo lo que no empiece con «scrypt$» se considera formato antiguo.
# EN: Anything that does not start with "scrypt$" is treated as the old format.
def _is_legacy(stored) -> bool:
    return not (isinstance(stored, str) and stored.startswith("scrypt$"))

# Comprueba una contraseña contra su hash guardado. Compara en tiempo constante (compare_digest) para no
# filtrar información por latencia, y devuelve False ante cualquier hash mal formado.
# EN: Check a password against its stored hash. It compares in constant time (compare_digest) so latency
#     leaks nothing, and returns False for any malformed hash.
def _verify(stored, password: str) -> bool:
    """Check a password against a stored hash (scrypt, or the legacy sha256 format)."""
    if not isinstance(stored, str): return False
    if _is_legacy(stored):
        return hmac.compare_digest(stored, _legacy_hash(password))
    try:
        _, n, r, p, salt, want = stored.split("$")
        dk = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p),
                            dklen=len(want) // 2, maxmem=128 * 1024 * 1024)
        return hmac.compare_digest(dk.hex(), want)
    except Exception:
        return False

# Para un usuario inexistente se gasta el mismo tiempo que para uno real: así no se puede averiguar qué
# usuarios existen midiendo cuánto tarda la respuesta.
# EN: For a non-existent user the same time is spent as for a real one, so you cannot find out which
#     users exist by measuring how long the answer takes.
_dummy_hash = None
def _burn_time(password: str):
    """Spend the same time as a real check so an unknown user cannot be told apart by latency."""
    global _dummy_hash
    if _dummy_hash is None: _dummy_hash = _hash("x")
    _verify(_dummy_hash, password)


# ─── Usuarios ─────────────────────────────────────────────────────────────────
# El hash de la contraseña inicial «admin» se calcula una sola vez, porque se consulta en cada petición de una instalación nueva.
# EN: The hash of the initial password "admin" is computed only once, because it is queried on every request of a fresh install.
_default_pw_hash = None

# Usuario inicial de una instalación nueva: admin/admin con obligación de cambiar la contraseña en el primer inicio de sesión.
# EN: Initial user of a fresh install: admin/admin, forced to change the password at the first login.
def _default_users() -> dict:
    global _default_pw_hash
    if _default_pw_hash is None: _default_pw_hash = _hash("admin")      # computed once: this runs per request on a fresh install
    return {
        "admin": {
            "password_hash": _default_pw_hash,
            "permissions": {"wol": "admin", "nut": "admin", "net": "admin", "pve": "admin"},
            "created": int(time.time()),
            "must_change_password": True,
        }
    }

# Caché de users.json: se vuelve a leer del disco solo cuando cambia el archivo (firma = fecha de modificación + tamaño).
# EN: Cache of users.json: re-read from disk only when the file changes (signature = modification time + size).
_ucache = {"sig": None, "data": None}

# Marcador que indica «esta instalación ya tuvo usuarios». Sin él, un users.json borrado reabriría el panel
# con admin/admin; con él, falla cerrado (nadie entra) hasta restaurar el archivo.
# EN: Marker meaning "this install has already had users". Without it, a deleted users.json would reopen the panel
#     with admin/admin; with it, the system fails closed (nobody gets in) until the file is restored.
INIT_MARKER = USERS_FILE.with_name(".users-initialized")

# Una instalación se considera ya usada si existe el marcador o la copia de seguridad.
# EN: An install counts as already used if the marker or the backup copy exists.
def _initialized() -> bool:
    """True once this install has had a users table (marker or backup present)."""
    return INIT_MARKER.exists() or USERS_FILE.with_name(USERS_FILE.name + ".bak").exists()

# Crea el marcador (si no se puede escribir, solo se avisa: no es motivo para fallar).
# EN: Create the marker (if it cannot be written, only a warning: it is not a reason to fail).
def _mark_initialized():
    try:
        if not INIT_MARKER.exists():
            atomic_write(INIT_MARKER, "1\n")
    except OSError as e:
        log.warning(f"cannot write {INIT_MARKER}: {e}")

# Firma barata de un archivo para saber si cambió sin releerlo.
# EN: Cheap signature of a file to know whether it changed without re-reading it.
def _file_sig(p: Path):
    try:
        st = p.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None

# Fuente única de la tabla de usuarios para todo el módulo. Orden de decisión:
#   1. users.json no existe y la instalación es nueva → usuario inicial admin/admin.
#   2. users.json no existe pero la instalación ya se usó → se usa la copia .bak, o nadie entra.
#   3. users.json existe → se usa (de la caché si no cambió); si está corrupto, la copia .bak.
# Nunca se vuelve a admin/admin por un archivo dañado o borrado.
# EN: Single source of the users table for the whole module. Decision order:
#       1. users.json is missing and the install is new → initial admin/admin user.
#       2. users.json is missing but the install was already used → use the .bak copy, or nobody gets in.
#       3. users.json exists → use it (from the cache if unchanged); if corrupt, the .bak copy.
#     It never falls back to admin/admin because of a damaged or deleted file.
def _users_cached() -> dict:
    """Parsed users.json (shared object: do not mutate). Re-read only when the file changes.

    * Missing file, never initialised → the initial admin account (fresh install only).
    * Missing file after use         → the last good copy (users.json.bak) or NO users.
    * Unreadable/corrupt file       → the last good copy (users.json.bak) or, failing that,
      NO users. It must never fall back to the default admin/admin account, which would
      silently reopen the panel with well-known credentials after a bad write.
    """
    sig = _file_sig(USERS_FILE)
    if sig is None:
        # users.json missing. Only a genuinely fresh install (no marker, no backup) gets the
        # initial admin; otherwise the file was removed and nobody may log in with defaults.
        if not _initialized():
            return _default_users()
        sig = ("missing",)
    if sig == _ucache["sig"] and _ucache["data"] is not None:
        return _ucache["data"]
    for p in (USERS_FILE, USERS_FILE.with_name(USERS_FILE.name + ".bak")):
        try:
            data = json.loads(p.read_text())
            if isinstance(data, dict):
                if p is not USERS_FILE:
                    log.error(f"{USERS_FILE} is unreadable; using {p.name}")
                _ucache["sig"], _ucache["data"] = sig, data
                _mark_initialized()
                return data
        except FileNotFoundError:
            continue
        except Exception as e:
            log.error(f"{p}: {e}")
    log.error(f"{USERS_FILE} is missing or corrupt and there is no usable backup: no user can "
              f"log in until it is restored (or {INIT_MARKER} is removed to start from scratch)")
    return {}

# Migración que corre al iniciar cada servicio: deja un nivel explícito para «net» y «pve» a los usuarios
# creados antes de que existieran esos módulos. Es idempotente (si ya están, no toca nada).
# EN: Migration that runs when each service starts: gives an explicit "net" and "pve" level to users
#     created before those modules existed. It is idempotent (if they are already there, nothing changes).
def ensure_permissions(modules=("net", "pve")) -> bool:
    """One-time migration at service start: give every user an EXPLICIT level for `modules`.

    Users that predate a module get "admin" if they administer WOL, else "readonly" (what the
    old runtime fallback granted). After this a missing permission means no access: levels are
    never derived from another module at request time. Returns True if users.json changed."""
    with users_lock():
        users = load_users()
        changed = False
        for udata in users.values():
            perms = udata.setdefault("permissions", {})
            for m in modules:
                if m not in perms:
                    perms[m] = "admin" if perms.get("wol") == "admin" else "readonly"
                    changed = True
        if changed:
            save_users(users)
        return changed

# Devuelve una COPIA de los usuarios, segura de modificar antes de pasarla a save_users.
# EN: Return a COPY of the users, safe to modify before passing it to save_users.
def load_users() -> dict:
    """A private copy of the users table, safe to modify and pass to save_users()."""
    return copy.deepcopy(_users_cached())

# Guarda la tabla de usuarios: copia .bak de la versión anterior, escritura atómica, marcador de «ya usada»
# y refresco de la caché. Debe llamarse dentro de «with users_lock()».
# EN: Save the users table: .bak copy of the previous version, atomic write, "already used" marker and cache
#     refresh. It must be called inside "with users_lock()".
def save_users(users: dict):
    with _users_lock:
        if USERS_FILE.exists():                      # keep the previous good version
            try:
                json.loads(USERS_FILE.read_text())
                atomic_write(USERS_FILE.with_name(USERS_FILE.name + ".bak"), USERS_FILE.read_bytes())
            except Exception:
                pass
        atomic_write(USERS_FILE, json.dumps(users, indent=2))
        _mark_initialized()
        _ucache["sig"], _ucache["data"] = _file_sig(USERS_FILE), copy.deepcopy(users)


# ─── Sesiones compartidas (persistidas a disco) ────────────────────────────────
# Caché de sessions.json por la misma razón que la de usuarios: otro servicio pudo escribirlo, así que se compara la firma.
# EN: Cache of sessions.json for the same reason as the users one: another service may have written it, so the signature is compared.
_scache = {"sig": None, "data": {}}

def _load_sessions() -> dict:
    """Lee sessions.json solo si cambió en disco (otro servicio pudo escribirlo)."""
    sig = _file_sig(SESSIONS_FILE)
    if sig is not None and sig == _scache["sig"]:
        return _scache["data"]
    try:
        if sig is not None:
            data = json.loads(SESSIONS_FILE.read_text())
            if isinstance(data, dict):
                _scache["sig"], _scache["data"] = sig, data
                return data
    except Exception as e:
        log.warning(f"sessions.json: {e}")
    _scache["sig"], _scache["data"] = None, {}
    return {}

# Escritura atómica de todas las sesiones y actualización de la caché.
# EN: Atomic write of all the sessions and cache update.
def _save_sessions(sessions: dict):
    atomic_write(SESSIONS_FILE, json.dumps(sessions))
    _scache["sig"], _scache["data"] = _file_sig(SESSIONS_FILE), sessions

# Abre una sesión: token aleatorio de 256 bits. Se guardan usuario, permisos al momento del login y
# vencimiento. Aprovecha para purgar las sesiones vencidas.
# EN: Open a session: random 256-bit token. Stores the user, the permissions at login time and the expiry.
#     It takes the chance to purge expired sessions.
def create_session(username: str, permissions: dict) -> str:
    token = secrets.token_hex(32)
    with _sessions_lock:
        sessions = _load_sessions()
        sessions[token] = {
            "username":    username,
            "permissions": permissions,
            "expires":     time.time() + SESSION_TTL,
        }
        _purge(sessions)
        _save_sessions(sessions)
    return token

# Valida un token y devuelve la sesión o None. Reglas:
#   · si venció, se borra;
#   · si el usuario ya no existe, se borra (eliminar un usuario corta su sesión de inmediato);
#   · los permisos devueltos son siempre los ACTUALES de users.json, no los del login;
#   · la ventana de 24 h se renueva, pero solo se escribe a disco si pasaron más de RENEW_EVERY segundos.
# EN: Validate a token and return the session or None. Rules:
#       · if it expired, it is deleted;
#       · if the user no longer exists, it is deleted (removing a user cuts their session at once);
#       · the permissions returned are always the CURRENT ones from users.json, not the ones at login;
#       · the 24 h window is renewed, but written to disk only if more than RENEW_EVERY seconds passed.
# Devuelve la sesión del token (o None). Si la cuenta tiene must_change_password (primer ingreso con admin/admin, o marcada por un admin), la sesión NO es válida para nada, salvo para cambiar la contraseña (allow_pending=True): así ningún módulo da acceso hasta que se cambie.
# EN: Return the session of the token (or None). If the account has must_change_password (first login with admin/admin, or flagged by an admin), the session is NOT valid for anything except changing the password (allow_pending=True): no module grants access until it is changed.
def get_session(token: str, allow_pending: bool = False) -> dict | None:
    if not token: return None
    with _sessions_lock:
        sessions = _load_sessions()
        s = sessions.get(token)
        if not s: return None
        now = time.time()
        if now > s.get("expires", 0):
            sessions.pop(token, None); _save_sessions(sessions); return None
        # The account must still exist, and the permissions are always the current ones:
        # deleting or demoting a user takes effect immediately instead of when the session expires.
        user = _users_cached().get(s.get("username"))
        if user is None:
            sessions.pop(token, None); _save_sessions(sessions); return None
        # Ventana deslizante de 24h, pero persistida solo si pasaron > RENEW_EVERY s
        # desde la última renovación (evita una escritura a disco por request).
        if s["expires"] - now < SESSION_TTL - RENEW_EVERY:
            s["expires"] = now + SESSION_TTL
            sessions[token] = s
            _save_sessions(sessions)
        if user.get("must_change_password") and not allow_pending:
            return None
        return {**s, "permissions": dict(user.get("permissions", {})),
                "must_change_password": bool(user.get("must_change_password"))}

# Cierre de sesión (logout).
# EN: Logout.
def delete_session(token: str):
    with _sessions_lock:
        sessions = _load_sessions()
        if sessions.pop(token, None) is not None:
            _save_sessions(sessions)

# Cierra todas las sesiones de un usuario (cambio de contraseña o eliminación), dejando opcionalmente una.
# EN: Close all the sessions of a user (password change or removal), optionally keeping one.
def delete_user_sessions(username: str, keep: str | None = None):
    """Log a user out everywhere (password change, account removal), optionally keeping one session."""
    with _sessions_lock:
        sessions = _load_sessions()
        gone = [t for t, s in sessions.items() if s.get("username") == username and t != keep]
        for t in gone: del sessions[t]
        if gone: _save_sessions(sessions)

# Elimina las sesiones vencidas del diccionario recibido.
# EN: Remove the expired sessions from the given dictionary.
def _purge(sessions: dict):
    now = time.time()
    for t in [k for k, v in sessions.items() if now > v.get("expires", 0)]:
        del sessions[t]


# ─── Helpers ──────────────────────────────────────────────────────────────────
# Niveles de permiso ordenados: un nivel mayor incluye a los menores (admin puede lo que puede execute y readonly).
# EN: Permission levels in order: a higher level includes the lower ones (admin can do what execute and readonly can).
LEVELS = {"readonly": 1, "execute": 2, "admin": 3}

# Verifica usuario y contraseña y devuelve una copia del usuario, o None.
# Si la contraseña es correcta pero el hash es del formato antiguo, lo reemplaza por scrypt en ese momento.
# EN: Check username and password and return a copy of the user, or None.
#     If the password is right but the hash is in the old format, it is replaced by scrypt right then.
def authenticate(username: str, password: str) -> dict | None:
    user = _users_cached().get(username) if isinstance(username, str) else None
    if not user or not isinstance(password, str):
        _burn_time(password if isinstance(password, str) else "")
        return None
    stored = user.get("password_hash")
    if not _verify(stored, password): return None
    if _is_legacy(stored):                              # old sha256 hash: upgrade it now that we know the password
        try:
            with users_lock():
                users = load_users()
                if username in users and users[username].get("password_hash") == stored:
                    users[username]["password_hash"] = _hash(password)
                    save_users(users)
        except Exception as e:
            log.warning(f"could not upgrade the password hash of {username}: {e}")
    return copy.deepcopy(user)


# ─── Login throttling ─────────────────────────────────────────────────────────
# Per client IP and per process (each service keeps its own counters): MAX_FAILS failed
# logins within WINDOW seconds lock that IP out for LOCKOUT seconds.
# Límite de intentos: tras MAX_FAILS fallos desde la misma IP dentro de WINDOW segundos, esa IP queda
# bloqueada LOCKOUT segundos. Cada proceso lleva su propia cuenta (no se comparte entre servicios).
# EN: Attempt limit: after MAX_FAILS failures from the same IP within WINDOW seconds, that IP is
#     locked for LOCKOUT seconds. Each process keeps its own count (not shared between services).
MAX_FAILS, WINDOW, LOCKOUT = 5, 600, 300
_fails: dict = {}
_fails_lock = threading.Lock()

# IP real del cliente. Detrás de nginx todas las peticiones llegan desde 127.0.0.1, así que solo en ese caso
# se confía en la cabecera X-Real-IP (que pone nginx); un cliente remoto no puede falsearla.
# EN: Real client IP. Behind nginx every request comes from 127.0.0.1, so only in that case the
#     X-Real-IP header (set by nginx) is trusted; a remote client cannot forge it.
def client_ip(handler) -> str:
    """Peer address; X-Real-IP is honoured only when the request comes from the local nginx."""
    ip = handler.client_address[0]
    if ip in ("127.0.0.1", "::1"):
        real = (handler.headers.get("X-Real-IP") or "").strip()
        if real and len(real) <= 45: return real
    return ip

# Inicio de sesión con límite de intentos. Devuelve (usuario, None) si entra, o (None, (código, mensaje)):
# 429 si la IP está bloqueada, 401 si las credenciales son inválidas (con una pausa de 0,3 s).
# EN: Login with attempt limiting. Returns (user, None) on success, or (None, (code, message)):
#     429 if the IP is locked, 401 for invalid credentials (with a 0.3 s pause).
def login(handler, username, password):
    """Throttled login: returns (user, None) or (None, (http_status, message))."""
    ip, now = client_ip(handler), time.time()
    with _fails_lock:
        if len(_fails) > 2048:
            for k in [k for k, v in _fails.items() if v["lock"] < now and now - v["first"] > WINDOW]: del _fails[k]
        f = _fails.get(ip)
        if f and f["lock"] > now:
            wait = int(f["lock"] - now) + 1
            return None, (429, f"Too many failed attempts. Try again in {wait} s")
    u = authenticate(username, password)
    with _fails_lock:
        if u:
            _fails.pop(ip, None)
            return u, None
        f = _fails.get(ip)
        if not f or now - f["first"] > WINDOW: f = _fails[ip] = {"n": 0, "first": now, "lock": 0}
        f["n"] += 1
        if f["n"] >= MAX_FAILS:
            f["lock"], f["n"], f["first"] = now + LOCKOUT, 0, now
            log.warning(f"login locked for {ip} after {MAX_FAILS} failed attempts")
    time.sleep(0.3)
    return None, (401, "Invalid credentials")

# ¿La sesión del token tiene al menos el nivel «required» sobre el recurso (wol, nut, net, pve)?
# EN: Does the token's session have at least the "required" level on the resource (wol, nut, net, pve)?
def check_permission(token: str, resource: str, required: str) -> bool:
    s = get_session(token)
    if not s: return False
    return LEVELS.get(s["permissions"].get(resource, ""), 0) >= LEVELS.get(required, 999)

# Extrae el token de la cabecera «Authorization: Bearer …» o, si no está, de la cookie «session».
# EN: Extract the token from the "Authorization: Bearer …" header or, if absent, from the "session" cookie.
def token_from_request(headers, cookie_str="") -> str | None:
    auth = headers.get("Authorization", "")
    if auth.startswith("Bearer "): return auth[7:].strip()
    for part in cookie_str.split(";"):
        part = part.strip()
        if part.startswith("session="): return part[8:].strip()
    return None


# ─── Version ──────────────────────────────────────────────────────────────────
# Versión instalada: la variable PICONSOLE_VERSION si existe; si no, el archivo VERSION de la raíz de la instalación.
# EN: Installed version: the PICONSOLE_VERSION variable if set; otherwise the VERSION file at the install root.
def version() -> str:
    """Installed Pi Console version: $PICONSOLE_VERSION, else the VERSION file at the install root."""
    v = os.environ.get("PICONSOLE_VERSION", "").strip()
    if v: return v
    try:
        return (Path(__file__).resolve().parent.parent / "VERSION").read_text().strip() or "dev"
    except OSError:
        return "dev"


# ─── Health ───────────────────────────────────────────────────────────────────
# ─── Salud ───────────────────────────────────────────────────────────────────────────
# Cada servicio expone /api/health con una lista de chequeos (ok / warn / fail). Aquí están los
# chequeos comunes a todos y el armado de la respuesta.
# EN: ─── Health ───────────────────────────────────────────────────────────────────────────
#     Every service exposes /api/health with a list of checks (ok / warn / fail). Here are the checks
#     common to all of them and the assembly of the response.
STARTED = time.time()
OK, WARN, FAIL = "ok", "warn", "fail"

# Resultado de un chequeo individual: nivel y texto de detalle.
# EN: Result of one check: level and detail text.
def chk(level, detail=""):
    """One health check result: level is OK, WARN (degraded) or FAIL."""
    return {"level": level, "detail": detail}

# El archivo de datos es legible (si existe) y su carpeta es escribible.
# EN: The data file is readable (if it exists) and its folder is writable.
def check_file(path, writable_dir=True, must_exist=False):
    """Data file is readable (if present) and its directory writable."""
    path = Path(path)
    try:
        if path.exists():
            with open(path, "rb") as f: json.loads(f.read() or b"null")
        elif must_exist:
            return chk(FAIL, f"{path.name} missing")
    except Exception as e:
        return chk(FAIL, f"{path.name} unreadable: {e}")
    if writable_dir and not os.access(path.parent, os.W_OK):
        return chk(FAIL, f"{path.parent} not writable")
    return chk(OK)

# Chequeos que comparten todos los módulos: usuarios, sesiones y espacio libre en disco.
# EN: Checks shared by every module: users, sessions and free disk space.
def check_common():
    """Checks every module shares: users file, sessions file, disk space."""
    out = {}
    users = _users_cached()
    out["users"] = chk(OK) if users else chk(FAIL, "no usable users.json")
    out["sessions"] = check_file(SESSIONS_FILE)
    try:
        st = os.statvfs(str(SESSIONS_FILE.parent if SESSIONS_FILE.parent.exists() else "/"))
        mb = st.f_bavail * st.f_frsize // (1024 * 1024)
        out["disk"] = chk(FAIL if mb < 5 else WARN if mb < 100 else OK, f"{mb} MB free")
    except OSError as e:
        out["disk"] = chk(WARN, str(e))
    return out

# Detecta si el equipo es una Raspberry Pi leyendo el modelo del device-tree (no existe en VM ni en otros PC).
# EN: Detect whether the machine is a Raspberry Pi by reading the device-tree model (it does not exist on VMs or other PCs).
def _is_raspberry_pi() -> bool:
    for f in (os.environ.get("PICONSOLE_PI_MODEL"), "/proc/device-tree/model", "/sys/firmware/devicetree/base/model"):
        if not f: continue
        try:
            return "raspberry pi" in Path(f).read_bytes().decode("utf-8", "ignore").lower()
        except OSError:
            continue
    return False

# Bits de «vcgencmd get_throttled» que nos importan. Los bajos (0, 2, 3) indican lo que pasa AHORA; los altos
# (16, 18, 19) lo que pasó desde el arranque y solo se borran al reiniciar.
# EN: Bits of "vcgencmd get_throttled" that matter to us. The low ones (0, 2, 3) say what is happening NOW; the high
#     ones (16, 18, 19) what happened since boot and only clear on reboot.
_THROTTLE_BITS = ((0, "under-voltage now"), (2, "throttled now"), (3, "temperature limit now"),
                  (16, "under-voltage since boot"), (18, "throttling since boot"), (19, "temperature limit since boot"))

# Lee la máscara de bits con vcgencmd o, si el servicio no puede usarlo, con la interfaz del kernel.
# EN: Read the bit mask with vcgencmd or, if the service cannot use it, through the kernel interface.
def _read_throttled():
    """Raspberry Pi firmware 'throttled' bit mask, or None when it cannot be read."""
    cmd = os.environ.get("PICONSOLE_VCGENCMD") or shutil.which("vcgencmd") or "/usr/bin/vcgencmd"
    try:
        out = subprocess.run([cmd, "get_throttled"], capture_output=True, text=True, timeout=3).stdout
        return int(out.split("=")[1].strip(), 16)
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        pass
    try:                                              # kernel interface, if the service user cannot use vcgencmd
        return int(Path("/sys/devices/platform/soc/soc:firmware/get_throttled").read_text().strip(), 16)
    except (OSError, ValueError):
        return None

# Chequeo de la fuente de la Pi: solo existe en una Raspberry Pi (en otro equipo devuelve None y no se muestra).
# Combina vcgencmd (historial) con la alarma de hwmon (estado actual); cualquier subtensión o limitación da aviso.
# EN: Raspberry Pi power supply check: it exists only on a Raspberry Pi (elsewhere it returns None and is not shown).
#     It combines vcgencmd (history) with the hwmon alarm (current state); any under-voltage or throttling gives a warning.
def check_power():
    """Raspberry Pi power supply health (under-voltage / throttling).

    Returns None on anything that is not a Raspberry Pi (VMs, other hardware), so no check is
    shown there. The 'since boot' bits only clear on reboot, so after replacing the power
    supply the warning stays until the Pi is restarted."""
    if not _is_raspberry_pi():
        return None
    bits = _read_throttled()
    now, have_hwmon = False, False
    for d in glob.glob(os.environ.get("PICONSOLE_HWMON", "/sys/class/hwmon") + "/hwmon*"):
        try:
            if Path(d, "name").read_text().strip() == "rpi_volt":
                now = Path(d, "in0_lcrit_alarm").read_text().strip() == "1"
                have_hwmon = True
        except OSError:
            pass
    if bits is None and not have_hwmon:
        return None                                   # no way to read the power state on this Pi
    flags = [txt for b, txt in _THROTTLE_BITS if bits and bits & (1 << b)]
    if now and "under-voltage now" not in flags:
        flags.insert(0, "under-voltage now")
    if not flags:
        return chk(OK)
    return chk(WARN, ", ".join(flags) + " — check the power supply and cable"
               + ("" if any("now" in f for f in flags) else " (a reboot clears the history)"))

# Arma la respuesta de /api/health: el estado global es el peor de los chequeos. Sin sesión de admin solo se
# entregan los niveles, sin el texto de detalle. Un fallo grave responde 503.
# EN: Build the /api/health response: the overall status is the worst of the checks. Without an admin session only
#     the levels are returned, without the detail text. A serious failure answers 503.
def health_reply(module, checks, detailed=False, extra=None):
    """Build (http_code, body). Unauthenticated callers get levels only, no detail text."""
    levels = [c["level"] for c in checks.values()]
    status = FAIL if FAIL in levels else "degraded" if WARN in levels else OK
    body = {"module": module, "version": version(), "status": status, "uptime": int(time.time() - STARTED),
            "checks": {k: ({**v} if detailed else {"level": v["level"]}) for k, v in checks.items()}}
    if extra and detailed: body.update(extra)
    return (503 if status == FAIL else 200), body

