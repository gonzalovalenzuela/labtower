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
#   página y lento (60 s) cuando nadie la tiene abierta, para no gastar CPU en la Pi.
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
#       page and slowly (60 s) when nobody has it open, so the Pi does not waste CPU.
#
#     Certificate security: Proxmox uses its own certificate by default, so it cannot be validated against a
#     public authority. Instead the SHA-256 fingerprint of the certificate is "pinned" when the cluster is added
#     (the user confirms it) and every connection checks it is still the same BEFORE sending the token.
#
#     Structure: API client · cluster configuration · cache and history · poller · health · HTTP.
import json, os, re, ssl, sys, time, logging, threading, http.client, hashlib, socket
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128      # default is 5: a burst of simultaneous connections got reset
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen, Request
from urllib.error import URLError
from pathlib import Path

# Módulo compartido de autenticación (carpeta hermana /auth).
# EN: Shared authentication module (sibling folder /auth).
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

# Solo loopback; el acceso desde la red pasa por nginx.
# EN: Loopback only; network access goes through nginx.
HOST       = "127.0.0.1"
PORT       = 8084
STATIC_DIR = Path(__file__).parent / "static"
# clusters.json: clusters configurados, con su token de API (por eso el archivo es privado, modo 0600).
# EN: clusters.json: configured clusters, with their API token (so the file is private, mode 0600).
# Los datos viven en /var/lib/pi-console/proxmox-monitor (el código de /opt es de solo lectura para el servicio).
# EN: The data lives in /var/lib/pi-console/proxmox-monitor (the code in /opt is read-only for the service).
DATA_DIR   = auth.module_data("proxmox-monitor")
auth.adopt_legacy(Path(__file__).parent, DATA_DIR, ("clusters.json", "history.json"))
DATA_FILE  = DATA_DIR / "clusters.json"
# Ritmos de consulta: rápido cuando hay alguien mirando, lento cuando no (variables PVE_POLL_*).
# EN: Polling rates: fast when someone is looking, slow when not (PVE_POLL_* variables).
POLL_ACTIVE = float(os.environ.get("PVE_POLL_ACTIVE", 5))    # seconds, while someone is watching
POLL_IDLE   = float(os.environ.get("PVE_POLL_IDLE", 60))     # seconds, when nobody has the page open
# Una página abierta cuenta como «mirando» durante este tiempo desde su última petición.
# EN: An open page counts as "looking" for this long after its last request.
VIEW_GRACE  = 30                                              # a viewer counts as active for this long
# Versión de Proxmox y estado de Ceph cambian poco: se refrescan solo una vez por minuto.
# EN: Proxmox version and Ceph state change little: they are refreshed only once a minute.
SLOW_EVERY  = 60                                              # version / ceph refresh period
# Cada cuántos segundos se guarda una muestra de CPU/RAM por nodo para los gráficos.
# EN: How often, in seconds, a CPU/RAM sample per node is stored for the charts.
HIST_EVERY  = 30                                              # node history sampling period
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
    with socket.create_connection((host, int(port)), timeout=timeout) as raw:
        with ctx.wrap_socket(raw, server_hostname=host) as tls:
            return hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest()

# Cliente de la API de Proxmox con una conexión HTTPS persistente (evita repetir el handshake TLS en cada consulta).
# Autentica con el token de API en la cabecera Authorization.
# EN: Proxmox API client with a persistent HTTPS connection (avoids repeating the TLS handshake on every query).
#     Authenticates with the API token in the Authorization header.
class PVEClient:
    """PVE API client with a persistent HTTPS connection (avoids a TLS handshake on every poll)."""
    def __init__(self, host, port, user, token_name, token_value, verify_ssl=False, fingerprint=None):
        self.host, self.port = host, int(port)
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
        except Exception:
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

    def node_status(self, node: str) -> dict:
        return self.get(f"/nodes/{node}/status").get("data", {})

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
        except Exception:
            return []

    # Versión de Proxmox VE; si falla devuelve cadena vacía.
    # EN: Proxmox VE version; returns an empty string on failure.
    def version(self) -> str:
        try:
            return self.get("/version").get("data", {}).get("version", "")
        except Exception:
            return ""

# ─── Clusters config ──────────────────────────────────────────────────────────
# Candado de la lista de clusters. Regla: cargar → modificar → guardar dentro de este candado.
# EN: Lock of the cluster list. Rule: load → modify → save inside this lock.
_cl_lock = threading.RLock()      # hold around load_clusters() → modify → save_clusters()

