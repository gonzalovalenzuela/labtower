#!/usr/bin/env python3
"""
NAS Monitor — estado de uno o varios NAS Synology por SNMP / status of one or more Synology NAS over SNMP
"""
# NAS Monitor (puerto 8086): muestra el estado de uno o varios NAS Synology leyendo su MIB por SNMP (v3 o v2c): sistema,
# temperatura, CPU, memoria, discos, volúmenes (RAID), red, UPS y carga de disco. Es solo lectura: no hace falta ninguna cuenta del NAS.
#
# Flujo de datos:
#   un hilo «poller» por NAS → collect() ejecuta snmpget / snmpbulkwalk (net-snmp) → NasCache guarda la última lectura
#   → la página la pide a /api/nas. El hilo consulta rápido (15 s) mientras alguien mira la página y lento (60 s) si nadie la tiene abierta.
#
# Seguridad: las credenciales SNMP van en un snmp.conf temporal privado (0600), nunca en la línea de comandos (se verían con «ps»), y
# nunca se devuelven al navegador (solo «has_*»). El archivo nas.json es privado (0600).
#
# Estructura: SNMP · configuración · lectura de un NAS · caché e historial · poller · salud · HTTP.
# EN: NAS Monitor (port 8086): shows the status of one or more Synology NAS by reading their MIB over SNMP (v3 or v2c): system,
#     temperature, CPU, memory, disks, volumes (RAID), network, UPS and disk load. It is read-only: no NAS account is needed.
#
#     Data flow:
#       one "poller" thread per NAS → collect() runs snmpget / snmpbulkwalk (net-snmp) → NasCache keeps the last reading
#       → the page requests it from /api/nas. The thread polls fast (15 s) while someone is looking at the page and slowly (60 s) if nobody has it open.
#
#     Security: SNMP credentials go in a private temporary snmp.conf (0600), never on the command line (they would show in "ps"),
#     and are never returned to the browser (only "has_*"). nas.json is private (0600).
#
#     Structure: SNMP · configuration · reading one NAS · cache and history · poller · health · HTTP.
import json, os, re, shutil, subprocess, sys, tempfile, time, logging, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128
from urllib.parse import urlparse, parse_qs
from collections import deque as _deque
from pathlib import Path

# Módulo compartido de autenticación (carpeta hermana /auth).
# EN: Shared authentication module (sibling folder /auth).
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

# Solo loopback; el acceso desde la red pasa por nginx.
# EN: Loopback only; network access goes through nginx.
HOST       = "127.0.0.1"
PORT       = 8086
STATIC_DIR = Path(__file__).parent / "static"
DATA_DIR   = auth.module_dir("nas-monitor")          # solo la ruta; la carpeta se crea al arrancar / EN: path only, created at startup
LEGACY_FILES = ()
DATA_FILE  = DATA_DIR / "nas.json"
POLL_ACTIVE = float(os.environ.get("NAS_POLL_ACTIVE", 15))   # seconds, while someone is watching
POLL_IDLE   = float(os.environ.get("NAS_POLL_IDLE", 60))     # seconds, when nobody has the page open
VIEW_GRACE  = 30                                              # a viewer counts as active for this long
HIST_EVERY  = 30                                              # history sampling period (s)
_HIST_MAX   = 1440                                            # ~12 h at 30 s
HIST_KEEP   = auth.keep_days("NAS_KEEP_DAYS", 7) * 86400
_last_view  = 0.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("nas")

# ─── SNMP (net-snmp) ──────────────────────────────────────────────────────────
# Credenciales: lo que se puede guardar por NAS. Los secretos nunca salen hacia el navegador.
# EN: Credentials: what can be stored per NAS. Secrets never go out to the browser.
SNMP_FIELDS  = ("host", "port", "version", "community", "user", "level", "auth_proto", "auth_pass", "priv_proto", "priv_pass", "timeout")
SNMP_SECRETS = ("community", "auth_pass", "priv_pass")
DEFAULTS     = {"port": 161, "version": "3", "community": "", "user": "", "level": "authPriv", "auth_proto": "SHA",
                "auth_pass": "", "priv_proto": "AES", "priv_pass": "", "timeout": 5}

class SnmpError(RuntimeError):
    pass

# Dirección para net-snmp: IPv4 / nombre → udp:host:puerto; IPv6 → udp6:[host]:puerto.
# EN: Address for net-snmp: IPv4 / name → udp:host:port; IPv6 → udp6:[host]:port.
def _target(cfg: dict) -> str:
    h = cfg["host"]
    return f"udp6:[{h}]:{cfg['port']}" if ":" in h else f"udp:{h}:{cfg['port']}"

