#!/usr/bin/env python3
"""NUT Monitor — Backend con auth, multi-servidor, historial SQLite."""
import json, os, re, socket, time, logging, threading, sys, sqlite3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from collections import deque
from contextlib import contextmanager

# Auth compartido
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

HOST        = "127.0.0.1"
PORT        = 8081
POLL_SEC    = int(os.environ.get("NUT_POLL", 10))
STATIC_DIR  = Path(__file__).parent / "static"
DATA_FILE   = Path(__file__).parent / "servers.json"
DB_FILE     = Path(__file__).parent / "history.db"

# Cuántos puntos devolver en la API según rango
RANGE_LIMIT = {
    "1h":  720,    # 1h a 10s = 360 pts (margen x2 para no truncar los puntos recientes)
    "1d":  2880,   # 1d a 30s = 2880 pts
    "1w":  2016,   # 1w a 5min = 2016 pts
    "1mo": 2880,   # 1mes a 15min = 2880 pts
    "all": 4320,   # máx a mostrar en gráfico
}

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("nut")

# ─── SQLite ───────────────────────────────────────────────────────────────────
_db_lock = threading.Lock()

def db_connect():
    # timeout: wait for a competing writer instead of failing at once with "database is locked"
    conn = sqlite3.connect(str(DB_FILE), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def db_init():
    with _db_lock:
        conn = db_connect()
        conn.execute("PRAGMA journal_mode=WAL")      # persistent; set once, not on every connection
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                srv_id  TEXT NOT NULL,
                ups     TEXT NOT NULL,
                ts      INTEGER NOT NULL,
                charge  REAL DEFAULT 0,
                runtime INTEGER DEFAULT 0,
                load    REAL DEFAULT 0,
                vin     REAL DEFAULT 0,
                vout    REAL DEFAULT 0,
                watts   REAL DEFAULT 0,
                temp    REAL DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hist_srv_ups_ts ON history(srv_id, ups, ts)")
        conn.commit(); conn.close()
    log.info(f"DB: {DB_FILE}")

# Las filas se acumulan en memoria y se escriben juntas cada DB_FLUSH_SEC segundos
# (un commit por lote en vez de uno cada POLL_SEC por UPS: menos desgaste de la SD).
# Si el UPS no está en línea (ups.status distinto de OL: batería, carga baja, etc.)
# se escribe de inmediato, porque ahí es cuando más importa no perder datos.
DB_FLUSH_SEC = int(os.environ.get("NUT_DB_FLUSH", 60))
_INSERT_SQL = """
    INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp)
    VALUES (?,?,?,?,?,?,?,?,?,?)
"""
_ins_buf = []
_ins_last = time.time()
_flush_err = None            # last history-write error (None once a write succeeds), for /api/health

def _flush_locked():
    global _ins_last, _flush_err
    if not _ins_buf: return
    conn = db_connect()
    try:
        conn.executemany(_INSERT_SQL, _ins_buf)
        conn.commit()
        _ins_buf.clear()
        _ins_last = time.time()
        _flush_err = None
    except Exception as e:
        _flush_err = str(e)
        raise
    finally:
        conn.close()

def db_flush(timeout=3):
    # timeout: desde el handler de SIGTERM (hilo principal) el lock podría estar tomado
    if not _db_lock.acquire(timeout=timeout): return
    try: _flush_locked()
    except Exception as e: log.error(f"db_flush: {e}")
    finally: _db_lock.release()

def db_insert(srv_id, ups, entry, urgent=False):
    with _db_lock:
        _ins_buf.append((srv_id, ups,
                         entry["ts"], entry["charge"], entry["runtime"], entry["load"],
                         entry["vin"], entry["vout"], entry["watts"], entry["temp"]))
        if len(_ins_buf) > 5000:          # si el disco falla, no crecer sin límite
            del _ins_buf[:len(_ins_buf)-5000]
        if urgent or time.time() - _ins_last >= DB_FLUSH_SEC:
            try: _flush_locked()
            except Exception as e: log.error(f"db flush: {e}")

def db_query(srv_id, ups, since_ts=0, limit=4320):
    """Historial de un UPS reducido a como máximo ~`limit` puntos.

    Agrupa por intervalos de tiempo iguales y promedia cada uno (el último punto
    conserva su timestamp real). Así la muestra es pareja, llega hasta el dato más
    reciente y no depende de los ids de fila, que se comparten entre todos los UPS.
    (Elegir filas con `id % paso` dejaba sin ningún punto a un UPS cuando había
    dos o más y el paso era par.)
    """
    with _db_lock:
        conn = db_connect()
        try:
            lo, hi = conn.execute(
                "SELECT MIN(ts), MAX(ts) FROM history WHERE srv_id=? AND ups=? AND ts>=?",
                (srv_id, ups, since_ts)).fetchone()
            if lo is None:
                return []
            bucket = max(1, -(-(hi - lo) // max(1, limit - 1)))   # techo de span/(limit-1)
            rows = conn.execute("""
                SELECT MAX(ts) AS ts, AVG(charge) AS charge, AVG(runtime) AS runtime,
                       AVG(load) AS load, AVG(vin) AS vin, AVG(vout) AS vout,
                       AVG(watts) AS watts, AVG(temp) AS temp
                FROM history
                WHERE srv_id=? AND ups=? AND ts>=?
                GROUP BY (ts - ?) / ?
                ORDER BY ts ASC
            """, (srv_id, ups, since_ts, lo, bucket)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

def db_prune():
    """Elimina registros de más de 1 año. Llamar periódicamente."""
    cutoff = int(time.time()) - 365 * 86400
    with _db_lock:
        conn = db_connect()
        try:
            deleted = conn.execute("DELETE FROM history WHERE ts < ?", (cutoff,)).rowcount
            conn.commit()    # close the DELETE transaction first: a checkpoint inside it fails
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            conn.close()     # always release the connection (an open one keeps the DB locked)
    if deleted: log.info(f"DB pruned: {deleted} registros >1 año eliminados")

def _db_prune_safe():
    try: db_prune()
    except Exception as e: log.error(f"db_prune: {e}")

# ─── Servidores ───────────────────────────────────────────────────────────────
_srv_lock = threading.RLock()     # hold around load_servers() → modify → save_servers()

def load_servers():
    # A missing file means a fresh install (default local server); an existing but empty
    # list is valid (the user deleted every server). Damaged file → last good copy.
    if not DATA_FILE.exists() and not DATA_FILE.with_name(DATA_FILE.name + ".bak").exists():
        return [{"id": "local", "name": "Local", "host": "127.0.0.1", "port": 3493}]
    return auth.read_json(DATA_FILE, [], list)

def save_servers(s):
    with _srv_lock:
        auth.write_json(DATA_FILE, s, mode=0o644)

# ─── Watts ────────────────────────────────────────────────────────────────────
def _calc_watts(vars_):
    try:
        rp = float(vars_.get("ups.realpower") or 0)
        if rp > 0: return rp
    except: pass
    try:
        pva = float(vars_.get("ups.power") or 0)
        pf  = float(vars_.get("ups.powerfactor") or 0)
        if pva > 0 and pf > 0: return round(pva * pf, 1)
    except: pass
    try:
        vout = float(vars_.get("output.voltage") or 0)
        iout = float(vars_.get("output.current") or 0)
        if vout > 0 and iout > 0: return round(vout * iout, 1)
    except: pass
    try:
        pva  = float(vars_.get("ups.power") or 0)
        load = float(vars_.get("ups.load") or 0)
        if pva > 0 and load > 0: return round(pva * (load / 100) * 0.8, 1)
    except: pass
    try:
        nom  = float(vars_.get("ups.realpower.nominal") or
                     vars_.get("ups.power.nominal") or 0)
        load = float(vars_.get("ups.load") or 0)
        if nom > 0 and load > 0: return round(nom * (load / 100), 1)
    except: pass
    return 0.0

# ─── NUT Client ───────────────────────────────────────────────────────────────
class NUTClient:
    def __init__(self, host, port, timeout=5.0):
        self.host = host; self.port = int(port); self.timeout = timeout

    def _conn(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout); s.connect((self.host, self.port)); return s

    def _readline(self, sock):
        buf = b""
        while True:
            ch = sock.recv(1)
            if not ch or ch == b"\n": break
            buf += ch
        return buf.decode(errors="replace").strip()

    def _cmd(self, sock, cmd):
        sock.sendall((cmd + "\n").encode())
        lines = []; is_list = cmd.strip().upper().startswith("LIST")
        while True:
            line = self._readline(sock)
            if not line: break
            lines.append(line)
            if is_list:
                if line.startswith("END LIST") or line.startswith("ERR"): break
            else:
                if line.startswith("VAR ") or line.startswith("VER ") or \
                   line.startswith("ERR") or line.startswith("OK"): break
        return lines

    @staticmethod
    def _check(lines):
        """upsd answers errors as `ERR <CODE>` (e.g. DATA-STALE): raise instead of treating it as empty data."""
        for l in lines:
            if l.startswith("ERR"):
                raise RuntimeError(f"upsd: {l[3:].strip() or 'error'}")
        return lines

    def list_ups(self):
        with self._conn() as s: lines = self._check(self._cmd(s, "LIST UPS"))
        return [{"name": m.group(1), "desc": m.group(2)}
                for line in lines for m in [re.match(r'^UPS (\S+) "(.*)"$', line)] if m]

    def get_vars(self, ups):
        with self._conn() as s: lines = self._check(self._cmd(s, f"LIST VAR {ups}"))
        return {m.group(1): m.group(2)
                for line in lines for m in [re.match(r'^VAR \S+ (\S+) "(.*)"$', line)] if m}

    def list_clients(self, ups):
        try:
            with self._conn() as s: lines = self._cmd(s, f"LIST CLIENT {ups}")
            return [m.group(1) for line in lines
                    for m in [re.match(r'^CLIENT \S+ (\S+)$', line)] if m]
        except Exception as e:
            log.debug(f"list_clients: {e}"); return []

    def get_version(self):
        try:
            with self._conn() as s: lines = self._cmd(s, "VER")
            return next((l.strip() for l in lines if l.strip()), "")
        except: return ""

# ─── Cache en memoria (solo estado actual) ────────────────────────────────────
class SCache:
    def __init__(self, sid):
        self.id = sid; self._lock = threading.RLock()
        self._ups = {}; self._clients = {}
        self._error = None; self._last_ok = None; self._ver = ""

    def reset(self):
        with self._lock:
            self._ups = {}; self._clients = {}
            self._error = None; self._last_ok = None; self._ver = ""

    def update(self, name, vars_, clients=None, ver=""):
        with self._lock:
            self._ups[name]     = {**vars_, "_ts": time.time()}
            self._clients[name] = clients or []
            self._error = None; self._last_ok = time.time()
            if ver: self._ver = ver
        # Insertar en DB fuera del lock
        try:
            watts = _calc_watts(vars_)
            entry = {
                "ts":      int(time.time()),
                "charge":  float(vars_.get("battery.charge") or 0),
                "runtime": int(float(vars_.get("battery.runtime") or 0)),
                "load":    float(vars_.get("ups.load") or 0),
                "vin":     float(vars_.get("input.voltage") or 0),
                "vout":    float(vars_.get("output.voltage") or 0),
                "watts":   watts,
                "temp":    float(vars_.get("ups.temperature") or
                                 vars_.get("battery.temperature") or 0),
            }
            status = (vars_.get("ups.status") or "OL").strip()
            db_insert(self.id, name, entry, urgent=not status.startswith("OL"))
        except Exception as e:
            log.debug(f"db_insert error: {e}")

    def set_error(self, msg):
        with self._lock: self._error = msg

    def snap(self, range_="all"):
        """Devuelve estado actual + historial según rango."""
        with self._lock:
            ups_snap  = dict(self._ups)
            cli_snap  = dict(self._clients)
            error     = self._error
            last_ok   = self._last_ok
            ver       = self._ver

        # range=none: solo estado actual, sin tocar la base (refresco automático de la página)
        if range_ == "none":
            return {"id": self.id, "ups": ups_snap, "clients": cli_snap,
                    "history": {}, "error": error, "last_ok": last_ok,
                    "version": ver, "ts": time.time()}

        # Cargar historial de DB según rango
        since = 0
        now   = int(time.time())
        range_secs = {"1h":3600,"1d":86400,"1w":604800,"1mo":2592000}
        if range_ in range_secs: since = now - range_secs[range_]
        limit = RANGE_LIMIT.get(range_, 4320)

        history = {}
        for ups_name in ups_snap:
            history[ups_name] = db_query(self.id, ups_name, since_ts=since, limit=limit)

        return {"id": self.id, "ups": ups_snap, "clients": cli_snap,
                "history": history, "error": error, "last_ok": last_ok,
                "version": ver, "ts": time.time()}

_caches: dict = {}; _pollers: dict = {}; _wake: dict = {}; _gl = threading.Lock()

def ensure_poller(server):
    sid = server["id"]
    with _gl:
        if sid not in _caches: _caches[sid] = SCache(sid)
        ev = _wake.setdefault(sid, threading.Event())
        if sid in _pollers: ev.set()   # edited server: poll again right away
        if sid not in _pollers or not _pollers[sid].is_alive():
            t = threading.Thread(target=_poll, args=(server,), daemon=True)
            _pollers[sid] = t; t.start()
            log.info(f"Poller → {server['name']} ({server['host']}:{server['port']})")

def remove_poller(sid):
    with _gl: _caches.pop(sid, None); _pollers.pop(sid, None); _wake.pop(sid, None)

def _poll(server):
    sid = server["id"]; nut = NUTClient(server["host"], server["port"])
    cache = _caches.get(sid)
    if not cache: return
    poll_n = 0
    target = (server["host"], int(server["port"]))
    while True:
        try:
            cur = next((s for s in load_servers() if s["id"] == sid), None)
            if cur is None: return
            if (cur["host"], int(cur["port"])) != target:
                # host/port edited: reconnect and drop data from the old address
                target = (cur["host"], int(cur["port"]))
                nut = NUTClient(*target); cache.reset()
                log.info(f"Poller → {cur['name']} ({target[0]}:{target[1]}) (edited)")
        except Exception as e:                # never let the poller thread die
            log.error(f"poll config: {e}"); cur = None
        if cur is None and not any(s["id"] == sid for s in _safe_servers()):
            return
        try:
            ver   = nut.get_version()
            ups_l = nut.list_ups()
            if not ups_l: cache.set_error("No UPS found in upsd")
            for u in ups_l:
                vars_   = nut.get_vars(u["name"])
                clients = nut.list_clients(u["name"])
                vars_["_desc"]   = u["desc"]
                vars_["_serial"] = vars_.get("ups.serial") or vars_.get("device.serial") or ""
                cache.update(u["name"], vars_, clients, ver)
        except ConnectionRefusedError:
            cache.set_error(f"upsd no disponible en {server['host']}:{server['port']}")
        except socket.timeout:
            cache.set_error("Timeout connecting to upsd")
        except Exception as e:
            cache.set_error(str(e)); log.error(f"poll error: {e}")
        poll_n += 1
        # Limpiar DB cada 1440 polls (~4h con poll=10s)
        if poll_n % 1440 == 0:
            threading.Thread(target=_db_prune_safe, daemon=True).start()
        ev = _wake.get(sid)
        if ev: ev.wait(POLL_SEC); ev.clear()
        else: time.sleep(POLL_SEC)

def _safe_servers():
    try: return load_servers()
    except Exception: return []

def start_all():
    db_init()
    for s in load_servers(): ensure_poller(s)

# ─── Health ───────────────────────────────────────────────────────────────────
def health_report(detailed=False):
    c = auth.check_common()
    c["servers_file"] = auth.check_file(DATA_FILE)
    now = time.time()
    # History database: reachable, and rows are really being written
    if not _db_lock.acquire(timeout=2):
        c["database"] = auth.chk(auth.FAIL, "database lock held for more than 2 s")
        last_by = {}
    else:
        last_by = {}
        try:
            conn = db_connect()
            try:
                conn.execute("SELECT 1").fetchone()
                for r in conn.execute("SELECT srv_id, ups, MAX(ts) AS t FROM history GROUP BY srv_id, ups"):
                    last_by[(r["srv_id"], r["ups"])] = r["t"]
            finally:
                conn.close()
            c["database"] = auth.chk(auth.OK)
        except Exception as e:
            c["database"] = auth.chk(auth.FAIL, f"database error: {e}")
        finally:
            _db_lock.release()
    if _flush_err:
        c["history_write"] = auth.chk(auth.FAIL, f"last write failed: {_flush_err}")
    elif _ins_buf and now - _ins_last > max(3 * DB_FLUSH_SEC, 180):
        c["history_write"] = auth.chk(auth.FAIL, f"{len(_ins_buf)} rows unsaved for {int(now - _ins_last)} s")
    else:
        c["history_write"] = auth.chk(auth.OK, f"{len(_ins_buf)} rows buffered")
    # Pollers and data freshness, per server
    srvs = _safe_servers(); dead = []; stale = []; stuck = []
    stale_after = max(6 * POLL_SEC, 60)
    for s in srvs:
        sid = s["id"]; t = _pollers.get(sid)
        if t is None or not t.is_alive(): dead.append(s["name"]); continue
        cache = _caches.get(sid)
        if cache is None: continue
        sn = cache.snap("none")
        if sn["error"] or not sn["last_ok"] or now - sn["last_ok"] > stale_after:
            stale.append(f'{s["name"]}: {sn["error"] or "no data yet"}')
        else:
            for ups in sn["ups"]:                      # fresh data in memory but nothing in the DB?
                lt = last_by.get((sid, ups))
                if lt is None or now - lt > max(5 * DB_FLUSH_SEC, 600):
                    stuck.append(f"{s['name']}/{ups}: last saved {'never' if lt is None else str(int(now - lt)) + ' s ago'}")
    if not srvs:
        c["pollers"] = auth.chk(auth.OK, "no servers configured")
    elif dead:
        c["pollers"] = auth.chk(auth.FAIL, "poller stopped: " + ", ".join(dead))
    else:
        c["pollers"] = auth.chk(auth.OK, f"{len(srvs)} running")
    c["upsd"] = auth.chk(auth.WARN, "; ".join(stale)) if stale else auth.chk(auth.OK, "all servers answering")
    if stuck: c["history_fresh"] = auth.chk(auth.FAIL, "history not being saved — " + "; ".join(stuck))
    else:     c["history_fresh"] = auth.chk(auth.OK)
    return auth.health_reply("nut", c, detailed)

# ─── HTTP Handler ─────────────────────────────────────────────────────────────
class H(BaseHTTPRequestHandler):
    timeout = 30      # a stalled client must not hold a thread forever
    def log_message(self, fmt, *a):
        if int(a[1]) >= 400: log.warning(f"{self.client_address[0]} {a[1]}")

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

    def _token(self):
        return auth.token_from_request(dict(self.headers),
                                       self.headers.get("Cookie", ""))

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

    def _range_param(self):
        qs = parse_qs(urlparse(self.path).query)
        return qs.get("range", ["all"])[0]

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        tok  = self._token()

        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if path == "/api/version":     # public: shown in the page footer
            return self._json(200, {"version": auth.version()})
        if path == "/api/health":      # public: levels only; details need a valid session
            code, body = health_report(auth.get_session(tok) is not None)
            return self._json(code, body)
        if path == "/api/login":
            return self._json(200, {"ok": True})

        if not auth.check_permission(tok, "nut", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        if path == "/api/config":
            self._json(200, {"poll_sec": POLL_SEC})
        elif path == "/api/servers":
            range_ = self._range_param()
            srvs   = load_servers()
            for s_ in srvs:                      # revive a poller thread that died unexpectedly
                t_ = _pollers.get(s_["id"])
                if t_ is None or not t_.is_alive():
                    ensure_poller(s_)
            out    = [{**s, "status": _caches.get(s["id"], SCache(s["id"])).snap(range_)} for s in srvs]
            self._json(200, {"servers": out})
        elif path == "/api/ups":
            range_ = self._range_param()
            self._json(200, {sid: c.snap(range_) for sid, c in _caches.items()})
        elif path == "/api/history":
            # Historial de un UPS concreto para un rango (resolucion propia del rango)
            qs     = parse_qs(urlparse(self.path).query)
            sid    = qs.get("srv", ["local"])[0]
            ups    = qs.get("ups", ["ups"])[0]
            range_ = qs.get("range", ["all"])[0]
            range_secs = {"1h":3600,"1d":86400,"1w":604800,"1mo":2592000}
            since = int(time.time()) - range_secs[range_] if range_ in range_secs else 0
            rows  = db_query(sid, ups, since_ts=since, limit=RANGE_LIMIT.get(range_, 4320))
            self._json(200, {"history": rows})
        elif path == "/api/export/csv":
            # Export CSV del historial de un UPS específico
            qs    = parse_qs(urlparse(self.path).query)
            sid   = qs.get("srv", ["local"])[0]
            ups   = qs.get("ups", ["ups"])[0]
            range_ = qs.get("range", ["all"])[0]
            since = 0
            now   = int(time.time())
            range_secs = {"1h":3600,"1d":86400,"1w":604800,"1mo":2592000}
            if range_ in range_secs: since = now - range_secs[range_]
            rows = db_query(sid, ups, since_ts=since, limit=8640)
            import csv, io
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["timestamp","datetime","charge_pct","runtime_s","load_pct","vin_v","vout_v","watts","temp_c"])
            for r in rows:
                writer.writerow([
                    r["ts"],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r["ts"])),
                    r["charge"], r["runtime"], r["load"],
                    r["vin"], r["vout"], r["watts"], r["temp"]
                ])
            body = buf.getvalue().encode()
            fname = f"ups-history-{sid}-{ups}-{time.strftime('%Y%m%d')}.csv"
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers(); self.wfile.write(body)

        elif path == "/api/me":
            sess = auth.get_session(tok)
            self._json(200, {"username": sess["username"],
                              "permissions": sess["permissions"]} if sess else {})
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._token()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})

        if path == "/api/login":
            u = auth.authenticate(body.get("username",""), body.get("password",""))
            if not u: return self._json(401, {"error": "Invalid credentials"})
            token = auth.create_session(body["username"], u["permissions"])
            users = auth.load_users()
            must  = users.get(body["username"], {}).get("must_change_password", False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie",
                f"session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400")
            body_resp = json.dumps({"ok": True, "token": token, "username": body["username"],
                                    "permissions": u["permissions"],
                                    "must_change_password": must}).encode()
            self.send_header("Content-Length", str(len(body_resp)))
            self.end_headers(); self.wfile.write(body_resp); return

        if path == "/api/logout":
            auth.delete_session(tok)
            return self._json(200, {"ok": True})

        if not auth.check_permission(tok, "nut", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        if path == "/api/servers":
            if not auth.check_permission(tok, "nut", "admin"):
                return self._json(403, {"error": "Requiere permiso admin"})
            host = (body.get("host") or "").strip()
            name = (body.get("name") or "").strip()
            try: port = int(body.get("port") or 3493)
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
            if not host or not name: return self._json(400, {"error": "host y name requeridos"})
            if not 1 <= port <= 65535: return self._json(400, {"error": "Invalid port"})
            import uuid
            with _srv_lock:
                srvs = load_servers()
                if any(s["host"]==host and s["port"]==port for s in srvs):
                    return self._json(409, {"error": "Ya existe ese host:puerto"})
                server = {"id": str(uuid.uuid4()), "name": name, "host": host, "port": port}
                srvs.append(server); save_servers(srvs)
            ensure_poller(server)
            self._json(201, {"server": server})
        elif path == "/api/test":
            if not auth.check_permission(tok, "nut", "admin"):
                return self._json(403, {"error": "Requiere permiso admin"})
            host = (body.get("host") or "").strip()
            try: port = int(body.get("port") or 3493)
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
            if not host or not 1 <= port <= 65535: return self._json(400, {"error": "Invalid host or port"})
            try:
                nut  = NUTClient(host, port, timeout=4)
                ups  = nut.list_ups(); ver = nut.get_version()
                self._json(200, {"ok": True, "ups_count": len(ups), "ups": ups, "version": ver})
            except Exception as e:
                self._json(200, {"ok": False, "error": str(e)})
        else:
            self._json(404, {"error": "Not found"})

    def do_PUT(self):
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._token()
        if not auth.check_permission(tok, "nut", "admin"):
            return self._json(403, {"error": "Requiere permiso admin"})
        m = re.match(r'^/api/servers/([a-zA-Z0-9\-]+)$', path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})
        sid  = m.group(1)
        host = (body.get("host") or "").strip()
        name = (body.get("name") or "").strip()
        try: port = int(body.get("port") or 3493)
        except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
        if not host or not name: return self._json(400, {"error": "host y name requeridos"})
        if not 1 <= port <= 65535: return self._json(400, {"error": "Invalid port"})
        with _srv_lock:
            srvs = load_servers()
            srv  = next((x for x in srvs if x["id"] == sid), None)
            if srv is None: return self._json(404, {"error": "No encontrado"})
            if any(x["id"] != sid and x["host"] == host and x["port"] == port for x in srvs):
                return self._json(409, {"error": "Ya existe ese host:puerto"})
            srv.update({"name": name, "host": host, "port": port})
            save_servers(srvs)
        ensure_poller(srv)
        self._json(200, {"server": srv})

    def do_DELETE(self):
        path = urlparse(self.path).path
        tok  = self._token()
        if not auth.check_permission(tok, "nut", "admin"):
            return self._json(403, {"error": "Requiere permiso admin"})
        m = re.match(r'^/api/servers/([a-zA-Z0-9\-]+)$', path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        sid = m.group(1)
        with _srv_lock:
            srvs = load_servers()
            new  = [s for s in srvs if s["id"] != sid]
            if len(new) == len(srvs): return self._json(404, {"error": "No encontrado"})
            save_servers(new)
        remove_poller(sid); self._json(200, {"ok": True})

if __name__ == "__main__":
    import signal, atexit
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    start_all()
    atexit.register(db_flush)
    # systemd detiene el servicio con SIGTERM: vaciar el buffer antes de salir
    signal.signal(signal.SIGTERM, lambda *_: (db_flush(), sys.exit(0)))
    log.info(f"NUT Monitor en http://{HOST}:{PORT} — poll cada {POLL_SEC}s")
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
