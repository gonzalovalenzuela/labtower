const LANG={
  en:{loginTitle:'Sign in',loginSub:'Enter your credentials to continue.',
    username:'Username',password:'Password',loginBtn:'Sign in',loginFill:'Fill in all fields',aliasPrompt:(ip)=>'Alias for '+ip+':',aliasSaved:'Alias updated',autoScanToast:'Auto-scan: ',autoScanLbl:'Auto-scan:',rememberMe:'Remember me',rem1d:'1 day',rem1w:'1 week',rem1m:'1 month',remForever:'Forever',
    navSection:'Navigation',osDetected:'Detected OS',
    netTitle:'Network Monitor',themeLight:'Light',themeDark:'Dark',
    apply:'Apply',scanNet:'Scan network',
    statDiscovered:'Hosts discovered',statOnline:'Online',statOffline:'Offline',
    statOpenPorts:'Open ports',statLastScan:'Last scan',
    filterAll:'All',filterOnline:'Online',filterOffline:'Offline',
    hostsTitle:'Hosts on network',
    colOpenPorts:'Open ports',colLastSeen:'Last seen',colLatency:'Latency',colStatus:'Status',
    cancel:'Cancel',save:'Save',saveConnect:'Save & connect',
    scanningNet:'Scanning network...',
    permReadonly:'Read-only',permExecute:'Execute',permAdmin:'Administrator',
    sessionExpired:'Session expired',
    noHosts:'No hosts found',searchPlaceholder:'IP, hostname, OS, port...',
    piholeIntegration:'Pi-hole Integration',piholeDesc:'Pi-hole v6 API for name resolution and MAC vendor. Credentials are stored on the server.',
    piholeHosts:'Pi-hole hosts (comma separated)',piholePass:'Pi-hole admin password',
    piholeConnected:'Connected',piholeConnecting:'Connecting…',piholeNeedHost:'Enter at least one host',
    piholeSuccess:'Saved — syncing names…',piholeToast:'Pi-hole connected — names will appear on next scan',
    intervalNegative:'Interval cannot be negative',intervalMin:'Minimum 60 seconds (or 0 for manual)',
    scanning:'Scanning…',scanStarted:(msg)=>`Scan started — ${msg}`,rescanHost:(ip)=>`Re-scanning ${ip}`,
    scanProgress:(p,t)=>`Scanning ${p}/${t} hosts…`,scanBtn:'Scan network',
    noResults:'No results',noHosts2:'No hosts discovered',filterHint:'Try a different filter.',
    startScanHint:'Start a scan to discover hosts on the network.',
    initialScanNet:(n)=>`Nothing has been scanned yet. Network detected: ${n}`,initialScanBtn:'Run initial scan',
    uptimeEmpty:'No events recorded yet',uptimeStats:(h,d)=>`${h} monitored · ${d} outage${d!==1?'s':''}`,
    availHistory:'Availability history',
    chartMonitoring:'Monitoring — data will appear after several scans',
    snmpTitle:'SNMP source',snmpDesc:'Reads the ARP table of a switch or router to get MAC addresses (and vendor) for hosts the server cannot see directly. Requires the snmp package on the server.',snmpMissing:'snmpwalk is not installed — run: apt install snmp',snmpEnable:'Use SNMP during scans',snmpHost:'Switch / router IP',snmpPort:'Port',snmpVersion:'Version',snmpTimeout:'Timeout (s)',snmpCommunity:'Community',snmpUser:'Username',snmpLevel:'Security level',snmpAuthProto:'Auth',snmpAuthPass:'Auth password',snmpPrivProto:'Privacy',snmpPrivPass:'Privacy password',snmpTest:'Test',snmpTesting:'Testing…',snmpSaved:'SNMP settings saved',snmpEntries:'ARP entries found',snmpKeep:'unchanged',snmpLast:'Last scan',ouiTitle:'MAC vendor database',ouiDesc:'Wireshark manuf list, downloaded weekly (ieee-data is used as fallback).',ouiAuto:'Update weekly',ouiUpdate:'Update now',ouiUpdating:'Downloading…',ouiPrefixes:'prefixes',ouiNever:'not downloaded yet',ouiDone:'Vendor database updated',osUnknown:'Unknown',colType:'Type',deviceTypes:'Device type',editDevice:'Edit device',fieldType:'Device type',fieldOs:'Operating system',autoDetect:'Auto-detect',saved:'Device updated',tComputer:'Computer',tRouter:'Router',tSwitch:'Switch',tAp:'Access point',tStorage:'Storage / NAS',tPhone:'Phone',tTv:'TV',tCamera:'Camera',tAppliance:'Appliance',tPrinter:'Printer',tTablet:'Tablet',tConsole:'Game Console',tServer:'Server',tVoip:'IP Phone',tUps:'UPS',tSpeaker:'Smart Speaker',tOther:'Other',newDevice:'NEW',delHost:'Delete host',delConfirm:(n,ip)=>`Delete "${n}" (${ip}) from Net Monitor?\n\nIf it is still connected, the next scan will discover it again.`,delDone:'Host deleted',
    newDeviceMsg:(n,names,more)=>`${n} new device${n>1?'s':''} detected: ${names}${more?' and more':''}`,
    osEditTitle:'Edit OS',unitSec:'sec',titleSeconds:'Seconds',titleMinutes:'Minutes',titleLogout:'Sign out',titleDrag:'Drag',every:'every',manual:'manual',autoOff:'disabled (manual)',detailInfo:'Information',seen:'Seen',discovered:'Discovered',noOpenPortsDetected:'No open ports detected',ago:x=>x+' ago',},
  es:{loginTitle:'Iniciar sesión',loginSub:'Ingresa tus credenciales para continuar.',
    username:'Usuario',password:'Contraseña',loginBtn:'Entrar',loginFill:'Completa todos los campos',aliasPrompt:(ip)=>'Alias para '+ip+':',aliasSaved:'Alias actualizado',autoScanToast:'Escaneo automático: ',autoScanLbl:'Escaneo automático:',rememberMe:'Recordarme',rem1d:'1 día',rem1w:'1 semana',rem1m:'1 mes',remForever:'Siempre',
    navSection:'Navegación',osDetected:'OS detectado',
    netTitle:'Monitoreo de red',themeLight:'Claro',themeDark:'Oscuro',
    apply:'Aplicar',scanNet:'Escanear red',
    statDiscovered:'Hosts descubiertos',statOnline:'En línea',statOffline:'Sin conexión',
    statOpenPorts:'Puertos abiertos',statLastScan:'Último escaneo',
    filterAll:'Todos',filterOnline:'En línea',filterOffline:'Sin conexión',
    hostsTitle:'Hosts en la red',
    colOpenPorts:'Puertos abiertos',colLastSeen:'Último contacto',colLatency:'Latencia',colStatus:'Estado',
    cancel:'Cancelar',save:'Guardar',saveConnect:'Guardar y conectar',
    scanningNet:'Escaneando red...',
    permReadonly:'Solo lectura',permExecute:'Ejecución',permAdmin:'Administrador',
    sessionExpired:'Sesión expirada',
    noHosts:'Sin hosts encontrados',searchPlaceholder:'IP, hostname, OS, puerto...',
    piholeIntegration:'Integración Pi-hole',piholeDesc:'Pi-hole v6 API para resolución de nombres y vendor MAC. Las credenciales se guardan en el servidor.',
    piholeHosts:'Hosts Pi-hole (separados por coma)',piholePass:'Password Pi-hole admin',
    piholeConnected:'Conectado',piholeConnecting:'Conectando…',piholeNeedHost:'Ingresa al menos un host',
    piholeSuccess:'Guardado — sincronizando nombres…',piholeToast:'Pi-hole conectado — los nombres aparecerán en el próximo escaneo',
    intervalNegative:'El intervalo no puede ser negativo',intervalMin:'Mínimo 60 segundos (o 0 para manual)',
    scanning:'Escaneando…',scanStarted:(msg)=>`Escaneo iniciado — ${msg}`,rescanHost:(ip)=>`Re-escaneando ${ip}`,
    scanProgress:(p,tt)=>`Escaneando ${p}/${tt} hosts…`,scanBtn:'Escanear red',
    noResults:'Sin resultados',noHosts2:'Sin hosts descubiertos',filterHint:'Prueba otro filtro.',
    startScanHint:'Inicia un escaneo para descubrir hosts en la red.',
    initialScanNet:(n)=>`Aún no se ha escaneado nada. Red detectada: ${n}`,initialScanBtn:'Hacer escaneo inicial',
    uptimeEmpty:'Sin eventos registrados aún',uptimeStats:(h,d)=>`${h} monitoreado · ${d} caída${d!==1?'s':''}`,
    availHistory:'Historial de disponibilidad',
    chartMonitoring:'Monitoreando — los datos aparecerán tras varios escaneos',
    snmpTitle:'Fuente SNMP',snmpDesc:'Lee la tabla ARP de un switch o router para obtener MAC (y fabricante) de equipos que el servidor no ve directamente. Requiere el paquete snmp en el servidor.',snmpMissing:'snmpwalk no está instalado — ejecuta: apt install snmp',snmpEnable:'Usar SNMP en los escaneos',snmpHost:'IP del switch / router',snmpPort:'Puerto',snmpVersion:'Versión',snmpTimeout:'Tiempo de espera (s)',snmpCommunity:'Comunidad',snmpUser:'Usuario',snmpLevel:'Nivel de seguridad',snmpAuthProto:'Auth',snmpAuthPass:'Password auth',snmpPrivProto:'Privacidad',snmpPrivPass:'Password privacidad',snmpTest:'Probar',snmpTesting:'Probando…',snmpSaved:'Configuración SNMP guardada',snmpEntries:'entradas ARP encontradas',snmpKeep:'sin cambios',snmpLast:'Último escaneo',ouiTitle:'Base de datos de vendors MAC',ouiDesc:'Lista manuf de Wireshark, descargada cada semana (ieee-data como respaldo).',ouiAuto:'Actualizar cada semana',ouiUpdate:'Actualizar ahora',ouiUpdating:'Descargando…',ouiPrefixes:'prefijos',ouiNever:'aún no descargada',ouiDone:'Base de vendors actualizada',osUnknown:'Desconocido',colType:'Tipo',deviceTypes:'Tipo de dispositivo',editDevice:'Editar dispositivo',fieldType:'Tipo de dispositivo',fieldOs:'Sistema operativo',autoDetect:'Detección automática',saved:'Dispositivo actualizado',tComputer:'Equipo',tRouter:'Router',tSwitch:'Switch',tAp:'Punto de acceso',tStorage:'Almacenamiento / NAS',tPhone:'Teléfono',tTv:'TV',tCamera:'Cámara',tAppliance:'Electrodoméstico',tPrinter:'Impresora',tTablet:'Tablet',tConsole:'Consola de juegos',tServer:'Servidor',tVoip:'Teléfono IP',tUps:'UPS',tSpeaker:'Altavoz inteligente',tOther:'Otro',newDevice:'NUEVO',delHost:'Eliminar equipo',delConfirm:(n,ip)=>`¿Eliminar "${n}" (${ip}) de Net Monitor?\n\nSi sigue conectado, el próximo escaneo lo volverá a descubrir.`,delDone:'Equipo eliminado',
    newDeviceMsg:(n,names,more)=>`${n} nuevo${n>1?'s dispositivos':'dispositivo'} detectado${n>1?'s':''}: ${names}${more?' y más':''}`,
    osEditTitle:'Editar OS',unitSec:'seg',titleSeconds:'Segundos',titleMinutes:'Minutos',titleLogout:'Cerrar sesión',titleDrag:'Arrastrar',every:'cada',manual:'manual',autoOff:'desactivado (manual)',detailInfo:'Información',seen:'Visto',discovered:'Descubierto',noOpenPortsDetected:'Sin puertos abiertos detectados',ago:x=>'hace '+x,}
};
let _lang=localStorage.getItem('pi-lang')||'en';
var _i18nReady=false;
// Traducción: busca la clave en el idioma activo (admite textos con función para incluir valores).
// EN: Translation: looks the key up in the active language (supports function texts that take values).
function t(k,...args){const v=(LANG[_lang]||LANG.en)[k]||(LANG.en)[k]||k;return typeof v==='function'?v(...args):v;}
// Tipos de dispositivo y su ícono/color. devType() cae en «other» si el servidor envía un tipo que esta página no conoce.
// EN: Device types and their icon/color. devType() falls back to "other" if the server sends a type this page does not know.
const DEVICE_TYPES=['computer','phone','router','switch','ap','storage','tv','camera','appliance','printer','tablet','console','server','voip','ups','speaker','other'];
const TYPE_META={computer:{icon:'💻',key:'tComputer',color:'#4361ee'},router:{icon:'🌐',key:'tRouter',color:'#f4a261'},
  switch:{icon:'🔀',key:'tSwitch',color:'#2a9d8f'},ap:{icon:'📡',key:'tAp',color:'#9b5de5'},
  storage:{icon:'🗄️',key:'tStorage',color:'#e76f51'},phone:{icon:'📱',key:'tPhone',color:'#06b6d4'},
  tv:{icon:'📺',key:'tTv',color:'#e63946'},camera:{icon:'📷',key:'tCamera',color:'#6c757d'},appliance:{icon:'🏠',key:'tAppliance',color:'#d4a017'},printer:{icon:'🖨️',key:'tPrinter',color:'#7b2cbf'},tablet:{icon:'📲',key:'tTablet',color:'#2a9d8f'},console:{icon:'🎮',key:'tConsole',color:'#e11d48'},server:{icon:'🖥️',key:'tServer',color:'#0ea5e9'},voip:{icon:'☎️',key:'tVoip',color:'#4d7c0f'},ups:{icon:'🔋',key:'tUps',color:'#f59e0b'},speaker:{icon:'🔊',key:'tSpeaker',color:'#a855f7'},other:{icon:'❔',key:'tOther',color:'#8d99ae'}};
