"""
Proxmox Monitor — diagnóstico de cluster: reinicios de nodos, quórum de corosync, OSD de Ceph y SMART.
Funciones puras (sin red ni disco) para poder probarlas con datos de ejemplo; server.py las usa con la API real.
EN: Proxmox Monitor — cluster diagnostics: node reboots, corosync quorum, Ceph OSDs and SMART.
    Pure functions (no network, no disk) so they can be tested with sample data; server.py uses them with the real API.
"""
import re

REBOOT_JITTER = 90          # s: the boot time computed from "uptime" wobbles by a few seconds between polls
GROUP_WINDOW  = 600         # s: reboots of different nodes closer than this belong to the same "wave"
KEEP_REBOOTS  = 200

def _i(x, default=0):
    try:
        if isinstance(x, bool): return default
        return int(float(x))
    except (TypeError, ValueError, OverflowError):
        return default

def _s(x, n=80):
    return str(x)[:n] if x is not None else ""

# ─── Reinicios ────────────────────────────────────────────────────────────────
# Compara la hora de arranque de cada nodo (ahora − uptime) con la última conocida. Si es más reciente que el margen,
# el nodo se reinició (aunque el módulo haya estado parado: el estado se guarda en disco). Devuelve los reinicios nuevos.
# EN: Compare each node's boot time (now − uptime) with the last known one. If it is newer than the margin, the node
#     rebooted (even if this module was stopped meanwhile: the state is kept on disk). Returns the new reboots.
def observe_boots(state, cid, cname, nodes, now):
    """state = {"boots": {"cid:node": boot_ts}, "reboots": [...]} (modified in place). Returns the list of new reboots."""
    boots = state.setdefault("boots", {})
    log = state.setdefault("reboots", [])
    new = []
    for nd in nodes or []:
        if not isinstance(nd, dict) or nd.get("status") != "online": continue
        name, up = _s(nd.get("name")), _i(nd.get("uptime"))
        if not name or up <= 0: continue
        boot = int(now) - up
        key = f"{cid}:{name}"
        old = boots.get(key)
        if isinstance(old, int) and boot - old > REBOOT_JITTER:
            r = {"cid": cid, "c": _s(cname), "n": name, "boot": boot, "seen": int(now), "prev": old}
            log.append(r); new.append(r)
            boots[key] = boot
        elif not isinstance(old, int) or boot < old - REBOOT_JITTER:
            boots[key] = boot                 # first sight (or clock correction): just remember
        # otherwise keep the first computed value: it must not creep with the polling jitter
    if len(log) > KEEP_REBOOTS: del log[:-KEEP_REBOOTS]
    return new

# Agrupa en «oleadas» los reinicios de nodos distintos cercanos en el tiempo. Cada elemento recibe `wave` (0 = reinicio aislado).
# EN: Group reboots of different nodes that are close in time into "waves". Each item gets `wave` (0 = isolated reboot).
def with_waves(reboots, window=GROUP_WINDOW):
    items = sorted((dict(r) for r in reboots if isinstance(r, dict)), key=lambda r: _i(r.get("boot")))
    wave = 0; i = 0
    while i < len(items):
        j = i
        while j + 1 < len(items) and items[j + 1]["cid"] == items[i]["cid"] and _i(items[j + 1]["boot"]) - _i(items[j]["boot"]) <= window:
            j += 1
        grp = items[i:j + 1]
        if len({g["n"] for g in grp}) >= 2:
            wave += 1
            for g in grp: g["wave"] = wave
        else:
            for g in grp: g["wave"] = 0
        i = j + 1
    return list(reversed(items))

# ─── Corosync ─────────────────────────────────────────────────────────────────
# Resume /cluster/status: quórum y miembros. Un cluster de un solo nodo no tiene entrada «cluster» (→ None).
# EN: Summarise /cluster/status: quorum and members. A single-node setup has no "cluster" entry (→ None).
def corosync_summary(status):
    if not isinstance(status, list): return None
    cl = next((x for x in status if isinstance(x, dict) and x.get("type") == "cluster"), None)
    if cl is None: return None
    members = []
    for x in status:
        if isinstance(x, dict) and x.get("type") == "node":
            members.append({"name": _s(x.get("name")), "online": bool(_i(x.get("online"))),
                            "ip": _s(x.get("ip"), 45), "id": _i(x.get("nodeid"))})
    members.sort(key=lambda m: (m["id"], m["name"]))
    return {"name": _s(cl.get("name")), "quorate": bool(_i(cl.get("quorate"))),
            "expected": _i(cl.get("nodes")) or len(members), "version": _i(cl.get("version")),
            "online": sum(1 for m in members if m["online"]), "members": members}

# ─── Ceph ─────────────────────────────────────────────────────────────────────
# Resume /cluster/ceph/status: salud, OSD (total/arriba/dentro) y los avisos activos con su gravedad.
# EN: Summarise /cluster/ceph/status: health, OSDs (total/up/in) and the active health checks with their severity.
def ceph_summary(ceph):
    if not isinstance(ceph, dict) or ceph.get("error"): return None
    health = ceph.get("health") if isinstance(ceph.get("health"), dict) else {}
    om = ceph.get("osdmap") if isinstance(ceph.get("osdmap"), dict) else {}
    om = om.get("osdmap") if isinstance(om.get("osdmap"), dict) else om          # older releases nest it
    checks = []
    raw = health.get("checks")
    if isinstance(raw, dict):
        for k, v in raw.items():
            if not isinstance(v, dict): continue
            s = v.get("summary")
            msg = s.get("message") if isinstance(s, dict) else s
            checks.append({"code": _s(k, 40), "sev": _s(v.get("severity"), 20), "msg": _s(msg, 160)})
    checks.sort(key=lambda c: (c["sev"] != "HEALTH_ERR", c["code"]))
    n, up, inn = _i(om.get("num_osds")), _i(om.get("num_up_osds")), _i(om.get("num_in_osds"))
    return {"health": _s(health.get("status"), 20), "osds": n, "up": up, "in": inn,
            "down": max(n - up, 0), "out": max(n - inn, 0), "checks": checks[:12]}

