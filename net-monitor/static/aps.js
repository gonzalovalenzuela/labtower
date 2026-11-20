// AP Monitor — pestaña de Net Monitor para los puntos de acceso Wi-Fi: estado, uptime, radios, SSID y clientes conectados.
// Tipos: OpenWrt (ubus), MitraStar Smart WiFi (web o ping) y HPE Aruba Instant On (portal en la nube o ping). Se agregan desde aquí (solo admin).
// EN: AP Monitor — Net Monitor tab for Wi-Fi access points: status, uptime, radios, SSIDs and connected clients.
//     Types: OpenWrt (ubus), MitraStar Smart WiFi (web or ping) and HPE Aruba Instant On (cloud portal or ping). Added from here (admin only).
// Usa t(), esc(), toast(), canAdmin() y LANG de app.js. Sin JavaScript en línea (CSP): eventos delegados con data-act.
// EN: Uses t(), esc(), toast(), canAdmin() and LANG from app.js. No inline JavaScript (CSP): delegated events with data-act.
(function () {
'use strict';
if (typeof LANG === 'undefined' || typeof t !== 'function') return;

Object.assign(LANG.en, {
  tabAps: 'AP Monitor',
  apKpiOnline: 'APs online', apKpiClients: 'Wi-Fi clients', apKpi24: 'Clients 2.4 GHz', apKpi5: 'Clients 5 GHz', apKpiSsid: 'SSIDs',
  apSubStatus: 'Status', apSubClients: 'Clients', apAdd: '+ Add AP', apEdit: 'Edit', apRefresh: 'Refresh', apRefreshing: 'Refreshing…',
  apUpdated: s => 'Updated ' + s + ' ago', apNever: 'no data yet', apEvery: 'every', apSec: 's', apMin: 'min',
  apEmptyAdmin: 'No access points yet. Add one to see its status, radios and clients.', apEmptyRead: 'No access points have been added yet.',
  apOnline: 'Online', apOffline: 'Unreachable', apPaused: 'Paused', apWaiting: 'Waiting for the first reading…', apPingOnly: 'Ping only',
  apPause: 'Pause', apResume: 'Resume', apPausedOk: n => n + ' paused', apResumedOk: n => n + ' resumed',
  apUptime: 'Uptime', apSerial: 'Serial', apBand: 'Band', apChannel: 'Channel', apWidth: 'Width', apPower: 'Power', apUtil: 'Channel use', apClients: 'Clients',
  apSsids: 'SSIDs', apNoClients: 'This device does not report its clients.', apNoRadios: 'No radio data.',
  apColAp: 'AP', apColName: 'Name', apColIp: 'IP', apColMac: 'MAC', apColBand: 'Band', apColSsid: 'SSID', apColSignal: 'Signal', apColRate: 'Rate', apColTime: 'Connected',
  apSearch: 'Search name, IP, MAC, AP or SSID…', apAll: 'All APs', apCount: (n, m) => n + ' of ' + m + ' clients', apNone: 'No clients.', apNoMatch: 'Nothing matches the search.',
  apMdlAdd: 'Add access point', apMdlEdit: 'Edit access point', apName: 'Name', apType: 'Type', apMode: 'How to read it', apHost: 'IP or name', apUser: 'User', apPass: 'Password',
  apAccount: 'Instant On account (e-mail)', apSite: 'Site (empty = all)', apKeep: 'leave empty to keep the stored one', apActive: 'Monitor this entry (untick to pause it without deleting it)',
  apDrvOpenwrt: 'OpenWrt (ubus)', apDrvMitrastar: 'MitraStar Smart WiFi (Movistar)', apDrvInstanton: 'HPE Aruba Instant On', apDrvUnifi: 'Ubiquiti UniFi (controller)',
  apModeController: 'UniFi Network controller (status, radios and clients)', apController: 'Controller (IP or name, optional :port)', apSiteId: 'Site id (empty = default)', apVerifyTls: 'Verify TLS against the system CAs (otherwise the fingerprint is pinned)',
  apHintUnifi: 'Reads the UniFi Network controller (UniFi OS on a UDM or Cloud Key, or the classic controller) with a local user, preferably read-only, without 2FA. One entry brings every AP of the site. Without "Verify TLS" the certificate fingerprint is pinned on the first read.',
  apModeUbus: 'ubus (status, radios and clients)', apModeWeb: 'Web session (model, firmware, SSIDs and channels)', apModeCloud: 'Cloud portal (status, radios and clients)', apModePing: 'Ping only (online or not)',
  apHintOpenwrt: 'Uses ubus: uhttpd-mod-ubus or, on OpenWrt 19.07 and later, the one in LuCI. The root user works. Channel use only if the AP allows it.',
  apHintWeb: 'Logs in, reads the info page and logs out on every reading. This unit does not report clients or uptime. While LabTower reads it, the unit\'s web page may sign you out.',
  apHintCloud: 'Uses the Instant On cloud portal (unofficial HPE API, it may change). The account cannot have 2FA: use a separate account invited to the site. Depends on the Internet.',
  apHintPing: 'Only checks that the device answers ping.',
  apTest: 'Test', apTesting: 'Testing…', apSave: 'Save', apDelete: 'Delete', apCancel: 'Cancel', apDelConfirm: n => 'Delete "' + n + '"?',
  apTestOk: r => 'OK — ' + r.aps + ' AP' + (r.aps === 1 ? '' : 's') + ' (' + r.online + ' online)' + (r.model ? ', ' + r.model : '') + (r.clients != null ? ', ' + r.clients + ' clients' : '') + ' · ' + r.seconds + ' s',
  apSaved: 'Access point saved', apDeleted: 'Access point deleted', apPollSet: 'Interval updated',
  apReadOnlyNote: 'Read-only: this tab only reads from the access points; nothing here changes them.',
  apQ: { good: 'good', fair: 'fair', poor: 'poor' }
});
Object.assign(LANG.es, {
  tabAps: 'AP Monitor',
  apKpiOnline: 'AP en línea', apKpiClients: 'Clientes Wi-Fi', apKpi24: 'Clientes 2,4 GHz', apKpi5: 'Clientes 5 GHz', apKpiSsid: 'SSID',
  apSubStatus: 'Estado', apSubClients: 'Clientes', apAdd: '+ Agregar AP', apEdit: 'Editar', apRefresh: 'Actualizar', apRefreshing: 'Actualizando…',
  apUpdated: s => 'Actualizado hace ' + s, apNever: 'sin datos aún', apEvery: 'cada', apSec: 's', apMin: 'min',
  apEmptyAdmin: 'Aún no hay puntos de acceso. Agrega uno para ver su estado, radios y clientes.', apEmptyRead: 'Todavía no se ha agregado ningún punto de acceso.',
  apOnline: 'En línea', apOffline: 'Sin conexión', apPaused: 'Pausado', apWaiting: 'Esperando la primera lectura…', apPingOnly: 'Solo ping',
  apPause: 'Pausar', apResume: 'Reanudar', apPausedOk: n => n + ' pausado', apResumedOk: n => n + ' reanudado',
  apUptime: 'Encendido', apSerial: 'Serie', apBand: 'Banda', apChannel: 'Canal', apWidth: 'Ancho', apPower: 'Potencia', apUtil: 'Uso del canal', apClients: 'Clientes',
  apSsids: 'SSID', apNoClients: 'Este equipo no informa sus clientes.', apNoRadios: 'Sin datos de radios.',
  apColAp: 'AP', apColName: 'Nombre', apColIp: 'IP', apColMac: 'MAC', apColBand: 'Banda', apColSsid: 'SSID', apColSignal: 'Señal', apColRate: 'Velocidad', apColTime: 'Conectado',
  apSearch: 'Buscar nombre, IP, MAC, AP o SSID…', apAll: 'Todos los AP', apCount: (n, m) => n + ' de ' + m + ' clientes', apNone: 'Sin clientes.', apNoMatch: 'Nada coincide con la búsqueda.',
  apMdlAdd: 'Agregar punto de acceso', apMdlEdit: 'Editar punto de acceso', apName: 'Nombre', apType: 'Tipo', apMode: 'Cómo leerlo', apHost: 'IP o nombre', apUser: 'Usuario', apPass: 'Contraseña',
  apAccount: 'Cuenta Instant On (correo)', apSite: 'Sitio (vacío = todos)', apKeep: 'vacío = conservar la guardada', apActive: 'Vigilar esta entrada (desmarca para pausarla sin borrarla)',
  apDrvOpenwrt: 'OpenWrt (ubus)', apDrvMitrastar: 'MitraStar Smart WiFi (Movistar)', apDrvInstanton: 'HPE Aruba Instant On', apDrvUnifi: 'Ubiquiti UniFi (controlador)',
  apModeController: 'Controlador UniFi Network (estado, radios y clientes)', apController: 'Controlador (IP o nombre, :puerto opcional)', apSiteId: 'Id del sitio (vacío = default)', apVerifyTls: 'Verificar TLS con las CA del sistema (si no, se fija la huella)',
  apHintUnifi: 'Lee el controlador UniFi Network (UniFi OS en un UDM o Cloud Key, o el controlador clásico) con un usuario local, de preferencia de solo lectura y sin 2FA. Una entrada trae todos los AP del sitio. Sin «Verificar TLS» la huella del certificado se fija en la primera lectura.',
  apModeUbus: 'ubus (estado, radios y clientes)', apModeWeb: 'Sesión web (modelo, firmware, SSID y canales)', apModeCloud: 'Portal en la nube (estado, radios y clientes)', apModePing: 'Solo ping (responde o no)',
  apHintOpenwrt: 'Usa ubus: uhttpd-mod-ubus o, en OpenWrt 19.07 y posteriores, el de LuCI. El usuario root sirve. El uso del canal, solo si el AP lo permite.',
  apHintWeb: 'Inicia sesión, lee la página de información y cierra la sesión en cada lectura. Este equipo no informa clientes ni uptime. Mientras LabTower lo lee, la web del equipo te puede cerrar la sesión.',
  apHintCloud: 'Usa el portal en la nube de Instant On (API no oficial de HPE, puede cambiar). La cuenta no puede tener 2FA: usa una cuenta aparte invitada al sitio. Depende de internet.',
  apHintPing: 'Solo revisa que el equipo responda al ping.',
  apTest: 'Probar', apTesting: 'Probando…', apSave: 'Guardar', apDelete: 'Eliminar', apCancel: 'Cancelar', apDelConfirm: n => '¿Eliminar «' + n + '»?',
  apTestOk: r => 'OK — ' + r.aps + ' AP (' + r.online + ' en línea)' + (r.model ? ', ' + r.model : '') + (r.clients != null ? ', ' + r.clients + ' clientes' : '') + ' · ' + r.seconds + ' s',
  apSaved: 'Punto de acceso guardado', apDeleted: 'Punto de acceso eliminado', apPollSet: 'Intervalo actualizado',
  apReadOnlyNote: 'Solo lectura: esta pestaña solo lee de los puntos de acceso; nada aquí los modifica.',
  apQ: { good: 'buena', fair: 'regular', poor: 'mala' }
});

const $ = id => document.getElementById(id);
const AP = { sub: 'status', data: null, hash: '', timer: null, busy: false, again: false, q: '', only: '' };
const POLLS = [30, 60, 120, 300, 600];
const MODES = { openwrt: ['ubus'], mitrastar: ['web', 'ping'], instanton: ['cloud', 'ping'], unifi: ['controller', 'ping'] };
const MODE_LBL = { ubus: 'apModeUbus', web: 'apModeWeb', cloud: 'apModeCloud', controller: 'apModeController', ping: 'apModePing' };
const HINT = { ubus: 'apHintOpenwrt', web: 'apHintWeb', cloud: 'apHintCloud', controller: 'apHintUnifi', ping: 'apHintPing' };

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (r.status === 401) { location.reload(); throw new Error('401'); }
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || ('HTTP ' + r.status));
  return d;
}
const post = (p, b) => api(p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b || {}) });

