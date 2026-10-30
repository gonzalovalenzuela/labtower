#!/usr/bin/env python3
"""
LabTower — Auth Module
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
# Este módulo lo importan los servicios (WOL, UPS, Net, Proxmox, NAS, DNS, WAN, Resumen y Admin). Cada servicio es
# un proceso distinto, pero todos comparten dos archivos en /var/lib/labtower:
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
#     Imported by the services (WOL, UPS, Net, Proxmox, NAS, DNS, WAN, Overview and Admin). Each service is a separate
#     process, but they all share two files in /var/lib/labtower:
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
import base64, copy, functools, json, os, re, hashlib, hmac, secrets, struct, time, logging, threading, glob, stat, shutil, subprocess, sqlite3
from pathlib import Path

try:
    import fcntl
except ImportError:          # pragma: no cover - solo Linux/macOS
    fcntl = None

# Registro de mensajes; cada servicio decide el formato y el destino (journalctl).
# EN: Message log; each service decides the format and destination (journalctl).
log = logging.getLogger("auth")

# ─── Dos modos de funcionamiento / Two operating modes ──────────────────────────────────────────────────
# ES: Este archivo lo importan todos los servicios, pero NO todos pueden tocar usuarios y sesiones:
#   · Panel de administración (servicio de autenticación, usuario «labtower-auth»): modo LOCAL. Lee y escribe users.json, sessions.json y los
#     contadores de intentos, y atiende por un socket Unix (authrpc.py) a los demás.
#   · Cada uno de los otros módulos (usuario propio, sin acceso a esos archivos): modo REMOTO, activado por LABTOWER_AUTH_SOCKET. get_session,
#     login_session, delete_session, record_event, read_events y check_common hablan con el servicio; las funciones que tocan usuarios o sesiones
#     (load_users, create_session, authenticate…) fallan si se llaman desde un módulo.
#   Sin LABTOWER_AUTH_SOCKET (pruebas, desarrollo) todo es local, como antes.
# EN: Every service imports this file, but NOT every service may touch users and sessions:
#   · Admin Panel (the authentication service, user "labtower-auth"): LOCAL mode. It reads and writes users.json, sessions.json and the attempt
#     counters, and serves the others through a Unix socket (authrpc.py).
#   · Each of the other modules (own user, no access to those files): REMOTE mode, turned on by LABTOWER_AUTH_SOCKET. get_session, login_session,
#     delete_session, record_event, read_events and check_common talk to the service; the functions that touch users or sessions (load_users,
#     create_session, authenticate…) fail when called from a module.
#   Without LABTOWER_AUTH_SOCKET (tests, development) everything is local, as before.
AUTH_SOCKET = os.environ.get("LABTOWER_AUTH_SOCKET", "").strip()
REMOTE = bool(AUTH_SOCKET)

def _local(fn):
    """Mark a function that only the authentication service may run: in a module (remote mode) it raises instead of touching files."""
    @functools.wraps(fn)
    def wrapper(*a, **k):
        if REMOTE: raise RuntimeError(f"auth.{fn.__name__}() is only available in the authentication service")
        return fn(*a, **k)
    return wrapper

# Rutas de los archivos compartidos. Las variables LABTOWER_* permiten cambiarlas en las pruebas
# sin tocar /var/lib/labtower.
# EN: Paths of the shared files. The LABTOWER_* variables let tests move them
#     without touching /var/lib/labtower.
USERS_FILE    = Path(os.environ.get("LABTOWER_USERS",    "/var/lib/labtower/auth/users.json"))
# Carpeta de datos de la instalación y subcarpeta de cada módulo (/var/lib/labtower/<módulo>). El código en /opt/labtower es de solo
# lectura para los servicios: todo lo que escriben vive aquí.
# EN: Data folder of the installation and the sub-folder of each module (/var/lib/labtower/<module>). The code in /opt/labtower is
#     read-only for the services: everything they write lives here.
# Los archivos de autenticación viven en /var/lib/labtower/auth (solo del usuario labtower-auth); cada módulo tiene la suya junto a ella.
# EN: The authentication files live in /var/lib/labtower/auth (readable only by user labtower-auth); each module has its own folder beside it.
DATA_ROOT = (Path(os.environ["LABTOWER_DATA"]) if os.environ.get("LABTOWER_DATA")
             else USERS_FILE.parent.parent if USERS_FILE.parent.name == "auth" else USERS_FILE.parent)
def module_dir(name: str) -> Path:
    """Data folder of a module. Only computes the path: nothing is created (so importing a module has no side effects)."""
    return DATA_ROOT / name

def module_data(name: str) -> Path:
    """Writable data folder of a module (created on demand)."""
    d = module_dir(name)
    try: d.mkdir(parents=True, exist_ok=True)
    except OSError as e: log.warning(f"cannot create {d}: {e}")
    return d

# Prepara la carpeta de datos de un módulo al arrancar (no al importarlo): la crea y adopta los archivos antiguos.
# EN: Prepare a module's data folder at startup (not at import): create it and adopt the old files.
def prepare_module(data_dir, old_dir, names):
    d = Path(data_dir)
    try: d.mkdir(parents=True, exist_ok=True)
    except OSError as e: log.warning(f"cannot create {d}: {e}")
    adopt_legacy(old_dir, d, names)
    return d

# Datos que antes vivían junto al código (versiones < 1.2.0u): si el archivo nuevo no existe, se copia el viejo (las bases SQLite con su API de
# respaldo). En una instalación con paquete, postinst ya los movió; esto cubre ejecuciones de desarrollo.
# EN: Data that used to live next to the code (versions < 1.2.0u): if the new file does not exist the old one is copied (SQLite databases
#     with their backup API). On a packaged install postinst has already moved them; this covers development runs.
def adopt_legacy(old_dir, new_dir, names):
    old_dir, new_dir = Path(old_dir), Path(new_dir)
    for n in names:
        old, new = old_dir / n, new_dir / n
        try:
            if old.is_symlink() or not old.is_file() or new.exists(): continue
            if n.endswith(".db"):
                s_, d_ = sqlite3.connect(f"file:{old}?mode=ro", uri=True), sqlite3.connect(str(new))
                try: s_.backup(d_)
                finally: d_.close(); s_.close()
            else:
                shutil.copyfile(old, new)
            os.chmod(new, 0o600)
            log.info(f"adopted {old} -> {new}")
        except Exception as e:
            log.warning(f"could not adopt {old}: {e}")

# Duración de una sesión sin actividad.
# EN: How long a session lasts without activity.
SESSION_TTL = 24 * 3600   # 24 horas
# Vida máxima de una sesión desde su creación, aunque se siga usando (la ventana deslizante no la alarga): un token robado no vale para siempre.
# EN: Maximum life of a session since its creation, even if it keeps being used (the sliding window does not extend it): a stolen token is not good forever.
ABSOLUTE_MAX = {24 * 3600: 14 * 24 * 3600, 7 * 24 * 3600: 30 * 24 * 3600, 30 * 24 * 3600: 90 * 24 * 3600, 400 * 24 * 3600: 400 * 24 * 3600}
# «Recordarme» en el login: duraciones permitidas (ventana deslizante: cada uso la renueva). El servidor solo acepta estos valores. «forever» son 400 días porque los navegadores limitan la vida de una cookie a ~400 días; mientras se use, no vence hasta ese tope.
# EN: "Remember me" at login: allowed durations (sliding window: every use renews it). The server accepts only these values. "forever" is 400 days because browsers cap a cookie's lifetime at ~400 days; as long as it is used, it does not expire until that cap.
REMEMBER = {"day": 24 * 3600, "week": 7 * 24 * 3600, "month": 30 * 24 * 3600, "forever": 400 * 24 * 3600}
def remember_ttl(value) -> int:
    return REMEMBER.get(value, SESSION_TTL) if isinstance(value, str) else SESSION_TTL
# Cookie de sesión. Por defecto sin «Secure» (LabTower se usa por HTTP en la LAN: con «Secure» el navegador no la enviaría). Si se publica detrás de HTTPS, LABTOWER_SECURE_COOKIE=1 agrega «Secure». No se deduce de encabezados del cliente.
# EN: Session cookie. Without "Secure" by default (LabTower is used over HTTP on the LAN: with "Secure" the browser would not send it). If published behind HTTPS, LABTOWER_SECURE_COOKIE=1 adds "Secure". It is never inferred from client-supplied headers.
SECURE_COOKIE = os.environ.get("LABTOWER_SECURE_COOKIE", "").strip().lower() in ("1", "true", "yes", "on")
def session_cookie(token: str, ttl: int = SESSION_TTL) -> str:
    return (f"session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={ttl if ttl == SESSION_TTL or ttl in REMEMBER.values() else SESSION_TTL}"
            + ("; Secure" if SECURE_COOKIE else ""))
# La ventana deslizante se renueva como máximo cada RENEW_EVERY segundos: renovar en
# cada request reescribiría sessions.json (y la SD) varias veces por segundo.
RENEW_EVERY = 600
SESSIONS_FILE = Path(os.environ.get("LABTOWER_SESSIONS", str(USERS_FILE.with_name("sessions.json"))))


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
    LabTower services) can never interleave their bytes. Files are created with `mode`
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
PUBLISHED_MAX = 4 * 1024 * 1024
def read_published(path, default, typ):
    """Read a JSON file that ANOTHER module publishes (e.g. WOL Console reads Net Monitor's hosts). Treated as untrusted input: symlinks are
    not followed, it must be a regular file, and it is size-capped so a compromised publisher cannot exhaust this process's memory."""
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
    except OSError:
        return default
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > PUBLISHED_MAX: return default
        with os.fdopen(fd, "rb", closefd=False) as f: raw = f.read(PUBLISHED_MAX + 1)
        if len(raw) > PUBLISHED_MAX: return default
        v = json.loads(raw)
        return v if isinstance(v, typ) else default
    except (OSError, ValueError):
        return default
    finally:
        os.close(fd)


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
@_local
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

# Política de contraseñas: mínimo 8 caracteres (sin contar espacios de los extremos), distinta del nombre de usuario y fuera de una lista corta de
# contraseñas evidentes. Devuelve el texto del error (en inglés) o None si es aceptable.
# EN: Password policy: at least 8 characters (ignoring surrounding spaces), different from the username and not in a short list of obvious
#     passwords. Returns the error text (in English) or None when acceptable.
PASSWORD_MIN = 8
_COMMON_PW = {"password", "password1", "12345678", "123456789", "1234567890", "qwerty123", "admin123", "administrator", "letmein1",
              "labtower", "pi-console", "piconsole", "raspberry", "raspberrypi", "11111111", "00000000", "abcd1234", "iloveyou"}
def password_error(pw, username=None):
    if not isinstance(pw, str): return "Invalid password"
    pw = pw.strip()
    if len(pw) < PASSWORD_MIN: return f"Password must be at least {PASSWORD_MIN} characters"
    if len(pw) > 256: return "Password is too long"
    if username and pw.lower() == str(username).lower(): return "Password must be different from the username"
    if pw.lower() in _COMMON_PW: return "That password is too common"
    return None

# Contraseña aleatoria legible (sin 0/O/1/l/I) para la cuenta inicial.
# EN: Readable random password (no 0/O/1/l/I) for the initial account.
def _random_password(n=14):
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))

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
# Cuenta inicial de una instalación nueva: «admin» con una contraseña ALEATORIA (ya no existe admin/admin) y cambio obligatorio en el primer
# inicio de sesión. La contraseña se guarda en initial-admin-password (modo 600) hasta que se cambia, y se muestra al instalar y en el journal.
# EN: Initial account of a fresh install: "admin" with a RANDOM password (admin/admin no longer exists) and a mandatory change at first login.
#     The password is kept in initial-admin-password (mode 600) until it is changed, and shown at install time (never in the journal).
INITIAL_PW_FILE = USERS_FILE.with_name("initial-admin-password")

