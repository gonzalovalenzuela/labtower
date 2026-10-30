#!/usr/bin/env python3
"""
WAN Monitor — salud de la conexión a Internet: latencia, pérdida, cortes, IP pública y velocidad / Internet connection health
"""
# WAN Monitor (puerto 8088): vigila la conexión a Internet desde este equipo. Cada pocos segundos hace ping (o conexión TCP) a varios destinos
# y a la puerta de enlace, mide la resolución de un nombre DNS y guarda latencia, jitter y pérdida; registra los cortes (con su duración y si el fallo
# fue de la red local o de Internet), avisa si cambia la IP pública y mide la velocidad de bajada y subida con un servidor compatible con Cloudflare.
#
# Flujo de datos:
#   un hilo «sonda» → probe_round() → WanState guarda la última lectura, el historial y los cortes → la página la pide a /api/wan.
#   Otro hilo revisa cada minuto si toca medir la velocidad según la programación (o si alguien pulsó «Medir ahora»).
#
# Notas: la velocidad es la que ESTE equipo alcanza hacia el servidor de prueba; una máquina pequeña puede quedar por debajo de una línea gigabit. Durante la
# medición se pausan las sondas para que la línea saturada no cuente como un corte. La medición consume ancho de banda: por eso es programable.
#
# Estructura: configuración · sondas · velocidad · estado, cortes e historial · hilos · salud · HTTP.
# EN: WAN Monitor (port 8088): watches the Internet connection from this machine. Every few seconds it pings (or opens a TCP connection to) several
#     targets and the gateway, times a DNS name resolution and stores latency, jitter and loss; it records outages (with duration and whether the
#     local network or the Internet failed), warns when the public IP changes and measures download and upload speed against a Cloudflare-compatible server.
#
#     Data flow:
#       one "probe" thread → probe_round() → WanState keeps the last reading, the history and the outages → the page requests it from /api/wan.
#       Another thread checks every minute whether a speed test is due by schedule (or whether someone pressed "Measure now").
#
#     Notes: the speed is what THIS machine reaches toward the test server; a small machine can fall below a gigabit line. Probes are paused during
#     the measurement so the saturated line does not count as an outage. The measurement uses bandwidth: that is why it is schedulable.
#
#     Structure: configuration · probes · speed · state, outages and history · threads · health · HTTP.
import http.client, ipaddress, json, os, re, shutil, socket, ssl, subprocess, sys, time, logging, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ThreadingHTTPServer.request_queue_size = 128
from urllib.parse import urlparse, parse_qs
from collections import deque as _deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "auth"))
import auth

HOST       = "127.0.0.1"
PORT       = 8088
STATIC_DIR = Path(__file__).parent / "static"
DATA_DIR   = auth.module_dir("wan-monitor")
LEGACY_FILES = ()
DATA_FILE  = DATA_DIR / "wan.json"
STATE_FILE = DATA_DIR / "state.json"                       # last known public IP and when it changed
HIST_KEEP  = auth.keep_days("WAN_KEEP_DAYS", 30) * 86400
_HIST_MAX  = 1500                                          # ~12 h at 30 s
DOWN_AFTER = 2                                             # failed rounds in a row before declaring an outage
IP_EVERY   = 600                                           # public IP check period (s)
_STARTED   = time.time()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("wan")

# ─── Configuración ────────────────────────────────────────────────────────────
DEFAULTS = {
    "targets": [{"host": "1.1.1.1", "kind": "ping"}, {"host": "8.8.8.8", "kind": "ping"}, {"host": "9.9.9.9", "kind": "ping"}],
    "gateway": "auto",                    # "auto" (default route), "" (off) or an IP
    "dns_name": "cloudflare.com",         # name resolved with the system resolver ("" = off)
    "interval": 30,                       # seconds between rounds
    "ip_url": "https://api.ipify.org",    # returns the public IP as plain text ("" = off)
    "speed": {"enabled": True, "every_hours": 12, "down_url": "https://speed.cloudflare.com/__down", "up_url": "https://speed.cloudflare.com/__up",
              "seconds": 8, "streams": 4, "upload": True, "engine": "builtin"},
}
_cfg_lock = threading.RLock()
# Motores de la prueba de velocidad: el integrado (Cloudflare) y, si están instalados, los programas Ookla y LibreSpeed para contrastar.
# EN: Speed test engines: the built-in one (Cloudflare) and, when installed, the Ookla and LibreSpeed programs to cross-check.
ENGINES = {"builtin": None, "ookla": "speedtest", "librespeed": "librespeed-cli"}
def engines_available():
    return {k: (b is None or bool(shutil.which(b))) for k, b in ENGINES.items()}

