// VPN Monitor — página del módulo (/vpn/). Clientes conectados a Tailscale, OpenVPN y WireGuard.
// EN: VPN Monitor — module page (/vpn/). Clients connected to Tailscale, OpenVPN and WireGuard.
const LANG={
  en:{
  "connecting":"Connecting…",
  "loginTitle":"Sign in",
  "loginSub":"Enter your credentials to continue.",
  "username":"Username",
  "password":"Password",
  "loginBtn":"Sign in",
  "rememberMe":"Remember me",
  "rem1d":"1 day",
  "rem1w":"1 week",
  "rem1m":"1 month",
  "remForever":"Forever",
  "navSection":"Navigation",
  "themeLight":"Light",
  "themeDark":"Dark",
  "fieldType":"Type",
  "fieldName":"Name",
  "fieldPort":"Port",
  "fieldTimeout":"Timeout (s)",
  "fieldApiKey":"API key",
  "secretKept":"Saved. Leave empty to keep it.",
  "cancel":"Cancel",
  "test":"Test",
  "save":"Save",
  "delete":"Delete",
  "edit":"Edit",
  "testFillAll":"Fill in the name, host and credentials.",
  "saved":"Saved",
  "permReadonly":"Read-only",
  "permExecute":"Execute",
  "permAdmin":"Administrator",
  "online":"Online",
  "offline":"Unreachable",
  "sessionExpired":"Session expired",
  "status":"Status",
  "summary":"VPN Summary",
  "connectingMsg":"Reading the VPN server…",
  "navVpn":"VPN servers",
  "addVpn":"Add VPN",
  "addVpnTitle":"Add VPN",
  "editVpnTitle":"Edit VPN",
  "deleteVpn":"Delete VPN",
  "statServers":"Servers reachable",
  "statOnline":"Connected clients",
  "statRx":"Received (now)",
  "statTx":"Sent (now)",
  "noVpn":"No VPN configured",
  "noVpnHint":"Add a Tailscale, OpenVPN or WireGuard server to get started.",
  "hint_tailscale":"Create a read-only API key in the Tailscale admin console (Settings → Keys). Tailnet: \"-\" uses the key's own tailnet.",
  "hint_openvpn":"LabTower reads the OpenVPN status file over SSH (read-only). The server needs \"status <file> 2\" (or 3) in its configuration.",
  "hint_wireguard":"LabTower runs \"wg show all dump\" over SSH (read-only). Use root or a user that may run it with sudo.",
  "fieldTailnet":"Tailnet",
  "tailnetHint":"\"-\" = the tailnet of the API key, or your tailnet name (example.com).",
  "fieldSshUser":"SSH user",
  "fieldSudo":"Run with sudo (needs passwordless sudo for that command)",
  "sudoHint":"Needed when the file or command is root-only (for example Synology). Add to sudoers on the VPN server: <user> ALL=(root) NOPASSWD: /bin/cat <status file>  (or wg show all dump).",
  "fieldStatusPath":"Status file",
  "statusPathHint":"Default on Debian: /run/openvpn-server/status-server.log",
  "fieldAliases":"Peer names",
  "aliasesHint":"One per line: <public key> <name>. WireGuard has no users; this is how peers get a name.",
  "sshKeyTitle":"SSH key of LabTower",
  "sshKeyHint":"Add this public key to ~/.ssh/authorized_keys on the VPN server. The host key is accepted the first time and enforced afterwards.",
  "sshKeyBtn":"Create / show key",
  "sshRestrict":"Recommended authorized_keys line (restricts the key to this single read):",
  "unreachable":"Unreachable",
  "colServer":"Server",
  "colType":"Type",
  "colClients":"Connected",
  "colTraffic":"Traffic",
  "colTrend":"Trend",
  "colClient":"Client",
  "colUser":"User",
  "colIface":"Interface",
  "colIp":"Address",
  "colVirtual":"VPN IP",
  "colSince":"Connected for",
  "colLast":"Last seen",
  "connectedNow":"Connected",
  "noClients":"No clients known yet.",
  "clients":"Clients",
  "sessions":"Recent sessions",
  "noSessions":"No finished sessions yet.",
  "updateAvail":"update",
  "testOk":(a,b)=>`OK — ${a} connected of ${b} known`,
  "agoFmt":d=>`${d} ago`,
  "deleteConfirm":n=>`Delete “${n}”? Its recent sessions are removed too.`,
  "added":n=>`“${n}” added`,
  "deleted":n=>`“${n}” deleted`
  },
  es:{
  "connecting":"Conectando…",
  "loginTitle":"Iniciar sesión",
  "loginSub":"Ingresa tus credenciales para continuar.",
  "username":"Usuario",
  "password":"Contraseña",
  "loginBtn":"Entrar",
  "rememberMe":"Recordarme",
  "rem1d":"1 día",
  "rem1w":"1 semana",
  "rem1m":"1 mes",
  "remForever":"Siempre",
  "navSection":"Navegación",
  "themeLight":"Claro",
  "themeDark":"Oscuro",
  "fieldType":"Tipo",
  "fieldName":"Nombre",
  "fieldPort":"Puerto",
  "fieldTimeout":"Tiempo de espera (s)",
  "fieldApiKey":"Clave de API",
  "secretKept":"Guardada. Déjala vacía para conservarla.",
  "cancel":"Cancelar",
  "test":"Probar",
  "save":"Guardar",
  "delete":"Eliminar",
  "edit":"Editar",
  "testFillAll":"Completa nombre, host y credenciales.",
  "saved":"Guardado",
  "permReadonly":"Solo lectura",
  "permExecute":"Ejecutar",
  "permAdmin":"Administrador",
  "online":"En línea",
  "offline":"Sin conexión",
  "sessionExpired":"Sesión vencida",
  "status":"Estado",
  "summary":"Resumen de VPN",
  "connectingMsg":"Leyendo el servidor VPN…",
  "navVpn":"Servidores VPN",
  "addVpn":"Agregar VPN",
  "addVpnTitle":"Agregar VPN",
  "editVpnTitle":"Editar VPN",
  "deleteVpn":"Eliminar VPN",
  "statServers":"Servidores alcanzables",
  "statOnline":"Clientes conectados",
  "statRx":"Recibido (ahora)",
  "statTx":"Enviado (ahora)",
  "noVpn":"Sin VPN configuradas",
  "noVpnHint":"Agrega un servidor Tailscale, OpenVPN o WireGuard para empezar.",
  "hint_tailscale":"Crea una clave de API de solo lectura en la consola de Tailscale (Settings → Keys). Tailnet: «-» usa la tailnet de la propia clave.",
  "hint_openvpn":"LabTower lee el archivo de estado de OpenVPN por SSH (solo lectura). El servidor necesita «status <archivo> 2» (o 3) en su configuración.",
  "hint_wireguard":"LabTower ejecuta «wg show all dump» por SSH (solo lectura). Usa root o un usuario que pueda ejecutarlo con sudo.",
  "fieldTailnet":"Tailnet",
  "tailnetHint":"«-» = la tailnet de la clave de API, o el nombre de tu tailnet (ejemplo.com).",
  "fieldSshUser":"Usuario SSH",
  "fieldSudo":"Ejecutar con sudo (requiere sudo sin contraseña para ese comando)",
  "sudoHint":"Se necesita cuando el archivo o comando es solo de root (por ejemplo Synology). Agrega en sudoers del servidor VPN: <usuario> ALL=(root) NOPASSWD: /bin/cat <archivo de estado>  (o wg show all dump).",
  "fieldStatusPath":"Archivo de estado",
  "statusPathHint":"Por defecto en Debian: /run/openvpn-server/status-server.log",
  "fieldAliases":"Nombres de peers",
  "aliasesHint":"Uno por línea: <clave pública> <nombre>. WireGuard no tiene usuarios; así se les pone nombre a los peers.",
  "sshKeyTitle":"Llave SSH de LabTower",
  "sshKeyHint":"Agrega esta clave pública a ~/.ssh/authorized_keys del servidor VPN. La huella del servidor se acepta la primera vez y después se exige.",
  "sshKeyBtn":"Crear / mostrar llave",
  "sshRestrict":"Línea recomendada para authorized_keys (limita la llave a esta única lectura):",
  "unreachable":"Sin conexión",
  "colServer":"Servidor",
  "colType":"Tipo",
  "colClients":"Conectados",
  "colTraffic":"Tráfico",
  "colTrend":"Tendencia",
  "colClient":"Cliente",
  "colUser":"Usuario",
  "colIface":"Interfaz",
  "colIp":"Dirección",
  "colVirtual":"IP VPN",
  "colSince":"Conectado hace",
  "colLast":"Visto",
  "connectedNow":"Conectado",
  "noClients":"Aún no hay clientes conocidos.",
  "clients":"Clientes",
  "sessions":"Sesiones recientes",
  "noSessions":"Aún no hay sesiones terminadas.",
  "updateAvail":"actualizar",
  "testOk":(a,b)=>`OK — ${a} conectados de ${b} conocidos`,
  "agoFmt":d=>`hace ${d}`,
  "deleteConfirm":n=>`¿Eliminar «${n}»? Sus sesiones recientes también se borran.`,
  "added":n=>`«${n}» agregado`,
  "deleted":n=>`«${n}» eliminado`
  }
};
let _lang=localStorage.getItem('pi-lang')||'en';
var _i18nReady=false;
// Traducción: busca la clave en el idioma activo (admite textos con función para incluir valores).
// EN: Translation: looks the key up in the active language (supports function texts that take values).
function t(k,...args){const v=(LANG[_lang]||LANG.en)[k]??(LANG.en)[k]??k;return typeof v==='function'?v(...args):v;}
function setLang(l){
  _lang=l;localStorage.setItem('pi-lang',l);document.documentElement.lang=l;
  document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=t(el.getAttribute('data-i18n')));
  ['en','es'].forEach(x=>document.getElementById('lang-'+x)?.classList.toggle('active',x===l));
  if(_i18nReady&&typeof renderAll==='function')renderAll();
  const ov=document.getElementById('add-overlay');if(ov&&ov.classList.contains('show')&&typeof typeChanged==='function')typeChanged();
}
(()=>setLang(_lang))();

