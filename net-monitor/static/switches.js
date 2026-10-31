// Switch Monitor — pestaña de Net Monitor para ver switches administrables: panel frontal, puertos, temperatura, errores,
// tasas, tabla MAC cruzada con los equipos conocidos, topología e historial. Los switches se agregan desde aquí (solo admin).
// EN: Switch Monitor — Net Monitor tab for managed switches: front panel, ports, temperature, errors, rates, MAC table matched
//     to known devices, topology and history. Switches are added from here (admin only).
// Usa t(), esc(), toast(), canAdmin() y LANG de app.js. Sin JavaScript en línea (CSP): eventos delegados con data-act.
// EN: Uses t(), esc(), toast(), canAdmin() and LANG from app.js. No inline JavaScript (CSP): delegated events with data-act.
(function () {
'use strict';
if (typeof LANG === 'undefined' || typeof t !== 'function') return;

Object.assign(LANG.en, {
  tabHosts: 'Devices', tabSwitches: 'Switch Monitor',
  swKpiOnline: 'Switches online', swKpiPorts: 'Ports up', swKpiTemp: 'Max temperature', swKpiErr: 'Ports with new errors', swKpiMacs: 'MACs learned',
  swUpdated: s => 'Updated ' + s + ' ago', swEvery: 'every', swNever: 'no data yet', swRefresh: 'Refresh', swAdd: '+ Add switch', swEdit: 'Edit',
  swEmptyAdmin: 'No switches yet. Add one to start monitoring ports, temperature and errors.', swEmptyRead: 'No switches have been added yet.',
  swLegUp: 'Up', swLegDown: 'Down', swLegWarn: 'New errors', swLegUplink: 'Link between switches', swLegOff: 'Disabled', swLegLoop: 'Loop',
  swTotal: 'Total rx / tx', swInfoTotal: 'Total received / sent',
  swSubStatus: 'Status', swSubHist: 'History', swSubMac: 'MAC table',
  swMacSearch: 'Search MAC, IP, name, port or VLAN…', swMacAll: 'All switches', swMacKnown: 'Only known devices', swMacCount: (n, m) => n + ' of ' + m + ' addresses',
  swMacEmpty: 'No MAC addresses yet: they appear after the first reading.', swMacNone: 'Nothing matches the search.', swColSw: 'Switch', swColMac: 'MAC', swColVlan: 'VLAN', swColIp: 'IP', swColName: 'Name', swMacUplink: 'link to another switch',
  swTopoReset: 'Reset layout', swTopoDrag: 'Drag the nodes to arrange the map; the layout is kept in this browser.',
  swHistNote: 'Cumulative data, not affected by restarts: LabTower adds up how much each counter advances between reads, so the totals do not drop when a switch reboots or its counters are cleared. They start from the value the switch already had when it was added, and the traffic of the few seconds around a restart is lost.',
  swHistSince: d => 'Counting since ' + d, swHistResets: n => n ? n + ' counter reset' + (n > 1 ? 's' : '') + ' detected' : 'no counter resets detected',
  swHistEmpty: 'No totals yet: they appear after the first reading.', swColRx: 'Received', swColTx: 'Sent', swColSum: 'Total', swColPkRx: 'Packets received', swColPkTx: 'Packets sent', swHistTotal: 'All ports',
  swHistPktOnly: 'This model does not report bytes, only packets.', swPort: 'Port', swState: 'State', swSpeed: 'Speed', swRxPps: 'Rx pkt/s', swTxPps: 'Tx pkt/s', swMbps: 'Mbit/s rx / tx', swErrors: 'Errors', swStp: 'STP', swConn: 'Connected to',
  swSideTitle: 'Switches', swAllSwitches: 'All switches', swNoneSide: 'No switches yet', swStUp: 'Up', swStDown: 'Down', swStOff: 'Disabled', swStLoop: 'Loop', swStUplink: 'Uplink', swStWarn: 'Errors',
  swShowAll: n => 'Show all ' + n + ' ports', swShowActive: 'Show only active ports',
  swOnline: 'Online', swOffline: 'Unreachable', swWaiting: 'Waiting for the first reading…', swTempHigh: 'High temperature', swTempCrit: 'Critical temperature',
  swNoTemp: 'This model does not report temperature, loop per port or bytes; only packets.', swNoLoop: 'No per-port loop flag on this model.',
  swTopo: 'Topology', swTopoHint: 'Worked out from the MAC tables: a port that has another switch\'s MAC behind it is a link between them.', swTopoNone: 'No links between switches detected yet.',
  swTempChart: 'Temperature', swTraffic: 'Traffic', swPackets: 'Packets/s', swErrChart: 'Errors (counter)', swNoData: 'No data in this range yet.',
  swPortTitle: (n, p) => n + ' · Port ' + p, swLabel: 'Label', swLabelPh: 'e.g. NAS, uplink to the office', swUplinkChk: 'Link to another switch (do not alert on loop)', swSavePort: 'Save', swClose: 'Close',
  swInfoLink: 'Link', swInfoCfg: 'Configured', swInfoFlow: 'Flow control', swInfoDisc: 'Discards rx / tx', swInfoMacs: 'MACs seen', swInfoErr1h: 'New errors (1 h)', swInfoCrc: 'CRC / FCS errors', swInfoAlign: 'Alignment errors', swInfoFlaps: 'Link changes (1 h)', swWatchChk: 'Alert when this port goes down or up',
  swMdlAdd: 'Add switch', swMdlEdit: 'Edit switch', swName: 'Name', swDriver: 'Type', swHost: 'IP or name', swUser: 'User', swPass: 'Password', swKeep: 'leave empty to keep the stored one',
  swCommunity: 'SNMP community (read-only)', swSnmpPort: 'SNMP port', swMacPag: 'Read the whole MAC table (HC; not tried on the real unit)', swEst: 'Estimated bytes per packet (0 = off)', swEstNote: 'Estimated: this model only reports packets, so bytes = packets × the average size set for this switch. Not exact.', swEstTip: 'estimated',
  swDrvZx: 'ZX310S (web interface)', swDrvHc: 'HC-SWTGW218AS (web interface)', swDrvSnmp: 'SNMP v2c (TP-Link and others)',
  swTest: 'Test', swTesting: 'Testing…', swSave: 'Save', swDelete: 'Delete', swCancel: 'Cancel', swDelConfirm: n => 'Delete "' + n + '" and its history?',
  swTestOk: r => 'OK — ' + (r.model || 'switch') + ', ' + r.ports + ' ports (' + r.ports_up + ' up)' + (r.temperature_c != null ? ', ' + r.temperature_c + ' °C' : '') + (r.has_bytes ? ', byte counters available' : r.bytes_est ? ', packet counters (bytes estimated at ' + r.bytes_est + ' B/pkt)' : ', packet counters only') + ' · ' + r.seconds + ' s',
  swSaved: 'Switch saved', swDeleted: 'Switch deleted', swPollSet: 'Interval updated', swRefreshing: 'Refreshing…',
  swLayout: 'Panel layout', swLayAuto: 'Automatic', swLayRow: 'One row (1-2-3…)', swLayAlt: 'Two rows (odd on top, even below)',
  swReadOnlyNote: 'Read-only: these tools only read from the switches; nothing here changes them.',
  swAlertDown: 'unreachable', swAlertTemp: 'temperature', swAlertLoop: n => 'loop on port ' + n, swAlertErr: (n, d) => 'port ' + n + ': ' + d + ' new errors',
  swSec: 's', swMin: 'min'
});
Object.assign(LANG.es, {
  tabHosts: 'Equipos', tabSwitches: 'Switch Monitor',
  swKpiOnline: 'Switches en línea', swKpiPorts: 'Puertos arriba', swKpiTemp: 'Temperatura máx.', swKpiErr: 'Puertos con errores nuevos', swKpiMacs: 'MACs aprendidas',
  swUpdated: s => 'Actualizado hace ' + s, swEvery: 'cada', swNever: 'sin datos aún', swRefresh: 'Actualizar', swAdd: '+ Agregar switch', swEdit: 'Editar',
  swEmptyAdmin: 'Aún no hay switches. Agrega uno para monitorear puertos, temperatura y errores.', swEmptyRead: 'Todavía no se ha agregado ningún switch.',
  swLegUp: 'Arriba', swLegDown: 'Abajo', swLegWarn: 'Errores nuevos', swLegUplink: 'Enlace entre switches', swLegOff: 'Deshabilitado', swLegLoop: 'Loop',
  swTotal: 'Total rx / tx', swInfoTotal: 'Total recibido / enviado',
  swSubStatus: 'Estado', swSubHist: 'Historial', swSubMac: 'Tabla MAC',
  swMacSearch: 'Buscar MAC, IP, nombre, puerto o VLAN…', swMacAll: 'Todos los switches', swMacKnown: 'Solo equipos conocidos', swMacCount: (n, m) => n + ' de ' + m + ' direcciones',
  swMacEmpty: 'Aún no hay direcciones MAC: aparecen tras la primera lectura.', swMacNone: 'Nada coincide con la búsqueda.', swColSw: 'Switch', swColMac: 'MAC', swColVlan: 'VLAN', swColIp: 'IP', swColName: 'Nombre', swMacUplink: 'enlace a otro switch',
  swTopoReset: 'Restablecer posiciones', swTopoDrag: 'Arrastra los nodos para ordenar el mapa; la disposición se guarda en este navegador.',
  swHistNote: 'Datos acumulados, sin tomar en cuenta los reinicios: LabTower suma cuánto avanza cada contador entre lecturas, así que el total no baja cuando el switch se reinicia o se borran sus contadores. Parte del valor que el switch ya traía al agregarlo, y se pierde el tráfico de los pocos segundos alrededor de un reinicio.',
  swHistSince: d => 'Contando desde ' + d, swHistResets: n => n ? n + ' reinicio' + (n > 1 ? 's' : '') + ' de contadores detectado' + (n > 1 ? 's' : '') : 'sin reinicios de contadores detectados',
  swHistEmpty: 'Aún no hay totales: aparecen tras la primera lectura.', swColRx: 'Recibido', swColTx: 'Enviado', swColSum: 'Total', swColPkRx: 'Paquetes recibidos', swColPkTx: 'Paquetes enviados', swHistTotal: 'Todos los puertos',
  swHistPktOnly: 'Este modelo no informa bytes, solo paquetes.', swPort: 'Puerto', swState: 'Estado', swSpeed: 'Velocidad', swRxPps: 'Rx pkt/s', swTxPps: 'Tx pkt/s', swMbps: 'Mbit/s rx / tx', swErrors: 'Errores', swStp: 'STP', swConn: 'Conectado a',
  swSideTitle: 'Switches', swAllSwitches: 'Todos los switches', swNoneSide: 'Aún no hay switches', swStUp: 'Arriba', swStDown: 'Abajo', swStOff: 'Deshabilitado', swStLoop: 'Loop', swStUplink: 'Uplink', swStWarn: 'Errores',
  swShowAll: n => 'Mostrar los ' + n + ' puertos', swShowActive: 'Mostrar solo puertos activos',
  swOnline: 'En línea', swOffline: 'Sin conexión', swWaiting: 'Esperando la primera lectura…', swTempHigh: 'Temperatura alta', swTempCrit: 'Temperatura crítica',
  swNoTemp: 'Este modelo no informa temperatura, loop por puerto ni bytes; solo paquetes.', swNoLoop: 'Este modelo no informa loop por puerto.',
  swTopo: 'Topología', swTopoHint: 'Se deduce de las tablas MAC: un puerto que tiene detrás la MAC de otro switch es un enlace entre ambos.', swTopoNone: 'Aún no se detectan enlaces entre switches.',
  swTempChart: 'Temperatura', swTraffic: 'Tráfico', swPackets: 'Paquetes/s', swErrChart: 'Errores (contador)', swNoData: 'Aún no hay datos en este rango.',
  swPortTitle: (n, p) => n + ' · Puerto ' + p, swLabel: 'Etiqueta', swLabelPh: 'p. ej. NAS, enlace a la oficina', swUplinkChk: 'Enlace a otro switch (no alertar por loop)', swSavePort: 'Guardar', swClose: 'Cerrar',
  swInfoLink: 'Enlace', swInfoCfg: 'Configurado', swInfoFlow: 'Control de flujo', swInfoDisc: 'Descartes rx / tx', swInfoMacs: 'MACs vistas', swInfoErr1h: 'Errores nuevos (1 h)', swInfoCrc: 'Errores CRC / FCS', swInfoAlign: 'Errores de alineación', swInfoFlaps: 'Cambios de enlace (1 h)', swWatchChk: 'Avisar si este puerto se cae o vuelve',
  swMdlAdd: 'Agregar switch', swMdlEdit: 'Editar switch', swName: 'Nombre', swDriver: 'Tipo', swHost: 'IP o nombre', swUser: 'Usuario', swPass: 'Contraseña', swKeep: 'vacío = conservar la guardada',
  swCommunity: 'Community SNMP (solo lectura)', swSnmpPort: 'Puerto SNMP', swMacPag: 'Leer toda la tabla MAC (HC; no probado en el equipo real)', swEst: 'Bytes estimados por paquete (0 = desactivado)', swEstNote: 'Estimado: este modelo solo informa paquetes, así que los bytes = paquetes × el tamaño medio configurado en este switch. No es exacto.', swEstTip: 'estimado',
  swDrvZx: 'ZX310S (interfaz web)', swDrvHc: 'HC-SWTGW218AS (interfaz web)', swDrvSnmp: 'SNMP v2c (TP-Link y otros)',
  swTest: 'Probar', swTesting: 'Probando…', swSave: 'Guardar', swDelete: 'Eliminar', swCancel: 'Cancelar', swDelConfirm: n => '¿Eliminar «' + n + '» y su historial?',
  swTestOk: r => 'OK — ' + (r.model || 'switch') + ', ' + r.ports + ' puertos (' + r.ports_up + ' arriba)' + (r.temperature_c != null ? ', ' + r.temperature_c + ' °C' : '') + (r.has_bytes ? ', con contadores de bytes' : r.bytes_est ? ', contadores de paquetes (bytes estimados a ' + r.bytes_est + ' B/paq.)' : ', solo contadores de paquetes') + ' · ' + r.seconds + ' s',
  swSaved: 'Switch guardado', swDeleted: 'Switch eliminado', swPollSet: 'Intervalo actualizado', swRefreshing: 'Actualizando…',
  swLayout: 'Distribución del panel', swLayAuto: 'Automática', swLayRow: 'Una fila (1-2-3…)', swLayAlt: 'Dos filas (impares arriba, pares abajo)',
  swReadOnlyNote: 'Solo lectura: esta herramienta solo lee de los switches; nada aquí los modifica.',
  swAlertDown: 'sin conexión', swAlertTemp: 'temperatura', swAlertLoop: n => 'loop en el puerto ' + n, swAlertErr: (n, d) => 'puerto ' + n + ': ' + d + ' errores nuevos',
  swSec: 's', swMin: 'min'
});

const $ = id => document.getElementById(id);
const SW = { sub: 'status', tot: null, macs: null, q: '', msw: '', known: false, pos: {}, drag: null, view: 'hosts', data: null, hash: '', sel: null, range: '1d', hist: {}, charts: {}, showAll: {}, timer: null, busy: false, cfg: null, only: '' };
const POLLS = [30, 60, 120, 300, 600];

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (r.status === 401) { location.reload(); throw new Error('401'); }
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || ('HTTP ' + r.status));
  return d;
}
const post = (p, b) => api(p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b || {}) });