# Ejecuta un comando de net-snmp. Las credenciales van en un snmp.conf temporal privado (0600) y NO en la línea de comandos.
# EN: Run a net-snmp command. Credentials go in a private temporary snmp.conf (0600) and NOT on the command line.
def _run(tool: str, cfg: dict, oids: list, extra=()) -> str:
    exe = shutil.which(tool)
    if not exe:
        raise SnmpError(f"{tool} not installed (apt install snmp)")
    d = tempfile.mkdtemp(prefix="pc-nas-")
    try:
        os.chmod(d, 0o700)
        lines = []
        if cfg["version"] == "3":
            lines += [f"defSecurityName {cfg['user']}", f"defSecurityLevel {cfg['level']}"]
            if cfg["level"] != "noAuthNoPriv":
                lines += [f"defAuthType {cfg['auth_proto']}", f"defAuthPassphrase {cfg['auth_pass']}"]
            if cfg["level"] == "authPriv":
                lines += [f"defPrivType {cfg['priv_proto']}", f"defPrivPassphrase {cfg['priv_pass']}"]
        else:
            lines += [f"defCommunity {cfg['community']}"]
        fd = os.open(Path(d) / "snmp.conf", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write("\n".join(lines) + "\n")
        env = dict(os.environ, SNMPCONFPATH=d, SNMP_PERSISTENT_DIR=d, MIBS="")
        cmd = [exe, f"-v{cfg['version']}", "-t", str(cfg["timeout"]), "-r", "1", "-On", "-m", "", *extra, _target(cfg), *oids]
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=cfg["timeout"] * 4 + 20)
    except subprocess.TimeoutExpired:
        raise SnmpError("SNMP query timed out")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if r.returncode != 0 and not r.stdout.strip():
        msg = [l.strip() for l in (r.stderr or r.stdout).splitlines()
               if l.strip() and not l.startswith(("Created directory", "Cannot adopt"))]
        raise SnmpError((msg[-1] if msg else f"{tool} failed")[:200])
    return r.stdout

_RE_LINE = re.compile(r"^\.?((?:\d+\.)*\d+)\s*=\s*([A-Za-z0-9-]+):\s*(.*)$")

