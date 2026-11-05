"""
Proxmox Monitor — información adicional: días hasta llenarse (almacenamiento / Ceph), cambios de estado de VM/CT, bloqueos
atascados, capacidad (sobreasignación y prueba N-1), HA, replicación, tareas fallidas, estado de PG de Ceph y datos por nodo
(versión, kernel, carga, swap, iowait, certificado). Funciones puras: sin red ni disco, para probarlas con datos de ejemplo.
EN: Proxmox Monitor — extra information: days until full (storage / Ceph), VM/CT state changes, stuck locks, capacity
    (overcommit and N-1 test), HA, replication, failed tasks, Ceph PG state and per-node data (version, kernel, load, swap,
    iowait, certificate). Pure functions: no network, no disk, so they can be tested with sample data.
"""
import re, math

LOCK_MIN        = 60          # min: a lock older than this is "stuck" (a running backup holds 'backup' much longer)
LOCK_BACKUP_MIN = 360
DAYS_WARN, DAYS_CRIT = 14, 3  # storage / Ceph days until full
CERT_WARN, CERT_CRIT = 21, 7  # days left on the node certificate
MEM_USABLE      = 0.9         # share of a node's RAM counted as usable for the N-1 test
IGNORE_TAG      = "labtower-ignore"
NOISE_TASKS     = {"vncproxy", "vncshell", "spiceproxy", "termproxy", "aptupdate"}
MAX_CHANGES     = 5           # more state changes than this in one pass are reported as a single summary event

def _n(x, default=None):
    try:
        if isinstance(x, bool) or x is None: return default
        v = float(x)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError, OverflowError):
        return default

def _i(x, default=0):
    v = _n(x)
    return int(v) if v is not None else default

def _s(x, n=80):
    return str(x)[:n] if x is not None else ""

# ─── Días hasta llenarse ──────────────────────────────────────────────────────
# points: [(ts, bytes_usados)] del más viejo al más nuevo. None si hay poco historial (< 2 días), no crece, es ruidoso o tardaría más de un año.
# EN: points: [(ts, used_bytes)] oldest first. None when there is little history (< 2 days), no growth, noise or more than a year away.
def days_to_full(points, free):
    n = len(points)
    free = _n(free)
    if n < 24 or free is None or free < 0: return None
    t0 = points[0][0]
    if points[-1][0] - t0 < 2 * 86400: return None
    xs = [(p[0] - t0) / 86400 for p in points]; ys = [float(p[1]) for p in points]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs); syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0 or sxy <= 0 or (sxy * sxy) / (sxx * syy) < 0.5: return None
    days = free / (sxy / sxx)
    return round(days, 1) if days <= 365 else None

def days_why(points):
    """Why days_to_full gave no answer: ('history', days collected) while there is not enough data yet, else ('flat', days collected)."""
    n = len(points); span = (points[-1][0] - points[0][0]) / 86400 if n > 1 else 0
    return ("history" if n < 24 or span < 2 else "flat"), round(span, 1)

def series_points(nodes, ceph):
    """{key: used_bytes} to store: one per storage (shared ones once), plus the Ceph cluster. key = 's:<storage>' / 's:<node>/<storage>' / 'ceph'."""
    out, seen = {}, set()
    for nd in nodes or []:
        if not isinstance(nd, dict) or nd.get("status") != "online": continue
        for st in nd.get("storage") or []:
            if not isinstance(st, dict) or not st.get("active"): continue
            tot, used = _n(st.get("total")), _n(st.get("used"))
            if not tot or used is None or tot <= 0: continue
            name = _s(st.get("storage"), 60)
            if not name: continue
            key = "s:" + name if st.get("shared") else f"s:{_s(nd.get('name'), 40)}/{name}"
            if key in seen: continue
            seen.add(key); out[key] = (used, tot)
    pg = (ceph or {}).get("pgmap") if isinstance(ceph, dict) else None
    if isinstance(pg, dict) and _n(pg.get("bytes_total")) and _n(pg.get("bytes_used")) is not None:
        out["ceph"] = (_n(pg["bytes_used"]), _n(pg["bytes_total"]))
    return out

