#!/usr/bin/env python3
"""
Proxmox Monitor — Dashboard de nodos, VMs y CTs
API REST de Proxmox VE — sin dependencias externas
"""
# Proxmox Monitor (puerto 8084): muestra nodos, VMs, contenedores, almacenamiento y Ceph de uno o varios
# clusters Proxmox VE, hablando con su API REST (HTTPS, puerto 8006) con un token de API.
#
# Flujo de datos:
#   un hilo «poller» por cluster → PVEClient consulta la API → ClusterCache guarda la última lectura
#   → la página la pide a /api/clusters. El hilo consulta rápido (5 s) mientras alguien mira la
#   página y lento (60 s) cuando nadie la tiene abierta, para no gastar CPU en el servidor.
#
# Seguridad del certificado: Proxmox usa por defecto un certificado propio, así que no se puede
# validar contra una autoridad pública. En su lugar se «fija» la huella SHA-256 del certificado al
# agregar el cluster (el usuario la confirma) y cada conexión comprueba que siga siendo la misma
# ANTES de enviar el token.
#
# Estructura: cliente de la API · configuración de clusters · caché e historial · poller · salud · HTTP.
# EN: Proxmox Monitor (port 8084): shows nodes, VMs, containers, storage and Ceph of one or more Proxmox VE
#     clusters, talking to their REST API (HTTPS, port 8006) with an API token.
#
#     Data flow:
#       one "poller" thread per cluster → PVEClient queries the API → ClusterCache keeps the last reading
#       → the page requests it from /api/clusters. The thread polls fast (5 s) while someone is looking at the
#       page and slowly (60 s) when nobody has it open, so the server does not waste CPU.
#
#     Certificate security: Proxmox uses its own certificate by default, so it cannot be validated against a
#     public authority. Instead the SHA-256 fingerprint of the certificate is "pinned" when the cluster is added
#     (the user confirms it) and every connection checks it is still the same BEFORE sending the token.
#
#     Structure: API client · cluster configuration · cache and history · poller · health · HTTP.
import hashlib
import http.client
import json
import logging
import math
import os
import re
import socket
import ssl
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ThreadingHTTPServer.request_queue_size = 128      # default is 5: a burst of simultaneous connections got reset
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Módulo compartido de autenticación (carpeta hermana /auth).
# EN: Shared authentication module (sibling folder /auth).
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

sys.path.insert(0, str(Path(__file__).parent))
import backups
import diag
import extra

# Solo loopback; el acceso desde la red pasa por nginx.
# EN: Loopback only; network access goes through nginx.
HOST       = "127.0.0.1"
PORT       = 8084
STATIC_DIR = Path(__file__).parent / "static"
# clusters.json: clusters configurados, con su token de API (por eso el archivo es privado, modo 0600).
# EN: clusters.json: configured clusters, with their API token (so the file is private, mode 0600).
# Los datos viven en /var/lib/labtower/proxmox-monitor (el código de /opt es de solo lectura para el servicio).
# EN: The data lives in /var/lib/labtower/proxmox-monitor (the code in /opt is read-only for the service).
DATA_DIR   = auth.module_dir("proxmox-monitor")      # solo la ruta; la carpeta se crea al arrancar (auth.prepare_module en main)
LEGACY_FILES = ("clusters.json", "history.json")
DATA_FILE  = DATA_DIR / "clusters.json"
# Ritmos de consulta: rápido cuando hay alguien mirando, lento cuando no (variables PVE_POLL_*).
# EN: Polling rates: fast when someone is looking, slow when not (PVE_POLL_* variables).
POLL_ACTIVE = float(os.environ.get("PVE_POLL_ACTIVE", "5"))    # seconds, while someone is watching
POLL_IDLE   = float(os.environ.get("PVE_POLL_IDLE", "60"))     # seconds, when nobody has the page open
# Una página abierta cuenta como «mirando» durante este tiempo desde su última petición.
# EN: An open page counts as "looking" for this long after its last request.
VIEW_GRACE  = 30                                              # a viewer counts as active for this long
# Versión de Proxmox y estado de Ceph cambian poco: se refrescan solo una vez por minuto.
# EN: Proxmox version and Ceph state change little: they are refreshed only once a minute.
SLOW_EVERY  = 60                                              # version / ceph refresh period
# Cada cuántos segundos se guarda una muestra de CPU/RAM por nodo para los gráficos.
# EN: How often, in seconds, a CPU/RAM sample per node is stored for the charts.
HIST_EVERY  = 30                                              # node history sampling period
# Cada cuántos segundos se lee el SMART de los discos de cada nodo (smartctl es pesado: no hace falta más seguido).
# EN: How often, in seconds, the SMART data of each node's disks is read (smartctl is heavy: no need to do it more often).
SMART_EVERY = float(os.environ.get("PVE_SMART_EVERY", "900"))
# Cada cuántos segundos se revisan los respaldos (contenido de los storages de backup y tareas vzdump).
# EN: How often, in seconds, the backups are checked (content of the backup storages and vzdump tasks).
BACKUP_EVERY = float(os.environ.get("PVE_BACKUP_EVERY", "600"))
# Cada cuántos segundos se leen las MAC e IP de las VM y contenedores (para mapearlos en Net Monitor).
# EN: How often, in seconds, the MACs and IPs of VMs and containers are read (to map them in Net Monitor).
GUEST_EVERY = float(os.environ.get("PVE_GUEST_EVERY", "300"))
# Información adicional (HA, replicación, certificados, tareas, tendencias): cada tanto; 0 la desactiva.
# EN: Extra information (HA, replication, certificates, tasks, trends): this often; 0 turns it off.
EXTRA_EVERY = float(os.environ.get("PVE_EXTRA_EVERY", "300"))
SERIES_EVERY, SERIES_KEEP = 900, 45 * 86400
# Instante de la última petición de un navegador (decide el ritmo de consulta).
# EN: Time of the last browser request (decides the polling rate).
_last_view  = 0.0                                             # last time a browser asked for data

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("pve")

# ─── Proxmox API client ────────────────────────────────────────────────────────
# Error HTTP devuelto por la API de Proxmox; guarda el código para decidir si reintentar o cambiar de método.
# EN: HTTP error returned by the Proxmox API; keeps the code to decide whether to retry or switch method.
class PVEHTTPError(RuntimeError):
    def __init__(self, status, reason=""):
        super().__init__(f"HTTP {status}: {reason}")
        self.status = status

# El certificado presentado no coincide con la huella fijada (posible cambio legítimo o intento de suplantación).
# EN: The presented certificate does not match the pinned fingerprint (a legitimate change or a spoofing attempt).
class PVECertError(Exception):
    pass

# Normaliza una huella SHA-256 a 64 caracteres hexadecimales en minúscula; devuelve '' si no es válida.
# EN: Normalise a SHA-256 fingerprint to 64 lowercase hex characters; returns '' if invalid.
def _fp_norm(fp) -> str:
    """Normalise a SHA-256 fingerprint to 64 lowercase hex chars ('' if it is not one)."""
    h = re.sub(r"[^0-9a-fA-F]", "", fp or "").lower() if isinstance(fp, str) else ""
    return h if len(h) == 64 else ""

# Formato legible de la huella: pares hexadecimales en mayúscula separados por «:» (como la muestra Proxmox).
# EN: Readable fingerprint format: uppercase hex pairs separated by ":" (as Proxmox shows it).
def _fp_fmt(h: str) -> str:
    return ":".join(h[i:i + 2] for i in range(0, 64, 2)).upper()

