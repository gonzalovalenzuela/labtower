// WAN Monitor — página del módulo (/wan/). Latencia, pérdida, cortes, IP pública y prueba de velocidad de la salida a internet.
// EN: WAN Monitor — module page (/wan/). Latency, loss, outages, public IP and speed test of the internet uplink.
const LANG={
  en:{
 "loginTitle": "Sign in",
 "loginSub": "Enter your credentials to continue.",
 "username": "Username",
 "password": "Password",
 "loginBtn": "Sign in",
 "rememberMe": "Remember me",
 "rem1d": "1 day",
 "rem1w": "1 week",
 "rem1m": "1 month",
 "remForever": "Forever",
 "navSection": "Navigation",
 "themeLight": "Light",
 "themeDark": "Dark",
 "permReadonly": "Read-only",
 "permExecute": "Execute",
 "permAdmin": "Administrator",
 "cancel": "Cancel",
 "test": "Test",
 "save": "Save",
 "delete": "Delete",
 "edit": "Edit",
 "saved": "Saved",
 "status": "Status",
 "filterAll": "All",
 "accumulating": "Collecting data…",
 "noDataChart": "No data for this range",
 "sessionExpired": "Session expired",
 "testFillAll": "Fill in the required fields.",
 "connecting": "Measuring…",
 "connectingMsg": "The first round takes a few seconds.",
 "statState": "Internet",
 "statRtt": "Latency",
 "statLoss": "Packet loss",
 "statDown": "Last download",
 "statIp": "Public IP",
 "stUp": "Online",
 "stDownNet": "No internet",
 "stDownLan": "No local network",
 "stDownWan": "No internet (WAN)",
 "scopeWan": "WAN (router)",
 "routerRow": "Router",
 "rtConnFor": "Router: WAN connected for",
 "rtCross": "Outages meanwhile",
 "rtCrossNone": "none",
 "rtCrossSome": "{0} here · {1} WAN",
 "rtWanUp": "WAN link up",
 "rtWanDown": "WAN link DOWN",
 "rtNoRead": "no reading",
 "setRouter": "Router check (tells a local outage from a line/provider outage)",
 "setRouterOn": "Ask the router for its WAN state",
 "setRouterType": "Router type",
 "rtHuawei": "Huawei (WiFi AX3, Mesh, HiLink)",
 "rtOpenwrt": "OpenWrt",
 "rtDdwrt": "DD-WRT",
 "rtTplink": "TP-Link (classic firmware)",
 "setRouterHost": "Router address (empty = default gateway)",
 "setRouterPort": "Port",
 "setRouterHttps": "Use HTTPS",
 "setRouterUser": "User",
 "setRouterPass": "Password",
 "setRouterPassKept": "stored (leave empty to keep it)",
 "setRouterIface": "WAN interface (OpenWrt)",
 "setRouterEvery": "Check every (s)",
 "setRouterHint": "Read only: LabTower only asks the router for the state of its internet link. Use an account that cannot change settings if the router allows it.",
 "setRouterTest": "Test router",
 "rtTesting": "Asking the router…",
 "rtTestOk": "Router answered: WAN {0}{1}",
 "rtTestUp": "up",
 "rtTestDown": "down",
 "rtTestFail": "Could not read the router: {0}",
 "stWait": "Measuring",
 "since": "since {0}",
 "gRtt": "Latency",
 "gJitter": "Jitter",
 "gLoss": "Loss",
 "gDns": "DNS lookup",
 "gGw": "Gateway",
 "gUp24": "Uptime 24 h",
 "gUp7": "Uptime 7 d",
 "gUp30": "Uptime 30 d",
 "targets": "Targets",
 "colTarget": "Target",
 "colKind": "Check",
 "colRtt": "Latency",
 "colLoss": "Loss",
 "colJitter": "Jitter",
 "colOk": "State",
 "kindPing": "Ping",
 "kindTcp": "TCP {0}",
 "gatewayRow": "Gateway",
 "ok": "OK",
 "fail": "Failed",
 "speed": "Speed test",
 "speedNow": "Measure now",
 "speedRunning": "Measuring… (≈{0} s)",
 "speedStarted": "Speed test started",
 "speedNext": "Next automatic test: {0}",
 "speedOff": "Automatic tests are off",
 "speedNone": "No speed test yet",
 "speedDown": "Download",
 "speedUp": "Upload",
 "speedPing": "Ping",
 "speedServer": "Server",
 "speedErr": "Test failed",
 "speedHint": "The test saturates the line for a few seconds; the checks pause meanwhile.",
 "tooSoon": "Wait a few seconds before measuring again",
 "outages": "Outages",
 "noOutages": "No outages recorded",
 "traceBtn": "Traceroute", "traceTo": "Traceroute to {0} when the outage started", "traceNone": "No traceroute for this outage", "ipHistory": "Public IP history", "ipSince": "Date this record started", "ipSinceSaved": "Date saved", "ipNow": "current", "noIpHistory": "No changes recorded yet",
 "stTitle": "Quality and availability",
 "stLatency": "Latency (percentiles)",
 "stP50": "Median",
 "stSamples": "Samples",
 "stAvail": "Availability",
 "stOutN": "Outages",
 "stOutMean": "Mean duration",
 "stOutLong": "Longest",
 "stMtbf": "Time between outages",
 "stByScope": "By cause",
 "stNone": "None",
 "stCollect": "Collecting data…",
 "stObserved": "observed",
 "colP95Day": "p95 24 h",
 "colFail24": "Failed 24 h",
 "spHours": "Speed by hour of the day",
 "spTrend": "Daily trend (30 days)",
 "spAvg30": "30-day average",
 "spLowWarn": "{0} speed tests in a row under 70 % of the contracted speed",
 "spHint": "Download, mean of the tests of each hour",
 "colStart": "Start",
 "colDur": "Duration",
 "colScope": "Where",
 "scopeInternet": "Internet",
 "scopeLan": "Local network",
 "ongoing": "ongoing",
 "info": "Connection",
 "pubIp": "Public IP",
 "gwIp": "Gateway",
 "lastCheck": "Last check",
 "ipChanged": "IP changed", "ipWas": "was", "pubIpSb": "Public IP",
 "noPing": "The ping command is not installed; only TCP checks will work.",
 "histRtt": "Latency",
 "histLoss": "Packet loss and jitter",
 "histSpeed": "Speed tests",
 "sRtt": "internet",
 "sGw": "gateway",
 "sDns": "DNS",
 "sLoss": "loss",
 "sJitter": "jitter",
 "sDown": "download",
 "sUp": "upload",
 "settings": "Settings",
 "setTitle": "WAN Monitor settings",
 "setTargets": "Targets (one per line)",
 "setTargetsHint": "host for ping, or tcp:host:port. Between 1 and 6.",
 "setGateway": "Gateway (auto, empty to turn off, or an IP)",
 "setDns": "Name to resolve (empty = off)",
 "setInterval": "Seconds between checks (10–300)",
 "setIpUrl": "Public IP service (https, empty = off)",
 "setSpeed": "Automatic speed test",
 "setPlanDown": "Contracted download (Mb/s, 0 = not set)",
 "setPlanUp": "Contracted upload (Mb/s, 0 = not set)",
 "planOf": "of contracted",
 "planAvg": "7-day average",
 "setEvery": "Every (hours, 0 = never)",
 "setSecs": "Seconds per direction",
 "setStreams": "Parallel streams",
 "setUpload": "Also measure upload",
 "setDownUrl": "Download address (https)",
 "setUpUrl": "Upload address (https)",
 "setEngine": "Test engine",
 "engBuiltin": "Built-in (Cloudflare)",
 "engOokla": "Ookla Speedtest CLI",
 "engLibre": "LibreSpeed CLI",
 "engMissing": "not installed",
 "engHint": "Ookla and LibreSpeed need their program installed on this server; use them to cross-check the built-in result. Ookla is for personal, non-commercial use.",
 "setSpeedHint": "Default: Cloudflare. Any server that answers /__down?bytes=N and /__up works.",
 "al": {
  "down_internet": "No internet access since {0}",
  "down_lan": "The local network is unreachable since {0}",
  "down_wan": "The router reports its internet (WAN) link is down since {0}",
  "speed_low": "Speed under 70 % of the plan in {0} tests in a row",
  "loss": "Packet loss {0}%",
  "latency": "High latency ({0} ms)",
  "dns_slow": "Slow DNS lookup ({0} ms)",
  "dns_fail": "The DNS lookup failed",
  "ip_changed": "The public IP changed to {0}",
  "ip_changed_from": "The public IP changed from {1} to {0}"
 }
},
  es:{
 "loginTitle": "Iniciar sesión",
 "loginSub": "Ingresa tus credenciales para continuar.",
 "username": "Usuario",
 "password": "Contraseña",
 "loginBtn": "Entrar",
 "rememberMe": "Recordarme",
 "rem1d": "1 día",
 "rem1w": "1 semana",
 "rem1m": "1 mes",
 "remForever": "Siempre",
 "navSection": "Navegación",
 "themeLight": "Claro",
 "themeDark": "Oscuro",
 "permReadonly": "Solo lectura",
 "permExecute": "Ejecutar",
 "permAdmin": "Administrador",
 "cancel": "Cancelar",
 "test": "Probar",
 "save": "Guardar",
 "delete": "Eliminar",
 "edit": "Editar",
 "saved": "Guardado",
 "status": "Estado",
 "filterAll": "Todo",
 "accumulating": "Reuniendo datos…",
 "noDataChart": "Sin datos en este rango",
 "sessionExpired": "Sesión vencida",
 "testFillAll": "Completa los campos obligatorios.",
 "connecting": "Midiendo…",
 "connectingMsg": "La primera ronda toma unos segundos.",
 "statState": "Internet",
 "statRtt": "Latencia",
 "statLoss": "Pérdida de paquetes",
 "statDown": "Última bajada",
 "statIp": "IP pública",
 "stUp": "En línea",
 "stDownNet": "Sin internet",
 "stDownLan": "Sin red local",
 "stDownWan": "Sin internet (WAN)",
 "scopeWan": "WAN (router)",
 "routerRow": "Router",
 "rtConnFor": "Router: WAN conectada hace",
 "rtCross": "Cortes en el período",
 "rtCrossNone": "ninguno",
 "rtCrossSome": "{0} aquí · {1} WAN",
 "rtWanUp": "Enlace WAN arriba",
 "rtWanDown": "Enlace WAN CAÍDO",
 "rtNoRead": "sin lectura",
 "setRouter": "Chequeo del router (distingue un corte local de uno de la línea o del proveedor)",
 "setRouterOn": "Preguntar al router por su estado WAN",
 "setRouterType": "Tipo de router",
 "rtHuawei": "Huawei (WiFi AX3, Mesh, HiLink)",
 "rtOpenwrt": "OpenWrt",
 "rtDdwrt": "DD-WRT",
 "rtTplink": "TP-Link (firmware clásico)",
 "setRouterHost": "Dirección del router (vacío = puerta de enlace)",
 "setRouterPort": "Puerto",
 "setRouterHttps": "Usar HTTPS",
 "setRouterUser": "Usuario",
 "setRouterPass": "Contraseña",
 "setRouterPassKept": "guardada (déjala vacía para conservarla)",
 "setRouterIface": "Interfaz WAN (OpenWrt)",
 "setRouterEvery": "Revisar cada (s)",
 "setRouterHint": "Solo lectura: LabTower solo le pregunta al router por el estado de su enlace a internet. Si el router lo permite, usa una cuenta que no pueda cambiar ajustes.",
 "setRouterTest": "Probar router",
 "rtTesting": "Preguntando al router…",
 "rtTestOk": "El router respondió: WAN {0}{1}",
 "rtTestUp": "arriba",
 "rtTestDown": "caída",
 "rtTestFail": "No se pudo leer el router: {0}",
 "stWait": "Midiendo",
 "since": "desde {0}",
 "gRtt": "Latencia",
 "gJitter": "Jitter",
 "gLoss": "Pérdida",
 "gDns": "Resolución DNS",
 "gGw": "Puerta de enlace",
 "gUp24": "Disponibilidad 24 h",
 "gUp7": "Disponibilidad 7 d",
 "gUp30": "Disponibilidad 30 d",
 "targets": "Destinos",
 "colTarget": "Destino",
 "colKind": "Prueba",
 "colRtt": "Latencia",
 "colLoss": "Pérdida",
 "colJitter": "Jitter",
 "colOk": "Estado",
 "kindPing": "Ping",
 "kindTcp": "TCP {0}",
 "gatewayRow": "Puerta de enlace",
 "ok": "OK",
 "fail": "Falla",
 "speed": "Prueba de velocidad",
 "speedNow": "Medir ahora",
 "speedRunning": "Midiendo… (≈{0} s)",
 "speedStarted": "Prueba de velocidad iniciada",
 "speedNext": "Próxima prueba automática: {0}",
 "speedOff": "Las pruebas automáticas están desactivadas",
 "speedNone": "Aún sin pruebas de velocidad",
 "speedDown": "Bajada",
 "speedUp": "Subida",
 "speedPing": "Ping",
 "speedServer": "Servidor",
 "speedErr": "La prueba falló",
 "speedHint": "La prueba satura la línea unos segundos; las mediciones se pausan mientras tanto.",
 "tooSoon": "Espera unos segundos antes de volver a medir",
 "outages": "Cortes",
 "noOutages": "Sin cortes registrados",
 "traceBtn": "Traceroute", "traceTo": "Traceroute a {0} al empezar el corte", "traceNone": "Este corte no tiene traceroute", "ipHistory": "Historial de IP pública", "ipSince": "Fecha en que empezó este registro", "ipSinceSaved": "Fecha guardada", "ipNow": "actual", "noIpHistory": "Aún no hay cambios registrados",
 "stTitle": "Calidad y disponibilidad",
 "stLatency": "Latencia (percentiles)",
 "stP50": "Mediana",
 "stSamples": "Muestras",
 "stAvail": "Disponibilidad",
 "stOutN": "Cortes",
 "stOutMean": "Duración media",
 "stOutLong": "El más largo",
 "stMtbf": "Tiempo entre cortes",
 "stByScope": "Por causa",
 "stNone": "Ninguno",
 "stCollect": "Recopilando datos…",
 "stObserved": "observado",
 "colP95Day": "p95 24 h",
 "colFail24": "Fallos 24 h",
 "spHours": "Velocidad por hora del día",
 "spTrend": "Tendencia diaria (30 días)",
 "spAvg30": "Promedio de 30 días",
 "spLowWarn": "{0} pruebas de velocidad seguidas bajo el 70 % de lo contratado",
 "spHint": "Bajada, promedio de las pruebas de cada hora",
 "colStart": "Inicio",
 "colDur": "Duración",
 "colScope": "Dónde",
 "scopeInternet": "Internet",
 "scopeLan": "Red local",
 "ongoing": "en curso",
 "info": "Conexión",
 "pubIp": "IP pública",
 "gwIp": "Puerta de enlace",
 "lastCheck": "Última medición",
 "ipChanged": "IP cambió", "ipWas": "antes", "pubIpSb": "IP pública",
 "noPing": "El comando ping no está instalado; solo funcionarán las pruebas TCP.",
 "histRtt": "Latencia",
 "histLoss": "Pérdida de paquetes y jitter",
 "histSpeed": "Pruebas de velocidad",
 "sRtt": "internet",
 "sGw": "puerta de enlace",
 "sDns": "DNS",
 "sLoss": "pérdida",
 "sJitter": "jitter",
 "sDown": "bajada",
 "sUp": "subida",
 "settings": "Ajustes",
 "setTitle": "Ajustes de WAN Monitor",
 "setTargets": "Destinos (uno por línea)",
 "setTargetsHint": "host para ping, o tcp:host:puerto. Entre 1 y 6.",
 "setGateway": "Puerta de enlace (auto, vacío para apagar, o una IP)",
 "setDns": "Nombre a resolver (vacío = apagado)",
 "setInterval": "Segundos entre mediciones (10–300)",
 "setIpUrl": "Servicio de IP pública (https, vacío = apagado)",
 "setSpeed": "Prueba de velocidad automática",
 "setPlanDown": "Bajada contratada (Mb/s, 0 = sin definir)",
 "setPlanUp": "Subida contratada (Mb/s, 0 = sin definir)",
 "planOf": "de lo contratado",
 "planAvg": "Promedio 7 días",
 "setEvery": "Cada (horas, 0 = nunca)",
 "setSecs": "Segundos por sentido",
 "setStreams": "Flujos paralelos",
 "setUpload": "Medir también la subida",
 "setDownUrl": "Dirección de bajada (https)",
 "setUpUrl": "Dirección de subida (https)",
 "setEngine": "Motor de la prueba",
 "engBuiltin": "Integrado (Cloudflare)",
 "engOokla": "Ookla Speedtest CLI",
 "engLibre": "LibreSpeed CLI",
 "engMissing": "no instalado",
 "engHint": "Ookla y LibreSpeed requieren su programa instalado en este servidor; sirven para contrastar el resultado integrado. Ookla es solo para uso personal no comercial.",
 "setSpeedHint": "Por defecto: Cloudflare. Sirve cualquier servidor que responda /__down?bytes=N y /__up.",
 "al": {
  "down_internet": "Sin acceso a internet desde {0}",
  "down_lan": "La red local no responde desde {0}",
  "down_wan": "El router informa que su enlace a internet (WAN) está caído desde {0}",
  "speed_low": "Velocidad bajo el 70 % del plan en {0} pruebas seguidas",
  "loss": "Pérdida de paquetes {0}%",
  "latency": "Latencia alta ({0} ms)",
  "dns_slow": "Resolución DNS lenta ({0} ms)",
  "dns_fail": "Falló la resolución DNS",
  "ip_changed": "La IP pública cambió a {0}",
  "ip_changed_from": "La IP pública cambió de {1} a {0}"
 }
}
};

