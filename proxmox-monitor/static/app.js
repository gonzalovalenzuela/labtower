const LANG={
  en:{connecting:'Connecting…',connectingMsg:'Fetching data from Proxmox.',noNodes:'No nodes',noNodesMsg:'No nodes were found in this cluster.',loginTitle:'Sign in',loginSub:'Enter your credentials to continue.',
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
    running:'running',
    nodeOfflineMsg:'Node offline — no data available',connError:'Connection error',connErrorHint:'Check host, port and API token',
    nodeCountNav:(n)=>`${n} node${n!==1?'s':''}`,
    pinNode:'Pin node in place',unpinNode:'Unpin node',moveEarlier:'Move earlier',moveLater:'Move later',dragReorder:'Drag to reorder',resetOrder:'Reset node order',layoutSaved:'Node order saved',
    testConnected:(v,n)=>`✓ PVE ${v} — ${n} node${n!==1?'s':''}`,
    testFillAll:'Fill in all fields',
    fpConfirm:(fp)=>`Certificate SHA-256: ${fp} — compare it with the one shown in Proxmox (Datacenter → Node → Certificates). Press Test again to trust it and test the connection.`,
    fpNeedTest:'Run Test and confirm the certificate first',fpChanged:'Host or port changed: run Test again',
    unpinnedWarn:'This cluster\'s certificate is not verified.',unpinnedDesc:'The connection does not check the identity of the server before sending the API token, so someone on the network could impersonate it.',unpinned:'Certificate not verified',pinCert:'Pin certificate',pinPrompt:(fp)=>`Trust this certificate for this cluster?\n\nSHA-256:\n${fp}`,pinned:'Certificate pinned',
    clusterAdded:(name)=>`${name} added`,
    deleteClusterConfirm:(name)=>`Delete cluster "${name}"?`,
    cpuAlert:(pct)=>`CPU at ${pct}%`,ramAlert:(pct)=>`RAM at ${pct}%`},
  es:{connecting:'Conectando…',connectingMsg:'Obteniendo datos de Proxmox.',noNodes:'Sin nodos',noNodesMsg:'No se encontraron nodos en este cluster.',loginTitle:'Iniciar sesión',loginSub:'Ingresa tus credenciales para continuar.',
    username:'Usuario',password:'Contraseña',loginBtn:'Entrar',rememberMe:'Recordarme',rem1d:'1 día',rem1w:'1 semana',rem1m:'1 mes',remForever:'Siempre',
    navSection:'Navegación',clustersPVE:'Clusters PVE',addCluster:'Agregar cluster',
    themeLight:'Claro',themeDark:'Oscuro',
    statNodesOnline:'Nodos online',statVMsRunning:'VMs corriendo',
    statCTsRunning:'CTs corriendo',statAvgCPU:'CPU promedio',statAvgRAM:'RAM promedio',
    noClusters:'Sin clusters configurados',noClustersHint:'Agrega un cluster Proxmox para comenzar.',
    addClusterTitle:'Agregar cluster Proxmox',
    addClusterHint:'Necesitas un API Token en Proxmox: Datacenter → API Tokens → Add',
    fieldName:'Nombre',fieldPort:'Puerto',fieldPVEUser:'Usuario PVE',
    formatLabel:'Formato',cancel:'Cancelar',test:'Probar',delete:'Eliminar',
    deleteCluster:'Eliminar cluster',
    permReadonly:'Solo lectura',permExecute:'Ejecución',permAdmin:'Administrador',
    sessionExpired:'Sesión expirada',
    nodeOnline:'Online',nodeOffline:'Offline',
    vmsRunning:'VMs',ctsRunning:'CTs',
    cpu:'CPU',memory:'Memoria',disk:'Disco',
    historyChart:'Historial CPU/RAM (últimas muestras)',
    sectionVMs:'Máquinas Virtuales',sectionCTs:'Contenedores',
    running:'corriendo',
    nodeOfflineMsg:'Nodo offline — sin datos disponibles',connError:'Error de conexión',connErrorHint:'Verifica host, puerto y token API',
    nodeCountNav:(n)=>`${n} nodo${n!==1?'s':''}`,
    pinNode:'Fijar nodo en su lugar',unpinNode:'Desfijar nodo',moveEarlier:'Mover antes',moveLater:'Mover después',dragReorder:'Arrastra para reordenar',resetOrder:'Restablecer orden de nodos',layoutSaved:'Orden de nodos guardado',
    testConnected:(v,n)=>`✓ PVE ${v} — ${n} nodo${n!==1?'s':''}`,
    testFillAll:'Completa todos los campos',
    fpConfirm:(fp)=>`Certificado SHA-256: ${fp} — compáralo con el de Proxmox (Datacenter → Nodo → Certificates). Presiona Probar otra vez para confiar en él y probar la conexión.`,
    fpNeedTest:'Primero usa Probar y confirma el certificado',fpChanged:'Cambió el host o el puerto: usa Probar otra vez',
    unpinnedWarn:'El certificado de este cluster no está verificado.',unpinnedDesc:'La conexión no comprueba la identidad del servidor antes de enviar el token de la API, así que alguien en la red podría suplantarlo.',unpinned:'Certificado sin verificar',pinCert:'Fijar certificado',pinPrompt:(fp)=>`¿Confiar en este certificado para este cluster?\n\nSHA-256:\n${fp}`,pinned:'Certificado fijado',
    clusterAdded:(name)=>`${name} agregado`,
    deleteClusterConfirm:(name)=>`¿Eliminar el cluster "${name}"?`,
    cpuAlert:(pct)=>`CPU al ${pct}%`,ramAlert:(pct)=>`RAM al ${pct}%`}
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
  ['en','es'].forEach(x=>document.getElementById('lang-'+x)?.classList.toggle('active',x===l));
  if(_i18nReady && typeof renderAll==='function')renderAll();
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
(()=>{const t=localStorage.getItem('pi-theme')||'system';applyTheme(t);window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if((localStorage.getItem('pi-theme')||'system')==='system')applyTheme('system');});setTimeout(()=>{['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===(localStorage.getItem('pi-theme')||'system')));},0);})();

// ── Nav reordenable ───────────────────────────────────────────────────────────
// ¿Puede agregar y borrar clusters, fijar certificados y ordenar nodos? (nivel «admin» de Proxmox).
// EN: Can it add and delete clusters, pin certificates and reorder nodes? (Proxmox "admin" level).
function canAdmin(){return ME&&ME.permissions?.pve==='admin';}
// Barra lateral común: los mismos accesos en todas las páginas. El usuario puede reordenarlos arrastrando (el orden se guarda en el navegador, clave pi-nav-order). «Admin» solo se muestra a administradores.
// EN: Common sidebar: the same links on every page. The user can reorder them by dragging (the order is stored in the browser, key pi-nav-order). "Admin" is shown to administrators only.
const _NAV_ITEMS=[
  {id:'overview', href:'/overview/', label:'Overview', svg:'<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>'},
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
const _NAV_SELF='pve';
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

// ── Login ────────────────────────────────────────────────────────────────────
document.getElementById('l-pass').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
// Inicio de sesión. La cookie la fija el servidor (HttpOnly): el JavaScript nunca guarda el token.
// EN: Login. The cookie is set by the server (HttpOnly): the JavaScript never stores the token.
async function doLogin(){
  const btn=document.getElementById('btn-l'),err=document.getElementById('login-err');
  const u=document.getElementById('l-user').value.trim(),p=document.getElementById('l-pass').value;
  err.className='login-err';
  if(!u||!p){err.textContent='Completa todos los campos';err.className='login-err show';return;}
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
  finally{btn.disabled=false;btn.textContent='Entrar';}
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
  const grid=document.createElement('div');grid.className='nodes-grid';
  const names=nodes.map(n=>n.name), pinnedSet=new Set(cluster.layout?.pinned||[]);
  if(isPveAdmin()&&(cluster.layout?.order?.length||cluster.layout?.pinned?.length)){
    const bar=document.createElement('div');bar.className='layout-bar';
    bar.innerHTML=`<button data-on-click="resetLayout" data-on-click-args="${jsargs([cluster.id])}">${esc(t('resetOrder'))}</button>`;
    main.appendChild(bar);
  }
  nodes.forEach(node=>{const card=buildNodeCard(node);decorateCard(card,cluster,node.name,names,pinnedSet);grid.appendChild(card);});
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

  // Dibujar sparklines después de que el DOM esté pintado
  renderSparklines(nodes);
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
function buildNodeCard(node){
  const card=document.createElement('div');card.className='node-card';
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
        <div class="node-name">${esc(node.name)}</div>
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
    ${node.history?.length>2?`<div style="padding:4px 12px 8px">
      <div style="font-size:10px;color:var(--text-dim);margin-bottom:3px;font-weight:500">${t('historyChart')}</div>
      <canvas id="spark-${esc(node.name)}" height="32" style="width:100%;height:32px;display:block;border-radius:4px;background:var(--bg)"></canvas>
    </div>`:''}
    ${buildVMSection(allVMs, 'VM', runVMs, node.name)}
    ${buildVMSection(allCTs, 'CT', runCTs, node.name)}
    `:`<div style="padding:20px;text-align:center;color:var(--text-dim);font-size:12px">${t('nodeOfflineMsg')}</div>`}`;
  return card;
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
  const sorted=[...items].sort((a,b)=>{
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
            <span class="vm-name" title="${esc(v.name||'')}">${esc(v.name||'—')}${v.lock==='migrate'?' <span title="migrating" style="color:var(--orange)">⇄</span>':''}</span>
            <span class="vm-type ${type.toLowerCase()}">${type}</span>
            ${v.status==='running'?`
              <span class="vm-cpu">${cpuPct}%</span>
              <span class="vm-mem">${fmtBytes(v.mem||0)}</span>
              <span class="vm-uptime">${fmtUptime(v.uptime)}</span>
            `:`<span style="font-size:10px;color:var(--text-dim);flex:1;text-align:right">${esc(v.status)}</span>`}
          </div>`;
        }).join('')}
      </div>
    </div>
  </div>`;
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
function fmtBytes(b){b=Number(b);if(!b)return'0B';const u=['B','KB','MB','GB','TB'];let i=0;while(b>=1024&&i<u.length-1){b/=1024;i++;}return b.toFixed(i>0?1:0)+' '+u[i];}
function fmtUptime(s){s=Number(s);if(!s)return'—';const d=Math.floor(s/86400),h=Math.floor((s%86400)/3600),m=Math.floor((s%3600)/60);if(d>0)return d+'d '+h+'h';if(h>0)return h+'h '+m+'m';return m+'m';}
// Escapa HTML antes de insertar texto de usuarios, equipos o la red en la página: evita inyección de código (XSS).
// EN: Escape HTML before inserting text from users, devices or the network into the page: prevents code injection (XSS).
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
// Valor seguro dentro de un handler on*="…": literal JS entre comillas, escapado también para HTML.
function jsa(s){return esc(JSON.stringify(String(s)));}
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
