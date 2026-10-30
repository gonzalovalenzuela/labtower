#!/usr/bin/env python3
"""
LabTower — servicio de autenticación por socket Unix / authentication service over a Unix socket.

ES: Solo el Panel de administración (usuario «labtower-auth») toca users.json, sessions.json y los contadores de intentos. Los demás módulos
corren con su propio usuario del sistema, no pueden leer esos archivos y le piden al panel, por un socket Unix, lo que necesitan:
    session   ¿es válido este token? → usuario y permisos actuales
    login     usuario + contraseña → sesión nueva (la contraseña se verifica SOLO aquí; el módulo nunca ve un hash)
    logout    cierra la sesión de ese token
    event     anota un evento en la línea de tiempo (el módulo lo fija el sistema operativo, no el que llama)
    events    lee la línea de tiempo (solo el Resumen)
    health    estado de los archivos de usuarios y sesiones
No existe ninguna operación para crear una sesión sin contraseña ni para leer usuarios: un módulo comprometido no puede falsificar sesiones ni
llevarse hashes. Quién llama se sabe por SO_PEERCRED (lo rellena el kernel, no el cliente).

EN: Only the Admin Panel (user "labtower-auth") touches users.json, sessions.json and the attempt counters. Every other module runs under
its own system user, cannot read those files and asks the panel, through a Unix socket, for what it needs (operations above). There is no
operation to create a session without a password or to read users: a compromised module can neither forge sessions nor take hashes away.
The caller is identified with SO_PEERCRED (filled in by the kernel, not by the client).

Protocolo / Protocol: una petición JSON y una respuesta JSON, cada una en una línea (UTF-8, terminada en «\\n»); una conexión por petición.
"""
import json, logging, os, pwd, re, socket, struct, threading, time

log = logging.getLogger("auth.rpc")

MAX_REQUEST = 65536          # bytes of one request line
MAX_REPLY   = 1 << 20        # bytes of one reply line (the event list is the biggest)
TIMEOUT     = 5.0            # TOTAL seconds per connection, both sides (a slow client cannot keep a thread for longer)
MAX_CONNS   = 64             # concurrent connections served; the rest are closed at once (bounded threads and memory)
RESERVED    = frozenset({"module", "level", "text", "k", "self"})   # names a caller must not pass as event parameters
USER_PREFIX = "labtower-"
# Identidades que pueden hablar con el servicio: usuario del sistema «labtower-<id>». / Identities allowed to talk to the service.
CALLERS = ("wol", "nut", "net", "pve", "nas", "dns", "wan", "overview")


class AuthUnavailable(Exception):
    """The authentication service cannot be reached (it is restarting, or not running)."""


# ─── Servidor / Server ───────────────────────────────────────────────────────────────────────────
class _Peer:
    """Stand-in for an HTTP handler: auth.login() / auth.create_session() only need the client address and the User-Agent."""
    def __init__(self, ip, ua):
        self.client_address = (ip, 0)
        self.headers = {"User-Agent": ua}


def identify_by_uid(uid):
    """Caller identity from the kernel-provided uid: 'wol', 'net'… for the users labtower-<id>, 'root' for uid 0, otherwise None."""
    if uid == 0: return "root"
    try: name = pwd.getpwuid(uid).pw_name
    except KeyError: return None
    if name.startswith(USER_PREFIX) and name[len(USER_PREFIX):] in CALLERS: return name[len(USER_PREFIX):]
    return None


def _clean_ip(v):
    v = v if isinstance(v, str) else ""
    return v if re.fullmatch(r"[0-9A-Fa-f:.%a-zA-Z]{1,45}", v) else "unknown"


