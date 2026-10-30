"""
NAS Monitor — lectores de TrueNAS y OpenMediaVault por API / TrueNAS and OpenMediaVault readers over their APIs
"""
# ES: Este módulo lee un TrueNAS (25.04 o más nuevo: JSON-RPC 2.0 sobre WebSocket en /api/current, clave de API) o un OpenMediaVault
#     (JSON-RPC por /rpc.php, usuario y contraseña) y devuelve el MISMO formato de lectura que el lector SNMP de Synology, para que la página,
#     el historial y el Resumen funcionen igual. Solo lectura: nunca se llama a un método que cambie algo.
#
#     Seguridad:
#       · Con «verificar TLS» activo el certificado se valida contra las CA del sistema. Sin él NO se acepta cualquier certificado: se FIJA la huella
#         SHA-256 la primera vez (como DNS Monitor y Proxmox) y, si cambia, se corta la conexión ANTES de enviar la clave o la contraseña.
#       · TrueNAS exige TLS (revoca las claves de API que viajan sin cifrar), así que solo se usa wss://.
#       · No se siguen redirecciones; cada respuesta tiene un tamaño máximo; todo tiene un plazo total.
#       · Los errores del NAS se reducen a su mensaje (sin trazas) y nunca incluyen la clave ni la contraseña.
#
#     Cliente WebSocket (RFC 6455) mínimo con la biblioteca estándar: la aplicación no tiene dependencias externas.
# EN: This module reads a TrueNAS (25.04 or newer: JSON-RPC 2.0 over WebSocket at /api/current, API key) or an OpenMediaVault
#     (JSON-RPC at /rpc.php, user and password) and returns the SAME reading format as the Synology SNMP reader, so the page, the history
#     and the Overview work unchanged. Read-only: no method that changes anything is ever called.
#
#     Security:
#       · With "verify TLS" on, the certificate is validated against the system CAs. Without it ANY certificate is NOT accepted: the SHA-256
#         fingerprint is PINNED the first time (like DNS Monitor and Proxmox) and, if it changes, the connection is dropped BEFORE the key or
#         the password is sent.
#       · TrueNAS requires TLS (it revokes API keys sent in clear), so only wss:// is used.
#       · Redirects are not followed; every answer has a size cap; everything has a total deadline.
#       · NAS errors are reduced to their message (no traces) and never include the key or the password.
#
#     Minimal WebSocket client (RFC 6455) on the standard library: the application has no external dependencies.
import base64, hashlib, http.client, json, os, re, socket, ssl, struct, time

MAX_MSG   = 8 << 20          # largest WebSocket message / HTTP body accepted (bytes)
MAX_HDR   = 16384            # largest HTTP header block accepted
_CTRL     = re.compile(r"[\x00-\x1f\x7f]")
GUID      = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

class RemoteError(RuntimeError):
    pass

def clean(s, n=200):
    return _CTRL.sub(" ", str(s))[:n]

def _num(x): return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x

def _flt(x):
    try:
        v = float(x)
        return v if v == v and v not in (float("inf"), float("-inf")) else None
    except (TypeError, ValueError):
        return None

def _int(x):
    v = _flt(x)
    return int(v) if v is not None else None

# ─── TLS ──────────────────────────────────────────────────────────────────────
# learn(fp) guarda la huella aprendida (la aporta el servidor). cfg["tls_pin"] es la huella ya fijada, si existe.
# EN: learn(fp) stores the learned fingerprint (provided by the server). cfg["tls_pin"] is the already pinned one, if any.
def tls_context(cfg):
    c = ssl.create_default_context()
    if not cfg.get("verify_tls", True):
        c.check_hostname = False; c.verify_mode = ssl.CERT_NONE
    return c

