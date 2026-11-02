// Descubrimiento de servicios: sugiere agregar a un monitor los equipos que Net Monitor vio con puertos típicos (Proxmox 8006, UPS 3493, Pi-hole/AdGuard 53 + web,
// Synology 5000/5001) y que todavía no están configurados. Solo lo ve quien es administrador del módulo sugerido. Se carga después de app.js.
// EN: Service discovery: suggests adding to a monitor the devices Net Monitor saw with typical ports (Proxmox 8006, UPS 3493, Pi-hole/AdGuard 53 + web,
//     Synology 5000/5001) that are not configured yet. Only shown to an administrator of the suggested module. Loads after app.js.
(function () {
  const L = {
    en: {title: 'Suggested monitors', hint: 'Net Monitor found these devices; they look like services LabTower can monitor.', open: 'Set up →', dismiss: 'Dismiss', undo: 'Show dismissed',
         pve: 'Proxmox VE', nut: 'UPS (NUT server)', dns: 'Pi-hole / AdGuard Home', nas: 'Synology DSM'},
    es: {title: 'Monitores sugeridos', hint: 'Net Monitor encontró estos equipos; parecen servicios que LabTower puede monitorear.', open: 'Configurar →', dismiss: 'Descartar', undo: 'Mostrar descartados',
         pve: 'Proxmox VE', nut: 'UPS (servidor NUT)', dns: 'Pi-hole / AdGuard Home', nas: 'Synology DSM'}
  };
  const X = k => (L[lang] || L.en)[k] || k;
  const PAGE = {pve: '/pve/', nut: '/nut/', dns: '/dns/', nas: '/nas/'};
  const KEY = 'pi-sug-dismissed';
  let last = null;
  const getDis = () => { try { const v = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(v) ? v : []; } catch (e) { return []; } };
  const setDis = a => { try { localStorage.setItem(KEY, JSON.stringify(a.slice(-200))); } catch (e) { /* private mode */ } };

  // Qué servicios sugiere un equipo según sus puertos abiertos. / Which services a device suggests from its open ports.
  function kinds(h) {
    const p = new Set((h.ports || []).map(x => Number(x && x.port !== undefined ? x.port : x)));
    const out = [];
    if (p.has(8006)) out.push('pve');
    if (p.has(3493)) out.push('nut');
    if (p.has(53) && (p.has(80) || p.has(443) || p.has(3000))) out.push('dns');
    if (p.has(5000) || p.has(5001)) out.push('nas');
    return out;
  }
  // Direcciones ya configuradas en cada monitor. / Addresses already configured in each monitor.
  function configured(src) {
    const c = {pve: new Set(), nut: new Set(), dns: new Set(), nas: new Set()}, add = (k, v) => { if (v) c[k].add(String(v).toLowerCase()); };
    ((src.pve || {}).clusters || []).forEach(x => { add('pve', x.host); (((x.snap || {}).data || {}).nodes || []).forEach(n => { add('pve', n.node); add('pve', n.name); add('pve', n.ip); }); });
    ((src.nut || {}).servers || []).forEach(x => add('nut', x.host));
    ((src.dns || {}).servers || []).forEach(x => add('dns', x.host));
    ((src.nas || {}).nas || []).forEach(x => add('nas', x.host));
    return c;
  }
  function suggestions(src) {
    const hosts = (src.net || {}).hosts || [], c = configured(src), out = [];
    hosts.forEach(h => {
      if (!h.online || !h.ip) return;
      kinds(h).forEach(k => {
        if (lvl(k) < 3) return;                       // only an administrator of that module can add it
        const names = [h.ip, h.hostname, h.alias].filter(Boolean).map(s => String(s).toLowerCase());
        if (names.some(n => c[k].has(n))) return;
        out.push({k, ip: h.ip, name: h.alias || h.hostname || h.ip, id: h.ip + '|' + k});
      });
    });
    return out;
  }
  function render(showAll) {
    const el = $('c-sug'); if (!el) return;
    if (!last) { el.classList.add('hide'); return; }
    const dis = new Set(getDis()), all = suggestions(last), list = showAll ? all : all.filter(s => !dis.has(s.id)), hidden = all.length - all.filter(s => !dis.has(s.id)).length;
    if (!list.length && !hidden) { el.classList.add('hide'); el.innerHTML = ''; return; }
    el.classList.remove('hide');
    let h = `<div class="ch"><h2>${esc(X('title'))}</h2></div><div class="sub">${esc(X('hint'))}</div>`;
    h += list.map(s => `<div class="sug-row"><span class="sug-k">${esc(X(s.k))}</span><span class="sug-n"><b>${esc(s.name)}</b>${s.name !== s.ip ? ' · ' + esc(s.ip) : ''}</span>` +
      `<a class="btn" href="${PAGE[s.k]}">${esc(X('open'))}</a>` +
      (dis.has(s.id) ? '' : `<button type="button" class="btn" data-sug="${esc(s.id)}">${esc(X('dismiss'))}</button>`) + '</div>').join('');
    if (hidden && !showAll) h += `<div><button type="button" class="btn" data-sug-all="1">${esc(X('undo'))} (${hidden})</button></div>`;
    el.innerHTML = h;
  }
  document.addEventListener('click', e => {
    const t = e.target.closest && e.target.closest('[data-sug],[data-sug-all]'); if (!t) return;
    if (t.dataset.sugAll) { setDis([]); render(); return; }
    const a = getDis(); a.push(t.dataset.sug); setDis(a); render();
  });
  window.discoverUpdate = R => {
    const v = k => R[k] && R[k].status === 'fulfilled' ? R[k].value : null;
    last = {net: v('net'), pve: v('pve'), nut: v('nut'), dns: v('dns'), nas: v('nas')};
    render();
  };
  window.discoverLang = () => render();
})();
