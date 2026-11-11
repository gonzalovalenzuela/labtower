#!/usr/bin/env python3
"""
NAS Monitor — estado de uno o varios NAS Synology por SNMP / status of one or more Synology NAS over SNMP
"""
# NAS Monitor (puerto 8086): muestra el estado de uno o varios NAS Synology leyendo su MIB por SNMP (v3 o v2c): sistema,
# temperatura, CPU, memoria, discos, volúmenes (RAID), red, UPS y carga de disco. Es solo lectura: no hace falta ninguna cuenta del NAS.
# También lee el vencimiento de los certificados TLS de los puertos elegidos (por defecto 5001, DSM), con auth/certinfo.py.
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
#     It also reads the expiry of the TLS certificates on the chosen ports (default 5001, DSM), with auth/certinfo.py.
#
#     Data flow:
#       one "poller" thread per NAS → collect() runs snmpget / snmpbulkwalk (net-snmp) → NasCache keeps the last reading
#       → the page requests it from /api/nas. The thread polls fast (15 s) while someone is looking at the page and slowly (60 s) if nobody has it open.
#
#     Security: SNMP credentials go in a private temporary snmp.conf (0600), never on the command line (they would show in "ps"),
#     and are never returned to the browser (only "has_*"). nas.json is private (0600).
#
#     Structure: SNMP · configuration · reading one NAS · cache and history · poller · health · HTTP.
import json
import logging
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ThreadingHTTPServer.request_queue_size = 128
from collections import deque as _deque
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Módulo compartido de autenticación (carpeta hermana /auth).
# EN: Shared authentication module (sibling folder /auth).
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import certinfo  # lectura de certificados TLS / TLS certificate reading

import auth

sys.path.insert(0, str(Path(__file__).parent))
import remote  # TrueNAS y OpenMediaVault por API / TrueNAS and OpenMediaVault over their APIs

# Solo loopback; el acceso desde la red pasa por nginx.
# EN: Loopback only; network access goes through nginx.
HOST       = "127.0.0.1"
PORT       = 8086
STATIC_DIR = Path(__file__).parent / "static"
DATA_DIR   = auth.module_dir("nas-monitor")          # solo la ruta; la carpeta se crea al arrancar / EN: path only, created at startup
LEGACY_FILES = ()
DATA_FILE  = DATA_DIR / "nas.json"
POLL_ACTIVE = float(os.environ.get("NAS_POLL_ACTIVE", "15"))   # seconds, while someone is watching
POLL_IDLE   = float(os.environ.get("NAS_POLL_IDLE", "60"))     # seconds, when nobody has the page open
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
# Tipos de NAS: «synology» (SNMP, el original), «truenas» (API JSON-RPC por WebSocket, clave de API) y «omv» (OpenMediaVault, rpc.php, usuario y clave).
# EN: NAS types: "synology" (SNMP, the original), "truenas" (JSON-RPC WebSocket API, API key) and "omv" (OpenMediaVault, rpc.php, user and password).
TYPES        = ("synology", "truenas", "omv")
API_FIELDS   = ("host", "port", "https", "verify_tls", "user", "password", "api_key", "timeout")
API_SECRETS  = ("password", "api_key")
SECRETS      = SNMP_SECRETS + API_SECRETS
API_DEFAULTS = {"truenas": {"port": 443, "https": True, "verify_tls": False, "user": "", "api_key": "", "timeout": 8},
                "omv":     {"port": 443, "https": True, "verify_tls": False, "user": "admin", "password": "", "timeout": 8}}
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
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=cfg["timeout"] * 4 + 20, check=False)
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
    cfg = _validate_base(body, current)
    _vol_thresholds(cfg, body, current)
    _cert_opts(cfg, body, current)
    # La pausa solo cambia por su propia ruta (/pause): editar el NAS la conserva y el formulario no la puede fijar.
    # EN: The pause only changes through its own route (/pause): editing the NAS keeps it and the form cannot set it.
    if current is not None and current.get("enabled") is False: cfg["enabled"] = False
    return cfg

def is_paused(n: dict) -> bool:
    """Pausado por un administrador: no se consulta, no avisa ni genera eventos. / EN: Paused by an administrator: not polled, no alerts or events."""
    return auth.paused(n)

# Certificados: puertos TLS que se revisan en el host del NAS y días antes del vencimiento para el aviso y el crítico (por defecto 14 / 3;
# 1–90 y crítico < aviso). Sin lista guardada: Synology revisa 5001 (DSM) y TrueNAS / OpenMediaVault su propio puerto si usan HTTPS.
# Una lista vacía no revisa nada.
# EN: Certificates: TLS ports checked on the NAS host and days before expiry for the warning and the critical level (default 14 / 3;
#     1-90 and critical < warning). With no stored list: Synology checks 5001 (DSM) and TrueNAS / OpenMediaVault their own port when they
#     use HTTPS. An empty list checks nothing.
CERT_WARN, CERT_CRIT, CERT_MAX_PORTS = 14, 3, 8

def cert_ports_default(cfg: dict) -> list:
    if (cfg.get("type") or "synology") == "synology": return [5001]
    return [cfg["port"]] if cfg.get("https", True) and isinstance(cfg.get("port"), int) else []

def cert_ports(cfg: dict) -> list:
    v = cfg.get("cert_ports")
    return list(v) if isinstance(v, list) else cert_ports_default(cfg)

def cert_thr(cfg: dict) -> tuple:
    """(días de aviso, días de crítico) / (warning days, critical days)."""
    w, c = cfg.get("cert_warn", CERT_WARN), cfg.get("cert_crit", CERT_CRIT)
    ok = all(isinstance(v, int) and not isinstance(v, bool) for v in (w, c)) and 1 <= c < w <= 90
    return (w, c) if ok else (CERT_WARN, CERT_CRIT)