def days_alerts(days_by_key, labels=None):
    """days_by_key: {key: days|None}. Alerts for the ones that fill in less than DAYS_WARN days."""
    out = []
    for k, d in sorted((days_by_key or {}).items()):
        if d is None or d > DAYS_WARN: continue
        name = (labels or {}).get(k) or k.split(":", 1)[-1]
        out.append({"type": "ceph_days" if k == "ceph" else "sto_days", "lv": "crit" if d <= DAYS_CRIT else "warn", "name": name, "value": d})
    return out

# ─── Cambios de estado de VM/CT ───────────────────────────────────────────────
# prev: {vmid: {"st", "name", "node"}} o None la primera vez (solo memoriza). Devuelve (estado nuevo, cambios).
# EN: prev: {vmid: {"st", "name", "node"}} or None the first time (it only remembers). Returns (new state, changes).
def guest_state(nodes):
    cur = {}
    for nd in nodes or []:
        if not isinstance(nd, dict) or nd.get("status") != "online": continue
        for kind, items in (("qemu", nd.get("vms")), ("lxc", nd.get("cts"))):
            for g in items or []:
                if not isinstance(g, dict) or g.get("template"): continue
                vmid = _i(g.get("vmid"))
                if vmid <= 0: continue
                if IGNORE_TAG in re.split(r"[;, ]+", _s(g.get("tags"), 200)): continue
                cur[vmid] = {"st": _s(g.get("status"), 20), "name": _s(g.get("name"), 60) or str(vmid), "node": _s(nd.get("name"), 40), "kind": kind}
    return cur

def guest_changes(prev, cur):
    if prev is None: return []
    ch = []
    for vmid, g in cur.items():
        p = prev.get(vmid)
        if p is None:
            ch.append({"vmid": vmid, "name": g["name"], "node": g["node"], "kind": g["kind"], "what": "new"})
        elif p["st"] != g["st"] and {p["st"], g["st"]} <= {"running", "stopped"}:
            ch.append({"vmid": vmid, "name": g["name"], "node": g["node"], "kind": g["kind"], "what": "start" if g["st"] == "running" else "stop"})
        elif p["node"] != g["node"]:
            ch.append({"vmid": vmid, "name": g["name"], "node": g["node"], "kind": g["kind"], "what": "moved", "from": p["node"]})
    # a node that is down hides its guests from the list: do not report them as deleted (no "gone" event on purpose)
    return sorted(ch, key=lambda c: c["vmid"])

