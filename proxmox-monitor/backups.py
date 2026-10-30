"""
Proxmox Monitor — respaldos: último respaldo correcto de cada VM/CT y tareas vzdump fallidas.
Funciones puras (sin red ni disco) para probarlas con datos de ejemplo; server.py las usa con la API real.
EN: Proxmox Monitor — backups: last good backup of each VM/CT and failed vzdump tasks.
    Pure functions (no network, no disk) so they can be tested with sample data; server.py uses them with the real API.
"""
DEFAULT_MAX_AGE_H = 36          # a daily job + margin
MAX_IGNORE = 200

def _i(x, default=0):
    try:
        if isinstance(x, bool): return default
        return int(float(x))
    except (TypeError, ValueError, OverflowError):
        return default

def _s(x, n=80):
    return str(x)[:n] if x is not None else ""

# Reúne el contenido «backup» de uno o varios storages y deja, por VM/CT, el respaldo más reciente (más cuántos hay).
# contents = [{"storage", "node", "items": [{volid, vmid, ctime, size, verification}]}]
# EN: Gather the "backup" content of one or more storages and keep, per VM/CT, the newest backup (plus how many there are).
def newest_by_vmid(contents):
    out = {}
    for c in contents if isinstance(contents, list) else []:
        if not isinstance(c, dict): continue
        for it in c.get("items") or []:
            if not isinstance(it, dict): continue
            vmid, ct = _i(it.get("vmid")), _i(it.get("ctime"))
            if vmid <= 0 or ct <= 0: continue
            e = out.setdefault(vmid, {"count": 0, "ctime": 0})
            e["count"] += 1
            if ct > e["ctime"]:
                ver = it.get("verification")
                st = _s(ver.get("state"), 12).lower() if isinstance(ver, dict) else None
                e.update(ctime=ct, size=_i(it.get("size")), storage=_s(c.get("storage"), 40), node=_s(c.get("node"), 40),
                         volid=_s(it.get("volid"), 120), verify=st if st in ("ok", "failed") else None)
    return out

# Estado de cada VM/CT frente a su último respaldo: ok · old (más viejo que el máximo) · never (no hay ninguno) · ignored.
# EN: State of each VM/CT against its last backup: ok · old (older than the maximum) · never (none at all) · ignored.
def evaluate(guests, newest, max_age_h, ignore, now):
    ign = {_i(v) for v in ignore} if isinstance(ignore, (list, tuple, set)) else set()
    limit = max(_i(max_age_h, DEFAULT_MAX_AGE_H), 1) * 3600
    rows = []
    for g in guests if isinstance(guests, list) else []:
        if not isinstance(g, dict): continue
        vmid = _i(g.get("vmid"))
        if vmid <= 0 or _i(g.get("template")): continue
        nb = newest.get(vmid)
        row = {"vmid": vmid, "name": _s(g.get("name"), 60), "type": "ct" if g.get("type") == "lxc" else "vm", "node": _s(g.get("node"), 40),
               "last": nb["ctime"] if nb else None, "age": max(int(now) - nb["ctime"], 0) if nb else None,
               "size": nb.get("size") if nb else None, "storage": nb.get("storage") if nb else None,
               "count": nb["count"] if nb else 0, "verify": nb.get("verify") if nb else None}
        if vmid in ign:         row["status"] = "ignored"
        elif not nb:            row["status"] = "never"
        elif row["age"] > limit: row["status"] = "old"
        else:                   row["status"] = "ok"
        rows.append(row)
    order = {"never": 0, "old": 1, "ok": 2, "ignored": 3}
    rows.sort(key=lambda r: (order[r["status"]], r["vmid"]))
    return rows

# Compacta las tareas de /cluster/tasks: solo vzdump de los últimos `days` días. ok = None mientras sigue corriendo.
# EN: Compact the /cluster/tasks list: only vzdump of the last `days` days. ok = None while it is still running.
def parse_tasks(tasks, now, days=7):
    out = []
    for t in tasks if isinstance(tasks, list) else []:
        if not isinstance(t, dict) or t.get("type") != "vzdump": continue
        st = _i(t.get("starttime"))
        if st <= 0 or now - st > days * 86400: continue
        status = _s(t.get("status"), 160)
        end = _i(t.get("endtime"))
        if not end and not status: ok = None
        else: ok = status.upper().startswith(("OK", "WARNINGS"))
        out.append({"upid": _s(t.get("upid"), 200), "node": _s(t.get("node"), 40), "start": st, "end": end or None,
                    "vmid": _i(t.get("id")) or None, "ok": ok, "status": status})
    out.sort(key=lambda x: -x["start"])
    return out[:60]

# Tareas fallidas que aún no se habían visto. La primera lectura solo memoriza (reiniciar el servicio no genera eventos falsos).
# EN: Failed tasks not seen before. The first reading only remembers them (restarting the service does not create false events).
def new_failures(seen, tasks):
    """seen: a set kept by the caller, or None on the first reading. Returns (seen, failures)."""
    fails = [t for t in tasks if t["ok"] is False]
    if seen is None:
        return {t["upid"] for t in fails}, []
    new = [t for t in fails if t["upid"] not in seen]
    seen = (seen | {t["upid"] for t in fails})
    return seen, new

# Valida la configuración de respaldos de un cluster (máximo de antigüedad y VMs ignoradas).
# EN: Validate a cluster's backup settings (maximum age and ignored VMs).
def clean_config(body):
    if not isinstance(body, dict): raise ValueError("Invalid settings")
    h = body.get("max_age_h", DEFAULT_MAX_AGE_H)
    if isinstance(h, bool) or not isinstance(h, (int, float)) or h != h or not (1 <= h <= 8760): raise ValueError("Invalid maximum age")
    ign = body.get("ignore", [])
    if not isinstance(ign, list) or len(ign) > MAX_IGNORE: raise ValueError("Invalid ignore list")
    ids = []
    for v in ign:
        if isinstance(v, bool) or not isinstance(v, int) or not (100 <= v <= 999999999): raise ValueError("Invalid VM id")
        ids.append(v)
    return {"max_age_h": int(h), "ignore": sorted(set(ids))}