def _cert_opts(cfg: dict, body: dict, current=None) -> None:
    cur = current or {}
    ports = body["cert_ports"] if "cert_ports" in body else cur.get("cert_ports", cert_ports_default(cfg))
    if isinstance(ports, str): ports = [x for x in re.split(r"[\s,;]+", ports) if x]
    if not isinstance(ports, list) or len(ports) > CERT_MAX_PORTS: raise ValueError(f"Up to {CERT_MAX_PORTS} certificate ports")
    out = []
    for x in ports:
        try:    x = int(None if isinstance(x, bool) else x)          # True/False no son puertos / True/False are not ports
        except (TypeError, ValueError): raise ValueError("Invalid certificate port")
        if not 1 <= x <= 65535: raise ValueError("Invalid certificate port")
        if x not in out: out.append(x)
    thr = {}
    for k, d in (("cert_warn", CERT_WARN), ("cert_crit", CERT_CRIT)):
        v = body[k] if k in body else cur.get(k, d)
        try:    v = int(None if isinstance(v, bool) else v)
        except (TypeError, ValueError): raise ValueError("Invalid certificate days")
        if not 1 <= v <= 90: raise ValueError("Certificate days must be 1-90")
        thr[k] = v
    if thr["cert_crit"] >= thr["cert_warn"]: raise ValueError("Certificate critical days must be lower than warning days")
    cfg["cert_ports"] = out; cfg.update(thr)

# Umbrales de aviso / crítico de los volúmenes, por NAS (por defecto 90 / 95). 1–100 y aviso < crítico.
# EN: Per-NAS volume warning / critical thresholds (default 90 / 95). 1-100 and warning < critical.
def _vol_thresholds(cfg: dict, body: dict, current=None) -> None:
    out = {}
    for k, d in (("vol_warn", VOL_WARN), ("vol_crit", VOL_CRIT)):
        v = body[k] if k in body else (current or {}).get(k, d)
        if isinstance(v, bool): raise ValueError("Invalid volume threshold")  # noqa: TRY004 - validación de entrada; quien llama espera ValueError / EN: input validation, callers expect ValueError
        try:    v = int(v)
        except (TypeError, ValueError): raise ValueError("Invalid volume threshold")
        if not 1 <= v <= 100: raise ValueError("Volume thresholds must be 1-100")
        out[k] = v
    if out["vol_warn"] >= out["vol_crit"]: raise ValueError("Volume warning must be lower than critical")
    cfg.update(out)

def vol_thr(cfg) -> tuple:
    try:
        w, c = int(cfg.get("vol_warn", VOL_WARN)), int(cfg.get("vol_crit", VOL_CRIT))
        if 1 <= w < c <= 100: return w, c
    except (TypeError, ValueError): pass
    return VOL_WARN, VOL_CRIT

def _validate_base(body: dict, current=None) -> dict:
    typ = (current.get("type") or "synology") if current is not None else body.get("type") or "synology"
    if not isinstance(typ, str) or typ not in TYPES: raise ValueError("Invalid NAS type")
    if current is not None and body.get("type") not in (None, "", typ): raise ValueError("The NAS type cannot be changed")
    if typ != "synology": return _validate_api(typ, body, current)
    cfg = dict(DEFAULTS); cfg.update({k: v for k, v in (current or {}).items() if k in SNMP_FIELDS or k in ("name", "id", "vol_warn", "vol_crit")})
    cfg["type"] = "synology"
    for k in ("name",) + SNMP_FIELDS:
        if k not in body: continue
        v = body[k]
        if k in SNMP_SECRETS and (v is None or v == ""): continue      # empty secret = keep the stored one
        cfg[k] = v
    cfg["name"] = str(cfg.get("name") or "").strip()
    if not cfg["name"] or len(cfg["name"]) > 60 or re.search(r"[\x00-\x1f\x7f]", cfg["name"]): raise ValueError("Invalid name")
    cfg["host"] = str(cfg.get("host") or "").strip()
    if not auth.valid_target(cfg["host"]): raise ValueError("Invalid host (this machine and link-local addresses are not allowed)")
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

# TrueNAS y OpenMediaVault: valida la petición mezclada con lo guardado. Un secreto vacío = conservar el actual.
# La huella TLS fijada (tls_pin) la aprende el servidor y nunca se acepta del formulario; guardar el NAS otra vez la borra
# (se vuelve a aprender en la siguiente conexión): es la forma de aceptar un certificado nuevo a propósito.
# EN: TrueNAS and OpenMediaVault: validate the request merged with what is stored. An empty secret = keep the current one.
#     The pinned TLS fingerprint (tls_pin) is learned by the server and never accepted from the form; saving the NAS again clears it
#     (it is learned again on the next connection): that is how a new certificate is accepted on purpose.
def _validate_api(typ: str, body: dict, current=None) -> dict:
    cfg = dict(API_DEFAULTS[typ]); cfg.update({k: v for k, v in (current or {}).items() if k in API_FIELDS or k in ("name", "id", "vol_warn", "vol_crit")})
    cfg["type"] = typ
    for k in ("name", "host", "user", "password", "api_key"):
        if body.get(k) is not None and not isinstance(body[k], str): raise ValueError(f"Invalid {k}")
    for k in ("name",) + API_FIELDS:
        if k not in body: continue
        v = body[k]
        if k in API_SECRETS and (v is None or v == ""): continue
        cfg[k] = v
    cfg["name"] = str(cfg.get("name") or "").strip()
    if not cfg["name"] or len(cfg["name"]) > 60 or re.search(r"[\x00-\x1f\x7f]", cfg["name"]): raise ValueError("Invalid name")
    cfg["host"] = str(cfg.get("host") or "").strip()
    if not auth.valid_target(cfg["host"]): raise ValueError("Invalid host (this machine and link-local addresses are not allowed)")
    if isinstance(cfg["port"], bool): raise ValueError("Invalid port")  # noqa: TRY004 - validación de entrada; quien llama espera ValueError / EN: input validation, callers expect ValueError
    try:    cfg["port"] = int(cfg["port"])
    except (TypeError, ValueError): raise ValueError("Invalid port")
    if not 1 <= cfg["port"] <= 65535: raise ValueError("Invalid port")
    try:    cfg["timeout"] = int(cfg["timeout"])
    except (TypeError, ValueError): raise ValueError("Invalid timeout")
    if not 1 <= cfg["timeout"] <= 30: raise ValueError("Timeout must be 1-30 seconds")
    cfg["https"] = True if typ == "truenas" else bool(cfg.get("https", True))      # TrueNAS only works over TLS
    cfg["verify_tls"] = bool(cfg.get("verify_tls", False))
    cfg["tls_pin"] = ""
    for k in ("user", "password", "api_key"):
        cfg[k] = str(cfg.get(k) or "") if k in cfg or k == "user" else ""
        if re.search(r"[\x00-\x1f\x7f]", cfg[k]) or len(cfg[k]) > 512: raise ValueError(f"Invalid {k}")
    if not cfg["user"].strip() or len(cfg["user"]) > 128: raise ValueError("Username required")
    if typ == "truenas":
        cfg.pop("password", None)
        if not cfg["api_key"]: raise ValueError("API key required")
    else:
        cfg.pop("api_key", None)
        if not cfg["password"]: raise ValueError("Password required")
    return cfg