const devType=h=>TYPE_META[h.device_type]?h.device_type:'other';
const tType=ty=>t(TYPE_META[ty].key);
// El servidor guarda «Desconocido» en español; aquí se muestra traducido al idioma de la página.
// EN: The server stores "Desconocido" in Spanish; here it is shown translated to the page language.
function tOs(os){return os==='Desconocido'||os==='Unknown'?t('osUnknown'):os;}
// Cambia el idioma, lo recuerda y vuelve a pintar los textos de la página.
// EN: Switch the language, remember it and repaint the page texts.
function setLang(l){
  _lang=l;localStorage.setItem('pi-lang',l);document.documentElement.lang=l;
  document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=t(el.getAttribute('data-i18n')));
  document.querySelectorAll('[data-i18n-title]').forEach(el=>el.title=t(el.getAttribute('data-i18n-title')));
  const si=document.getElementById('search-input');
  if(si)si.placeholder=t('searchPlaceholder');
  ['en','es'].forEach(x=>document.getElementById('lang-'+x)?.classList.toggle('active',x===l));
  if(_i18nReady && typeof renderTable==='function' && hosts.length){renderOsFilters();renderTable();}
}
(()=>setLang(_lang))();

// Estado: sesión, equipos, filtros activos, búsqueda y equipo expandido.
// EN: State: session, devices, active filters, search and expanded device.
// Enlace profundo desde otras páginas: /net/?ip=192.168.0.10 abre ese equipo expandido.
// EN: Deep link from other pages: /net/?ip=192.168.0.10 opens that device expanded.
let _deepIp=(()=>{try{const v=new URLSearchParams(location.search).get('ip')||'';return /^\d{1,3}(\.\d{1,3}){3}$/.test(v)?v:null}catch(e){return null}})();
let ME=null, scanNetwork='', scanRunning=false, hosts=[], filterOs='ALL', filterType='ALL', filterStatus='ALL', searchQ='', expanded=null, pollTimer=null;
let sortKeyName=null, sortDir=1;   // null = orden por defecto (online primero, luego IP)
try{const sv=JSON.parse(localStorage.getItem('pi-net-sort')||'null');if(sv&&['status','ip','os','vendor','ports','latency','seen'].includes(sv.k)){sortKeyName=sv.k;sortDir=sv.d===-1?-1:1;}}catch(e){}
// Refresco en reposo cada 30 s; durante un escaneo baja a 3 s para mostrar el progreso (ver fetchData).
// EN: Idle refresh every 30 s; during a scan it drops to 3 s to show progress (see fetchData).
const POLL=30000;
let _lastDataHash='', _currentPoll=POLL;

// Color e ícono de cada sistema operativo para las etiquetas.
// EN: Color and icon of each operating system for the badges.
const OS_COLORS={Windows:'#0078d4',Linux:'#f97316',macOS:'#8b5cf6',iOS:'#22c55e',IoT:'#eab308',Android:'#ef4444',BSD:'#14b8a6',Desconocido:'#94a3b8'};
const OS_ICONS={Windows:'🪟',Linux:'🐧',macOS:'🍎',iOS:'📱',IoT:'🔌',Android:'🤖',BSD:'😈',Desconocido:'❓'};