@_local
def clear_initial_password():
    """Delete the initial-password file (called once the administrator has set their own password)."""
    try: INITIAL_PW_FILE.unlink()
    except OSError: pass

@_local
def ensure_initial_user() -> bool:
    """Create the initial administrator on a fresh install (idempotent, safe across processes). Returns True if created."""
    with users_lock():
        if USERS_FILE.exists() or _initialized():
            return False
        pw = _random_password()
        users = {"admin": {
            "password_hash": _hash(pw),
            "permissions": {"wol": "admin", "nut": "admin", "net": "admin", "pve": "admin", "nas": "admin", "dns": "admin", "wan": "admin"},
            "created": int(time.time()),
            "must_change_password": True,
        }}
        save_users(users)
        try: atomic_write(INITIAL_PW_FILE, pw + "\n")
        except OSError as e: log.warning(f"cannot write {INITIAL_PW_FILE}: {e}")
        # La contraseña NO se escribe en el journal (lo leen otros usuarios del sistema): está en el archivo 0600 y el instalador la muestra.
        # EN: The password is NOT written to the journal (other system users can read it): it is in the 0600 file and the installer shows it.
        log.warning(f"Initial administrator created (user: admin). Password: see {INITIAL_PW_FILE} (mode 600); "
                    f"you must change it at the first login")
        return True

# Caché de users.json: se vuelve a leer del disco solo cuando cambia el archivo (firma = fecha de modificación + tamaño).
# EN: Cache of users.json: re-read from disk only when the file changes (signature = modification time + size).
_ucache = {"sig": None, "data": None}

# Marcador que indica «esta instalación ya tuvo usuarios». Sin él, un users.json borrado reabriría el panel
# con una cuenta inicial nueva; con él, falla cerrado (nadie entra) hasta restaurar el archivo.
# EN: Marker meaning "this install has already had users". Without it, a deleted users.json would reopen the panel
#     with a new initial account; with it, the system fails closed (nobody gets in) until the file is restored.
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
#   1. users.json no existe y la instalación es nueva → se crea el usuario inicial (admin con contraseña aleatoria).
#   2. users.json no existe pero la instalación ya se usó → se usa la copia .bak, o nadie entra.
#   3. users.json existe → se usa (de la caché si no cambió); si está corrupto, la copia .bak.
# Nunca se vuelve a una cuenta por defecto por un archivo dañado o borrado.
# EN: Single source of the users table for the whole module. Decision order:
#       1. users.json is missing and the install is new → the initial user is created (admin with a random password).
#       2. users.json is missing but the install was already used → use the .bak copy, or nobody gets in.
#       3. users.json exists → use it (from the cache if unchanged); if corrupt, the .bak copy.
#     It never falls back to a default account because of a damaged or deleted file.
# Normaliza lo leído de users.json (que puede venir de un respaldo restaurado o de una edición a mano): descarta entradas sin forma de usuario y deja cada nivel
# de permiso en un valor conocido. Así nada raro llega a la interfaz (donde los niveles se usan como nombre de clase) ni a las comprobaciones de permisos.
# EN: Normalise what was read from users.json (it may come from a restored backup or a hand edit): drop entries that are not shaped like a user and leave every
#     permission level at a known value. So nothing odd reaches the UI (where levels are used as a class name) or the permission checks.
_KNOWN_LEVELS = ("none", "readonly", "execute", "admin")
def _sanitize_users(data: dict) -> dict:
    out = {}
    for name, u in data.items():
        if not isinstance(name, str) or not isinstance(u, dict): continue
        u = dict(u)
        perms = u.get("permissions")
        u["permissions"] = ({k: (v if v in _KNOWN_LEVELS else "none") for k, v in perms.items() if isinstance(k, str)}
                            if isinstance(perms, dict) else {})
        out[name] = u
    return out

def _users_cached() -> dict:
    """Parsed users.json (shared object: do not mutate). Re-read only when the file changes.

    * Missing file, never initialised → the initial admin account is created (fresh install only).
    * Missing file after use         → the last good copy (users.json.bak) or NO users.
    * Unreadable/corrupt file       → the last good copy (users.json.bak) or, failing that,
      NO users. It must never fall back to a default account, which would
      silently reopen the panel with well-known credentials after a bad write.
    """
    sig = _file_sig(USERS_FILE)
    if sig is None:
        # users.json missing. Only a genuinely fresh install (no marker, no backup) gets the
        # initial admin; otherwise the file was removed and nobody may log in with defaults.
        if not _initialized():
            try:
                if ensure_initial_user():
                    return _users_cached()
            except Exception as e:
                log.error(f"cannot create the initial administrator: {e}")
            return {}
        sig = ("missing",)
    if sig == _ucache["sig"] and _ucache["data"] is not None:
        return _ucache["data"]
    for p in (USERS_FILE, USERS_FILE.with_name(USERS_FILE.name + ".bak")):
        try:
            data = json.loads(p.read_text())
            if isinstance(data, dict):
                data = _sanitize_users(data)
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
def ensure_permissions(modules=("net", "pve", "nas", "dns", "wan")) -> bool:
    """One-time migration at service start: give every user an EXPLICIT level for `modules`.

    Users that predate a module get "admin" if they administer WOL, else "readonly" (what the
    old runtime fallback granted). After this a missing permission means no access: levels are
    never derived from another module at request time. Returns True if users.json changed.
    Only the authentication service owns users.json: in a module (remote mode) it does nothing."""
    if REMOTE: return False
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
@_local
def load_users() -> dict:
    """A private copy of the users table, safe to modify and pass to save_users()."""
    return copy.deepcopy(_users_cached())

# Guarda la tabla de usuarios: copia .bak de la versión anterior, escritura atómica, marcador de «ya usada»
# y refresco de la caché. Debe llamarse dentro de «with users_lock()».
# EN: Save the users table: .bak copy of the previous version, atomic write, "already used" marker and cache
#     refresh. It must be called inside "with users_lock()".
@_local
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

# Los tokens NO se guardan en claro: sessions.json y los respaldos solo contienen su SHA-256, así que leer el archivo no permite usar una sesión.
# EN: Tokens are NOT stored in clear: sessions.json and backups only hold their SHA-256, so reading the file does not let anyone use a session.
def _tkey(token: str) -> str:
    return hashlib.sha256(str(token).encode()).hexdigest()