let _lang=localStorage.getItem('pi-lang')||'en';
var _i18nReady=false;
// Traducción: busca la clave en el idioma activo; los textos admiten {0}, {1}… para incluir valores.
// EN: Translation: looks the key up in the active language; texts accept {0}, {1}… to include values.
function t(k,...a){const v=(LANG[_lang]||LANG.en)[k]??(LANG.en)[k]??k;return typeof v==='string'&&a.length?v.replace(/\{(\d+)\}/g,(m,i)=>a[i]??''):v;}
function setLang(l){
  _lang=l;localStorage.setItem('pi-lang',l);document.documentElement.lang=l;
  document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=t(el.getAttribute('data-i18n')));
  ['en','es'].forEach(x=>document.getElementById('lang-'+x)?.classList.toggle('active',x===l));
  if(_i18nReady&&typeof renderAll==='function')renderAll();
  try{renderNav();}catch(e){}
}
(()=>setLang(_lang))();

let ME=null;
const $=id=>document.getElementById(id);

// ── Tema ─────────────────────────────────────────────────────────────────────
function setTheme(t){localStorage.setItem('pi-theme',t);applyTheme(t);['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));}
function applyTheme(t){const p=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;document.documentElement.setAttribute('data-theme',p==='dark'?'dark':'light');}
(()=>{const t=localStorage.getItem('pi-theme')||'dark';applyTheme(t);window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if((localStorage.getItem('pi-theme')||'dark')==='system')applyTheme('system');});setTimeout(()=>document.getElementById('theme-'+t)?.classList.add('active'),0);})();