# Obtiene la huella del certificado que presenta un servidor, SIN enviar el token (se usa para que el usuario la confirme).
# EN: Get the fingerprint of the certificate a server presents, WITHOUT sending the token (so the user can confirm it).
def fetch_fingerprint(host, port, timeout=8) -> str:
    """SHA-256 of the certificate the server presents (no token is sent). Normalised hex."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, int(port)), timeout=timeout) as raw, ctx.wrap_socket(raw, server_hostname=host) as tls:
        return hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest()

# Cliente de la API de Proxmox con una conexión HTTPS persistente (evita repetir el handshake TLS en cada consulta).
# Autentica con el token de API en la cabecera Authorization.
# EN: Proxmox API client with a persistent HTTPS connection (avoids repeating the TLS handshake on every query).
#     Authenticates with the API token in the Authorization header.
class PVEClient:
    """PVE API client with a persistent HTTPS connection (avoids a TLS handshake on every poll)."""
    def __init__(self, host, port, user, token_name, token_value, verify_ssl=False, fingerprint=None):
        self.host, self.port = host, int(port)
        self.sig = (host, int(port), user, token_name, token_value, bool(verify_ssl))   # connection data, see _client_for
        self.fingerprint = _fp_norm(fingerprint)          # pinned SHA-256 of the server certificate
        self.headers = {
            "Authorization": f"PVEAPIToken={user}!{token_name}={token_value}",
            "Accept":        "application/json",
        }
        self.ctx = ssl.create_default_context()
        if not verify_ssl:
            self.ctx.check_hostname = False
            self.ctx.verify_mode    = ssl.CERT_NONE
        self._conn = None
        self._lock = threading.Lock()

    # Cierra la conexión actual (la siguiente consulta abre una nueva).
    # EN: Close the current connection (the next query opens a new one).
    def close(self):
        try:
            if self._conn: self._conn.close()
        except Exception:  # noqa: BLE001, S110 - limpieza al terminar; un fallo no cambia el resultado / EN: cleanup; a failure does not change the result
            pass
        self._conn = None

    # GET a la API. Si hay huella fijada, se comprueba apenas se abre la conexión y antes de enviar el token.
    # Si una conexión persistente quedó vieja, se reabre y se reintenta una vez.
    # EN: GET to the API. If a fingerprint is pinned, it is checked as soon as the connection opens and before the token is sent.
    #     If a persistent connection went stale, it is reopened and retried once.
    def get(self, path: str) -> dict:
        with self._lock:
            for attempt in (1, 2):
                try:
                    if self._conn is None:
                        self._conn = http.client.HTTPSConnection(self.host, self.port, timeout=8, context=self.ctx)
                        if self.fingerprint:            # check the certificate BEFORE sending the API token
                            self._conn.connect()
                            got = hashlib.sha256(self._conn.sock.getpeercert(binary_form=True)).hexdigest()
                            if got != self.fingerprint:
                                self.close()
                                raise PVECertError("Certificate fingerprint mismatch: the server's certificate "
                                                   "changed (re-pin it if this is expected)")
                    self._conn.request("GET", "/api2/json" + path, headers=self.headers)
                    r = self._conn.getresponse()
                    body = r.read()
                    if r.status >= 400:
                        raise PVEHTTPError(r.status, r.reason)
                    return json.loads(body.decode())
                except (PVEHTTPError, PVECertError):
                    raise
                except (http.client.HTTPException, OSError, ValueError):
                    self.close()                      # stale keep-alive connection: reconnect once
                    if attempt == 2:
                        raise

    # Una sola llamada trae nodos, VMs, contenedores y almacenamientos de todo el cluster.
    # EN: A single call brings nodes, VMs, containers and storage of the whole cluster.
    def resources(self) -> list:
        """One call for nodes, VMs, CTs and storages of the whole cluster."""
        return self.get("/cluster/resources").get("data", [])

    def nodes(self) -> list:
        return self.get("/nodes").get("data", [])

    def vms(self, node: str) -> list:
        return self.get(f"/nodes/{node}/qemu").get("data", [])

    def containers(self, node: str) -> list:
        return self.get(f"/nodes/{node}/lxc").get("data", [])

    def storage(self, node: str) -> list:
        return self.get(f"/nodes/{node}/storage").get("data", [])

    # Estado del cluster (quórum, miembros); si falla devuelve lista vacía.
    # EN: Cluster status (quorum, members); returns an empty list on failure.
    def cluster_status(self) -> list:
        try:
            return self.get("/cluster/status").get("data", [])
        except Exception:  # noqa: BLE001 - red o servicio externo: cualquier fallo es «sin respuesta» / network or external service: any failure means «no answer»
            return []

    # Versión de Proxmox VE; si falla devuelve cadena vacía.
    # EN: Proxmox VE version; returns an empty string on failure.
    def version(self) -> str:
        try:
            return self.get("/version").get("data", {}).get("version", "")
        except Exception:  # noqa: BLE001 - red o servicio externo: cualquier fallo es «sin respuesta» / network or external service: any failure means «no answer»
            return ""

# ─── Clusters config ──────────────────────────────────────────────────────────
# Candado de la lista de clusters. Regla: cargar → modificar → guardar dentro de este candado.
# EN: Lock of the cluster list. Rule: load → modify → save inside this lock.
_cl_lock = threading.RLock()      # hold around load_clusters() → modify → save_clusters()

# Lee clusters.json (con la red de seguridad de auth.read_json).
# EN: Read clusters.json (with the safety net of auth.read_json).
# Valida los campos de un cluster (alta o edición). En edición, un secreto vacío conserva el guardado.
# EN: Validate a cluster's fields (add or edit). When editing, an empty secret keeps the stored one.
def cluster_fields(body: dict, current=None) -> dict:
    g = lambda k: str(body.get(k) or "").strip()
    host, name, user, tname, tval = g("host"), g("name"), g("user"), g("token_name"), g("token_value")
    if not tval and current is not None: tval = current.get("token_value", "")
    try: port = int(body.get("port", 8006))
    except (TypeError, ValueError): raise ValueError("Invalid port")
    if not all([host, name, user, tname, tval]): raise ValueError("All fields are required")
    if not auth.valid_target(host): raise ValueError("Invalid host (this machine and link-local addresses are not allowed)")
    if len(name) > 60 or re.search(r"[\x00-\x1f\x7f]", name): raise ValueError("Invalid name")
    if not re.fullmatch(r"[A-Za-z0-9_.@!-]{1,64}", user) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", tname):
        raise ValueError("Invalid user or token name")
    if not 1 <= port <= 65535: raise ValueError("Invalid port")
    if len(tval) > 256 or re.search(r"[\x00-\x1f\x7f\s]", tval): raise ValueError("Invalid token secret")
    return {"name": name, "host": host, "port": port, "user": user, "token_name": tname, "token_value": tval}

# Cliente para la configuración actual de un cluster: si host, puerto, usuario o token no cambiaron se reutiliza (y adopta una
# huella fijada después); si cambiaron (el cluster se editó) se cierra y se crea otro. Así una edición se aplica sin reiniciar.
# EN: Client for a cluster's current configuration: if host, port, user or token did not change it is reused (and adopts a
#     fingerprint pinned later); if they changed (the cluster was edited) it is closed and a new one is made. An edit applies without a restart.
def _client_for(cur: dict, client=None):
    sig = (cur["host"], int(cur.get("port", 8006)), cur["user"], cur["token_name"], cur["token_value"], bool(cur.get("verify_ssl", False)))
    if client is not None and client.sig == sig:
        fp = _fp_norm(cur.get("fingerprint"))
        if fp != client.fingerprint: client.fingerprint = fp; client.close()
        return client
    if client is not None: client.close()
    return PVEClient(host=cur["host"], port=cur.get("port", 8006), user=cur["user"], token_name=cur["token_name"],
                     token_value=cur["token_value"], verify_ssl=cur.get("verify_ssl", False), fingerprint=cur.get("fingerprint"))

def load_clusters() -> list:
    return auth.read_json(DATA_FILE, [], list)

# Guarda clusters.json de forma atómica y con permisos 0600 (contiene tokens).
# EN: Save clusters.json atomically with 0600 permissions (it contains tokens).
def save_clusters(c: list):
    # clusters.json holds the Proxmox API tokens: private to the service (0600)
    with _cl_lock:
        auth.write_json(DATA_FILE, c)

# ─── Cache ────────────────────────────────────────────────────────────────────
# Última lectura por cluster y hilo de consulta por cluster (protegidos por _glock).
# EN: Last reading per cluster and polling thread per cluster (protected by _glock).
_cache:   dict = {}   # { cluster_id: snapshot }
_pollers: dict = {}
_glock = threading.Lock()

# ─── Ring buffer de historial CPU/RAM por nodo ────────────────────────────────
# Historial de CPU y RAM por nodo: un «buffer circular» de ~12 horas (1 muestra cada 30 s) para los gráficos de
# cada nodo y del Resumen. Vive en memoria y se guarda en la base de datos (ver «Persistencia» más abajo).
# EN: CPU and RAM history per node: a ~12-hour "circular buffer" (1 sample every 30 s) for the per-node charts and
#     the Overview. It lives in memory and is saved to the database (see "Persistence" below).
from collections import deque as _deque

_NODE_HISTORY: dict = {}   # { "cid:node": deque of {ts, cpu, mem_pct} }
_HIST_MAX = 1440           # ~12h a 30s
_hist_lock = threading.Lock()

# Agrega una muestra de CPU/RAM de un nodo; fija el muestreo en 30 s aunque se consulte más rápido.
# EN: Add a CPU/RAM sample of a node; sampling is fixed at 30 s even if polling is faster.
def push_node_history(cid: str, node_name: str, cpu: float, mem: int, maxmem: int):
    key = f"{cid}:{node_name}"
    mem_pct = round(mem / maxmem * 100, 1) if maxmem > 0 else 0
    with _hist_lock:
        if key not in _NODE_HISTORY:
            _NODE_HISTORY[key] = _deque(maxlen=_HIST_MAX)
        if _NODE_HISTORY[key] and time.time() - _NODE_HISTORY[key][-1]["ts"] < HIST_EVERY - 1:
            return                         # fixed 30 s sampling even when polling faster
        pt = {"ts": int(time.time()), "cpu": round(cpu*100, 1), "mem": mem_pct}
        _NODE_HISTORY[key].append(pt)
    _store_sample(cid, node_name, pt["ts"], pt["cpu"], pt["mem"])

# Muestras guardadas de un nodo.
# EN: Stored samples of a node.
def get_node_history(cid: str, node_name: str) -> list:
    key = f"{cid}:{node_name}"
    with _hist_lock:
        return list(_NODE_HISTORY.get(key, []))

# Persistencia: cada muestra se guarda en metrics.db (tabla pve_samples, compartida con el Resumen) en el momento, y
# al arrancar se recargan las últimas ~12 h para los gráficos, así que sobreviven a reinicios, actualizaciones y cortes
# de luz. Se conservan PVE_KEEP_DAYS días (7 por defecto). Si queda un history.json de la versión 1.2.0o, se importa
# una vez y se renombra a .migrated.
# EN: Persistence: every sample is stored at once in metrics.db (table pve_samples, shared with the Overview) and at
#     startup the last ~12 h are reloaded for the charts, so they survive restarts, upgrades and power cuts.
#     PVE_KEEP_DAYS days are kept (7 by default). A leftover history.json from version 1.2.0o is imported once and
#     renamed to .migrated.
HIST_FILE  = Path(os.environ.get("PVE_HISTORY", str(DATA_FILE.with_name("history.json"))))   # legacy JSON (1.2.0o)
HIST_KEEP  = auth.keep_days("PVE_KEEP_DAYS", 7) * 86400

def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and not math.isnan(x)

def _store_sample(cid, node, ts, cpu, mem):
    try:
        c = auth.metrics_conn()
        try:
            c.execute("INSERT OR REPLACE INTO pve_samples (cid,node,ts,cpu,mem) VALUES (?,?,?,?,?)", (cid, node, ts, cpu, mem))
            c.commit()
        finally: c.close()
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not store the history sample: {e}")

def _migrate_history(c):
    if not HIST_FILE.is_file(): return
    try:
        if c.execute("SELECT 1 FROM pve_samples LIMIT 1").fetchone() is None:
            data, now, rows = auth.read_json(HIST_FILE, {}, dict), time.time(), []
            for key, pts in data.items():
                if not isinstance(key, str) or ":" not in key or not isinstance(pts, list): continue
                cid, node = key.rsplit(":", 1)
                rows += [(cid, node, int(r[0]), r[1], r[2]) for r in pts
                         if isinstance(r, list) and len(r) == 3 and all(_num(v) for v in r) and now - HIST_KEEP < r[0] <= now + 60]
            c.executemany("INSERT OR IGNORE INTO pve_samples (cid,node,ts,cpu,mem) VALUES (?,?,?,?,?)", rows); c.commit()
            log.info(f"History: imported {len(rows)} samples from {HIST_FILE.name}")
        HIST_FILE.rename(HIST_FILE.with_name(HIST_FILE.name + ".migrated"))
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not import the old history: {e}")

# Recarga las últimas ~12 h de los clusters que siguen configurados.
# EN: Reload the last ~12 h of the clusters that are still configured.
def load_history():
    n = 0
    try:
        c = auth.metrics_conn()
        try:
            _migrate_history(c)
            c.execute("DELETE FROM pve_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,)); c.commit()
            try: keep = {x.get("id") for x in load_clusters()}
            except (OSError, ValueError): keep = None
            cut = int(time.time()) - _HIST_MAX * HIST_EVERY
            rows = c.execute("SELECT cid,node,ts,cpu,mem FROM pve_samples WHERE ts >= ? ORDER BY ts", (cut,)).fetchall()
        finally: c.close()
        with _hist_lock:
            for cid, node, ts, cpu, mem in rows:
                if keep is not None and cid not in keep: continue
                dq = _NODE_HISTORY.setdefault(f"{cid}:{node}", _deque(maxlen=_HIST_MAX))
                dq.append({"ts": ts, "cpu": cpu, "mem": mem}); n += 1
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not load the history: {e}")
    return n

def _history_pruner():
    while True:
        time.sleep(3600)
        try:
            c = auth.metrics_conn()
            try: c.execute("DELETE FROM pve_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,)); c.commit()
            finally: c.close()
        except Exception as e: log.warning(f"could not prune the history: {e}")  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running


# Última lectura de un cluster (datos, error y hora). El evento «wake» obliga al poller a refrescar de inmediato.
# EN: Last reading of a cluster (data, error and time). The "wake" event forces the poller to refresh at once.
class ClusterCache:
    def __init__(self, cid):
        self.id    = cid
        self._lock = threading.RLock()
        self._data = {}
        self._err  = None
        self._ts   = None
        self._kind = None
        self.wake  = threading.Event()     # set to make the poller refresh right now

    def update(self, data: dict):
        with self._lock:
            self._data = data
            self._err  = self._kind = None
            self._ts   = time.time()

    # kind: «cert» si el certificado ya no coincide con la huella fijada (la página ofrece volver a fijarlo).
    # EN: kind: "cert" when the certificate no longer matches the pinned fingerprint (the page offers to pin it again).
    def set_error(self, e: str, kind=None):
        with self._lock:
            self._err, self._kind = e, kind

    def snap(self) -> dict:
        with self._lock:
            return {"id": self.id, "data": dict(self._data),
                    "error": self._err, "error_kind": self._kind if self._err else None, "ts": self._ts}

# ─── Diagnóstico: reinicios, SMART ────────────────────────────────────────────
# diag.json guarda la hora de arranque conocida de cada nodo, el registro de reinicios y los «unsafe shutdowns» vistos,
# para detectar reinicios ocurridos mientras este módulo estaba parado.
# EN: ─── Diagnostics: reboots, SMART ───────────────────────────────────────────
#     diag.json keeps each node's last known boot time, the reboot log and the "unsafe shutdowns" seen, so reboots that
#     happened while this module was stopped are detected too.
DIAG_FILE   = DATA_DIR / "diag.json"
_diag_lock  = threading.Lock()
_diag_state = None            # loaded on first use
_diag_dump  = ""              # last text written, to save only on change
_smart: dict = {}             # { cluster_id: {"ts": .., "nodes": {node: {"disks": [...], "error": str|None}}} }
_smart_threads: dict = {}
_waves_sent: set = set()

def _diag_load():
    global _diag_state, _diag_dump
    if _diag_state is None:
        d = auth.read_json(DIAG_FILE, {}, dict)
        _diag_state = {"boots": d.get("boots") if isinstance(d.get("boots"), dict) else {},
                       "reboots": [r for r in d.get("reboots", []) if isinstance(r, dict)] if isinstance(d.get("reboots"), list) else [],
                       "unsafe": d.get("unsafe") if isinstance(d.get("unsafe"), dict) else {}}
        _diag_dump = json.dumps(_diag_state, sort_keys=True)
    return _diag_state

def _diag_save():
    global _diag_dump
    txt = json.dumps(_diag_state, sort_keys=True)
    if txt == _diag_dump: return
    try:
        auth.write_json(DIAG_FILE, _diag_state, indent=None)
        _diag_dump = txt
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not save the diagnostics state: {e}")

# Detecta reinicios de nodos y los anota en la línea de tiempo; si varios nodos se reinician casi a la vez, lo marca aparte.
# EN: Detect node reboots and put them on the timeline; if several nodes reboot at about the same time, it is flagged separately.
def _observe_reboots(cluster, nodes_data):
    cid, cname = cluster["id"], cluster["name"]
    with _diag_lock:
        st = _diag_load()
        new = diag.observe_boots(st, cid, cname, nodes_data, time.time())
        waves = diag.with_waves([r for r in st["reboots"] if r.get("cid") == cid]) if new else []
        _diag_save()
    for r in new:
        hm = time.strftime("%H:%M", time.localtime(r["boot"]))
        auth.record_event("pve", "warn", f"{cname}/{r['n']}: node rebooted (boot {hm})", "pve_reboot", c=cname, n=r["n"], b=hm)
    for r in new:
        w = next((x for x in waves if x["boot"] == r["boot"] and x["n"] == r["n"]), None)
        if not w or not w.get("wave"): continue
        grp = [x for x in waves if x.get("wave") == w["wave"]]
        members = {x["n"] for x in grp}
        key = (cid, min(x["boot"] for x in grp), len(members))
        if key in _waves_sent: continue
        _waves_sent.add(key)
        if len(_waves_sent) > 500: _waves_sent.clear()
        names = ", ".join(sorted(members))
        auth.record_event("pve", "crit", f"{cname}: {len(members)} nodes rebooted within {diag.GROUP_WINDOW // 60} min ({names})",
                          "pve_reboot_multi", c=cname, cnt=len(members), mins=diag.GROUP_WINDOW // 60, ns=names)

# Quórum de corosync y OSD de Ceph: anota cuando cambian.
# EN: Corosync quorum and Ceph OSDs: record when they change.
def _diag_events(cluster, cs, cp):
    cid, cname = cluster["id"], cluster["name"]
    if cs:
        ch = auth.state_changed(f"pve-quorum:{cid}", "ok" if cs["quorate"] else "lost")
        if ch:
            if ch[1] == "lost": auth.record_event("pve", "crit", f"{cname}: cluster lost quorum", "pve_quorum_lost", c=cname)
            else:               auth.record_event("pve", "info", f"{cname}: quorum recovered", "pve_quorum_ok", c=cname)
    if cp:
        ch = auth.state_changed(f"pve-osd:{cid}", cp["down"])
        if ch and ch[1] > ch[0]:
            auth.record_event("pve", "crit", f"{cname}: Ceph has {cp['down']} OSD down ({cp['up']}/{cp['osds']} up)", "pve_osd_down", c=cname, d=cp["down"], u=cp["up"], t=cp["osds"])
        elif ch and ch[1] == 0:
            auth.record_event("pve", "info", f"{cname}: all Ceph OSDs up again", "pve_osd_ok", c=cname)

# Lee la lista de discos y el SMART de un nodo. Un disco que falle no impide leer los demás.
# EN: Read the disk list and the SMART data of a node. A disk that fails does not stop the others being read.
_DEV_RE = re.compile(r"^/dev/[A-Za-z0-9_./-]{1,40}$")
def _read_node_smart(client, node):
    from urllib.parse import quote
    rows = client.get(f"/nodes/{quote(node, safe='')}/disks/list").get("data") or []
    out = []
    for row in rows[:64]:
        if not isinstance(row, dict) or not _DEV_RE.match(str(row.get("devpath", ""))): continue
        try:    sm = client.get(f"/nodes/{quote(node, safe='')}/disks/smart?disk={quote(row['devpath'], safe='/')}").get("data")
        except Exception: sm = None  # noqa: BLE001 - red o servicio externo: cualquier fallo es «sin respuesta» / network or external service: any failure means «no answer»
        out.append(diag.summarize_disk(row, sm))
    return out

def _smart_round(cluster, client, cache):
    cid, cname = cluster["id"], cluster["name"]
    names = [n["name"] for n in (cache.snap().get("data", {}).get("nodes") or []) if n.get("status") == "online"]
    res = {}
    for node in names:
        try:
            disks = _read_node_smart(client, node)
            res[node] = {"disks": disks, "error": None}
        except Exception as e:  # noqa: BLE001 - el error queda guardado y se muestra / the error is kept and shown
            res[node] = {"disks": [], "error": str(e)[:160]}
            continue
        for d in disks:
            ch = auth.state_changed(f"pve-smart:{cid}:{node}:{d['serial'] or d['dev']}", "bad" if d["warns"] else "ok")
            if ch and ch[1] == "bad":
                auth.record_event("pve", "warn", f"{cname}/{node}: disk {d['dev']} SMART warning ({', '.join(d['warns'])})",
                                  "pve_smart", c=cname, n=node, d=d["dev"], w=", ".join(d["warns"]))
        with _diag_lock:
            up = diag.unsafe_increases(_diag_load(), cid, node, disks)
            _diag_save()
        for u in up:
            auth.record_event("pve", "warn", f"{cname}/{node}: {u['dev']} unsafe shutdowns {u['was']} → {u['now']} (power loss or unclean reboot)",
                              "pve_unsafe", c=cname, n=node, d=u["dev"], a=u["was"], b=u["now"])
    _smart[cid] = {"ts": int(time.time()), "nodes": res}

# Hilo del SMART de un cluster: termina cuando el cluster se elimina.
# EN: A cluster's SMART thread: it ends when the cluster is deleted.
def _smart_loop(cluster, cache):
    cid = cluster["id"]
    client = None
    time.sleep(min(30, SMART_EVERY))
    while _cache.get(cid) is cache:
        try:
            cur = next((c for c in load_clusters() if c["id"] == cid), None)
            if cur is None: break
            client = _client_for(cur, client)
            _smart_round(cur, client, cache)
        except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
            log.warning(f"[{cluster['name']}] SMART round: {e}")
            if client: client.close()
        time.sleep(SMART_EVERY)
    if client: client.close()
    _smart.pop(cid, None)

# ─── Respaldos ────────────────────────────────────────────────────────────────
# Para cada VM/CT: su respaldo más reciente (leído del contenido de los storages que admiten «backup») y si es demasiado
# viejo. Además, las tareas vzdump de los últimos 7 días. Se lee en un hilo aparte cada PVE_BACKUP_EVERY segundos.
# EN: ─── Backups ───────────────────────────────────────────────────────────────
#     For each VM/CT: its newest backup (read from the content of the storages that allow "backup") and whether it is too
#     old. Plus the vzdump tasks of the last 7 days. Read in a separate thread every PVE_BACKUP_EVERY seconds.
_backups: dict = {}           # { cluster_id: {"ts", "max_age_h", "ignore", "rows", "tasks", "storages"} }
_backup_threads: dict = {}
_guest_threads: dict = {}
_bk_seen: dict = {}           # { cluster_id: set of failed task ids already reported (None before the first reading) }

def _backup_round(cluster, client, cache):
    from urllib.parse import quote
    cid, cname = cluster["id"], cluster["name"]
    cfg = cluster.get("backup") if isinstance(cluster.get("backup"), dict) else {}
    try:    cfg = backups.migrate_config(backups.clean_config(cfg)) if cfg else {"max_age_h": backups.DEFAULT_MAX_AGE_H, "ignore": []}
    except ValueError: cfg = {"max_age_h": backups.DEFAULT_MAX_AGE_H, "ignore": []}
    nodes = cache.snap().get("data", {}).get("nodes") or []
    guests, targets, seen_shared = [], [], set()
    for n in nodes:
        if n.get("status") != "online": continue
        guests += [dict(g, type="qemu", node=n["name"]) for g in n.get("vms") or []]
        guests += [dict(g, type="lxc", node=n["name"]) for g in n.get("cts") or []]
        for st in n.get("storage") or []:
            if "backup" not in str(st.get("content", "")) or not st.get("active"): continue
            if st.get("shared"):
                if st["storage"] in seen_shared: continue
                seen_shared.add(st["storage"])
            targets.append((n["name"], st["storage"]))
    contents, storages = [], []
    for node, sto in targets[:40]:
        try:
            items = client.get(f"/nodes/{quote(node, safe='')}/storage/{quote(sto, safe='')}/content?content=backup").get("data") or []
            contents.append({"storage": sto, "node": node, "items": items}); storages.append({"storage": sto, "node": node, "count": len(items), "error": None})
        except Exception as e:  # noqa: BLE001 - el error queda guardado y se muestra / the error is kept and shown
            storages.append({"storage": sto, "node": node, "count": 0, "error": str(e)[:120]})
    try:    tasks = backups.parse_tasks(client.get("/cluster/tasks").get("data"), time.time())
    except Exception: tasks = []  # noqa: BLE001 - red o servicio externo: cualquier fallo es «sin respuesta» / network or external service: any failure means «no answer»
    now = time.time()
    rows = backups.evaluate(guests, backups.newest_by_vmid(contents), cfg["max_age_h"], cfg["ignore"], now)
    # Un storage que no se pudo leer no debe hacer pasar por «sin respaldo» a las VMs: se anota y no se evalúa nada.
    unreadable = any(s["error"] for s in storages)
    for r in rows:
        if unreadable and r["status"] in ("never", "old"): r["status"] = "unknown"
        if r["status"] == "unknown": continue
        ch = auth.state_changed(f"pve-bk:{cid}:{r['vmid']}", r["status"])
        if ch and ch[1] in ("old", "never"):
            h = int(r["age"] // 3600) if r["age"] is not None else -1
            auth.record_event("pve", "warn", f"{cname}/{r['name'] or r['vmid']}: " + ("no backup found" if ch[1] == "never" else f"last backup {h} h ago"),
                              "pve_backup_old" if ch[1] == "old" else "pve_backup_never", c=cname, n=r["name"] or str(r["vmid"]), v=r["vmid"], h=h)
        elif ch and ch[0] in ("old", "never") and ch[1] == "ok":
            auth.record_event("pve", "info", f"{cname}/{r['name'] or r['vmid']}: backup up to date again", "pve_backup_ok", c=cname, n=r["name"] or str(r["vmid"]), v=r["vmid"])
    _bk_seen[cid], failed = backups.new_failures(_bk_seen.get(cid), tasks)
    for t in failed:
        who = f"VM {t['vmid']}" if t["vmid"] else "job"
        auth.record_event("pve", "crit", f"{cname}/{t['node']}: backup {who} failed ({t['status'][:60]})", "pve_backup_fail", c=cname, n=t["node"], w=who, e=t["status"][:60])
    _backups[cid] = {"ts": int(now), "max_age_h": cfg["max_age_h"], "ignore": cfg["ignore"], "rows": rows, "tasks": tasks, "storages": storages}

def _backup_loop(cluster, cache):
    cid = cluster["id"]
    client = None
    time.sleep(min(20, BACKUP_EVERY))
    while _cache.get(cid) is cache:
        try:
            cur = next((c for c in load_clusters() if c["id"] == cid), None)
            if cur is None: break
            client = _client_for(cur, client)
            _backup_round(cur, client, cache)
        except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
            log.warning(f"[{cluster['name']}] backup round: {e}")
            if client: client.close()
        time.sleep(BACKUP_EVERY)
    if client: client.close()
    _backups.pop(cid, None); _bk_seen.pop(cid, None)

# ─── Información adicional ────────────────────────────────────────────────────
# Lo que se calcula con la lectura que ya hay (cambios de estado, bloqueos, capacidad) se hace en cada vuelta del poller; lo que
# necesita más consultas a la API (HA, replicación, certificados, tareas, tendencias) va en un hilo aparte cada EXTRA_EVERY s.
# Cada consulta que el token no pueda hacer se anota en `errors` y esa parte queda vacía: nada falla por falta de permisos.
# EN: What is computed from the reading we already have (state changes, locks, capacity) happens on every poller pass; what
#     needs more API queries (HA, replication, certificates, tasks, trends) runs in its own thread every EXTRA_EVERY s.
#     Every query the token cannot make is noted in `errors` and that part stays empty: nothing fails for lack of permission.
_extra: dict = {}             # cid -> result of the last extra round
_extra_threads: dict = {}
_live: dict = {}              # cid -> {"alerts": [...], "cap": {...}} from the last poller pass
_xlock = threading.Lock()
_guest_prev: dict = {}        # cid -> {vmid: {st, name, node, kind}} (absent before the first pass)
_lock_state: dict = {}        # cid -> {vmid: {lock, since}}
_task_seen: dict = {}         # cid -> set of failed task upids already reported (None before the first reading)
_al_on: dict = {}             # cid -> set of alert keys active at the last pass (None before the first one)
_ser_last: dict = {}

_PVE_ACT = {"start": "started", "stop": "stopped", "new": "created", "moved": "moved"}

def _guest_events(cluster, nodes_data):
    cid, cname = cluster["id"], cluster["name"]
    cur = extra.guest_state(nodes_data)
    if any(n.get("status") != "online" for n in nodes_data or []) and cid in _guest_prev:
        # a node that is not online hides its guests: keep what we knew about them so they do not look "new" when it returns
        for v, g in _guest_prev[cid].items():
            if v not in cur and not any(n.get("name") == g["node"] and n.get("status") == "online" for n in nodes_data): cur[v] = g
    ch = extra.guest_changes(_guest_prev.get(cid), cur)
    _guest_prev[cid] = cur
    if not ch: return
    if len(ch) > extra.MAX_CHANGES:
        auth.record_event("pve", "info", f"{cname}: {len(ch)} VM/CT changed state", "pve_guest_many", c=cname, cnt=len(ch))
        return
    for g in ch:
        what = g["what"]
        params = {"c": cname, "n": g["name"], "v": g["vmid"], "nd": g["node"]}
        if what == "moved": params["f"] = g["from"]
        auth.record_event("pve", "info" if what != "stop" else "warn", f"{cname}/{g['name']} ({g['vmid']}): {_PVE_ACT[what]} on {g['node']}", "pve_guest_" + what, **params)

def _live_pass(cluster, nodes_data):
    now = time.time()
    st = _lock_state.setdefault(cluster["id"], {})
    cap = extra.capacity(nodes_data)
    al = extra.lock_alerts(st, nodes_data, now) + extra.capacity_alerts(cap)
    with _xlock: _live[cluster["id"]] = {"alerts": al, "cap": cap, "locks": {v: dict(x) for v, x in st.items()}}
    _guest_events(cluster, nodes_data)
    _emit_alerts(cluster)

def _alert_key(cid, a):
    ident = a.get("name") or a.get("sid") or a.get("id") or a.get("vmid") or a.get("node") or ""
    return f"{cid}:{a['type']}:{ident}"

def all_alerts(cid):
    with _xlock:
        return list((_live.get(cid) or {}).get("alerts", [])) + list((_extra.get(cid) or {}).get("alerts", []))

# Evento al aparecer cada alerta nueva (la primera vez solo se memoriza, para que reiniciar no repita lo ya conocido).
# EN: One event when each new alert appears (the first time it only remembers, so a restart does not repeat what was already known).
def _emit_alerts(cluster):
    cid, cname = cluster["id"], cluster["name"]
    if EXTRA_EVERY > 0 and cid not in _extra: return          # wait for the first extra round so everything is memorized together
    al = {_alert_key(cid, a): a for a in all_alerts(cid)}
    prev = _al_on.get(cid)
    _al_on[cid] = set(al)
    if prev is None: return
    for k, a in al.items():
        if k in prev: continue
        params = {p: v for p, v in a.items() if p not in ("type", "lv") and isinstance(v, (int, float, str)) and not isinstance(v, bool)}
        params["c"] = cname
        auth.record_event("pve", a.get("lv", "warn"), f"{cname}: {a['type']} " + " ".join(f"{p}={v}" for p, v in sorted(params.items()) if p != "c"), "pve_al_" + a["type"], **params)

def _series_store(cid, rows):
    now = int(time.time())
    try:
        c = auth.metrics_conn()
        try:
            c.executemany("INSERT OR REPLACE INTO pve_series (cid,k,ts,v) VALUES (?,?,?,?)", [(cid, k, now, float(u)) for k, (u, _t) in rows.items()])
            c.execute("DELETE FROM pve_series WHERE cid = ? AND ts < ?", (cid, now - SERIES_KEEP)); c.commit()
        finally: c.close()
        _ser_last[cid] = now
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not store the slow series: {e}")

def _series_days(cid, rows):
    out, why, now = {}, {}, int(time.time())
    try:
        c = auth.metrics_conn()
        try:
            for k, (used, tot) in rows.items():
                pts = c.execute("SELECT ts,v FROM pve_series WHERE cid=? AND k=? AND ts>=? ORDER BY ts", (cid, k, now - 14 * 86400)).fetchall()
                pp = [(r[0], r[1]) for r in pts]
                out[k] = extra.days_to_full(pp, tot - used)
                if out[k] is None: why[k] = list(extra.days_why(pp))
        finally: c.close()
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not read the slow series: {e}")
    return out, why

def _extra_round(cluster, client, cache):
    from urllib.parse import quote
    cid, cname = cluster["id"], cluster["name"]
    now = time.time()
    data = cache.snap().get("data") or {}
    nodes = data.get("nodes") or []
    errors = {}
    def tryget(feat, path):
        try:    return client.get(path).get("data")
        except PVEHTTPError as e:
            errors.setdefault(feat, "perm" if e.status in (401, 403) else str(e.status)); return None
        except Exception as e:  # noqa: BLE001 - el error queda guardado y se muestra / the error is kept and shown
            errors.setdefault(feat, str(e)[:80]); return None
    ninfo, repl_rows = {}, {}
    for nd in nodes:
        if nd.get("status") != "online": continue
        q = quote(str(nd["name"]), safe="")
        ninfo[nd["name"]] = extra.node_info(tryget("node", f"/nodes/{q}/status"), tryget("cert", f"/nodes/{q}/certificates/info"), now)
        r = tryget("repl", f"/nodes/{q}/replication")
        if isinstance(r, list) and r: repl_rows[nd["name"]] = r
    ha = extra.ha_summary(tryget("ha", "/cluster/ha/status/current"))
    repl = extra.repl_summary(repl_rows)
    tasks = extra.failed_tasks(tryget("tasks", "/cluster/tasks"), now)
    _task_seen[cid], new = extra.new_task_failures(_task_seen.get(cid), tasks)
    for t in new[:5]:
        auth.record_event("pve", "warn", f"{cname}/{t['node']}: task {t['type']} {t['id']} failed ({t['status'][:60]})", "pve_task_fail", c=cname, n=t["node"], w=t["type"] + (" " + t["id"] if t["id"] else ""), e=t["status"][:60])
    io = extra.ceph_io(data.get("ceph"))
    rows = extra.series_points(nodes, data.get("ceph"))
    if rows and now - _ser_last.get(cid, 0) >= SERIES_EVERY: _series_store(cid, rows)
    days, days_why = _series_days(cid, rows) if rows else ({}, {})
    labels = {k: k.split(":", 1)[-1] for k in rows}
    al = (extra.days_alerts(days, labels) + ha["bad"] + repl["bad"] + extra.ceph_alerts(io) + extra.node_alerts(ninfo))
    res = {"ts": int(now), "nodes": ninfo, "ha": ha, "repl": repl, "tasks": tasks, "ceph": io, "days": days, "days_why": days_why,
           "drift": extra.version_drift(ninfo), "errors": errors, "alerts": al}
    with _xlock: _extra[cid] = res
    _emit_alerts(cluster)

def _extra_loop(cluster, cache):
    cid = cluster["id"]
    client = None
    time.sleep(min(25, EXTRA_EVERY))
    while _cache.get(cid) is cache:
        try:
            cur = next((c for c in load_clusters() if c["id"] == cid), None)
            if cur is None: break
            client = _client_for(cur, client)
            _extra_round(cur, client, cache)
        except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
            log.warning(f"[{cluster['name']}] extra round: {e}")
            if client: client.close()
        time.sleep(EXTRA_EVERY)
    if client: client.close()
    for d in (_extra, _live, _guest_prev, _lock_state, _task_seen, _al_on, _ser_last): d.pop(cid, None)

# ─── Consultas bajo demanda de un nodo (panel de detalle y gráficos) ──────────────
# Un cliente por cluster, reutilizado entre peticiones, y respuestas en caché corta para no cargar a Proxmox si varias personas miran.
# El nodo debe existir en la última lectura del cluster: el nombre nunca llega a la API sin validar.
# EN: On-demand node queries (detail panel and charts). One client per cluster, reused between requests, and short-lived cached answers so
#     Proxmox is not loaded when several people look. The node must exist in the cluster's last reading: the name never reaches the API unchecked.
_nclients: dict = {}
_ncache: dict = {}
_ncl_lock = threading.Lock()
NODE_DETAIL_TTL, NODE_RRD_TTL = 20, 60

def _node_client(cid):
    cur = next((c for c in load_clusters() if c["id"] == cid), None)
    if cur is None: return None
    sig = (cur["host"], cur.get("port", 8006), cur["user"], cur["token_name"], cur["token_value"], cur.get("verify_ssl", False), _fp_norm(cur.get("fingerprint")))
    with _ncl_lock:
        e = _nclients.get(cid)
        if e is None or e[0] != sig:
            if e: e[1].close()
            e = (sig, PVEClient(host=cur["host"], port=cur.get("port", 8006), user=cur["user"], token_name=cur["token_name"],
                                token_value=cur["token_value"], verify_ssl=cur.get("verify_ssl", False), fingerprint=cur.get("fingerprint")))
            _nclients[cid] = e
        return e[1]

def _node_known(cid, name):
    cc = _cache.get(cid)
    return bool(cc) and any(n.get("name") == name for n in (cc.snap().get("data") or {}).get("nodes") or [])

def _ncached(key, ttl, fn):
    now = time.time()
    with _ncl_lock:
        c = _ncache.get(key)
        if c and now - c[0] < ttl: return c[1]
    v = fn()
    with _ncl_lock:
        _ncache[key] = (now, v)
        if len(_ncache) > 300:
            for k in sorted(_ncache, key=lambda x: _ncache[x][0])[:100]: _ncache.pop(k, None)
    return v

def node_rrd(cid, name, rng):
    from urllib.parse import quote
    client = _node_client(cid)
    if client is None: raise PVEHTTPError(404, "no cluster")
    tf = extra.RRD_FRAME[rng]
    def go(): return extra.rrd_points(client.get(f"/nodes/{quote(name, safe='')}/rrddata?timeframe={tf}&cf=AVERAGE").get("data"))
    return _ncached(("rrd", cid, name, rng), NODE_RRD_TTL, go)

# Quita el número de serie de cada disco (SMART) salvo que el usuario tenga el permiso «serials».
# EN: Remove each drive's serial number (SMART) unless the user holds the "serials" permission.
def _smart_view(sm, allowed):
    if allowed or not isinstance(sm, dict): return sm
    return {**sm, "nodes": {n: ({**v, "disks": [{**d, "serial": ""} for d in v.get("disks", [])]} if isinstance(v, dict) else v) for n, v in (sm.get("nodes") or {}).items()}}

def node_detail(cid, name):
    from urllib.parse import quote
    client = _node_client(cid)
    if client is None: raise PVEHTTPError(404, "no cluster")
    q, errors = quote(name, safe=""), {}
    def tryget(feat, sub):
        try: return client.get(f"/nodes/{q}/{sub}").get("data")
        except PVEHTTPError as e:
            errors[feat] = "perm" if e.status in (401, 403) else str(e.status); return None
        except Exception as e:  # noqa: BLE001 - el error queda guardado y se muestra / the error is kept and shown
            errors[feat] = str(e)[:80]; return None
    def go():
        errors.clear()
        st = tryget("status", "status")
        if st is None and "status" in errors: raise PVEHTTPError(502, errors["status"])
        d = extra.node_detail(st, tryget("version", "version"), tryget("time", "time"), tryget("dns", "dns"), tryget("network", "network"),
                              tryget("subscription", "subscription"), tryget("apt", "apt/update"), tryget("services", "services"), tryget("disks", "disks/list"))
        d["errors"] = dict(errors)
        return d
    return _ncached(("detail", cid, name), NODE_DETAIL_TTL, go)

# ─── Red de las VM y contenedores (para Net Monitor) ─────────────────────────
# Por cada VM/CT se leen sus MAC (de la configuración) y sus IP: las fijas del contenedor, las que informa el agente de
# invitado (VM) o la interfaz del contenedor. Si falta algún permiso o el agente no corre, queda solo lo que se pudo leer.
# EN: Network of VMs and containers (for Net Monitor). For each VM/CT its MACs (from the configuration) and its IPs are
#     read: the container's static ones, those the guest agent reports (VM) or the container's interface. If a permission
#     is missing or the agent is not running, only what could be read is kept.
_gnets: dict = {}                                    # cluster id -> list of guests with macs / ips
_MAC_RE = re.compile(r"(?i)\b([0-9a-f]{2}(?::[0-9a-f]{2}){5})\b")
_IP4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

def _guest_ips(client, node, kind, vmid, cfg, running):
    ips = []
    if kind == "lxc":
        for k, v in cfg.items():                     # net0: name=eth0,hwaddr=..,ip=192.0.2.5/24
            if re.fullmatch(r"net\d+", k):
                m = re.search(r"(?:^|,)ip=(\d{1,3}(?:\.\d{1,3}){3})(?:/\d+)?", str(v))
                if m: ips.append(m.group(1))
    if running:
        try:
            if kind == "qemu" and re.match(r"(enabled=)?1\b", str(cfg.get("agent", "0"))):
                for itf in client.get(f"/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces").get("data", {}).get("result", []):
                    for a in itf.get("ip-addresses", []):
                        if a.get("ip-address-type") == "ipv4": ips.append(a.get("ip-address", ""))
            elif kind == "lxc":
                for itf in client.get(f"/nodes/{node}/lxc/{vmid}/interfaces").get("data", []):
                    ips.append(str(itf.get("inet", "")).split("/")[0])
        except Exception:  # noqa: BLE001, S110 - sin agente o sin permiso: se usa la configuración / EN: no agent or no permission: the config is used
            pass                                      # no agent / no permission: keep what the config gave
    return sorted({i for i in ips if _IP4_RE.match(i) and not i.startswith(("127.", "169.254."))})

def _guest_round(cur, client, cache):
    out = []
    for nd in (cache.snap().get("data") or {}).get("nodes", []):
        if nd.get("status") != "online": continue
        for kind, items in (("qemu", nd.get("vms") or []), ("lxc", nd.get("cts") or [])):
            for g in items:
                if g.get("template"): continue
                vmid = g.get("vmid")
                try:
                    cfg = client.get(f"/nodes/{nd['name']}/{kind}/{vmid}/config").get("data", {})
                except Exception:  # noqa: BLE001 - red o servicio externo: cualquier fallo es «sin respuesta» / network or external service: any failure means «no answer»
                    cfg = {}
                macs = sorted({m.lower() for k, v in cfg.items() if re.fullmatch(r"net\d+", k) for m in _MAC_RE.findall(str(v))})
                ips = _guest_ips(client, nd["name"], kind, vmid, cfg, g.get("status") == "running")
                out.append({"cid": cur["id"], "cluster": cur["name"], "node": nd["name"], "vmid": vmid, "type": kind,
                            "name": g.get("name", ""), "status": g.get("status", ""), "macs": macs, "ips": ips})
    _gnets[cur["id"]] = out

def _guest_loop(cluster, cache):
    cid = cluster["id"]
    client = None
    time.sleep(min(15, GUEST_EVERY))
    while _cache.get(cid) is cache:
        try:
            cur = next((c for c in load_clusters() if c["id"] == cid), None)
            if cur is None: break
            client = _client_for(cur, client)
            _guest_round(cur, client, cache)
        except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
            log.warning(f"[{cluster['name']}] guest network round: {e}")
            if client: client.close()
        time.sleep(GUEST_EVERY)
    if client: client.close()
    _gnets.pop(cid, None)

# Orden «natural» (pve2 antes que pve10) para que el orden de los nodos no cambie entre consultas.
# EN: "Natural" order (pve2 before pve10) so the node order does not change between queries.
def _natural(s: str):
    """Natural sort key (pve2 < pve10) so the default node order never changes between polls."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s or "")]

