// Reglas de alerta del Resumen: el administrador define umbrales sobre las métricas que la página ya lee (temperatura, CPU, batería...).
// En cada actualización se evalúan y las que se cumplen salen en el panel de atención. Usa lang, esc, $, jget y issues de app.js; se carga después de él.
// EN: Overview alert rules: the administrator defines thresholds on the metrics the page already reads. They are evaluated on every refresh and the ones that hold show in the attention panel.
(function () {
  const M = {   // key: [module, unit, es, en]
    pi_temp: ['pi', '°C', 'Temperatura del servidor', 'Server temperature'], pi_cpu: ['pi', '%', 'CPU del servidor', 'Server CPU'], pi_mem: ['pi', '%', 'Memoria del servidor', 'Server memory'], pi_disk: ['pi', '%', 'Disco del servidor', 'Server disk'],
    ups_charge: ['ups', '%', 'Batería del UPS', 'UPS battery'], ups_load: ['ups', '%', 'Carga del UPS', 'UPS load'], ups_temp: ['ups', '°C', 'Temperatura del UPS', 'UPS temperature'], ups_runtime: ['ups', 'min', 'Autonomía del UPS', 'UPS runtime'],
    nas_cpu: ['nas', '%', 'CPU del NAS', 'NAS CPU'], nas_mem: ['nas', '%', 'Memoria del NAS', 'NAS memory'], nas_vol: ['nas', '%', 'Volumen más lleno del NAS', 'NAS fullest volume'], nas_temp: ['nas', '°C', 'Temperatura del NAS', 'NAS temperature'],
    pve_cpu: ['pve', '%', 'CPU de nodo Proxmox', 'Proxmox node CPU'], pve_ram: ['pve', '%', 'Memoria de nodo Proxmox', 'Proxmox node memory'],
    dns_pct: ['dns', '%', 'DNS bloqueado', 'DNS blocked'], wan_rtt: ['wan', 'ms', 'Latencia a internet', 'Internet latency'], wan_loss: ['wan', '%', 'Pérdida a internet', 'Internet loss']
  };
  const HREF = {pi: '', ups: '/nut/', nas: '/nas/', pve: '/pve/', dns: '/dns/', wan: '/wan/'};
  const L = {
    en: {title: 'Alert rules', edit: 'Edit', save: 'Save', cancel: 'Cancel', add: 'Add rule', rm: 'Remove', warn: 'Warning', crit: 'Critical', on: 'Active', saveErr: 'Could not save',
         none: 'No rules yet. Use Edit to be warned when, for example, the server temperature goes above 65 °C or the UPS battery drops below 50 %.', noneRO: '', hint: 'Evaluated on this page every refresh; matches appear in the attention panel.', is: 'is'},
    es: {title: 'Reglas de alerta', edit: 'Editar', save: 'Guardar', cancel: 'Cancelar', add: 'Agregar regla', rm: 'Quitar', warn: 'Aviso', crit: 'Crítico', on: 'Activa', saveErr: 'No se pudo guardar',
         none: 'Aún no hay reglas. Usa Editar para que te avise, por ejemplo, si la temperatura del servidor pasa de 65 °C o la batería del UPS baja de 50 %.', noneRO: '', hint: 'Se evalúan en esta página en cada actualización; las que se cumplen salen en el panel de atención.', is: 'está en'}
  };
  const X = k => (L[lang] || L.en)[k] || k, name = k => M[k][lang === 'es' ? 2 : 3];
  let RU = [], canEdit = false, loaded = false, editing = false, ts = 0;

  async function load() {
    try { const d = await jget('api/rules'); RU = Array.isArray(d.rules) ? d.rules : []; canEdit = !!d.can_edit; loaded = true; ts = Date.now(); } catch (e) { /* keeps what it had */ }
  }
  const num = v => { const n = typeof v === 'number' ? v : parseFloat(v); return isFinite(n) ? n : null; };

  // Lecturas actuales de cada métrica: [{k, who, v}]. / Current readings of each metric.
  function readings(R) {
    const out = [], ok = k => R[k] && R[k].status === 'fulfilled' ? R[k].value : null, add = (k, who, v) => { v = num(v); if (v != null) out.push({k, who, v}); };
    const s = ok('sys'); if (s) { add('pi_temp', '', s.temp); add('pi_cpu', '', s.cpu); add('pi_mem', '', s.mem && s.mem.pct); add('pi_disk', '', s.disk && s.disk.pct); }
    ((ok('nut') || {}).servers || []).forEach(sv => Object.entries((sv.status || {}).ups || {}).forEach(([n, v]) => {
      add('ups_charge', n, v['battery.charge']); add('ups_load', n, v['ups.load']); add('ups_temp', n, v['ups.temperature'] != null ? v['ups.temperature'] : v['battery.temperature']);
      const r = num(v['battery.runtime']); if (r != null) add('ups_runtime', n, r / 60);
    }));
    ((ok('nas') || {}).nas || []).forEach(n => {
      const d = ((n.snap || {}).data || {}); add('nas_cpu', n.name, d.cpu && d.cpu.pct); add('nas_mem', n.name, d.mem && d.mem.pct); add('nas_temp', n.name, (d.system || {}).temp);
      const vols = (d.raids || []).filter(x => x.pct != null && !x.pool); if (vols.length) add('nas_vol', n.name, Math.max(...vols.map(x => x.pct)));
    });
    ((ok('pve') || {}).clusters || []).forEach(c => (((c.snap || {}).data || {}).nodes || []).filter(x => x.status === 'online').forEach(x => {
      const w = c.name + '/' + (x.node || x.name); if (x.cpu != null) add('pve_cpu', w, x.cpu * 100); if (x.maxmem) add('pve_ram', w, (x.mem || 0) / x.maxmem * 100);
    }));
    ((ok('dns') || {}).servers || []).forEach(n => { const d = (n.snap || {}).data; if (d) add('dns_pct', n.name, d.pct); });
    const w = (ok('wan') || {}).snap; if (w) { add('wan_rtt', '', w.rtt); add('wan_loss', '', w.loss); }
    return out;
  }

  // Evalúa las reglas activas; agrega los avisos al panel y devuelve la peor severidad. / Evaluates the active rules; adds the issues to the panel and returns the worst severity.
  window.rulesEval = function (R) {
    let sev = 'ok';
    const act = RU.filter(r => r.on);
    if (!act.length) return sev;
    const rd = readings(R);
    act.forEach(r => rd.filter(x => x.k === r.m).forEach(x => {
      if (!(r.o === '>' ? x.v > r.v : x.v < r.v)) return;
      const u = M[r.m][1], val = Math.round(x.v * 10) / 10;
      issues.push({lv: r.lv, m: M[r.m][0], t: `${name(r.m)}${x.who ? ' ' + x.who : ''}: ${val}${u === '°C' ? ' °C' : u === '%' ? '%' : ' ' + u} (${r.o} ${r.v})`, href: HREF[M[r.m][0]] || undefined});
      if (r.lv === 'crit') sev = 'crit'; else if (sev === 'ok') sev = 'warn';
    }));
    return sev;
  };

  const opt = (v, t, cur) => `<option value="${esc(v)}"${v === cur ? ' selected' : ''}>${esc(t)}</option>`;
  function rowHtml(r) {
    r = r || {m: 'pi_temp', o: '>', v: 65, lv: 'warn', on: true};
    return `<div class="rl-row"><select class="rl-m">${Object.keys(M).map(k => opt(k, name(k) + ' (' + M[k][1] + ')', r.m)).join('')}</select>` +
      `<select class="rl-o">${opt('>', '>', r.o)}${opt('<', '<', r.o)}</select><input class="rl-v" type="number" step="any" value="${esc(r.v)}">` +
      `<select class="rl-l">${opt('warn', X('warn'), r.lv)}${opt('crit', X('crit'), r.lv)}</select>` +
      `<label class="rl-on"><input type="checkbox" class="rl-c"${r.on ? ' checked' : ''}> ${esc(X('on'))}</label>` +
      `<button type="button" class="btn" data-rl="rm" title="${esc(X('rm'))}" aria-label="${esc(X('rm'))}">×</button></div>`;
  }
  function render(force) {
    const el = $('c-rules'); if (!el || (editing && !force)) return;
    if (!loaded || (!RU.length && !canEdit)) { el.classList.add('hide'); return; }
    el.classList.remove('hide');
    let h = `<div class="ch"><h2>${esc(X('title'))}</h2><span class="spacer"></span>`;
    if (canEdit && !editing) h += `<button type="button" class="btn nokiosk" data-rl="edit">${esc(X('edit'))}</button>`;
    h += '</div>';
    if (editing) {
      h += '<div id="rl-rows">' + (RU.length ? RU : [null]).map(rowHtml).join('') + '</div>' +
        `<div class="bm-act"><button type="button" class="btn" data-rl="add">${esc(X('add'))}</button><span class="spacer"></span><span class="bm-err" id="rl-err"></span>` +
        `<button type="button" class="btn" data-rl="cancel">${esc(X('cancel'))}</button><button type="button" class="btn bm-save" data-rl="save">${esc(X('save'))}</button></div>`;
    } else if (!RU.length) h += `<div class="empty">${esc(X('none'))}</div>`;
    else h += '<ul class="rl-list">' + RU.map(r => `<li class="${r.on ? '' : 'rl-off'}"><b class="${r.lv}" style="background:none">${esc(X(r.lv))}</b> ${esc(name(r.m))} ${esc(r.o)} ${esc(r.v)} ${esc(M[r.m][1])}</li>`).join('') + `</ul><div class="sub">${esc(X('hint'))}</div>`;
    el.innerHTML = h;
  }
  async function save() {
    const rows = [...document.querySelectorAll('#rl-rows .rl-row')], err = $('rl-err');
    const draft = rows.map(r => ({m: r.querySelector('.rl-m').value, o: r.querySelector('.rl-o').value, v: parseFloat(r.querySelector('.rl-v').value), lv: r.querySelector('.rl-l').value, on: r.querySelector('.rl-c').checked}));
    if (draft.some(d => !isFinite(d.v))) { if (err) err.textContent = X('saveErr'); return; }
    try {
      const r = await fetch('api/rules', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({rules: draft})});
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { if (err) err.textContent = d.error || X('saveErr'); return; }
      RU = d.rules || draft; editing = false; render(true);
      if (typeof refresh === 'function') refresh();
    } catch (e) { if (err) err.textContent = X('saveErr'); }
  }
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('[data-rl]'); if (!b) return;
    const a = b.dataset.rl;
    if (a === 'edit') { editing = true; render(true); }
    else if (a === 'cancel') { editing = false; render(true); }
    else if (a === 'add') { const box = $('rl-rows'); if (box) box.insertAdjacentHTML('beforeend', rowHtml()); }
    else if (a === 'rm') { const r = b.closest('.rl-row'); if (r) r.remove(); }
    else if (a === 'save') save();
  });
  // Se llama en cada actualización: las reglas se leen una vez por minuto. / Called on every refresh: rules are read once a minute.
  window.rulesUpdate = async function () { if (!loaded || Date.now() - ts > 60000) await load(); render(); };
  window.rulesLang = () => render();
})();