def _https_url(u, what):
    u = str(u or "").strip()
    p = urlparse(u)
    if p.scheme != "https" or p.username or p.password or not auth.valid_host(p.hostname or ""): raise ValueError(f"{what} must be an https:// address")
    try: p.port
    except ValueError: raise ValueError(f"Invalid port in {what}")
    if len(u) > 300 or re.search(r"[\x00-\x20\x7f]", u): raise ValueError(f"Invalid {what}")
    return u

def _int(v, lo, hi, what):
    try: v = int(v)
    except (TypeError, ValueError): raise ValueError(f"Invalid {what}")
    if not lo <= v <= hi: raise ValueError(f"{what} must be {lo}-{hi}")
    return v

# Combina lo recibido con lo guardado y valida cada campo.
# EN: Merge what arrived with what is stored and validate every field.
def validate(body: dict, current=None) -> dict:
    cfg = json.loads(json.dumps(current or DEFAULTS))
    for k in ("targets", "gateway", "dns_name", "interval", "ip_url"):
        if k in body: cfg[k] = body[k]
    if isinstance(body.get("speed"), dict): cfg["speed"].update(body["speed"])
    tg = cfg["targets"]
    if not isinstance(tg, list) or not 1 <= len(tg) <= 6: raise ValueError("Between 1 and 6 targets")
    out = []
    for t in tg:
        if not isinstance(t, dict): raise ValueError("Invalid target")
        host, kind = str(t.get("host") or "").strip(), str(t.get("kind") or "ping")
        if not auth.valid_host(host): raise ValueError("Invalid target host")
        if kind not in ("ping", "tcp"): raise ValueError("Invalid target type")
        item = {"host": host, "kind": kind}
        if kind == "tcp": item["port"] = _int(t.get("port", 443), 1, 65535, "port")
        if any(o["host"] == host and o["kind"] == kind and o.get("port") == item.get("port") for o in out): raise ValueError("Repeated target")
        out.append(item)
    cfg["targets"] = out
    gw = str(cfg.get("gateway") or "").strip()
    if gw not in ("", "auto"):
        try: ipaddress.ip_address(gw)
        except ValueError: raise ValueError("Gateway must be auto, empty or an IP")
    cfg["gateway"] = gw
    dn = str(cfg.get("dns_name") or "").strip()
    if dn and not auth.valid_host(dn): raise ValueError("Invalid DNS name")
    cfg["dns_name"] = dn
    cfg["interval"] = _int(cfg["interval"], 10, 300, "Interval")
    iu = str(cfg.get("ip_url") or "").strip()
    cfg["ip_url"] = _https_url(iu, "IP address service") if iu else ""
    sp = cfg["speed"]
    sp["enabled"], sp["upload"] = bool(sp.get("enabled")), bool(sp.get("upload"))
    if sp.get("engine", "builtin") not in ENGINES: raise ValueError("Unknown speed test engine")
    sp["engine"] = sp.get("engine", "builtin")
    sp["every_hours"] = _int(sp.get("every_hours", 12), 0, 720, "Speed test period")
    sp["seconds"] = _int(sp.get("seconds", 8), 3, 20, "Speed test duration")
    sp["streams"] = _int(sp.get("streams", 4), 1, 8, "Streams")
    sp["down_url"] = _https_url(sp.get("down_url"), "Download address")
    sp["up_url"] = _https_url(sp.get("up_url"), "Upload address")
    return cfg

def load_config() -> dict:
    cur = auth.read_json(DATA_FILE, {}, dict)
    try: return validate(cur) if cur else validate({})
    except ValueError as e:
        log.warning(f"stored configuration invalid ({e}); using defaults"); return validate({})

def save_config(cfg: dict):
    with _cfg_lock: auth.write_json(DATA_FILE, cfg)

# Puerta de enlace IPv4 predeterminada, leída de /proc/net/route.
# EN: Default IPv4 gateway, read from /proc/net/route.
def default_gateway(path="/proc/net/route"):
    try:
        for line in Path(path).read_text().splitlines()[1:]:
            f = line.split()
            if len(f) >= 4 and f[1] == "00000000" and int(f[3], 16) & 2:
                return socket.inet_ntoa(int(f[2], 16).to_bytes(4, "little"))
    except (OSError, ValueError): pass
    return None

# ─── Sondas ───────────────────────────────────────────────────────────────────
_RE_SENT = re.compile(r"(\d+) packets transmitted, (\d+) (?:packets )?received")
_RE_RTT  = re.compile(r"= ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms")