// ── Formatos / formats ───────────────────────────────────────────────────────────────────
function dur(s) {
  if (s == null) return '—';
  const d = Math.floor(s / 86400), h = Math.floor(s / 3600) % 24, m = Math.floor(s / 60) % 60;
  return d ? d + 'd ' + h + 'h' : h ? h + 'h ' + m + 'm' : m + 'm';
}
function ago(sec) { return sec == null ? '—' : sec < 60 ? Math.round(sec) + ' ' + t('apSec') : Math.floor(sec / 60) + ' ' + t('apMin'); }
const bandTxt = b => b ? b.replace('.', _lang === 'es' ? ',' : '.') + ' GHz' : '—';
// Ancho del canal: «80mhz» (Instant On) se muestra «80 MHz»; «HT40» (OpenWrt) queda igual. / EN: channel width: "80mhz" shows as "80 MHz".
const widthTxt = w => !w ? '—' : /^\d+\s*mhz$/i.test(w) ? w.replace(/\s*mhz$/i, ' MHz') : w;
function signal(c) {
  if (c.signal != null) return `<span class="${c.signal >= -65 ? 'ap-ok' : c.signal >= -75 ? 'amber' : 'ap-bad'}">${c.signal} dBm</span>`;
  if (c.snr != null) return `<span class="${c.snr >= 25 ? 'ap-ok' : c.snr >= 15 ? 'amber' : 'ap-bad'}">SNR ${c.snr} dB</span>`;
  return '<span class="dim">—</span>';
}
const allClients = d => d.aps.filter(a => !a.paused && a.clients).flatMap(a => a.clients.map(c => ({ ...c, ap: a.name })));

