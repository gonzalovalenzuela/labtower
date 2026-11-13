// ── i18n ──────────────────────────────────────────────
const LANG={
  en:{
    titleLogout:'Sign out',titleCsv:'Export history as CSV',phServer:'Server',
    loginTitle:'Sign in',loginSub:'Enter your credentials to continue.',
    username:'Username',password:'Password',loginBtn:'Sign in',rememberMe:'Remember me',rem1d:'1 day',rem1w:'1 week',rem1m:'1 month',remForever:'Forever',
    navSection:'Navigation',nutServers:'NUT Servers',addServer:'Add server',
    dashTitle:'Dashboard — All UPS',
    themeLight:'Light',themeDark:'Dark',
    statTotalUPS:'Total UPS',statOnline:'Online',statOnBatt:'On battery',
    statClients:'Connected clients',statLoad:'Total load',
    upsSummary:'UPS Summary',srvErrSince:d=>`data shown is from ${d}`,
    colUPSServer:'UPS / Server',colStatus:'Status',colBattery:'Battery',
    colRuntime:'Runtime',colClients:'Clients',
    criticalBatt:'Critical battery!',onBattMsg:'On battery',
    noUPS:'No UPS found',details:'Details',close:'Close',cancel:'Cancel',
    permReadonly:'Read-only',permExecute:'Execute',permAdmin:'Administrator',
    sessionExpired:'Session expired',
    statusOnline:'Online',statusOnBatt:'On battery',statusLowBatt:'Low battery',
    statusUnknown:'Unknown',
    gaugeLabel_battery:'Battery',gaugeLabel_load:'Load',gaugeLabel_runtime:'Runtime',
    gaugeUnit_minLeft:'min left',
    gaugeLabel_power:'Power',gaugeLabel_temp:'Temperature',gaugeLabel_current:'Current',
    varLabel_inputV:'Input voltage',varLabel_outputV:'Output voltage',
    varLabel_battV:'Battery voltage',varLabel_temp:'Temperature',
    varLabel_outCurr:'Output current',varLabel_freq:'Frequency',
    clientsLabel:'Clients',
    alertCritBatt:'Critical battery — connect to power immediately',
    alertOnBatt:'On battery —',alertMinLeft:'min left',
    pwTitle:'Power & status',pwFlag_RB:'Replace battery',pwFlag_OVER:'Overload',pwFlag_BYPASS:'Bypass',pwFlag_OFF:'Output off',pwFlag_FSD:'Forced shutdown',pwFlag_ALARM:'Alarm',pwFlag_TRIM:'Trimming high voltage',pwFlag_BOOST:'Boosting low voltage',pwFlag_CAL:'Calibrating',
    pwFlagTip_RB:'The UPS says its battery needs replacing',pwFlagTip_OVER:'The load exceeds what the UPS can supply',pwFlagTip_BYPASS:'The load is fed straight from the mains, without protection',pwFlagTip_OFF:'The UPS output is off',pwFlagTip_FSD:'The UPS ordered the connected machines to shut down',pwFlagTip_ALARM:'The UPS reports an alarm',pwFlagTip_TRIM:'The UPS is lowering a mains voltage that is too high',pwFlagTip_BOOST:'The UPS is raising a mains voltage that is too low',pwFlagTip_CAL:'Runtime calibration in progress',
    pwAlarm:'UPS alarm',pwBeeper:'Beeper',pwBeep_enabled:'enabled',pwBeep_disabled:'disabled',pwBeep_muted:'muted',
    pwMargin:'Shutdown margin',pwMarginOk:(m,n)=>`${m} min of runtime before shutdown (machines need ${n} min)`,pwMarginBad:(m,n)=>`Only ${m} min before shutdown, machines need ${n} min`,pwMarginFull:'at full charge',pwMarginNow:'now',
    pwVolt:'Input voltage',pwVoltFmt:(a,b,c)=>`${a}–${b} V (nominal ${c})`,pwSag:'Sags',pwSurge:'Surges',pwXfer:'Transfers to battery',pwNone:'None',pwWindow:'last',pwNeedHist:'Collecting voltage history…',pwBand:(l,h)=>`Outside ${l}–${h} V (±10 %)`,
    batTitle:'Battery',batRuntime:'Runtime now',batFull:'Runtime at full charge',batPlus50:'If the load rises 50 %',batAge:'Battery age',batSetDateTip:'Set the date the battery was replaced',batSince:(d)=>`replaced ${d}`,batUnknown:'unknown',batAskDate:'Date the battery was replaced (YYYY-MM-DD). Leave empty to use the date the UPS reports:',batDateSaved:'Battery date saved',batYears:(y)=>`${y} years`,batMonths:(m)=>m<1?'less than 1 month':m===1?'1 month':`${m} months`,batAging:'Capacity trend',batAgingFmt:(c,w)=>`${c>0?'+':''}${c} % in ${w} weeks`,batCollecting:'collecting data (needs about a month)',batAgingWarn:'The battery holds noticeably less than before: consider replacing it',batOldWarn:'Battery older than 4 years: consider replacing it',batTests:'Self-tests',batTestNow:'Last result',batNoTests:'No self-test recorded yet (only changes are logged)',batApprox:'estimate',tkpassed:'passed',tkfailed:'failed',tkrunning:'running',tknone:'none',tkother:'other',
    avStreak:'Online streak',avSince:'since monitoring began',avOnBatt:'On battery now',av24:'Availability 24 h',av7:'Availability 7 d',av30:'Availability 30 d',avLast:'Last outage',avNone:'None recorded',avCount:'Outages (30 d)',avMin:'min. charge',
    chartTitle_voltage:'Input vs output voltage',
    chartLegend_input:'Input',chartLegend_output:'Output',chartLegend_watts:'Watts',
    chartTitle_power:'Power consumption',chartTitle_temp:'UPS temperature',chartLegend_temp:'Temperature (°C)',chartTitle_runtime:'Runtime',chartLegend_runtime:'Runtime (min)',
    filterAll:'All',filterActivity:'Activity',filterClear:'Clear',
    noDataChart:'No consumption data for this period',
    accumulating:'Accumulating data…',
    testConnected:(n,v)=>`✓ Connected — ${n} UPS${v?' · '+v:''}`,
    calcVA:'V×A calculated',calcLoad:'VA×load',
    upsCountUnit:(n)=>`${n} UPS`,nodeCountUnit:(n)=>`${n} node${n!==1?'s':''}`,pause:'Pause',resume:'Resume',paused:'Paused',pausedOk:n=>`${n} paused`,resumedOk:n=>`${n} resumed`,
    addServerTitle:'Add NUT server',editServerTitle:'Edit NUT server',saveBtn:'Save',serverEdited:(name)=>`${name} updated`,serverEditedLog:(name)=>`Server updated: ${name}`,addServerName:'Name',addServerHost:'Host / IP',
    addServerPort:'Port',addServerTest:'Test',addServerBtn:'Add',
    deleteServerTitle:'Delete server',deleteServerConfirm:(name)=>`Delete server "${name}"? Monitoring will stop.`,
    noUPSDetail:'No UPS found. Add a NUT server or verify upsd is running.',
    connectingSrv:'Connecting to the NUT server…',
    upsCountMsg:(ups,srv)=>`${ups} UPS on ${srv} server${srv!==1?'s':''}`,
    serverAdded:(name)=>`${name} added`,serverDeleted:(name)=>`${name} deleted`,
    serverAddedLog:(name)=>`Server added: ${name}`,serverDeletedLog:(name)=>`Server deleted: ${name}`,
    testBtn:'Test',connecting:'Connecting…',testFillAll:'Fill in all fields'
  },
  es:{
    titleLogout:'Cerrar sesión',titleCsv:'Exportar histórico CSV',phServer:'Servidor',
    loginTitle:'Iniciar sesión',loginSub:'Ingresa tus credenciales para continuar.',
    username:'Usuario',password:'Contraseña',loginBtn:'Entrar',rememberMe:'Recordarme',rem1d:'1 día',rem1w:'1 semana',rem1m:'1 mes',remForever:'Siempre',
    navSection:'Navegación',nutServers:'Servidores NUT',addServer:'Agregar servidor',
    dashTitle:'Dashboard — Todas las UPS',
    themeLight:'Claro',themeDark:'Oscuro',
    statTotalUPS:'UPS totales',statOnline:'En línea',statOnBatt:'En batería',
    statClients:'Clientes conectados',statLoad:'Consumo total',
    upsSummary:'Resumen de UPS',srvErrSince:d=>`los datos son de ${d}`,
    colUPSServer:'UPS / Servidor',colStatus:'Estado',colBattery:'Batería',
    colRuntime:'Autonomía',colClients:'Clientes',
    criticalBatt:'¡Batería crítica!',onBattMsg:'En batería',
    noUPS:'Sin UPS encontradas',details:'Detalles',close:'Cerrar',cancel:'Cancelar',
    permReadonly:'Solo lectura',permExecute:'Ejecución',permAdmin:'Administrador',
    sessionExpired:'Sesión expirada',
    statusOnline:'En línea',statusOnBatt:'En batería',statusLowBatt:'Batería baja',
    statusUnknown:'Desconocido',
    gaugeLabel_battery:'Batería',gaugeLabel_load:'Carga',gaugeLabel_runtime:'Autonomía',
    gaugeUnit_minLeft:'min restantes',
    gaugeLabel_power:'Consumo',gaugeLabel_temp:'Temperatura',gaugeLabel_current:'Corriente',
    varLabel_inputV:'Tensión entrada',varLabel_outputV:'Tensión salida',
    varLabel_battV:'Tensión batería',varLabel_temp:'Temperatura',
    varLabel_outCurr:'Corriente salida',varLabel_freq:'Frecuencia',
    clientsLabel:'Clientes',
    alertCritBatt:'Batería crítica — conectar a corriente inmediatamente',
    alertOnBatt:'En batería —',alertMinLeft:'min restantes',
    pwTitle:'Energía y estado',pwFlag_RB:'Reemplazar batería',pwFlag_OVER:'Sobrecarga',pwFlag_BYPASS:'Bypass',pwFlag_OFF:'Salida apagada',pwFlag_FSD:'Apagado forzado',pwFlag_ALARM:'Alarma',pwFlag_TRIM:'Reduciendo voltaje alto',pwFlag_BOOST:'Elevando voltaje bajo',pwFlag_CAL:'Calibrando',
    pwFlagTip_RB:'El UPS informa que su batería debe reemplazarse',pwFlagTip_OVER:'La carga supera lo que el UPS puede entregar',pwFlagTip_BYPASS:'La carga se alimenta directo de la red, sin protección',pwFlagTip_OFF:'La salida del UPS está apagada',pwFlagTip_FSD:'El UPS ordenó apagar los equipos conectados',pwFlagTip_ALARM:'El UPS informa una alarma',pwFlagTip_TRIM:'El UPS está bajando un voltaje de red demasiado alto',pwFlagTip_BOOST:'El UPS está subiendo un voltaje de red demasiado bajo',pwFlagTip_CAL:'Calibración de autonomía en curso',
    pwAlarm:'Alarma del UPS',pwBeeper:'Beeper',pwBeep_enabled:'activado',pwBeep_disabled:'desactivado',pwBeep_muted:'silenciado',
    pwMargin:'Margen de apagado',pwMarginOk:(m,n)=>`${m} min de autonomía antes del apagado (los equipos necesitan ${n} min)`,pwMarginBad:(m,n)=>`Solo ${m} min antes del apagado, los equipos necesitan ${n} min`,pwMarginFull:'a carga completa',pwMarginNow:'ahora',
    pwVolt:'Voltaje de entrada',pwVoltFmt:(a,b,c)=>`${a}–${b} V (nominal ${c})`,pwSag:'Bajones',pwSurge:'Subidas',pwXfer:'Cambios a batería',pwNone:'Ninguno',pwWindow:'últimas',pwNeedHist:'Recopilando historial de voltaje…',pwBand:(l,h)=>`Fuera de ${l}–${h} V (±10 %)`,
    batTitle:'Batería',batRuntime:'Autonomía ahora',batFull:'Autonomía con batería llena',batPlus50:'Si la carga sube 50 %',batAge:'Edad de la batería',batSetDateTip:'Indicar la fecha en que se cambió la batería',batSince:(d)=>`cambiada ${d}`,batUnknown:'desconocida',batAskDate:'Fecha en que se cambió la batería (AAAA-MM-DD). Déjala vacía para usar la fecha que informa el UPS:',batDateSaved:'Fecha de la batería guardada',batYears:(y)=>`${y} años`,batMonths:(m)=>m<1?'menos de 1 mes':m===1?'1 mes':`${m} meses`,batAging:'Tendencia de capacidad',batAgingFmt:(c,w)=>`${c>0?'+':''}${c} % en ${w} semanas`,batCollecting:'reuniendo datos (hace falta cerca de un mes)',batAgingWarn:'La batería aguanta bastante menos que antes: conviene cambiarla',batOldWarn:'Batería de más de 4 años: conviene cambiarla',batTests:'Autotests',batTestNow:'Último resultado',batNoTests:'Aún no hay autotests registrados (solo se anotan los cambios)',batApprox:'estimación',tkpassed:'aprobado',tkfailed:'falló',tkrunning:'en curso',tknone:'ninguno',tkother:'otro',
    avStreak:'Tiempo en línea',avSince:'desde que se monitorea',avOnBatt:'En batería ahora',av24:'Disponibilidad 24 h',av7:'Disponibilidad 7 d',av30:'Disponibilidad 30 d',avLast:'Último corte',avNone:'Ninguno registrado',avCount:'Cortes (30 d)',avMin:'carga mín.',
    chartTitle_voltage:'Voltaje entrada vs salida',
    chartLegend_input:'Entrada',chartLegend_output:'Salida',chartLegend_watts:'Watts',
    chartTitle_power:'Consumo',chartTitle_temp:'Temperatura de la UPS',chartLegend_temp:'Temperatura (°C)',chartTitle_runtime:'Autonomía',chartLegend_runtime:'Autonomía (min)',
    filterAll:'Todo',filterActivity:'Actividad',filterClear:'Limpiar',
    noDataChart:'Sin datos de consumo en este período',
    accumulating:'Acumulando datos…',
    testConnected:(n,v)=>`✓ Conectado — ${n} UPS${v?' · '+v:''}`,
    calcVA:'V×A calculado',calcLoad:'VA×carga',
    upsCountUnit:(n)=>`${n} UPS`,nodeCountUnit:(n)=>`${n} nodo${n!==1?'s':''}`,pause:'Pausar',resume:'Reanudar',paused:'Pausado',pausedOk:n=>`${n} pausado`,resumedOk:n=>`${n} reanudado`,
    addServerTitle:'Agregar servidor NUT',editServerTitle:'Editar servidor NUT',saveBtn:'Guardar',serverEdited:(name)=>`${name} actualizado`,serverEditedLog:(name)=>`Servidor actualizado: ${name}`,addServerName:'Nombre',addServerHost:'Host / IP',
    addServerPort:'Puerto',addServerTest:'Probar',addServerBtn:'Agregar',
    deleteServerTitle:'Eliminar servidor',deleteServerConfirm:(name)=>`¿Eliminar el servidor "${name}"? Se detendrá el monitoreo.`,
    noUPSDetail:'Sin UPS. Agrega un servidor NUT o verifica que upsd esté activo.',
    connectingSrv:'Conectando con el servidor NUT…',
    upsCountMsg:(ups,srv)=>`${ups} UPS en ${srv} servidor${srv!==1?'es':''}`,
    serverAdded:(name)=>`${name} agregado`,serverDeleted:(name)=>`${name} eliminado`,
    serverAddedLog:(name)=>`Servidor agregado: ${name}`,serverDeletedLog:(name)=>`Servidor eliminado: ${name}`,
    testBtn:'Probar',connecting:'Conectando…',testFillAll:'Completa todos los campos'
  }
};
let _lang=localStorage.getItem('pi-lang')||'en';
var _i18nReady=false;
// Traducción: busca la clave en el idioma activo (admite textos con función para incluir valores).
// EN: Translation: looks the key up in the active language (supports function texts that take values).
function t(k,...args){const v=(LANG[_lang]||LANG.en)[k]||(LANG.en)[k]||k;return typeof v==='function'?v(...args):v;}
// Cambia el idioma, lo recuerda y vuelve a pintar los textos de la página.
// EN: Switch the language, remember it and repaint the page texts.
function setLang(l){
  _lang=l;localStorage.setItem('pi-lang',l);document.documentElement.lang=l;try{renderNav();}catch(e){}
  document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=t(el.getAttribute('data-i18n')));
  document.querySelectorAll('[data-i18n-title]').forEach(el=>el.title=t(el.getAttribute('data-i18n-title')));
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>el.placeholder=t(el.getAttribute('data-i18n-ph')));
  ['en','es'].forEach(x=>document.getElementById('lang-'+x)?.classList.toggle('active',x===l));
  if(_i18nReady && typeof renderDashboard==='function')renderDashboard();
  try{setServerForm();}catch(e){}
}
(()=>setLang(_lang))();

