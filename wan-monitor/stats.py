"""
WAN Monitor — percentiles de latencia, calidad por destino, velocidad contra el plan, disponibilidad / MTBF y avisos sostenidos.
Funciones puras (sin red ni disco) para probarlas con datos de ejemplo.
EN: WAN Monitor — latency percentiles, per-target quality, speed against the plan, availability / MTBF and sustained alerts.
    Pure functions (no network, no disk) so they can be tested with sample data.
"""
import math

LOW_PLAN = 0.70               # a speed test under 70 % of the plan counts as low
LOW_STREAK = 3                # this many low tests in a row raise the warning

def _f(x):
    try:
        if isinstance(x, bool) or x is None: return None
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError, OverflowError):
        return None

def percentile(vals, p):
    """p in 0..100, linear interpolation. None for an empty list."""
    v = sorted(x for x in (_f(a) for a in vals) if x is not None)
    if not v: return None
    k = (len(v) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] if lo == hi else v[lo] + (v[hi] - v[lo]) * (k - lo)

def latency_stats(rtts):
    v = [x for x in (_f(a) for a in rtts) if x is not None]
    if not v: return {"n": 0, "p50": None, "p95": None, "p99": None, "max": None}
    r = lambda x: round(x, 1)
    return {"n": len(v), "p50": r(percentile(v, 50)), "p95": r(percentile(v, 95)), "p99": r(percentile(v, 99)), "max": r(max(v))}

def target_stats(rows):
    """rows: [(host, rtt, loss, ok)] for one window. Per target: samples, mean and p95 latency, mean loss and share of failed rounds."""
    by = {}
    for host, rtt, loss, ok in rows:
        by.setdefault(host, []).append((_f(rtt), _f(loss), ok))
    out = []
    for host, a in by.items():
        rtts = [r for r, _, _ in a if r is not None]; losses = [l for _, l, _ in a if l is not None]
        out.append({"host": host, "n": len(a), "rtt": round(sum(rtts) / len(rtts), 1) if rtts else None,
                    "p95": round(percentile(rtts, 95), 1) if rtts else None,
                    "loss": round(sum(losses) / len(losses), 2) if losses else None,
                    "fail_pct": round(100.0 * sum(1 for _, _, ok in a if not ok) / len(a), 2)})
    return sorted(out, key=lambda x: x["host"])

def _pct(v, plan):
    return round(100.0 * v / plan) if v is not None and plan else None

def speed_stats(rows, plan_down, plan_up, now, tz_hour):
    """rows: [(ts, down, up, error)] oldest first. Share of the plan (last test, 7 and 30 day means), the mean speed by hour of the
    day, the daily trend and how many of the latest tests in a row are under 70 % of the plan. tz_hour(ts) -> local hour."""
    ok = [(t, _f(d), _f(u)) for t, d, u, e in rows if not e and (_f(d) is not None or _f(u) is not None)]
    pd_, pu = _f(plan_down) or 0, _f(plan_up) or 0
    out = {"plan_down": pd_ or None, "plan_up": pu or None, "n": len(ok), "last": None, "avg7": {}, "avg30": {}, "hours": [], "trend": [], "low_streak": 0}
    if not ok: return out
    def mean(sel, i): 
        v = [x[i] for x in sel if x[i] is not None]
        return sum(v) / len(v) if v else None
    t, d, u = ok[-1]
    out["last"] = {"ts": t, "down": _pct(d, pd_), "up": _pct(u, pu)}
    for key, w in (("avg7", 7 * 86400), ("avg30", 30 * 86400)):
        sel = [x for x in ok if x[0] >= now - w]
        out[key] = {"down": _pct(mean(sel, 1), pd_), "up": _pct(mean(sel, 2), pu), "n": len(sel)}
    hrs = {}
    for t, d, u in ok: hrs.setdefault(tz_hour(t), []).append((t, d, u))
    out["hours"] = [{"h": h, "n": len(hrs[h]), "down": round(mean(hrs[h], 1), 1) if mean(hrs[h], 1) is not None else None,
                     "up": round(mean(hrs[h], 2), 1) if mean(hrs[h], 2) is not None else None} for h in sorted(hrs)]
    days = {}
    for t, d, u in ok:
        if t >= now - 30 * 86400: days.setdefault(int(t // 86400), []).append((t, d, u))
    out["trend"] = [{"ts": k * 86400, "down": round(mean(v, 1), 1) if mean(v, 1) is not None else None,
                     "up": round(mean(v, 2), 1) if mean(v, 2) is not None else None} for k, v in sorted(days.items())]
    if pd_ or pu:
        n = 0
        for _t, d, u in reversed(ok):
            low = (pd_ and d is not None and d < pd_ * LOW_PLAN) or (pu and u is not None and u < pu * LOW_PLAN)
            if not low: break
            n += 1
        out["low_streak"] = n
    return out

def outage_stats(outages, now, window, first_ts):
    """outages: [(start, end|None, scope)]. Counted inside the last `window` seconds (clipped); first_ts = first sample of the history,
    so a new install is not judged over time it did not observe. MTBF = observed time with the line up / number of outages."""
    since = max(now - window, first_ts or (now - window))
    observed = max(now - since, 0)
    n, down, longest, scopes = 0, 0, 0, {"lan": 0, "wan": 0, "internet": 0}
    for s, e, sc in outages:
        e = e or now
        if e < since or s > now: continue
        d = min(e, now) - max(s, since)
        n += 1; down += max(d, 0); longest = max(longest, max(d, 0))
        scopes[sc if sc in scopes else "internet"] += 1
    return {"observed": int(observed), "count": n, "down": int(down), "mean": int(down / n) if n else None, "longest": int(longest),
            "mtbf": int((observed - down) / n) if n and observed > down else None,
            "pct": round(100.0 * (1 - down / observed), 3) if observed >= 3600 else None, "scopes": scopes}

class Sustain:
    """A condition must hold for `n` rounds in a row to turn on, and be clear for `n` rounds to turn off. update() returns 'on' / 'off' / None."""
    def __init__(self, n=3): self.n, self.on, self.c = n, {}, {}
    def update(self, key, bad):
        c = self.c.get(key, 0)
        c = (c + 1) if bool(bad) != self.on.get(key, False) else 0
        if c >= self.n:
            self.on[key] = bool(bad); self.c[key] = 0
            return "on" if bad else "off"
        self.c[key] = c
        return None