# ─── Bloqueos atascados ───────────────────────────────────────────────────────
# state: {vmid: {"lock", "since"}} se modifica; devuelve las alertas de los bloqueos que pasaron el límite.
# EN: state: {vmid: {"lock", "since"}} is modified; returns the alerts for the locks past the limit.
def lock_alerts(state, nodes, now):
    seen, out = set(), []
    for nd in nodes or []:
        if not isinstance(nd, dict) or nd.get("status") != "online": continue
        for items in (nd.get("vms"), nd.get("cts")):
            for g in items or []:
                if not isinstance(g, dict): continue
                lk, vmid = _s(g.get("lock"), 30), _i(g.get("vmid"))
                if not lk or vmid <= 0: continue
                seen.add(vmid)
                cur = state.get(vmid)
                if not cur or cur["lock"] != lk: cur = state[vmid] = {"lock": lk, "since": int(now)}
                mins = int((now - cur["since"]) // 60)
                if mins >= (LOCK_BACKUP_MIN if lk == "backup" else LOCK_MIN):
                    out.append({"type": "lock", "lv": "warn", "node": _s(nd.get("name"), 40), "vmid": vmid, "name": _s(g.get("name"), 60) or str(vmid), "lock": lk, "mins": mins})
    present = {_i(g.get("vmid")) for nd in nodes or [] if isinstance(nd, dict) and nd.get("status") == "online"
               for g in (nd.get("vms") or []) + (nd.get("cts") or []) if isinstance(g, dict)}
    for v in [v for v in state if v not in seen and v in present]:     # an offline node keeps its entries
        state.pop(v, None)
    return out

# ─── Capacidad ────────────────────────────────────────────────────────────────
# vCPU y RAM asignadas a las VM/CT encendidas por nodo y prueba N-1: ¿caben todas si se cae el nodo más grande?
# EN: vCPU and RAM allocated to running VMs/CTs per node and the N-1 test: do they all fit if the biggest node goes down?
def capacity(nodes):
    per, total_mem, tot_max = [], 0, 0
    for nd in nodes or []:
        if not isinstance(nd, dict) or nd.get("status") != "online": continue
        vc = mem = 0
        for g in (nd.get("vms") or []) + (nd.get("cts") or []):
            if not isinstance(g, dict) or g.get("template") or g.get("status") != "running": continue
            vc += _i(g.get("cpus")); mem += _i(g.get("maxmem"))
        cpus, mm = _i(nd.get("maxcpu")), _i(nd.get("maxmem"))
        per.append({"node": _s(nd.get("name"), 40), "vcpu": vc, "cpus": cpus, "mem": mem, "maxmem": mm,
                    "cpu_ratio": round(vc / cpus, 2) if cpus else None, "mem_ratio": round(mem / mm, 2) if mm else None})
        total_mem += mem; tot_max += mm
    n1 = None
    if len(per) >= 2:
        big = max(per, key=lambda p: p["maxmem"])
        have = (tot_max - big["maxmem"]) * MEM_USABLE
        n1 = {"ok": total_mem <= have, "node": big["node"], "need": total_mem, "have": int(have)}
    return {"nodes": per, "n1": n1}

def capacity_alerts(cap):
    out = []
    n1 = cap.get("n1")
    if n1 and not n1["ok"]:
        out.append({"type": "n1", "lv": "warn", "node": n1["node"], "need": n1["need"], "have": n1["have"]})
    for p in cap.get("nodes", []):
        if p["mem_ratio"] is not None and p["mem_ratio"] > 1.0:
            out.append({"type": "overcommit", "lv": "warn", "node": p["node"], "value": round(p["mem_ratio"] * 100)})
    return out

# ─── HA ───────────────────────────────────────────────────────────────────────
# items: /cluster/ha/status/current. Servicios con estado malo y gestores (LRM) caídos.
# EN: items: /cluster/ha/status/current. Services in a bad state and dead managers (LRM).
BAD_HA = {"error", "fence", "recovery", "freeze"}
def ha_summary(items):
    services, bad = [], []
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict): continue
        t = it.get("type")
        if t == "service":
            s = {"sid": _s(it.get("sid"), 30), "state": _s(it.get("state"), 20), "node": _s(it.get("node"), 40), "status": _s(it.get("status"), 100)}
            services.append(s)
            if s["state"] in BAD_HA or "error" in s["status"].lower():
                bad.append({"type": "ha", "lv": "crit" if s["state"] in ("error", "fence") else "warn", "sid": s["sid"], "state": s["state"] or "error", "node": s["node"]})
        elif t == "lrm":
            st = _s(it.get("status"), 100).lower()
            if st.startswith(("old timestamp", "dead")):
                bad.append({"type": "ha_lrm", "lv": "warn", "node": _s(it.get("node"), 40)})
    return {"services": services[:200], "bad": bad}

# ─── Replicación ──────────────────────────────────────────────────────────────
# EN: rows: /nodes/<n>/replication entries. Failing jobs (fail_count > 0 or an error).
def repl_summary(rows_by_node):
    jobs, bad = [], []
    for node, rows in (rows_by_node or {}).items():
        for r in rows if isinstance(rows, list) else []:
            if not isinstance(r, dict): continue
            j = {"id": _s(r.get("id"), 30), "guest": _i(r.get("guest")), "node": _s(node, 40), "target": _s(r.get("target"), 40),
                 "fails": _i(r.get("fail_count")), "error": _s(r.get("error"), 120), "last": _i(r.get("last_sync")) or None,
                 "dur": _n(r.get("duration")), "next": _i(r.get("next_sync")) or None}
            jobs.append(j)
            if j["fails"] > 0 or j["error"]:
                bad.append({"type": "repl", "lv": "warn", "node": j["node"], "vmid": j["guest"], "id": j["id"], "fails": j["fails"], "error": j["error"]})
    return {"jobs": jobs[:200], "bad": bad}

