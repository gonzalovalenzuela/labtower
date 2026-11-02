// Marcadores y búsqueda global del Resumen. Usa las variables de app.js (lang, esc, me, lvl, jget, $) y se carga después de él.
// EN: Overview bookmarks and global search. Uses app.js variables (lang, esc, me, lvl, jget, $) and loads after it.
(function () {
  const L = {
    en: {bm: 'Links', edit: 'Edit', save: 'Save', cancel: 'Cancel', add: 'Add link', grp: 'Group', name: 'Name', url: 'https://… or /path', rm: 'Remove',
         none: 'No links yet.', noneAdmin: 'No links yet. Use Edit to add the router, a media server or any page you use.', saveErr: 'Could not save',
         srch: 'Search…', nores: 'No results', kHost: 'Host', kUps: 'UPS', kVm: 'VM', kCt: 'Container', kNas: 'NAS', kDns: 'DNS', kWol: 'Wake-on-LAN', kLink: 'Link'},
    es: {bm: 'Enlaces', edit: 'Editar', save: 'Guardar', cancel: 'Cancelar', add: 'Agregar enlace', grp: 'Grupo', name: 'Nombre', url: 'https://… o /ruta', rm: 'Quitar',
         none: 'Aún no hay enlaces.', noneAdmin: 'Aún no hay enlaces. Usa Editar para agregar el router, un servidor de medios o cualquier página que uses.', saveErr: 'No se pudo guardar',
         srch: 'Buscar…', nores: 'Sin resultados', kHost: 'Equipo', kUps: 'UPS', kVm: 'VM', kCt: 'Contenedor', kNas: 'NAS', kDns: 'DNS', kWol: 'Wake-on-LAN', kLink: 'Enlace'}
  };
  const X = k => (L[lang] || L.en)[k] || k;
  let BM = [], canEdit = false, editing = false, loaded = false, bmTs = 0, wol = [], wolTs = 0, IDX = [], sel = -1;

  // ───────── Marcadores / bookmarks ─────────
  async function loadBm() {
    try {
      const d = await jget('api/bookmarks');
      BM = Array.isArray(d.bookmarks) ? d.bookmarks : []; canEdit = !!d.can_edit; loaded = true; bmTs = Date.now();
    } catch (e) { /* the card keeps what it had */ }
  }
  const linkAttrs = u => u.charAt(0) === '/' ? `href="${esc(u)}"` : `href="${esc(u)}" target="_blank" rel="noopener noreferrer"`;
  function rowHtml(b) {
    return `<div class="bm-row"><input class="bm-g" maxlength="30" placeholder="${esc(X('grp'))}" value="${esc(b.g || '')}">` +
      `<input class="bm-n" maxlength="40" placeholder="${esc(X('name'))}" value="${esc(b.n || '')}">` +
      `<input class="bm-u" maxlength="500" placeholder="${esc(X('url'))}" value="${esc(b.u || '')}">` +
      `<button type="button" class="btn" data-bm="rm" title="${esc(X('rm'))}" aria-label="${esc(X('rm'))}">×</button></div>`;
  }
  function renderBm(force) {
    const el = $('c-bm'); if (!el || (editing && !force)) return;
    if (!loaded || (!BM.length && !canEdit)) { el.classList.add('hide'); return; }
    el.classList.remove('hide');
    let h = `<div class="ch"><h2>${esc(X('bm'))}</h2><span class="spacer"></span>`;
    if (canEdit && !editing) h += `<button type="button" class="btn nokiosk" data-bm="edit">${esc(X('edit'))}</button>`;
    h += '</div>';
    if (editing) {
      h += '<div id="bm-rows">' + (BM.length ? BM : [{}]).map(rowHtml).join('') + '</div>' +
        `<div class="bm-act"><button type="button" class="btn" data-bm="add">${esc(X('add'))}</button><span class="spacer"></span><span class="bm-err" id="bm-err"></span>` +
        `<button type="button" class="btn" data-bm="cancel">${esc(X('cancel'))}</button><button type="button" class="btn bm-save" data-bm="save">${esc(X('save'))}</button></div>`;
    } else if (!BM.length) {
      h += `<div class="sub">${esc(X('noneAdmin'))}</div>`;
    } else {
      const groups = [];
      BM.forEach(b => { let g = groups.find(x => x.g === b.g); if (!g) groups.push(g = {g: b.g, l: []}); g.l.push(b); });
      h += groups.map(g => `<div class="bm-grp">${g.g ? `<div class="bm-gn">${esc(g.g)}</div>` : ''}<div class="bm-list">` +
        g.l.map(b => `<a class="bm" ${linkAttrs(b.u)}><span class="bm-i">${esc((b.n.charAt(0) || '?').toUpperCase())}</span>${esc(b.n)}</a>`).join('') + '</div></div>').join('');
    }
    el.innerHTML = h;
  }
  function readDraft() {
    return Array.from(document.querySelectorAll('#bm-rows .bm-row')).map(r => ({
      g: r.querySelector('.bm-g').value.trim(), n: r.querySelector('.bm-n').value.trim(), u: r.querySelector('.bm-u').value.trim()
    })).filter(b => b.n || b.u || b.g);
  }
  async function saveBm() {
    const err = $('bm-err'), draft = readDraft();
    try {
      const r = await fetch('api/bookmarks', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({bookmarks: draft})});
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { if (err) err.textContent = d.error || X('saveErr'); return; }
      BM = d.bookmarks || draft; editing = false; renderBm(); buildIdx();
    } catch (e) { if (err) err.textContent = X('saveErr'); }
  }
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('[data-bm]'); if (!b) return;
    const a = b.dataset.bm;
    if (a === 'edit') { editing = true; renderBm(true); }
    else if (a === 'cancel') { editing = false; renderBm(true); }
    else if (a === 'add') { const box = $('bm-rows'); if (box) { box.insertAdjacentHTML('beforeend', rowHtml({})); const r = box.lastElementChild; if (r) r.querySelector('.bm-n').focus(); } }
    else if (a === 'rm') { const r = b.closest('.bm-row'); if (r) r.remove(); }
    else if (a === 'save') saveBm();
  });

  // ───────── Búsqueda global / global search ─────────
  let src = {};   // last data of each module (set by linksUpdate)
  const vv = (R, k) => R[k] && R[k].status === 'fulfilled' ? R[k].value : null;
  function buildIdx() {
    const I = [], add = (k, kl, title, sub, href, ext) => { if (title) I.push({k, kl, t: String(title), s: sub.filter(Boolean).join(' · '), href, ext, hay: (title + ' ' + sub.join(' ')).toLowerCase()}); };
    ((src.net || {}).hosts || []).forEach(h => add('net', 'kHost', h.alias || h.hostname || h.ip, [h.ip, h.mac, h.vendor, h.hostname && h.alias ? h.hostname : ''], '/net/'));
    ((src.nut || {}).servers || []).forEach(sv => Object.keys((sv.status || {}).ups || {}).forEach(n => add('nut', 'kUps', n, [sv.name || sv.id], '/nut/')));
    ((src.pve || {}).clusters || []).forEach(c => (((c.snap || {}).data || {}).nodes || []).forEach(nd => {
      (nd.vms || []).filter(v => !v.template).forEach(v => add('pve', 'kVm', v.name, [String(v.vmid || ''), nd.node || nd.name, c.name], '/pve/'));
      (nd.cts || []).filter(v => !v.template).forEach(v => add('pve', 'kCt', v.name, [String(v.vmid || ''), nd.node || nd.name, c.name], '/pve/'));
    }));
    ((src.nas || {}).nas || []).forEach(n => add('nas', 'kNas', n.name, [n.host], '/nas/'));
    ((src.dns || {}).servers || []).forEach(n => add('dns', 'kDns', n.name, [n.host], '/dns/'));
    wol.forEach(d => add('wol', 'kWol', d.name, [d.mac, d.ip, (d.net || {}).name], '/wol/'));
    BM.forEach(b => add('bm', 'kLink', b.n, [b.g, b.u], b.u, b.u.charAt(0) !== '/'));
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
    box.innerHTML = r.length ? r.map((it, i) => `<a class="gsi${i === sel ? ' on' : ''}" href="${esc(it.href)}"${it.ext ? ' target="_blank" rel="noopener noreferrer"' : ''}>` +
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
  function textsLang() { const i = $('gs'); if (i) { i.placeholder = X('srch'); i.setAttribute('aria-label', X('srch')); } renderBm(); paintResults(); }

  // app.js llama a esto después de cada actualización. / app.js calls this after every refresh.
  window.linksUpdate = async function (R) {
    src = {net: vv(R, 'net'), nut: vv(R, 'nut'), pve: vv(R, 'pve'), nas: vv(R, 'nas'), dns: vv(R, 'dns')};
    if (!loaded || Date.now() - bmTs > 60000) { if (!editing) { await loadBm(); renderBm(); } }
    if (lvl('wol') && Date.now() - wolTs > 60000) {
      wolTs = Date.now();
      try { const d = await jget('/wol/api/devices'); wol = Array.isArray(d.devices) ? d.devices : []; } catch (e) { wol = []; }
    }
    buildIdx(); textsLang();
    const w = $('gs-wrap'); if (w) w.classList.remove('hide');
  };
  window.linksLang = textsLang;
  initSearch(); textsLang();
})();