# Plan B cuando /cluster/resources no está disponible (nodo suelto o token con pocos permisos): una consulta por nodo.
# EN: Plan B when /cluster/resources is unavailable (standalone node or token with few permissions): one query per node.
def _fetch_legacy(client, name):
    """Fallback when /cluster/resources is unavailable (standalone node, limited token): per-node calls."""
    nodes_data = []
    for node in client.nodes():
        n = node["node"]
        info = {k: node.get(k, 0) for k in ("uptime", "cpu", "maxcpu", "mem", "maxmem", "disk", "maxdisk")}
        info.update(name=n, status=node.get("status"), vms=[], cts=[], storage=[])
        if node.get("status") == "online":
            try:
                info["vms"], info["cts"], info["storage"] = client.vms(n), client.containers(n), client.storage(n)
            except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
                log.warning(f"[{name}] {n} detail error: {e}")
        nodes_data.append(info)
    return sorted(nodes_data, key=lambda x: _natural(x["name"]))

# Convierte la respuesta de /cluster/resources al formato que usa la página: agrupa VMs, contenedores y almacenamientos por nodo.
# EN: Convert the /cluster/resources response to the format the page uses: groups VMs, containers and storage by node.
def _build_from_resources(res: list) -> list:
    """Group /cluster/resources by node, mapped to the shape the UI already uses."""
    nodes, order = {}, []
    for r in res:
        t = r.get("type")
        if t == "node":
            n = r.get("node")
            nodes[n] = {"name": n, "status": r.get("status"), "uptime": r.get("uptime", 0),
                        "cpu": r.get("cpu", 0), "maxcpu": r.get("maxcpu", 0),
                        "mem": r.get("mem", 0), "maxmem": r.get("maxmem", 0),
                        "disk": r.get("disk", 0), "maxdisk": r.get("maxdisk", 0),
                        "vms": [], "cts": [], "storage": []}
            order.append(n)
    for r in res:
        t, n = r.get("type"), r.get("node")
        if n not in nodes: continue
        if t in ("qemu", "lxc"):
            item = {"vmid": r.get("vmid"), "name": r.get("name", ""), "status": r.get("status", ""),
                    "cpu": r.get("cpu", 0), "cpus": r.get("maxcpu", 0), "mem": r.get("mem", 0),
                    "maxmem": r.get("maxmem", 0), "disk": r.get("disk", 0), "maxdisk": r.get("maxdisk", 0),
                    "uptime": r.get("uptime", 0), "netin": r.get("netin", 0), "netout": r.get("netout", 0),
                    "tags": r.get("tags", ""), "lock": r.get("lock", ""), "template": r.get("template", 0)}
            nodes[n]["vms" if t == "qemu" else "cts"].append(item)
        elif t == "storage":
            tot, used = r.get("maxdisk", 0), r.get("disk", 0)
            nodes[n]["storage"].append({"storage": r.get("storage"), "type": r.get("plugintype", ""),
                                        "content": r.get("content", ""), "shared": r.get("shared", 0),
                                        "active": 1 if r.get("status") == "available" else 0,
                                        "total": tot, "used": used, "avail": max(tot - used, 0),
                                        "used_fraction": (used / tot) if tot else 0})
    for nd in nodes.values():
        if nd["status"] != "online":                # same as the per-node path: nothing listed for offline nodes
            nd["vms"], nd["cts"], nd["storage"] = [], [], []
    return [nodes[n] for n in sorted(order, key=_natural)]

