"""
UPS Monitor — banderas de estado, alarmas, calidad de la red eléctrica y margen para apagar los equipos.
Funciones puras (sin red ni disco) para probarlas con datos de ejemplo.
EN: UPS Monitor — status flags, alarms, mains quality and the margin to shut machines down.
    Pure functions (no network, no disk) so they can be tested with sample data.
"""
import math

GAP = 600                     # s: a hole longer than this in the history ends a run
BAND = 0.10                   # ±10 % around the nominal voltage counts as normal
MIN_RUN = 2                   # samples outside the band in a row to count as an excursion (one stray reading is noise)

# Palabras de ups.status que importan además de OL / OB / LB (CHRG y DISCHRG son normales y se ignoran).
# EN: Words of ups.status that matter besides OL / OB / LB (CHRG and DISCHRG are normal and ignored).
FLAGS = {"RB": "warn", "OVER": "warn", "BYPASS": "warn", "OFF": "warn", "FSD": "crit", "ALARM": "warn",
         "TRIM": "info", "BOOST": "info", "CAL": "info"}

def _f(x):
    try:
        if isinstance(x, bool) or x is None: return None
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError, OverflowError):
        return None

def flags(status):
    """[{"f": "RB", "lv": "warn"}, ...] for the words of ups.status worth showing, in a stable order."""
    words = set(str(status or "").upper().split())
    return [{"f": k, "lv": v} for k, v in FLAGS.items() if k in words]

def alarm(vars_):
    """Text of ups.alarm ('' when none). Some drivers report 'No alarms' style text: treated as none."""
    a = str((vars_ or {}).get("ups.alarm") or "").strip()[:200]
    return "" if a.lower() in ("", "none", "no alarm", "no alarms", "ok", "0") else a

def beeper(vars_):
    b = str((vars_ or {}).get("ups.beeper.status") or "").strip().lower()
    return b if b in ("enabled", "disabled", "muted") else ""

def margin(vars_, need_s):
    """How long the UPS can run before it has to shut down, against the time the machines need to shut down.
    On battery it uses the runtime left now; on mains, the runtime projected at full charge (what a cut would give).
    None when the UPS does not report a runtime."""
    v = vars_ or {}
    rt, ch = _f(v.get("battery.runtime")), _f(v.get("battery.charge"))
    if rt is None or rt <= 0: return None
    on_batt = bool(set(str(v.get("ups.status") or "").upper().split()) & {"OB", "LB"})
    if on_batt or ch is None or ch < 10: basis, total = "now", rt
    else: basis, total = "full", rt * 100.0 / min(ch, 100.0)
    low = _f(v.get("battery.runtime.low")) or 0.0
    m = int(total - low)
    return {"need": int(need_s), "margin_s": m, "basis": basis, "runtime_low": int(low), "charge": ch,
            "charge_low": _f(v.get("battery.charge.low")), "ok": m >= need_s}

def _median(a):
    s = sorted(a); n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2

def quality(rows, nominal, now, windows=(("24h", 86400), ("7d", 604800))):
    """rows: [(ts, input_voltage)] oldest first. Per window: min / max / mean of the input voltage and the excursions
    (runs of samples above or below the ±10 % band). Samples under 20 V are outages (counted elsewhere), 0 means 'not measured'."""
    out = {"nominal": None, "lo": None, "hi": None, "w": {}}
    good = [(t, v) for t, v in rows if _f(v) is not None and v >= 20]
    nom = _f(nominal)
    if not nom or nom < 50: nom = _median([v for _, v in good]) if len(good) >= 30 else None
    if not nom: return out
    lo, hi = nom * (1 - BAND), nom * (1 + BAND)
    out.update(nominal=round(nom), lo=round(lo), hi=round(hi))
    for label, w in windows:
        pts = [(t, v) for t, v in good if t >= now - w]
        r = {"n": len(pts), "min": None, "max": None, "avg": None, "low": 0, "high": 0}
        if pts:
            vs = [v for _, v in pts]
            r.update(min=round(min(vs), 1), max=round(max(vs), 1), avg=round(sum(vs) / len(vs), 1))
            run = []; kind = None; last_t = None
            def close(r=r):
                nonlocal run, kind
                if kind and len(run) >= MIN_RUN: r[kind] += 1
                run = []; kind = None
            for t, v in pts:
                k = "low" if v < lo else "high" if v > hi else None
                if last_t is not None and t - last_t > GAP: close()
                if k != kind: close()
                if k: kind = k; run.append(t)
                last_t = t
            close()
        out["w"][label] = r
    return out
