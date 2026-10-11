#!/usr/bin/env python3
"""
Pi Console — Auth Module
Gestión de usuarios, sesiones y permisos compartido por todos los módulos.

Los módulos son procesos distintos que comparten users.json y sessions.json, así que
toda lectura-modificación-escritura se hace bajo un bloqueo de archivo (flock) además
del bloqueo entre hilos, y todo se escribe de forma atómica (archivo temporal propio,
fsync y rename) para no perder ni corromper datos ante cortes de energía.
"""
import copy, json, os, hashlib, hmac, secrets, time, logging, threading
from pathlib import Path

try:
    import fcntl
except ImportError:          # pragma: no cover - solo Linux/macOS
    fcntl = None

log = logging.getLogger("auth")

USERS_FILE    = Path(os.environ.get("PICONSOLE_USERS",    "/var/lib/pi-console/users.json"))
SESSION_TTL = 24 * 3600   # 24 horas
# La ventana deslizante se renueva como máximo cada RENEW_EVERY segundos: renovar en
# cada request reescribiría sessions.json (y la SD) varias veces por segundo.
RENEW_EVERY = 600
SESSIONS_FILE = Path(os.environ.get("PICONSOLE_SESSIONS", "/var/lib/pi-console/sessions.json"))


# ─── Escritura atómica y bloqueo entre procesos ───────────────────────────────
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
                except OSError as e:       # read-only dir etc.: keep going with the thread lock only
                    log.warning(f"file lock unavailable ({self.path}): {e}")
                    self._fd = None
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


_users_lock    = FileLock(USERS_FILE.with_name(USERS_FILE.name + ".lock"))
_sessions_lock = FileLock(SESSIONS_FILE.with_name(SESSIONS_FILE.name + ".lock"))

def users_lock():
    """Hold this around any load_users() → modify → save_users() sequence."""
    return _users_lock


def _salt() -> str:
    return os.environ.get("PICONSOLE_SALT", "pi-console-salt-change-me")

def _hash(password: str) -> str:
    return hashlib.sha256(f"{_salt()}:{password}".encode()).hexdigest()


# ─── Usuarios ─────────────────────────────────────────────────────────────────
def _default_users() -> dict:
    return {
        "admin": {
            "password_hash": _hash("admin"),
            "permissions": {"wol": "admin", "nut": "admin", "net": "admin", "pve": "admin"},
            "created": int(time.time()),
            "must_change_password": True,
        }
    }

_ucache = {"sig": None, "data": None}

def _file_sig(p: Path):
    try:
        st = p.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None

def _users_cached() -> dict:
    """Parsed users.json (shared object: do not mutate). Re-read only when the file changes.

    * Missing file (fresh install)  → the initial admin account.
    * Unreadable/corrupt file       → the last good copy (users.json.bak) or, failing that,
      NO users. It must never fall back to the default admin/admin account, which would
      silently reopen the panel with well-known credentials after a bad write.
    """
    sig = _file_sig(USERS_FILE)
    if sig is None:
        return _default_users()
    if sig == _ucache["sig"] and _ucache["data"] is not None:
        return _ucache["data"]
    for p in (USERS_FILE, USERS_FILE.with_name(USERS_FILE.name + ".bak")):
        try:
            data = json.loads(p.read_text())
            if isinstance(data, dict):
                if p is not USERS_FILE:
                    log.error(f"{USERS_FILE} is unreadable; using {p.name}")
                _ucache["sig"], _ucache["data"] = sig, data
                return data
        except Exception as e:
            log.error(f"{p}: {e}")
    log.error(f"{USERS_FILE} is corrupt and there is no usable backup: no user can log in "
              f"until it is fixed or deleted (deleting it recreates the default admin account)")
    return {}

def load_users() -> dict:
    """A private copy of the users table, safe to modify and pass to save_users()."""
    return copy.deepcopy(_users_cached())

def save_users(users: dict):
    with _users_lock:
        if USERS_FILE.exists():                      # keep the previous good version
            try:
                json.loads(USERS_FILE.read_text())
                atomic_write(USERS_FILE.with_name(USERS_FILE.name + ".bak"), USERS_FILE.read_bytes())
            except Exception:
                pass
        atomic_write(USERS_FILE, json.dumps(users, indent=2))
        _ucache["sig"], _ucache["data"] = _file_sig(USERS_FILE), copy.deepcopy(users)


# ─── Sesiones compartidas (persistidas a disco) ────────────────────────────────
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

def _save_sessions(sessions: dict):
    atomic_write(SESSIONS_FILE, json.dumps(sessions))
    _scache["sig"], _scache["data"] = _file_sig(SESSIONS_FILE), sessions

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

def get_session(token: str) -> dict | None:
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
        return {**s, "permissions": dict(user.get("permissions", {}))}

def delete_session(token: str):
    with _sessions_lock:
        sessions = _load_sessions()
        if sessions.pop(token, None) is not None:
            _save_sessions(sessions)

def delete_user_sessions(username: str, keep: str | None = None):
    """Log a user out everywhere (password change, account removal), optionally keeping one session."""
    with _sessions_lock:
        sessions = _load_sessions()
        gone = [t for t, s in sessions.items() if s.get("username") == username and t != keep]
        for t in gone: del sessions[t]
        if gone: _save_sessions(sessions)

def _purge(sessions: dict):
    now = time.time()
    for t in [k for k, v in sessions.items() if now > v.get("expires", 0)]:
        del sessions[t]


# ─── Helpers ──────────────────────────────────────────────────────────────────
LEVELS = {"readonly": 1, "execute": 2, "admin": 3}

def authenticate(username: str, password: str) -> dict | None:
    user = _users_cached().get(username)
    if not user: return None
    if not hmac.compare_digest(user["password_hash"], _hash(password)): return None
    return copy.deepcopy(user)

def check_permission(token: str, resource: str, required: str) -> bool:
    s = get_session(token)
    if not s: return False
    return LEVELS.get(s["permissions"].get(resource, ""), 0) >= LEVELS.get(required, 999)

def token_from_request(headers, cookie_str="") -> str | None:
    auth = headers.get("Authorization", "")
    if auth.startswith("Bearer "): return auth[7:].strip()
    for part in cookie_str.split(";"):
        part = part.strip()
        if part.startswith("session="): return part[8:].strip()
    return None


# ─── Health ───────────────────────────────────────────────────────────────────
STARTED = time.time()
OK, WARN, FAIL = "ok", "warn", "fail"

def chk(level, detail=""):
    """One health check result: level is OK, WARN (degraded) or FAIL."""
    return {"level": level, "detail": detail}

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

def health_reply(module, checks, detailed=False, extra=None):
    """Build (http_code, body). Unauthenticated callers get levels only, no detail text."""
    levels = [c["level"] for c in checks.values()]
    status = FAIL if FAIL in levels else "degraded" if WARN in levels else OK
    body = {"module": module, "status": status, "uptime": int(time.time() - STARTED),
            "checks": {k: ({**v} if detailed else {"level": v["level"]}) for k, v in checks.items()}}
    if extra and detailed: body.update(extra)
    return (503 if status == FAIL else 200), body

