// NAS Monitor — página del módulo (/nas/). Muestra uno o varios NAS Synology leídos por SNMP.
// EN: NAS Monitor — module page (/nas/). Shows one or more Synology NAS read over SNMP.
const LANG={
  en:{connecting:'Connecting…',connectingMsg:'Reading the NAS over SNMP.',loginTitle:'Sign in',loginSub:'Enter your credentials to continue.',
    username:'Username',password:'Password',loginBtn:'Sign in',rememberMe:'Remember me',rem1d:'1 day',rem1w:'1 week',rem1m:'1 month',remForever:'Forever',
    navSection:'Navigation',navNAS:'NAS devices',addNas:'Add NAS',themeLight:'Light',themeDark:'Dark',
    statNasOnline:'NAS online',statAvgCPU:'Avg CPU',statAvgRAM:'Avg RAM',statDisks:'Healthy disks',statVols:'Volume usage',
    noNas:'No NAS configured',noNasHint:'Add a Synology NAS to get started. SNMP must be enabled on it.',
    addNasTitle:'Add NAS',editNasTitle:'Edit NAS',addNasHint:'Enable SNMP on the NAS: Control Panel → Terminal & SNMP → SNMP. SNMPv3 is recommended.',
    fieldName:'Name',fieldPort:'Port',fieldVersion:'SNMP version',fieldTimeout:'Timeout (s)',fieldCommunity:'Community',fieldUser:'SNMP user',fieldLevel:'Security level',
    fieldAuthProto:'Auth protocol',fieldAuthPass:'Auth password',fieldPrivProto:'Privacy protocol',fieldPrivPass:'Privacy password',
    secretKept:'Saved. Leave empty to keep it.',cancel:'Cancel',test:'Test',save:'Save',delete:'Delete',deleteNas:'Delete NAS',deleteConfirm:n=>`Delete "${n}" and its history?`,
    edit:'Edit',testFillAll:'Fill in the name, host and credentials.',testOk:(m,d)=>`✓ ${m||'SNMP'}${d?' — '+d:''}`,testNotSyno:'✓ SNMP answers, but this is not a Synology (no Synology MIB).',
    added:n=>`${n} added`,saved:'Saved',deleted:n=>`${n} deleted`,
    permReadonly:'Read-only',permExecute:'Execute',permAdmin:'Administrator',
    online:'Online',offline:'Unreachable',connError:'Connection error',connErrorHint:'Check host, port, SNMP version and credentials; SNMP must be allowed from this Pi.',
    system:'System',model:'Model',serial:'Serial',dsm:'DSM',uptime:'Uptime',temp:'Temperature',cpu:'CPU',memory:'Memory',load:'Load',swap:'Swap',
    power:'Power supply',fans:'Fans',normal:'Normal',failed:'Failed',upgradeYes:'Update available',upgradeNo:'Up to date',upgradeUnk:'—',updates:'DSM update',
    volumes:'Volumes',disks:'Disks',network:'Network',ups:'UPS',diskLoad:'Disk activity',history:'History (last hours)',histCpuMem:'CPU / RAM',histTemp:'Temperature',filterAll:'All',trend:'CPU / RAM',accumulating:'Collecting data…',noDataChart:'No data for this range',summary:'NAS Summary',colNas:'NAS',colModel:'Model',colAlerts:'Alerts',histNet:'Network traffic',
    noVolumes:'No volume data (is this a Synology with the Synology MIB enabled?)',noDisks:'No disk data',noNet:'No network data yet',noHist:'Collecting history…',
    used:'used',free:'free',rx:'In',tx:'Out',model2:'Model',status:'Status',charge:'Battery',loadPct:'Load',
    disk:{1:'Normal',2:'Initialized',3:'Not initialized',4:'System partition failed',5:'Crashed',6:'Disconnected'},
    raid:{1:'Normal',2:'Repairing',3:'Migrating',4:'Expanding',5:'Deleting',6:'Creating',7:'Syncing',8:'Checking parity',9:'Assembling',10:'Canceling',11:'Degraded',12:'Crashed',13:'Scrubbing',14:'Deploying',15:'Undeploying',16:'Mounting cache',17:'Unmounting cache',18:'Expanding (SHR)',19:'Converting (SHR)',20:'Migrating (SHR)',21:'Unknown'},
    al:{system:'System partition failure',power:'Power supply failure',fan:'Fan failure',temp:v=>`High temperature (${v} °C)`,cpu:v=>`High CPU (${v}%)`,mem:v=>`High memory use (${v}%)`,
        disk:(i,v)=>`${i}: ${LANG.en.disk[v]||v}`,disk_temp:(i,v)=>`${i}: ${v} °C`,raid:(i,v)=>`${i}: ${LANG.en.raid[v]||v}`,vol_full:(i,v)=>`${i} is ${v}% full`,upgrade:'A DSM update is available'},
    sessionExpired:'Session expired'},
  es:{connecting:'Conectando…',connectingMsg:'Leyendo el NAS por SNMP.',loginTitle:'Iniciar sesión',loginSub:'Ingresa tus credenciales para continuar.',
    username:'Usuario',password:'Contraseña',loginBtn:'Entrar',rememberMe:'Recordarme',rem1d:'1 día',rem1w:'1 semana',rem1m:'1 mes',remForever:'Siempre',
    navSection:'Navegación',navNAS:'Equipos NAS',addNas:'Agregar NAS',themeLight:'Claro',themeDark:'Oscuro',
    statNasOnline:'NAS en línea',statAvgCPU:'CPU promedio',statAvgRAM:'RAM promedio',statDisks:'Discos sanos',statVols:'Uso de volúmenes',
    noNas:'Sin NAS configurados',noNasHint:'Agrega un NAS Synology para empezar. Debe tener SNMP activado.',
    addNasTitle:'Agregar NAS',editNasTitle:'Editar NAS',addNasHint:'Activa SNMP en el NAS: Panel de control → Terminal y SNMP → SNMP. Se recomienda SNMPv3.',
    fieldName:'Nombre',fieldPort:'Puerto',fieldVersion:'Versión de SNMP',fieldTimeout:'Tiempo de espera (s)',fieldCommunity:'Comunidad',fieldUser:'Usuario SNMP',fieldLevel:'Nivel de seguridad',
    fieldAuthProto:'Protocolo de autenticación',fieldAuthPass:'Clave de autenticación',fieldPrivProto:'Protocolo de privacidad',fieldPrivPass:'Clave de privacidad',
    secretKept:'Guardada. Déjala vacía para conservarla.',cancel:'Cancelar',test:'Probar',save:'Guardar',delete:'Eliminar',deleteNas:'Eliminar NAS',deleteConfirm:n=>`¿Eliminar «${n}» y su historial?`,
    edit:'Editar',testFillAll:'Completa nombre, host y credenciales.',testOk:(m,d)=>`✓ ${m||'SNMP'}${d?' — '+d:''}`,testNotSyno:'✓ SNMP responde, pero no es un Synology (sin la MIB de Synology).',
    added:n=>`${n} agregado`,saved:'Guardado',deleted:n=>`${n} eliminado`,
    permReadonly:'Solo lectura',permExecute:'Ejecutar',permAdmin:'Administrador',
    online:'En línea',offline:'Sin conexión',connError:'Error de conexión',connErrorHint:'Revisa host, puerto, versión de SNMP y credenciales; SNMP debe permitirse desde esta Pi.',
    system:'Sistema',model:'Modelo',serial:'Serie',dsm:'DSM',uptime:'Tiempo encendido',temp:'Temperatura',cpu:'CPU',memory:'Memoria',load:'Carga',swap:'Swap',
    power:'Fuente de poder',fans:'Ventiladores',normal:'Normal',failed:'Falla',upgradeYes:'Actualización disponible',upgradeNo:'Al día',upgradeUnk:'—',updates:'Actualización de DSM',
    volumes:'Volúmenes',disks:'Discos',network:'Red',ups:'UPS',diskLoad:'Actividad de disco',history:'Historial (últimas horas)',histCpuMem:'CPU / RAM',histTemp:'Temperatura',filterAll:'Todo',trend:'CPU / RAM',accumulating:'Reuniendo datos…',noDataChart:'Sin datos en este rango',summary:'Resumen de NAS',colNas:'NAS',colModel:'Modelo',colAlerts:'Avisos',histNet:'Tráfico de red',
    noVolumes:'Sin datos de volúmenes (¿es un Synology con la MIB de Synology habilitada?)',noDisks:'Sin datos de discos',noNet:'Aún sin datos de red',noHist:'Reuniendo historial…',
    used:'usado',free:'libre',rx:'Entrada',tx:'Salida',model2:'Modelo',status:'Estado',charge:'Batería',loadPct:'Carga',
    disk:{1:'Normal',2:'Inicializado',3:'Sin inicializar',4:'Falla de partición del sistema',5:'Dañado',6:'Desconectado'},
    raid:{1:'Normal',2:'Reparando',3:'Migrando',4:'Expandiendo',5:'Eliminando',6:'Creando',7:'Sincronizando',8:'Verificando paridad',9:'Ensamblando',10:'Cancelando',11:'Degradado',12:'Dañado',13:'Depurando datos',14:'Desplegando',15:'Retirando',16:'Montando caché',17:'Desmontando caché',18:'Expandiendo (SHR)',19:'Convirtiendo (SHR)',20:'Migrando (SHR)',21:'Desconocido'},
    al:{system:'Falla en la partición del sistema',power:'Falla en la fuente de poder',fan:'Falla en un ventilador',temp:v=>`Temperatura alta (${v} °C)`,cpu:v=>`CPU alta (${v}%)`,mem:v=>`Memoria alta (${v}%)`,
        disk:(i,v)=>`${i}: ${LANG.es.disk[v]||v}`,disk_temp:(i,v)=>`${i}: ${v} °C`,raid:(i,v)=>`${i}: ${LANG.es.raid[v]||v}`,vol_full:(i,v)=>`${i} está al ${v}%`,upgrade:'Hay una actualización de DSM'},
    sessionExpired:'Sesión vencida'}
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
}
(()=>setLang(_lang))();