// ── Theme ────────────────────────────────────────────────────────────────────
// Elige el tema (claro, oscuro o automático según el sistema) y lo recuerda (clave pi-theme).
// EN: Choose the theme (light, dark or automatic following the system) and remember it (key pi-theme).
function setTheme(t){localStorage.setItem('pi-theme',t);applyTheme(t);['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));}
// Aplica el tema al documento.
// EN: Apply the theme to the document.
function applyTheme(t){const p=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;document.documentElement.setAttribute('data-theme',p==='dark'?'dark':'light');}
(()=>{const t=localStorage.getItem('pi-theme')||'dark';applyTheme(t);window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if((localStorage.getItem('pi-theme')||'dark')==='system')applyTheme('system');});setTimeout(()=>{['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===(localStorage.getItem('pi-theme')||'dark')));},0);})();

// ── Nav reordenable ───────────────────────────────────────────────────────────
// ¿Puede editar equipos y cambiar la configuración? (nivel «admin» de Net).
// EN: Can it edit devices and change the configuration? (Net "admin" level).
function canAdmin(){return ME&&ME.permissions?.net==='admin';}
// Escanear la red requiere nivel «execute» o superior (un usuario de solo lectura no puede lanzar escaneos).
// EN: Scanning the network requires the "execute" level or higher (a read-only user cannot start scans).
function canScan(){const l=ME&&ME.permissions?.net;return l==='execute'||l==='admin';}
// Barra lateral común: los mismos accesos en todas las páginas. El usuario puede reordenarlos arrastrando (el orden se guarda en el navegador, clave pi-nav-order). «Admin» solo se muestra a administradores.
// EN: Common sidebar: the same links on every page. The user can reorder them by dragging (the order is stored in the browser, key pi-nav-order). "Admin" is shown to administrators only.
const _NAV_ITEMS=[
  {id:'overview', href:'/overview/', get label(){return _lang==='es'?'Resumen':'Overview'}, svg:'<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>'},
  {id:'nut',  href:'/nut/',   label:'UPS Monitor', svg:'<path d="M5 9V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v4"/><rect x="3" y="9" width="18" height="11" rx="2"/><line x1="12" y1="13" x2="12" y2="16"/>'},
  {id:'net',  href:'/net/',   label:'Net Monitor', svg:'<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>'},
  {id:'pve',  href:'/pve/',   label:'Proxmox',     svg:'<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>'},
  {id:'nas',  href:'/nas/',   label:'NAS Monitor',svg:'<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="7" y1="9" x2="17" y2="9"/><line x1="7" y1="14" x2="17" y2="14"/><line x1="16" y1="18" x2="16.01" y2="18"/>'},
  {id:'dns',  href:'/dns/',   label:'DNS Monitor', svg:'<circle cx="12" cy="12" r="9"/><line x1="3" y1="12" x2="21" y2="12"/><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z"/>'},
  {id:'wan',  href:'/wan/',   label:'WAN Monitor', svg:'<path d="M5 12.55a11 11 0 0 1 14 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/>'},
  {id:'wol',  href:'/wol/',   label:'WOL Console', svg:'<polygon points="13,2 3,14 12,14 11,22 21,10 12,10"/>'},
  {id:'admin',href:'/admin/', label:'Admin Panel', svg:'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',adminOnly:true},
];
// Identificador de esta página en la barra lateral (se marca como activa).
// EN: Identifier of this page in the sidebar (shown as active).
const _NAV_SELF='net';
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
    a.innerHTML=`<span class="nav-drag-handle" title="${esc(t('titleDrag'))}">⠿</span><svg viewBox="0 0 24 24">${item.svg}</svg>${item.label}`;
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

// ── Login ────────────────────────────────────────────────────────────────────
document.getElementById('l-pass').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
// Inicio de sesión. La cookie la fija el servidor (HttpOnly): el JavaScript nunca guarda el token.
// EN: Login. The cookie is set by the server (HttpOnly): the JavaScript never stores the token.
async function doLogin(){
  const btn=document.getElementById('btn-l'),err=document.getElementById('login-err');
  const u=document.getElementById('l-user').value.trim(),p=document.getElementById('l-pass').value;
  err.className='login-err';
  if(!u||!p){err.textContent=t('loginFill');err.className='login-err show';return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const r=await fetch('api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p,remember:remValue()})});
    const d=await r.json();
    if(!r.ok||!d.ok){err.textContent=d.error||'Credenciales incorrectas';err.className='login-err show';return;}
    // Cuenta con contraseña por cambiar (admin/admin inicial): se va a la pantalla obligatoria antes de entrar.
    // EN: Account with a password to change (initial admin/admin): go to the mandatory screen before entering.
    if(d.must_change_password){location.href='/admin/change-password?next='+encodeURIComponent(location.pathname);return;}
    ME=d;applyPermissions();await initApp();
    const ls=document.getElementById('login-screen');ls.style.opacity='0';setTimeout(()=>ls.style.display='none',150);
  }catch(e){err.textContent='Error: '+e.message;err.className='login-err show';}
  finally{btn.disabled=false;btn.textContent=t('loginBtn');}
}
// Pregunta al servidor quién es el usuario; sin sesión o sin acceso a Net devuelve false y se muestra el login.
// EN: Ask the server who the user is; without a session or without Net access it returns false and the login is shown.
async function checkSession(){
  try{const r=await fetch('api/me');if(!r.ok)return false;const d=await r.json();if(!d.username)return false;ME=d;return true;}catch{return false;}
}
// Muestra nombre y rol y oculta los controles de administración a quien no es admin.
// EN: Show name and role and hide the admin controls from non-admins.
function applyPermissions(){
  const _un=String(ME.username||'?');
  document.getElementById('me-name').textContent=_un;
  document.getElementById('avatar').textContent=_un[0].toUpperCase();
  const _permKey={readonly:'permReadonly',execute:'permExecute',admin:'permAdmin'}[ME.permissions?.net];
  document.getElementById('me-role').textContent=_permKey?t(_permKey):'—';
  const _bs=document.getElementById('btn-scan');if(_bs)_bs.style.display=canScan()?'':'none';
  renderNav();
}
// Cierra la sesión en el servidor y recarga la página.
// EN: Close the session on the server and reload the page.
async function logout(){await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.reload();}

// ── Init ─────────────────────────────────────────────────────────────────────
// Arranque tras iniciar sesión: carga la configuración, los equipos y programa el refresco.
// EN: Startup after login: load the configuration and devices and schedule the refresh.
async function initApp(){
  updateClock();setInterval(updateClock,1000);
  document.getElementById('search-input').addEventListener('input',e=>{searchQ=e.target.value.trim().toLowerCase();renderTable();});
  // Cargar intervalo actual desde backend
  try{
    const cfg = await fetch('api/config').then(r=>r.json());
    if(cfg.scan_interval !== undefined) loadIntervalFields(cfg.scan_interval);
    scanNetwork=cfg.network||'';
  }catch(e){}
  await fetchData();
  pollTimer=setInterval(fetchData,POLL);
  setInterval(updateNextScan, 5000);
}

// Muestra el intervalo de escaneo guardado como número + unidad (minutos, horas…).
// EN: Show the stored scan interval as number + unit (minutes, hours…).
function loadIntervalFields(secs){
  const min = Math.floor(secs / 60);
  const sec = secs % 60;
  const mEl = document.getElementById('iv-min');
  const sEl = document.getElementById('iv-sec');
  if(mEl) mEl.value = min;
  if(sEl) sEl.value = sec;
  updateNextScan();
}

// Texto «próximo escaneo en…» calculado con la hora del último escaneo.
// EN: "Next scan in…" text computed from the last scan time.
function updateNextScan(){
  const el = document.getElementById('iv-next');
  if(!el) return;
  const secs = getIntervalSecs();
  if(secs === 0){ el.textContent = '('+t('manual')+')'; return; }
  el.textContent = t('every') + ' ' + fmtInterval(secs);
}

// Lee el campo de intervalo y lo convierte a segundos.
// EN: Read the interval field and convert it to seconds.
function getIntervalSecs(){
  const min = parseInt(document.getElementById('iv-min')?.value||0)||0;
  const sec = parseInt(document.getElementById('iv-sec')?.value||0)||0;
  return min*60 + sec;
}

// Segundos a texto legible.
// EN: Seconds to readable text.
function fmtInterval(secs){
  if(secs === 0) return t('manual');
  if(secs < 60)  return secs+'s';
  if(secs < 3600) return Math.floor(secs/60)+'m '+(secs%60?secs%60+'s':'');
  const h = Math.floor(secs/3600), m = Math.floor((secs%3600)/60);
  return h+'h'+(m?' '+m+'m':'');
}

// Guarda el nuevo intervalo en el servidor (mínimo 60 s; 0 = solo manual).
// EN: Save the new interval on the server (minimum 60 s; 0 = manual only).
async function applyInterval(){
  const secs = getIntervalSecs();
  if(secs < 0){ toast(t('intervalNegative'), true); return; }
  if(secs > 0 && secs < 60){ toast(t('intervalMin'), true); return; }
  try{
    const r = await fetch('api/scan/interval',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({interval: secs})
    });
    const d = await r.json();
    if(!r.ok) throw new Error(d.error);
    const label = secs===0 ? t('autoOff') : t('every')+' '+fmtInterval(secs);
    toast(t('autoScanToast')+label);
    updateNextScan();
  }catch(e){ toast(e.message, true); }
}

// Enter en los campos aplica
document.addEventListener('DOMContentLoaded',()=>{
  ['iv-min','iv-sec'].forEach(id=>{
    document.getElementById(id)?.addEventListener('keydown', e=>{
      if(e.key==='Enter') applyInterval();
    });
    document.getElementById(id)?.addEventListener('input', updateNextScan);
  });
});

// Descarga los equipos y el estado del escaneo. Durante un escaneo consulta cada 3 s y en reposo cada 30 s. Solo repinta si algo cambió realmente (quickHash), para no parpadear ni gastar CPU.
// EN: Download the devices and scan state. During a scan it polls every 3 s and at rest every 30 s. It repaints only if something really changed (quickHash), to avoid flicker and wasted CPU.
async function fetchData(){
  try{
    const r=await fetch('api/hosts');
    if(r.status===401){location.reload();return;}
    const d=await r.json();

    updateScanBar(d.scan);
    if(d.pihole_enabled !== undefined) updatePiholeStatusDot(d.pihole_enabled);
    refreshSnmpDot();

    // Durante escaneo activo: poll cada 3s; en reposo: cada 30s
    const targetPoll = d.scan?.running ? 3000 : 30000;
    if(targetPoll !== _currentPoll){
      _currentPoll = targetPoll;
      clearInterval(pollTimer);
      pollTimer = setInterval(fetchData, targetPoll);
    }

    // Solo re-renderizar tabla si los datos cambiaron
    const newHash = quickHash(d.hosts||[], d.scan);
    if(newHash !== _lastDataHash){
      _lastDataHash = newHash;
      hosts = d.hosts||[];
      renderOsFilters();
      renderStats(d.scan);
      if(_deepIp){const dh=hosts.find(x=>x.ip===_deepIp);_deepIp=null;if(dh){expanded=dh.ip;filterOs='ALL';filterType='ALL';filterStatus='ALL';searchQ='';renderOsFilters();renderTable();requestAnimationFrame(()=>{const r=document.querySelector('tr.expanded');if(r)r.scrollIntoView({block:'center'})});return}}
      renderTable();
    }
  }catch(e){console.error(e);}
}

// Huella barata de lo que se ve en pantalla; si no cambia entre dos consultas no hay que repintar.
// EN: Cheap fingerprint of what is on screen; if it does not change between two queries there is nothing to repaint.
function quickHash(hosts, scan){
  // Hash liviano: IPs online + conteo de puertos + estado del scan
  const onlineKey = hosts.filter(h=>h.online).map(h=>h.ip+h.ports?.length+h.os+h.device_type).sort().join('|');
  const metaKey   = hosts.map(h=>h.ip+h.online+h.os+h.device_type+h.type_manual+h.alias).join('|');
  const scanKey   = scan?.running+':'+scan?.progress+':'+scan?.finished;
  return onlineKey + '||' + metaKey + '||' + scanKey;
}

// ── Scan ─────────────────────────────────────────────────────────────────────
// Pide al servidor un escaneo completo de la red.
// EN: Ask the server for a full network scan.
async function startScan(){
  if(!canScan())return;
  const btn=document.getElementById('btn-scan');
  btn.disabled=true;btn.innerHTML=`<span class="spin">⟳</span> ${t('scanning')}`;
  try{
    const r=await fetch('api/scan/start',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    const d=await r.json();
    if(!r.ok)throw new Error(d.error);
    toast(t('scanStarted',d.message));
    // Mismo efecto inmediato venga el clic del botón superior o del «escaneo inicial»: barra de progreso, botón ocupado y lista vacía en «Escaneando…» sin esperar a la primera consulta de estado.
    // EN: Same immediate effect whether the click comes from the top button or the "initial scan" one: progress bar, busy button and the empty list showing "Scanning…" without waiting for the first status poll.
    updateScanBar({running:true,progress:0,total:0});
    setTimeout(fetchData,600);   // show progress right away and switch to the fast poll (3 s) while scanning
  }catch(e){toast(e.message,true);btn.disabled=false;btn.innerHTML=`<svg viewBox="0 0 24 24" style="width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> ${t('scanBtn')}`;}
}

// Reescanea una sola IP (botón en la fila del equipo).
// EN: Rescan a single IP (button in the device row).

// Elimina un equipo de la lista (solo admin de Net Monitor). Si sigue conectado, el próximo escaneo lo vuelve a descubrir.
// EN: Remove a host from the list (Net Monitor admins only). If it is still connected, the next scan discovers it again.
async function deleteHost(ip){
  if(!canAdmin())return;
  const h=(typeof hosts!=='undefined'?hosts:[]).find(x=>x.ip===ip);
  const name=(h&&(h.alias||h.hostname))||ip;
  if(!confirm(t('delConfirm',name,ip)))return;
  try{
    const r=await fetch('api/hosts/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ip})});
    const d=await r.json().catch(()=>({}));
    if(!r.ok)throw new Error(d.error||('HTTP '+r.status));
    if(expanded===ip)expanded=null;
    toast(t('delDone'));
    await fetchData();
  }catch(e){toast(e.message,true);}
}

async function rescanHost(ip){
  if(!canScan())return;
  try{
    const r=await fetch('api/scan/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ip})});
    const d=await r.json();
    if(!r.ok)throw new Error(d.error);
    toast(t('rescanHost',ip));
  }catch(e){toast(e.message,true);}
}

// Barra de progreso del escaneo en curso.
// EN: Progress bar of the scan in progress.
function updateScanBar(scan){
  if(!scan)return;
  const wasRunning=scanRunning; scanRunning=!!scan.running;
  if(wasRunning!==scanRunning&&!hosts.length)renderTable();   // refresh the empty-state offer
  const bar=document.getElementById('scan-bar');
  const btn=document.getElementById('btn-scan');
  if(scan.running){
    bar.className='scan-bar show';
    const pct=scan.total>0?Math.round((scan.progress/scan.total)*100):0;
    document.getElementById('scan-fill').style.width=pct+'%';
    document.getElementById('scan-pct').textContent=pct+'%';
    document.getElementById('scan-text').textContent=t('scanProgress',scan.progress,scan.total);
    btn.disabled=true;btn.innerHTML=`<span class="spin">⟳</span> ${t('scanning')}`;
  }else{
    bar.className='scan-bar';
    btn.disabled=false;
    btn.innerHTML='<svg viewBox="0 0 24 24" style="width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> '+t('scanBtn');
  }
}

// ── Filters ───────────────────────────────────────────────────────────────────
// Filtros por tipo, sistema operativo y estado (en línea / fuera de línea). Se combinan entre sí y con la búsqueda.
// EN: Filters by type, operating system and status (online / offline). They combine with each other and with the search.
function setTypeFilter(el){
  document.querySelectorAll('.os-filter[data-type]').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
  filterType=el.dataset.type;
  renderTable();
}
function setOsFilter(el){
  document.querySelectorAll('.os-filter[data-os]').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
  filterOs=el.dataset.os;
  renderTable();
}
function setStatusFilter(el){
  document.querySelectorAll('.pill').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
  filterStatus=el.dataset.status;
  renderTable();
}

// Aplica todos los filtros y la búsqueda a la lista de equipos.
// EN: Apply all the filters and the search to the device list.
function filtered(){
  return hosts.filter(h=>{
    if(filterOs!=='ALL'&&h.os!==filterOs)return false;
    if(filterType!=='ALL'&&devType(h)!==filterType)return false;
    if(filterStatus==='online'&&!h.online)return false;
    if(filterStatus==='offline'&&h.online)return false;
    if(searchQ){
      const hay=(h.ip+' '+(h.hostname||'')+' '+(h.alias||'')+' '+h.os+' '+tType(devType(h))+' '+(h.vendor||'')+' '+(h.mac||'')+' '+(h.ports||[]).map(p=>p.port+' '+p.service).join(' ')).toLowerCase();
      if(!hay.includes(searchQ))return false;
    }
    return true;
  }).sort(compareHosts);
}

// ── Ordenamiento ─────────────────────────────────────────────
// Ordenamiento: las IP se comparan numéricamente (rellenando cada número a 3 dígitos), no como texto. Sin columna elegida: en línea primero y luego por IP.
// EN: Sorting: IPs are compared numerically (padding each number to 3 digits), not as text. With no column chosen: online first and then by IP.
const ipKey=ip=>String(ip).split('.').map(n=>n.padStart(3,'0')).join('');
const SORT_VALUE={
  status: h=>h.online?0:1,
  ip:     h=>ipKey(h.ip),
  type:   h=>tType(devType(h)).toLowerCase(),
  os:     h=>tOs(h.os||'Desconocido').toLowerCase(),
  vendor: h=>(h.vendor||h.mac||'').toLowerCase(),
  ports:  h=>(h.ports||[]).length,
  latency:h=>h.online&&h.latency?h.latency:null,   // sin dato (offline / sin respuesta) va al final
  seen:   h=>h.last_seen||null,
};
// Compara dos equipos según la columna activa.
// EN: Compare two devices according to the active column.
function compareHosts(a,b){
  if(!sortKeyName){          // por defecto: online primero, luego IP
    if(a.online!==b.online)return a.online?-1:1;
    return ipKey(a.ip).localeCompare(ipKey(b.ip));
  }
  const va=SORT_VALUE[sortKeyName](a), vb=SORT_VALUE[sortKeyName](b);
  const ea=va===null||va==='', eb=vb===null||vb==='';
  if(ea!==eb)return ea?1:-1;                       // vacíos siempre al final, en ambos sentidos
  if(!ea){
    const c=typeof va==='number'?va-vb:String(va).localeCompare(String(vb),undefined,{numeric:true});
    if(c)return c*sortDir;
  }
  return ipKey(a.ip).localeCompare(ipKey(b.ip));   // desempate estable por IP
}
function updateSortHeaders(){
  document.querySelectorAll('thead th.sortable').forEach(th=>{
    const on=th.dataset.sort===sortKeyName;
    th.setAttribute('aria-sort',on?(sortDir===1?'ascending':'descending'):'none');
  });
}
// Clic en la misma columna: ascendente → descendente → orden por defecto
function setSort(k){
  if(sortKeyName!==k){sortKeyName=k;sortDir=1;}
  else if(sortDir===1){sortDir=-1;}
  else{sortKeyName=null;sortDir=1;}
  try{if(sortKeyName)localStorage.setItem('pi-net-sort',JSON.stringify({k:sortKeyName,d:sortDir}));else localStorage.removeItem('pi-net-sort');}catch(e){}
  updateSortHeaders();renderTable();
}
function sortKey(e,k){if(e.key==='Enter'||e.key===' '){e.preventDefault();setSort(k);}}

// ── Render ────────────────────────────────────────────────────────────────────
// Dibuja los filtros con el conteo de equipos de cada tipo.
// EN: Draw the filters with the count of devices of each type.
function renderTypeFilters(){
  const c=document.getElementById('type-filters');if(!c)return;
  const counts={ALL:hosts.length};
  hosts.forEach(h=>{const k=devType(h);counts[k]=(counts[k]||0)+1;});
  let html=`<div class="os-filter${filterType==='ALL'?' active':''}" data-type="ALL" data-on-click="setTypeFilter" data-on-click-args="[{&quot;@&quot;:&quot;this&quot;}]">
    <span class="os-dot" style="background:var(--teal)"></span><span class="os-filter-name">${esc(t('filterAll'))}</span>
    <span class="os-count">${counts.ALL}</span></div>`;
  DEVICE_TYPES.forEach(k=>{
    if(!counts[k])return;
    html+=`<div class="os-filter${filterType===k?' active':''}" data-type="${esc(k)}" data-on-click="setTypeFilter" data-on-click-args="[{&quot;@&quot;:&quot;this&quot;}]">
      <span class="os-dot" style="background:${TYPE_META[k].color}"></span><span class="os-filter-name">${esc(tType(k))}</span>
      <span class="os-count">${counts[k]}</span></div>`;
  });
  c.innerHTML=html;
}
function renderOsFilters(){
  renderTypeFilters();
  const counts={ALL:0};
  hosts.forEach(h=>{
    const os=h.os||'Desconocido';
    counts[os]=(counts[os]||0)+1;
    counts.ALL++;
  });
  const container=document.getElementById('os-filters');
  // Update ALL count
  const allEl=container.querySelector('[data-os="ALL"] .os-count');
  if(allEl)allEl.textContent=counts.ALL;

  // OS entries
  const osList=Object.keys(counts).filter(k=>k!=='ALL');
  osList.sort((a,b)=>(counts[b]||0)-(counts[a]||0));
  // Remove existing OS filters
  container.querySelectorAll('[data-os]:not([data-os="ALL"])').forEach(e=>e.remove());
  osList.forEach(os=>{
    if(!counts[os])return;
    const div=document.createElement('div');
    div.className='os-filter'+(filterOs===os?' active':'');
    div.dataset.os=os;
    div.onclick=()=>setOsFilter(div);
    div.innerHTML=`<span class="os-dot dot-${cssId(os)}"></span>
      <span class="os-filter-name">${esc(tOs(os))}</span>
      <span class="os-count">${counts[os]}</span>`;
    container.appendChild(div);
  });
}

// Contadores de la cabecera: total, en línea, fuera de línea, nuevos y estado del último escaneo.
// EN: Header counters: total, online, offline, new and state of the last scan.
function renderStats(scan){
  const online=hosts.filter(h=>h.online).length;
  const offline=hosts.filter(h=>!h.online).length;
  const totalPorts=hosts.reduce((n,h)=>n+(h.ports||[]).length,0);
  document.getElementById('st-total').textContent=hosts.length||'—';
  document.getElementById('st-online').textContent=online||'—';
  document.getElementById('st-offline').textContent=offline||'—';
  document.getElementById('st-ports').textContent=totalPorts||'—';
  if(scan?.finished){
    const d=new Date(scan.finished*1000);
    document.getElementById('st-last-scan').textContent=PCT.time(d);
  }else{
    document.getElementById('st-last-scan').textContent='—';
  }
}

// Dibuja la tabla de equipos y, si hay uno expandido, su detalle (puertos, historial de conexión, edición). Todo texto de la red pasa por esc().
// EN: Draw the device table and, if one is expanded, its detail (ports, connection history, editing). All network text goes through esc().
function renderTable(){
  const tbody=document.getElementById('hosts-tbody');
  const list=filtered();
  document.getElementById('host-count').textContent=list.length===hosts.length?hosts.length+' hosts':list.length+' / '+hosts.length+' hosts';

  if(!list.length){
    tbody.innerHTML=`<tr><td colspan="9"><div class="empty-state">
      <strong>${hosts.length?t('noResults'):(scanRunning?t('scanning'):t('noHosts2'))}</strong>
      ${hosts.length?t('filterHint'):(scanRunning?'':t('startScanHint'))}
      ${(!hosts.length&&!scanRunning&&canScan())?`<div class="empty-offer">${scanNetwork?`<div class="empty-net">${esc(t('initialScanNet',scanNetwork))}</div>`:''}<button class="btn-scan" data-on-click="startScan">${esc(t('initialScanBtn'))}</button></div>`:''}
    </div></td></tr>`;
    return;
  }

  const newTbody=document.createElement('tbody');
  newTbody.id='hosts-tbody';

  // Detectar nuevos dispositivos
  const newDevices = list.filter(h=>h.new_device);
  const netBanner = document.getElementById('net-new-banner');
  if(netBanner && newDevices.length){
    const names = newDevices.slice(0,3).map(h=>h.alias||h.hostname||h.ip).join(', ');
    document.getElementById('net-new-msg').textContent = t('newDeviceMsg',newDevices.length,names,newDevices.length>3);
    netBanner.style.display='flex';
  }

  list.forEach((h,i)=>{
    const isExp=expanded===h.ip;
    const os=h.os||'Desconocido';
    const name=h.alias||h.hostname||h.ip;
    const sub=h.alias?h.hostname||h.ip:h.ip;
    const topPorts=(h.ports||[]).slice(0,4);
    const extraPorts=(h.ports||[]).length-4;

    // Main row
    const tr=document.createElement('tr');
    tr.className=isExp?'expanded':'';
    tr.style.animationDelay=i*15+'ms';
    tr.onclick=()=>{expanded=expanded===h.ip?null:h.ip;renderTable();};
    tr.innerHTML=`
      <td><span class="status-dot ${h.online?'online':'offline'}"></span></td>
      <td>
        <span class="host-name">${esc(name)}</span>
        ${sub!==name?`<span class="host-sub">${esc(sub)}</span>`:''}
        ${h.wol?`<span title="WOL Console" style="margin-left:5px;font-size:9px;font-weight:700;padding:1px 5px;border-radius:99px;background:rgba(42,157,143,.15);color:var(--teal);vertical-align:middle">WOL</span>`:''}
        ${h.new_device?`<span style="margin-left:5px;font-size:9px;font-weight:700;padding:1px 5px;border-radius:99px;background:rgba(67,97,238,.15);color:var(--blue);vertical-align:middle">${t('newDevice')}</span>`:''}
      </td>
      <td data-on-click="@stop">
        <span class="os-badge" style="cursor:pointer" data-on-click="editOs" data-on-click-args="${jsargs([h.ip])}" title="${esc(t('editDevice'))}">
          <span style="font-size:12px">${TYPE_META[devType(h)].icon}</span>
          <span style="font-size:11px;font-weight:600;color:${TYPE_META[devType(h)].color}">${esc(tType(devType(h)))}</span>
        </span>${h.type_manual?'<span class="os-manual-badge">manual</span>':''}
      </td>
      <td data-on-click="@stop">
        <div style="display:flex;align-items:center;gap:4px">
          <span class="os-badge">
            <span style="font-size:12px">${OS_ICONS[os]||'❓'}</span>
            <span class="os-${cssId(os)}" style="font-size:11px;font-weight:600">${esc(tOs(os))}</span>
          </span>
          ${h.os_manual?'<span class="os-manual-badge">manual</span>':''}
          <button data-on-click="editOs" data-on-click-args="${jsargs([h.ip])}" title="${esc(t('editDevice'))}"
            style="background:none;border:none;cursor:pointer;color:var(--text-dim);font-size:11px;padding:2px 4px;border-radius:4px;transition:color .15s"
            data-on-mouseover="@style" data-on-mouseover-args="[{&quot;color&quot;:&quot;var(--teal)&quot;}]" data-on-mouseout="@style" data-on-mouseout-args="[{&quot;color&quot;:&quot;var(--text-dim)&quot;}]">✎</button>
        </div>
      </td>
      <td style="font-size:11px;color:var(--text-dim);font-family:var(--mono)">${h.vendor?`<div>${esc(h.vendor)}</div>`:''}${h.mac?`<div style="${h.vendor?'font-size:10px;opacity:.75':''}">${esc(h.mac)}</div>`:''}${!h.vendor&&!h.mac?'—':''}</td>
      <td>
        <div class="port-chips">
          ${topPorts.map(p=>`<span class="port-chip known" title="${esc(p.service)}">${p.port}</span>`).join('')}
          ${extraPorts>0?`<span class="port-chip">+${extraPorts}</span>`:''}
          ${!h.ports?.length?'<span style="color:var(--text-dim);font-size:11px">—</span>':''}
        </div>
      </td>
      <td style="font-family:var(--mono);font-size:11px;color:${(h.latency||0)>100?'var(--orange)':(h.latency||0)>200?'var(--red)':'var(--text-mid)'}">${h.online&&h.latency?h.latency+'ms':'<span style="color:var(--border-b)">—</span>'}</td>
      <td class="last-seen">${h.last_seen?relTime(h.last_seen*1000):'—'}</td>
      <td style="white-space:nowrap">${canAdmin()?`<button class="btn-trash" data-on-click="deleteHost" data-on-click-args="${jsargs([h.ip])}" data-on-click-stop="1" title="${esc(t('delHost'))}" aria-label="${esc(t('delHost'))}"><svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg></button>`:''}<span class="expand-arrow ${isExp?'open':''}">▶</span></td>`;
    newTbody.appendChild(tr);

    // Detail row
    const dtr=document.createElement('tr');
    dtr.className='detail-row'+(isExp?' show':'');
    const allPorts=h.ports||[];
    dtr.innerHTML=`<td colspan="9" class="detail-cell">
      <div class="detail-inner">
        <div class="detail-section">
          <div class="detail-label">${esc(t('detailInfo'))}</div>
          <div class="detail-value">IP: ${esc(h.ip)}</div>
          ${h.hostname?`<div class="detail-value">Host: ${esc(h.hostname)}</div>`:''}
          ${h.vendor?`<div class="detail-value">Vendor: ${esc(h.vendor)}</div>`:''}${h.mac?`<div class="detail-value">MAC: ${esc(h.mac)}</div>`:''}
          ${h.os_raw?`<div class="detail-value" style="color:var(--text-dim);font-size:10px">${esc(h.os_raw)}</div>`:''}
          <div class="detail-value" style="margin-top:6px">
            <button class="btn-rescan"${canScan()?'':' style="display:none"'} data-on-click="rescanHost" data-on-click-args="${jsargs([h.ip])}" data-on-click-stop="1">
              <svg style="width:11px;height:11px;stroke:currentColor;fill:none;stroke-width:2" viewBox="0 0 24 24"><polyline points="23,4 23,10 17,10"/><path d="M20.49,15a9,9,0,1,1-2.12-9.36L23,10"/></svg>
              Re-escanear
            </button>
            <button class="btn-edit-host" data-on-click="editAlias" data-on-click-args="${jsargs([h.ip])}" data-on-click-stop="1">✎ Alias</button>
          </div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Tiempos</div>
          <div class="detail-value">${esc(t('seen'))}: ${h.last_seen?PCT.ls(new Date(h.last_seen*1000),_lang==='es'?'es-CL':'en-GB'):'—'}</div>
          <div class="detail-value">${esc(t('discovered'))}: ${h.first_seen?new Date(h.first_seen*1000).toLocaleDateString(_lang==='es'?'es-CL':'en-GB'):'—'}</div>
          <div class="detail-value" style="margin-top:4px">${esc(t("colStatus"))}: <span style="color:${h.online?'var(--green)':'var(--text-dim)'};font-weight:600">${h.online?'Online':'Offline'}</span></div>
          ${h.latency?`<div class="detail-value">${esc(t("colLatency"))}: <span style="font-family:var(--mono);font-weight:600">${h.latency} ms</span></div>`:''}
          ${(()=>{
            const hist=h.uptime_history||[];
            if(!hist.length) return '';
            const now=Date.now()/1000;
            let upTime=0, totalTime=0;
            for(let i=0;i<hist.length-1;i++){
              const dur=hist[i+1].ts-hist[i].ts;
              totalTime+=dur;
              if(hist[i].event==='up') upTime+=dur;
            }
            if(totalTime<60) return '';
            const pct=Math.round((upTime/totalTime)*100);
            const color=pct>=99?'var(--green)':pct>=95?'var(--yellow)':'var(--red)';
            return '<div class="detail-value">Uptime: <span style="font-family:var(--mono);font-weight:700;color:'+color+'">'+pct+'%</span></div>';
          })()}
        </div>
        <div class="detail-section" style="grid-column:1/-1">
          <div class="detail-label">${allPorts.length} puertos abiertos</div>
          ${allPorts.length?`<div class="ports-full">
            ${allPorts.map(p=>`<div class="port-full">
              <span class="port-full-num">${p.port}</span>
              <span class="port-full-svc">${esc(p.service||'unknown')}</span>
            </div>`).join('')}
          </div>`:`<div style="font-size:12px;color:var(--text-dim)">${esc(t('noOpenPortsDetected'))}</div>`}
        </div>
        <div class="detail-section" style="grid-column:1/-1">
          <div class="detail-label" style="margin-bottom:6px" data-i18n="availHistory">Availability history</div>
          <div style="position:relative">
            <canvas id="uptime-${esc(h.ip.replace(/\./g,'-'))}" height="40"
              style="width:100%;height:40px;display:block;border-radius:var(--r-sm);background:var(--bg);border:1px solid var(--border)"></canvas>
            <div id="uptime-tip-${esc(h.ip.replace(/\./g,'-'))}"
              style="position:absolute;top:4px;right:8px;font-size:10px;font-family:var(--mono);color:var(--text-dim)">
              ${(()=>{
                const hist = h.uptime_history||[];
                if(!hist.length) return t('uptimeEmpty');
                const now=Date.now()/1000;
                const since=hist[0]?.ts||now;
                const hrs=Math.round((now-since)/3600);
                const downs=hist.filter(e=>e.event==='down').length;
                return t('uptimeStats',hrs>=24?Math.floor(hrs/24)+'d '+(hrs%24)+'h':hrs+'h',downs);
              })()}
            </div>
          </div>
        </div>
      </div>
    </td>`;
    newTbody.appendChild(dtr);
  });

  tbody.parentNode.replaceChild(newTbody, tbody);
  // Dibujar gráfico de uptime si hay fila expandida
  requestAnimationFrame(drawAllUptimeCharts);
}

// ── SNMP config ───────────────────────────────────────────────────────────────
// SNMP: panel para configurar un switch/router que aporta la tabla ARP (MAC de equipos en otras subredes). Los secretos no se muestran: el campo vacío significa «conservar».
// EN: SNMP: panel to configure a switch/router that provides the ARP table (MAC of devices on other subnets). Secrets are not shown: an empty field means "keep".
let _snmpOpen=false, _snmpHas={};
const $sn=id=>document.getElementById(id);
function toggleSnmpPanel(){
  _snmpOpen=!_snmpOpen;
  $sn('snmp-panel').style.display=_snmpOpen?'block':'none';
  if(_snmpOpen)loadSnmp();
}
document.addEventListener('click',e=>{
  if(_snmpOpen&&!$sn('snmp-wrap').contains(e.target)){_snmpOpen=false;$sn('snmp-panel').style.display='none';}
},{passive:true});
function snmpLayout(){
  const v=$sn('sn-version').value, lvl=$sn('sn-level').value;
  $sn('sn-v2').style.display=v==='3'?'none':'flex';
  $sn('sn-v3').style.display=v==='3'?'flex':'none';
  $sn('sn-auth').style.display=lvl==='noAuthNoPriv'?'none':'grid';
  $sn('sn-priv').style.display=lvl==='authPriv'?'grid':'none';
}
function snmpStatus(msg,ok){
  const st=$sn('sn-status');
  if(!msg){st.style.display='none';return;}
  st.style.display='block';
  st.style.background=ok?'var(--teal-dim)':'var(--red-dim)';
  st.style.color=ok?'var(--teal)':'var(--red)';
  st.textContent=(ok?'✓ ':'✕ ')+msg;
}
function snmpDot(on){
  const d=$sn('snmp-status-dot');if(!d)return;
  d.style.background=on?'var(--teal)':'var(--border-b)';d.style.boxShadow=on?'0 0 0 2px var(--teal-dim)':'none';
}
// OUI: base de fabricantes por MAC. Aquí se ve cuántos prefijos hay, se fuerza la actualización y se activa o no la actualización semanal.
// EN: OUI: MAC-to-vendor database. Here you see how many prefixes there are, force the update and turn the weekly update on or off.
async function loadOui(){
  try{
    const r=await fetch('api/oui');const d=await r.json();if(!r.ok)return;
    $sn('oui-auto').checked=d.auto!==false;
    const when=d.updated?new Date(d.updated*1000).toLocaleDateString():t('ouiNever');
    $sn('oui-status').textContent=`${d.count} ${t('ouiPrefixes')} · ${d.source||'—'} · ${when}`+(d.error?' ✕ '+d.error:'');
  }catch(e){}
}
async function updateOui(){
  const b=$sn('btn-oui');b.disabled=true;b.textContent=t('ouiUpdating');
  try{
    const r=await fetch('api/oui/update',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    const d=await r.json();if(!r.ok)throw new Error(d.error);
    toast(t('ouiDone'));fetchData();
  }catch(e){toast(e.message,true);}
  finally{b.disabled=false;b.textContent=t('ouiUpdate');loadOui();}
}
async function saveOuiAuto(){
  try{await fetch('api/oui',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({auto:$sn('oui-auto').checked})});}catch(e){}
}
// Carga la configuración SNMP guardada y si snmpwalk está instalado.
// EN: Load the stored SNMP configuration and whether snmpwalk is installed.
async function loadSnmp(){
  loadOui();
  try{
    const r=await fetch('api/snmp');const d=await r.json();if(!r.ok)throw new Error(d.error);
    const c=d.config;
    $sn('snmp-missing').style.display=d.available?'none':'block';
    $sn('sn-enabled').checked=!!c.enabled;$sn('sn-host').value=c.host||'';$sn('sn-port').value=c.port||161;
    $sn('sn-timeout').value=c.timeout||5;$sn('sn-version').value=c.version||'2c';$sn('sn-user').value=c.user||'';
    $sn('sn-level').value=c.level||'authPriv';$sn('sn-auth-proto').value=c.auth_proto||'SHA';$sn('sn-priv-proto').value=c.priv_proto||'AES';
    _snmpHas={community:c.has_community,auth_pass:c.has_auth_pass,priv_pass:c.has_priv_pass};
    [['sn-community','community'],['sn-auth-pass','auth_pass'],['sn-priv-pass','priv_pass']].forEach(([id,k])=>{
      $sn(id).value='';$sn(id).placeholder=_snmpHas[k]?'•••••• ('+t('snmpKeep')+')':'';
    });
    snmpLayout();snmpDot(!!c.enabled);
    const s=d.status||{};
    if(c.enabled&&s.ts){snmpStatus(s.error?s.error:`${s.count} ${t('snmpEntries')} — ${PCT.time(new Date(s.ts*1000),true)}`,!s.error);}else snmpStatus('');
  }catch(e){snmpStatus(e.message,false);}
}
function snmpBody(){
  const b={enabled:$sn('sn-enabled').checked,host:$sn('sn-host').value.trim(),port:+$sn('sn-port').value||161,
    timeout:+$sn('sn-timeout').value||5,version:$sn('sn-version').value,user:$sn('sn-user').value.trim(),
    level:$sn('sn-level').value,auth_proto:$sn('sn-auth-proto').value,priv_proto:$sn('sn-priv-proto').value};
  // secrets are only sent when typed; empty keeps the stored value on the server
  [['sn-community','community'],['sn-auth-pass','auth_pass'],['sn-priv-pass','priv_pass']].forEach(([id,k])=>{if($sn(id).value)b[k]=$sn(id).value;});
  return b;
}
async function snmpPost(url,btnId,label){
  const btn=$sn(btnId);btn.disabled=true;
  try{
    const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(snmpBody())});
    const d=await r.json();if(!r.ok)throw new Error(d.error||'Error');return d;
  }finally{btn.disabled=false;btn.textContent=label;}
}
// Prueba la configuración SNMP sin guardarla.
// EN: Test the SNMP configuration without saving it.
async function testSnmp(){
  snmpStatus(t('snmpTesting'),true);
  try{
    const d=await snmpPost('api/snmp/test','btn-sn-test',t('snmpTest'));
    snmpStatus(`${d.count} ${t('snmpEntries')}`+(d.sample.length?' — '+d.sample.map(x=>x.ip+' '+x.mac).join(', '):''),true);
  }catch(e){snmpStatus(e.message,false);}
}
// Guarda la configuración SNMP.
// EN: Save the SNMP configuration.
async function saveSnmp(){
  try{
    await snmpPost('api/snmp','btn-sn-save',t('save'));
    snmpDot($sn('sn-enabled').checked);toast(t('snmpSaved'));
    _snmpOpen=false;$sn('snmp-panel').style.display='none';
  }catch(e){snmpStatus(e.message,false);toast(e.message,true);}
}
['sn-version','sn-level'].forEach(id=>$sn(id).addEventListener('change',snmpLayout));
let _snmpDotDone=false;
async function refreshSnmpDot(){if(_snmpDotDone)return;_snmpDotDone=true;try{const r=await fetch('api/snmp');if(r.ok){const d=await r.json();snmpDot(!!d.config.enabled);}}catch(e){}}

// ── Pi-hole config ────────────────────────────────────────────────────────────
// Pi-hole: panel para indicar sus direcciones y contraseña; Net Monitor le pide nombres, MAC y fabricante de cada IP.
// EN: Pi-hole: panel to enter its addresses and password; Net Monitor asks it for names, MACs and vendors of each IP.
let _piholeOpen=false;
function togglePiholePanel(){
  _piholeOpen=!_piholeOpen;
  const panel=document.getElementById('pihole-panel');
  if(_piholeOpen){
    panel.style.display='block';
    loadPiholeConfig();
    setTimeout(()=>document.getElementById('ph-pass').focus(),80);
  }else{
    panel.style.display='none';
  }
}
// Cerrar al hacer click fuera
document.addEventListener('click',e=>{
  if(_piholeOpen&&!document.getElementById('pihole-wrap').contains(e.target)){
    _piholeOpen=false;
    document.getElementById('pihole-panel').style.display='none';
  }
},{passive:true});

async function loadPiholeConfig(){
  try{
    const r=await fetch('api/config');const d=await r.json();
    document.getElementById('ph-hosts').value=d.pihole_hosts||'';
    const st=document.getElementById('ph-status');
    if(d.pihole_enabled){
      const ts=d.pihole_cache_ts?PCT.time(new Date(d.pihole_cache_ts*1000),true):'—';
      st.style.display='block';st.style.background='var(--teal-dim)';st.style.color='var(--teal)';
      st.style.border='1px solid rgba(20,184,166,.2)';
      st.textContent=`✓ ${t('piholeConnected')||'Connected'} — ${d.pihole_entries} hosts | ${ts}`;
    }else{st.style.display='none';}
  }catch(e){}
}

// Guarda la configuración de Pi-hole (la contraseña se envía al servidor y nunca se vuelve a mostrar).
// EN: Save the Pi-hole configuration (the password is sent to the server and never shown again).
async function savePiholeConfig(){
  const hosts=document.getElementById('ph-hosts').value.trim();
  const pass=document.getElementById('ph-pass').value;
  const btn=document.getElementById('btn-ph-save');
  const st=document.getElementById('ph-status');
  if(!hosts){toast(t('piholeNeedHost')||'Enter at least one host',true);return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  st.style.display='block';st.style.background='var(--bg)';st.style.border='1px solid var(--border)';st.style.color='var(--text-dim)';
  st.textContent=t('piholeConnecting')||'Connecting…';
  try{
    const r=await fetch('api/pihole/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({hosts,password:pass})});
    const d=await r.json();if(!r.ok)throw new Error(d.error);
    st.style.background='var(--teal-dim)';st.style.color='var(--teal)';st.style.border='1px solid rgba(20,184,166,.2)';
    st.textContent=`✓ ${t('piholeSuccess')||'Saved — syncing names…'}`;
    document.getElementById('pihole-status-dot').style.background='var(--teal)';
    document.getElementById('pihole-status-dot').style.boxShadow='0 0 0 2px var(--teal-dim)';
    toast(t('piholeToast')||'Pi-hole connected — names will appear on next scan');
    setTimeout(()=>{_piholeOpen=false;document.getElementById('pihole-panel').style.display='none';},1500);
  }catch(e){
    st.style.background='var(--red-dim)';st.style.color='var(--red)';st.style.border='1px solid rgba(239,68,68,.2)';
    st.textContent='✕ '+e.message;toast(e.message,true);
  }finally{btn.disabled=false;btn.textContent=t('saveConnect')||'Save & connect';}
}

function updatePiholeStatusDot(enabled){
  const dot = document.getElementById('pihole-status-dot');
  if(!dot) return;
  if(enabled){
    dot.style.background='var(--teal)';
    dot.style.boxShadow='0 0 0 2px var(--teal-dim)';
  }else{
    dot.style.background='var(--border-b)';
    dot.style.boxShadow='none';
  }
}

// ── Uptime chart ──────────────────────────────────────────────────────────────
// Dibuja en un canvas la línea de tiempo de conexiones y desconexiones de un equipo (historial uptime_history).
// EN: Draw on a canvas the connect/disconnect timeline of a device (uptime_history).
function drawUptimeChart(ip, history){
  const cid = 'uptime-'+ip.replace(/\./g,'-');
  const canvas = document.getElementById(cid);
  if(!canvas) return;
  const dpr = window.devicePixelRatio||1;
  const W = canvas.offsetWidth||600, H = 40;
  if(canvas.width!==W*dpr){ canvas.width=W*dpr; canvas.height=H*dpr; }
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr,dpr); ctx.clearRect(0,0,W,H);

  const css = k => getComputedStyle(document.documentElement).getPropertyValue(k).trim();
  ctx.fillStyle = css('--bg')||'#f0f2f5';
  ctx.fillRect(0,0,W,H);

  if(!history||!history.length){
    ctx.fillStyle = css('--text-dim')||'#94a3b8';
    ctx.font = '10px DM Mono,monospace';
    ctx.textAlign = 'center';
    ctx.fillText(t('chartMonitoring'), W/2, H/2+4);
    ctx.scale(1/dpr,1/dpr); return;
  }

  // Build timeline: reconstruct online/offline periods
  const now  = Date.now()/1000;
  const span = Math.max(now - history[0].ts, 3600); // al menos 1h
  const xOf  = ts => Math.max(0, Math.min(W, ((ts - history[0].ts) / span) * W));

  // Draw background (offline = rojo tenue)
  ctx.fillStyle = 'rgba(239,68,68,.15)';
  ctx.fillRect(0,0,W,H);

  // Draw online periods as green bars
  ctx.fillStyle = 'rgba(34,197,94,.3)';
  let periodStart = null;
  const events = [...history, {ts: now, event: 'end'}];
  events.forEach((ev,i)=>{
    if(ev.event==='up') periodStart = ev.ts;
    if((ev.event==='down'||ev.event==='end') && periodStart!==null){
      const x1 = xOf(periodStart), x2 = xOf(ev.ts);
      ctx.fillRect(x1, 0, Math.max(2, x2-x1), H);
      periodStart = null;
    }
  });

  // Green line on top of online periods
  ctx.strokeStyle = 'var(--green,#22c55e)';
  ctx.lineWidth = 2;
  periodStart = null;
  events.forEach(ev=>{
    if(ev.event==='up') periodStart = ev.ts;
    if((ev.event==='down'||ev.event==='end') && periodStart!==null){
      const x1=xOf(periodStart), x2=xOf(ev.ts);
      ctx.beginPath(); ctx.moveTo(x1,H/2); ctx.lineTo(x2,H/2); ctx.stroke();
      periodStart=null;
    }
  });

  // Event markers
  history.forEach(ev=>{
    const x = xOf(ev.ts);
    ctx.beginPath(); ctx.arc(x, H/2, 3, 0, 2*Math.PI);
    ctx.fillStyle = ev.event==='up' ? '#22c55e' : '#ef4444';
    ctx.fill();
  });

  // Time labels
  ctx.fillStyle = css('--text-dim')||'#94a3b8';
  ctx.font = '9px DM Mono,monospace';
  ctx.textAlign = 'left';
  ctx.fillText(PCT.ls(new Date(history[0].ts*1000),_lang==='es'?'es-CL':'en-GB',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}), 4, H-3);
  ctx.textAlign = 'right';
  ctx.fillText('Ahora', W-4, H-3);

  ctx.scale(1/dpr,1/dpr);
}

// Draw uptime charts when expanding a row
const _origToggle = window._origToggle;
function drawAllUptimeCharts(){
  if(!expanded) return;
  const h = filtered().find(h=>h.ip===expanded);
  if(h) requestAnimationFrame(()=>drawUptimeChart(h.ip, h.uptime_history||[]));
}

// ── Edit OS ───────────────────────────────────────────────────────────────────
// Edición manual del sistema operativo y del alias de un equipo (admin); lo editado a mano no lo sobrescriben los escaneos siguientes.
// EN: Manual editing of a device's operating system and alias (admin); what is edited by hand is not overwritten by later scans.
const OS_LIST = ["Windows","Linux","macOS","iOS","IoT","Android","BSD","Desconocido"];

// Cambia el SO de un equipo.
// EN: Change a device's OS.
async function editOs(ip){
  const host = hosts.find(h=>h.ip===ip);
  if(!host) return;
  const curOs = host.os || 'Desconocido', curType = devType(host);
  const osOpts = OS_LIST.map(o=>`<option value="${o}"${o===curOs?' selected':''}>${esc(tOs(o))}</option>`).join('');
  const typeOpts = DEVICE_TYPES.map(k=>`<option value="${k}"${k===curType?' selected':''}>${TYPE_META[k].icon} ${esc(tType(k))}</option>`).join('')
    + (host.type_manual?`<option value="auto">↺ ${esc(t('autoDetect'))}</option>`:'');
  const selCss='background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);color:var(--text);font-family:var(--sans);font-size:13px;padding:8px 10px;outline:none;width:100%;margin-bottom:14px';
  const lblCss='display:block;font-size:11px;color:var(--text-dim);margin-bottom:4px';
  const overlay = document.createElement('div');
  overlay.style.cssText='position:fixed;inset:0;background:rgba(15,20,30,.45);backdrop-filter:blur(2px);z-index:9999;display:flex;align-items:center;justify-content:center';
  overlay.innerHTML=`
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:24px;max-width:340px;width:92%;box-shadow:var(--shadow-md)">
      <div style="font-size:14px;font-weight:600;color:var(--text);margin-bottom:6px">${esc(t('editDevice'))}</div>
      <div style="font-size:12px;color:var(--text-dim);margin-bottom:16px;font-family:var(--mono)">${esc(ip)} — ${esc(host.hostname||host.ip)}</div>
      <label style="${lblCss}">${esc(t('fieldType'))}</label>
      <select id="dev-type-sel" style="${selCss}">${typeOpts}</select>
      <label style="${lblCss}">${esc(t('fieldOs'))}</label>
      <select id="os-edit-sel" style="${selCss}">${osOpts}</select>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button id="os-edit-cancel" style="padding:8px 16px;border-radius:var(--r-sm);border:1px solid var(--border);background:transparent;color:var(--text-mid);font-family:var(--sans);font-size:13px;cursor:pointer">${esc(t('cancel'))}</button>
        <button id="os-edit-ok" style="padding:8px 16px;border-radius:var(--r-sm);border:none;background:var(--teal);color:#fff;font-family:var(--sans);font-size:13px;font-weight:600;cursor:pointer">${esc(t('save'))}</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  document.getElementById('dev-type-sel').focus();
  const cleanup = () => overlay.remove();
  overlay.addEventListener('click', e=>{ if(e.target===overlay) cleanup(); });
  document.getElementById('os-edit-cancel').onclick = cleanup;
  document.getElementById('os-edit-ok').onclick = async () => {
    const newOs = document.getElementById('os-edit-sel').value;
    const newType = document.getElementById('dev-type-sel').value;
    cleanup();
    const body = {ip};
    if(newOs!==curOs) body.os = newOs;                       // only send what changed (a change marks it manual)
    if(newType!==curType || newType==='auto') body.device_type = newType;
    if(Object.keys(body).length===1) return;
    try{
      const r = await fetch('api/hosts/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const d = await r.json();
      if(!r.ok) throw new Error(d.error);
      toast(t('saved'));
      await fetchData();
    }catch(e){ toast(e.message, true); }
  };
}

// ── Edit alias ────────────────────────────────────────────────────────────────
// Cambia el alias (nombre amigable) de un equipo.
// EN: Change a device's alias (friendly name).
async function editAlias(ip){
  const host=hosts.find(h=>h.ip===ip);
  if(!host)return;
  const alias=prompt(t('aliasPrompt',ip), host.alias||'');
  if(alias===null)return;
  try{
    const r=await fetch('api/hosts/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ip,alias})});
    const d=await r.json();
    if(!r.ok)throw new Error(d.error);
    toast(t('aliasSaved'));await fetchData();
  }catch(e){toast(e.message,true);}
}

// ── Helpers ───────────────────────────────────────────────────────────────────
// Escapa HTML antes de insertar texto de usuarios, equipos o la red en la página: evita inyección de código (XSS).
// EN: Escape HTML before inserting text from users, devices or the network into the page: prevents code injection (XSS).
// Identificador seguro para class="…": solo letras, números, guion y guion bajo.
function cssId(s){return String(s).replace(/[^A-Za-z0-9_-]/g,'');}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
// Valor seguro dentro de un handler on*="…": literal JS entre comillas, escapado también para HTML.
function jsa(s){return esc(JSON.stringify(String(s)));}
// Lista de argumentos para data-on-*-args="…" (JSON escapado para HTML).
function jsargs(a){return esc(JSON.stringify(a));}
function relTime(ts){const d=Math.floor((Date.now()-ts)/1000);if(d<60)return t('ago',d+'s');if(d<3600)return t('ago',Math.floor(d/60)+'m');if(d<86400)return t('ago',Math.floor(d/3600)+'h');return new Date(ts).toLocaleDateString(_lang==='es'?'es-CL':'en-GB',{day:'2-digit',month:'2-digit'});}
function updateClock(){const el=document.getElementById('clock');if(el)el.textContent=PCT.time(new Date(),true);}
let _tt;
// Aviso emergente breve (error si isErr).
// EN: Short pop-up notice (error if isErr).
function toast(msg,isErr=false){const el=document.getElementById('toast');el.textContent=msg;el.style.background=isErr?'var(--red)':'var(--text)';void el.offsetWidth;el.classList.add('show');clearTimeout(_tt);_tt=setTimeout(()=>el.classList.remove('show'),3400);}

_i18nReady=true;
updateSortHeaders();
(async()=>{
  const ok=await checkSession();
  if(ok){applyPermissions();await initApp();const ls=document.getElementById('login-screen');ls.style.opacity='0';setTimeout(()=>ls.style.display='none',150);}else{document.getElementById('login-screen').style.display='flex';}
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
if (window.cspRegister) cspRegister({ applyInterval, deleteHost, doLogin, editAlias, editOs, logout, rescanHost, saveOuiAuto, savePiholeConfig, saveSnmp, setLang, setOsFilter, setSort, setStatusFilter, setTheme, setTypeFilter, sortKey, startScan, testSnmp, toggleNav, togglePiholePanel, toggleSnmpPanel, updateOui });
