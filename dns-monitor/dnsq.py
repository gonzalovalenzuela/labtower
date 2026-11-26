"""Cliente DNS mínimo (UDP, sin dependencias) para sondear resolutores y probar nombres desde DNS Monitor."""
# EN: Minimal DNS client (UDP, no dependencies) to probe resolvers and test names from DNS Monitor.
import ipaddress
import re
import secrets
import socket
import struct
import time

TYPES = {"A": 1, "CNAME": 5, "AAAA": 28}
NAME_RE = re.compile(r"^(?=.{1,253}$)([A-Za-z0-9_]([A-Za-z0-9_-]{0,61}[A-Za-z0-9_])?\.)*[A-Za-z0-9_]([A-Za-z0-9_-]{0,61}[A-Za-z0-9_])?\.?$")

# True si el texto es un nombre de dominio razonable (etiquetas de hasta 63 caracteres, 253 en total).
# EN: True if the text is a reasonable domain name (labels up to 63 characters, 253 in total).
def valid_name(n):
    return isinstance(n, str) and bool(NAME_RE.match(n)) and not n.startswith("-")

def build_query(name, qtype, qid=None):
    qid = secrets.randbelow(1 << 16) if qid is None else qid
    q = b"".join(bytes([len(p)]) + p.encode("ascii") for p in name.rstrip(".").split("."))
    return qid, struct.pack(">HHHHHH", qid, 0x0100, 1, 0, 0, 0) + q + b"\x00" + struct.pack(">HH", qtype, 1)

def _name(buf, i, depth=0):
    """Decode a (possibly compressed) name at i. Returns (name, next_index)."""
    labels, end = [], None
    while True:
        if i >= len(buf) or depth > 20: raise ValueError("bad name")
        n = buf[i]
        if n == 0:
            return ".".join(labels), (end if end is not None else i + 1)
        if n & 0xC0 == 0xC0:
            if i + 1 >= len(buf): raise ValueError("bad pointer")
            if end is None: end = i + 2
            i, depth = ((n & 0x3F) << 8) | buf[i + 1], depth + 1
            continue
        if n > 63 or i + 1 + n > len(buf): raise ValueError("bad label")
        labels.append(buf[i + 1:i + 1 + n].decode("ascii", "replace")); i += 1 + n

# Interpreta una respuesta: {"rcode", "answers": [{"type", "value"}]}. Lanza ValueError si el paquete no es válido.
# EN: Parse a response: {"rcode", "answers": [{"type", "value"}]}. Raises ValueError if the packet is not valid.
def parse_response(buf, qid):
    if len(buf) < 12: raise ValueError("short")
    rid, flags, qd, an = struct.unpack(">HHHH", buf[:8])
    if rid != qid or not flags & 0x8000: raise ValueError("not our answer")
    i = 12
    for _ in range(qd):
        _, i = _name(buf, i); i += 4
    out = []
    for _ in range(min(an, 32)):
        _, i = _name(buf, i)
        if i + 10 > len(buf): raise ValueError("short")
        rt, _, _, rl = struct.unpack(">HHIH", buf[i:i + 10]); i += 10
        rd = buf[i:i + rl]
        if len(rd) != rl: raise ValueError("short")
        if rt == 1 and rl == 4: out.append({"type": "A", "value": str(ipaddress.IPv4Address(rd))})
        elif rt == 28 and rl == 16: out.append({"type": "AAAA", "value": str(ipaddress.IPv6Address(rd))})
        elif rt == 5: out.append({"type": "CNAME", "value": _name(buf, i)[0]})
        i += rl
    return {"rcode": flags & 0xF, "answers": out}

# Consulta un resolutor por UDP. Devuelve {"ok", "ms", "rcode", "answers"} o {"ok": False, "error"}; ok = respondió con NOERROR/NXDOMAIN.
# EN: Query a resolver over UDP. Returns {"ok", "ms", "rcode", "answers"} or {"ok": False, "error"}; ok = answered NOERROR/NXDOMAIN.
def query(host, port, name, qtype="A", timeout=2.0):
    try: fam = socket.AF_INET6 if ipaddress.ip_address(host).version == 6 else socket.AF_INET
    except ValueError: return {"ok": False, "error": "invalid address"}
    qid, pkt = build_query(name, TYPES[qtype])
    t0 = time.monotonic()
    try:
        with socket.socket(fam, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout); s.connect((host, int(port))); s.send(pkt)
            while True:
                try: r = parse_response(s.recv(4096), qid); break
                except ValueError:
                    if time.monotonic() - t0 > timeout: return {"ok": False, "error": "no valid answer"}
    except TimeoutError: return {"ok": False, "error": "timeout"}
    except OSError as e: return {"ok": False, "error": (e.strerror or "error")[:60]}
    r["ms"] = round((time.monotonic() - t0) * 1000, 1)
    r["ok"] = r["rcode"] in (0, 3)
    return r