def check_pin(cfg, sock, learn):
    if cfg.get("verify_tls", True): return
    der = sock.getpeercert(True)
    if not der: raise RemoteError("The server sent no certificate")
    fp = hashlib.sha256(der).hexdigest()
    pin = cfg.get("tls_pin") or ""
    if not pin:
        cfg["tls_pin"] = fp
        if learn: learn(fp)
    elif pin != fp:
        raise RemoteError("The server's certificate changed (pinned fingerprint mismatch); nothing was sent. Edit and save the NAS to learn it again")

def _hostport(host, port):
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"

# ─── Cliente WebSocket / WebSocket client ─────────────────────────────────────
class WsClient:
    def __init__(self, cfg, path, learn=None, deadline=None):
        self.cfg, self.path, self.learn = cfg, path, learn
        self.deadline = deadline or (time.monotonic() + 20)
        self.sock, self.buf = None, b""

    def _left(self):
        left = self.deadline - time.monotonic()
        if left <= 0: raise RemoteError("Timed out")
        return left

    def open(self):
        host, port, t = self.cfg["host"], self.cfg["port"], self.cfg["timeout"]
        try:
            raw = socket.create_connection((host, port), timeout=min(t, self._left()))
            try:
                self.sock = tls_context(self.cfg).wrap_socket(raw, server_hostname=host)
            except Exception:
                raw.close(); raise
            check_pin(self.cfg, self.sock, self.learn)
            key = base64.b64encode(os.urandom(16)).decode()
            hp = _hostport(host, port)
            req = (f"GET {self.path} HTTP/1.1\r\nHost: {hp}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                   f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nOrigin: https://{hp}\r\nUser-Agent: LabTower-NAS\r\n\r\n")
            self.sock.sendall(req.encode())
            head = b""
            while b"\r\n\r\n" not in head:
                if len(head) > MAX_HDR: raise RemoteError("Handshake answer too large")
                self.sock.settimeout(self._left())
                chunk = self.sock.recv(4096)
                if not chunk: raise RemoteError("Connection closed during the handshake")
                head += chunk
            head, _, self.buf = head.partition(b"\r\n\r\n")
        except ssl.SSLError as e:
            self.close(); raise RemoteError(clean(f"TLS error: {getattr(e, 'reason', None) or e}"))
        except (OSError, socket.timeout) as e:
            self.close(); raise RemoteError(clean(f"{type(e).__name__}: {e}"))
        except RemoteError:
            self.close(); raise
        lines = head.decode("latin-1").split("\r\n")
        status = lines[0].split(" ", 2)
        if len(status) < 2 or status[1] != "101":
            self.close()
            code = status[1] if len(status) > 1 else "?"
            raise RemoteError(f"WebSocket handshake refused (HTTP {clean(code, 5)}); TrueNAS 25.04 or newer is required")
        hdr = {}
        for l in lines[1:]:
            k, _, v = l.partition(":")
            hdr[k.strip().lower()] = v.strip()
        want = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
        if hdr.get("sec-websocket-accept") != want:
            self.close(); raise RemoteError("Invalid WebSocket handshake answer")
        return self

    def close(self):
        s, self.sock = self.sock, None
        if s:
            try: s.close()
            except OSError: pass

    def _read(self, n):
        while len(self.buf) < n:
            self.sock.settimeout(self._left())
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                raise RemoteError("Timed out")
            except (OSError, ssl.SSLError) as e:
                raise RemoteError(clean(f"{type(e).__name__}: {e}"))
            if not chunk: raise RemoteError("Connection closed by the server")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _send(self, opcode, payload=b""):
        n = len(payload)
        head = bytes([0x80 | opcode])
        if n < 126:        head += bytes([0x80 | n])
        elif n < 65536:    head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:              head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        body = bytes(b ^ mask[i & 3] for i, b in enumerate(payload))
        try:
            self.sock.settimeout(self._left())
            self.sock.sendall(head + mask + body)
        except (OSError, ssl.SSLError) as e:
            raise RemoteError(clean(f"{type(e).__name__}: {e}"))

    def send_json(self, obj):
        self._send(0x1, json.dumps(obj).encode())

    # Devuelve el siguiente mensaje de texto completo (une fragmentos, responde a ping, termina en close).
    # EN: Returns the next complete text message (joins fragments, answers ping, ends on close).
    def recv_text(self):
        parts, size = [], 0
        while True:
            b0, b1 = self._read(2)
            fin, op, ln = b0 & 0x80, b0 & 0x0F, b1 & 0x7F
            if b0 & 0x70: raise RemoteError("Unsupported WebSocket extension")
            if ln == 126:   ln = struct.unpack(">H", self._read(2))[0]
            elif ln == 127: ln = struct.unpack(">Q", self._read(8))[0]
            if ln > MAX_MSG: raise RemoteError("Answer too large")
            mask = self._read(4) if b1 & 0x80 else None
            data = self._read(ln) if ln else b""
            if mask: data = bytes(b ^ mask[i & 3] for i, b in enumerate(data))
            if op == 0x8: raise RemoteError("The server closed the connection")
            if op == 0x9:
                if ln > 125: raise RemoteError("Invalid ping")
                self._send(0xA, data); continue
            if op == 0xA: continue
            if op in (0x1, 0x2, 0x0):
                size += len(data)
                if size > MAX_MSG: raise RemoteError("Answer too large")
                parts.append(data)
                if fin: return b"".join(parts).decode("utf-8", "replace")
                continue
            raise RemoteError("Invalid WebSocket frame")