# Anota en la línea de tiempo del Resumen: nodo caído o recuperado, cluster otra vez alcanzable y cambios de salud de Ceph.
# EN: Record on the Overview timeline: node down or recovered, cluster reachable again and Ceph health changes.
def _cluster_events(cluster, nodes_data, ceph):
    cid, cname = cluster["id"], cluster["name"]
    if auth.state_changed(f"pve-cl:{cid}", "up"):
        auth.record_event("pve", "info", f"{cname}: cluster reachable again", "pve_cl_up", c=cname)
    for nd in nodes_data or []:
        ch = auth.state_changed(f"pve-node:{cid}:{nd.get('name')}", nd.get("status") or "unknown")
        if not ch: continue
        if ch[1] == "online": auth.record_event("pve", "info", f"{cname}/{nd.get('name')}: node online", "pve_node_on", c=cname, n=nd.get("name"))
        else:                 auth.record_event("pve", "crit", f"{cname}/{nd.get('name')}: node {ch[1]}", "pve_node_off", c=cname, n=nd.get("name"), st=ch[1])
    try:
        h = (ceph or {}).get("health", {}).get("status")
        if h:
            ch = auth.state_changed(f"pve-ceph:{cid}", h)
            if ch:
                auth.record_event("pve", "info" if h == "HEALTH_OK" else "crit" if h == "HEALTH_ERR" else "warn",
                                  f"{cname}: Ceph {ch[0]} → {h}", "pve_ceph", c=cname, a=ch[0], b=h)
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"{cname}: Ceph health event not recorded: {e}")

