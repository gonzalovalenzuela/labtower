#!/usr/bin/env python3
"""
Net Monitor — Escaneo de red sin nmap + mapeo de host con mac address + evaluacion de sistema operativo y tipo de dispositivo.
Detección: TTL + puertos Python puro + HTTP banner + mDNS

EN: Network scan without nmap + host-to-MAC mapping + operating system and device type assessment.
Detection: TTL + pure-Python ports + HTTP banner + mDNS
"""
# Net Monitor (puerto 8083): descubre los equipos de la LAN SIN nmap, usando solo Python y utilidades básicas.
#
# Cómo identifica cada equipo: ping (da el TTL, que sugiere el sistema operativo), escaneo de puertos TCP,
# banner HTTP, DNS inverso, MAC (tabla ARP, Pi-hole o SNMP de un switch/router) y fabricante por OUI.
# Con esas pistas, identify() puntúa el tipo de dispositivo (router, NAS, cámara, teléfono…) y el SO.
#
# Flujo: un escaneo recorre todas las IP de la red con un pool de hilos → guarda hosts.json → la página lo lee.
# Los escaneos se repiten solos cada SCAN_INTERVAL segundos (o solo a mano si es 0).
#
# Estructura: configuración · sondeos (ping, puertos, banner) · Pi-hole · SNMP · base OUI de fabricantes ·
# reglas de identificación · escáner · salud · manejador HTTP.
# EN: Net Monitor (port 8083): discovers LAN devices WITHOUT nmap, using only Python and basic utilities.
#
#     How it identifies each device: ping (gives the TTL, which hints at the operating system), TCP port scan,
#     HTTP banner, reverse DNS, MAC (ARP table, Pi-hole or SNMP from a switch/router) and vendor from OUI.
#     With those clues, identify() scores the device type (router, NAS, camera, phone…) and the OS.
#
#     Flow: a scan walks every IP of the network with a thread pool → saves hosts.json → the page reads it.
#     Scans repeat by themselves every SCAN_INTERVAL seconds (or only by hand if it is 0).
#
#     Structure: configuration · probes (ping, ports, banner) · Pi-hole · SNMP · OUI vendor database ·
#     identification rules · scanner · health · HTTP handler.
import json, os, re, socket, struct, subprocess, sys, time, logging, threading, ipaddress, ssl
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
# Cola de conexiones pendientes más grande que la de fábrica (5), para no rechazar ráfagas.
# EN: Larger pending-connection queue than the default (5), so bursts are not rejected.
ThreadingHTTPServer.request_queue_size = 128      # default is 5: a burst of simultaneous connections got reset
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    from urllib.request import urlopen, Request
except ImportError:
    pass

# Módulo compartido de autenticación (carpeta hermana /auth).
# EN: Shared authentication module (sibling folder /auth).
sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth
sys.path.insert(0, str(Path(__file__).parent))
import switches as swmod      # Switch Monitor: drivers, sondeo, historial / drivers, polling, history

# Solo loopback; el acceso desde la red pasa por nginx. hosts.json: equipos descubiertos. config.json: ajustes (SNMP, Pi-hole, intervalo).
# EN: Loopback only; network access goes through nginx. hosts.json: discovered devices. config.json: settings (SNMP, Pi-hole, interval).
HOST          = "127.0.0.1"
PORT          = 8083
STATIC_DIR    = Path(__file__).parent / "static"
# Los datos viven en /var/lib/labtower/net-monitor (el código de /opt es de solo lectura para el servicio).
# EN: The data lives in /var/lib/labtower/net-monitor (the code in /opt is read-only for the service).
DATA_DIR      = auth.module_dir("net-monitor")      # solo la ruta; la carpeta se crea al arrancar (auth.prepare_module en main)
LEGACY_FILES = ("hosts.json", "config.json")
DATA_FILE     = DATA_DIR / "hosts.json"
CONF_FILE     = DATA_DIR / "config.json"

# Candado de config.json. Regla: cargar → modificar → guardar dentro de este candado.
# EN: Lock of config.json. Rule: load → modify → save inside this lock.
_cfg_lock = threading.RLock()     # hold around load_config() → modify → save_config()

# Lee config.json (diccionario vacío si no existe o está dañado).
# EN: Read config.json (empty dictionary if missing or damaged).
def load_config() -> dict:
    return auth.read_json(CONF_FILE, {}, dict)

# Guarda config.json de forma atómica.
# EN: Save config.json atomically.
def save_config(cfg: dict):
    # config.json holds the SNMP community and Pi-hole password: private to the service
    with _cfg_lock:
        auth.write_json(CONF_FILE, cfg)
# Parámetros del escáner; todos se pueden cambiar con variables de entorno. NETWORK es la red a recorrer, SCAN_PORTS los puertos que se sondean por equipo, PORT_TIMEOUT cuánto se espera por puerto y MAX_WORKERS cuántos equipos se escanean a la vez.
# EN: Scanner parameters; all can be changed with environment variables. NETWORK is the network to walk, SCAN_PORTS the ports probed per device, PORT_TIMEOUT how long to wait per port and MAX_WORKERS how many devices are scanned at once.
# Red a escanear por defecto: la /24 de la IP de esta máquina (sin enviar nada: connect() en UDP solo elige la interfaz).
# EN: Default network to scan: the /24 of this machine's IP (nothing is sent: a UDP connect() only picks the interface).
def _default_network():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))
            return str(ipaddress.ip_network(s.getsockname()[0] + "/24", strict=False))
    except Exception:
        return "192.0.2.0/24"
NETWORK       = os.environ.get("SCAN_NETWORK",   _default_network())
SCAN_PORTS    = os.environ.get("SCAN_PORTS",     "21,22,23,25,53,80,111,135,139,443,445,548,554,873,902,1883,2049,3074,3260,3306,3389,3493,5000,5001,5060,5061,5357,5432,5555,5900,6379,7547,8001,8002,8006,8008,8009,8080,8291,8443,9100,9295,27017,62078")
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL", 3600))
PORT_TIMEOUT  = float(os.environ.get("PORT_TIMEOUT", 0.5))
MAX_WORKERS   = int(os.environ.get("MAX_WORKERS", 30))

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("net")

# Pi-hole v6 API
# Pi-hole (API v6) como fuente de nombres, MAC y fabricante. Opcional: sin contraseña no se usa. La caché se refresca cada 30 min.
# EN: Pi-hole (API v6) as a source of names, MACs and vendors. Optional: it is not used without a password. The cache is refreshed every 30 min.
PIHOLE_HOSTS  = os.environ.get("PIHOLE_HOSTS",  "")
PIHOLE_PASS   = os.environ.get("PIHOLE_PASS",   "")
_pihole_cache: dict = {}   # { ip: {hostname, vendor, mac} }
_pihole_lock  = threading.Lock()
_pihole_ts    = 0          # timestamp of last successful fetch

# Nombre del servicio típico de cada puerto, para mostrarlo en la página.
# EN: Typical service name for each port, to show on the page.
PORT_NAMES = {
    21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS",
    80:"HTTP", 139:"NetBIOS", 443:"HTTPS", 445:"SMB",
    554:"RTSP", 1883:"MQTT", 3306:"MySQL", 3389:"RDP",
    5432:"PostgreSQL", 5900:"VNC", 6379:"Redis",
    8080:"HTTP-Alt", 8443:"HTTPS-Alt", 27017:"MongoDB", 62078:"iTunes",
    111:"RPC", 135:"MSRPC", 548:"AFP", 873:"rsync", 2049:"NFS", 3260:"iSCSI",
    5000:"DSM/HTTP", 5001:"DSM/HTTPS", 5357:"WSDD", 5555:"ADB", 7547:"TR-069",
    8001:"Tizen", 8002:"Tizen-TLS", 8008:"Cast", 8009:"Cast", 8291:"Winbox", 9100:"Print",
    902:"VMware", 3074:"Xbox Live", 3493:"NUT", 5060:"SIP", 5061:"SIP-TLS", 8006:"Proxmox", 9295:"PS Remote Play"
}

# Grupos de sistema operativo que la página ofrece para filtrar y editar.
# EN: OS groups the page offers for filtering and editing.
OS_GROUPS = ["Windows", "Linux", "macOS", "iOS", "IoT", "Android", "BSD", "Desconocido"]

# ─── TTL → OS hint ────────────────────────────────────────────────────────────
# El TTL inicial del ping delata la familia del SO: 64 Linux/Apple/Android, 128 Windows, 255 equipos de red.
# EN: The initial ping TTL reveals the OS family: 64 Linux/Apple/Android, 128 Windows, 255 network equipment.
def ttl_os_hint(ttl: int) -> str:
    if ttl <= 0:   return ""
    if ttl <= 64:  return "linux_or_apple"   # Linux / macOS / iOS / Android
    if ttl <= 128: return "windows"           # Windows
    return "network_device"                   # routers, IoT

# ─── Ping con TTL ─────────────────────────────────────────────────────────────
# Un ping con tiempo límite: devuelve (responde, TTL, latencia en ms). Se usa el comando del sistema porque enviar ICMP directo requiere root.
# EN: One ping with a timeout: returns (alive, TTL, latency in ms). The system command is used because sending ICMP directly requires root.
def ping_ttl(ip: str) -> tuple[bool, int, float]:
    """Retorna (alive, ttl, latency_ms). TTL=0, latency=0 si no responde."""
    try:
        r = subprocess.run(
            ["ping", "-c1", "-W1", str(ip)],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode != 0:
            return False, 0, 0.0
        # Extraer TTL
        m_ttl = re.search(r"ttl=(\d+)", r.stdout, re.IGNORECASE)
        ttl = int(m_ttl.group(1)) if m_ttl else 0
        # Extraer tiempo en ms
        m_t = re.search(r"time[=<]([\d.]+)\s*ms", r.stdout, re.IGNORECASE)
        latency = float(m_t.group(1)) if m_t else 0.0
        return True, ttl, round(latency, 2)
    except Exception:
        return False, 0, 0.0

# ─── Port scan (Python puro) ──────────────────────────────────────────────────
# ¿Acepta conexiones TCP el puerto? (conexión completa, sin paquetes especiales).
# EN: Does the port accept TCP connections? (full connection, no special packets).
def check_port(ip: str, port: int) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=PORT_TIMEOUT):
            return True
    except Exception:
        return False

# Sondea la lista de puertos en paralelo y devuelve los abiertos, ordenados.
# EN: Probe the list of ports in parallel and return the open ones, sorted.
def scan_ports(ip: str, ports: list[int]) -> list[int]:
    """Escanea lista de puertos en paralelo, retorna los abiertos."""
    open_ports = []
    with ThreadPoolExecutor(max_workers=min(len(ports), 20)) as ex:
        futures = {ex.submit(check_port, ip, p): p for p in ports}
        for f in as_completed(futures):
            if f.result():
                open_ports.append(futures[f])
    return sorted(open_ports)