# ─── TrueNAS ──────────────────────────────────────────────────────────────────
class TnRpc:
    def __init__(self, ws):
        self.ws, self.n, self.events = ws, 0, {}

    def _stash(self, m):
        if not isinstance(m, dict) or m.get("method") != "collection_update": return
        p = m.get("params")
        if isinstance(p, dict) and isinstance(p.get("collection"), str):
            f = p.get("fields")
            self.events[p["collection"]] = f if isinstance(f, dict) else p

    def call(self, method, params=None):
        self.n += 1; rid = self.n
        self.ws.send_json({"jsonrpc": "2.0", "id": rid, "method": method, "params": params if params is not None else []})
        while True:
            try:    m = json.loads(self.ws.recv_text())
            except (ValueError, RecursionError): continue
            if isinstance(m, dict) and m.get("id") == rid:
                e = m.get("error")
                if e:
                    msg = e.get("message") if isinstance(e, dict) else e
                    d = e.get("data") if isinstance(e, dict) else None
                    reason = d.get("reason") if isinstance(d, dict) else None
                    raise RemoteError(clean(reason or msg or "error"))
                return m.get("result")
            self._stash(m)

    # Espera un evento (hasta «seconds»). None si no llega: la lectura sigue sin ese dato.
    # EN: Wait for an event (up to "seconds"). None if it does not arrive: the reading goes on without that data.
    def wait_event(self, name, seconds):
        orig = self.ws.deadline
        self.ws.deadline = min(orig, time.monotonic() + seconds)
        try:
            while name not in self.events:
                try:    m = json.loads(self.ws.recv_text())
                except (ValueError, RecursionError): continue
                self._stash(m)
            return self.events[name]
        except RemoteError:
            return None
        finally:
            self.ws.deadline = orig

TN_PATH = "/api/current"

def tn_open(cfg, learn=None):
    ws = WsClient(cfg, TN_PATH, learn, time.monotonic() + max(cfg["timeout"] * 3, 15)).open()
    rpc = TnRpc(ws)
    try:
        r = rpc.call("auth.login_ex", [{"mechanism": "API_KEY_PLAIN", "username": cfg["user"], "api_key": cfg["api_key"]}])
        ok = isinstance(r, dict) and r.get("response_type") == "SUCCESS"
        if not ok:
            raise RemoteError("Authentication failed (check the API key and the user it belongs to)")
    except Exception:
        ws.close(); raise
    return rpc

