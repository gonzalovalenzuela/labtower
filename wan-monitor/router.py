"""Router checks for WAN Monitor: ask the router whether ITS internet link (WAN) is up, to tell a line/provider outage from a local one.
ES: Cada adaptador habla con un tipo de router y devuelve lo mismo: {ok, wan_up, ip, uptime, error}. `wan_up` es True/False según lo que informa el router, o None si no se
    pudo saber. Solo lee: nunca cambia nada en el router. Solo biblioteca estándar.
EN: Each adapter talks to one router type and returns the same thing: {ok, wan_up, ip, uptime, error}. `wan_up` is True/False as the router reports it, or None when it
    could not be told. Read only: it never changes anything on the router. Standard library only."""
import base64, hashlib, hmac, http.cookiejar, json, os, re, ssl, time
import urllib.error, urllib.request

TYPES = ("huawei", "openwrt", "ddwrt", "tplink")
TIMEOUT = 6
MAX_BODY = 512 * 1024

class RouterError(Exception):
    pass

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None

class Http:
    """One small HTTP session (cookies kept) against one router. Never follows redirects to other hosts."""
    def __init__(self, base, verify=False, basic=None):
        self.base, self.basic = base.rstrip("/"), basic
        ctx = ssl.create_default_context()
        if not verify: ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE
        self.jar = http.cookiejar.CookieJar(http.cookiejar.DefaultCookiePolicy(allowed_domains=None))
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), urllib.request.HTTPSHandler(context=ctx), _NoRedirect())
    def request(self, path, data=None, headers=None, method=None):
        h = dict(headers or {})
        if self.basic: h["Authorization"] = "Basic " + base64.b64encode(f"{self.basic[0]}:{self.basic[1]}".encode()).decode()
        body = data.encode() if isinstance(data, str) else data
        req = urllib.request.Request(self.base + path, data=body, headers=h, method=method or ("POST" if body is not None else "GET"))
        try:
            with self.opener.open(req, timeout=TIMEOUT) as r: return r.status, r.read(MAX_BODY).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            try: txt = e.read(MAX_BODY).decode("utf-8", "replace")
            except Exception: txt = ""
            return e.code, txt
        except (urllib.error.URLError, OSError, ssl.SSLError) as e:
            raise RouterError("no connection to the router: " + str(getattr(e, "reason", e))[:100])

def _json(txt, what):
    try: v = json.loads(txt)
    except ValueError: raise RouterError(f"{what}: the router did not answer with JSON")
    return v

def _res(wan_up, ip=None, uptime=None, detail=""):
    return {"ok": wan_up is not None, "wan_up": wan_up, "ip": ip or None, "uptime": uptime, "detail": detail[:160], "error": ""}

# ─── Huawei (HiLink: WiFi AX3, Mesh 3/7, WS7xxx …) ────────────────────────────────────────────────
# ES: Entrada tipo SCRAM-SHA256 (nonce → sal e iteraciones → prueba del cliente) y luego GET api/ntwk/wandetect. Protocolo documentado por el proyecto público
#     huawei_mesh_router. EN: SCRAM-SHA256-like login (nonce → salt and iterations → client proof), then GET api/ntwk/wandetect.
def huawei_proof(password, salt_hex, iterations, first_nonce, server_nonce):
    salted = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), iterations, 32)
    auth_msg = f"{first_nonce},{server_nonce},{server_nonce}"
    client_key = hmac.new(b"Client Key", salted, hashlib.sha256).digest()
    stored = hashlib.sha256(client_key).digest()
    sig = hmac.new(auth_msg.encode(), stored, hashlib.sha256).digest()
    return bytes(a ^ b for a, b in zip(client_key, sig)).hex()

def _hw_err(d, what):
    if isinstance(d, dict):
        for k in ("err", "errcode"):
            if d.get(k) not in (None, 0):
                cat = str(d.get("errorCategory") or "")
                if cat == "user_pass_err": raise RouterError("wrong user or password")
                if cat == "Too_Many_user": raise RouterError("the router has too many open sessions")
                raise RouterError(f"{what}: the router refused it ({k}={d.get(k)} {cat})".strip())

