"""
Net Monitor — cambios de MAC en una IP, puertos nuevos, equipos conocidos, conectividad de cada equipo y latencia de los vigilados.
Funciones puras (sin red ni disco) para probarlas con datos de ejemplo.
EN: Net Monitor — MAC changes on an IP, new ports, known devices, per-device connectivity and latency of the watched ones.
    Pure functions (no network, no disk) so they can be tested with sample data.
"""
import math

# Puertos cuya aparición merece destacarse (acceso remoto, archivos compartidos y bases de datos).
# EN: Ports whose appearance deserves to be highlighted (remote access, file sharing and databases).
RISKY = {21, 23, 111, 135, 139, 445, 873, 1883, 2049, 3306, 3389, 5432, 5900, 6379, 27017}
MAX_SEEN = 80

def _num(x):
    try:
        if isinstance(x, bool) or x is None: return None
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError, OverflowError):
        return None

def _mac(m):
    s = "".join(c for c in str(m or "").lower() if c in "0123456789abcdef")
    return s if len(s) == 12 else ""

def same_mac(a, b):
    """Misma MAC aunque cambie el formato. / EN: Same MAC whatever the format."""
    a = _mac(a)
    return bool(a) and a == _mac(b)

# MAC que ya tuvo una IP: la guardada, la anterior y las de macs_seen. / EN: MACs an IP already had: the stored one, the previous one and macs_seen.
def _known_macs(existing):
    ex = existing if isinstance(existing, dict) else {}
    out = list(ex.get("macs_seen") or []) if isinstance(ex.get("macs_seen"), list) else []
    return out + [ex.get("mac_prev"), ex.get("mac")]

# La MAC de una IP que estaba conectada cambió en el siguiente escaneo: IP duplicada, equipo reemplazado o suplantación.
# Si el equipo estuvo desconectado entre medio no se avisa: el DHCP reparte la IP a otro equipo y es normal. Tampoco si esa MAC
# ya se vio antes en la IP: un equipo con dos tarjetas en la misma red puede contestar por cualquiera (ARP flux).
# EN: The MAC of an IP that was online changed by the next scan: duplicate IP, replaced device or spoofing.
#     Nothing is reported if the device was offline in between: DHCP handing the IP to another device is normal. Nor if that MAC
#     was already seen on the IP: a device with two cards on the same network may answer through either one (ARP flux).
#     Un registro anterior a macs_seen (actualización desde 2.1.9b o antes) solo aprende en su primer escaneo: la MAC pasó a leerse
#     primero de ARP y no de Pi-hole, y avisar ahí serían falsas alarmas. / EN: A record older than macs_seen (upgrade from 2.1.9b or
#     earlier) only learns on its first scan: the MAC is now read from ARP first instead of Pi-hole, and warning there would be false alarms.
def mac_change(existing, result):
    if not isinstance(existing, dict) or not isinstance(result, dict) or not existing.get("online"): return None
    if "macs_seen" not in existing: return None
    a, b = _mac(existing.get("mac")), _mac(result.get("mac"))
    if a and b and a != b and b not in {_mac(x) for x in _known_macs(existing)}:
        return {"old": existing.get("mac"), "new": result.get("mac")}
    return None

# MAC vistas en una IP (las MACS_MAX más recientes, sin repetir y en minúsculas). / EN: MACs seen on an IP (the MACS_MAX latest, unique, lower case).
MACS_MAX = 8
def macs_seen(existing, result):
    out = {}
    for m in _known_macs(existing) + [(result or {}).get("mac") if isinstance(result, dict) else None]:
        k = _mac(m)
        if k:
            out.pop(k, None); out[k] = str(m).lower().replace("-", ":")
    return list(out.values())[-MACS_MAX:]