_TN_BAD_IF = ("lo", "veth", "docker", "br-", "kube", "cali", "vnet", "tap", "flannel", "cni")

def _tn_lv_alert(level):
    return {"INFO": "info", "NOTICE": "info", "WARNING": "warn"}.get(str(level).upper(), "crit")

def tn_collect(cfg, prev, learn=None):
    rpc = tn_open(cfg, learn)
    warnings = []
    try:
        try:    rpc.call("core.subscribe", ["reporting.realtime"])
        except RemoteError as e: warnings.append(f"realtime: {e}")
        info = rpc.call("system.info") or {}
        if not isinstance(info, dict): info = {}
        def opt(label, method, params=None, default=None):
            try:    return rpc.call(method, params)
            except RemoteError as e:
                warnings.append(f"{label}: {e}"); return default
        pools = opt("pools", "pool.query", [], [])
        disks_raw = opt("disks", "disk.query", [], [])
        alerts_raw = opt("alerts", "alert.list", [], [])
        pools = [p for p in pools if isinstance(p, dict)] if isinstance(pools, list) else []
        disks_raw = [d for d in disks_raw if isinstance(d, dict)] if isinstance(disks_raw, list) else []
        alerts_raw = [a for a in alerts_raw if isinstance(a, dict)] if isinstance(alerts_raw, list) else []
        names = [d["name"] for d in disks_raw if isinstance(d.get("name"), str)]
        temps = opt("temperatures", "disk.temperatures", [names], {}) if names else {}
        if not isinstance(temps, dict): temps = {}
        rt = rpc.events.get("reporting.realtime") or rpc.wait_event("reporting.realtime", 3.0) or {}
    finally:
        rpc.ws.close()

    up = _flt(info.get("uptime_seconds"))
    load = info.get("loadavg") if isinstance(info.get("loadavg"), list) else []
    load = [_flt(x) for x in load[:3]] + [None] * (3 - len(load[:3]))
    cpu_rt = rt.get("cpu") if isinstance(rt.get("cpu"), dict) else {}
    tot = cpu_rt.get("cpu") if isinstance(cpu_rt.get("cpu"), dict) else {}
    pct = _flt(tot.get("usage"))
    if pct is None and _flt(tot.get("idle")) is not None: pct = 100.0 - _flt(tot.get("idle"))
    pct = round(max(0.0, min(100.0, pct)), 1) if pct is not None else None
    cpu = {"pct": pct, "user": _flt(tot.get("user")), "sys": _flt(tot.get("system")), "load": load}
    temp = _flt(tot.get("temp"))

    mem = None
    mr = rt.get("memory") if isinstance(rt.get("memory"), dict) else {}
    mt, ma = _flt(mr.get("physical_memory_total")), _flt(mr.get("physical_memory_available"))
    if mt is None: mt = _flt(info.get("physmem"))
    if mt and mt > 0 and ma is not None:
        used = max(0.0, mt - ma)
        mem = {"total": int(mt), "used": int(used), "pct": round(used / mt * 100, 1), "swap_total": 0, "swap_used": 0}

    system = {"name": clean(info.get("hostname") or ""), "descr": clean(info.get("model") or ""), "uptime": up,
              "model": clean(info.get("system_product") or "TrueNAS"), "serial": clean(info.get("system_serial") or ""),
              "dsm": clean(info.get("version") or ""), "upgrade": None, "status": None, "temp": temp, "power": None,
              "fan_sys": None, "fan_cpu": None}

    # Alertas del NAS (las que no se descartaron).
    # EN: NAS alerts (the ones not dismissed).
    nas_alerts, bad_disk = [], {}
    for a in alerts_raw:
        if a.get("dismissed"): continue
        lv, text, klass = _tn_lv_alert(a.get("level")), clean(a.get("formatted") or a.get("text") or a.get("klass") or "alert", 200), clean(a.get("klass") or "", 40)
        nas_alerts.append({"lv": lv, "type": "remote", "item": klass or "alert", "value": text})
        if lv in ("warn", "crit") and re.search(r"smart|disk", klass, re.I):
            for nm in names:
                if re.search(r"\b" + re.escape(nm) + r"\b", text): bad_disk[nm] = max(bad_disk.get(nm, "warn"), lv, key=("warn", "crit").index)
    disks = []
    for i, d in enumerate(sorted(disks_raw, key=lambda x: str(x.get("name"))), 1):
        nm = clean(d.get("name") or f"Disk {i}", 40)
        t = _flt(temps.get(nm)) if isinstance(temps.get(nm), (int, float)) else None
        lv = bad_disk.get(nm, "ok")
        disks.append({"idx": str(i), "name": nm, "model": clean(d.get("model") or "", 60).strip(), "type": clean(d.get("type") or "", 12),
                      "status": None, "status_text": {"ok": "OK", "warn": "WARNING", "crit": "FAILING"}[lv], "lv": lv, "temp": t})

    raids = []
    for i, p in enumerate(sorted(pools, key=lambda x: str(x.get("name"))), 1):
        st = clean(p.get("status") or "UNKNOWN", 20).upper()
        scan = p.get("scan") if isinstance(p.get("scan"), dict) else {}
        lv = {"ONLINE": "ok", "DEGRADED": "warn"}.get(st, "crit")
        if lv == "ok" and p.get("healthy") is False: lv = "warn"
        if lv == "ok" and str(scan.get("state") or "").upper() == "SCANNING": lv = "info"
        size, free = _flt(p.get("size")), _flt(p.get("free"))
        total = int(size) if size and size > 0 else None
        fr = int(free) if free is not None and total else None
        pct = round((total - fr) / total * 100, 1) if total and fr is not None else None
        raids.append({"idx": str(i), "name": clean(p.get("name") or f"Pool {i}", 60), "status": None, "status_text": st, "lv": lv,
                      "total": total, "free": fr, "pct": pct, "pool": False})

    net = []
    ifs = rt.get("interfaces") if isinstance(rt.get("interfaces"), dict) else {}
    for nm in sorted(ifs):
        v = ifs[nm]
        if not isinstance(v, dict) or not isinstance(nm, str) or nm.startswith(_TN_BAD_IF): continue
        rx, tx = _flt(v.get("received_bytes_rate")), _flt(v.get("sent_bytes_rate"))
        net.append({"name": clean(nm, 20), "rx": round(rx * 8) if rx is not None else None, "tx": round(tx * 8) if tx is not None else None,
                    "speed": _int(v.get("speed")), "rx_total": _int(v.get("received_bytes")), "tx_total": _int(v.get("sent_bytes"))})

    io = []
    dr = rt.get("disks") if isinstance(rt.get("disks"), dict) else {}
    if dr:
        io.append({"dev": "disks", "load": _flt(dr.get("busy")), "read": _int(dr.get("read_bytes")), "write": _int(dr.get("write_bytes"))})

    snap = {"system": system, "cpu": cpu, "mem": mem, "disks": disks, "raids": raids, "ups": None, "io": io, "net": net,
            "synology": False, "kind": "truenas", "warnings": warnings}
    snap["extra_alerts"] = nas_alerts[:20]
    return snap

