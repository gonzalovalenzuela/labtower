"""
AP Monitor — puntos de acceso Wi-Fi para Net Monitor (solo biblioteca estándar de Python 3).

Tipos (driver) de cada entrada de configuración:
  · openwrt   — OpenWrt por ubus sobre HTTP (uhttpd-mod-ubus / rpcd): estado, uptime, radios, SSID y clientes.
  · mitrastar — Amplificador Smart WiFi de Movistar (MitraStar). Modo «web»: lee su página de información (modelo, firmware,
                SSID y canales; no informa clientes ni uptime) y cierra la sesión al terminar. Modo «ping»: solo responde o no.
  · instanton — HPE Aruba Instant On. Modo «cloud»: portal en la nube (API no oficial, cuenta sin 2FA); una entrada trae todos
                los AP del sitio. Modo «ping»: solo responde o no.
  · unifi     — Ubiquiti UniFi, por el controlador UniFi Network (UniFi OS o clásico). Modo «controller»: estado, radios, SSID y clientes
                de todos los AP del sitio. Modo «ping»: solo responde o no.
Todos entregan la misma lista normalizada de AP: [{key, name, model, fw, serial, ip, mac, uptime, online, radios, ssids, clients}].
Los campos que un equipo no informa quedan en None. Nada aquí cambia la configuración de los equipos: SOLO LECTURA.

EN: AP Monitor — Wi-Fi access points for Net Monitor (Python 3 standard library only).
    Drivers: openwrt (ubus over HTTP: status, uptime, radios, SSIDs and clients); mitrastar (Movistar Smart WiFi extender:
    "web" mode reads its info page — model, firmware, SSIDs and channels, no clients or uptime — and logs out afterwards;
    "ping" mode is reachability only); instanton (HPE Aruba Instant On: "cloud" mode uses the unofficial portal API with an
    account without 2FA and one entry brings every AP of the site; "ping" mode is reachability only).
    unifi (Ubiquiti UniFi through the UniFi Network controller, UniFi OS or classic: "controller" mode reads every AP of the site; "ping"
    mode is reachability only).
    All return the same normalised AP list; fields a device does not report stay None. READ ONLY.
"""
import base64
import hashlib
import http.client
import json
import os
import re
import secrets
import ssl
import subprocess  # nosec B404 - only the fixed ping command, no shell
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import auth  # valid_target(): the AP address cannot be this machine or a link-local address / la dirección no puede ser esta máquina ni de enlace local

TIMEOUT = 10
POLL_DEFAULT, POLL_MIN, POLL_MAX = 60, 30, 3600
FAILS_FOR_DOWN = 2                 # lecturas fallidas seguidas para dar un AP por caído / failed reads in a row before an AP is "down"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,31}$")
HOST_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?(:\d{1,5})?$")
DRIVERS = {"openwrt": ("ubus",), "mitrastar": ("web", "ping"), "instanton": ("cloud", "ping"), "unifi": ("controller", "ping")}


class APError(Exception):
    pass


def _md5(s):
    return hashlib.md5(s.encode()).hexdigest()  # nosec B324 - md5 is the MitraStar login format, not a security use


def _clean(s, n):
    return "".join(ch for ch in str(s if s is not None else "") if ch.isprintable())[:n].strip()


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def band_of(mhz=None, name=None):
    """Banda «2.4», «5» o «6» desde la frecuencia (MHz) o un texto como «2.4ghz». / Band from the frequency or a text."""
    m = _int(mhz)
    if m:
        return "2.4" if m < 3000 else "5" if m < 5925 else "6"
    s = str(name or "").lower()
    return "2.4" if s.startswith("2") else "6" if s.startswith("6") else "5" if s.startswith("5") else None


def ping(host):
    """¿Responde al ping? (comando del sistema: ICMP directo necesita root). / Does it answer ping? (system command)."""
    h = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    try:
        r = subprocess.run(["ping", "-c1", "-W2", h], capture_output=True, text=True, timeout=5, check=False)  # nosec B603 B607 - fixed command, validated host
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _ap(key, name, **kw):
    out = {"key": key, "name": name, "model": None, "fw": None, "serial": None, "ip": None, "mac": None, "uptime": None,
           "online": True, "radios": [], "ssids": [], "clients": None, "note": None}
    out.update(kw)
    return out


# =========================================================================== OpenWrt (ubus)
class Denied(APError):
    """ubus negó la llamada (sesión vencida o ACL de rpcd). / ubus refused the call (expired session or rpcd ACL)."""