// ── Formatos / formats ───────────────────────────────────────────────────────────────────
const spd = m => !m ? '—' : m >= 1000 ? (m / 1000 % 1 ? (m / 1000).toFixed(1) : m / 1000) + 'G' : m + 'M';
// Clase de color según la velocidad del enlace: 10G · 2.5G · 1G · 100M · 10M.
// EN: Colour class by link speed: 10G · 2.5G · 1G · 100M · 10M.
const SPD_CLS = m => !m ? '' : m >= 10000 ? 's10g' : m >= 2500 ? 's25g' : m >= 1000 ? 's1g' : m >= 100 ? 's100m' : 's10m';
const spdLong = m => !m ? '—' : m >= 1000 ? (m / 1000) + ' Gb/s' : m + ' Mb/s';
function pps(v) { return v == null ? '—' : v >= 10000 ? (v / 1000).toFixed(0) + 'k' : v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v >= 10 ? v.toFixed(0) : v.toFixed(1); }
function mbps(v) { return v == null ? '—' : v >= 1e9 ? (v / 1e9).toFixed(2) + ' G' : v >= 1e6 ? (v / 1e6).toFixed(v >= 1e7 ? 0 : 1) : v >= 1e3 ? (v / 1e6).toFixed(2) : '0'; }
function bytesFmt(v) {
  if (v == null) return '—';
  const u = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']; let i = 0;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return (i < 2 ? Math.round(v) : v.toFixed(v >= 100 ? 0 : v >= 10 ? 1 : 2)) + ' ' + u[i];
}
const num = v => v == null ? '—' : Number(v).toLocaleString(_lang === 'es' ? 'es-CL' : 'en-GB');
const dateOf = ts => new Date(ts * 1000).toLocaleDateString(_lang === 'es' ? 'es-CL' : 'en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' });
function ago(sec) { return sec == null ? '—' : sec < 60 ? Math.round(sec) + ' ' + t('swSec') : Math.floor(sec / 60) + ' ' + t('swMin'); }
function clock(ts, secs) { const d = new Date(ts * 1000); return typeof PCT !== 'undefined' ? PCT.time(d, secs) : d.toLocaleTimeString(); }
function dayTime(ts) {
  const d = new Date(ts * 1000), day = d.toLocaleDateString(_lang === 'es' ? 'es-CL' : 'en-GB', { day: '2-digit', month: '2-digit' });
  return SW.range === '1h' || SW.range === '1d' ? clock(ts) : day + ' ' + clock(ts);
}
const nameOf = n => (n.name || n.ip || n.mac || '').toString();