# Ping con 3 paquetes. Devuelve {sent, recv, loss, rtt, jitter}; nunca lanza excepción.
# EN: Ping with 3 packets. Returns {sent, recv, loss, rtt, jitter}; never raises.
def ping(host, count=3, timeout=2):
    exe = shutil.which("ping")
    res = {"sent": count, "recv": 0, "loss": 100.0, "rtt": None, "jitter": None}
    if not exe: res["error"] = "ping not installed"; return res
    try:
        r = subprocess.run([exe, "-n", "-q", "-c", str(count), "-W", str(timeout), host], capture_output=True, text=True, timeout=count * (timeout + 1) + 3)
    except (subprocess.TimeoutExpired, OSError) as e:
        res["error"] = type(e).__name__; return res
    out = r.stdout or ""
    s = _RE_SENT.search(out)
    if s:
        res["sent"], res["recv"] = int(s.group(1)), int(s.group(2))
        res["loss"] = round(100.0 * (res["sent"] - res["recv"]) / max(1, res["sent"]), 1)
    m = _RE_RTT.search(out)
    if m and res["recv"]: res["rtt"], res["jitter"] = round(float(m.group(2)), 2), round(float(m.group(4)), 2)
    return res

# Conexión TCP cronometrada (tres intentos).
# EN: Timed TCP connection (three attempts).
def tcp_probe(host, port, count=3, timeout=2):
    ts = []
    for _ in range(count):
        t0 = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout): pass
            ts.append((time.perf_counter() - t0) * 1000)
        except OSError: pass
        time.sleep(0.05)
    res = {"sent": count, "recv": len(ts), "loss": round(100.0 * (count - len(ts)) / count, 1), "rtt": None, "jitter": None}
    if ts:
        avg = sum(ts) / len(ts); res["rtt"] = round(avg, 2); res["jitter"] = round((sum((x - avg) ** 2 for x in ts) / len(ts)) ** 0.5, 2)
    return res

# Tiempo de resolución de un nombre con el DNS del sistema (en un hilo, para no quedar colgado si el DNS no responde).
# EN: Resolution time of a name with the system DNS (in a thread, so it does not hang if the DNS does not answer).
def dns_probe(name, timeout=4):
    box = {}
    def run():
        t0 = time.perf_counter()
        try: socket.getaddrinfo(name, 443, proto=socket.IPPROTO_TCP); box["ms"] = round((time.perf_counter() - t0) * 1000, 1)
        except OSError: box["fail"] = True
    t = threading.Thread(target=run, daemon=True); t.start(); t.join(timeout)
    return box.get("ms")

def _probe_one(t):
    r = ping(t["host"]) if t["kind"] == "ping" else tcp_probe(t["host"], t["port"])
    r.update(host=t["host"], kind=t["kind"], ok=r["recv"] > 0)
    if t["kind"] == "tcp": r["port"] = t["port"]
    return r

def _avg(vals):
    v = [x for x in vals if x is not None]
    return round(sum(v) / len(v), 2) if v else None

# Una ronda: todos los destinos y la puerta de enlace en paralelo, más el DNS. «up» = al menos un destino de Internet respondió.
# EN: One round: every target and the gateway in parallel, plus DNS. "up" = at least one Internet target answered.
def probe_round(cfg, gw_ip):
    jobs = list(cfg["targets"]) + ([{"host": gw_ip, "kind": "ping", "gateway": True}] if gw_ip else [])
    results, th = [None] * len(jobs), []
    def work(i, t): results[i] = _probe_one(t)
    for i, t in enumerate(jobs):
        x = threading.Thread(target=work, args=(i, t), daemon=True); x.start(); th.append(x)
    dns = [None]
    if cfg["dns_name"]:
        d = threading.Thread(target=lambda: dns.__setitem__(0, dns_probe(cfg["dns_name"])), daemon=True); d.start(); th.append(d)
    for x in th: x.join(30)
    for i, r in enumerate(results):
        if r is None: results[i] = {"host": jobs[i]["host"], "kind": jobs[i]["kind"], "sent": 3, "recv": 0, "loss": 100.0, "rtt": None, "jitter": None, "ok": False}
        if jobs[i].get("gateway"): results[i]["gateway"] = True
    net = [r for r in results if not r.get("gateway")]
    gw = next((r for r in results if r.get("gateway")), None)
    ok = [r for r in net if r["ok"]]
    return {"ts": int(time.time()), "up": bool(ok), "targets": net, "gateway": gw,
            "rtt": _avg([r["rtt"] for r in ok]), "jitter": _avg([r["jitter"] for r in ok]), "loss": _avg([r["loss"] for r in net]),
            "gw": gw["rtt"] if gw else None, "dns": dns[0]}

# ─── Velocidad ────────────────────────────────────────────────────────────────
def _conn(url, timeout=10):
    p = urlparse(url)
    c = http.client.HTTPSConnection(p.hostname, p.port or 443, timeout=timeout, context=ssl.create_default_context())
    return c, (p.path or "/")

# Latencia hacia el servidor de prueba: pide 0 bytes por una conexión ya abierta y toma el menor tiempo.
# EN: Latency to the test server: ask for 0 bytes over an already-open connection and take the lowest time.
def speed_ping(cfg):
    c, path = _conn(cfg["speed"]["down_url"])
    best = None
    try:
        for i in range(4):
            t0 = time.perf_counter()
            c.request("GET", path + "?bytes=0", headers={"User-Agent": "LabTower-WAN"}); r = c.getresponse(); r.read()
            dt = (time.perf_counter() - t0) * 1000
            if i and (best is None or dt < best): best = dt
    finally: c.close()
    return round(best, 1) if best else None