# ─── HTTP banner ──────────────────────────────────────────────────────────────
# Pide solo las cabeceras (HEAD) y devuelve el valor de «Server:», que a menudo delata el producto (nginx, Synology…).
# EN: Ask for the headers only (HEAD) and return the "Server:" value, which often reveals the product (nginx, Synology…).
def http_banner(ip: str, port: int = 80) -> str:
    try:
        with socket.create_connection((ip, port), timeout=2) as s:
            s.sendall(b"HEAD / HTTP/1.0\r\nHost: " + ip.encode() + b"\r\n\r\n")
            banner = s.recv(1024).decode(errors="replace")
        server = re.search(r"Server:\s*(.+)", banner, re.IGNORECASE)
        return server.group(1).strip()[:80] if server else ""
    except Exception:
        return ""

# ─── Pi-hole v6 API ───────────────────────────────────────────────────────────
# Llamada a la API de Pi-hole. Pi-hole usa un certificado propio en la LAN, así que no se valida contra una CA: se FIJA su huella la primera vez que
# se conecta (TOFU) y si después cambia, la conexión se rechaza y la contraseña no se envía. Guardar de nuevo la configuración de Pi-hole borra
# las huellas fijadas (se vuelven a aprender en la siguiente conexión).
# EN: Call to the Pi-hole API. Pi-hole uses its own certificate on the LAN, so it is not validated against a CA: its fingerprint is PINNED the
#     first time it connects (TOFU) and if it later changes the connection is refused and the password is not sent. Saving the Pi-hole
#     configuration again clears the pinned fingerprints (they are learned again on the next connection).
PIHOLE_HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,251}[A-Za-z0-9])?(?::[0-9]{1,5})?$")
def _pihole_request(host: str, path: str, method: str = "GET",
                    data: bytes = None, sid: str = None) -> dict:
    import http.client, hashlib
    if not PIHOLE_HOST_RE.match(host or ""):
        raise ValueError("invalid Pi-hole host")
    name, _, port = host.partition(":")
    if not auth.valid_target(name):
        raise ValueError("invalid Pi-hole host (this machine and link-local addresses are not allowed)")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    headers = {"Content-Type": "application/json"}
    if sid:
        headers["X-FTL-SID"] = sid
    conn = http.client.HTTPSConnection(name, int(port or 443), timeout=5, context=ctx)
    try:
        conn.connect()
        fp = hashlib.sha256(conn.sock.getpeercert(True)).hexdigest()
        with _cfg_lock:
            cfg = load_config()
            pins = cfg.setdefault("pihole_pins", {})
            if pins.get(host) is None:
                pins[host] = fp; save_config(cfg)
                log.info(f"Pi-hole {host}: certificate fingerprint pinned ({fp[:16]}…)")
            elif pins[host] != fp:
                raise RuntimeError(f"Pi-hole {host}: the certificate changed (pinned fingerprint mismatch); nothing was sent")
        conn.request(method, path, body=data, headers=headers)
        r = conn.getresponse()
        raw = r.read()
        if r.status >= 400:
            raise RuntimeError(f"HTTP {r.status}")
        return json.loads(raw.decode())
    finally:
        conn.close()

# Abre sesión en Pi-hole y devuelve el identificador de sesión (o None).
# EN: Log in to Pi-hole and return the session id (or None).
def _pihole_login(host: str, password: str) -> str | None:
    try:
        d = _pihole_request(host, "/api/auth", "POST",
                            json.dumps({"password": password}).encode())
        sid = d.get("session", {}).get("sid")
        if sid:
            log.info(f"Pi-hole login OK: {host}")
        return sid
    except Exception as e:
        log.warning(f"Pi-hole login error {host}: {e}")
        return None

# Cierra la sesión de Pi-hole para no dejar sesiones colgadas.
# EN: Close the Pi-hole session so none are left hanging.
def _pihole_logout(host: str, sid: str):
    try:
        _pihole_request(host, "/api/auth", "DELETE", sid=sid)
    except Exception:
        pass

# MAC válida con formato aa:bb:cc:dd:ee:ff.
# EN: Valid MAC in aa:bb:cc:dd:ee:ff format.
MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")

# Descarga de Pi-hole los dispositivos conocidos (nombre, fabricante, MAC por IP). Usa el primer Pi-hole que responda.
# EN: Download the known devices from Pi-hole (name, vendor, MAC per IP). Uses the first Pi-hole that answers.
def refresh_pihole_cache():
    """Obtiene hostname+vendor+MAC de Pi-hole y llena _pihole_cache."""
    global _pihole_ts
    password = PIHOLE_PASS
    if not password:
        return

    hosts_list = [h.strip() for h in PIHOLE_HOSTS.split(",") if h.strip()]
    new_cache: dict = {}

    for host in hosts_list:
        sid = _pihole_login(host, password)
        if not sid:
            continue
        try:
            data = _pihole_request(host, "/api/network/devices", sid=sid)
            devices = data.get("devices", [])
            for dev in devices:
                mac    = dev.get("hwaddr", "") or ""
                if not MAC_RE.match(mac):
                    mac = ""          # Pi-hole uses placeholders like "ip-192.0.2.5"
                vendor = dev.get("macVendor", "")
                for ip_entry in dev.get("ips", []):
                    ip   = ip_entry.get("ip", "")
                    name = re.sub(r"(\.local)?\.?$", "", ip_entry.get("name", "") or "")
                    if ip:
                        new_cache[ip] = {
                            "hostname": name,
                            "vendor":   vendor or (oui_vendor(mac) if mac else ""),
                            "mac":      mac,
                        }
            log.info(f"Pi-hole cache: {len(new_cache)} entries from {host}")
            break  # Usar solo el primero que responda
        except Exception as e:
            log.warning(f"Pi-hole network/devices error {host}: {e}")
        finally:
            _pihole_logout(host, sid)

    with _pihole_lock:
        _pihole_cache.clear()
        _pihole_cache.update(new_cache)
        _pihole_ts = time.time()

# Datos de una IP desde la caché; si tiene más de 30 minutos, la refresca en segundo plano sin bloquear.
# EN: Data of an IP from the cache; if it is older than 30 minutes, it is refreshed in the background without blocking.
def pihole_lookup(ip: str) -> dict:
    """Retorna {hostname, vendor, mac} desde cache de Pi-hole."""
    # Refrescar cache si tiene más de 30 minutos
    if time.time() - _pihole_ts > 1800 and PIHOLE_PASS:
        threading.Thread(target=refresh_pihole_cache, daemon=True).start()
    with _pihole_lock:
        return _pihole_cache.get(ip, {})

# ─── DNS inverso ──────────────────────────────────────────────────────────────
# DNS inverso: nombre del equipo a partir de su IP (cadena vacía si no hay).
# EN: Reverse DNS: device name from its IP (empty string if none).
def resolve_dns(ip: str) -> str:
    try:
        return socket.gethostbyaddr(str(ip))[0]
    except Exception:
        return ""

# ─── mDNS hint (sin librería externa) ────────────────────────────────────────
# Pista barata de que el nombre corresponde a un equipo Apple.
# EN: Cheap hint that the name belongs to an Apple device.
def mdns_hint(hostname: str) -> str:
    """Si el hostname termina en .local y tiene sufijo típico de Apple."""
    if not hostname:
        return ""
    h = hostname.lower()
    if any(s in h for s in ["iphone", "ipad", "macbook", "imac", "apple"]):
        return "apple"
    return ""

# ─── SNMP: ARP table from a switch/router (MAC for hosts the server cannot see) ───
import shutil, tempfile
# SNMP: pregunta la tabla ARP de un switch/router para conocer la MAC de equipos que el servidor no ve directamente (otras subredes o VLAN). Los secretos (comunidad, claves) nunca se devuelven al navegador.
# EN: SNMP: asks a switch/router for its ARP table to learn the MAC of devices the server cannot see directly (other subnets or VLANs). Secrets (community, keys) are never returned to the browser.
SNMP_DEFAULT = {"enabled": False, "host": "", "port": 161, "version": "2c", "community": "",
                "user": "", "level": "authPriv", "auth_proto": "SHA", "auth_pass": "",
                "priv_proto": "AES", "priv_pass": "", "timeout": 5}
SNMP_SECRETS = ("community", "auth_pass", "priv_pass")
# Caché ip → MAC obtenida por SNMP y estado de la última consulta.
# EN: Cache of ip → MAC obtained by SNMP and the state of the last query.
_snmp_macs: dict = {}                       # { ip: mac }
_snmp_status = {"ts": 0, "count": 0, "error": ""}
_snmp_lock = threading.Lock()
OID_ARP_V4  = "1.3.6.1.2.1.4.22.1.2"        # ipNetToMediaPhysAddress
# OID de la tabla ARP: la MIB clásica (ipNetToMedia) y la más nueva (ipNetToPhysical).
# EN: OID of the ARP table: the classic MIB (ipNetToMedia) and the newer one (ipNetToPhysical).
OID_ARP_NEW = "1.3.6.1.2.1.4.35.1.4"        # ipNetToPhysicalPhysAddress
RE_ARP_V4  = re.compile(r"\.?1\.3\.6\.1\.2\.1\.4\.22\.1\.2\.\d+\.(\d+\.\d+\.\d+\.\d+)\s*=\s*[A-Za-z-]+:\s*(.*)")
RE_ARP_NEW = re.compile(r"\.?1\.3\.6\.1\.2\.1\.4\.35\.1\.4\.\d+\.1\.4\.(\d+\.\d+\.\d+\.\d+)\s*=\s*[A-Za-z-]+:\s*(.*)")

# Configuración SNMP guardada. Sin include_secrets se vacían los secretos y solo se indica si existen (has_*).
# EN: Stored SNMP configuration. Without include_secrets the secrets are blanked and only their existence is indicated (has_*).
def snmp_config(include_secrets: bool = False) -> dict:
    cfg = dict(SNMP_DEFAULT)
    cfg.update(load_config().get("snmp", {}) or {})
    if not include_secrets:
        for k in SNMP_SECRETS:
            cfg["has_" + k] = bool(cfg.get(k))
            cfg[k] = ""
    return cfg