let ME=null, items=[], activeId=null, pollTimer=null;
const POLL=5000;                 // el servidor lee cada 15 s con alguien mirando; la página pide cada 5 s mientras se ve
let _histTs=0, _histCache={};    // el historial es grande y cambia cada 30 s: se pide cada 30 s

// ── Tema ─────────────────────────────────────────────────────────────────────
function setTheme(t){localStorage.setItem('pi-theme',t);applyTheme(t);['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));}
function applyTheme(t){const p=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;document.documentElement.setAttribute('data-theme',p==='dark'?'dark':'light');}
(()=>{const t=localStorage.getItem('pi-theme')||'system';applyTheme(t);window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if((localStorage.getItem('pi-theme')||'system')==='system')applyTheme('system');});setTimeout(()=>{['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));},0);})();

// ── Menú lateral común (reordenable; el orden se guarda en el navegador, clave pi-nav-order) ──
function canAdmin(){return ME&&ME.permissions?.nas==='admin';}
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
const _NAV_SELF='nas';
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
  const k={readonly:'permReadonly',execute:'permExecute',admin:'permAdmin'}[ME.permissions?.nas];
  document.getElementById('me-role').textContent=k?t(k):'—';
  renderNav();
  document.getElementById('btn-add-nas').style.display=canAdmin()?'':'none';
}
async function logout(){await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});location.reload();}

// ── Datos ────────────────────────────────────────────────────────────────────
async function initApp(){
  updateClock();setInterval(updateClock,1000);
  await fetchAll();
  pollTimer=setInterval(()=>{if(!document.hidden)fetchAll();},POLL);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)fetchAll();});
}
// Descarga los NAS con su última lectura. El historial pesado se pide solo cada 30 s y se reutiliza entre medias.
// EN: Download the NAS with their last reading. The heavy history is requested only every 30 s and reused in between.
async function fetchAll(){
  try{
    const wantHist=Date.now()-_histTs>=30000;
    const r=await fetch('api/nas'+(wantHist?'':'?hist=0'));
    if(r.status===401){location.reload();return;}
    const d=await r.json();
    items=d.nas||[];
    items.forEach(n=>{if(wantHist)_histCache[n.id]=n.history; else n.history=_histCache[n.id]||[];});
    if(wantHist)_histTs=Date.now();
    if(activeId!==''&&!items.some(n=>n.id===activeId))activeId=items[0]?.id||null;   // '' = el usuario cerró todas las filas
    renderAll();ensureRanges();
  }catch(e){console.error(e);}
}
function renderAll(){renderSidebar();renderSummary();renderDashboard();updateGlobalStats();}
function selectNas(id){activeId=id;renderAll();ensureRanges();}
// Pulsar la fila abierta la cierra; pulsar otra la abre (solo una a la vez, como en UPS Monitor).
// EN: Clicking the open row closes it; clicking another opens it (only one at a time, like UPS Monitor).
function toggleNas(id){activeId=activeId===id?'':id;renderAll();ensureRanges();}