// Estado: sesión, servidores, últimos datos de cada uno y la UPS expandida (clave «servidor/ups»).
// EN: State: session, servers, latest data of each one and the expanded UPS (key "server/ups").
let ME=null, servers=[], allData={}, expanded=null, pollTimer=null, _firstChartDrawn=false;
// El estado actual se refresca cada 5 segundos.
// EN: The current state is refreshed every 5 seconds.
const POLL=5000;
// Anillo de carga/carga de batería: radio 14.5 y trazo 4.5 en un viewBox de 36, así el borde exterior (16.75) queda dentro del lienzo y no se corta.
// EN: Battery/load ring: radius 14.5 and stroke 4.5 in a 36 viewBox, so the outer edge (16.75) stays inside the canvas and is not clipped.
const RING_R=14.5, CIRC=2*Math.PI*RING_R;
const ringDash=pct=>{const p=Math.max(0,Math.min(100,+pct||0));return p<=0?`0 ${CIRC}`:`${CIRC} ${CIRC}`};
const ringOff=pct=>CIRC-(Math.max(0,Math.min(100,+pct||0))/100)*CIRC;

// ¿Puede agregar, editar y borrar servidores? (nivel «admin» de UPS).
// EN: Can it add, edit and delete servers? (UPS "admin" level).
function canAdmin(){return ME&&ME.permissions?.nut==='admin';}

// ── Nav reordenable ───────────────────────────────────────────────────────────
const _NAV_SELF='nut';
// Navegación compartida (nav.js): mismo orden y grupos en todos los módulos. / EN: shared navigation (nav.js): same order and groups in every module.
function renderNav(){if(window.labNav)labNav.render({self:_NAV_SELF,lang:_lang,me:ME});}

// ── Login ─────────────────────────────────────────────────────────────────────
document.getElementById('l-pass').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});