# Bucle del hilo de consulta de un cluster. En cada vuelta: vuelve a leer la configuración (si el cluster se borró, el
# hilo termina; si se fijó una huella, la adopta), consulta la API, guarda la lectura y duerme según haya o no alguien mirando.
# Un error se anota y se reintenta: el hilo nunca muere por un fallo de red.
# EN: Loop of a cluster's polling thread. On each pass: re-read the configuration (if the cluster was deleted the
#     thread ends; if a fingerprint was pinned, it adopts it), query the API, store the reading and sleep depending on whether someone is looking.
#     An error is logged and retried: the thread never dies because of a network failure.
def _poll_cluster(cluster):
    cid = cluster["id"]
    cache = _cache.get(cid)
    if not cache: return

    client = PVEClient(
        host=cluster["host"], port=cluster.get("port", 8006),
        user=cluster["user"], token_name=cluster["token_name"],
        token_value=cluster["token_value"],
        verify_ssl=cluster.get("verify_ssl", False),
        fingerprint=cluster.get("fingerprint")
    )
    version, ceph, slow_ts = "", None, 0.0
    corosync, cephsum = None, None
    use_resources = True
    if SMART_EVERY > 0 and not (_smart_threads.get(cid) and _smart_threads[cid].is_alive()):
        _smart_threads[cid] = threading.Thread(target=_smart_loop, args=(cluster, cache), daemon=True); _smart_threads[cid].start()
    if BACKUP_EVERY > 0 and not (_backup_threads.get(cid) and _backup_threads[cid].is_alive()):
        _backup_threads[cid] = threading.Thread(target=_backup_loop, args=(cluster, cache), daemon=True); _backup_threads[cid].start()
    if EXTRA_EVERY > 0 and not (_extra_threads.get(cid) and _extra_threads[cid].is_alive()):
        _extra_threads[cid] = threading.Thread(target=_extra_loop, args=(cluster, cache), daemon=True); _extra_threads[cid].start()
    if GUEST_EVERY > 0 and not (_guest_threads.get(cid) and _guest_threads[cid].is_alive()):
        _guest_threads[cid] = threading.Thread(target=_guest_loop, args=(cluster, cache), daemon=True); _guest_threads[cid].start()

    while True:
        try:
            cur = next((c for c in load_clusters() if c["id"] == cid), None)
            gone = cur is None
            if cur is not None:                  # picks up a pinned certificate or an edit while running
                client = _client_for(cur, client); cluster = cur
        except Exception as e:                    # never let the poller thread die on a config hiccup  # noqa: BLE001
            log.error(f"[{cluster['name']}] config read: {e}"); gone = False
        if gone:
            client.close()
            return
        t0 = time.time()
        try:
            nodes_data = None
            if use_resources:
                try:
                    nodes_data = _build_from_resources(client.resources())
                    if not nodes_data: raise RuntimeError("empty /cluster/resources")
                except PVEHTTPError as e:
                    if e.status not in (403, 404, 501): raise      # transient server error: keep using /cluster/resources
                    log.warning(f"[{cluster['name']}] /cluster/resources unavailable ({e}); using per-node calls")
                    use_resources = False
            if nodes_data is None:
                nodes_data = _fetch_legacy(client, cluster["name"])

            # version and ceph change rarely: refresh them once a minute
            if t0 - slow_ts >= SLOW_EVERY:
                v = client.version()
                if v: version = v
                try:    ceph = client.get("/cluster/ceph/status").get("data")
                except Exception: ceph = None  # noqa: BLE001 - red o servicio externo: cualquier fallo es «sin respuesta» / network or external service: any failure means «no answer»
                cephsum = diag.ceph_summary(ceph)
                corosync = diag.corosync_summary(client.cluster_status())
                slow_ts = t0

            for nd in nodes_data:
                if nd.get("status") == "online":
                    push_node_history(cid, nd["name"], nd.get("cpu", 0), nd.get("mem", 0), nd.get("maxmem", 0))

            cache.update({"nodes": nodes_data, "version": version,
                          "name": cluster["name"], "ceph": ceph, "ceph_sum": cephsum, "corosync": corosync})
            _cluster_events(cluster, nodes_data, ceph)
            _observe_reboots(cluster, nodes_data)
            _diag_events(cluster, corosync, cephsum)
            try:    _live_pass(cluster, nodes_data)
            except Exception as e: log.warning(f"[{cluster['name']}] extra pass: {e}")  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
            log.debug(f"[{cluster['name']}] {len(nodes_data)} nodes in {time.time()-t0:.2f}s")

        except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
            cache.set_error(str(e), "cert" if isinstance(e, PVECertError) else None)
            client.close()
            log.error(f"[{cluster['name']}] poll error: {e}")
            if auth.state_changed(f"pve-cl:{cid}", "down"):
                auth.record_event("pve", "crit", f"{cluster['name']}: cluster unreachable", "pve_cl_down", c=cluster["name"])

        # fast while a browser is watching, slow otherwise; a new viewer wakes the poller at once
        active = (time.time() - _last_view) < VIEW_GRACE
        cache.wake.wait(POLL_ACTIVE if active else POLL_IDLE)
        cache.wake.clear()