function lvOf(n){const s=n.snap;if(!s?.ts)return 'loading';if(s.error)return 'err';return 'ok';}
function renderSidebar(){
  const list=document.getElementById('nas-list');list.innerHTML='';
  items.forEach(n=>{
    const dotCls=lvOf(n),isActive=n.id===activeId,m=n.snap?.data?.system?.model;
    const div=document.createElement('div');
    div.className='cluster-nav'+(isActive?' active':'');
    div.onclick=()=>selectNas(n.id);
    div.innerHTML=`<span class="cluster-dot ${dotCls}"></span>
      <div style="flex:1;min-width:0"><div class="cluster-nav-name ${isActive?'act':''}">${esc(n.name)}</div>
      <div class="cluster-nav-host"><span data-nethost="${esc(n.host)}">${esc(n.host)}</span>${m?' · '+esc(m):''}</div></div>`;
    list.appendChild(div);
  });
}
// Contadores de la cabecera sumando todos los NAS.
// EN: Header counters adding up all the NAS.
function updateGlobalStats(){
  let on=0,cpuS=0,cpuN=0,memS=0,memN=0,dOk=0,dAll=0,vS=0,vN=0;
  items.forEach(n=>{
    const d=n.snap?.data;if(!d||n.snap.error)return;on++;
    if(d.cpu&&d.cpu.pct!=null){cpuS+=d.cpu.pct;cpuN++;}
    if(d.mem){memS+=d.mem.pct;memN++;}
    (d.disks||[]).forEach(x=>{dAll++;if(x.lv==='ok')dOk++;});
    (d.raids||[]).forEach(x=>{if(x.pct!=null&&!x.pool){vS+=x.pct;vN++;}});
  });
  const pc=v=>v==null?'—':Math.round(v)+'<span style="font-size:13px;color:var(--text-dim)">%</span>';
  document.getElementById('st-nas').textContent=items.length?`${on}/${items.length}`:'—';
  document.getElementById('st-cpu').innerHTML=pc(cpuN?cpuS/cpuN:null);
  document.getElementById('st-mem').innerHTML=pc(memN?memS/memN:null);
  document.getElementById('st-disks').textContent=dAll?`${dOk}/${dAll}`:'—';
  document.getElementById('st-vols').innerHTML=pc(vN?vS/vN:null);
}