def check_huawei(c, http):
    st, html = http.request("/html/index.html")
    mp, mt = re.search(r'<meta name="csrf_param" content="([^"]+)"', html), re.search(r'<meta name="csrf_token" content="([^"]+)"', html)
    if st != 200 or not mp or not mt: raise RouterError("this does not look like a Huawei HiLink router (no login page found)")
    csrf = {"csrf_param": mp.group(1), "csrf_token": mt.group(1)}
    def post(path, data):
        nonlocal csrf
        s, t = http.request("/" + path, json.dumps({"csrf": csrf, "data": data}), {"Content-Type": "text/plain; charset=UTF-8"})
        if s != 200: raise RouterError(f"{path}: HTTP {s}")
        d = _json(t, path)
        if isinstance(d, dict) and "csrf_param" in d and "csrf_token" in d: csrf = {"csrf_param": d["csrf_param"], "csrf_token": d["csrf_token"]}
        _hw_err(d, path); return d
    first = os.urandom(32).hex()
    d = post("api/system/user_login_nonce", {"username": c["user"], "firstnonce": first})
    try: proof = huawei_proof(c["password"], d["salt"], int(d["iterations"]), first, d["servernonce"])
    except (KeyError, ValueError, TypeError): raise RouterError("unexpected login answer from the router")
    post("api/system/user_login_proof", {"clientproof": proof, "finalnonce": d["servernonce"]})
    try:
        s, t = http.request("/api/ntwk/wandetect")
        d = _json(t, "wandetect")
        if s != 200 or not isinstance(d, dict) or "Status" not in d: raise RouterError("the router did not report the WAN status (unexpected answer)")
        ip = d.get("ExternalIPAddress"); ip = None if ip in (None, "", "-", "0.0.0.0") else str(ip)
        up = d.get("Uptime"); up = int(up) if isinstance(up, (int, float)) or str(up).isdigit() else None
        return _res(str(d.get("Status")) == "Connected", ip, up, "Status=" + str(d.get("Status")))
    finally:
        try: post("api/system/user_logout", {})
        except Exception: pass

# ─── OpenWrt (ubus por HTTP / ubus over HTTP, uhttpd-mod-ubus) ───────────────────────────────────
def check_openwrt(c, http):
    n = [0]
    def call(sid, obj, method, args):
        n[0] += 1
        s, t = http.request("/ubus", json.dumps({"jsonrpc": "2.0", "id": n[0], "method": "call", "params": [sid, obj, method, args]}), {"Content-Type": "application/json"})
        if s != 200: raise RouterError(f"ubus: HTTP {s} (is uhttpd-mod-ubus installed?)")
        d = _json(t, "ubus")
        if isinstance(d, dict) and d.get("error"): raise RouterError("ubus: " + str((d["error"] or {}).get("message", "error"))[:80])
        r = d.get("result") if isinstance(d, dict) else None
        if not isinstance(r, list) or not r: raise RouterError("ubus: unexpected answer")
        if r[0] == 6: raise RouterError("wrong user or password" if obj == "session" else "this user may not read the network status (ubus access denied)")
        if r[0] != 0: raise RouterError(f"ubus {obj}.{method}: code {r[0]}")
        return r[1] if len(r) > 1 and isinstance(r[1], dict) else {}
    sid = call("0" * 32, "session", "login", {"username": c["user"], "password": c["password"]}).get("ubus_rpc_session")
    if not isinstance(sid, str): raise RouterError("wrong user or password")
    try:
        d = call(sid, "network.interface." + c["interface"], "status", {})
        addr = (d.get("ipv4-address") or [{}])[0].get("address") if isinstance(d.get("ipv4-address"), list) and d.get("ipv4-address") else None
        if "up" not in d: raise RouterError(f"interface '{c['interface']}' did not report its state")
        up = d.get("uptime")
        return _res(bool(d.get("up")), addr, int(up) if isinstance(up, (int, float)) else None, f"{c['interface']} proto={d.get('proto', '?')}")
    finally:
        try: call(sid, "session", "destroy", {})
        except Exception: pass

# ─── DD-WRT (páginas «live» con HTTP básico / "live" pages with HTTP basic) ──────────────────────
_RE_KV = re.compile(r"\{(\w+)::(.*?)\}", re.S)
_IP4 = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