// Inicio de sesión. La cookie la fija el servidor (HttpOnly): el JavaScript nunca guarda el token.
// EN: Login. The cookie is set by the server (HttpOnly): the JavaScript never stores the token.
async function doLogin(){
  const btn=document.getElementById('btn-l'),err=document.getElementById('login-err');
  const u=document.getElementById('l-user').value.trim(),p=document.getElementById('l-pass').value;
  err.className='login-err';
  if(!u||!p){err.textContent=t('testFillAll')||'Fill in all fields';err.className='login-err show';return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const r=await fetch('api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p,remember:remValue()})});
    const d=await r.json();
    if(!r.ok||!d.ok){err.textContent=d.error||'Credenciales incorrectas';err.className='login-err show';return;}
    // Cuenta con contraseña por cambiar (admin/admin inicial): se va a la pantalla obligatoria antes de entrar.
    // EN: Account with a password to change (initial admin/admin): go to the mandatory screen before entering.
    if(d.must_change_password){location.href='/admin/change-password?next='+encodeURIComponent(location.pathname);return;}
    if(!d.permissions?.nut||d.permissions.nut==='none'){err.textContent=t('noAccess')||'No access to UPS Monitor';err.className='login-err show';return;}
    ME=d;applyPermissions();await initApp();
    document.getElementById('login-screen').style.display='none';
  }catch(e){err.textContent='Error: '+e.message;err.className='login-err show';}
  finally{btn.disabled=false;btn.textContent=t('loginBtn');}
}

// Pregunta al servidor quién es el usuario; sin sesión o sin acceso a UPS devuelve false y se muestra el login.
// EN: Ask the server who the user is; without a session or without UPS access it returns false and the login is shown.
async function checkSession(){
  try{
    const r=await fetch('api/me');if(!r.ok)return false;
    const d=await r.json();
    if(!d.username||!d.permissions?.nut||d.permissions.nut==='none')return false;
    ME=d;return true;
  }catch{return false;}
}

// Muestra nombre y rol y oculta los controles de administración a quien no es admin.
// EN: Show name and role and hide the admin controls from non-admins.
function applyPermissions(){
  const _un=String(ME.username||'?');
  document.getElementById('me-name').textContent=_un;
  document.getElementById('avatar').textContent=_un[0].toUpperCase();
  const _permKey={readonly:'permReadonly',execute:'permExecute',admin:'permAdmin'}[ME.permissions?.nut];
  document.getElementById('me-role').textContent=_permKey?t(_permKey):'—';
  renderNav();
  if(canAdmin()){document.getElementById('btn-add-srv').style.display='';}
}

// Cierra la sesión en el servidor y recarga la página.
// EN: Close the session on the server and reload the page.
async function logout(){await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.reload();}

// ── Init & fetch ──────────────────────────────────────────────────────────────
// Arranque tras iniciar sesión: reloj, primera descarga y refresco periódico.
// EN: Startup after login: clock, first download and periodic refresh.
async function initApp(){
  updateClock();setInterval(updateClock,1000);
  log('INFO','UPS Monitor iniciando...');
  await fetchAll();
  pollTimer=setInterval(fetchAll,POLL);
}

// El refresco automático pide solo el estado actual (sin historial); el historial de cada
// gráfico se pide aparte, por rango, y solo cuando ese gráfico lo necesita.
// El refresco automático pide solo el estado actual (range=none, sin historial); el historial de cada gráfico se pide aparte, por rango, y solo cuando ese gráfico lo necesita. Así el servidor no envía un año de datos cada 5 s.
// EN: The automatic refresh asks only for the current state (range=none, no history); each chart's history is requested separately, by range, and only when that chart needs it. This way the server does not send a year of data every 5 s.
const _pollRange = 'none';
const _csvRange  = 'all';
const DEFAULT_RANGE = '1h';   // rango inicial de los gráficos
// Hora en que cada UPS pasó a batería (OB), para mostrar cuánto lleva funcionando con ella.
// EN: Time when each UPS switched to battery (OB), to show how long it has been running on it.
let _obStartTs = {}; // { "srvId:upsName": timestamp cuando entró en OB }

// Descarga el historial completo de la UPS activa como CSV (lo genera el servidor).
// EN: Download the full history of the active UPS as CSV (generated by the server).
function exportCSV(){
  // Exportar historial del servidor/UPS activo (usa expanded o primer srv/ups disponible)
  if(!servers.length){toast(t('noUPS'),true);return;}
  let srvId = 'local', upsName = 'ups';
  if(expanded){
    const parts = expanded.split('/');
    srvId = parts[0];
    upsName = parts.slice(1).join('/');
  } else if(servers.length>0){
    srvId = servers[0].id;
    const snap = allData[srvId];
    const keys = snap ? Object.keys(snap.ups||{}) : [];
    if(keys.length>0) upsName = keys[0];
  }
  const range = _csvRange;
  const url = `api/export/csv?srv=${encodeURIComponent(srvId)}&ups=${encodeURIComponent(upsName)}&range=${range}`;
  const a = document.createElement('a');
  a.href = url;
  a.download = `ups-history-${srvId}-${upsName}-${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}

// Descarga servidores y datos de las UPS en paralelo y repinta. Un 401 recarga la página (sesión vencida).
// EN: Download servers and UPS data in parallel and repaint. A 401 reloads the page (expired session).
let NET_NAMES={};   // IP → nombre conocido por Net Monitor / EN: IP → name known by Net Monitor
async function fetchAll(){
  try{
    const [r1,r2]=await Promise.all([
      fetch('api/servers?range='+_pollRange),
      fetch('api/ups?range='+_pollRange)
    ]);
    if(r1.status===401||r2.status===401){location.reload();return;}
    const j1=await r1.json(); servers=j1.servers||[]; NET_NAMES=j1.names||{};
    allData=await r2.json();
    renderSidebar();
    renderDashboard();
    // Redibujar gráfico de voltaje si hay detalle abierto
    if(expanded){
      const parts = expanded.split('/');
      const sid = parts[0], upsName = parts.slice(1).join('/');
      const snap = allData[sid];
      if(snap) drawVoltageChartForKey(expanded);
    }
    // Primera carga: dibujar gráfico de la primera UPS auto-expandida
    if(!_firstChartDrawn && expanded){
      _firstChartDrawn = true;
      const parts = expanded.split('/');
      const snap = allData[parts[0]];
      if(snap){
        const upsName = parts.slice(1).join('/');
        setTimeout(()=>drawVoltageChartForKey(expanded),100);
      }
    }
  }catch(e){log('ERR','Error: '+e.message);}
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
// Lista de servidores NUT con su estado de conexión.
// EN: List of NUT servers with their connection state.
function renderSidebar(){
  const list=document.getElementById('srv-list');list.innerHTML='';
  servers.forEach(s=>{
    const snap=allData[s.id];
    const dotCls=s.paused?'paused':!snap?'loading':snap.error?'err':snap.last_ok?'ok':'loading';
    const upsCount=snap?Object.keys(snap.ups||{}).length:0;
    const div=document.createElement('div');div.className='srv-nav';
    div.innerHTML=`<span class="srv-dot-sm ${dotCls}"></span>
      <div class="srv-nav-info">
        <div class="srv-nav-top"><div class="srv-nav-name">${esc(s.name)}</div>${canAdmin()?`<span class="srv-acts"><button class="btn-ghost-sm edit" data-on-click="pauseServer" data-on-click-args="${jsargs([{'@':'this'},s.id,!s.paused])}" title="${esc(t(s.paused?'resume':'pause'))}" aria-label="${esc(t(s.paused?'resume':'pause'))}">${s.paused?'<svg viewBox="0 0 24 24"><polygon points="7,4 20,12 7,20"/></svg>':'<svg viewBox="0 0 24 24"><line x1="8" y1="5" x2="8" y2="19"/><line x1="16" y1="5" x2="16" y2="19"/></svg>'}</button><button class="btn-ghost-sm edit" data-on-click="openEditServer" data-on-click-args="${jsargs([s.id])}" title="${t('editServerTitle')}"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg></button><button class="btn-ghost-sm" data-on-click="confirmDeleteServer" data-on-click-args="${jsargs([s.id,s.name])}" title="${t('deleteServerTitle')}"><svg viewBox="0 0 24 24"><polyline points="3,6 5,6 21,6"/><path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6"/></svg></button></span>`:''}</div>
        <div class="srv-nav-host" title="${esc(s.host)}:${s.port}"><span data-nethost="${esc(s.host)}">${esc(s.host)}</span>:${s.port}</div>
        ${s.paused?`<div class="srv-nav-host">${esc(t('paused'))}</div>`:upsCount?`<div class="srv-nav-host">${t('upsCountUnit',upsCount)}</div>`:''}
      </div>
      `;
    list.appendChild(div);
  });
}

// ── Dashboard: todas las UPS de todos los servidores ──────────────────────────
// Dibuja la tabla: junta todas las UPS de todos los servidores en una lista, calcula los totales de la cabecera (en línea, a batería, clientes y consumo en vatios: ups.realpower o, si falta, voltaje × corriente) y arma cada fila con su estado, carga, autonomía y detalle. La primera UPS se expande sola.
// EN: Draw the table: gather every UPS of every server in a list, compute the header totals (online, on battery, clients and power draw in watts: ups.realpower or, if missing, voltage × current) and build each row with its state, charge, runtime and detail. The first UPS expands by itself.
function renderDashboard(){
  const tbody=document.getElementById('ups-tbody');
  // Servidores cuya última lectura falló: el error y desde cuándo son los datos (si hay). / Servers whose last reading failed: the error and how old the data is.
  const se=document.getElementById('srv-errs');
  if(se){
    const bad=servers.filter(sv=>allData[sv.id]?.error);
    se.innerHTML=bad.map(sv=>{const sn=allData[sv.id];return `<div class="srv-err">⚠ <b>${esc(sv.name)}</b>: ${esc(sn.error)}${sn.last_ok?` <span>· ${esc(t('srvErrSince',fdt(sn.last_ok)))}</span>`:''}</div>`;}).join('');
    se.style.display=bad.length?'':'none';
  }

  // Construir lista plana de todas las UPS
  const rows=[];
  servers.forEach(srv=>{
    const snap=allData[srv.id];
    if(!snap)return;
    const ups=snap.ups||{};
    Object.keys(ups).forEach(upsName=>{
      rows.push({
        srv, upsName,
        v:    ups[upsName],
        clients: (snap.clients||{})[upsName]||[],
        history: (snap.history||{})[upsName]||[],
        stats: (snap.stats||{})[upsName]||null,
        error: snap.error,
      });
    });
  });

  // Auto-expandir la primera UPS si aún no hay ninguna expandida
  if(rows.length>0 && !expanded){
    expanded = rows[0].srv.id+'/'+rows[0].upsName;
  }

  // Stats globales
  const totalClients=rows.reduce((n,r)=>n+r.clients.length,0);
  const onlineCount =rows.filter(r=>statusClass(r.v)==='online').length;
  const battCount   =rows.filter(r=>['onbatt','lowbatt'].includes(statusClass(r.v))).length;

  // Consumo total en watts — usa ups.realpower si existe, si no V×A
  let totalWatts=0;
  rows.forEach(r=>{
    const v=r.v;
    const realPower=parseFloat(v['ups.realpower']||0);
    if(realPower>0){
      totalWatts+=realPower;
    } else {
      // Calcular: output.voltage × output.current (VA no es W pero es aproximación)
      const volt=parseFloat(v['output.voltage']||0);
      const amp =parseFloat(v['output.current']||0);
      const load=parseFloat(v['ups.load']||0);
      const power=parseFloat(v['ups.power']||0);
      if(volt>0&&amp>0) totalWatts+=volt*amp;
      else if(power>0&&load>0) totalWatts+=power*(load/100);
    }
  });

  document.getElementById('st-total').textContent  = rows.length||'—';
  document.getElementById('st-online').textContent = onlineCount||'—';
  document.getElementById('st-onbatt').textContent = battCount||'—';
  document.getElementById('st-clients').textContent= totalClients||'—';

  // ── Banners: batería crítica (<30%) y on-battery (OB) ──────────────────────
  {
    let hasCrit=false, critMsg='', hasOB=false, obMsg='';
    rows.forEach(({srv, upsName, v})=>{
      const rs=(v['ups.status']||'');
      const charge=parseFloat(v['battery.charge']||100);
      const runtime=parseFloat(v['battery.runtime']||0);
      if(rs.includes('OB')){
        hasOB=true;
        const key=`${srv.id}:${upsName}`;
        if(!_obStartTs[key]) _obStartTs[key]=Date.now();
        const elapsed=Math.round((Date.now()-_obStartTs[key])/1000);
        const m=Math.floor(elapsed/60), s=elapsed%60;
        obMsg=`${upsName} ${t('alertOnBatt')} ${Math.round(runtime/60)} ${t('alertMinLeft')} · ${m}:${s.toString().padStart(2,'0')}`;
      } else {
        delete _obStartTs[`${srv.id}:${upsName}`];
      }
      if(charge>0 && charge<30 && !rs.includes('OB')){
        hasCrit=true;
        critMsg=`${t('criticalBatt')} ${upsName}: ${Math.round(charge)}% — ${t('alertCritBatt')}`;
      }
    });
    const obBanner=document.getElementById('ups-ob-banner');
    const critBanner=document.getElementById('ups-critical-banner');
    if(obBanner){ obBanner.style.display=hasOB?'flex':'none'; if(hasOB)document.getElementById('ups-ob-msg').textContent=obMsg; }
    if(critBanner){ critBanner.style.display=hasCrit?'flex':'none'; if(hasCrit)document.getElementById('ups-critical-msg').textContent=critMsg; }
  }
  const wEl=document.getElementById('st-watts');
  if(wEl) wEl.innerHTML=totalWatts>0
    ? Math.round(totalWatts)+'<span style="font-size:13px;color:var(--text-dim)">W</span>'
    : '—';
  document.getElementById('ups-count').textContent = t('upsCountMsg',rows.length,servers.length);

  if(!rows.length){
    // A server was just added and upsd has not answered yet: say so instead of "No UPS found".
    const connecting=servers.some(sv=>{if(sv.paused)return false;const sn=allData[sv.id];return !sn||(!sn.last_ok&&!sn.error);});
    tbody.innerHTML=`<tr><td colspan="7" style="padding:40px;text-align:center;color:var(--text-dim);font-size:13px">
      <strong style="display:block;color:var(--text-mid);margin-bottom:6px" data-i18n="noUPS">${connecting?t('connectingSrv'):t('noUPS')}</strong>
      ${connecting?'':t('noUPSDetail')}</td></tr>`;
    return;
  }

  // Reconstruir tbody preservando filas expandidas
  const newTbody=document.createElement('tbody');newTbody.id='ups-tbody';

  rows.forEach((row,i)=>{
    const key=row.srv.id+'/'+row.upsName;
    const cls=statusClass(row.v);
    const charge=parseFloat(row.v['battery.charge']??0)||0;
    const runtime=parseFloat(row.v['battery.runtime']??0)||0;
    const load=parseFloat(row.v['ups.load']??0)||0;
    const barColor=charge>60?'var(--green)':charge>25?'var(--yellow)':'var(--red)';
    const isExp=expanded===key;
    const rs=(row.v['ups.status']||'').toUpperCase();
    let badgeCls='badge-unknown',badgeTxt=rs||t('statusUnknown');
    if(rs.includes('OL')){badgeCls='badge-online';badgeTxt=t('statusOnline');}
    if(rs.includes('OB')){badgeCls='badge-onbatt';badgeTxt=t('statusOnBatt');}
    if(rs.includes('LB')){badgeCls='badge-lowbatt';badgeTxt=t('statusLowBatt');}

    // Main row
    const tr=document.createElement('tr');
    tr.className='ups-row'+(isExp?' expanded':'');
    tr.style.animationDelay=i*20+'ms';
    tr.onclick=()=>toggleExpand(key,row);
    tr.innerHTML=`
      <td><span class="sdot ${cls}"></span></td>
      <td>
        <span class="ups-cell-name">${esc(row.upsName)} <span class="srv-tag">${esc(row.srv.name)}</span></span>
        <span class="ups-cell-sub">${esc(row.v['_desc']||'UPS')}${row.v['_serial']?' &nbsp;·&nbsp; <span style="font-family:var(--mono);letter-spacing:.3px">SN '+esc(row.v['_serial'])+'</span>':''}</span>
        <span class="ups-cell-sub" style="font-family:var(--mono);letter-spacing:.3px"><span data-nethost="${esc(row.srv.host)}" data-nethost-click="1">${esc(row.srv.host)}</span><span style="color:var(--border-b)">:</span>${row.srv.port}</span>
      </td>
      <td><span class="ups-badge ${badgeCls}">${esc(badgeTxt)}</span></td>
      <td>
        <div class="charge-wrap">
          <div class="charge-bar"><div class="charge-fill" style="width:${charge}%;background:${barColor}"></div></div>
          <span class="charge-val">${charge?Math.round(charge)+'%':'—'}</span>
        </div>
      </td>
      <td style="font-family:var(--mono);font-size:12px;color:var(--text-mid)">${runtime?Math.round(runtime/60)+' min':'—'}</td>
      <td style="font-family:var(--mono);font-size:12px;color:var(--text-mid)">${row.clients.length||'—'}</td>
      <td><span class="expand-arrow ${isExp?'open':''}">▶</span></td>`;
    newTbody.appendChild(tr);

    // Alert row
    if(rs.includes('OB')||rs.includes('LB')){
      const atr=document.createElement('tr');atr.className='alert-row show';
      const cls2=rs.includes('LB')?'crit':'';
      atr.innerHTML=`<td colspan="7" class="alert-cell ${cls2}">⚠ ${rs.includes('LB')?t('alertCritBatt'):t('alertOnBatt')+' '+Math.round(runtime/60)+' '+t('alertMinLeft')}</td>`;
      newTbody.appendChild(atr);
    }

    // Detail row
    const dtr=document.createElement('tr');
    dtr.className='detail-row'+(isExp?' show':'');
    dtr.id='detail-'+key.replace(/[^a-z0-9]/gi,'-');
    const VARS=[
      ['input.voltage',     t('varLabel_inputV'),  'V'],
      ['output.voltage',    t('varLabel_outputV'),  'V'],
      ['battery.voltage',   t('varLabel_battV'),  'V'],
      ['ups.temperature',   t('varLabel_temp'),      '°C'],
      ['output.current',    t('varLabel_outCurr'), 'A'],
      ['input.frequency',   t('varLabel_freq'),       'Hz'],
    ];
    dtr.innerHTML=`<td colspan="7" class="detail-cell">
      <div class="detail-inner">
        <div class="gauge-box">
          <span class="gauge-lbl">${t('gaugeLabel_battery')}</span>
          <div class="circle-wrap">
            <svg viewBox="0 0 36 36"><circle class="circle-bg" cx="18" cy="18" r="14.5"/>
            <circle class="circle-fill" cx="18" cy="18" r="14.5"
              style="opacity:${charge>0?1:0};stroke-dasharray:${ringDash(charge)};stroke-dashoffset:${ringOff(charge)};stroke:${charge>60?'var(--green)':charge>25?'var(--yellow)':'var(--red)'}"/></svg>
            <span class="circle-val">${charge?Math.round(charge):'—'}</span>
          </div>
          <span class="gauge-unit">%</span>
        </div>
        <div class="gauge-box">
          <span class="gauge-lbl">${t('gaugeLabel_load')}</span>
          <div class="circle-wrap">
            <svg viewBox="0 0 36 36"><circle class="circle-bg" cx="18" cy="18" r="14.5"/>
            <circle class="circle-fill" cx="18" cy="18" r="14.5"
              style="opacity:${load>0?1:0};stroke-dasharray:${ringDash(load)};stroke-dashoffset:${ringOff(load)};stroke:${load<60?'var(--blue)':load<85?'var(--orange)':'var(--red)'}"/></svg>
            <span class="circle-val">${load?Math.round(load):'—'}</span>
          </div>
          <span class="gauge-unit">%</span>
        </div>
        <div class="gauge-box">
          <span class="gauge-lbl">${t('gaugeLabel_runtime')}</span>
          <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:56px;gap:4px">
            <span class="runtime-num">${runtime?Math.round(runtime/60):'—'}</span>
            <span class="gauge-unit">${t('gaugeUnit_minLeft')}</span>
          </div>
          <span class="gauge-unit">&nbsp;</span>
        </div>
        <div class="gauge-box power-box" style="flex-direction:row;justify-content:space-around;padding:8px 14px">
          ${(()=>{
            const realP=parseFloat(row.v['ups.realpower']||0);
            const volt=parseFloat(row.v['output.voltage']||0);
            const amp=parseFloat(row.v['output.current']||0);
            const pwr=parseFloat(row.v['ups.power']||0);
            const ld=parseFloat(row.v['ups.load']||0);
            let watts=0,source='';
            if(realP>0){watts=realP;source='ups.realpower';}
            else if(volt>0&&amp>0){watts=volt*amp;source=t('calcVA');}
            else if(pwr>0&&ld>0){watts=pwr*(ld/100);source=t('calcLoad');}
            const temp=parseFloat(row.v['ups.temperature']||row.v['battery.temperature']||0);
            return `
            <div style="text-align:center">
              <div class="gauge-lbl">${t('gaugeLabel_power')}</div>
              <div style="font-family:var(--mono);font-size:24px;font-weight:700;color:var(--orange);line-height:1;margin:4px 0">
                ${watts>0?Math.round(watts):'—'}
              </div>
              <div class="gauge-unit">${watts>0?'W ('+source+')':''}</div>
            </div>
            <div style="text-align:center">
              <div class="gauge-lbl">${t('gaugeLabel_temp')}</div>
              <div style="font-family:var(--mono);font-size:24px;font-weight:700;color:${temp>40?'var(--red)':temp>35?'var(--orange)':'var(--blue)'};line-height:1;margin:4px 0">
                ${temp?temp.toFixed(1):'—'}
              </div>
              <div class="gauge-unit">${temp?'°C':''}</div>
            </div>
            <div style="text-align:center">
              <div class="gauge-lbl">${t('gaugeLabel_current')}</div>
              <div style="font-family:var(--mono);font-size:24px;font-weight:700;color:var(--text);line-height:1;margin:4px 0">
                ${amp?amp:'—'}
              </div>
              <div class="gauge-unit">${amp?'A':''}</div>
            </div>`;
          })()}
        </div>
        ${availHtml(row.stats)}
        ${batHtml(row.stats,row.srv.id,row.upsName)}
        ${powerHtml(row.stats)}
        <div class="vars-section">
          ${VARS.map(([k,l,u])=>{const val=row.v[k];return`<div class="var-cell"><span class="var-key">${l}</span><span class="var-val">${val?esc(val)+' '+u:'<span style="opacity:.3">—</span>'}</span></div>`;}).join('')}
        </div>
        ${row.clients.length?`<div class="clients-section">
          <span class="clients-lbl">${t('clientsLabel')}</span>
          <div class="client-chips">${row.clients.map(c=>`<span class="client-chip"><span data-nethost="${esc(c)}" data-nethost-click="1">${esc(NET_NAMES[c]?NET_NAMES[c]+' · '+c:c)}</span></span>`).join('')}</div>
        </div>`:''}
        ${nutChartHtml(key,'v')}
        ${nutChartHtml(key,'w')}
        ${parseFloat(row.v['ups.temperature']||row.v['battery.temperature']||0)>0?nutChartHtml(key,'t'):''}
        ${runtime>0?nutChartHtml(key,'r'):''}
      </div>
    </td>`;
    newTbody.appendChild(dtr);
  });

  tbody.parentNode.replaceChild(newTbody,tbody);
  fitCharts();
}

// Traduce ups.status de NUT (OL, OB, LB…) a una clase: online, onbatt, lowbatt o unknown.
// EN: Translate NUT's ups.status (OL, OB, LB…) to a class: online, onbatt, lowbatt or unknown.
function statusClass(v){
  const rs=(v['ups.status']||'').toUpperCase();
  if(rs.includes('LB'))return'lowbatt';
  if(rs.includes('OB'))return'onbatt';
  if(rs.includes('OL'))return'online';
  return'unknown';
}

// Expande o contrae el detalle de una UPS.
// EN: Expand or collapse a UPS's detail.
function toggleExpand(key,row){
  expanded=expanded===key?null:key;
  renderDashboard();
  if(expanded){
    const el=document.getElementById('detail-'+key.replace(/[^a-z0-9]/gi,'-'));
    if(el)el.scrollIntoView({behavior:'smooth',block:'nearest'});
    // Draw voltage chart after DOM settles
    drawVoltageChartForKey(key);
  }
}

// ── Voltage + Watts charts ─────────────────────────────────────────────────────
// GRÁFICOS de voltaje y de potencia: cada uno con su rango (1 h, 1 día, 1 mes, todo). rangeCache evita pedir lo mismo muchas veces: cuanto más largo el rango, más tarda en caducar.
// EN: Voltage and power CHARTS: each with its own range (1 h, 1 day, 1 month, all). rangeCache avoids requesting the same thing many times: the longer the range, the longer it takes to expire.
const vchartRanges = {};  // { key: '1h'|'1d'|'1mo'|'all' }
const wchartRanges = {};  // idem para watts
const tchartRanges = {};  // idem para la temperatura de la UPS / same for the UPS temperature
const rchartRanges = {};  // idem para la autonomía (battery.runtime) / same for the runtime (battery.runtime)

// Historial por rango: el servidor devuelve cada rango ya reducido (agrupado por tiempo).
// Cada rango se pide solo cuando algún gráfico lo usa y se vuelve a pedir a su propio
// ritmo: los rangos largos casi no cambian, así que no hace falta releerlos seguido.
const rangeCache = {};   // 'srv/ups|range' -> {ts, rows}
const RANGE_TTL = {'1h':10000, '1d':60000, '1w':180000, '1mo':300000, 'all':600000}; // ms
// Pide al servidor el historial de una UPS para un rango, con caché; si la red falla, devuelve lo último que tenía.
// EN: Ask the server for a UPS's history for a range, with cache; if the network fails, it returns the last copy it had.
async function fetchRangeHistory(key, range, prev){
  const ck = key+'|'+range+(prev?'|prev':''), c = rangeCache[ck];
  if(c && Date.now()-c.ts < (RANGE_TTL[range]||10000)) return c.rows;
  const srv = key.split('/')[0], ups = key.split('/').slice(1).join('/');
  try{
    const r = await fetch('api/history?srv='+encodeURIComponent(srv)+'&ups='+encodeURIComponent(ups)+'&range='+range+(prev?'&prev=1':''));
    if(!r.ok) throw new Error('HTTP '+r.status);
    const rows = (await r.json()).history||[];
    rangeCache[ck] = {ts:Date.now(), rows};
    return rows;
  }catch(e){ return c ? c.rows : null; }
}
// Filas ya descargadas para ese rango (null si todavía no llegaron)
// Filas de historial ya cargadas para un gráfico y rango.
// EN: History rows already loaded for a chart and range.
function rangeRows(key, range, prev){
  const c = rangeCache[key+'|'+range+(prev?'|prev':'')];
  return c ? c.rows : null;
}
// Make the whole dashboard fit one screen: the charts take whatever vertical space is left (90-300 px).
let _fitBusy=false;
// Ajusta la altura de los gráficos para que quepan en la pantalla sin hacer scroll (mide el espacio ocupado y reparte el resto, entre 90 y 300 px).
// EN: Adjust the chart height so they fit on screen without scrolling (measures the used space and distributes the rest, between 90 and 300 px).
function fitCharts(){
  const root=document.documentElement, content=document.querySelector('.content'), top=document.querySelector('.topbar');
  if(!content||!top||!document.querySelector('canvas.vchart'))return;
  const cur=parseInt(root.style.getPropertyValue('--chart-h'))||140;
  root.style.setProperty('--chart-h','140px');                         // measure from a known baseline
  const cs=getComputedStyle(content), gap=parseFloat(cs.rowGap)||0;
  const used=[...content.children].filter(e=>e.offsetParent!==null).reduce((a,e)=>a+e.offsetHeight+gap,0)-gap
    +parseFloat(cs.paddingTop)+parseFloat(cs.paddingBottom)+top.offsetHeight;
  const h=Math.max(90,Math.min(300,Math.floor(140+(window.innerHeight-used)-2)));
  root.style.setProperty('--chart-h',h+'px');
  if(h!==cur&&expanded&&!_fitBusy){_fitBusy=true;requestAnimationFrame(()=>{drawChartsFor(expanded);_fitBusy=false;});}
}
window.addEventListener('resize',()=>{clearTimeout(window._fitT);window._fitT=setTimeout(fitCharts,120);});
// Dibuja los gráficos de una UPS.
// EN: Draw a UPS's charts.
function drawChartsFor(key){
  Object.keys(NUT_CH).forEach(ty=>{const r=NUT_CH[ty].ranges[key]||DEFAULT_RANGE, rows=rangeRows(key,r); if(rows) drawNutChart(ty, key, rows, r);});
}
// Vuelve a pedir y dibujar los gráficos del rango elegido.
// EN: Request and draw again the charts of the chosen range.
async function refreshRangeCharts(key){
  const ranges = new Set(Object.values(NUT_CH).map(C=>C.ranges[key]||DEFAULT_RANGE));
  const jobs=[...ranges].map(r=>fetchRangeHistory(key, r));
  Object.keys(NUT_CH).forEach(ty=>{const r=NUT_CH[ty].ranges[key]||DEFAULT_RANGE;if(VC.cmp[key+'|'+ty]&&r!=='all')jobs.push(fetchRangeHistory(key,r,true));});
  await Promise.all(jobs);
  drawChartsFor(key);
}

// Cambia el rango de un gráfico (botones 1 h / 1 d / 1 mes / todo).
// EN: Change a chart's range (1 h / 1 d / 1 month / all buttons).
async function setVChartRange(btn, key, type){
  type = NUT_CH[type] ? type : 'v';
  const cid = NUT_CH[type].pfx+'-filters-'+key.replace(/[^a-z0-9]/gi,'-');
  document.querySelectorAll('#'+cid+' .vchart-filter:not(.vchart-cmp)').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  const store = NUT_CH[type].ranges;
  store[key] = btn.dataset.range;
  await fetchRangeHistory(key, store[key]);
  if(VC.cmp[key+'|'+type]&&store[key]!=='all') await fetchRangeHistory(key, store[key], true);
  drawChartsFor(key);
}

// Dibujar ambos gráficos al expandir detalle
// Recorta el historial al rango pedido.
// EN: Trim the history to the requested range.
function filterHistory(history, range){
  if(!history||!history.length) return history;
  if(range==='all') return history;
  // The server already limits each range using ITS clock. Trim relative to the newest point
  // (also server time), never to this browser's clock: a Pi without RTC/NTP, or a PC with a
  // different time, would otherwise drop every point and show an empty chart.
  const cutoffs = {'1h':3600,'1d':86400,'1w':604800,'1mo':2592000};
  const cutoff = cutoffs[range]||0;
  const ref = history[history.length-1].ts;
  return history.filter(p=>p.ts>=(ref-cutoff));
}

// Los gráficos de la UPS (voltaje, consumo, temperatura y autonomía) los dibuja el motor común VC (charts.js), igual que en los demás módulos.
// EN: The UPS charts (voltage, power, temperature and runtime) are drawn by the shared VC engine (charts.js), like in the other modules.
const NUT_CH = {
  v: {pfx:'vchart', tip:'vtooltip', title:'chartTitle_voltage', ranges:vchartRanges},
  w: {pfx:'wchart', tip:'wtooltip', title:'chartTitle_power',   ranges:wchartRanges},
  t: {pfx:'tchart', tip:'ttooltip', title:'chartTitle_temp',    ranges:tchartRanges},
  r: {pfx:'rchart', tip:'rtooltip', title:'chartTitle_runtime', ranges:rchartRanges}
};
function nutSeries(type){
  if(type==='w') return {keys:['watts'], series:[{k:'watts',c:'#f97316',l:t('chartLegend_watts'),f:v=>Math.round(v)+' W'}],
    axis:v=>Math.round(v)+'W', pl:40, pr:36, scale:vals=>[0,Math.ceil(Math.max(...vals)*1.15)||10],
    extra:p=>p.load?[t('gaugeLabel_load')+': '+Math.round(p.load)+'%']:[]};
  // Autonomía: el historial la guarda en segundos y se dibuja en minutos; el tooltip agrega la batería y la carga.
  // EN: Runtime: the history stores it in seconds and it is drawn in minutes; the tooltip adds the battery charge and the load.
  if(type==='r') return {keys:['rtmin'], series:[{k:'rtmin',c:'#8b5cf6',l:t('chartLegend_runtime'),f:v=>Math.round(v)+' min'}],
    axis:v=>Math.round(v)+'m', pl:40, pr:40, scale:vals=>[0,Math.ceil(Math.max(...vals)*1.15)||10],
    prep:p=>({rtmin:p.runtime>0?p.runtime/60:null}),
    extra:p=>[p.charge?'🔋 '+t('gaugeLabel_battery')+': '+Math.round(p.charge)+'%':'',p.load?t('gaugeLabel_load')+': '+Math.round(p.load)+'%':''].filter(Boolean)};
  if(type==='t') return {keys:['temp'], series:[{k:'temp',c:'#ef4444',l:t('chartLegend_temp'),f:v=>v.toFixed(1)+' °C'}],
    axis:v=>Math.round(v)+'°', pl:34, pr:30, scale:vals=>{const lo=Math.floor(Math.min(...vals)-2);return [lo,Math.max(Math.ceil(Math.max(...vals)+2),lo+6)]},
    extra:()=>[]};
  return {keys:['vin','vout'], series:[{k:'vin',c:'#4361ee',l:t('chartLegend_input'),f:v=>v.toFixed(1)+' V'},{k:'vout',c:'#22c55e',l:t('chartLegend_output'),f:v=>v.toFixed(1)+' V'}],
    axis:v=>Math.round(v)+'V', pl:34, pr:30, scale:vals=>[Math.max(0,Math.floor(Math.min(...vals)-5)),Math.ceil(Math.max(...vals)+5)],
    extra:p=>p.charge?['🔋 '+t('gaugeLabel_battery')+': '+Math.round(p.charge)+'%']:[]};
}
function nutChartHtml(key,type){
  const C=NUT_CH[type], id=key.replace(/[^a-z0-9]/gi,'-'), S=nutSeries(type);
  return VC.section({title:t(C.title), legend:S.series.map(x=>({c:x.c,l:x.l})), filtersId:C.pfx+'-filters-'+id,
    filters:VC.filters(C.ranges[key]||DEFAULT_RANGE, r=>`data-on-click="setVChartRange" data-on-click-args="${jsargs([{"@":"this"},key,type])}"`,
      `data-on-click="toggleVCmp" data-on-click-args="${jsargs([{"@":"this"},key,type])}"`, VC.cmp[key+'|'+type]),
    canvasId:C.pfx+'-'+id, tipId:C.tip+'-'+id});
}
// Valores 0 = sin lectura: la línea se corta. / Zero values mean "no reading": the line breaks.
const nz=(rows,keys)=>(rows||[]).map(p=>{const q=Object.assign({},p);keys.forEach(k=>{if(!(q[k]>0))q[k]=null;});return q;});
function drawNutChart(type,key,rows,range){
  const C=NUT_CH[type], id=key.replace(/[^a-z0-9]/gi,'-'), cv=document.getElementById(C.pfx+'-'+id); if(!cv) return;
  const S=nutSeries(type), ups=key.split('/').slice(1).join('/');
  const cmpOn=VC.cmp[key+'|'+type]&&range!=='all', prev=cmpOn?rangeRows(key,range,true):null;
  const fix=r=>r&&S.prep?r.map(p=>Object.assign({},p,S.prep(p))):r;
  VC.draw(cv,{pts:nz(fix(filterHistory(rows,range)),S.keys), prev:prev?nz(fix(prev),S.keys):null, series:S.series, range, h:null, pl:S.pl, pr:S.pr, scale:S.scale,
    axis:S.axis, lastLabels:true, extra:S.extra, mod:'nut', evFilter:e=>!e.p||!e.p.n||e.p.n===ups, tipId:C.tip+'-'+id});
}
async function toggleVCmp(btn,key,type){
  const k=key+'|'+type; VC.cmp[k]=!VC.cmp[k]; btn.classList.toggle('active',!!VC.cmp[k]);
  const range=NUT_CH[type].ranges[key]||DEFAULT_RANGE;
  if(VC.cmp[k]&&range!=='all') await fetchRangeHistory(key,range,true);
  drawChartsFor(key);
}

function drawVoltageChartForKey(key){
  requestAnimationFrame(()=>{
    drawChartsFor(key);          // al instante con lo que ya hay descargado
    refreshRangeCharts(key);     // y actualiza solo si venció el TTL del rango
  });
}

// ── Add/delete server ─────────────────────────────────────────────────────────
// Agregar, editar y borrar servidores NUT (admin). «Probar» consulta el upsd sin guardar.
// EN: Add, edit and delete NUT servers (admin). "Test" queries the upsd without saving.
let editingSrv=null;
function setServerForm(){
  document.getElementById('srv-form-title').textContent=t(editingSrv?'editServerTitle':'addServerTitle');
  document.getElementById('btn-save-srv').textContent=t(editingSrv?'saveBtn':'addServerBtn');
}
function openAddServer(){editingSrv=null;closeAddServer();setServerForm();document.getElementById('add-srv-card').style.display='block';document.getElementById('f-sname').focus();}
function openEditServer(sid){
  const s=servers.find(x=>x.id===sid);if(!s)return;
  closeAddServer();editingSrv=sid;
  document.getElementById('f-sname').value=s.name;document.getElementById('f-shost').value=s.host;document.getElementById('f-sport').value=s.port;
  setServerForm();document.getElementById('add-srv-card').style.display='block';document.getElementById('f-sname').focus();
}
function closeAddServer(){editingSrv=null;document.getElementById('add-srv-card').style.display='none';document.getElementById('test-result').className='test-result';['f-sname','f-shost'].forEach(id=>{document.getElementById(id).value='';document.getElementById(id).classList.remove('err');});document.getElementById('f-sport').value='3493';}

// Prueba la conexión a un upsd y muestra los UPS que encuentra.
// EN: Test the connection to an upsd and show the UPS units it finds.
async function testServer(){
  const host=document.getElementById('f-shost').value.trim(),port=parseInt(document.getElementById('f-sport').value)||3493;
  const btn=document.getElementById('btn-test'),res=document.getElementById('test-result');
  if(!host){document.getElementById('f-shost').classList.add('err');return;}
  btn.innerHTML='<span class="spin">⟳</span>';btn.disabled=true;
  try{
    const r=await fetch('api/test',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({host,port})});
    const d=await r.json();
    if(d.ok){res.className='test-result ok show';res.textContent=t('testConnected',d.ups_count,d.version);log('OK','Test OK: '+host+':'+port);}
    else{res.className='test-result fail show';res.textContent='✕ '+d.error;}
  }catch(e){res.className='test-result fail show';res.textContent='✕ '+e.message;}
  finally{btn.textContent=t('addServerTest');btn.disabled=false;}
}

// Guarda el servidor nuevo o el editado.
// EN: Save the new or the edited server.
async function setBatteryDate(sid,upsName,cur){
  const v=window.prompt(t('batAskDate'),cur||new Date().toISOString().slice(0,10));
  if(v===null)return;
  try{
    const r=await fetch('api/battery-date',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({server:sid,ups:upsName,date:v.trim()})});
    const d=await r.json();if(!r.ok)throw new Error(d.error||'HTTP '+r.status);
    toast(t('batDateSaved'),false);fetchAll();
  }catch(e){toast(e.message,true);}
}
async function saveServer(){
  const name=document.getElementById('f-sname').value.trim(),host=document.getElementById('f-shost').value.trim(),port=parseInt(document.getElementById('f-sport').value)||3493;
  const btn=document.getElementById('btn-save-srv');
  [document.getElementById('f-sname'),document.getElementById('f-shost')].forEach(e=>e.classList.remove('err'));
  if(!name){document.getElementById('f-sname').classList.add('err');document.getElementById('f-sname').focus();return;}
  if(!host){document.getElementById('f-shost').classList.add('err');document.getElementById('f-shost').focus();return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const ed=editingSrv;
    const r=await fetch(ed?'api/servers/'+ed:'api/servers',{method:ed?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,host,port})});
    const d=await r.json();if(!r.ok)throw new Error(d.error||'HTTP '+r.status);
    if(ed){log('OK',t('serverEditedLog',name));toast(t('serverEdited',name),false);}
    else{log('OK',t('serverAddedLog',name));toast(t('serverAdded',name),false);}
    closeAddServer();await fetchAll();
    fastRefresh();   // the first poll of a new server takes a few seconds: refresh quickly until its data arrives
  }catch(e){log('ERR',e.message);toast(e.message,true);}
  finally{btn.disabled=false;setServerForm();}
}

// Tras agregar un servidor, repite la descarga cada 1,5 s (hasta ~20 s) hasta que llegue algún dato, en vez de esperar al refresco normal de 5 s.
// EN: After adding a server, repeat the download every 1.5 s (up to ~20 s) until some data arrives, instead of waiting for the normal 5 s refresh.
function fastRefresh(n=13){
  if(n<=0)return;
  setTimeout(async()=>{
    await fetchAll();
    const has=Object.values(allData).some(sn=>sn&&Object.keys(sn.ups||{}).length);
    if(!has)fastRefresh(n-1);
  },1500);
}

// Pausar o reanudar un servidor NUT (solo admin): sin lecturas, eventos ni historial mientras esté pausado.
// EN: Pause or resume a NUT server (admin only): no readings, events or history while paused.
async function pauseServer(btn,sid,paused){
  if(btn)btn.disabled=true;
  try{
    const r=await fetch('api/servers/'+encodeURIComponent(sid)+'/pause',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({paused})});
    const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||'Error');
    toast(t(paused?'pausedOk':'resumedOk',d.server?.name||''),false);await fetchAll();
  }catch(e){toast(e.message,true);if(btn)btn.disabled=false;}
}
// Pide confirmación y borra un servidor (admin).
// EN: Ask for confirmation and delete a server (admin).
function confirmDeleteServer(sid,name){
  document.getElementById('del-msg').textContent=t('deleteServerConfirm',name);
  document.getElementById('del-btn').onclick=async()=>{
    closeModals();
    try{
      const r=await fetch('api/servers/'+sid,{method:'DELETE'});const d=await r.json();if(!r.ok)throw new Error(d.error);
      log('WARN',t('serverDeletedLog',name));toast(t('serverDeleted',name),false);await fetchAll();
    }catch(e){log('ERR',e.message);toast(e.message,true);}
  };
  document.getElementById('del-overlay').classList.add('show');
}

// ── Helpers ───────────────────────────────────────────────────────────────────
// ── Theme ─────────────────────────────────────────────────────────────────────
// Elige el tema (claro, oscuro o automático según el sistema) y lo recuerda (clave pi-theme).
// EN: Choose the theme (light, dark or automatic following the system) and remember it (key pi-theme).
function setTheme(t){
  localStorage.setItem('pi-theme',t);
  applyTheme(t);
  ['light','dark','system'].forEach(x=>{
    document.getElementById('theme-'+x)?.classList.toggle('active',x===t);
  });
}
// Aplica el tema al documento.
// EN: Apply the theme to the document.
function applyTheme(t){
  const pref = t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;
  document.documentElement.setAttribute('data-theme', pref==='dark'?'dark':'light');
}
(()=>{
  const t=localStorage.getItem('pi-theme')||'dark';
  applyTheme(t);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{
    if((localStorage.getItem('pi-theme')||'dark')==='system') applyTheme('system');
  });
  // Set active button after DOM ready
  document.addEventListener('DOMContentLoaded',()=>{
    ['light','dark','system'].forEach(x=>{
      document.getElementById('theme-'+x)?.classList.toggle('active',x===t);
    });
  });
  // Also set immediately for SSR-like case
  setTimeout(()=>{
    ['light','dark','system'].forEach(x=>{
      document.getElementById('theme-'+x)?.classList.toggle('active',x===t);
    });
  },0);
})();

// ── Chart tooltip ─────────────────────────────────────────────────────────────
// Cursor sobre el gráfico: muestra el valor de la muestra más cercana.
// EN: Cursor over the chart: shows the value of the nearest sample.
function closeModals(){document.querySelectorAll('.overlay').forEach(o=>o.classList.remove('show'));}
// Escapa HTML antes de insertar texto de usuarios, equipos o la red en la página: evita inyección de código (XSS).
// EN: Escape HTML before inserting text from users, devices or the network into the page: prevents code injection (XSS).
// Duración en texto corto: 3d 4h, 2h 15m, 7m, 40s / Duration as short text
function fmtDur(sec){sec=Math.max(0,Math.round(sec));const d=Math.floor(sec/86400),h=Math.floor(sec%86400/3600),m=Math.floor(sec%3600/60);
  return d?`${d}d ${h}h`:h?`${h}h ${m}m`:m?`${m}m`:`${sec}s`}
function fmtPct(v){return v==null?'—':(v>=99.995?'100':v.toFixed(v>=99?2:1))+' %'}
// Fila de disponibilidad del UPS (racha en línea, 24h/7d/30d, último corte) / UPS availability row
function availHtml(st){
  if(!st)return'';
  const cell=(k,v,c)=>`<div class="var-cell"><span class="var-key">${k}</span><span class="var-val"${c?` style="color:${c}"`:''}>${v}</span></div>`;
  const a=st.avail||{},L=st.last;
  const streak=st.on_battery?cell(t('avStreak'),t('avOnBatt'),'var(--red)')
    :cell(t('avStreak'),fmtDur(st.streak)+(L?'':' <span style="opacity:.55;font-size:10px" title="'+esc(t('avSince'))+'">*</span>'));
  const lastTxt=L?`${fdt(L.start)} · ${fmtDur(L.dur)}${L.min_charge!=null?' · '+t('avMin')+' '+Math.round(L.min_charge)+'%':''}`:t('avNone');
  return `<div class="vars-section avail">${streak}${cell(t('av24'),fmtPct(a['24h']))}${cell(t('av7'),fmtPct(a['7d']))}${cell(t('av30'),fmtPct(a['30d']))}${cell(t('avCount'),st.count30)}${cell(t('avLast'),esc(lastTxt))}</div>`;
}
// Batería: autonomía estimada, edad, tendencia de capacidad y registro de autotests / battery: estimated runtime, age, capacity trend and self-test log
// Resultados de autotest que informa NUT, en español cuando la interfaz está en español; texto desconocido se deja tal cual.
// EN: Self-test results as NUT reports them, in Spanish when the interface is Spanish; unknown text is left as is.
const TEST_ES={'done and passed':'Aprobado','done and warning':'Terminó con advertencia','done and error':'Terminó con error','aborted':'Cancelado','in progress':'En curso','no test initiated':'Sin prueba','ok':'Aprobado'};
function testTxt(r){const k=String(r||'').trim().toLowerCase();return _lang==='es'&&TEST_ES[k]?TEST_ES[k]:r;}
// Fecha y hora con el formato del idioma (día/mes/año), no el del navegador.
function fdt(ts){return PCT.ls(new Date(ts*1000),_lang==='es'?'es-CL':'en-GB',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'});}
// Energía y estado: banderas del UPS, alarma, margen de apagado y calidad de la red (bajones, subidas y cambios a batería).
// EN: Power & status: UPS flags, alarm, shutdown margin and mains quality (sags, surges and transfers to battery).
function powerHtml(st){
  const p=st&&st.power;if(!p)return'';
  const cell=(k,v,c,tip)=>`<div class="var-cell"${tip?` title="${esc(tip)}"`:''}><span class="var-key">${esc(k)}</span><span class="var-val"${c?` style="color:${c}"`:''}>${v}</span></div>`;
  const col={crit:'var(--red)',warn:'var(--orange)',info:'var(--blue)'};
  const cells=[];
  (p.flags||[]).forEach(f=>cells.push(cell(t('pwFlag_'+f.f),'●',col[f.lv],t('pwFlagTip_'+f.f))));
  if(p.alarm)cells.push(cell(t('pwAlarm'),esc(p.alarm),'var(--orange)'));
  if(p.beeper)cells.push(cell(t('pwBeeper'),esc(t('pwBeep_'+p.beeper))));
  const m=p.margin;
  if(m){const mm=Math.floor(m.margin_s/60),nn=Math.floor(m.need/60);
    cells.push(cell(t('pwMargin'),esc((m.ok?t('pwMarginOk',mm,nn):t('pwMarginBad',mm,nn))+' · '+(m.basis==='full'?t('pwMarginFull'):t('pwMarginNow'))),m.ok?'':'var(--orange)'));}
  const q=p.quality,w=q&&q.w||{},d=w['24h'],wk=w['7d'];
  if(q&&q.nominal&&d&&d.n){
    const tip=t('pwBand',q.lo,q.hi);
    cells.push(cell(t('pwVolt')+' · 24 h',esc(t('pwVoltFmt',Math.round(d.min),Math.round(d.max),q.nominal)),(d.min<q.lo||d.max>q.hi)?'var(--orange)':'',tip));
    [['24h',d],['7d',wk]].forEach(([lab,x])=>{if(!x)return;
      cells.push(cell(t('pwSag')+' · '+(lab==='24h'?'24 h':'7 d'),x.low?String(x.low):esc(t('pwNone')),x.low?'var(--orange)':'',tip));
      cells.push(cell(t('pwSurge')+' · '+(lab==='24h'?'24 h':'7 d'),x.high?String(x.high):esc(t('pwNone')),x.high?'var(--orange)':'',tip));
      cells.push(cell(t('pwXfer')+' · '+(lab==='24h'?'24 h':'7 d'),x.transfers?String(x.transfers):esc(t('pwNone')),x.transfers?'var(--orange)':''));});
  }else if(q&&!q.nominal)cells.push(cell(t('pwVolt'),'<span style="opacity:.55">'+esc(t('pwNeedHist'))+'</span>'));
  if(!cells.length)return'';
  return `<div style="grid-column:1 / -1"><div style="font-size:12px;font-weight:600;margin:8px 0 2px">${esc(t('pwTitle'))}</div><div class="vars-section bat">${cells.join('')}</div></div>`;
}
function batHtml(st,sid,upsName){
  const b=st&&st.battery;if(!b)return'';
  const cell=(k,v,c)=>`<div class="var-cell"><span class="var-key">${esc(k)}</span><span class="var-val"${c?` style="color:${c}"`:''}>${v}</span></div>`;
  const R=b.runtime,cells=[];
  if(R){
    cells.push(cell(t('batRuntime'),fmtDur(R.now_s)));
    cells.push(cell(t('batFull'),'≈ '+fmtDur(R.full_s)));
    if(R.plus50_s)cells.push(cell(t('batPlus50'),'≈ '+fmtDur(R.plus50_s)));
  }
  const btn=canAdmin()?` <button type="button" class="bat-edit" data-on-click="setBatteryDate" data-on-click-args="${jsargs([sid,upsName,b.age_manual||''])}" title="${esc(b.age_manual?t('batSince',b.age_manual)+' · '+t('batSetDateTip'):t('batSetDateTip'))}">✎</button>`:'';
  if(b.age_years!=null)cells.push(cell(t('batAge'),esc(b.age_months!=null?t('batMonths',b.age_months):t('batYears',b.age_years))+btn,b.age_years>=4?'var(--orange)':''));
  else if(canAdmin())cells.push(cell(t('batAge'),'<span style="opacity:.55">'+esc(t('batUnknown'))+'</span>'+btn));
  const A=b.aging;
  cells.push(cell(t('batAging'),A?esc(t('batAgingFmt',A.change_pct,A.weeks)):'<span style="opacity:.55">'+esc(t('batCollecting'))+'</span>',A&&A.warn?'var(--orange)':''));
  if(b.test_now){const kc={passed:'var(--green)',failed:'var(--red)'}[b.test_now.kind]||'';cells.push(cell(t('batTestNow'),esc(testTxt(b.test_now.result))+(b.test_now.ts?` <span style="opacity:.6;font-size:11px">· ${esc(fdt(b.test_now.ts))}</span>`:''),kc));}
  let warn='';
  if(A&&A.warn)warn=`<div style="color:var(--orange);font-size:12px;margin:6px 0 0">⚠ ${esc(t('batAgingWarn'))}</div>`;
  else if(b.age_years!=null&&b.age_years>=4)warn=`<div style="color:var(--orange);font-size:12px;margin:6px 0 0">⚠ ${esc(t('batOldWarn'))}</div>`;
  const tests=(b.tests||[]).length?`<div style="font-size:12px;margin-top:8px"><div style="font-weight:600;margin-bottom:2px">${esc(t('batTests'))}</div>`+
    b.tests.map(x=>`<div style="font-family:var(--mono);font-size:11px;color:${{passed:'var(--green)',failed:'var(--red)'}[x.kind]||'var(--text-mid)'}">${esc(fdt(x.ts))} · ${esc(testTxt(x.result))}</div>`).join('')+'</div>':'';
  return `<div style="grid-column:1 / -1"><div class="vars-section bat">${cells.join('')}</div>${warn}${tests}</div>`;
}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
// Valor seguro dentro de un handler on*="…": literal JS entre comillas, escapado también para HTML.
// Lista de argumentos para data-on-*-args="…" (JSON escapado para HTML).
function jsargs(a){return esc(JSON.stringify(a));}
function updateClock(){const el=document.getElementById('clock');if(el)el.textContent=PCT.time(new Date(),true);}
let _tt;
// Aviso emergente breve (error si isErr).
// EN: Short pop-up notice (error if isErr).
function toast(msg,isErr=false){const el=document.getElementById('toast');el.textContent=msg;el.className=isErr?'err':'';void el.offsetWidth;el.classList.add('show');clearTimeout(_tt);_tt=setTimeout(()=>el.classList.remove('show'),3400);}
// Línea en el registro de actividad de la pantalla.
// EN: Line in the on-screen activity log.
function log(level,msg){const out=document.getElementById('log-out'),ts=PCT.time(new Date(),true);const el=document.createElement('div');el.className='log-row';el.innerHTML='<span class="lt">'+ts+'</span><span class="lv '+level+'">'+level+'</span><span class="lm">'+esc(msg)+'</span>';out.appendChild(el);out.scrollTop=out.scrollHeight;while(out.children.length>80)out.removeChild(out.firstChild);}
function clearLog(){document.getElementById('log-out').innerHTML='';}

document.querySelectorAll('.overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)closeModals();}));
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModals();});

_i18nReady=true;
(async()=>{
  const ok=await checkSession();
  if(ok){applyPermissions();await initApp();document.getElementById('login-screen').style.display='none';}else{document.getElementById('login-screen').style.display='flex';}
})();

// ── Mobile navigation drawer ──
// Menú lateral desplegable en pantallas pequeñas (celular y tablet).
// EN: Slide-out side menu on small screens (phone and tablet).
function toggleNav(force){
  const open=force!==undefined?force:!document.body.classList.contains('nav-open');
  document.body.classList.toggle('nav-open',open);
  const b=document.getElementById('nav-toggle');if(b)b.setAttribute('aria-expanded',open);
}
(function(){
  const sb=document.querySelector('.sidebar');
  if(sb)sb.addEventListener('click',e=>{if(e.target.closest('a,.nav-item,.srv-nav,.btn-add-srv'))setTimeout(()=>toggleNav(false),0);});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')toggleNav(false);});
  window.addEventListener('resize',()=>{if(window.innerWidth>960)toggleNav(false);});
})();

// ───────── Recordarme / Remember me ─────────
// Devuelve la duración elegida ("day","week","month","forever") o "" si no se marcó. Recuerda la última elección en este navegador.
// EN: Returns the chosen duration ("day","week","month","forever") or "" if unchecked. Remembers the last choice in this browser.
function remValue(){const c=document.getElementById('l-rem'),s=document.getElementById('l-remsel');const v=c&&c.checked&&s?s.value:'';try{localStorage.setItem('pi-remember',v)}catch(e){}return v}
(function remInit(){try{const v=localStorage.getItem('pi-remember')||'';const c=document.getElementById('l-rem'),s=document.getElementById('l-remsel');if(c&&s&&['day','week','month','forever'].includes(v)){c.checked=true;s.disabled=false;s.value=v}}catch(e){}})();

// Funciones que el HTML puede invocar con data-on-* (lista cerrada; ver csp-bind.js).
// EN: Functions the HTML may call through data-on-* (closed list; see csp-bind.js).
if (window.cspRegister) cspRegister({ clearLog, closeAddServer, closeModals, confirmDeleteServer, doLogin, exportCSV, logout, openAddServer, openEditServer, pauseServer, saveServer, setBatteryDate, setLang, setTheme, setVChartRange, testServer, toggleNav, toggleVCmp });