# Vista para el navegador: sin secretos, solo «has_*»; de la huella solo si existe.
# EN: View for the browser: no secrets, only "has_*"; for the fingerprint only whether it exists.
def public(n: dict) -> dict:
    out = {k: v for k, v in n.items() if k not in SECRETS and k != "tls_pin"}
    out.setdefault("type", "synology")
    out["cert_ports"] = cert_ports(n); out["cert_warn"], out["cert_crit"] = cert_thr(n)
    for k in SECRETS: out["has_" + k] = bool(n.get(k))
    out["tls_pinned"] = bool(n.get("tls_pin"))
    return out

# Guarda la huella TLS aprendida de un NAS (TOFU). Solo si todavía no hay una y el host no cambió.
# EN: Store the learned TLS fingerprint of a NAS (TOFU). Only if there is none yet and the host did not change.
def _learn_pin(cfg: dict):
    def learn(fp):
        sid = cfg.get("id")
        if not sid: return                      # connection test of an unsaved NAS: kept in memory only
        with _nas_lock:
            items = load_nas()
            for x in items:
                if x.get("id") == sid and not x.get("tls_pin") and x.get("host") == cfg.get("host") and x.get("port") == cfg.get("port"):
                    x["tls_pin"] = fp; save_nas(items)
                    log.info(f"NAS {x.get('name')!r}: certificate fingerprint pinned ({fp[:16]}…)")
                    break
    return learn

# ─── Lectura de un NAS ────────────────────────────────────────────────────────
OID_SYNO = "1.3.6.1.4.1.6574"
OID_IFX  = "1.3.6.1.2.1.31.1.1.1"
OID_IF   = "1.3.6.1.2.1.2.2.1"          # ifTable: estado del enlace y errores / link state and errors
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

def _num(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and not math.isnan(x)

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
_POOL_RE = re.compile(r"storage\s*pool|pool de almacenamiento|grupo de almacenamiento|reserva de almacenamiento", re.IGNORECASE)

# ES: Series lentas (cada 15 min): uso de cada volumen y temperatura de cada disco. De ahí salen los días hasta llenarse y los máximos de temperatura.
# EN: Slow series (every 15 min): usage of each volume and temperature of each disk. They give the days until full and the temperature peaks.
SERIES_EVERY, SERIES_KEEP = 900, 45 * 86400
_SER_LAST: dict = {}
_DERIVED: dict = {}          # nid -> {"vol": {name: days|None}, "temp": {disk: {max24, avg24, max7}}}

def days_to_full(points, free):
    """points: [(ts, used_bytes)], oldest first. Days until `free` more bytes are used at the recent growth rate, or None when there is
    not enough history (< 2 days), the volume is not growing, the trend is noisy (R² < 0.5) or it would take more than a year."""
    n = len(points)
    if n < 24 or not _num(free) or free < 0: return None
    t0 = points[0][0]
    if points[-1][0] - t0 < 2 * 86400: return None
    xs = [(p[0] - t0) / 86400 for p in points]; ys = [float(p[1]) for p in points]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs); syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0 or sxy <= 0 or (sxy * sxy) / (sxx * syy) < 0.5: return None
    days = free / (sxy / sxx)
    return round(days, 1) if days <= 365 else None

def record_series(nid: str, snap: dict) -> bool:
    now = int(time.time())
    if now - _SER_LAST.get(nid, 0) < SERIES_EVERY: return False
    rows = [(nid, "v:" + r["name"], now, float(r["total"] - r["free"])) for r in snap.get("raids", [])
            if not r.get("pool") and _num(r.get("total")) and _num(r.get("free"))]
    rows += [(nid, "t:" + d["name"], now, float(d["temp"])) for d in snap.get("disks", []) if _num(d.get("temp"))]
    if not rows: return False
    try:
        c = auth.metrics_conn()
        try:
            c.executemany("INSERT OR REPLACE INTO nas_series (nid,k,ts,v) VALUES (?,?,?,?)", rows)
            c.execute("DELETE FROM nas_series WHERE nid = ? AND ts < ?", (nid, now - SERIES_KEEP)); c.commit()
        finally: c.close()
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not store the slow series: {e}"); return False
    _SER_LAST[nid] = now
    return True

def refresh_derived(nid: str, snap: dict):
    now, out = int(time.time()), {"vol": {}, "temp": {}}
    try:
        c = auth.metrics_conn()
        try:
            for r in snap.get("raids", []):
                if r.get("pool") or not _num(r.get("free")): continue
                rows = c.execute("SELECT ts,v FROM nas_series WHERE nid=? AND k=? AND ts>=? ORDER BY ts", (nid, "v:" + r["name"], now - 14 * 86400)).fetchall()
                out["vol"][r["name"]] = days_to_full(rows, r["free"])
            for d in snap.get("disks", []):
                rows = c.execute("SELECT ts,v FROM nas_series WHERE nid=? AND k=? AND ts>=? ORDER BY ts", (nid, "t:" + d["name"], now - 7 * 86400)).fetchall()
                last = [v for ts, v in rows if ts >= now - 86400 and v is not None]
                if last: out["temp"][d["name"]] = {"max24": round(max(last)), "avg24": round(sum(last) / len(last)), "max7": round(max(v for _, v in rows if v is not None))}
        finally: c.close()
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not compute the slow series: {e}"); return
    _DERIVED[nid] = out