// ── Vista / view ─────────────────────────────────────────────────────────────────────────
// switches.js cambia de pestaña y avisa con el evento «netview»; esta pestaña solo lee mientras está visible.
// EN: switches.js switches tabs and fires the "netview" event; this tab only polls while visible.
document.addEventListener('netview', e => {
  clearInterval(AP.timer);
  if (e.detail === 'aps') { load(); AP.timer = setInterval(() => { if (!document.hidden) load(); }, 10000); }
});

// Si llega un pedido mientras otro está en curso (un clic durante el refresco), se repite al terminar para no perder el cambio.
// EN: A request arriving while another runs (a click during the refresh) is repeated afterwards so the change is not lost.
async function load() {
  if (AP.busy) { AP.again = true; return; }
  AP.busy = true;
  try {
    const d = await api('api/aps');
    const h = AP.sub + JSON.stringify(d.aps) + d.poll_seconds + (typeof ME !== 'undefined' && ME && ME.permissions ? ME.permissions.net : '');
    AP.data = d;
    if (h !== AP.hash) { AP.hash = h; render(); } else updateStamp();
  } catch (e) { if (e.message !== '401') console.error(e); }
  finally { AP.busy = false; if (AP.again) { AP.again = false; load(); } }
}

function updateStamp() {
  const el = $('ap-stamp'); if (!el || !AP.data) return;
  const ages = AP.data.aps.map(a => a.updated ? AP.data.now - a.updated : null).filter(v => v != null);
  el.textContent = ages.length ? t('apUpdated', ago(Math.max(0, Math.min(...ages)))) : t('apNever');
}