# Bajada: varios flujos leen del servidor hasta que se cumple el tiempo; Mb/s = bits recibidos / segundos.
# EN: Download: several streams read from the server until the time is up; Mb/s = bits received / seconds.
def speed_down(cfg):
    sp = cfg["speed"]; total, lock, end = [0], threading.Lock(), time.time() + sp["seconds"]
    why = []                                                  # first reason a stream gave up (shown instead of a generic error)
    base = "https://" + (urlparse(sp["down_url"]).hostname or "")
    hdr = {"User-Agent": "Mozilla/5.0 (LabTower-WAN)", "Accept": "*/*", "Referer": base + "/", "Origin": base}
    def work():
        got = 0
        try:
            while time.time() < end:
                c, path = _conn(sp["down_url"], 15)
                try:
                    c.request("GET", path + "?bytes=25000000", headers=hdr); r = c.getresponse()
                    if r.status != 200:
                        why.append(f"HTTP {r.status} from the download address"); break
                    buf = bytearray(262144)
                    while time.time() < end:
                        n = r.readinto(buf)
                        if not n: break
                        got += n
                finally: c.close()
        except (OSError, http.client.HTTPException) as e: why.append(f"{type(e).__name__}: {e}"[:120])
        with lock: total[0] += got
    t0 = time.perf_counter(); th = [threading.Thread(target=work, daemon=True) for _ in range(sp["streams"])]
    for x in th: x.start()
    for x in th: x.join(sp["seconds"] + 20)
    el = max(0.001, time.perf_counter() - t0)
    if not total[0] and why: raise RuntimeError(why[0])
    return round(total[0] * 8 / el / 1e6, 1) if total[0] else None

# Subida: varios flujos envían bloques de 2 MB al servidor hasta que se cumple el tiempo.
# EN: Upload: several streams send 2 MB blocks to the server until the time is up.
def speed_up(cfg):
    sp = cfg["speed"]; total, lock, end = [0], threading.Lock(), time.time() + sp["seconds"]
    block = bytes(2 * 1024 * 1024)
    why = []
    def work():
        got = 0
        try:
            c, path = _conn(sp["up_url"], 15)
            try:
                while time.time() < end:
                    c.request("POST", path, body=block, headers={"User-Agent": "LabTower-WAN", "Content-Type": "application/octet-stream"})
                    r = c.getresponse(); r.read()
                    if r.status >= 400:
                        why.append(f"HTTP {r.status} from the upload address"); break
                    got += len(block)
            finally: c.close()
        except (OSError, http.client.HTTPException) as e: why.append(f"{type(e).__name__}: {e}"[:120])
        with lock: total[0] += got
    t0 = time.perf_counter(); th = [threading.Thread(target=work, daemon=True) for _ in range(sp["streams"])]
    for x in th: x.start()
    for x in th: x.join(sp["seconds"] + 20)
    el = max(0.001, time.perf_counter() - t0)
    if not total[0] and why: raise RuntimeError(why[0])
    return round(total[0] * 8 / el / 1e6, 1) if total[0] else None

def _run_tool(cmd, timeout):
    env = dict(os.environ, HOME=str(DATA_DIR))                 # Ookla keeps its licence acceptance in $HOME/.config
    try: r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired: raise RuntimeError(f"{cmd[0]} timed out")
    if r.returncode != 0: raise RuntimeError((r.stderr or r.stdout or f"{cmd[0]} exited with {r.returncode}").strip().splitlines()[-1][:160])
    try: return json.loads(r.stdout)
    except ValueError: raise RuntimeError(f"{cmd[0]} did not return JSON")

def _g(d, *keys):
    for k in keys:
        d = d.get(k) if isinstance(d, dict) else None
    return d

def _mbps(v, scale):
    try: return round(float(v) * scale, 1)
    except (TypeError, ValueError): return None

# Ookla Speedtest CLI oficial: «bandwidth» viene en bytes por segundo.
# EN: Official Ookla Speedtest CLI: "bandwidth" is in bytes per second.
def speed_ookla(cfg, res):
    j = _run_tool([shutil.which("speedtest") or "speedtest", "--accept-license", "--accept-gdpr", "-f", "json"], 150)
    res["down"], res["up"] = _mbps(_g(j, "download", "bandwidth"), 8 / 1e6), _mbps(_g(j, "upload", "bandwidth"), 8 / 1e6)
    res["ping"] = _mbps(_g(j, "ping", "latency"), 1)
    sv = j.get("server") if isinstance(j.get("server"), dict) else {}
    res["server"] = str(sv.get("host") or sv.get("name") or "Ookla")[:80]
    if res["down"] is None: res["error"] = "Ookla returned no download result"