// Tabla con todos los NAS (como el resumen de UPS Monitor): cada fila se abre y muestra el detalle justo debajo. Por defecto, el primero.
// EN: Table with every NAS (like UPS Monitor's summary): each row opens and shows its detail right below. The first one by default.
function renderSummary(){
  const box=document.getElementById('nas-summary');if(!box)return;
  if(!items.length){box.innerHTML='';return;}
  const pc=v=>v==null?'—':Math.round(v)+'%';
  const rows=items.map(n=>{
    const sn=n.snap||{},d=sn.data,sy=d?.system||{},lv=lvOf(n),open=n.id===activeId;
    const vmax=(d?.raids||[]).filter(x=>x.pct!=null&&!x.pool).reduce((m,x)=>Math.max(m,x.pct),-1);
    const dk=d?.disks||[],dOk=dk.filter(x=>x.lv==='ok').length;
    const al=(d?.alerts||[]).filter(a=>a.lv!=='info'),worst=al.some(a=>a.lv==='crit')?'crit':al.length?'warn':'ok';
    const state=lv==='loading'?pill('off','…'):lv==='err'?pill('crit',t('offline')):pill(worst,worst==='ok'?t('online'):al.length+' ⚠');
    const cell=(v,w,c)=>v==null?'—':`<span style="color:${barColor(v,w,c)};font-weight:600">${esc(pc(v))}</span>`;
    return `<tr class="nas-row${open?' expanded':''}" data-on-click="toggleNas" data-on-click-args="${jsargs([n.id])}">
      <td><span class="cluster-dot ${lv}"></span></td>
      <td><div class="sum-name">${esc(n.name)}</div><div class="sum-sub">${esc(n.host)}</div></td>
      <td class="c-model">${esc(sy.model||'—')}<div class="sum-sub">${esc(sy.dsm||'')}</div></td>
      <td>${state}</td>
      <td>${cell(d?.cpu?.pct,CPU_W,CPU_C)}</td><td>${cell(d?.mem?.pct,MEM_W,MEM_C)}</td>
      <td class="c-temp">${sy.temp==null?'—':esc(sy.temp)+' °C'}</td>
      <td>${dk.length?esc(dOk+'/'+dk.length):'—'}</td>
      <td>${vmax>=0?cell(vmax,VOL_W,VOL_C):'—'}</td>
      <td class="c-spark">${spark(n.history)}</td>
      <td><span class="expand-arrow ${open?'open':''}">▶</span></td></tr>
    <tr class="detail-row${open?' show':''}"><td colspan="11" class="detail-cell"><div class="nas-detail">${open?buildDetail(n):''}</div></td></tr>`;
  }).join('');
  box.innerHTML=`<div class="card"><div class="card-hd"><span class="card-title">${esc(t('summary'))}</span><span class="card-meta">${esc(items.length)}</span></div>
    <div class="tbl-wrap"><table class="nas-table"><thead><tr><th style="width:24px"></th><th>${esc(t('colNas'))}</th><th class="c-model">${esc(t('colModel'))}</th><th>${esc(t('status'))}</th><th>${esc(t('cpu'))}</th><th>RAM</th><th class="c-temp">${esc(t('temp'))}</th><th>${esc(t('disks'))}</th><th>${esc(t('volumes'))}</th><th class="c-spark">${esc(t('trend'))}</th><th style="width:28px"></th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
  fitDetail();drawCharts(activeId);
}
// El detalle ocupa el ancho visible de la tarjeta aunque la tabla sea más ancha y se desplace (iPad, pantallas angostas).
// EN: The detail takes the visible card width even if the table is wider and scrolls (iPad, narrow screens).
function fitDetail(){const w=document.querySelector('#nas-summary .tbl-wrap');if(w)w.style.setProperty('--wrapw',w.clientWidth+'px');}

// ── Panel del NAS activo ─────────────────────────────────────────────────────
function pill(lv,text){return `<span class="pill ${esc(lv)}">${esc(text)}</span>`;}
function barColor(p,w,c){return p>=c?'var(--red)':p>=w?'var(--orange)':'var(--green)';}
function bar(p,w=80,c=92){p=Math.max(0,Math.min(100,Number(p)||0));return `<div class="res-bar-wrap"><div class="res-bar" style="width:${p}%;background:${barColor(p,w,c)}"></div></div>`;}
function kv(k,v){return `<div class="kv"><span class="k">${esc(k)}</span><span class="v">${v}</span></div>`;}
function okFail(v){return v==null?'—':v===1?pill('ok',t('normal')):pill('crit',t('failed'));}

// Título de la barra superior y mensaje cuando no hay NAS; el detalle de cada NAS vive dentro de su fila (buildDetail).
// EN: Top bar title and the message when there is no NAS; each NAS's detail lives inside its row (buildDetail).
function renderDashboard(){
  const main=document.getElementById('main-content');
  const n=items.find(x=>x.id===activeId);
  main.innerHTML=items.length?'':'<div class="state-msg"><strong>'+esc(t('noNas'))+'</strong>'+esc(t('noNasHint'))+'</div>';
  const sub=document.getElementById('tb-sub');sub.textContent='';
  document.getElementById('tb-title').textContent=n?n.name:'NAS Monitor';
  if(n){const hs=document.createElement('span');hs.textContent=n.host;hs.setAttribute('data-nethost',n.host);hs.setAttribute('data-nethost-click','1');sub.appendChild(hs);sub.appendChild(document.createTextNode(':'+n.port+' · SNMP '+n.version));}
}

function buildDetail(n){
  const snap=n.snap||{};
  const tools=canAdmin()?`<div class="nas-tools"><button class="btn-secondary" data-on-click="openNasForm" data-on-click-args="${jsargs([n.id])}">${esc(t('edit'))}</button><button class="btn-secondary" data-on-click="confirmDelete" data-on-click-args="${jsargs([n.id,n.name])}" style="color:var(--red)">${esc(t('delete'))}</button></div>`:'';
  if(!snap.ts){return '<div class="state-msg"><strong>'+esc(t('connecting'))+'</strong>'+esc(t('connectingMsg'))+'</div>';}
  if(snap.error&&!snap.data?.system){
    return `<div class="nas-head"><div><h2>${esc(n.name)}</h2></div>${tools}</div><div class="state-msg err"><strong>${esc(t('connError'))}</strong>${esc(snap.error)}<br><br><span style="font-size:12px;font-family:var(--mono)">${esc(t('connErrorHint'))}</span></div>`;
  }
  const d=snap.data,s=d.system||{};
  const offline=!!snap.error;
  let h=`<div class="nas-head"><div><h2>${esc(s.model||n.name)} ${offline?pill('crit',t('offline')):pill('ok',t('online'))}</h2><div class="sub">${esc([s.dsm,s.serial].filter(Boolean).join(' · '))}</div></div>${tools}</div>`;
  if(offline)h+=`<div class="alerts"><div class="alert crit">⚠ ${esc(t('connError'))}: ${esc(snap.error)}</div></div>`;
  const al=(d.alerts||[]);
  if(al.length){
    h+='<div class="alerts">'+al.map(a=>{const f=LANG[_lang].al[a.type]||LANG.en.al[a.type];const txt=typeof f==='function'?(a.item!==undefined?f(a.item,a.value):f(a.value)):(f||a.type);
      return `<div class="alert ${esc(a.lv)}">${a.lv==='crit'?'⛔':a.lv==='warn'?'⚠':'ℹ'} ${esc(txt)}</div>`;}).join('')+'</div>';
  }
  h+=gauges(d);
  h+='<div class="nas-grid">';
  // Sistema
  const cpu=d.cpu||{},mem=d.mem;
  h+=`<div class="node-card"><div class="node-hd"><div><div class="node-name">${esc(t('system'))}</div><div class="node-sub">${esc(s.name||'')}</div></div></div>
    <div class="res-bars">
      <div class="res-row"><span class="res-lbl">${esc(t('cpu'))}</span>${bar(cpu.pct,CPU_W,CPU_C)}<span class="res-val">${cpu.pct==null?'—':esc(cpu.pct)+'%'}</span></div>
      <div class="res-row"><span class="res-lbl">RAM</span>${bar(mem?mem.pct:0,MEM_W,MEM_C)}<span class="res-val">${mem?esc(mem.pct)+'% · '+esc(fmtBytes(mem.total)):'—'}</span></div>
    </div>
    ${kv(t('uptime'),esc(fmtUptime(s.uptime)))}
    ${kv(t('temp'),s.temp==null?'—':`${esc(s.temp)} °C`)}
    ${(cpu.load||[]).some(x=>x!=null)?kv(t('load'),esc((cpu.load||[]).map(x=>x==null?'—':x.toFixed(2)).join(' / '))):''}
    ${kv(t('power'),okFail(s.power))}
    ${kv(t('fans'),okFail(s.fan_sys===2||s.fan_cpu===2?2:(s.fan_sys==null&&s.fan_cpu==null?null:1)))}
    ${kv(t('updates'),s.upgrade===1?pill('info',t('upgradeYes')):s.upgrade===2?pill('ok',t('upgradeNo')):esc(t('upgradeUnk')))}
    ${mem&&mem.swap_total>0?kv(t('swap'),esc(fmtBytes(mem.swap_used)+' / '+fmtBytes(mem.swap_total))):''}
  </div>`;
  // Volúmenes
  h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('volumes'))}</div></div>`;
  if(!(d.raids||[]).length)h+=`<div class="nas-empty">${esc(t('noVolumes'))}</div>`;
  (d.raids||[]).forEach(r=>{
    const st=(LANG[_lang].raid||{})[r.status]||('#'+r.status);
    h+=`<div class="vol-row"><div class="vol-top"><span class="vol-name">${esc(r.name)}</span>${pill(r.lv,st)}</div>
      ${r.pct!=null?(r.pool?bar(r.pct,101,101):bar(r.pct,VOL_W,VOL_C)):''}
      <div class="vol-size">${r.pct!=null?esc(r.pct)+'% '+esc(t('used'))+' · '+esc(fmtBytes(r.total-r.free))+' / '+esc(fmtBytes(r.total))+' · '+esc(fmtBytes(r.free))+' '+esc(t('free')):'—'}</div></div>`;
  });
  h+='</div>';
  // Discos
  h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('disks'))}</div></div>`;
  if(!(d.disks||[]).length)h+=`<div class="nas-empty">${esc(t('noDisks'))}</div>`;
  (d.disks||[]).forEach(x=>{
    const st=(LANG[_lang].disk||{})[x.status]||('#'+x.status);
    h+=`<div class="disk-row"><span class="dn">${esc(x.name)}</span><span class="dm">${esc(x.model||'—')}<small>${esc(x.type||'')}</small></span><span class="dt${x.temp>=DISK_HOT?' hot':''}">${x.temp==null?'—':esc(x.temp)+' °C'}</span>${pill(x.lv,st)}</div>`;
  });
  h+='</div>';
  // Red
  h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('network'))}</div></div>`;
  if(!(d.net||[]).length)h+=`<div class="nas-empty">${esc(t('noNet'))}</div>`;
  (d.net||[]).forEach(x=>{
    h+=`<div class="net-row"><span class="nn">${esc(x.name)}${x.speed?` <small style="color:var(--text-dim);font-weight:400">${esc(x.speed>=1000?x.speed/1000+' Gb/s':x.speed+' Mb/s')}</small>`:''}</span><span class="nv"><em>↓ ${esc(t('rx'))}</em>${esc(fmtBps(x.rx))}</span><span class="nv"><em>↑ ${esc(t('tx'))}</em>${esc(fmtBps(x.tx))}</span></div>`;
  });
  h+='</div>';
  // UPS del NAS
  if(d.ups){
    h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('ups'))}</div></div>${kv(t('model2'),esc(d.ups.model||'—'))}${kv(t('status'),esc(d.ups.status||'—'))}${kv(t('charge'),d.ups.charge==null?'—':esc(d.ups.charge)+'%')}${kv(t('loadPct'),d.ups.load==null?'—':esc(d.ups.load)+'%')}</div>`;
  }
  // Actividad de disco
  if((d.io||[]).length){
    h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('diskLoad'))}</div></div>`+d.io.map(x=>`<div class="vol-row"><div class="vol-top"><span class="vol-name">${esc(x.dev)}</span><span class="vol-size">${x.read!=null&&x.write!=null?'<small style="color:var(--text-dim);font-weight:400">R '+esc(fmtBytes(x.read))+'/s · W '+esc(fmtBytes(x.write))+'/s</small> · ':''}${x.load==null?'—':esc(x.load)+'%'}</span></div>${bar(x.load||0,70,90)}</div>`).join('')+'</div>';
  }
  h+='</div>'+chartSections(n);
  return h;
}
const CPU_W=70,CPU_C=85,MEM_W=80,MEM_C=90,VOL_W=80,VOL_C=90,DISK_HOT=55;