# ─── Tareas fallidas (todas, no solo vzdump) ──────────────────────────────────
# EN: Failed tasks of any type (vzdump has its own view). `seen` works like backups.new_failures.
def failed_tasks(tasks, now, days=2):
    out = []
    for t in tasks if isinstance(tasks, list) else []:
        if not isinstance(t, dict): continue
        ty = _s(t.get("type"), 30)
        if not ty or ty == "vzdump" or ty in NOISE_TASKS: continue
        st = _i(t.get("starttime"))
        if st <= 0 or now - st > days * 86400: continue
        status = _s(t.get("status"), 160)
        if not status or status.upper().startswith(("OK", "WARNINGS")): continue    # empty = still running
        out.append({"upid": _s(t.get("upid"), 200), "type": ty, "node": _s(t.get("node"), 40), "user": _s(t.get("user"), 60),
                    "id": _s(t.get("id"), 30), "start": st, "status": status})
    out.sort(key=lambda x: -x["start"])
    return out[:40]

def new_task_failures(seen, fails):
    if seen is None: return {t["upid"] for t in fails}, []
    new = [t for t in fails if t["upid"] not in seen]
    return seen | {t["upid"] for t in fails}, new

# ─── Ceph: rendimiento, recuperación y estado de PG ───────────────────────────
# EN: Ceph: throughput, recovery and PG state (from /cluster/ceph/status, which is already read).
def ceph_io(ceph):
    pg = (ceph or {}).get("pgmap") if isinstance(ceph, dict) else None
    if not isinstance(pg, dict): return None
    states = []
    for s in pg.get("pgs_by_state") or []:
        if isinstance(s, dict): states.append({"state": _s(s.get("state_name"), 80), "n": _i(s.get("count"))})
    total = _i(pg.get("num_pgs"))
    clean = sum(s["n"] for s in states if s["state"] == "active+clean")
    return {"read_bps": _n(pg.get("read_bytes_sec"), 0), "write_bps": _n(pg.get("write_bytes_sec"), 0),
            "read_ops": _n(pg.get("read_op_per_sec"), 0), "write_ops": _n(pg.get("write_op_per_sec"), 0),
            "recover_bps": _n(pg.get("recovering_bytes_per_sec"), 0), "degraded": _n(pg.get("degraded_ratio"), 0),
            "misplaced": _n(pg.get("misplaced_ratio"), 0), "pgs": total, "clean": clean,
            "states": sorted([s for s in states if s["state"] != "active+clean"], key=lambda s: -s["n"])[:10]}

def ceph_alerts(io):
    if not io or not io["pgs"] or io["clean"] >= io["pgs"]: return []
    bad = [s for s in io["states"] if not s["state"].startswith("active+clean+")]       # scrubbing is normal
    if not bad and not io["degraded"]: return []
    return [{"type": "pg", "lv": "warn", "value": io["pgs"] - io["clean"], "total": io["pgs"]}]

# ─── Datos por nodo ───────────────────────────────────────────────────────────
# EN: Per-node data from /nodes/<n>/status and /nodes/<n>/certificates/info.
def node_info(status, certs, now):
    st = status if isinstance(status, dict) else {}
    ver = ""
    m = re.match(r"pve-manager/([^/]+)", _s(st.get("pveversion"), 120))
    if m: ver = m.group(1)
    kern = _s((st.get("current-kernel") or {}).get("release") if isinstance(st.get("current-kernel"), dict) else st.get("kversion"), 80)
    if not kern: kern = _s(st.get("kversion"), 80)
    load = [x for x in (_n(v) for v in (st.get("loadavg") or [])[:3]) if x is not None]
    sw = st.get("swap") if isinstance(st.get("swap"), dict) else {}
    cert_days = None
    for c in certs if isinstance(certs, list) else []:
        if not isinstance(c, dict): continue
        na = _i(c.get("notafter"))
        if na > 0 and _s(c.get("filename")) in ("pve-ssl.pem", "pveproxy-ssl.pem", ""):
            d = round((na - now) / 86400, 1)
            if cert_days is None or d < cert_days: cert_days = d
    return {"version": ver, "kernel": kern, "load": load, "cpus": _i((st.get("cpuinfo") or {}).get("cpus")) if isinstance(st.get("cpuinfo"), dict) else 0,
            "swap_used": _i(sw.get("used")), "swap_total": _i(sw.get("total")), "iowait": _n(st.get("wait")), "cert_days": cert_days}