# LibreSpeed CLI: devuelve una lista; «download» y «upload» ya vienen en Mb/s.
# EN: LibreSpeed CLI: returns a list; "download" and "upload" are already in Mb/s.
def speed_librespeed(cfg, res):
    sp = cfg["speed"]
    cmd = [shutil.which("librespeed-cli") or "librespeed-cli", "--json", "--duration", str(sp["seconds"])] + ([] if sp["upload"] else ["--no-upload"])
    j = _run_tool(cmd, 40 + 3 * sp["seconds"])
    j = j[0] if isinstance(j, list) and j else j
    if not isinstance(j, dict): raise RuntimeError("librespeed-cli returned no result")
    res["down"], res["up"] = _mbps(j.get("download"), 1), (_mbps(j.get("upload"), 1) if sp["upload"] else None)
    res["ping"] = _mbps(j.get("ping"), 1)
    sv = j.get("server") if isinstance(j.get("server"), dict) else {}
    res["server"] = (urlparse(str(sv.get("url") or "")).hostname or str(sv.get("name") or "LibreSpeed"))[:80]
    if not res["down"]: res["error"] = "LibreSpeed returned no download result"

def run_speedtest(cfg) -> dict:
    eng = cfg["speed"].get("engine", "builtin")
    if eng != "builtin":
        res = {"ts": int(time.time()), "down": None, "up": None, "ping": None, "server": eng, "error": None}
        try:
            if not shutil.which(ENGINES[eng]): raise RuntimeError(f"{ENGINES[eng]} is not installed")
            (speed_ookla if eng == "ookla" else speed_librespeed)(cfg, res)
        except Exception as e: res["error"] = f"{e}"[:200]
        return res
    return _builtin_speedtest(cfg)

def _builtin_speedtest(cfg) -> dict:
    res = {"ts": int(time.time()), "down": None, "up": None, "ping": None, "server": urlparse(cfg["speed"]["down_url"]).hostname, "error": None}
    try:
        res["ping"] = speed_ping(cfg)
        res["down"] = speed_down(cfg)
        if res["down"] is None: res["error"] = "No data received from the test server"
        elif cfg["speed"]["upload"]:
            try: res["up"] = speed_up(cfg)
            except Exception as e: log.warning(f"upload test failed: {e}")      # the download result is still worth keeping
    except Exception as e:
        res["error"] = f"{type(e).__name__}: {e}"[:200]
    return res

# ─── IP pública ───────────────────────────────────────────────────────────────
def fetch_public_ip(url):
    c, path = _conn(url, 6)
    try:
        c.request("GET", path, headers={"User-Agent": "LabTower-WAN", "Accept": "text/plain"}); r = c.getresponse(); raw = r.read(256)
        if r.status != 200: return None
        return str(ipaddress.ip_address(raw.decode("ascii", "ignore").strip()))
    except (OSError, http.client.HTTPException, ValueError): return None
    finally: c.close()

# ─── Estado, cortes e historial ───────────────────────────────────────────────
class WanState:
    def __init__(self):
        self.lock = threading.RLock()
        self.last, self.fails, self.down_since, self.scope = None, 0, None, None
        self.history = _deque(maxlen=_HIST_MAX)
        self.ip, self.ip_changed, self.ip_checked = None, None, 0
        self.speed_running, self.speed_started, self.speed_last = False, 0, 0
        self.wake = threading.Event()
        self.gw = None

S = WanState()

def _db(sql, args=(), many=False, fetch=False):
    c = auth.metrics_conn()
    try:
        cur = c.execute(sql, args); rows = cur.fetchall() if fetch else None; c.commit(); return rows
    finally: c.close()

def store_sample(r):
    try: _db("INSERT OR REPLACE INTO wan_samples (ts,up,rtt,loss,jitter,gw,dns) VALUES (?,?,?,?,?,?,?)", (r["ts"], 1 if r["up"] else 0, r["rtt"], r["loss"], r["jitter"], r["gw"], r["dns"]))
    except Exception as e: log.warning(f"could not store the sample: {e}")