def _attach(nid, snap: dict):
    dv = _DERIVED.get(nid) or {}
    for r in snap.get("raids", []): r["days_full"] = (dv.get("vol") or {}).get(r["name"])
    for d in snap.get("disks", []):
        t = (dv.get("temp") or {}).get(d["name"])
        if t: d["t24"] = t

def collect(cfg: dict, prev: dict) -> dict:
    typ = cfg.get("type") or "synology"
    if typ == "synology": return collect_synology(cfg, prev)
    snap = (remote.tn_collect if typ == "truenas" else remote.omv_collect)(cfg, prev, _learn_pin(cfg))
    snap["thr"] = dict(zip(("vol_warn", "vol_crit"), vol_thr(cfg)))
    _attach(cfg.get("id"), snap)
    snap["alerts"] = compute_alerts(snap, vol_thr(cfg)) + snap.pop("extra_alerts", [])
    return snap

def collect_synology(cfg: dict, prev: dict) -> dict:
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
    try:    iff = snmp_walk(cfg, OID_IF)
    except SnmpError as e: iff = {}; warnings.append(f"network link: {e}")

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

    # ES: Actividad de disco. La columna 8 (LA) es instantánea y en muchos equipos marca 0 casi siempre; se usa también el promedio de 1 min (9) y se calcula el rendimiento real (bytes leídos/escritos entre dos lecturas; contadores de 64 bits 12/13, o 3/4 de 32 bits).
    # EN: Disk activity. Column 8 (LA) is instantaneous and reads 0 most of the time on many units; the 1-min average (9) is used too, and real throughput is computed (bytes read/written between two readings; 64-bit counters 12/13, or 32-bit 3/4).
    ib = f"{OID_SYNO}.101.1.1"
    io_name, io_la, io_la1 = (_col(syn, ib, c) for c in (2, 8, 9))
    io_rd, io_wr = _col(syn, ib, 12), _col(syn, ib, 13)
    io_rd32, io_wr32 = _col(syn, ib, 3), _col(syn, ib, 4)
    io, io_cnt, dtio = [], {}, now - prev.get("io_ts", 0)
    for i in sorted(io_name, key=_idx_key):
        dev = io_name[i]
        rd = io_rd.get(i) if _num(io_rd.get(i)) else io_rd32.get(i)
        wr = io_wr.get(i) if _num(io_wr.get(i)) else io_wr32.get(i)
        rrate = wrate = None
        if _num(rd) and _num(wr):
            io_cnt[dev] = (rd, wr)
            p = prev.get("io", {}).get(dev)
            if p and 0 < dtio < 600 and rd >= p[0] and wr >= p[1]:
                rrate, wrate = round((rd - p[0]) / dtio), round((wr - p[1]) / dtio)
        la = [v for v in (io_la.get(i), io_la1.get(i)) if _num(v)]
        io.append({"dev": dev, "load": max(la) if la else None, "read": rrate, "write": wrate})
    prev["io"], prev["io_ts"] = io_cnt, now

    n_name, n_in, n_out, n_speed = (_col(ifx, OID_IFX, c) for c in (1, 6, 10, 15))
    n_oper, n_ein, n_eout = (_col(iff, OID_IF, c) for c in (8, 14, 20))
    net, counters, errs = [], {}, {}
    for i in sorted(n_name, key=_idx_key):
        nm = n_name[i]
        if not IF_OK.match(nm) or not _num(n_in.get(i)) or not _num(n_out.get(i)): continue
        counters[nm] = (n_in[i], n_out[i])
        rx = tx = None
        p = prev.get("net", {}).get(nm)
        dt = now - prev.get("ts", 0)
        if p and 0 < dt < 600 and n_in[i] >= p[0] and n_out[i] >= p[1]:
            rx, tx = round((n_in[i] - p[0]) * 8 / dt), round((n_out[i] - p[1]) * 8 / dt)
        ein, eout = n_ein.get(i), n_eout.get(i)
        erate = None
        if _num(ein) and _num(eout):
            errs[nm] = (ein, eout)
            pe = prev.get("errs", {}).get(nm)
            if pe and 0 < dt < 600 and ein >= pe[0] and eout >= pe[1]: erate = round((ein - pe[0] + eout - pe[1]) / dt * 60, 1)
        oper = n_oper.get(i)
        net.append({"name": nm, "rx": rx, "tx": tx, "speed": n_speed.get(i), "rx_total": n_in[i], "tx_total": n_out[i],
                    "up": (oper == 1) if _num(oper) else None, "err_in": ein if _num(ein) else None, "err_out": eout if _num(eout) else None, "err_rate": erate})
    prev["net"], prev["ts"], prev["errs"] = counters, now, errs

    snap = {"system": system, "cpu": cpu, "mem": mem, "disks": disks, "raids": raids, "ups": ups, "io": io, "net": net,
            "synology": bool(syn), "warnings": warnings}
    snap["thr"] = dict(zip(("vol_warn", "vol_crit"), vol_thr(cfg)))
    _attach(cfg.get("id"), snap)
    snap["alerts"] = compute_alerts(snap, vol_thr(cfg))
    return snap