def parse_ddwrt(text):
    kv = {k: v.strip() for k, v in _RE_KV.findall(text)}
    st, ip = kv.get("wan_status") or kv.get("wan_state") or "", kv.get("wan_ipaddr", "")
    ip = ip if _IP4.match(ip) else ""
    if st:
        s = st.lower()
        up = ("connected" in s or "up" == s) and "disconnected" not in s and "not connected" not in s
    elif "wan_ipaddr" in kv: up = bool(ip) and ip != "0.0.0.0"
    else: return None, None, None, ""
    upt = re.match(r"\s*(?:(\d+) days?,\s*)?(\d+):(\d+):(\d+)", kv.get("wan_uptime", "") or "")
    secs = (int(upt.group(1) or 0) * 86400 + int(upt.group(2)) * 3600 + int(upt.group(3)) * 60 + int(upt.group(4))) if upt else None
    return up, (ip if ip not in ("", "0.0.0.0") else None), secs, "wan_status=" + st if st else "wan_ipaddr=" + kv.get("wan_ipaddr", "")

def check_ddwrt(c, http):
    last = ""
    for path in ("/Status_Router.live.asp", "/Status_Internet.live.asp"):
        s, t = http.request(path)
        if s == 401: raise RouterError("wrong user or password")
        if s != 200: last = f"HTTP {s} on {path}"; continue
        up, ip, secs, det = parse_ddwrt(t)
        if up is not None: return _res(up, ip, secs, det)
        last = f"{path} has no WAN state"
    raise RouterError("could not read the WAN state from DD-WRT (" + last + ")")

# ─── TP-Link (firmware con interfaz «userRpm», HTTP básico) / (firmware with the "userRpm" interface, HTTP basic) ─────────────
# ES: Los TP-Link nuevos (Archer/Deco con inicio cifrado) no se pueden leer sin cifrado propio: se avisa.
# EN: Newer TP-Link models (Archer/Deco with encrypted login) cannot be read this way: a clear message is returned.
def parse_tplink(text):
    m = re.search(r"var\s+wanPara\s*=\s*new\s+Array\s*\((.*?)\)\s*;", text, re.S)
    if not m: return None, None
    toks = [x.strip().strip('"\'') for x in m.group(1).split(",")]
    ip = next((x for x in toks[:6] if _IP4.match(x)), None)
    if ip is None: return None, None
    return ip != "0.0.0.0", (None if ip == "0.0.0.0" else ip)

def check_tplink(c, http):
    s, t = http.request("/userRpm/StatusRpm.htm", headers={"Referer": http.base + "/userRpm/MenuRpm.htm"})
    if s == 401: raise RouterError("wrong user or password")
    if s != 200: raise RouterError(f"this TP-Link does not offer the classic status page (HTTP {s}); newer models encrypt their login and are not supported")
    up, ip = parse_tplink(t)
    if up is None: raise RouterError("no WAN data in the TP-Link status page (newer models encrypt their login and are not supported)")
    return _res(up, ip, None, "wanPara")

ADAPTERS = {"huawei": check_huawei, "openwrt": check_openwrt, "ddwrt": check_ddwrt, "tplink": check_tplink}

def check(c, host):
    """Query the router described by config `c` (type, port, https, user, password, interface) at `host`. Never raises: errors go in the result."""
    out = {"ok": False, "wan_up": None, "ip": None, "uptime": None, "detail": "", "error": "", "type": c.get("type"), "host": host, "ts": int(time.time())}
    try:
        if c["type"] not in ADAPTERS: raise RouterError("unknown router type")
        if not host: raise RouterError("no router address (and no default gateway)")
        scheme = "https" if c.get("https") else "http"
        basic = (c["user"], c["password"]) if c["type"] in ("ddwrt", "tplink") else None
        http = Http(f"{scheme}://{host}:{int(c['port'])}", verify=False, basic=basic)
        out.update(ADAPTERS[c["type"]](c, http)); out["ts"] = int(time.time())
    except RouterError as e: out["error"] = str(e)[:200]
    except Exception as e: out["error"] = f"{type(e).__name__}: {e}"[:200]
    return out

def classify_scope(gateway_ok, router):
    """'lan' when the router itself does not answer; 'wan' when it answers and says its internet link is down; otherwise 'internet' (beyond the router / unknown)."""
    if not gateway_ok: return "lan"
    if router and router.get("ok") and router.get("wan_up") is False: return "wan"
    return "internet"