# Garantiza que haya un hilo de consulta vivo para el cluster.
# EN: Guarantee a live polling thread for the cluster.
def ensure_poller(cluster):
    cid = cluster["id"]
    with _glock:
        if cid not in _cache:
            _cache[cid] = ClusterCache(cid)
        if cid not in _pollers or not _pollers[cid].is_alive():
            t = threading.Thread(target=_poll_cluster, args=(cluster,), daemon=True)
            _pollers[cid] = t; t.start()
            log.info(f"Poller → {cluster['name']} ({cluster['host']})")

# Olvida un cluster eliminado; su hilo termina solo.
# EN: Forget a deleted cluster; its thread ends by itself.
def remove_poller(cid):
    with _glock:
        _cache.pop(cid, None)
        _pollers.pop(cid, None)

# Al arrancar: un hilo de consulta por cada cluster configurado.
# EN: On startup: one polling thread for each configured cluster.
def start_all():
    for c in load_clusters():
        ensure_poller(c)

# ─── Health ───────────────────────────────────────────────────────────────────
# Chequeos de salud de Proxmox: archivo de clusters, hilos vivos y que cada cluster responda con datos recientes.
# EN: Proxmox health checks: clusters file, live threads and that each cluster answers with recent data.
def health_report(detailed=False):
    c = auth.check_common()
    c["clusters_file"] = auth.check_file(DATA_FILE)
    now = time.time(); cls = load_clusters(); dead = []; bad = []
    for cl in cls:
        t = _pollers.get(cl["id"])
        if t is None or not t.is_alive(): dead.append(cl["name"]); continue
        cc = _cache.get(cl["id"])
        if cc is None: continue
        sn = cc.snap()
        if sn["error"]:
            bad.append(f'{cl["name"]}: {sn["error"]}')
        elif sn["ts"] and now - sn["ts"] > max(3 * POLL_IDLE, 180):
            bad.append(f'{cl["name"]}: data {int(now - sn["ts"])} s old')
    if not cls:   c["pollers"] = auth.chk(auth.OK, "no clusters configured")
    elif dead:    c["pollers"] = auth.chk(auth.FAIL, "poller stopped: " + ", ".join(dead))
    else:         c["pollers"] = auth.chk(auth.OK, f"{len(cls)} running")
    c["clusters"] = auth.chk(auth.WARN, "; ".join(bad)) if bad else auth.chk(auth.OK, "all clusters answering")
    return auth.health_reply("pve", c, detailed)

