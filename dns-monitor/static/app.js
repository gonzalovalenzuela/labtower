// DNS Monitor — página del módulo (/dns/). Muestra uno o varios Pi-hole (v6 y v5) o AdGuard Home.
// EN: DNS Monitor — module page (/dns/). Shows one or more Pi-hole (v6 and v5) or AdGuard Home servers.
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
 "connecting": "Connecting…",
 "connectingMsg": "Reading the DNS server.",
 "navServers": "DNS servers",
 "addServer": "Add server",
 "statSrv": "Servers online",
 "statQ": "Queries (24 h)",
 "statBlk": "Blocked",
 "statMs": "Avg response",
 "statProt": "Protection",
 "noServers": "No DNS server configured",
 "noServersHint": "Add a Pi-hole or an AdGuard Home to get started.",
 "addTitle": "Add DNS server",
 "editTitle": "Edit DNS server",
 "formHintPihole": "Pi-hole v6 and v5 are detected by themselves. v6: use the web password or an app password (Settings → Web interface / API). v5: use the API token (Settings → API → Show API token).",
 "formHintAdguard": "AdGuard Home: use a user of its web panel. Its HTTP port is the one of the panel (3000 or 80).",
 "fieldName": "Name",
 "fieldType": "Type",
 "fieldUrl": "Address",
 "fieldUser": "Username",
 "fieldPassPihole": "Password or token",
 "fieldPassAdguard": "Password",
 "fieldTls": "Verify the TLS certificate (if off, the certificate is pinned on first connection and a change is refused)",
 "fieldTimeout": "Timeout (s)",
 "secretKept": "Saved. Leave empty to keep it.",
 "added": "{0} added",
 "deleted": "{0} deleted",
 "deleteServer": "Delete server",
 "deleteConfirm": "Delete \"{0}\" and its history?",
 "testOk": "✓ {0} {1} — {2} queries",
 "online": "Online",
 "offline": "Unreachable",
 "connError": "Connection error",
 "connErrorHint": "Check the address, the password or token and, for HTTPS with its own certificate, turn off the certificate check.",
 "colServer": "Server",
 "colType": "Type",
 "colQueries": "Queries",
 "colBlocked": "Blocked",
 "colClients": "Clients",
 "colResp": "Response",
 "colProt": "Protection",
 "summary": "DNS servers",
 "protOn": "Active",
 "protOff": "Paused",
 "protFail": "Failed",
 "protUnk": "Unknown",
 "pause": "Pause blocking",
 "resume": "Resume blocking",
 "pauseTitle": "Pause blocking",
 "pauseHint": "Ads and trackers will not be blocked on \"{0}\" for the time you choose.",
 "pause5": "5 minutes",
 "pause30": "30 minutes",
 "pause60": "1 hour",
 "pauseUntil": "Until I resume it",
 "paused": "Blocking paused",
 "resumed": "Blocking resumed",
 "pauseBtn": "Pause",
 "gBlocked": "% blocked",
 "gQueries": "Queries",
 "gBlockedN": "Blocked",
 "gLists": "Domains in lists",
 "gClients": "Clients",
 "gResp": "Response",
 "topDomains": "Top domains",
 "topBlocked": "Top blocked",
 "topClients": "Top clients",
 "upstreams": "Upstream DNS",
 "hourly": "Queries per hour (last 24 h)",
 "info": "Server",
 "version": "Version",
 "api": "API",
 "cached": "Answered from cache",
 "forwarded": "Forwarded",
 "uniqueDomains": "Unique domains",
 "gravity": "Lists updated",
 "legTotal": "All",
 "legBlocked": "Blocked",
 "noData": "No data yet",
 "now": "now",
 "histPct": "% blocked",
 "histMs": "Response time",
 "sPct": "% blocked",
 "sMs": "response",
 "al": {
  "blocking_off": "Blocking is paused",
  "blocking_failed": "Blocking failed",
  "no_lists": "No domains in the block lists",
  "slow_upstream": "Slow upstream DNS ({0} ms)"
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
 "connecting": "Conectando…",
 "connectingMsg": "Leyendo el servidor DNS.",
 "navServers": "Servidores DNS",
 "addServer": "Agregar servidor",
 "statSrv": "Servidores en línea",
 "statQ": "Consultas (24 h)",
 "statBlk": "Bloqueadas",
 "statMs": "Respuesta media",
 "statProt": "Protección",
 "noServers": "Sin servidores DNS configurados",
 "noServersHint": "Agrega un Pi-hole o un AdGuard Home para empezar.",
 "addTitle": "Agregar servidor DNS",
 "editTitle": "Editar servidor DNS",
 "formHintPihole": "Pi-hole v6 y v5 se detectan solos. v6: usa la contraseña web o una contraseña de aplicación (Ajustes → Interfaz web / API). v5: usa el token de la API (Ajustes → API → Mostrar token).",
 "formHintAdguard": "AdGuard Home: usa un usuario de su panel web. Su puerto HTTP es el del panel (3000 u 80).",
 "fieldName": "Nombre",
 "fieldType": "Tipo",
 "fieldUrl": "Dirección",
 "fieldUser": "Usuario",
 "fieldPassPihole": "Contraseña o token",
 "fieldPassAdguard": "Contraseña",
 "fieldTls": "Verificar el certificado TLS (si se desactiva, se fija la huella en la primera conexión y un cambio se rechaza)",
 "fieldTimeout": "Tiempo de espera (s)",
 "secretKept": "Guardada. Déjala vacía para conservarla.",
 "added": "{0} agregado",
 "deleted": "{0} eliminado",
 "deleteServer": "Eliminar servidor",
 "deleteConfirm": "¿Eliminar «{0}» y su historial?",
 "testOk": "✓ {0} {1} — {2} consultas",
 "online": "En línea",
 "offline": "Sin conexión",
 "connError": "Error de conexión",
 "connErrorHint": "Revisa la dirección, la contraseña o el token y, para HTTPS con certificado propio, desactiva la verificación del certificado.",
 "colServer": "Servidor",
 "colType": "Tipo",
 "colQueries": "Consultas",
 "colBlocked": "Bloqueadas",
 "colClients": "Clientes",
 "colResp": "Respuesta",
 "colProt": "Protección",
 "summary": "Servidores DNS",
 "protOn": "Activa",
 "protOff": "Pausada",
 "protFail": "Con falla",
 "protUnk": "Desconocida",
 "pause": "Pausar bloqueo",
 "resume": "Reanudar bloqueo",
 "pauseTitle": "Pausar el bloqueo",
 "pauseHint": "No se bloquearán anuncios ni rastreadores en «{0}» durante el tiempo que elijas.",
 "pause5": "5 minutos",
 "pause30": "30 minutos",
 "pause60": "1 hora",
 "pauseUntil": "Hasta que lo reanude",
 "paused": "Bloqueo pausado",
 "resumed": "Bloqueo reanudado",
 "pauseBtn": "Pausar",
 "gBlocked": "% bloqueado",
 "gQueries": "Consultas",
 "gBlockedN": "Bloqueadas",
 "gLists": "Dominios en listas",
 "gClients": "Clientes",
 "gResp": "Respuesta",
 "topDomains": "Dominios más consultados",
 "topBlocked": "Dominios más bloqueados",
 "topClients": "Clientes más activos",
 "upstreams": "DNS de salida",
 "hourly": "Consultas por hora (últimas 24 h)",
 "info": "Servidor",
 "version": "Versión",
 "api": "API",
 "cached": "Respondidas desde la caché",
 "forwarded": "Reenviadas",
 "uniqueDomains": "Dominios únicos",
 "gravity": "Listas actualizadas",
 "legTotal": "Todas",
 "legBlocked": "Bloqueadas",
 "noData": "Aún sin datos",
 "now": "ahora",
 "histPct": "% bloqueado",
 "histMs": "Tiempo de respuesta",
 "sPct": "% bloqueado",
 "sMs": "respuesta",
 "al": {
  "blocking_off": "El bloqueo está pausado",
  "blocking_failed": "El bloqueo falló",
  "no_lists": "No hay dominios en las listas de bloqueo",
  "slow_upstream": "DNS de salida lento ({0} ms)"
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
}
(()=>setLang(_lang))();

let ME=null;
const $=id=>document.getElementById(id);

// ── Tema ─────────────────────────────────────────────────────────────────────
function setTheme(t){localStorage.setItem('pi-theme',t);applyTheme(t);['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));}
function applyTheme(t){const p=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;document.documentElement.setAttribute('data-theme',p==='dark'?'dark':'light');}
(()=>{const t=localStorage.getItem('pi-theme')||'dark';applyTheme(t);window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if((localStorage.getItem('pi-theme')||'dark')==='system')applyTheme('system');});setTimeout(()=>document.getElementById('theme-'+t)?.classList.add('active'),0);})();

// ── Menú lateral común (reordenable; el orden se guarda en el navegador, clave pi-nav-order) ──
function canAdmin(){return ME&&ME.permissions?.dns==='admin';}
function canExec(){return ME&&['execute','admin'].includes(ME.permissions?.dns);}
const _NAV_ITEMS=[
  {id:'overview', href:'/overview/', label:'Overview', svg:'<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>'},
  {id:'nut',  href:'/nut/',   label:'UPS Monitor', svg:'<path d="M5 9V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v4"/><rect x="3" y="9" width="18" height="11" rx="2"/><line x1="12" y1="13" x2="12" y2="16"/>'},
  {id:'net',  href:'/net/',   label:'Net Monitor', svg:'<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>'},
  {id:'pve',  href:'/pve/',   label:'Proxmox',     svg:'<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>'},
  {id:'nas',  href:'/nas/',   label:'NAS Monitor', svg:'<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="7" y1="9" x2="17" y2="9"/><line x1="7" y1="14" x2="17" y2="14"/><line x1="16" y1="18" x2="16.01" y2="18"/>'},
  {id:'dns',  href:'/dns/',   label:'DNS Monitor', svg:'<circle cx="12" cy="12" r="9"/><line x1="3" y1="12" x2="21" y2="12"/><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z"/>'},
  {id:'wan',  href:'/wan/',   label:'WAN Monitor', svg:'<path d="M5 12.55a11 11 0 0 1 14 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/>'},
  {id:'wol',  href:'/wol/',   label:'WOL Console', svg:'<polygon points="13,2 3,14 12,14 11,22 21,10 12,10"/>'},
  {id:'admin',href:'/admin/', label:'Admin Panel', svg:'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',adminOnly:true},
];
const _NAV_SELF='dns';
let _navDragSrc=null;
function _navOrder(){
  try{const s=JSON.parse(localStorage.getItem('pi-nav-order')||'[]');
    if(s.length){const ids=_NAV_ITEMS.map(i=>i.id);const o=s.filter(id=>ids.includes(id));ids.forEach(id=>{if(!o.includes(id))o.push(id);});return o;}}catch(e){}
  return _NAV_ITEMS.map(i=>i.id);
}
function renderNav(){
  const wrap=document.getElementById('nav-items');if(!wrap)return;
  const order=_navOrder(),isAdmin=ME&&Object.values(ME.permissions||{}).includes('admin');
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
}

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
  const k={readonly:'permReadonly',execute:'permExecute',admin:'permAdmin'}[ME.permissions?.dns];
  document.getElementById('me-role').textContent=k?t(k):'—';
  renderNav();
  if(typeof afterPermissions==='function')afterPermissions();
}
async function logout(){await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.reload();}