// ── Vistas / views ───────────────────────────────────────────────────────────────────────
function setView(v) {
  SW.view = v === 'switches' ? 'switches' : 'hosts';
  $('view-hosts').hidden = SW.view !== 'hosts';
  $('view-switches').hidden = SW.view !== 'switches';
  document.body.classList.toggle('view-sw', SW.view === 'switches');
  const sd = $('sw-side'); if (sd) sd.hidden = SW.view !== 'switches';
  document.querySelectorAll('.view-tab').forEach(b => b.classList.toggle('active', b.dataset.view === SW.view));
  try { localStorage.setItem('pi-net-view', SW.view); } catch (e) {}
  try { history.replaceState(null, '', SW.view === 'switches' ? '#switches' : location.pathname + location.search); } catch (e) {}
  clearInterval(SW.timer);
  if (SW.view === 'switches') { load(); SW.timer = setInterval(() => { if (!document.hidden) load(); }, 10000); }
}

async function load() {
  if (SW.busy) return;
  SW.busy = true;
  try {
    const d = await api('api/switches');
    if (SW.sub === 'hist') { try { SW.tot = await api('api/switches/totals'); } catch (e) { if (e.message === '401') throw e; } }
    if (SW.sub === 'mac') { try { SW.macs = await api('api/switches/macs'); } catch (e) { if (e.message === '401') throw e; } }
    const h = (SW.sub === 'hist' ? JSON.stringify(SW.tot) : SW.sub === 'mac' ? JSON.stringify(SW.macs) : '') + SW.sub + JSON.stringify(d.switches) + JSON.stringify(d.edges) + d.poll_seconds + (typeof ME !== 'undefined' && ME && ME.permissions ? ME.permissions.net : '');
    const changed = h !== SW.hash;
    SW.data = d; SW.hash = h;
    if (changed) render();
    else updateStamp();
    loadHistory();
  } catch (e) { if (e.message !== '401') console.error(e); }
  finally { SW.busy = false; }
}

// ── Historial y gráficos / history and charts ────────────────────────────────────────────
function histKey(sid, port) { return sid + '|' + (port == null ? '' : port) + '|' + SW.range; }
async function loadHistory(force) {
  if (!SW.data) return;
  const want = [];
  SW.data.switches.forEach(s => {
    if (s.system && s.system.temperature_c != null) want.push([s.id, null]);
    if (SW.sel && SW.sel.sid === s.id) want.push([s.id, SW.sel.port]);
  });
  await Promise.all(want.map(async ([sid, port]) => {
    const k = histKey(sid, port), c = SW.hist[k], ttl = SW.range === '1h' ? 30000 : 120000;
    if (!force && c && Date.now() - c.ts < ttl) return;
    try {
      const d = await api('api/switches/' + encodeURIComponent(sid) + '/history?range=' + SW.range + (port != null ? '&port=' + port : ''));
      SW.hist[k] = { ts: Date.now(), d };
    } catch (e) { return; }
  }));
  drawCharts();
}