function pill(a) {
  if (a.paused) return `<span class="sw-pill">${esc(t('apPaused'))}</span>`;
  if (a.waiting) return `<span class="sw-pill">${esc(t('apWaiting'))}</span>`;
  return a.online ? `<span class="sw-pill green">${esc(t('apOnline'))}</span>` : `<span class="sw-pill red">${esc(t('apOffline'))}</span>`;
}

function card(a) {
  const admin = canAdmin(), ping = a.mode === 'ping';
  const sub = [a.model, a.ip || a.host, a.fw ? 'fw ' + a.fw : '', a.serial ? t('apSerial') + ' ' + a.serial : ''].filter(Boolean).join(' · ');
  const entry = a.entry !== a.name ? `<span class="dim">${esc(a.entry)}</span>` : '';
  const btns = admin ? `<button type="button" class="sw-btn" data-act="pause" data-id="${esc(a.id)}" data-name="${esc(a.entry)}" data-on="${a.paused ? '1' : ''}">${esc(a.paused ? '▶ ' + t('apResume') : '⏸ ' + t('apPause'))}</button><button type="button" class="sw-btn" data-act="edit" data-id="${esc(a.id)}">${esc(t('apEdit'))}</button>` : '';
  const facts = [a.uptime != null ? t('apUptime') + ' ' + dur(a.uptime) : '', a.nclients != null ? t('apClients') + ' ' + a.nclients : '', ping ? t('apPingOnly') : a.note || ''].filter(Boolean);
  const err = a.error && !a.online && !a.paused ? `<div class="sw-err">${esc(a.error)}</div>` : '';
  let body = '';
  if (!ping && a.radios.length) {
    body += `<div class="sw-tablewrap"><table class="sw-table"><thead><tr>${['apBand', 'apChannel', 'apWidth', 'apPower', 'apUtil', 'apClients'].map(h => `<th>${esc(t(h))}</th>`).join('')}</tr></thead><tbody>` +
      a.radios.map(r => `<tr><td>${esc(bandTxt(r.band))}</td><td>${r.channel != null ? esc(r.channel) : '—'}</td><td>${esc(widthTxt(r.width))}</td><td>${r.txpower != null ? esc(r.txpower) + ' dBm' : '—'}</td>` +
        `<td>${r.util != null ? `<span class="${r.util >= 70 ? 'ap-bad' : r.util >= 50 ? 'amber' : ''}">${esc(r.util)} %</span>` : '—'}</td><td>${r.clients != null ? esc(r.clients) : '—'}</td></tr>`).join('') + '</tbody></table></div>';
  }
  if (!ping && a.ssids.length) body += `<div class="ap-ssids"><span class="dim">${esc(t('apSsids'))}:</span> ${a.ssids.map(s => `<span class="sw-pill">${esc(s.name)}${s.bands.length ? ' · ' + esc(s.bands.map(bandTxt).join(' / ')) : ''}</span>`).join(' ')}</div>`;
  if (!ping && a.clients === null && a.online) body += `<div class="sw-note">${esc(t('apNoClients'))}</div>`;
  return `<div class="card sw-card${a.paused ? ' paused' : ''}"><div class="sw-head"><b class="sw-name">${esc(a.name)}</b>${entry}<span class="dim mono">${esc(sub)}</span>${pill(a)}<span class="grow"></span>` +
    `<span class="dim mono">${esc(facts.join(' · '))}</span>${btns}</div>${err}${body}</div>`;
}

