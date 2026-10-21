#!/usr/bin/env python3
"""NUT Monitor — Backend con auth, multi-servidor, historial SQLite."""
# UPS Monitor (puerto 8081): consulta uno o varios servidores NUT (upsd), muestra el estado de los UPS y
# guarda un historial de 1 año en SQLite.
#
# Cómo se conecta con el UPS: NUT tiene un driver que habla con el UPS (en esta instalación por
# puerto serie) y un servidor, upsd, que expone los datos por TCP (puerto 3493) con un protocolo de
# texto sencillo: «LIST UPS», «LIST VAR <ups>», etc. Este módulo es un cliente de upsd.
#
# Flujo de datos:
#   hilo «poller» por servidor → NUTClient pregunta a upsd cada POLL_SEC segundos
#   → SCache guarda el estado actual en memoria → la API lo entrega a la página
#   → cada lectura también se acumula en un búfer y se escribe a SQLite por lotes (history.db)
#
# Estructura del archivo: SQLite · servidores · cálculo de watts · cliente NUT · caché ·
# pollers · salud · manejador HTTP.
# EN: UPS Monitor (port 8081): queries one or more NUT servers (upsd), shows the status of the UPS units and
#     keeps a 1-year history in SQLite.
#
#     How it talks to the UPS: NUT has a driver that talks to the UPS (over a serial port in this install)
#     and a server, upsd, that exposes the data over TCP (port 3493) with a simple text protocol:
#     "LIST UPS", "LIST VAR <ups>", etc. This module is a client of upsd.
#
#     Data flow:
#       one "poller" thread per server → NUTClient asks upsd every POLL_SEC seconds
#       → SCache keeps the current state in memory → the API hands it to the page
#       → every reading is also accumulated in a buffer and written to SQLite in batches (history.db)
#
#     File structure: SQLite · servers · watts calculation · NUT client · cache ·
#     pollers · health · HTTP handler.
import json, os, re, socket, time, logging, threading, sys, sqlite3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128      # default is 5: a burst of simultaneous connections got reset
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from collections import deque
from contextlib import contextmanager

# Auth compartido
# Módulo compartido de autenticación (carpeta hermana /auth).
# EN: Shared authentication module (sibling folder /auth).
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

# Solo loopback; el acceso desde la red pasa por nginx.
# EN: Loopback only; network access goes through nginx.
HOST        = "127.0.0.1"
PORT        = 8081
# Cada cuántos segundos se consulta a upsd (variable NUT_POLL, 10 por defecto).
# EN: How often upsd is queried, in seconds (NUT_POLL variable, 10 by default).
POLL_SEC    = int(os.environ.get("NUT_POLL", 10))
STATIC_DIR  = Path(__file__).parent / "static"
# servers.json: lista de servidores NUT configurados. history.db: historial en SQLite.
# EN: servers.json: list of configured NUT servers. history.db: history in SQLite.
# Los datos viven en /var/lib/pi-console/nut-monitor (el código de /opt es de solo lectura para el servicio).
# EN: The data lives in /var/lib/pi-console/nut-monitor (the code in /opt is read-only for the service).
DATA_DIR    = auth.module_data("nut-monitor")
auth.adopt_legacy(Path(__file__).parent, DATA_DIR, ("servers.json", "history.db"))
DATA_FILE   = DATA_DIR / "servers.json"
DB_FILE     = DATA_DIR / "history.db"

# Cuántos puntos devolver en la API según rango
# Máximo de puntos que se devuelven por rango del gráfico. Se reducen promediando intervalos
# (ver db_query), así la gráfica es liviana aunque el historial sea de un año.
# EN: Maximum number of points returned per chart range. They are reduced by averaging intervals
#     (see db_query), so the chart stays light even with a one-year history.
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
# Un solo hilo a la vez usa la base: SQLite tolera varios lectores pero un único escritor.
# EN: Only one thread at a time uses the database: SQLite tolerates many readers but a single writer.
_db_lock = threading.Lock()