class Service:
    """The operations, bound to the local `auth` module. `identify(uid)` is replaceable (tests run everything under one uid)."""
    def __init__(self, auth, identify=identify_by_uid):
        self.auth, self.identify = auth, identify
        self.slots = threading.BoundedSemaphore(MAX_CONNS)

    # Each handler gets (caller, request dict) and returns a JSON-able dict. Errors are {"error": "..."}.
    def op_session(self, caller, r):
        tok = r.get("token")
        if not isinstance(tok, str) or not 1 <= len(tok) <= 128: return {"session": None}
        s = self.auth.get_session(tok, allow_pending=bool(r.get("allow_pending")))
        return {"session": s}

    def op_login(self, caller, r):
        a = self.auth
        user, pw = r.get("username"), r.get("password")
        if not isinstance(user, str) or not isinstance(pw, str) or len(user) > 256 or len(pw) > 1024:
            return {"status": 400, "error": "Invalid request body"}
        peer = _Peer(_clean_ip(r.get("ip")), (r.get("ua") if isinstance(r.get("ua"), str) else "")[:200])
        code = r.get("code") if isinstance(r.get("code"), str) and len(r["code"]) <= 32 else None
        res, err = a.login_session(peer, user, pw, r.get("remember"), code)
        if err: return {"status": err[0], "error": err[1]}
        return {"login": res}

    def op_logout(self, caller, r):
        tok = r.get("token")
        if isinstance(tok, str) and 1 <= len(tok) <= 128: self.auth.delete_session(tok)
        return {"ok": True}

    def op_event(self, caller, r):
        # The module name of the event is the caller's own: a compromised module cannot write events as another one.
        if caller not in CALLERS: return {"error": "forbidden"}
        text, level = r.get("text"), r.get("level")
        if not isinstance(text, str) or level not in ("info", "warn", "crit"): return {"error": "bad event"}
        k = r.get("k") if isinstance(r.get("k"), str) and len(r["k"]) <= 64 else None
        params = r.get("params") if isinstance(r.get("params"), dict) else {}
        self.auth.record_event(caller, level, text, k, **{str(a)[:32]: b for a, b in list(params.items())[:16]
                                                          if isinstance(b, (int, float, str)) and str(a) not in RESERVED})
        return {"ok": True}

    def op_audit(self, caller, r):
        # The module recorded is the caller's own (taken from the operating-system user), like events.
        if caller not in CALLERS: return {"error": "forbidden"}
        f = lambda k, n: r.get(k)[:n] if isinstance(r.get(k), str) else ""
        self.auth.audit(f("actor", 64), f("action", 48), f("target", 128), f("detail", 200), f("ip", 64), module=caller)
        return {"ok": True}

    def op_events(self, caller, r):
        if caller not in ("overview", "root"): return {"error": "forbidden"}
        mods = r.get("modules")
        mods = [m for m in mods if isinstance(m, str)][:32] if isinstance(mods, list) else None
        try: limit = max(1, min(300, int(r.get("limit", 100))))
        except (TypeError, ValueError): limit = 100
        return {"events": self.auth.read_events(mods, limit)}

    def op_health(self, caller, r):
        checks = self.auth.check_common_local()
        checks["events"] = self.auth.check_file(self.auth.EVENTS_FILE)
        return {"checks": checks}

    def handle(self, caller, r):
        op = r.get("op") if isinstance(r, dict) else None
        fn = getattr(self, "op_" + op, None) if isinstance(op, str) and re.fullmatch(r"[a-z_]{1,20}", op) else None
        if fn is None: return {"error": "unknown operation"}
        try: return fn(caller, r)
        except Exception as e:                        # never take the service down because of one request
            log.warning(f"{op}: {type(e).__name__}: {e}")
            return {"error": "internal error"}


def _read_line(conn, limit, deadline):
    buf = b""
    while b"\n" not in buf:
        left = deadline - time.monotonic()
        if left <= 0: raise socket.timeout("deadline")
        conn.settimeout(left)
        chunk = conn.recv(min(4096, limit + 1 - len(buf)))
        if not chunk: break
        buf += chunk
        if len(buf) > limit: raise ValueError("too large")
    return buf.split(b"\n", 1)[0]


def _serve_conn(svc, conn):
    try:
        deadline = time.monotonic() + TIMEOUT
        conn.settimeout(TIMEOUT)
        pid, uid, gid = struct.unpack("3i", conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")))
        caller = svc.identify(uid)
        if caller is None:
            reply = {"error": "forbidden"}
        else:
            try: req = json.loads(_read_line(conn, MAX_REQUEST, deadline))
            except (ValueError, UnicodeDecodeError): reply = {"error": "bad request"}
            else: reply = svc.handle(caller, req)
        conn.sendall(json.dumps(reply, separators=(",", ":")).encode() + b"\n")
    except (OSError, ValueError, struct.error):
        pass
    finally:
        try: conn.close()
        except OSError: pass
        svc.slots.release()


def serve(path, auth, identify=identify_by_uid, mode=0o660):
    """Listen on the Unix socket `path` (a thread per connection). Returns the listening socket; the accept loop runs in a daemon thread."""
    svc = Service(auth, identify)
    try: os.unlink(path)
    except FileNotFoundError: pass
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    old = os.umask(0o117)                              # the socket is created 0660
    try: srv.bind(path)
    finally: os.umask(old)
    os.chmod(path, mode)
    srv.listen(64)

    def loop():
        while True:
            try: conn, _ = srv.accept()
            except OSError: return
            if not svc.slots.acquire(blocking=False):          # too many at once: refuse instead of piling up threads
                try: conn.close()
                except OSError: pass
                continue
            threading.Thread(target=_serve_conn, args=(svc, conn), daemon=True).start()
    threading.Thread(target=loop, daemon=True, name="auth-rpc").start()
    log.info(f"authentication service listening on {path}")
    return srv


# ─── Cliente / Client ────────────────────────────────────────────────────────────────────────────
def call(path, op, retries=6, **fields):
    """One request to the service. Retries briefly while it is (re)starting. Raises AuthUnavailable if it cannot be reached."""
    data = json.dumps({"op": op, **fields}, separators=(",", ":")).encode() + b"\n"
    last = None
    for i in range(retries):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                s.settimeout(TIMEOUT)
                s.connect(path)
                s.sendall(data)
                line = _read_line(s, MAX_REPLY, time.monotonic() + TIMEOUT)
            finally:
                s.close()
            r = json.loads(line)
            if not isinstance(r, dict): raise ValueError("bad reply")
            return r
        except (FileNotFoundError, ConnectionRefusedError) as e:      # not up yet / restarting
            last = e; time.sleep(0.5)
        except (OSError, ValueError) as e:
            last = e
            break
    raise AuthUnavailable(str(last))