// Gráfico de líneas en SVG con cuadrícula, cortes donde faltan datos y cursor con valores.
// EN: SVG line chart with grid, breaks where data is missing and a hover cursor with values.
function lineChart(id, rows, series, o) {
  const W = 900, H = o.h || 130, L = 46, R = 8, T = 8, B = 22;
  rows = rows.filter(r => series.some(s => r[s.k] != null));
  if (rows.length < 2) return '<div class="sw-nodata">' + esc(t('swNoData')) + '</div>';
  const x0 = rows[0].ts, x1 = rows[rows.length - 1].ts, xs = ts => L + (ts - x0) / Math.max(1, x1 - x0) * (W - L - R);
  let lo = Infinity, hi = -Infinity;
  rows.forEach(r => series.forEach(s => { const v = r[s.k]; if (v != null) { lo = Math.min(lo, v * (s.mul || 1)); hi = Math.max(hi, v * (s.mul || 1)); } }));
  if (o.zero) lo = 0;
  if (o.line != null) { hi = Math.max(hi, o.line * 1.05); lo = Math.min(lo, o.line * 0.9); }
  if (hi === lo) { hi += 1; lo = Math.max(0, lo - 1); }
  const pad = (hi - lo) * 0.08; hi += pad; if (!o.zero) lo = Math.max(lo - pad, o.min != null ? o.min : -Infinity); else lo = 0;
  const ys = v => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const gaps = rows.map((r, i) => i ? r.ts - rows[i - 1].ts : 0).filter(Boolean).sort((a, b) => a - b), med = gaps.length ? gaps[gaps.length >> 1] : 60;
  let g = '';
  for (let i = 0; i <= 3; i++) {
    const v = lo + (hi - lo) * i / 3, y = ys(v);
    g += `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" class="sw-grid"/><text x="${L - 5}" y="${y + 3}" text-anchor="end" class="sw-ax">${esc(o.fmtAxis(v))}</text>`;
  }
  for (let i = 0; i <= 4; i++) { const ts = x0 + (x1 - x0) * i / 4; g += `<text x="${xs(ts)}" y="${H - 6}" text-anchor="${i === 0 ? 'start' : i === 4 ? 'end' : 'middle'}" class="sw-ax">${esc(dayTime(ts))}</text>`; }
  if (o.line != null) g += `<line x1="${L}" x2="${W - R}" y1="${ys(o.line)}" y2="${ys(o.line)}" class="sw-warnline"/>`;
  series.forEach(s => {
    let d = '', pen = false;
    rows.forEach((r, i) => {
      const v = r[s.k];
      if (v == null) { pen = false; return; }
      if (i && r.ts - rows[i - 1].ts > med * 4) pen = false;
      d += (pen ? 'L' : 'M') + xs(r.ts).toFixed(1) + ' ' + ys(v * (s.mul || 1)).toFixed(1) + ' ';
      pen = true;
    });
    g += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="1.6" stroke-linejoin="round"/>`;
  });
  SW.charts[id] = { rows, series, x0, x1, W, L, R, fmt: o.fmtVal };
  const leg = series.length > 1 || o.legend ? '<div class="sw-legend">' + series.map(s => `<span><i style="background:${s.color}"></i>${esc(s.label)}</span>`).join('') + '</div>' : '';
  return `<div class="sw-chartbox" data-chart="${id}">${leg}<svg viewBox="0 0 ${W} ${H}" class="sw-svg">${g}<line class="sw-cursor" x1="0" x2="0" y1="${T}" y2="${H - B}" style="display:none"/></svg></div>`;
}

function chartFor(el) {
  const key = el.dataset.key, kind = el.dataset.kind, c = SW.hist[key];
  if (!c) { el.innerHTML = '<div class="sw-nodata">…</div>'; return; }
  const id = key + '|' + kind, d = c.d, sw = (SW.data.switches.find(s => s.id === key.split('|')[0]) || {});
  if (kind === 'temp') el.innerHTML = lineChart(id, d.sys, [{ k: 'temp', color: '#ef4444', label: t('swTempChart'), mul: 1 }], { h: 110, fmtAxis: v => Math.round(v) + '°', fmtVal: v => v.toFixed(1) + ' °C', line: SW.data.temp_warn, min: 0 });
  else if (kind === 'traffic') {
    if (sw.has_bytes) el.innerHTML = lineChart(id, d.port, [{ k: 'rxb', color: '#22c55e', label: 'rx', mul: 1e-6 }, { k: 'txb', color: '#4361ee', label: 'tx', mul: 1e-6 }], { h: 130, zero: true, fmtAxis: v => v.toFixed(v < 10 ? 1 : 0) + ' M', fmtVal: v => v.toFixed(2) + ' Mb/s' });
    else el.innerHTML = lineChart(id, d.port, [{ k: 'rxp', color: '#22c55e', label: 'rx', mul: 1 }, { k: 'txp', color: '#4361ee', label: 'tx', mul: 1 }], { h: 130, zero: true, fmtAxis: v => pps(v), fmtVal: v => v.toFixed(1) + ' pkt/s' });
  } else if (kind === 'errs') el.innerHTML = lineChart(id, d.port, [{ k: 'err', color: '#f59e0b', label: t('swErrChart') }], { h: 90, legend: true, fmtAxis: v => Math.round(v), fmtVal: v => Math.round(v) + '' });
}
function drawCharts() { document.querySelectorAll('#view-switches .sw-chart').forEach(chartFor); }

// Cursor con valores al pasar el mouse. / Hover cursor with values.
function onMove(e) {
  const box = e.target.closest && e.target.closest('.sw-chartbox');
  const tip = $('sw-tip');
  if (!box) { if (tip) tip.style.display = 'none'; return; }
  const m = SW.charts[box.dataset.chart], svg = box.querySelector('svg'), cur = box.querySelector('.sw-cursor');
  if (!m || !svg) return;
  const r = svg.getBoundingClientRect(), x = (e.clientX - r.left) / r.width * m.W;
  const ts = m.x0 + (x - m.L) / Math.max(1, m.W - m.L - m.R) * (m.x1 - m.x0);
  let best = null;
  m.rows.forEach(p => { if (best === null || Math.abs(p.ts - ts) < Math.abs(best.ts - ts)) best = p; });
  if (!best) return;
  const bx = m.L + (best.ts - m.x0) / Math.max(1, m.x1 - m.x0) * (m.W - m.L - m.R);
  cur.setAttribute('x1', bx); cur.setAttribute('x2', bx); cur.style.display = '';
  tip.innerHTML = '<b>' + esc(dayTime(best.ts)) + '</b>' + m.series.filter(s => best[s.k] != null).map(s => `<div><i style="background:${s.color}"></i>${esc(s.label)}: ${esc(m.fmt(best[s.k] * (s.mul || 1)))}</div>`).join('');
  tip.style.display = 'block';
  tip.style.left = Math.min(window.innerWidth - tip.offsetWidth - 8, e.clientX + 14) + 'px';
  tip.style.top = (e.clientY + 14) + 'px';
}

// ── Dibujo de la pestaña / drawing the tab ──────────────────────────────────────────────
function updateStamp() {
  const el = $('sw-stamp'); if (!el || !SW.data) return;
  const ages = SW.data.switches.map(s => s.updated ? SW.data.now - s.updated : null).filter(v => v != null);
  el.textContent = (ages.length ? t('swUpdated', ago(Math.max(0, Math.min(...ages)))) : t('swNever'));
}

function tile(s, p) {
  let sub = '';
  if (p.flag === 'warn') sub = p.crc_1h ? p.crc_1h + ' CRC' : p.err_1h + ' err';
  else if (p.link_to) sub = '↔ ' + p.link_to;
  else if (p.label) sub = p.label;
  else if (p.neighbors && p.neighbors[0]) sub = p.neighbors[0].name || p.neighbors[0].ip || '';
  else if (p.link_up && (p.rx_bps != null || p.rx_pps != null)) sub = p.rx_bps != null ? mbps((p.rx_bps || 0) + (p.tx_bps || 0)) + ' Mb/s' : pps((p.rx_pps || 0) + (p.tx_pps || 0)) + ' pkt/s';
  const num = s.driver === 'zx' && p.port > 8 ? p.port + ' SFP+' : p.port;
  const tip = [t('swPortTitle', s.name, p.port), p.link_up ? spdLong(p.speed_mbps) : t('swStDown'), p.label, p.link_to ? '↔ ' + p.link_to : '',
    p.rx_pps != null ? 'rx ' + pps(p.rx_pps) + ' / tx ' + pps(p.tx_pps) + ' pkt/s' : '', (p.rx_err || p.tx_err) ? t('swErrors') + ': ' + (p.rx_err || 0) + ' / ' + (p.tx_err || 0) : ''].filter(Boolean).join(' · ');
  const on = SW.sel && SW.sel.sid === s.id && SW.sel.port === p.port;
  return `<button type="button" class="sw-port sw-p-${String(p.flag).replace(/[^a-z0-9_-]/g, '')}${on ? ' sel' : ''}" data-act="port" data-id="${esc(s.id)}" data-port="${p.port}" title="${esc(tip)}"><span class="n">${esc(num)}</span><span class="s ${p.link_up ? SPD_CLS(p.speed_mbps) : ''}">${p.link_up ? esc(spd(p.speed_mbps)) : '—'}</span><span class="x">${esc(sub)}</span></button>`;
}

function stPill(p) {
  const m = { up: ['green', 'swStUp'], uplink: ['teal', 'swStUplink'], down: ['', 'swStDown'], off: ['red', 'swStOff'], loop: ['amber', 'swStLoop'], warn: ['amber', 'swStUp'] }[p.flag] || ['', 'swStDown'];
  return `<span class="sw-pill ${m[0]}">${esc(t(m[1]))}</span>`;
}

function connCell(p) {
  const bits = [];
  if (p.label) bits.push('<b>' + esc(p.label) + '</b>');
  if (p.link_to) bits.push('↔ <b>' + esc(p.link_to) + '</b> <span class="dim">(' + esc(t('swStUplink').toLowerCase()) + ')</span>');
  const nb = (p.neighbors || []).filter(n => !p.link_to || n.name || n.ip);
  nb.slice(0, 2).forEach(n => bits.push(esc(nameOf(n)) + (n.ip && n.name ? ' <span class="dim">' + esc(n.ip) + '</span>' : '')));
  if (p.mac_count > Math.min(2, nb.length) && !p.link_to) bits.push('<span class="dim">+' + (p.mac_count - Math.min(2, nb.length)) + ' MAC</span>');
  else if (p.link_to && p.mac_count) bits.push('<span class="dim">' + p.mac_count + ' MAC</span>');
  return bits.join(' · ') || '<span class="dim">—</span>';
}

function errCell(p) {
  if (!p.rx_err && !p.tx_err) return '<span class="dim">0</span>';
  const txt = (p.rx_err || 0) + ' Rx · ' + (p.tx_err || 0) + ' Tx';
  return p.err_1h > 0 ? '<b class="amber">' + txt + '</b> <span class="amber">(+' + p.err_1h + ' / 1 h)</span>' : txt;
}

function portRow(s, p) {
  const on = SW.sel && SW.sel.sid === s.id && SW.sel.port === p.port;
  return `<tr class="sw-row${on ? ' sel' : ''}" data-act="port" data-id="${esc(s.id)}" data-port="${p.port}"><td>${esc(p.port)}</td><td>${stPill(p)}</td><td>${p.link_up ? `<span class="spd-pill ${SPD_CLS(p.speed_mbps)}">${esc(spdLong(p.speed_mbps))}</span>` : '<span class="dim">—</span>'}</td>` +
    `<td>${pps(p.rx_pps)}</td><td>${pps(p.tx_pps)}</td>` + (s.has_bytes ? `<td>${p.rx_bps != null ? (p.bytes_est ? '≈ ' : '') + mbps(p.rx_bps) + ' / ' + mbps(p.tx_bps) : '—'}</td><td>${p.rx_bytes != null ? esc((p.bytes_est ? '≈ ' : '') + bytesFmt(p.rx_bytes) + ' / ' + bytesFmt(p.tx_bytes)) : '—'}</td>` : '') +
    `<td>${errCell(p)}</td><td>${esc(p.stp_state || '—')}</td><td class="sw-conn">${connCell(p)}</td></tr>`;
}

function portDetail(s, p) {
  const admin = canAdmin();
  const info = [[t('swInfoLink'), p.link_up ? spdLong(p.speed_mbps) : t('swStDown')], [t('swInfoCfg'), p.speed_cfg || '—'], [t('swInfoFlow'), p.flow_ctrl || '—'], [t('swStp'), p.stp_state || '—'],
    [t('swErrors'), (p.rx_err || 0) + ' rx / ' + (p.tx_err || 0) + ' tx'], [t('swInfoErr1h'), p.err_1h], ...(p.crc != null ? [[t('swInfoCrc'), p.crc + (p.crc_1h ? ' (+' + p.crc_1h + ' / 1 h)' : '')], [t('swInfoAlign'), p.align != null ? p.align : '—']] : []), [t('swInfoFlaps'), p.flaps_1h || 0], ...(p.rx_bytes != null ? [[t('swInfoTotal'), (p.bytes_est ? '≈ ' : '') + bytesFmt(p.rx_bytes) + ' / ' + bytesFmt(p.tx_bytes)]] : []), [t('swInfoDisc'), p.rx_discards != null ? p.rx_discards + ' / ' + p.tx_discards : '—'], [t('swInfoMacs'), p.mac_count]];
  const macs = (p.neighbors || []).map(n => `<code>${esc(n.mac)}</code> ${n.name || n.ip ? esc(nameOf(n)) + (n.ip ? ' <span class="dim">' + esc(n.ip) + '</span>' : '') : '<span class="dim">—</span>'}${n.vlan != null ? ' <span class="dim">VLAN ' + esc(n.vlan) + '</span>' : ''}`).join('<br>');
  const ctl = admin ? `<div class="sw-portform"><label>${esc(t('swLabel'))}<input id="sw-lbl" maxlength="32" value="${esc(p.label || '')}" placeholder="${esc(t('swLabelPh'))}"></label>` +
    `<label class="chk"><input type="checkbox" id="sw-upl"${p.uplink_manual ? ' checked' : ''}> ${esc(t('swUplinkChk'))}</label><label class="chk"><input type="checkbox" id="sw-watch"${p.watch ? ' checked' : ''}> ${esc(t('swWatchChk'))}</label><button type="button" class="sw-btn teal" data-act="saveport" data-id="${esc(s.id)}" data-port="${p.port}">${esc(t('swSavePort'))}</button></div>` : '';
  const ranges = ['1h', '1d', '1w', '1mo', 'all'].map(r => `<button type="button" class="sw-chip${SW.range === r ? ' active' : ''}" data-act="range" data-range="${r}">${r === 'all' ? (_lang === 'es' ? 'Todo' : 'All') : r}</button>`).join('');
  const k = histKey(s.id, p.port);
  return `<div class="sw-detail"><div class="sw-dhead"><b>${esc(t('swPortTitle', s.name, p.port))}</b>${p.label ? ' <span class="dim">' + esc(p.label) + '</span>' : ''}<span class="grow"></span>${ranges}<button type="button" class="sw-btn" data-act="closeport">${esc(t('swClose'))}</button></div>` +
    `<div class="sw-info">${info.map(([a, b]) => `<div><span>${esc(a)}</span><b>${esc(b)}</b></div>`).join('')}</div>${macs ? '<div class="sw-macs">' + macs + '</div>' : ''}${ctl}` +
    `<div class="sw-charttitle">${esc(s.has_bytes ? t('swTraffic') + (s.bytes_est ? ' (≈ ' + t('swEstTip') + ')' : '') : t('swPackets'))}</div><div class="sw-chart" data-key="${esc(k)}" data-kind="traffic"></div>` +
    `<div class="sw-charttitle">${esc(t('swErrChart'))}</div><div class="sw-chart" data-key="${esc(k)}" data-kind="errs"></div></div>`;
}

function card(s) {
  const admin = canAdmin(), sy = s.system || {};
  const tl = s.temp_level, tPill = sy.temperature_c != null ? `<span class="sw-pill ${tl === 'crit' ? 'red' : tl === 'warn' ? 'amber' : 'green'}">${Math.round(sy.temperature_c)} °C${tl === 'warn' ? ' · ' + esc(t('swTempHigh')) : tl === 'crit' ? ' · ' + esc(t('swTempCrit')) : ''}</span>` : '';
  const state = !s.updated ? `<span class="sw-pill">${esc(t('swWaiting'))}</span>` : s.online ? `<span class="sw-pill green">${esc(t('swOnline'))}</span>` : `<span class="sw-pill red">${esc(t('swOffline'))}</span>`;
  const sub = [sy.model, s.host, sy.fw ? 'fw ' + sy.fw : ''].filter(Boolean).join(' · ');
  let grid = '', prev = 0;
  s.ports.forEach(p => { if (s.layout !== 'alt' && s.driver === 'zx' && p.port > 8 && prev <= 8) grid += '<span class="sw-gap"></span>'; prev = p.port; grid += tile(s, p); });
  const all = SW.showAll[s.id], hasMore = s.ports.some(p => p.flag === 'down');
  const rows = s.ports.filter(p => all || p.flag !== 'down' || p.label);
  const selP = SW.sel && SW.sel.sid === s.id ? s.ports.find(p => p.port === SW.sel.port) : null;
  const heads = ['swPort', 'swState', 'swSpeed', 'swRxPps', 'swTxPps'].concat(s.has_bytes ? ['swMbps', 'swTotal'] : [], ['swErrors', 'swStp', 'swConn']);
  const errs = (s.error && !s.online ? `<div class="sw-err">${esc(s.error)}</div>` : '') + (s.bytes_est ? `<div class="sw-note">${esc(t('swEstNote'))}</div>` : '');
  const hasT = sy.temperature_c != null;
  const alt = s.layout === 'alt';
  return `<div class="card sw-card"><div class="sw-head"><b class="sw-name">${esc(s.name)}</b><span class="dim mono">${esc(sub)}</span>${state}${tPill}<span class="grow"></span>` +
    `<span class="dim mono sw-scr">${esc(s.driver)}${s.scrape != null ? ' · ' + s.scrape + ' s' : ''}</span>${admin ? `<button type="button" class="sw-btn" data-act="edit" data-id="${esc(s.id)}">${esc(t('swEdit'))}</button>` : ''}</div>${errs}` +
    (s.ports.length ? `<div class="sw-grid-ports${alt ? ' alt' : ''}">${grid}</div><div class="sw-leg"><span class="up">${esc(t('swLegUp'))}</span><span class="down">${esc(t('swLegDown'))}</span><span class="warn">${esc(t('swLegWarn'))}</span><span class="uplink">${esc(t('swLegUplink'))}</span><span class="off">${esc(t('swLegOff'))}</span>${s.driver !== 'hc' ? `<span class="loop">${esc(t('swLegLoop'))}</span>` : ''}</div><div class="sw-leg sw-leg-spd"><span class="s10g">10 Gb/s</span><span class="s25g">2.5 Gb/s</span><span class="s1g">1 Gb/s</span><span class="s100m">100 Mb/s</span><span class="s10m">10 Mb/s</span></div>` +
      `<div class="sw-tablewrap"><table class="sw-table"><thead><tr>${heads.map(h => `<th>${esc(t(h))}</th>`).join('')}</tr></thead><tbody>${rows.map(p => portRow(s, p)).join('')}</tbody></table></div>` +
      (hasMore ? `<button type="button" class="sw-link" data-act="showall" data-id="${esc(s.id)}">${esc(all ? t('swShowActive') : t('swShowAll', s.ports.length))}</button>` : '') : '') +
    (selP ? portDetail(s, selP) : '') +
    (hasT ? `<div class="sw-charttitle">${esc(t('swTempChart'))}</div><div class="sw-chart" data-key="${esc(histKey(s.id, null))}" data-kind="temp"></div>` : '') +
    (!hasT && s.ports.length ? `<div class="sw-note">${esc(t('swNoTemp'))}</div>` : '') + '</div>';
}

function topoPos(d) {
  const sw = d.switches, n = sw.length, pos = {};
  sw.forEach((s, i) => { pos[s.name] = SW.pos[s.name] || (n === 2 ? [i ? 395 : 125, 100] : i === 0 ? [260, 38] : [n === 3 ? (i === 1 ? 125 : 395) : 60 + (i - 1) * (400 / (n - 2)), 160]); });
  return pos;
}
function topoSvg(d) {
  const sw = d.switches, W = 520, H = 200, pos = topoPos(d);
  let g = '';
  d.edges.forEach(e => {
    const a = pos[e.a], b = pos[e.b]; if (!a || !b) return;
    g += `<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="var(--teal)" stroke-width="2"/><text x="${(a[0] + b[0]) / 2}" y="${(a[1] + b[1]) / 2 - 5}" text-anchor="middle" class="sw-ax">p${esc(e.a_port)} ↔ ${e.b_port != null ? 'p' + esc(e.b_port) : '?'}</text>`;
  });
  sw.forEach(s => {
    const p = pos[s.name], c = s.online ? 'var(--green)' : 'var(--red)', tp = s.system && s.system.temperature_c != null ? ' · ' + Math.round(s.system.temperature_c) + '°' : '';
    g += `<g class="sw-node-g" data-name="${esc(s.name)}"><rect x="${p[0] - 62}" y="${p[1] - 15}" width="124" height="30" rx="7" fill="var(--surface2)" stroke="${c}"/><text x="${p[0]}" y="${p[1] + 4}" text-anchor="middle" class="sw-node">${esc(s.name)}${esc(tp)}</text></g>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" class="sw-topo" data-w="${W}" data-h="${H}">${g}</svg>`;
}
function topology(d) {
  const sw = d.switches; if (sw.length < 2) return '';
  return `<div class="card sw-card"><div class="sw-head"><span class="sw-sechead">${esc(t('swTopo'))}</span><span class="grow"></span>${Object.keys(SW.pos).length ? `<button type="button" class="sw-link" data-act="toporeset">${esc(t('swTopoReset'))}</button>` : ''}</div>` +
    (d.edges.length ? `<div id="sw-topo-box">${topoSvg(d)}</div>` : `<div class="sw-nodata">${esc(t('swTopoNone'))}</div>`) +
    `<div class="sw-note">${esc(t('swTopoHint'))} ${esc(t('swTopoDrag'))}</div></div>`;
}

function macRows() {
  const all = SW.macs && SW.macs.macs || [], q = SW.q.trim().toLowerCase();
  const rows = all.filter(r => (!SW.msw || r.switch === SW.msw) && (!SW.known || r.ip || r.name) &&
    (!q || [r.mac, r.ip, r.name, r.label, r.switch, String(r.port), r.vlan == null ? '' : 'vlan' + r.vlan + ' ' + r.vlan].join(' ').toLowerCase().includes(q)));
  return { all, rows };
}
function macBody() {
  const { all, rows } = macRows();
  const tr = rows.map(r => `<tr><td>${esc(r.switch)}</td><td>${esc(r.port)}${r.label ? ' <span class="dim">' + esc(r.label) + '</span>' : ''}${r.uplink ? ' <span class="sw-pill teal" title="' + esc(t('swMacUplink')) + '">↔</span>' : ''}</td><td><code>${esc(r.mac)}</code></td><td>${r.vlan != null ? esc(r.vlan) : '—'}</td><td>${r.ip ? esc(r.ip) : '<span class="dim">—</span>'}</td><td class="sw-conn">${r.name ? esc(r.name) : '<span class="dim">—</span>'}</td></tr>`).join('');
  return { html: tr || `<tr><td colspan="6" class="sw-nodata">${esc(all.length ? t('swMacNone') : t('swMacEmpty'))}</td></tr>`, count: t('swMacCount', rows.length, all.length) };
}
function macHtml() {
  const names = [...new Set((SW.macs && SW.macs.macs || []).map(r => r.switch))].sort();
  const b = macBody();
  return `<div class="card sw-card"><div class="sw-macbar"><input id="sw-q" type="search" class="sw-search" placeholder="${esc(t('swMacSearch'))}" value="${esc(SW.q)}" autocomplete="off">` +
    `<select id="sw-msw" class="sw-sel"><option value="">${esc(t('swMacAll'))}</option>${names.map(n => `<option${SW.msw === n ? ' selected' : ''}>${esc(n)}</option>`).join('')}</select>` +
    `<label class="chk dim"><input type="checkbox" id="sw-mknown"${SW.known ? ' checked' : ''}> ${esc(t('swMacKnown'))}</label><span class="grow"></span><span class="dim mono" id="sw-maccount">${esc(b.count)}</span></div>` +
    `<div class="sw-tablewrap"><table class="sw-table"><thead><tr>${['swColSw', 'swPort', 'swColMac', 'swColVlan', 'swColIp', 'swColName'].map(h => `<th>${esc(t(h))}</th>`).join('')}</tr></thead><tbody id="sw-macbody">${b.html}</tbody></table></div></div>`;
}

function histHtml() {
  const T = SW.tot && SW.tot.switches || [];
  const note = `<div class="card sw-card sw-histnote"><div class="sw-note">${esc(t('swHistNote'))}</div></div>`;
  if (!T.length || T.every(s => !s.ports.length)) return note + `<div class="card sw-card"><div class="sw-nodata">${esc(t('swHistEmpty'))}</div></div>`;
  return note + T.filter(s => s.ports.length).map(s => {
    const sum = k => s.ports.reduce((a, p) => a + (p[k] || 0), 0);
    const heads = s.has_bytes ? ['swPort', 'swColRx', 'swColTx', 'swColSum', 'swColPkRx', 'swColPkTx'] : ['swPort', 'swColPkRx', 'swColPkTx'];
    const ap = s.bytes_est ? '≈ ' : '';
    const row = (lbl, p, bold) => `<tr${bold ? ' class="sw-sumrow"' : ''}><td>${lbl}</td>` + (s.has_bytes ?
      `<td>${esc(ap + bytesFmt(p.rx_bytes))}</td><td>${esc(ap + bytesFmt(p.tx_bytes))}</td><td>${esc(ap + bytesFmt((p.rx_bytes || 0) + (p.tx_bytes || 0)))}</td>` : '') +
      `<td>${num(p.rx_pkts)}</td><td>${num(p.tx_pkts)}</td></tr>`;
    const total = { rx_bytes: sum('rx_bytes'), tx_bytes: sum('tx_bytes'), rx_pkts: sum('rx_pkts'), tx_pkts: sum('tx_pkts') };
    const rows = s.ports.filter(p => (p.rx_bytes || 0) + (p.tx_bytes || 0) + (p.rx_pkts || 0) + (p.tx_pkts || 0) > 0);
    return `<div class="card sw-card"><div class="sw-head"><b class="sw-name">${esc(s.name)}</b><span class="grow"></span>` +
      `<span class="dim mono">${s.since ? esc(t('swHistSince', dateOf(s.since))) + ' · ' : ''}${esc(t('swHistResets', s.resets))}</span></div>` +
      (s.has_bytes ? (s.bytes_est ? `<div class="sw-note">${esc(t('swEstNote'))}</div>` : '') : `<div class="sw-note">${esc(t('swHistPktOnly'))}</div>`) +
      `<div class="sw-tablewrap"><table class="sw-table"><thead><tr>${heads.map(h => `<th>${esc(t(h))}</th>`).join('')}</tr></thead><tbody>` +
      rows.map(p => row(esc(p.port) + (p.label ? ' <span class="dim">' + esc(p.label) + '</span>' : ''), p)).join('') + row('<b>' + esc(t('swHistTotal')) + '</b>', total, true) + `</tbody></table></div></div>`;
  }).join('');
}

// Lista de switches en la barra lateral (como «Tipo de dispositivo»): clic para ver solo uno.
// EN: Switch list in the sidebar (like "Device type"): click to show only one.
function sbSwitches(S) {
  const box = $('sw-side-list'); if (!box) return;
  const lb = document.querySelector('#sw-side .sb-lbl'); if (lb) lb.textContent = t('swSideTitle');      // switches.js loads after app.js translated the page
  if (SW.only && !S.some(s => s.id === SW.only)) SW.only = '';
  const dot = s => !s.updated ? 'var(--text-dim)' : s.online ? 'var(--green)' : 'var(--red)';
  const row = (id, color, name, cnt) => `<div class="os-filter${SW.only === id ? ' active' : ''}" data-sw-only="${esc(id)}" role="button" tabindex="0"><span class="os-dot" style="background:${color}"></span><span class="os-filter-name">${esc(name)}</span><span class="os-filter-count">${esc(cnt)}</span></div>`;
  box.innerHTML = S.length ? row('', 'var(--teal)', t('swAllSwitches'), S.length) + S.map(s => row(s.id, dot(s), s.name, s.online ? s.ports_up + '/' + s.ports_total : '—')).join('') : '<div class="dim" style="padding:4px 10px;font-size:11.5px">' + esc(t('swNoneSide')) + '</div>';
}
function render() {
  const root = $('view-switches'); if (!root || !SW.data) return;
  const d = SW.data, admin = canAdmin(), S = d.switches;
  sbSwitches(S);
  const upSw = S.filter(s => s.online).length;
  const pUp = S.reduce((a, s) => a + s.ports_up, 0), pTot = S.reduce((a, s) => a + s.ports_total, 0);
  const temps = S.filter(s => s.system && s.system.temperature_c != null).sort((a, b) => b.system.temperature_c - a.system.temperature_c);
  const errPorts = S.reduce((a, s) => a + s.ports.filter(p => p.flag === 'warn').length, 0);
  const macs = S.reduce((a, s) => a + s.macs_total, 0);
  const tmax = temps[0], tcol = tmax ? (tmax.temp_level === 'crit' ? 'var(--red)' : tmax.temp_level === 'warn' ? 'var(--amber)' : '') : '';
  const kpi = (ico, val, lbl, col) => `<div class="stat-card"><div class="stat-ico ${ico}"><svg viewBox="0 0 24 24"><rect x="2" y="9" width="20" height="8" rx="2"/><line x1="6" y1="13" x2="6.01" y2="13"/><line x1="10" y1="13" x2="10.01" y2="13"/><line x1="14" y1="13" x2="14.01" y2="13"/></svg></div><div><div class="stat-val"${col ? ` style="color:${col}"` : ''}>${val}</div><div class="stat-lbl">${esc(lbl)}</div></div></div>`;
  const polls = POLLS.map(v => `<option value="${v}"${v === d.poll_seconds ? ' selected' : ''}>${v >= 60 ? v / 60 + ' ' + t('swMin') : v + ' ' + t('swSec')}</option>`).join('') + (POLLS.includes(d.poll_seconds) ? '' : `<option value="${d.poll_seconds}" selected>${d.poll_seconds} ${t('swSec')}</option>`);
  const bar = `<div class="sw-bar"><span class="dim mono" id="sw-stamp"></span><span class="dim mono">· ${esc(t('swEvery'))} ${admin ? `<select id="sw-poll" class="sw-sel">${polls}</select>` : polls.match(new RegExp('value="' + d.poll_seconds + '"[^>]*>([^<]*)'))[1]}</span><span class="grow"></span>` +
    `<button type="button" class="sw-btn" data-act="refresh">↻ ${esc(t('swRefresh'))}</button>${admin ? `<button type="button" class="sw-btn teal" data-act="add">${esc(t('swAdd'))}</button>` : ''}</div>`;
  const empty = S.length ? '' : `<div class="card sw-card"><div class="sw-nodata">${esc(admin ? t('swEmptyAdmin') : t('swEmptyRead'))}</div></div>`;
  const subbar = `<div class="sw-sub"><button type="button" class="sw-chip${SW.sub === 'status' ? ' active' : ''}" data-act="sub" data-sub="status">${esc(t('swSubStatus'))}</button><button type="button" class="sw-chip${SW.sub === 'hist' ? ' active' : ''}" data-act="sub" data-sub="hist">${esc(t('swSubHist'))}</button><button type="button" class="sw-chip${SW.sub === 'mac' ? ' active' : ''}" data-act="sub" data-sub="mac">${esc(t('swSubMac'))}</button></div>`;
  if (SW.sub === 'hist') { root.innerHTML = bar + subbar + histHtml(); updateStamp(); return; }
  if (SW.sub === 'mac') { root.innerHTML = bar + subbar + macHtml(); updateStamp(); return; }
  root.innerHTML = bar + subbar +
    (S.length ? `<div class="stats-row">${kpi('teal', upSw + '/' + S.length, t('swKpiOnline'))}${kpi('green', pUp + '<span class="dim"> / ' + pTot + '</span>', t('swKpiPorts'))}${kpi('orange', tmax ? Math.round(tmax.system.temperature_c) + ' °C' : '—', t('swKpiTemp') + (tmax ? ' (' + tmax.name + ')' : ''), tcol)}${kpi('red', errPorts, t('swKpiErr'), errPorts ? 'var(--amber)' : '')}${kpi('blue', macs, t('swKpiMacs'))}</div>` : '') +
    empty + S.filter(x => !SW.only || x.id === SW.only).map(card).join('') + topology(d) + (S.length ? `<div class="sw-note">${esc(t('swReadOnlyNote'))}</div>` : '');
  updateStamp();
  drawCharts();
}

// ── Formulario de alta / edición / add-edit form ─────────────────────────────────────────
function closeModal() { const m = $('sw-modal'); if (m) m.remove(); }
async function openModal(id) {
  let cur = null;
  if (id) { try { cur = (await api('api/switches/config')).switches.find(s => s.id === id); } catch (e) {} }
  closeModal();
  const c = cur || { driver: 'zx', name: '', host: '', user: 'admin', port: 161 };
  const m = document.createElement('div'); m.id = 'sw-modal'; m.className = 'sw-ov';
  m.innerHTML = `<div class="sw-dlg" role="dialog"><h3>${esc(t(cur ? 'swMdlEdit' : 'swMdlAdd'))}</h3>` +
    `<label>${esc(t('swName'))}<input id="m-name" maxlength="32" value="${esc(c.name)}"></label>` +
    `<label>${esc(t('swDriver'))}<select id="m-driver"><option value="zx">${esc(t('swDrvZx'))}</option><option value="hc">${esc(t('swDrvHc'))}</option><option value="snmp">${esc(t('swDrvSnmp'))}</option></select></label>` +
    `<label>${esc(t('swHost'))}<input id="m-host" value="${esc(c.host)}" placeholder="192.168.0.x"></label>` +
    `<div class="m-web"><label>${esc(t('swUser'))}<input id="m-user" maxlength="64" value="${esc(c.user || 'admin')}" autocomplete="off"></label>` +
    `<label>${esc(t('swPass'))}<input id="m-pass" type="password" autocomplete="new-password" placeholder="${cur && c.has_password ? esc(t('swKeep')) : ''}"></label>` +
    `<label class="chk m-hc"><input type="checkbox" id="m-pag"${c.mac_paginate ? ' checked' : ''}> ${esc(t('swMacPag'))}</label></div>` +
    `<label class="m-web m-est">${esc(t('swEst'))}<input id="m-est" type="number" min="0" max="9000" value="${esc(c.est_bytes != null ? c.est_bytes : 800)}"></label>` +
    `<div class="m-snmp"><label>${esc(t('swCommunity'))}<input id="m-comm" type="password" autocomplete="new-password" placeholder="${cur && c.has_community ? esc(t('swKeep')) : ''}"></label>` +
    `<label>${esc(t('swSnmpPort'))}<input id="m-sport" type="number" min="1" max="65535" value="${esc(c.port || 161)}"></label></div>` +
    `<label>${esc(t('swLayout'))}<select id="m-layout"><option value="auto">${esc(t('swLayAuto'))}</option><option value="row">${esc(t('swLayRow'))}</option><option value="alt">${esc(t('swLayAlt'))}</option></select></label>` +
    `<div id="m-res" class="m-res"></div><div class="m-btns">${cur ? `<button type="button" class="sw-btn red" data-act="mdel" data-id="${esc(c.id)}">${esc(t('swDelete'))}</button>` : ''}<span class="grow"></span>` +
    `<button type="button" class="sw-btn" data-act="mcancel">${esc(t('swCancel'))}</button><button type="button" class="sw-btn" data-act="mtest" data-id="${esc(c.id || '')}">${esc(t('swTest'))}</button><button type="button" class="sw-btn teal" data-act="msave" data-id="${esc(c.id || '')}">${esc(t('swSave'))}</button></div></div>`;
  document.body.appendChild(m);
  $('m-driver').value = c.driver; $('m-layout').value = c.layout || 'auto';
  const sync = () => { const v = $('m-driver').value; m.querySelector('.m-web').style.display = v === 'snmp' ? 'none' : ''; m.querySelector('.m-snmp').style.display = v === 'snmp' ? '' : 'none'; m.querySelector('.m-hc').style.display = v === 'hc' ? '' : 'none'; m.querySelector('.m-est').style.display = v === 'snmp' ? 'none' : ''; };
  $('m-driver').addEventListener('change', sync); sync();
  m.addEventListener('click', e => { if (e.target === m) closeModal(); });
  $('m-name').focus();
}
function formBody(id) {
  const b = { name: $('m-name').value.trim(), driver: $('m-driver').value, host: $('m-host').value.trim(), layout: $('m-layout').value };
  if (id) b.id = id;
  if (b.driver === 'snmp') { b.community = $('m-comm').value; b.port = Number($('m-sport').value) || 161; }
  else { b.user = $('m-user').value.trim() || 'admin'; b.password = $('m-pass').value; if (b.driver === 'hc') b.mac_paginate = $('m-pag').checked; b.est_bytes = Number($('m-est').value); }
  return b;
}

// ── Eventos / events ─────────────────────────────────────────────────────────────────────
async function onClick(e) {
  const el = e.target.closest && e.target.closest('[data-act]'); if (!el) return;
  const act = el.dataset.act, id = el.dataset.id;
  try {
    if (act === 'refresh') { toast(t('swRefreshing')); await post('api/switches/refresh', {}); setTimeout(load, 4000); }
    else if (act === 'add') openModal(null);
    else if (act === 'edit') openModal(id);
    else if (act === 'port') {
      const port = Number(el.dataset.port);
      SW.sel = SW.sel && SW.sel.sid === id && SW.sel.port === port ? null : { sid: id, port };
      render(); loadHistory();
      if (SW.sel) { const d = document.querySelector('.sw-detail'); if (d) d.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); }
    }
    else if (act === 'sub') {
      SW.sub = el.dataset.sub === 'hist' ? 'hist' : el.dataset.sub === 'mac' ? 'mac' : 'status';
      try { localStorage.setItem('pi-net-sub', SW.sub); } catch (e) {}
      SW.hash = ''; await load();
    }
    else if (act === 'toporeset') { SW.pos = {}; try { localStorage.removeItem('pi-sw-topo'); } catch (e) {} render(); }
    else if (act === 'closeport') { SW.sel = null; render(); }
    else if (act === 'range') { SW.range = el.dataset.range; render(); loadHistory(true); }
    else if (act === 'showall') { SW.showAll[id] = !SW.showAll[id]; render(); }
    else if (act === 'saveport') {
      await post('api/switches/port', { id, port: Number(el.dataset.port), label: $('sw-lbl').value, uplink: $('sw-upl').checked, watch: $('sw-watch').checked });
      toast(t('swSaved')); SW.hash = ''; await load();
    }
    else if (act === 'mcancel') closeModal();
    else if (act === 'mtest') {
      const r = $('m-res'); r.className = 'm-res'; r.textContent = t('swTesting'); el.disabled = true;
      try { const d = await post('api/switches/test', formBody(id)); r.className = 'm-res ok'; r.textContent = t('swTestOk', d); }
      catch (er) { r.className = 'm-res bad'; r.textContent = er.message; }
      el.disabled = false;
    }
    else if (act === 'msave') {
      el.disabled = true;
      try { await post('api/switches/save', formBody(id)); closeModal(); toast(t('swSaved')); SW.hash = ''; await load(); setTimeout(() => { SW.hash = ''; load(); }, 6000); }
      catch (er) { const r = $('m-res'); r.className = 'm-res bad'; r.textContent = er.message; el.disabled = false; }
    }
    else if (act === 'mdel') {
      const name = $('m-name').value;
      if (!confirm(t('swDelConfirm', name))) return;
      await post('api/switches/delete', { id }); closeModal(); toast(t('swDeleted')); SW.sel = null; SW.hash = ''; await load();
    }
  } catch (er) { if (er.message !== '401') toast(er.message, true); }
}

function init() {
  const root = $('view-switches'); if (!root) return;
  root.addEventListener('click', onClick);
  const side = $('sw-side-list');
  if (side) {
    const pick = e => { const r = e.target.closest && e.target.closest('[data-sw-only]'); if (!r) return; SW.only = r.getAttribute('data-sw-only') || ''; if (SW.data) render(); };
    side.addEventListener('click', pick);
    side.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(e); } });
  }
  document.addEventListener('click', e => { if (e.target.closest && e.target.closest('#sw-modal')) onClick(e); });
  root.addEventListener('mousemove', onMove); root.addEventListener('mouseleave', () => { const tip = $('sw-tip'); if (tip) tip.style.display = 'none'; });
  const refreshMac = () => { const b = macBody(), body = $('sw-macbody'); if (body) body.innerHTML = b.html; const c = $('sw-maccount'); if (c) c.textContent = b.count; };
  root.addEventListener('input', e => { if (e.target.id === 'sw-q') { SW.q = e.target.value; refreshMac(); } });
  root.addEventListener('change', e => {
    if (e.target.id === 'sw-msw') { SW.msw = e.target.value; refreshMac(); }
    else if (e.target.id === 'sw-mknown') { SW.known = e.target.checked; refreshMac(); }
  });
  // Arrastrar los nodos del mapa. / EN: Drag the map nodes.
  root.addEventListener('pointerdown', e => {
    const g = e.target.closest && e.target.closest('.sw-node-g'); if (!g) return;
    SW.drag = { name: g.dataset.name }; e.preventDefault();
  });
  document.addEventListener('pointermove', e => {
    if (!SW.drag || !SW.data) return;
    const svg = document.querySelector('#sw-topo-box svg'); if (!svg) return;
    const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
    const m = svg.getScreenCTM(); if (!m) return;
    const p = pt.matrixTransform(m.inverse()), W = +svg.dataset.w, H = +svg.dataset.h;
    SW.pos[SW.drag.name] = [Math.round(Math.min(W - 62, Math.max(62, p.x))), Math.round(Math.min(H - 15, Math.max(15, p.y)))];
    $('sw-topo-box').innerHTML = topoSvg(SW.data);
  });
  const endDrag = () => { if (!SW.drag) return; SW.drag = null; try { localStorage.setItem('pi-sw-topo', JSON.stringify(SW.pos)); } catch (e) {} render(); };
  document.addEventListener('pointerup', endDrag); document.addEventListener('pointercancel', endDrag);
  root.addEventListener('change', async e => {
    if (e.target.id !== 'sw-poll') return;
    try { await post('api/switches/poll', { seconds: Number(e.target.value) }); toast(t('swPollSet')); SW.hash = ''; load(); } catch (er) { toast(er.message, true); }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
  document.querySelectorAll('.view-tab').forEach(b => b.addEventListener('click', () => setView(b.dataset.view)));
  // El cambio de idioma de app.js repinta sus textos; esta pestaña se vuelve a dibujar también.
  // EN: app.js's language switch repaints its texts; this tab is redrawn too.
  if (typeof window.setLang === 'function') {
    const orig = window.setLang;
    window.setLang = function (l) { orig.apply(this, arguments); document.querySelectorAll('.view-tab').forEach(b => { b.textContent = t(b.dataset.i18n); }); if (SW.data) render(); };
  }
  document.querySelectorAll('.view-tab').forEach(b => { b.textContent = t(b.dataset.i18n); });
  try { const sv = localStorage.getItem('pi-net-sub'); if (sv === 'hist' || sv === 'mac') SW.sub = sv; SW.pos = JSON.parse(localStorage.getItem('pi-sw-topo') || '{}') || {}; } catch (e) {}
  let v = 'hosts';
  try { v = location.hash === '#switches' ? 'switches' : (location.hash === '' && localStorage.getItem('pi-net-view') === 'switches' ? 'switches' : 'hosts'); } catch (e) {}
  setView(v);
  window.addEventListener('hashchange', () => { if (location.hash === '#switches' && SW.view !== 'switches') setView('switches'); });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