let ME=null, items=[], activeId=null, pollTimer=null;
const POLL=5000;                 // el servidor lee cada 20 s con alguien mirando; la página pide cada 5 s mientras se ve
let _histTs=0, _histCache={};    // el historial es grande y cambia cada 30 s: se pide cada 30 s

// ── Tema ─────────────────────────────────────────────────────────────────────
function setTheme(t){localStorage.setItem('pi-theme',t);applyTheme(t);['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));}
function applyTheme(t){const p=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;document.documentElement.setAttribute('data-theme',p==='dark'?'dark':'light');}
(()=>{const t=localStorage.getItem('pi-theme')||'dark';applyTheme(t);window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if((localStorage.getItem('pi-theme')||'dark')==='system')applyTheme('system');});setTimeout(()=>{['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));},0);})();

// ── Menú lateral común (reordenable; el orden se guarda en el navegador, clave pi-nav-order) ──
function canAdmin(){return ME&&ME.permissions?.vpn==='admin';}
const _NAV_ITEMS=[
  {id:'overview', href:'/overview/', get label(){return _lang==='es'?'Resumen':'Overview'}, svg:'<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>'},
  {id:'nut',  href:'/nut/',   label:'UPS Monitor', svg:'<path d="M5 9V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v4"/><rect x="3" y="9" width="18" height="11" rx="2"/><line x1="12" y1="13" x2="12" y2="16"/>'},
  {id:'net',  href:'/net/',   label:'Net Monitor', svg:'<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>'},
  {id:'pve',  href:'/pve/',   label:'Proxmox',     svg:'<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>'},
  {id:'nas',  href:'/nas/',   label:'NAS Monitor', svg:'<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="7" y1="9" x2="17" y2="9"/><line x1="7" y1="14" x2="17" y2="14"/><line x1="16" y1="18" x2="16.01" y2="18"/>'},
  {id:'dns',  href:'/dns/',   label:'DNS Monitor', svg:'<circle cx="12" cy="12" r="9"/><line x1="3" y1="12" x2="21" y2="12"/><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z"/>'},
  {id:'wan',  href:'/wan/',   label:'WAN Monitor', svg:'<path d="M5 12.55a11 11 0 0 1 14 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/>'},
  {id:'vpn',  href:'/vpn/',   label:'VPN Monitor', svg:'<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>'},
  {id:'wol',  href:'/wol/',   label:'WOL Console', svg:'<polygon points="13,2 3,14 12,14 11,22 21,10 12,10"/>'},
  {id:'admin',href:'/admin/', label:'Admin Panel', svg:'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',adminOnly:true},
];
const _NAV_SELF='vpn';
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
  const k={readonly:'permReadonly',execute:'permExecute',admin:'permAdmin'}[ME.permissions?.vpn];
  document.getElementById('me-role').textContent=k?t(k):'—';
  renderNav();
  document.getElementById('btn-add-vpn').style.display=canAdmin()?'':'none';
}
async function logout(){await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.reload();}

// ── Datos ────────────────────────────────────────────────────────────────────
// Descarga los servidores VPN con su última lectura (el servidor lee cada 20 s si alguien mira la página).
// EN: Download the VPN servers with their last reading (the server polls every 20 s while someone looks at the page).
async function initApp(){
  updateClock();setInterval(updateClock,1000);
  await fetchAll();
  pollTimer=setInterval(()=>{if(!document.hidden)fetchAll();},POLL);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)fetchAll();});
}
async function fetchAll(){
  try{
    const wantHist=Date.now()-_histTs>=30000;
    const r=await fetch('api/vpn'+(wantHist?'':'?hist=0'));
    if(r.status===401){location.reload();return;}
    const d=await r.json();
    items=d.vpn||[];
    items.forEach(n=>{if(wantHist)_histCache[n.id]=n.history; else n.history=_histCache[n.id]||[];});
    if(wantHist)_histTs=Date.now();
    if(activeId!==''&&!items.some(n=>n.id===activeId))activeId=items[0]?.id||null;   // '' = el usuario cerró todas las filas
    renderAll();
  }catch(e){console.error(e);}
}
function renderAll(){renderSidebar();renderSummary();renderDashboard();updateGlobalStats();}
function selectVpn(id){activeId=id;renderAll();}
function toggleVpn(id){activeId=activeId===id?'':id;renderAll();}

function lvOf(n){const s=n.snap;if(!s?.ts)return s?.error?'err':'loading';if(s.error)return 'err';return 'ok';}
function typeName(ty){return {tailscale:'Tailscale',openvpn:'OpenVPN',wireguard:'WireGuard'}[ty]||ty;}
function renderSidebar(){
  const list=document.getElementById('vpn-list');list.innerHTML='';
  items.forEach(n=>{
    const isActive=n.id===activeId,d=n.snap?.data;
    const div=document.createElement('div');
    div.className='cluster-nav'+(isActive?' active':'');
    div.onclick=()=>selectVpn(n.id);
    const sub=typeName(n.type)+(d&&d.total!=null?' · '+d.online+'/'+d.total:'');
    div.innerHTML=`<span class="cluster-dot ${lvOf(n)}"></span>
      <div style="flex:1;min-width:0"><div class="cluster-nav-name ${isActive?'act':''}">${esc(n.name)}</div>
      <div class="cluster-nav-host">${esc(sub)}</div></div>`;
    list.appendChild(div);
  });
}
function updateGlobalStats(){
  let on=0,cl=0,rx=0,tx=0,has=false;
  items.forEach(n=>{const d=n.snap?.data;if(!d||n.snap.error||!d.clients)return;on++;cl+=d.online||0;if(d.rx!=null){rx+=d.rx;has=true;}if(d.tx!=null)tx+=d.tx;});
  document.getElementById('st-srv').textContent=items.length?`${on}/${items.length}`:'—';
  document.getElementById('st-on').textContent=items.length?cl:'—';
  document.getElementById('st-rx').textContent=has?fmtBytes(rx):'—';
  document.getElementById('st-tx').textContent=has?fmtBytes(tx):'—';
}

function pill(lv,text){return `<span class="pill ${esc(lv)}">${esc(text)}</span>`;}
function kv(k,v){return `<div class="kv"><span class="k">${esc(k)}</span><span class="v">${v}</span></div>`;}
function spark(hist){
  const pts=(hist||[]).filter(p=>Array.isArray(p));if(pts.length<3)return '<span class="sum-sub">—</span>';
  const W=90,H=24,t0=pts[0][0],t1=pts[pts.length-1][0]||t0+1,mx=Math.max(1,...pts.map(p=>p[1]));
  const d=pts.map((p,i)=>(i?'L':'M')+(((p[0]-t0)/Math.max(1,t1-t0))*W).toFixed(1)+' '+(H-1-(p[1]/mx)*(H-2)).toFixed(1)).join(' ');
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}"><path d="${d}" fill="none" stroke="#6366f1" stroke-width="1.5"/></svg>`;
}
function renderSummary(){
  const box=document.getElementById('vpn-summary');if(!box)return;
  if(!items.length){box.innerHTML='';return;}
  const rows=items.map(n=>{
    const sn=n.snap||{},d=sn.data&&sn.data.clients?sn.data:null,lv=lvOf(n),open=n.id===activeId;
    const state=lv==='loading'?pill('off','…'):lv==='err'?pill('crit',t('unreachable')):pill('ok',t('online'));
    const sub=n.type==='tailscale'?(n.tailnet==='-'?'tailnet':n.tailnet):n.host+':'+n.port;
    return `<tr class="nas-row${open?' expanded':''}" data-on-click="toggleVpn" data-on-click-args="${jsargs([n.id])}">
      <td><span class="cluster-dot ${lv}"></span></td>
      <td><div class="sum-name">${esc(n.name)}</div><div class="sum-sub">${esc(sub)}</div></td>
      <td><span class="vpn-badge">${esc(typeName(n.type))}</span></td>
      <td>${state}</td>
      <td><b>${d?esc(d.online):'—'}</b>${d?' <span class="sum-sub">/ '+esc(d.total)+'</span>':''}</td>
      <td class="c-temp">${d&&d.rx!=null?'↓ '+esc(fmtBytes(d.rx))+' · ↑ '+esc(fmtBytes(d.tx)):'—'}</td>
      <td class="c-spark">${spark(n.history)}</td>
      <td><span class="expand-arrow ${open?'open':''}">▶</span></td></tr>
    <tr class="detail-row${open?' show':''}"><td colspan="8" class="detail-cell"><div class="nas-detail">${open?buildDetail(n):''}</div></td></tr>`;
  }).join('');
  box.innerHTML=`<div class="card"><div class="card-hd"><span class="card-title">${esc(t('summary'))}</span><span class="card-meta">${esc(items.length)}</span></div>
    <div class="tbl-wrap"><table class="nas-table"><thead><tr><th style="width:24px"></th><th>${esc(t('colServer'))}</th><th>${esc(t('colType'))}</th><th>${esc(t('status'))}</th><th>${esc(t('colClients'))}</th><th class="c-temp">${esc(t('colTraffic'))}</th><th class="c-spark">${esc(t('colTrend'))}</th><th style="width:24px"></th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
  fitDetail();
}
function fitDetail(){const w=document.querySelector('#vpn-summary .tbl-wrap');if(w)w.style.setProperty('--wrapw',w.clientWidth+'px');}
window.addEventListener('resize',fitDetail);
function renderDashboard(){
  const main=document.getElementById('main-content');
  const n=items.find(x=>x.id===activeId);
  main.innerHTML=items.length?'':'<div class="state-msg"><strong>'+esc(t('noVpn'))+'</strong>'+esc(t('noVpnHint'))+'</div>';
  const sub=document.getElementById('tb-sub');sub.textContent='';
  document.getElementById('tb-title').textContent=n?n.name:'VPN Monitor';
  if(n)sub.textContent=typeName(n.type)+(n.host?' · '+n.host:'');
}

// ── Detalle de un servidor: clientes y sesiones recientes ────────────────────
function fmtDur(s){s=Math.max(0,Math.round(Number(s)||0));const d=Math.floor(s/86400),h=Math.floor((s%86400)/3600),m=Math.floor((s%3600)/60);return d>0?d+'d '+h+'h':h>0?h+'h '+m+'m':m>0?m+'m':s+'s';}
function ago(ts){return ts?t('agoFmt',fmtDur(Date.now()/1000-ts)):'—';}
function buildDetail(n){
  const sn=n.snap||{},d=sn.data;let h='';
  if(sn.error)h+=`<div class="conn-err">${esc(sn.error)}</div>`;
  if(!d||!d.clients){return h||`<div class="nas-empty">${esc(t('connecting'))}</div>`;}
  const now=Date.now()/1000,cl=[...d.clients].sort((a,b)=>(b.online-a.online)||String(a.name).localeCompare(String(b.name)));
  const ts=n.type==='tailscale',wg=n.type==='wireguard';
  const th=[t('colClient'),ts?t('colUser'):wg?t('colIface'):'',t('colIp'),ts?'':t('colVirtual'),t('colSince'),ts?'':t('colTraffic'),t('colLast')].map(x=>`<th>${esc(x)}</th>`).join('');
  const body=cl.map(c=>`<tr class="vpn-cl" style="cursor:default"><td><i style="display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:${c.online?'var(--green)':'var(--text-dim)'}"></i><b>${esc(c.name)}</b>${c.tags&&c.tags.length?' <span class="sum-sub">'+esc(c.tags.join(' '))+'</span>':''}${c.update?' <span class="vpn-badge">'+esc(t('updateAvail'))+'</span>':''}</td>
    <td class="dim">${esc(ts?(c.user||'')+(c.os?' · '+c.os:''):wg?(c.iface||''):'')}</td>
    <td>${esc(c.ip||'—')}</td><td>${ts?'':esc(c.virtual||'—')}</td>
    <td>${c.online&&c.since?esc(fmtDur(now-c.since)):c.online?'…':'—'}</td>
    <td>${ts?'':c.rx!=null?'↓ '+esc(fmtBytes(c.rx))+' · ↑ '+esc(fmtBytes(c.tx)):'—'}</td>
    <td class="dim">${c.online?esc(t('connectedNow')):esc(ago(c.last))}</td></tr>`).join('');
  h+=`<div class="card"><div class="card-hd"><span class="card-title">${esc(t('clients'))}</span><span class="card-meta">${esc(d.online)} / ${esc(d.total)}</span></div>
    ${cl.length?`<div class="tbl-wrap"><table class="nas-table"><thead><tr>${th}</tr></thead><tbody>${body}</tbody></table></div>`:`<div class="nas-empty">${esc(t('noClients'))}</div>`}</div>`;
  const lg=(d.log||[]).slice(0,15);
  h+=`<div class="card" style="margin-top:12px"><div class="card-hd"><span class="card-title">${esc(t('sessions'))}</span></div><div style="padding:6px 14px">${
    lg.length?lg.map(x=>`<div class="vpn-log"><b>${esc(x.name)}</b><span>${esc(PCT.time(new Date(x.start*1000),false))} → ${esc(PCT.time(new Date(x.end*1000),false))}</span><span>${esc(fmtDur(x.end-x.start))}</span></div>`).join(''):`<div class="nas-empty">${esc(t('noSessions'))}</div>`}</div></div>`;
  if(canAdmin())h+=`<div class="nas-tools" style="margin-top:12px"><button class="btn-secondary" data-on-click="openVpnForm" data-on-click-args="${jsargs([n.id])}">${esc(t('edit'))}</button> <button class="btn-mok" data-on-click="confirmDelete" data-on-click-args="${jsargs([n.id,n.name])}">${esc(t('delete'))}</button></div>`;
  return h;
}

// ── Alta, edición, prueba y borrado (solo administradores) ────────────────────
let editingId=null;
const $=id=>document.getElementById(id);
function curType(){return $('f-type').value;}
function typeChanged(){
  const ty=curType(),ts=ty==='tailscale';
  $('ts-box').style.display=ts?'flex':'none';$('ssh-box').style.display=ts?'none':'flex';
  $('ovpn-box').style.display=ty==='openvpn'?'':'none';$('wg-box').style.display=ty==='wireguard'?'':'none';
  $('add-hint').textContent=t('hint_'+ty);
  $('ssh-restrict').textContent=ts?'':t('sshRestrict')+'\n'+(ty==='wireguard'?'command="wg show all dump"':'command="cat '+($('f-status-path').value||'/run/openvpn-server/status-server.log')+'"')+',no-pty,no-port-forwarding,no-agent-forwarding,no-X11-forwarding '+($('ssh-pub').value.split(' ').slice(0,2).join(' ')||'<key>');
}
async function openVpnForm(id){
  editingId=typeof id==='string'?id:null;
  const n=editingId?items.find(x=>x.id===editingId):null,ty=n?n.type:'tailscale';
  $('vpn-form-title').textContent=t(n?'editVpnTitle':'addVpnTitle');
  $('f-type').value=ty;$('f-type').disabled=!!n;
  $('f-name').value=n?n.name:'';$('f-timeout').value=n?n.timeout:10;
  $('f-tailnet').value=n&&n.tailnet?n.tailnet:'-';$('f-api-key').value='';$('h-api-key').textContent=n&&n.has_api_key?t('secretKept'):'';
  $('f-host').value=n&&n.host?n.host:'';$('f-ssh-user').value=n&&n.ssh_user?n.ssh_user:'';$('f-port').value=n&&n.port?n.port:22;$('f-sudo').checked=!!(n&&n.use_sudo);
  $('f-status-path').value=n&&n.status_path?n.status_path:'/run/openvpn-server/status-server.log';
  $('f-aliases').value=n&&n.aliases_text?n.aliases_text:'';
  $('test-result').className='test-result';
  try{const r=await fetch('api/ssh-key');if(r.ok)$('ssh-pub').value=(await r.json()).public_key||'';}catch(e){}
  typeChanged();
  $('add-overlay').classList.add('show');$('f-name').focus();
}
function formBody(){
  const ty=curType(),b={type:ty,name:$('f-name').value.trim(),timeout:parseInt($('f-timeout').value)||10};
  if(ty==='tailscale'){b.tailnet=$('f-tailnet').value.trim()||'-';b.api_key=$('f-api-key').value.trim();}
  else{
    Object.assign(b,{host:$('f-host').value.trim(),ssh_user:$('f-ssh-user').value.trim(),port:parseInt($('f-port').value)||22,use_sudo:$('f-sudo').checked});
    if(ty==='openvpn')b.status_path=$('f-status-path').value.trim();else b.aliases=$('f-aliases').value;
  }
  if(editingId)b.id=editingId;
  return b;
}
async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json().catch(()=>({}));return {ok:r.ok,status:r.status,d};}
async function makeSshKey(){
  const btn=$('btn-ssh');btn.disabled=true;
  try{const {ok,d}=await post('api/ssh-key',{});if(!ok)throw new Error(d.error||'Error');$('ssh-pub').value=d.public_key||'';typeChanged();}
  catch(e){toast(e.message,true);}
  finally{btn.disabled=false;}
}
async function testVpn(){
  const btn=$('btn-test'),res=$('test-result'),b=formBody();
  if(!b.name||(b.type!=='tailscale'&&!b.host)){res.className='test-result fail show';res.textContent='✕ '+t('testFillAll');return;}
  btn.innerHTML='<span class="spin">⟳</span>';btn.disabled=true;
  try{
    const {d}=await post('api/test',b);
    if(d.ok){res.className='test-result ok show';res.textContent=t('testOk',d.online,d.total);}
    else{res.className='test-result fail show';res.textContent='✕ '+(d.error||'Error');}
  }catch(e){res.className='test-result fail show';res.textContent='✕ '+e.message;}
  finally{btn.disabled=false;btn.textContent=t('test');}
}
async function saveVpn(){
  const btn=$('btn-save'),b=formBody();
  if(!b.name||(b.type!=='tailscale'&&!b.host)){toast(t('testFillAll'),true);return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const {ok,d}=await post(editingId?'api/vpn/'+editingId:'api/vpn',b);
    if(!ok)throw new Error(d.error||'Error');
    toast(editingId?t('saved'):t('added',b.name));closeModals();_histTs=0;await fetchAll();if(!editingId)selectVpn(d.vpn.id);
  }catch(e){toast(e.message,true);}
  finally{btn.disabled=false;btn.textContent=t('save');}
}
function confirmDelete(id,name){
  $('del-msg').textContent=t('deleteConfirm',name);
  $('del-btn').onclick=async()=>{
    closeModals();
    try{const r=await fetch('api/vpn/'+id,{method:'DELETE'});if(!r.ok)throw new Error((await r.json().catch(()=>({}))).error||'Error');toast(t('deleted',name));await fetchAll();}
    catch(e){toast(e.message,true);}
  };
  $('del-overlay').classList.add('show');
}

// ── Utilidades ───────────────────────────────────────────────────────────────
function fmtBytes(b){b=Number(b);if(!b)return'0 B';const u=['B','KB','MB','GB','TB','PB'];let i=0;while(b>=1024&&i<u.length-1){b/=1024;i++;}return b.toFixed(i>0?1:0)+' '+u[i];}
// Escapa HTML antes de insertar texto de la red o de usuarios en la página: evita inyección de código (XSS).
// EN: Escape HTML before inserting network or user text into the page: prevents code injection (XSS).
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
function jsargs(a){return esc(JSON.stringify(a));}
function updateClock(){const el=document.getElementById('clock');if(el)el.textContent=PCT.time(new Date(),true);}
function closeModals(){document.querySelectorAll('.overlay').forEach(o=>o.classList.remove('show'));}
let _tt;
function toast(msg,isErr=false){const el=document.getElementById('toast');el.textContent=msg;el.style.background=isErr?'var(--red)':'var(--text)';void el.offsetWidth;el.classList.add('show');clearTimeout(_tt);_tt=setTimeout(()=>el.classList.remove('show'),3200);}

document.querySelectorAll('.overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)closeModals();}));
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModals();});

_i18nReady=true;
(async()=>{
  const ok=await checkSession();
  if(ok){applyPermissions();await initApp();const ls=document.getElementById('login-screen');ls.style.opacity='0';setTimeout(()=>ls.style.display='none',150);}else{document.getElementById('login-screen').style.display='flex';}
})();

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

// Funciones que el HTML puede invocar con data-on-* (lista cerrada; ver csp-bind.js).
// EN: Functions the HTML may call through data-on-* (closed list; see csp-bind.js).
if (window.cspRegister) cspRegister({ closeModals, confirmDelete, doLogin, logout, makeSshKey, openVpnForm, saveVpn, setLang, setTheme, testVpn, toggleNav, toggleVpn, typeChanged });