class OpenWrtDriver:
    """ubus por HTTP. Ruta: /ubus (uhttpd-mod-ubus) o, si no existe, el ubus de LuCI (/cgi-bin/luci/admin/ubus, OpenWrt 19.07+).
    Radios e interfaces: luci-rpc getWirelessDevices (permitido a root en LuCI) o, sin LuCI, iwinfo devices/info. Clientes: iwinfo assoclist.
    Uso del canal: iwinfo survey, solo si el equipo lo permite.
    EN: ubus over HTTP. Path: /ubus (uhttpd-mod-ubus) or, if missing, LuCI's ubus (/cgi-bin/luci/admin/ubus, OpenWrt 19.07+).
        Radios and interfaces: luci-rpc getWirelessDevices (allowed to root in LuCI) or, without LuCI, iwinfo devices/info. Clients: iwinfo
        assoclist. Channel use: iwinfo survey, only if the device allows it."""
    PATHS = ("/ubus", "/cgi-bin/luci/admin/ubus")

    def __init__(self, cfg):
        self.cfg, self.sid, self.n, self.path = cfg, None, 0, None
        self.skip = set()       # llamadas que el equipo no permite: no se repiten (cada rechazo cuesta un login) / calls the device refuses: not repeated

    def _post(self, path, body):
        conn = http.client.HTTPConnection(self.cfg["host"], timeout=TIMEOUT)
        try:
            conn.request("POST", path, body, {"Content-Type": "application/json"})
            r = conn.getresponse()
            return r.status, r.read(4 * 1024 * 1024)
        finally:
            conn.close()

    def _call(self, sid, obj, method, args=None):
        self.n += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self.n, "method": "call", "params": [sid, obj, method, args or {}]}).encode()
        for path in ([self.path] if self.path else self.PATHS):
            st, text = self._post(path, body)
            if st == 404 and not self.path:
                continue                             # no uhttpd-mod-ubus: try LuCI's ubus / sin uhttpd-mod-ubus: se prueba el de LuCI
            if st != 200:
                raise APError(f"ubus: HTTP {st}")
            self.path = path
            break
        else:
            raise APError("ubus not found (install uhttpd-mod-ubus or LuCI)")
        try:
            d = json.loads(text)
        except ValueError:
            raise APError("ubus: answer is not JSON")
        err = d.get("error") if isinstance(d, dict) else None
        if err:
            # -32002: sin permiso (ACL); -32000/-32601: objeto o método que este firmware no tiene. / no permission; object or method missing.
            if (err or {}).get("code") in (-32002, -32000, -32601):
                raise Denied(f"ubus {obj}.{method}: " + _clean(err.get("message", "access denied"), 40).lower())
            raise APError("ubus: " + _clean((err or {}).get("message", "error"), 80))
        res = d.get("result") if isinstance(d, dict) else None
        if not isinstance(res, list) or not res:
            raise APError("ubus: unexpected answer")
        if res[0] == 6:
            if obj == "session":
                raise APError("wrong user or password")
            raise Denied(f"access denied to ubus {obj}.{method}")
        if res[0] != 0:
            raise APError(f"ubus {obj}.{method}: code {res[0]}")
        return res[1] if len(res) > 1 and isinstance(res[1], dict) else {}

    def _login(self):
        r = self._call("0" * 32, "session", "login", {"username": self.cfg.get("user") or "root", "password": self.cfg.get("password") or ""})
        self.sid = r.get("ubus_rpc_session")
        if not self.sid:
            raise APError("ubus: no session")

    def call(self, obj, method, args=None):
        if not self.sid:
            self._login()
            return self._call(self.sid, obj, method, args)
        try:
            return self._call(self.sid, obj, method, args)
        except Denied:
            self._login()                          # the session may have expired: one new login / la sesión pudo vencer: un nuevo login
            return self._call(self.sid, obj, method, args)

    def _ifaces(self):
        """[(radio, ifname, info)] de las interfaces en modo AP. getWirelessDevices también trae la clave del Wi-Fi: no se guarda.
        EN: AP-mode interfaces. getWirelessDevices also carries the Wi-Fi key: it is not kept."""
        out = []
        try:
            if "luci" in self.skip:
                raise Denied("skip")
            wd = self.call("luci-rpc", "getWirelessDevices")
            for rn, rv in sorted(wd.items()):
                if not isinstance(rv, dict):
                    continue
                rinfo = rv.get("iwinfo") or {}
                for i in rv.get("interfaces") or []:
                    iw, cf = i.get("iwinfo") or {}, i.get("config") or {}
                    if not i.get("ifname") or str(iw.get("mode") or cf.get("mode") or "").lower() not in ("master", "ap"):
                        continue
                    out.append((rn, _clean(i["ifname"], 32), {"ssid": iw.get("ssid") or cf.get("ssid"), "frequency": iw.get("frequency") or rinfo.get("frequency"),
                                                              "channel": iw.get("channel") or rinfo.get("channel"), "txpower": iw.get("txpower") or rinfo.get("txpower"),
                                                              "htmode": (rv.get("config") or {}).get("htmode")}))
            return out
        except Denied:
            self.skip.add("luci")                    # no LuCI: plain iwinfo from now on / sin LuCI: iwinfo directo en adelante
        for dev in (self.call("iwinfo", "devices").get("devices") or [])[:16]:
            dev = _clean(dev, 32)
            i = self.call("iwinfo", "info", {"device": dev}) if dev else {}
            if str(i.get("mode", "")).lower() in ("master", "ap"):
                out.append((dev, dev, i))
        return out

    def snapshot(self):
        board = self.call("system", "board")
        info = self.call("system", "info")
        rel = board.get("release") or {}
        radios, ssids, clients = {}, {}, []
        for rn, dev, i in self._ifaces()[:16]:
            band = band_of(i.get("frequency"))
            ssid = _clean(i.get("ssid"), 64)
            r = radios.setdefault(rn, {"band": band, "channel": _int(i.get("channel")), "width": _clean(i.get("htmode"), 16) or None,
                                       "txpower": _int(i.get("txpower")), "util": None, "clients": 0})
            if r["util"] is None and "survey" not in self.skip:
                try:
                    for s in self.call("iwinfo", "survey", {"device": dev}).get("results") or []:
                        if _int(s.get("mhz")) == _int(i.get("frequency")) and _int(s.get("active_time")):
                            r["util"] = round(100 * (_int(s.get("busy_time")) or 0) / _int(s["active_time"]))
                except APError:
                    self.skip.add("survey")        # optional (older firmware or ACL): not asked again / opcional: no se vuelve a pedir
            if ssid:
                ssids.setdefault(ssid, set()).add(band)
            for c in (self.call("iwinfo", "assoclist", {"device": dev}).get("results") or [])[:256]:
                rate = ((c.get("rx") or {}).get("rate"), (c.get("tx") or {}).get("rate"))
                sig, noise = _int(c.get("signal")), _int(c.get("noise"))
                clients.append({"mac": _clean(c.get("mac"), 17).lower(), "band": band, "ssid": ssid, "signal": sig,
                                "snr": sig - noise if sig and noise else None, "rate": round(max(_int(x) or 0 for x in rate) / 1000) or None,
                                "connected": _int(c.get("connected_time")), "quality": None})
                r["clients"] += 1
        return [_ap("main", self.cfg["name"], model=_clean(board.get("model"), 64) or None, fw=_clean(rel.get("description") or rel.get("version"), 64) or None,
                    ip=self.cfg["host"], uptime=_int(info.get("uptime")), radios=sorted(radios.values(), key=lambda x: str(x["band"])),
                    ssids=[{"name": k, "bands": sorted(b for b in v if b)} for k, v in sorted(ssids.items())], clients=clients)]


