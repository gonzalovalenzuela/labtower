// NAS Monitor — página del módulo (/nas/). Muestra uno o varios NAS Synology leídos por SNMP.
// EN: NAS Monitor — module page (/nas/). Shows one or more Synology NAS read over SNMP.
const LANG={
  en:{connecting:'Connecting…',connectingMsg:'Reading the NAS over SNMP.',loginTitle:'Sign in',loginSub:'Enter your credentials to continue.',
    username:'Username',password:'Password',loginBtn:'Sign in',rememberMe:'Remember me',rem1d:'1 day',rem1w:'1 week',rem1m:'1 month',remForever:'Forever',
    navSection:'Navigation',navNAS:'NAS devices',addNas:'Add NAS',themeLight:'Light',themeDark:'Dark',
    statNasOnline:'NAS online',statAvgCPU:'Avg CPU',statAvgRAM:'Avg RAM',statDisks:'Healthy disks',statVols:'Volume usage',
    noNas:'No NAS configured',noNasHint:'Add a Synology, TrueNAS or OpenMediaVault NAS to get started.',
    fieldType:'Type',typeSynology:'Synology (SNMP)',fieldApiUser:'User',fieldApiKey:'API key',fieldPassword:'Password',fieldHttps:'Use HTTPS',fieldVerifyTls:'Verify the TLS certificate',
    tlsNote:'If off, the certificate is pinned on the first connection and a later change is refused (edit and save the NAS to accept a new one).',
    hint_synology:'Enable SNMP on the NAS: Control Panel → Terminal & SNMP → SNMP. SNMPv3 is recommended.',
    hint_truenas:'Needs TrueNAS 25.04 or newer. Create an API key for a dedicated user (the Read-only Admin role is enough) and paste it here; it stays on this server and is never shown again.',
    hint_omv:'Use an OpenMediaVault administrator account (OpenMediaVault has no read-only role); a dedicated one is recommended. Prefer HTTPS: over HTTP the password travels unencrypted.',
    fieldApiUserTn:'User that owns the key',connErrorHintTn:'Check host, port, API key and the user it belongs to. TrueNAS 25.04 or newer is required and this server must be able to reach it.',
    connErrorHintOmv:'Check host, port, HTTP/HTTPS, user and password. The account must be an OpenMediaVault administrator.',
    addNasTitle:'Add NAS',editNasTitle:'Edit NAS',addNasHint:'Enable SNMP on the NAS: Control Panel → Terminal & SNMP → SNMP. SNMPv3 is recommended.',
    fieldName:'Name',fieldPort:'Port',fieldVersion:'SNMP version',fieldTimeout:'Timeout (s)',fieldVolWarn:'Volume warning (%)',fieldVolCrit:'Volume critical (%)',fieldCommunity:'Community',fieldUser:'SNMP user',fieldLevel:'Security level',
    fieldAuthProto:'Auth protocol',fieldAuthPass:'Auth password',fieldPrivProto:'Privacy protocol',fieldPrivPass:'Privacy password',
    secretKept:'Saved. Leave empty to keep it.',cancel:'Cancel',test:'Test',save:'Save',delete:'Delete',deleteNas:'Delete NAS',deleteConfirm:n=>`Delete "${n}" and its history?`,
    edit:'Edit',pause:'Pause',resume:'Resume',paused:'Paused',pausedMsg:'Paused: this NAS is not polled and raises no alerts. Resume it to watch it again.',pausedOk:n=>`${n} paused`,resumedOk:n=>`${n} resumed`,testFillAll:'Fill in the name, host and credentials.',testOk:(m,d)=>`✓ ${m||'SNMP'}${d?' — '+d:''}`,testNotSyno:'✓ SNMP answers, but this is not a Synology (no Synology MIB).',
    added:n=>`${n} added`,saved:'Saved',deleted:n=>`${n} deleted`,
    permReadonly:'Read-only',permExecute:'Execute',permAdmin:'Administrator',
    online:'Online',offline:'Unreachable',connError:'Connection error',connErrorHint:'Check host, port, SNMP version and credentials; SNMP must be allowed from this server.',
    system:'System',model:'Model',serial:'Serial',dsm:'DSM',uptime:'Uptime',temp:'Temperature',cpu:'CPU',memory:'Memory',load:'Load',swap:'Swap',
    power:'Power supply',fans:'Fans',normal:'Normal',failed:'Failed',upgradeYes:'Update available',upgradeNo:'Up to date',upgradeUnk:'—',updates:'System update',
    volumes:'Volumes',disks:'Disks',network:'Network',ups:'UPS',diskLoad:'Disk activity',diskAllIdle:'All disks idle ({n})',diskIdleN:'Idle disks: {n}',history:'History (last hours)',histCpuMem:'CPU / RAM',histTemp:'Temperature',filterAll:'All',trend:'CPU / RAM',accumulating:'Collecting data…',noDataChart:'No data for this range',summary:'NAS Summary',colNas:'NAS',colModel:'Model',colAlerts:'Alerts',histNet:'Network traffic',
    noVolumes:'No volume data (is this a Synology with the Synology MIB enabled?)',noDisks:'No disk data',noNet:'No network data yet',noHist:'Collecting history…',
    daysFull:'~{n} days until full',tempTip:'24 h: max {a} · avg {b} °C — 7 days: max {c} °C',linkDown:'Link down',netErrs:'Errors in/out',
    used:'used',free:'free',rx:'In',tx:'Out',model2:'Model',status:'Status',charge:'Battery',loadPct:'Load',
    disk:{1:'Normal',2:'Initialized',3:'Not initialized',4:'System partition failed',5:'Crashed',6:'Disconnected'},
    raid:{1:'Normal',2:'Repairing',3:'Migrating',4:'Expanding',5:'Deleting',6:'Creating',7:'Syncing',8:'Checking parity',9:'Assembling',10:'Canceling',11:'Degraded',12:'Crashed',13:'Scrubbing',14:'Deploying',15:'Undeploying',16:'Mounting cache',17:'Unmounting cache',18:'Expanding (SHR)',19:'Converting (SHR)',20:'Migrating (SHR)',21:'Unknown'},
    al:{system:'System partition failure',power:'Power supply failure',fan:'Fan failure',temp:v=>`High temperature (${v} °C)`,cpu:v=>`High CPU (${v}%)`,mem:v=>`High memory use (${v}%)`,
        disk:(i,v)=>`${i}: ${LANG.en.disk[v]||v}`,disk_temp:(i,v)=>`${i}: ${v} °C`,raid:(i,v)=>`${i}: ${LANG.en.raid[v]||v}`,vol_full:(i,v)=>`${i} is ${v}% full`,vol_days:(i,v)=>`${i}: fills up in ~${v} days at the current growth`,remote:(i,v)=>`${i}: ${v}`,upgrade:'A system update is available',cert:(i,v)=>`${i}: certificate expires in ${v} days`,cert_exp:i=>`${i}: certificate expired`,cert_err:(i,v)=>`${i}: cannot read the certificate (${v})`},
    certs:'Certificates',certChecking:'Reading certificates…',certSelf:'self-signed',certDaysLeft:'{n} d',certExpired:'Expired',certErr:'Error',certUntil:'Expires {d}',certCheckNow:'Check now',certChecked:'Certificates checked',certCheckErr:'Could not check the certificates',
    fieldCertPorts:'Certificate ports',fieldCertWarn:'Certificate warning (days)',fieldCertCrit:'Certificate critical (days)',certPortsHint:'TLS ports on this NAS whose certificate expiry is checked, comma-separated (for example 5001, 443). Empty = none.',
    sessionExpired:'Session expired'},
  es:{connecting:'Conectando…',connectingMsg:'Leyendo el NAS por SNMP.',loginTitle:'Iniciar sesión',loginSub:'Ingresa tus credenciales para continuar.',
    username:'Usuario',password:'Contraseña',loginBtn:'Entrar',rememberMe:'Recordarme',rem1d:'1 día',rem1w:'1 semana',rem1m:'1 mes',remForever:'Siempre',
    navSection:'Navegación',navNAS:'Equipos NAS',addNas:'Agregar NAS',themeLight:'Claro',themeDark:'Oscuro',
    statNasOnline:'NAS en línea',statAvgCPU:'CPU promedio',statAvgRAM:'RAM promedio',statDisks:'Discos sanos',statVols:'Uso de volúmenes',
    noNas:'Sin NAS configurados',noNasHint:'Agrega un NAS Synology, TrueNAS u OpenMediaVault para empezar.',
    fieldType:'Tipo',typeSynology:'Synology (SNMP)',fieldApiUser:'Usuario',fieldApiKey:'Clave de API',fieldPassword:'Contraseña',fieldHttps:'Usar HTTPS',fieldVerifyTls:'Verificar el certificado TLS',
    tlsNote:'Si está desactivado, el certificado se fija en la primera conexión y un cambio posterior se rechaza (edita y guarda el NAS para aceptar uno nuevo).',
    hint_synology:'Activa SNMP en el NAS: Panel de control → Terminal y SNMP → SNMP. Se recomienda SNMPv3.',
    hint_truenas:'Requiere TrueNAS 25.04 o más nuevo. Crea una clave de API para un usuario dedicado (basta el rol Read-only Admin) y pégala aquí; queda en este servidor y no se vuelve a mostrar.',
    hint_omv:'Usa una cuenta de administrador de OpenMediaVault (no tiene un rol de solo lectura); se recomienda una dedicada. Prefiere HTTPS: con HTTP la contraseña viaja sin cifrar.',
    fieldApiUserTn:'Usuario dueño de la clave',connErrorHintTn:'Revisa host, puerto, clave de API y el usuario al que pertenece. Se requiere TrueNAS 25.04 o más nuevo y que este servidor pueda alcanzarlo.',
    connErrorHintOmv:'Revisa host, puerto, HTTP/HTTPS, usuario y contraseña. La cuenta debe ser administrador de OpenMediaVault.',
    addNasTitle:'Agregar NAS',editNasTitle:'Editar NAS',addNasHint:'Activa SNMP en el NAS: Panel de control → Terminal y SNMP → SNMP. Se recomienda SNMPv3.',
    fieldName:'Nombre',fieldPort:'Puerto',fieldVersion:'Versión de SNMP',fieldTimeout:'Tiempo de espera (s)',fieldVolWarn:'Aviso de volumen (%)',fieldVolCrit:'Crítico de volumen (%)',fieldCommunity:'Comunidad',fieldUser:'Usuario SNMP',fieldLevel:'Nivel de seguridad',
    fieldAuthProto:'Protocolo de autenticación',fieldAuthPass:'Clave de autenticación',fieldPrivProto:'Protocolo de privacidad',fieldPrivPass:'Clave de privacidad',
    secretKept:'Guardada. Déjala vacía para conservarla.',cancel:'Cancelar',test:'Probar',save:'Guardar',delete:'Eliminar',deleteNas:'Eliminar NAS',deleteConfirm:n=>`¿Eliminar «${n}» y su historial?`,
    edit:'Editar',pause:'Pausar',resume:'Reanudar',paused:'Pausado',pausedMsg:'Pausado: este NAS no se consulta ni genera avisos. Reanúdalo para volver a vigilarlo.',pausedOk:n=>`${n} pausado`,resumedOk:n=>`${n} reanudado`,testFillAll:'Completa nombre, host y credenciales.',testOk:(m,d)=>`✓ ${m||'SNMP'}${d?' — '+d:''}`,testNotSyno:'✓ SNMP responde, pero no es un Synology (sin la MIB de Synology).',
    added:n=>`${n} agregado`,saved:'Guardado',deleted:n=>`${n} eliminado`,
    permReadonly:'Solo lectura',permExecute:'Ejecutar',permAdmin:'Administrador',
    online:'En línea',offline:'Sin conexión',connError:'Error de conexión',connErrorHint:'Revisa host, puerto, versión de SNMP y credenciales; SNMP debe permitirse desde este servidor.',
    system:'Sistema',model:'Modelo',serial:'Serie',dsm:'DSM',uptime:'Tiempo encendido',temp:'Temperatura',cpu:'CPU',memory:'Memoria',load:'Carga',swap:'Swap',
    power:'Fuente de poder',fans:'Ventiladores',normal:'Normal',failed:'Falla',upgradeYes:'Actualización disponible',upgradeNo:'Al día',upgradeUnk:'—',updates:'Actualización del sistema',
    volumes:'Volúmenes',disks:'Discos',network:'Red',ups:'UPS',diskLoad:'Actividad de disco',diskAllIdle:'Todos los discos en reposo ({n})',diskIdleN:'Discos en reposo: {n}',history:'Historial (últimas horas)',histCpuMem:'CPU / RAM',histTemp:'Temperatura',filterAll:'Todo',trend:'CPU / RAM',accumulating:'Reuniendo datos…',noDataChart:'Sin datos en este rango',summary:'Resumen de NAS',colNas:'NAS',colModel:'Modelo',colAlerts:'Avisos',histNet:'Tráfico de red',
    noVolumes:'Sin datos de volúmenes (¿es un Synology con la MIB de Synology habilitada?)',noDisks:'Sin datos de discos',noNet:'Aún sin datos de red',noHist:'Reuniendo historial…',
    daysFull:'~{n} días para llenarse',tempTip:'24 h: máx {a} · prom {b} °C — 7 días: máx {c} °C',linkDown:'Enlace caído',netErrs:'Errores ent./sal.',
    used:'usado',free:'libre',rx:'Entrada',tx:'Salida',model2:'Modelo',status:'Estado',charge:'Batería',loadPct:'Carga',
    disk:{1:'Normal',2:'Inicializado',3:'Sin inicializar',4:'Falla de partición del sistema',5:'Dañado',6:'Desconectado'},
    raid:{1:'Normal',2:'Reparando',3:'Migrando',4:'Expandiendo',5:'Eliminando',6:'Creando',7:'Sincronizando',8:'Verificando paridad',9:'Ensamblando',10:'Cancelando',11:'Degradado',12:'Dañado',13:'Depurando datos',14:'Desplegando',15:'Retirando',16:'Montando caché',17:'Desmontando caché',18:'Expandiendo (SHR)',19:'Convirtiendo (SHR)',20:'Migrando (SHR)',21:'Desconocido'},
    al:{system:'Falla en la partición del sistema',power:'Falla en la fuente de poder',fan:'Falla en un ventilador',temp:v=>`Temperatura alta (${v} °C)`,cpu:v=>`CPU alta (${v}%)`,mem:v=>`Memoria alta (${v}%)`,
        disk:(i,v)=>`${i}: ${LANG.es.disk[v]||v}`,disk_temp:(i,v)=>`${i}: ${v} °C`,raid:(i,v)=>`${i}: ${LANG.es.raid[v]||v}`,vol_full:(i,v)=>`${i} está al ${v}%`,vol_days:(i,v)=>`${i}: se llena en ~${v} días al ritmo actual`,remote:(i,v)=>`${i}: ${v}`,upgrade:'Hay una actualización del sistema disponible',cert:(i,v)=>`${i}: el certificado vence en ${v} días`,cert_exp:i=>`${i}: certificado vencido`,cert_err:(i,v)=>`${i}: no se pudo leer el certificado (${v})`},
    certs:'Certificados',certChecking:'Leyendo certificados…',certSelf:'autofirmado',certDaysLeft:'{n} d',certExpired:'Vencido',certErr:'Error',certUntil:'Vence el {d}',certCheckNow:'Revisar ahora',certChecked:'Certificados revisados',certCheckErr:'No se pudieron revisar los certificados',
    fieldCertPorts:'Puertos de certificados',fieldCertWarn:'Aviso de certificado (días)',fieldCertCrit:'Crítico de certificado (días)',certPortsHint:'Puertos TLS de este NAS cuyo certificado se revisa, separados por coma (por ejemplo 5001, 443). Vacío = ninguno.',
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
  try{renderNav();}catch(e){}
  const ov=document.getElementById('add-overlay');if(ov&&ov.classList.contains('show')&&typeof typeChanged==='function')typeChanged();
}
(()=>setLang(_lang))();

let ME=null, items=[], activeId=null, pollTimer=null;
const POLL=5000;                 // el servidor lee cada 15 s con alguien mirando; la página pide cada 5 s mientras se ve
let _histTs=0, _histCache={};    // el historial es grande y cambia cada 30 s: se pide cada 30 s

// ── Tema ─────────────────────────────────────────────────────────────────────
function setTheme(t){localStorage.setItem('pi-theme',t);applyTheme(t);['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));}
function applyTheme(t){const p=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;document.documentElement.setAttribute('data-theme',p==='dark'?'dark':'light');}
(()=>{const t=localStorage.getItem('pi-theme')||'dark';applyTheme(t);window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if((localStorage.getItem('pi-theme')||'dark')==='system')applyTheme('system');});setTimeout(()=>{['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===t));},0);})();

function canAdmin(){return ME&&ME.permissions?.nas==='admin';}
function canExec(){return ME&&['execute','admin'].includes(ME.permissions?.nas);}
const _NAV_SELF='nas';
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

function lvOf(n){if(n.paused)return 'paused';const s=n.snap;if(!s?.ts)return 'loading';if(s.error)return 'err';return 'ok';}
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
    const d=n.snap?.data;if(n.paused||!d||n.snap.error)return;on++;
    if(d.cpu&&d.cpu.pct!=null){cpuS+=d.cpu.pct;cpuN++;}
    if(d.mem){memS+=d.mem.pct;memN++;}
    (d.disks||[]).forEach(x=>{dAll++;if(x.lv==='ok')dOk++;});
    (d.raids||[]).forEach(x=>{if(x.pct!=null&&!x.pool){vS+=x.pct;vN++;}});
  });
  const pc=v=>v==null?'—':Math.round(v)+'<span style="font-size:13px;color:var(--text-dim)">%</span>';
  // Los pausados no cuentan: no se leen. / EN: Paused ones do not count: they are not read.
  const act=items.filter(n=>!n.paused).length;
  document.getElementById('st-nas').textContent=act?`${on}/${act}`:'—';
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
    const state=lv==='paused'?pill('off',t('paused')):lv==='loading'?pill('off','…'):lv==='err'?pill('crit',t('offline')):pill(worst,worst==='ok'?t('online'):al.length+' ⚠');
    const cell=(v,w,c)=>v==null?'—':`<span style="color:${barColor(v,w,c)};font-weight:600">${esc(pc(v))}</span>`;
    return `<tr class="nas-row${open?' expanded':''}" data-on-click="toggleNas" data-on-click-args="${jsargs([n.id])}">
      <td><span class="cluster-dot ${lv}"></span></td>
      <td><div class="sum-name">${esc(n.name)}</div><div class="sum-sub">${esc(n.host)}</div></td>
      <td class="c-model">${esc(sy.model||'—')}<div class="sum-sub">${esc(sy.dsm||'')}</div></td>
      <td>${state}</td>
      <td>${cell(d?.cpu?.pct,CPU_W,CPU_C)}</td><td>${cell(d?.mem?.pct,MEM_W,MEM_C)}</td>
      <td class="c-temp">${sy.temp==null?'—':esc(sy.temp)+' °C'}</td>
      <td>${dk.length?esc(dOk+'/'+dk.length):'—'}</td>
      <td>${vmax>=0?cell(vmax,volW(d),volC(d)):'—'}</td>
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
  if(n){const hs=document.createElement('span');hs.textContent=n.host;hs.setAttribute('data-nethost',n.host);hs.setAttribute('data-nethost-click','1');sub.appendChild(hs);sub.appendChild(document.createTextNode(':'+n.port+' · '+((n.type||'synology')==='synology'?'SNMP '+n.version:n.type==='truenas'?'TrueNAS API':'OpenMediaVault RPC'+(n.https===false?' (HTTP)':''))));}
}

function buildDetail(n){
  const snap=n.snap||{};
  const tools=canAdmin()?`<div class="nas-tools"><button class="btn-secondary" data-on-click="pauseNas" data-on-click-args="${jsargs([{'@':'this'},n.id,!n.paused])}">${esc(n.paused?'▶ '+t('resume'):'⏸ '+t('pause'))}</button><button class="btn-secondary" data-on-click="openNasForm" data-on-click-args="${jsargs([n.id])}">${esc(t('edit'))}</button><button class="btn-secondary" data-on-click="confirmDelete" data-on-click-args="${jsargs([n.id,n.name])}" style="color:var(--red)">${esc(t('delete'))}</button></div>`:'';
  if(n.paused)return `<div class="nas-head"><div><h2>${esc(n.name)} ${pill('off',t('paused'))}</h2></div>${tools}</div><div class="state-msg">${esc(t('pausedMsg'))}</div>`;
  if(!snap.ts){return '<div class="state-msg"><strong>'+esc(t('connecting'))+'</strong>'+esc(t('connectingMsg'))+'</div>';}
  if(snap.error&&!snap.data?.system){
    return `<div class="nas-head"><div><h2>${esc(n.name)}</h2></div>${tools}</div><div class="state-msg err"><strong>${esc(t('connError'))}</strong>${esc(snap.error)}<br><br><span style="font-size:12px;font-family:var(--mono)">${esc(t(n.type==='truenas'?'connErrorHintTn':n.type==='omv'?'connErrorHintOmv':'connErrorHint'))}</span></div>`;
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
    ${s.power==null?'':kv(t('power'),okFail(s.power))}
    ${s.fan_sys==null&&s.fan_cpu==null?'':kv(t('fans'),okFail(s.fan_sys===2||s.fan_cpu===2?2:1))}
    ${(n.type||'synology')!=='synology'&&s.upgrade==null?'':kv(t('updates'),s.upgrade===1?pill('info',t('upgradeYes')):s.upgrade===2?pill('ok',t('upgradeNo')):esc(t('upgradeUnk')))}
    ${mem&&mem.swap_total>0?kv(t('swap'),esc(fmtBytes(mem.swap_used)+' / '+fmtBytes(mem.swap_total))):''}
  </div>`;
  // Volúmenes
  h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('volumes'))}</div></div>`;
  if(!(d.raids||[]).length)h+=`<div class="nas-empty">${esc(t('noVolumes'))}</div>`;
  (d.raids||[]).forEach(r=>{
    const st=r.status_text||(LANG[_lang].raid||{})[r.status]||('#'+r.status);
    h+=`<div class="vol-row"><div class="vol-top"><span class="vol-name">${esc(r.name)}</span>${pill(r.lv,st)}</div>
      ${r.pct!=null?(r.pool?bar(r.pct,101,101):bar(r.pct,volW(d),volC(d))):''}
      <div class="vol-size">${r.pct!=null?esc(r.pct)+'% '+esc(t('used'))+' · '+esc(fmtBytes(r.total-r.free))+' / '+esc(fmtBytes(r.total))+' · '+esc(fmtBytes(r.free))+' '+esc(t('free')):'—'}${r.days_full!=null&&!r.pool?` · <span class="${r.days_full<=30?'days-soon':''}">${esc(t('daysFull').replace('{n}',Math.round(r.days_full)))}</span>`:''}</div></div>`;
  });
  h+='</div>';
  // Discos
  h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('disks'))}</div></div>`;
  if(!(d.disks||[]).length)h+=`<div class="nas-empty">${esc(t('noDisks'))}</div>`;
  (d.disks||[]).forEach(x=>{
    const st=x.status_text||(LANG[_lang].disk||{})[x.status]||('#'+x.status);
    h+=`<div class="disk-row"><span class="dn">${esc(x.name)}</span><span class="dm">${esc(x.model||'—')}<small>${esc(x.type||'')}</small></span><span class="dt${x.temp>=DISK_HOT?' hot':''}"${x.t24?` title="${esc(t('tempTip').replace('{a}',x.t24.max24).replace('{b}',x.t24.avg24).replace('{c}',x.t24.max7))}"`:''}>${x.temp==null?'—':esc(x.temp)+' °C'}${x.t24?` <small>▲${esc(x.t24.max24)}</small>`:''}</span>${pill(x.lv,st)}</div>`;
  });
  h+='</div>';
  // Red
  h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('network'))}</div></div>`;
  if(!(d.net||[]).length)h+=`<div class="nas-empty">${esc(t('noNet'))}</div>`;
  (d.net||[]).forEach(x=>{
    h+=`<div class="net-row"><span class="nn">${esc(x.name)}${x.up===false?` ${pill('warn',t('linkDown'))}`:''}${(x.err_in||x.err_out)?` <small class="net-err" title="${esc(t('netErrs'))}">⚠ ${esc(x.err_in||0)}/${esc(x.err_out||0)}</small>`:''}${x.speed?` <small style="color:var(--text-dim);font-weight:400">${esc(x.speed>=1000?x.speed/1000+' Gb/s':x.speed+' Mb/s')}</small>`:''}</span><span class="nv"><em>↓ ${esc(t('rx'))}</em>${esc(fmtBps(x.rx))}</span><span class="nv"><em>↑ ${esc(t('tx'))}</em>${esc(fmtBps(x.tx))}</span></div>`;
  });
  h+='</div>';
  // UPS del NAS
  if(d.ups){
    h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('ups'))}</div></div>${kv(t('model2'),esc(d.ups.model||'—'))}${kv(t('status'),esc(d.ups.status||'—'))}${kv(t('charge'),d.ups.charge==null?'—':esc(d.ups.charge)+'%')}${kv(t('loadPct'),d.ups.load==null?'—':esc(d.ups.load)+'%')}</div>`;
  }
  // Certificados TLS de los puertos configurados: puerto, nombre y emisor, fecha de vencimiento y días restantes.
  // EN: TLS certificates of the configured ports: port, name and issuer, expiry date and days left.
  if((n.cert_ports||[]).length){
    const chk=canExec()?`<button class="btn-secondary btn-sm" data-on-click="checkCerts" data-on-click-args="${jsargs([{'@':'this'},n.id])}">${esc(t('certCheckNow'))}</button>`:'';
    h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('certs'))}</div>${chk}</div>`;
    if(!(d.certs||[]).length)h+=`<div class="nas-empty">${esc(t('certChecking'))}</div>`;
    (d.certs||[]).forEach(c=>{
      const who=c.error?esc(c.error):`${esc(c.cn||'—')}<small>${esc(c.self_signed?t('certSelf'):(c.issuer||''))}</small>`;
      const when=c.not_after?new Date(c.not_after*1000).toLocaleDateString(_lang==='es'?'es-CL':'en-US',{year:'numeric',month:'short',day:'numeric'}):'';
      const tag=c.lv==='err'?pill('warn',t('certErr')):c.lv==='exp'?pill('crit',t('certExpired')):pill(c.lv,t('certDaysLeft').replace('{n}',c.days));
      h+=`<div class="disk-row cert-row"><span class="dn">:${esc(c.port)}</span><span class="dm"${when?` title="${esc(t('certUntil').replace('{d}',when))}"`:''}>${who}</span><span class="dt">${esc(when)}</span>${tag}</div>`;
    });
    h+='</div>';
  }
  // Actividad de disco: solo se listan los discos con actividad real; los que están en reposo se resumen en una línea (con 8 discos a 0 % eran filas de ruido).
  // EN: Disk activity: only disks with real activity are listed; idle ones are summed up in one line (eight disks at 0 % were noise).
  if((d.io||[]).length){
    const busy=d.io.filter(x=>(x.load||0)>=5||((x.read||0)+(x.write||0))>=262144),idle=d.io.length-busy.length;
    h+=`<div class="node-card"><div class="node-hd"><div class="node-name">${esc(t('diskLoad'))}</div></div>`+busy.map(x=>`<div class="vol-row"><div class="vol-top"><span class="vol-name">${esc(x.dev)}</span><span class="vol-size">${x.read!=null&&x.write!=null?'<small style="color:var(--text-dim);font-weight:400">R '+esc(fmtBytes(x.read))+'/s · W '+esc(fmtBytes(x.write))+'/s</small> · ':''}${x.load==null?'—':esc(x.load)+'%'}</span></div>${bar(x.load||0,70,90)}</div>`).join('')+
      (idle?`<div style="padding:10px 16px;font-size:12px;color:var(--text-dim)">${esc(t(busy.length?'diskIdleN':'diskAllIdle').replace('{n}',idle))}</div>`:'')+'</div>';
  }
  h+='</div>'+chartSections(n);
  return h;
}
const volW=d=>d?.thr?.vol_warn||90,volC=d=>d?.thr?.vol_crit||95;
// Revisar ahora los certificados de un NAS: muestra el resultado al tiro y luego recarga (el poller recalcula las alertas).
// EN: Check a NAS's certificates now: shows the result at once, then reloads (the poller recomputes the alerts).
async function checkCerts(btn,id){
  btn.disabled=true;btn.textContent=t('certChecking');
  try{
    const r=await post('api/nas/'+encodeURIComponent(id)+'/certs',{});
    if(!r.ok){toast(r.d.error||t('certCheckErr'),true);return;}
    const n=items.find(x=>x.id===id);if(n?.snap?.data)n.snap.data.certs=r.d.certs;
    toast(t('certChecked'));renderAll();setTimeout(fetchAll,1500);
  }catch(e){toast(t('certCheckErr'),true);}
  finally{if(btn.isConnected){btn.disabled=false;btn.textContent=t('certCheckNow');}}
}
const CPU_W=70,CPU_C=85,MEM_W=80,MEM_C=90,DISK_HOT=55;

// ── Gráficos de detalle (como los de UPS Monitor): canvas con rangos 1h / 1d / 1mo / todo, cuadrícula, valores actuales y cursor con tooltip ──
// EN: Detail charts (like UPS Monitor's): canvas with 1h / 1d / 1mo / all ranges, grid, current values and a hover cursor with tooltip.
const RANGES=VC.RANGES;
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
async function loadRange(id,range,force,prev){
  const key=id+'|'+range+(prev?'|prev':''),c=_rangeData[key],ttl=range==='1h'?30000:120000;
  if(!force&&c&&Date.now()-c.ts<ttl)return;
  if(_rangeBusy[key])return;_rangeBusy[key]=true;
  try{
    const r=await fetch('api/nas/'+encodeURIComponent(id)+'/history?range='+range+(prev?'&prev=1':''));
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
  btn.parentNode.querySelectorAll('.vchart-filter:not(.vchart-cmp)').forEach(b=>b.classList.toggle('active',b===btn));
  const n=items.find(x=>x.id===activeId);if(!n)return;
  if(_rangeData[n.id+'|'+range])drawCharts(n.id);
  loadRange(n.id,range,true);
  if(VC.cmp[kind]&&range!=='all')loadRange(n.id,range,true,true);
}
function toggleCmp(btn,kind){VC.cmp[kind]=!VC.cmp[kind];btn.classList.toggle('active',!!VC.cmp[kind]);const n=items.find(x=>x.id===activeId);if(!n)return;const range=chartRange[kind];if(VC.cmp[kind]&&range!=='all')loadRange(n.id,range,false,true);drawCharts(n.id);}
const serL=x=>x.l==='cpu'?t('cpu'):x.l==='temp'?t('temp'):x.l==='rx'?'↓ '+t('rx'):x.l==='tx'?'↑ '+t('tx'):x.l;
function chartSections(n){
  return Object.keys(CHARTS).map(k=>{
    const C=CHARTS[k],id=_cid(n.id,k);
    return VC.section({title:t(C.title),legend:C.series.map(x=>({c:x.c,l:serL(x)})),filters:VC.filters(chartRange[k],r=>`data-on-click="setRange" data-on-click-args="${jsargs([{'@':'this'},k,r])}"`,`data-on-click="toggleCmp" data-on-click-args="${jsargs([{'@':'this'},k])}"`,VC.cmp[k]),canvasId:id,tipId:id+'-tip',h:C.h});
  }).join('');
}
function drawCharts(id){
  if(id!==activeId)return;
  Object.keys(CHARTS).forEach(k=>drawChart(id,k,-1));
}
function drawChart(id,kind,hover){
  const C=CHARTS[kind],cv=document.getElementById(_cid(id,kind));if(!cv)return;
  const range=chartRange[kind];
  VC.draw(cv,{pts:(_rangeData[id+'|'+range]||{}).pts||[],prev:VC.cmp[kind]?((_rangeData[id+'|'+range+'|prev']||{}).pts||[]):null,
    series:C.series.map(x=>({k:x.k,c:x.c,l:serL(x),f:x.f})),range,hover,h:C.h,pl:C.series[0].k==='rx'?64:38,max:C.max===100?100:0,axis:C.axis,mod:'nas',
    scale:kind==='tp'?vals=>[Math.max(0,Math.floor(Math.min(...vals)-3)),Math.ceil(Math.max(...vals)+3)]:null});
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
    ring(t('volumes'),vmax>=0?vmax:null,barColor(vmax,volW(d),volC(d)))+
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
// Tipos de NAS: Synology (SNMP), TrueNAS (clave de API) y OpenMediaVault (usuario y contraseña). Puerto y tiempo de espera típicos de cada uno.
// EN: NAS types: Synology (SNMP), TrueNAS (API key) and OpenMediaVault (user and password). Typical port and timeout of each.
const TYPE_PORT={synology:161,truenas:443,omv:443},TYPE_TIMEOUT={synology:5,truenas:8,omv:8},TYPE_CERT={synology:'5001',truenas:'443',omv:'443'};
function curType(){return $('f-type').value;}
function typeChanged(){
  const ty=curType(),syn=ty==='synology',port=parseInt($('f-port').value);
  $('snmp-box').style.display=syn?'flex':'none';$('api-box').style.display=syn?'none':'flex';
  $('add-hint').textContent=t('hint_'+ty);
  if(syn)versionChanged();
  else{
    $('l-api-user').textContent=t(ty==='truenas'?'fieldApiUserTn':'fieldApiUser');
    $('l-api-secret').textContent=t(ty==='truenas'?'fieldApiKey':'fieldPassword');
    $('https-field').style.display=ty==='omv'?'':'none';
    $('f-api-secret').autocomplete='new-password';
  }
  if(!editingId&&[161,443,80].includes(port)){$('f-port').value=(ty==='omv'&&!$('f-https').checked)?80:TYPE_PORT[ty];}
  if(!editingId){$('f-api-timeout').value=TYPE_TIMEOUT[ty];$('f-cert-ports').value=ty==='omv'&&!$('f-https').checked?'':TYPE_CERT[ty];}
}
function httpsChanged(){const p=parseInt($('f-port').value);if($('f-https').checked&&p===80)$('f-port').value=443;else if(!$('f-https').checked&&p===443)$('f-port').value=80;if(!editingId)$('f-cert-ports').value=$('f-https').checked?TYPE_CERT.omv:'';}
function openNasForm(id){
  editingId=typeof id==='string'?id:null;
  const n=editingId?items.find(x=>x.id===editingId):null,ty=n?(n.type||'synology'):'synology';
  $('nas-form-title').textContent=t(n?'editNasTitle':'addNasTitle');
  $('f-type').value=ty;$('f-type').disabled=!!n;
  $('f-vol-warn').value=n?.vol_warn||90;$('f-vol-crit').value=n?.vol_crit||95;
  $('f-cert-ports').value=n?(n.cert_ports||[]).join(', '):TYPE_CERT[ty];$('f-cert-warn').value=n?.cert_warn||14;$('f-cert-crit').value=n?.cert_crit||3;
  $('f-name').value=n?n.name:'';$('f-host').value=n?n.host:'';$('f-port').value=n?n.port:TYPE_PORT[ty];
  $('f-version').value=n&&ty==='synology'?n.version:'3';$('f-timeout').value=n&&ty==='synology'?n.timeout:5;
  $('f-user').value=n&&ty==='synology'?n.user:'';$('f-level').value=n&&ty==='synology'?n.level:'authPriv';
  $('f-auth-proto').value=n&&ty==='synology'?n.auth_proto:'SHA';$('f-priv-proto').value=n&&ty==='synology'?n.priv_proto:'AES';
  ['community','auth_pass','priv_pass'].forEach(k=>{
    const el=$('f-'+k.replace('_','-'));el.value='';
    $('h-'+k).textContent=n&&n['has_'+k]?t('secretKept'):'';
  });
  $('f-api-user').value=n&&ty!=='synology'?n.user:(ty==='omv'?'admin':'');$('f-api-secret').value='';
  const sk=ty==='truenas'?'api_key':'password';
  $('h-api-secret').textContent=n&&n['has_'+sk]?t('secretKept'):'';
  $('f-https').checked=n&&ty!=='synology'?n.https!==false:true;$('f-verify').checked=n&&ty!=='synology'?!!n.verify_tls:false;
  $('f-api-timeout').value=n&&ty!=='synology'?n.timeout:TYPE_TIMEOUT[ty];
  $('test-result').className='test-result';
  typeChanged();
  $('add-overlay').classList.add('show');$('f-name').focus();
}
function formBody(){
  const ty=curType();
  const b={type:ty,name:$('f-name').value.trim(),vol_warn:parseInt($('f-vol-warn').value)||90,vol_crit:parseInt($('f-vol-crit').value)||95,cert_ports:$('f-cert-ports').value,cert_warn:parseInt($('f-cert-warn').value)||14,cert_crit:parseInt($('f-cert-crit').value)||3,host:$('f-host').value.trim(),port:parseInt($('f-port').value)||TYPE_PORT[ty]};
  if(ty==='synology'){
    Object.assign(b,{version:$('f-version').value,timeout:parseInt($('f-timeout').value)||5,user:$('f-user').value.trim(),level:$('f-level').value,
      auth_proto:$('f-auth-proto').value,priv_proto:$('f-priv-proto').value,
      community:$('f-community').value,auth_pass:$('f-auth-pass').value,priv_pass:$('f-priv-pass').value});
  }else{
    Object.assign(b,{user:$('f-api-user').value.trim(),timeout:parseInt($('f-api-timeout').value)||8,verify_tls:$('f-verify').checked});
    b[ty==='truenas'?'api_key':'password']=$('f-api-secret').value;
    if(ty==='omv')b.https=$('f-https').checked;
  }
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
// Pausar o reanudar un NAS (solo admin): no toca su configuración ni la huella del certificado.
// EN: Pause or resume a NAS (admin only): its settings and the certificate fingerprint are left alone.
async function pauseNas(btn,id,paused){
  if(btn)btn.disabled=true;
  try{
    const r=await fetch('api/nas/'+encodeURIComponent(id)+'/pause',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({paused})});
    const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||'Error');
    toast(t(paused?'pausedOk':'resumedOk',d.nas?.name||''));await fetchAll();
  }catch(e){toast(e.message,true);if(btn)btn.disabled=false;}
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

// Funciones que el HTML puede invocar con data-on-* (lista cerrada; ver csp-bind.js).
// EN: Functions the HTML may call through data-on-* (closed list; see csp-bind.js).
if (window.cspRegister) cspRegister({ checkCerts, closeModals, confirmDelete, doLogin, httpsChanged, levelChanged, logout, openNasForm, pauseNas, saveNas, setLang, setRange, toggleCmp, setTheme, testNas, toggleNas, toggleNav, typeChanged, versionChanged });