// ── Datos ────────────────────────────────────────────────────────────────────
const POLL=5000;                 // el servidor lee cada 15 s con alguien mirando; la página pide cada 5 s mientras se ve
let items=[], activeId=null, pollTimer=null, _histTs=0, _histCache={};
function afterPermissions(){$('btn-add').style.display=canAdmin()?'':'none';}
async function initApp(){
  updateClock();setInterval(updateClock,1000);
  await fetchAll();
  pollTimer=setInterval(()=>{if(!document.hidden)fetchAll();},POLL);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)fetchAll();});
}
// Descarga los servidores con su última lectura. El historial pesado se pide solo cada 30 s y se reutiliza entre medias.
// EN: Download the servers with their last reading. The heavy history is requested only every 30 s and reused in between.
async function fetchAll(){
  try{
    const wantHist=Date.now()-_histTs>=30000;
    const r=await fetch('api/dns'+(wantHist?'':'?hist=0'));
    if(r.status===401){location.reload();return;}
    const d=await r.json();
    items=d.servers||[];
    items.forEach(n=>{if(wantHist)_histCache[n.id]=n.history; else n.history=_histCache[n.id]||[];});
    if(wantHist)_histTs=Date.now();
    if(activeId!==''&&!items.some(n=>n.id===activeId))activeId=items[0]?.id||null;
    renderAll();ensureRanges();
  }catch(e){console.error(e);}
}
function renderAll(){renderSidebar();renderSummary();renderMain();updateGlobalStats();}
function selectServer(id){activeId=id;renderAll();ensureRanges();}
function toggleServer(id){activeId=activeId===id?'':id;renderAll();ensureRanges();}
function lvOf(n){const s=n.snap;if(!s?.ts)return 'loading';if(s.error)return 'err';return 'ok';}
function typeName(n){const d=n.snap?.data||{};return n.type==='adguard'?'AdGuard Home':'Pi-hole'+(d.api?' '+d.api:'');}
function renderSidebar(){
  const list=$('srv-list');list.innerHTML='';
  items.forEach(n=>{
    const isActive=n.id===activeId,div=document.createElement('div');
    div.className='cluster-nav'+(isActive?' active':'');
    div.onclick=()=>selectServer(n.id);
    div.innerHTML=`<span class="cluster-dot ${lvOf(n)}"></span><div style="flex:1;min-width:0"><div class="cluster-nav-name ${isActive?'act':''}">${esc(n.name)}</div>
      <div class="cluster-nav-host">${esc(typeName(n))}</div></div>`;
    list.appendChild(div);
  });
}
function protLabel(b){return t({enabled:'protOn',disabled:'protOff',failed:'protFail'}[b]||'protUnk');}
function protPill(d){const b=d?.blocking;return pill(b==='enabled'?'ok':b==='disabled'?'warn':b==='failed'?'crit':'off',protLabel(b));}
// Contadores de la cabecera sumando todos los servidores.
// EN: Header counters adding up all the servers.
function updateGlobalStats(){
  let on=0,q=0,b=0,msS=0,msN=0,prot=0,protAll=0;
  items.forEach(n=>{
    const d=n.snap?.data;if(!d||n.snap.error)return;on++;q+=d.queries||0;b+=d.blocked||0;
    if(d.ms!=null){msS+=d.ms;msN++;}protAll++;if(d.blocking==='enabled')prot++;
  });
  $('st-srv').textContent=items.length?`${on}/${items.length}`:'—';
  $('st-q').textContent=on?fmtNum(q):'—';
  $('st-blk').innerHTML=q?Math.round(b/q*1000)/10+'<span style="font-size:13px;color:var(--text-dim)">%</span>':'—';
  $('st-ms').innerHTML=msN?Math.round(msS/msN)+'<span style="font-size:13px;color:var(--text-dim)"> ms</span>':'—';
  $('st-prot').textContent=protAll?`${prot}/${protAll}`:'—';
}
function renderMain(){
  const n=items.find(x=>x.id===activeId);
  $('main-content').innerHTML=items.length?'':'<div class="state-msg"><strong>'+esc(t('noServers'))+'</strong>'+esc(t('noServersHint'))+'</div>';
  const sub=$('tb-sub');sub.textContent='';
  $('tb-title').textContent=n?n.name:'DNS Monitor';
  if(n){const hs=document.createElement('span');hs.textContent=n.url;sub.appendChild(hs);}
}
function spark(hist){
  const pts=(hist||[]).filter(p=>p&&typeof p.ts==='number');if(pts.length<3)return '<span class="sum-sub">—</span>';
  const W=90,H=24,t0=pts[0].ts,t1=pts[pts.length-1].ts||t0+1;let d='',pen=false;
  const mx=Math.max(1,...pts.map(p=>Number(p.pct)||0));
  pts.forEach(p=>{const v=Number(p.pct);if(p.pct==null||!isFinite(v)){pen=false;return;}d+=(pen?'L':'M')+(((p.ts-t0)/Math.max(1,t1-t0))*W).toFixed(1)+' '+(H-1-v/mx*(H-2)).toFixed(1)+' ';pen=true;});
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}"><path d="${d}" fill="none" stroke="#10b981" stroke-width="1.5"/></svg>`;
}
// Tabla con todos los servidores: cada fila se abre y muestra el detalle justo debajo. Por defecto, el primero.
// EN: Table with every server: each row opens and shows its detail right below. The first one by default.
function renderSummary(){
  const box=$('dns-summary');if(!box)return;
  if(!items.length){box.innerHTML='';return;}
  const rows=items.map(n=>{
    const sn=n.snap||{},d=sn.data,lv=lvOf(n),open=n.id===activeId;
    const al=(d?.alerts||[]).filter(a=>a.lv!=='info'),worst=al.some(a=>a.lv==='crit')?'crit':al.length?'warn':'ok';
    const state=lv==='loading'?pill('off','…'):lv==='err'?pill('crit',t('offline')):pill(worst,worst==='ok'?t('online'):al.length+' ⚠');
    return `<tr class="dns-row${open?' expanded':''}" data-on-click="toggleServer" data-on-click-args="${jsargs([n.id])}">
      <td><span class="cluster-dot ${lv}"></span></td>
      <td><div class="sum-name">${esc(n.name)}</div><div class="sum-sub">${esc(n.url)}</div></td>
      <td class="c-model">${esc(typeName(n))}<div class="sum-sub">${esc(d?.version||'')}</div></td>
      <td>${state}</td>
      <td>${d?esc(fmtNum(d.queries)):'—'}</td>
      <td>${d?`<span style="font-weight:600">${esc(d.pct)}%</span><div class="sum-sub">${esc(fmtNum(d.blocked))}</div>`:'—'}</td>
      <td class="c-temp">${d&&d.clients!=null?esc(d.clients):'—'}</td>
      <td class="c-temp">${d&&d.ms!=null?esc(d.ms)+' ms':'—'}</td>
      <td>${d?protPill(d):'—'}</td>
      <td class="c-spark">${spark(n.history)}</td>
      <td><span class="expand-arrow ${open?'open':''}">▶</span></td></tr>
    <tr class="detail-row${open?' show':''}"><td colspan="11" class="detail-cell"><div class="dns-detail">${open?buildDetail(n):''}</div></td></tr>`;
  }).join('');
  box.innerHTML=`<div class="card"><div class="card-hd"><span class="card-title">${esc(t('summary'))}</span><span class="card-meta">${esc(items.length)}</span></div>
    <div class="tbl-wrap"><table class="dns-table"><thead><tr><th style="width:24px"></th><th>${esc(t('colServer'))}</th><th class="c-model">${esc(t('colType'))}</th><th>${esc(t('status'))}</th><th>${esc(t('colQueries'))}</th><th>${esc(t('colBlocked'))}</th><th class="c-temp">${esc(t('colClients'))}</th><th class="c-temp">${esc(t('colResp'))}</th><th>${esc(t('colProt'))}</th><th class="c-spark">%</th><th style="width:24px"></th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
  fitDetail();drawCharts(activeId);
}
function fitDetail(){const w=document.querySelector('#dns-summary .tbl-wrap');if(w)w.style.setProperty('--wrapw',w.clientWidth+'px');}
function topList(title,list,color){
  const mx=Math.max(1,...(list||[]).map(x=>x.count||0));
  const rows=(list||[]).length?list.map(x=>`<div class="top-row"><span class="tn" title="${esc(x.name||'')}">${esc(x.name||'—')}</span><span class="tc">${esc(fmtNum(x.count))}</span><div class="tb">${bar((x.count||0)/mx*100,101,101,color)}</div></div>`).join(''):`<div class="dns-empty">${esc(t('noData'))}</div>`;
  return `<div class="node-card"><div class="node-hd"><div class="node-name">${esc(title)}</div></div>${rows}</div>`;
}
// Barras de las últimas 24 horas (total y bloqueadas), como SVG sin JavaScript extra; el título de cada barra da la hora y los valores.
// EN: Bars for the last 24 hours (total and blocked), as SVG with no extra JavaScript; each bar's title gives the hour and the values.
function hourly(h){
  const tot=h?.total||[],blk=h?.blocked||[];
  if(!tot.length||!tot.some(x=>x>0))return `<div class="dns-empty">${esc(t('noData'))}</div>`;
  const mx=Math.max(...tot,1),W=240,H=64,bw=W/24,now=Date.now();let s='';
  tot.forEach((v,i)=>{
    const hh=Math.max(.6,v/mx*(H-4)),bh=Math.min(hh,(blk[i]||0)/mx*(H-4)),x=(i*bw+1.2).toFixed(1),w=(bw-2.4).toFixed(1),hr=new Date(now-(23-i)*3600000).getHours();
    s+=`<g><title>${esc(String(hr).padStart(2,'0')+':00 · '+fmtNum(v)+' / '+fmtNum(blk[i]||0))}</title><rect x="${x}" y="${(H-hh).toFixed(1)}" width="${w}" height="${hh.toFixed(1)}" rx="1.5" class="hb-t"/><rect x="${x}" y="${(H-bh).toFixed(1)}" width="${w}" height="${bh.toFixed(1)}" rx="1.5" class="hb-b"/></g>`;
  });
  return `<svg class="dns-hourly" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${s}</svg><div class="dns-hourly-axis"><span>-24 h</span><span>-12 h</span><span>${esc(t('now'))}</span></div>
    <div class="vchart-legend" style="padding:6px 14px 10px"><div class="vchart-legend-item"><div class="vchart-legend-dot" style="background:var(--dns-soft)"></div>${esc(t('legTotal'))}</div><div class="vchart-legend-item"><div class="vchart-legend-dot" style="background:var(--dns)"></div>${esc(t('legBlocked'))}</div></div>`;
}
function buildDetail(n){
  const snap=n.snap||{};
  const d=snap.data,hasData=d&&d.queries!=null;
  let tools='';
  if(canExec()&&hasData){
    tools+=d.blocking==='disabled'?`<button class="btn-secondary" data-on-click="resumeBlocking" data-on-click-args="${jsargs([n.id])}">${esc(t('resume'))}</button>`
      :`<button class="btn-secondary" data-on-click="openPause" data-on-click-args="${jsargs([n.id,n.name])}">${esc(t('pause'))}</button>`;
  }
  if(canAdmin())tools+=`<button class="btn-secondary" data-on-click="openForm" data-on-click-args="${jsargs([n.id])}">${esc(t('edit'))}</button><button class="btn-secondary" data-on-click="confirmDelete" data-on-click-args="${jsargs([n.id,n.name])}">${esc(t('delete'))}</button>`;
  tools=`<div class="dns-tools">${tools}</div>`;
  if(!snap.ts)return '<div class="state-msg"><strong>'+esc(t('connecting'))+'</strong>'+esc(t('connectingMsg'))+'</div>';
  if(snap.error&&!hasData){
    return `<div class="dns-head"><div><h2>${esc(n.name)}</h2></div>${tools}</div><div class="state-msg err"><strong>${esc(t('connError'))}</strong>${esc(snap.error)}<br><br><span style="font-size:12px;font-family:var(--mono)">${esc(t('connErrorHint'))}</span></div>`;
  }
  const offline=!!snap.error;
  let h=`<div class="dns-head"><div><h2>${esc(n.name)} ${offline?pill('crit',t('offline')):pill('ok',t('online'))}</h2><div class="sub">${esc(typeName(n))} ${esc(d.version||'')} · ${esc(n.url)}</div></div>${tools}</div>`;
  if(offline)h+=`<div class="alerts"><div class="alert crit">⚠ ${esc(t('connError'))}: ${esc(snap.error)}</div></div>`;
  h+=alertsHtml(d.alerts);
  const pc=d.pct==null?null:d.pct;
  h+='<div class="dns-gauges">'+ring(t('gBlocked'),pc,'var(--dns)',pc==null?'—':pc+'%')+bigNum(t('gQueries'),fmtNum(d.queries),'')+bigNum(t('gBlockedN'),fmtNum(d.blocked),'','var(--red)')
    +bigNum(t('gLists'),fmtNum(d.domains_blocked),'')+bigNum(t('gClients'),d.clients==null?'—':d.clients,'')+bigNum(t('gResp'),d.ms==null?'—':d.ms,d.ms==null?'':'ms',d.ms>=200?'var(--orange)':'var(--text)')+'</div>';
  h+='<div class="dns-grid">';
  h+=`<div class="node-card wide"><div class="node-hd"><div class="node-name">${esc(t('hourly'))}</div></div>${hourly(d.hourly)}</div>`;
  h+=topList(t('topDomains'),d.top_domains,'var(--dns)')+topList(t('topBlocked'),d.top_blocked,'var(--red)')+topList(t('topClients'),d.top_clients,'var(--blue)');
  const ups=(d.upstreams||[]).map(u=>`<div class="top-row"><span class="tn" title="${esc(u.ip||'')}">${esc(u.name||u.ip||'—')}${u.port?`<small>:${esc(u.port)}</small>`:''}</span><span class="tc">${esc(fmtNum(u.count))}${u.ms!=null?' · '+esc(u.ms)+' ms':''}</span></div>`).join('');
  h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('upstreams'))}</div></div>${ups||`<div class="dns-empty">${esc(t('noData'))}</div>`}</div>`;
  const cachedPct=d.cached!=null&&d.queries?Math.round(d.cached/d.queries*100):null;
  h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('info'))}</div></div>
    ${kv(t('colProt'),protPill(d)+(d.timer?` <span class="sum-sub">${esc(fmtDur(d.timer))}</span>`:''))}
    ${kv(t('version'),esc(d.version||'—'))}${kv(t('api'),esc(d.api||'—'))}
    ${d.cached!=null?kv(t('cached'),esc(fmtNum(d.cached)+(cachedPct!=null?' ('+cachedPct+'%)':''))):''}${d.forwarded!=null?kv(t('forwarded'),esc(fmtNum(d.forwarded))):''}
    ${d.unique_domains!=null?kv(t('uniqueDomains'),esc(fmtNum(d.unique_domains))):''}${d.gravity_updated?kv(t('gravity'),esc(fmtDate(d.gravity_updated))):''}</div>`;
  h+='</div>'+chartSections(n.id);
  return h;
}
// Gráficos de historial: % bloqueado y tiempo de respuesta.
// EN: History charts: % blocked and response time.
const CHARTS={
  pct:{title:'histPct',max:100,series:[{k:'pct',c:'#10b981',l:'sPct',f:v=>v.toFixed(1)+'%'}],axis:v=>Math.round(v)+'%',h:130,pl:40},
  ms:{title:'histMs',series:[{k:'ms',c:'#f97316',l:'sMs',f:v=>v.toFixed(1)+' ms'}],axis:v=>Math.round(v)+' ms',h:120,pl:52},
};
const chartRange={pct:'1d',ms:'1d'};
const chartOwner=()=>activeId||null;
const historyUrl=(id,range)=>'api/dns/'+encodeURIComponent(id)+'/history?range='+range;

// ── Pausar y reanudar el bloqueo (nivel «execute») ───────────────────────────
let _pauseId=null;
function openPause(id,name){
  _pauseId=id;$('pause-msg').textContent=t('pauseHint',name);
  $('pause-btn').onclick=async()=>{
    const s=parseInt($('pause-sel').value)||null;closeModals();
    try{const r=await post('api/dns/'+_pauseId+'/blocking',{enabled:false,seconds:s});if(!r.ok)throw new Error(r.d.error||'Error');toast(t('paused'));setTimeout(fetchAll,1200);}
    catch(e){toast(e.message,true);}
  };
  $('pause-overlay').classList.add('show');
}
async function resumeBlocking(id){
  try{const r=await post('api/dns/'+id+'/blocking',{enabled:true});if(!r.ok)throw new Error(r.d.error||'Error');toast(t('resumed'));setTimeout(fetchAll,1200);}
  catch(e){toast(e.message,true);}
}

// ── Alta, edición, prueba y borrado (solo administradores) ────────────────────
// La clave nunca vuelve del servidor: al editar queda vacía y dejarla vacía conserva la guardada.
// EN: The password never comes back from the server: when editing it is empty and leaving it empty keeps the stored one.
let editingId=null;
function typeChanged(){
  const ag=$('f-type').value==='adguard';
  $('user-wrap').style.display=ag?'':'none';
  $('pass-lbl').textContent=t(ag?'fieldPassAdguard':'fieldPassPihole');
  $('form-hint').textContent=t(ag?'formHintAdguard':'formHintPihole');
  if(!$('f-url').value.trim()||/^http:\/\/192\.0\.2\.5(:\d+)?$/.test($('f-url').value))$('f-url').placeholder=ag?'http://192.0.2.5:3000':'http://192.0.2.5';
}
function openForm(id){
  editingId=typeof id==='string'?id:null;
  const n=editingId?items.find(x=>x.id===editingId):null;
  $('form-title').textContent=t(n?'editTitle':'addTitle');
  $('f-name').value=n?n.name:'';$('f-type').value=n?n.type:'pihole';$('f-url').value=n?n.url:'';
  $('f-user').value=n?n.username:'';$('f-pass').value='';$('f-timeout').value=n?n.timeout:8;$('f-tls').checked=n?n.verify_tls!==false:true;
  $('h-password').textContent=n&&n.has_password?t('secretKept'):'';
  $('test-result').className='test-result';
  typeChanged();
  $('add-overlay').classList.add('show');$('f-name').focus();
}
function formBody(){
  const b={name:$('f-name').value.trim(),type:$('f-type').value,url:$('f-url').value.trim(),username:$('f-user').value.trim(),password:$('f-pass').value,
    verify_tls:$('f-tls').checked,timeout:parseInt($('f-timeout').value)||8};
  if(editingId)b.id=editingId;
  return b;
}
async function testServer(){
  const btn=$('btn-test'),res=$('test-result'),b=formBody();
  if(!b.name||!b.url){res.className='test-result fail show';res.textContent='✕ '+t('testFillAll');return;}
  btn.innerHTML='<span class="spin">⟳</span>';btn.disabled=true;
  try{
    const {d}=await post('api/test',b);
    if(d.ok){res.className='test-result ok show';res.textContent=t('testOk',d.type==='adguard'?'AdGuard Home':'Pi-hole',d.version||d.api||'',fmtNum(d.queries));}
    else{res.className='test-result fail show';res.textContent='✕ '+(d.error||'Error');}
  }catch(e){res.className='test-result fail show';res.textContent='✕ '+e.message;}
  finally{btn.disabled=false;btn.textContent=t('test');}
}
async function saveServer(){
  const btn=$('btn-save'),b=formBody();
  if(!b.name||!b.url){toast(t('testFillAll'),true);return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const {ok,d}=await post(editingId?'api/dns/'+editingId:'api/dns',b);
    if(!ok)throw new Error(d.error||'Error');
    toast(editingId?t('saved'):t('added',b.name));closeModals();_histTs=0;await fetchAll();if(!editingId)selectServer(d.server.id);
  }catch(e){toast(e.message,true);}
  finally{btn.disabled=false;btn.textContent=t('save');}
}
function confirmDelete(id,name){
  $('del-msg').textContent=t('deleteConfirm',name);
  $('del-btn').onclick=async()=>{
    closeModals();
    try{const r=await fetch('api/dns/'+id,{method:'DELETE'});if(!r.ok)throw new Error((await r.json().catch(()=>({}))).error||'Error');toast(t('deleted',name));await fetchAll();}
    catch(e){toast(e.message,true);}
  };
  $('del-overlay').classList.add('show');
}


// ── Gráficos de detalle: canvas con rangos 1h / 1d / 1mo / todo, cuadrícula, cursor con tooltip ──
// EN: Detail charts: canvas with 1h / 1d / 1mo / all ranges, grid, hover cursor with tooltip.
const RANGES=['1h','1d','1mo','all'];
const _rangeData={}, _rangeBusy={};          // «clave|rango» → {ts, pts}
const _cid=(id,kind)=>'ch-'+kind+'-'+String(id).replace(/[^a-z0-9]/gi,'-');
async function loadRange(id,range,force){
  const key=id+'|'+range,c=_rangeData[key],ttl=range==='1h'?30000:120000;
  if(!force&&c&&Date.now()-c.ts<ttl)return;
  if(_rangeBusy[key])return;_rangeBusy[key]=true;
  try{
    const r=await fetch(historyUrl(id,range));
    if(r.ok){const d=await r.json();_rangeData[key]={ts:Date.now(),pts:d.history||[]};drawCharts(id);}
  }catch(e){console.error(e);}
  finally{_rangeBusy[key]=false;}
}
function ensureRanges(){const id=chartOwner();if(id==null)return;Object.keys(CHARTS).forEach(k=>{if(!CHARTS[k].local)loadRange(id,chartRange[k]);});}
function setRange(btn,kind,range){
  chartRange[kind]=range;
  btn.parentNode.querySelectorAll('.vchart-filter').forEach(b=>b.classList.toggle('active',b===btn));
  const id=chartOwner();if(id==null)return;
  if(_rangeData[id+'|'+range])drawCharts(id);
  loadRange(id,range,true);
}
function chartSections(id,kinds){
  return (kinds||Object.keys(CHARTS)).map(k=>{
    const C=CHARTS[k],cid=_cid(id,k);
    const leg=C.series.map(x=>`<div class="vchart-legend-item"><div class="vchart-legend-dot" style="background:${x.c}"></div>${esc(t(x.l))}</div>`).join('');
    const flt=C.local?'':RANGES.map(r=>`<button class="vchart-filter${chartRange[k]===r?' active':''}" data-on-click="setRange" data-on-click-args="${jsargs([{'@':'this'},k,r])}">${r==='all'?esc(t('filterAll')):r}</button>`).join('');
    return `<div class="vchart-section"><div class="vchart-header"><span class="vchart-title">${esc(t(C.title))}</span><div class="vchart-legend">${leg}</div><div class="vchart-filters">${flt}</div></div>
      <div class="vchart-body" style="position:relative"><div class="vchart-tooltip" id="${cid}-tip"></div><canvas class="vchart" id="${cid}" style="--chart-h:${C.h}px"></canvas></div></div>`;
  }).join('');
}
function drawCharts(id){if(id!==chartOwner())return;Object.keys(CHARTS).forEach(k=>drawChart(id,k,-1));}
function drawChart(id,kind,hover){
  const C=CHARTS[kind],cv=document.getElementById(_cid(id,kind));if(!cv)return;
  const range=chartRange[kind],pts=(C.local?localPts(kind):((_rangeData[id+'|'+range]||{}).pts||[])).filter(p=>p&&typeof p.ts==='number');
  const dpr=window.devicePixelRatio||1,W=cv.offsetWidth||600,H=Math.round(cv.getBoundingClientRect().height)||C.h;
  if(cv.width!==W*dpr||cv.height!==H*dpr){cv.width=W*dpr;cv.height=H*dpr;}
  const ctx=cv.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
  const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
  const cBg=css('--bg')||'#f0f2f5',cBorder=css('--border')||'#e3e8ef',cDim=css('--text-dim')||'#94a3b8',cSurface=css('--surface')||'#fff';
  ctx.fillStyle=cBg;ctx.fillRect(0,0,W,H);
  ctx.font='11px DM Mono,monospace';ctx.textAlign='center';
  if(pts.length<2){ctx.fillStyle=cDim;ctx.fillText(t(pts.length?'accumulating':'noDataChart'),W/2,H/2);cv._pts=[];return;}
  const N=pts.length,PL=C.pl||44,PR=10,PT=8,PB=18,W2=W-PL-PR,H2=H-PT-PB;
  const vals=[];pts.forEach(p=>C.series.forEach(x=>{const v=Number(p[x.k]);if(p[x.k]!=null&&isFinite(v))vals.push(v);}));
  if(!vals.length){ctx.fillStyle=cDim;ctx.fillText(t('noDataChart'),W/2,H/2);cv._pts=[];return;}
  let lo=C.min!=null?C.min:0,hi=C.max?C.max:Math.max(...vals,1)*1.15;
  const rg=hi-lo||1,xOf=i=>PL+(i/(N-1))*W2,yOf=v=>PT+H2-((Math.min(hi,Math.max(lo,v))-lo)/rg)*H2;
  ctx.strokeStyle=cBorder;ctx.lineWidth=.5;ctx.fillStyle=cDim;ctx.font='9px DM Mono,monospace';ctx.textAlign='right';
  for(let i=0;i<=4;i++){const v=lo+rg/4*i,y=yOf(v);ctx.beginPath();ctx.moveTo(PL,y);ctx.lineTo(W-PR,y);ctx.stroke();ctx.fillText(C.axis(v),PL-3,y+3);}
  C.series.forEach((x,si)=>{
    const line=()=>{ctx.beginPath();let pen=false;pts.forEach((p,i)=>{const v=Number(p[x.k]);if(p[x.k]==null||!isFinite(v)){pen=false;return;}pen?ctx.lineTo(xOf(i),yOf(v)):ctx.moveTo(xOf(i),yOf(v));pen=true;});};
    if(si===0&&!C.points){line();ctx.lineTo(xOf(N-1),PT+H2);ctx.lineTo(PL,PT+H2);ctx.closePath();const g=ctx.createLinearGradient(0,PT,0,PT+H2);g.addColorStop(0,x.c+'33');g.addColorStop(1,x.c+'00');ctx.fillStyle=g;ctx.fill();}
    line();ctx.strokeStyle=x.c;ctx.lineWidth=1.8;ctx.stroke();
    if(C.points)pts.forEach((p,i)=>{if(p[x.k]==null)return;ctx.beginPath();ctx.arc(xOf(i),yOf(Number(p[x.k])),2.6,0,2*Math.PI);ctx.fillStyle=x.c;ctx.fill();});
  });
  if(C.down){pts.forEach((p,i)=>{if(p.up===0){ctx.fillStyle='rgba(239,68,68,.25)';const w=Math.max(2,W2/N);ctx.fillRect(xOf(i)-w/2,PT,w,H2);}});}
  ctx.fillStyle=cDim;ctx.font='9px DM Mono,monospace';ctx.textAlign='center';
  const step=Math.max(1,Math.floor(N/5));
  for(let i=0;i<N;i+=step){const d=new Date(pts[i].ts*1000);ctx.fillText(range==='1mo'||range==='all'||C.local?d.toLocaleDateString(_lang==='es'?'es-CL':'en-GB',{day:'2-digit',month:'2-digit'}):PCT.time(d),xOf(i),H-3);}
  if(hover>=0&&hover<N){
    const cx=xOf(hover),p=pts[hover];
    ctx.beginPath();ctx.moveTo(cx,PT);ctx.lineTo(cx,PT+H2);ctx.strokeStyle='rgba(100,116,139,.4)';ctx.lineWidth=1;ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
    C.series.forEach(x=>{if(p[x.k]==null)return;ctx.beginPath();ctx.arc(cx,yOf(Number(p[x.k])),4,0,2*Math.PI);ctx.fillStyle=x.c;ctx.fill();ctx.strokeStyle=cSurface;ctx.lineWidth=1.5;ctx.stroke();});
  }
  cv._pts=pts;cv._geo={PL,W2,N};
  if(!cv._bound){
    cv._bound=true;
    cv.addEventListener('mousemove',e=>{
      const g=cv._geo,ps=cv._pts;if(!g||!ps||!ps.length)return;
      const r=cv.getBoundingClientRect(),x=e.clientX-r.left;
      const i=Math.max(0,Math.min(g.N-1,Math.round((x-g.PL)/g.W2*(g.N-1))));
      drawChart(id,kind,i);
      const tip=document.getElementById(_cid(id,kind)+'-tip');if(!tip)return;
      const p=ps[i],d=new Date(p.ts*1000);
      tip.replaceChildren();
      const hd=document.createElement('div');hd.style.color='var(--text-dim)';hd.textContent=d.toLocaleDateString(_lang==='es'?'es-CL':'en-GB',{day:'2-digit',month:'2-digit'})+' '+PCT.time(d,true);tip.appendChild(hd);
      C.series.forEach(sx=>{const row=document.createElement('div');const dot=document.createElement('span');dot.style.cssText='display:inline-block;width:8px;height:3px;border-radius:2px;margin-right:6px;background:'+sx.c;
        row.appendChild(dot);row.appendChild(document.createTextNode(t(sx.l)+': '+(p[sx.k]==null?'—':sx.f(Number(p[sx.k])))));tip.appendChild(row);});
      tip.classList.add('show');
      const tw=tip.offsetWidth,px=e.clientX-r.left+14;tip.style.left=Math.max(0,Math.min(r.width-tw,px>r.width-tw?e.clientX-r.left-tw-14:px))+'px';tip.style.top='6px';
    });
    cv.addEventListener('mouseleave',()=>{const tip=document.getElementById(_cid(id,kind)+'-tip');if(tip)tip.classList.remove('show');drawChart(id,kind,-1);});
  }
}
window.addEventListener('resize',()=>{const id=chartOwner();if(id!=null)drawCharts(id);});

// ── Utilidades ───────────────────────────────────────────────────────────────
function fmtNum(n){if(n==null||!isFinite(Number(n)))return '—';return Number(n).toLocaleString(_lang==='es'?'es-CL':'en-GB');}
function fmtBps(v){if(v==null||!isFinite(Number(v)))return'—';v=Number(v);const u=['bit/s','Kb/s','Mb/s','Gb/s'];let i=0;while(v>=1000&&i<u.length-1){v/=1000;i++;}return v.toFixed(i>0?1:0)+' '+u[i];}
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
function alertText(a){const f=(LANG[_lang].al||{})[a.type]||(LANG.en.al||{})[a.type];return f?f.replace(/\{0\}/g,a.value==null?'':a.value):a.type;}
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
if (window.cspRegister) cspRegister({ closeModals, confirmDelete, doLogin, logout, openForm, openPause, resumeBlocking, saveServer, setLang, setRange, setTheme, testServer, toggleNav, toggleServer, typeChanged });
