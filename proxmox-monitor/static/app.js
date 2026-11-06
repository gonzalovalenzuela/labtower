const LANG={
  en:{ndPrimary:'Primary metrics',ndSecondary:'Secondary metrics',ndSystem:'System',ndCpu:'CPU usage',ndOfCpus:n=>'of '+n+' CPUs',ndRam:'Memory usage',ndKsm:'KSM sharing',ndSwap:'SWAP usage',ndDisk:'Disk (/) usage',ndLoadAvg:'CPU load average',ndIowait:'CPU I/O delay',ndCpuModel:'CPU model',ndKernel:'Kernel version',ndBoot:'Boot mode',ndManager:'Manager version',ndUptime:'Uptime',ndTz:'Time zone',ndDns:'DNS',ndSub:'Subscription',ndUpdates:'Pending updates',ndDisks:'Disks',ndNetIf:'Network interfaces',ndServices:'Services',ndServState:'State',ndRunning:'running',ndInactive:'inactive (off on purpose)',ndInfo:'Information',ndSnCpu:'CPU thermal state',ndSnNvme:'NVMe temperatures',ndSnOther:'Other temperatures',ndSnFans:'System fans',ndPveMod:'Sensor Mod Version',ndUps:'UPS (PVE mod)',ndOther:'Other data',ndLoading:'Loading…',ndErr:'Could not read the node from Proxmox.',ndPerm:'The API token has no permission to read this.',ndExpand:'Click to show or hide the node details',ndChCpu:'CPU usage',ndChMem:'Memory usage',ndChLoad:'Server load',ndChNet:'Network traffic',ndSCpu:'CPU',ndSIo:'IO delay',ndSRam:'RAM',ndSSwap:'Swap',ndSLoad:'Load average',ndSIn:'In',ndSOut:'Out',ndRangeNote:'History comes from Proxmox itself; “All” is the last year.',ndNone:'None',ndYes:'yes',ndNo:'no',connecting:'Connecting…',connectingMsg:'Fetching data from Proxmox.',noNodes:'No nodes',noNodesMsg:'No nodes were found in this cluster.',loginTitle:'Sign in',loginSub:'Enter your credentials to continue.',
    username:'Username',password:'Password',loginBtn:'Sign in',rememberMe:'Remember me',rem1d:'1 day',rem1w:'1 week',rem1m:'1 month',remForever:'Forever',
    navSection:'Navigation',clustersPVE:'PVE Clusters',addCluster:'Add cluster',
    themeLight:'Light',themeDark:'Dark',
    statNodesOnline:'Nodes online',statVMsRunning:'VMs running',
    statCTsRunning:'CTs running',statAvgCPU:'Avg CPU',statAvgRAM:'Avg RAM',
    noClusters:'No clusters configured',noClustersHint:'Add a Proxmox cluster to get started.',
    addClusterTitle:'Add Proxmox cluster',
    addClusterHint:'You need an API Token in Proxmox: Datacenter → API Tokens → Add',
    fieldName:'Name',fieldPort:'Port',fieldPVEUser:'PVE User',
    formatLabel:'Format',cancel:'Cancel',test:'Test',delete:'Delete',
    deleteCluster:'Delete cluster',
    permReadonly:'Read-only',permExecute:'Execute',permAdmin:'Administrator',
    sessionExpired:'Session expired',
    nodeOnline:'Online',nodeOffline:'Offline',
    vmsRunning:'VMs',ctsRunning:'CTs',
    cpu:'CPU',memory:'Memory',disk:'Disk',
    historyChart:'CPU/RAM history (last samples)',
    sectionVMs:'Virtual Machines',sectionCTs:'Containers',
    running:'running',hideStopped:'Hide stopped',showStopped:'Show stopped',
    nodeOfflineMsg:'Node offline — no data available',connError:'Connection error',connErrorHint:'Check host, port and API token',
    nodeCountNav:(n)=>`${n} node${n!==1?'s':''}`,
    pinNode:'Pin node in place',unpinNode:'Unpin node',moveEarlier:'Move earlier',moveLater:'Move later',dragReorder:'Drag to reorder',resetOrder:'Reset node order',layoutSaved:'Node order saved',
    testConnected:(v,n)=>`✓ PVE ${v} — ${n} node${n!==1?'s':''}`,
    testFillAll:'Fill in all fields',
    fpConfirm:(fp)=>`Certificate SHA-256: ${fp} — compare it with the one shown in Proxmox (Datacenter → Node → Certificates). Press Test again to trust it and test the connection.`,
    fpNeedTest:'Run Test and confirm the certificate first',fpChanged:'Host or port changed: run Test again',
    unpinnedWarn:'This cluster\'s certificate is not verified.',staleTitle:'No connection to the cluster',staleAge:m=>`The data shown is from ${m}.`,certChanged:'The cluster certificate changed',certChangedDesc:'LabTower does not send the API token until the new certificate is confirmed, so nothing is being read. If you renewed or replaced the Proxmox certificate, pin it again.',repin:'Pin certificate again',unpinnedDesc:'The connection does not check the identity of the server before sending the API token, so someone on the network could impersonate it.',unpinned:'Certificate not verified',pinCert:'Pin certificate',pinPrompt:(fp)=>`Trust this certificate for this cluster?\n\nSHA-256:\n${fp}`,pinned:'Certificate pinned',
    clusterAdded:(name)=>`${name} added`,
    deleteClusterConfirm:(name)=>`Delete cluster "${name}"?`,
    cpuAlert:(pct)=>`CPU at ${pct}%`,ramAlert:(pct)=>`RAM at ${pct}%`,
    bkSelAll:'Select all',bkSelNone:'Clear selection',bkSelPending:'Select those without backup or too old',bkIgnoreSel:n=>`Ignore selected (${n})`,bkUnignoreSel:n=>`Stop ignoring selected (${n})`,bkTitle:'Backups (vzdump)',bkWait:'Reading backups… (first read takes a minute)',bkNone:'No backup storage found. The API token needs Datastore.Audit on the storages.',bkOk:'Up to date',bkOld:'Too old',bkNever:'No backup',bkIgnored:'Ignored',bkUnknown:'Unknown',bkAge:(h)=>h<48?`${h} h ago`:`${Math.floor(h/24)} d ago`,bkProblems:(n)=>`${n} without a recent backup`,bkAllOk:'Backups up to date',bkMax:(h)=>`Marked old after ${Math.round(h/24*10)/10} days`,bkDays:'days',bkApply:'Apply',bkIgnore:'Ignore',bkUnignore:'Stop ignoring',bkFailedTasks:'Failed backup tasks',bkVerified:'verified',bkVerFail:'verification failed',bkSaved:'Saved',bkStorageErr:'Could not read storage',bkCopies:(n)=>`${n} copies`,
    xTitle:'Capacity & health',xWait:'Collecting data…',xPerm:'Not available: the API token lacks permission (see the README)',
    xDays:'Days until full',xDaysNone:'Not enough history or not growing',xDaysHist:d=>'Collecting history ('+d+' of 2 days needed)',xDaysFlat:'Not growing',xDaysV:d=>d+' d',xCeph:'Ceph cluster',
    xCap:'Allocation (running guests)',xVcpu:'vCPU',xMemAl:'RAM',xN1Ok:'Survives losing the biggest node',xN1Bad:(n,a,b)=>`Does not fit if ${n} goes down: needs ${a}, ${b} available`,
    xHa:'High availability',xHaNone:'No HA services',xRepl:'Replication',xReplNone:'No replication jobs',xTasks:'Failed tasks (last 2 days)',xTasksNone:'No failed tasks',
    xNodes:'Nodes',xLoad:'load',xSwap:'swap',xIow:'iowait',xCert:'certificate',xCertD:d=>d+' d left',xDrift:v=>'Different PVE versions: '+v,
    xPg:'PGs not clean',xIo:'Ceph I/O',xRec:'recovering',xLocks:'Locked guests',xLockFor:(l,m)=>`${l} for ${m} min`,xFails:n=>n+' failures',
    xAlLock:(n,l,m)=>`${n}: locked (${l}) for ${m} min`,
    diagTitle:'Cluster diagnostics',diagExpand:'Expand all',diagCollapse:'Collapse all',quorum:'Quorum',quorumOk:'Quorum OK',quorumLost:'NO QUORUM',membersOnline:(a,b)=>`${a}/${b} nodes in corosync`,
    cephOsdDown:(n)=>`${n} OSD down`,cephOsdOut:(n)=>`${n} OSD out`,cephChecks:'Ceph warnings',
    rebootsTitle:'Node reboots',noReboots:'No reboots recorded since this was enabled.',rebootAt:'booted',rebootWave:'simultaneous',
    smartTitle:'Disks (SMART)',smartWait:'Reading SMART data… (first read takes up to a minute)',smartNone:'No disk data. The API token needs the Sys.Audit privilege on /nodes.',
    smartHealth:'Health',smartWear:'Wear',smartTemp:'Temp',smartUnsafe:'Unsafe shutdowns',smartErrs:'Media errors',smartAge:(m)=>`read ${m} min ago`,
    wHealth:'SMART failed',wMedia:'media errors',wCritwarn:'critical warning',wSectors:'bad sectors',wRealloc:'reallocated sectors',wWear:'worn out',wSpare:'low spare',nodeErr:'unavailable'},
  es:{ndPrimary:'Métricas principales',ndSecondary:'Métricas secundarias',ndSystem:'Sistema',ndCpu:'Uso de CPU',ndOfCpus:n=>'de '+n+' CPU',ndRam:'Uso de memoria',ndKsm:'Compartido por KSM',ndSwap:'Uso de SWAP',ndDisk:'Uso de disco (/)',ndLoadAvg:'Carga promedio de CPU',ndIowait:'Espera de E/S de CPU',ndCpuModel:'Modelo de CPU',ndKernel:'Versión del kernel',ndBoot:'Modo de arranque',ndManager:'Versión del gestor',ndUptime:'Tiempo encendido',ndTz:'Zona horaria',ndDns:'DNS',ndSub:'Suscripción',ndUpdates:'Actualizaciones pendientes',ndDisks:'Discos',ndNetIf:'Interfaces de red',ndServices:'Servicios',ndServState:'Estado',ndRunning:'en ejecución',ndInactive:'inactivos (apagados a propósito)',ndInfo:'Información',ndSnCpu:'Estado térmico de la CPU',ndSnNvme:'Temperaturas NVMe',ndSnOther:'Otras temperaturas',ndSnFans:'Ventiladores',ndPveMod:'Versión de Sensor Mod',ndUps:'UPS (PVE mod)',ndOther:'Otros datos',ndLoading:'Cargando…',ndErr:'No se pudo leer el nodo desde Proxmox.',ndPerm:'El token de API no tiene permiso para leer esto.',ndExpand:'Clic para mostrar u ocultar el detalle del nodo',ndChCpu:'Uso de CPU',ndChMem:'Uso de memoria',ndChLoad:'Carga del servidor',ndChNet:'Tráfico de red',ndSCpu:'CPU',ndSIo:'Espera E/S',ndSRam:'RAM',ndSSwap:'Swap',ndSLoad:'Carga promedio',ndSIn:'Entrada',ndSOut:'Salida',ndRangeNote:'El historial lo entrega Proxmox; «Todo» es el último año.',ndNone:'Ninguna',ndYes:'sí',ndNo:'no',connecting:'Conectando…',connectingMsg:'Obteniendo datos de Proxmox.',noNodes:'Sin nodos',noNodesMsg:'No se encontraron nodos en este cluster.',loginTitle:'Iniciar sesión',loginSub:'Ingresa tus credenciales para continuar.',
    username:'Usuario',password:'Contraseña',loginBtn:'Entrar',rememberMe:'Recordarme',rem1d:'1 día',rem1w:'1 semana',rem1m:'1 mes',remForever:'Siempre',
    navSection:'Navegación',clustersPVE:'Clusters PVE',addCluster:'Agregar cluster',
    themeLight:'Claro',themeDark:'Oscuro',
    statNodesOnline:'Nodos en línea',statVMsRunning:'VMs en ejecución',
    statCTsRunning:'CTs corriendo',statAvgCPU:'CPU promedio',statAvgRAM:'RAM promedio',
    noClusters:'Sin clusters configurados',noClustersHint:'Agrega un cluster Proxmox para comenzar.',
    addClusterTitle:'Agregar cluster Proxmox',
    addClusterHint:'Necesitas un API Token en Proxmox: Datacenter → API Tokens → Add',
    fieldName:'Nombre',fieldPort:'Puerto',fieldPVEUser:'Usuario PVE',
    formatLabel:'Formato',cancel:'Cancelar',test:'Probar',delete:'Eliminar',
    deleteCluster:'Eliminar cluster',
    permReadonly:'Solo lectura',permExecute:'Ejecución',permAdmin:'Administrador',
    sessionExpired:'Sesión expirada',
    nodeOnline:'En línea',nodeOffline:'Sin conexión',
    vmsRunning:'VMs',ctsRunning:'CTs',
    cpu:'CPU',memory:'Memoria',disk:'Disco',
    historyChart:'Historial CPU/RAM (últimas muestras)',
    sectionVMs:'Máquinas Virtuales',sectionCTs:'Contenedores',
    running:'corriendo',hideStopped:'Ocultar detenidas',showStopped:'Mostrar detenidas',
    nodeOfflineMsg:'Nodo offline — sin datos disponibles',connError:'Error de conexión',connErrorHint:'Verifica host, puerto y token API',
    nodeCountNav:(n)=>`${n} nodo${n!==1?'s':''}`,
    pinNode:'Fijar nodo en su lugar',unpinNode:'Desfijar nodo',moveEarlier:'Mover antes',moveLater:'Mover después',dragReorder:'Arrastra para reordenar',resetOrder:'Restablecer orden de nodos',layoutSaved:'Orden de nodos guardado',
    testConnected:(v,n)=>`✓ PVE ${v} — ${n} nodo${n!==1?'s':''}`,
    testFillAll:'Completa todos los campos',
    fpConfirm:(fp)=>`Certificado SHA-256: ${fp} — compáralo con el de Proxmox (Datacenter → Nodo → Certificates). Presiona Probar otra vez para confiar en él y probar la conexión.`,
    fpNeedTest:'Primero usa Probar y confirma el certificado',fpChanged:'Cambió el host o el puerto: usa Probar otra vez',
    unpinnedWarn:'El certificado de este cluster no está verificado.',staleTitle:'Sin conexión con el cluster',staleAge:m=>`Los datos que ves son de ${m}.`,certChanged:'El certificado del cluster cambió',certChangedDesc:'LabTower no envía el token de la API hasta confirmar el certificado nuevo, así que no se está leyendo nada. Si renovaste o cambiaste el certificado de Proxmox, vuelve a fijarlo.',repin:'Volver a fijar certificado',unpinnedDesc:'La conexión no comprueba la identidad del servidor antes de enviar el token de la API, así que alguien en la red podría suplantarlo.',unpinned:'Certificado sin verificar',pinCert:'Fijar certificado',pinPrompt:(fp)=>`¿Confiar en este certificado para este cluster?\n\nSHA-256:\n${fp}`,pinned:'Certificado fijado',
    clusterAdded:(name)=>`${name} agregado`,
    deleteClusterConfirm:(name)=>`¿Eliminar el cluster "${name}"?`,
    cpuAlert:(pct)=>`CPU al ${pct}%`,ramAlert:(pct)=>`RAM al ${pct}%`,
    bkSelAll:'Seleccionar todas',bkSelNone:'Limpiar selección',bkSelPending:'Seleccionar las sin respaldo o muy viejas',bkIgnoreSel:n=>`Ignorar seleccionadas (${n})`,bkUnignoreSel:n=>`Dejar de ignorar seleccionadas (${n})`,bkTitle:'Respaldos (vzdump)',bkWait:'Leyendo respaldos… (la primera lectura tarda un minuto)',bkNone:'No hay storages de respaldo. El token de la API necesita Datastore.Audit en los storages.',bkOk:'Al día',bkOld:'Muy viejo',bkNever:'Sin respaldo',bkIgnored:'Ignorado',bkUnknown:'Desconocido',bkAge:(h)=>h<48?`hace ${h} h`:`hace ${Math.floor(h/24)} d`,bkProblems:(n)=>`${n} sin respaldo reciente`,bkAllOk:'Respaldos al día',bkMax:(h)=>`Se marca como vieja tras ${Math.round(h/24*10)/10} días`,bkDays:'días',bkApply:'Aplicar',bkIgnore:'Ignorar',bkUnignore:'Dejar de ignorar',bkFailedTasks:'Tareas de respaldo fallidas',bkVerified:'verificado',bkVerFail:'verificación fallida',bkSaved:'Guardado',bkStorageErr:'No se pudo leer el storage',bkCopies:(n)=>`${n} copias`,
    xTitle:'Capacidad y salud',xWait:'Recopilando datos…',xPerm:'No disponible: el token de la API no tiene permiso (ver el README)',
    xDays:'Días hasta llenarse',xDaysNone:'Sin historial suficiente o no crece',xDaysHist:d=>'Reuniendo historial ('+d+' de 2 días necesarios)',xDaysFlat:'No crece',xDaysV:d=>d+' d',xCeph:'Cluster Ceph',
    xCap:'Asignación (invitados encendidos)',xVcpu:'vCPU',xMemAl:'RAM',xN1Ok:'Resiste la caída del nodo más grande',xN1Bad:(n,a,b)=>`No caben si cae ${n}: necesitan ${a}, hay ${b} disponibles`,
    xHa:'Alta disponibilidad',xHaNone:'Sin servicios HA',xRepl:'Replicación',xReplNone:'Sin trabajos de replicación',xTasks:'Tareas fallidas (últimos 2 días)',xTasksNone:'Sin tareas fallidas',
    xNodes:'Nodos',xLoad:'carga',xSwap:'swap',xIow:'iowait',xCert:'certificado',xCertD:d=>'quedan '+d+' d',xDrift:v=>'Versiones de PVE distintas: '+v,
    xPg:'PG no limpios',xIo:'E/S de Ceph',xRec:'recuperando',xLocks:'Invitados bloqueados',xLockFor:(l,m)=>`${l} hace ${m} min`,xFails:n=>n+' fallos',
    xAlLock:(n,l,m)=>`${n}: bloqueado (${l}) hace ${m} min`,
    diagTitle:'Diagnóstico del cluster',diagExpand:'Expandir todo',diagCollapse:'Contraer todo',quorum:'Quórum',quorumOk:'Quórum OK',quorumLost:'SIN QUÓRUM',membersOnline:(a,b)=>`${a}/${b} nodos en corosync`,
    cephOsdDown:(n)=>`${n} OSD caído${n!==1?'s':''}`,cephOsdOut:(n)=>`${n} OSD fuera`,cephChecks:'Avisos de Ceph',
    rebootsTitle:'Reinicios de nodos',noReboots:'Sin reinicios registrados desde que se activó.',rebootAt:'arrancó',rebootWave:'simultáneo',
    smartTitle:'Discos (SMART)',smartWait:'Leyendo SMART… (la primera lectura tarda hasta un minuto)',smartNone:'Sin datos de discos. El token de la API necesita el privilegio Sys.Audit en /nodes.',
    smartHealth:'Salud',smartWear:'Desgaste',smartTemp:'Temp',smartUnsafe:'Apagados inseguros',smartErrs:'Errores de medio',smartAge:(m)=>`leído hace ${m} min`,
    wHealth:'SMART falló',wMedia:'errores de medio',wCritwarn:'aviso crítico',wSectors:'sectores dañados',wRealloc:'sectores reasignados',wWear:'desgastado',wSpare:'poca reserva',nodeErr:'no disponible'}
};
let _lang=localStorage.getItem('pi-lang')||'en';
var _i18nReady=false;
// Traducción: busca la clave en el idioma activo (admite textos con función para incluir valores).
// EN: Translation: looks the key up in the active language (supports function texts that take values).
function t(k,...args){const v=(LANG[_lang]||LANG.en)[k]||(LANG.en)[k]||k;return typeof v==='function'?v(...args):v;}
// Ocultar VM detenidas (se declara antes que setLang, que se ejecuta al cargar). / EN: hide stopped VMs (declared before setLang, which runs on load).
let _hideStopped=false; try{_hideStopped=localStorage.getItem('pi-px-hide-stopped')==='1';}catch(e){}
// Cambia el idioma, lo recuerda y vuelve a pintar los textos de la página.
// EN: Switch the language, remember it and repaint the page texts.
function setLang(l){
  _lang=l;localStorage.setItem('pi-lang',l);document.documentElement.lang=l;try{renderNav();}catch(e){}
  document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=t(el.getAttribute('data-i18n')));
  ['en','es'].forEach(x=>document.getElementById('lang-'+x)?.classList.toggle('active',x===l));
  stoppedBtn();
  if(_i18nReady && typeof renderDashboard==='function')renderDashboard();
}
(()=>setLang(_lang))();