function clientsBody() {
  const d = AP.data, all = allClients(d), q = AP.q.trim().toLowerCase();
  const rows = all.filter(c => (!AP.only || c.ap === AP.only) && (!q || [c.name, c.ip, c.mac, c.ap, c.ssid].some(v => v && String(v).toLowerCase().includes(q))))
    .sort((x, y) => (x.ap || '').localeCompare(y.ap || '') || (x.name || x.ip || x.mac).localeCompare(y.name || y.ip || y.mac));
  const html = rows.length ? rows.map(c => `<tr><td>${esc(c.ap)}</td><td>${c.name ? esc(c.name) : '<span class="dim">—</span>'}</td><td class="mono">${esc(c.ip || '—')}</td><td class="mono">${esc(c.mac)}</td>` +
    `<td>${esc(bandTxt(c.band))}</td><td>${esc(c.ssid || '—')}</td><td>${signal(c)}${c.quality ? ' <span class="dim">' + esc(t('apQ')[c.quality] || c.quality) + '</span>' : ''}</td><td>${c.rate != null ? esc(c.rate) + ' Mb/s' : '—'}</td><td>${esc(dur(c.connected))}</td></tr>`).join('')
    : `<tr><td colspan="9"><div class="sw-nodata">${esc(all.length ? t('apNoMatch') : t('apNone'))}</div></td></tr>`;
  return { html, count: t('apCount', rows.length, all.length) };
}

function clientsHtml() {
  const names = [...new Set(AP.data.aps.filter(a => a.clients).map(a => a.name))];
  const b = clientsBody();
  return `<div class="card sw-card"><div class="sw-macbar"><input id="ap-q" type="search" class="sw-search" autocomplete="off" value="${esc(AP.q)}" placeholder="${esc(t('apSearch'))}">` +
    `<select id="ap-only" class="sw-sel"><option value="">${esc(t('apAll'))}</option>${names.map(n => `<option value="${esc(n)}"${n === AP.only ? ' selected' : ''}>${esc(n)}</option>`).join('')}</select><span class="dim mono" id="ap-count">${esc(b.count)}</span></div>` +
    `<div class="sw-tablewrap"><table class="sw-table"><thead><tr>${['apColAp', 'apColName', 'apColIp', 'apColMac', 'apColBand', 'apColSsid', 'apColSignal', 'apColRate', 'apColTime'].map(h => `<th>${esc(t(h))}</th>`).join('')}</tr></thead><tbody id="ap-cbody">${b.html}</tbody></table></div></div>`;
}