def tn_test(cfg, learn=None):
    rpc = tn_open(cfg, learn)
    try:
        info = rpc.call("system.info") or {}
    finally:
        rpc.ws.close()
    if not isinstance(info, dict): info = {}
    return {"name": clean(info.get("hostname") or ""), "descr": clean(info.get("model") or ""),
            "model": clean(info.get("system_product") or "TrueNAS"), "dsm": clean(info.get("version") or ""), "kind": "truenas"}

# ─── OpenMediaVault ───────────────────────────────────────────────────────────
OMV_PATH = "/rpc.php"
_SESSION_ERR = (5000, 5001, 5002)

# Estado de la sesión de un NAS (cookies). Se conserva entre lecturas: así no se inicia sesión en cada consulta y OMV no manda
# el aviso de «nuevo navegador» cada vez (la cookie de «navegador conocido» se guarda aquí).
# EN: Session state of a NAS (cookies). It is kept between readings: this way there is no login on every poll and OMV does not send
#     the "new browser" notice every time (the "known browser" cookie is kept here).
class OmvSession:
    def __init__(self):
        self.cookies, self.sid, self.key = {}, "", None

    def bind(self, cfg):
        key = (cfg["host"], cfg["port"], bool(cfg.get("https", True)), cfg["user"])
        if self.key != key: self.cookies, self.sid, self.key = {}, "", key

    def drop_session(self):
        self.sid = ""
        self.cookies.pop("PHPSESSID", None)

