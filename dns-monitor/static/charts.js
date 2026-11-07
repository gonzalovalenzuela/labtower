// Motor de gráficos de LabTower: todos los gráficos de detalle (UPS, NAS, DNS, WAN) se dibujan aquí para verse y comportarse igual: rejilla, área bajo la primera
// serie, rangos 1h/1d/1w/1mes/todo, cursor con tooltip, marcas de eventos del módulo y comparación con el periodo anterior. Copia idéntica en cada módulo.
// EN: LabTower chart engine: every detail chart (UPS, NAS, DNS, WAN) is drawn here so they look and behave the same: grid, area under the first series,
//     1h/1d/1w/1mo/all ranges, hover cursor with tooltip, module event marks and comparison with the previous period. Identical copy in each module.
(function () {
  const TXT = {en: {cmp: 'vs previous', cmpTip: 'Compare with the previous period of the same length', all: 'All', accumulating: 'Collecting data…', noData: 'No data yet'},
               es: {cmp: 'vs anterior', cmpTip: 'Comparar con el periodo anterior de la misma duración', all: 'Todo', accumulating: 'Acumulando datos…', noData: 'Sin datos aún'}};
  const lg = () => (typeof _lang !== 'undefined' && TXT[_lang]) ? _lang : 'en';
  const X = k => TXT[lg()][k];
  const loc = () => lg() === 'es' ? 'es-CL' : 'en-GB';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const RANGES = ['1h', '1d', '1w', '1mo', 'all'];
  const cmp = {};                                   // chart key → true when the comparison is on
  const COL = {crit: '#ef4444', warn: '#f59e0b', info: '#4361ee'};

  // ── Eventos del módulo (los anota el servidor); se piden a lo más cada 90 s. / Module events (recorded by the server); fetched at most every 90 s.
  const EV = {};
  function events(mod, redraw) {
    const c = EV[mod] || (EV[mod] = {ts: 0, list: [], busy: false});
    if (!c.busy && Date.now() - c.ts > 90000) {
      c.busy = true; c.ts = Date.now();
      fetch('/overview/api/events?limit=200&m=' + encodeURIComponent(mod), {credentials: 'same-origin'})
        .then(r => r.ok ? r.json() : {events: []}).then(d => { c.list = Array.isArray(d.events) ? d.events : []; if (redraw) redraw(); })
        .catch(() => {}).finally(() => { c.busy = false; });
    }
    return c.list;
  }
  function nearest(pts, t) {                        // index of the point closest to time t (points are sorted)
    let lo = 0, hi = pts.length - 1;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (pts[mid].ts < t) lo = mid + 1; else hi = mid; }
    if (lo > 0 && Math.abs(pts[lo - 1].ts - t) <= Math.abs(pts[lo].ts - t)) lo--;
    return lo;
  }
  function marks(ctx, cv, mod, pts, xOf, PT, H2, evFilter) {
    cv._marks = [];
    let list = mod ? events(mod, () => { if (cv._vc) draw(cv, Object.assign({}, cv._vc, {hover: -1})); }) : [];
    if (evFilter) list = list.filter(evFilter);
    if (!list.length || pts.length < 2) return;
    const t0 = pts[0].ts, t1 = pts[pts.length - 1].ts, gap = Math.max(60, (t1 - t0) / pts.length * 3);
    list.forEach(e => {
      const t = Number(e.t); if (!(t >= t0 - gap && t <= t1 + gap)) return;
      const i = nearest(pts, t); if (Math.abs(pts[i].ts - t) > gap) return;          // not inside a hole of the data
      const x = Math.round(xOf(i)) + .5, c = COL[e.lv] || COL.info;
      ctx.save(); ctx.strokeStyle = c; ctx.globalAlpha = .55; ctx.lineWidth = 1; ctx.setLineDash([2, 3]);
      ctx.beginPath(); ctx.moveTo(x, PT + 5); ctx.lineTo(x, PT + H2); ctx.stroke(); ctx.setLineDash([]);
      ctx.globalAlpha = 1; ctx.fillStyle = c; ctx.beginPath(); ctx.moveTo(x - 4, PT); ctx.lineTo(x + 4, PT); ctx.lineTo(x, PT + 6); ctx.closePath(); ctx.fill(); ctx.restore();
      cv._marks.push({x, e});
    });
  }

  // ── Cabecera y filtros (HTML idéntico en todos los módulos) / Header and filters (same HTML in every module)
  // attrs(range) → atributos data-on-click del botón; cmpAttrs → los del botón «vs anterior» (o null si no hay comparación).
  function filters(active, attrs, cmpAttrs, cmpOn) {
    return RANGES.map(r => `<button type="button" class="vchart-filter${active === r ? ' active' : ''}" data-range="${r}" ${attrs(r)}>${r === 'all' ? esc(X('all')) : r}</button>`).join('') +
      (cmpAttrs ? `<button type="button" class="vchart-filter vchart-cmp${cmpOn ? ' active' : ''}" ${cmpAttrs} title="${esc(X('cmpTip'))}">${esc(X('cmp'))}</button>` : '');
  }
  function section(o) {   // o: {title, legend:[{c,l}], filters (html), canvasId, tipId, h, canvasAttrs}
    const leg = (o.legend || []).map(x => `<div class="vchart-legend-item"><div class="vchart-legend-dot" style="background:${esc(x.c)}"></div>${esc(x.l)}</div>`).join('');
    return `<div class="vchart-section"><div class="vchart-header"><span class="vchart-title">${esc(o.title)}</span><div class="vchart-legend">${leg}</div>` +
      `<div class="vchart-filters"${o.filtersId ? ` id="${esc(o.filtersId)}"` : ''}>${o.filters || ''}</div></div>` +
      `<div class="vchart-body" style="position:relative"><div class="vchart-tooltip" id="${esc(o.tipId)}"></div>` +
      `<canvas class="vchart" id="${esc(o.canvasId)}"${o.h ? ` style="--chart-h:${o.h}px"` : ''}></canvas></div></div>`;
  }

  // ── Dibujo / Drawing
  // o: {pts, series:[{k,c,l,f}], range, hover, h, pl, pr, min, max, scale(vals)→[lo,hi], axis(v), points, down, mod, evFilter(e), hline, prev, lastLabels, extra(p)→[texts], tipId}
  function draw(cv, o) {
    if (!cv) return;
    cv._vc = o;
    const pts = (o.pts || []).filter(p => p && typeof p.ts === 'number'), S = o.series, range = o.range || '1d', hover = o.hover == null ? -1 : o.hover;
    const dpr = window.devicePixelRatio || 1, W = cv.offsetWidth || 600, H = Math.round(cv.getBoundingClientRect().height) || o.h || 130;
    if (cv.width !== W * dpr || cv.height !== H * dpr) { cv.width = W * dpr; cv.height = H * dpr; }
    const ctx = cv.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
    const css = k => getComputedStyle(document.documentElement).getPropertyValue(k).trim();
    const cBg = css('--bg') || '#f0f2f5', cBorder = css('--border') || '#e3e8ef', cDim = css('--text-dim') || '#94a3b8', cSurface = css('--surface') || '#fff';
    ctx.fillStyle = cBg; ctx.fillRect(0, 0, W, H); ctx.font = '11px DM Mono,monospace'; ctx.textAlign = 'center';
    cv._pts = []; cv._geo = null;
    if (pts.length < 2) { ctx.fillStyle = cDim; ctx.fillText(X(pts.length ? 'accumulating' : 'noData'), W / 2, H / 2); return; }
    const N = pts.length, PL = o.pl || 44, PR = o.pr || 10, PT = 8, PB = 18, W2 = W - PL - PR, H2 = H - PT - PB;
    const prev = o.prev && range !== 'all' ? o.prev : [], k0 = S[0].k;
    const vals = []; pts.forEach(p => S.forEach(x => { const v = Number(p[x.k]); if (p[x.k] != null && isFinite(v)) vals.push(v); }));
    prev.forEach(p => { const v = Number(p[k0]); if (p[k0] != null && isFinite(v)) vals.push(v); });
    if (!vals.length) { ctx.fillStyle = cDim; ctx.fillText(X('noData'), W / 2, H / 2); return; }
    let lo = o.min != null ? o.min : 0, hi = o.max ? o.max : Math.max(...vals, 1) * 1.15;
    if (o.scale) { const r = o.scale(vals); lo = r[0]; hi = r[1]; }
    const rg = hi - lo || 1, xOf = i => PL + (i / (N - 1)) * W2, yOf = v => PT + H2 - ((Math.min(hi, Math.max(lo, v)) - lo) / rg) * H2;
    ctx.strokeStyle = cBorder; ctx.lineWidth = .5; ctx.fillStyle = cDim; ctx.font = '9px DM Mono,monospace'; ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) { const v = lo + rg / 4 * i, y = yOf(v); ctx.beginPath(); ctx.moveTo(PL, y); ctx.lineTo(W - PR, y); ctx.stroke(); ctx.fillText(o.axis ? o.axis(v) : String(Math.round(v)), PL - 3, y + 3); }
    if (o.hline != null && o.hline >= lo && o.hline <= hi) { ctx.save(); ctx.strokeStyle = css('--yellow') || '#f59e0b'; ctx.lineWidth = 1; ctx.setLineDash([4, 4]); ctx.beginPath(); ctx.moveTo(PL, yOf(o.hline)); ctx.lineTo(W - PR, yOf(o.hline)); ctx.stroke(); ctx.restore(); }
    S.forEach((x, si) => {
      const line = () => { ctx.beginPath(); let pen = false; pts.forEach((p, i) => { const v = Number(p[x.k]); if (p[x.k] == null || !isFinite(v)) { pen = false; return; } pen ? ctx.lineTo(xOf(i), yOf(v)) : ctx.moveTo(xOf(i), yOf(v)); pen = true; }); };
      if (si === 0 && !o.points) { line(); ctx.lineTo(xOf(N - 1), PT + H2); ctx.lineTo(PL, PT + H2); ctx.closePath(); const g = ctx.createLinearGradient(0, PT, 0, PT + H2); g.addColorStop(0, x.c + '33'); g.addColorStop(1, x.c + '00'); ctx.fillStyle = g; ctx.fill(); }
      line(); ctx.strokeStyle = x.c; ctx.lineWidth = 1.8; ctx.stroke();
      if (o.points) pts.forEach((p, i) => { if (p[x.k] == null) return; ctx.beginPath(); ctx.arc(xOf(i), yOf(Number(p[x.k])), 2.6, 0, 2 * Math.PI); ctx.fillStyle = x.c; ctx.fill(); });
    });
    if (o.down) pts.forEach((p, i) => { if (p.up === 0) { ctx.fillStyle = 'rgba(239,68,68,.25)'; const w = Math.max(2, W2 / N); ctx.fillRect(xOf(i) - w / 2, PT, w, H2); } });
    if (prev.length > 1) {                                                  // previous period: dotted line stretched to the chart width
      ctx.save(); ctx.strokeStyle = cDim; ctx.globalAlpha = .7; ctx.lineWidth = 1.4; ctx.setLineDash([4, 3]); ctx.beginPath(); let pen = false;
      prev.forEach((p, i) => { const v = Number(p[k0]); if (p[k0] == null || !isFinite(v)) { pen = false; return; } const x = PL + i / (prev.length - 1) * W2; pen ? ctx.lineTo(x, yOf(v)) : ctx.moveTo(x, yOf(v)); pen = true; });
      ctx.stroke(); ctx.restore();
    }
    marks(ctx, cv, o.mod, pts, xOf, PT, H2, o.evFilter);
    ctx.fillStyle = cDim; ctx.font = '9px DM Mono,monospace'; ctx.textAlign = 'center';
    const step = Math.max(1, Math.floor(N / 5)), longRange = range === '1w' || range === '1mo' || range === 'all';
    // Etiquetas de tiempo centradas en su punto, pero sin salirse del borde del gráfico. EN: Time labels centred on their point, but never past the chart edge.
    for (let i = 0; i < N; i += step) {
      const d = new Date(pts[i].ts * 1000), tx = longRange ? d.toLocaleDateString(loc(), {day: '2-digit', month: '2-digit'}) : PCT.time(d), hw = ctx.measureText(tx).width / 2;
      ctx.fillText(tx, Math.max(hw + 1, Math.min(W - hw - 1, xOf(i))), H - 3);
    }
    if (o.lastLabels) {                                                      // current value at the right edge (UPS charts)
      const last = pts[N - 1]; ctx.font = 'bold 9px DM Mono,monospace'; ctx.textAlign = 'left';
      S.forEach((x, si) => { if (last[x.k] != null) { ctx.fillStyle = x.c; ctx.fillText(x.f(Number(last[x.k])).replace(/\s+/g, ''), W - PR + 4, yOf(Number(last[x.k])) + 3 + si * 9); } });
    }
    if (hover >= 0 && hover < N) {
      const cx = xOf(hover), p = pts[hover];
      ctx.beginPath(); ctx.moveTo(cx, PT); ctx.lineTo(cx, PT + H2); ctx.strokeStyle = 'rgba(100,116,139,.4)'; ctx.lineWidth = 1; ctx.setLineDash([3, 3]); ctx.stroke(); ctx.setLineDash([]);
      S.forEach(x => { if (p[x.k] == null) return; ctx.beginPath(); ctx.arc(cx, yOf(Number(p[x.k])), 4, 0, 2 * Math.PI); ctx.fillStyle = x.c; ctx.fill(); ctx.strokeStyle = cSurface; ctx.lineWidth = 1.5; ctx.stroke(); });
    }
    cv._pts = pts; cv._geo = {PL, W2, N};
    if (!cv._vcBound) {
      cv._vcBound = true;
      const tipEl = () => document.getElementById((cv._vc && cv._vc.tipId) || (cv.id + '-tip'));
      cv.addEventListener('mousemove', e => {
        const g = cv._geo, ps = cv._pts, oo = cv._vc; if (!g || !ps || !ps.length || !oo) return;
        const r = cv.getBoundingClientRect(), x = e.clientX - r.left, i = Math.max(0, Math.min(g.N - 1, Math.round((x - g.PL) / g.W2 * (g.N - 1))));
        draw(cv, Object.assign({}, oo, {hover: i}));
        const tip = tipEl(); if (!tip) return;
        const p = ps[i], d = new Date(p.ts * 1000); tip.replaceChildren();
        const hd = document.createElement('div'); hd.style.color = 'var(--text-dim)';
        hd.textContent = d.toLocaleDateString(loc(), {day: '2-digit', month: '2-digit'}) + ' ' + PCT.time(d, true); tip.appendChild(hd);
        oo.series.forEach(sx => {
          const row = document.createElement('div'), dot = document.createElement('span');
          dot.style.cssText = 'display:inline-block;width:8px;height:3px;border-radius:2px;margin-right:6px;background:' + sx.c;
          row.appendChild(dot); row.appendChild(document.createTextNode(sx.l + ': ' + (p[sx.k] == null ? '—' : sx.f(Number(p[sx.k]))))); tip.appendChild(row);
        });
        if (oo.extra) (oo.extra(p) || []).forEach(txt => { const ex = document.createElement('div'); ex.style.cssText = 'color:var(--text-mid)'; ex.textContent = txt; tip.appendChild(ex); });
        (cv._marks || []).filter(m => Math.abs(m.x - x) <= 6).slice(0, 3).forEach(m => {
          const ev = document.createElement('div'); ev.style.cssText = 'margin-top:3px;color:#f59e0b;max-width:240px;white-space:normal';
          ev.textContent = '▲ ' + String(m.e.tx || m.e.k || ''); tip.appendChild(ev);
        });
        tip.classList.add('show');
        const tw = tip.offsetWidth, px = e.clientX - r.left + 14;
        tip.style.left = Math.max(0, Math.min(r.width - tw, px > r.width - tw ? e.clientX - r.left - tw - 14 : px)) + 'px'; tip.style.top = '6px';
      });
      cv.addEventListener('mouseleave', () => { const tip = tipEl(); if (tip) tip.classList.remove('show'); if (cv._vc) draw(cv, Object.assign({}, cv._vc, {hover: -1})); });
    }
  }
  window.VC = {RANGES, X, cmp, filters, section, draw};
})();