def node_alerts(nodes_info):
    out = []
    for name, ni in sorted((nodes_info or {}).items()):
        d = ni.get("cert_days")
        if d is not None and d <= CERT_WARN:
            out.append({"type": "cert", "lv": "crit" if d <= CERT_CRIT else "warn", "node": name, "value": max(int(d), 0)})
        if ni.get("iowait") is not None and ni["iowait"] > 0.3:
            out.append({"type": "iowait", "lv": "warn", "node": name, "value": round(ni["iowait"] * 100)})
        if ni.get("swap_total") and ni["swap_used"] / ni["swap_total"] > 0.5:
            out.append({"type": "swap", "lv": "warn", "node": name, "value": round(ni["swap_used"] / ni["swap_total"] * 100)})
    return out

def version_drift(nodes_info):
    """Distinct pve-manager versions across nodes (more than one = the cluster is half-upgraded)."""
    v = sorted({ni["version"] for ni in (nodes_info or {}).values() if ni.get("version")})
    return v if len(v) > 1 else []


# ─── Detalle de un nodo y su historial (rrddata) ────────────────────────────────
# El historial de un nodo lo guarda Proxmox mismo (hora, día, semana, mes y año): se pide a /nodes/<n>/rrddata y se traduce a
# los rangos de los gráficos de LabTower (1h, 1d, 1w, 1mo, todo = año). Funciones puras, sin red.
# EN: Node detail and its history (rrddata). A node's history is kept by Proxmox itself (hour, day, week, month and year): it is
#     read from /nodes/<n>/rrddata and mapped to LabTower's chart ranges (1h, 1d, 1w, 1mo, all = year). Pure functions, no network.
RRD_FRAME = {"1h": "hour", "1d": "day", "1w": "week", "1mo": "month", "all": "year"}
_MAX_ROWS = 2000

def _pct(used, total):
    u, t = _n(used), _n(total)
    return round(u / t * 100, 2) if u is not None and t else None

def rrd_points(rows):
    """rrddata rows → chart points: cpu / iowait / mem / swap / root in %, load, memory bytes and network bytes per second."""
    out = []
    for r in (rows if isinstance(rows, list) else [])[:_MAX_ROWS]:
        if not isinstance(r, dict): continue
        ts = _i(r.get("time"))
        if ts <= 0: continue
        cpu, io = _n(r.get("cpu")), _n(r.get("iowait"))
        out.append({"ts": ts, "cpu": round(cpu * 100, 2) if cpu is not None else None, "iowait": round(io * 100, 2) if io is not None else None,
                    "load": _n(r.get("loadavg")), "mem": _pct(r.get("memused"), r.get("memtotal")), "memused": _n(r.get("memused")),
                    "swap": _pct(r.get("swapused"), r.get("swaptotal")), "root": _pct(r.get("rootused"), r.get("roottotal")),
                    "netin": _n(r.get("netin")), "netout": _n(r.get("netout"))})
    return sorted(out, key=lambda p: p["ts"])

def _flat(v, depth=0):
    """Short, safe text for a value the page does not know (numbers, strings, small lists / objects)."""
    if isinstance(v, bool): return "yes" if v else "no"
    if isinstance(v, int): return str(v)
    if isinstance(v, float): return str(round(v, 3)) if math.isfinite(v) else ""
    if isinstance(v, str): return _s(v, 160)
    if isinstance(v, list) and depth < 2: return ", ".join(_flat(x, depth + 1) for x in v[:12])
    if isinstance(v, dict) and depth < 2: return " · ".join(f"{_s(k, 40)}: {_flat(x, depth + 1)}" for k, x in list(v.items())[:12])
    return ""

_STATUS_KNOWN = {"cpu", "cpuinfo", "memory", "swap", "rootfs", "ksm", "loadavg", "wait", "uptime", "kversion", "pveversion", "current-kernel", "boot-info", "idle"}

