// Búsqueda global del Resumen: encuentra equipos de Net Monitor, UPS, VMs y contenedores de Proxmox, NAS, servidores DNS y equipos de Wake-on-LAN. Usa las
// variables de app.js (lang, esc, lvl, jget, $) y se carga después de él.
// EN: Overview global search: finds Net Monitor hosts, UPS, Proxmox VMs and containers, NAS, DNS servers and Wake-on-LAN devices. Uses app.js variables
//     (lang, esc, lvl, jget, $) and loads after it.
(function () {
  const L = {
    en: {srch: 'Search…', nores: 'No results', kHost: 'Host', kUps: 'UPS', kVm: 'VM', kCt: 'Container', kNas: 'NAS', kDns: 'DNS', kWol: 'Wake-on-LAN'},
    es: {srch: 'Buscar…', nores: 'Sin resultados', kHost: 'Equipo', kUps: 'UPS', kVm: 'VM', kCt: 'Contenedor', kNas: 'NAS', kDns: 'DNS', kWol: 'Wake-on-LAN'}
  };
  const X = k => (L[lang] || L.en)[k] || k;
  let wol = [], wolTs = 0, IDX = [], sel = -1;

  let src = {};   // last data of each module (set by searchUpdate)
  const vv = (R, k) => R[k] && R[k].status === 'fulfilled' ? R[k].value : null;
  function buildIdx() {
    const I = [], add = (k, kl, title, sub, href) => { if (title) I.push({k, kl, t: String(title), s: sub.filter(Boolean).join(' · '), href, hay: (title + ' ' + sub.join(' ')).toLowerCase()}); };
    ((src.net || {}).hosts || []).forEach(h => add('net', 'kHost', h.alias || h.hostname || h.ip, [h.ip, h.mac, h.vendor, h.hostname && h.alias ? h.hostname : ''], '/net/'));
    ((src.nut || {}).servers || []).forEach(sv => Object.keys((sv.status || {}).ups || {}).forEach(n => add('nut', 'kUps', n, [sv.name || sv.id], '/nut/')));
    ((src.pve || {}).clusters || []).forEach(c => (((c.snap || {}).data || {}).nodes || []).forEach(nd => {
      (nd.vms || []).filter(v => !v.template).forEach(v => add('pve', 'kVm', v.name, [String(v.vmid || ''), nd.node || nd.name, c.name], '/pve/'));
      (nd.cts || []).filter(v => !v.template).forEach(v => add('pve', 'kCt', v.name, [String(v.vmid || ''), nd.node || nd.name, c.name], '/pve/'));
    }));
    ((src.nas || {}).nas || []).forEach(n => add('nas', 'kNas', n.name, [n.host], '/nas/'));
    ((src.dns || {}).servers || []).forEach(n => add('dns', 'kDns', n.name, [n.host], '/dns/'));
    wol.forEach(d => add('wol', 'kWol', d.name, [d.mac, d.ip, (d.net || {}).name], '/wol/'));
    IDX = I;
  }
  function results(q) {
    const toks = q.toLowerCase().split(/\s+/).filter(Boolean); if (!toks.length) return [];
    const out = [];
    for (const it of IDX) { if (toks.every(t => it.hay.indexOf(t) >= 0)) { out.push(it); if (out.length >= 14) break; } }
    out.sort((a, b) => (b.t.toLowerCase().indexOf(toks[0]) === 0) - (a.t.toLowerCase().indexOf(toks[0]) === 0));
    return out;
  }
  function paintResults() {
    const box = $('gsr'), inp = $('gs'); if (!box || !inp) return;
    const q = inp.value.trim();
    if (!q) { box.classList.add('hide'); box.innerHTML = ''; sel = -1; return; }
    const r = results(q); sel = r.length ? 0 : -1;
    box.innerHTML = r.length ? r.map((it, i) => `<a class="gsi${i === sel ? ' on' : ''}" href="${esc(it.href)}">` +
      `<span class="gsk">${esc(X(it.kl))}</span><span class="gst">${esc(it.t)}</span><span class="gss">${esc(it.s)}</span></a>`).join('') : `<div class="gsn">${esc(X('nores'))}</div>`;
    box.classList.remove('hide');
  }
  function move(d) {
    const items = document.querySelectorAll('#gsr .gsi'); if (!items.length) return;
    sel = (sel + d + items.length) % items.length;
    items.forEach((a, i) => a.classList.toggle('on', i === sel));
    if (items[sel].scrollIntoView) items[sel].scrollIntoView({block: 'nearest'});
  }
  function initSearch() {
    const inp = $('gs'); if (!inp) return;
    inp.addEventListener('input', paintResults);
    inp.addEventListener('focus', paintResults);
    inp.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') { const a = document.querySelector('#gsr .gsi.on'); if (a) { e.preventDefault(); a.click(); } }
      else if (e.key === 'Escape') { inp.value = ''; paintResults(); inp.blur(); }
    });
    document.addEventListener('click', e => { if (!e.target.closest || !e.target.closest('.gs-wrap')) { const b = $('gsr'); if (b) b.classList.add('hide'); } });
    document.addEventListener('keydown', e => {
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey && !/^(INPUT|TEXTAREA|SELECT)$/.test((e.target || {}).tagName || '')) { e.preventDefault(); inp.focus(); }
    });
  }
  function textsLang() { const i = $('gs'); if (i) { i.placeholder = X('srch'); i.setAttribute('aria-label', X('srch')); } paintResults(); }

  // app.js llama a esto después de cada actualización. / app.js calls this after every refresh.
  window.searchUpdate = async function (R) {
    src = {net: vv(R, 'net'), nut: vv(R, 'nut'), pve: vv(R, 'pve'), nas: vv(R, 'nas'), dns: vv(R, 'dns')};
    if (lvl('wol') && Date.now() - wolTs > 60000) {
      wolTs = Date.now();
      try { const d = await jget('/wol/api/devices'); wol = Array.isArray(d.devices) ? d.devices : []; } catch (e) { wol = []; }
    }
    buildIdx(); textsLang();
    const w = $('gs-wrap'); if (w) w.classList.remove('hide');
  };
  window.searchLang = textsLang;
  initSearch(); textsLang();
})();