# =========================================================================== MitraStar (Movistar Smart WiFi)
# ES: La sesión de este equipo va por la IP del cliente (sin cookies). Login: POST index.cgi con login_password = md5(clave + ":" + sid),
#     donde sid viene en la misma página. Después de leer se llama a logout.cgi para no dejar la sesión tomada.
# EN: This unit tracks the session by client IP (no cookies). Login: POST index.cgi with login_password = md5(password + ":" + sid),
#     sid coming in that same page. After reading, logout.cgi is called so the session is not left taken.
MS_LABELS = ("Nombre del equipo", "Modelo", "Serial Number", "Versión Hardware", "Versión Software", "Versión Firmware", "Código de país",
             "Estado", "Información Red WiFi Plus", "Estado WiFi", "Identificador Red Inalámbrica (SSID)", "Modo", "Ocultar SSID",
             "Tipo cifrado", "Encriptación", "Canal Uso", "Información Red Local", "Dirección IP (Gateway)", "Máscara de subred",
             "Cliente DHCP", "Información Red WiFi", "©")


def _text(html):
    html = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    html = re.sub(r"<[^>]+>", " ", html)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        html = html.replace(a, b)
    return re.sub(r"\s+", " ", html).strip()


def parse_mitrastar(html):
    """Datos de sysinfo.cgi. La página repite etiquetas (una vez por banda): se leen en orden. / Data from sysinfo.cgi, labels in order."""
    text = _text(html)
    if "Información de equipo" in text:
        text = text[text.index("Información de equipo"):]
    pat = "|".join(re.escape(x) for x in sorted(MS_LABELS, key=len, reverse=True))
    parts = re.split(r"(" + pat + r")\s*:?", text)
    vals, section = {}, "dev"
    for i in range(1, len(parts) - 1, 2):
        lab, val = parts[i], parts[i + 1].strip()
        if lab == "Información Red WiFi Plus":
            section = "5"
        elif lab == "Información Red WiFi":
            section = "2.4"
        elif lab == "Información Red Local":
            section = "lan"
        else:
            vals.setdefault((section, lab), _clean(val, 64))
    radios, ssids = [], []
    for b in ("2.4", "5"):
        ch, ssid = _int(vals.get((b, "Canal Uso"))), vals.get((b, "Identificador Red Inalámbrica (SSID)"))
        if ch or ssid:
            radios.append({"band": b, "channel": ch, "width": None, "txpower": None, "util": None, "clients": None})
        if ssid:
            ssids.append({"name": ssid, "bands": [b]})
    if not vals.get(("dev", "Modelo")):
        raise APError("unexpected page (is this a MitraStar Smart WiFi?)")
    return {"model": vals.get(("dev", "Modelo")), "fw": vals.get(("dev", "Versión Software")) or vals.get(("dev", "Versión Firmware")),
            "serial": vals.get(("dev", "Serial Number")), "mode": vals.get(("dev", "Estado")), "radios": radios, "ssids": ssids}