# Alertas de una lectura: la página y el Resumen las traducen por «type».
# EN: Alerts of a reading: the page and the Overview translate them by "type".
def compute_alerts(s: dict, thr=None) -> list:
    vw, vc = thr or (VOL_WARN, VOL_CRIT)
    a = []
    sysd = s["system"]
    if sysd.get("status") == 2: a.append({"lv": "crit", "type": "system"})
    if sysd.get("power") == 2: a.append({"lv": "crit", "type": "power"})
    if sysd.get("fan_sys") == 2 or sysd.get("fan_cpu") == 2: a.append({"lv": "warn", "type": "fan"})
    if _num(sysd.get("temp")) and sysd["temp"] >= T_SYS_WARN: a.append({"lv": "warn", "type": "temp", "value": sysd["temp"]})
    if _num(s["cpu"].get("pct")) and s["cpu"]["pct"] >= CPU_WARN: a.append({"lv": "warn", "type": "cpu", "value": s["cpu"]["pct"]})
    if s["mem"] and s["mem"]["pct"] >= MEM_WARN: a.append({"lv": "warn", "type": "mem", "value": s["mem"]["pct"]})
    for d in s["disks"]:
        if d["lv"] in ("warn", "crit"): a.append({"lv": d["lv"], "type": "disk", "item": d["name"], "value": d.get("status_text") or d["status"]})
        if _num(d.get("temp")) and d["temp"] >= T_DISK_WARN: a.append({"lv": "warn", "type": "disk_temp", "item": d["name"], "value": d["temp"]})
    for r in s["raids"]:
        if r["lv"] in ("warn", "crit"): a.append({"lv": r["lv"], "type": "raid", "item": r["name"], "value": r.get("status_text") or r["status"]})
        if r["pct"] is not None and r["pct"] >= vw and not r.get("pool"):
            a.append({"lv": "crit" if r["pct"] >= vc else "warn", "type": "vol_full", "item": r["name"], "value": r["pct"]})
    for r in s["raids"]:                                    # se llena pronto por la tendencia / fills up soon by trend
        d = r.get("days_full")
        if _num(d) and d <= 30 and not r.get("pool") and not (r["pct"] is not None and r["pct"] >= vw):
            a.append({"lv": "crit" if d <= 7 else "warn", "type": "vol_days", "item": r["name"], "value": d})
    if s["system"].get("upgrade") == 1: a.append({"lv": "info", "type": "upgrade"})
    return a

# Prueba de conexión con credenciales sin guardar: modelo, DSM y nombre.
# EN: Connection test with credentials, nothing saved: model, DSM and name.
def test_connection(cfg: dict) -> dict:
    typ = cfg.get("type") or "synology"
    if typ != "synology":
        return (remote.tn_test if typ == "truenas" else remote.omv_test)(cfg, _learn_pin(cfg))
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
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
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
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"could not load the history: {e}")
    return n

# Historial de un NAS para un rango (1h, 1d, 1w, 1mo o all) desde la base, reducido a un máximo de puntos promediando intervalos.
# EN: History of one NAS for a range (1h, 1d, 1w, 1mo or all) from the database, reduced to a maximum number of points by averaging intervals.
RANGE_SECS = {"1h": 3600, "1d": 86400, "1w": 604800, "1mo": 2592000}
RANGE_POINTS = 600

def history_window(range_: str, prev: bool = False):
    """(since, until) of a range. prev=True gives the period just before it (same length) so charts can compare the two; "all" has none."""
    now, span = int(time.time()), RANGE_SECS.get(range_)
    if prev: return ((now - 2 * span, now - span) if span else None)
    return (now - span if span else 0, now + 1)