function render() {
  const root = $('view-aps'); if (!root || !AP.data) return;
  const d = AP.data, admin = canAdmin(), A = d.aps.filter(a => !a.paused);
  const cl = allClients(d), b24 = cl.filter(c => c.band === '2.4').length, b5 = cl.filter(c => c.band === '5').length;
  const ssids = new Set(A.flatMap(a => a.ssids.map(s => s.name)));
  const kpi = (ico, val, lbl) => `<div class="stat-card"><div class="stat-ico ${ico}"><svg viewBox="0 0 24 24"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg></div><div><div class="stat-val">${val}</div><div class="stat-lbl">${esc(lbl)}</div></div></div>`;
  const polls = POLLS.map(v => `<option value="${v}"${v === d.poll_seconds ? ' selected' : ''}>${v >= 60 ? v / 60 + ' ' + t('apMin') : v + ' ' + t('apSec')}</option>`).join('') + (POLLS.includes(d.poll_seconds) ? '' : `<option value="${d.poll_seconds}" selected>${d.poll_seconds} ${t('apSec')}</option>`);
  const pollTxt = d.poll_seconds >= 60 ? d.poll_seconds / 60 + ' ' + t('apMin') : d.poll_seconds + ' ' + t('apSec');
  const bar = `<div class="sw-bar"><span class="dim mono" id="ap-stamp"></span><span class="dim mono">· ${esc(t('apEvery'))} ${admin ? `<select id="ap-poll" class="sw-sel">${polls}</select>` : esc(pollTxt)}</span><span class="grow"></span>` +
    `<button type="button" class="sw-btn" data-act="refresh">↻ ${esc(t('apRefresh'))}</button>${admin ? `<button type="button" class="sw-btn teal" data-act="add">${esc(t('apAdd'))}</button>` : ''}</div>`;
  const subbar = `<div class="sw-sub"><button type="button" class="sw-chip${AP.sub === 'status' ? ' active' : ''}" data-act="sub" data-sub="status">${esc(t('apSubStatus'))}</button><button type="button" class="sw-chip${AP.sub === 'clients' ? ' active' : ''}" data-act="sub" data-sub="clients">${esc(t('apSubClients'))}</button></div>`;
  if (!d.aps.length) { root.innerHTML = bar + `<div class="card sw-card"><div class="sw-nodata">${esc(admin ? t('apEmptyAdmin') : t('apEmptyRead'))}</div></div>`; updateStamp(); return; }
  if (AP.sub === 'clients') { root.innerHTML = bar + subbar + clientsHtml(); updateStamp(); return; }
  root.innerHTML = bar + subbar +
    `<div class="stats-row">${kpi('teal', A.filter(a => a.online).length + '/' + A.length, t('apKpiOnline'))}${kpi('green', cl.length, t('apKpiClients'))}${kpi('blue', b24, t('apKpi24'))}${kpi('orange', b5, t('apKpi5'))}${kpi('red', ssids.size, t('apKpiSsid'))}</div>` +
    d.aps.map(card).join('') + `<div class="sw-note">${esc(t('apReadOnlyNote'))}</div>`;
  updateStamp();
}