# Puertos que este equipo nunca había mostrado. `ports_seen` acumula todos los vistos (un puerto que se cierra y se abre por un
# tiempo de espera no cuenta como nuevo). Un equipo sin lectura previa solo memoriza.
# EN: Ports this device had never shown. `ports_seen` accumulates every port seen (a port that closes and opens because of a
#     timeout does not count as new). A device with no previous reading only memorizes.
def port_news(existing, result):
    cur = {int(p["port"]) for p in (result or {}).get("ports") or [] if isinstance(p, dict) and _num(p.get("port")) is not None}
    ex = existing if isinstance(existing, dict) else {}
    seen = {int(p) for p in ex.get("ports_seen") or [] if _num(p) is not None}
    base = {int(p["port"]) for p in ex.get("ports") or [] if isinstance(p, dict) and _num(p.get("port")) is not None}
    known_before = bool(ex) and ("ports_seen" in ex or "ports" in ex)
    new = sorted(cur - seen - base) if known_before else []
    allseen = sorted(seen | base | cur)[:MAX_SEEN]
    return allseen, new

def known(h, baseline):
    """A device counts as known when it was marked, or when it was discovered before the feature existed (baseline)."""
    if not isinstance(h, dict): return False
    if h.get("known"): return True
    fs = _num(h.get("first_seen"))
    return bool(baseline and fs is not None and fs < baseline)

# Conectividad de un equipo a partir de su registro de «up»/«down» (un cambio por evento). Estado inicial: conectado desde que se descubrió;
# si el registro está recortado (200 eventos), el estado anterior al primer evento se deduce de él.
# EN: Connectivity of a device from its "up"/"down" log (one change per event). Initial state: online since discovery; if the log
#     is trimmed (200 events), the state before the first event is deduced from it.
def timeline(history, first_seen, online_now, now):
    ev = sorted([e for e in (history or []) if isinstance(e, dict) and e.get("event") in ("up", "down") and _num(e.get("ts")) is not None], key=lambda e: e["ts"])
    fs = _num(first_seen)
    if ev and fs is not None and ev[0]["ts"] < fs: fs = None
    if ev and (len(ev) >= 200 or fs is None):
        start, state = ev[0]["ts"], ev[0]["event"] == "down"          # before an "up" it was down; before a "down" it was up
    else:
        start, state = (fs if fs is not None else (ev[0]["ts"] if ev else now)), True
    segs, t = [], start
    for e in ev:
        if e["ts"] < start: continue
        if e["ts"] > t: segs.append((t, e["ts"], state))
        t, state = max(t, e["ts"]), e["event"] == "up"
    if now > t: segs.append((t, now, state))
    return segs

def conn_stats(history, first_seen, online_now, now, windows=(("7d", 7 * 86400), ("30d", 30 * 86400))):
    segs = timeline(history, first_seen, online_now, now)
    out = {}
    for label, w in windows:
        lo = max(now - w, segs[0][0]) if segs else now
        total = up = 0
        for a, b, s in segs:
            a2, b2 = max(a, lo), b
            if b2 <= a2: continue
            total += b2 - a2; up += (b2 - a2) if s else 0
        drops = sum(1 for e in history or [] if isinstance(e, dict) and e.get("event") == "down" and _num(e.get("ts")) is not None and e["ts"] >= now - w)
        out[label] = {"pct": round(100.0 * up / total, 2) if total >= 3600 else None, "drops": drops, "observed": int(total)}
    return out

def week_bar(history, first_seen, online_now, now, buckets=42, window=7 * 86400):
    """Share online in each of `buckets` slices of the last week (None where there is no data): small bar for the detail."""
    segs = timeline(history, first_seen, online_now, now)
    lo = now - window; step = window / buckets; out = []
    for i in range(buckets):
        a, b = lo + i * step, lo + (i + 1) * step
        tot = up = 0.0
        for s0, s1, st in segs:
            x, y = max(a, s0), min(b, s1)
            if y > x: tot += y - x; up += (y - x) if st else 0
        out.append(round(up / tot, 2) if tot > 0 else None)
    return out

def latency_summary(points):
    """points: [(ts, ms|None, ok)] of the watched device: mean, p95, max and loss."""
    n = len(points)
    if not n: return {"n": 0, "avg": None, "p95": None, "max": None, "loss": None}
    v = sorted(m for _, m, ok in points if ok and _num(m) is not None)
    p95 = v[min(len(v) - 1, math.ceil(0.95 * len(v)) - 1)] if v else None
    return {"n": n, "avg": round(sum(v) / len(v), 1) if v else None, "p95": round(p95, 1) if p95 is not None else None,
            "max": round(max(v), 1) if v else None, "loss": round(100.0 * sum(1 for _, _, ok in points if not ok) / n, 2)}