def history_range(nid: str, range_: str, prev: bool = False) -> list:
    win = history_window(range_, prev)
    if win is None: return []
    c = auth.metrics_conn()
    try:
        rows = c.execute("SELECT ts,cpu,mem,temp,rx,tx FROM nas_samples WHERE nid = ? AND ts >= ? AND ts < ? ORDER BY ts", (nid, win[0], win[1])).fetchall()
    finally: c.close()
    if len(rows) <= RANGE_POINTS: step = 1
    else: step = -(-len(rows) // RANGE_POINTS)
    def avg(grp, k):
        v = [r[k] for r in grp if r[k] is not None]
        return round(sum(v) / len(v), 2) if v else None
    out = []
    for i in range(0, len(rows), step):
        grp = rows[i:i + step]
        out.append({"ts": grp[len(grp) // 2][0], "cpu": avg(grp, 1), "mem": avg(grp, 2), "temp": avg(grp, 3), "rx": avg(grp, 4), "tx": avg(grp, 5)})
    return out

def forget_history(nid: str):
    with _hist_lock: _HISTORY.pop(nid, None)
    try:
        c = auth.metrics_conn()
        try: c.execute("DELETE FROM nas_samples WHERE nid = ?", (nid,)); c.commit()
        finally: c.close()
    except Exception as e: log.warning(f"could not delete the history: {e}")  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running

def _history_pruner():
    while True:
        time.sleep(3600)
        try:
            c = auth.metrics_conn()
            try: c.execute("DELETE FROM nas_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,)); c.commit()
            finally: c.close()
        except Exception as e: log.warning(f"could not prune the history: {e}")  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running

# ─── Certificados TLS ─────────────────────────────────────────────────────────
# Un hilo se conecta una vez al día a los puertos de certificado de cada NAS (a la hora si un puerto falló, y enseguida al arrancar o si
# cambian el host o los puertos); el botón «Revisar ahora» (permiso de ejecutar) fuerza una lectura. Solo lee el certificado: no lo valida ni confía en él. Los días, el nivel, las alertas y los eventos se calculan en cada lectura del NAS
# con lo último leído, así que el aviso y el crítico llegan el día que corresponde aunque no se vuelva a conectar.
# EN: A thread connects once a day to the certificate ports of every NAS (after an hour if a port failed, and at once at startup or when
#     the host or the ports change); the "Check now" button (execute permission) forces a read. It only reads the certificate: it does not validate or trust it. Days, level, alerts and events are computed on every NAS reading
#     from the last read, so the warning and the critical level arrive on the right day without reconnecting.
CERT_EVERY, CERT_RETRY, CERT_LOOP, CERT_MIN_GAP = 86400, 3600, 30, 10
_cert_gate = threading.Semaphore(2)        # forced checks at once / lecturas forzadas a la vez
_CERTS: dict = {}            # nid -> {"ts", "sig", "list"}
_cert_lock = threading.Lock()

def _err_text(e) -> str:
    return str(getattr(e, "reason", None) or getattr(e, "strerror", None) or e or type(e).__name__)[:120]

def read_cert(host: str, port: int, timeout: float) -> dict:
    """Lee el certificado de host:puerto / Read the certificate of host:port → {port, cn, issuer, not_after, self_signed} o {port, error}."""
    e = {"port": port}
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        fam, sa = next(((f, a) for f, _, _, _, a in infos if auth.valid_target(a[0].split("%")[0])), (None, None))
        if sa is None: raise ValueError("address not allowed")
        p = certinfo.parse(certinfo.fetch(sa, host, timeout, fam))
        if not p: raise ValueError("unreadable certificate")
    except (OSError, ValueError) as ex:              # incluye ssl.SSLError y socket.timeout / includes ssl.SSLError and socket.timeout
        e["error"] = _err_text(ex); return e
    e.update(cn=p["subject"].get("cn", ""), issuer=p["issuer"].get("o") or p["issuer"].get("cn", ""),
             not_after=p["not_after"], self_signed=p["self_signed"])
    return e

def cert_level(c: dict, thr: tuple, now=None) -> tuple:
    """(nivel, días restantes) de un certificado leído: ok, warn, crit (pocos días), exp (vencido) o err.
    EN: (level, days left) of a read certificate: ok, warn, crit (few days), exp (expired) or err."""
    if c.get("error") or not _num(c.get("not_after")): return "err", None
    warn, crit = thr
    days = math.floor((c["not_after"] - (now or time.time())) / 86400)
    return ("exp" if days < 0 else "crit" if days <= crit else "warn" if days <= warn else "ok"), days

# Certificados de un NAS para la página y sus alertas («item» = «TLS :puerto»).
# EN: Certificates of a NAS for the page and their alerts ("item" = "TLS :port").
def cert_view(n: dict, now=None) -> tuple:
    c = _CERTS.get(n["id"])
    if not c: return [], []
    thr, certs, alerts = cert_thr(n), [], []
    for x in c["list"]:
        lv, days = cert_level(x, thr, now)
        certs.append({**x, "lv": lv, "days": days})
        item = f"TLS :{x['port']}"
        if lv == "err":   alerts.append({"lv": "warn", "type": "cert_err", "item": item, "value": x.get("error")})
        elif lv == "exp": alerts.append({"lv": "crit", "type": "cert_exp", "item": item})
        elif lv in ("warn", "crit"): alerts.append({"lv": lv, "type": "cert", "item": item, "value": days})
    return certs, alerts

# Eventos (con los certificados de cert_view): por vencer (aviso o crítico según los días), vencido (crítico) y renovado (info).
# Un error de conexión no genera eventos.
# EN: Events (from cert_view's certificates): expiring (warning or critical by days), expired (critical) and renewed (info).
#     A connection error raises no events.
def _cert_events(n: dict, certs: list):
    for x in certs:
        lv, days = x["lv"], x["days"]
        if lv == "err": continue
        ch = auth.state_changed(f"nas-cert:{n['id']}:{x['port']}", lv)
        if not ch: continue
        name, p = n["name"], x["port"]
        if lv == "exp": auth.record_event("nas", "crit", f"{name}: certificate on port {p} expired", "nas_certexp", n=name, p=p)
        elif lv in ("warn", "crit"): auth.record_event("nas", lv, f"{name}: certificate on port {p} expires in {days} days", "nas_cert", n=name, p=p, d=days)
        elif ch[0] in ("warn", "crit", "exp"): auth.record_event("nas", "info", f"{name}: certificate on port {p} renewed", "nas_cert_ok", n=name, p=p)

def check_certs_due(n: dict, now=None, force=False) -> bool:
    """Revisa los certificados de un NAS si toca (o si force, salvo que se revisaran hace menos de CERT_MIN_GAP s). True si se revisaron.
    EN: Check a NAS's certificates when due (or when forced, unless checked less than CERT_MIN_GAP s ago). True if checked."""
    now = now or time.time()
    ports = cert_ports(n); sig = (n.get("host"), tuple(ports))
    c = _CERTS.get(n["id"])
    if c and c["sig"] == sig:
        age = now - c["ts"]
        if age < (CERT_MIN_GAP if force else CERT_RETRY if any(x.get("error") for x in c["list"]) else CERT_EVERY): return False
    timeout = min(max(int(n.get("timeout") or 5), 2), 10)
    lst = [read_cert(n["host"], p, timeout) for p in ports]
    with _cert_lock: _CERTS[n["id"]] = {"ts": now, "sig": sig, "list": lst}
    return True

def _cert_loop():
    while True:
        try:
            items = load_nas()
            for n in items:
                if not is_paused(n): check_certs_due(n)
            keep = {n["id"] for n in items}
            with _cert_lock:
                for nid in [k for k in _CERTS if k not in keep]: _CERTS.pop(nid, None)
        except Exception as e:                       # noqa: BLE001 - the thread must survive any failure and retry
            log.error(f"certificate check: {e}")
        time.sleep(CERT_LOOP)

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
    def clear(self):
        with self._lock: self._data, self._err, self._ts = {}, None, None

# La lectura de un NAS sin su número de serie (la copia en caché no se toca).
# EN: A NAS reading without its serial number (the cached copy is not touched).
def _snap_no_serial(snap):
    d = snap.get("data")
    if not isinstance(d, dict) or not isinstance(d.get("system"), dict): return snap
    return {**snap, "data": {**d, "system": {**d["system"], "serial": ""}}}

_cache: dict = {}
_pollers: dict = {}
_glock = threading.Lock()

# Eventos en la línea de tiempo del Resumen cuando cambia el estado de algo importante.
# EN: Events on the Overview timeline when something important changes state.
def _events(n: dict, snap: dict, prev=None):
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
            auth.record_event("nas", {"ok": "info", "info": "info"}.get(lv, lv), f"{name}/{obj['name']}: volume status {obj.get('status_text') or obj['status']}", "nas_raid", n=name, v=obj["name"], st=obj.get("status_text") or (obj["status"] if obj["status"] is not None else "?"))
        else:
            auth.record_event("nas", {"ok": "info", "info": "info"}.get(lv, lv), f"{name}/{obj['name']}: disk status {obj.get('status_text') or obj['status']}", "nas_disk", n=name, d=obj["name"], st=obj.get("status_text") or (obj["status"] if obj["status"] is not None else "?"))
    # ES: Eventos nuevos: actualización de DSM, ventiladores, temperatura de cada disco, enlace y errores de red y reinicio del NAS.
    # EN: New events: DSM update, fans, temperature of each disk, link and errors of each network port, and NAS restart.
    sysd = snap.get("system") or {}
    if auth.state_changed(f"nas-upg:{nid}", "info" if sysd.get("upgrade") == 1 else "ok") and sysd.get("upgrade") == 1:
        auth.record_event("nas", "info", f"{name}: system update available", "nas_upgrade", n=name)
    if auth.state_changed(f"nas-fan:{nid}", "warn" if 2 in (sysd.get("fan_sys"), sysd.get("fan_cpu")) else "ok"):
        bad = 2 in (sysd.get("fan_sys"), sysd.get("fan_cpu"))
        auth.record_event("nas", "warn" if bad else "info", f"{name}: fan " + ("failure" if bad else "back to normal"), "nas_fan" if bad else "nas_fan_ok", n=name)
    for d in snap["disks"]:
        hot = _num(d.get("temp")) and d["temp"] >= T_DISK_WARN
        if auth.state_changed(f"nas-dt:{nid}:{d['idx']}", "warn" if hot else "ok"):
            auth.record_event("nas", "warn" if hot else "info", f"{name}/{d['name']}: " + (f"disk at {d['temp']} °C" if hot else "disk temperature back to normal"),
                              "nas_dtemp" if hot else "nas_dtemp_ok", n=name, d=d["name"], t=d["temp"] if hot else 0)
    for x in snap.get("net", []):
        if x.get("up") is not None and auth.state_changed(f"nas-link:{nid}:{x['name']}", "ok" if x["up"] else "warn"):
            auth.record_event("nas", "info" if x["up"] else "warn", f"{name}: network {x['name']} link " + ("up" if x["up"] else "down"),
                              "nas_link_ok" if x["up"] else "nas_link", n=name, i=x["name"])
        if x.get("err_rate") is not None:
            bad = x["err_rate"] >= 10
            if auth.state_changed(f"nas-ne:{nid}:{x['name']}", "warn" if bad else "ok"):
                auth.record_event("nas", "warn" if bad else "info", f"{name}: network {x['name']} " + (f"errors ({x['err_rate']}/min)" if bad else "errors stopped"),
                                  "nas_neterr" if bad else "nas_neterr_ok", n=name, i=x["name"], e=x["err_rate"] if bad else 0)
    up = sysd.get("uptime")
    if prev is not None and _num(up):
        old = prev.get("uptime")
        if _num(old) and up < old: auth.record_event("nas", "warn", f"{name}: NAS restarted", "nas_reboot", n=name)
        prev["uptime"] = up

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
        except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
            log.error(f"[{nid}] config read: {e}"); n = False
        if n is None: return
        if n and is_paused(n):
            cache.clear()                 # sin datos viejos al reanudar / no stale data when resumed
        elif n:
            t0 = time.time()
            try:
                snap = collect(n, prev)
                snap["name"] = n["name"]
                snap["certs"], cal = cert_view(n); snap["alerts"] += cal
                _cert_events(n, snap["certs"])
                push_history(nid, snap)
                if record_series(nid, snap): refresh_derived(nid, snap)
                cache.update(snap)
                _events(n, snap, prev)
                if auth.state_changed(f"nas-dn:{nid}", "up"):
                    auth.record_event("nas", "info", f"{n['name']}: reachable again", "nas_up", n=n["name"])
                log.debug(f"[{n['name']}] read in {time.time() - t0:.2f}s")
            except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
                cache.set_error(str(e)[:200])
                keep = {k: prev[k] for k in ("omv", "uptime") if k in prev}; prev.clear(); prev.update(keep)      # uptime survives so a reboot while unreachable is noticed
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
    now = time.time(); items = load_nas(); dead, bad = [], []
    snmp_ok = bool(shutil.which("snmpget") and (shutil.which("snmpbulkwalk") or shutil.which("snmpwalk")))
    c["snmp_tools"] = auth.chk(auth.OK, "snmpget / snmpbulkwalk found") if snmp_ok \
        else auth.chk(auth.FAIL if any((x.get("type") or "synology") == "synology" for x in items) else auth.WARN, "net-snmp tools not installed (apt install snmp)")
    paused = [n for n in items if is_paused(n)]
    for n in items:
        if is_paused(n): continue                    # a paused NAS is not checked, so it raises no warning
        t = _pollers.get(n["id"])
        if t is None or not t.is_alive(): dead.append(n["name"]); continue
        cc = _cache.get(n["id"])
        if cc is None: continue
        sn = cc.snap()
        if sn["error"]: bad.append(f'{n["name"]}: {sn["error"]}')
        elif sn["ts"] and now - sn["ts"] > max(3 * POLL_IDLE, 180): bad.append(f'{n["name"]}: data {int(now - sn["ts"])} s old')
    if not items: c["pollers"] = auth.chk(auth.OK, "no NAS configured")
    elif dead:    c["pollers"] = auth.chk(auth.FAIL, "poller stopped: " + ", ".join(dead))
    else:         c["pollers"] = auth.chk(auth.OK, f"{len(items) - len(paused)} running" + (f", {len(paused)} paused" if paused else ""))
    c["nas_snmp"] = auth.chk(auth.WARN, "; ".join(bad)) if bad else auth.chk(auth.OK, "all NAS answering")
    return auth.health_reply("nas", c, detailed)

# ─── HTTP ─────────────────────────────────────────────────────────────────────
_test_gate = threading.Semaphore(2)        # a stuck test must not pile up processes

class H(BaseHTTPRequestHandler):
    timeout = 30
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
            return self._json(200, {"username": sess["username"], "permissions": sess["permissions"],
                      "disabled": auth.disabled_modules()} if sess else {})
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
            ser = auth.can_see_serials(tok)
            out = []
            for n in load_nas():
                if n["id"] not in _pollers or not _pollers[n["id"]].is_alive(): ensure_poller(n)
                snap = NasCache(n["id"]).snap() if is_paused(n) else _cache.get(n["id"], NasCache(n["id"])).snap()
                if not ser: snap = _snap_no_serial(snap)          # serial numbers need the "serials" permission
                out.append({**public(n), "paused": is_paused(n), "snap": snap, "history": get_history(n["id"]) if with_hist else []})
            return self._json(200, {"nas": out})
        # GET /api/nas/<id>/history?range=1h|1d|1w|1mo|all: historial reducido de un NAS para los gráficos de detalle.
        # EN: GET /api/nas/<id>/history?range=...: reduced history of one NAS for the detail charts.
        mh = re.fullmatch(r"/api/nas/([A-Za-z0-9_-]{1,40})/history", path)
        if mh:
            if not any(n.get("id") == mh.group(1) for n in load_nas()): return self._json(404, {"error": "NAS not found"})
            rng = parse_qs(urlparse(self.path).query).get("range", ["1d"])[0]
            if rng not in RANGE_SECS and rng != "all": return self._json(400, {"error": "Invalid range"})
            prev = parse_qs(urlparse(self.path).query).get("prev", ["0"])[0] == "1"
            try: return self._json(200, {"range": rng, "prev": prev, "history": history_range(mh.group(1), rng, prev)})
            except Exception as e:  # noqa: BLE001 - error de la petición: se responde sin caer / request error: answered without crashing
                log.warning(f"history query failed: {e}"); return self._json(500, {"error": "Could not read the history"})
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
            r, err = auth.login_session(self, body.get("username", ""), body.get("password", ""), body.get("remember"), body.get("code"))   # the service checks the password and opens the session
            if not r: return self._json(err[0], {"error": err[1]})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", auth.session_cookie(r["token"], r["ttl"]))
            br = json.dumps({"ok": True, "username": r["username"], "permissions": r["permissions"], "must_change_password": r["must_change_password"]}).encode()
            self.send_header("Content-Length", str(len(br)))
            self.end_headers(); self.wfile.write(br); return
        if path == "/api/logout":
            auth.delete_session(tok); return self._json(200, {"ok": True})
        # Revisar ahora los certificados de un NAS (permiso de ejecutar). Devuelve los certificados y sus alertas, y despierta al poller.
        # EN: Check a NAS's certificates now (execute permission). Returns the certificates and their alerts, and wakes the poller.
        mc = re.fullmatch(r"/api/nas/([A-Za-z0-9_-]{1,40})/certs", path)
        if mc:
            if not auth.check_permission(tok, "nas", "execute"):
                return self._json(403 if auth.check_permission(tok, "nas", "readonly") else 401, {"error": "Execute permission required"})
            n = next((x for x in load_nas() if x["id"] == mc.group(1)), None)
            if not n: return self._json(404, {"error": "NAS not found"})
            if is_paused(n): return self._json(409, {"error": "The NAS is paused"})
            if not _cert_gate.acquire(blocking=False): return self._json(429, {"error": "Too many checks at once"})
            try:     check_certs_due(n, force=True)
            finally: _cert_gate.release()
            cc = _cache.get(n["id"])
            if cc: cc.wake.set()
            certs, alerts = cert_view(n)
            return self._json(200, {"ok": True, "certs": certs, "alerts": alerts})
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
            if cur and cur.get("tls_pin") and cur.get("host") == cfg["host"] and cur.get("port") == cfg["port"]:
                cfg["tls_pin"] = cur["tls_pin"]          # a test keeps the pinned certificate of the saved NAS
            if not _test_gate.acquire(blocking=False): return self._json(429, {"error": "Too many tests at once"})
            try:
                return self._json(200, {"ok": True, **test_connection(cfg)})
            except Exception as e:  # noqa: BLE001 - error de la petición: se responde sin caer / request error: answered without crashing
                return self._json(200, {"ok": False, "error": str(e)[:200]})
            finally: _test_gate.release()

        # Pausar o reanudar: {"paused": true|false}. Solo cambia «enabled»; no toca secretos ni la huella fijada del certificado.
        # EN: Pause or resume: {"paused": true|false}. Only changes "enabled"; secrets and the pinned certificate are left alone.
        mp = re.fullmatch(r"/api/nas/([A-Za-z0-9_-]{1,40})/pause", path)
        if mp:
            if not isinstance(body.get("paused"), bool): return self._json(400, {"error": "paused must be true or false"})
            with _nas_lock:
                items = load_nas()
                cur = next((x for x in items if x["id"] == mp.group(1)), None)
                if not cur: return self._json(404, {"error": "Not found"})
                auth.set_paused(cur, body["paused"]); save_nas(items)
            log.info(f"[{cur['name']}] " + ("paused" if body["paused"] else "resumed"))
            ensure_poller(cur)
            c = _cache.get(cur["id"])
            if c: c.wake.set()                       # stops at once, or reads at once when resumed
            return self._json(200, {"nas": {**public(cur), "paused": is_paused(cur)}})

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
    except Exception as e:  # noqa: BLE001 - se registra y el servicio sigue / logged, the service keeps running
        log.warning(f"Permissions: {e}")
    log.info(f"NAS Monitor en http://{HOST}:{PORT} — poll {POLL_ACTIVE:g}s active / {POLL_IDLE:g}s idle")
    n = load_history()
    if n: log.info(f"History restored: {n} samples")
    start_all()
    threading.Thread(target=_history_pruner, daemon=True, name="history-pruner").start()
    threading.Thread(target=_cert_loop, daemon=True, name="cert-check").start()
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