// ── Formulario de alta / edición / add-edit form ─────────────────────────────────────────
function closeModal() { const m = $('ap-modal'); if (m) m.remove(); }
async function openModal(id) {
  let cur = null;
  if (id) { try { cur = (await api('api/aps/config')).aps.find(a => a.id === id); } catch (e) {} }
  closeModal();
  const c = cur || { driver: 'openwrt', mode: 'ubus', name: '', host: '', user: '' };
  const m = document.createElement('div'); m.id = 'ap-modal'; m.className = 'sw-ov';
  m.innerHTML = `<div class="sw-dlg" role="dialog"><h3>${esc(t(cur ? 'apMdlEdit' : 'apMdlAdd'))}</h3>` +
    `<label>${esc(t('apName'))}<input id="am-name" maxlength="32" value="${esc(c.name)}"></label>` +
    `<label>${esc(t('apType'))}<select id="am-driver"><option value="openwrt">${esc(t('apDrvOpenwrt'))}</option><option value="mitrastar">${esc(t('apDrvMitrastar'))}</option><option value="instanton">${esc(t('apDrvInstanton'))}</option><option value="unifi">${esc(t('apDrvUnifi'))}</option></select></label>` +
    `<label>${esc(t('apMode'))}<select id="am-mode"></select></label><div id="am-hint" class="sw-note"></div>` +
    `<label class="am-host"><span id="am-host-l">${esc(t('apHost'))}</span><input id="am-host" value="${esc(c.host || '')}" placeholder="192.0.2.x"></label>` +
    `<label class="am-user">${esc(t('apUser'))}<input id="am-user" maxlength="64" value="${esc(c.driver === 'openwrt' || c.driver === 'unifi' ? c.user || '' : 'root')}" autocomplete="off"></label>` +
    `<label class="am-uni">${esc(t('apSiteId'))}<input id="am-usite" maxlength="64" value="${esc(c.driver === 'unifi' ? c.site || '' : '')}" placeholder="default"></label>` +
    `<label class="chk am-uni"><input type="checkbox" id="am-tls"${c.verify_tls ? ' checked' : ''}> ${esc(t('apVerifyTls'))}</label>` +
    `<label class="am-acct">${esc(t('apAccount'))}<input id="am-acct" maxlength="128" value="${esc(c.driver === 'instanton' ? c.user || '' : '')}" autocomplete="off"></label>` +
    `<label class="am-acct">${esc(t('apSite'))}<input id="am-site" maxlength="64" value="${esc(c.site || '')}"></label>` +
    `<label class="am-pass">${esc(t('apPass'))}<input id="am-pass" type="password" autocomplete="new-password" placeholder="${cur && c.has_password ? esc(t('apKeep')) : ''}"></label>` +
    `<label class="chk"><input type="checkbox" id="am-on"${c.enabled === false ? '' : ' checked'}> ${esc(t('apActive'))}</label>` +
    `<div id="am-res" class="m-res"></div><div class="m-btns">${cur ? `<button type="button" class="sw-btn red" data-act="mdel" data-id="${esc(c.id)}">${esc(t('apDelete'))}</button>` : ''}<span class="grow"></span>` +
    `<button type="button" class="sw-btn" data-act="mcancel">${esc(t('apCancel'))}</button><button type="button" class="sw-btn" data-act="mtest" data-id="${esc(c.id || '')}">${esc(t('apTest'))}</button><button type="button" class="sw-btn teal" data-act="msave" data-id="${esc(c.id || '')}">${esc(t('apSave'))}</button></div></div>`;
  document.body.appendChild(m);
  $('am-driver').value = c.driver;
  const fill = mode => { const d = $('am-driver').value; $('am-mode').innerHTML = MODES[d].map(v => `<option value="${v}">${esc(t(MODE_LBL[v]))}</option>`).join(''); $('am-mode').value = MODES[d].includes(mode) ? mode : MODES[d][0]; };
  const sync = () => {
    const d = $('am-driver').value, mo = $('am-mode').value, cloud = mo === 'cloud';
    $('am-hint').textContent = t(HINT[mo]);
    m.querySelector('.am-host').style.display = cloud ? 'none' : '';
    m.querySelector('.am-user').style.display = d === 'openwrt' || mo === 'controller' ? '' : 'none';
    m.querySelectorAll('.am-uni').forEach(x => { x.style.display = mo === 'controller' ? '' : 'none'; });
    $('am-host-l').textContent = t(mo === 'controller' ? 'apController' : 'apHost');
    m.querySelectorAll('.am-acct').forEach(x => { x.style.display = cloud ? '' : 'none'; });
    m.querySelector('.am-pass').style.display = mo === 'ping' ? 'none' : '';
  };
  fill(c.mode);
  $('am-driver').addEventListener('change', () => { fill(); sync(); });
  $('am-mode').addEventListener('change', sync); sync();
  m.addEventListener('click', e => { if (e.target === m) closeModal(); else onClick(e); });
  $('am-name').focus();
}
function formBody(id) {
  const b = { name: $('am-name').value.trim(), driver: $('am-driver').value, mode: $('am-mode').value, enabled: $('am-on').checked, password: $('am-pass').value };
  if (id) b.id = id;
  if (b.mode === 'cloud') { b.user = $('am-acct').value.trim(); b.site = $('am-site').value.trim(); }
  else {
    b.host = $('am-host').value.trim();
    if (b.driver === 'openwrt') b.user = $('am-user').value.trim() || 'root';
    if (b.mode === 'controller') { b.user = $('am-user').value.trim(); b.site = $('am-usite').value.trim(); b.verify_tls = $('am-tls').checked; }
  }
  return b;
}