# ─── SMART ────────────────────────────────────────────────────────────────────
_NVME_FIELDS = (                                   # (clave, texto que busca en la salida de smartctl)
    ("unsafe",   r"Unsafe Shutdowns"),
    ("media_err", r"Media and Data Integrity Errors"),
    ("used_pct", r"Percentage Used"),
    ("spare",    r"Available Spare"),
    ("spare_thr", r"Available Spare Threshold"),
    ("temp",     r"Temperature"),
    ("crit",     r"Critical Warning"),
    ("poh",      r"Power On Hours"),
    ("cycles",   r"Power Cycles"),
)

def _num_after(label, text):
    m = re.search(r"^\s*" + label + r"\s*:\s*(0x[0-9a-fA-F]+|[\d,\.]+)", text, re.M | re.I)
    if not m: return None
    v = m.group(1).replace(",", "")
    try: return int(v, 16) if v.lower().startswith("0x") else int(float(v))
    except ValueError: return None

# Extrae los contadores útiles de la salida de texto de smartctl para NVMe («Unsafe Shutdowns», desgaste, errores…).
# EN: Extract the useful counters from smartctl's text output for NVMe ("Unsafe Shutdowns", wear, errors…).
def parse_nvme_text(text):
    text = text if isinstance(text, str) else ""
    out = {}
    for key, label in _NVME_FIELDS:
        # «Available Spare» must not swallow «Available Spare Threshold»: the label is anchored at the colon
        v = _num_after(label, text)
        if v is not None: out[key] = v
    return out

_ATA = {5: "realloc", 187: "uncorr", 188: "cmd_timeout", 196: "realloc_ev", 197: "pending", 198: "offline_unc",
        199: "crc", 9: "poh", 12: "cycles", 192: "retract", 174: "unsafe"}

# Lo mismo para discos SATA/SAS (atributos SMART por número). Para SSD con 174 (Unexpected Power Loss) se usa como «unsafe».
# EN: The same for SATA/SAS disks (SMART attributes by number). On SSDs, 174 (Unexpected Power Loss) is used as "unsafe".
def parse_ata_attrs(attrs):
    out = {}
    for a in attrs if isinstance(attrs, list) else []:
        if not isinstance(a, dict): continue
        k = _ATA.get(_i(a.get("id"), -1))
        raw = a.get("raw")
        m = re.match(r"\s*(\d+)", str(raw)) if raw is not None else None
        if k and m: out[k] = int(m.group(1))
        if _i(a.get("id"), -1) in (190, 194) and m and "temp" not in out: out["temp"] = int(m.group(1))
    return out

def _wear(w):
    if isinstance(w, bool): return None
    if isinstance(w, (int, float)): return int(w)
    try: return int(str(w).strip().rstrip("%"))
    except ValueError: return None

# Une la fila de /nodes/N/disks/list con la respuesta de /disks/smart en un registro plano y calcula avisos.
# EN: Merge a row of /nodes/N/disks/list with the /disks/smart answer into a flat record and compute warnings.
def summarize_disk(row, smart):
    row = row if isinstance(row, dict) else {}
    smart = smart if isinstance(smart, dict) else {}
    dev = _s(row.get("devpath"), 40)
    typ = _s(row.get("type"), 10).lower()
    health = _s(smart.get("health") or row.get("health"), 20).upper() or "UNKNOWN"
    d = {"dev": dev, "model": _s(row.get("model"), 60), "serial": _s(row.get("serial"), 40), "type": typ,
         "size": _i(row.get("size")), "health": health, "wearout": _wear(row.get("wearout"))}
    d.update(parse_nvme_text(smart.get("text")) if isinstance(smart.get("text"), str) else {})
    d.update(parse_ata_attrs(smart.get("attributes")))
    warns = []
    if health not in ("PASSED", "OK", "UNKNOWN"): warns.append("health")
    if d.get("media_err", 0) > 0: warns.append("media")
    if d.get("crit", 0) > 0: warns.append("critwarn")
    if d.get("pending", 0) > 0 or d.get("offline_unc", 0) > 0 or d.get("uncorr", 0) > 0: warns.append("sectors")
    if d.get("realloc", 0) > 0: warns.append("realloc")
    u = d.get("used_pct")
    if u is None and d["wearout"] is not None: u = 100 - d["wearout"]
    if u is not None and u >= 90: warns.append("wear")
    if "spare" in d and "spare_thr" in d and d["spare"] <= d["spare_thr"]: warns.append("spare")
    d["warns"] = warns
    return d

# Compara los «unsafe shutdowns» con la lectura anterior (guardada por número de serie): devuelve los discos cuyo contador subió.
# EN: Compare "unsafe shutdowns" with the previous reading (kept by serial number): returns the disks whose counter went up.
def unsafe_increases(state, cid, node, disks):
    base = state.setdefault("unsafe", {})
    up = []
    for d in disks:
        if "unsafe" not in d: continue
        key = f"{cid}:{node}:{d.get('serial') or d.get('dev')}"
        old = base.get(key)
        if isinstance(old, int) and d["unsafe"] > old:
            up.append({"dev": d["dev"], "model": d["model"], "was": old, "now": d["unsafe"]})
        base[key] = d["unsafe"]
    return up