# Dirección y puerto de un DNS de salida: «1.1.1.1», «1.1.1.1:53», «[2606:4700::1111]:53» o «127.0.0.1#5335»; None para DoH/DoT u otros textos.
# EN: Address and port of an upstream: "1.1.1.1", "1.1.1.1:53", "[2606:4700::1111]:53" or "127.0.0.1#5335"; None for DoH/DoT or other text.
def split_upstream(text, port=None):
    t = str(text or "").strip()
    m = re.fullmatch(r"\[([0-9a-fA-F:]+)\](?::(\d{1,5}))?", t) or re.fullmatch(r"([0-9.]+)(?:[:#](\d{1,5}))?", t)
    if m: host, p = m.group(1), m.group(2) or port or 53
    else: host, p = t, port or 53
    try: ip = str(ipaddress.ip_address(host))
    except ValueError: return None
    p = int(p) if str(p).isdigit() else 53
    return (ip, p) if 1 <= p <= 65535 else None

# Puertos por omisión de cada esquema de DNS de salida (sin esquema = UDP).
# EN: Default port of each upstream scheme (no scheme = UDP).
_DEF_PORT = {"udp": 53, "tcp": 53, "tls": 853, "quic": 853, "https": 443, "h3": 443}

# Forma comparable de un DNS de salida, para cruzar las estadísticas con la configuración: (esquema, host, puerto, ruta).
# Acepta «1.1.1.1», «1.1.1.1:53», «127.0.0.1#5335», «2606:4700::1111», «[2606:4700::1111]:53», «tls://dns.quad9.net» o
# «https://dns.quad9.net:443/dns-query». None si no se entiende (p. ej. un sello sdns:// o un puerto inválido).
# EN: Comparable form of an upstream, to match the statistics with the configuration: (scheme, host, port, path).
#     None when it cannot be understood (e.g. an sdns:// stamp or an invalid port).
def upstream_key(text, port=None):
    t = str(text or "").strip()
    scheme, sep, rest = t.partition("://")
    scheme = scheme.lower() if sep else "udp"
    if not sep: rest = t
    if scheme not in _DEF_PORT: return None
    hp, _, path = rest.partition("/")
    m = re.fullmatch(r"\[([0-9a-fA-F:.]+)\](?:[:#](\d{1,5}))?", hp)
    if m: host, p = m.group(1), m.group(2)
    elif hp.count(":") > 1: host, _, p = hp.partition("#")                    # bare IPv6, port only with "#"
    else: host, _, p = hp.replace("#", ":").partition(":")
    if p and not p.isdigit(): return None
    p = int(p) if p else (port if port is not None else _DEF_PORT[scheme])
    if not host or not isinstance(p, int) or not 1 <= p <= 65535: return None
    try: host = str(ipaddress.ip_address(host))
    except ValueError:
        host = host.lower().rstrip(".")
        if not re.fullmatch(r"[a-z0-9.-]+", host): return None
    return (scheme, host, p, "/" + path.split("?")[0].strip("/") if scheme in ("https", "h3") else "")

# Conjunto de DNS de salida de una lista de configuración (una entrada por línea; varias separadas por espacios).
# Salta comentarios «#…» y, en las reglas por dominio «[/lan/]192.0.2.1», toma lo que va después de «]».
# None si hay alguna entrada que no se entiende o la lista queda vacía: entonces no se marca nada como antiguo.
# EN: Set of upstreams in a configuration list (one entry per line; several separated by spaces). Skips "#…" comments
#     and, in per-domain rules "[/lan/]192.0.2.1", takes what follows "]". None when an entry cannot be understood
#     or the list is empty: then nothing is marked as old.
def config_upstreams(lines):
    keys = set()
    for ln in lines or []:
        ln = str(ln).strip()
        if ln.startswith("[/"): ln = ln.partition("]")[2].strip()
        if not ln or ln.startswith("#"): continue                          # also "[/lan/]#" = default upstreams
        for tok in ln.split():
            k = upstream_key(tok)
            if k is None: return None
            keys.add(k)
    return keys or None