// ── Gráficos de detalle (como los de UPS Monitor): canvas con rangos 1h / 1d / 1mo / todo, cuadrícula, valores actuales y cursor con tooltip ──
// EN: Detail charts (like UPS Monitor's): canvas with 1h / 1d / 1mo / all ranges, grid, current values and a hover cursor with tooltip.
const RANGES=['1h','1d','1mo','all'];
const CHARTS={
  cm:{title:'histCpuMem',max:100,series:[{k:'cpu',c:'#f97316',l:'cpu',f:v=>v.toFixed(1)+'%'},{k:'mem',c:'#8b5cf6',l:'RAM',f:v=>v.toFixed(1)+'%'}],axis:v=>Math.round(v)+'%',h:140},
  tp:{title:'histTemp',min:null,series:[{k:'temp',c:'#ef4444',l:'temp',f:v=>v.toFixed(1)+' °C'}],axis:v=>Math.round(v)+'°',h:120},
  nt:{title:'histNet',max:0,series:[{k:'rx',c:'#22c55e',l:'rx',f:fmtBps},{k:'tx',c:'#4361ee',l:'tx',f:fmtBps}],axis:fmtBps,h:120},
};
const chartRange={cm:'1d',tp:'1d',nt:'1d'};
const _rangeData={}, _rangeBusy={};          // «id|rango» → {ts, pts}
const _cid=(id,kind)=>'nch-'+kind+'-'+String(id).replace(/[^a-z0-9]/gi,'-');