def history_range(range_: str) -> list:
    since = int(time.time()) - RANGE_SECS[range_] if range_ in RANGE_SECS else 0
    rows = _db("SELECT ts,up,rtt,loss,jitter,gw,dns FROM wan_samples WHERE ts >= ? ORDER BY ts", (since,), fetch=True)
    step = 1 if len(rows) <= RANGE_POINTS else -(-len(rows) // RANGE_POINTS)
    out = []
    for i in range(0, len(rows), step):
        g = rows[i:i + step]
        def avg(k):
            v = [r[k] for r in g if r[k] is not None]
            return round(sum(v) / len(v), 2) if v else None
        out.append({"ts": g[len(g) // 2][0], "up": min(r[1] for r in g), "rtt": avg(2), "loss": avg(3), "jitter": avg(4), "gw": avg(5), "dns": avg(6)})
    return out
RANGE_SECS = {"1h": 3600, "1d": 86400, "1w": 604800, "1mo": 2592000}
RANGE_POINTS = 600

def uptime():
    now, out = int(time.time()), {}
    for k, secs in (("24h", 86400), ("7d", 604800), ("30d", 2592000)):
        try:
            n, up = _db("SELECT COUNT(*), COALESCE(SUM(up),0) FROM wan_samples WHERE ts >= ?", (now - secs,), fetch=True)[0]
            out[k] = round(100.0 * up / n, 3) if n else None
        except Exception: out[k] = None
    return out

def recent_outages(limit=15):
    try:
        rows = _db("SELECT start,end,scope FROM wan_outages ORDER BY start DESC LIMIT ?", (limit,), fetch=True)
        return [{"start": a, "end": b, "scope": s} for a, b, s in rows]
    except Exception: return []

def recent_speed(limit=40):
    try:
        rows = _db("SELECT ts,down,up,ping,server,error FROM wan_speed ORDER BY ts DESC LIMIT ?", (limit,), fetch=True)
        return [{"ts": a, "down": b, "up": c, "ping": d, "server": e, "error": f} for a, b, c, d, e, f in reversed(rows)]
    except Exception: return []

def load_history() -> int:
    try:
        _db("DELETE FROM wan_samples WHERE ts < ?", (int(time.time()) - HIST_KEEP,))
        _db("DELETE FROM wan_speed WHERE ts < ?", (int(time.time()) - HIST_KEEP,))
        _db("DELETE FROM wan_outages WHERE start < ?", (int(time.time()) - HIST_KEEP,))
        rows = _db("SELECT ts,up,rtt,loss,jitter,gw,dns FROM wan_samples WHERE ts >= ? ORDER BY ts", (int(time.time()) - 43200,), fetch=True)
        with S.lock:
            for ts, up, rtt, loss, jit, gw, dns in rows: S.history.append({"ts": ts, "up": up, "rtt": rtt, "loss": loss, "jitter": jit, "gw": gw, "dns": dns})
        open_ = _db("SELECT start,scope FROM wan_outages WHERE end IS NULL ORDER BY start DESC LIMIT 1", fetch=True)
        if open_: S.down_since, S.scope, S.fails = open_[0][0], open_[0][1], DOWN_AFTER      # an outage was open when the service stopped: keep it open
        last = _db("SELECT ts FROM wan_speed ORDER BY ts DESC LIMIT 1", fetch=True)
        if last: S.speed_last = last[0][0]
        st = auth.read_json(STATE_FILE, {}, dict)
        if isinstance(st.get("ip"), str): S.ip, S.ip_changed = st["ip"], st.get("changed")
        return len(rows)
    except Exception as e:
        log.warning(f"could not load the history: {e}"); return 0

# Registra el paso de «arriba» a «caído» (tras DOWN_AFTER rondas fallidas) y la recuperación; escribe eventos para la línea de tiempo del Resumen.
# EN: Record the change from "up" to "down" (after DOWN_AFTER failed rounds) and the recovery; writes events for the Overview timeline.
def track_outage(r, first_fail_ts):
    gw_ok = (r["gateway"] or {}).get("ok", True) if r.get("gateway") else True
    with S.lock:
        if r["up"]:
            S.fails = 0
            if S.down_since is not None:
                dur = r["ts"] - S.down_since
                S.down_since, S.scope = None, None
                try: _db("UPDATE wan_outages SET end = ? WHERE end IS NULL", (r["ts"],))
                except Exception as e: log.warning(f"could not close the outage: {e}")
                auth.record_event("wan", "info", f"Internet connection restored after {int(dur)} s", "wan_up", d=int(dur))
                log.info(f"connection restored after {int(dur)} s")
            return
        S.fails += 1
        if S.fails >= DOWN_AFTER and S.down_since is None:
            S.down_since, S.scope = first_fail_ts, ("internet" if gw_ok else "lan")
            try: _db("INSERT OR REPLACE INTO wan_outages (start,end,scope) VALUES (?,NULL,?)", (S.down_since, S.scope))
            except Exception as e: log.warning(f"could not store the outage: {e}")
            auth.record_event("wan", "crit", "Internet connection down" + (" (local network too)" if S.scope == "lan" else ""), "wan_down_" + S.scope)
            log.warning(f"connection down ({S.scope})")

def compute_alerts(s: dict) -> list:
    a = []
    if s.get("down_since"): a.append({"lv": "crit", "type": "down_" + (s.get("scope") or "internet"), "value": s["down_since"]})
    else:
        if s.get("loss") is not None and s["loss"] >= 5: a.append({"lv": "warn", "type": "loss", "value": s["loss"]})
        if s.get("rtt") is not None and s["rtt"] >= 150: a.append({"lv": "warn", "type": "latency", "value": s["rtt"]})
        if s.get("dns") is not None and s["dns"] >= 500: a.append({"lv": "warn", "type": "dns_slow", "value": s["dns"]})
        elif s.get("dns_fail"): a.append({"lv": "warn", "type": "dns_fail"})
    if s.get("ip_changed") and time.time() - s["ip_changed"] < 3600: a.append({"lv": "info", "type": "ip_changed", "value": s.get("public_ip")})
    return a

# La lectura que ve la página: última ronda, estado, IP, alertas.
# EN: The reading the page sees: last round, state, IP, alerts.
def snapshot(cfg):
    with S.lock:
        r = S.last
        if not r: return None
        s = {"ts": r["ts"], "up": r["up"], "rtt": r["rtt"], "jitter": r["jitter"], "loss": r["loss"], "gw": r["gw"], "dns": r["dns"],
             "dns_fail": bool(cfg["dns_name"]) and r["dns"] is None, "targets": r["targets"], "gateway": r["gateway"], "gateway_ip": S.gw,
             "down_since": S.down_since, "scope": S.scope, "public_ip": S.ip, "ip_changed": S.ip_changed}
    s["alerts"] = compute_alerts(s)
    return s

# ─── Hilos ────────────────────────────────────────────────────────────────────
_stop = threading.Event()

def probe_loop():
    first_fail = None
    while not _stop.is_set():
        cfg = load_config()
        if S.speed_running: S.wake.wait(2); S.wake.clear(); continue          # the line is saturated on purpose: do not judge it
        gw_ip = (default_gateway() if cfg["gateway"] == "auto" else cfg["gateway"]) or None
        S.gw = gw_ip
        t0 = time.time()
        try: r = probe_round(cfg, gw_ip)
        except Exception as e:
            log.error(f"probe round failed: {e}"); S.wake.wait(5); continue
        if not r["up"] and first_fail is None: first_fail = r["ts"]
        if r["up"]: first_fail = None
        with S.lock: S.last = r; S.history.append({"ts": r["ts"], "up": 1 if r["up"] else 0, "rtt": r["rtt"], "loss": r["loss"], "jitter": r["jitter"], "gw": r["gw"], "dns": r["dns"]})
        store_sample(r)
        track_outage(r, first_fail or r["ts"])
        if r["up"] and cfg["ip_url"] and time.time() - S.ip_checked >= IP_EVERY: check_ip(cfg)
        S.wake.wait(max(1.0, cfg["interval"] - (time.time() - t0))); S.wake.clear()

def check_ip(cfg):
    S.ip_checked = time.time()
    ip = fetch_public_ip(cfg["ip_url"])
    if not ip: return
    with S.lock:
        old = S.ip
        if ip != old:
            S.ip, S.ip_changed = ip, (int(time.time()) if old else S.ip_changed)
            try: auth.write_json(STATE_FILE, {"ip": ip, "changed": S.ip_changed})
            except Exception as e: log.warning(f"could not store the state: {e}")
            if old: auth.record_event("wan", "info", f"Public IP changed to {ip}", "wan_ip", ip=ip)

def start_speedtest(by_schedule=False):
    cfg = load_config()
    with S.lock:
        if S.speed_running: return False
        S.speed_running, S.speed_started = True, time.time()
    def work():
        try:
            res = run_speedtest(cfg)
            _db("INSERT OR REPLACE INTO wan_speed (ts,down,up,ping,server,error) VALUES (?,?,?,?,?,?)", (res["ts"], res["down"], res["up"], res["ping"], res["server"], res["error"]))
            S.speed_last = res["ts"]
            log.info(f"speed test: ↓ {res['down']} Mb/s ↑ {res['up']} Mb/s ping {res['ping']} ms" + (f" [{res['error']}]" if res["error"] else ""))
        except Exception as e: log.error(f"speed test failed: {e}")
        finally:
            with S.lock: S.speed_running = False
            S.wake.set()
    threading.Thread(target=work, daemon=True, name="speedtest").start()
    return True

def next_speedtest(cfg):
    sp = cfg["speed"]
    if not sp["enabled"] or not sp["every_hours"]: return None
    return (S.speed_last + sp["every_hours"] * 3600) if S.speed_last else (_STARTED + 300)       # first test 5 min after the first start

def speed_scheduler():
    while not _stop.is_set():
        _stop.wait(60)
        try:
            cfg = load_config(); nxt = next_speedtest(cfg)
            if nxt and time.time() >= nxt and S.last and S.last["up"] and not S.speed_running: start_speedtest(True)
        except Exception as e: log.error(f"scheduler: {e}")

def _pruner():
    while True:
        time.sleep(3600)
        try:
            cut = int(time.time()) - HIST_KEEP
            _db("DELETE FROM wan_samples WHERE ts < ?", (cut,)); _db("DELETE FROM wan_speed WHERE ts < ?", (cut,)); _db("DELETE FROM wan_outages WHERE start < ? AND end IS NOT NULL", (cut,))
        except Exception as e: log.warning(f"could not prune: {e}")

# ─── Health ───────────────────────────────────────────────────────────────────
def health_report(detailed=False):
    c = auth.check_common()
    c["wan_file"] = auth.check_file(DATA_FILE)
    c["ping_tool"] = auth.chk(auth.OK, "ping found") if shutil.which("ping") else auth.chk(auth.WARN, "ping not installed (apt install iputils-ping): TCP targets still work")
    with S.lock: last = S.last
    if last is None: c["probe"] = auth.chk(auth.OK, "starting")
    else:
        age = time.time() - last["ts"]
        c["probe"] = auth.chk(auth.WARN, f"last probe {int(age)} s ago") if age > max(120, 4 * load_config()["interval"]) else auth.chk(auth.OK, f"last probe {int(age)} s ago")
    return auth.health_reply("wan", c, detailed)

# ─── HTTP ─────────────────────────────────────────────────────────────────────
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

    # GET: página, versión y salud son públicos; el resto exige sesión con WAN «readonly». Rutas: /api/wan, /api/wan/history, /api/me.
    # EN: GET: page, version and health are public; the rest requires a session with WAN "readonly".
    def do_GET(self):
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
        if not auth.check_permission(tok, "wan", "readonly"):
            return self._json(401, {"error": "Unauthorized"})
        if path == "/api/wan":
            cfg = load_config()
            with_hist = parse_qs(urlparse(self.path).query).get("hist", ["1"])[0] != "0"
            with S.lock: hist = list(S.history) if with_hist else []
            return self._json(200, {"config": cfg, "snap": snapshot(cfg), "history": hist, "uptime": uptime(), "outages": recent_outages(), "speed": recent_speed(),
                                    "speed_running": S.speed_running, "next_speed": next_speedtest(cfg), "ping_available": bool(shutil.which("ping")), "engines": engines_available()})
        if path == "/api/wan/history":
            rng = parse_qs(urlparse(self.path).query).get("range", ["1d"])[0]
            if rng not in RANGE_SECS and rng != "all": return self._json(400, {"error": "Invalid range"})
            try: return self._json(200, {"range": rng, "history": history_range(rng)})
            except Exception as e:
                log.warning(f"history query failed: {e}"); return self._json(500, {"error": "Could not read the history"})
        self._json(404, {"error": "Not found"})

    # POST: login/logout; «execute»: medir la velocidad ahora; solo admin: cambiar la configuración.
    # EN: POST: login/logout; "execute": measure the speed now; admin only: change the configuration.
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
        if path == "/api/wan/speedtest":
            if not auth.check_permission(tok, "wan", "execute"):
                return self._json(403 if auth.check_permission(tok, "wan", "readonly") else 401, {"error": "Execute permission required"})
            if time.time() - S.speed_started < 30: return self._json(429, {"error": "A speed test ran a moment ago"})
            if not start_speedtest(): return self._json(409, {"error": "A speed test is already running"})
            who = (auth.get_session(tok) or {}).get("username", "?"); log.info(f"{who}: speed test started")
            return self._json(202, {"ok": True})
        if path == "/api/wan/config":
            if not auth.check_permission(tok, "wan", "admin"):
                return self._json(403 if auth.check_permission(tok, "wan", "readonly") else 401, {"error": "Admin permission required"})
            with _cfg_lock:
                try: cfg = validate(body, load_config())
                except ValueError as e: return self._json(400, {"error": str(e)})
                save_config(cfg)
            S.ip_checked = 0; S.wake.set()
            return self._json(200, {"config": cfg})
        self._json(404, {"error": "Not found"})

# Arranque: permiso «wan» para usuarios antiguos (una vez), hilos y servidor en loopback.
# EN: Startup: "wan" permission for old users (once), threads and the loopback server.
if __name__ == "__main__":
    auth.prepare_module(DATA_DIR, Path(__file__).parent, LEGACY_FILES)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if auth.ensure_permissions(("wan",)): log.info("'wan' permissions updated")
    except Exception as e:
        log.warning(f"Permissions: {e}")
    log.info(f"WAN Monitor en http://{HOST}:{PORT}")
    n = load_history()
    if n: log.info(f"History restored: {n} samples")
    for fn, name in ((probe_loop, "probe"), (speed_scheduler, "speed-scheduler"), (_pruner, "pruner")):
        threading.Thread(target=fn, daemon=True, name=name).start()
    try:
        srv = ThreadingHTTPServer((HOST, PORT), H)
        srv.daemon_threads = True
        srv.serve_forever()
    except KeyboardInterrupt: sys.exit(0)