# Abre una sesión: token aleatorio de 256 bits. Se guardan usuario, permisos al momento del login y
# vencimiento. Aprovecha para purgar las sesiones vencidas.
# EN: Open a session: random 256-bit token. Stores the user, the permissions at login time and the expiry.
#     It takes the chance to purge expired sessions.
@_local
def create_session(username: str, permissions: dict, ttl: int = SESSION_TTL, handler=None) -> str:
    if ttl != SESSION_TTL and ttl not in REMEMBER.values(): ttl = SESSION_TTL
    token = secrets.token_hex(32)
    meta = {}
    if handler is not None:     # IP y navegador, solo para mostrarlos en «Sesiones activas» / EN: IP and browser, only to show them in "Active sessions"
        try:
            meta = {"ip": client_ip(handler)[:64],
                    "ua": re.sub(r"[\x00-\x1f\x7f]", "", handler.headers.get("User-Agent") or "")[:200]}
        except Exception:
            meta = {}
    with _sessions_lock:
        sessions = _load_sessions()
        sessions[_tkey(token)] = {
            "username":    username,
            "permissions": permissions,
            "expires":     time.time() + ttl,
            "ttl":         ttl,
            "created":     time.time(),
            **meta,
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
# Devuelve la sesión del token (o None). Si la cuenta tiene must_change_password (primer ingreso con la contraseña inicial, o marcada por un admin), la sesión NO es válida para nada, salvo para cambiar la contraseña (allow_pending=True): así ningún módulo da acceso hasta que se cambie.
# EN: Return the session of the token (or None). If the account has must_change_password (first login with the initial password, or flagged by an admin), the session is NOT valid for anything except changing the password (allow_pending=True): no module grants access until it is changed.
def get_session(token: str, allow_pending: bool = False) -> dict | None:
    if not token: return None
    if REMOTE: return _remote_session(token, allow_pending)
    return _get_session_local(token, allow_pending)

def _get_session_local(token: str, allow_pending: bool = False) -> dict | None:
    key = _tkey(token)
    with _sessions_lock:
        sessions = _load_sessions()
        s = sessions.get(key)
        if not s: return None
        now = time.time()
        ttl0 = s.get("ttl", SESSION_TTL)
        cap  = ABSOLUTE_MAX.get(ttl0, 14 * 24 * 3600)
        if now > s.get("expires", 0) or now - s.get("created", now) > cap:
            sessions.pop(key, None); _save_sessions(sessions); return None
        # The account must still exist, and the permissions are always the current ones:
        # deleting or demoting a user takes effect immediately instead of when the session expires.
        user = _users_cached().get(s.get("username"))
        if user is None:
            sessions.pop(key, None); _save_sessions(sessions); return None
        # Ventana deslizante de 24h, pero persistida solo si pasaron > RENEW_EVERY s
        # desde la última renovación (evita una escritura a disco por request).
        ttl = s.get("ttl", SESSION_TTL)
        if ttl != SESSION_TTL and ttl not in REMEMBER.values(): ttl = SESSION_TTL
        if s["expires"] - now < ttl - RENEW_EVERY:
            s["expires"] = now + ttl
            sessions[key] = s
            _save_sessions(sessions)
        if user.get("must_change_password") and not allow_pending:
            return None
        return {**s, "permissions": dict(user.get("permissions", {})),
                "must_change_password": bool(user.get("must_change_password"))}

# Cierre de sesión (logout).
# EN: Logout.
def delete_session(token: str):
    if REMOTE:
        with _remote_cache_lock:                      # drop the cached answer first: a closed session must not survive for the cache's second
            for pending in (False, True): _remote_cache.pop((_tkey(token), pending), None)
        try: _rpc("logout", token=token)
        except Exception as e: log.warning(f"logout: {e}")
        return
    with _sessions_lock:
        sessions = _load_sessions()
        if sessions.pop(_tkey(token), None) is not None:
            _save_sessions(sessions)

# Cierra todas las sesiones de un usuario (cambio de contraseña o eliminación), dejando opcionalmente una.
# EN: Close all the sessions of a user (password change or removal), optionally keeping one.
@_local
def delete_user_sessions(username: str, keep: str | None = None):
    """Log a user out everywhere (password change, account removal), optionally keeping one session."""
    keep_key = _tkey(keep) if keep else None
    with _sessions_lock:
        sessions = _load_sessions()
        gone = [t for t, s in sessions.items() if s.get("username") == username and t != keep_key]
        for t in gone: del sessions[t]
        if gone: _save_sessions(sessions)

# Sesiones activas para el panel Admin. El id es un prefijo del SHA-256 del token (no sirve para usar la sesión).
# «last» es la última renovación (se persiste como máximo cada RENEW_EVERY s), así que es aproximada.
# EN: Active sessions for the Admin panel. The id is a prefix of the token's SHA-256 (useless to use the session).
#     "last" is the last renewal (persisted at most every RENEW_EVERY s), so it is approximate.
@_local
def list_sessions(current_token: str | None = None) -> list:
    cur = _tkey(current_token)[:16] if current_token else None
    now = time.time()
    with _sessions_lock:
        sessions = _load_sessions()
    out = []
    for k, v in sessions.items():
        if now > v.get("expires", 0): continue
        ttl = v.get("ttl", SESSION_TTL)
        out.append({"id": k[:16], "username": v.get("username", ""),
                    "created": v.get("created"), "last": v.get("expires", 0) - ttl,
                    "expires": v.get("expires", 0), "ttl": ttl,
                    "ip": v.get("ip", ""), "ua": v.get("ua", ""), "current": k[:16] == cur})
    out.sort(key=lambda x: x["last"], reverse=True)
    return out

# Cierra una sesión por su id; devuelve el nombre de usuario o None. `allow(username)` decide si se puede cerrar.
# EN: Close a session by its id; returns the username or None. `allow(username)` decides whether it may be closed.
@_local
def revoke_session_id(sid: str, allow=None, keep: str | None = None):
    if not re.fullmatch(r"[0-9a-f]{16}", sid or ""): return None
    keep_id = _tkey(keep)[:16] if keep else None
    with _sessions_lock:
        sessions = _load_sessions()
        found = [k for k in sessions if k[:16] == sid]
        if len(found) != 1 or sid == keep_id: return None
        uname = sessions[found[0]].get("username", "")
        if allow and not allow(uname): return False
        del sessions[found[0]]; _save_sessions(sessions)
    return uname

# Elimina las sesiones vencidas del diccionario recibido.
# EN: Remove the expired sessions from the given dictionary.
def _purge(sessions: dict):
    now = time.time()
    for t in [k for k, v in sessions.items() if now > v.get("expires", 0)]:
        del sessions[t]


# ─── Cliente del servicio de autenticación (modo remoto) ─────────────────────────────────────────────
# ES: En un módulo, la sesión de un token la valida el servicio. El resultado se recuerda un segundo por token (una petición HTTP consulta los
#     permisos varias veces): borrar o degradar a un usuario sigue surtiendo efecto casi al instante. Si el servicio no responde, la sesión se
#     considera no válida (falla cerrado).
# EN: In a module, a token's session is validated by the service. The result is remembered for one second per token (one HTTP request checks
#     the permissions several times): deleting or demoting a user still takes effect almost at once. If the service does not answer, the
#     session counts as invalid (fails closed).
_remote_cache: dict = {}
_remote_cache_lock = threading.Lock()
REMOTE_CACHE_SECONDS = 1.0

# Cortacircuito: si el servicio no responde, durante 1 s las demás peticiones fallan al instante en vez de esperar cada una (hilos bloqueados) y se anota UN aviso.
# EN: Circuit breaker: if the service does not answer, for 1 s the other requests fail at once instead of each waiting (blocked threads), and ONE warning is logged.
_rpc_down_until = 0.0

def _rpc(op, retries=6, **fields):
    global _rpc_down_until
    import authrpc
    if time.monotonic() < _rpc_down_until: raise authrpc.AuthUnavailable("authentication service unavailable")
    try:
        return authrpc.call(AUTH_SOCKET, op, retries=retries, **fields)
    except authrpc.AuthUnavailable as e:
        if retries > 1 or time.monotonic() >= _rpc_down_until:
            _rpc_down_until = time.monotonic() + 1.0
            log.warning(f"authentication service unavailable: {e}")
        raise

def _remote_session(token: str, allow_pending: bool):
    key = (_tkey(token), bool(allow_pending))
    now = time.monotonic()
    with _remote_cache_lock:
        hit = _remote_cache.get(key)
        if hit and now - hit[0] < REMOTE_CACHE_SECONDS: return copy.deepcopy(hit[1])
    try:
        r = _rpc("session", token=token, allow_pending=bool(allow_pending))
    except Exception:                                  # _rpc already logged it (once per second)
        return None
    sess = r.get("session") if isinstance(r.get("session"), dict) else None
    with _remote_cache_lock:
        if len(_remote_cache) > 512:
            for k in [k for k, v in _remote_cache.items() if now - v[0] >= REMOTE_CACHE_SECONDS]: del _remote_cache[k]
            if len(_remote_cache) > 2048: _remote_cache.clear()     # hard cap: a flood of bogus tokens cannot grow memory
        _remote_cache[key] = (now, sess)
    return copy.deepcopy(sess)

# ─── Helpers ──────────────────────────────────────────────────────────────────
# Niveles de permiso ordenados: un nivel mayor incluye a los menores (admin puede lo que puede execute y readonly).
# EN: Permission levels in order: a higher level includes the lower ones (admin can do what execute and readonly can).
LEVELS = {"readonly": 1, "execute": 2, "admin": 3}

# Verifica usuario y contraseña y devuelve una copia del usuario, o None.
# Si la contraseña es correcta pero el hash es del formato antiguo, lo reemplaza por scrypt en ese momento.
# EN: Check username and password and return a copy of the user, or None.
#     If the password is right but the hash is in the old format, it is replaced by scrypt right then.
@_local
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
                    users[username]["must_change_password"] = True    # old fixed-salt hash: ask for a new password
                    save_users(users)
            user = copy.deepcopy(user); user["must_change_password"] = True
        except Exception as e:
            log.warning(f"could not upgrade the password hash of {username}: {e}")
    return copy.deepcopy(user)


# ─── Límite de intentos (compartido) ──────────────────────────────────────────────
# Los contadores viven en login-throttle.json (con candado entre procesos), así que los 6 servicios comparten la misma cuenta: probar contraseñas
# en otro módulo ya no da más intentos. Se lleva una cuenta por IP (MAX_FAILS fallos en WINDOW s bloquean esa IP LOCKOUT s) y otra por cuenta de
# usuario (ACCOUNT_FAILS fallos, desde cualquier IP, la bloquean LOCKOUT s). El mismo mecanismo protege el cambio de contraseña. Si el archivo no se
# puede usar se cae a contadores en memoria.
# EN: ─── Attempt limiting (shared) ─────────────────────────────────────────────────────
#     The counters live in login-throttle.json (with a cross-process lock), so the 6 services share the same count: guessing passwords on another
#     module no longer gives more attempts. One count per IP (MAX_FAILS failures within WINDOW s lock that IP for LOCKOUT s) and one per user account
#     (ACCOUNT_FAILS failures, from any IP, lock it for LOCKOUT s). The same mechanism protects password changes. If the file cannot be used it
#     falls back to in-memory counters.
MAX_FAILS, WINDOW, LOCKOUT = 5, 600, 300
try: ACCOUNT_FAILS = max(5, int(os.environ.get("LABTOWER_LOGIN_MAX_ACCOUNT", "20")))
except ValueError: ACCOUNT_FAILS = 20
THROTTLE_FILE = Path(os.environ.get("LABTOWER_THROTTLE", str(USERS_FILE.with_name("login-throttle.json"))))
_throttle_lock = FileLock(THROTTLE_FILE.with_name(THROTTLE_FILE.name + ".lock"))
_mem_fails: dict = {}
_mem_lock = threading.Lock()

def _th_read():
    try:
        d = json.loads(THROTTLE_FILE.read_text())
        return d if isinstance(d, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        log.warning(f"{THROTTLE_FILE}: {e}")
        return {}

@_local
def throttle_wait(key: str) -> int:
    """Seconds the caller must still wait for `key` (an IP, account or other string); 0 when it may proceed."""
    now = time.time()
    f = _th_read().get(key)
    w = int(f["lock"] - now) + 1 if isinstance(f, dict) and f.get("lock", 0) > now else 0
    with _mem_lock:
        m = _mem_fails.get(key)
        if m and m.get("lock", 0) > now: w = max(w, int(m["lock"] - now) + 1)
    return w

def _th_bump(d: dict, key: str, now: float, max_fails: int, window: int, lockout: int) -> bool:
    if len(d) > 2048:
        for k in [k for k, v in d.items() if not isinstance(v, dict) or (v.get("lock", 0) < now and now - v.get("first", 0) > window)]: del d[k]
    f = d.get(key)
    if not isinstance(f, dict) or now - f.get("first", 0) > window: f = d[key] = {"n": 0, "first": now, "lock": 0}
    f["n"] = f.get("n", 0) + 1
    if f["n"] >= max_fails:
        f["lock"], f["n"], f["first"] = now + lockout, 0, now
        return True
    return False

@_local
def throttle_fail(key: str, max_fails: int = MAX_FAILS, window: int = WINDOW, lockout: int = LOCKOUT) -> bool:
    """Count one failure for `key`; returns True when it has just been locked."""
    now = time.time()
    try:
        with _throttle_lock:
            d = _th_read()
            locked = _th_bump(d, key, now, max_fails, window, lockout)
            atomic_write(THROTTLE_FILE, json.dumps(d))
        return locked
    except Exception as e:
        log.warning(f"login-throttle file unusable, using memory: {e}")
        with _mem_lock:
            return _th_bump(_mem_fails, key, now, max_fails, window, lockout)

@_local
def throttle_clear(key: str):
    try:
        with _throttle_lock:
            d = _th_read()
            if d.pop(key, None) is not None: atomic_write(THROTTLE_FILE, json.dumps(d))
    except Exception:
        pass
    with _mem_lock: _mem_fails.pop(key, None)

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

# ¿La petición viene directamente de esta máquina (sin pasar por nginx)? Es el caso de labtower-health y de los demás servicios.
# EN: Does the request come straight from this machine (not through nginx)? That is the case of labtower-health and of the other services.
def is_local_request(handler) -> bool:
    return handler.client_address[0] in ("127.0.0.1", "::1") and not (handler.headers.get("X-Real-IP") or "").strip()

# Nombre de archivo seguro para cabeceras (Content-Disposition): solo letras, números, punto, guion y guion bajo.
# EN: Safe file name for headers (Content-Disposition): only letters, digits, dot, dash and underscore.
def safe_filename(name, maxlen: int = 120) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(name))[:maxlen] or "file"

# ¿Es un nombre de host o una IP razonable? Nunca empieza con «-» ni lleva espacios, «/», «@» ni otros caracteres especiales (se usa en conexiones y comandos).
# EN: Is it a reasonable host name or IP? It never starts with "-" and has no spaces, "/", "@" or other special characters (used in connections and commands).
_HOSTNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,251}[A-Za-z0-9])?$")
def valid_host(h) -> bool:
    if not isinstance(h, str) or not h or len(h) > 253: return False
    if _HOSTNAME_RE.fullmatch(h): return True
    try:
        import ipaddress
        ipaddress.ip_address(h); return True
    except ValueError:
        return False

