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
    upsSummary:'UPS Summary',
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
    chartTitle_voltage:'Input vs output voltage',
    chartLegend_input:'Input',chartLegend_output:'Output',chartLegend_watts:'Watts',
    chartTitle_power:'Power consumption',chartTitle_temp:'UPS temperature',chartLegend_temp:'Temperature (°C)',
    filterAll:'All',filterActivity:'Activity',filterClear:'Clear',
    noDataChart:'No consumption data for this period',
    accumulating:'Accumulating data…',
    testConnected:(n,v)=>`✓ Connected — ${n} UPS${v?' · '+v:''}`,
    calcVA:'V×A calculated',calcLoad:'VA×load',
    upsCountUnit:(n)=>`${n} UPS`,nodeCountUnit:(n)=>`${n} node${n!==1?'s':''}`,
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
    upsSummary:'Resumen de UPS',
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
    chartTitle_voltage:'Voltaje entrada vs salida',
    chartLegend_input:'Entrada',chartLegend_output:'Salida',chartLegend_watts:'Watts',
    chartTitle_power:'Consumo',chartTitle_temp:'Temperatura de la UPS',chartLegend_temp:'Temperatura (°C)',
    filterAll:'Todo',filterActivity:'Actividad',filterClear:'Limpiar',
    noDataChart:'Sin datos de consumo en este período',
    accumulating:'Acumulando datos…',
    testConnected:(n,v)=>`✓ Conectado — ${n} UPS${v?' · '+v:''}`,
    calcVA:'V×A calculado',calcLoad:'VA×carga',
    upsCountUnit:(n)=>`${n} UPS`,nodeCountUnit:(n)=>`${n} nodo${n!==1?'s':''}`,
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
  _lang=l;localStorage.setItem('pi-lang',l);document.documentElement.lang=l;
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
// Barra lateral común: los mismos accesos en todas las páginas. El usuario puede reordenarlos arrastrando (el orden se guarda en el navegador, clave pi-nav-order). «Admin» solo se muestra a administradores.
// EN: Common sidebar: the same links on every page. The user can reorder them by dragging (the order is stored in the browser, key pi-nav-order). "Admin" is shown to administrators only.
const _NAV_ITEMS=[
  {id:'overview', href:'/overview/', label:'Overview', svg:'<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>'},
  {id:'nut',  href:'/nut/',   label:'UPS Monitor', svg:'<path d="M5 9V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v4"/><rect x="3" y="9" width="18" height="11" rx="2"/><line x1="12" y1="13" x2="12" y2="16"/>'},
  {id:'net',  href:'/net/',   label:'Net Monitor', svg:'<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>'},
  {id:'pve',  href:'/pve/',   label:'Proxmox',     svg:'<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>'},
  {id:'wol',  href:'/wol/',   label:'WOL Console', svg:'<polygon points="13,2 3,14 12,14 11,22 21,10 12,10"/>'},
  {id:'admin',href:'/admin/', label:'Admin Panel', svg:'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',adminOnly:true},
];
// Identificador de esta página en la barra lateral (se marca como activa).
// EN: Identifier of this page in the sidebar (shown as active).
const _NAV_SELF='nut';
let _navDragSrc=null;
// Orden guardado de los accesos; si falta alguno nuevo, se agrega al final.
// EN: Saved order of the links; any new one missing is appended at the end.
function _navOrder(){
  try{const s=JSON.parse(localStorage.getItem('pi-nav-order')||'[]');
    if(s.length){const ids=_NAV_ITEMS.map(i=>i.id);const o=s.filter(id=>ids.includes(id));ids.forEach(id=>{if(!o.includes(id))o.push(id);});return o;}}catch(e){}
  return _NAV_ITEMS.map(i=>i.id);
}
// Dibuja la barra lateral y activa el arrastrar y soltar para reordenar.
// EN: Draw the sidebar and enable drag and drop to reorder.
function renderNav(){
  const wrap=document.getElementById('nav-items');if(!wrap)return;
  const order=_navOrder(),isAdmin=canAdmin();
  wrap.innerHTML='';
  order.forEach(id=>{
    const item=_NAV_ITEMS.find(i=>i.id===id);if(!item)return;
    if(item.adminOnly&&!isAdmin)return;
    const isSelf=item.id===_NAV_SELF;
    const a=document.createElement('a');
    a.className='nav-item nav-drag-item'+(isSelf?' active':'');
    a.href=isSelf?'#':item.href;a.dataset.navId=item.id;a.draggable=true;
    a.innerHTML=`<span class="nav-drag-handle" title="Arrastrar">⠿</span><svg viewBox="0 0 24 24">${item.svg}</svg>${item.label}`;
    a.addEventListener('dragstart',e=>{_navDragSrc=id;e.dataTransfer.effectAllowed='move';a.classList.add('nav-dragging');});
    a.addEventListener('dragend',()=>a.classList.remove('nav-dragging'));
    a.addEventListener('dragover',e=>{e.preventDefault();e.dataTransfer.dropEffect='move';a.classList.add('nav-drag-over');});
    a.addEventListener('dragleave',()=>a.classList.remove('nav-drag-over'));
    a.addEventListener('drop',e=>{
      e.preventDefault();a.classList.remove('nav-drag-over');
      if(_navDragSrc&&_navDragSrc!==id){
        const cur=_navOrder(),from=cur.indexOf(_navDragSrc),to=cur.indexOf(id);
        if(from>-1&&to>-1){cur.splice(from,1);cur.splice(to,0,_navDragSrc);}
        try{localStorage.setItem('pi-nav-order',JSON.stringify(cur));}catch(e){}
        renderNav();
      }
      _navDragSrc=null;
    });
    wrap.appendChild(a);
  });
  const adminEl=wrap.querySelector('[data-nav-id="admin"]');
  if(adminEl)adminEl.id='nav-admin';
}

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
// El refresco automático pide solo el estado actual (range=none, sin historial); el historial de cada gráfico se pide aparte, por rango, y solo cuando ese gráfico lo necesita. Así la Pi no envía un año de datos cada 5 s.
// EN: The automatic refresh asks only for the current state (range=none, no history); each chart's history is requested separately, by range, and only when that chart needs it. This way the Pi does not send a year of data every 5 s.
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
async function fetchAll(){
  try{
    const [r1,r2]=await Promise.all([
      fetch('api/servers?range='+_pollRange),
      fetch('api/ups?range='+_pollRange)
    ]);
    if(r1.status===401||r2.status===401){location.reload();return;}
    servers=(await r1.json()).servers||[];
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
    const dotCls=!snap?'loading':snap.error?'err':snap.last_ok?'ok':'loading';
    const upsCount=snap?Object.keys(snap.ups||{}).length:0;
    const div=document.createElement('div');div.className='srv-nav';
    div.innerHTML=`<span class="srv-dot-sm ${dotCls}"></span>
      <div class="srv-nav-info">
        <div class="srv-nav-top"><div class="srv-nav-name">${esc(s.name)}</div>${canAdmin()?`<span class="srv-acts"><button class="btn-ghost-sm edit" data-on-click="openEditServer" data-on-click-args="${jsargs([s.id])}" title="${t('editServerTitle')}"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg></button><button class="btn-ghost-sm" data-on-click="confirmDeleteServer" data-on-click-args="${jsargs([s.id,s.name])}" title="${t('deleteServerTitle')}"><svg viewBox="0 0 24 24"><polyline points="3,6 5,6 21,6"/><path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6"/></svg></button></span>`:''}</div>
        <div class="srv-nav-host" title="${esc(s.host)}:${s.port}"><span data-nethost="${esc(s.host)}">${esc(s.host)}</span>:${s.port}</div>
        ${upsCount?`<div class="srv-nav-host">${t('upsCountUnit',upsCount)}</div>`:''}
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
    const connecting=servers.some(sv=>{const sn=allData[sv.id];return !sn||(!sn.last_ok&&!sn.error);});
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
        <div class="vars-section">
          ${VARS.map(([k,l,u])=>{const val=row.v[k];return`<div class="var-cell"><span class="var-key">${l}</span><span class="var-val">${val?esc(val)+' '+u:'<span style="opacity:.3">—</span>'}</span></div>`;}).join('')}
        </div>
        ${row.clients.length?`<div class="clients-section">
          <span class="clients-lbl">${t('clientsLabel')}</span>
          <div class="client-chips">${row.clients.map(c=>`<span class="client-chip"><span data-nethost="${esc(c)}" data-nethost-click="1">${esc(c)}</span></span>`).join('')}</div>
        </div>`:''}
        <div class="vchart-section">
          <div class="vchart-header">
            <span class="vchart-title">${t('chartTitle_voltage')}</span>
            <div class="vchart-legend">
              <div class="vchart-legend-item"><div class="vchart-legend-dot" style="background:#4361ee"></div>${t('chartLegend_input')}</div>
              <div class="vchart-legend-item"><div class="vchart-legend-dot" style="background:#22c55e"></div>${t('chartLegend_output')}</div>
            </div>
            <div class="vchart-filters" id="vchart-filters-${key.replace(/[^a-z0-9]/gi,'-')}">
              ${['1h','1d','1mo','all'].map(r=>`<button class="vchart-filter${(vchartRanges[key]||DEFAULT_RANGE)===r?' active':''}" data-range="${r}" data-on-click="setVChartRange" data-on-click-args="${jsargs([{"@":"this"},key,"v"])}">${r==='all'?t('filterAll'):r}</button>`).join('')}
            </div>
          </div>
          <div class="vchart-body" style="position:relative">
            <div class="vchart-tooltip" id="vtooltip-${key.replace(/[^a-z0-9]/gi,'-')}"></div>
            <canvas class="vchart" id="vchart-${key.replace(/[^a-z0-9]/gi,'-')}" height="140"
              data-on-mousemove="onVChartMove" data-on-mousemove-args="${jsargs([{"@":"event"},{"@":"this"},key,"v"])}"
              data-on-mouseleave="onVChartLeave" data-on-mouseleave-args="${jsargs([key,"v"])}"></canvas>
          </div>
        </div>
        <div class="vchart-section">
          <div class="vchart-header">
            <span class="vchart-title">${t('chartTitle_power')}</span>
            <div class="vchart-legend">
              <div class="vchart-legend-item"><div class="vchart-legend-dot" style="background:#f97316"></div>${t('chartLegend_watts')}</div>
            </div>
            <div class="vchart-filters" id="wchart-filters-${key.replace(/[^a-z0-9]/gi,'-')}">
              ${['1h','1d','1mo','all'].map(r=>`<button class="vchart-filter${(wchartRanges[key]||DEFAULT_RANGE)===r?' active':''}" data-range="${r}" data-on-click="setVChartRange" data-on-click-args="${jsargs([{"@":"this"},key,"w"])}">${r==='all'?t('filterAll'):r}</button>`).join('')}
            </div>
          </div>
          <div class="vchart-body" style="position:relative">
            <div class="vchart-tooltip" id="wtooltip-${key.replace(/[^a-z0-9]/gi,'-')}"></div>
            <canvas class="vchart" id="wchart-${key.replace(/[^a-z0-9]/gi,'-')}" height="120"
              data-on-mousemove="onVChartMove" data-on-mousemove-args="${jsargs([{"@":"event"},{"@":"this"},key,"w"])}"
              data-on-mouseleave="onVChartLeave" data-on-mouseleave-args="${jsargs([key,"w"])}"></canvas>
          </div>
        </div>
        ${parseFloat(row.v['ups.temperature']||row.v['battery.temperature']||0)>0?`<div class="vchart-section">
          <div class="vchart-header">
            <span class="vchart-title">${t('chartTitle_temp')}</span>
            <div class="vchart-legend">
              <div class="vchart-legend-item"><div class="vchart-legend-dot" style="background:#ef4444"></div>${t('chartLegend_temp')}</div>
            </div>
            <div class="vchart-filters" id="tchart-filters-${key.replace(/[^a-z0-9]/gi,'-')}">
              ${['1h','1d','1mo','all'].map(r=>`<button class="vchart-filter${(tchartRanges[key]||DEFAULT_RANGE)===r?' active':''}" data-range="${r}" data-on-click="setVChartRange" data-on-click-args="${jsargs([{"@":"this"},key,"t"])}">${r==='all'?t('filterAll'):r}</button>`).join('')}
            </div>
          </div>
          <div class="vchart-body" style="position:relative">
            <div class="vchart-tooltip" id="ttooltip-${key.replace(/[^a-z0-9]/gi,'-')}"></div>
            <canvas class="vchart" id="tchart-${key.replace(/[^a-z0-9]/gi,'-')}" height="120"
              data-on-mousemove="onVChartMove" data-on-mousemove-args="${jsargs([{"@":"event"},{"@":"this"},key,"t"])}"
              data-on-mouseleave="onVChartLeave" data-on-mouseleave-args="${jsargs([key,"t"])}"></canvas>
          </div>
        </div>`:''}
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

// Historial por rango: el servidor devuelve cada rango ya reducido (agrupado por tiempo).
// Cada rango se pide solo cuando algún gráfico lo usa y se vuelve a pedir a su propio
// ritmo: los rangos largos casi no cambian, así que no hace falta releerlos seguido.
const rangeCache = {};   // 'srv/ups|range' -> {ts, rows}
const RANGE_TTL = {'1h':10000, '1d':60000, '1mo':300000, 'all':600000}; // ms
// Pide al servidor el historial de una UPS para un rango, con caché; si la red falla, devuelve lo último que tenía.
// EN: Ask the server for a UPS's history for a range, with cache; if the network fails, it returns the last copy it had.
async function fetchRangeHistory(key, range){
  const ck = key+'|'+range, c = rangeCache[ck];
  if(c && Date.now()-c.ts < (RANGE_TTL[range]||10000)) return c.rows;
  const srv = key.split('/')[0], ups = key.split('/').slice(1).join('/');
  try{
    const r = await fetch('api/history?srv='+encodeURIComponent(srv)+'&ups='+encodeURIComponent(ups)+'&range='+range);
    if(!r.ok) throw new Error('HTTP '+r.status);
    const rows = (await r.json()).history||[];
    rangeCache[ck] = {ts:Date.now(), rows};
    return rows;
  }catch(e){ return c ? c.rows : null; }
}
// Filas ya descargadas para ese rango (null si todavía no llegaron)
// Filas de historial ya cargadas para un gráfico y rango.
// EN: History rows already loaded for a chart and range.
function rangeRows(key, range){
  const c = rangeCache[key+'|'+range];
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
  const id = key.replace(/[^a-z0-9]/gi,'-');
  const vr = vchartRanges[key]||DEFAULT_RANGE, wr = wchartRanges[key]||DEFAULT_RANGE;
  const tr = tchartRanges[key]||DEFAULT_RANGE;
  const vrows = rangeRows(key,vr), wrows = rangeRows(key,wr), trows = rangeRows(key,tr);
  if(vrows) drawVoltageChart('vchart-'+id, vrows, vr);
  if(wrows) drawWattsChart('wchart-'+id, wrows, wr);
  if(trows) drawTempChart('tchart-'+id, trows, tr);
}
// Vuelve a pedir y dibujar los gráficos del rango elegido.
// EN: Request and draw again the charts of the chosen range.
async function refreshRangeCharts(key){
  const ranges = new Set([vchartRanges[key]||DEFAULT_RANGE, wchartRanges[key]||DEFAULT_RANGE, tchartRanges[key]||DEFAULT_RANGE]);
  await Promise.all([...ranges].map(r=>fetchRangeHistory(key, r)));
  drawChartsFor(key);
}

// Cambia el rango de un gráfico (botones 1 h / 1 d / 1 mes / todo).
// EN: Change a chart's range (1 h / 1 d / 1 month / all buttons).
async function setVChartRange(btn, key, type){
  type = type||'v';
  const pfx = type==='w' ? 'wchart' : type==='t' ? 'tchart' : 'vchart';
  const cid = pfx+'-filters-'+key.replace(/[^a-z0-9]/gi,'-');
  document.querySelectorAll('#'+cid+' .vchart-filter').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  const store = type==='w' ? wchartRanges : type==='t' ? tchartRanges : vchartRanges;
  store[key] = btn.dataset.range;
  await fetchRangeHistory(key, store[key]);
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
  const cutoffs = {'1h':3600,'1d':86400,'1mo':2592000};
  const cutoff = cutoffs[range]||0;
  const ref = history[history.length-1].ts;
  return history.filter(p=>p.ts>=(ref-cutoff));
}

// Gráfico de voltaje de entrada y salida dibujado en un canvas (sin librerías), con rejilla, escala automática y cursor.
// EN: Input and output voltage chart drawn on a canvas (no libraries), with grid, automatic scale and cursor.
function drawVoltageChart(canvasId, history, range, hoverIdx=-1){
  const canvas=document.getElementById(canvasId); if(!canvas) return;
  const filtered = filterHistory(history, range||'all');
  const dpr=window.devicePixelRatio||1;
  const W=canvas.offsetWidth||600, H=Math.round(canvas.getBoundingClientRect().height)||140;
  if(canvas.width!==W*dpr||canvas.height!==H*dpr){canvas.width=W*dpr;canvas.height=H*dpr;}
  const ctx=canvas.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,W,H);
  const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
  const cBg=css('--bg')||'#f0f2f5';
  const cBorder=css('--border')||'#e3e8ef';
  const cDim=css('--text-dim')||'#94a3b8';
  const cSurface=css('--surface')||'#fff';
  ctx.fillStyle=cBg; ctx.fillRect(0,0,W,H);

  if(!filtered||filtered.length<2){
    ctx.fillStyle=cDim; ctx.font='11px DM Mono,monospace'; ctx.textAlign='center';
    ctx.fillText(filtered&&filtered.length===1?t('accumulating'):t('noDataChart'),W/2,H/2);
    ctx.scale(1/dpr,1/dpr); return;
  }

  const N=filtered.length;
  const PL=34, PR=30, PT=8, PB=18;
  const W2=W-PL-PR, H2=H-PT-PB;

  // Calcular rango de voltaje con margen
  const allV = filtered.flatMap(p=>[p.vin||0,p.vout||0]).filter(v=>v>0);
  if(!allV.length){ctx.scale(1/dpr,1/dpr);return;}
  const vMin = Math.max(0, Math.floor(Math.min(...allV)-5));
  const vMax = Math.ceil(Math.max(...allV)+5);
  const vRange = vMax-vMin||1;

  const xOf = i=>PL+(i/(N-1))*W2;
  const yOf = v=>PT+H2-((v-vMin)/vRange)*H2;

  // Grid horizontal
  const gridSteps = 4;
  ctx.strokeStyle=cBorder; ctx.lineWidth=0.5;
  ctx.fillStyle=cDim; ctx.font='9px DM Mono,monospace'; ctx.textAlign='right';
  for(let i=0;i<=gridSteps;i++){
    const v=vMin+(vRange/gridSteps)*i;
    const y=yOf(v);
    ctx.beginPath(); ctx.moveTo(PL,y); ctx.lineTo(W-PR,y); ctx.stroke();
    ctx.fillText(Math.round(v)+'V', PL-3, y+3);
  }

  // Área bajo la línea de entrada
  ctx.beginPath();
  filtered.forEach((pt,i)=>{
    const x=xOf(i), y=yOf(pt.vin||vMin);
    i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
  });
  ctx.lineTo(xOf(N-1),PT+H2); ctx.lineTo(PL,PT+H2); ctx.closePath();
  const g1=ctx.createLinearGradient(0,PT,0,PT+H2);
  g1.addColorStop(0,'rgba(67,97,238,.2)'); g1.addColorStop(1,'rgba(67,97,238,0)');
  ctx.fillStyle=g1; ctx.fill();

  // Línea entrada (azul)
  ctx.beginPath();
  filtered.forEach((pt,i)=>{
    const x=xOf(i), y=yOf(pt.vin||vMin);
    i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
  });
  ctx.strokeStyle='#4361ee'; ctx.lineWidth=1.8; ctx.globalAlpha=1; ctx.stroke();

  // Línea salida (verde)
  ctx.beginPath();
  filtered.forEach((pt,i)=>{
    const x=xOf(i), y=yOf(pt.vout||vMin);
    i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
  });
  ctx.strokeStyle='#22c55e'; ctx.lineWidth=1.8; ctx.stroke();

  // Etiquetas X (tiempo)
  ctx.fillStyle=cDim; ctx.font='9px DM Mono,monospace'; ctx.textAlign='center';
  const step=Math.max(1,Math.floor(N/5));
  for(let i=0;i<N;i+=step){
    const d=new Date(filtered[i].ts*1000);
    const label = range==='1mo'?
      d.toLocaleDateString((_lang==='es'?'es-CL':'en-GB'),{day:'2-digit',month:'2-digit'}):
      d.toTimeString().slice(0,5);
    ctx.fillText(label, xOf(i), H-3);
  }

  // Valores actuales en el extremo derecho
  const last=filtered[N-1];
  if(last.vin){
    ctx.fillStyle='#4361ee'; ctx.font='bold 9px DM Mono,monospace'; ctx.textAlign='left';
    ctx.fillText(Math.round(last.vin)+'V', W-PR+4, yOf(last.vin)+3);
  }
  if(last.vout){
    ctx.fillStyle='#22c55e'; ctx.font='bold 9px DM Mono,monospace'; ctx.textAlign='left';
    ctx.fillText(Math.round(last.vout)+'V', W-PR+4, yOf(last.vout)+12);
  }

  // Crosshair
  if(hoverIdx>=0 && hoverIdx<N){
    const cx = xOf(hoverIdx);
    const pt = filtered[hoverIdx];
    // Vertical line
    ctx.beginPath(); ctx.moveTo(cx,PT); ctx.lineTo(cx,PT+H2);
    ctx.strokeStyle='rgba(100,116,139,.4)'; ctx.lineWidth=1; ctx.setLineDash([3,3]); ctx.stroke();
    ctx.setLineDash([]);
    // Dots on lines
    if(pt.vin){
      ctx.beginPath(); ctx.arc(cx,yOf(pt.vin),4,0,2*Math.PI);
      ctx.fillStyle='#4361ee'; ctx.fill();
      ctx.strokeStyle=cSurface; ctx.lineWidth=1.5; ctx.stroke();
    }
    if(pt.vout){
      ctx.beginPath(); ctx.arc(cx,yOf(pt.vout),4,0,2*Math.PI);
      ctx.fillStyle='#22c55e'; ctx.fill();
      ctx.strokeStyle=cSurface; ctx.lineWidth=1.5; ctx.stroke();
    }
  }

  ctx.scale(1/dpr,1/dpr);
}

// Dibujar gráfico de watts (área naranja)
// Gráfico del consumo en vatios (mismo estilo que el de voltaje).
// EN: Power draw chart in watts (same style as the voltage one).
function drawWattsChart(canvasId, history, range, hoverIdx=-1){
  const canvas=document.getElementById(canvasId); if(!canvas) return;
  const filtered = filterHistory(history, range||'all');
  const dpr=window.devicePixelRatio||1;
  const W=canvas.offsetWidth||600, H=Math.round(canvas.getBoundingClientRect().height)||120;
  if(canvas.width!==W*dpr||canvas.height!==H*dpr){canvas.width=W*dpr;canvas.height=H*dpr;}
  const ctx=canvas.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,W,H);
  const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
  const cBg=css('--bg')||'#f0f2f5';
  const cBorder=css('--border')||'#e3e8ef';
  const cDim=css('--text-dim')||'#94a3b8';
  const cSurface=css('--surface')||'#fff';
  ctx.fillStyle=cBg; ctx.fillRect(0,0,W,H);

  const withWatts = filtered ? filtered.filter(p=>p.watts>0) : [];
  if(!filtered||filtered.length<2||!withWatts.length){
    ctx.fillStyle=cDim; ctx.font='11px DM Mono,monospace'; ctx.textAlign='center';
    ctx.fillText(t('noDataChart'),W/2,H/2);
    ctx.scale(1/dpr,1/dpr); return;
  }

  const N=filtered.length;
  const PL=40, PR=36, PT=8, PB=18;
  const W2=W-PL-PR, H2=H-PT-PB;

  const allW = filtered.map(p=>p.watts||0);
  const wMax = Math.ceil(Math.max(...allW)*1.15)||10;
  const wMin = 0;
  const wRange = wMax-wMin||1;

  const xOf = i=>PL+(i/(N-1))*W2;
  const yOf = v=>PT+H2-((v-wMin)/wRange)*H2;

  // Grid
  const gridSteps=4;
  ctx.strokeStyle=cBorder; ctx.lineWidth=0.5;
  ctx.fillStyle=cDim; ctx.font='9px DM Mono,monospace'; ctx.textAlign='right';
  for(let i=0;i<=gridSteps;i++){
    const v=wMin+(wRange/gridSteps)*i;
    const y=yOf(v);
    ctx.beginPath(); ctx.moveTo(PL,y); ctx.lineTo(W-PR,y); ctx.stroke();
    ctx.fillText(Math.round(v)+'W', PL-3, y+3);
  }

  // Área rellena naranja
  ctx.beginPath();
  filtered.forEach((pt,i)=>{
    const x=xOf(i), y=yOf(pt.watts||0);
    i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
  });
  ctx.lineTo(xOf(N-1),PT+H2); ctx.lineTo(PL,PT+H2); ctx.closePath();
  const g=ctx.createLinearGradient(0,PT,0,PT+H2);
  g.addColorStop(0,'rgba(249,115,22,.35)'); g.addColorStop(1,'rgba(249,115,22,0)');
  ctx.fillStyle=g; ctx.fill();

  // Línea naranja
  ctx.beginPath();
  filtered.forEach((pt,i)=>{
    const x=xOf(i), y=yOf(pt.watts||0);
    i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
  });
  ctx.strokeStyle='#f97316'; ctx.lineWidth=2; ctx.stroke();

  // Etiquetas X
  ctx.fillStyle=cDim; ctx.font='9px DM Mono,monospace'; ctx.textAlign='center';
  const step=Math.max(1,Math.floor(N/5));
  for(let i=0;i<N;i+=step){
    const d=new Date(filtered[i].ts*1000);
    const label=range==='1mo'?
      d.toLocaleDateString((_lang==='es'?'es-CL':'en-GB'),{day:'2-digit',month:'2-digit'}):
      d.toTimeString().slice(0,5);
    ctx.fillText(label, xOf(i), H-3);
  }

  // Último valor
  const last=filtered[N-1];
  if(last.watts){
    ctx.fillStyle='#f97316'; ctx.font='bold 9px DM Mono,monospace'; ctx.textAlign='left';
    ctx.fillText(Math.round(last.watts)+'W', W-PR+4, yOf(last.watts)+3);
  }

  // Crosshair
  if(hoverIdx>=0 && hoverIdx<N){
    const cx=xOf(hoverIdx), pt=filtered[hoverIdx];
    ctx.beginPath(); ctx.moveTo(cx,PT); ctx.lineTo(cx,PT+H2);
    ctx.strokeStyle='rgba(100,116,139,.4)'; ctx.lineWidth=1; ctx.setLineDash([3,3]); ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath(); ctx.arc(cx,yOf(pt.watts||0),4,0,2*Math.PI);
    ctx.fillStyle='#f97316'; ctx.fill();
    ctx.strokeStyle=cSurface; ctx.lineWidth=1.5; ctx.stroke();
  }
  ctx.scale(1/dpr,1/dpr);
}