// Pide al servidor el historial de un NAS y rango; se reutiliza 30 s (1h) o 2 min (el resto).
// EN: Ask the server for one NAS and range history; reused for 30 s (1h) or 2 min (the rest).
async function loadRange(id,range,force){
  const key=id+'|'+range,c=_rangeData[key],ttl=range==='1h'?30000:120000;
  if(!force&&c&&Date.now()-c.ts<ttl)return;
  if(_rangeBusy[key])return;_rangeBusy[key]=true;
  try{
    const r=await fetch('api/nas/'+encodeURIComponent(id)+'/history?range='+range);
    if(r.ok){const d=await r.json();_rangeData[key]={ts:Date.now(),pts:d.history||[]};drawCharts(id);}
  }catch(e){console.error(e);}
  finally{_rangeBusy[key]=false;}
}
function ensureRanges(){
  const n=items.find(x=>x.id===activeId);if(!n)return;
  Object.keys(CHARTS).forEach(k=>loadRange(n.id,chartRange[k]));
}
function setRange(btn,kind,range){
  chartRange[kind]=range;
  btn.parentNode.querySelectorAll('.vchart-filter').forEach(b=>b.classList.toggle('active',b===btn));
  const n=items.find(x=>x.id===activeId);if(!n)return;
  if(_rangeData[n.id+'|'+range])drawCharts(n.id);
  loadRange(n.id,range,true);
}
function chartSections(n){
  return Object.keys(CHARTS).map(k=>{
    const C=CHARTS[k],id=_cid(n.id,k);
    const leg=C.series.map(x=>`<div class="vchart-legend-item"><div class="vchart-legend-dot" style="background:${x.c}"></div>${esc(x.l==='cpu'?t('cpu'):x.l==='temp'?t('temp'):x.l==='rx'?'↓ '+t('rx'):x.l==='tx'?'↑ '+t('tx'):x.l)}</div>`).join('');
    const flt=RANGES.map(r=>`<button class="vchart-filter${chartRange[k]===r?' active':''}" data-on-click="setRange" data-on-click-args="${jsargs([{'@':'this'},k,r])}">${r==='all'?esc(t('filterAll')):r}</button>`).join('');
    return `<div class="vchart-section"><div class="vchart-header"><span class="vchart-title">${esc(t(C.title))}</span><div class="vchart-legend">${leg}</div><div class="vchart-filters">${flt}</div></div>
      <div class="vchart-body" style="position:relative"><div class="vchart-tooltip" id="${id}-tip"></div><canvas class="vchart" id="${id}" style="--chart-h:${C.h}px"></canvas></div></div>`;
  }).join('');
}
function drawCharts(id){
  if(id!==activeId)return;
  Object.keys(CHARTS).forEach(k=>drawChart(id,k,-1));
}
function drawChart(id,kind,hover){
  const C=CHARTS[kind],cv=document.getElementById(_cid(id,kind));if(!cv)return;
  const range=chartRange[kind],pts=((_rangeData[id+'|'+range]||{}).pts||[]).filter(p=>p&&typeof p.ts==='number');
  const dpr=window.devicePixelRatio||1,W=cv.offsetWidth||600,H=Math.round(cv.getBoundingClientRect().height)||C.h;
  if(cv.width!==W*dpr||cv.height!==H*dpr){cv.width=W*dpr;cv.height=H*dpr;}
  const ctx=cv.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
  const css=k=>getComputedStyle(document.documentElement).getPropertyValue(k).trim();
  const cBg=css('--bg')||'#f0f2f5',cBorder=css('--border')||'#e3e8ef',cDim=css('--text-dim')||'#94a3b8',cSurface=css('--surface')||'#fff';
  ctx.fillStyle=cBg;ctx.fillRect(0,0,W,H);
  ctx.font='11px DM Mono,monospace';ctx.textAlign='center';
  if(pts.length<2){ctx.fillStyle=cDim;ctx.fillText(t(pts.length?'accumulating':'noDataChart'),W/2,H/2);cv._pts=[];return;}
  const N=pts.length,PL=C.series[0].k==='rx'?64:38,PR=10,PT=8,PB=18,W2=W-PL-PR,H2=H-PT-PB;
  const vals=[];pts.forEach(p=>C.series.forEach(x=>{const v=Number(p[x.k]);if(p[x.k]!=null&&isFinite(v))vals.push(v);}));
  if(!vals.length){ctx.fillStyle=cDim;ctx.fillText(t('noDataChart'),W/2,H/2);cv._pts=[];return;}
  let lo=0,hi=C.max===100?100:Math.max(...vals);
  if(kind==='tp'){lo=Math.max(0,Math.floor(Math.min(...vals)-3));hi=Math.ceil(Math.max(...vals)+3);}
  else if(!C.max)hi=Math.max(hi,1)*1.1;
  const rg=hi-lo||1,xOf=i=>PL+(i/(N-1))*W2,yOf=v=>PT+H2-((v-lo)/rg)*H2;
  ctx.strokeStyle=cBorder;ctx.lineWidth=.5;ctx.fillStyle=cDim;ctx.font='9px DM Mono,monospace';ctx.textAlign='right';
  for(let i=0;i<=4;i++){const v=lo+rg/4*i,y=yOf(v);ctx.beginPath();ctx.moveTo(PL,y);ctx.lineTo(W-PR,y);ctx.stroke();ctx.fillText(C.axis(v),PL-3,y+3);}
  C.series.forEach((x,si)=>{
    const line=()=>{ctx.beginPath();let pen=false;pts.forEach((p,i)=>{const v=Number(p[x.k]);if(p[x.k]==null||!isFinite(v)){pen=false;return;}pen?ctx.lineTo(xOf(i),yOf(v)):ctx.moveTo(xOf(i),yOf(v));pen=true;});};
    if(si===0){line();ctx.lineTo(xOf(N-1),PT+H2);ctx.lineTo(PL,PT+H2);ctx.closePath();const g=ctx.createLinearGradient(0,PT,0,PT+H2);g.addColorStop(0,x.c+'33');g.addColorStop(1,x.c+'00');ctx.fillStyle=g;ctx.fill();}
    line();ctx.strokeStyle=x.c;ctx.lineWidth=1.8;ctx.stroke();
  });
  ctx.fillStyle=cDim;ctx.font='9px DM Mono,monospace';ctx.textAlign='center';
  const step=Math.max(1,Math.floor(N/5));
  for(let i=0;i<N;i+=step){const d=new Date(pts[i].ts*1000);ctx.fillText(range==='1mo'||range==='all'?d.toLocaleDateString(_lang==='es'?'es-CL':'en-GB',{day:'2-digit',month:'2-digit'}):PCT.time(d),xOf(i),H-3);}
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
        row.appendChild(dot);row.appendChild(document.createTextNode((sx.l==='cpu'?t('cpu'):sx.l==='temp'?t('temp'):sx.l==='rx'?'↓ '+t('rx'):sx.l==='tx'?'↑ '+t('tx'):sx.l)+': '+(p[sx.k]==null?'—':sx.f(Number(p[sx.k])))));tip.appendChild(row);});
      tip.classList.add('show');
      const tw=tip.offsetWidth,px=e.clientX-r.left+14;tip.style.left=Math.max(0,Math.min(r.width-tw,px>r.width-tw?e.clientX-r.left-tw-14:px))+'px';tip.style.top='6px';
    });
    cv.addEventListener('mouseleave',()=>{const tip=document.getElementById(_cid(id,kind)+'-tip');if(tip)tip.classList.remove('show');drawChart(id,kind,-1);});
  }
}
window.addEventListener('resize',()=>{fitDetail();if(activeId)drawCharts(activeId);});