function canAdmin(){return ME&&ME.permissions?.wan==='admin';}
function canExec(){return ME&&['execute','admin'].includes(ME.permissions?.wan);}
const _NAV_SELF='wan';
// Navegación compartida (nav.js): mismo orden y grupos en todos los módulos. / EN: shared navigation (nav.js): same order and groups in every module.
function renderNav(){if(window.labNav)labNav.render({self:_NAV_SELF,lang:_lang,me:ME});}

// ── Inicio de sesión (la cookie la fija el servidor, HttpOnly: el JavaScript nunca guarda el token) ──
// EN: Login (the cookie is set by the server, HttpOnly: the JavaScript never stores the token)
document.getElementById('l-pass').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
async function doLogin(){
  const btn=document.getElementById('btn-l'),err=document.getElementById('login-err');
  const u=document.getElementById('l-user').value.trim(),p=document.getElementById('l-pass').value;
  err.className='login-err';
  if(!u||!p){err.textContent=t('testFillAll');err.className='login-err show';return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const r=await fetch('api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p,remember:remValue()})});
    const d=await r.json();
    if(!r.ok||!d.ok){err.textContent=d.error||'Error';err.className='login-err show';return;}
    if(d.must_change_password){location.href='/admin/change-password?next='+encodeURIComponent(location.pathname);return;}
    ME=d;applyPermissions();await initApp();
    const ls=document.getElementById('login-screen');ls.style.opacity='0';setTimeout(()=>ls.style.display='none',150);
  }catch(e){err.textContent='Error: '+e.message;err.className='login-err show';}
  finally{btn.disabled=false;btn.textContent=t('loginBtn');}
}
async function checkSession(){
  try{const r=await fetch('api/me');if(!r.ok)return false;const d=await r.json();if(!d.username)return false;ME=d;return true;}catch{return false;}
}
function applyPermissions(){
  const _un=String(ME.username||'?');
  document.getElementById('me-name').textContent=_un;
  document.getElementById('avatar').textContent=_un[0].toUpperCase();
  const k={readonly:'permReadonly',execute:'permExecute',admin:'permAdmin'}[ME.permissions?.wan];
  document.getElementById('me-role').textContent=k?t(k):'—';
  renderNav();
  if(typeof afterPermissions==='function')afterPermissions();
}
async function logout(){await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.reload();}

// ── Datos ────────────────────────────────────────────────────────────────────
let W=null, pollTimer=null, _histTs=0, _histCache=[];
function afterPermissions(){renderAll();}
async function initApp(){
  updateClock();setInterval(updateClock,1000);
  await fetchAll();
  schedulePoll();
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)fetchAll();});
}
// Pide cada 5 s (cada 2 s mientras corre una prueba de velocidad). El historial pesado se pide solo cada 30 s.
// EN: Poll every 5 s (every 2 s while a speed test runs). The heavy history is requested only every 30 s.
function schedulePoll(){clearTimeout(pollTimer);pollTimer=setTimeout(async()=>{if(!document.hidden)await fetchAll();schedulePoll();},W&&W.speed_running?2000:5000);}
async function fetchAll(){
  try{
    const wantHist=Date.now()-_histTs>=30000;
    const r=await fetch('api/wan'+(wantHist?'':'?hist=0'));
    if(r.status===401){location.reload();return;}
    const d=await r.json();
    if(wantHist){_histCache=d.history||[];_histTs=Date.now();}else d.history=_histCache;
    W=d;renderAll();ensureRanges();
  }catch(e){console.error(e);}
}
const chartOwner=()=>'wan';
const historyUrl=(id,range)=>'api/wan/history?range='+range;
function localPts(kind){return kind==='speed'?((W&&W.speed)||[]).filter(s=>s.down!=null||s.up!=null):[];}
function renderAll(){if(!W)return;renderMain();updateGlobalStats();}
function stateInfo(s){
  if(!s)return {lv:'off',txt:t('stWait')};
  if(!s.up)return {lv:'crit',txt:t(s.scope==='lan'?'stDownLan':s.scope==='wan'?'stDownWan':'stDownNet')};
  return {lv:(s.alerts||[]).some(a=>a.lv==='warn')?'warn':'ok',txt:t('stUp')};
}
function updateGlobalStats(){
  const s=W.snap,si=stateInfo(s);
  $('st-state').innerHTML=`<span class="${si.lv==='ok'?'':'wan-st-'+si.lv}">${esc(si.txt)}</span>`;
  $('st-rtt').innerHTML=s&&s.rtt!=null?Math.round(s.rtt*10)/10+'<span style="font-size:13px;color:var(--text-dim)"> ms</span>':'—';
  $('st-loss').innerHTML=s&&s.loss!=null?Math.round(s.loss*10)/10+'<span style="font-size:13px;color:var(--text-dim)">%</span>':'—';
  const last=lastSpeed();
  $('st-down').innerHTML=last&&last.down!=null?fmtMbps(last.down):'—';
  $('st-ip').textContent=s&&s.public_ip?s.public_ip:'—';
  const sb=$('sb-ip');
  if(sb){
    sb.style.display=s&&s.public_ip?'':'none';
    if(s&&s.public_ip){
      const ch=s.ip_changed?`<div class="sb-ip-sub">${esc(t('ipChanged'))} ${esc(fmtDate(s.ip_changed))}${s.ip_prev?' · '+esc(t('ipWas'))+' '+esc(s.ip_prev):''}</div>`:'';
      $('sb-ip-body').innerHTML=`<div class="sb-ip" title="${esc(s.public_ip)}"><span class="sb-ip-dot${s.ip_changed&&Date.now()/1000-s.ip_changed<86400?' chg':''}"></span><span class="sb-ip-val">${esc(s.public_ip)}</span></div>${ch}`;
    }
  }
}
function fmtMbps(v){return v==null?'—':(v>=100?Math.round(v):Math.round(v*10)/10)+'<span style="font-size:13px;color:var(--text-dim)"> Mb/s</span>';}
function lastSpeed(){const l=(W.speed||[]).filter(s=>!s.error&&s.down!=null);return l.length?l[l.length-1]:null;}
function ms(v){return v==null?'—':(Math.round(v*10)/10)+' ms';}
function tkeyOf(x){return x.kind==='tcp'?'tcp:'+x.host+':'+x.port:x.host;}
function targetRows(s){
  const list=[...(s.targets||[])];if(s.gateway)list.push(s.gateway);
  const ts={};((W.stats&&W.stats.targets&&W.stats.targets['24h'])||[]).forEach(x=>{ts[x.host]=x;});
  return list.map(x=>{
    const st=x.gateway?null:ts[tkeyOf(x)];
    const kind=x.kind==='tcp'?t('kindTcp',x.port||''):t('kindPing');
    return `<tr><td>${x.gateway?`<span class="sum-name">${esc(t('gatewayRow'))}</span><div class="sum-sub">${esc(x.host)}</div>`:`<span class="sum-name">${esc(x.host)}</span>`}</td>
      <td>${esc(kind)}</td><td>${ms(x.rtt)}</td><td>${x.loss==null?'—':esc(Math.round(x.loss))+'%'}</td><td class="c-temp">${ms(x.jitter)}</td><td>${st?ms(st.p95):'—'}</td><td>${st?(st.fail_pct>0?`<span style="color:${st.fail_pct>=1?'var(--orange)':'inherit'}">${esc(st.fail_pct)}%</span>`:'0%'):'—'}</td><td>${pill(x.ok?'ok':'crit',t(x.ok?'ok':'fail'))}</td></tr>`;
  }).join('');
}
// % de lo entregado respecto a la velocidad contratada (última prueba y promedio de 7 días). / Delivered vs contracted speed in % (last test and 7-day average).
function pctCol(p){return p>=90?'var(--green)':p>=70?'var(--orange)':'var(--red)';}
function planRows(cfg,sp,last){
  const wk=Date.now()/1000-7*86400,ok=sp.filter(x=>!x.error&&x.ts>=wk);
  const one=(lbl,plan,key)=>{
    if(!plan)return '';
    const v=last[key];if(v==null)return '';
    const p=Math.round(v/plan*100),vs=ok.map(x=>x[key]).filter(x=>x!=null),avg=vs.length?Math.round(vs.reduce((a,b)=>a+b,0)/vs.length/plan*100):null;
    return kv(lbl,`<b style="color:${pctCol(p)}">${p}%</b> <span class="sum-sub">${esc(t('planOf'))} (${fmtNum(plan)} Mb/s)</span>`+(avg!=null?` · <span class="sum-sub">${esc(t('planAvg'))}: <b style="color:${pctCol(avg)}">${avg}%</b></span>`:''));
  };
  return one(t('speedDown'),cfg.plan_down,'down')+one(t('speedUp'),cfg.plan_up,'up');
}
// Mini gráfico de barras (CSS) con una etiqueta al pasar el mouse. / Small bar chart (CSS) with a tooltip.
function miniBars(items,color){
  const mx=Math.max(1,...items.map(i=>i.v||0));
  return '<div style="display:flex;align-items:flex-end;gap:2px;height:46px;margin:6px 14px 2px">'+items.map(i=>`<div title="${esc(i.tip)}" style="flex:1;min-width:3px;height:${i.v==null?2:Math.max(3,Math.round(i.v/mx*100))}%;background:${i.v==null?'var(--border)':color};border-radius:2px 2px 0 0;opacity:${i.v==null?1:.85}"></div>`).join('')+'</div>';
}
function statsCard(){
  const st=W.stats;if(!st)return '';
  const L=st.latency||{},A=st.avail||{};
  const row=(lab,k)=>{const l=L[k]||{},a=A[k]||{};
    return `<tr><td>${esc(lab)}</td><td>${l.n?ms(l.p50):'—'}</td><td>${l.n?ms(l.p95):'—'}</td><td>${l.n?ms(l.p99):'—'}</td><td>${a.pct==null?'—':esc(a.pct)+'%'}</td><td>${a.count==null?'—':(a.count?esc(a.count):esc(t('stNone')))}</td><td>${a.mean==null?'—':esc(fmtDur(a.mean))}</td><td>${a.longest?esc(fmtDur(a.longest)):'—'}</td><td>${a.mtbf==null?'—':esc(fmtDur(a.mtbf))}</td></tr>`;};
  const sc=A['30d']&&A['30d'].count?A['30d'].scopes:null;
  const scTxt=sc?['lan','wan','internet'].filter(k=>sc[k]).map(k=>t(k==='lan'?'scopeLan':k==='wan'?'scopeWan':'scopeInternet')+': '+sc[k]).join(' · '):'';
  return `<div class="node-card wide"><div class="node-hd"><div class="node-name">${esc(t('stTitle'))}</div></div><div class="tbl-wrap"><table class="wan-table"><thead><tr><th></th><th>${esc(t('stP50'))}</th><th>p95</th><th>p99</th><th>${esc(t('stAvail'))}</th><th>${esc(t('stOutN'))}</th><th>${esc(t('stOutMean'))}</th><th>${esc(t('stOutLong'))}</th><th>${esc(t('stMtbf'))}</th></tr></thead><tbody>${row('24 h','24h')}${row('7 d','7d')}${row('30 d','30d')}</tbody></table></div>${scTxt?`<div class="wan-note">${esc(t('stByScope'))} (30 d): ${esc(scTxt)}</div>`:''}</div>`;
}
function speedExtra(){
  const sp=W.stats&&W.stats.speed;if(!sp||!sp.n)return '';
  let h='';
  if(sp.plan_down&&sp.avg30&&sp.avg30.down!=null)h+=kv(t('spAvg30'),`<b style="color:${pctCol(sp.avg30.down)}">${sp.avg30.down}%</b> <span class="sum-sub">↓</span>`+(sp.plan_up&&sp.avg30.up!=null?` · <b style="color:${pctCol(sp.avg30.up)}">${sp.avg30.up}%</b> <span class="sum-sub">↑</span>`:''));
  if(sp.hours&&sp.hours.length>=3){
    const byH={};sp.hours.forEach(x=>{byH[x.h]=x;});
    h+=`<div class="wan-note" style="padding-bottom:0">${esc(t('spHours'))}</div>`+miniBars(Array.from({length:24},(_,i)=>({v:byH[i]?byH[i].down:null,tip:String(i).padStart(2,'0')+':00 — '+(byH[i]?fmtNum(byH[i].down)+' Mb/s ('+byH[i].n+')':'—')})),'var(--green)');
  }
  if(sp.trend&&sp.trend.length>=3)h+=`<div class="wan-note" style="padding-bottom:0">${esc(t('spTrend'))}</div>`+miniBars(sp.trend.map(x=>({v:x.down,tip:fmtDate(x.ts).split(' ')[0]+' — '+(x.down==null?'—':fmtNum(x.down)+' Mb/s')})),'var(--blue)');
  return h;
}
function speedCard(){
  const sp=W.speed||[],cfg=W.config.speed,last=sp.length?sp[sp.length-1]:null;
  let btn='';
  if(canExec())btn=W.speed_running?`<button class="btn-secondary" disabled><span class="spin">⟳</span> ${esc(t('speedRunning',cfg.seconds*(cfg.upload?2:1)+4))}</button>`
    :`<button class="btn-secondary" data-on-click="runSpeed">${esc(t('speedNow'))}</button>`;
  let body;
  if(!last)body=`<div class="wan-empty">${esc(t('speedNone'))}</div>`;
  else if(last.error)body=`<div class="wan-empty" style="color:var(--red)">${esc(t('speedErr'))}: ${esc(last.error)}</div>`;
  else body=`<div class="wan-gauges" style="grid-template-columns:repeat(3,1fr);padding:12px 14px">${bigNum(t('speedDown'),last.down==null?'—':fmtNum(Math.round(last.down*10)/10),'Mb/s','var(--green)')}${bigNum(t('speedUp'),last.up==null?'—':fmtNum(Math.round(last.up*10)/10),last.up==null?'':'Mb/s','var(--blue)')}${bigNum(t('speedPing'),last.ping==null?'—':last.ping,last.ping==null?'':'ms')}</div>
    ${planRows(cfg,sp,last)}${speedExtra()}${kv(t('speedServer'),esc(last.server||'—')+(cfg.engine&&cfg.engine!=='builtin'?' <span class="sum-sub">'+esc(cfg.engine==='ookla'?'Ookla':'LibreSpeed')+'</span>':''))}${kv(t('lastCheck'),esc(fmtDate(last.ts)))}`;
  const next=!cfg.enabled||!cfg.every_hours?t('speedOff'):(W.next_speed?t('speedNext',fmtDate(W.next_speed)):'');
  return `<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('speed'))}</div>${btn}</div>${body}<div class="wan-note">${esc(next)}<br>${esc(t('speedHint'))}</div></div>`;
}
// Traceroute guardado al abrirse cada corte: se carga al pedirlo y queda en memoria mientras la página esté abierta.
// EN: Traceroute stored when each outage opened: loaded on request and kept in memory while the page stays open.
const TRACES={},OPEN_TRACE=new Set();
async function toggleTrace(start){
  if(OPEN_TRACE.has(start)){OPEN_TRACE.delete(start);renderMain();return;}
  if(!(start in TRACES)){
    try{const r=await fetch('api/wan/trace?start='+encodeURIComponent(start));TRACES[start]=r.ok?(await r.json()).trace:null;}
    catch{TRACES[start]=null;}
  }
  OPEN_TRACE.add(start);renderMain();
}
function outagesCard(){
  const o=W.outages||[];
  const rows=o.length?o.map(x=>{
    const tr=x.trace?`<br><button class="wan-link" data-on-click="toggleTrace" data-on-click-args="${jsargs([x.start])}">${esc(t('traceBtn'))}</button>`:'';
    let r=`<tr><td>${esc(fmtDate(x.start))}</td><td>${x.end?esc(fmtDur(x.end-x.start)):pill('crit',t('ongoing'))}</td><td>${esc(t(x.scope==='lan'?'scopeLan':x.scope==='wan'?'scopeWan':'scopeInternet'))}${tr}</td></tr>`;
    if(x.trace&&OPEN_TRACE.has(x.start)){
      const d=TRACES[x.start];
      r+=`<tr class="trace-row"><td colspan="3">${d?`<div class="wan-note">${esc(t('traceTo',d.dest))}</div><pre class="wan-trace">${esc(d.text)}</pre>`:`<div class="wan-note">${esc(t('traceNone'))}</div>`}</td></tr>`;
    }
    return r;}).join('')
    :`<tr><td colspan="3" class="wan-empty">${esc(t('noOutages'))}</td></tr>`;
  return `<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('outages'))}</div></div><div class="tbl-wrap"><table class="wan-table"><thead><tr><th>${esc(t('colStart'))}</th><th>${esc(t('colDur'))}</th><th>${esc(t('colScope'))}</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
}
// Historial de cambios de IP pública (el más reciente primero).
// EN: Public IP change history (newest first).
function isoDay(ts){const d=new Date(ts*1000),p=n=>String(n).padStart(2,'0');return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());}
function fmtFull(ts){const d=new Date(ts*1000);return d.toLocaleDateString(_lang==='es'?'es-CL':'en-GB',{day:'2-digit',month:'2-digit',year:'numeric'})+' '+PCT.time(d);}
// Cambia la fecha de inicio del registro más antiguo (administradores). / EN: Change the start date of the oldest record (administrators).
async function setIpSince(v){
  const m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(v||'');if(!m)return;
  const old=(W.ips||[]).slice(-1)[0],d=old?new Date(old.ts*1000):new Date();
  const ts=Math.floor(new Date(+m[1],+m[2]-1,+m[3],d.getHours(),d.getMinutes(),0).getTime()/1000);
  try{const r=await post('api/wan/ip/since',{ts});if(r.ok){W.ips=r.d.ips;toast(t('ipSinceSaved'));renderMain();}else toast(r.d.error||'Error',true);}
  catch(e){toast(e.message,true);}
}
function ipHistoryCard(){
  const l=W.ips||[];
  const rows=l.length?l.map((x,i)=>`<tr><td>${esc(fmtFull(x.ts))}${canAdmin()&&i===l.length-1?`<br><input type="date" class="ip-since" max="${esc(isoDay(Date.now()/1000))}" value="${esc(isoDay(x.ts))}" aria-label="${esc(t('ipSince'))}" title="${esc(t('ipSince'))}" data-on-change="setIpSince" data-on-change-args='[{"@":"value"}]'>`:''}</td><td>${esc(x.ip)}${i===0?' <span class="sum-sub">'+esc(t('ipNow'))+'</span>':''}${x.prev?'<br><span class="sum-sub">'+esc(t('ipWas'))+' '+esc(x.prev)+'</span>':''}</td></tr>`).join('')
    :`<tr><td colspan="2" class="wan-empty">${esc(t('noIpHistory'))}</td></tr>`;
  return `<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('ipHistory'))}</div></div><div class="tbl-wrap"><table class="wan-table"><thead><tr><th>${esc(t('colStart'))}</th><th>IP</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
}
function renderMain(){
  const s=W.snap,box=$('main-content');
  $('tb-title').textContent='WAN Monitor';
  $('tb-sub').textContent='';
  // Los botones van en #tb-actions: la barra con menú superior oculta #tb-sub (solo texto informativo) y los botones se perdían.
  // EN: Buttons go in #tb-actions: the top-bar menu mode hides #tb-sub (informative text only) and the buttons were lost.
  const act=$('tb-actions');act.textContent='';
  if(canAdmin()){const b=document.createElement('button');b.className='lt-btn';b.textContent=t('settings');b.onclick=openSettings;act.appendChild(b);}
  if(!s){box.innerHTML='<div class="state-msg"><strong>'+esc(t('connecting'))+'</strong>'+esc(t('connectingMsg'))+'</div>';return;}
  const si=stateInfo(s),up=W.uptime||{};
  const pc=v=>v==null?null:v,upTxt=v=>v==null?'—':v+'%';
  let h='';
  if(W.ping_available===false)h+=`<div class="alerts"><div class="alert warn">⚠ ${esc(t('noPing'))}</div></div>`;
  h+=alertsHtml(s.alerts);
  h+='<div class="wan-gauges">'+bigNum(t('gRtt'),s.rtt==null?'—':Math.round(s.rtt*10)/10,s.rtt==null?'':'ms',s.rtt>=150?'var(--orange)':'var(--text)')
    +bigNum(t('gJitter'),s.jitter==null?'—':Math.round(s.jitter*10)/10,s.jitter==null?'':'ms')
    +bigNum(t('gLoss'),s.loss==null?'—':Math.round(s.loss*10)/10,s.loss==null?'':'%',s.loss>=5?'var(--red)':'var(--text)')
    +bigNum(t('gDns'),s.dns==null?'—':Math.round(s.dns),s.dns==null?'':'ms',s.dns>=500||s.dns_fail?'var(--orange)':'var(--text)')
    +bigNum(t('gGw'),s.gw==null?'—':Math.round(s.gw*10)/10,s.gw==null?'':'ms')
    +ring(t('gUp24'),pc(up['24h']),'var(--wan)',upTxt(up['24h']))+'</div>';
  h+='<div class="wan-grid">';
  h+=`<div class="node-card wide"><div class="node-hd"><div class="node-name">${esc(t('targets'))}</div><span>${pill(si.lv,si.txt)}</span></div><div class="tbl-wrap"><table class="wan-table"><thead><tr><th>${esc(t('colTarget'))}</th><th>${esc(t('colKind'))}</th><th>${esc(t('colRtt'))}</th><th>${esc(t('colLoss'))}</th><th class="c-temp">${esc(t('colJitter'))}</th><th>${esc(t('colP95Day'))}</th><th>${esc(t('colFail24'))}</th><th>${esc(t('colOk'))}</th></tr></thead><tbody>${targetRows(s)}</tbody></table></div></div>`;
  h+=statsCard()+speedCard()+outagesCard()+ipHistoryCard();
  h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('info'))}</div></div>
    ${kv(t('pubIp'),esc(s.public_ip||'—')+(s.ip_changed?` <span class="sum-sub">${esc(t('ipChanged'))} ${esc(fmtDate(s.ip_changed))}</span>`:''))}
    ${kv(t('gwIp'),esc(s.gateway_ip||'—'))}${routerRow(s)}${kv(t('gUp7'),esc(upTxt(up['7d'])))}${kv(t('gUp30'),esc(upTxt(up['30d'])))}${kv(t('lastCheck'),esc(fmtDate(s.ts)))}</div>`;
  h+='</div>'+chartSections('wan');
  box.innerHTML=h;
  drawCharts('wan');
}
// Fila «Router» de la tarjeta de información: estado WAN que informa el router (solo si el chequeo está activo).
// EN: "Router" row of the info card: the WAN state the router reports (only when the check is on).
function routerRow(s){
  const c=W.config&&W.config.router;if(!c||!c.enabled)return '';
  const r=s.router;
  if(!r)return kv(t('routerRow'),esc(t('rtNoRead')));
  if(!r.ok)return kv(t('routerRow'),`<span style="color:var(--orange)">${esc(t('rtNoRead'))}: ${esc(r.error||'')}</span>`);
  return kv(t('routerRow'),r.wan_up?`<span style="color:var(--green)">${esc(t('rtWanUp'))}</span>`:`<span style="color:var(--red)">${esc(t('rtWanDown'))}</span>`)+(r.ip?kv('IP WAN',esc(r.ip)):'')+(r.uptime?kv(t('rtConnFor'),esc(fmtDur(r.uptime))):'')+crossRow(s.router_check);
}
function crossRow(x){
  if(!x)return '';
  const same=x.outages===0;
  return kv(t('rtCross'),`<span style="color:var(--${same?'green':'orange'})">${esc(same?t('rtCrossNone'):t('rtCrossSome',x.outages,x.wan_outages))}</span>`);
}
// Gráficos: latencia (con los cortes sombreados), pérdida y jitter, y las pruebas de velocidad (puntos).
// EN: Charts: latency (outages shaded), loss and jitter, and the speed tests (points).
const CHARTS={
  rtt:{title:'histRtt',down:true,series:[{k:'rtt',c:'#0ea5e9',l:'sRtt',f:v=>v.toFixed(1)+' ms'},{k:'gw',c:'#22c55e',l:'sGw',f:v=>v.toFixed(1)+' ms'},{k:'dns',c:'#f97316',l:'sDns',f:v=>Math.round(v)+' ms'}],axis:v=>Math.round(v)+' ms',h:140,pl:52},
  loss:{title:'histLoss',series:[{k:'loss',c:'#ef4444',l:'sLoss',f:v=>v.toFixed(1)+'%'},{k:'jitter',c:'#a855f7',l:'sJitter',f:v=>v.toFixed(1)+' ms'}],axis:v=>(Math.round(v*10)/10)+'',h:110,pl:40},
  speed:{title:'histSpeed',local:true,points:true,series:[{k:'down',c:'#22c55e',l:'sDown',f:v=>v.toFixed(1)+' Mb/s'},{k:'up',c:'#3b82f6',l:'sUp',f:v=>v.toFixed(1)+' Mb/s'}],axis:v=>Math.round(v)+'',h:120,pl:46},
};
const chartRange={rtt:'1d',loss:'1d',speed:'1d'};

async function runSpeed(){
  try{const r=await post('api/wan/speedtest',{});if(r.ok){toast(t('speedStarted'));W.speed_running=true;renderMain();schedulePoll();}else toast(r.d.error||(r.status===429?t('tooSoon'):'Error'),true);}
  catch(e){toast(e.message,true);}
}

// ── Ajustes (solo administradores) ────────────────────────────────────────────
function targetsToText(l){return (l||[]).map(x=>x.kind==='tcp'?'tcp:'+x.host+':'+x.port:x.host).join('\n');}
function textToTargets(s){
  return s.split('\n').map(x=>x.trim()).filter(Boolean).map(x=>{
    const m=/^tcp:(.+):(\d{1,5})$/i.exec(x);
    return m?{host:m[1],kind:'tcp',port:parseInt(m[2])}:{host:x,kind:'ping'};
  });
}
function openSettings(){
  const c=W.config,sp=c.speed;
  $('s-targets').value=targetsToText(c.targets);$('s-gw').value=c.gateway;$('s-dns').value=c.dns_name;$('s-interval').value=c.interval;$('s-ipurl').value=c.ip_url;
  $('s-sp-on').checked=!!sp.enabled;$('s-sp-every').value=sp.every_hours;$('s-sp-secs').value=sp.seconds;$('s-sp-streams').value=sp.streams;$('s-sp-pdown').value=sp.plan_down||0;$('s-sp-pup').value=sp.plan_up||0;$('s-sp-up').checked=!!sp.upload;
  const av=W.engines||{builtin:true},nm={builtin:t('engBuiltin'),ookla:t('engOokla'),librespeed:t('engLibre')};
  ['builtin','ookla','librespeed'].forEach(k=>{const o=$('o-eng-'+k);o.textContent=nm[k]+(av[k]?'':' ('+t('engMissing')+')');o.disabled=!av[k]&&sp.engine!==k;});
  $('s-sp-engine').value=sp.engine||'builtin';
  $('s-sp-down').value=sp.down_url;$('s-sp-upurl').value=sp.up_url;
  const rc=c.router||{};
  $('s-rt-on').checked=!!rc.enabled;$('s-rt-type').value=rc.type||'huawei';$('s-rt-host').value=rc.host||'';$('s-rt-port').value=rc.port||80;$('s-rt-https').checked=!!rc.https;
  $('s-rt-user').value=rc.user||'';$('s-rt-pass').value='';$('s-rt-pass').placeholder=rc.has_password?t('setRouterPassKept'):'';$('s-rt-iface').value=rc.interface||'wan';$('s-rt-every').value=rc.every||30;$('rt-result').textContent='';
  rtTypeChanged(false);
  $('set-overlay').classList.add('show');
}
const RT_PORTS={huawei:80,openwrt:80,ddwrt:80,tplink:80};
function rtTypeChanged(setPort){
  const ty=$('s-rt-type').value;
  if(setPort)$('s-rt-port').value=$('s-rt-https').checked?443:RT_PORTS[ty];
  $('rt-iface-field').style.display=ty==='openwrt'?'':'none';
  if(setPort){$('s-rt-user').value=ty==='ddwrt'?'root':ty==='openwrt'?'root':'admin';}
}
function routerBody(){
  const num=(id,d)=>{const v=parseInt($(id).value);return isNaN(v)?d:v;};
  const o={enabled:$('s-rt-on').checked,type:$('s-rt-type').value,host:$('s-rt-host').value.trim(),port:num('s-rt-port',80),https:$('s-rt-https').checked,user:$('s-rt-user').value.trim(),interface:$('s-rt-iface').value.trim()||'wan',every:num('s-rt-every',30)};
  const pw=$('s-rt-pass').value;if(pw)o.password=pw;
  return o;
}
async function testRouter(){
  const box=$('rt-result'),btn=$('btn-rt-test');box.style.color='var(--text-dim)';box.textContent=t('rtTesting');btn.disabled=true;
  try{
    const {ok,d}=await post('api/wan/router/test',{router:routerBody()});
    if(!ok){box.style.color='var(--red)';box.textContent=d.error||'Error';return;}
    const r=d.result;
    if(r.ok){box.style.color='var(--green)';box.textContent=t('rtTestOk',t(r.wan_up?'rtTestUp':'rtTestDown'),r.ip?' · IP '+r.ip:'');}
    else{box.style.color='var(--red)';box.textContent=t('rtTestFail',r.error||'?');}
  }catch(e){box.style.color='var(--red)';box.textContent=e.message;}
  finally{btn.disabled=false;}
}
async function saveSettings(){
  const btn=$('btn-save');
  const num=(id,d)=>{const v=parseInt($(id).value);return isNaN(v)?d:v;};
  const body={targets:textToTargets($('s-targets').value),gateway:$('s-gw').value.trim(),dns_name:$('s-dns').value.trim(),interval:num('s-interval',30),ip_url:$('s-ipurl').value.trim(),
    speed:{engine:$('s-sp-engine').value,enabled:$('s-sp-on').checked,every_hours:num('s-sp-every',12),seconds:num('s-sp-secs',8),streams:num('s-sp-streams',4),plan_down:num('s-sp-pdown',0),plan_up:num('s-sp-pup',0),upload:$('s-sp-up').checked,down_url:$('s-sp-down').value.trim(),up_url:$('s-sp-upurl').value.trim()},router:routerBody()};
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const {ok,d}=await post('api/wan/config',body);
    if(!ok)throw new Error(d.error||'Error');
    toast(t('saved'));closeModals();_histTs=0;await fetchAll();
  }catch(e){toast(e.message,true);}
  finally{btn.disabled=false;btn.textContent=t('save');}
}


// ── Gráficos de detalle: canvas con rangos 1h / 1d / 1mo / todo, cuadrícula, cursor con tooltip ──
// EN: Detail charts: canvas with 1h / 1d / 1mo / all ranges, grid, hover cursor with tooltip.
const RANGES=VC.RANGES;
const _rangeData={}, _rangeBusy={};          // «clave|rango» → {ts, pts}
const _cid=(id,kind)=>'ch-'+kind+'-'+String(id).replace(/[^a-z0-9]/gi,'-');
async function loadRange(id,range,force,prev){
  const key=id+'|'+range+(prev?'|prev':''),c=_rangeData[key],ttl=range==='1h'?30000:120000;
  if(!force&&c&&Date.now()-c.ts<ttl)return;
  if(_rangeBusy[key])return;_rangeBusy[key]=true;
  try{
    const r=await fetch(historyUrl(id,range)+(prev?'&prev=1':''));
    if(r.ok){const d=await r.json();_rangeData[key]={ts:Date.now(),pts:d.history||[]};drawCharts(id);}
  }catch(e){console.error(e);}
  finally{_rangeBusy[key]=false;}
}
function ensureRanges(){const id=chartOwner();if(id==null)return;Object.keys(CHARTS).forEach(k=>{if(!CHARTS[k].local)loadRange(id,chartRange[k]);});}
function setRange(btn,kind,range){
  chartRange[kind]=range;
  btn.parentNode.querySelectorAll('.vchart-filter:not(.vchart-cmp)').forEach(b=>b.classList.toggle('active',b===btn));
  const id=chartOwner();if(id==null)return;
  if(_rangeData[id+'|'+range])drawCharts(id);
  loadRange(id,range,true);
  if(VC.cmp[kind]&&range!=='all')loadRange(id,range,true,true);
}
function toggleCmp(btn,kind){VC.cmp[kind]=!VC.cmp[kind];btn.classList.toggle('active',!!VC.cmp[kind]);const id=chartOwner();if(id==null)return;const range=chartRange[kind];if(VC.cmp[kind]&&range!=='all')loadRange(id,range,false,true);drawCharts(id);}
function chartSections(id,kinds){
  return (kinds||Object.keys(CHARTS)).map(k=>{
    const C=CHARTS[k],cid=_cid(id,k);
    return VC.section({title:t(C.title),legend:C.series.map(x=>({c:x.c,l:t(x.l)})),filters:C.local?'':VC.filters(chartRange[k],r=>`data-on-click="setRange" data-on-click-args="${jsargs([{'@':'this'},k,r])}"`,`data-on-click="toggleCmp" data-on-click-args="${jsargs([{'@':'this'},k])}"`,VC.cmp[k]),canvasId:cid,tipId:cid+'-tip',h:C.h});
  }).join('');
}
function drawCharts(id){if(id!==chartOwner())return;Object.keys(CHARTS).forEach(k=>drawChart(id,k,-1));}
function drawChart(id,kind,hover){
  const C=CHARTS[kind],cv=document.getElementById(_cid(id,kind));if(!cv)return;
  const range=chartRange[kind],loc=!!C.local;
  VC.draw(cv,{pts:loc?localPts(kind):((_rangeData[id+'|'+range]||{}).pts||[]),prev:!loc&&VC.cmp[kind]?((_rangeData[id+'|'+range+'|prev']||{}).pts||[]):null,
    series:C.series.map(x=>({k:x.k,c:x.c,l:t(x.l),f:x.f})),range:loc?'1mo':range,hover,h:C.h,pl:C.pl,min:C.min,max:C.max,axis:C.axis,points:C.points,down:C.down,mod:loc?null:'wan'});
}
window.addEventListener('resize',()=>{const id=chartOwner();if(id!=null)drawCharts(id);});

// ── Utilidades ───────────────────────────────────────────────────────────────
function fmtNum(n){if(n==null||!isFinite(Number(n)))return '—';return Number(n).toLocaleString(_lang==='es'?'es-CL':'en-GB');}
function fmtDur(s){s=Math.max(0,Math.round(Number(s)||0));const d=Math.floor(s/86400),h=Math.floor((s%86400)/3600),m=Math.floor((s%3600)/60);if(d>0)return d+'d '+h+'h';if(h>0)return h+'h '+m+'m';if(m>0)return m+'m '+(s%60)+'s';return s+'s';}
function fmtDate(ts){const d=new Date(ts*1000);return d.toLocaleDateString(_lang==='es'?'es-CL':'en-GB',{day:'2-digit',month:'2-digit'})+' '+PCT.time(d);}
// Escapa HTML antes de insertar texto de la red o de usuarios en la página: evita inyección de código (XSS).
// EN: Escape HTML before inserting network or user text into the page: prevents code injection (XSS).
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
function jsargs(a){return esc(JSON.stringify(a));}
function updateClock(){const el=document.getElementById('clock');if(el)el.textContent=PCT.time(new Date(),true);}
function closeModals(){document.querySelectorAll('.overlay').forEach(o=>o.classList.remove('show'));}
let _tt;
function toast(msg,isErr=false){const el=document.getElementById('toast');el.textContent=msg;el.style.background=isErr?'var(--red)':'var(--text)';void el.offsetWidth;el.classList.add('show');clearTimeout(_tt);_tt=setTimeout(()=>el.classList.remove('show'),3200);}
async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json().catch(()=>({}));return {ok:r.ok,status:r.status,d};}
function pill(lv,text){return `<span class="pill ${esc(lv)}">${esc(text)}</span>`;}
function barColor(p,w,c){return p>=c?'var(--red)':p>=w?'var(--orange)':'var(--green)';}
function bar(p,w=80,c=92,color){p=Math.max(0,Math.min(100,Number(p)||0));return `<div class="res-bar-wrap"><div class="res-bar" style="width:${p}%;background:${color||barColor(p,w,c)}"></div></div>`;}
function kv(k,v){return `<div class="kv"><span class="k">${esc(k)}</span><span class="v">${v}</span></div>`;}
function ring(label,pct,color,txt){
  const C=2*Math.PI*14.5,p=pct==null?0:Math.max(0,Math.min(100,pct));
  return `<div class="gauge-box"><span class="gauge-lbl">${esc(label)}</span><div class="circle-wrap"><svg viewBox="0 0 36 36"><circle class="circle-bg" cx="18" cy="18" r="14.5"/><circle class="circle-fill" cx="18" cy="18" r="14.5" style="opacity:${pct==null?0:1};stroke:${color};stroke-dasharray:${C};stroke-dashoffset:${C*(1-p/100)}"/></svg><div class="circle-val">${esc(txt==null?(pct==null?'—':Math.round(pct)+'%'):txt)}</div></div></div>`;
}
function bigNum(label,val,unit,color){
  return `<div class="gauge-box"><span class="gauge-lbl">${esc(label)}</span><div class="gauge-num"><span class="runtime-num" style="color:${color||'var(--text)'}">${esc(val)}</span></div><span class="gauge-unit">${esc(unit||'')}</span></div>`;
}
function alertText(a){const ty=(a.type==='ip_changed'&&a.prev)?'ip_changed_from':a.type;const f=(LANG[_lang].al||{})[ty]||(LANG.en.al||{})[ty];return f?f.replace(/\{1\}/g,a.prev||'').replace(/\{0\}/g,a.value==null?'':(a.type.indexOf('down_')===0?fmtDate(a.value):a.value)):a.type;}
function alertsHtml(list){
  const al=(list||[]);if(!al.length)return '';
  return '<div class="alerts">'+al.map(a=>`<div class="alert ${esc(a.lv)}">${a.lv==='crit'?'⛔':a.lv==='warn'?'⚠':'ℹ'} ${esc(alertText(a))}</div>`).join('')+'</div>';
}

document.querySelectorAll('.overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)closeModals();}));
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModals();});

// ── Menú lateral en pantallas pequeñas ──
function toggleNav(force){
  const open=force!==undefined?force:!document.body.classList.contains('nav-open');
  document.body.classList.toggle('nav-open',open);
  const b=document.getElementById('nav-toggle');if(b)b.setAttribute('aria-expanded',open);
}
(function(){
  const sb=document.querySelector('.sidebar');
  if(sb)sb.addEventListener('click',e=>{if(e.target.closest('a,.nav-item,.cluster-nav,.btn-add-cluster'))setTimeout(()=>toggleNav(false),0);});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')toggleNav(false);});
  window.addEventListener('resize',()=>{if(window.innerWidth>960)toggleNav(false);});
})();

// ── Recordarme ──
function remValue(){const c=document.getElementById('l-rem'),s=document.getElementById('l-remsel');const v=c&&c.checked&&s?s.value:'';try{localStorage.setItem('pi-remember',v)}catch(e){}return v}
(function remInit(){try{const v=localStorage.getItem('pi-remember')||'';const c=document.getElementById('l-rem'),s=document.getElementById('l-remsel');if(c&&s&&['day','week','month','forever'].includes(v)){c.checked=true;s.disabled=false;s.value=v}}catch(e){}})();

_i18nReady=true;
(async()=>{
  const ok=await checkSession();
  if(ok){applyPermissions();await initApp();const ls=document.getElementById('login-screen');ls.style.opacity='0';setTimeout(()=>ls.style.display='none',150);}else{document.getElementById('login-screen').style.display='flex';}
})();

// Funciones que el HTML puede invocar con data-on-* (lista cerrada; ver csp-bind.js).
// EN: Functions the HTML may call through data-on-* (closed list; see csp-bind.js).
if (window.cspRegister) cspRegister({ setIpSince, toggleTrace, closeModals, doLogin, logout, rtTypeChanged, runSpeed, saveSettings, testRouter, setLang, setRange, toggleCmp, setTheme, toggleNav });
