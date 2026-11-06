// Uptime Monitor — página del módulo (/uptime/). Disponibilidad de servicios por HTTP(S), TCP y DNS.
// EN: Uptime Monitor — module page (/uptime/). Service availability over HTTP(S), TCP and DNS.
const LANG={
  en:{
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
  "navMon":"Monitors",
  "addMon":"Add monitor",
  "addMonTitle":"Add monitor",
  "editMonTitle":"Edit monitor",
  "deleteMon":"Delete monitor",
  "statUp":"Services up",
  "statDown":"Down",
  "statPct":"Uptime 24 h (average)",
  "statCert":"Certificates expiring",
  "noMon":"No monitors yet",
  "noMonHint":"Add an HTTP(S), TCP or DNS monitor to get started.",
  "summary":"Monitors",
  "fieldType":"Type",
  "fieldName":"Name",
  "fieldPort":"Port",
  "fieldExpect":"Expected status codes",
  "fieldKeyword":"Keyword (optional)",
  "fieldInsecure":"Do not verify the certificate",
  "insecureHint":"For self-signed certificates on the LAN (Proxmox, NAS). The expiry date is still checked.",
  "fieldCertDays":"Warn days before expiry",
  "fieldQname":"Name to resolve",
  "fieldRtype":"Record",
  "fieldServer":"DNS server (optional)",
  "serverHint":"Empty = the resolver of this server.",
  "fieldExpectIp":"Expected IP (optional)",
  "fieldInterval":"Interval (s)",
  "fieldTimeout":"Timeout (s)",
  "fieldDownAfter":"Failures before down",
  "downAfterHint":"Failed checks in a row before the monitor is marked down (3 by default). Until then it shows Pending.",
  "hint_http":"GET to the URL. Up when the status code is in the list (example: 200-399 or 200,301) and the page contains the keyword, if one is set (case-insensitive). Redirects are not followed.",
  "hint_tcp":"Opens a TCP connection to the port (SSH, SMB, MQTT, a database…). Up when the connection is accepted.",
  "hint_dns":"Resolves the name. Up when it returns a record and, if an IP is set, that IP is among the answers.",
  "cancel":"Cancel",
  "test":"Test",
  "save":"Save",
  "delete":"Delete",
  "edit":"Edit",
  "checkNow":"Check now",
  "checking":"Checking…",
  "saved":"Saved",
  "fillAll":"Fill in the name and the target.",
  "permReadonly":"Read-only",
  "permExecute":"Execute",
  "permAdmin":"Administrator",
  "colMon":"Monitor",
  "colType":"Type",
  "status":"Status",
  "colBeats":"Last checks",
  "col24":"24 h",
  "col30":"30 d",
  "colMs":"Response",
  "colCert":"Certificate",
  "st_up":"Up",
  "st_down":"Down",
  "st_pending":"Pending",
  "st_none":"Waiting…",
  "certOk":d=>`${d} d`,
  "certWarn":d=>`expires in ${d} d`,
  "certExpired":"expired",
  "uptime":"Uptime",
  "u24":"Last 24 h",
  "u7":"Last 7 days",
  "u30":"Last 30 days",
  "avgMs":"Average response 24 h",
  "lastCheck":"Last check",
  "every":s=>`every ${s} s`,
  "sinceFor":"Current state for",
  "httpCode":"HTTP code",
  "certExp":"Certificate expires",
  "latency":"Response time",
  "sMs":"Response",
  "sPct":"Uptime",
  "noData":"No data yet.",
  "testOk":(ms,x)=>`OK — ${ms} ms${x?' · '+x:''}`,
  "agoFmt":d=>`${d} ago`,
  "deleteConfirm":n=>`Delete “${n}”? Its history is removed too.`,
  "added":n=>`“${n}” added`,
  "deleted":n=>`“${n}” deleted`,
  "sessionExpired":"Session expired"
  },
  es:{
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
  "navMon":"Monitores",
  "addMon":"Agregar monitor",
  "addMonTitle":"Agregar monitor",
  "editMonTitle":"Editar monitor",
  "deleteMon":"Eliminar monitor",
  "statUp":"Servicios arriba",
  "statDown":"Caídos",
  "statPct":"Disponibilidad 24 h (promedio)",
  "statCert":"Certificados por vencer",
  "noMon":"Aún no hay monitores",
  "noMonHint":"Agrega un monitor HTTP(S), TCP o DNS para empezar.",
  "summary":"Monitores",
  "fieldType":"Tipo",
  "fieldName":"Nombre",
  "fieldPort":"Puerto",
  "fieldExpect":"Códigos de respuesta esperados",
  "fieldKeyword":"Palabra clave (opcional)",
  "fieldInsecure":"No verificar el certificado",
  "insecureHint":"Para certificados autofirmados en la LAN (Proxmox, NAS). Igual se revisa la fecha de vencimiento.",
  "fieldCertDays":"Avisar días antes de vencer",
  "fieldQname":"Nombre a resolver",
  "fieldRtype":"Registro",
  "fieldServer":"Servidor DNS (opcional)",
  "serverHint":"Vacío = el resolvedor de este servidor.",
  "fieldExpectIp":"IP esperada (opcional)",
  "fieldInterval":"Intervalo (s)",
  "fieldTimeout":"Tiempo de espera (s)",
  "fieldDownAfter":"Fallos para marcar caído",
  "downAfterHint":"Revisiones fallidas seguidas antes de marcar el monitor como caído (3 por defecto). Mientras tanto queda Pendiente.",
  "hint_http":"GET a la URL. Arriba si el código de respuesta está en la lista (ejemplo: 200-399 o 200,301) y la página contiene la palabra clave, si se indica (sin distinguir mayúsculas). No se siguen redirecciones.",
  "hint_tcp":"Abre una conexión TCP al puerto (SSH, SMB, MQTT, una base de datos…). Arriba si la conexión se acepta.",
  "hint_dns":"Resuelve el nombre. Arriba si devuelve un registro y, si se indica una IP, esa IP está entre las respuestas.",
  "cancel":"Cancelar",
  "test":"Probar",
  "save":"Guardar",
  "delete":"Eliminar",
  "edit":"Editar",
  "checkNow":"Revisar ahora",
  "checking":"Revisando…",
  "saved":"Guardado",
  "fillAll":"Completa el nombre y el destino.",
  "permReadonly":"Solo lectura",
  "permExecute":"Ejecutar",
  "permAdmin":"Administrador",
  "colMon":"Monitor",
  "colType":"Tipo",
  "status":"Estado",
  "colBeats":"Últimas revisiones",
  "col24":"24 h",
  "col30":"30 d",
  "colMs":"Respuesta",
  "colCert":"Certificado",
  "st_up":"Arriba",
  "st_down":"Caído",
  "st_pending":"Pendiente",
  "st_none":"Esperando…",
  "certOk":d=>`${d} d`,
  "certWarn":d=>`vence en ${d} d`,
  "certExpired":"vencido",
  "uptime":"Disponibilidad",
  "u24":"Últimas 24 h",
  "u7":"Últimos 7 días",
  "u30":"Últimos 30 días",
  "avgMs":"Respuesta promedio 24 h",
  "lastCheck":"Última revisión",
  "every":s=>`cada ${s} s`,
  "sinceFor":"En este estado hace",
  "httpCode":"Código HTTP",
  "certExp":"El certificado vence",
  "latency":"Tiempo de respuesta",
  "sMs":"Respuesta",
  "sPct":"Disponibilidad",
  "noData":"Aún no hay datos.",
  "testOk":(ms,x)=>`OK — ${ms} ms${x?' · '+x:''}`,
  "agoFmt":d=>`hace ${d}`,
  "deleteConfirm":n=>`¿Eliminar «${n}»? Su historial también se borra.`,
  "added":n=>`«${n}» agregado`,
  "deleted":n=>`«${n}» eliminado`,
  "sessionExpired":"Sesión vencida"
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
  try{renderNav();}catch(e){}
  const ov=document.getElementById('add-overlay');if(ov&&ov.classList.contains('show')&&typeof typeChanged==='function')typeChanged();
}
(()=>setLang(_lang))();

let ME=null, items=[], activeId=null, pollTimer=null;
const POLL=10000;                // la página pide el estado cada 10 s mientras se ve / EN: the page asks every 10 s while visible
// Gráfico de detalle (charts.js): mismos rangos 1h / 1d / 1w / 1mo / todo y «vs anterior» que los demás módulos.
// EN: Detail chart (charts.js): the same 1h / 1d / 1w / 1mo / all ranges and "vs previous" as the other modules.
const CHART={series:[{k:'ms',c:'#65a30d',l:'sMs',f:v=>fmtMs(v)}],axis:v=>Math.round(v)+' ms',h:140,pl:52};
let chartRange='1d';
const _rangeData={},_rangeBusy={};

// ── Tema ─────────────────────────────────────────────────────────────────────
function setTheme(t){localStorage.setItem('pi-theme',t);applyTheme(t);['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));}
function applyTheme(t){const p=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;document.documentElement.setAttribute('data-theme',p==='dark'?'dark':'light');}
(()=>{const t=localStorage.getItem('pi-theme')||'dark';applyTheme(t);window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if((localStorage.getItem('pi-theme')||'dark')==='system')applyTheme('system');});setTimeout(()=>{['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));},0);})();

function level(){return ME&&ME.permissions?.uptime;}
function canAdmin(){return level()==='admin';}
function canExec(){return level()==='admin'||level()==='execute';}
const _NAV_SELF='uptime';
// Navegación compartida (nav.js): mismo orden y grupos en todos los módulos. / EN: shared navigation (nav.js): same order and groups in every module.
function renderNav(){if(window.labNav)labNav.render({self:_NAV_SELF,lang:_lang,me:ME});}

// ── Inicio de sesión (la cookie la fija el servidor, HttpOnly: el JavaScript nunca guarda el token) ──
// EN: Login (the cookie is set by the server, HttpOnly: the JavaScript never stores the token)
document.getElementById('l-pass').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
async function doLogin(){
  const btn=document.getElementById('btn-l'),err=document.getElementById('login-err');
  const u=document.getElementById('l-user').value.trim(),p=document.getElementById('l-pass').value;
  err.className='login-err';
  if(!u||!p){err.textContent=t('fillAll');err.className='login-err show';return;}
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
  const k={readonly:'permReadonly',execute:'permExecute',admin:'permAdmin'}[level()];
  document.getElementById('me-role').textContent=k?t(k):'—';
  renderNav();
  document.getElementById('btn-add-mon').style.display=canAdmin()?'':'none';
}
async function logout(){await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.reload();}

// ── Datos ────────────────────────────────────────────────────────────────────
async function initApp(){
  updateClock();setInterval(updateClock,1000);
  await fetchAll();
  pollTimer=setInterval(()=>{if(!document.hidden)fetchAll();},POLL);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)fetchAll();});
}
async function fetchAll(){
  try{
    const r=await fetch('api/monitors');
    if(r.status===401){location.reload();return;}
    const d=await r.json();
    items=d.monitors||[];
    if(activeId&&!items.some(n=>n.id===activeId))activeId=null;
    if(activeId){loadRange(activeId,chartRange);if(VC.cmp.ms&&chartRange!=='all')loadRange(activeId,chartRange,false,true);}
    renderAll();
  }catch(e){console.error(e);}
}
async function loadRange(id,range,force,prev){
  const key=id+'|'+range+(prev?'|prev':''),c=_rangeData[key],ttl=range==='1h'?30000:120000;
  if(!force&&c&&Date.now()-c.ts<ttl)return;
  if(_rangeBusy[key])return;_rangeBusy[key]=true;
  try{
    const r=await fetch('api/monitors/'+encodeURIComponent(id)+'/history?range='+range+(prev?'&prev=1':''));
    if(r.ok){_rangeData[key]={ts:Date.now(),pts:(await r.json()).history||[]};drawChart(id,-1);}
  }catch(e){console.error(e);}
  finally{_rangeBusy[key]=false;}
}
function setRange(btn,range){
  chartRange=range;
  btn.parentNode.querySelectorAll('.vchart-filter:not(.vchart-cmp)').forEach(b=>b.classList.toggle('active',b===btn));
  if(!activeId)return;
  drawChart(activeId,-1);loadRange(activeId,range,true);
  if(VC.cmp.ms&&range!=='all')loadRange(activeId,range,true,true);
}
function toggleCmp(btn){VC.cmp.ms=!VC.cmp.ms;btn.classList.toggle('active',!!VC.cmp.ms);if(!activeId)return;if(VC.cmp.ms&&chartRange!=='all')loadRange(activeId,chartRange,false,true);drawChart(activeId,-1);}
const _cid=id=>'ch-ms-'+String(id).replace(/[^a-z0-9]/gi,'-');
function chartSection(n){
  return VC.section({title:t('latency'),legend:CHART.series.map(x=>({c:x.c,l:t(x.l)})),
    filters:VC.filters(chartRange,r=>`data-on-click="setRange" data-on-click-args="${jsargs([{'@':'this'},r])}"`,`data-on-click="toggleCmp" data-on-click-args="${jsargs([{'@':'this'}])}"`,VC.cmp.ms),
    canvasId:_cid(n.id),tipId:_cid(n.id)+'-tip',h:CHART.h});
}
// Las marcas de eventos son solo las de este monitor (caído, recuperado, certificado). / EN: event marks are only this monitor's.
function drawChart(id,hover){
  const cv=document.getElementById(_cid(id)),n=items.find(x=>x.id===id);if(!cv||!n||id!==activeId)return;
  VC.draw(cv,{pts:((_rangeData[id+'|'+chartRange]||{}).pts||[]),prev:VC.cmp.ms?((_rangeData[id+'|'+chartRange+'|prev']||{}).pts||[]):null,
    series:CHART.series.map(x=>({k:x.k,c:x.c,l:t(x.l),f:x.f})),range:chartRange,hover,h:CHART.h,pl:CHART.pl,axis:CHART.axis,down:true,mod:'uptime',
    evFilter:e=>(e.p||{}).n===n.name,extra:p=>p.pct==null?[]:[t('sPct')+': '+fmtPct(p.pct)]});
}
window.addEventListener('resize',()=>{if(activeId)drawChart(activeId,-1);});
function renderAll(){renderSidebar();renderSummary();renderDashboard();updateGlobalStats();}
function toggleMon(id){activeId=activeId===id?null:id;renderAll();if(activeId)loadRange(activeId,chartRange);}

function stOf(n){return n.status||'none';}
function dotOf(n){return {up:'ok',down:'err'}[n.status]||'loading';}
function typeName(ty){return {http:'HTTP',tcp:'TCP',dns:'DNS'}[ty]||ty;}
function typeLabel(n){return n.type==='http'&&String(n.url||'').startsWith('https://')?'HTTPS':typeName(n.type);}
function renderSidebar(){
  const list=document.getElementById('mon-list');list.innerHTML='';
  items.forEach(n=>{
    const div=document.createElement('div');
    div.className='cluster-nav'+(n.id===activeId?' active':'');
    div.onclick=()=>toggleMon(n.id);
    div.innerHTML=`<span class="cluster-dot ${dotOf(n)}"></span>
      <div style="flex:1;min-width:0"><div class="cluster-nav-name ${n.id===activeId?'act':''}">${esc(n.name)}</div>
      <div class="cluster-nav-host">${esc(typeLabel(n))} · ${esc(t('st_'+stOf(n)))}</div></div>`;
    list.appendChild(div);
  });
}
function certDays(n){return n.cert_exp?Math.floor((n.cert_exp-Date.now()/1000)/86400):null;}
function updateGlobalStats(){
  const up=items.filter(n=>n.status==='up'||n.status==='pending').length,dn=items.filter(n=>n.status==='down').length;
  const pcts=items.map(n=>n.uptime&&n.uptime['24h']).filter(x=>typeof x==='number');
  const cw=items.filter(n=>n.cert==='warn'||n.cert==='expired').length;
  document.getElementById('st-up').textContent=items.length?`${up}/${items.length}`:'—';
  document.getElementById('st-down').textContent=items.length?dn:'—';
  document.getElementById('st-pct').textContent=pcts.length?fmtPct(pcts.reduce((a,b)=>a+b,0)/pcts.length):'—';
  document.getElementById('st-cert').textContent=items.some(n=>n.cert)?cw:'—';
}

function pill(lv,text){return `<span class="pill ${esc(lv)}">${esc(text)}</span>`;}
function statePill(n){return pill({up:'ok',down:'crit',pending:'warn'}[n.status]||'off',t('st_'+stOf(n)));}
function kv(k,v){return `<div class="kv"><span class="k">${esc(k)}</span><span class="v">${v}</span></div>`;}
function fmtPct(p){return typeof p==='number'?(p>=99.995?'100':p.toFixed(2))+' %':'—';}
function pctCell(p){return `<span class="up-pct ${typeof p==='number'?(p<95?'lo':p<99?'mid':''):''}">${esc(fmtPct(p))}</span>`;}
function fmtMs(ms){return typeof ms==='number'?(ms>=1000?(ms/1000).toFixed(2)+' s':Math.round(ms)+' ms'):'—';}
// Barra de las últimas revisiones: cada una es un cuadro (verde arriba, rojo caído, naranjo pendiente) con su hora y respuesta en el título.
// EN: Bar of the last checks: one box each (green up, red down, orange pending) with its time and response in the title.
function beatBar(n){
  const b=n.beats||[],pad=Math.max(0,50-b.length);
  const cells='<i></i>'.repeat(pad)+b.map(x=>{const c={1:'u',0:'d',2:'p'}[x[1]]||'';
    return `<i class="${c}" title="${esc(PCT.time(new Date(x[0]*1000),true)+' · '+(x[1]===1?fmtMs(x[2]):t(x[1]===0?'st_down':'st_pending')))}"></i>`;}).join('');
  const up=b.filter(x=>x[1]!==0).length;
  return `<div class="beats" role="img" aria-label="${esc(b.length?up+'/'+b.length+' '+t('st_up'):t('noData'))}">${cells}</div>`;
}
function certCell(n){
  if(!n.cert)return '<span class="sum-sub">—</span>';
  const d=certDays(n);
  if(n.cert==='expired')return pill('crit',t('certExpired'));
  if(n.cert==='warn')return pill('warn',t('certWarn',d));
  return `<span class="up-pct">${esc(t('certOk',d))}</span>`;
}
function renderSummary(){
  const box=document.getElementById('mon-summary');if(!box)return;
  if(!items.length){box.innerHTML='';return;}
  const rows=items.map(n=>{
    const open=n.id===activeId,u=n.uptime||{};
    return `<tr class="nas-row${open?' expanded':''}" data-on-click="toggleMon" data-on-click-args="${jsargs([n.id])}">
      <td><span class="cluster-dot ${dotOf(n)}"></span></td>
      <td><div class="sum-name">${esc(n.name)}</div><div class="sum-sub">${esc(n.target||'')}</div></td>
      <td><span class="up-badge">${esc(typeLabel(n))}</span></td>
      <td>${statePill(n)}</td>
      <td class="c-beats">${beatBar(n)}</td>
      <td>${pctCell(u['24h'])}</td>
      <td class="c-temp">${pctCell(u['30d'])}</td>
      <td class="c-temp"><span class="up-pct">${esc(fmtMs(n.last&&n.last.ms))}</span></td>
      <td class="c-temp">${certCell(n)}</td>
      <td><span class="expand-arrow ${open?'open':''}">▶</span></td></tr>
    <tr class="detail-row${open?' show':''}"><td colspan="10" class="detail-cell"><div class="nas-detail">${open?buildDetail(n):''}</div></td></tr>`;
  }).join('');
  box.innerHTML=`<div class="card"><div class="card-hd"><span class="card-title">${esc(t('summary'))}</span><span class="card-meta">${esc(items.length)}</span></div>
    <div class="tbl-wrap"><table class="nas-table"><thead><tr><th style="width:24px"></th><th>${esc(t('colMon'))}</th><th>${esc(t('colType'))}</th><th>${esc(t('status'))}</th><th class="c-beats">${esc(t('colBeats'))}</th><th>${esc(t('col24'))}</th><th class="c-temp">${esc(t('col30'))}</th><th class="c-temp">${esc(t('colMs'))}</th><th class="c-temp">${esc(t('colCert'))}</th><th style="width:24px"></th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
  fitDetail();
  if(activeId)drawChart(activeId,-1);        // el canvas se rehízo con la tabla / the canvas was rebuilt with the table
}
function fitDetail(){const w=document.querySelector('#mon-summary .tbl-wrap');if(w)w.style.setProperty('--wrapw',w.clientWidth+'px');}
window.addEventListener('resize',fitDetail);
function renderDashboard(){
  const main=document.getElementById('main-content');
  const n=items.find(x=>x.id===activeId);
  main.innerHTML=items.length?'':'<div class="state-msg"><strong>'+esc(t('noMon'))+'</strong>'+esc(t('noMonHint'))+'</div>';
  document.getElementById('tb-title').textContent=n?n.name:'Uptime Monitor';
  document.getElementById('tb-sub').textContent=n?typeLabel(n)+' · '+(n.target||''):'';
}

// ── Detalle de un monitor: porcentajes, última revisión, gráfico de 24 h y certificado ──
// EN: Monitor detail: percentages, last check, 24 h chart and certificate
function fmtDur(s){s=Math.max(0,Math.round(Number(s)||0));const d=Math.floor(s/86400),h=Math.floor((s%86400)/3600),m=Math.floor((s%3600)/60);return d>0?d+'d '+h+'h':h>0?h+'h '+m+'m':m>0?m+'m':s+'s';}
function ago(ts){return ts?t('agoFmt',fmtDur(Date.now()/1000-ts)):'—';}
function buildDetail(n){
  const u=n.uptime||{},l=n.last;let h='';
  if(l&&!l.ok&&l.error)h+=`<div class="up-err">${esc(l.error)}</div>`;
  h+=`<div class="up-grid"><div class="card"><div class="card-hd"><span class="card-title">${esc(t('uptime'))}</span></div>
    ${kv(t('u24'),pctCell(u['24h']))}${kv(t('u7'),pctCell(u['7d']))}${kv(t('u30'),pctCell(u['30d']))}${kv(t('avgMs'),esc(fmtMs(u.avg)))}</div>
    <div class="card"><div class="card-hd"><span class="card-title">${esc(t('lastCheck'))}</span><span class="card-meta">${esc(t('every',n.interval))}</span></div>
    ${kv(t('lastCheck'),esc(l?ago(l.ts):'—'))}${kv(t('status'),statePill(n))}${kv(t('colMs'),esc(fmtMs(l&&l.ms)))}
    ${n.since?kv(t('sinceFor'),esc(fmtDur(Date.now()/1000-n.since))):''}${l&&l.code?kv(t('httpCode'),esc(l.code)):''}
    ${n.cert_exp?kv(t('certExp'),esc(new Date(n.cert_exp*1000).toLocaleDateString(_lang))+' · '+certCell(n)):''}</div></div>`;
  h+=chartSection(n);
  const tools=[];
  if(canExec())tools.push(`<button class="btn-secondary" data-on-click="checkNow" data-on-click-args="${jsargs([n.id])}">${esc(t('checkNow'))}</button>`);
  if(canAdmin())tools.push(`<button class="btn-secondary" data-on-click="openForm" data-on-click-args="${jsargs([n.id])}">${esc(t('edit'))}</button>`,`<button class="btn-mok" data-on-click="confirmDelete" data-on-click-args="${jsargs([n.id,n.name])}">${esc(t('delete'))}</button>`);
  if(tools.length)h+=`<div class="nas-tools">${tools.join(' ')}</div>`;
  return h;
}
async function checkNow(id){
  try{const {ok,d}=await post('api/monitors/'+encodeURIComponent(id)+'/check',{});if(!ok)throw new Error(d.error||'Error');toast(t('checking'));setTimeout(fetchAll,2500);}
  catch(e){toast(e.message,true);}
}

// ── Alta, edición, prueba y borrado (solo administradores) ────────────────────
let editingId=null;
const $=id=>document.getElementById(id);
function typeChanged(){
  const ty=$('f-type').value;
  $('http-box').style.display=ty==='http'?'flex':'none';$('tcp-box').style.display=ty==='tcp'?'grid':'none';$('dns-box').style.display=ty==='dns'?'flex':'none';
  $('tls-box').style.display=ty==='http'&&$('f-url').value.trim().toLowerCase().startsWith('https://')?'grid':'none';
  $('add-hint').textContent=t('hint_'+ty);
}
function openForm(id){
  editingId=typeof id==='string'?id:null;
  const n=editingId?items.find(x=>x.id===editingId):null;
  $('form-title').textContent=t(n?'editMonTitle':'addMonTitle');
  $('f-type').value=n?n.type:'http';
  $('f-name').value=n?n.name:'';
  $('f-url').value=n&&n.url?n.url:'';$('f-expect').value=n&&n.expect?n.expect:'200-399';$('f-keyword').value=n&&n.keyword?n.keyword:'';
  $('f-insecure').checked=!!(n&&n.insecure);$('f-cert-days').value=n&&n.cert_days?n.cert_days:14;
  $('f-host').value=n&&n.host?n.host:'';$('f-port').value=n&&n.port?n.port:'';
  $('f-qname').value=n&&n.qname?n.qname:'';$('f-rtype').value=n&&n.rtype?n.rtype:'A';$('f-server').value=n&&n.server?n.server:'';$('f-expect-ip').value=n&&n.expect_ip?n.expect_ip:'';
  $('f-interval').value=n?n.interval:60;$('f-timeout').value=n?n.timeout:10;$('f-down-after').value=n?n.down_after:3;
  $('test-result').className='test-result';
  typeChanged();
  $('add-overlay').classList.add('show');$('f-name').focus();
}
function formBody(){
  const ty=$('f-type').value,num=(id,d)=>{const v=parseInt($(id).value,10);return Number.isFinite(v)?v:d;};
  const b={type:ty,name:$('f-name').value.trim(),interval:num('f-interval',60),timeout:num('f-timeout',10),down_after:num('f-down-after',3)};
  if(ty==='http')Object.assign(b,{url:$('f-url').value.trim(),expect:$('f-expect').value.trim()||'200-399',keyword:$('f-keyword').value.trim(),insecure:$('f-insecure').checked,cert_days:num('f-cert-days',14)});
  else if(ty==='tcp')Object.assign(b,{host:$('f-host').value.trim(),port:num('f-port',0)});
  else Object.assign(b,{qname:$('f-qname').value.trim(),rtype:$('f-rtype').value,server:$('f-server').value.trim(),expect_ip:$('f-expect-ip').value.trim()});
  if(editingId)b.id=editingId;
  return b;
}
function filled(b){return !!b.name&&!!(b.type==='http'?b.url:b.type==='tcp'?b.host&&b.port:b.qname);}
async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json().catch(()=>({}));return {ok:r.ok,status:r.status,d};}
async function testMon(){
  const btn=$('btn-test'),res=$('test-result'),b=formBody();
  if(!filled(b)){res.className='test-result fail show';res.textContent='✕ '+t('fillAll');return;}
  btn.innerHTML='<span class="spin">⟳</span>';btn.disabled=true;
  try{
    const {ok,d}=await post('api/test',b);
    if(ok&&d.ok){res.className='test-result ok show';res.textContent=t('testOk',Math.round(d.ms||0),d.code?'HTTP '+d.code:d.ips?d.ips.join(', '):'');}
    else{res.className='test-result fail show';res.textContent='✕ '+(d.error||'Error');}
  }catch(e){res.className='test-result fail show';res.textContent='✕ '+e.message;}
  finally{btn.disabled=false;btn.textContent=t('test');}
}
async function saveMon(){
  const btn=$('btn-save'),b=formBody();
  if(!filled(b)){toast(t('fillAll'),true);return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const {ok,d}=await post(editingId?'api/monitors/'+editingId:'api/monitors',b);
    if(!ok)throw new Error(d.error||'Error');
    toast(editingId?t('saved'):t('added',b.name));closeModals();
    if(!editingId)activeId=d.monitor.id;
    await fetchAll();
  }catch(e){toast(e.message,true);}
  finally{btn.disabled=false;btn.textContent=t('save');}
}
function confirmDelete(id,name){
  $('del-msg').textContent=t('deleteConfirm',name);
  $('del-btn').onclick=async()=>{
    closeModals();
    try{const r=await fetch('api/monitors/'+id,{method:'DELETE'});if(!r.ok)throw new Error((await r.json().catch(()=>({}))).error||'Error');toast(t('deleted',name));await fetchAll();}
    catch(e){toast(e.message,true);}
  };
  $('del-overlay').classList.add('show');
}

// ── Utilidades ───────────────────────────────────────────────────────────────
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
if (window.cspRegister) cspRegister({ checkNow, closeModals, confirmDelete, doLogin, logout, openForm, saveMon, setLang, setRange, setTheme, testMon, toggleCmp, toggleMon, toggleNav, typeChanged });