// Estado: sesión, clusters, cluster activo y temporizador de refresco.
// EN: State: session, clusters, active cluster and refresh timer.
let ME=null, clusters=[], activeId=null, pollTimer=null;
// Refresco rápido mientras la pestaña está visible; en segundo plano se detiene (así el servidor pasa a su ritmo lento).
// EN: Fast refresh while the tab is visible; it stops in the background (so the server switches to its slow rate).
const POLL=5000;            // fast refresh while the tab is visible; paused when hidden
// El historial de CPU/RAM de los nodos es grande y cambia cada 30 s: se pide cada 30 s y entre medias se reutiliza la copia anterior.
// EN: The nodes' CPU/RAM history is large and changes every 30 s: it is requested every 30 s and the previous copy is reused in between.
let _histTs=0, _histCache={}, _collapsed=new Set();

// ── Theme ────────────────────────────────────────────────────────────────────
// Elige el tema (claro, oscuro o automático según el sistema) y lo recuerda (clave pi-theme).
// EN: Choose the theme (light, dark or automatic following the system) and remember it (key pi-theme).
function setTheme(t){localStorage.setItem('pi-theme',t);applyTheme(t);['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));}
// Aplica el tema al documento.
// EN: Apply the theme to the document.
function applyTheme(t){const p=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;document.documentElement.setAttribute('data-theme',p==='dark'?'dark':'light');}
(()=>{const t=localStorage.getItem('pi-theme')||'dark';applyTheme(t);window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if((localStorage.getItem('pi-theme')||'dark')==='system')applyTheme('system');});setTimeout(()=>{['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===(localStorage.getItem('pi-theme')||'dark')));},0);})();

// ── Nav reordenable ───────────────────────────────────────────────────────────
// ¿Puede agregar y borrar clusters, fijar certificados y ordenar nodos? (nivel «admin» de Proxmox).
// EN: Can it add and delete clusters, pin certificates and reorder nodes? (Proxmox "admin" level).
function canAdmin(){return ME&&ME.permissions?.pve==='admin';}
const _NAV_SELF='pve';
// Navegación compartida (nav.js): mismo orden y grupos en todos los módulos. / EN: shared navigation (nav.js): same order and groups in every module.
function renderNav(){if(window.labNav)labNav.render({self:_NAV_SELF,lang:_lang,me:ME});}

// ── Login ────────────────────────────────────────────────────────────────────
document.getElementById('l-pass').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
// Inicio de sesión. La cookie la fija el servidor (HttpOnly): el JavaScript nunca guarda el token.
// EN: Login. The cookie is set by the server (HttpOnly): the JavaScript never stores the token.
async function doLogin(){
  const btn=document.getElementById('btn-l'),err=document.getElementById('login-err');
  const u=document.getElementById('l-user').value.trim(),p=document.getElementById('l-pass').value;
  err.className='login-err';
  if(!u||!p){err.textContent=t('testFillAll');err.className='login-err show';return;}
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
// Pregunta al servidor quién es el usuario; sin sesión o sin acceso a Proxmox devuelve false y se muestra el login.
// EN: Ask the server who the user is; without a session or without Proxmox access it returns false and the login is shown.
async function checkSession(){
  try{
    const r=await fetch('api/me');
    if(!r.ok) return false;
    const d=await r.json();
    if(!d.username) return false;
    ME=d;
    return true;
  }catch{return false;}
}

// Si hay sesión válida en otra app, pre-rellena el usuario y muestra aviso
// Reutiliza la sesión existente (cookie); si no hay, se muestra el login normal.
// EN: Reuse the existing session (cookie); if there is none, the normal login is shown.
async function tryAutoLogin(){
  // Intenta reusar sesión existente vía cookie
  const ok = await checkSession();
  if(ok) return true;
  // No hay sesión — mostrar login normal
  return false;
}
// Muestra nombre y rol y oculta los controles de administración a quien no es admin.
// EN: Show name and role and hide the admin controls from non-admins.
function applyPermissions(){
  const _un=String(ME.username||'?');
  document.getElementById('me-name').textContent=_un;
  document.getElementById('avatar').textContent=_un[0].toUpperCase();
  const _permKey={readonly:'permReadonly',execute:'permExecute',admin:'permAdmin'}[ME.permissions?.pve];
  document.getElementById('me-role').textContent=_permKey?t(_permKey):'—';
  renderNav();
  if(ME.permissions?.pve==='admin') document.getElementById('btn-add-cluster').style.display='';
}
// Cierra la sesión en el servidor y recarga la página.
// EN: Close the session on the server and reload the page.
async function logout(){await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.reload();}

// ── Init ────────────────────────────────────────────────────────────────────
// Arranque tras iniciar sesión: primera descarga y refresco periódico (pausado cuando la pestaña no se ve).
// EN: Startup after login: first download and periodic refresh (paused when the tab is not visible).
async function initApp(){
  updateClock();setInterval(updateClock,1000);
  await fetchAll();
  pollTimer=setInterval(()=>{if(!document.hidden)fetchAll();},POLL);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)fetchAll();});
}

// Descarga los clusters con su última lectura. El historial pesado se pide solo cada 30 s y se reutiliza entre medias. Un 401 recarga la página (sesión vencida).
// EN: Download the clusters with their last reading. The heavy history is requested only every 30 s and reused in between. A 401 reloads the page (expired session).
async function fetchAll(){
  loadGuestHosts();
  try{
    // node history is big and only changes every 30 s: ask for it rarely, reuse the last copy otherwise
    const wantHist=Date.now()-_histTs>=30000;
    const r=await fetch('api/clusters'+(wantHist?'':'?hist=0'));
    if(r.status===401){location.reload();return;}
    const d=await r.json();
    clusters=d.clusters||[];
    clusters.forEach(c=>(c.snap?.data?.nodes||[]).forEach(nd=>{
      const k=c.id+':'+nd.name;
      if(wantHist)_histCache[k]=nd.history; else nd.history=_histCache[k];
    }));
    if(wantHist)_histTs=Date.now();
    renderSidebar();
    if(!activeId&&clusters.length>0) selectCluster(clusters[0].id);
    else if(activeId) renderDashboard();
    updateGlobalStats();
  }catch(e){console.error(e);}
}

// Cambia el cluster mostrado.
// EN: Switch the displayed cluster.
function selectCluster(id){activeId=id;renderSidebar();renderDashboard();}

// Lista de clusters en la barra lateral: punto de estado (cargando / error / ok), host:puerto, cantidad de nodos y, para administradores, botón de borrar.
// EN: Cluster list in the sidebar: status dot (loading / error / ok), host:port, node count and, for administrators, a delete button.
function renderSidebar(){
  const list=document.getElementById('cluster-list');list.innerHTML='';
  clusters.forEach(c=>{
    const snap=c.snap;
    const isActive=c.id===activeId;
    const dotCls=!snap?.ts?'loading':snap?.error?'err':'ok';
    const nodeCount=(snap?.data?.nodes||[]).length;
    const div=document.createElement('div');
    div.className='cluster-nav'+(isActive?' active':'');
    div.onclick=()=>selectCluster(c.id);
    div.innerHTML=`<span class="cluster-dot ${dotCls}"></span>
      <div style="flex:1;min-width:0">
        <div class="cluster-nav-name ${isActive?'act':''}">${esc(c.name)}</div>
        <div class="cluster-nav-host"><span data-nethost="${esc(c.host)}">${esc(c.host)}</span>:${c.port}${nodeCount?' · '+t('nodeCountNav',nodeCount):''}</div>
      </div>
      ${c.id!=='local'&&ME?.permissions?.pve==='admin'?`<button style="background:none;border:none;color:var(--text-dim);cursor:pointer;font-size:12px;padding:2px 4px" data-on-click="confirmDelete" data-on-click-args="${jsargs([c.id,c.name])}" data-on-click-stop="1">✕</button>`:''}`;
    list.appendChild(div);
  });
}

// ── Stats globales ────────────────────────────────────────────────────────────
// Contadores de la cabecera sumando todos los clusters: nodos en línea, VMs y contenedores en ejecución, y CPU y RAM promedio.
// EN: Header counters adding up all the clusters: online nodes, running VMs and containers, and average CPU and RAM.
function updateGlobalStats(){
  let totalNodes=0, runVMs=0, runCTs=0, cpuSum=0, memSum=0, cpuN=0, memN=0;
  clusters.forEach(c=>{
    const nodes=c.snap?.data?.nodes||[];
    nodes.forEach(n=>{
      if(n.status==='online'){
        totalNodes++;
        if(n.cpu>0){cpuSum+=n.cpu*100;cpuN++;}
        if(n.maxmem>0){memSum+=(n.mem/n.maxmem)*100;memN++;}
      }
      runVMs+=(n.vms||[]).filter(v=>v.status==='running').length;
      runCTs+=(n.cts||[]).filter(v=>v.status==='running').length;
    });
  });
  document.getElementById('st-nodes').textContent=totalNodes||'—';
  document.getElementById('st-vms').textContent=runVMs||'—';
  document.getElementById('st-cts').textContent=runCTs||'—';
  document.getElementById('st-cpu').innerHTML=(cpuN?Math.round(cpuSum/cpuN):'—')+'<span style="font-size:13px;color:var(--text-dim)">%</span>';
  document.getElementById('st-mem').innerHTML=(memN?Math.round(memSum/memN):'—')+'<span style="font-size:13px;color:var(--text-dim)">%</span>';
}

// ── Dashboard cluster activo ──────────────────────────────────────────────────
// Dibuja el cluster activo: resumen, estado de Ceph y una tarjeta por nodo. Si el certificado no está fijado, ofrece el botón «Fijar certificado».
// EN: Draw the active cluster: summary, Ceph state and one card per node. If the certificate is not pinned, it offers the "Pin certificate" button.
function renderDashboard(){
  if(_dragging) return;                       // do not rebuild the DOM under a drag in progress
  const cluster=clusters.find(c=>c.id===activeId);
  if(!cluster) return;
  const snap=cluster.snap;
  document.getElementById('tb-title').textContent=cluster.name;
  {const sub=document.getElementById('tb-sub');sub.textContent='';const hs=document.createElement('span');hs.textContent=cluster.host;hs.setAttribute('data-nethost',cluster.host);hs.setAttribute('data-nethost-click','1');sub.appendChild(hs);sub.appendChild(document.createTextNode(':'+cluster.port+(snap?.data?.version?' · PVE '+snap.data.version:'')));}
  const bn=document.getElementById('pin-banner');
  if(bn){
    bn.style.display=cluster.pinned?'none':'';
    document.getElementById('pin-banner-t').textContent=t('unpinnedWarn');
    document.getElementById('pin-banner-d').textContent=t('unpinnedDesc');
    const bb=document.getElementById('pin-banner-b');bb.style.display=isPveAdmin()?'':'none';bb.textContent=t('pinCert');
  }
  const pb=document.getElementById('tb-pin');
  if(pb){pb.style.display=cluster.pinned?'none':'';pb.textContent='⚠ '+t('unpinned')+' — '+t('pinCert');}
  const main=document.getElementById('main-content');

  if(!snap?.ts){
    main.innerHTML='<div class="state-msg"><strong>'+esc(t('connecting'))+'</strong>'+esc(t('connectingMsg'))+'</div>';return;
  }
  if(snap.error&&!snap.data?.nodes?.length){
    main.innerHTML=`<div class="state-msg err"><strong>${t('connError')||'Connection error'}</strong>${esc(snap.error)}<br><br><span style="font-size:12px;font-family:var(--mono)">${t('connErrorHint')||'Check host, port and API token'}</span></div>`;return;
  }

  const nodes=orderedNodes(cluster,snap.data?.nodes||[]);
  if(!nodes.length){
    main.innerHTML='<div class="state-msg"><strong>'+esc(t('noNodes'))+'</strong>'+esc(t('noNodesMsg'))+'</div>';return;
  }

  main.innerHTML='';
  // Lectura fallida con datos anteriores: se muestra el error y la antigüedad de los datos (si es el certificado, el botón para volver a fijarlo).
  // EN: Failed reading with older data: show the error and the age of the data (if it is the certificate, the button to pin it again).
  if(snap.error){
    const box=document.createElement('div');box.className='stale-banner';
    const when=snap.ts?PCT.ls(new Date(snap.ts*1000),_lang==='es'?'es-CL':'en-US',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}):'—';
    const cert=snap.error_kind==='cert';
    box.innerHTML=`<strong>⚠ ${esc(t(cert?'certChanged':'staleTitle'))}</strong> <span>${esc(cert?t('certChangedDesc'):snap.error)} ${esc(t('staleAge',when))}</span>`+
      (cert&&isPveAdmin()?` <button class="btn-secondary" data-on-click="pinCluster">${esc(t('repin'))}</button>`:'')+
      (cert?`<div class="stale-err">${esc(snap.error)}</div>`:'');
    main.appendChild(box);
  }
  const grid=document.createElement('div');grid.className='nodes-grid';
  const names=nodes.map(n=>n.name), pinnedSet=new Set(cluster.layout?.pinned||[]);
  if(isPveAdmin()&&(cluster.layout?.order?.length||cluster.layout?.pinned?.length)){
    const bar=document.createElement('div');bar.className='layout-bar';
    bar.innerHTML=`<button data-on-click="resetLayout" data-on-click-args="${jsargs([cluster.id])}">${esc(t('resetOrder'))}</button>`;
    main.appendChild(bar);
  }
  nodes.forEach(node=>{const card=buildNodeCard(node,cluster);decorateCard(card,cluster,node.name,names,pinnedSet);grid.appendChild(card);});
  main.appendChild(grid);

  // Agregar sección Ceph si está disponible
  const ceph=cluster.snap?.data?.ceph;
  if(ceph&&!ceph.error){
    const cephDiv=document.createElement('div');
    const cephStatus=['HEALTH_OK','HEALTH_WARN','HEALTH_ERR'].includes(ceph.health?.status)?ceph.health.status:'UNKNOWN';
    const cephColor=cephStatus==='HEALTH_OK'?'var(--green)':cephStatus==='HEALTH_WARN'?'var(--orange)':'var(--red)';
    const pools=Number((ceph.pools||[]).length)||0;
    const osds=ceph.osdmap?.num_osds||'?';
    const osdsUp=ceph.osdmap?.num_up_osds||'?';
    cephDiv.innerHTML=`
      <div style="margin-top:16px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:14px 18px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
          <span style="font-size:13px;font-weight:600">Ceph Cluster</span>
          <span style="font-size:11px;font-weight:700;color:${cephColor};background:${cephStatus==='HEALTH_OK'?'rgba(34,197,94,.12)':cephStatus==='HEALTH_WARN'?'rgba(249,115,22,.12)':'rgba(239,68,68,.12)'};padding:2px 8px;border-radius:99px">${cephStatus}</span>
        </div>
        <div style="display:flex;gap:24px;font-size:12px;color:var(--text-mid)">
          <div>OSDs: <strong>${esc(osdsUp)}/${esc(osds)}</strong> online</div>
          <div>Pools: <strong>${pools}</strong></div>
          ${ceph.pgmap?.bytes_used!=null?`<div>Usado: <strong>${fmtBytes(ceph.pgmap.bytes_used)}</strong> / ${fmtBytes(ceph.pgmap.bytes_total||0)}</div>`:''}
        </div>
      </div>`;
    main.appendChild(cephDiv);
  }
  const dg=buildDiag(cluster);
  if(dg)main.appendChild(dg);

  // Dibujar sparklines después de que el DOM esté pintado
  renderSparklines(nodes);
  refreshOpenNodes(cluster,nodes);
}

// ── Cluster diagnostics: corosync, Ceph warnings, reboots, SMART ──────────────────
// Diagnóstico: quórum de corosync, avisos de Ceph (vienen en la lectura del cluster) y, pedidos aparte cada minuto a /api/diag, reinicios y SMART.
// EN: Diagnostics: corosync quorum, Ceph warnings (they come with the cluster reading) and, requested separately every minute from /api/diag, reboots and SMART.
let _diag={}, _diagTs={}, _diagShown=new Set();
async function fetchDiag(cid){
  if(Date.now()-(_diagTs[cid]||0)<60000)return;
  _diagTs[cid]=Date.now();
  try{const r=await fetch('api/diag?id='+encodeURIComponent(cid));if(r.ok){_diag[cid]=await r.json();if(activeId===cid&&!_dragging)renderDashboard();}}catch(e){}
}
const _bkSel={};
function bkSelSet(cid){return _bkSel[cid]||(_bkSel[cid]=new Set());}
function bkSelToggle(cid,vmid){const q=bkSelSet(cid);if(q.has(vmid))q.delete(vmid);else q.add(vmid);renderDashboard();}
function bkSelMode(cid,mode){
  const bk=_diag[cid]&&_diag[cid].backups;if(!bk)return;const q=bkSelSet(cid);q.clear();
  if(mode!=='none')bk.rows.forEach(r=>{if(r.status==='unknown')return;if(mode==='all'||r.status==='never'||r.status==='old')q.add(r.vmid);});
  renderDashboard();
}
async function bkBulk(cid,ignore){
  const bk=_diag[cid]&&_diag[cid].backups;if(!bk)return;const q=bkSelSet(cid);if(!q.size)return;
  const set=new Set(bk.ignore||[]);q.forEach(v=>{if(ignore)set.add(v);else set.delete(v);});
  try{
    const r=await fetch('api/clusters/'+encodeURIComponent(cid)+'/backup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({max_age_h:bk.max_age_h,ignore:[...set]})});
    if(!r.ok)throw new Error((await r.json()).error||'Error');
    bk.ignore=[...set];bk.rows.forEach(x=>{if(q.has(x.vmid))x.status=set.has(x.vmid)?'ignored':(x.last==null?'never':(x.age>bk.max_age_h*3600?'old':'ok'));});
    q.clear();_diagTs[cid]=0;renderDashboard();toast(t('bkSaved'));
  }catch(e){toast(e.message,true);}
}
// Cambia a partir de cuántos días un respaldo se considera viejo (1 a 365).
// EN: Change after how many days a backup counts as old (1 to 365).
async function bkSetDays(cid){
  const bk=_diag[cid]&&_diag[cid].backups;if(!bk)return;
  const d=parseInt(document.getElementById('bk-days')?.value||'',10);
  if(!(d>=1&&d<=365)){toast(t('bkDays')+': 1-365',true);return;}
  try{
    const r=await fetch('api/clusters/'+encodeURIComponent(cid)+'/backup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({max_age_h:d*24,ignore:bk.ignore||[]})});
    if(!r.ok)throw new Error((await r.json()).error||'Error');
    bk.max_age_h=d*24;const ig=new Set(bk.ignore||[]);
    bk.rows.forEach(x=>{if(x.status==='unknown'||ig.has(x.vmid))return;x.status=x.last==null?'never':(x.age>bk.max_age_h*3600?'old':'ok');});
    _diagTs[cid]=0;renderDashboard();toast(t('bkSaved'));
  }catch(e){toast(e.message,true);}
}
async function toggleBkIgnore(cid,vmid){
  const bk=_diag[cid]&&_diag[cid].backups;if(!bk)return;
  const set=new Set(bk.ignore||[]);if(set.has(vmid))set.delete(vmid);else set.add(vmid);
  try{
    const r=await fetch('api/clusters/'+encodeURIComponent(cid)+'/backup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({max_age_h:bk.max_age_h,ignore:[...set]})});
    if(!r.ok)throw new Error((await r.json()).error||'Error');
    bk.ignore=[...set];bk.rows.forEach(x=>{if(x.vmid===vmid){x.status=set.has(vmid)?'ignored':(x.last==null?'never':(x.age>bk.max_age_h*3600?'old':'ok'));}});
    _diagTs[cid]=0;renderDashboard();toast(t('bkSaved'));
  }catch(e){toast(e.message,true);}
}
const DIAG_KEYS=['extra','reboots','backups','smart'];
function toggleDiagAll(){if(DIAG_KEYS.every(k=>_diagShown.has(k)))_diagShown.clear();else DIAG_KEYS.forEach(k=>_diagShown.add(k));renderDashboard();}
function toggleDiag(k){if(_diagShown.has(k))_diagShown.delete(k);else _diagShown.add(k);renderDashboard();}
function pill(txt,col){const e=document.createElement('span');e.textContent=txt;e.style.cssText='font-size:11px;font-weight:700;padding:2px 8px;border-radius:99px;color:'+col+';background:color-mix(in srgb,'+col+' 14%,transparent);white-space:nowrap';return e;}
function dtFmt(ts){const d=new Date(Number(ts)*1000);return isNaN(d)?'—':d.toLocaleDateString(_lang==='es'?'es-CL':'en-GB',{day:'2-digit',month:'short'})+' '+PCT.time(d,false);}
function buildDiag(cluster){
  const data=cluster.snap?.data||{}, cs=data.corosync, cp=data.ceph_sum;
  fetchDiag(cluster.id);
  const dg=_diag[cluster.id];
  const box=document.createElement('div');
  box.style.cssText='margin-top:16px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:14px 18px';
  const hd=document.createElement('div');hd.style.cssText='font-size:13px;font-weight:600;margin-bottom:10px';hd.style.display='flex';hd.style.justifyContent='space-between';hd.style.alignItems='center';
  const hdt=document.createElement('span');hdt.textContent=t('diagTitle');hd.appendChild(hdt);
  const all=document.createElement('button');all.type='button';all.className='btn-secondary';all.style.cssText='font-size:11px;padding:2px 10px';
  all.setAttribute('data-on-click','toggleDiagAll');all.textContent=DIAG_KEYS.every(k=>_diagShown.has(k))?t('diagCollapse'):t('diagExpand');hd.appendChild(all);box.appendChild(hd);
  const row=document.createElement('div');row.style.cssText='display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:12px;color:var(--text-mid)';
  if(cs){
    row.appendChild(pill(cs.quorate?t('quorumOk'):t('quorumLost'),cs.quorate?'var(--green)':'var(--red)'));
    row.appendChild(pill(t('membersOnline',Number(cs.online)||0,Number(cs.expected)||0),(cs.online>=cs.expected)?'var(--green)':'var(--orange)'));
  }
  if(cp){
    if(cp.down>0)row.appendChild(pill(t('cephOsdDown',Number(cp.down)),'var(--red)'));
    if(cp.out>0)row.appendChild(pill(t('cephOsdOut',Number(cp.out)),'var(--orange)'));
  }
  const ex=dg&&dg.extra;
  if(ex){
    const nbad=(ex.ha&&ex.ha.bad||[]).length;if(nbad)row.appendChild(pill(t('xHa')+': '+nbad,'var(--red)'));
    const rb=(ex.repl&&ex.repl.bad||[]).length;if(rb)row.appendChild(pill(t('xRepl')+': '+rb,'var(--orange)'));
    if(ex.cap&&ex.cap.n1&&!ex.cap.n1.ok)row.appendChild(pill('N-1 ✗','var(--orange)'));
  }
  const bk=dg&&dg.backups;
  if(bk&&bk.rows){
    const bad=bk.rows.filter(r=>r.status==='old'||r.status==='never').length;
    row.appendChild(bad?pill(t('bkProblems',bad),'var(--orange)'):pill(t('bkAllOk'),'var(--green)'));
  }
  box.appendChild(row);
  if(cp&&cp.checks&&cp.checks.length){
    const ul=document.createElement('div');ul.style.cssText='margin-top:8px;font-size:12px;color:var(--text-mid)';
    const h=document.createElement('div');h.style.cssText='font-weight:600;margin-bottom:2px';h.textContent=t('cephChecks');ul.appendChild(h);
    cp.checks.forEach(c=>{const l=document.createElement('div');l.style.cssText='font-family:var(--mono);font-size:11px;color:'+(c.sev==='HEALTH_ERR'?'var(--red)':'var(--orange)');l.textContent=c.code+' — '+c.msg;ul.appendChild(l);});
    box.appendChild(ul);
  }
  const sect=(key,title,fill)=>{
    const h=document.createElement('div');h.style.cssText='margin-top:12px;font-size:12px;font-weight:600;cursor:pointer;color:var(--text-mid);user-select:none';
    h.setAttribute('data-on-click','toggleDiag');h.setAttribute('data-on-click-args',JSON.stringify([key]));
    h.textContent=(_diagShown.has(key)?'▾ ':'▸ ')+title;box.appendChild(h);
    if(_diagShown.has(key)){const b=document.createElement('div');b.style.cssText='margin-top:6px;font-size:12px';fill(b);box.appendChild(b);}
  };
  sect('extra',t('xTitle'),b=>{
    if(!ex){b.style.color='var(--text-dim)';b.textContent=t('xWait');return;}
    const h=(txt)=>{const e=document.createElement('div');e.style.cssText='font-weight:600;margin:10px 0 3px;color:var(--text-mid)';e.textContent=txt;b.appendChild(e);};
    const ln=(txt,col,mono)=>{const e=document.createElement('div');e.style.cssText='padding:1px 0;font-size:11px;'+(mono?'font-family:var(--mono);':'')+(col?'color:'+col+';':'');e.textContent=txt;b.appendChild(e);};
    const er=ex.errors||{};
    if(Object.values(er).includes('perm'))ln('ℹ '+t('xPerm')+' ('+Object.keys(er).filter(k=>er[k]==='perm').join(', ')+')','var(--text-dim)');
    // days until full
    const dk=Object.keys(ex.days||{});
    if(dk.length){h(t('xDays'));dk.sort().forEach(k=>{const d=ex.days[k];const nm=k==='ceph'?t('xCeph'):k.slice(2);
      const w=(ex.days_why||{})[k];ln(nm+' — '+(d!=null?t('xDaysV',d):w&&w[0]==='history'?t('xDaysHist',Math.min(2,w[1])):w&&w[0]==='flat'?t('xDaysFlat'):t('xDaysNone')),d!=null&&d<=3?'var(--red)':d!=null&&d<=14?'var(--orange)':'');});}
    // capacity
    const cap=ex.cap;
    if(cap&&cap.nodes&&cap.nodes.length){h(t('xCap'));
      cap.nodes.forEach(p=>ln(p.node+' — '+t('xVcpu')+' '+p.vcpu+'/'+p.cpus+(p.cpu_ratio!=null?' ('+p.cpu_ratio+'×)':'')+' · '+t('xMemAl')+' '+fmtBytes(p.mem)+'/'+fmtBytes(p.maxmem)+(p.mem_ratio!=null?' ('+Math.round(p.mem_ratio*100)+'%)':''),p.mem_ratio>1?'var(--orange)':''));
      if(cap.n1)ln(cap.n1.ok?'✓ '+t('xN1Ok'):'⚠ '+t('xN1Bad',cap.n1.node,fmtBytes(cap.n1.need),fmtBytes(cap.n1.have)),cap.n1.ok?'var(--green)':'var(--orange)');}
    const lk=Object.entries(ex.locks||{});
    if(lk.length){const now=Date.now()/1000;const old=lk.filter(([v,x])=>now-x.since>=1800);if(old.length){h(t('xLocks'));old.forEach(([v,x])=>ln(v+' — '+t('xLockFor',x.lock,Math.floor((now-x.since)/60)),'var(--orange)'));}}
    // HA
    const ha=ex.ha;if(ha&&ha.services&&ha.services.length){h(t('xHa'));ha.services.forEach(s=>ln(s.sid+' — '+s.state+(s.node?' @ '+s.node:''),['error','fence','recovery','freeze'].includes(s.state)?'var(--red)':'',true));}
    // replication
    const rp=ex.repl;if(rp&&rp.jobs&&rp.jobs.length){h(t('xRepl'));rp.jobs.forEach(j=>ln(j.id+' '+j.node+' → '+j.target+(j.last?' · '+dtFmt(j.last):'')+(j.fails?' · '+t('xFails',j.fails):'')+(j.error?' · '+j.error:''),j.fails||j.error?'var(--orange)':'',true));}
    // ceph
    const ci=ex.ceph;if(ci){h(t('xIo'));
      ln('R '+fmtBytes(ci.read_bps)+'/s · W '+fmtBytes(ci.write_bps)+'/s · '+Math.round(ci.read_ops)+'/'+Math.round(ci.write_ops)+' IOPS'+(ci.recover_bps>0?' · '+t('xRec')+' '+fmtBytes(ci.recover_bps)+'/s':''),'',true);
      if(ci.pgs&&ci.clean<ci.pgs)ln(t('xPg')+': '+(ci.pgs-ci.clean)+'/'+ci.pgs+' — '+ci.states.map(x=>x.n+' '+x.state).join(', '),'var(--orange)',true);}
    // nodes
    const nk=Object.keys(ex.nodes||{});
    if(nk.length){h(t('xNodes'));nk.sort().forEach(k=>{const n=ex.nodes[k];const bits=[];
      if(n.version)bits.push('PVE '+n.version);if(n.kernel)bits.push(n.kernel);if(n.load&&n.load.length)bits.push(t('xLoad')+' '+n.load.join(' / '));
      if(n.swap_total)bits.push(t('xSwap')+' '+Math.round(n.swap_used/n.swap_total*100)+'%');if(n.iowait!=null)bits.push(t('xIow')+' '+(n.iowait*100).toFixed(1)+'%');
      if(n.cert_days!=null)bits.push(t('xCert')+' '+t('xCertD',Math.floor(n.cert_days)));
      ln(k+' — '+bits.join(' · '),n.cert_days!=null&&n.cert_days<=21?'var(--orange)':'',true);});
      if((ex.drift||[]).length)ln('⚠ '+t('xDrift',ex.drift.join(', ')),'var(--orange)');}
    // failed tasks
    h(t('xTasks'));
    if(!(ex.tasks||[]).length)ln(t('xTasksNone'),'var(--text-dim)');
    (ex.tasks||[]).slice(0,10).forEach(x=>ln(dtFmt(x.start)+' '+x.node+' '+x.type+(x.id?' '+x.id:'')+' — '+x.status,'var(--orange)',true));
  });
  sect('reboots',t('rebootsTitle')+(dg&&dg.reboots&&dg.reboots.length?' ('+dg.reboots.length+')':''),b=>{
    const rb=(dg&&dg.reboots)||[];
    if(!rb.length){b.style.color='var(--text-dim)';b.textContent=t('noReboots');return;}
    let lastWave=-1;
    rb.slice(0,30).forEach(r=>{
      const l=document.createElement('div');l.style.cssText='display:flex;gap:10px;padding:3px 0;font-family:var(--mono);font-size:11px;align-items:center';
      const d=document.createElement('span');d.style.color='var(--text-dim)';d.textContent=dtFmt(r.boot);l.appendChild(d);
      const n=document.createElement('strong');n.textContent=String(r.n);l.appendChild(n);
      if(r.wave){l.appendChild(pill('⚠ '+t('rebootWave'),'var(--red)'));}
      b.appendChild(l);
    });
  });
  sect('backups',t('bkTitle'),b=>{
    if(!bk){b.style.color='var(--text-dim)';b.textContent=t('bkWait');return;}
    if(!bk.rows.length&&!(bk.storages||[]).length){b.style.color='var(--text-dim)';b.textContent=t('bkNone');return;}
    const meta=document.createElement('div');meta.style.cssText='color:var(--text-dim);font-size:11px;margin-bottom:4px';
    meta.textContent=t('bkMax',bk.max_age_h)+' · '+(bk.storages||[]).map(s=>s.storage+' ('+s.node+')'+(s.error?' ⚠':'')).join(', ');b.appendChild(meta);
    if(isPveAdmin()){
      const w=document.createElement('div');w.style.cssText='display:flex;gap:6px;align-items:center;margin:0 0 6px;font-size:11px;color:var(--text-dim)';
      const inp=document.createElement('input');inp.type='number';inp.id='bk-days';inp.min='1';inp.max='365';inp.value=String(Math.max(1,Math.round(bk.max_age_h/24)));inp.style.cssText='width:56px;text-align:center';inp.setAttribute('aria-label',t('bkDays'));
      const bt=document.createElement('button');bt.type='button';bt.className='btn-secondary';bt.style.cssText='width:auto;padding:3px 10px;font-size:11px';bt.textContent=t('bkApply');bt.setAttribute('data-on-click','bkSetDays');bt.setAttribute('data-on-click-args',JSON.stringify([cluster.id]));
      const lb=document.createElement('span');lb.textContent=t('bkDays');
      w.appendChild(inp);w.appendChild(lb);w.appendChild(bt);b.appendChild(w);
    }
    (bk.storages||[]).filter(s=>s.error).forEach(s=>{const e=document.createElement('div');e.style.cssText='color:var(--red);font-size:11px';e.textContent=t('bkStorageErr')+': '+s.storage+' — '+s.error;b.appendChild(e);});
    const ST={ok:['bkOk','var(--green)'],old:['bkOld','var(--orange)'],never:['bkNever','var(--red)'],ignored:['bkIgnored','var(--text-dim)'],unknown:['bkUnknown','var(--text-dim)']};
    const sel=bkSelSet(cluster.id);
    if(isPveAdmin()&&bk.rows.length){
      const tb=document.createElement('div');tb.style.cssText='display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:4px 0 6px;font-size:11px';
      const lk=(txt,fn,args)=>{const a=document.createElement('span');a.style.cssText='cursor:pointer;color:var(--blue)';a.textContent=txt;a.setAttribute('data-on-click',fn);a.setAttribute('data-on-click-args',JSON.stringify(args));tb.appendChild(a);};
      lk(t('bkSelAll'),'bkSelMode',[cluster.id,'all']);lk(t('bkSelPending'),'bkSelMode',[cluster.id,'pending']);if(sel.size)lk(t('bkSelNone'),'bkSelMode',[cluster.id,'none']);
      if(sel.size){
        const ig=new Set(bk.ignore||[]);const nIgn=[...sel].filter(v=>ig.has(v)).length;
        if(sel.size-nIgn>0){const x=document.createElement('button');x.className='btn-sec';x.style.cssText='font-size:11px;padding:3px 10px';x.textContent=t('bkIgnoreSel',sel.size-nIgn);x.setAttribute('data-on-click','bkBulk');x.setAttribute('data-on-click-args',JSON.stringify([cluster.id,true]));tb.appendChild(x);}
        if(nIgn>0){const x=document.createElement('button');x.className='btn-sec';x.style.cssText='font-size:11px;padding:3px 10px';x.textContent=t('bkUnignoreSel',nIgn);x.setAttribute('data-on-click','bkBulk');x.setAttribute('data-on-click-args',JSON.stringify([cluster.id,false]));tb.appendChild(x);}
      }
      b.appendChild(tb);
    }
    bk.rows.forEach(r=>{
      const l=document.createElement('div');l.style.cssText='display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:2px 0;font-size:11px';
      if(isPveAdmin()&&r.status!=='unknown'){const cb=document.createElement('input');cb.type='checkbox';cb.checked=sel.has(r.vmid);cb.setAttribute('data-on-click','bkSelToggle');cb.setAttribute('data-on-click-args',JSON.stringify([cluster.id,r.vmid]));l.appendChild(cb);}
      const id=document.createElement('span');id.style.cssText='font-family:var(--mono);min-width:48px';id.textContent=(r.type==='ct'?'CT ':'VM ')+r.vmid;l.appendChild(id);
      const nm=document.createElement('span');nm.style.cssText='min-width:140px';nm.textContent=r.name||'';l.appendChild(nm);
      const s=ST[r.status]||ST.unknown;l.appendChild(pill(t(s[0]),s[1]));
      const bits=[];
      if(r.age!=null)bits.push(t('bkAge',Math.floor(r.age/3600)));
      if(r.size)bits.push(fmtBytes(r.size));
      if(r.storage)bits.push(r.storage);
      if(r.count>1)bits.push(t('bkCopies',r.count));
      const x=document.createElement('span');x.style.color='var(--text-mid)';x.textContent=bits.join(' · ');l.appendChild(x);
      if(r.verify==='ok')l.appendChild(pill(t('bkVerified'),'var(--green)'));
      if(r.verify==='failed')l.appendChild(pill(t('bkVerFail'),'var(--red)'));
      if(isPveAdmin()&&r.status!=='unknown'){
        const a=document.createElement('span');a.style.cssText='cursor:pointer;color:var(--blue);margin-left:auto';a.textContent=r.status==='ignored'?t('bkUnignore'):t('bkIgnore');
        a.setAttribute('data-on-click','toggleBkIgnore');a.setAttribute('data-on-click-args',JSON.stringify([cluster.id,r.vmid]));l.appendChild(a);
      }
      b.appendChild(l);
    });
    const bad=(bk.tasks||[]).filter(x=>x.ok===false).slice(0,8);
    if(bad.length){
      const h=document.createElement('div');h.style.cssText='margin-top:8px;font-weight:600;color:var(--red)';h.textContent=t('bkFailedTasks');b.appendChild(h);
      bad.forEach(x=>{const l=document.createElement('div');l.style.cssText='font-family:var(--mono);font-size:11px;color:var(--text-mid)';l.textContent=dtFmt(x.start)+' · '+x.node+(x.vmid?' · VM '+x.vmid:'')+' · '+x.status;b.appendChild(l);});
    }
  });
  sect('smart',t('smartTitle'),b=>{
    const sm=dg&&dg.smart;
    if(!sm){b.style.color='var(--text-dim)';b.textContent=t('smartWait');return;}
    const nodes=Object.keys(sm.nodes||{}).sort();
    if(!nodes.some(n=>(sm.nodes[n].disks||[]).length)&&!nodes.some(n=>sm.nodes[n].error)){b.style.color='var(--text-dim)';b.textContent=t('smartNone');return;}
    const age=document.createElement('div');age.style.cssText='color:var(--text-dim);font-size:11px;margin-bottom:4px';age.textContent=t('smartAge',Math.max(0,Math.round((Date.now()/1000-sm.ts)/60)));b.appendChild(age);
    const WT={health:'wHealth',media:'wMedia',critwarn:'wCritwarn',sectors:'wSectors',realloc:'wRealloc',wear:'wWear',spare:'wSpare'};
    nodes.forEach(n=>{
      const nh=document.createElement('div');nh.style.cssText='font-weight:600;margin:6px 0 2px';nh.textContent=n+(sm.nodes[n].error?' — '+t('nodeErr'):'');b.appendChild(nh);
      (sm.nodes[n].disks||[]).forEach(d=>{
        const l=document.createElement('div');l.style.cssText='display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:2px 0;font-size:11px';
        const nm=document.createElement('span');nm.style.cssText='font-family:var(--mono);min-width:110px';nm.textContent=d.dev;l.appendChild(nm);
        const md=document.createElement('span');md.style.cssText='color:var(--text-dim);min-width:120px';md.textContent=d.model||'';l.appendChild(md);
        l.appendChild(pill(d.health||'?',(d.health==='PASSED'||d.health==='OK')?'var(--green)':d.health==='UNKNOWN'?'var(--text-dim)':'var(--red)'));
        const bits=[];
        if(d.used_pct!=null)bits.push(t('smartWear')+' '+d.used_pct+'%');else if(d.wearout!=null)bits.push(t('smartWear')+' '+(100-d.wearout)+'%');
        if(d.temp!=null)bits.push(t('smartTemp')+' '+d.temp+'°');
        if(d.unsafe!=null)bits.push(t('smartUnsafe')+' '+d.unsafe);
        if(d.media_err)bits.push(t('smartErrs')+' '+d.media_err);
        const x=document.createElement('span');x.style.color='var(--text-mid)';x.textContent=bits.join(' · ');l.appendChild(x);
        (d.warns||[]).forEach(w=>l.appendChild(pill(t(WT[w]||'wHealth'),'var(--orange)')));
        b.appendChild(l);
      });
    });
  });
  return box;
}

// ── Manual node order + pins (saved on the server, shared by all browsers) ────────
// Orden manual y nodos fijados: se guardan en el servidor junto al cluster, así todos los navegadores ven lo mismo. Solo el admin puede cambiarlos.
// EN: Manual order and pinned nodes: stored on the server with the cluster, so every browser sees the same. Only the admin can change them.
let _dragging=false;
const isPveAdmin=()=>ME?.permissions?.pve==='admin';
// Nodos en el orden guardado; los nodos nuevos o desconocidos van al final, en orden natural (pve2 antes que pve10). No depende del orden en que responda la API.
// EN: Nodes in the saved order; new or unknown nodes go last, in natural order (pve2 before pve10). It does not depend on the order the API answers in.
function orderedNodes(cluster,nodes){
  const idx=new Map((cluster.layout?.order||[]).map((n,i)=>[n,i]));
  const pos=n=>idx.has(n.name)?idx.get(n.name):1e6;        // unknown/new nodes go last, in the server's stable order
  const nat=(a,b)=>a.name.localeCompare(b.name,undefined,{numeric:true,sensitivity:'base'});
  return [...nodes].sort((a,b)=>pos(a)-pos(b)||nat(a,b));      // never depends on the order the API returns
}
// Pinned nodes keep their slot; the others are redistributed among the remaining slots.
// Calcula el nuevo orden al arrastrar una tarjeta sobre otra: los nodos fijados conservan su posición y los demás se mueven alrededor.
// EN: Compute the new order when dragging one card over another: pinned nodes keep their position and the others move around them.
function reorderNames(names,pinned,drag,target){
  if(drag===target||pinned.has(drag))return names;
  const unp=names.filter(n=>!pinned.has(n)&&n!==drag);
  const forward=names.indexOf(drag)<names.indexOf(target);
  let ins;
  if(pinned.has(target)) ins=names.slice(0,names.indexOf(target)).filter(n=>!pinned.has(n)&&n!==drag).length;
  else ins=unp.indexOf(target)+(forward?1:0);
  unp.splice(ins,0,drag);
  let k=0;
  return names.map(n=>pinned.has(n)?n:unp[k++]);
}
// Guarda el orden y los fijados en el servidor.
// EN: Save the order and the pins on the server.
async function saveLayout(cluster,order,pinned){
  cluster.layout={order,pinned};
  renderDashboard();
  try{
    const r=await fetch('api/clusters/'+cluster.id+'/layout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({order,pinned})});
    if(!r.ok)throw new Error((await r.json()).error||'Error');
  }catch(e){toast(e.message,true);}
}
function curLayout(cid){
  const c=clusters.find(x=>x.id===cid);
  const names=orderedNodes(c,c.snap?.data?.nodes||[]).map(n=>n.name);
  return {c,names,pinned:new Set(c.layout?.pinned||[])};
}
// Fija o suelta un nodo.
// EN: Pin or unpin a node.
function togglePin(cid,name){
  const {c,names,pinned}=curLayout(cid);
  pinned.has(name)?pinned.delete(name):pinned.add(name);
  saveLayout(c,names,[...pinned]);
}
// Mueve un nodo una posición con los botones (alternativa al arrastre, útil en pantallas táctiles).
// EN: Move a node one position with the buttons (alternative to dragging, useful on touch screens).
function moveNode(cid,name,dir){
  const {c,names,pinned}=curLayout(cid);
  let i=names.indexOf(name)+dir;
  while(i>=0&&i<names.length&&pinned.has(names[i]))i+=dir;      // skip over pinned nodes
  if(i<0||i>=names.length)return;
  saveLayout(c,reorderNames(names,pinned,name,names[i]),[...pinned]);
}
function resetLayout(cid){const c=clusters.find(x=>x.id===cid);saveLayout(c,[],[]);}
function decorateCard(card,cluster,name,names,pinned){
  const hd=card.querySelector('.node-hd');if(!hd)return;
  const isPinned=pinned.has(name), admin=isPveAdmin(), cid=esc(cluster.id), nm=esc(name);
  const i=names.indexOf(name);
  const canL=names.slice(0,i).some(n=>!pinned.has(n)), canR=names.slice(i+1).some(n=>!pinned.has(n));
  const tools=document.createElement('div');tools.className='node-tools';
  tools.innerHTML=admin
    ?`<button class="node-tool" ${isPinned||!canL?'disabled':''} title="${esc(t('moveEarlier'))}" data-on-click="moveNode" data-on-click-args="${jsargs([cluster.id,name,-1])}">‹</button>
      <button class="node-tool" ${isPinned||!canR?'disabled':''} title="${esc(t('moveLater'))}" data-on-click="moveNode" data-on-click-args="${jsargs([cluster.id,name,1])}">›</button>
      ${isPinned?'':`<span class="node-tool grab" title="${esc(t('dragReorder'))}" data-grab>⠿</span>`}
      <button class="node-tool pin${isPinned?' on':''}" title="${esc(t(isPinned?'unpinNode':'pinNode'))}" data-on-click="togglePin" data-on-click-args="${jsargs([cluster.id,name])}">${isPinned?'📌':'📍'}</button>`
    :(isPinned?`<span class="node-tool pin on" title="${esc(t('unpinNode'))}">📌</span>`:'');
  const badge=hd.querySelector('.node-badge');
  hd.insertBefore(tools,badge);
  if(!admin)return;
  const grab=tools.querySelector('[data-grab]');
  if(grab){
    grab.addEventListener('mousedown',()=>{card.draggable=true;});
    grab.addEventListener('mouseup',()=>{card.draggable=false;});
  }
  card.addEventListener('dragstart',e=>{
    if(!card.draggable){e.preventDefault();return;}
    _dragging=true;card.classList.add('dragging');e.dataTransfer.setData('text/plain',name);e.dataTransfer.effectAllowed='move';
  });
  card.addEventListener('dragend',()=>{_dragging=false;card.draggable=false;card.classList.remove('dragging');
    document.querySelectorAll('.drop-target').forEach(x=>x.classList.remove('drop-target'));renderDashboard();});
  card.addEventListener('dragover',e=>{if(!_dragging)return;e.preventDefault();card.classList.add('drop-target');});
  card.addEventListener('dragleave',()=>card.classList.remove('drop-target'));
  card.addEventListener('drop',e=>{
    e.preventDefault();card.classList.remove('drop-target');
    const drag=e.dataTransfer.getData('text/plain');
    _dragging=false;
    if(drag&&drag!==name)saveLayout(cluster,reorderNames(names,pinned,drag,name),[...pinned]);
  });
}

// Tarjeta de un nodo: CPU, RAM, disco, tiempo encendido, gráfico pequeño y secciones de VMs y contenedores.
// EN: Node card: CPU, RAM, disk, uptime, small chart and sections for VMs and containers.
function buildNodeCard(node,cluster){
  const card=document.createElement('div');card.className='node-card';
  const isOpen=!!cluster&&node.status==='online'&&_nOpen.has(nkey(cluster.id,node.name));
  if(isOpen)card.classList.add('open');
  const isOnline=node.status==='online';
  const cpuPct=Math.round((node.cpu||0)*100);
  const memPct=node.maxmem?Math.round((node.mem/node.maxmem)*100):0;
  const diskPct=node.maxdisk?Math.round((node.disk/node.maxdisk)*100):0;
  const allVMs=(node.vms||[]);
  const allCTs=(node.cts||[]);
  const runVMs=allVMs.filter(v=>v.status==='running').length;
  const runCTs=allCTs.filter(v=>v.status==='running').length;

  card.innerHTML=`
    <div class="node-hd">
      <div>
        <div class="node-name${cluster?' clickable':''}"${cluster?` data-on-click="toggleNode" data-on-click-args="${jsargs([cluster.id,node.name])}" title="${esc(t('ndExpand'))}"`:''}>${cluster&&isOnline?`<span class="node-chev">${isOpen?'▾':'▸'}</span>`:''}${esc(node.name)}</div>
        <div class="node-sub">${allVMs.length} VMs · ${allCTs.length} CTs · uptime: ${fmtUptime(node.uptime)}</div>
      </div>
      <span class="node-badge ${isOnline?'badge-online':'badge-offline'}">${isOnline?'Online':'Offline'}</span>
    </div>
    ${isOnline?`
    ${cpuPct>80||memPct>90?`<div style="padding:6px 12px 0"><div style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);border-radius:4px;padding:6px 10px;font-size:11px;color:var(--red);font-weight:600">
      ⚠ ${cpuPct>80?t('cpuAlert',cpuPct):''} ${cpuPct>80&&memPct>90?' · ':''} ${memPct>90?t('ramAlert',memPct):''}
    </div></div>`:''}
    <div class="res-bars">
      <div class="res-row">
        <span class="res-lbl">CPU</span>
        <div class="res-bar-wrap"><div class="res-bar" style="width:${cpuPct}%;background:${cpuPct>85?'var(--red)':cpuPct>60?'var(--orange)':'var(--blue)'}"></div></div>
        <span class="res-val">${cpuPct}% / ${esc(node.maxcpu??'?')} cores</span>
      </div>
      <div class="res-row">
        <span class="res-lbl">RAM</span>
        <div class="res-bar-wrap"><div class="res-bar" style="width:${memPct}%;background:${memPct>85?'var(--red)':memPct>70?'var(--orange)':'var(--green)'}"></div></div>
        <span class="res-val">${memPct}% / ${fmtBytes(node.maxmem)}</span>
      </div>
      <div class="res-row">
        <span class="res-lbl">Disk</span>
        <div class="res-bar-wrap"><div class="res-bar" style="width:${diskPct}%;background:${diskPct>85?'var(--red)':diskPct>70?'var(--orange)':'var(--text-dim)'}"></div></div>
        <span class="res-val">${diskPct}% / ${fmtBytes(node.maxdisk)}</span>
      </div>
    </div>
    ${isOpen?buildNodePanel(cluster.id,node):''}
    ${!isOpen&&node.history?.length>2?`<div style="padding:4px 12px 8px">
      <div style="font-size:10px;color:var(--text-dim);margin-bottom:3px;font-weight:500">${t('historyChart')}</div>
      <canvas id="spark-${esc(node.name)}" height="32" style="width:100%;height:32px;display:block;border-radius:4px;background:var(--bg)"></canvas>
    </div>`:''}
    ${buildVMSection(allVMs, 'VM', runVMs, node.name)}
    ${buildVMSection(allCTs, 'CT', runCTs, node.name)}
    `:`<div style="padding:20px;text-align:center;color:var(--text-dim);font-size:12px">${t('nodeOfflineMsg')}</div>`}`;
  return card;
}


// ── Detalle de un nodo: métricas, sistema y gráficos con rangos (el historial lo entrega Proxmox) ──
// EN: Node detail: metrics, system and charts with ranges (the history comes from Proxmox itself).
const _nOpen=new Set((()=>{try{return JSON.parse(localStorage.getItem('pve-open-nodes')||'[]');}catch(e){return [];}})());
const _nd={}, _nrd={}, _nbusy={};                 // detalle «cid|nodo» → {ts,d,err}; series «cid|nodo|rango» → {ts,pts}
const _nrange={cpu:'1d',mem:'1d',load:'1d',net:'1d'};
const nkey=(cid,name)=>cid+'|'+name;
const nid=(cid,name,kind)=>'nch-'+kind+'-'+String(cid+'-'+name).replace(/[^a-z0-9]/gi,'-');
const fmtBps=v=>fmtBytes(v)+'/s';
const NCH={
  cpu:{title:'ndChCpu',max:100,series:[{k:'cpu',c:'#4361ee',l:'ndSCpu',f:v=>v.toFixed(1)+'%'},{k:'iowait',c:'#f97316',l:'ndSIo',f:v=>v.toFixed(2)+'%'}],axis:v=>Math.round(v)+'%',h:130,pl:40},
  mem:{title:'ndChMem',max:100,series:[{k:'mem',c:'#22c55e',l:'ndSRam',f:v=>v.toFixed(1)+'%'},{k:'swap',c:'#a855f7',l:'ndSSwap',f:v=>v.toFixed(1)+'%'}],axis:v=>Math.round(v)+'%',h:130,pl:40},
  load:{title:'ndChLoad',series:[{k:'load',c:'#f59e0b',l:'ndSLoad',f:v=>v.toFixed(2)}],axis:v=>v.toFixed(1),h:120,pl:40},
  net:{title:'ndChNet',series:[{k:'netin',c:'#22c55e',l:'ndSIn',f:fmtBps},{k:'netout',c:'#4361ee',l:'ndSOut',f:fmtBps}],axis:fmtBps,h:120,pl:64},
};
function saveOpen(){try{localStorage.setItem('pve-open-nodes',JSON.stringify([..._nOpen]));}catch(e){}}
function toggleNode(cid,name){
  const k=nkey(cid,name);
  if(_nOpen.has(k))_nOpen.delete(k);else _nOpen.add(k);
  saveOpen();
  if(_nOpen.has(k))loadNode(cid,name,true);
  renderDashboard();
}
async function loadNode(cid,name,force){
  const k=nkey(cid,name),c=_nd[k];
  if(!force&&c&&Date.now()-c.ts<30000)return;
  if(_nbusy[k])return;_nbusy[k]=true;
  try{
    const r=await fetch('api/clusters/'+encodeURIComponent(cid)+'/nodes/'+encodeURIComponent(name)+'/detail');
    if(r.ok){const d=await r.json();_nd[k]={ts:Date.now(),d:d.detail,err:null};}
    else _nd[k]={ts:Date.now(),d:(c&&c.d)||null,err:r.status};
  }catch(e){_nd[k]={ts:Date.now(),d:(c&&c.d)||null,err:-1};}
  finally{_nbusy[k]=false;}
  if(_nOpen.has(k))renderDashboard();
  Object.keys(NCH).forEach(kind=>loadNodeRange(cid,name,_nrange[kind]));
}
async function loadNodeRange(cid,name,range,force){
  const key=nkey(cid,name)+'|'+range,c=_nrd[key],ttl=range==='1h'?30000:120000;
  if(!force&&c&&Date.now()-c.ts<ttl)return;
  if(_nbusy[key])return;_nbusy[key]=true;
  try{
    const r=await fetch('api/clusters/'+encodeURIComponent(cid)+'/nodes/'+encodeURIComponent(name)+'/rrd?range='+range);
    if(r.ok){const d=await r.json();_nrd[key]={ts:Date.now(),pts:d.history||[]};drawNodeCharts(cid,name);}
  }catch(e){console.error(e);}
  finally{_nbusy[key]=false;}
}
// Pide lo que falta de los nodos abiertos (cada ~30 s) y dibuja sus gráficos tras cada pintado del panel.
// EN: Fetch what is missing for the open nodes (every ~30 s) and draw their charts after each panel paint.
function refreshOpenNodes(cluster,nodes){
  nodes.forEach(n=>{
    if(n.status!=='online'||!_nOpen.has(nkey(cluster.id,n.name)))return;
    loadNode(cluster.id,n.name,false);
    requestAnimationFrame(()=>drawNodeCharts(cluster.id,n.name));
  });
}
function setNRange(btn,cid,name,kind,range){
  _nrange[kind]=range;
  document.querySelectorAll('.nd-ch-'+kind+' .vchart-filter').forEach(b=>b.classList.toggle('active',b.dataset.range===range));
  if(_nrd[nkey(cid,name)+'|'+range])drawNodeCharts(cid,name);
  loadNodeRange(cid,name,range,true);
}
function drawNodeCharts(cid,name,hover){
  Object.keys(NCH).forEach(kind=>{
    const cv=document.getElementById(nid(cid,name,kind));if(!cv)return;
    const C=NCH[kind],range=_nrange[kind];
    VC.draw(cv,{pts:((_nrd[nkey(cid,name)+'|'+range]||{}).pts||[]),series:C.series.map(x=>({k:x.k,c:x.c,l:t(x.l),f:x.f})),range:range,hover:-1,h:C.h,pl:C.pl,max:C.max,axis:C.axis});
  });
}
window.addEventListener('resize',()=>{_nOpen.forEach(k=>{const i=k.indexOf('|');drawNodeCharts(k.slice(0,i),k.slice(i+1));});});
const dash='—';
const OTH={PveMod_systemInfo:'ndInfo',PveMod_Version:'ndPveMod',PveMod_upsInfo:'ndUps'},SYS_MOD=['PveMod_Version','PveMod_systemInfo'];
function nrow(label,value,pct,cls){
  const bar=pct==null?'':`<div class="nd-bar"><div style="width:${Math.max(0,Math.min(100,pct))}%;background:${pct>85?'var(--red)':pct>70?'var(--orange)':'var(--blue)'}"></div></div>`;
  return `<div class="nd-row"><span class="nd-l">${esc(label)}</span><span class="nd-v${cls?' '+cls:''}">${value==null||value===''?dash:esc(value)}${bar}</span></div>`;
}
const pctOf=(u,tot)=>(u!=null&&tot)?Math.round(u/tot*1000)/10:null;
function buildNodePanel(cid,node){
  const c=_nd[nkey(cid,node.name)],d=c&&c.d;
  if(!d)return `<div class="nd"><div class="nd-msg">${esc(c&&c.err?t('ndErr'):t('ndLoading'))}</div></div>`;
  const cpus=d.cpuinfo.cpus||node.maxcpu;
  const mp=pctOf(d.mem.used,d.mem.total),sp=pctOf(d.swap.used,d.swap.total),rp=pctOf(d.root.used,d.root.total);
  const sec=(title,rows)=>`<div class="nd-sec"><div class="nd-title">${esc(title)}</div>${rows}</div>`;
  const perm=k=>d.errors&&d.errors[k]==='perm'?t('ndPerm'):null;
  const primary=sec(t('ndPrimary'),
    nrow(t('ndCpu'),d.cpu==null?null:d.cpu.toFixed(2)+'% '+t('ndOfCpus',cpus||'?'),d.cpu)+
    nrow(t('ndRam'),mp==null?null:mp+'% ('+fmtBytes(d.mem.used)+' / '+fmtBytes(d.mem.total)+')',mp)+
    nrow(t('ndKsm'),d.ksm==null?null:fmtBytes(d.ksm))+
    nrow(t('ndSwap'),sp==null?null:sp+'% ('+fmtBytes(d.swap.used)+' / '+fmtBytes(d.swap.total)+')',d.swap.total?sp:null)+
    nrow(t('ndDisk'),rp==null?null:rp+'% ('+fmtBytes(d.root.used)+' / '+fmtBytes(d.root.total)+')',rp));
  const ci=d.cpuinfo, model=[ci.model,ci.sockets?(ci.sockets+'×'+(ci.cores||'?')+' cores'):'',ci.mhz?Math.round(ci.mhz)+' MHz':''].filter(Boolean).join(' · ');
  const secondary=sec(t('ndSecondary'),
    nrow(t('ndLoadAvg'),d.load.length?d.load.map(x=>x.toFixed(2)).join(', '):null)+
    nrow(t('ndIowait'),d.iowait==null?null:d.iowait.toFixed(2)+'%')+
    nrow(t('ndCpuModel'),model)+
    d.other.filter(o=>!SYS_MOD.includes(o.k)).map(o=>nrow(OTH[o.k]?t(OTH[o.k]):o.k,o.v)).join(''));
  const sub=d.subscription?[d.subscription.status,d.subscription.level,d.subscription.product,d.subscription.due].filter(Boolean).join(' · '):perm('subscription');
  const bad=d.services.filter(x=>x.bad),run=d.services.filter(x=>x.state==='running').length,off=d.services.length-run-bad.length;
  const system=sec(t('ndSystem'),
    nrow(t('ndKernel'),d.kernel)+nrow(t('ndBoot'),d.boot.mode?(d.boot.mode.toUpperCase()+(d.boot.secureboot==null?'':' ('+(d.boot.secureboot?'Secure Boot':'no Secure Boot')+')')):null)+
    nrow(t('ndManager'),d.pveversion||d.version)+nrow(t('ndUptime'),fmtUptime(d.uptime))+
    nrow(t('ndTz'),d.timezone)+nrow(t('ndDns'),[d.dns.search,...d.dns.servers].filter(Boolean).join(' · '))+
    nrow(t('ndSub'),sub)+nrow(t('ndUpdates'),d.updates==null?perm('apt'):String(d.updates))+
    d.other.filter(o=>SYS_MOD.includes(o.k)).map(o=>nrow(t(OTH[o.k]),o.k==='PveMod_systemInfo'&&d.serial?o.v+' | Serial: '+d.serial:o.v)).join(''));
  const lists=[];
  const SG=[['cpu','ndSnCpu',1],['nvme','ndSnNvme',1],['other','ndSnOther',1],['fans','ndSnFans',0]];
  SG.forEach(([g,k,tmp])=>{const rows=(d.sensors||[]).filter(x=>x.g===g);if(rows.length)lists.push(sec(t(k),rows.map(x=>nrow(x.l,tmp?x.v+' °'+d.temp_unit+(x.mx||x.cr?' ('+[x.mx?'max '+x.mx:'',x.cr?'crit '+x.cr:''].filter(Boolean).join(', ')+')':''):Math.round(x.v)+' RPM'+(x.mx?' (max '+x.mx+')':''))).join('')));});
  if(d.disks.length)lists.push(sec(t('ndDisks'),d.disks.map(x=>nrow(x.dev+(x.model?' · '+x.model:''),[x.type,x.size?fmtBytes(x.size):'',x.health,x.wearout&&x.wearout!=='N/A'?x.wearout+'%':''].filter(Boolean).join(' · '))).join('')));
  if(d.net.length)lists.push(sec(t('ndNetIf'),d.net.map(x=>nrow(x.iface+' ('+x.type+')',[x.address,x.gateway?'gw '+x.gateway:'',x.ports,x.active?'':'down'].filter(Boolean).join(' · '))).join('')));
  if(d.services.length)lists.push(sec(t('ndServices'),nrow(t('ndServState'),run+' '+t('ndRunning')+(off?' · '+off+' '+t('ndInactive'):''))+bad.map(x=>nrow(x.name,x.state,null,'bad')).join('')));
  const charts=Object.keys(NCH).map(kind=>{
    const C=NCH[kind],cvid=nid(cid,node.name,kind);
    return `<div class="nd-ch nd-ch-${kind}">`+VC.section({title:t(C.title),legend:C.series.map(x=>({c:x.c,l:t(x.l)})),
      filters:VC.filters(_nrange[kind],r=>`data-on-click="setNRange" data-on-click-args="${jsargs([{'@':'this'},cid,node.name,kind,r])}"`,null,false),
      canvasId:cvid,tipId:cvid+'-tip',h:C.h})+`</div>`;
  }).join('');
  return `<div class="nd"><div class="nd-grid">${primary}${secondary}${system}</div>${lists.length?`<div class="nd-grid">${lists.join('')}</div>`:''}<div class="nd-charts">${charts}</div><div class="nd-note">${esc(t('ndRangeNote'))}</div></div>`;
}

// Gráfico pequeño de CPU y RAM de las últimas ~12 horas, dibujado en un canvas.
// EN: Small CPU and RAM chart of the last ~12 hours, drawn on a canvas.
function drawSparkline(nodeId, history){
  const canvas=document.getElementById('spark-'+nodeId);
  if(!canvas||!history?.length) return;
  const W=canvas.offsetWidth||canvas.parentElement?.offsetWidth||300;
  canvas.width=W; canvas.height=32;
  const ctx=canvas.getContext('2d');
  const max=history.length;
  if(max<2) return;
  // Draw CPU (blue) and RAM (green)
  ['cpu','mem'].forEach((key,ki)=>{
    const color=ki===0?'rgba(67,97,238,0.8)':'rgba(34,197,94,0.6)';
    ctx.beginPath();
    history.forEach((pt,i)=>{
      const x=Math.round((i/(max-1))*W);
      const y=Math.round(32-((pt[key]||0)/100)*28)-2;
      i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
    });
    ctx.strokeStyle=color; ctx.lineWidth=1.5; ctx.stroke();
  });
}

function renderSparklines(nodes){
  requestAnimationFrame(()=>{
    nodes.forEach(n=>{
      if(n.history?.length>2) drawSparkline(n.name, n.history);
    });
  });
}

// Lista desplegable de VMs o contenedores de un nodo, con estado, CPU y RAM.
// EN: Collapsible list of a node's VMs or containers, with state, CPU and RAM.
function buildVMSection(items, type, running, nodeName){
  if(!items.length) return '';
  const id='sec-'+String(nodeName).replace(/[^\w-]/g,'_')+'-'+type;   // stable id: collapsed state survives refreshes
  const open=!_collapsed.has(id);
  const shown=_hideStopped?items.filter(v=>v.status==='running'||v.status==='paused'):items;
  const sorted=[...shown].sort((a,b)=>{
    if(a.status==='running'&&b.status!=='running')return-1;
    if(b.status==='running'&&a.status!=='running')return 1;
    return(a.vmid||0)-(b.vmid||0);
  });
  return `<div>
    <div class="section-hd" data-on-click="toggleSection" data-on-click-args="${jsargs([id])}">
      <span class="section-title">${type === 'VM' ? t('sectionVMs') : t('sectionCTs')}</span>
      <div style="display:flex;align-items:center;gap:8px">
        <span class="section-count">${running}/${items.length} ${t('running')}</span>
        <span class="section-arrow${open?' open':''}" id="arr-${id}">▶</span>
      </div>
    </div>
    <div class="section-body${open?' show':''}" id="${id}">
      <div class="vm-list">
        ${sorted.map(v=>{
          const cpuPct=Math.round((v.cpu||0)*100);
          const memPct=v.maxmem?Math.round((v.mem/v.maxmem)*100):0;
          const dotCls=v.status==='running'?'running':v.status==='paused'?'paused':'stopped';
          return `<div class="vm-row">
            <span class="vm-dot ${dotCls}"></span>
            <span class="vm-id">${esc(v.vmid)}</span>
            <span class="vm-main"><span class="vm-name" title="${esc(v.name||'')}" data-nethost="${esc(guestHost(v))}" data-nethost-click="1">${esc(v.name||'—')}${v.lock==='migrate'?' <span title="migrating" style="color:var(--orange)">⇄</span>':v.lock?' <span title="lock: '+esc(v.lock)+'" style="color:var(--orange)">🔒</span>':''}</span>${v.status==='running'?`<span class="vm-meta">${cpuPct}% · ${fmtBytes(v.mem||0)} · ${fmtUptime(v.uptime)}</span>`:''}</span>
            <span class="vm-type ${esc(String(type).toLowerCase().replace(/[^a-z0-9_-]/g,''))}">${esc(type)}</span>
            ${v.status==='running'?'':`<span class="vm-state">${esc(v.status)}</span>`}
          </div>`;
        }).join('')}
      </div>
    </div>
  </div>`;
}

// Botón de la barra superior: oculta o muestra las VM y contenedores detenidos (se recuerda en el navegador).
// EN: Top-bar button: hides or shows stopped VMs and containers (remembered in the browser).
function stoppedBtn(){
  const b=document.getElementById('tb-stopped'); if(b)b.textContent=_hideStopped?t('showStopped'):t('hideStopped');
}
function toggleStopped(){
  _hideStopped=!_hideStopped;
  try{localStorage.setItem('pi-px-hide-stopped',_hideStopped?'1':'0');}catch(e){}
  stoppedBtn(); renderDashboard();
}

function toggleSection(id){
  const body=document.getElementById(id);
  const arr=document.getElementById('arr-'+id);
  if(!body||!arr)return;
  const isOpen=body.classList.contains('show');
  body.classList.toggle('show',!isOpen);
  if(isOpen)_collapsed.add(id); else _collapsed.delete(id);
  arr.classList.toggle('open',!isOpen);
}

// ── Add cluster ───────────────────────────────────────────────────────────────
// AGREGAR CLUSTER (dos pasos, por seguridad del certificado). 1.º «Probar»: se muestra la huella SHA-256 del certificado que presenta el servidor, sin enviar todavía el token. 2.º El administrador la compara y vuelve a pulsar «Probar»: se prueba con esa huella fijada. Solo entonces se puede guardar.
// EN: ADD CLUSTER (two steps, for certificate security). 1st "Test": the SHA-256 fingerprint of the certificate the server presents is shown, without sending the token yet. 2nd The administrator compares it and presses "Test" again: it is tested with that fingerprint pinned. Only then can it be saved.
function openAddCluster(){document.getElementById('add-overlay').classList.add('show');document.getElementById('f-name').focus();}

// Huella mostrada al administrador en el diálogo; se invalida si cambia host o puerto.
// EN: Fingerprint shown to the administrator in the dialog; invalidated if host or port changes.
let pendingFp=null;                                          // certificate shown to the admin in the add dialog
// Paso 1 o 2 según haya una huella pendiente (ver arriba).
// EN: Step 1 or 2 depending on whether a fingerprint is pending (see above).
async function testCluster(){
  const btn=document.getElementById('btn-test'),res=document.getElementById('test-result');
  const host=document.getElementById('f-host').value.trim();
  const port=parseInt(document.getElementById('f-port').value)||8006;
  const user=document.getElementById('f-user').value.trim();
  const tname=document.getElementById('f-tname').value.trim();
  const tval=document.getElementById('f-tval').value.trim();
  if(!host||!user||!tname||!tval){res.className='test-result fail show';res.textContent='✕ '+t('testFillAll');return;}
  btn.innerHTML='<span class="spin">⟳</span>';btn.disabled=true;
  try{
    if(!pendingFp||pendingFp.hp!==host+':'+port){          // step 1: show the certificate, token not sent yet
      const r0=await fetch('api/fingerprint',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({host,port})});
      const d0=await r0.json();
      if(!d0.ok){res.className='test-result fail show';res.textContent='✕ '+(d0.error||'Error');return;}
      pendingFp={hp:host+':'+port,fp:d0.fingerprint,confirmed:false};
      res.className='test-result show';res.textContent=t('fpConfirm',d0.fingerprint);return;
    }
    pendingFp.confirmed=true;                               // step 2: pinned test
    const r=await fetch('api/test',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({host,port,user,token_name:tname,token_value:tval,fingerprint:pendingFp.fp})});
    const d=await r.json();
    if(d.ok){res.className='test-result ok show';res.textContent=t('testConnected',d.version,d.nodes);log('OK','Test OK: '+host);}
    else{res.className='test-result fail show';res.textContent='✕ '+d.error;}
  }catch(e){res.className='test-result fail show';res.textContent='✕ '+e.message;}
  finally{btn.disabled=false;btn.textContent=t('test');}
}

// Guarda el cluster junto con la huella confirmada; el servidor rechaza el alta sin ella.
// EN: Save the cluster together with the confirmed fingerprint; the server rejects adding without it.
async function saveCluster(){
  const name=document.getElementById('f-name').value.trim();
  const host=document.getElementById('f-host').value.trim();
  const port=parseInt(document.getElementById('f-port').value)||8006;
  const user=document.getElementById('f-user').value.trim();
  const tname=document.getElementById('f-tname').value.trim();
  const tval=document.getElementById('f-tval').value.trim();
  const btn=document.getElementById('btn-save');
  if(!name||!host||!user||!tname||!tval){toast(t('testFillAll'),true);return;}
  if(!pendingFp||!pendingFp.confirmed){toast(t('fpNeedTest'),true);return;}
  if(pendingFp.hp!==host+':'+port){toast(t('fpChanged'),true);return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const r=await fetch('api/clusters',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,host,port,user,token_name:tname,token_value:tval,fingerprint:pendingFp.fp})});
    const d=await r.json();if(!r.ok)throw new Error(d.error||'HTTP '+r.status);
    pendingFp=null;toast(t('clusterAdded',name));closeModals();await fetchAll();selectCluster(d.cluster.id);
  }catch(e){toast(e.message,true);}
  finally{btn.disabled=false;btn.textContent=t('addCluster');}
}

// Para clusters antiguos sin certificado fijado: muestra la huella actual, pide confirmación y la guarda.
// EN: For old clusters without a pinned certificate: show the current fingerprint, ask for confirmation and save it.
async function pinCluster(){
  const c=clusters.find(x=>x.id===activeId);if(!c)return;
  try{
    const post=b=>fetch('api/clusters/'+c.id+'/pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json());
    const d=await post({});
    if(!d.ok){toast(d.error||'Error',true);return;}
    if(!confirm(t('pinPrompt',d.fingerprint)))return;
    const d2=await post({fingerprint:d.fingerprint});
    if(!d2.ok){toast(d2.error||'Error',true);return;}
    toast(t('pinned'));await fetchAll();
  }catch(e){toast(e.message,true);}
}

// Pide confirmación y borra un cluster (admin).
// EN: Ask for confirmation and delete a cluster (admin).
function confirmDelete(id,name){
  document.getElementById('del-msg').textContent=t('deleteClusterConfirm',name);
  document.getElementById('del-btn').onclick=async()=>{
    closeModals();
    try{await fetch('api/clusters/'+id,{method:'DELETE'});toast(name+' eliminado');await fetchAll();}
    catch(e){toast(e.message,true);}
  };
  document.getElementById('del-overlay').classList.add('show');
}

// ── Helpers ──────────────────────────────────────────────────────────────────
// Formateadores: bytes y tiempo encendido a texto legible.
// EN: Formatters: bytes and uptime to readable text.
// Para llevar una VM/CT al detalle de Net Monitor: se busca su equipo por IP y, si no, por MAC; sin ninguna de las dos se usa el nombre.
// Los datos se piden cada minuto y solo si el usuario tiene acceso a Net Monitor.
// EN: To take a VM/CT to the Net Monitor detail: its device is looked up by IP and then by MAC; with neither the name is used.
//     The data is requested once a minute and only if the user has access to Net Monitor.
let _gHost={}, _gTs=0;
async function loadGuestHosts(){
  if(Date.now()-_gTs<60000)return;
  _gTs=Date.now();
  try{
    const [g,n]=await Promise.all([fetch('api/guests'),fetch('/net/api/hosts')]);
    if(!g.ok)return;
    const guests=(await g.json()).guests||[];
    const hosts=n.ok?((await n.json()).hosts||[]):[];
    const ips=new Set(hosts.map(h=>h.ip)), byMac=new Map(hosts.filter(h=>h.mac).map(h=>[String(h.mac).toLowerCase(),h.ip]));
    const m={};
    guests.forEach(x=>{
      const ip=(x.ips||[]).find(i=>ips.has(i))||(x.macs||[]).map(a=>byMac.get(a)).find(Boolean);
      if(ip)m[x.vmid]=ip;
    });
    _gHost=m;
  }catch(e){}
}
function guestHost(v){return _gHost[v.vmid]||v.name||''}

function fmtBytes(b){b=Number(b);if(!b)return'0B';const u=['B','KB','MB','GB','TB'];let i=0;while(b>=1024&&i<u.length-1){b/=1024;i++;}return b.toFixed(i>0?1:0)+' '+u[i];}
function fmtUptime(s){s=Number(s);if(!s)return'—';const d=Math.floor(s/86400),h=Math.floor((s%86400)/3600),m=Math.floor((s%3600)/60);if(d>0)return d+'d '+h+'h';if(h>0)return h+'h '+m+'m';return m+'m';}
// Escapa HTML antes de insertar texto de usuarios, equipos o la red en la página: evita inyección de código (XSS).
// EN: Escape HTML before inserting text from users, devices or the network into the page: prevents code injection (XSS).
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
// Valor seguro dentro de un handler on*="…": literal JS entre comillas, escapado también para HTML.
// Lista de argumentos para data-on-*-args="…" (JSON escapado para HTML).
function jsargs(a){return esc(JSON.stringify(a));}
function updateClock(){const el=document.getElementById('clock');if(el)el.textContent=PCT.time(new Date(),true);}
function closeModals(){document.querySelectorAll('.overlay').forEach(o=>o.classList.remove('show'));}
let _tt;
// Aviso emergente breve (error si isErr).
// EN: Short pop-up notice (error if isErr).
function toast(msg,isErr=false){const el=document.getElementById('toast');el.textContent=msg;el.style.background=isErr?'var(--red)':'var(--text)';void el.offsetWidth;el.classList.add('show');clearTimeout(_tt);_tt=setTimeout(()=>el.classList.remove('show'),3400);}
function log(l,m){console.log(`[${l}] ${m}`);}

document.querySelectorAll('.overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)closeModals();}));
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModals();});

_i18nReady=true;
(async()=>{
  const ok=await tryAutoLogin();
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
if (window.cspRegister) cspRegister({ bkSetDays, closeModals, confirmDelete, doLogin, logout, moveNode, openAddCluster, pinCluster, toggleStopped, resetLayout, saveCluster, toggleBkIgnore, bkSelToggle, bkSelMode, bkBulk, toggleDiag, toggleDiagAll, setLang, setTheme, testCluster, toggleNav, togglePin, toggleSection, toggleNode, setNRange });