# Combina la petición con lo guardado y valida cada campo. Un secreto vacío significa «conservar el actual».
# EN: Merge the request with what is stored and validate every field. An empty secret means "keep the current one".
def snmp_validate(body: dict, current: dict) -> dict:
    """Merge a request over the stored config and validate every field (raises ValueError)."""
    cfg = dict(current)
    for k in SNMP_DEFAULT:
        if k not in body: continue
        v = body[k]
        if k in SNMP_SECRETS and (v is None or v == ""):
            continue                                  # empty secret = keep the stored one
        cfg[k] = v
    cfg["enabled"] = bool(cfg["enabled"])
    cfg["host"] = str(cfg["host"]).strip()
    if cfg["host"] and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,252}", cfg["host"]):
        raise ValueError("Invalid host")
    try:    cfg["port"] = int(cfg["port"])
    except Exception: raise ValueError("Invalid port")
    if not 1 <= cfg["port"] <= 65535: raise ValueError("Invalid port")
    try:    cfg["timeout"] = int(cfg["timeout"])
    except Exception: raise ValueError("Invalid timeout")
    if not 1 <= cfg["timeout"] <= 30: raise ValueError("Timeout must be 1-30 seconds")
    cfg["version"] = str(cfg["version"])
    if cfg["version"] not in ("1", "2c", "3"): raise ValueError("Invalid SNMP version")
    for k in ("community", "user", "auth_pass", "priv_pass"):
        cfg[k] = str(cfg.get(k) or "")
        if re.search(r"[\x00-\x1f\x7f]", cfg[k]) or len(cfg[k]) > 128:
            raise ValueError(f"Invalid {k}")
    if cfg["version"] in ("1", "2c"):
        if cfg["enabled"] and not cfg["community"]: raise ValueError("Community required")
    else:
        if not re.fullmatch(r"[\w.@-]{1,32}", cfg["user"]): raise ValueError("Username required (v3)")
        if cfg["level"] not in ("noAuthNoPriv", "authNoPriv", "authPriv"): raise ValueError("Invalid security level")
        if cfg["auth_proto"] not in ("MD5", "SHA", "SHA-224", "SHA-256", "SHA-384", "SHA-512"): raise ValueError("Invalid auth protocol")
        if cfg["priv_proto"] not in ("DES", "AES", "AES-192", "AES-256"): raise ValueError("Invalid privacy protocol")
        if cfg["level"] != "noAuthNoPriv" and len(cfg["auth_pass"]) < 8: raise ValueError("Auth password must be at least 8 characters")
        if cfg["level"] == "authPriv" and len(cfg["priv_pass"]) < 8: raise ValueError("Privacy password must be at least 8 characters")
    if cfg["enabled"] and not cfg["host"]: raise ValueError("Host required")
    return cfg

# Ejecuta snmpwalk. Las credenciales van en un snmp.conf temporal privado (0600) y NO en la línea de comandos, donde cualquier usuario las vería con ps.
# EN: Run snmpwalk. Credentials go in a private temporary snmp.conf (0600) and NOT on the command line, where any user could see them with ps.
def _snmp_walk(cfg: dict, oid: str, regex) -> dict:
    """Run snmpwalk (net-snmp) with credentials in a private temp snmp.conf, not on the command line."""
    exe = shutil.which("snmpwalk")
    if not exe:
        raise RuntimeError("snmpwalk not installed (apt install snmp)")
    d = tempfile.mkdtemp(prefix="pc-snmp-")
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
        conf = Path(d) / "snmp.conf"
        fd = os.open(conf, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write("\n".join(lines) + "\n")
        env = dict(os.environ, SNMPCONFPATH=d, SNMP_PERSISTENT_DIR=d, MIBS="")
        cmd = [exe, f"-v{cfg['version']}", "-t", str(cfg["timeout"]), "-r", "1",
               "-On", "-Ox", "-m", "", f"udp:{cfg['host']}:{cfg['port']}", oid]
        r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                           timeout=cfg["timeout"] * 2 + 30)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if r.returncode != 0 and not r.stdout.strip():
        msg = [l.strip() for l in (r.stderr or r.stdout).splitlines()
               if l.strip() and not l.startswith(("Created directory", "Cannot adopt"))]
        raise RuntimeError((msg[-1] if msg else "snmpwalk failed")[:200])
    out = {}
    for line in r.stdout.splitlines():
        m = regex.match(line.strip())
        if not m: continue
        raw = re.findall(r"[0-9A-Fa-f]{2}", m.group(2).replace('"', ""))
        if len(raw) != 6: continue
        mac = ":".join(raw).lower()
        if mac != "00:00:00:00:00:00" and mac != "ff:ff:ff:ff:ff:ff":
            out[m.group(1)] = mac
    return out

# Tabla ip → MAC del equipo SNMP; prueba la MIB clásica y, si viene vacía, la nueva.
# EN: ip → MAC table of the SNMP device; tries the classic MIB and, if empty, the new one.
def snmp_fetch_arp(cfg: dict) -> dict:
    """ip → mac from the device's ARP table (tries the classic MIB, then the newer one)."""
    res = _snmp_walk(cfg, OID_ARP_V4, RE_ARP_V4)
    if not res:
        try:    res = _snmp_walk(cfg, OID_ARP_NEW, RE_ARP_NEW)
        except Exception: pass
    return res

# Actualiza la caché SNMP al inicio de cada escaneo (si está habilitado). Un fallo se anota pero no detiene el escaneo.
# EN: Update the SNMP cache at the start of each scan (if enabled). A failure is logged but does not stop the scan.
def refresh_snmp():
    """Refresh the SNMP MAC cache (called at the start of each scan, if enabled)."""
    cfg = snmp_config(include_secrets=True)
    if not cfg["enabled"] or not cfg["host"]:
        return
    try:
        res = snmp_fetch_arp(cfg)
        with _snmp_lock:
            _snmp_macs.clear(); _snmp_macs.update(res)
            _snmp_status.update(ts=int(time.time()), count=len(res), error="")
        log.info(f"SNMP: {len(res)} ARP entries from {cfg['host']}")
    except Exception as e:
        with _snmp_lock:
            _snmp_status.update(ts=int(time.time()), count=0, error=str(e)[:200])
        log.warning(f"SNMP error: {e}")

# ─── Device identification (OS + device type, no nmap) ───────────────────────
# Tipos de dispositivo que identify() puede asignar (y que el usuario puede elegir a mano).
# EN: Device types identify() can assign (and the user can choose by hand).
DEVICE_TYPES = ["computer", "phone", "router", "switch", "ap", "storage", "tv", "camera", "appliance", "printer", "tablet",
                "console", "server", "voip", "ups", "speaker", "other"]

# OUI = los 3 primeros bytes de una MAC identifican al fabricante. Fuentes: la lista de Wireshark (se descarga y se actualiza cada semana) y, opcional, el paquete ieee-data del sistema.
# EN: OUI = the first 3 bytes of a MAC identify the manufacturer. Sources: the Wireshark list (downloaded and updated weekly) and, optionally, the system's ieee-data package.
_OUI_PATHS = ["/usr/share/ieee-data/oui.txt", "/var/lib/ieee-data/oui.txt",
              "/usr/share/misc/oui.txt"]
OUI_URL   = os.environ.get("OUI_URL", "https://www.wireshark.org/download/automated/data/manuf.gz")
OUI_FILE  = Path(os.environ.get("LABTOWER_OUI", str(auth.module_dir("net-monitor") / "manuf")))
OUI_MAX_AGE = 7 * 24 * 3600
_oui_db: dict | None = None            # { 24-bit prefix hex: vendor }
_oui_ext: dict = {28: {}, 36: {}}      # longer prefixes (MA-M / MA-S blocks)
_oui_lock = threading.Lock()
_oui_status = {"ts": 0, "count": 0, "error": "", "source": ""}

# Deja solo los dígitos hexadecimales de una MAC, en minúscula.
# EN: Keep only the hexadecimal digits of a MAC, lowercase.
def _hex_only(mac: str) -> str:
    return re.sub(r"[^0-9A-Fa-f]", "", mac or "").upper()