// Gráfico de la temperatura de la UPS (solo aparece si la UPS informa temperatura; NUT guarda 0 cuando no la tiene).
// EN: UPS temperature chart (it only appears if the UPS reports a temperature; NUT stores 0 when it has none).
function drawTempChart(canvasId, history, range, hoverIdx=-1){
  const canvas=document.getElementById(canvasId); if(!canvas) return;
  const filtered = filterHistory(history, range||'all');
  const dpr=window.devicePixelRatio||1;
  const W=canvas.offsetWidth||600, H=Math.round(canvas.getBoundingClientRect().height)||120;
  if(canvas.width!==W*dpr||canvas.height!==H*dpr){canvas.width=W*dpr;canvas.height=H*dpr;}
  const ctx=canvas.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,W,H);
  const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
  const cBg=css('--bg')||'#f0f2f5', cBorder=css('--border')||'#e3e8ef', cDim=css('--text-dim')||'#94a3b8', cSurface=css('--surface')||'#fff';
  ctx.fillStyle=cBg; ctx.fillRect(0,0,W,H);
  const temps = filtered ? filtered.map(p=>p.temp).filter(v=>v>0) : [];
  if(!filtered||filtered.length<2||!temps.length){
    ctx.fillStyle=cDim; ctx.font='11px DM Mono,monospace'; ctx.textAlign='center';
    ctx.fillText(filtered&&filtered.length===1?t('accumulating'):t('noDataChart'),W/2,H/2);
    ctx.scale(1/dpr,1/dpr); return;
  }
  const N=filtered.length, PL=34, PR=30, PT=8, PB=18, W2=W-PL-PR, H2=H-PT-PB;
  const tMin=Math.floor(Math.min(...temps)-2), tMax=Math.max(Math.ceil(Math.max(...temps)+2), tMin+6), tRange=tMax-tMin||1;
  const xOf=i=>PL+(i/(N-1))*W2, yOf=v=>PT+H2-((v-tMin)/tRange)*H2;
  const gridSteps=4;
  ctx.strokeStyle=cBorder; ctx.lineWidth=0.5; ctx.fillStyle=cDim; ctx.font='9px DM Mono,monospace'; ctx.textAlign='right';
  for(let i=0;i<=gridSteps;i++){
    const v=tMin+(tRange/gridSteps)*i, y=yOf(v);
    ctx.beginPath(); ctx.moveTo(PL,y); ctx.lineTo(W-PR,y); ctx.stroke();
    ctx.fillText(Math.round(v)+'°', PL-3, y+3);
  }
  // Línea: se corta donde no hay lectura (temp = 0) / the line breaks where there is no reading (temp = 0)
  ctx.beginPath(); let pen=false;
  filtered.forEach((pt,i)=>{
    if(!(pt.temp>0)){pen=false;return;}
    const x=xOf(i), y=yOf(pt.temp);
    pen?ctx.lineTo(x,y):ctx.moveTo(x,y); pen=true;
  });
  ctx.strokeStyle='#ef4444'; ctx.lineWidth=1.8; ctx.stroke();
  ctx.fillStyle=cDim; ctx.font='9px DM Mono,monospace'; ctx.textAlign='center';
  const step=Math.max(1,Math.floor(N/5));
  for(let i=0;i<N;i+=step){
    const d=new Date(filtered[i].ts*1000);
    const label=range==='1mo'?
      d.toLocaleDateString((_lang==='es'?'es-CL':'en-GB'),{day:'2-digit',month:'2-digit'}):
      d.toTimeString().slice(0,5);
    ctx.fillText(label, xOf(i), H-3);
  }
  const last=filtered[N-1];
  if(last.temp>0){
    ctx.fillStyle='#ef4444'; ctx.font='bold 9px DM Mono,monospace'; ctx.textAlign='left';
    ctx.fillText(parseFloat(last.temp).toFixed(0)+'°', W-PR+4, yOf(last.temp)+3);
  }
  if(hoverIdx>=0 && hoverIdx<N && filtered[hoverIdx].temp>0){
    const cx=xOf(hoverIdx), pt=filtered[hoverIdx];
    ctx.beginPath(); ctx.moveTo(cx,PT); ctx.lineTo(cx,PT+H2);
    ctx.strokeStyle='rgba(100,116,139,.4)'; ctx.lineWidth=1; ctx.setLineDash([3,3]); ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath(); ctx.arc(cx,yOf(pt.temp),4,0,2*Math.PI);
    ctx.fillStyle='#ef4444'; ctx.fill(); ctx.strokeStyle=cSurface; ctx.lineWidth=1.5; ctx.stroke();
  }
  ctx.scale(1/dpr,1/dpr);
}