# Destino al que el servidor se conectará por orden de un administrador de módulo (Proxmox, NAS, DNS, Pi-hole, switches): además de ser un host válido, no puede
# ser la propia máquina (loopback, 0.0.0.0) ni una dirección de enlace local (169.254.x.x, p. ej. el servicio de metadatos de una nube), ni un nombre que resuelva
# a una de ellas. Evita usar a LabTower como «puente» hacia sus propios servicios internos o hacia los metadatos (SSRF). No se aplica a NUT ni a los objetivos
# de ping/TCP, donde mirar la propia máquina es legítimo.
# EN: Destination the server will connect to on a module administrator's order (Proxmox, NAS, DNS, Pi-hole, switches): besides being a valid host, it cannot be
#     the machine itself (loopback, 0.0.0.0) nor a link-local address (169.254.x.x, e.g. a cloud metadata service), nor a name resolving to one of them. It keeps
#     LabTower from being used as a "bridge" to its own internal services or to metadata (SSRF). Not applied to NUT or to ping/TCP targets, where looking at the
#     own machine is legitimate.
def valid_target(h) -> bool:
    import ipaddress, socket
    if not valid_host(h): return False
    name = h.strip("[]").lower()
    if name == "localhost" or name.endswith(".localhost"): return False
    def bad(a):
        try: ip = ipaddress.ip_address(a.split("%")[0])
        except ValueError: return True
        if getattr(ip, "ipv4_mapped", None): ip = ip.ipv4_mapped
        return ip.is_loopback or ip.is_unspecified or ip.is_link_local or ip.is_multicast
    try:
        ipaddress.ip_address(name); return not bad(name)
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(name, None, proto=socket.IPPROTO_TCP)
    except OSError:
        return True            # does not resolve (yet): the connection will simply fail; nothing to protect against
    return not any(bad(i[4][0]) for i in infos)

# ─── Segundo factor (TOTP, RFC 6238) ─────────────────────────────────────────────────────────────────
# ES: Código de 6 dígitos cada 30 s (compatible con Google Authenticator, Aegis, 1Password…). El secreto vive en users.json (0600, solo labtower-auth).
#     Cada código se acepta UNA vez (se recuerda el último intervalo usado) y hay 10 códigos de recuperación de un solo uso, guardados como SHA-256.
# EN: 6-digit code every 30 s (works with Google Authenticator, Aegis, 1Password…). The secret lives in users.json (0600, labtower-auth only).
#     Every code is accepted ONCE (the last used time step is remembered) and there are 10 single-use recovery codes, stored as SHA-256.
NEED_CODE = "2FA code required"
TOTP_ISSUER = "LabTower"

def totp_new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")