// Anillos y números de la parte alta del detalle (como los medidores de UPS Monitor).
// EN: Rings and numbers at the top of the detail (like UPS Monitor's gauges).
function ring(label,pct,color,txt){
  const C=2*Math.PI*14.5,p=pct==null?0:Math.max(0,Math.min(100,pct));
  return `<div class="gauge-box"><span class="gauge-lbl">${esc(label)}</span><div class="circle-wrap"><svg viewBox="0 0 36 36"><circle class="circle-bg" cx="18" cy="18" r="14.5"/><circle class="circle-fill" cx="18" cy="18" r="14.5" style="opacity:${pct==null?0:1};stroke-dasharray:${C.toFixed(1)};stroke-dashoffset:${(C*(1-p/100)).toFixed(1)};stroke:${color}"/></svg><span class="circle-val">${pct==null?'—':esc(Math.round(pct))}</span></div><span class="gauge-unit">${esc(txt||'%')}</span></div>`;
}
function bigNum(label,val,unit,color){
  return `<div class="gauge-box"><span class="gauge-lbl">${esc(label)}</span><div class="gauge-num"><span class="runtime-num" style="color:${color||'var(--text)'}">${esc(val)}</span></div><span class="gauge-unit">${esc(unit||'')}</span></div>`;
}
function gauges(d){
  const cpu=d.cpu||{},mem=d.mem,s=d.system||{};
  const vmax=(d.raids||[]).filter(x=>x.pct!=null&&!x.pool).reduce((m,x)=>Math.max(m,x.pct),-1);
  const dk=d.disks||[],dOk=dk.filter(x=>x.lv==='ok').length;
  const tc=s.temp==null?'var(--text)':s.temp>=70?'var(--red)':s.temp>=55?'var(--orange)':'var(--blue)';
  return '<div class="nas-gauges">'+
    ring(t('cpu'),cpu.pct,barColor(cpu.pct||0,CPU_W,CPU_C))+ring('RAM',mem?mem.pct:null,barColor(mem?mem.pct:0,MEM_W,MEM_C))+
    ring(t('volumes'),vmax>=0?vmax:null,barColor(vmax,VOL_W,VOL_C))+
    bigNum(t('temp'),s.temp==null?'—':s.temp,s.temp==null?'':'°C',tc)+bigNum(t('disks'),dk.length?dOk+'/'+dk.length:'—','',dk.length&&dOk<dk.length?'var(--red)':'var(--text)')+
    bigNum(t('uptime'),fmtUptime(s.uptime),'')+'</div>';
}
// Mini-gráfico (CPU y RAM de las últimas horas) para la tabla: al pulsarlo se abre el detalle de ese NAS.
// EN: Mini chart (CPU and RAM of the last hours) for the table: clicking it opens that NAS's detail.
function spark(hist){
  const pts=(hist||[]).filter(p=>p&&typeof p.ts==='number');if(pts.length<3)return '<span class="sum-sub">—</span>';
  const W=90,H=24,t0=pts[0].ts,t1=pts[pts.length-1].ts||t0+1;
  const path=(k,c)=>{let d='',pen=false;pts.forEach(p=>{const v=Number(p[k]);if(p[k]==null||!isFinite(v)){pen=false;return;}d+=(pen?'L':'M')+(((p.ts-t0)/Math.max(1,t1-t0))*W).toFixed(1)+' '+(H-1-Math.max(0,Math.min(100,v))/100*(H-2)).toFixed(1)+' ';pen=true;});return `<path d="${d}" fill="none" stroke="${c}" stroke-width="1.4" stroke-linejoin="round"/>`;};
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">${path('cpu','#f97316')}${path('mem','#8b5cf6')}</svg>`;
}
// ── Alta, edición, prueba y borrado (solo administradores) ────────────────────
// SNMP v3 (usuario y claves) o v2c (comunidad). Al editar, los secretos llegan vacíos: dejarlos vacíos conserva los guardados.
// EN: SNMP v3 (user and keys) or v2c (community). When editing, secrets arrive empty: leaving them empty keeps the stored ones.
let editingId=null;
const $=id=>document.getElementById(id);
function versionChanged(){const v3=$('f-version').value==='3';$('v3-box').style.display=v3?'flex':'none';$('v2-box').style.display=v3?'none':'';levelChanged();}
function levelChanged(){const l=$('f-level').value;$('auth-box').style.display=l==='noAuthNoPriv'?'none':'';$('priv-box').style.display=l==='authPriv'?'':'none';}
function openNasForm(id){
  editingId=typeof id==='string'?id:null;
  const n=editingId?items.find(x=>x.id===editingId):null;
  $('nas-form-title').textContent=t(n?'editNasTitle':'addNasTitle');
  $('f-name').value=n?n.name:'';$('f-host').value=n?n.host:'';$('f-port').value=n?n.port:161;
  $('f-version').value=n?n.version:'3';$('f-timeout').value=n?n.timeout:5;
  $('f-user').value=n?n.user:'';$('f-level').value=n?n.level:'authPriv';
  $('f-auth-proto').value=n?n.auth_proto:'SHA';$('f-priv-proto').value=n?n.priv_proto:'AES';
  ['community','auth_pass','priv_pass'].forEach(k=>{
    const el=$('f-'+k.replace('_','-'));el.value='';
    $('h-'+k).textContent=n&&n['has_'+k]?t('secretKept'):'';
  });
  $('test-result').className='test-result';
  versionChanged();
  $('add-overlay').classList.add('show');$('f-name').focus();
}
function formBody(){
  const b={name:$('f-name').value.trim(),host:$('f-host').value.trim(),port:parseInt($('f-port').value)||161,version:$('f-version').value,
    timeout:parseInt($('f-timeout').value)||5,user:$('f-user').value.trim(),level:$('f-level').value,
    auth_proto:$('f-auth-proto').value,priv_proto:$('f-priv-proto').value,
    community:$('f-community').value,auth_pass:$('f-auth-pass').value,priv_pass:$('f-priv-pass').value};
  if(editingId)b.id=editingId;
  return b;
}
async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json().catch(()=>({}));return {ok:r.ok,status:r.status,d};}
// «Probar» consulta el NAS con lo escrito en el formulario, sin guardar nada.
// EN: "Test" queries the NAS with what is typed in the form, saving nothing.
async function testNas(){
  const btn=$('btn-test'),res=$('test-result'),b=formBody();
  if(!b.name||!b.host){res.className='test-result fail show';res.textContent='✕ '+t('testFillAll');return;}
  btn.innerHTML='<span class="spin">⟳</span>';btn.disabled=true;
  try{
    const {d}=await post('api/test',b);
    if(d.ok){res.className='test-result ok show';res.textContent=d.synology===false?t('testNotSyno'):t('testOk',d.model,d.dsm);}
    else{res.className='test-result fail show';res.textContent='✕ '+(d.error||'Error');}
  }catch(e){res.className='test-result fail show';res.textContent='✕ '+e.message;}
  finally{btn.disabled=false;btn.textContent=t('test');}
}
async function saveNas(){
  const btn=$('btn-save'),b=formBody();
  if(!b.name||!b.host){toast(t('testFillAll'),true);return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const {ok,d}=await post(editingId?'api/nas/'+editingId:'api/nas',b);
    if(!ok)throw new Error(d.error||'Error');
    toast(editingId?t('saved'):t('added',b.name));closeModals();_histTs=0;await fetchAll();if(!editingId)selectNas(d.nas.id);
  }catch(e){toast(e.message,true);}
  finally{btn.disabled=false;btn.textContent=t('save');}
}
function confirmDelete(id,name){
  $('del-msg').textContent=t('deleteConfirm',name);
  $('del-btn').onclick=async()=>{
    closeModals();
    try{const r=await fetch('api/nas/'+id,{method:'DELETE'});if(!r.ok)throw new Error((await r.json().catch(()=>({}))).error||'Error');toast(t('deleted',name));await fetchAll();}
    catch(e){toast(e.message,true);}
  };
  $('del-overlay').classList.add('show');
}

// ── Utilidades ───────────────────────────────────────────────────────────────
function fmtBytes(b){b=Number(b);if(!b)return'0 B';const u=['B','KB','MB','GB','TB','PB'];let i=0;while(b>=1024&&i<u.length-1){b/=1024;i++;}return b.toFixed(i>0?1:0)+' '+u[i];}
function fmtBps(v){if(v==null||!isFinite(Number(v)))return'—';v=Number(v);const u=['bit/s','Kb/s','Mb/s','Gb/s'];let i=0;while(v>=1000&&i<u.length-1){v/=1000;i++;}return v.toFixed(i>0?1:0)+' '+u[i];}
function fmtUptime(s){s=Number(s);if(!s)return'—';const d=Math.floor(s/86400),h=Math.floor((s%86400)/3600),m=Math.floor((s%3600)/60);if(d>0)return d+'d '+h+'h';if(h>0)return h+'h '+m+'m';return m+'m';}
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
