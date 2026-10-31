"""
UPS Monitor — salud de la batería: autonomía estimada, envejecimiento y autotests.
Funciones puras (sin red ni base de datos) para probarlas con datos de ejemplo; server.py las usa con las lecturas reales.
EN: UPS Monitor — battery health: estimated runtime, ageing and self-tests.
    Pure functions (no network, no database) so they can be tested with sample data; server.py uses them with the real readings.
"""
import datetime, re

AGING_WARN_PCT = -20.0          # % change of the full-battery runtime that is worth a warning
BATTERY_OLD_YEARS = 4.0         # sealed lead-acid batteries last about 3-5 years

def _f(x):
    try:
        if isinstance(x, bool) or x is None or x == "": return None
        v = float(x)
        return v if v == v and abs(v) != float("inf") else None
    except (TypeError, ValueError, OverflowError):
        return None

# Autonomía con la carga actual. `battery.runtime` ya es la que informa el UPS con la carga de ahora y la carga de batería de ahora;
# aquí se proyecta a batería llena (runtime ÷ carga) y se estima qué pasaría si la carga subiera (aproximación: autonomía ∝ 1 ÷ carga).
# EN: Runtime at the current load. `battery.runtime` is what the UPS reports for the present load and present charge;
#     here it is projected to a full battery (runtime ÷ charge) and an estimate is given for a higher load (approximation: runtime ∝ 1 ÷ load).
def runtime_estimate(vars_):
    if not isinstance(vars_, dict): return None
    rt, ch = _f(vars_.get("battery.runtime")), _f(vars_.get("battery.charge"))
    load = _f(vars_.get("ups.load"))
    if rt is None or rt <= 0 or ch is None or ch < 10: return None
    full = rt * 100.0 / min(ch, 100.0)
    out = {"now_s": int(rt), "full_s": int(full), "charge": round(ch, 1), "load": load}
    if load and load >= 1:
        out["plus50_s"] = int(full * load / min(load * 1.5, 100.0)) if load * 1.5 <= 100 else None
    return out

# Fecha de la batería informada por el UPS (formatos habituales de NUT); None si no sirve («00/00/00», vacía, futura o absurda).
# EN: Battery date reported by the UPS (common NUT formats); None if unusable ("00/00/00", empty, in the future or absurd).
def parse_battery_date(s, today=None):
    if not isinstance(s, str): return None
    s = s.strip()
    if not s: return None
    today = today or datetime.date.today()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y"):
        try: d = datetime.datetime.strptime(s, fmt).date()
        except ValueError: continue
        if d.year < 2000 or d > today: continue
        return d
    return None

# ES: Muchos UPS (APC Easy, por ejemplo) dejan la fecha de fábrica del firmware y no la actualizan al cambiar la batería. Una batería de plomo de más de
#     MAX_PLAUSIBLE_YEARS años no es creíble: esa fecha se ignora (y se puede indicar la fecha real del cambio en LabTower).
# EN: Many UPSs (APC Easy, for one) keep the firmware's factory date and do not update it when the battery is replaced. A lead-acid battery older than
#     MAX_PLAUSIBLE_YEARS is not credible: that date is ignored (and the real replacement date can be set in LabTower).
MAX_PLAUSIBLE_YEARS = 10

def battery_age_years(s, today=None):
    today = today or datetime.date.today()
    d = parse_battery_date(s, today)
    if d is None: return None
    y = round((today - d).days / 365.25, 1)
    return y if y <= MAX_PLAUSIBLE_YEARS else None

# ES: Algunos UPS (APC Back-UPS) guardan la fecha de la batería en battery.date y otros en battery.mfr.date, y las herramientas del fabricante cambian una u otra.
#     Se toma la más reciente de las dos que sean creíbles.
# EN: Some UPSs (APC Back-UPS) keep the battery date in battery.date and others in battery.mfr.date, and vendor tools change one or the other.
#     The most recent credible one of the two is used.
def best_battery_date(vars_, today=None):
    today = today or datetime.date.today()
    ds = [parse_battery_date(vars_.get(k), today) for k in ("battery.date", "battery.mfr.date")] if isinstance(vars_, dict) else []
    ds = [d for d in ds if d is not None]
    if not ds: return None
    d = max(ds)
    return d if (today - d).days / 365.25 <= MAX_PLAUSIBLE_YEARS else None

def best_battery_age_years(vars_, today=None):
    today = today or datetime.date.today()
    d = best_battery_date(vars_, today)
    return battery_age_years(d.isoformat(), today) if d else None

# ES: Meses cumplidos entre la fecha de la batería y hoy (0 = menos de un mes). Solo se usa para baterías de menos de 1 año.
# EN: Whole months between the battery date and today (0 = under a month). Only used for batteries younger than 1 year.
def age_months(d, today=None):
    today = today or datetime.date.today()
    if d is None or d > today: return None
    m = (today.year - d.year) * 12 + today.month - d.month - (1 if today.day < d.day else 0)
    return max(m, 0)

def parse_manual_date(s, today=None):
    """YYYY-MM-DD typed by the user: not in the future, not before 2000. Returns a date or None."""
    today = today or datetime.date.today()
    try: d = datetime.datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except ValueError: return None
    return d if 2000 <= d.year and d <= today else None

# Tendencia de la autonomía a batería llena. `weeks` = [(semana, autonomía_media_s, muestras)] de lecturas con batería ≥ 95 % y
# carga parecida, ordenadas por semana. Compara el comienzo con el final de la ventana. Con poco historial devuelve None.
# EN: Trend of the full-battery runtime. `weeks` = [(week, mean_runtime_s, samples)] from readings with battery ≥ 95 % and a similar
#     load, ordered by week. Compares the start with the end of the window. Returns None with too little history.
def aging_trend(weeks, min_weeks=4, min_samples=200):
    ok = [(int(w), float(r), int(n)) for w, r, n in weeks if _f(r) and _f(r) > 0 and isinstance(n, int) and n >= min_samples] if isinstance(weeks, list) else []
    if len(ok) < min_weeks or ok[-1][0] - ok[0][0] < min_weeks - 1: return None
    k = max(1, len(ok) // 4)
    first = sum(r for _, r, _ in ok[:k]) / k
    last = sum(r for _, r, _ in ok[-k:]) / k
    change = round((last - first) * 100.0 / first, 1)
    return {"first_s": int(first), "last_s": int(last), "change_pct": change, "weeks": ok[-1][0] - ok[0][0] + 1, "warn": change <= AGING_WARN_PCT}

# Clasifica el resultado de `ups.test.result`: running · passed · failed · none (sin prueba) · other.
# EN: Classify the result of `ups.test.result`: running · passed · failed · none (no test) · other.
def classify_test(result):
    r = result.strip().lower() if isinstance(result, str) else ""
    if not r: return "none"
    if "progress" in r: return "running"
    if "no test" in r or "not initiated" in r or "no self" in r: return "none"
    if re.search(r"fail|error|abort|cancel|interrupt|warning|bad|replace|unsuccess", r): return "failed"
    if re.search(r"pass|done|ok|success|complete", r): return "passed"
    return "other"