# Convierte la salida de net-snmp (-On) a {oid: valor}: enteros como int, Timeticks en segundos, textos sin comillas.
# EN: Convert net-snmp output (-On) to {oid: value}: integers as int, Timeticks in seconds, strings without quotes.
def parse(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = _RE_LINE.match(line.strip())
        if not m: continue
        oid, typ, raw = m.group(1), m.group(2), m.group(3).strip()
        try:
            if typ in ("INTEGER", "Counter32", "Counter64", "Gauge32", "Unsigned32"):
                v = int(raw.split()[0])
            elif typ == "Timeticks":
                v = int(re.match(r"\((\d+)\)", raw).group(1)) / 100.0
            elif typ == "STRING":
                v = raw[1:-1] if len(raw) >= 2 and raw[0] == raw[-1] == '"' else raw
            else:
                continue
        except (ValueError, AttributeError, IndexError):
            continue
        out[oid] = v
    return out

def snmp_get(cfg, oids):  return parse(_run("snmpget", cfg, list(oids)))
def snmp_walk(cfg, oid):
    return parse(_run("snmpbulkwalk" if shutil.which("snmpbulkwalk") else "snmpwalk", cfg, [oid]))

# ─── Configuración de los NAS ─────────────────────────────────────────────────
# Candado de la lista. Regla: cargar → modificar → guardar dentro de este candado.
# EN: List lock. Rule: load → modify → save inside this lock.
_nas_lock = threading.RLock()

def load_nas() -> list:
    return auth.read_json(DATA_FILE, [], list)

def save_nas(items: list):
    with _nas_lock:
        auth.write_json(DATA_FILE, items)        # contiene secretos SNMP: 0600 / EN: holds SNMP secrets: 0600

# Combina la petición con lo guardado y valida cada campo. Un secreto vacío significa «conservar el actual».
# EN: Merge the request with what is stored and validate every field. An empty secret means "keep the current one".
def validate(body: dict, current=None) -> dict:
    cfg = dict(DEFAULTS); cfg.update({k: v for k, v in (current or {}).items() if k in SNMP_FIELDS or k in ("name", "id")})
    for k in ("name",) + SNMP_FIELDS:
        if k not in body: continue
        v = body[k]
        if k in SNMP_SECRETS and (v is None or v == ""): continue      # empty secret = keep the stored one
        cfg[k] = v
    cfg["name"] = str(cfg.get("name") or "").strip()
    if not cfg["name"] or len(cfg["name"]) > 60 or re.search(r"[\x00-\x1f\x7f]", cfg["name"]): raise ValueError("Invalid name")
    cfg["host"] = str(cfg.get("host") or "").strip()
    if not auth.valid_host(cfg["host"]): raise ValueError("Invalid host")
    try:    cfg["port"] = int(cfg["port"])
    except (TypeError, ValueError): raise ValueError("Invalid port")
    if not 1 <= cfg["port"] <= 65535: raise ValueError("Invalid port")
    try:    cfg["timeout"] = int(cfg["timeout"])
    except (TypeError, ValueError): raise ValueError("Invalid timeout")
    if not 1 <= cfg["timeout"] <= 15: raise ValueError("Timeout must be 1-15 seconds")
    cfg["version"] = str(cfg["version"])
    if cfg["version"] not in ("2c", "3"): raise ValueError("Invalid SNMP version")
    for k in ("community", "user", "auth_pass", "priv_pass"):
        cfg[k] = str(cfg.get(k) or "")
        if re.search(r"[\x00-\x1f\x7f\s]", cfg[k]) or len(cfg[k]) > 128: raise ValueError(f"Invalid {k}")
    if cfg["version"] == "2c":
        if not cfg["community"]: raise ValueError("Community required")
    else:
        if not re.fullmatch(r"[\w.@-]{1,32}", cfg["user"]): raise ValueError("Username required (v3)")
        if cfg["level"] not in ("noAuthNoPriv", "authNoPriv", "authPriv"): raise ValueError("Invalid security level")
        if cfg["auth_proto"] not in ("MD5", "SHA", "SHA-224", "SHA-256", "SHA-384", "SHA-512"): raise ValueError("Invalid auth protocol")
        if cfg["priv_proto"] not in ("DES", "AES", "AES-192", "AES-256"): raise ValueError("Invalid privacy protocol")
        if cfg["level"] != "noAuthNoPriv" and len(cfg["auth_pass"]) < 8: raise ValueError("Auth password must be at least 8 characters")
        if cfg["level"] == "authPriv" and len(cfg["priv_pass"]) < 8: raise ValueError("Privacy password must be at least 8 characters")
    return cfg

# Vista para el navegador: sin secretos, solo «has_*».
# EN: View for the browser: no secrets, only "has_*".
def public(n: dict) -> dict:
    out = {k: v for k, v in n.items() if k not in SNMP_SECRETS}
    for k in SNMP_SECRETS: out["has_" + k] = bool(n.get(k))
    return out

# ─── Lectura de un NAS ────────────────────────────────────────────────────────
OID_SYNO = "1.3.6.1.4.1.6574"
OID_IFX  = "1.3.6.1.2.1.31.1.1.1"
SCALARS = {
    "descr": "1.3.6.1.2.1.1.1.0", "sysup": "1.3.6.1.2.1.1.3.0", "name": "1.3.6.1.2.1.1.5.0", "hrup": "1.3.6.1.2.1.25.1.1.0",
    "cpu_user": "1.3.6.1.4.1.2021.11.9.0", "cpu_sys": "1.3.6.1.4.1.2021.11.10.0", "cpu_idle": "1.3.6.1.4.1.2021.11.11.0",
    "mem_total": "1.3.6.1.4.1.2021.4.5.0", "mem_avail": "1.3.6.1.4.1.2021.4.6.0", "mem_buf": "1.3.6.1.4.1.2021.4.14.0",
    "mem_cache": "1.3.6.1.4.1.2021.4.15.0", "swap_total": "1.3.6.1.4.1.2021.4.3.0", "swap_avail": "1.3.6.1.4.1.2021.4.4.0",
    "load1": "1.3.6.1.4.1.2021.10.1.3.1", "load5": "1.3.6.1.4.1.2021.10.1.3.2", "load15": "1.3.6.1.4.1.2021.10.1.3.3",
}
# Nivel de cada estado (ok / info / warn / crit) según la MIB de Synology.
# EN: Level of every state (ok / info / warn / crit) according to the Synology MIB.
DISK_LV = {1: "ok", 2: "ok", 3: "warn", 4: "warn", 5: "crit", 6: "warn"}
RAID_LV = {1: "ok", 2: "warn", 7: "info", 11: "crit", 12: "crit", 21: "warn"}      # el resto (verificando, scrubbing…) es «info»
UP_LV   = {1: "ok", 2: "ok"}
IF_OK   = re.compile(r"^(eth|eno|enp|ens|bond|ovs_eth|ovs_bond|lan|wlan|ppp)[\w.]*$")
T_SYS_WARN, T_DISK_WARN, VOL_WARN, VOL_CRIT, CPU_WARN, MEM_WARN = 70, 55, 90, 95, 85, 90

def _num(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x

# Columna de una tabla: {índice: valor}.
# EN: Column of a table: {index: value}.
def _col(vals: dict, base: str, col: int) -> dict:
    p = f"{base}.{col}."
    return {k[len(p):]: v for k, v in vals.items() if k.startswith(p)}

def _fnum(x):
    try:    return float(x)
    except (TypeError, ValueError): return None

def _idx_key(i): return [int(t) if t.isdigit() else 0 for t in str(i).split(".")]

# Lee todo un NAS. Falla (SnmpError) solo si no responde; si faltan partes de la MIB de Synology, devuelve lo que haya.
# prev: contadores de red de la lectura anterior, para calcular la velocidad.
# EN: Read a whole NAS. It fails (SnmpError) only when it does not answer; if parts of the Synology MIB are missing, it returns what exists.
#     prev: network counters of the previous reading, to compute the rate.
# Un «Storage Pool» (o «Grupo de almacenamiento») queda lleno por diseño cuando sus volúmenes usan todo el espacio: no genera aviso de espacio.
# EN: A "Storage Pool" is full by design when its volumes take all the space: it raises no "nearly full" alert.
_POOL_RE = re.compile(r"storage\s*pool|pool de almacenamiento|grupo de almacenamiento|reserva de almacenamiento", re.I)

def collect(cfg: dict, prev: dict) -> dict:
    now = time.time()
    sc = snmp_get(cfg, SCALARS.values())
    if not sc:
        raise SnmpError("No SNMP answer")
    g = lambda k: sc.get(SCALARS[k])
    warnings = []
    try:    syn = snmp_walk(cfg, OID_SYNO)
    except SnmpError as e: syn = {}; warnings.append(f"synology: {e}")
    try:    ifx = snmp_walk(cfg, OID_IFX)
    except SnmpError as e: ifx = {}; warnings.append(f"network: {e}")

    S = lambda suffix: syn.get(f"{OID_SYNO}.{suffix}")
    system = {"name": g("name") or "", "descr": g("descr") or "", "uptime": g("hrup") if _num(g("hrup")) else g("sysup"),
              "model": S("1.5.1.0") or "", "serial": S("1.5.2.0") or "", "dsm": S("1.5.3.0") or "",
              "upgrade": S("1.5.4.0"), "status": S("1.1.0"), "temp": S("1.2.0"), "power": S("1.3.0"),
              "fan_sys": S("1.4.1.0"), "fan_cpu": S("1.4.2.0")}

    idle = _fnum(g("cpu_idle"))
    cpu = {"pct": round(max(0.0, min(100.0, 100.0 - idle)), 1) if idle is not None else None,
           "user": g("cpu_user"), "sys": g("cpu_sys"), "load": [_fnum(g("load1")), _fnum(g("load5")), _fnum(g("load15"))]}
    mem = None
    if _num(g("mem_total")) and g("mem_total") > 0 and _num(g("mem_avail")):
        tot = g("mem_total") * 1024
        used = max(0, g("mem_total") - g("mem_avail") - (g("mem_buf") or 0) - (g("mem_cache") or 0)) * 1024
        mem = {"total": tot, "used": used, "pct": round(used / tot * 100, 1),
               "swap_total": (g("swap_total") or 0) * 1024, "swap_used": max(0, (g("swap_total") or 0) - (g("swap_avail") or 0)) * 1024}

    base = f"{OID_SYNO}.2.1.1"
    d_id, d_model, d_type, d_st, d_t = (_col(syn, base, c) for c in (2, 3, 4, 5, 6))
    disks = [{"idx": i, "name": d_id.get(i) or f"Disk {n}", "model": (d_model.get(i) or "").strip(), "type": d_type.get(i) or "",
              "status": d_st.get(i), "lv": DISK_LV.get(d_st.get(i), "warn"), "temp": d_t.get(i)}
             for n, i in enumerate(sorted(set(d_id) | set(d_st) | set(d_model), key=_idx_key), 1)]

    base = f"{OID_SYNO}.3.1.1"
    r_name, r_st, r_free, r_tot = (_col(syn, base, c) for c in (2, 3, 4, 5))
    raids = []
    for i in sorted(set(r_name) | set(r_st), key=_idx_key):
        tot, free = r_tot.get(i), r_free.get(i)
        pct = round((tot - free) / tot * 100, 1) if _num(tot) and _num(free) and tot > 0 else None
        name = r_name.get(i) or f"Volume {i}"
        raids.append({"idx": i, "name": name, "status": r_st.get(i), "lv": RAID_LV.get(r_st.get(i), "info"),
                      "total": tot, "free": free, "pct": pct, "pool": bool(_POOL_RE.search(name))})

    ups = None
    u = {"model": S("4.1.1.0"), "status": S("4.2.1.0"), "load": S("4.2.12.1.0"), "charge": S("4.3.1.1.0")}
    if any(v is not None for v in u.values()):
        ups = {"model": u["model"] or "", "status": u["status"] or "", "load": _fnum(u["load"]), "charge": _fnum(u["charge"])}

    io_name, io_la = _col(syn, f"{OID_SYNO}.101.1.1", 2), _col(syn, f"{OID_SYNO}.101.1.1", 8)
    io = [{"dev": io_name[i], "load": io_la.get(i)} for i in sorted(io_name, key=_idx_key)]

    n_name, n_in, n_out, n_speed = (_col(ifx, OID_IFX, c) for c in (1, 6, 10, 15))
    net, counters = [], {}
    for i in sorted(n_name, key=_idx_key):
        nm = n_name[i]
        if not IF_OK.match(nm) or not _num(n_in.get(i)) or not _num(n_out.get(i)): continue
        counters[nm] = (n_in[i], n_out[i])
        rx = tx = None
        p = prev.get("net", {}).get(nm)
        dt = now - prev.get("ts", 0)
        if p and 0 < dt < 600 and n_in[i] >= p[0] and n_out[i] >= p[1]:
            rx, tx = round((n_in[i] - p[0]) * 8 / dt), round((n_out[i] - p[1]) * 8 / dt)
        net.append({"name": nm, "rx": rx, "tx": tx, "speed": n_speed.get(i), "rx_total": n_in[i], "tx_total": n_out[i]})
    prev["net"], prev["ts"] = counters, now

    snap = {"system": system, "cpu": cpu, "mem": mem, "disks": disks, "raids": raids, "ups": ups, "io": io, "net": net,
            "synology": bool(syn), "warnings": warnings}
    snap["alerts"] = compute_alerts(snap)
    return snap

# Alertas de una lectura: la página y el Resumen las traducen por «type».
# EN: Alerts of a reading: the page and the Overview translate them by "type".
def compute_alerts(s: dict) -> list:
    a = []
    sysd = s["system"]
    if sysd.get("status") == 2: a.append({"lv": "crit", "type": "system"})
    if sysd.get("power") == 2: a.append({"lv": "crit", "type": "power"})
    if sysd.get("fan_sys") == 2 or sysd.get("fan_cpu") == 2: a.append({"lv": "warn", "type": "fan"})
    if _num(sysd.get("temp")) and sysd["temp"] >= T_SYS_WARN: a.append({"lv": "warn", "type": "temp", "value": sysd["temp"]})
    if _num(s["cpu"].get("pct")) and s["cpu"]["pct"] >= CPU_WARN: a.append({"lv": "warn", "type": "cpu", "value": s["cpu"]["pct"]})
    if s["mem"] and s["mem"]["pct"] >= MEM_WARN: a.append({"lv": "warn", "type": "mem", "value": s["mem"]["pct"]})
    for d in s["disks"]:
        if d["lv"] in ("warn", "crit"): a.append({"lv": d["lv"], "type": "disk", "item": d["name"], "value": d["status"]})
        if _num(d.get("temp")) and d["temp"] >= T_DISK_WARN: a.append({"lv": "warn", "type": "disk_temp", "item": d["name"], "value": d["temp"]})
    for r in s["raids"]:
        if r["lv"] in ("warn", "crit"): a.append({"lv": r["lv"], "type": "raid", "item": r["name"], "value": r["status"]})
        if r["pct"] is not None and r["pct"] >= VOL_WARN and not r.get("pool"):
            a.append({"lv": "crit" if r["pct"] >= VOL_CRIT else "warn", "type": "vol_full", "item": r["name"], "value": r["pct"]})
    if s["system"].get("upgrade") == 1: a.append({"lv": "info", "type": "upgrade"})
    return a

# Prueba de conexión con credenciales sin guardar: modelo, DSM y nombre.
# EN: Connection test with credentials, nothing saved: model, DSM and name.
def test_connection(cfg: dict) -> dict:
    sc = snmp_get(cfg, [SCALARS["name"], SCALARS["descr"], f"{OID_SYNO}.1.5.1.0", f"{OID_SYNO}.1.5.3.0"])
    if not sc: raise SnmpError("No SNMP answer")
    return {"name": sc.get(SCALARS["name"], ""), "descr": sc.get(SCALARS["descr"], ""),
            "model": sc.get(f"{OID_SYNO}.1.5.1.0", ""), "dsm": sc.get(f"{OID_SYNO}.1.5.3.0", ""),
            "synology": f"{OID_SYNO}.1.5.1.0" in sc}

# ─── Historial (CPU, memoria, temperatura y red por NAS) ──────────────────────
# Un buffer circular de ~12 h por NAS para los gráficos; cada muestra se guarda al instante en metrics.db (tabla nas_samples)
# y al arrancar se recargan las últimas ~12 h. Se conservan NAS_KEEP_DAYS días (7 por defecto).
# EN: A ~12 h circular buffer per NAS for the charts; every sample is stored at once in metrics.db (table nas_samples) and
#     the last ~12 h are reloaded at startup. NAS_KEEP_DAYS days are kept (7 by default).
_HISTORY: dict = {}
_hist_lock = threading.Lock()

def push_history(nid: str, snap: dict):
    sysd, rx, tx = snap["system"], 0, 0
    for n in snap["net"]:
        rx += n["rx"] or 0; tx += n["tx"] or 0
    pt = {"ts": int(time.time()), "cpu": snap["cpu"].get("pct"), "mem": snap["mem"]["pct"] if snap["mem"] else None,
          "temp": sysd.get("temp") if _num(sysd.get("temp")) else None, "rx": rx, "tx": tx}
    with _hist_lock:
        dq = _HISTORY.setdefault(nid, _deque(maxlen=_HIST_MAX))
        if dq and pt["ts"] - dq[-1]["ts"] < HIST_EVERY - 1: return        # fixed 30 s sampling even when polling faster
        dq.append(pt)
    try:
        c = auth.metrics_conn()
        try:
            c.execute("INSERT OR REPLACE INTO nas_samples (nid,ts,cpu,mem,temp,rx,tx) VALUES (?,?,?,?,?,?,?)",
                      (nid, pt["ts"], pt["cpu"], pt["mem"], pt["temp"], pt["rx"], pt["tx"]))
            c.commit()
        finally: c.close()
    except Exception as e:
        log.warning(f"could not store the history sample: {e}")

def get_history(nid: str) -> list:
    with _hist_lock: return list(_HISTORY.get(nid, []))

def load_history() -> int:
    n = 0
    try:
        c = auth.metrics_conn()
        try:
            c.execute("DELETE FROM nas_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,)); c.commit()
            keep = {x.get("id") for x in load_nas()}
            cut = int(time.time()) - _HIST_MAX * HIST_EVERY
            rows = c.execute("SELECT nid,ts,cpu,mem,temp,rx,tx FROM nas_samples WHERE ts >= ? ORDER BY ts", (cut,)).fetchall()
        finally: c.close()
        with _hist_lock:
            for nid, ts, cpu, mem, temp, rx, tx in rows:
                if nid not in keep: continue
                _HISTORY.setdefault(nid, _deque(maxlen=_HIST_MAX)).append({"ts": ts, "cpu": cpu, "mem": mem, "temp": temp, "rx": rx, "tx": tx}); n += 1
    except Exception as e:
        log.warning(f"could not load the history: {e}")
    return n

def forget_history(nid: str):
    with _hist_lock: _HISTORY.pop(nid, None)
    try:
        c = auth.metrics_conn()
        try: c.execute("DELETE FROM nas_samples WHERE nid = ?", (nid,)); c.commit()
        finally: c.close()
    except Exception as e: log.warning(f"could not delete the history: {e}")

def _history_pruner():
    while True:
        time.sleep(3600)
        try:
            c = auth.metrics_conn()
            try: c.execute("DELETE FROM nas_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,)); c.commit()
            finally: c.close()
        except Exception as e: log.warning(f"could not prune the history: {e}")

# ─── Caché y hilos de consulta ────────────────────────────────────────────────
# Última lectura de un NAS (datos, error y hora). El evento «wake» obliga al poller a refrescar de inmediato.
# EN: Last reading of a NAS (data, error and time). The "wake" event forces the poller to refresh at once.
class NasCache:
    def __init__(self, nid):
        self.id, self._lock, self._data, self._err, self._ts = nid, threading.RLock(), {}, None, None
        self.wake = threading.Event()
    def update(self, data):
        with self._lock: self._data, self._err, self._ts = data, None, time.time()
    def set_error(self, e):
        with self._lock: self._err = e
    def snap(self):
        with self._lock: return {"id": self.id, "data": dict(self._data), "error": self._err, "ts": self._ts}

_cache: dict = {}
_pollers: dict = {}
_glock = threading.Lock()

# Eventos en la línea de tiempo del Resumen cuando cambia el estado de algo importante.
# EN: Events on the Overview timeline when something important changes state.
def _events(n: dict, snap: dict):
    nid, name = n["id"], n["name"]
    items = [(f"nas-sys:{nid}", "crit" if any(x["type"] in ("system", "power") for x in snap["alerts"] if x["lv"] == "crit") else "ok", "system", None)]
    for r in snap["raids"]:
        items.append((f"nas-raid:{nid}:{r['idx']}", r["lv"], "raid", r))
    for d in snap["disks"]:
        items.append((f"nas-disk:{nid}:{d['idx']}", d["lv"], "disk", d))
    for key, lv, kind, obj in items:
        ch = auth.state_changed(key, lv)
        if not ch: continue
        if kind == "system":
            if lv == "crit": auth.record_event("nas", "crit", f"{name}: system or power failure", "nas_sys", n=name)
        elif kind == "raid":
            auth.record_event("nas", {"ok": "info", "info": "info"}.get(lv, lv), f"{name}/{obj['name']}: volume status {obj['status']}", "nas_raid", n=name, v=obj["name"], st=obj["status"] if obj["status"] is not None else "?")
        else:
            auth.record_event("nas", {"ok": "info", "info": "info"}.get(lv, lv), f"{name}/{obj['name']}: disk status {obj['status']}", "nas_disk", n=name, d=obj["name"], st=obj["status"] if obj["status"] is not None else "?")

# Bucle del hilo de consulta de un NAS: vuelve a leer su configuración (si se borró, termina; si cambió, la adopta), consulta, guarda
# la lectura y duerme según haya o no alguien mirando. Un error se anota y se reintenta: el hilo nunca muere por un fallo de red.
# EN: Loop of a NAS's polling thread: re-reads its configuration (ends if deleted, adopts changes), queries, stores the reading and sleeps
#     depending on whether someone is looking. An error is logged and retried: the thread never dies because of a network failure.
def _poll(nid: str):
    cache, prev = _cache.get(nid), {}
    if not cache: return
    while True:
        try:
            n = next((x for x in load_nas() if x["id"] == nid), None)
        except Exception as e:
            log.error(f"[{nid}] config read: {e}"); n = False
        if n is None: return
        if n:
            t0 = time.time()
            try:
                snap = collect(n, prev)
                snap["name"] = n["name"]
                push_history(nid, snap)
                cache.update(snap)
                _events(n, snap)
                if auth.state_changed(f"nas-dn:{nid}", "up"):
                    auth.record_event("nas", "info", f"{n['name']}: reachable again", "nas_up", n=n["name"])
                log.debug(f"[{n['name']}] read in {time.time() - t0:.2f}s")
            except Exception as e:
                cache.set_error(str(e)[:200]); prev.clear()
                log.error(f"[{n['name']}] poll error: {e}")
                if auth.state_changed(f"nas-dn:{nid}", "down"):
                    auth.record_event("nas", "crit", f"{n['name']}: unreachable", "nas_down", n=n["name"])
        active = (time.time() - _last_view) < VIEW_GRACE
        cache.wake.wait(POLL_ACTIVE if active else POLL_IDLE)
        cache.wake.clear()

def ensure_poller(n: dict):
    nid = n["id"]
    with _glock:
        if nid not in _cache: _cache[nid] = NasCache(nid)
        if nid not in _pollers or not _pollers[nid].is_alive():
            t = threading.Thread(target=_poll, args=(nid,), daemon=True, name=f"nas-{nid[:8]}")
            _pollers[nid] = t; t.start()
            log.info(f"Poller → {n['name']} ({n['host']})")

def remove_poller(nid: str):
    with _glock:
        c = _cache.pop(nid, None); _pollers.pop(nid, None)
    if c: c.wake.set()                   # the thread notices the NAS is gone and ends
    forget_history(nid)

def start_all():
    for n in load_nas(): ensure_poller(n)

# ─── Health ───────────────────────────────────────────────────────────────────
def health_report(detailed=False):
    c = auth.check_common()
    c["nas_file"] = auth.check_file(DATA_FILE)
    c["snmp_tools"] = auth.chk(auth.OK, "snmpget / snmpbulkwalk found") if shutil.which("snmpget") and (shutil.which("snmpbulkwalk") or shutil.which("snmpwalk")) \
        else auth.chk(auth.FAIL, "net-snmp tools not installed (apt install snmp)")
    now = time.time(); items = load_nas(); dead, bad = [], []
    for n in items:
        t = _pollers.get(n["id"])
        if t is None or not t.is_alive(): dead.append(n["name"]); continue
        cc = _cache.get(n["id"])
        if cc is None: continue
        sn = cc.snap()
        if sn["error"]: bad.append(f'{n["name"]}: {sn["error"]}')
        elif sn["ts"] and now - sn["ts"] > max(3 * POLL_IDLE, 180): bad.append(f'{n["name"]}: data {int(now - sn["ts"])} s old')
    if not items: c["pollers"] = auth.chk(auth.OK, "no NAS configured")
    elif dead:    c["pollers"] = auth.chk(auth.FAIL, "poller stopped: " + ", ".join(dead))
    else:         c["pollers"] = auth.chk(auth.OK, f"{len(items)} running")
    c["nas_snmp"] = auth.chk(auth.WARN, "; ".join(bad)) if bad else auth.chk(auth.OK, "all NAS answering")
    return auth.health_reply("nas", c, detailed)

# ─── HTTP ─────────────────────────────────────────────────────────────────────
_test_gate = threading.Semaphore(2)        # a stuck test must not pile up processes

class H(BaseHTTPRequestHandler):
    timeout = 30
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
            self.send_header("Content-Type", mime); self.send_header("Content-Length", str(len(c)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"); self.send_header("Pragma", "no-cache")
            self.end_headers(); self.wfile.write(c)
        except FileNotFoundError: self._json(404, {"error": "Not found"})

    # GET: página, versión y salud son públicos; el resto exige sesión con NAS «readonly».
    # Rutas: /api/nas, /api/me.
    # EN: GET: page, version and health are public; the rest requires a session with NAS "readonly".
    #     Routes: /api/nas, /api/me.
    def do_GET(self):
        global _last_view
        path = urlparse(self.path).path.rstrip("/") or "/"
        tok  = self._tok()
        if auth.serve_asset(self, STATIC_DIR, path): return
        if path in ("/", "/index.html"):
            return self._file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if path == "/api/version":
            return self._json(200, {"version": auth.version()} if (auth.get_session(tok) or auth.is_local_request(self)) else {})
        if path == "/api/health":
            code, body = health_report(auth.health_mode(self, tok))
            return self._json(code, body)
        if path == "/api/me":
            sess = auth.get_session(tok)
            return self._json(200, {"username": sess["username"], "permissions": sess["permissions"]} if sess else {})
        if not auth.check_permission(tok, "nas", "readonly"):
            return self._json(401, {"error": "Unauthorized"})
        # Lista de NAS con su última lectura, historial y alertas. Pedir esta ruta marca «alguien mira» y despierta a los pollers.
        # Nunca se envían secretos SNMP al navegador.
        # EN: NAS list with their last reading, history and alerts. Requesting this route marks "someone is looking" and wakes the pollers.
        #     SNMP secrets are never sent to the browser.
        if path == "/api/nas":
            was_idle = (time.time() - _last_view) >= VIEW_GRACE
            _last_view = time.time()
            if was_idle:
                for cc in list(_cache.values()): cc.wake.set()
            with_hist = parse_qs(urlparse(self.path).query).get("hist", ["1"])[0] != "0"
            out = []
            for n in load_nas():
                if n["id"] not in _pollers or not _pollers[n["id"]].is_alive(): ensure_poller(n)
                snap = _cache.get(n["id"], NasCache(n["id"])).snap()
                out.append({**public(n), "snap": snap, "history": get_history(n["id"]) if with_hist else []})
            return self._json(200, {"nas": out})
        self._json(404, {"error": "Not found"})

    # POST: login/logout y, solo admin, alta de NAS, edición y prueba de conexión.
    # EN: POST: login/logout and, admin only, add a NAS, edit and connection test.
    def do_POST(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        path = urlparse(self.path).path.rstrip("/")
        tok  = self._tok()
        body = self._body()
        if body is None: return self._json(400, {"error": "Invalid request body"})
        if path == "/api/login":
            u, err = auth.login(self, body.get("username", ""), body.get("password", ""))
            if not u: return self._json(err[0], {"error": err[1]})
            ttl = auth.remember_ttl(body.get("remember"))
            token = auth.create_session(body["username"], u["permissions"], ttl, self)
            must = auth.load_users().get(body["username"], {}).get("must_change_password", False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", auth.session_cookie(token, ttl))
            br = json.dumps({"ok": True, "username": body["username"], "permissions": u["permissions"], "must_change_password": must}).encode()
            self.send_header("Content-Length", str(len(br)))
            self.end_headers(); self.wfile.write(br); return
        if path == "/api/logout":
            auth.delete_session(tok); return self._json(200, {"ok": True})
        if not auth.check_permission(tok, "nas", "admin"):
            return self._json(403 if auth.check_permission(tok, "nas", "readonly") else 401, {"error": "Admin permission required"})

        # Alta de un NAS. Rechaza host:puerto repetido y nunca devuelve secretos.
        # EN: Add a NAS. Rejects a repeated host:port and never returns secrets.
        if path == "/api/nas":
            try: cfg = validate(body)
            except ValueError as e: return self._json(400, {"error": str(e)})
            import uuid
            cfg["id"] = str(uuid.uuid4())
            with _nas_lock:
                items = load_nas()
                if len(items) >= 32: return self._json(400, {"error": "Too many NAS"})
                if any(x["host"] == cfg["host"] and x.get("port") == cfg["port"] for x in items):
                    return self._json(409, {"error": "That host:port already exists"})
                items.append(cfg); save_nas(items)
            ensure_poller(cfg)
            return self._json(201, {"nas": public(cfg)})

        # Prueba de conexión sin guardar. Con «id» usa los secretos guardados para los campos que lleguen vacíos.
        # EN: Connection test without saving. With "id" it uses the stored secrets for fields that arrive empty.
        if path == "/api/test":
            cur = next((x for x in load_nas() if x["id"] == body.get("id")), None) if body.get("id") else None
            try: cfg = validate(body, cur)
            except ValueError as e: return self._json(400, {"error": str(e)})
            if not _test_gate.acquire(blocking=False): return self._json(429, {"error": "Too many tests at once"})
            try:
                return self._json(200, {"ok": True, **test_connection(cfg)})
            except Exception as e:
                return self._json(200, {"ok": False, "error": str(e)[:200]})
            finally: _test_gate.release()

        # Edición: PUT lógico por POST /api/nas/<id>; los secretos vacíos conservan los guardados.
        # EN: Edit: POST /api/nas/<id>; empty secrets keep the stored ones.
        m = re.fullmatch(r"/api/nas/([a-zA-Z0-9\-]+)", path)
        if m:
            with _nas_lock:
                items = load_nas()
                cur = next((x for x in items if x["id"] == m.group(1)), None)
                if not cur: return self._json(404, {"error": "Not found"})
                try: cfg = validate(body, cur)
                except ValueError as e: return self._json(400, {"error": str(e)})
                cfg["id"] = cur["id"]
                if any(x["id"] != cur["id"] and x["host"] == cfg["host"] and x.get("port") == cfg["port"] for x in items):
                    return self._json(409, {"error": "That host:port already exists"})
                items[items.index(cur)] = cfg; save_nas(items)
            c = _cache.get(cfg["id"])
            if c: c.wake.set()
            return self._json(200, {"nas": public(cfg)})
        self._json(404, {"error": "Not found"})

    # DELETE /api/nas/<id>: elimina un NAS, su historial y detiene su consulta (solo admin).
    # EN: DELETE /api/nas/<id>: remove a NAS, its history and stop its polling (admin only).
    def do_DELETE(self):
        if auth.cross_origin(self.headers): return self._json(403, {"error": "Cross-origin request blocked"})
        tok = self._tok()
        if not auth.check_permission(tok, "nas", "admin"):
            return self._json(403, {"error": "Admin permission required"})
        m = re.fullmatch(r"/api/nas/([a-zA-Z0-9\-]+)", urlparse(self.path).path)
        if not m: return self._json(400, {"error": "Invalid ID"})
        with _nas_lock:
            items = load_nas()
            new = [x for x in items if x["id"] != m.group(1)]
            if len(new) == len(items): return self._json(404, {"error": "Not found"})
            save_nas(new)
        remove_poller(m.group(1))
        self._json(200, {"ok": True})

# Arranque: permiso «nas» para usuarios antiguos (una vez), hilos de consulta y servidor en loopback.
# EN: Startup: "nas" permission for old users (once), polling threads and the loopback server.
if __name__ == "__main__":
    auth.prepare_module(DATA_DIR, Path(__file__).parent, LEGACY_FILES)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if auth.ensure_permissions(("nas",)): log.info("'nas' permissions updated")
    except Exception as e:
        log.warning(f"Permissions: {e}")
    log.info(f"NAS Monitor en http://{HOST}:{PORT} — poll {POLL_ACTIVE:g}s active / {POLL_IDLE:g}s idle")
    n = load_history()
    if n: log.info(f"History restored: {n} samples")
    start_all()
    threading.Thread(target=_history_pruner, daemon=True, name="history-pruner").start()
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