# Lee clusters.json (con la red de seguridad de auth.read_json).
# EN: Read clusters.json (with the safety net of auth.read_json).
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
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x

def _store_sample(cid, node, ts, cpu, mem):
    try:
        c = auth.metrics_conn()
        try:
            c.execute("INSERT OR REPLACE INTO pve_samples (cid,node,ts,cpu,mem) VALUES (?,?,?,?,?)", (cid, node, ts, cpu, mem))
            c.commit()
        finally: c.close()
    except Exception as e:
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
    except Exception as e:
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
            except Exception: keep = None
            cut = int(time.time()) - _HIST_MAX * HIST_EVERY
            rows = c.execute("SELECT cid,node,ts,cpu,mem FROM pve_samples WHERE ts >= ? ORDER BY ts", (cut,)).fetchall()
        finally: c.close()
        with _hist_lock:
            for cid, node, ts, cpu, mem in rows:
                if keep is not None and cid not in keep: continue
                dq = _NODE_HISTORY.setdefault(f"{cid}:{node}", _deque(maxlen=_HIST_MAX))
                dq.append({"ts": ts, "cpu": cpu, "mem": mem}); n += 1
    except Exception as e:
        log.warning(f"could not load the history: {e}")
    return n

def _history_pruner():
    while True:
        time.sleep(3600)
        try:
            c = auth.metrics_conn()
            try: c.execute("DELETE FROM pve_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,)); c.commit()
            finally: c.close()
        except Exception as e: log.warning(f"could not prune the history: {e}")


# Última lectura de un cluster (datos, error y hora). El evento «wake» obliga al poller a refrescar de inmediato.
# EN: Last reading of a cluster (data, error and time). The "wake" event forces the poller to refresh at once.
class ClusterCache:
    def __init__(self, cid):
        self.id    = cid
        self._lock = threading.RLock()
        self._data = {}
        self._err  = None
        self._ts   = None
        self.wake  = threading.Event()     # set to make the poller refresh right now

    def update(self, data: dict):
        with self._lock:
            self._data = data
            self._err  = None
            self._ts   = time.time()

    def set_error(self, e: str):
        with self._lock:
            self._err = e

    def snap(self) -> dict:
        with self._lock:
            return {"id": self.id, "data": dict(self._data),
                    "error": self._err, "ts": self._ts}

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
            except Exception as e:
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
    except Exception:
        pass

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
    use_resources = True

    while True:
        try:
            cur = next((c for c in load_clusters() if c["id"] == cid), None)
            gone = cur is None
            if cur is not None:                  # picks up a certificate pinned while running
                fp = _fp_norm(cur.get("fingerprint"))
                if fp != client.fingerprint:
                    client.fingerprint = fp; client.close()
        except Exception as e:                    # never let the poller thread die on a config hiccup
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
                except Exception: ceph = None
                slow_ts = t0

            for nd in nodes_data:
                if nd.get("status") == "online":
                    push_node_history(cid, nd["name"], nd.get("cpu", 0), nd.get("mem", 0), nd.get("maxmem", 0))

            cache.update({"nodes": nodes_data, "version": version,
                          "name": cluster["name"], "ceph": ceph})
            _cluster_events(cluster, nodes_data, ceph)
            log.debug(f"[{cluster['name']}] {len(nodes_data)} nodes in {time.time()-t0:.2f}s")

        except Exception as e:
            cache.set_error(str(e))
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
                pub = {k: v for k, v in c.items() if k != "token_value"}     # never send the API token to the browser
                pub["pinned"] = bool(_fp_norm(c.get("fingerprint")))
                pub.setdefault("layout", {"order": [], "pinned": []})
                out.append({**pub, "snap": snap, "alerts": alerts})
            self._json(200, {"clusters": out})

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
                                  "permissions": sess["permissions"]})
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
            u, err = auth.login(self, body.get("username",""), body.get("password",""))
            if not u: return self._json(err[0], {"error": err[1]})
            token = auth.create_session(body["username"], u["permissions"])
            users = auth.load_users()
            must  = users.get(body["username"],{}).get("must_change_password", False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie",
                auth.session_cookie(token))
            br = json.dumps({"ok": True, "username": body["username"],
                             "permissions": u["permissions"],
                             "must_change_password": must}).encode()
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

        if not auth.check_permission(tok, "pve", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        # Alta de cluster: valida los campos y EXIGE la huella del certificado confirmada por el usuario (flujo «Probar» dos
        # veces en la página). Rechaza host:puerto duplicado y nunca devuelve el token.
        # EN: Add a cluster: validates the fields and REQUIRES the certificate fingerprint confirmed by the user (the "Test" two-step
        #     flow on the page). Rejects a duplicate host:port and never returns the token.
        if path == "/api/clusters":
            if not auth.check_permission(tok, "pve", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            host  = str(body.get("host","")).strip()
            name  = (body.get("name","")).strip()
            user  = str(body.get("user","")).strip()
            tname = str(body.get("token_name","")).strip()
            tval  = str(body.get("token_value","")).strip()
            try: port = int(body.get("port", 8006))
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
            if not all([host,name,user,tname,tval]):
                return self._json(400, {"error": "All fields are required"})
            if not auth.valid_host(host): return self._json(400, {"error": "Invalid host"})
            if len(name) > 60 or re.search(r"[\x00-\x1f\x7f]", name): return self._json(400, {"error": "Invalid name"})
            if not re.fullmatch(r"[A-Za-z0-9_.@!-]{1,64}", user) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", tname):
                return self._json(400, {"error": "Invalid user or token name"})
            if not 1 <= port <= 65535: return self._json(400, {"error": "Invalid port"})
            fp = _fp_norm(body.get("fingerprint"))
            if not fp:
                return self._json(400, {"error": "Certificate fingerprint required: run Test and confirm it"})
            import uuid
            cluster = {"id": str(uuid.uuid4()), "name": name, "host": host,
                       "port": port, "user": user, "token_name": tname,
                       "token_value": tval, "verify_ssl": False, "fingerprint": fp}
            with _cl_lock:
                clusters = load_clusters()
                if any(c["host"]==host and c.get("port")==port for c in clusters):
                    return self._json(409, {"error": "That host:port already exists"})
                clusters.append(cluster)
                save_clusters(clusters)
            ensure_poller(cluster)
            # never echo the API token back
            self._json(201, {"cluster": {k: v for k, v in cluster.items() if k != "token_value"}})

        # Paso 1 del alta: devuelve la huella del certificado que presenta el servidor (no se envía ningún token).
        # EN: Step 1 of adding: returns the fingerprint of the certificate the server presents (no token is sent).
        elif path == "/api/fingerprint":
            if not auth.check_permission(tok, "pve", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            host = str(body.get("host","")).strip()
            try: port = int(body.get("port", 8006))
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid port"})
            if not auth.valid_host(host) or not 1 <= port <= 65535: return self._json(400, {"error": "Invalid host or port"})
            try:
                self._json(200, {"ok": True, "fingerprint": _fp_fmt(fetch_fingerprint(host, port))})
            except Exception as e:
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
            except Exception as e:
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
            if not auth.valid_host(host) or not 1 <= port <= 65535: return self._json(400, {"error": "Invalid host or port"})
            user  = str(body.get("user","")).strip()
            tname = str(body.get("token_name","")).strip()
            tval  = str(body.get("token_value","")).strip()
            try:
                fp = _fp_norm(body.get("fingerprint"))
                if not fp: return self._json(400, {"error": "Certificate fingerprint required"})
                client = PVEClient(host, port, user, tname, tval, fingerprint=fp)
                ver    = client.version()
                nodes  = client.nodes()
                self._json(200, {"ok": True, "version": ver,
                                 "nodes": len(nodes)})
            except Exception as e:
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
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    # Explicit 'pve' level for users that predate the module (one-time migration)
    try:
        if auth.ensure_permissions(("pve",)): log.info("'pve' permissions updated")
    except Exception as e:
        log.warning(f"Permissions: {e}")

    log.info(f"Proxmox Monitor en http://{HOST}:{PORT} — poll {POLL_ACTIVE:g}s active / {POLL_IDLE:g}s idle")
    # Aviso en el log por cada cluster sin huella fijada: se conecta sin validar el certificado del servidor.
    # EN: Log warning for every cluster without a pinned fingerprint: it connects without validating the server certificate.
    try:
        for _c in load_clusters():
            if not _fp_norm(_c.get("fingerprint")):
                log.warning(f"Cluster '{_c.get('name', _c.get('id'))}' has no pinned certificate: the server identity is NOT verified. Pin it from the Proxmox page.")
    except Exception as e:
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