def totp_at(secret: str, step: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    h = hmac.new(key, struct.pack(">Q", step), "sha1").digest()
    o = h[-1] & 15
    return "%06d" % ((int.from_bytes(h[o:o + 4], "big") & 0x7fffffff) % 1000000)

def totp_check(secret: str, code, last: int = 0, now: float | None = None) -> int | None:
    """Return the time step of a valid code (±1 step of tolerance, never one already used), or None."""
    code = re.sub(r"\s", "", code) if isinstance(code, str) else ""
    if not re.fullmatch(r"\d{6}", code): return None
    step = int((time.time() if now is None else now) // 30)
    ok = None
    for s in (step - 1, step, step + 1):
        if hmac.compare_digest(totp_at(secret, s), code) and s > last: ok = s
    return ok

def totp_uri(username: str, secret: str) -> str:
    from urllib.parse import quote
    return f"otpauth://totp/{quote(TOTP_ISSUER)}:{quote(username)}?secret={secret}&issuer={quote(TOTP_ISSUER)}&algorithm=SHA1&digits=6&period=30"

def _rkey(code: str) -> str:
    return hashlib.sha256(re.sub(r"[^0-9a-z]", "", str(code).lower()).encode()).hexdigest()

def _new_recovery() -> list:
    return ["%s-%s" % (secrets.token_hex(2), secrets.token_hex(2)) for _ in range(10)]

@_local
def totp_status(username: str) -> dict:
    t = (_users_cached().get(username) or {}).get("totp")
    return {"enabled": bool(t), "recovery_left": len(t.get("recovery", [])) if t else 0, "since": t.get("since") if t else None}

# Genera un secreto nuevo (pendiente hasta confirmar con un código). / EN: Generate a new secret (pending until confirmed with a code).
@_local
def totp_begin(username: str):
    with users_lock():
        users = load_users()
        if username not in users: return None
        if users[username].get("totp"): return None
        sec = totp_new_secret()
        users[username]["totp_pending"] = sec
        save_users(users)
    return {"secret": sec, "uri": totp_uri(username, sec)}

# Confirma con un código del autenticador, activa el 2FA y devuelve los códigos de recuperación (única vez que se ven).
# EN: Confirm with a code from the authenticator, turn 2FA on and return the recovery codes (the only time they are shown).
@_local
def totp_enable(username: str, code):
    with users_lock():
        users = load_users()
        u = users.get(username)
        if not u or not u.get("totp_pending"): return None, "Start the setup first"
        step = totp_check(u["totp_pending"], code)
        if step is None: return None, "Invalid code"
        rec = _new_recovery()
        u["totp"] = {"secret": u.pop("totp_pending"), "last": step, "since": int(time.time()), "recovery": [_rkey(c) for c in rec]}
        save_users(users)
    return rec, None

@_local
def totp_disable(username: str) -> bool:
    with users_lock():
        users = load_users()
        u = users.get(username)
        if not u or not (u.get("totp") or u.get("totp_pending")): return False
        u.pop("totp", None); u.pop("totp_pending", None)
        save_users(users)
    return True

# Comprueba el segundo factor de un usuario con contraseña ya verificada: "ok" (sin 2FA o código válido), "need" (falta el código) o "bad".
# EN: Check the second factor of a user whose password is already verified: "ok" (no 2FA or valid code), "need" (code missing) or "bad".
def _second_factor(username: str, code) -> str:
    if not (_users_cached().get(username) or {}).get("totp"): return "ok"
    if not isinstance(code, str) or not code.strip(): return "need"
    with users_lock():
        users = load_users()
        t = (users.get(username) or {}).get("totp")
        if not t: return "ok"
        step = totp_check(t["secret"], code, int(t.get("last", 0)))
        if step is not None:
            t["last"] = step; save_users(users); return "ok"
        k = _rkey(code)
        if k in t.get("recovery", []):
            t["recovery"].remove(k); save_users(users)
            audit(username, "2fa_recovery_used", username, f"{len(t['recovery'])} left")
            return "ok"
    return "bad"


# Registra un inicio de sesión fallido (por IP y por cuenta).
# EN: Record a failed login (per IP and per account).
@_local
def login_failed(handler, username):
    ip = client_ip(handler)
    uname = username.strip().lower()[:64] if isinstance(username, str) else ""
    if throttle_fail("ip:" + ip):
        log.warning(f"login locked for {ip} after {MAX_FAILS} failed attempts")
        audit(uname or "?", "lockout_ip", ip, f"{MAX_FAILS} failed attempts", ip)
    if uname and throttle_fail("u:" + uname, ACCOUNT_FAILS):
        log.warning(f"account {uname!r} locked after {ACCOUNT_FAILS} failed attempts")
        audit(uname, "lockout_account", uname, f"{ACCOUNT_FAILS} failed attempts", ip)

# Inicio de sesión con límite de intentos. Devuelve (usuario, None) si entra, o (None, (código, mensaje)):
# 429 si la IP o la cuenta están bloqueadas, 401 si las credenciales son inválidas (con una pausa de 0,3 s).
# EN: Login with attempt limiting. Returns (user, None) on success, or (None, (code, message)):
#     429 if the IP or the account is locked, 401 for invalid credentials (with a 0.3 s pause).
@_local
def login(handler, username, password, code=None):
    """Throttled login: returns (user, None) or (None, (http_status, message)). With 2FA on, the message is NEED_CODE when the code is missing."""
    ip = client_ip(handler)
    uname = username.strip().lower()[:64] if isinstance(username, str) else ""
    wait = max(throttle_wait("ip:" + ip), throttle_wait("u:" + uname) if uname else 0)
    if wait:
        return None, (429, f"Too many failed attempts. Try again in {wait} s")
    u = authenticate(username, password)
    if u:
        sf = _second_factor(username, code)
        if sf == "need": return None, (401, NEED_CODE)
        if sf == "bad":
            login_failed(handler, username)
            audit(username, "2fa_failed", username, "", client_ip(handler))
            time.sleep(0.3)
            return None, (401, "Invalid code")
        # Solo se limpia el contador de la CUENTA. El de la IP NO: si no, quien conoce una cuenta propia (p. ej. un invitado) podría entrar entre
        # intentos y reiniciar la cuenta para adivinar otras contraseñas sin límite. El contador de la IP caduca solo con su ventana.
        # EN: Only the ACCOUNT counter is cleared. The IP counter is NOT: otherwise someone who owns an account (a guest, say) could log in between
        #     attempts and reset the count to guess other passwords without limit. The IP counter expires by itself with its window.
        if uname: throttle_clear("u:" + uname)
        audit(username, "login", username, "2fa" if (u.get("totp")) else "", ip)
        return u, None
    login_failed(handler, username)
    time.sleep(0.3)
    return None, (401, "Invalid credentials")

# Inicio de sesión completo: verifica usuario y contraseña (con límite de intentos) y abre la sesión. Es lo que usan TODOS los módulos. Devuelve
# ({"token", "ttl", "username", "permissions", "must_change_password"}, None) o (None, (código, mensaje)). En un módulo (modo remoto) lo hace el servicio de
# autenticación: el módulo manda la contraseña una vez y recibe solo el token; no hay forma de abrir una sesión sin contraseña.
# EN: Complete login: checks username and password (with attempt limiting) and opens the session. It is what EVERY module uses. Returns
#     ({"token", "ttl", "username", "permissions", "must_change_password"}, None) or (None, (code, message)). In a module (remote mode) the
#     authentication service does it: the module sends the password once and gets back only the token; there is no way to open a session without a password.
def login_session(handler, username, password, remember=None, code=None):
    ttl = remember_ttl(remember)
    if code is not None and not isinstance(code, str): code = None
    if not isinstance(username, str) or not isinstance(password, str):
        return None, (400, "Invalid request body")
    if REMOTE:
        try:
            ua = re.sub(r"[\x00-\x1f\x7f]", "", handler.headers.get("User-Agent") or "")[:200]
            r = _rpc("login", ip=client_ip(handler), ua=ua, username=username, password=password, remember=remember, code=(code or "")[:32])
        except Exception:
            return None, (503, "Authentication service unavailable")
        if isinstance(r.get("login"), dict): return r["login"], None
        code = r.get("status") if isinstance(r.get("status"), int) else 500
        return None, (code, str(r.get("error") or "Login failed")[:200])
    u, err = login(handler, username, password, code)
    if not u: return None, err
    token = create_session(username, u["permissions"], ttl, handler)
    return {"token": token, "ttl": ttl, "username": username, "permissions": u["permissions"],
            "must_change_password": bool(u.get("must_change_password", False))}, None

# Freno para operaciones que verifican una contraseña con la sesión ya abierta (cambio de contraseña): 5 fallos en 10 min bloquean 5 min.
# EN: Brake for operations that verify a password with a session already open (password change): 5 failures in 10 min lock for 5 min.
@_local
def password_guard_wait(username) -> int:
    return throttle_wait("pw:" + str(username))
@_local
def password_guard_fail(username):
    throttle_fail("pw:" + str(username))
@_local
def password_guard_ok(username):
    throttle_clear("pw:" + str(username))

# ¿La sesión del token tiene al menos el nivel «required» sobre el recurso (wol, nut, net, pve)?
# EN: Does the token's session have at least the "required" level on the resource (wol, nut, net, pve, nas, dns, wan)?
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


# ─── Defensa CSRF ─────────────────────────────────────────────────────────────
# SameSite=Strict no distingue puertos ni subdominios del mismo host, y un POST «text/plain» no necesita preflight CORS: otra página del
# mismo host podría escribir con la sesión del usuario. Toda petición que modifica datos se rechaza si el navegador dice que no es del mismo origen.
# Sec-Fetch-Site (navegadores modernos) manda; si falta (Safari/iOS antiguos) se compara el host de «Origin» con el de «Host» (nginx pasa Host sin puerto).
# Sin ninguna de las dos cabeceras (curl, scripts) no hay cookie ambiente que abusar y se permite.
# EN: CSRF defence. SameSite=Strict does not tell ports or sibling subdomains of the same host apart, and a "text/plain" POST needs no CORS
#     preflight: another page on the same host could write with the user's session. Every request that changes data is rejected when the browser
#     says it is not same-origin. Sec-Fetch-Site (modern browsers) decides; if missing (old Safari/iOS) the host of "Origin" is compared with "Host"
#     (nginx passes Host without the port). With neither header (curl, scripts) there is no ambient cookie to abuse, so it is allowed.
def cross_origin(headers) -> bool:
    site = headers.get("Sec-Fetch-Site")
    if site is not None:
        return site.strip().lower() not in ("same-origin", "none")
    origin = headers.get("Origin")
    if origin is None:
        return False
    try:
        from urllib.parse import urlsplit
        oh = (urlsplit(origin).hostname or "").lower()
    except ValueError:
        return True
    hh = headers.get("Host", "").strip().lower()
    hh = hh[1:hh.index("]")] if hh.startswith("[") and "]" in hh else hh.split(":")[0]
    if not oh or oh != hh:
        return True
    # nginx añade X-Forwarded-Proto/Port (los servicios solo escuchan en 127.0.0.1, así que el cliente no puede falsearlos): si están, también deben coincidir esquema y puerto.
    # EN: nginx adds X-Forwarded-Proto/Port (the services listen on 127.0.0.1 only, so the client cannot forge them): when present, scheme and port must match too.
    proto = (headers.get("X-Forwarded-Proto") or "").strip().lower()
    port = (headers.get("X-Forwarded-Port") or "").strip()
    if proto in ("http", "https") or port.isdigit():
        try:
            parts = urlsplit(origin)
            if proto in ("http", "https") and parts.scheme.lower() != proto:
                return True
            if port.isdigit() and (parts.port or {"http": 80, "https": 443}.get(parts.scheme.lower(), 0)) != int(port):
                return True
        except ValueError:
            return True
    return False


# ─── Archivos estáticos de las páginas (.js / .css) ──────────────────────────
# Las páginas no llevan JavaScript ni <style> en línea (CSP sin 'unsafe-inline'): su código y su CSS se sirven como archivos aparte desde la
# carpeta static/ de cada módulo. Solo nombres simples «<nombre>.js|css» (sin rutas), archivos normales (nunca enlaces) y con ETag para que el
# navegador revalide en vez de volver a descargar.
# EN: Static page files (.js / .css). The pages carry no inline JavaScript or <style> (CSP without 'unsafe-inline'): their code and CSS are served as separate
#     files from each module's static/ folder. Plain names only (no paths), regular files (never links), with an ETag so the browser revalidates.
_ASSET_RE    = re.compile(r"/([a-z0-9][a-z0-9._-]{0,40})\.(js|css)")
_ASSET_TYPES = {"js": "application/javascript; charset=utf-8", "css": "text/css; charset=utf-8"}

def serve_asset(handler, static_dir, path) -> bool:
    """Serve static_dir/<name>.js|css for a request path like /app.js. Returns True if it answered."""
    m = _ASSET_RE.fullmatch(path or "")
    if not m: return False
    p = Path(static_dir) / f"{m.group(1)}.{m.group(2)}"
    try:
        if p.is_symlink() or not p.is_file(): return False
        st = p.stat(); data = p.read_bytes()
    except OSError:
        return False
    etag = '"%x-%x"' % (int(st.st_mtime), st.st_size)
    handler.send_response(304 if handler.headers.get("If-None-Match") == etag else 200)
    handler.send_header("ETag", etag)
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("X-Content-Type-Options", "nosniff")
    if handler.headers.get("If-None-Match") == etag:
        handler.end_headers(); return True
    handler.send_header("Content-Type", _ASSET_TYPES[m.group(2)])
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers(); handler.wfile.write(data)
    return True

# ─── Version ──────────────────────────────────────────────────────────────────
# Versión instalada: la variable LABTOWER_VERSION si existe; si no, el archivo VERSION de la raíz de la instalación.
# EN: Installed version: the LABTOWER_VERSION variable if set; otherwise the VERSION file at the install root.
def version() -> str:
    """Installed LabTower version: $LABTOWER_VERSION, else the VERSION file at the install root."""
    v = os.environ.get("LABTOWER_VERSION", "").strip()
    if v: return v
    try:
        return (Path(__file__).resolve().parent.parent / "VERSION").read_text().strip() or "dev"
    except OSError:
        return "dev"


# ─── Eventos (línea de tiempo del Resumen) ────────────────────────────────────────────────
# Los módulos anotan aquí los cambios de estado importantes (UPS a batería, host nuevo, nodo caído…) y la
# página Resumen los muestra como línea de tiempo. Se guardan pocos y se usa el mismo candado entre procesos
# que en los demás archivos compartidos.
# EN: ─── Events (Overview timeline) ─────────────────────────────────────────────────────────
#     Modules record important state changes here (UPS on battery, new host, node down…) and the Overview
#     page shows them as a timeline. Few are kept and the same cross-process lock as other shared files is used.
EVENTS_FILE  = Path(os.environ.get("LABTOWER_EVENTS", str(USERS_FILE.with_name("events.json"))))
EVENTS_MAX   = 300                      # entries kept
EVENTS_DAYS  = 30                       # entries older than this are dropped
_events_lock = FileLock(EVENTS_FILE.with_name(EVENTS_FILE.name + ".lock"))
_state_seen: dict = {}                  # last state seen per key, in THIS process only

# Anota un evento. level: "info", "warn" o "crit". Nunca lanza excepción: un fallo al anotar no debe afectar al módulo.
# EN: Record an event. level: "info", "warn" or "crit". Never raises: a failure to record must not affect the module.
def record_event(module, level, text, k=None, **params):
    """Append an event {t, m, lv, tx[, k, p]} to events.json (best effort). `text` is the English message; `k` + `params`
    let the page translate it (it falls back to `text` for unknown keys). In a module the authentication service writes it,
    and records it under the module's own name (taken from the operating-system user, not from `module`)."""
    if REMOTE:
        try: _rpc("event", retries=1, level=level, text=str(text)[:200], k=k, params={a: b for a, b in params.items() if isinstance(b, (int, float, str))})
        except Exception as e: log.debug(f"record_event: {e}")
        return
    try:
        now = int(time.time())
        with _events_lock:
            ev = read_json(EVENTS_FILE, [], list)
            ev = [e for e in ev if isinstance(e, dict) and now - int(e.get("t", 0)) < EVENTS_DAYS * 86400]
            if ev and ev[-1].get("m") == module and ev[-1].get("tx") == text and now - int(ev[-1].get("t", 0)) < 60:
                return                                  # same event just recorded
            e = {"t": now, "m": module, "lv": level, "tx": str(text)[:200]}
            if k: e["k"] = k; e["p"] = {a: (b if isinstance(b, (int, float)) else str(b)[:80]) for a, b in params.items()}
            ev.append(e)
            write_json(EVENTS_FILE, ev[-EVENTS_MAX:], indent=None)
    except Exception as e:
        log.debug(f"record_event: {e}")

# ─── Registro de auditoría ───────────────────────────────────────────────────────────────────────────
# ES: Quién cambió qué y cuándo (usuarios, permisos, contraseñas, 2FA, sesiones, respaldos, bloqueos). Es un archivo de líneas JSON que solo escribe el servicio de
#     autenticación; se conservan las últimas AUDIT_MAX entradas. Nunca guarda contraseñas, códigos ni tokens.
# EN: Who changed what and when (users, permissions, passwords, 2FA, sessions, backups, lockouts). A JSON-lines file written only by the authentication service;
#     the last AUDIT_MAX entries are kept. It never stores passwords, codes or tokens.
AUDIT_FILE = Path(os.environ.get("LABTOWER_AUDIT", str(USERS_FILE.with_name("audit.log"))))
AUDIT_MAX  = 5000
_audit_lock = FileLock(AUDIT_FILE.with_name(AUDIT_FILE.name + ".lock"))
_audit_lines = [0]

def audit(actor, action, target="", detail="", ip="", module="auth"):
    """Append {t, a (actor), x (action), g (target), d (detail), ip, m} to the audit log. Never raises. In a module the service writes it as the module."""
    clean = lambda v, n: re.sub(r"[\x00-\x1f\x7f]", " ", str(v or ""))[:n]
    if REMOTE:
        try: _rpc("audit", retries=1, actor=clean(actor, 64), action=clean(action, 48), target=clean(target, 128), detail=clean(detail, 200), ip=clean(ip, 64))
        except Exception as e: log.debug(f"audit: {e}")
        return
    try:
        rec = json.dumps({"t": int(time.time()), "a": clean(actor, 64), "x": clean(action, 48), "g": clean(target, 128),
                          "d": clean(detail, 200), "ip": clean(ip, 64), "m": clean(module, 24)}, separators=(",", ":"))
        with _audit_lock:
            fd = os.open(str(AUDIT_FILE), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
            try: os.write(fd, (rec + "\n").encode())
            finally: os.close(fd)
            _audit_lines[0] += 1
            if _audit_lines[0] % 200 == 1:                 # trim from time to time (and on the first write after a restart)
                lines = AUDIT_FILE.read_text().splitlines()
                if len(lines) > AUDIT_MAX + 200:
                    atomic_write(AUDIT_FILE, "\n".join(lines[-AUDIT_MAX:]) + "\n")
    except Exception as e:
        log.debug(f"audit: {e}")

@_local
def read_audit(limit=200, actor=None, action=None) -> list:
    """Newest first; optionally filtered by actor or action."""
    try: lines = AUDIT_FILE.read_text().splitlines()
    except OSError: return []
    out = []
    for ln in reversed(lines):
        try: e = json.loads(ln)
        except ValueError: continue
        if not isinstance(e, dict): continue
        if actor and e.get("a") != actor: continue
        if action and e.get("x") != action: continue
        out.append(e)
        if len(out) >= limit: break
    return out

# Detecta un CAMBIO de estado: la primera vez que ve una clave solo la memoriza (así reiniciar el servicio no
# genera eventos falsos); cuando el estado cambia devuelve (anterior, nuevo), si no devuelve None.
# EN: Detect a state CHANGE: the first time it sees a key it only remembers it (so restarting the service does not
#     create false events); when the state changes it returns (previous, new), otherwise None.
def state_changed(key, state):
    """Return (old, new) when `state` differs from the last one seen for `key` in this process, else None."""
    old = _state_seen.get(key)
    _state_seen[key] = state
    if old is None or old == state:
        return None
    return old, state

# Lee los eventos (más recientes primero), solo de los módulos pedidos.
# EN: Read the events (newest first), only for the requested modules.
def read_events(modules=None, limit=100):
    if REMOTE:
        try: return _rpc("events", retries=2, modules=list(modules) if modules is not None else None, limit=limit).get("events") or []
        except Exception as e:
            log.warning(f"events unavailable: {e}")
            return []
    ev = read_json(EVENTS_FILE, [], list)
    out = [e for e in ev if isinstance(e, dict) and (modules is None or e.get("m") in modules)]
    return list(reversed(out))[:limit]


# ─── Datos del equipo (widget «Pi» del Resumen) ────────────────────────────────────────────
# Temperatura, CPU, memoria, disco y tiempo encendido leídos de /proc y /sys; sin comandos externos salvo lo que ya usa check_power.
# EN: ─── Host data ("Pi" widget of the Overview) ──────────────────────────────────────────────
#     Temperature, CPU, memory, disk and uptime read from /proc and /sys; no external commands beyond what check_power already uses.
_cpu_prev: list = [None]

def _cpu_percent():
    """CPU usage since the previous call (first call: since boot)."""
    try:
        with open("/proc/stat") as f:
            parts = [int(x) for x in f.readline().split()[1:8]]
        idle = parts[3] + parts[4]; total = sum(parts)
        prev = _cpu_prev[0]; _cpu_prev[0] = (idle, total)
        if not prev or total == prev[1]:
            return None if not prev else 0.0
        return round(100.0 * (1 - (idle - prev[0]) / (total - prev[1])), 1)
    except Exception:
        return None

# Resultado de `labtower-sftp-backup verify` (comprobación en el storage); None si nunca corrió o el archivo no sirve.
# EN: Result of `labtower-sftp-backup verify` (check on the storage); None if it never ran or the file is unusable.
def _backup_verify():
    f = os.environ.get("LABTOWER_BACKUP_VERIFY", "/var/log/labtower/backup.verify")
    try:
        d = json.loads(Path(f).read_text())
        if not isinstance(d, dict): return None
        t = d.get("time")
        return {"state": "ok" if d.get("ok") is True else "fail", "time": t if isinstance(t, (int, float)) and not isinstance(t, bool) else None,
                "file": str(d.get("file") or "")[:120], "age_h": d.get("age_h") if isinstance(d.get("age_h"), (int, float)) else None,
                "count": d.get("count") if isinstance(d.get("count"), int) else None, "message": str(d.get("message") or "")[:220]}
    except Exception:
        return None

def backup_status():
    """State of the automatic SFTP backup for the Overview card: off (not configured), pending (configured, no run yet), ok, fail or unknown.
    ES: Estado del respaldo SFTP: lee el archivo que escribe labtower-sftp-backup (root, 644) y, si no existe, si hay SFTP_USER en la configuración."""
    f = os.environ.get("LABTOWER_BACKUP_STATUS", "/var/log/labtower/backup.status")
    conf = os.environ.get("LABTOWER_BACKUP_CONF", "/etc/labtower/backup.conf")
    try:
        d = json.loads(Path(f).read_text())
        if not isinstance(d, dict): raise ValueError("not an object")
        out = {"state": "ok" if d.get("ok") is True else "fail", "time": d.get("time"), "file": d.get("file") or "",
               "size": d.get("size"), "message": str(d.get("message") or "")[:220]}
        v = _backup_verify()
        if v: out["verify"] = v
        return out
    except FileNotFoundError:
        pass
    except Exception:
        return {"state": "unknown"}          # empty or corrupt file: shown as «sin datos», never an error
    try:
        user = ""
        for ln in Path(conf).read_text().splitlines():
            m = re.match(r"\s*SFTP_USER\s*=\s*(\S*)", ln)
            if m: user = m.group(1)
        return {"state": "pending" if user else "off"}
    except Exception:
        return {"state": "off"}

def system_stats():
    """Snapshot of the machine: temp (°C), cpu %, load, memory, disk, uptime, model, power flags."""
    out = {"model": None, "temp": None, "cpu": _cpu_percent(), "load": None, "cores": os.cpu_count() or 1,
           "mem": None, "disk": None, "uptime": None, "power": None}
    try: out["load"] = [round(x, 2) for x in os.getloadavg()]
    except OSError: pass
    for f in (os.environ.get("LABTOWER_PI_MODEL"), "/proc/device-tree/model", "/sys/firmware/devicetree/base/model"):
        if not f: continue
        try: out["model"] = Path(f).read_bytes().decode("utf-8", "ignore").strip("\x00 \n"); break
        except OSError: continue
    for f in ("/sys/class/thermal/thermal_zone0/temp",):
        try: out["temp"] = round(int(Path(f).read_text().strip()) / 1000.0, 1); break
        except Exception: continue
    try:
        m = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1); m[k] = int(v.split()[0]) * 1024
        total = m.get("MemTotal", 0); avail = m.get("MemAvailable", m.get("MemFree", 0))
        if total: out["mem"] = {"total": total, "used": total - avail, "pct": round(100.0 * (total - avail) / total, 1)}
    except Exception: pass
    try:
        st = os.statvfs("/")
        total = st.f_blocks * st.f_frsize; free = st.f_bavail * st.f_frsize
        if total: out["disk"] = {"total": total, "used": total - free, "pct": round(100.0 * (total - free) / total, 1)}
    except OSError: pass
    try: out["uptime"] = int(float(Path("/proc/uptime").read_text().split()[0]))
    except Exception: pass
    try:
        if _is_raspberry_pi():
            bits = _read_throttled()
            if bits is not None:
                out["power"] = {"under_voltage": bool(bits & 0x1), "throttled": bool(bits & 0x4),
                                "temp_limit": bool(bits & 0x8), "since_boot": bool(bits & 0xF0000)}
    except Exception: pass
    out["backup"] = backup_status()
    return out


# ─── Detalle completo del equipo (vista «Raspberry Pi» del Resumen) ─────────────────────────────────────────
# Todo sale de /proc, /sys y /run/utmp; solo «ip» y «systemctl --failed» son comandos externos (con tiempo máximo).
# CPU por núcleo y por proceso se calculan con dos lecturas separadas por ~0,4 s. Usuarios conectados, procesos y
# servicios solo se incluyen si `full` es True (administradores del panel).
# EN: ─── Full host detail ("Raspberry Pi" view of the Overview) ────────────────────────────────────────────
#     Everything comes from /proc, /sys and /run/utmp; only "ip" and "systemctl --failed" are external commands (with a timeout).
#     Per-core and per-process CPU use two reads ~0.4 s apart. Logged-in users, processes and services are included
#     only when `full` is True (panel administrators).
_SKIP_FS = {"proc", "sysfs", "devtmpfs", "devpts", "tmpfs", "cgroup", "cgroup2", "securityfs", "debugfs", "tracefs",
            "configfs", "fusectl", "mqueue", "hugetlbfs", "pstore", "bpf", "autofs", "binfmt_misc", "overlay", "squashfs",
            "nsfs", "ramfs", "rpc_pipefs", "efivarfs", "fuse.gvfsd-fuse"}

def _read(path, default=""):
    try: return Path(path).read_text().strip()
    except Exception: return default

def _cpu_times():
    """Per-core jiffies: [(idle, total), …] with the aggregate first."""
    out = []
    try:
        with open("/proc/stat") as f:
            for line in f:
                if not line.startswith("cpu"): break
                p = line.split(); v = [int(x) for x in p[1:8]]
                out.append((v[3] + v[4], sum(v)))
    except Exception: pass
    return out

def _proc_times():
    """pid → (name, jiffies, rss_bytes, user, state) for every process we can read."""
    page = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096
    res = {}
    for d in os.listdir("/proc"):
        if not d.isdigit(): continue
        try:
            raw = Path(f"/proc/{d}/stat").read_text()
            name = raw[raw.index("(") + 1:raw.rindex(")")]
            f = raw[raw.rindex(")") + 2:].split()
            res[int(d)] = (name, int(f[11]) + int(f[12]), int(f[21]) * page, f[0])
        except Exception: continue
    return res

def _uid_name(pid):
    try:
        import pwd
        uid = os.stat(f"/proc/{pid}").st_uid
        try: return pwd.getpwuid(uid).pw_name
        except KeyError: return str(uid)
    except Exception: return ""

def _utmp_users(path="/run/utmp"):
    """Sessions in /run/utmp (same data as the old «who»). struct utmp is 384 bytes on Linux."""
    import struct
    out = []
    try: data = Path(path).read_bytes()
    except Exception: return out
    for i in range(0, len(data) - 383, 384):
        r = data[i:i + 384]
        if struct.unpack_from("<h", r, 0)[0] != 7: continue          # USER_PROCESS
        user = r[44:76].split(b"\0")[0].decode("utf-8", "ignore")
        if user: out.append({"user": user, "tty": r[8:40].split(b"\0")[0].decode("utf-8", "ignore"),
                             "host": r[76:332].split(b"\0")[0].decode("utf-8", "ignore"), "since": struct.unpack_from("<i", r, 340)[0]})
    return out

def _logind_users(path="/run/systemd/sessions"):
    """Sessions known to systemd-logind (what «w» and «loginctl» show). Newer Raspberry Pi OS / Debian 13 no longer fill /run/utmp."""
    out = []
    try: names = os.listdir(path)
    except OSError: return out
    for n in names:
        if not n.isalnum(): continue                                  # skips «.ref» and other helper files
        kv = {}
        try:
            for line in Path(path, n).read_text().splitlines():
                if "=" in line: k, v = line.split("=", 1); kv[k] = v
        except Exception: continue
        if kv.get("CLASS", "user") != "user" or kv.get("STATE") == "closing" or not kv.get("USER"): continue
        try: since = int(kv.get("REALTIME", "0")) // 1000000
        except ValueError: since = 0
        out.append({"user": kv["USER"], "tty": kv.get("TTY") or kv.get("DISPLAY") or kv.get("TYPE", ""),
                    "host": kv.get("REMOTE_HOST", ""), "since": since})
    return out

def _proc_users(proc="/proc"):
    """Fallback when neither utmp nor logind know the sessions (minimal images such as DietPi, Debian 13 without utmp).
    Looks for the processes that exist only while someone is logged in: «sshd-session: user@pts/0» and login shells («-bash») with a terminal.
    ES: Respaldo cuando ni utmp ni logind conocen las sesiones: busca los procesos de una sesión abierta (sshd y shells de login con terminal)."""
    import pwd, re
    out = []
    try:
        btime = int(next(l.split()[1] for l in Path(proc, "stat").read_text().splitlines() if l.startswith("btime ")))
        hz = os.sysconf("SC_CLK_TCK")
    except Exception: btime, hz = 0, 100
    try: pids = [n for n in os.listdir(proc) if n.isdigit()]
    except OSError: return out
    ssh = re.compile(r"^sshd(?:-session)?: ([^@\s\[]+)@(\S+)$")
    for pid in pids:
        try:
            parts = Path(proc, pid, "cmdline").read_bytes().split(b"\0")
            cmd = parts[0].decode("utf-8", "ignore")
            st = Path(proc, pid, "stat").read_text()
            f = st[st.rindex(")") + 2:].split()
            tty_nr, since = int(f[4]), btime + int(f[19]) // hz if btime else 0
            user = tty = ""
            m = ssh.match(cmd.strip())
            if m: user, tty = m.group(1), m.group(2)
            elif cmd.startswith("-") and len(cmd) > 1 and tty_nr:           # login shell attached to a terminal
                major, minor = (tty_nr >> 8) & 0xfff, (tty_nr & 0xff) | ((tty_nr >> 12) & 0xfff00)
                tty = f"pts/{minor}" if major in range(136, 144) else f"tty{minor}" if major == 4 else ""
                try: user = pwd.getpwuid(os.stat(Path(proc, pid)).st_uid).pw_name
                except Exception: user = ""
            if user and tty: out.append({"user": user, "tty": tty, "host": "", "since": since})
        except Exception: continue
    return out

def _logged_users():
    """Logged-in sessions from utmp, logind and (as a last resort) the process list, without duplicates (same user and terminal)."""
    seen, out = set(), []
    for u in _utmp_users() + _logind_users() + _proc_users():
        k = (u["user"], u["tty"])
        if k in seen: continue
        seen.add(k); out.append(u)
    return sorted(out, key=lambda u: u["since"])

def _net_info(full=False):
    ifs = []
    addrs = {}
    try:
        o = subprocess.run(["ip", "-j", "addr"], capture_output=True, text=True, timeout=3).stdout
        for it in json.loads(o or "[]"):
            addrs[it.get("ifname")] = [f'{a.get("local")}/{a.get("prefixlen")}' for a in it.get("addr_info", []) if a.get("family") in ("inet", "inet6") and a.get("scope") != "host"]
    except Exception: pass
    base = Path("/sys/class/net")
    try: names = sorted(os.listdir(base))
    except OSError: names = []
    for n in names:
        if n == "lo" or n.startswith(("veth", "docker", "br-")): continue
        d = base / n
        try: rx = int(_read(d / "statistics/rx_bytes", "0")); tx = int(_read(d / "statistics/tx_bytes", "0"))
        except ValueError: rx = tx = 0
        sp = _read(d / "speed", "")
        ifs.append({"name": n, "state": _read(d / "operstate", "?"), "mac": _read(d / "address") if full else None,
                    "speed": int(sp) if sp.lstrip("-").isdigit() and int(sp) > 0 else None,
                    "rx": rx, "tx": tx, "addrs": addrs.get(n, [])})
    return ifs

def _disk_info():
    out, seen = [], set()
    try:
        with open("/proc/mounts") as f:
            for line in f:
                dev, mp, fs = line.split()[:3]
                if fs in _SKIP_FS or not dev.startswith("/") or dev in seen: continue
                if mp.startswith(("/proc", "/sys", "/dev", "/run", "/snap")): continue
                seen.add(dev)
                try: st = os.statvfs(mp)
                except OSError: continue
                total = st.f_blocks * st.f_frsize; free = st.f_bavail * st.f_frsize
                if total: out.append({"dev": dev, "mount": mp.replace("\\040", " "), "fs": fs, "total": total, "used": total - free,
                                      "pct": round(100.0 * (total - free) / total, 1)})
    except Exception: pass
    return out

_THROTTLE_BITS = [(0, "under_voltage", True), (1, "freq_capped", True), (2, "throttled", True), (3, "soft_temp_limit", True),
                  (16, "under_voltage", False), (17, "freq_capped", False), (18, "throttled", False), (19, "soft_temp_limit", False)]

def system_detail(full=False):
    """Everything the Overview's Raspberry Pi view shows. Never raises: a missing piece is just None / empty."""
    out = system_stats()
    t0 = _cpu_times(); p0 = _proc_times() if full else {}
    time.sleep(0.4)
    t1 = _cpu_times(); p1 = _proc_times() if full else {}
    cores = []
    for a, b in zip(t0, t1):
        dt = b[1] - a[1]
        cores.append(round(100.0 * (1 - (b[0] - a[0]) / dt), 1) if dt > 0 else 0.0)
    out["cpu_total"] = cores[0] if cores else out.get("cpu")
    out["cpu_cores"] = cores[1:]
    try:
        u = os.uname()
        out["host"] = {"hostname": u.nodename, "kernel": u.release, "arch": u.machine}
    except Exception: out["host"] = {}
    osr = {}
    for line in _read("/etc/os-release").splitlines():
        if "=" in line: k, v = line.split("=", 1); osr[k] = v.strip('"')
    out["host"]["os"] = osr.get("PRETTY_NAME")
    try:
        import platform
        out["host"]["python"] = platform.python_version()
    except Exception: pass
    out["boot"] = int(time.time() - out["uptime"]) if out.get("uptime") is not None else None
    out["time"] = int(time.time())
    out["tz"] = time.strftime("%Z")
    fq = {}
    for k, n in (("cur", "scaling_cur_freq"), ("max", "scaling_max_freq"), ("min", "scaling_min_freq")):
        v = _read(f"/sys/devices/system/cpu/cpu0/cpufreq/{n}")
        if v.isdigit(): fq[k] = int(v) // 1000
    out["freq_mhz"] = fq or None
    out["governor"] = _read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor") or None
    try:
        m = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1); m[k] = int(v.split()[0]) * 1024
        out["mem_detail"] = {"total": m.get("MemTotal"), "available": m.get("MemAvailable"), "free": m.get("MemFree"),
                             "buffers": m.get("Buffers"), "cached": m.get("Cached"),
                             "swap_total": m.get("SwapTotal"), "swap_used": (m.get("SwapTotal", 0) - m.get("SwapFree", 0))}
    except Exception: out["mem_detail"] = None
    out["disks"] = _disk_info()
    out["net"] = _net_info(full)
    out["procs_total"] = len(p1) if full else None
    try:
        bits = _read_throttled() if _is_raspberry_pi() else None
        if bits is not None:
            out["throttle"] = {"raw": f"0x{bits:X}", "now": [n for b, n, now in _THROTTLE_BITS if now and bits & (1 << b)],
                               "since_boot": [n for b, n, now in _THROTTLE_BITS if not now and bits & (1 << b)]}
        else: out["throttle"] = None
    except Exception: out["throttle"] = None
    # Más sensores térmicos / other thermal zones
    zones = []
    try:
        for z in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
            v = _read(z / "temp")
            if v.lstrip("-").isdigit(): zones.append({"name": _read(z / "type") or z.name, "temp": round(int(v) / 1000.0, 1)})
    except Exception: pass
    out["thermal"] = zones
    out["full"] = bool(full)
    if full:
        out["users"] = _logged_users()
        dt = (t1[0][1] - t0[0][1]) if t0 and t1 else 0
        ncpu = max(1, len(t1) - 1)
        procs = []
        for pid, (name, j, rss, st) in p1.items():
            cpu = 0.0
            if pid in p0 and dt > 0: cpu = round(100.0 * ncpu * (j - p0[pid][1]) / dt, 1)
            procs.append({"pid": pid, "name": name, "cpu": max(0.0, cpu), "rss": rss, "state": st})
        top_cpu = sorted(procs, key=lambda p: (-p["cpu"], -p["rss"]))[:8]
        top_mem = sorted(procs, key=lambda p: -p["rss"])[:8]
        for p in {p["pid"]: p for p in top_cpu + top_mem}.values(): p["user"] = _uid_name(p["pid"])
        out["top_cpu"], out["top_mem"] = top_cpu, top_mem
        failed = []
        try:
            o = subprocess.run(["systemctl", "--failed", "--no-legend", "--plain", "--no-pager"], capture_output=True, text=True, timeout=4).stdout
            failed = [ln.split()[0] for ln in o.splitlines() if ln.strip()]
        except Exception: failed = None
        out["failed_units"] = failed
    return out


# ─── Métricas: historiales de los gráficos del Resumen ──────────────────────────────────────────
# Una base SQLite compartida (metrics.db, junto a users.json) con el historial de temperatura y subtensión de la Pi
# (lo escribe el servicio Resumen) y el de CPU y memoria de los nodos Proxmox (lo escribe Proxmox Monitor). Cada
# muestra se confirma al instante (WAL), así que un corte de luz no pierde datos; Teleporter la incluye en el respaldo.
# EN: ─── Metrics: histories behind the Overview charts ─────────────────────────────────────────
#     One shared SQLite database (metrics.db, next to users.json) holding the Pi temperature and under-voltage
#     history (written by the Overview service) and the CPU and memory history of the Proxmox nodes (written by
#     Proxmox Monitor). Each sample is committed at once (WAL), so a power cut loses nothing; Teleporter backs it up.
# ES: Cada módulo guarda su historial en SU carpeta (metrics.db dentro de /var/lib/labtower/<módulo>; el servicio fija LABTOWER_MODULE): un módulo
#     no puede leer ni borrar el historial de otro. Sin LABTOWER_MODULE (pruebas, desarrollo) hay una sola base junto a users.json.
# EN: Each module keeps its history in ITS folder (metrics.db inside /var/lib/labtower/<module>; the service sets LABTOWER_MODULE): a module
#     can neither read nor delete another one's history. Without LABTOWER_MODULE (tests, development) there is one database next to users.json.
MODULE = os.environ.get("LABTOWER_MODULE", "").strip()
METRICS_DB = Path(os.environ.get("LABTOWER_METRICS") or (str(module_dir(MODULE) / "metrics.db") if MODULE else str(USERS_FILE.with_name("metrics.db"))))
_METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS pi_samples  (ts INTEGER PRIMARY KEY, temp REAL, flags INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS pve_samples (cid TEXT NOT NULL, node TEXT NOT NULL, ts INTEGER NOT NULL, cpu REAL, mem REAL,
                                        PRIMARY KEY (cid, node, ts)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS nas_samples (nid TEXT NOT NULL, ts INTEGER NOT NULL, cpu REAL, mem REAL, temp REAL, rx REAL, tx REAL,
                                        PRIMARY KEY (nid, ts)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS dns_samples (sid TEXT NOT NULL, ts INTEGER NOT NULL, total INTEGER, blocked INTEGER, pct REAL, ms REAL,
                                        PRIMARY KEY (sid, ts)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS wan_samples (ts INTEGER PRIMARY KEY, up INTEGER NOT NULL, rtt REAL, loss REAL, jitter REAL, gw REAL, dns REAL);
CREATE TABLE IF NOT EXISTS wan_speed   (ts INTEGER PRIMARY KEY, down REAL, up REAL, ping REAL, server TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS wan_outages (start INTEGER PRIMARY KEY, end INTEGER, scope TEXT);
"""

def metrics_conn():
    """Open metrics.db (created on first use, mode 600). Callers close it; open per operation, they are rare."""
    new = not METRICS_DB.exists()
    c = sqlite3.connect(str(METRICS_DB), timeout=10)
    try:
        c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA synchronous=NORMAL")
        c.executescript(_METRICS_SCHEMA)
        if new:
            try: os.chmod(METRICS_DB, 0o600)
            except OSError: pass
    except Exception:
        c.close(); raise
    return c

def keep_days(env, default):
    """Retention in days from an environment variable (1–365)."""
    try: return max(1, min(365, int(os.environ.get(env, default))))
    except ValueError: return default


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
    """Checks every module shares: users file, sessions file, disk space. A module asks the authentication service for the first two."""
    if not REMOTE: return check_common_local()
    out = {}
    try:
        r = _rpc("health", retries=2).get("checks")
        for k in ("users", "sessions"):
            v = r.get(k) if isinstance(r, dict) else None
            out[k] = v if isinstance(v, dict) and v.get("level") in (OK, WARN, FAIL) else chk(FAIL, "no answer from the authentication service")
    except Exception as e:
        out["users"] = chk(FAIL, f"authentication service unavailable: {str(e)[:80]}")
        out["sessions"] = chk(FAIL, "authentication service unavailable")
    out["disk"] = _check_disk(DATA_ROOT)
    return out

def _check_disk(where):
    try:
        st = os.statvfs(str(where if Path(where).exists() else "/"))
        mb = st.f_bavail * st.f_frsize // (1024 * 1024)
        return chk(FAIL if mb < 5 else WARN if mb < 100 else OK, f"{mb} MB free")
    except OSError as e:
        return chk(WARN, str(e))

# Chequeo del archivo de eventos (lo guarda el servicio de autenticación; un módulo se lo pregunta).
# EN: Check of the events file (kept by the authentication service; a module asks it).
def events_check():
    if not REMOTE: return check_file(EVENTS_FILE)
    try:
        v = _rpc("health", retries=2).get("checks", {}).get("events")
        if isinstance(v, dict) and v.get("level") in (OK, WARN, FAIL): return v
    except Exception as e:
        return chk(FAIL, f"authentication service unavailable: {str(e)[:80]}")
    return chk(FAIL, "no answer from the authentication service")

def check_common_local():
    """The checks run by the authentication service itself."""
    out = {}
    users = _users_cached()
    out["users"] = chk(OK) if users else chk(FAIL, "no usable users.json")
    out["sessions"] = check_file(SESSIONS_FILE)
    out["disk"] = _check_disk(SESSIONS_FILE.parent)
    return out

# Detecta si el equipo es una Raspberry Pi leyendo el modelo del device-tree (no existe en VM ni en otros PC).
# EN: Detect whether the machine is a Raspberry Pi by reading the device-tree model (it does not exist on VMs or other PCs).
def _is_raspberry_pi() -> bool:
    for f in (os.environ.get("LABTOWER_PI_MODEL"), "/proc/device-tree/model", "/sys/firmware/devicetree/base/model"):
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
    cmd = os.environ.get("LABTOWER_VCGENCMD") or shutil.which("vcgencmd") or "/usr/bin/vcgencmd"
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
    for d in glob.glob(os.environ.get("LABTOWER_HWMON", "/sys/class/hwmon") + "/hwmon*"):
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
# Quién consulta /api/health: True = con sesión (detalle completo), False = desde esta máquina sin sesión (solo niveles: lo usa labtower-health),
# None = anónimo por la red (solo el estado global, sin versión ni nombres de chequeos).
# EN: Who is querying /api/health: True = with a session (full detail), False = from this machine without a session (levels only: used by
#     labtower-health), None = anonymous over the network (only the overall status, no version and no check names).
def health_mode(handler, tok):
    if get_session(tok) is not None: return True
    return False if is_local_request(handler) else None

def health_reply(module, checks, detailed=False, extra=None):
    """Build (http_code, body). detailed: True = everything, False = levels only, None = overall status only."""
    levels = [c["level"] for c in checks.values()]
    status = FAIL if FAIL in levels else "degraded" if WARN in levels else OK
    code = 503 if status == FAIL else 200
    if detailed is None:
        return code, {"status": status}
    body = {"module": module, "version": version(), "status": status, "uptime": int(time.time() - STARTED),
            "checks": {k: ({**v} if detailed else {"level": v["level"]}) for k, v in checks.items()}}
    if extra and detailed: body.update(extra)
    return code, body