def node_detail(status, version, tinfo, dns, net, subs, apt, services, disks):
    """Everything the node panel shows, trimmed and typed. Missing parts stay None / empty (a missing permission is not an error)."""
    st = status if isinstance(status, dict) else {}
    ci, mem, sw, rf = (st.get(k) if isinstance(st.get(k), dict) else {} for k in ("cpuinfo", "memory", "swap", "rootfs"))
    ksm = st.get("ksm") if isinstance(st.get("ksm"), dict) else {}
    ck, bi = (st.get(k) if isinstance(st.get(k), dict) else {} for k in ("current-kernel", "boot-info"))
    ver = version if isinstance(version, dict) else {}
    ti = tinfo if isinstance(tinfo, dict) else {}
    dn = dns if isinstance(dns, dict) else {}
    sb = subs if isinstance(subs, dict) else {}
    cpu = _n(st.get("cpu"))
    out = {
        "cpu": round(cpu * 100, 2) if cpu is not None else None, "iowait": round(_n(st.get("wait")) * 100, 2) if _n(st.get("wait")) is not None else None,
        "load": [x for x in (_n(v) for v in (st.get("loadavg") or [])[:3]) if x is not None] if isinstance(st.get("loadavg"), list) else [],
        "cpuinfo": {"model": _s(ci.get("model"), 120), "cpus": _i(ci.get("cpus")), "sockets": _i(ci.get("sockets")), "cores": _i(ci.get("cores")), "mhz": _n(ci.get("mhz"))},
        "mem": {"used": _n(mem.get("used")), "total": _n(mem.get("total")), "free": _n(mem.get("free"))},
        "swap": {"used": _n(sw.get("used")), "total": _n(sw.get("total"))},
        "root": {"used": _n(rf.get("used")), "total": _n(rf.get("total"))},
        "ksm": _n(ksm.get("shared")), "uptime": _i(st.get("uptime")),
        "kernel": _s(ck.get("release") or st.get("kversion"), 120), "kernel_full": _s(ck.get("version"), 160), "arch": _s(ck.get("machine"), 20),
        "pveversion": _s(st.get("pveversion"), 120), "version": _s(ver.get("version"), 40), "release": _s(ver.get("release"), 40), "repoid": _s(ver.get("repoid"), 40),
        "boot": {"mode": _s(bi.get("mode"), 20), "secureboot": bool(bi.get("secureboot")) if "secureboot" in bi else None},
        "timezone": _s(ti.get("timezone"), 60), "localtime": _i(ti.get("localtime")),
        "dns": {"search": _s(dn.get("search"), 120), "servers": [_s(dn.get(k), 60) for k in ("dns1", "dns2", "dns3") if dn.get(k)]},
        "subscription": {"status": _s(sb.get("status"), 40), "level": _s(sb.get("level"), 20), "product": _s(sb.get("productname"), 80), "due": _s(sb.get("nextduedate"), 20)} if sb else None,
        "updates": len(apt) if isinstance(apt, list) else None,
        "net": [], "services": [], "disks": [],
        "other": [{"k": _s(k, 60), "v": _flat(v)} for k, v in sorted(st.items()) if k not in _STATUS_KNOWN and _flat(v)][:40],
    }
    for n in (net if isinstance(net, list) else [])[:60]:
        if not isinstance(n, dict): continue
        out["net"].append({"iface": _s(n.get("iface"), 40), "type": _s(n.get("type"), 20), "active": bool(n.get("active")), "address": _s(n.get("cidr") or n.get("address"), 60),
                           "gateway": _s(n.get("gateway"), 60), "ports": _s(n.get("bridge_ports") or n.get("slaves"), 120), "comments": _s(n.get("comments"), 80)})
    for s in (services if isinstance(services, list) else [])[:60]:
        if isinstance(s, dict) and s.get("service"): out["services"].append({"name": _s(s.get("service"), 60), "state": _s(s.get("state"), 20), "desc": _s(s.get("desc"), 100)})
    for d in (disks if isinstance(disks, list) else [])[:60]:
        if isinstance(d, dict): out["disks"].append({"dev": _s(d.get("devpath"), 40), "model": _s(d.get("model"), 80), "size": _n(d.get("size")), "type": _s(d.get("type"), 12),
                                                     "health": _s(d.get("health"), 20), "wearout": _s(d.get("wearout"), 12)})
    return out