class OmvRpc:
    def __init__(self, cfg, state=None, learn=None):
        self.cfg, self.st, self.learn = cfg, state or OmvSession(), learn
        self.deadline = time.monotonic() + max(cfg["timeout"] * 3, 15)

    def _http(self, body):
        c = self.cfg
        left = self.deadline - time.monotonic()
        if left <= 0: raise RemoteError("Timed out")
        h = f"[{c['host']}]" if ":" in c["host"] else c["host"]
        https = c.get("https", True)
        conn = http.client.HTTPSConnection(h, c["port"], timeout=min(c["timeout"], left), context=tls_context(c)) if https \
            else http.client.HTTPConnection(h, c["port"], timeout=min(c["timeout"], left))
        hdr = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "LabTower-NAS", "Connection": "close"}
        if self.st.cookies: hdr["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.st.cookies.items())
        if self.st.sid: hdr["X-OPENMEDIAVAULT-SESSIONID"] = self.st.sid
        try:
            try:
                if https:
                    conn.connect(); check_pin(c, conn.sock, self.learn)
                conn.request("POST", OMV_PATH, json.dumps(body).encode(), hdr)
                r = conn.getresponse()
                raw = r.read(MAX_MSG + 1)
                for sc in (r.msg.get_all("Set-Cookie") or []):
                    kv = sc.split(";", 1)[0]
                    k, _, v = kv.partition("=")
                    k = k.strip()
                    if k and re.fullmatch(r"[\w.%-]{1,200}", k) and len(self.st.cookies) < 20:
                        if v.strip() in ("", "deleted"): self.st.cookies.pop(k, None)
                        else: self.st.cookies[k] = clean(v.strip(), 400).replace(";", "")
            finally:
                conn.close()
        except ssl.SSLError as e:
            raise RemoteError(clean(f"TLS error: {getattr(e, 'reason', None) or e}"))
        except (OSError, http.client.HTTPException) as e:
            raise RemoteError(clean(f"{type(e).__name__}: {e}"))
        if len(raw) > MAX_MSG: raise RemoteError("Answer too large")
        if 300 <= r.status < 400:
            raise RemoteError("The server redirected the request (not followed); check the HTTP/HTTPS setting and the port")
        try:    j = json.loads(raw) if raw.strip() else None
        except (ValueError, RecursionError): j = None
        return r.status, j

    def _raw(self, service, method, params=None):
        st, j = self._http({"service": service, "method": method, "params": params, "options": None})
        err = j.get("error") if isinstance(j, dict) else None
        if err:
            code = err.get("code") if isinstance(err, dict) else None
            msg = err.get("message") if isinstance(err, dict) else err
            if st == 401 or code in _SESSION_ERR: raise _NeedLogin(clean(msg or "not authenticated"))
            raise RemoteError(clean(msg or f"HTTP {st}"))
        if st == 401: raise _NeedLogin("not authenticated")
        if st >= 400 or not isinstance(j, dict): raise RemoteError(f"Unexpected answer (HTTP {st})")
        return j.get("response")

    def login(self):
        self.st.drop_session()
        r = self._raw("Session", "login", {"username": self.cfg["user"], "password": self.cfg["password"]})
        ok = isinstance(r, dict) and (r.get("authenticated") is True or r.get("status") == "authenticated")
        if not ok:
            raise RemoteError("Authentication failed" if not (isinstance(r, dict) and r.get("status") == "challengeRequired")
                              else "This account needs a second login step (not supported); use an account without it")
        sid = r.get("sessionid")
        self.st.sid = clean(sid, 200) if isinstance(sid, str) else ""

    def call(self, service, method, params=None):
        if not self.st.cookies.get("PHPSESSID") and not self.st.sid: self.login()
        try:
            return self._raw(service, method, params)
        except _NeedLogin:
            self.login()
            try:    return self._raw(service, method, params)
            except _NeedLogin as e: raise RemoteError(f"Session rejected: {e}")

class _NeedLogin(RemoteError):
    pass

def _omv_size(x):
    v = _flt(x)
    return int(v) if v is not None and v >= 0 else None

_OMV_SMART_LV = {"GOOD": "ok", "BAD_ATTRIBUTE_NOW": "crit", "BAD_STATUS": "crit", "BAD_ATTRIBUTE_IN_THE_PAST": "warn",
                 "BAD_SECTOR": "warn", "BAD_SECTOR_MANY": "crit", "UNKNOWN": "info"}
_OMV_FS_SKIP = ("swap", "vfat", "iso9660", "squashfs", "udf", "")

def omv_collect(cfg, prev, learn=None):
    state = prev.setdefault("omv", OmvSession()); state.bind(cfg)
    rpc = OmvRpc(cfg, state, learn)
    warnings = []
    info = rpc.call("System", "getInformation") or {}
    if not isinstance(info, dict): raise RemoteError("Unexpected answer from System.getInformation")
    def opt(label, service, method, params=None, default=None):
        try:    return rpc.call(service, method, params)
        except RemoteError as e:
            warnings.append(f"{label}: {e}"); return default
    def rows(x):
        if isinstance(x, dict): x = x.get("data")
        return [r for r in x if isinstance(r, dict)] if isinstance(x, list) else []
    devs = rows(opt("disks", "DiskMgmt", "enumerateDevices"))
    smart = rows(opt("smart", "Smart", "getList", {"start": 0, "limit": -1}))
    fss = rows(opt("filesystems", "FileSystemMgmt", "enumerateFilesystems"))
    if not fss:
        fss = rows(opt("filesystems", "FileSystemMgmt", "enumerateMountedFilesystems", {"includeRoot": True}))
    nics = rows(opt("network", "Network", "enumerateDevices"))

    la = info.get("loadAverage") if isinstance(info.get("loadAverage"), dict) else {}
    pct = _flt(info.get("cpuUtilization"))
    if pct is None: pct = _flt(info.get("cpuUsage"))
    cpu = {"pct": round(max(0.0, min(100.0, pct)), 1) if pct is not None else None, "user": None, "sys": None,
           "load": [_flt(la.get("1min")), _flt(la.get("5min")), _flt(la.get("15min"))]}
    mem, mt = None, _flt(info.get("memTotal"))
    mu, ma = _flt(info.get("memUsed")), _flt(info.get("memAvailable"))
    if mt and mt > 0:
        used = (mt - ma) if ma is not None else mu
        if used is not None:
            used = max(0.0, min(mt, used))
            mem = {"total": int(mt), "used": int(used), "pct": round(used / mt * 100, 1), "swap_total": 0, "swap_used": 0}
    upd = _int(info.get("availablePkgUpdates"))
    system = {"name": clean(info.get("hostname") or ""), "descr": clean(info.get("cpuModelName") or ""), "uptime": _flt(info.get("uptime")),
              "model": "OpenMediaVault", "serial": "", "dsm": clean(info.get("version") or ""),
              "upgrade": (1 if upd and upd > 0 else 2) if upd is not None else None, "status": None, "temp": None, "power": None,
              "fan_sys": None, "fan_cpu": None}

    by_file = {}
    for d in devs:
        f = d.get("devicefile")
        if isinstance(f, str) and not d.get("israid") and not str(d.get("devicename") or "").startswith(("md", "loop", "sr", "ram", "zram", "dm-")):
            by_file[f] = {"name": clean(d.get("devicename") or f.rsplit("/", 1)[-1], 40), "model": clean(d.get("model") or "", 60).strip(),
                          "type": "SSD" if d.get("rotationrate") == 0 or d.get("solid") else "", "temp": None, "state": None}
    for s in smart:
        f = s.get("devicefile")
        if not isinstance(f, str): continue
        o = by_file.setdefault(f, {"name": clean(s.get("devicename") or f.rsplit("/", 1)[-1], 40), "model": clean(s.get("model") or "", 60).strip(),
                                   "type": "", "temp": None, "state": None})
        t = _flt(s.get("temperature"))
        o["temp"] = t if t is not None and 0 < t < 150 else None
        o["state"] = clean(s.get("overallstatus") or "", 40).upper() or None
    disks = []
    for i, (f, o) in enumerate(sorted(by_file.items(), key=lambda kv: kv[1]["name"]), 1):
        lv = _OMV_SMART_LV.get(o["state"] or "UNKNOWN", "warn") if o["state"] else "ok"
        disks.append({"idx": str(i), "name": o["name"], "model": o["model"], "type": o["type"], "status": None,
                      "status_text": o["state"] or "OK", "lv": lv, "temp": o["temp"]})

    raids, seen = [], set()
    for f in sorted(fss, key=lambda x: str(x.get("label") or x.get("devicefile") or "")):
        typ = str(f.get("type") or "").lower()
        if typ in _OMV_FS_SKIP: continue
        key = f.get("uuid") or f.get("devicefile")
        if key in seen: continue
        seen.add(key)
        total, avail = _omv_size(f.get("size")), _omv_size(f.get("available"))
        used = _omv_size(f.get("used"))
        if total and avail is None and used is not None: avail = max(0, total - used)
        pct = round((total - avail) / total * 100, 1) if total and avail is not None and total > 0 else None
        mounted = f.get("mounted")
        lv = "ok" if mounted is None or mounted else "warn"
        raids.append({"idx": str(len(raids) + 1), "name": clean(f.get("label") or f.get("devicefile") or f"Filesystem {len(raids) + 1}", 60),
                      "status": None, "status_text": ("MOUNTED" if mounted is None or mounted else "UNMOUNTED") + (f" · {typ}" if typ else ""),
                      "lv": lv, "total": total, "free": avail, "pct": pct, "pool": False})

    net = []
    for n in nics:
        nm = n.get("devicename")
        if not isinstance(nm, str) or nm.startswith(("lo", "veth", "docker", "br-", "virbr", "tap", "vnet")): continue
        net.append({"name": clean(nm, 20), "rx": None, "tx": None, "speed": _int(n.get("speed")), "rx_total": None, "tx_total": None})

    snap = {"system": system, "cpu": cpu, "mem": mem, "disks": disks, "raids": raids, "ups": None, "io": [], "net": net,
            "synology": False, "kind": "omv", "warnings": warnings}
    snap["extra_alerts"] = ([{"lv": "warn", "type": "remote", "item": "reboot", "value": "reboot required"}] if info.get("rebootRequired") else [])
    return snap

def omv_test(cfg, learn=None):
    rpc = OmvRpc(cfg, None, learn)
    info = rpc.call("System", "getInformation") or {}
    if not isinstance(info, dict): raise RemoteError("Unexpected answer from System.getInformation")
    return {"name": clean(info.get("hostname") or ""), "descr": clean(info.get("cpuModelName") or ""), "model": "OpenMediaVault",
            "dsm": clean(info.get("version") or ""), "kind": "omv"}