// ── Eventos / events ─────────────────────────────────────────────────────────────────────
async function onClick(e) {
  const el = e.target.closest && e.target.closest('[data-act]'); if (!el) return;
  const act = el.dataset.act, id = el.dataset.id;
  try {
    if (act === 'refresh') { toast(t('apRefreshing')); await post('api/aps/refresh', {}); setTimeout(load, 5000); }
    else if (act === 'add') openModal(null);
    else if (act === 'edit') openModal(id);
    else if (act === 'pause') {
      // Pausar o reanudar sin abrir «Editar»: solo cambia «Vigilar esta entrada». / EN: Pause or resume without opening "Edit".
      const resume = el.dataset.on === '1'; el.disabled = true;
      try { await post('api/aps/save', { id, enabled: resume }); toast(t(resume ? 'apResumedOk' : 'apPausedOk', el.dataset.name || '')); AP.hash = ''; await load(); }
      catch (er) { toast(er.message, true); el.disabled = false; }
    }
    else if (act === 'sub') {
      AP.sub = el.dataset.sub === 'clients' ? 'clients' : 'status';
      try { localStorage.setItem('pi-ap-sub', AP.sub); } catch (er) {}
      AP.hash = ''; if (AP.data) render(); await load();
    }
    else if (act === 'mcancel') closeModal();
    else if (act === 'mtest') {
      const r = $('am-res'); r.className = 'm-res'; r.textContent = t('apTesting'); el.disabled = true;
      try { const d = await post('api/aps/test', formBody(id)); r.className = 'm-res ok'; r.textContent = t('apTestOk', d); }
      catch (er) { r.className = 'm-res bad'; r.textContent = er.message; }
      el.disabled = false;
    }
    else if (act === 'msave') {
      el.disabled = true;
      try { await post('api/aps/save', formBody(id)); closeModal(); toast(t('apSaved')); AP.hash = ''; await load(); setTimeout(() => { AP.hash = ''; load(); }, 8000); }
      catch (er) { const r = $('am-res'); r.className = 'm-res bad'; r.textContent = er.message; el.disabled = false; }
    }
    else if (act === 'mdel') {
      if (!confirm(t('apDelConfirm', $('am-name').value))) return;
      await post('api/aps/delete', { id }); closeModal(); toast(t('apDeleted')); AP.hash = ''; await load();
    }
  } catch (er) { if (er.message !== '401') toast(er.message, true); }
}

function init() {
  const root = $('view-aps'); if (!root) return;
  root.addEventListener('click', onClick);
  const refresh = () => { const b = clientsBody(), body = $('ap-cbody'); if (body) body.innerHTML = b.html; const c = $('ap-count'); if (c) c.textContent = b.count; };
  root.addEventListener('input', e => { if (e.target.id === 'ap-q') { AP.q = e.target.value; refresh(); } });
  root.addEventListener('change', async e => {
    if (e.target.id === 'ap-only') { AP.only = e.target.value; refresh(); }
    else if (e.target.id === 'ap-poll') {
      try { await post('api/aps/poll', { seconds: Number(e.target.value) }); toast(t('apPollSet')); AP.hash = ''; load(); } catch (er) { toast(er.message, true); }
    }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
  try { if (localStorage.getItem('pi-ap-sub') === 'clients') AP.sub = 'clients'; } catch (e) {}
  if (typeof window.setLang === 'function') {
    const orig = window.setLang;
    window.setLang = function () { orig.apply(this, arguments); if (AP.data) render(); };
  }
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