# Lee el archivo manuf de Wireshark (prefijos de 24, 28 y 36 bits) y llena las tablas. Devuelve cuántas entradas leyó.
# EN: Read Wireshark's manuf file (24, 28 and 36-bit prefixes) and fill the tables. Returns how many entries it read.
def _parse_manuf(path: str, db: dict, ext: dict) -> int:
    """Wireshark 'manuf': `00:00:0C<TAB>Cisco<TAB>Cisco Systems, Inc` (and `AA:BB:CC:D0:00:00/28` blocks)."""
    n = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip() or line.startswith("#"): continue
            c = line.rstrip("\n").split("\t")
            if len(c) < 2: continue
            pre, _, mask = c[0].partition("/")
            h = _hex_only(pre)
            name = (c[2] if len(c) > 2 and c[2].strip() else c[1]).strip()
            if not h or not name: continue
            bits = int(mask) if mask.isdigit() else 24
            if bits == 24 and len(h) >= 6:
                db[h[:6]] = name; n += 1
            elif bits in (28, 36) and len(h) >= bits // 4:
                ext[bits][h[:bits // 4]] = name; n += 1
    return n

# Lee el oui.txt del paquete ieee-data; solo agrega prefijos que aún no estén.
# EN: Read the oui.txt of the ieee-data package; only adds prefixes that are not there yet.
def _parse_ieee(path: str, db: dict) -> int:
    n = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "(hex)" in line:
                pre, _, name = line.partition("(hex)")
                k = _hex_only(pre)[:6]
                if k and k not in db:
                    db[k] = name.strip(); n += 1
    return n

# Carga perezosa de la base de fabricantes (la primera vez que se necesita).
# EN: Lazy load of the vendor database (the first time it is needed).
def _load_oui() -> dict:
    """Lazy-load: Wireshark manuf (downloaded) first, ieee-data (optional package) fills the gaps."""
    global _oui_db, _oui_ext
    with _oui_lock:
        if _oui_db is not None:
            return _oui_db
        db, ext, src = {}, {28: {}, 36: {}}, []
        if OUI_FILE.exists():
            try:
                if _parse_manuf(str(OUI_FILE), db, ext): src.append("wireshark")
            except Exception as e:
                log.warning(f"OUI manuf read error: {e}")
        for p in _OUI_PATHS:
            try:
                if os.path.exists(p) and _parse_ieee(p, db): src.append("ieee-data"); break
            except Exception:
                continue
        _oui_db, _oui_ext = db, ext
        _oui_status["source"] = "+".join(src)
        _oui_status["count"] = len(db) + len(ext[28]) + len(ext[36])
        try:    _oui_status["ts"] = int(OUI_FILE.stat().st_mtime)
        except Exception: pass
        return db

# Fabricante de una MAC; se prueba primero el prefijo más específico (36 bits), luego 28 y al final 24.
# EN: Vendor of a MAC; the most specific prefix (36 bits) is tried first, then 28 and finally 24.
def oui_vendor(mac: str) -> str:
    m = _hex_only(mac)
    if len(m) < 6: return ""
    db = _load_oui()
    return (_oui_ext[36].get(m[:9]) or _oui_ext[28].get(m[:7]) or db.get(m[:6], ""))

# Descarga la base de Wireshark (máx. 10 MB), la valida (≥ 1000 entradas) y reemplaza la caché de forma atómica; luego completa el fabricante de los equipos ya conocidos.
# EN: Download Wireshark's database (max 10 MB), validate it (≥ 1000 entries) and replace the cache atomically; then fill in the vendor of already known devices.
def oui_update() -> dict:
    """Download the Wireshark manuf file, validate it, replace the cache atomically, backfill hosts."""
    global _oui_db
    req = Request(OUI_URL, headers={"User-Agent": "labtower-net-monitor"})
    with urlopen(req, timeout=60) as r:  # constant https URL  # nosec B310
        data = r.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise RuntimeError("Downloaded file too large")
    if data[:2] == b"\x1f\x8b":                       # manuf.gz
        import zlib
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        try:    data = d.decompress(data, 40 * 1024 * 1024)
        except zlib.error: raise RuntimeError("Corrupt gzip download")
        if d.unconsumed_tail: raise RuntimeError("Downloaded file too large")
    OUI_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUI_FILE.with_suffix(".tmp")
    tmp.write_bytes(data)
    try:
        n = _parse_manuf(str(tmp), {}, {28: {}, 36: {}})
        if n < 1000:
            raise RuntimeError("Downloaded file does not look like a manuf database")
        tmp.replace(OUI_FILE)
    finally:
        tmp.unlink(missing_ok=True)
    with _oui_lock:
        _oui_db = None                       # force reload
    _load_oui()
    filled = oui_backfill()
    log.info(f"OUI database updated: {_oui_status['count']} prefixes, {filled} hosts got a vendor")
    return {"count": _oui_status["count"], "filled": filled}

# Completa el fabricante de equipos que tienen MAC pero no fabricante.
# EN: Fill in the vendor of devices that have a MAC but no vendor.
def oui_backfill() -> int:
    """Fill the vendor of known hosts that have a MAC but no vendor."""
    n = 0
    with _hosts_lock:
        hosts = _live_hosts if _live_hosts is not None else load_hosts()
        for h in hosts.values():
            if h.get("mac") and not h.get("vendor"):
                v = oui_vendor(h["mac"])
                if v: h["vendor"] = v; n += 1
        if n: save_hosts(hosts)
    return n

# Actualización semanal automática, en un hilo aparte para no demorar el escaneo. Si falla, reintenta la semana siguiente.
# EN: Automatic weekly update, in a separate thread so the scan is not delayed. If it fails, it retries next week.
def oui_maybe_update():
    """Weekly auto-update (called at scan start); never blocks the scan."""
    cfg = load_config().get("oui", {})
    if cfg.get("auto", True) is False: return
    try:    age = time.time() - OUI_FILE.stat().st_mtime
    except Exception: age = 1e12
    if age < OUI_MAX_AGE or _oui_status.get("_busy"): return
    def job():
        _oui_status["_busy"] = True
        try:    oui_update(); _oui_status["error"] = ""
        except Exception as e:
            _oui_status["error"] = str(e)[:200]
            try: OUI_FILE.touch() if OUI_FILE.exists() else None   # retry next week, not every scan
            except Exception: pass
            log.warning(f"OUI update failed: {e}")
        finally: _oui_status["_busy"] = False
    threading.Thread(target=job, daemon=True).start()

# Si el bit «administrada localmente» está activo, la MAC es aleatoria/privada (típico de teléfonos), y no sirve para deducir el fabricante.
# EN: If the "locally administered" bit is set, the MAC is random/private (typical of phones) and cannot be used to deduce the vendor.
def mac_is_private(mac: str) -> bool:
    """Locally-administered bit set → randomized / private address (phones)."""
    m = re.sub(r"[^0-9A-Fa-f]", "", mac or "")
    try:    return bool(int(m[:2], 16) & 0x02)
    except Exception: return False

# MAC de una IP leyendo la tabla ARP del kernel (/proc/net/arp), que el ping recién llenó.
# EN: MAC of an IP read from the kernel ARP table (/proc/net/arp), which the ping just filled.
def arp_mac(ip: str) -> str:
    try:
        with open("/proc/net/arp") as f:
            for line in list(f)[1:]:
                c = line.split()
                if len(c) >= 4 and c[0] == ip and c[3] != "00:00:00:00:00:00":
                    return c[3].lower()
    except Exception:
        pass
    return ""

_gw_cache = {"ts": 0, "ip": ""}
# IP de la puerta de enlace (ruta por defecto en /proc/net/route); se cachea 5 min. Ayuda a reconocer al router.
# EN: Gateway IP (default route in /proc/net/route); cached for 5 min. Helps to recognise the router.
def default_gateway() -> str:
    if time.time() - _gw_cache["ts"] < 300:
        return _gw_cache["ip"]
    gw = ""
    try:
        with open("/proc/net/route") as f:
            for line in list(f)[1:]:
                c = line.split()
                if len(c) > 2 and c[1] == "00000000":
                    gw = socket.inet_ntoa(struct.pack("<L", int(c[2], 16)))
                    break
    except Exception:
        pass
    _gw_cache.update(ts=time.time(), ip=gw)
    return gw

# ¿Alguna de las palabras aparece en el texto?
# EN: Does any of the words appear in the text?
def _has(text: str, words) -> bool:
    return any(w in text for w in words)

# Palabras clave por categoría. V_* se buscan en el fabricante y H_* en el nombre del equipo (hostname). Son pistas; el puntaje final decide.
# EN: Keywords per category. V_* are searched in the vendor and H_* in the device name (hostname). They are clues; the final score decides.
V_STORAGE = ("synology", "qnap", "western digital", "buffalo", "asustor", "terramaster",
             "drobo", "seagate", "lacie", "ixsystems", "readynas", "thecus", "iomega", "ugreen")
V_ROUTER  = ("mikrotik", "routerboard", "sagemcom", "technicolor", "arris", "zyxel", "tenda",
             "fortinet", "juniper", "draytek", "peplink", "sierra wireless", "teltonika", "netcomm")
V_AP      = ("ruckus", "aruba", "engenius", "cambium", "meraki", "aerohive", "grandstream networks")
V_NETGEAR = ("ubiquiti", "tp-link", "tp link", "d-link", "netgear", "cisco", "linksys", "huawei technologies", "hewlett packard enterprise")
V_ANDROID = ("samsung", "xiaomi", "oppo", "oneplus", "vivo", "motorola", "realme", "honor",
             "tecno", "infinix", "hmd global", "nokia", "zte", "lenovo mobile", "google, inc", "google llc")
V_CAMERA  = ("hikvision", "dahua", "axis communications", "reolink", "amcrest", "foscam", "ezviz",
             "vivotek", "uniview", "annke", "hanwha", "wyze", "lorex", "swann", "tp-link tapo")
V_TV      = ("roku", "vizio", "hisense", "tcl ", "tcl,", "lg electronics", "sony visual", "skyworth")
V_APPL    = ("espressif", "tuya", "shelly", "allterco", "sonoff", "itead", "irobot", "roborock", "ecovacs",
             "dyson", "signify", "philips lighting", "amazon technologies", "ecobee", "nest labs",
             "lifx", "meross", "govee", "bsh", "miele", "whirlpool", "electrolux", "smartthings", "xiaomi communications")
H_CAMERA  = re.compile(r"cam(era)?([-_.\d]|$)|^ipc|nvr|dvr|doorbell|hikvision|dahua|reolink", re.I)
H_TV      = re.compile(r"(^|[-_.])tv([-_.\d]|$)|bravia|roku|fire-?tv|apple-?tv|chromecast|webos|tizen|android-?tv|shield|smarttv", re.I)
H_APPL    = re.compile(r"^esp[-_]?\d|esp32|esp8266|shelly|tasmota|roomba|homekit|plug|bulb|lamp|fridge|washer|dryer|oven|vacuum|robot|aspirad|thermostat", re.I)
V_PRINTER = ("brother industries", "canon", "seiko epson", "epson", "lexmark", "xerox", "ricoh", "kyocera",
             "konica minolta", "oki data", "zebra technologies", "fuji xerox", "toshiba tec", "pantum", "sindoh")
H_PRINTER = re.compile(r"print|laserjet|officejet|deskjet|photosmart|pixma|(^|[-_])mfc-?\d|(^|[-_])dcp-?\d|^npi[0-9a-f]|^hp[0-9a-f]{6}|epson|brother|xerox|lexmark|ricoh|kyocera|(^|[-_.])mfp([-_.\d]|$)", re.I)
H_TABLET  = re.compile(r"ipad|tablet|galaxy[-_ ]?tab|^sm-[tx]\d|kindle|(^|[-_])tab([-_.\d]|$)|mi-?pad|matepad|lenovo[-_ ]?tab", re.I)
H_WIN     = re.compile(r"^(desktop|laptop|win|pc|workstation|surface)[-_]", re.I)
H_ANDROID = re.compile(r"android|galaxy|pixel|redmi|xiaomi|poco|oneplus|oppo|realme|huawei|honor|moto[-_ ]|^sm-|^sm[a-z]\d", re.I)
H_STORAGE = re.compile(r"nas|diskstation|synology|qnap|truenas|freenas|openmediavault|\bomv\b|unraid|storage|backup", re.I)
H_ROUTER  = re.compile(r"router|gateway|gw\d*\b|firewall|opnsense|pfsense|mikrotik|openwrt|fritz|^rt[-_]", re.I)
H_AP      = re.compile(r"(^|[-_.])(ap|uap|wap|wifi|wlan|unifi)([-_.\d]|$)|access.?point|eap\d", re.I)
H_SWITCH  = re.compile(r"switch|(^|[-_.])(sw|usw)([-_.\d]|$)|poe", re.I)

# Consolas de juegos, servidores, telefonía IP, UPS y altavoces: categorías que antes caían en «other».
# EN: Game consoles, servers, IP telephony, UPS and speakers: categories that used to end up as "other".
V_CONSOLE = ("nintendo", "sony interactive entertainment", "sony computer entertainment", "valve corp", "oculus vr",
             "meta platforms technologies")
H_CONSOLE = re.compile(r"nintendo|(^|[-_.])(ps[2-5]|psp|psvita|vita)([-_.\d]|$)|playstation|xbox|steam-?deck|(^|[-_.])(oculus|quest)([-_.\d]|$)|(^|[-_.])wii(u)?([-_.\d]|$)", re.I)
V_SERVER  = ("vmware", "super micro", "supermicro", "proxmox")
H_SERVER  = re.compile(r"(^|[-_.])(pve|proxmox|esxi|vcenter|hyperv|docker|k8s|kube|srv|server|node|vm|sql|plex|jellyfin|emby|grafana|nextcloud|gitea|portainer|homeassistant|hass|pihole|pi-hole)([-_.\d]|$)", re.I)
V_VOIP    = ("yealink", "polycom", "fanvil", "snom", "avaya", "mitel", "sangoma", "digium", "obihai", "alcatel-lucent enterprise")
H_VOIP    = re.compile(r"voip|(^|[-_.])sip([-_.\d]|$)|ip-?phone|yealink|polycom|snom|fanvil|asterisk|freepbx|(^|[-_.])(sep|spa)[0-9a-f]{6,}|^gxp\d|^ht\d{3}|^phone[-_]", re.I)
V_UPS     = ("american power conversion", "cyber power", "cyberpower", "tripp lite", "eaton", "riello", "apc ")
H_UPS     = re.compile(r"(^|[-_.])ups([-_.\d]|$)|apc[-_]?\d|^(smt|srt|smx)\d|cyberpower|eaton|powerware|^pdu", re.I)
V_SPEAKER = ("sonos", "bose", "harman", "denon", "marantz", "libratone", "bang & olufsen")
H_SPEAKER = re.compile(r"sonos|homepod|(^|[-_.])echo([-_.\d]|$)|echo[-_ ]?(dot|show|studio|pop|flex)|alexa|google[-_ ]?home|nest[-_ ]?(mini|audio|hub)|bose|soundbar|speaker|airplay|chromecast-?audio", re.I)

# Decide (SO, tipo) sumando puntos por cada pista: fabricante, banner, nombre, puertos abiertos y TTL. Gana el tipo con más puntos; sin pistas suficientes queda «other».
# EN: Decide (OS, type) by adding points for each clue: vendor, banner, name, open ports and TTL. The type with the most points wins; without enough clues it stays "other".
def identify(ip: str, open_ports: list, ttl: int, hostname: str, banner: str,
             vendor: str, mac: str) -> tuple[str, str]:
    """Return (os, device_type) from scored heuristics."""
    ports = set(open_ports)
    host  = (hostname or "").lower().split(".")[0]
    ban   = (banner or "").lower()
    ven   = (vendor or "").lower()
    gw    = (ip == default_gateway())
    web   = bool(ports & {80, 443, 8080, 8443})
    smb   = bool(ports & {445, 139})
    private_mac = mac_is_private(mac)

    # ── Device type scoring ──
    s = {t: 0 for t in DEVICE_TYPES}
    # storage
    if _has(ven, V_STORAGE):                          s["storage"] += 4
    if _has(ban, ("synology", "qnap", "dsm", "openmediavault", "truenas", "nas")): s["storage"] += 4
    if H_STORAGE.search(host):                        s["storage"] += 4
    if ports & {5000, 5001}:                          s["storage"] += 2
    if ports & {2049, 548, 3260, 873}:                s["storage"] += 3
    if smb and ttl and ttl <= 64 and 3389 not in ports and 135 not in ports:
        s["storage"] += 2
    # router
    if gw:                                            s["router"] += 6
    if _has(ven, V_ROUTER):                           s["router"] += 4
    if _has(ban, ("mikrotik", "routeros", "openwrt", "dd-wrt", "pfsense", "opnsense", "fortigate")): s["router"] += 4
    if H_ROUTER.search(host):                         s["router"] += 4
    if ports & {8291, 8728, 7547}:                    s["router"] += 4
    if 53 in ports and web and not smb:               s["router"] += 1
    # access point
    if _has(ven, V_AP):                               s["ap"] += 4
    if _has(ban, ("unifi", "ruckus", "aruba", "cambium", "ubnt")): s["ap"] += 3
    if H_AP.search(host):                             s["ap"] += 5
    # switch
    if H_SWITCH.search(host):                         s["switch"] += 5
    if _has(ban, ("procurve", "switch", "cisco", "netgear gs", "crs")): s["switch"] += 3
    # generic network-gear vendors: need web UI and no general-purpose ports
    if _has(ven, V_NETGEAR) and web and not (ports & {445, 3389, 5900}):
        for t in ("switch",): s[t] += 2
        s["router"] += 1
        s["ap"] += 1
        if "ubiquiti" in ven: s["ap"] += 3
    if ttl > 128 and len(ports) <= 4 and not gw:      s["switch"] += 2
    # computers
    if ports & {3389, 5900} or (22 in ports and not web): s["computer"] += 1
    if H_WIN.search(host) or "iphone" in host or "macbook" in host: s["computer"] += 3
    if "windows" in ban or "microsoft" in ban:        s["computer"] += 3

    # camera
    if _has(ven, V_CAMERA):                           s["camera"] += 4
    if 554 in ports:                                  s["camera"] += 4
    if _has(ban, ("hikvision", "dahua", "ipcam", "netcam", "dnvrs", "app-webs")): s["camera"] += 4
    if H_CAMERA.search(host):                         s["camera"] += 4
    # tv / media
    if _has(ven, V_TV):                               s["tv"] += 3
    if H_TV.search(host):                             s["tv"] += 5
    s["tv"] += 2 * len(ports & {8008, 8009})
    if ports & {8001, 8002}:                          s["tv"] += 4
    # appliance / smart home
    if _has(ven, V_APPL):                             s["appliance"] += 4
    if H_APPL.search(host):                           s["appliance"] += 4
    if 1883 in ports:                                 s["appliance"] += 2

    # printer
    if _has(ven, V_PRINTER):                          s["printer"] += 4
    if H_PRINTER.search(host):                        s["printer"] += 5
    if ports & {9100, 515}:                           s["printer"] += 4
    if 631 in ports:                                  s["printer"] += 3
    if _has(ban, ("printer", "jetdirect", "laserjet", "officejet", "cups", "brother", "lexmark", "xerox", "ricoh")): s["printer"] += 3
    # tablet
    if H_TABLET.search(host):                         s["tablet"] += 5
    # game console (Nintendo, PlayStation, Xbox, Steam Deck, Quest)
    if _has(ven, V_CONSOLE):                          s["console"] += 6
    if H_CONSOLE.search(host):                        s["console"] += 8
    if 3074 in ports:                                 s["console"] += 2
    if ports & {9295, 9296, 9297}:                    s["console"] += 4
    if s["console"] >= 6:                             # «Nintendo-Switch» no es un switch de red / a "Nintendo-Switch" is not a network switch
        s["switch"] = s["tv"] = s["appliance"] = s["tablet"] = 0
    # server / hypervisor / self-hosted services
    if _has(ven, V_SERVER):                           s["server"] += 3
    if H_SERVER.search(host):                         s["server"] += 4
    if 8006 in ports:                                 s["server"] += 5
    if 902 in ports:                                  s["server"] += 3
    if _has(ban, ("proxmox", "esxi", "vmware", "idrac", "supermicro", "cockpit", "portainer")): s["server"] += 4
    if ports & {3306, 5432, 6379, 27017}:             s["server"] += 2
    # IP phone / PBX
    if _has(ven, V_VOIP):                             s["voip"] += 5
    if H_VOIP.search(host):                           s["voip"] += 5
    if ports & {5060, 5061}:                          s["voip"] += 5
    # UPS / power
    if _has(ven, V_UPS):                              s["ups"] += 5
    if H_UPS.search(host):                            s["ups"] += 5
    if 3493 in ports:                                 s["ups"] += 5
    if _has(ban, ("apc", "powernet", "network management card", "eaton", "cyberpower")): s["ups"] += 4
    if "schneider electric" in ven:                   s["ups"] += 3
    # smart speaker
    if _has(ven, V_SPEAKER):                          s["speaker"] += 5
    if H_SPEAKER.search(host):                        s["speaker"] += 6

    best = max(DEVICE_TYPES[:-1], key=lambda t: s[t])
    dtype = best if s[best] >= 4 else ("computer" if s["computer"] >= 1 else "other")

    # ── OS ──
    win_strong = ("windows" in ban or "microsoft" in ban or "iis" in ban or H_WIN.search(host)
                  or "microsoft" in ven)
    if dtype in ("router", "switch", "ap", "tv", "camera", "appliance", "printer", "console", "voip", "ups", "speaker"):
        os_name = "IoT"
    elif dtype == "storage":
        os_name = "Linux"
    elif 62078 in ports or "iphone" in host or "ipad" in host:
        os_name = "iOS"
    elif "apple" in ven or _has(host, ("macbook", "imac", "mac-mini", "macmini", "mac-pro")):
        os_name = "macOS" if not (62078 in ports) else "iOS"
    elif win_strong and (not ttl or ttl > 64 or "windows" in ban):
        os_name = "Windows"
    elif ttl > 64 and ttl <= 128 and (3389 in ports or (135 in ports and smb) or 5357 in ports):
        os_name = "Windows"
    elif ttl > 64 and ttl <= 128 and smb and 22 not in ports:
        os_name = "Windows"
    elif (H_ANDROID.search(host) or _has(ven, V_ANDROID) or 5555 in ports) and 22 not in ports and not smb:
        os_name = "Android"
    elif private_mac and not ports and ttl and ttl <= 64 and (not host or H_ANDROID.search(host)):
        os_name = "Android"
    elif (554 in ports or 1883 in ports or 9100 in ports or 8009 in ports) and 22 not in ports:
        os_name = "IoT"
    elif "freebsd" in ban or "openbsd" in ban:
        os_name = "BSD"
    elif 22 in ports or (ttl and ttl <= 64 and ports):
        os_name = "Linux"
    elif ttl > 128:
        os_name = "IoT"
    elif ttl > 64:
        os_name = "Windows" if ports else "Desconocido"
    else:
        os_name = "Desconocido"

    if dtype == "other" and os_name in ("Windows", "Linux", "macOS", "Android", "iOS"):
        dtype = "computer"
    if os_name in ("Android", "iOS") and dtype in ("computer", "other"):
        dtype = "tablet" if H_TABLET.search(host) else "phone"
    return os_name, dtype

# ─── Scan host completo ───────────────────────────────────────────────────────
# Escanea una IP: si no responde al ping, se descarta. Si responde, junta nombre (Pi-hole o DNS), puertos, banner, MAC y fabricante, y devuelve el registro completo del equipo.
# EN: Scan one IP: if it does not answer ping, it is discarded. If it answers, it gathers name (Pi-hole or DNS), ports, banner, MAC and vendor, and returns the full device record.
def scan_host(ip: str) -> dict | None:
    ip_str = str(ip)
    alive, ttl, latency = ping_ttl(ip_str)
    if not alive:
        return None

    # Pi-hole lookup primero (más confiable que DNS inverso)
    ph        = pihole_lookup(ip_str)
    hostname  = ph.get("hostname") or resolve_dns(ip_str)
    vendor    = ph.get("vendor", "")
    mac       = ph.get("mac", "")

    port_list  = [int(p) for p in SCAN_PORTS.split(",") if p.strip()]
    open_ports = scan_ports(ip_str, port_list)

    # HTTP banner en puertos web abiertos
    banner = ""
    for p in [80, 8080, 443, 8443]:
        if p in open_ports:
            banner = http_banner(ip_str, p)
            if banner: break

    # MAC from the ARP table (the ping just populated it) and vendor from OUI
    if not mac:
        mac = arp_mac(ip_str)
    if not mac:
        with _snmp_lock:
            mac = _snmp_macs.get(ip_str, "")
    if not vendor and mac:
        vendor = oui_vendor(mac)

    os_guess, dev_type = identify(ip_str, open_ports, ttl, hostname, banner, vendor, mac)

    ports_info = [{"port": p, "service": PORT_NAMES.get(p, "unknown")} for p in open_ports]

    return {
        "ip":         ip_str,
        "hostname":   hostname,
        "vendor":     vendor,
        "mac":        mac,
        "os":         os_guess,
        "device_type": dev_type,
        "os_raw":     f"TTL={ttl}" + (f" | {banner[:40]}" if banner else ""),
        "ttl":        ttl,
        "latency":    latency,
        "banner":     banner,
        "ports":      ports_info,
        "online":     True,
        "last_seen":  int(time.time()),
        "first_seen": int(time.time()),
    }

# ─── Persistencia ─────────────────────────────────────────────────────────────
# Equipos de WOL Console (solo lectura): se usa para marcar en la página qué equipos tienen Wake-on-LAN configurado.
# EN: WOL Console devices (read-only): used to mark on the page which devices have Wake-on-LAN configured.
WOL_DEVICES_FILE = Path(os.environ.get("WOL_DEVICES_FILE", str(auth.DATA_ROOT / "wol-console" / "devices.json")))

# MAC reducida a 12 dígitos hexadecimales en minúscula (clave para cruzar con WOL).
# EN: MAC reduced to 12 lowercase hex digits (key to match against WOL).
def _mac_key(raw) -> str:
    h = re.sub(r"[^0-9a-fA-F]", "", raw or "").lower()
    return h if len(h) == 12 else ""

# Conjunto de MAC registradas en WOL Console.
# EN: Set of MACs registered in WOL Console.
def _wol_macs() -> set:
    """MACs registered in WOL Console (shared info, read-only)."""
    d = auth.read_published(WOL_DEVICES_FILE, [], list)        # published by WOL Console: untrusted input
    try:
        return {k for k in (_mac_key(x.get("mac")) for x in d[:5000] if isinstance(x, dict)) if k}
    except Exception:
        return set()

# Lee hosts.json: diccionario ip → registro del equipo.
# EN: Read hosts.json: dictionary of ip → device record.
def load_hosts() -> dict:
    return auth.read_json(DATA_FILE, {}, dict)

# Candado de hosts.json. _live_hosts apunta a la tabla en memoria mientras corre un escaneo, así una edición manual y el escaneo comparten los mismos datos y no se pisan.
# EN: Lock of hosts.json. _live_hosts points to the in-memory table while a scan runs, so a manual edit and the scan share the same data and do not overwrite each other.
_hosts_lock = threading.RLock()
_live_hosts = None   # the scan's in-memory table while a scan runs, so manual edits are not overwritten

# Guarda hosts.json con permisos 0640 (grupo labtower), porque WOL Console (otro proceso) también lo lee.
# EN: Save hosts.json with 0640 permissions (group labtower), because WOL Console (another process) also reads it.
def save_hosts(hosts: dict):
    with _hosts_lock:
        auth.write_json(DATA_FILE, hosts, mode=0o640)   # group labtower: WOL Console reads this file

# ─── Switch Monitor ───────────────────────────────────────────────
# El gestor se crea la primera vez que se usa (importar este archivo no lanza hilos) y se arranca en __main__.
# EN: The manager is created on first use (importing this file starts no threads) and started in __main__.
_sw_mgr = None
_sw_lock = threading.Lock()

# Equipos conocidos por MAC (sin separadores), para mostrar qué hay conectado a cada puerto.
# EN: Known devices by MAC (no separators), to show what is connected to each port.
def _sw_hosts() -> dict:
    out = {}
    for ip, h in load_hosts().items():
        k = _mac_key(h.get("mac"))
        if k: out[k] = {"ip": ip, "name": h.get("alias") or h.get("hostname") or h.get("vendor") or ""}
    return out

def sw_manager():
    global _sw_mgr
    with _sw_lock:
        if _sw_mgr is None:
            _sw_mgr = swmod.Manager(DATA_DIR, hooks={"event": auth.record_event, "changed": auth.state_changed, "hosts": _sw_hosts}, log=log)
        return _sw_mgr

# ─── Scanner ──────────────────────────────────────────────────────────────────
# Estado del escáner (para la barra de progreso), temporizador del próximo escaneo automático e intervalo actual.
# EN: Scanner state (for the progress bar), timer of the next automatic scan and current interval.
_scan_lock        = threading.Lock()
_scan_status      = {"running": False, "progress": 0, "total": 0,
                     "started": None, "finished": None, "error": None}
_scan_timer       = None
_saved            = {}
_current_interval = SCAN_INTERVAL
# Ajustes guardados y modo manual de una instalación nueva. Se ejecuta al arrancar (después de preparar la carpeta de datos), no al importar el módulo.
# EN: Saved settings and the manual mode of a fresh install. It runs at startup (after the data folder is prepared), not when the module is imported.
def init_runtime():
    global _saved, _current_interval, PIHOLE_PASS, PIHOLE_HOSTS
    _saved = load_config()
    _current_interval = _saved.get("scan_interval", SCAN_INTERVAL)
    # Instalación nueva (sin escaneos previos, sin intervalo guardado y sin SCAN_INTERVAL en el entorno): modo manual, no se escanea nada hasta que el usuario lo pida desde la página. Se guarda scan_interval=0 para que los reinicios no vuelvan al escaneo automático.
    # EN: Fresh install (no previous scan, no saved interval and no SCAN_INTERVAL in the environment): manual mode, nothing is scanned until the user asks from the page. scan_interval=0 is saved so restarts do not go back to automatic scanning.
    if "scan_interval" not in _saved and "SCAN_INTERVAL" not in os.environ and not DATA_FILE.exists():
        _current_interval = 0
        try:
            with _cfg_lock:
                _c = load_config(); _c["scan_interval"] = 0; save_config(_c)
        except Exception as _e:
            log.warning(f"could not save the default manual scan mode: {_e}")
    # Cargar credenciales Pi-hole guardadas
    # Credenciales de Pi-hole guardadas desde la página; una variable de entorno tiene prioridad.
    # EN: Pi-hole credentials saved from the page; an environment variable takes priority.
    if not PIHOLE_PASS and _saved.get("pihole_pass"):
        PIHOLE_PASS = _saved["pihole_pass"]
    if _saved.get("pihole_hosts"):
        PIHOLE_HOSTS = _saved["pihole_hosts"]


# Escaneo completo (o de una sola IP). Reserva el escaneo de forma atómica para que dos disparos no corran a la vez, recorre las IP con un pool de hilos y mezcla cada resultado con lo ya conocido:
# conserva alias, tipo y SO editados a mano, MAC/fabricante previos y el historial de conexión/desconexión. Guarda cada 20 equipos y al final. Pase lo que pase deja el estado en «no corriendo» y rearma el temporizador.
# EN: Full scan (or of a single IP). It reserves the scan atomically so two triggers cannot run at once, walks the IPs with a thread pool and merges each result with what is already known:
#     it keeps hand-edited alias, type and OS, previous MAC/vendor and the connect/disconnect history. It saves every 20 devices and at the end. Whatever happens it leaves the state as "not running" and re-arms the timer.
# Anota en la línea de tiempo del Resumen lo que cambió en un escaneo: hosts nuevos, que volvieron o que dejaron de responder.
# El primer escaneo se resume en una sola línea; si hay más de 5 cambios del mismo tipo se agrupan en un evento.
# EN: Record on the Overview timeline what a scan changed: new hosts, hosts back or no longer answering.
#     The first scan is summarised in one line; more than 5 changes of the same kind are grouped into one event.
def _record_scan_events(changes, first_inventory, online, single_ip=None):
    try:
        if first_inventory:
            if online: auth.record_event("net", "info", f"First scan: {online} hosts found", "net_first", n=online)
            return
        label = {"new": ("warn", "New device"), "up": ("info", "Back online"), "down": ("info", "Went offline")}
        for kind in ("new", "up", "down"):
            items = [(ip, h) for k, ip, h in changes if k == kind]
            if not items: continue
            lv, txt = label[kind]
            if len(items) > 5:
                auth.record_event("net", lv, f"{txt}: {len(items)} hosts", f"net_{kind}_n", n=len(items))
                continue
            for ip, h in items:
                name = h.get("alias") or h.get("hostname") or ""
                extra = h.get("vendor") or "" if kind == "new" else ""
                auth.record_event("net", lv, f"{txt}: {ip}" + (f" ({name})" if name else "") + (f" {extra}" if extra else ""),
                                  f"net_{kind}", ip=ip, n=name, v=extra)
    except Exception as e:
        log.debug(f"scan events: {e}")

# Elimina los equipos que llevan más de `days` días sin responder (0 = nunca). Se usa la última vez que se vieron conectados.
# EN: Remove devices that have not answered for more than `days` days (0 = never). Uses the last time they were seen online.
def purge_offline(hosts: dict, days: int, now: float = None) -> list:
    if not days or days < 1: return []
    now = now or time.time()
    gone = [ip for ip, h in hosts.items()
            if isinstance(h, dict) and not h.get("online") and isinstance(h.get("last_seen"), (int, float)) and now - h["last_seen"] > days * 86400]
    for ip in gone: del hosts[ip]
    return gone

def run_scan(network: str = None, single_ip: str = None):
    global _live_hosts
    with _scan_lock:                      # reserve the scan atomically: two triggers can't both start
        if _scan_status["running"]:
            return
        _scan_status.update({"running": True, "progress": 0, "total": 0,
                             "started": int(time.time()), "finished": None, "error": None})
    try:
        if single_ip:
            ips = [ipaddress.ip_address(single_ip)]
        else:
            ips = list(ipaddress.ip_network(network or NETWORK, strict=False).hosts())
        with _hosts_lock:
            hosts = load_hosts()
            _live_hosts = hosts
        refresh_snmp()
        oui_maybe_update()
    except Exception as e:
        log.error(f"Scan setup failed: {e}")
        with _hosts_lock: _live_hosts = None
        _scan_status.update({"running": False, "error": str(e), "finished": int(time.time())})
        if not single_ip: _schedule_next_scan()
        return

    _scan_status.update({"total": len(ips)})
    log.info(f"Starting scan: {len(ips)} hosts in {network or NETWORK}")
    _scan_events = []                    # changes found by this scan: ("new"|"up"|"down", ip, host)
    first_inventory = not hosts          # first scan ever: every host is "new", so it is summarised instead

    # Trabajo de cada hilo del pool: escanear una IP.
    # EN: Job of each pool thread: scan one IP.
    def scan_one(ip):
        return str(ip), scan_host(str(ip))

    try:
        completed = 0
        _last_save = 0.0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = {ex.submit(scan_one, ip): ip for ip in ips}
            for future in as_completed(futures):
                completed += 1
                _scan_status["progress"] = completed
                found = False
                try:
                    ip_str, result = future.result()
                    found = bool(result)
                    with _hosts_lock:
                        if result:
                            existing = hosts.get(ip_str, {})
                            is_new = ip_str not in hosts
                            result["first_seen"] = existing.get("first_seen", result["first_seen"])
                            result["alias"]      = existing.get("alias", "")
                            # Marcar como "nuevo" si nunca se vio antes o apareció en últimas 48h
                            new_threshold = int(time.time()) - 48 * 3600
                            result["new_device"] = is_new or (result["first_seen"] > new_threshold and is_new)
                            # Respetar latencia anterior si ahora no hay datos
                            if result.get("latency", 0) == 0 and existing.get("latency", 0) > 0:
                                result["latency"] = existing["latency"]
                            # Keep MAC/vendor from earlier scans when this one found none
                            for k in ("mac", "vendor"):
                                if not result.get(k) and existing.get(k):
                                    result[k] = existing[k]
                            # Keep manually chosen device type
                            if existing.get("type_manual"):
                                result["device_type"] = existing.get("device_type", result["device_type"])
                                result["type_manual"] = True
                            # Respetar OS editado manualmente
                            if existing.get("os_manual"):
                                result["os"]        = existing["os"]
                                result["os_manual"] = True
                            # Historial de disponibilidad: registrar evento si cambió estado
                            history = existing.get("uptime_history", [])
                            was_online = existing.get("online", False)
                            if not was_online and result["online"]:
                                history.append({"ts": int(time.time()), "event": "up"})
                            history = history[-200:]  # max 200 eventos
                            result["uptime_history"] = history
                            hosts[ip_str] = result
                            if is_new:
                                _scan_events.append(("new", ip_str, result))
                            elif not was_online and result["online"]:
                                _scan_events.append(("up", ip_str, result))
                            log.debug(f"[{completed}/{len(ips)}] {ip_str} → {result['os']} | TTL={result['ttl']} | {len(result['ports'])} puertos")
                        else:
                            if ip_str in hosts:
                                if hosts[ip_str].get("online"):  # was online, now offline
                                    _scan_events.append(("down", ip_str, hosts[ip_str]))
                                    history = hosts[ip_str].get("uptime_history", [])
                                    history.append({"ts": int(time.time()), "event": "down"})
                                    hosts[ip_str]["uptime_history"] = history[-200:]
                                hosts[ip_str]["online"] = False
                                hosts[ip_str]["last_seen_offline"] = int(time.time())
                except Exception as e:
                    log.error(f"Scan error: {e}")

                # Guardado parcial: si el servicio se corta a mitad de escaneo, no se pierde todo. Además, cada equipo encontrado se guarda enseguida (como máximo una vez cada 2 s) para que la página vaya mostrando la lista mientras el escaneo avanza, sin esperar a que termine toda la red.
                # EN: Partial save: if the service stops mid-scan, not everything is lost. In addition, each device found is saved right away (at most once every 2 s) so the page fills the list as the scan advances, without waiting for the whole network to finish.
                if (found and time.time() - _last_save >= 2) or completed % 20 == 0:
                    save_hosts(hosts); _last_save = time.time()

        with _hosts_lock:
            try:
                gone = purge_offline(hosts, int(load_config().get("purge_days", 0) or 0))
                if gone: log.info(f"Removed {len(gone)} devices offline for too long")
            except Exception as e: log.debug(f"purge: {e}")
            save_hosts(hosts)
            _live_hosts = None
        online = sum(1 for h in hosts.values() if h.get("online"))
        _record_scan_events(_scan_events, first_inventory, online, single_ip)
        _scan_status.update({"running": False, "finished": int(time.time())})
        log.info(f"Scan finished: {online} hosts online out of {len(ips)} scanned")

    except BaseException as e:
        with _hosts_lock: _live_hosts = None
        _scan_status.update({"running": False, "error": str(e), "finished": int(time.time())})
        log.error(f"Scan failed: {e}")
    finally:
        with _hosts_lock: _live_hosts = None
        _scan_status["running"] = False                   # never leave the scanner "running"
        if not single_ip:                                 # a one-host rescan must not stack another timer
            _schedule_next_scan()

# Arma el único temporizador de escaneo automático (cancela el anterior). Con intervalo 0 el modo es manual.
# EN: Arm the single automatic-scan timer (cancelling the previous one). With interval 0 the mode is manual.
def _schedule_next_scan():
    """(Re)arm the single automatic-scan timer."""
    global _scan_timer
    with _scan_lock:
        if _scan_timer:
            _scan_timer.cancel(); _scan_timer = None
        if _current_interval > 0:
            _scan_timer = threading.Timer(
                _current_interval,
                lambda: threading.Thread(target=run_scan, daemon=True).start()
            )
            _scan_timer.daemon = True
            _scan_timer.start()
            log.info(f"Next scan in {_current_interval//60} minutes")
        else:
            log.info("Auto-scan disabled (manual mode)")

# Al arrancar: carga la caché de Pi-hole y lanza el primer escaneo en segundo plano.
# EN: On startup: load the Pi-hole cache and launch the first scan in the background.
def start_auto_scan():
    # Cargar cache de Pi-hole antes del primer escaneo
    if PIHOLE_PASS:
        threading.Thread(target=refresh_pihole_cache, daemon=True).start()
    # Con intervalo 0 (modo manual) no se escanea al arrancar: solo cuando el usuario lo pide.
    # EN: With interval 0 (manual mode) nothing is scanned at startup: only when the user asks.
    if _current_interval > 0:
        threading.Thread(target=run_scan, daemon=True).start()
    else:
        log.info("Auto-scan disabled (manual mode): no scan at startup")

# ─── Health ───────────────────────────────────────────────────────────────────
# Chequeos de salud de Net Monitor: archivos de datos, escáner (¿atascado más de 2 h?) y que el temporizador automático esté armado y al día.
# EN: Net Monitor health checks: data files, scanner (stuck for more than 2 h?) and that the automatic timer is armed and up to date.
def health_report(detailed=False):
    c = auth.check_common()
    c["hosts_file"]  = auth.check_file(DATA_FILE)
    c["config_file"] = auth.check_file(CONF_FILE)
    now = time.time(); st = dict(_scan_status)
    if st.get("running"):
        age = now - (st.get("started") or now)
        c["scanner"] = (auth.chk(auth.FAIL, f"scan running for {int(age)} s ({st.get('progress')}/{st.get('total')})")
                        if age > 7200 else auth.chk(auth.OK, f"scanning {st.get('progress')}/{st.get('total')}"))
    elif st.get("error"):
        c["scanner"] = auth.chk(auth.WARN, f"last scan failed: {st['error']}")
    else:
        c["scanner"] = auth.chk(auth.OK, "idle")
    iv = _current_interval
    if iv > 0:
        t = _scan_timer
        armed = (t is not None and t.is_alive()) or st.get("running")
        fin = st.get("finished")
        if not armed:
            c["auto_scan"] = auth.chk(auth.FAIL, "auto-scan is enabled but no timer is armed")
        elif fin and now - fin > 2 * iv + 600:
            c["auto_scan"] = auth.chk(auth.WARN, f"last scan finished {int(now - fin)} s ago (interval {iv} s)")
        else:
            c["auto_scan"] = auth.chk(auth.OK, f"every {iv} s")
    else:
        c["auto_scan"] = auth.chk(auth.OK, "manual mode")
    try:
        cfgs = [x for x in sw_manager().list_config()["switches"] if x.get("enabled", True)]
        if cfgs:
            st = {x["id"]: x for x in sw_manager().state()["switches"]}
            bad = [x["name"] for x in cfgs if not st.get(x["id"], {}).get("online")]
            c["switches"] = (auth.chk(auth.WARN, f"{len(bad)} of {len(cfgs)} switches unreachable: {', '.join(bad)[:120]}") if bad
                             else auth.chk(auth.OK, f"{len(cfgs)} switches reachable"))
    except Exception as e:
        c["switches"] = auth.chk(auth.WARN, f"switch monitor: {str(e)[:100]}")
    return auth.health_reply("net", c, detailed)

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
            d = json.loads(self.rfile.read(n))
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

    # GET: página, versión y salud son públicos; el resto exige sesión con Net «readonly».
    # Rutas: /api/hosts, /api/snmp, /api/oui, /api/scan/status, /api/config, /api/me.
    # EN: GET: page, version and health are public; the rest requires a session with Net "readonly".
    #     Routes: /api/hosts, /api/snmp, /api/oui, /api/scan/status, /api/config, /api/me.
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

        if not auth.check_permission(tok, "net", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        # Lista de equipos con el estado del escaneo. Si el usuario tiene acceso a WOL, marca los que ya están configurados allí.
        # EN: List of devices with the scan state. If the user has WOL access, it marks the ones already configured there.
        if path == "/api/hosts":
            hosts = load_hosts()
            out = list(hosts.values())
            if auth.check_permission(tok, "wol", "readonly"):
                wol = _wol_macs()
                for h in out:
                    k = _mac_key(h.get("mac"))
                    if k and k in wol: h["wol"] = True
            self._json(200, {
                "hosts":   out,
                "scan":    _scan_status,
                "network": NETWORK,
            })
        # Switch Monitor: estado de todos los switches, resumen para el Resumen, configuración (sin secretos) e historial.
        # EN: Switch Monitor: state of all switches, summary for the Overview, configuration (no secrets) and history.
        elif path == "/api/switches":
            self._json(200, sw_manager().state())
        elif path == "/api/switches/summary":
            self._json(200, sw_manager().summary())
        elif path == "/api/switches/macs":
            self._json(200, sw_manager().macs())
        elif path == "/api/switches/totals":
            self._json(200, sw_manager().totals())
        elif path == "/api/switches/config":
            self._json(200, sw_manager().list_config())
        elif re.fullmatch(r"/api/switches/[a-z0-9-]+/history", path):
            q = parse_qs(urlparse(self.path).query)
            rng = (q.get("range") or ["1d"])[0]
            port = (q.get("port") or [None])[0]
            if rng not in ("1h", "1d", "1w", "1mo", "all") or (port is not None and not port.isdigit()):
                return self._json(400, {"error": "Invalid range or port"})
            self._json(200, sw_manager().history(path.split("/")[3], rng, port))
        elif path == "/api/snmp":
            with _snmp_lock:
                st = dict(_snmp_status)
            self._json(200, {"config": snmp_config(), "available": bool(shutil.which("snmpwalk")), "status": st})

        elif path == "/api/oui":
            _load_oui()
            self._json(200, {"count": _oui_status["count"], "source": _oui_status["source"],
                             "updated": _oui_status["ts"], "error": _oui_status["error"],
                             "auto": load_config().get("oui", {}).get("auto", True)})

        elif path == "/api/scan/status":
            self._json(200, _scan_status)

        # Configuración de Pi-hole y del intervalo (la primera definición es la que se usa; la siguiente nunca se alcanza).
        # EN: Pi-hole and interval configuration (the first definition is the one used; the next is never reached).
        elif path == "/api/config":
            cfg = load_config()
            self._json(200, {
                "scan_interval":   _current_interval,
                "purge_days":      int(cfg.get("purge_days", 0) or 0),
                "network":         NETWORK,
                "pihole_hosts":    PIHOLE_HOSTS,
                "pihole_enabled":  bool(PIHOLE_PASS or cfg.get("pihole_pass")),
                "pihole_cache_ts": _pihole_ts,
                "pihole_entries":  len(_pihole_cache),
            })

        # Ruta duplicada heredada: queda inalcanzable, se conserva para no cambiar el código.
        # EN: Inherited duplicate route: unreachable, kept so the code is not changed.
        elif path == "/api/config":
            self._json(200, {
                "network":       NETWORK,
                "scan_interval": _current_interval,
                "scan_ports":    SCAN_PORTS,
                "max_workers":   MAX_WORKERS,
            })
        elif path == "/api/me":
            sess = auth.get_session(tok)
            self._json(200, {"username": sess["username"],
                              "permissions": sess["permissions"]} if sess else {})
        else:
            self._json(404, {"error": "Not found"})

    # POST: login/logout, iniciar escaneo y, solo para admin, OUI, SNMP, Pi-hole, editar/borrar equipos e intervalo.
    # Orden: login (público) → exigir sesión → rutas protegidas.
    # EN: POST: login/logout, start scan and, for admin only, OUI, SNMP, Pi-hole, edit/delete devices and interval.
    #     Order: login (public) → require a session → protected routes.
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

        if not auth.check_permission(tok, "net", "readonly"):
            return self._json(401, {"error": "Unauthorized"})

        # Inicia un escaneo completo o de una sola IP (409 si ya hay uno corriendo).
        # EN: Start a full scan or one of a single IP (409 if one is already running).
        if path == "/api/scan/start":
            if not auth.check_permission(tok, "net", "execute"):
                return self._json(403, {"error": "Execute permission required"})
            if _scan_status["running"]:
                return self._json(409, {"error": "Scan already running"})
            single = str(body.get("ip") or "").strip() or None
            if single:
                try: ip_obj = ipaddress.ip_address(single)
                except ValueError: return self._json(400, {"error": "Invalid IP"})
                # Solo equipos de la red escaneada: así el servidor no sirve para sondear Internet ni ella misma (127.0.0.1, 169.254.x).
                # EN: Only hosts of the scanned network: so the server cannot be used to probe the Internet or itself (127.0.0.1, 169.254.x).
                if ip_obj.version != ipaddress.ip_network(NETWORK, strict=False).version or ip_obj not in ipaddress.ip_network(NETWORK, strict=False):
                    return self._json(400, {"error": "IP outside the scanned network"})
            threading.Thread(target=run_scan, kwargs={"single_ip": single}, daemon=True).start()
            self._json(200, {"ok": True, "message": single or NETWORK})

        # OUI: activar/desactivar la actualización automática o forzar la descarga ahora (admin).
        # EN: OUI: enable/disable the automatic update or force the download now (admin).
        elif path in ("/api/oui", "/api/oui/update"):
            if not auth.check_permission(tok, "net", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            if path == "/api/oui":
                cfg = load_config(); cfg.setdefault("oui", {})["auto"] = bool(body.get("auto", True))
                save_config(cfg)
                return self._json(200, {"ok": True})
            try:
                res = oui_update(); _oui_status["error"] = ""
                return self._json(200, {"ok": True, **res})
            except Exception as e:
                _oui_status["error"] = str(e)[:200]
                return self._json(502, {"error": str(e)[:200]})

        # Switch Monitor: «actualizar ahora» (cualquiera con acceso a Net) y, solo admin, guardar, borrar, probar, etiquetar puertos
        # y cambiar el intervalo. Las contraseñas nunca se devuelven.
        # EN: Switch Monitor: "refresh now" (anyone with Net access) and, admin only, save, delete, test, label ports and change
        #     the interval. Passwords are never returned.
        elif path == "/api/switches/refresh":
            return self._json(200, {"ok": True, "n": sw_manager().refresh(body.get("id") or None)})
        elif path.startswith("/api/switches/"):
            if not auth.check_permission(tok, "net", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            m, act = sw_manager(), path[len("/api/switches/"):]
            try:
                if act == "save":
                    return self._json(200, {"ok": True, "switch": m.save_switch(body)})
                if act == "delete":
                    m.delete_switch(str(body.get("id") or ""))
                    return self._json(200, {"ok": True})
                if act == "test":
                    return self._json(200, m.test(body))
                if act == "port":
                    m.set_port_meta(str(body.get("id") or ""), body.get("port"), body.get("label", ""), bool(body.get("uplink")), bool(body.get("watch")))
                    return self._json(200, {"ok": True})
                if act == "poll":
                    m.set_poll(body.get("seconds"))
                    return self._json(200, {"ok": True})
            except ValueError as e:
                return self._json(400, {"error": str(e)})
            except Exception as e:
                log.warning(f"switches/{act}: {e}")
                return self._json(502, {"error": f"{type(e).__name__}: {e}"[:200]})
            return self._json(404, {"error": "Not found"})

        # SNMP: guardar la configuración o solo probarla sin guardar (admin).
        # EN: SNMP: save the configuration or only test it without saving (admin).
        elif path in ("/api/snmp", "/api/snmp/test"):
            if not auth.check_permission(tok, "net", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            try:
                cfg = snmp_validate(body, snmp_config(include_secrets=True))
            except ValueError as e:
                return self._json(400, {"error": str(e)})
            if path == "/api/snmp/test":
                if not cfg["host"]:
                    return self._json(400, {"error": "Host required"})
                try:
                    res = snmp_fetch_arp(cfg)
                except Exception as e:
                    return self._json(502, {"error": str(e)})
                sample = [{"ip": k, "mac": v} for k, v in list(res.items())[:5]]
                return self._json(200, {"ok": True, "count": len(res), "sample": sample})
            allcfg = load_config()
            allcfg["snmp"] = cfg
            save_config(allcfg)
            try: os.chmod(CONF_FILE, 0o600)
            except Exception: pass
            if cfg["enabled"]:
                threading.Thread(target=refresh_snmp, daemon=True).start()
            else:
                with _snmp_lock:
                    _snmp_macs.clear()
            self._json(200, {"ok": True})

        # Guarda la contraseña y los hosts de Pi-hole y refresca la caché de inmediato (admin).
        # EN: Save the Pi-hole password and hosts and refresh the cache immediately (admin).
        elif path == "/api/pihole/config":
            if not auth.check_permission(tok, "net", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            global PIHOLE_PASS, PIHOLE_HOSTS
            if "password" in body and (not isinstance(body["password"], str) or len(body["password"]) > 256):
                return self._json(400, {"error": "Invalid password"})
            if "hosts" in body:
                hl = [h.strip() for h in str(body["hosts"]).split(",") if h.strip()] if isinstance(body["hosts"], str) else None
                if hl is None or len(hl) > 5 or not all(PIHOLE_HOST_RE.match(h) for h in hl):
                    return self._json(400, {"error": "Invalid Pi-hole host (name or IP, optional :port; up to 5, comma separated)"})
                body["hosts"] = ",".join(hl)
            with _cfg_lock:
                cfg = load_config()
                if "password" in body:
                    PIHOLE_PASS = body["password"]
                    cfg["pihole_pass"] = body["password"]
                if "hosts" in body:
                    PIHOLE_HOSTS = body["hosts"]
                    cfg["pihole_hosts"] = body["hosts"]
                cfg.pop("pihole_pins", None)          # saving again = the administrator accepts the current certificates
                save_config(cfg)
            # Refrescar cache inmediatamente
            if PIHOLE_PASS:
                threading.Thread(target=refresh_pihole_cache, daemon=True).start()
            self._json(200, {"ok": True})

        # Edita alias, SO, tipo o grupo de un equipo (admin). Lo editado a mano queda marcado para que los siguientes escaneos no lo sobrescriban.
        # EN: Edit alias, OS, type or group of a device (admin). What is edited by hand is flagged so later scans do not overwrite it.
        elif path == "/api/hosts/update":
            if not auth.check_permission(tok, "net", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            ip = str(body.get("ip") or "").strip()
            if not ip: return self._json(400, {"error": "IP required"})
            dt = None
            if "device_type" in body:
                dt = str(body["device_type"])
                if dt != "auto" and dt not in DEVICE_TYPES:
                    return self._json(400, {"error": "Invalid device type"})
            with _hosts_lock:
                hosts = _live_hosts if _live_hosts is not None else load_hosts()
                if ip not in hosts: return self._json(404, {"error": "Host not found"})
                h = hosts[ip]
                if "alias" in body:
                    h["alias"] = str(body["alias"])[:40]
                if "os" in body:
                    os_v = str(body["os"]).strip()[:30]
                    if not re.fullmatch(r"[\w .+/()-]{1,30}", os_v):
                        return self._json(400, {"error": "Invalid OS name"})
                    h["os"]        = os_v
                    h["os_manual"] = True   # marked as manually edited
                if dt is not None:
                    if dt == "auto":
                        h.pop("type_manual", None)   # back to auto-detection on next scan
                    else:
                        h["device_type"] = dt
                        h["type_manual"] = True
                if "group" in body:
                    grp = str(body["group"]).strip()[:20]
                    if grp and not re.fullmatch(r"[\w .+/()-]{1,20}", grp):
                        return self._json(400, {"error": "Invalid group name"})
                    h["group"] = grp
                save_hosts(hosts)
            self._json(200, {"ok": True})

        # Cambia el intervalo de escaneo automático (mínimo 60 s, 0 = solo manual) y rearma el temporizador (admin).
        # EN: Change the automatic scan interval (minimum 60 s, 0 = manual only) and re-arm the timer (admin).
        elif path == "/api/scan/interval":
            if not auth.check_permission(tok, "net", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            global _current_interval
            try: interval = int(body.get("interval", 3600))
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid interval"})
            if interval < 0 or (interval > 0 and interval < 60):
                return self._json(400, {"error": "Minimum 60 seconds or 0 for manual"})
            _current_interval = interval
            with _cfg_lock:                       # merge: don't wipe the SNMP / OUI / Pi-hole settings
                cfg = load_config(); cfg["scan_interval"] = interval
                save_config(cfg)
            _schedule_next_scan()
            self._json(200, {"ok": True, "interval": interval})

        # Días sin conexión tras los cuales un equipo se elimina solo de la lista (0 = nunca) (admin).
        # EN: Days offline after which a device is removed from the list by itself (0 = never) (admin).
        elif path == "/api/hosts/purge":
            if not auth.check_permission(tok, "net", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            try: days = int(body.get("days", 0))
            except (TypeError, ValueError): return self._json(400, {"error": "Invalid days"})
            if days < 0 or days > 3650: return self._json(400, {"error": "Days must be 0 (never) to 3650"})
            with _cfg_lock:
                cfg = load_config(); cfg["purge_days"] = days; save_config(cfg)
            removed = 0
            if days and not _scan_status.get("running"):
                with _hosts_lock:
                    hosts = load_hosts(); gone = purge_offline(hosts, days)
                    if gone: save_hosts(hosts)
                    removed = len(gone)
            self._json(200, {"ok": True, "days": days, "removed": removed})

        # Elimina un equipo de la lista (admin). Si sigue conectado, el próximo escaneo lo vuelve a descubrir.
        # EN: Remove a device from the list (admin). If it is still connected, the next scan discovers it again.
        elif path == "/api/hosts/delete":
            if not auth.check_permission(tok, "net", "admin"):
                return self._json(403, {"error": "Admin permission required"})
            ip = str(body.get("ip") or "").strip()
            with _hosts_lock:
                hosts = _live_hosts if _live_hosts is not None else load_hosts()
                if ip in hosts: del hosts[ip]; save_hosts(hosts)
            self._json(200, {"ok": True})

        else:
            self._json(404, {"error": "Not found"})

# Arranque: completa el permiso «net» de usuarios antiguos (una vez), lanza el primer escaneo y sirve en loopback.
# EN: Startup: fills in the "net" permission of old users (once), launches the first scan and serves on loopback.
if __name__ == "__main__":
    auth.prepare_module(DATA_DIR, Path(__file__).parent, LEGACY_FILES)
    init_runtime()
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    # Explicit 'net' level for users that predate the module (one-time migration)
    try:
        if auth.ensure_permissions(("net",)): log.info("'net' permissions updated")
    except Exception as e:
        log.warning(f"Could not update permissions: {e}")

    log.info(f"Net Monitor at http://{HOST}:{PORT}")
    log.info(f"Network: {NETWORK} | Workers: {MAX_WORKERS} | Auto-scan: {_current_interval//60}min (0 = manual)")
    log.info("Detection: TTL + Python ports + HTTP banner (no nmap)")
    start_auto_scan()
    try: sw_manager().start()
    except Exception as e: log.warning(f"Switch Monitor did not start: {e}")
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