// Dibujar ambos gráficos al expandir detalle
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
  const t=localStorage.getItem('pi-theme')||'system';
  applyTheme(t);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{
    if((localStorage.getItem('pi-theme')||'system')==='system') applyTheme('system');
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
function onVChartMove(e, canvas, key, type){
  type = type||'v';
  const tipId = (type==='w'?'wtooltip-':type==='t'?'ttooltip-':'vtooltip-')+key.replace(/[^a-z0-9]/gi,'-');
  const tip = document.getElementById(tipId);
  if(!tip) return;
  const snap = allData[key.split('/')[0]];
  if(!snap) return;
  const upsName = key.split('/').slice(1).join('/');
  const range = type==='w' ? (wchartRanges[key]||DEFAULT_RANGE) : type==='t' ? (tchartRanges[key]||DEFAULT_RANGE) : (vchartRanges[key]||DEFAULT_RANGE);
  const history = filterHistory(rangeRows(key, range)||[], range);
  if(!history||history.length<2){tip.className='vchart-tooltip';return;}

  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const W = canvas.offsetWidth;
  const PL = type==='w'?40:34, PR = type==='w'?36:30;
  const W2 = W-PL-PR;
  const N = history.length;

  const idx = Math.max(0, Math.min(N-1, Math.round(((mouseX-PL)/W2)*(N-1))));
  const pt = history[idx];
  if(!pt){tip.className='vchart-tooltip';return;}

  const d = new Date(pt.ts*1000);
  const timeStr = d.toLocaleString((_lang==='es'?'es-CL':'en-GB'),{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});

  if(type==='t'){
    tip.innerHTML = `<div style="color:var(--text-dim);margin-bottom:4px;font-size:10px">${timeStr}</div>`+
      `<div style="color:#ef4444">🌡 ${t('gaugeLabel_temp')}: <strong>${pt.temp>0?parseFloat(pt.temp).toFixed(1)+' °C':'—'}</strong></div>`;
  } else if(type==='w'){
    tip.innerHTML = `<div style="color:var(--text-dim);margin-bottom:4px;font-size:10px">${timeStr}</div>`+
      `<div style="color:#f97316">⚡ ${t('gaugeLabel_power')}: <strong>${pt.watts!=null?Math.round(pt.watts)+' W':'—'}</strong></div>`+
      (pt.load?`<div style="color:var(--text-mid)">${t('gaugeLabel_load')}: ${Math.round(pt.load)}%</div>`:'');
  } else {
    tip.innerHTML = `<div style="color:var(--text-dim);margin-bottom:4px;font-size:10px">${timeStr}</div>`+
      (pt.vin?`<div style="color:#4361ee">↓ ${t('chartLegend_input')}: <strong>${parseFloat(pt.vin).toFixed(1)} V</strong></div>`:'') +
      (pt.vout?`<div style="color:#22c55e">↑ ${t('chartLegend_output')}: <strong>${parseFloat(pt.vout).toFixed(1)} V</strong></div>`:'') +
      (pt.charge?`<div style="color:var(--text-mid)">🔋 ${t('gaugeLabel_battery')}: ${Math.round(pt.charge)}%</div>`:'');
  }

  const tipW = 170;
  let left = mouseX + 12;
  if(left + tipW > W) left = mouseX - tipW - 8;
  tip.style.left = left+'px';
  tip.style.top = '4px';
  tip.className = 'vchart-tooltip show';

  if(type==='t') drawTempChart('tchart-'+key.replace(/[^a-z0-9]/gi,'-'), history, range, idx);
  else if(type==='w') drawWattsChart('wchart-'+key.replace(/[^a-z0-9]/gi,'-'), history, range, idx);
  else           drawVoltageChart('vchart-'+key.replace(/[^a-z0-9]/gi,'-'), history, range, idx);
}

function onVChartLeave(key, type){
  type = type||'v';
  const tipId = (type==='w'?'wtooltip-':type==='t'?'ttooltip-':'vtooltip-')+key.replace(/[^a-z0-9]/gi,'-');
  const tip = document.getElementById(tipId);
  if(tip) tip.className='vchart-tooltip';
  const snap = allData[key.split('/')[0]];
  if(!snap) return;
  const upsName = key.split('/').slice(1).join('/');
  const range = type==='w' ? (wchartRanges[key]||DEFAULT_RANGE) : type==='t' ? (tchartRanges[key]||DEFAULT_RANGE) : (vchartRanges[key]||DEFAULT_RANGE);
  const history = filterHistory(rangeRows(key, range)||[], range);
  if(type==='t') drawTempChart('tchart-'+key.replace(/[^a-z0-9]/gi,'-'), history, range, -1);
  else if(type==='w') drawWattsChart('wchart-'+key.replace(/[^a-z0-9]/gi,'-'), history, range, -1);
  else           drawVoltageChart('vchart-'+key.replace(/[^a-z0-9]/gi,'-'), history, range, -1);
}

function closeModals(){document.querySelectorAll('.overlay').forEach(o=>o.classList.remove('show'));}
// Escapa HTML antes de insertar texto de usuarios, equipos o la red en la página: evita inyección de código (XSS).
// EN: Escape HTML before inserting text from users, devices or the network into the page: prevents code injection (XSS).
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
// Valor seguro dentro de un handler on*="…": literal JS entre comillas, escapado también para HTML.
function jsa(s){return esc(JSON.stringify(String(s)));}
// Lista de argumentos para data-on-*-args="…" (JSON escapado para HTML).
function jsargs(a){return esc(JSON.stringify(a));}
function updateClock(){const el=document.getElementById('clock');if(el)el.textContent=new Date().toTimeString().slice(0,8);}
let _tt;
// Aviso emergente breve (error si isErr).
// EN: Short pop-up notice (error if isErr).
function toast(msg,isErr=false){const el=document.getElementById('toast');el.textContent=msg;el.className=isErr?'err':'';void el.offsetWidth;el.classList.add('show');clearTimeout(_tt);_tt=setTimeout(()=>el.classList.remove('show'),3400);}
// Línea en el registro de actividad de la pantalla.
// EN: Line in the on-screen activity log.
function log(level,msg){const out=document.getElementById('log-out'),ts=new Date().toTimeString().slice(0,8);const el=document.createElement('div');el.className='log-row';el.innerHTML='<span class="lt">'+ts+'</span><span class="lv '+level+'">'+level+'</span><span class="lm">'+esc(msg)+'</span>';out.appendChild(el);out.scrollTop=out.scrollHeight;while(out.children.length>80)out.removeChild(out.firstChild);}
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