# ─── Datos editados a mano que siguen a la MAC ────────────────────────────────
# El alias, el grupo y el tipo y SO elegidos a mano se guardan por MAC (macs.json), no por IP: si el equipo cambia de IP los
# conserva, y si otro equipo toma esa IP no los hereda. Los equipos sin MAC conocida (p. ej. de otra subred) siguen por IP.
# «Conocido» y la vigilancia siguen ligados a la IP.
# EN: Alias, group and hand-picked type and OS are kept per MAC (macs.json), not per IP: a device that changes IP keeps them, and
#     another device taking that IP does not inherit them. Devices with no known MAC (e.g. on another subnet) stay per IP.
#     "Known" and watching stay tied to the IP.
PROFILES_MAX = 4096

def profile_of(h):
    """Lo editado a mano de un equipo. / EN: What was edited by hand on a device."""
    p = {"alias": str(h.get("alias") or ""), "group": str(h.get("group") or "")}
    if h.get("type_manual") and h.get("device_type"): p["device_type"] = h["device_type"]
    if h.get("os_manual") and h.get("os"): p["os"] = h["os"]
    return p

def _has_manual(p): return any(p.values())

def apply_profile(h, p):
    """Pone en el equipo lo guardado para su MAC. / EN: Put on the device what is kept for its MAC."""
    h["alias"] = p.get("alias", "")
    if p.get("group"): h["group"] = p["group"]
    else: h.pop("group", None)
    if p.get("device_type"): h["device_type"], h["type_manual"] = p["device_type"], True
    else: h.pop("type_manual", None)                       # back to auto-detection on the next scan
    if p.get("os"): h["os"], h["os_manual"] = p["os"], True
    else: h.pop("os_manual", None)

def same_device(existing, result):
    """ES: ¿el resultado del escaneo es el mismo equipo que ya estaba en esa IP? Sí si alguno no tiene MAC o si es la misma MAC; no si
    llegó otra MAC (otro equipo tomó la IP), y entonces no hereda lo editado a mano del anterior.
    EN: is the scan result the same device that was already on that IP? Yes when either has no MAC or it is the same MAC; no when
    another MAC arrived (another device took the IP), and then it does not inherit what was edited by hand on the previous one."""
    a, b = _mac((existing or {}).get("mac")), _mac((result or {}).get("mac"))
    return not a or not b or a == b

def sync_profiles(hosts, profiles):
    """ES: 1) adopta como perfil lo editado a mano de las MAC que aún no tienen uno (el equipo conectado o el visto más recientemente);
    2) aplica el perfil a todas las IP con esa MAC; 3) una IP desconectada cuya MAC responde en otra IP pierde el alias (el equipo se
    cambió de IP). Devuelve True si agregó perfiles (hay que guardar macs.json).
    EN: 1) adopts as profile what was edited by hand for MACs that still have none (the online device or the most recently seen);
    2) applies the profile to every IP with that MAC; 3) an offline IP whose MAC answers on another IP loses the alias (the device
    moved). Returns True when it added profiles (macs.json must be saved)."""
    rows = [(_mac(h.get("mac")), h) for h in hosts.values() if isinstance(h, dict)]
    rows = [(k, h) for k, h in rows if k]
    added = False
    best = {}
    for k, h in rows:
        if k in profiles or not _has_manual(profile_of(h)): continue
        rank = (bool(h.get("online")), _num(h.get("last_seen")) or 0)
        if k not in best or rank > best[k][0]: best[k] = (rank, h)
    for k, (_, h) in best.items():
        if len(profiles) >= PROFILES_MAX: break
        profiles[k] = profile_of(h); added = True
    online = {k for k, h in rows if h.get("online")}
    for k, h in rows:
        if k in profiles: apply_profile(h, profiles[k])
        if not h.get("online") and k in online: h["alias"] = ""
    return added

def set_profile(profiles, h):
    """ES: guarda lo editado a mano del equipo bajo su MAC; False si no tiene MAC (sigue por IP).
    EN: keeps what was edited by hand on the device under its MAC; False when it has no MAC (stays per IP)."""
    k = _mac(h.get("mac"))
    if not k or (k not in profiles and len(profiles) >= PROFILES_MAX): return False
    profiles[k] = profile_of(h)
    return True