class MitraStarDriver:
    def __init__(self, cfg):
        self.cfg, self.cookies = cfg, {}

    def _req(self, path, data=None):
        """Una petición. Las cookies que entrega el equipo (la de sesión es HttpOnly) se guardan y se reenvían.
        EN: One request. Cookies the unit hands out (the session one is HttpOnly) are kept and sent back."""
        conn = http.client.HTTPConnection(self.cfg["host"], timeout=TIMEOUT)
        try:
            hdr = {"Content-Type": "application/x-www-form-urlencoded"} if data is not None else {}
            if self.cookies:
                hdr["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
            conn.request("POST" if data is not None else "GET", "/" + path.lstrip("/"), urllib.parse.urlencode(data) if data is not None else None, hdr)
            r = conn.getresponse()
            for c in r.msg.get_all("Set-Cookie") or []:
                k, _, v = c.split(";", 1)[0].strip().partition("=")
                if k and len(self.cookies) < 16:
                    self.cookies[_clean(k, 64)] = _clean(v, 512)
            return r.status, r.read(1024 * 1024).decode("utf-8", "replace"), r.getheader("Location") or ""
        finally:
            conn.close()

    def snapshot(self):
        if self.cfg.get("mode") == "ping":
            return [_ap("main", self.cfg["name"], ip=self.cfg["host"], online=ping(self.cfg["host"]), note="ping")]
        self.cookies = {}                         # each reading is a new session / cada lectura es una sesión nueva
        _, page, _ = self._req("index.cgi")
        m = re.search(r"var\s+sid\s*=\s*'([0-9A-Fa-f]{4,64})'", page)
        if not m:
            raise APError("login page without sid (is this a MitraStar Smart WiFi?)")
        st, page, loc = self._req("index.cgi", {"login_password_old": "", "submitValue": "1",
                                                "login_password": _md5((self.cfg.get("password") or "") + ":" + m.group(1))})
        # ES: Con la clave mala el equipo devuelve el login con el aviso «tab_fail» (no hay sesión que cerrar).
        # EN: With a wrong password the unit returns the login page with the "tab_fail" notice (no session to close).
        if 'id="tab_fail"' in page:
            raise APError("wrong password (the device said so; it is the one on the label unless it was changed)")
        try:
            # Como el navegador: se sigue la redirección del login (a wifi5g.cgi) antes de pedir la información. / Like the browser: follow it.
            if st in (301, 302, 303) and re.fullmatch(r"/?[A-Za-z0-9_]+\.cgi", loc or ""):
                self._req(loc)
            st2, html, loc2 = self._req("sysinfo.cgi")
            if st2 != 200 or "Información de equipo" not in html:
                # Clave aceptada pero sin sesión: el equipo admite una sola y otro (un navegador) la tiene. / Password accepted but no session.
                raise APError(f"password accepted, but the device sent its login page again (login HTTP {st}{' → ' + _clean(loc, 40) if loc else ''}, "
                              f"info HTTP {st2}{' → ' + _clean(loc2, 40) if loc2 else ''}, cookies: {', '.join(self.cookies) or 'none'}): it allows one session "
                              "at a time; close the device's web page in any browser (or wait for it to expire) and try again")
            d = parse_mitrastar(html)
        finally:
            try:
                self._req("logout.cgi")            # free the session for the browser / libera la sesión para el navegador
            except OSError:
                pass
        return [_ap("main", self.cfg["name"], model=d["model"], fw=d["fw"], serial=d["serial"], ip=self.cfg["host"],
                    radios=d["radios"], ssids=d["ssids"], note=d["mode"])]


# =========================================================================== HPE Aruba Instant On (portal en la nube / cloud portal)
# ES: API no oficial del portal. Login OAuth con PKCE: settings.json → POST mfa/validate/full (usuario y clave; la cuenta no puede tener 2FA)
#     → GET authorization.oauth2 sin seguir la redirección (código en Location) → POST token.oauth2. Las llamadas llevan Bearer y
#     x-ion-api-version. El token se reutiliza hasta que el portal responde 401.
# EN: Unofficial portal API. OAuth login with PKCE: settings.json → POST mfa/validate/full (user and password; the account cannot have 2FA)
#     → GET authorization.oauth2 without following the redirect (code in Location) → POST token.oauth2. Calls carry Bearer and
#     x-ion-api-version. The token is reused until the portal answers 401.
ION_PORTAL = os.environ.get("LABTOWER_INSTANTON_PORTAL", "https://portal.instant-on.hpe.com")
ION_API_VERSION = "7"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        return None


class InstantOnDriver:
    def __init__(self, cfg):
        self.cfg, self.token, self.settings = cfg, None, None
        self.ctx = ssl.create_default_context()

    def _open(self, req, follow=True):
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=self.ctx), *([] if follow else [_NoRedirect()]))
        return opener.open(req, timeout=TIMEOUT * 2)

    def _json(self, url, data=None, headers=None):
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data is not None else None, headers=headers or {})
        with self._open(req) as r:
            return json.loads(r.read(8 * 1024 * 1024))

    def _login(self):
        if not self.settings:
            self.settings = self._json(ION_PORTAL + "/settings.json")
        s = self.settings
        sso, cid, redir = s.get("ssoFqdn"), s.get("ssoClientIdAuthZ"), s.get("ssoRedirectUrl") or ION_PORTAL
        if not (isinstance(sso, str) and sso.startswith("https://") and cid):
            raise APError("Instant On: unexpected settings.json")
        try:
            sess = self._json(sso + "/aio/api/v1/mfa/validate/full", {"username": self.cfg.get("user", ""), "password": self.cfg.get("password", "")})
        except urllib.error.HTTPError as e:
            raise APError(f"Instant On: login refused (HTTP {e.code}): check the user and password, and that the account has no 2FA")
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        q = urllib.parse.urlencode({"client_id": cid, "redirect_uri": redir, "response_type": "code", "scope": "profile openid",
                                    "state": secrets.token_urlsafe(16), "code_challenge_method": "S256", "code_challenge": challenge,
                                    "sessionToken": sess.get("access_token", "")})
        loc = ""
        try:
            with self._open(urllib.request.Request(sso + "/as/authorization.oauth2?" + q), follow=False) as r:
                loc = r.headers.get("Location", "")
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location", "") if e.code in (301, 302, 303, 307, 308) else ""
        code = (urllib.parse.parse_qs(urllib.parse.urlparse(loc).query).get("code") or [""])[0]
        if not code:
            raise APError("Instant On: no authorization code (the portal login flow may have changed)")
        tok = self._json(sso + "/as/token.oauth2", {"client_id": cid, "redirect_uri": redir, "code": code, "code_verifier": verifier,
                                                     "grant_type": "authorization_code"})
        self.token = tok.get("access_token")
        if not self.token:
            raise APError("Instant On: no access token")

    def api(self, path):
        base = (self.settings or {}).get("restApiUrl") or ION_PORTAL
        for attempt in (0, 1):
            if not self.token:
                self._login()
                base = (self.settings or {}).get("restApiUrl") or ION_PORTAL
            req = urllib.request.Request(base.rstrip("/") + "/api/" + path, headers={"Authorization": "Bearer " + self.token, "x-ion-api-version": ION_API_VERSION})
            try:
                with self._open(req) as r:
                    return json.loads(r.read(16 * 1024 * 1024))
            except urllib.error.HTTPError as e:
                if e.code == 401 and attempt == 0:
                    self.token = None                # expired: log in again once / vencido: un nuevo login
                    continue
                raise APError(f"Instant On: HTTP {e.code} on {path.split('/')[-1]}")
        raise APError("Instant On: not authorised")

    def snapshot(self):
        if self.cfg.get("mode") == "ping":
            return [_ap("main", self.cfg["name"], ip=self.cfg["host"], online=ping(self.cfg["host"]), note="ping")]
        want = (self.cfg.get("site") or "").strip().lower()
        sites = [s for s in (self.api("sites").get("elements") or []) if isinstance(s, dict) and s.get("id")]
        if want:
            sites = [s for s in sites if str(s.get("name", "")).strip().lower() == want]
            if not sites:
                raise APError("Instant On: site not found")
        out = []
        for site in sites[:8]:
            sid = urllib.parse.quote(str(site["id"]), safe="")
            inv = [d for d in (self.api(f"sites/{sid}/inventory").get("elements") or []) if isinstance(d, dict) and d.get("deviceType") == "accessPoint"]
            try:
                cl = self.api(f"sites/{sid}/clientSummary").get("elements") or []
            except APError:
                cl = []                              # clients are optional / opcional
            by_ap = {}
            for c in cl:
                # Solo clientes Wi-Fi conectados: el portal también lista los que se fueron hace poco (sin SNR ni calidad).
                # EN: Connected Wi-Fi clients only: the portal also lists recently gone ones (no SNR or quality).
                if not isinstance(c, dict) or not c.get("wirelessNetworkId") or c.get("status", "up") != "up":
                    continue
                mac = _clean(c.get("macAddress"), 17).lower()
                ip = _clean(c.get("ipAddress"), 45)
                # Sin nombre conocido el portal repite la MAC: se deja vacío. / With no known name the portal repeats the MAC: left empty.
                name = next((_clean(x, 64) for x in (c.get("name"), c.get("hostName")) if x and _clean(x, 64).lower() != mac), None)
                by_ap.setdefault(str(c.get("deviceId") or "").lower(), []).append({
                    "mac": mac, "ip": ip if ip and ip != "0.0.0.0" else None,  # nosec B104 - an unknown IP as the portal reports it, not a bind
                    "name": name,
                    "band": band_of(name=c.get("wirelessBand")), "ssid": _clean(c.get("wirelessNetworkName"), 64) or None,
                    "signal": None, "snr": _int(c.get("snrInDb")), "rate": None, "connected": _int(c.get("stateDurationInSeconds")),
                    "quality": _clean(c.get("signalQuality"), 16) or None})
            for d in inv:
                mac = _clean(d.get("macAddress") or d.get("id"), 17).lower()
                radios = [{"band": band_of(name=r.get("band")), "channel": _int(r.get("channel")), "width": _clean(r.get("channelWidth"), 16) or None,
                           "txpower": _int(r.get("txPowerEirpInDbm")), "util": _int(r.get("utilizationPercent")), "clients": _int(r.get("wirelessClientsCount"))}
                          for r in (d.get("radios") or []) if isinstance(r, dict)]
                ssids = [{"name": _clean(n.get("networkName"), 64), "bands": sorted(b for b in (band_of(name=x) for x in n.get("enabledRadioBands") or []) if b)}
                         for n in (d.get("wirelessNetworks") or []) if isinstance(n, dict) and n.get("networkName")]
                up = d.get("uplinkSummary") or {}
                note = (f"mesh → {_clean(up.get('name'), 32)}" if up.get("radioBand") else None)
                out.append(_ap(f"{site['id']}:{mac}", _clean(d.get("name"), 32) or mac, model=_clean(d.get("model"), 32) or None,
                               fw=_clean(d.get("deviceSoftwareVersion"), 32) or None, serial=_clean(d.get("serialNumber"), 32) or None,
                               ip=_clean(d.get("ipAddress"), 45) or None, mac=mac, uptime=_int(d.get("uptimeInSeconds")),
                               online=d.get("status") == "up", radios=radios, ssids=ssids, clients=by_ap.get(mac, []), note=note))
        return out