# Abre una conexión a history.db. El timeout hace que un escritor concurrente espere en vez de fallar con «database is locked».
# EN: Open a connection to history.db. The timeout makes a concurrent writer wait instead of failing with "database is locked".
def db_connect():
    # timeout: wait for a competing writer instead of failing at once with "database is locked"
    conn = sqlite3.connect(str(DB_FILE), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

# Crea la tabla de historial y su índice si no existen. Usa modo WAL (el diario de escritura queda aparte), que
# permite leer mientras se escribe y es más amable con la tarjeta SD.
# EN: Create the history table and its index if they do not exist. Uses WAL mode (the write journal is kept apart), which
#     allows reading while writing and is gentler on the SD card.
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
        # Cortes de energía (UPS en batería): inicio, fin (NULL = sigue en curso) y carga mínima. src: 'live' o 'hist' (deducido del historial).
        # EN: Power outages (UPS on battery): start, end (NULL = still going) and minimum charge. src: 'live' or 'hist' (inferred from history).
        conn.execute("""
            CREATE TABLE IF NOT EXISTS outages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                srv_id     TEXT NOT NULL,
                ups        TEXT NOT NULL,
                t_start    INTEGER NOT NULL,
                t_end      INTEGER,
                min_charge REAL,
                src        TEXT DEFAULT 'live'
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_out_srv_ups ON outages(srv_id, ups, t_start)")
        conn.commit()
        _outages_backfill(conn)
        conn.close()
    log.info(f"DB: {DB_FILE}")

# ─── Cortes de energía y disponibilidad ───────────────────────────────────────
# Se deducen del estado del UPS: «OB» o «LB» abre un corte y «OL» lo cierra. Al crear la tabla por primera vez se
# reconstruyen los cortes pasados desde el historial: tramos con voltaje de entrada bajo 20 V, solo en UPS que alguna
# vez informaron más de 100 V (los que no miden voltaje de entrada no se deducen).
# EN: ─── Power outages and availability ──────────────────────────────────────
#     Derived from the UPS status: "OB" or "LB" opens an outage and "OL" closes it. When the table is first created,
#     past outages are rebuilt from the history: runs with input voltage under 20 V, only for UPSs that ever reported
#     more than 100 V (those that do not measure input voltage are not inferred).
_open_out = {}               # (srv, ups) → id of the open outage row, or None; filled on first use
_out_min  = {}               # (srv, ups) → minimum charge seen in the open outage
_stats_cache = {}            # (srv, ups) → (time, stats)
OUT_GAP = 600                # s: a hole longer than this in the history ends a run (service was off)

def _outages_backfill(conn):
    if conn.execute("SELECT 1 FROM outages LIMIT 1").fetchone(): return
    if not conn.execute("SELECT 1 FROM history LIMIT 1").fetchone(): return
    n = 0
    for r in conn.execute("SELECT srv_id, ups FROM history GROUP BY srv_id, ups HAVING MAX(vin) > 100").fetchall():
        sid, ups = r[0], r[1]
        start = last = None; low = None
        def close():
            nonlocal n, start, last, low
            if start is not None:
                conn.execute("INSERT INTO outages (srv_id,ups,t_start,t_end,min_charge,src) VALUES (?,?,?,?,?, 'hist')",
                             (sid, ups, start, max(last, start + 1), low)); n += 1
            start = last = low = None
        for ts, vin, ch in conn.execute("SELECT ts, vin, charge FROM history WHERE srv_id=? AND ups=? ORDER BY ts", (sid, ups)):
            if vin < 20:
                if start is not None and ts - last > OUT_GAP: close()
                if start is None: start = ts; low = ch
                last = ts; low = ch if low is None else min(low, ch)
            else:
                if start is not None: last = max(last, ts); close()
        close()
    conn.commit()
    if n: log.info(f"outages: {n} rebuilt from history")

# Registra el estado actual de un UPS: abre, actualiza o cierra el corte. Solo escribe al cambiar de estado o al bajar la carga mínima.
# EN: Record a UPS current state: opens, updates or closes the outage. Writes only on a state change or a new minimum charge.
def outage_track(sid, ups, status, charge, now=None):
    now = int(now or time.time()); k = (sid, ups)
    words = status.split(); out = "OB" in words or "LB" in words
    with _db_lock:
        conn = db_connect()
        try:
            if k not in _open_out:
                r = conn.execute("SELECT id, min_charge FROM outages WHERE srv_id=? AND ups=? AND t_end IS NULL ORDER BY id DESC LIMIT 1", k).fetchone()
                _open_out[k] = r[0] if r else None; _out_min[k] = r[1] if r else None
            oid = _open_out[k]
            if out and oid is None:
                cur = conn.execute("INSERT INTO outages (srv_id,ups,t_start,min_charge) VALUES (?,?,?,?)", (sid, ups, now, charge))
                _open_out[k] = cur.lastrowid; _out_min[k] = charge; conn.commit(); _stats_cache.pop(k, None)
            elif out and (_out_min.get(k) is None or charge < _out_min[k]):
                conn.execute("UPDATE outages SET min_charge=? WHERE id=?", (charge, oid)); _out_min[k] = charge; conn.commit()
            elif not out and oid is not None:
                conn.execute("UPDATE outages SET t_end=? WHERE id=?", (now, oid)); conn.commit()
                _open_out[k] = None; _out_min[k] = None; _stats_cache.pop(k, None)
        finally: conn.close()

# Estadísticas de un UPS: racha en línea, disponibilidad en 24 h / 7 d / 30 d y último corte (se recalculan cada 30 s como mucho).
# La disponibilidad se mide sobre el tiempo con datos: si hay menos historial que el período, se usa solo ese tiempo.
# EN: Stats of one UPS: online streak, availability over 24 h / 7 d / 30 d and last outage (recomputed at most every 30 s).
#     Availability is measured over the time with data: if there is less history than the period, only that time is used.
def ups_stats(sid, ups):
    k = (sid, ups); now = int(time.time())
    c = _stats_cache.get(k)
    if c and now - c[0] < 30: return c[1]
    conn = db_connect()
    try:
        first = conn.execute("SELECT MIN(ts) FROM history WHERE srv_id=? AND ups=?", k).fetchone()[0]
        rows = conn.execute("SELECT t_start, t_end, min_charge FROM outages WHERE srv_id=? AND ups=? ORDER BY t_start", k).fetchall()
    finally: conn.close()
    if first is None: first = now
    first = min([first] + [r[0] for r in rows])
    st = {"since": first, "tracked": now - first, "on_battery": False, "streak": None, "last": None, "count30": 0, "avail": {}}
    for label, w in (("24h", 86400), ("7d", 604800), ("30d", 2592000)):
        lo = max(now - w, first); cover = now - lo
        down = sum(max(0, min(r[1] or now, now) - max(r[0], lo)) for r in rows)
        st["avail"][label] = round(100.0 * (1 - down / cover), 3) if cover >= 3600 else None
    st["count30"] = sum(1 for r in rows if (r[1] or now) >= now - 2592000)
    if rows:
        t0, t1, mc = rows[-1]
        st["last"] = {"start": t0, "end": t1, "dur": (t1 or now) - t0, "min_charge": mc}
        st["on_battery"] = t1 is None
        st["streak"] = 0 if t1 is None else now - t1
    else:
        st["streak"] = now - first
    _stats_cache[k] = (now, st)
    return st

# Las filas se acumulan en memoria y se escriben juntas cada DB_FLUSH_SEC segundos
# (un commit por lote en vez de uno cada POLL_SEC por UPS: menos desgaste de la SD).
# Si el UPS no está en línea (ups.status distinto de OL: batería, carga baja, etc.)
# se escribe de inmediato, porque ahí es cuando más importa no perder datos.
# Reduce el desgaste de la SD: se acumulan las filas y se escriben juntas cada DB_FLUSH_SEC segundos.
# EN: Reduces SD wear: rows are accumulated and written together every DB_FLUSH_SEC seconds.
DB_FLUSH_SEC = int(os.environ.get("NUT_DB_FLUSH", 60))
# Sentencia de inserción de una fila de historial.
# EN: Insert statement for one history row.
_INSERT_SQL = """
    INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp)
    VALUES (?,?,?,?,?,?,?,?,?,?)
"""
# Búfer de filas pendientes de escribir, instante de la última escritura y último error (lo usa /api/health).
# EN: Buffer of rows waiting to be written, time of the last write and last error (used by /api/health).
_ins_buf = []
_ins_last = time.time()
_first_rows = {}             # readings seen per (server, UPS) since startup; the first ones are written at once
_flush_err = None            # last history-write error (None once a write succeeds), for /api/health

# Escribe el búfer completo en una sola transacción. Debe llamarse con el candado de la base tomado.
# EN: Write the whole buffer in a single transaction. Must be called with the database lock held.
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

# Vacía el búfer a disco. Se usa al apagar el servicio; el timeout evita bloquearse si otro hilo tiene el candado.
# EN: Empty the buffer to disk. Used when the service shuts down; the timeout avoids blocking if another thread holds the lock.
def db_flush(timeout=3):
    # timeout: desde el handler de SIGTERM (hilo principal) el lock podría estar tomado
    if not _db_lock.acquire(timeout=timeout): return
    try: _flush_locked()
    except Exception as e: log.error(f"db_flush: {e}")
    finally: _db_lock.release()

# Agrega una lectura al búfer. Escribe de inmediato si el UPS NO está en línea (batería, carga baja…), porque
# en ese momento es cuando más importa no perder datos. Si el disco falla, el búfer se limita a 5000 filas.
# EN: Add a reading to the buffer. It writes immediately if the UPS is NOT online (battery, low charge…), because
#     that is when losing data matters most. If the disk fails, the buffer is capped at 5000 rows.
def db_insert(srv_id, ups, entry, urgent=False):
    with _db_lock:
        # Las dos primeras lecturas de cada UPS desde el arranque (o desde que se agrega el servidor) se escriben de inmediato: así el gráfico ya tiene dos puntos a los pocos segundos en vez de esperar un lote completo (DB_FLUSH_SEC).
        # EN: The first two readings of each UPS since startup (or since the server is added) are written immediately: so the chart already has two points after a few seconds instead of waiting for a whole batch (DB_FLUSH_SEC).
        k = (srv_id, ups)
        _first_rows[k] = _first_rows.get(k, 0) + 1
        if _first_rows[k] <= 2: urgent = True
        _ins_buf.append((srv_id, ups,
                         entry["ts"], entry["charge"], entry["runtime"], entry["load"],
                         entry["vin"], entry["vout"], entry["watts"], entry["temp"]))
        if len(_ins_buf) > 5000:          # si el disco falla, no crecer sin límite
            del _ins_buf[:len(_ins_buf)-5000]
        if urgent or time.time() - _ins_last >= DB_FLUSH_SEC:
            try: _flush_locked()
            except Exception as e: log.error(f"db flush: {e}")

# Historial de un UPS reducido a unos `limit` puntos: agrupa por intervalos iguales de tiempo y promedia
# cada uno. Es el único acceso de lectura al historial.
# EN: History of one UPS reduced to about `limit` points: groups by equal time intervals and averages
#     each one. It is the only read access to the history.
def db_query(srv_id, ups, since_ts=0, limit=4320):
    """Historial de un UPS reducido a como máximo ~`limit` puntos.

    Agrupa por intervalos de tiempo iguales y promedia cada uno (el último punto
    conserva su timestamp real). Así la muestra es pareja, llega hasta el dato más
    reciente y no depende de los ids de fila, que se comparten entre todos los UPS.
    (Elegir filas con `id % paso` dejaba sin ningún punto a un UPS cuando había
    dos o más y el paso era par.)

    EN: History of one UPS reduced to at most ~`limit` points. Groups by equal time intervals and
    averages each one (the last point keeps its real timestamp). This makes the sample even, reaches
    the most recent data and does not depend on row ids, which are shared by all the UPS units.
    (Picking rows with `id % step` left a UPS with no points at all when there were two or more
    and the step was even.)
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
                       AVG(watts) AS watts, AVG(NULLIF(temp, 0)) AS temp
                FROM history
                WHERE srv_id=? AND ups=? AND ts>=?
                GROUP BY (ts - ?) / ?
                ORDER BY ts ASC
            """, (srv_id, ups, since_ts, lo, bucket)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

# Borra registros de más de 1 año y compacta el diario WAL. Se llama periódicamente desde un hilo aparte.
# EN: Delete records older than 1 year and compact the WAL journal. Called periodically from a separate thread.
def db_prune():
    """Elimina registros de más de 1 año. Llamar periódicamente."""
    cutoff = int(time.time()) - 365 * 86400
    with _db_lock:
        conn = db_connect()
        try:
            deleted = conn.execute("DELETE FROM history WHERE ts < ?", (cutoff,)).rowcount
            conn.execute("DELETE FROM outages WHERE t_end IS NOT NULL AND t_end < ?", (cutoff,))
            # Un UPS o servidor NUT defectuoso (o malicioso) que alterne OL/OB sin parar no debe hacer crecer la tabla sin límite: se conservan los 2000 cortes más recientes de cada UPS.
            # EN: A faulty (or malicious) UPS or NUT server flapping OL/OB must not grow the table without limit: the 2000 most recent outages of each UPS are kept.
            conn.execute("""DELETE FROM outages WHERE t_end IS NOT NULL AND id NOT IN (
                              SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY srv_id, ups ORDER BY t_start DESC) AS rn FROM outages) WHERE rn <= 2000)""")
            conn.commit()    # close the DELETE transaction first: a checkpoint inside it fails
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            conn.close()     # always release the connection (an open one keeps the DB locked)
    if deleted: log.info(f"DB pruned: {deleted} records older than 1 year deleted")

# Envoltorio que registra el error en vez de dejar morir el hilo.
# EN: Wrapper that logs the error instead of letting the thread die.
def _db_prune_safe():
    try: db_prune()
    except Exception as e: log.error(f"db_prune: {e}")

# ─── Servidores ───────────────────────────────────────────────────────────────
# Candado de la lista de servidores. Regla: cargar → modificar → guardar dentro de este candado.
# EN: Lock of the server list. Rule: load → modify → save inside this lock.
_srv_lock = threading.RLock()     # hold around load_servers() → modify → save_servers()

# Lista de servidores NUT. Una instalación nueva empieza SIN servidores (la UPS es opcional; se agrega desde la página);
# una lista vacía es válida (el usuario los borró todos). Si el archivo está dañado, se usa la copia .bak.
# EN: List of NUT servers. A fresh install starts with NO servers (a UPS is optional; add one from the page);
#     an empty list is valid (the user deleted them all). If the file is damaged, the .bak copy is used.
def load_servers():
    # No default server: a fresh install starts with an empty list (a UPS is optional) and the
    # user adds one from the page. Damaged file → last good copy (auth.read_json).
    return auth.read_json(DATA_FILE, [], list)

# Guarda la lista de servidores de forma atómica.
# EN: Save the server list atomically.
def save_servers(s):
    with _srv_lock:
        auth.write_json(DATA_FILE, s, mode=0o644)

# ─── Watts ────────────────────────────────────────────────────────────────────
# Estima la potencia en vatios probando de la más fiable a la menos fiable:
#   1) ups.realpower (el UPS la informa) · 2) VA × factor de potencia · 3) voltaje × corriente de salida
#   4) VA × carga% × 0,8 · 5) potencia nominal × carga%
# Si ninguna sirve, devuelve 0. Hay UPS (como el APC Easy SRV) que no reportan vatios directamente.
# EN: Estimate power in watts, trying from the most to the least reliable source:
#       1) ups.realpower (reported by the UPS) · 2) VA × power factor · 3) output voltage × current
#       4) VA × load% × 0.8 · 5) nominal power × load%
#     If none works, returns 0. Some UPS units (like the APC Easy SRV) do not report watts directly.
def _calc_watts(vars_):
    try:
        rp = float(vars_.get("ups.realpower") or 0)
        if rp > 0: return rp
    except (TypeError, ValueError): pass
    try:
        pva = float(vars_.get("ups.power") or 0)
        pf  = float(vars_.get("ups.powerfactor") or 0)
        if pva > 0 and pf > 0: return round(pva * pf, 1)
    except (TypeError, ValueError): pass
    try:
        vout = float(vars_.get("output.voltage") or 0)
        iout = float(vars_.get("output.current") or 0)
        if vout > 0 and iout > 0: return round(vout * iout, 1)
    except (TypeError, ValueError): pass
    try:
        pva  = float(vars_.get("ups.power") or 0)
        load = float(vars_.get("ups.load") or 0)
        if pva > 0 and load > 0: return round(pva * (load / 100) * 0.8, 1)
    except (TypeError, ValueError): pass
    try:
        nom  = float(vars_.get("ups.realpower.nominal") or
                     vars_.get("ups.power.nominal") or 0)
        load = float(vars_.get("ups.load") or 0)
        if nom > 0 and load > 0: return round(nom * (load / 100), 1)
    except (TypeError, ValueError): pass
    return 0.0

# ─── NUT Client ───────────────────────────────────────────────────────────────
# Cliente del protocolo de texto de upsd. Abre una conexión corta por consulta.
# EN: Client of upsd's text protocol. Opens a short connection per query.
class NUTClient:
    def __init__(self, host, port, timeout=5.0):
        self.host = host; self.port = int(port); self.timeout = timeout

    # Abre el socket TCP hacia upsd con tiempo límite.
    # EN: Open the TCP socket to upsd with a timeout.
    def _conn(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout); s.connect((self.host, self.port)); return s

    # Lee una línea de la respuesta (hasta el salto de línea).
    # EN: Read one line of the reply (up to the line break).
    def _readline(self, sock):
        buf = b""
        while True:
            ch = sock.recv(1)
            if not ch or ch == b"\n": break
            buf += ch
        return buf.decode(errors="replace").strip()

    # Envía un comando y junta las líneas de respuesta. Un «LIST …» termina en «END LIST»; los demás comandos
    # terminan con la primera línea VAR/VER/OK/ERR.
    # EN: Send a command and collect the reply lines. A "LIST …" ends at "END LIST"; the other commands
    #     end with the first VAR/VER/OK/ERR line.
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

    # Si upsd responde un error (por ejemplo DATA-STALE: el driver dejó de enviar datos), se levanta una excepción en vez de tratarlo como «sin datos».
    # EN: If upsd answers with an error (for example DATA-STALE: the driver stopped sending data), an exception is raised instead of treating it as "no data".
    @staticmethod
    def _check(lines):
        """upsd answers errors as `ERR <CODE>` (e.g. DATA-STALE): raise instead of treating it as empty data."""
        for l in lines:
            if l.startswith("ERR"):
                raise RuntimeError(f"upsd: {l[3:].strip() or 'error'}")
        return lines

    # Nombres y descripciones de los UPS que expone el servidor.
    # EN: Names and descriptions of the UPS units the server exposes.
    def list_ups(self):
        with self._conn() as s: lines = self._check(self._cmd(s, "LIST UPS"))
        return [{"name": m.group(1), "desc": m.group(2)}
                for line in lines for m in [re.match(r'^UPS (\S+) "(.*)"$', line)] if m]

    # Todas las variables de un UPS (battery.charge, input.voltage, ups.status, …) como diccionario.
    # EN: All the variables of a UPS (battery.charge, input.voltage, ups.status, …) as a dictionary.
    def get_vars(self, ups):
        with self._conn() as s: lines = self._check(self._cmd(s, f"LIST VAR {ups}"))
        return {m.group(1): m.group(2)
                for line in lines for m in [re.match(r'^VAR \S+ (\S+) "(.*)"$', line)] if m}

    # Direcciones de los equipos conectados a este UPS (los clientes upsmon, p. ej. los Synology y servidores). Si falla, lista vacía.
    # EN: Addresses of the machines connected to this UPS (upsmon clients, e.g. Synology units and servers). Empty list on failure.
    def list_clients(self, ups):
        try:
            with self._conn() as s: lines = self._cmd(s, f"LIST CLIENT {ups}")
            return [m.group(1) for line in lines
                    for m in [re.match(r'^CLIENT \S+ (\S+)$', line)] if m]
        except Exception as e:
            log.debug(f"list_clients: {e}"); return []

    # Versión del servidor NUT.
    # EN: NUT server version.
    def get_version(self):
        try:
            with self._conn() as s: lines = self._cmd(s, "VER")
            return next((l.strip() for l in lines if l.strip()), "")
        except (OSError, ValueError): return ""

# Anota en la línea de tiempo del Resumen los cambios de estado del UPS: pasa a batería, batería baja o vuelve la red.
# El estado se agrupa en tres modos (red, batería, batería baja) para no anotar cada variación de carga («OL CHRG»).
# EN: Record UPS state changes on the Overview timeline: goes on battery, low battery or mains is back.
#     The status is grouped into three modes (mains, battery, low battery) so each charge variation ("OL CHRG") is not recorded.
def _status_event(sid, name, status, entry):
    words = status.split()
    mode = "lb" if "LB" in words else "ob" if "OB" in words else "ol" if "OL" in words else "other"
    ch = auth.state_changed(f"nut:{sid}:{name}", mode)
    if not ch: return
    old, new = ch
    pct = f"{entry.get('charge', 0):.0f} %"
    if new == "lb":      auth.record_event("nut", "crit", f"{name}: low battery ({pct})", "ups_lowb", n=name, pct=pct)
    elif new == "ob":    auth.record_event("nut", "warn", f"{name}: on battery ({pct})", "ups_batt", n=name, pct=pct)
    elif new == "ol":    auth.record_event("nut", "info", f"{name}: mains power restored ({pct})", "ups_mains", n=name, pct=pct)
    else:                auth.record_event("nut", "warn", f"{name}: status {status}", "ups_other", n=name, st=status)

# ─── Cache en memoria (solo estado actual) ────────────────────────────────────
# Estado actual en memoria de un servidor NUT: variables de cada UPS, clientes, último error y última lectura buena.
# Solo guarda el «ahora»; el historial vive en SQLite.
# EN: Current in-memory state of a NUT server: variables of each UPS, clients, last error and last good reading.
#     It only keeps the "now"; the history lives in SQLite.
class SCache:
    def __init__(self, sid):
        self.id = sid; self.name = sid; self._lock = threading.RLock()
        self._ups = {}; self._clients = {}
        self._error = None; self._last_ok = None; self._ver = ""

    # Borra el estado (por ejemplo cuando el usuario cambia la dirección del servidor).
    # EN: Clear the state (for example when the user changes the server address).
    def reset(self):
        with self._lock:
            self._ups = {}; self._clients = {}
            self._error = None; self._last_ok = None; self._ver = ""

    # Guarda una lectura nueva y la anota en el historial (fuera del candado). Convierte las variables NUT a números
    # seguros y calcula los vatios. Si el estado no empieza con «OL» se escribe a disco de inmediato.
    # EN: Store a new reading and record it in the history (outside the lock). Converts the NUT variables to safe
    #     numbers and computes watts. If the status does not start with "OL" it is written to disk immediately.
    def update(self, name, vars_, clients=None, ver=""):
        with self._lock:
            self._ups[name]     = {**vars_, "_ts": time.time()}
            self._clients[name] = clients or []
            self._error = None; self._last_ok = time.time()
            if ver: self._ver = ver
        if auth.state_changed(f"nut-srv:{self.id}", "up"):
            auth.record_event("nut", "info", f"UPS server {self.name} reachable again", "ups_srv_up", n=self.name)
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
            outage_track(self.id, name, status, entry["charge"], entry["ts"])
            _status_event(self.id, name, status, entry)
        except Exception as e:
            log.debug(f"db_insert error: {e}")

    # Guarda el último error de conexión para mostrarlo en la página.
    # EN: Store the last connection error to show it on the page.
    def set_error(self, msg):
        with self._lock: self._error = msg
        ch = auth.state_changed(f"nut-srv:{self.id}", "down")
        if ch: auth.record_event("nut", "crit", f"UPS server {self.name} unreachable: {str(msg)[:80]}", "ups_srv_down", n=self.name, e=str(msg)[:80])

    # Estadísticas de disponibilidad de cada UPS; un fallo no impide devolver el resto del estado.
    # EN: Availability stats of each UPS; a failure does not prevent returning the rest of the state.
    def _stats(self, ups_snap):
        out = {}
        for n in ups_snap:
            try: out[n] = ups_stats(self.id, n)
            except Exception as e: log.debug(f"ups_stats: {e}")
        return out

    # Instantánea para la API: estado actual más historial según el rango pedido (1h, 1d, 1w, 1mo, all).
    # Con range=none solo se devuelve el estado actual y no se toca la base (así refresca la página sin costo).
    # EN: Snapshot for the API: current state plus history for the requested range (1h, 1d, 1w, 1mo, all).
    #     With range=none only the current state is returned and the database is not touched (so the page refreshes at no cost).
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
                    "history": {}, "stats": self._stats(ups_snap), "error": error, "last_ok": last_ok,
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
                "history": history, "stats": self._stats(ups_snap), "error": error, "last_ok": last_ok,
                "version": ver, "ts": time.time()}

# Tablas globales: caché, hilo y evento de despertar por servidor, protegidas por _gl.
# EN: Global tables: cache, thread and wake-up event per server, protected by _gl.
_caches: dict = {}; _pollers: dict = {}; _wake: dict = {}; _gl = threading.Lock()

# Garantiza que haya un hilo de consulta vivo para el servidor; si ya existía, lo despierta para consultar de inmediato (por ejemplo tras editarlo).
# EN: Guarantee a live polling thread for the server; if it already existed, wake it to query at once (for example after editing it).
def ensure_poller(server):
    sid = server["id"]
    with _gl:
        if sid not in _caches: _caches[sid] = SCache(sid)
        _caches[sid].name = server.get("name") or sid       # readable name for the Overview timeline
        ev = _wake.setdefault(sid, threading.Event())
        if sid in _pollers: ev.set()   # edited server: poll again right away
        if sid not in _pollers or not _pollers[sid].is_alive():
            t = threading.Thread(target=_poll, args=(server,), daemon=True)
            _pollers[sid] = t; t.start()
            log.info(f"Poller → {server['name']} ({server['host']}:{server['port']})")

# Olvida un servidor eliminado; su hilo termina solo al ver que ya no está en la lista.
# EN: Forget a deleted server; its thread ends on its own when it sees it is no longer in the list.
def remove_poller(sid):
    with _gl: _caches.pop(sid, None); _pollers.pop(sid, None); _wake.pop(sid, None)

# Bucle del hilo de consulta de un servidor: cada POLL_SEC segundos pregunta a upsd versión, UPS y variables,
# y actualiza la caché. Si el usuario edita host o puerto, se reconecta y descarta lo viejo; si lo elimina, el hilo termina.
# Un error de conexión nunca mata el hilo: se anota y se reintenta. Cada ~4 h lanza la limpieza del historial.
# EN: Loop of a server's polling thread: every POLL_SEC seconds it asks upsd for version, UPS list and variables,
#     and updates the cache. If the user edits host or port, it reconnects and drops the old data; if the server is deleted, the thread ends.
#     A connection error never kills the thread: it is logged and retried. About every 4 h it triggers history cleanup.
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
            cache.set_error(f"upsd not available at {server['host']}:{server['port']}")
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

# Lista de servidores que nunca lanza excepción (devuelve vacío ante un error de lectura).
# EN: Server list that never raises (returns empty on a read error).
def _safe_servers():
    try: return load_servers()
    except Exception: return []

# Al arrancar: prepara la base y lanza un hilo de consulta por servidor.
# EN: On startup: prepare the database and launch one polling thread per server.
def start_all():
    db_init()
    for s in load_servers(): ensure_poller(s)

# ─── Health ───────────────────────────────────────────────────────────────────
# Chequeos de salud de UPS Monitor: archivo de servidores, base abierta y no bloqueada, escritura de historial al día,
# hilos vivos, que cada upsd responda con datos frescos, y que lo que está en memoria realmente llegue al historial.
# EN: UPS Monitor health checks: servers file, database open and not locked, history writes up to date,
#     threads alive, each upsd answering with fresh data, and that what is in memory really reaches the history.
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
# Manejador HTTP. Cada petición se atiende en su propio hilo.
# EN: HTTP handler. Each request is served in its own thread.
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
            if n < 0 or n > 8192: return None
            return json.loads(self.rfile.read(n))
        except (ValueError, TypeError, OSError): return None

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

    # Rango pedido por la página (?range=1h|1d|1w|1mo|all).
    # EN: Range requested by the page (?range=1h|1d|1w|1mo|all).
    def _range_param(self):
        qs = parse_qs(urlparse(self.path).query)
        return qs.get("range", ["all"])[0]

    # GET: página, versión y salud son públicos; el resto exige sesión con UPS «readonly».
    # Rutas: /api/config, /api/servers, /api/ups, /api/history, /api/export/csv, /api/me.
    # EN: GET: page, version and health are public; the rest requires a session with UPS "readonly".
    #     Routes: /api/config, /api/servers, /api/ups, /api/history, /api/export/csv, /api/me.
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        tok  = self._token()
        if auth.serve_asset(self, STATIC_DIR, path): return   # .js / .css de la página

        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if path == "/api/version":     # shown in the page footer; only with a session (or from this machine)
            return self._json(200, {"version": auth.version()} if (auth.get_session(tok) or auth.is_local_request(self)) else {})
        if path == "/api/health":      # public: levels only; details need a valid session
            code, body = health_report(auth.health_mode(self, tok))
            return self._json(code, body)
        # En GET siempre responde ok: la página lo usa para saber que el servicio está vivo.
        # EN: On GET it always answers ok: the page uses it to know the service is alive.
        if path == "/api/login":
            return self._json(200, {"ok": True})

        if not auth.check_permission(tok, "nut", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        if path == "/api/config":
            self._json(200, {"poll_sec": POLL_SEC})
        # Servidores con su estado actual e historial del rango pedido; revive hilos de consulta que hayan muerto.
        # EN: Servers with their current state and history for the requested range; revives polling threads that died.
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
        # Historial de un solo UPS para un rango (el gráfico lo pide al cambiar de rango).
        # EN: History of a single UPS for a range (the chart requests it when the range changes).
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
        # Exporta el historial de un UPS como archivo CSV descargable (hasta 8640 puntos).
        # EN: Export a UPS history as a downloadable CSV file (up to 8640 points).
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
            fname = auth.safe_filename(f"ups-history-{sid}-{ups}-{time.strftime('%Y%m%d')}.csv")
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

    # POST: login/logout, alta de servidor y prueba de conexión. Alta y prueba requieren nivel «admin» de UPS.
    # EN: POST: login/logout, add server and connection test. Adding and testing require UPS "admin" level.
    def do_POST(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._token()
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
            must  = users.get(body["username"], {}).get("must_change_password", False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie",
                auth.session_cookie(token, ttl))
            body_resp = json.dumps({"ok": True, "username": body["username"],
                                    "permissions": u["permissions"],
                                    "must_change_password": must}).encode()
            self.send_header("Content-Length", str(len(body_resp)))
            self.end_headers(); self.wfile.write(body_resp); return

        if path == "/api/logout":
            auth.delete_session(tok)
            return self._json(200, {"ok": True})

        if not auth.check_permission(tok, "nut", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        # Alta de servidor NUT: valida host, nombre y puerto, rechaza host:puerto duplicado y lanza su hilo de consulta.
        # EN: Add a NUT server: validates host, name and port, rejects a duplicate host:port and starts its polling thread.
        if path == "/api/servers":
            if not auth.check_permission(tok, "nut", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            host = str(body.get("host") or "").strip()
            name = str(body.get("name") or "").strip()
            try: port = int(body.get("port") or 3493)
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
            if not host or not name: return self._json(400, {"error": "host and name are required"})
            if not 1 <= port <= 65535: return self._json(400, {"error": "Invalid port"})
            if not auth.valid_host(host): return self._json(400, {"error": "Invalid host"})
            if len(name) > 60 or re.search(r"[\x00-\x1f\x7f]", name): return self._json(400, {"error": "Invalid name"})
            import uuid
            with _srv_lock:
                srvs = load_servers()
                if any(s["host"]==host and s["port"]==port for s in srvs):
                    return self._json(409, {"error": "That host:port already exists"})
                server = {"id": str(uuid.uuid4()), "name": name, "host": host, "port": port}
                srvs.append(server); save_servers(srvs)
            ensure_poller(server)
            self._json(201, {"server": server})
        # Prueba de conexión a un upsd sin guardarlo: devuelve los UPS que encuentra o el error.
        # EN: Connection test to an upsd without saving it: returns the UPS units it finds or the error.
        elif path == "/api/test":
            if not auth.check_permission(tok, "nut", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            host = str(body.get("host") or "").strip()
            try: port = int(body.get("port") or 3493)
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
            if not auth.valid_host(host) or not 1 <= port <= 65535: return self._json(400, {"error": "Invalid host or port"})
            try:
                nut  = NUTClient(host, port, timeout=4)
                ups  = nut.list_ups(); ver = nut.get_version()
                self._json(200, {"ok": True, "ups_count": len(ups), "ups": ups, "version": ver})
            except Exception as e:
                self._json(200, {"ok": False, "error": str(e)})
        else:
            self._json(404, {"error": "Not found"})

    # PUT /api/servers/<id>: edita nombre, host o puerto de un servidor (solo admin); el hilo se reconecta solo.
    # EN: PUT /api/servers/<id>: edit name, host or port of a server (admin only); the thread reconnects by itself.
    def do_PUT(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._token()
        if not auth.check_permission(tok, "nut", "admin"):
            return self._json(403, {"error": "Admin permission required"})
        m = re.match(r'^/api/servers/([a-zA-Z0-9\-]+)$', path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})
        sid  = m.group(1)
        host = str(body.get("host") or "").strip()
        name = str(body.get("name") or "").strip()
        try: port = int(body.get("port") or 3493)
        except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
        if not host or not name: return self._json(400, {"error": "host and name are required"})
        if not 1 <= port <= 65535: return self._json(400, {"error": "Invalid port"})
        if not auth.valid_host(host): return self._json(400, {"error": "Invalid host"})
        if len(name) > 60 or re.search(r"[\x00-\x1f\x7f]", name): return self._json(400, {"error": "Invalid name"})
        with _srv_lock:
            srvs = load_servers()
            srv  = next((x for x in srvs if x["id"] == sid), None)
            if srv is None: return self._json(404, {"error": "Not found"})
            if any(x["id"] != sid and x["host"] == host and x["port"] == port for x in srvs):
                return self._json(409, {"error": "That host:port already exists"})
            srv.update({"name": name, "host": host, "port": port})
            save_servers(srvs)
        ensure_poller(srv)
        self._json(200, {"server": srv})

    # DELETE /api/servers/<id>: elimina un servidor y detiene su consulta (solo admin).
    # EN: DELETE /api/servers/<id>: remove a server and stop its polling (admin only).
    def do_DELETE(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path
        tok  = self._token()
        if not auth.check_permission(tok, "nut", "admin"):
            return self._json(403, {"error": "Admin permission required"})
        m = re.match(r'^/api/servers/([a-zA-Z0-9\-]+)$', path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        sid = m.group(1)
        with _srv_lock:
            srvs = load_servers()
            new  = [s for s in srvs if s["id"] != sid]
            if len(new) == len(srvs): return self._json(404, {"error": "Not found"})
            save_servers(new)
        remove_poller(sid); self._json(200, {"ok": True})

# Arranque: inicia los hilos de consulta y asegura que el búfer del historial se escriba al salir.
# systemd detiene el servicio con SIGTERM, por eso se instala un manejador que vacía el búfer antes de terminar.
# EN: Startup: starts the polling threads and makes sure the history buffer is written on exit.
#     systemd stops the service with SIGTERM, so a handler is installed that empties the buffer before finishing.
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