# ─── HTTP Handler ─────────────────────────────────────────────────────────────
# Manejador HTTP. Cada petición se atiende en su propio hilo.
# EN: HTTP handler. Each request is served in its own thread.
class H(BaseHTTPRequestHandler):
    timeout = 30      # a stalled client must not hold a thread forever
    def log_message(self, fmt, *a):
        # send_error() llega aquí con (código, mensaje) y un 501 de HEAD trae el mensaje en a[1]: solo se registra un código numérico.
        # EN: send_error() arrives here with (code, message) and a HEAD 501 carries the message in a[1]: only a numeric code is logged.
        c = str(a[1]) if len(a) > 1 else ""
        if c.isdigit() and int(c) >= 400: log.warning(f"{self.client_address[0]} {c}")

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
            d = json.loads(self.rfile.read(n)) if n else {}
            return d if isinstance(d, dict) else None      # EN: a list/number would crash the handlers (500); reject it (400)
        except (ValueError, TypeError, OSError, RecursionError): return None

    def _tok(self):
        return auth.token_from_request(dict(self.headers), self.headers.get("Cookie", ""))

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

    # GET: página, versión y salud son públicos; el resto exige sesión con Proxmox «readonly».
    # Rutas: /api/clusters, /api/debug, /api/me.
    # EN: GET: page, version and health are public; the rest requires a session with Proxmox "readonly".
    #     Routes: /api/clusters, /api/debug, /api/me.
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        tok  = self._tok()
        if auth.serve_asset(self, STATIC_DIR, path): return   # .js / .css de la página

        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")

        if path == "/api/version":     # shown in the page footer; only with a session (or from this machine)
            return self._json(200, {"version": auth.version()} if (auth.get_session(tok) or auth.is_local_request(self)) else {})
        if path == "/api/health":      # public: levels only; details need a valid session
            code, body = health_report(auth.health_mode(self, tok))
            return self._json(code, body)

        if not auth.check_permission(tok, "pve", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        # Lista de clusters con su última lectura, historial por nodo y alertas (CPU > 80 % o RAM > 90 %).
        # Nunca se envía el token de API al navegador. Pedir esta ruta marca «alguien mira» y despierta a los pollers.
        # EN: Cluster list with their last reading, per-node history and alerts (CPU > 80 % or RAM > 90 %).
        #     The API token is never sent to the browser. Requesting this route marks "someone is looking" and wakes the pollers.
        m = re.fullmatch(r"/api/clusters/([a-zA-Z0-9\-]+)/nodes/([\w.\-]{1,64})/(rrd|detail)", path)
        if m:
            cid, name, what = m.groups()
            if not _node_known(cid, name): return self._json(404, {"error": "Unknown node"})
            try:
                if what == "detail":
                    det = node_detail(cid, name)
                    if not auth.can_see_serials(tok): det = {**det, "serial": ""}         # the machine serial needs the "serials" permission
                    return self._json(200, {"node": name, "detail": det})
                rng = parse_qs(urlparse(self.path).query).get("range", ["1d"])[0]
                if rng not in extra.RRD_FRAME: return self._json(400, {"error": "Invalid range"})
                return self._json(200, {"range": rng, "history": node_rrd(cid, name, rng)})
            except Exception as e:  # noqa: BLE001 - error de la petición: se responde sin caer / request error: answered without crashing
                log.warning(f"[{cid}] node {what} query failed: {e}")
                return self._json(502, {"error": "Could not read the node from Proxmox"})

        if path == "/api/clusters":
            global _last_view
            was_idle = (time.time() - _last_view) >= VIEW_GRACE
            _last_view = time.time()
            if was_idle:
                for cc in list(_cache.values()):
                    cc.wake.set()               # data may be up to a minute old: refresh now
            with_hist = parse_qs(urlparse(self.path).query).get("hist", ["1"])[0] != "0"
            clusters = load_clusters()
            out = []
            for c in clusters:
                if c["id"] not in _pollers or not _pollers[c["id"]].is_alive():
                    ensure_poller(c)                 # revive a poller thread that died
                snap = _cache.get(c["id"], ClusterCache(c["id"])).snap()
                # Inyectar historial por nodo
                nodes_with_hist = []
                for nd in snap.get("data", {}).get("nodes", []):
                    nd = dict(nd)
                    if with_hist:
                        nd["history"] = get_node_history(c["id"], nd["name"])
                    nodes_with_hist.append(nd)
                if "data" in snap:
                    snap = dict(snap)
                    snap["data"] = dict(snap["data"])
                    snap["data"]["nodes"] = nodes_with_hist
                # Agregar alertas de resource
                alerts = []
                for nd in nodes_with_hist:
                    if nd.get("status") == "online":
                        cpu_pct = nd.get("cpu", 0) * 100
                        maxmem  = nd.get("maxmem", 0)
                        mem_pct = (nd.get("mem", 0) / maxmem * 100) if maxmem > 0 else 0
                        if cpu_pct > 80:
                            alerts.append({"node": nd["name"], "type": "cpu", "value": round(cpu_pct, 1)})
                        if mem_pct > 90:
                            alerts.append({"node": nd["name"], "type": "mem", "value": round(mem_pct, 1)})
                alerts += all_alerts(c["id"])
                pub = {k: v for k, v in c.items() if k != "token_value"}     # never send the API token to the browser
                pub["pinned"] = bool(_fp_norm(c.get("fingerprint")))
                pub.setdefault("layout", {"order": [], "pinned": []})
                out.append({**pub, "snap": snap, "alerts": alerts})
            self._json(200, {"clusters": out})

        # Diagnóstico de un cluster: reinicios (con «oleadas») y SMART de los discos. Parámetro: ?id=<cluster>.
        # EN: Diagnostics of a cluster: reboots (with "waves") and disk SMART. Parameter: ?id=<cluster>.
        elif path == "/api/diag":
            cid = parse_qs(urlparse(self.path).query).get("id", [""])[0]
            if not any(c["id"] == cid for c in load_clusters()): return self._json(404, {"error": "Not found"})
            with _diag_lock:
                rb = diag.with_waves([r for r in _diag_load()["reboots"] if r.get("cid") == cid])
            with _xlock:
                ex = dict(_extra.get(cid) or {}) or None
                lv = _live.get(cid) or {}
            if ex: ex["cap"] = lv.get("cap"); ex["locks"] = lv.get("locks", {})
            self._json(200, {"reboots": rb[:100], "smart": _smart_view(_smart.get(cid), auth.can_see_serials(tok)), "smart_every": SMART_EVERY, "backups": _backups.get(cid), "extra": ex})

        # VM y contenedores con sus MAC e IP, para que Net Monitor los asocie a los equipos de la red.
        # EN: VMs and containers with their MACs and IPs, so Net Monitor can match them to the devices on the network.
        elif path == "/api/guests":
            gs = [g for c in load_clusters() for g in _gnets.get(c["id"], [])]
            self._json(200, {"guests": gs, "with_mac": sum(1 for g in gs if g["macs"]), "with_ip": sum(1 for g in gs if g["ips"])})

        # Resumen técnico del estado de cada cluster, útil para diagnosticar.
        # EN: Technical summary of each cluster's state, useful for diagnosis.
        elif path == "/api/debug":
            out = []
            for cid, cc in _cache.items():
                snap = cc.snap()
                nodes = snap.get("data", {}).get("nodes", [])
                out.append({
                    "id": cid, "error": snap.get("error"),
                    "ts": snap.get("ts"),
                    "nodes": [{
                        "name": n["name"],
                        "status": n["status"],
                        "cpu": n.get("cpu"), "maxcpu": n.get("maxcpu"),
                        "mem": n.get("mem"), "maxmem": n.get("maxmem"),
                        "vms": len(n.get("vms") or []),
                        "cts": len(n.get("cts") or []),
                    } for n in nodes]
                })
            self._json(200, out)

        elif path == "/api/me":
            sess = auth.get_session(tok)
            if sess:
                self._json(200, {"username": sess["username"],
                                  "permissions": sess["permissions"],
                      "disabled": auth.disabled_modules()})
            else:
                self._json(200, {})
        else:
            self._json(404, {"error": "Not found"})

    # POST: login/logout, orden de nodos, alta de cluster, huella del certificado, fijar certificado y prueba de conexión.
    # Las acciones de administración exigen nivel «admin» de Proxmox.
    # EN: POST: login/logout, node order, add cluster, certificate fingerprint, pin certificate and connection test.
    #     Administration actions require Proxmox "admin" level.
    def do_POST(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})

        # Login con límite de intentos (auth.login); la cookie es HttpOnly y SameSite=Strict.
        # EN: Login with attempt limiting (auth.login); the cookie is HttpOnly and SameSite=Strict.
        if path == "/api/login":
            r, err = auth.login_session(self, body.get("username", ""), body.get("password", ""), body.get("remember"), body.get("code"))   # the service checks the password and opens the session
            if not r: return self._json(err[0], {"error": err[1]})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie",
                auth.session_cookie(r["token"], r["ttl"]))
            br = json.dumps({"ok": True, "username": r["username"],
                             "permissions": r["permissions"],
                             "must_change_password": r["must_change_password"]}).encode()
            self.send_header("Content-Length", str(len(br)))
            self.end_headers(); self.wfile.write(br); return

        if path == "/api/logout":
            auth.delete_session(tok); return self._json(200, {"ok": True})

        # Orden manual de los nodos y cuáles están fijados; se guarda con el cluster, así lo ven todos los navegadores.
        # EN: Manual node order and which ones are pinned; stored with the cluster, so every browser sees it.
        m = re.match(r"^/api/clusters/([a-zA-Z0-9\-]+)/layout$", path)
        if m:
            # Manual node order and pins, stored with the cluster (shared by every browser, survives restarts/upgrades)
            if not auth.check_permission(tok, "pve", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            name_ok = lambda x: isinstance(x, str) and re.fullmatch(r"[\w.\-]{1,64}", x)
            order, pinned = body.get("order", []), body.get("pinned", [])
            if not (isinstance(order, list) and isinstance(pinned, list) and len(order) <= 200 and len(pinned) <= 200
                    and all(name_ok(x) for x in order) and all(name_ok(x) for x in pinned)):
                return self._json(400, {"error": "Invalid layout"})
            with _cl_lock:
                clusters = load_clusters()
                for c in clusters:
                    if c["id"] == m.group(1):
                        c["layout"] = {"order": list(dict.fromkeys(order)), "pinned": list(dict.fromkeys(pinned))}
                        save_clusters(clusters)
                        return self._json(200, {"ok": True})
            return self._json(404, {"error": "Not found"})

        # Ajustes de respaldos de un cluster: antigüedad máxima (horas) y VMs/CTs que se ignoran.
        # EN: A cluster's backup settings: maximum age (hours) and the VMs/CTs that are ignored.
        m = re.match(r"^/api/clusters/([a-zA-Z0-9\-]+)/backup$", path)
        if m:
            if not auth.check_permission(tok, "pve", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            try:    cfg = backups.clean_config(body)
            except ValueError as e: return self._json(400, {"error": str(e)})
            with _cl_lock:
                clusters = load_clusters()
                for c in clusters:
                    if c["id"] == m.group(1):
                        c["backup"] = cfg
                        save_clusters(clusters)
                        backups.apply_config(_backups.get(c["id"]), cfg)        # the page asks again right away: do not answer with the old settings
                        return self._json(200, {"ok": True, **cfg})
            return self._json(404, {"error": "Not found"})

        if not auth.check_permission(tok, "pve", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        # Alta de cluster: valida los campos y EXIGE la huella del certificado confirmada por el usuario (flujo «Probar» dos
        # veces en la página). Rechaza host:puerto duplicado y nunca devuelve el token.
        # EN: Add a cluster: validates the fields and REQUIRES the certificate fingerprint confirmed by the user (the "Test" two-step
        #     flow on the page). Rejects a duplicate host:port and never returns the token.
        if path == "/api/clusters":
            if not auth.check_permission(tok, "pve", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            try: f = cluster_fields(body)
            except ValueError as e: return self._json(400, {"error": str(e)})
            fp = _fp_norm(body.get("fingerprint"))
            if not fp:
                return self._json(400, {"error": "Certificate fingerprint required: run Test and confirm it"})
            import uuid
            host, port = f["host"], f["port"]
            cluster = {"id": str(uuid.uuid4()), **f, "verify_ssl": False, "fingerprint": fp}
            with _cl_lock:
                clusters = load_clusters()
                if any(c["host"]==host and c.get("port")==port for c in clusters):
                    return self._json(409, {"error": "That host:port already exists"})
                clusters.append(cluster)
                save_clusters(clusters)
            ensure_poller(cluster)
            # never echo the API token back
            self._json(201, {"cluster": {k: v for k, v in cluster.items() if k != "token_value"}})

        # Edición de un cluster: nombre, host, puerto, usuario y token (un secreto vacío conserva el guardado). Si cambia host o
        # puerto se exige la huella confirmada otra vez («Probar»); si no, se conserva la fijada (o se adopta la confirmada).
        # El poller y los demás hilos toman los datos nuevos en su próxima vuelta. Nunca devuelve el token.
        # EN: Edit a cluster: name, host, port, user and token (an empty secret keeps the stored one). If host or port change the
        #     confirmed fingerprint is required again ("Test"); otherwise the pinned one is kept (or the confirmed one adopted).
        #     The poller and the other threads pick up the new data on their next pass. Never returns the token.
        elif re.match(r'^/api/clusters/[a-zA-Z0-9\-]+$', path):
            if not auth.check_permission(tok, "pve", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            cid = path.split("/")[3]
            with _cl_lock:
                clusters = load_clusters()
                c = next((x for x in clusters if x["id"] == cid), None)
                if not c: return self._json(404, {"error": "Not found"})
                try: f = cluster_fields(body, c)
                except ValueError as e: return self._json(400, {"error": str(e)})
                fp = _fp_norm(body.get("fingerprint"))
                moved = (f["host"], f["port"]) != (c["host"], c.get("port", 8006))
                if moved and not fp:
                    return self._json(400, {"error": "Certificate fingerprint required: run Test and confirm it"})
                if any(x["id"] != cid and x["host"] == f["host"] and x.get("port") == f["port"] for x in clusters):
                    return self._json(409, {"error": "That host:port already exists"})
                c.update(f)
                if fp: c["fingerprint"] = fp
                save_clusters(clusters)
            cc = _cache.get(cid)
            if cc: cc.wake.set()
            self._json(200, {"cluster": {k: v for k, v in c.items() if k != "token_value"}})

        # Paso 1 del alta: devuelve la huella del certificado que presenta el servidor (no se envía ningún token).
        # EN: Step 1 of adding: returns the fingerprint of the certificate the server presents (no token is sent).
        elif path == "/api/fingerprint":
            if not auth.check_permission(tok, "pve", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            host = str(body.get("host","")).strip()
            try: port = int(body.get("port", 8006))
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
            if not auth.valid_target(host) or not 1 <= port <= 65535: return self._json(400, {"error": "Invalid host or port"})
            try:
                self._json(200, {"ok": True, "fingerprint": _fp_fmt(fetch_fingerprint(host, port))})
            except Exception as e:  # noqa: BLE001 - error de la petición: se responde sin caer / request error: answered without crashing
                self._json(200, {"ok": False, "error": str(e)})

        # Fijar el certificado de un cluster ya existente en dos pasos: sin huella devuelve la actual para que el usuario la
        # vea; con huella la guarda solo si coincide con la que el servidor presenta en ese momento.
        # EN: Pin the certificate of an already existing cluster in two steps: without a fingerprint it returns the current one so the user
        #     can see it; with a fingerprint it saves it only if it matches what the server presents at that moment.
        elif re.match(r'^/api/clusters/[a-zA-Z0-9\-]+/pin$', path):
            if not auth.check_permission(tok, "pve", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            cid = path.split("/")[3]
            with _cl_lock:
                clusters = load_clusters()
                c = next((x for x in clusters if x["id"] == cid), None)
            if not c: return self._json(404, {"error": "Not found"})
            try:
                cur = fetch_fingerprint(c["host"], c.get("port", 8006))
            except Exception as e:  # noqa: BLE001 - error de la petición: se responde sin caer / request error: answered without crashing
                return self._json(200, {"ok": False, "error": str(e)})
            want = _fp_norm(body.get("fingerprint"))
            if not want:                                  # step 1: show what the server presents now
                return self._json(200, {"ok": True, "fingerprint": _fp_fmt(cur)})
            if want != cur:
                return self._json(409, {"error": "The certificate changed since you looked at it"})
            with _cl_lock:
                clusters = load_clusters()
                for x in clusters:
                    if x["id"] == cid: x["fingerprint"] = cur
                save_clusters(clusters)
            self._json(200, {"ok": True, "pinned": True})

        # Prueba de conexión (con la huella fijada) sin guardar el cluster: devuelve la versión y la cantidad de nodos.
        # EN: Connection test (with the pinned fingerprint) without saving the cluster: returns the version and the number of nodes.
        elif path == "/api/test":
            if not auth.check_permission(tok, "pve", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            host  = str(body.get("host","")).strip()
            try: port = int(body.get("port", 8006))
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
            if not auth.valid_target(host) or not 1 <= port <= 65535: return self._json(400, {"error": "Invalid host or port"})
            user  = str(body.get("user","")).strip()
            tname = str(body.get("token_name","")).strip()
            tval  = str(body.get("token_value","")).strip()
            if not tval and body.get("id"):           # editing: an empty secret means the stored one / editando: secreto vacío = el guardado
                tval = next((x["token_value"] for x in load_clusters() if x["id"] == body.get("id")), "")
            try:
                fp = _fp_norm(body.get("fingerprint"))
                if not fp: return self._json(400, {"error": "Certificate fingerprint required"})
                client = PVEClient(host, port, user, tname, tval, fingerprint=fp)
                ver    = client.version()
                nodes  = client.nodes()
                self._json(200, {"ok": True, "version": ver,
                                 "nodes": len(nodes)})
            except Exception as e:  # noqa: BLE001 - error de la petición: se responde sin caer / request error: answered without crashing
                self._json(200, {"ok": False, "error": str(e)})

        else:
            self._json(404, {"error": "Not found"})

    # DELETE /api/clusters/<id>: elimina un cluster y detiene su consulta (solo admin).
    # EN: DELETE /api/clusters/<id>: remove a cluster and stop its polling (admin only).
    def do_DELETE(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path
        tok  = self._tok()
        if not auth.check_permission(tok, "pve", "admin"):
            return self._json(403, {"error": "Admin permission required"})
        m = re.match(r'^/api/clusters/([a-zA-Z0-9\-]+)$', path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        with _cl_lock:
            clusters = load_clusters()
            new = [c for c in clusters if c["id"] != m.group(1)]
            if len(new) == len(clusters): return self._json(404, {"error": "Not found"})
            save_clusters(new)
        remove_poller(m.group(1))
        self._json(200, {"ok": True})

# Arranque: completa el permiso «pve» de usuarios antiguos (una vez), lanza los hilos de consulta y sirve en loopback.
# EN: Startup: fills in the "pve" permission of old users (once), starts the polling threads and serves on loopback.
if __name__ == "__main__":
    auth.prepare_module(DATA_DIR, Path(__file__).parent, LEGACY_FILES)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    # Explicit 'pve' level for users that predate the module (one-time migration)
    try:
        if auth.ensure_permissions(("pve",)): log.info("'pve' permissions updated")
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"Permissions: {e}")

    log.info(f"Proxmox Monitor en http://{HOST}:{PORT} — poll {POLL_ACTIVE:g}s active / {POLL_IDLE:g}s idle")
    # Aviso en el log por cada cluster sin huella fijada: se conecta sin validar el certificado del servidor.
    # EN: Log warning for every cluster without a pinned fingerprint: it connects without validating the server certificate.
    try:
        for _c in load_clusters():
            if not _fp_norm(_c.get("fingerprint")):
                log.warning(f"Cluster '{_c.get('name', _c.get('id'))}' has no pinned certificate: the server identity is NOT verified. Pin it from the Proxmox page.")
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"Could not check pinned certificates: {e}")
    n = load_history()
    if n: log.info(f"History restored: {n} samples")
    start_all()
    threading.Thread(target=_history_pruner, daemon=True, name="history-pruner").start()
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