# =========================================================================== UniFi (Ubiquiti, controlador UniFi Network)
# ES: Lee el controlador UniFi Network: UniFi OS (UDM, Cloud Key Gen2+, UniFi OS Server; login en /api/auth/login y la API bajo /proxy/network)
#     o el controlador clásico (login en /api/login). Usuario local, de preferencia de solo lectura. Dispositivos: stat/device (solo los «uap»);
#     clientes: stat/sta (solo Wi-Fi). Sin «verificar TLS» se FIJA la huella SHA-256 del certificado la primera vez (TOFU, como DNS Monitor) y, si
#     cambia, la conexión se corta antes de enviar la contraseña.
# EN: Reads the UniFi Network controller: UniFi OS (UDM, Cloud Key Gen2+, UniFi OS Server; login at /api/auth/login, API under /proxy/network)
#     or the classic controller (login at /api/login). Local user, preferably read-only. Devices: stat/device (only "uap"); clients: stat/sta
#     (Wi-Fi only). Without "verify TLS" the certificate's SHA-256 fingerprint is PINNED the first time (TOFU, like DNS Monitor) and, if it
#     changes, the connection is dropped before the password is sent.
UNIFI_BANDS = {"ng": "2.4", "na": "5", "6e": "6"}


class UniFiDriver:
    def __init__(self, cfg):
        self.cfg, self.cookies, self.csrf, self.prefix = cfg, {}, "", None
        self.on_pin = None                    # el gestor guarda la huella aprendida / the manager stores the learned fingerprint

    def _hostport(self):
        h = self.cfg["host"]
        return (h.rsplit(":", 1)[0], int(h.rsplit(":", 1)[1])) if h.count(":") == 1 else (h, 443)

    def _req(self, method, path, body=None):
        host, port = self._hostport()
        verify = bool(self.cfg.get("verify_tls"))
        ctx = ssl.create_default_context()
        if not verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE   # nosec B501 - not "any certificate": the fingerprint is pinned right below / se fija la huella
        conn = http.client.HTTPSConnection(host, port, timeout=TIMEOUT, context=ctx)
        try:
            conn.connect()
            if not verify:
                fp = hashlib.sha256(conn.sock.getpeercert(True)).hexdigest()
                pin = self.cfg.get("tls_pin") or ""
                if not pin:
                    self.cfg["tls_pin"] = fp
                    if self.on_pin:
                        self.on_pin(fp)
                elif pin != fp:
                    raise APError("UniFi: the controller's certificate changed (pinned fingerprint mismatch); nothing was sent. "
                                  "Edit and save the entry to learn it again")
            hdr = {"Accept": "application/json", "Content-Type": "application/json"}
            if self.cookies:
                hdr["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
            if self.csrf:
                hdr["X-CSRF-Token"] = self.csrf
            conn.request(method, path, json.dumps(body).encode() if body is not None else None, hdr)
            r = conn.getresponse()
            for c in r.msg.get_all("Set-Cookie") or []:
                k, _, v = c.split(";", 1)[0].strip().partition("=")
                if k and len(self.cookies) < 16:
                    self.cookies[_clean(k, 64)] = _clean(v, 4096)
            tok = r.getheader("X-Updated-CSRF-Token") or r.getheader("X-CSRF-Token")
            if tok:
                self.csrf = _clean(tok, 256)
            raw = r.read(16 * 1024 * 1024)
            try:
                data = json.loads(raw) if raw else {}
            except ValueError:
                data = {}
            return r.status, data
        except ssl.SSLError as e:
            raise APError(f"UniFi: TLS error ({e.reason or e}); without \"verify TLS\" the fingerprint is pinned instead")
        finally:
            conn.close()

    def _login(self):
        self.cookies, self.csrf = {}, ""
        cred = {"username": self.cfg.get("user") or "", "password": self.cfg.get("password") or ""}
        st, _ = self._req("POST", "/api/auth/login", dict(cred, remember=False))     # UniFi OS
        if st == 200:
            self.prefix = "/proxy/network"
            return
        if st in (401, 403):
            raise APError("UniFi: wrong user or password (local account; accounts with 2FA cannot be used)")
        st, _ = self._req("POST", "/api/login", cred)                                 # classic controller / controlador clásico
        if st == 200:
            self.prefix = ""
            return
        raise APError("UniFi: wrong user or password" if st in (400, 401, 403) else f"UniFi: login answered HTTP {st}")

    def api(self, path):
        site = urllib.parse.quote(self.cfg.get("site") or "default", safe="")
        for attempt in (0, 1):
            if self.prefix is None:
                self._login()
            st, d = self._req("GET", f"{self.prefix}/api/s/{site}/{path}")
            if st == 401 and attempt == 0:
                self.prefix = None                   # the session expired: log in again once / la sesión venció: un nuevo login
                continue
            if st == 400 and "NoSiteContext" in json.dumps(d):
                raise APError("UniFi: site not found (use the site id, e.g. \"default\")")
            if st != 200:
                raise APError(f"UniFi: HTTP {st} on {path}")
            return d.get("data") if isinstance(d, dict) and isinstance(d.get("data"), list) else []
        raise APError("UniFi: not authorised")

    def snapshot(self):
        if self.cfg.get("mode") == "ping":
            return [_ap("main", self.cfg["name"], ip=self.cfg["host"], online=ping(self.cfg["host"]), note="ping")]
        devs = [d for d in self.api("stat/device") if isinstance(d, dict) and d.get("type") == "uap"]
        try:
            stas = [c for c in self.api("stat/sta") if isinstance(c, dict) and not c.get("is_wired")]
        except APError:
            stas = []                                # clients are optional / opcional
        by_ap = {}
        for c in stas:
            sig, noise = _int(c.get("signal")), _int(c.get("noise"))
            by_ap.setdefault(_clean(c.get("ap_mac"), 17).lower(), []).append({
                "mac": _clean(c.get("mac"), 17).lower(), "ip": _clean(c.get("ip"), 45) or None,
                "name": _clean(c.get("name") or c.get("hostname"), 64) or None, "band": UNIFI_BANDS.get(c.get("radio")),
                "ssid": _clean(c.get("essid"), 64) or None, "signal": sig, "snr": sig - noise if sig and noise else None,
                "rate": round((_int(c.get("tx_rate")) or 0) / 1000) or None, "connected": _int(c.get("uptime")), "quality": None})
        out = []
        for d in devs:
            mac = _clean(d.get("mac"), 17).lower()
            width = {r.get("radio"): r.get("ht") for r in d.get("radio_table") or [] if isinstance(r, dict)}
            radios = [{"band": UNIFI_BANDS.get(r.get("radio")), "channel": _int(r.get("channel")),
                       "width": f"{_int(width.get(r.get('radio')))} MHz" if _int(width.get(r.get("radio"))) else None,
                       "txpower": _int(r.get("tx_power")), "util": _int(r.get("cu_total")), "clients": _int(r.get("num_sta"))}
                      for r in d.get("radio_table_stats") or [] if isinstance(r, dict)]
            ssids = {}
            for v in d.get("vap_table") or []:
                if isinstance(v, dict) and v.get("essid"):
                    ssids.setdefault(_clean(v["essid"], 64), set()).add(UNIFI_BANDS.get(v.get("radio")))
            up = d.get("uplink") or {}
            note = f"mesh → {_clean(up.get('uplink_device_name'), 32)}" if up.get("type") == "wireless" and up.get("uplink_device_name") else None
            out.append(_ap(mac or _clean(d.get("_id"), 32), _clean(d.get("name"), 32) or _clean(d.get("model"), 32) or mac,
                           model=_clean(d.get("model"), 32) or None, fw=_clean(d.get("version"), 32) or None, serial=_clean(d.get("serial"), 32) or None,
                           ip=_clean(d.get("ip"), 45) or None, mac=mac, uptime=_int(d.get("uptime")), online=d.get("state") == 1,
                           radios=sorted(radios, key=lambda x: str(x["band"])),
                           ssids=[{"name": k, "bands": sorted(b for b in v if b)} for k, v in sorted(ssids.items())],
                           clients=by_ap.get(mac, []), note=note))
        return out


def build_driver(cfg):
    return {"openwrt": OpenWrtDriver, "mitrastar": MitraStarDriver, "instanton": InstantOnDriver, "unifi": UniFiDriver}[cfg["driver"]](cfg)


# =========================================================================== Configuración / configuration
def redact(cfg):
    out = {k: v for k, v in cfg.items() if k not in ("password", "tls_pin")}
    out["pinned"] = bool(cfg.get("tls_pin"))
    out["has_password"] = bool(cfg.get("password"))
    return out


def validate(body, current=None):
    """Valida «guardar» o «probar». Una clave vacía al editar conserva la guardada.
    EN: Validate "save" / "test". An empty password while editing keeps the stored one."""
    cur = current or {}
    name = _clean(body.get("name", cur.get("name", "")), 32)
    if not NAME_RE.match(name):
        raise ValueError("Invalid name (letters, digits, space . _ - ; up to 32)")
    driver = body.get("driver", cur.get("driver"))
    if driver not in DRIVERS:
        raise ValueError("Invalid type (openwrt, mitrastar, instanton or unifi)")
    mode = body.get("mode", cur.get("mode") if cur.get("driver") == driver else None) or DRIVERS[driver][0]
    if mode not in DRIVERS[driver]:
        raise ValueError("Invalid mode for this type")
    cfg = {"id": cur.get("id", ""), "name": name, "driver": driver, "mode": mode, "enabled": bool(body.get("enabled", cur.get("enabled", True)))}
    if driver == "instanton" and mode == "cloud":
        user = _clean(body.get("user", cur.get("user", "")), 128)
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", user):
            raise ValueError("Instant On account e-mail required")
        cfg["user"] = user
        cfg["site"] = _clean(body.get("site", cur.get("site", "")), 64)
    else:
        host = _clean(body.get("host", cur.get("host", "")), 255)
        if not HOST_RE.match(host) or (mode == "ping" and ":" in host):
            raise ValueError("Invalid host (IP or name" + ("" if mode == "ping" else ", optional :port") + ")")
        if not auth.valid_target(host.rsplit(":", 1)[0] if host.count(":") == 1 else host):
            raise ValueError("Invalid host (this machine and link-local addresses are not allowed)")
        cfg["host"] = host
        if driver == "openwrt":
            cfg["user"] = _clean(body.get("user", cur.get("user", "root")), 64) or "root"
        if driver == "unifi" and mode == "controller":
            # Usuario local del controlador y sitio («default» si se deja vacío). La huella fijada se conserva mientras no se edite la entrada
            # (pausar o reanudar no la toca); guardar desde «Editar» la vuelve a aprender en la próxima lectura.
            # EN: Controller local user and site ("default" if empty). The pinned fingerprint is kept unless the entry is edited (pause or
            #     resume leave it); saving from "Edit" learns it again on the next read.
            cfg["user"] = _clean(body.get("user", cur.get("user", "")), 64)
            if not cfg["user"]:
                raise ValueError("UniFi controller user required")
            cfg["site"] = _clean(body.get("site", cur.get("site", "")), 64) or "default"
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", cfg["site"]):
                raise ValueError("Invalid UniFi site id (letters, digits, _ and -)")
            cfg["verify_tls"] = bool(body.get("verify_tls", cur.get("verify_tls", False)))
            if cur.get("tls_pin") and "host" not in body and cur.get("host") == host:
                cfg["tls_pin"] = cur["tls_pin"]
    if mode != "ping":
        pw = body.get("password") or (cur.get("password") if cur.get("driver") == driver else "") or ""
        if not pw or len(pw) > 128 or not pw.isprintable():
            raise ValueError("Password required (up to 128 characters)")
        cfg["password"] = pw
    return cfg


def _atomic_json(path, data):
    tmp = str(path) + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


class _Worker:
    def __init__(self):
        self.stop, self.ev, self.thread, self.sig = False, threading.Event(), None, ""


# =========================================================================== Gestor / Manager
# ES: Guarda las entradas en aps.json (modo 600), lee cada una en su propio hilo cada POLL segundos y arma la respuesta de la pestaña «AP».
#     Único aviso: AP caído (y su vuelta), como evento del panel. Una entrada pausada no se lee ni avisa.
# EN: Keeps the entries in aps.json (mode 600), reads each one in its own thread every POLL seconds and builds the "AP" tab response.
#     Only alert: AP down (and back), as a panel event. A paused entry is neither read nor alerted.
class Manager:
    def __init__(self, data_dir, hooks=None, log=None):
        self.dir = Path(data_dir)
        self.conf_file = self.dir / "aps.json"
        self.hooks, self.log = hooks or {}, log
        self.lock = threading.RLock()
        self.rec, self.workers = {}, {}
        self.cfg = {"poll_seconds": POLL_DEFAULT, "aps": []}
        self._stopped = False
        self.load()

    def _say(self, level, msg):
        if self.log:
            getattr(self.log, level)(msg)

    def load(self):
        try:
            d = json.loads(self.conf_file.read_text())
            if isinstance(d, dict) and isinstance(d.get("aps"), list):
                d["aps"] = [a for a in d["aps"] if isinstance(a, dict) and a.get("id") and a.get("driver") in DRIVERS]
                d["poll_seconds"] = min(POLL_MAX, max(POLL_MIN, int(d.get("poll_seconds") or POLL_DEFAULT)))
                self.cfg = d
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError) as e:
            self._say("warning", f"aps.json unreadable: {e}")

    def _save(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        _atomic_json(self.conf_file, self.cfg)

    def poll_seconds(self):
        return self.cfg.get("poll_seconds", POLL_DEFAULT)

    def _find(self, aid):
        return next((a for a in self.cfg["aps"] if a["id"] == aid), None)

    def list_config(self):
        with self.lock:
            return {"poll_seconds": self.poll_seconds(), "aps": [redact(a) for a in self.cfg["aps"]]}

    def set_poll(self, seconds):
        try:
            seconds = int(seconds)
        except (TypeError, ValueError):
            raise ValueError("Invalid interval")
        if not POLL_MIN <= seconds <= POLL_MAX:
            raise ValueError(f"Interval must be between {POLL_MIN} and {POLL_MAX} seconds")
        with self.lock:
            self.cfg["poll_seconds"] = seconds
            self._save()
        for w in list(self.workers.values()):
            w.ev.set()

    def save(self, body):
        with self.lock:
            cur = self._find(body.get("id")) if body.get("id") else None
            if body.get("id") and not cur:
                raise ValueError("AP not found")
            cfg = validate(body, cur)
            for a in self.cfg["aps"]:
                if a["name"].lower() == cfg["name"].lower() and a["id"] != cfg["id"]:
                    raise ValueError("An entry with that name already exists")
            if cur:
                cur.clear()
                cur.update(cfg)
            else:
                base = re.sub(r"[^a-z0-9]+", "-", cfg["name"].lower()).strip("-") or "ap"
                aid, n = base, 1
                while self._find(aid):
                    n += 1
                    aid = f"{base}-{n}"
                cfg["id"] = aid
                self.cfg["aps"].append(cfg)
            self._save()
            out = redact(cfg)
        self.reconcile()
        return out

    def delete(self, aid):
        with self.lock:
            cur = self._find(aid)
            if not cur:
                raise ValueError("AP not found")
            self.cfg["aps"].remove(cur)
            self.rec.pop(aid, None)
            self._save()
        self.reconcile()

    def test(self, body):
        """Una lectura de prueba con los datos del formulario. / One test read with the form data."""
        with self.lock:
            cur = self._find(body.get("id")) if body.get("id") else None
        cfg = validate(body, cur)
        t0 = time.time()
        aps = build_driver(cfg).snapshot()
        return {"ok": True, "aps": len(aps), "online": sum(1 for a in aps if a["online"]), "model": aps[0]["model"] if aps else None,
                "clients": sum(len(a["clients"]) for a in aps if a["clients"] is not None) if any(a["clients"] is not None for a in aps) else None,
                "seconds": round(time.time() - t0, 1)}

    # ---- hilos / threads
    def start(self):
        self.reconcile()

    def stop(self):
        self._stopped = True
        for w in self.workers.values():
            w.stop = True
            w.ev.set()

    def reconcile(self):
        """Un hilo por entrada activa; reinicia el de las que cambiaron. / One thread per active entry; restart changed ones."""
        with self.lock:
            want = {a["id"]: json.dumps(a, sort_keys=True) for a in self.cfg["aps"] if a.get("enabled", True)}
            for aid in list(self.workers):
                w = self.workers[aid]
                if aid not in want or w.sig != want[aid]:
                    w.stop = True
                    w.ev.set()
                    del self.workers[aid]
            for i, (aid, sig) in enumerate(want.items()):
                if aid in self.workers:
                    continue
                w = _Worker()
                w.sig = sig
                w.thread = threading.Thread(target=self._loop, args=(aid, json.loads(sig), w, 2 + 3 * i), daemon=True, name=f"ap-{aid}")
                self.workers[aid] = w
                w.thread.start()

    def refresh(self):
        """«Actualizar ahora»: respeta POLL_MIN entre lecturas. / "Refresh now": at least POLL_MIN between reads."""
        n = 0
        with self.lock:
            for aid, w in self.workers.items():
                r = self.rec.get(aid)
                if not r or time.time() - r.get("try_ts", 0) >= POLL_MIN:
                    w.ev.set()
                    n += 1
        return n

    def _loop(self, aid, cfg, w, delay):
        if delay and w.ev.wait(delay) and w.stop:
            return
        w.ev.clear()
        drv = build_driver(cfg)
        if hasattr(drv, "on_pin"):
            drv.on_pin = lambda fp: self._learn_pin(aid, cfg, fp, w)
        while not w.stop and not self._stopped:
            with self.lock:
                self.rec.setdefault(aid, {"aps": [], "ok_ts": 0, "err": None, "fails": 0, "try_ts": 0})["try_ts"] = time.time()
            try:
                self._ingest(aid, cfg, drv.snapshot())
            except Exception as e:  # noqa: BLE001 - se anota y se reintenta / logged and retried
                self._fail(aid, cfg, e)
            w.ev.wait(self.poll_seconds())
            w.ev.clear()

    def _learn_pin(self, aid, cfg, fp, w):
        """Guarda la huella aprendida sin reiniciar el hilo. / Store the learned fingerprint without restarting the thread."""
        with self.lock:
            cur = self._find(aid)
            if cur and not cur.get("tls_pin") and cur.get("host") == cfg.get("host"):
                cur["tls_pin"] = fp
                self._save()
                w.sig = json.dumps(cur, sort_keys=True)
                self._say("info", f"[{cur['name']}] certificate fingerprint pinned ({fp[:16]}…)")

    def _event(self, level, text, key, **params):
        fn = self.hooks.get("event")
        if fn:
            try:
                fn("net", level, text, key, **params)
            except Exception as e:  # noqa: BLE001
                self._say("debug", f"event hook: {e}")

    def _down(self, key, name, down):
        fn = self.hooks.get("changed")
        if fn and fn(f"ap-dn:{key}", "down" if down else "up"):
            if down:
                self._event("crit", f"{name}: access point unreachable", "ap_down", n=name)
            else:
                self._event("info", f"{name}: access point reachable again", "ap_up", n=name)

    def _fail(self, aid, cfg, err):
        msg = f"{type(err).__name__}: {err}"[:200] if not isinstance(err, APError) else str(err)[:200]
        with self.lock:
            rec = self.rec.setdefault(aid, {"aps": [], "ok_ts": 0, "err": None, "fails": 0, "try_ts": 0})
            rec["err"], rec["fails"] = msg, rec["fails"] + 1
            fails, aps = rec["fails"], list(rec["aps"])
        self._say("warning", f"[{cfg['name']}] {msg}")
        if fails >= FAILS_FOR_DOWN:
            for a in aps or [_ap("main", cfg["name"])]:
                self._down(f"{aid}:{a['key']}", a["name"], True)

    def _ingest(self, aid, cfg, aps):
        with self.lock:
            rec = self.rec.setdefault(aid, {"aps": [], "ok_ts": 0, "err": None, "fails": 0, "try_ts": 0})
            prev = {a["key"]: a for a in rec["aps"]}
            for a in aps:                                   # an AP must fail twice in a row, like a failed read / dos veces seguidas
                a["fails"] = 0 if a["online"] else (prev.get(a["key"], {}).get("fails", 0) + 1)
            rec.update(aps=aps, ok_ts=time.time(), err=None, fails=0)
        for a in aps:
            if a["online"]:
                self._down(f"{aid}:{a['key']}", a["name"], False)
            elif a["fails"] >= FAILS_FOR_DOWN:
                self._down(f"{aid}:{a['key']}", a["name"], True)

    def state(self, serials=False):
        """Lista plana de AP. Sin el permiso de números de serie, el campo serial va vacío.
        EN: Flat AP list. Without the serial-number permission, the serial field is empty."""
        hosts = {}
        try:
            hosts = self.hooks["hosts"]() if self.hooks.get("hosts") else {}
        except Exception as e:  # noqa: BLE001
            self._say("debug", f"hosts hook: {e}")
        now = time.time()
        out = []
        with self.lock:
            for cfg in self.cfg["aps"]:
                aid = cfg["id"]
                rec = self.rec.get(aid) or {"aps": [], "ok_ts": 0, "err": None, "fails": 0}
                paused = not cfg.get("enabled", True)
                failing = rec["fails"] >= FAILS_FOR_DOWN
                aps = rec["aps"] or [_ap("main", cfg["name"], ip=cfg.get("host"), online=False)]
                for a in aps:
                    clients = None
                    if a["clients"] is not None:
                        clients = []
                        for c in a["clients"]:
                            h = hosts.get(re.sub(r"[^0-9a-f]", "", c["mac"])) or {}
                            clients.append({**c, "ip": c.get("ip") or h.get("ip"), "name": h.get("name") or c.get("name")})
                    online = bool(rec["ok_ts"]) and not failing and a["online"]
                    down = not paused and bool(rec["ok_ts"] or failing) and not online and (failing or a.get("fails", 0) >= FAILS_FOR_DOWN)
                    out.append({**{k: v for k, v in a.items() if k not in ("clients", "fails", "serial")},
                                "serial": a.get("serial") if serials else None,
                                "id": aid, "entry": cfg["name"], "driver": cfg["driver"], "mode": cfg.get("mode"), "host": cfg.get("host"),
                                "paused": paused, "online": online, "down": down, "waiting": not paused and not rec["ok_ts"] and not failing,
                                "error": rec["err"], "updated": int(rec["ok_ts"]) or None, "clients": clients,
                                "nclients": len(clients) if clients is not None else (sum(r["clients"] or 0 for r in a["radios"]) if any(r.get("clients") is not None for r in a["radios"]) else None)})
        return {"aps": out, "poll_seconds": self.poll_seconds(), "now": int(now)}
