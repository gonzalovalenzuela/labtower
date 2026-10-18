// ── i18n ──────────────────────────────────────────────
// Textos de la interfaz en inglés (en) y español (es). t('clave') devuelve el texto del idioma activo; si falta la clave en español, usa el inglés. Para agregar un idioma basta otro bloque con las mismas claves.
// EN: Interface texts in English (en) and Spanish (es). t('key') returns the text for the active language; if a Spanish key is missing, it falls back to English. Adding a language only takes another block with the same keys.
const LANG = {
  en: {
    filterAll:'All', titleLogout:'Sign out', errLoad:'Error loading data', noPerm:'No permission', titEdit:'Edit', titDelete:'Delete',
    msgSent:n=>`Magic packet sent to "${n}"`, noVisible:'No visible devices', errDelete:'Error deleting', errHistory:'Error loading history', ago:x=>x+' ago',
    loginTitle:'Sign in', loginSub:'Enter your credentials to continue.',
    username:'Username', password:'Password', loginBtn:'Sign in',
    navSection:'Navigation', actionsSection:'Actions',
    exportJSON:'Export JSON', wakeHistory:'Wake History',
    readonlyMsg:'Read-only mode — you cannot execute actions',
    devicesTitle:'Devices',
    colName:'Name', colType:'Type', colLastWake:'Last wake', colActions:'Actions',
    colDateTime:'Date/Time', colDevice:'Device', colUser:'User',
    fromNet:'From Net Monitor', fromNetPick:'Select a detected host…', fromNetHave:'already added', netIp:'IP from Net Monitor',
    addDevice:'Add device', editMode:'Edit mode', cancel:'Cancel',
    fieldName:'Name', fieldMAC:'MAC Address', macHint:'Formats: AA:BB:CC:DD:EE:FF · AA-BB-CC-DD-EE-FF',
    refOnly:'(reference only)', wolPort:'WOL Port', category:'Category',
    optional:'(optional)', notesPlaceholder:'Server room, rack 2...',
    btnSubmitAdd:'Add device', btnSubmitSave:'Save changes',
    activity:'Activity', clear:'Clear',
    deleteDevice:'Delete device', delete:'Delete',
    wakeAllMsg:'A magic packet will be sent to the following devices:',
    sendAll:'Send to all',
    alreadyOnlineTitle:'Device already on', alreadyOnlineMsg:'is responding to ping. Send magic packet anyway?',
    sendAnyway:'Send anyway', close:'Close',
    statRegistered:'Registered devices', statWakesSent:'Wakes sent',
    statLastWake:'Last wake', statSession:'Active session',
    themeLight:'Light', themeDark:'Dark',
    permReadonly:'Read-only', permExecute:'Execute', permAdmin:'Administrator',
    wakeNoPerms:'No execute permissions',
    noDevices:'No devices', noResults:'No results',
    addFirst:'Add the first device →', tryFilter:'Try another filter.',
    connError:'No connection',
    connErrorSub:'Verify that server.py is running.',
    wakeLogEmpty:'No records yet',
    logStarting:'WOL Console starting...', logLoaded:' device(s) loaded',
    logNoPerms:'No execute permissions',
    sessionExpired:'Session expired',
    searchPlaceholder:'Search by name, MAC, IP...',
    deleteConfirm:(name,mac)=>`Delete "${name}" (${mac})? This cannot be undone.`,
    signingIn:'Signing in…',saving:'Saving…'
  },
  es: {
    filterAll:'Todos', titleLogout:'Cerrar sesión', errLoad:'Error al cargar', noPerm:'Sin permisos', titEdit:'Editar', titDelete:'Eliminar',
    msgSent:n=>`Paquete enviado a "${n}"`, noVisible:'No hay equipos visibles', errDelete:'Error al eliminar', errHistory:'Error cargando historial', ago:x=>'hace '+x,
    loginTitle:'Iniciar sesión', loginSub:'Ingresa tus credenciales para continuar.',
    username:'Usuario', password:'Contraseña', loginBtn:'Entrar',
    navSection:'Navegación', actionsSection:'Acciones',
    exportJSON:'Exportar JSON', wakeHistory:'Historial Wakes',
    readonlyMsg:'Modo solo lectura — no puedes ejecutar acciones',
    devicesTitle:'Dispositivos',
    colName:'Nombre', colType:'Tipo', colLastWake:'Último wake', colActions:'Acciones',
    colDateTime:'Fecha/Hora', colDevice:'Equipo', colUser:'Usuario',
    fromNet:'Desde Net Monitor', fromNetPick:'Selecciona un equipo detectado…', fromNetHave:'ya agregado', netIp:'IP desde Net Monitor',
    addDevice:'Agregar equipo', editMode:'Modo edición', cancel:'Cancelar',
    fieldName:'Nombre', fieldMAC:'Dirección MAC', macHint:'Formatos: AA:BB:CC:DD:EE:FF · AA-BB-CC-DD-EE-FF',
    refOnly:'(solo referencia)', wolPort:'Puerto WOL', category:'Categoría',
    optional:'(opcional)', notesPlaceholder:'Sala de servidores, rack 2...',
    btnSubmitAdd:'Agregar dispositivo', btnSubmitSave:'Guardar cambios',
    activity:'Actividad', clear:'Limpiar',
    deleteDevice:'Eliminar equipo', delete:'Eliminar',
    wakeAllMsg:'Se enviará un magic packet a los siguientes equipos:',
    sendAll:'Enviar a todos',
    alreadyOnlineTitle:'Equipo ya encendido', alreadyOnlineMsg:'ya responde a ping. ¿Deseas enviar el magic packet de todas formas?',
    sendAnyway:'Enviar igual', close:'Cerrar',
    statRegistered:'Equipos registrados', statWakesSent:'Wakes enviados',
    statLastWake:'Último wake', statSession:'Sesión activa',
    themeLight:'Claro', themeDark:'Oscuro',
    permReadonly:'Solo lectura', permExecute:'Ejecución', permAdmin:'Administrador',
    wakeNoPerms:'Sin permisos de ejecución',
    noDevices:'Sin equipos', noResults:'Sin resultados',
    addFirst:'Agrega el primer equipo →', tryFilter:'Prueba otro filtro.',
    connError:'Sin conexión',
    connErrorSub:'Verifica que server.py esté corriendo.',
    wakeLogEmpty:'Sin registros aún',
    logStarting:'WOL Console iniciando...', logLoaded:' equipo(s) cargado(s)',
    logNoPerms:'Sin permisos de ejecución',
    sessionExpired:'Sesión expirada',
    searchPlaceholder:'Buscar por nombre, MAC, IP...',
    deleteConfirm:(name,mac)=>`¿Eliminar "${name}" (${mac})? No se puede deshacer.`,
    signingIn:'Entrando…',saving:'Guardando…'
  }
};
// Idioma elegido, guardado en el navegador (clave pi-lang) y compartido por todas las páginas. Por defecto, inglés.
// EN: Chosen language, stored in the browser (key pi-lang) and shared by all pages. English by default.
let _lang = localStorage.getItem('pi-lang') || 'en';
var _i18nReady = false;
// Traducción: busca la clave en el idioma activo (admite textos con función para incluir valores).
// EN: Translation: looks the key up in the active language (supports function texts that take values).
function t(k,...args){const v=(LANG[_lang]||LANG.en)[k]||(LANG.en)[k]||k;return typeof v==='function'?v(...args):v;}
// Cambia el idioma, lo recuerda y vuelve a pintar los textos de la página.
// EN: Switch the language, remember it and repaint the page texts.
function setLang(l){
  _lang = l;
  localStorage.setItem('pi-lang', l);
  document.documentElement.lang = l;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const k = el.getAttribute('data-i18n');
    el.textContent = t(k);
  });
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.getAttribute('data-i18n-title')); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
  });
  const si = document.getElementById('search-input');
  if(si) si.placeholder = t('searchPlaceholder');
  ['en','es'].forEach(x => document.getElementById('lang-'+x)?.classList.toggle('active', x===l));
  // Re-render dynamic content only after full script initialization
  if(_i18nReady && typeof renderAll === 'function') renderAll();
}
(()=>{ setLang(_lang); })();

// ── Auth & permissions ─────────────────────────────────
// Sesión actual {username, permissions}. Los botones se muestran u ocultan según el nivel, pero quien decide de verdad es el servidor.
// EN: Current session {username, permissions}. Buttons are shown or hidden by level, but the server is what really decides.
let ME = null;  // { username, permissions: {wol, nut} }

// ¿Puede encender equipos? (nivel «execute» o «admin»).
// EN: Can it wake devices? ("execute" or "admin" level).
function canExecute(){ return ME && ['execute','admin'].includes(ME.permissions?.wol); }
// ¿Puede agregar, editar y borrar equipos? (nivel «admin»).
// EN: Can it add, edit and delete devices? ("admin" level).
function canAdmin()  { return ME && ME.permissions?.wol === 'admin'; }

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
const _NAV_SELF='wol';
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

// Inicio de sesión. La cookie la fija el servidor (HttpOnly): el JavaScript nunca guarda el token.
// EN: Login. The cookie is set by the server (HttpOnly): the JavaScript never stores the token.
async function doLogin(){
  const btn=document.getElementById('btn-l');
  const err=document.getElementById('login-err');
  const u=document.getElementById('l-user').value.trim();
  const p=document.getElementById('l-pass').value;
  err.className='login-err';
  if(!u||!p){err.textContent='Completa todos los campos';err.className='login-err show';return;}
  btn.disabled=true;btn.innerHTML=`<span class="spin">⟳</span> ${t('signingIn')}`;
  try{
    const r=await fetch('api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
    const d=await r.json();
    if(!r.ok||!d.ok){err.textContent=d.error||'Credenciales incorrectas';err.className='login-err show';return;}
    // Cuenta con contraseña por cambiar (admin/admin inicial): se va a la pantalla obligatoria antes de entrar.
    // EN: Account with a password to change (initial admin/admin): go to the mandatory screen before entering.
    if(d.must_change_password){location.href='/admin/change-password?next='+encodeURIComponent(location.pathname);return;}
    if(!d.permissions?.wol||d.permissions.wol==='none'){
      err.textContent='No tienes acceso a WOL Console';err.className='login-err show';return;
    }
    ME=d;
    applyPermissions();
    await initApp();
    const ls=document.getElementById('login-screen');
    ls.style.opacity='0';
    setTimeout(()=>ls.style.display='none',150);
  }catch(e){err.textContent='Error: '+e.message;err.className='login-err show';}
  finally{btn.disabled=false;btn.textContent=t('loginBtn');}
}

// Pregunta al servidor quién es el usuario (api/me). Sin sesión, o sin acceso a WOL, devuelve false y se muestra el login.
// EN: Ask the server who the user is (api/me). Without a session, or without WOL access, it returns false and the login is shown.
async function checkSession(){
  try{
    const r=await fetch('api/me');
    if(!r.ok)return false;
    const d=await r.json();
    if(!d.username||!d.permissions?.wol||d.permissions.wol==='none')return false;
    ME=d;return true;
  }catch{return false;}
}

// Muestra nombre y rol, y para usuarios sin permiso de administrar oculta el formulario y muestra el aviso de solo lectura.
// EN: Show name and role, and for users without admin permission hide the form and show the read-only notice.
function applyPermissions(){
  const _un=String(ME.username||'?');
  document.getElementById('me-name').textContent=_un;
  document.getElementById('avatar').textContent=_un[0].toUpperCase();
  const perm=ME.permissions?.wol||'readonly';
  const LABELS={readonly:t('permReadonly'),execute:t('permExecute'),admin:t('permAdmin')};
  document.getElementById('me-role').textContent=LABELS[perm]||perm;
  renderNav();
  // Mostrar/ocultar según permisos
  if(!canAdmin()){
    document.getElementById('form-card').style.display='none';
    document.getElementById('readonly-banner').className='readonly-banner show';
  }
}

// Cierra la sesión en el servidor y recarga la página.
// EN: Close the session on the server and reload the page.
async function logout(){
  await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  location.reload();
}

// ── State ──────────────────────────────────────────────
// Estado de la pantalla: lista de equipos, filtro, búsqueda, orden y equipo en edición.
// EN: Screen state: device list, filter, search, sort order and the device being edited.
let devices=[],filterTag='ALL',searchQ='',sortCol='name',sortAsc=true,wakeCount=0,lastWakeName=null,editingId=null,sessionStart=Date.now();
// Datos solo del navegador (la última vez que se encendió cada equipo y sus notas); nada de esto va al servidor.
// EN: Browser-only data (when each device was last woken and its notes); none of it goes to the server.
const LOCAL_KEY='wol_meta';
function loadMeta(){try{return JSON.parse(localStorage.getItem(LOCAL_KEY)||'{}')}catch{return{}}}
function saveMeta(m){try{localStorage.setItem(LOCAL_KEY,JSON.stringify(m))}catch{}}
let meta=loadMeta();

let pollTimer=null;
// La lista se refresca sola cada 5 segundos y al volver a la pestaña.
// EN: The list refreshes itself every 5 seconds and when returning to the tab.
const POLL_MS=5000;

// Arranque tras iniciar sesión: relojes, búsqueda, primera carga de equipos y refresco periódico.
// EN: Startup after login: clocks, search, first device load and periodic refresh.
async function initApp(){
  updateClock();setInterval(updateClock,1000);setInterval(updateUptime,1000);
  document.getElementById('search-input').addEventListener('input',e=>{searchQ=e.target.value.trim().toLowerCase();renderTable();});
  log('INFO', t('logStarting'));
  await refreshDevices(true);
  loadNetHosts();
  pollTimer=setInterval(()=>refreshDevices(false), POLL_MS);
  // Refrescar también al volver a la pestaña (vuelve de background/sleep)
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) refreshDevices(false);
  });
}

// Descarga la lista de equipos y repinta. Un error solo se muestra en la primera carga, para no molestar con cortes breves.
// EN: Download the device list and repaint. An error is shown only on the first load, so brief outages do not annoy.
async function refreshDevices(isInitial){
  try{
    const fresh=await apiFetch('api/devices').then(d=>d.devices);
    // Merge preservando estado visual (indicadores de wake en curso) sin perder animaciones
    devices=fresh;
    if(isInitial) log('OK', devices.length + t('logLoaded'));
    renderAll();
  }catch(e){
    if(isInitial){ log('ERR',t('errLoad')+': '+e.message); showConnError(); }
  }
}

// ── API ────────────────────────────────────────────────
// Llamada a la API con manejo común: 401 recarga la página (sesión vencida) y otros errores se convierten en excepción con el mensaje del servidor.
// EN: API call with common handling: 401 reloads the page (expired session) and other errors become an exception with the server's message.
async function apiFetch(url, opts={}){
  const r=await fetch(url,opts);
  if(r.status===401){location.reload();throw new Error(t('sessionExpired'));}
  if(!r.ok){const d=await r.json().catch(()=>({}));throw new Error(d.error||'HTTP '+r.status);}
  return r.json();
}

// ── Render ─────────────────────────────────────────────
// Actualiza estadísticas y tabla.
// EN: Update statistics and table.
function renderAll(){updateStats();renderTable();}
// Aplica etiqueta y búsqueda de texto a la lista.
// EN: Apply the tag and text search to the list.
function filtered(){
  return devices.filter(d=>{
    if(filterTag!=='ALL'&&d.tag!==filterTag)return false;
    if(!searchQ)return true;
    return(d.name+' '+d.mac+' '+(d.ip||'')+' '+d.tag).toLowerCase().includes(searchQ);
  });
}
// Ordena por la columna elegida (nombre, IP, estado…).
// EN: Sort by the chosen column (name, IP, state…).
function sorted(arr){
  return[...arr].sort((a,b)=>{
    let va,vb;
    if(sortCol==='lastWoke'){va=meta[a.id]?.lastWoke||0;vb=meta[b.id]?.lastWoke||0;}
    else{va=(a[sortCol]||'').toString().toLowerCase();vb=(b[sortCol]||'').toString().toLowerCase();}
    if(va<vb)return sortAsc?-1:1;if(va>vb)return sortAsc?1:-1;return 0;
  });
}
// Dibuja la tabla de equipos. Todo texto proveniente de datos pasa por esc().
// EN: Draw the device table. All text coming from data goes through esc().
function renderTable(){
  const tbody=document.getElementById('dev-tbody');
  const list=sorted(filtered());
  document.getElementById('dev-count').textContent=list.length===devices.length?devices.length+(devices.length!==1?' devices':' device'):list.length+' / '+devices.length+' devices';
  if(!list.length){
    tbody.innerHTML='<tr><td colspan="6"><div class="empty"><strong>'+(devices.length?t('noResults'):t('noDevices'))+'</strong>'+(devices.length?t('tryFilter'):t('addFirst'))+'</div></td></tr>';
    return;
  }
  tbody.innerHTML='';
  list.forEach((d,i)=>{
    // Priorizar last_wake del servidor (más preciso) sobre meta local
    const serverTs = d.last_wake ? d.last_wake*1000 : 0;
    const localTs  = meta[d.id]?.lastWoke || 0;
    const lw       = Math.max(serverTs, localTs) || null;
    const lwUser   = d.last_wake_user ? ' · <span style="color:var(--blue);font-size:10px">'+esc(d.last_wake_user)+'</span>' : '';
    const lwText   = lw ? relTime(lw)+lwUser : '<span style="opacity:.3">—</span>';
    const notes    = meta[d.id]?.notes||d.notes||'';
    const tr=document.createElement('tr');
    tr.style.animationDelay=i*18+'ms';
    const canWake=canExecute();
    const canEdit=canAdmin();
    tr.innerHTML=`
      <td class="col-st"><span class="ind" id="ind-${d.id}"></span></td>
      <td><span class="dev-name">${esc(d.name)}</span><span class="dev-mac">${esc(d.mac)}${notes?' · <span style="color:var(--text-dim)">'+esc(notes)+'</span>':''}</span></td>
      <td><span class="tag tag-${d.tag.toLowerCase()}">${esc(d.tag)}</span></td>
      <td class="col-ip">${ipCell(d)}</td>
      <td class="col-lw">${lwText}</td>
      <td class="col-act">
        <button class="btn-wake" id="wake-${d.id}" data-on-click="wakeDevice" data-on-click-args="${jsargs([d.id])}" ${canWake?'':'disabled title="'+esc(t('noPerm'))+'"'}>Wake</button>
        ${canEdit?`<button class="btn-ri e" data-on-click="editDevice" data-on-click-args="${jsargs([d.id])}" title="${esc(t('titEdit'))}">✎</button><button class="btn-ri d" data-on-click="confirmDelete" data-on-click-args="${jsargs([d.id])}" title="${esc(t('titDelete'))}">✕</button>`:''}
      </td>`;
    tbody.appendChild(tr);
  });
}
function ipCell(d){
  const n=d.net;
  if(n&&n.ip&&n.ip!==d.ip)return '<span title="'+esc(t('netIp'))+'" data-nethost="'+esc(n.ip)+'" data-nethost-click="1">'+esc(n.ip)+'</span>'+(d.ip?'<span style="color:var(--text-dim);font-size:10px;display:block;text-decoration:line-through">'+esc(d.ip)+'</span>':'');
  return d.ip?'<span data-nethost="'+esc(d.ip)+'" data-nethost-click="1">'+esc(d.ip)+'</span>':'<span style="opacity:.25">—</span>';
}
// ── Net Monitor: pick a detected host (shared MAC/IP/name) ──
// Integración con Net Monitor: al agregar un equipo se puede elegir uno ya detectado en la red (se copian su MAC, IP y nombre).
// EN: Net Monitor integration: when adding a device you can pick one already detected on the network (its MAC, IP and name are copied).
let netHosts=[];
const NET_TAG={computer:'PC',storage:'NAS'};
async function loadNetHosts(){
  const f=document.getElementById('net-pick-field');if(!f)return;
  try{
    const d=await apiFetch('api/netmonitor/hosts');
    netHosts=d.hosts||[];
    if(!d.available||!netHosts.length||!canAdmin()){f.style.display='none';return;}
    const sel=document.getElementById('f-net');
    sel.innerHTML='<option value="">'+esc(t('fromNetPick'))+'</option>'+netHosts.map((h,i)=>
      '<option value="'+i+'"'+(h.in_wol?' disabled':'')+'>'+esc((h.name||h.ip)+' · '+h.ip+' · '+h.mac)+(h.in_wol?' ('+esc(t('fromNetHave'))+')':'')+'</option>').join('');
    f.style.display='';
  }catch(e){f.style.display='none';}
}
function pickNetHost(i){
  const h=netHosts[parseInt(i)];if(!h)return;
  document.getElementById('f-name').value=(h.name||h.ip).slice(0,40);
  document.getElementById('f-mac').value=h.mac;
  document.getElementById('f-ip').value=h.ip;
  document.getElementById('f-tag').value=NET_TAG[h.device_type]||'OTHER';
}
function updateStats(){
  document.getElementById('st-total').textContent=devices.length;
  document.getElementById('st-wakes').textContent=wakeCount;
  document.getElementById('st-last').textContent=lastWakeName||'—';
}
function showConnError(){
  document.getElementById('dev-tbody').innerHTML='<tr><td colspan="6"><div class="empty"><strong style="color:var(--red)">'+t('connError')+'</strong>'+t('connErrorSub')+'</div></td></tr>';
}
// ── Wake ────────────────────────────────────────────────
// Envía el magic packet. Si el equipo ya responde, abre un aviso y solo reenvía si el usuario confirma (force).
// EN: Send the magic packet. If the device already answers, a notice opens and it resends only if the user confirms (force).
async function wakeDevice(id, force=false){
  if(!canExecute()){toast(t('wakeNoPerms'),true);return;}
  const device=devices.find(d=>d.id===id);if(!device)return;
  const btn=document.getElementById('wake-'+id),ind=document.getElementById('ind-'+id);
  if(btn){btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';}
  if(ind)ind.className='ind waking';
  log('WARN','TX → "'+device.name+'" ['+device.mac+']');
  try{
    const res=await apiFetch('api/wake',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id, force})});
    if(res.already_online && !force){
      // Ya está encendido — preguntar si enviar de todas formas
      if(ind)ind.className='ind';
      if(btn){btn.disabled=!canExecute();btn.textContent='Wake';}
      showAlreadyOnlineModal(id, device.name);
      return;
    }
    wakeCount++;lastWakeName=device.name;
    meta[id]={...meta[id],lastWoke:Date.now()};saveMeta(meta);
    const msg = res.message||t('msgSent',device.name);
    log('OK', msg);
    toast('Magic packet → '+device.name,false);
    if(ind)ind.className='ind sent';
    setTimeout(()=>{if(ind)ind.className='ind';},9000);
    updateStats();renderTable();
  }catch(e){log('ERR','Error WOL: '+e.message);toast(e.message,true);if(ind)ind.className='ind';}
  finally{if(btn){btn.disabled=!canExecute();btn.textContent='Wake';}}
}
function showAlreadyOnlineModal(id, name){
  document.getElementById('aol-name').textContent = name;
  document.getElementById('aol-btn').onclick = ()=>{ closeModals(); wakeDevice(id, true); };
  document.getElementById('aol-overlay').classList.add('show');
}
// Confirmación para encender todos los equipos a la vez.
// EN: Confirmation to wake all devices at once.
function openWakeAll(){
  const list=filtered();
  if(!list.length){toast(t('noVisible'),true);return;}
  document.getElementById('wakeall-list').innerHTML=list.map(d=>'<div>'+esc(d.name)+' <span style="color:var(--text-dim)">'+esc(d.mac)+'</span></div>').join('');
  document.getElementById('wakeall-btn').onclick=async()=>{closeModals();for(const d of list){await wakeDevice(d.id);await sleep(300);}};
  document.getElementById('wakeall-overlay').classList.add('show');
}
// ── Form ────────────────────────────────────────────────
// El mismo formulario sirve para agregar y para editar, según haya un equipo en edición.
// EN: The same form serves to add and to edit, depending on whether a device is being edited.
function submitForm(){if(editingId)saveEdit();else addDevice();}
// Alta de equipo (admin).
// EN: Add a device (admin).
async function addDevice(){
  if(!canAdmin())return;
  const nameEl=document.getElementById('f-name'),macEl=document.getElementById('f-mac'),btn=document.getElementById('btn-submit');
  const{name,mac,ip,port,tag,notes}=readForm();
  [nameEl,macEl].forEach(e=>e.classList.remove('err'));
  if(!name){nameEl.classList.add('err');nameEl.focus();return;}
  if(!mac){macEl.classList.add('err');macEl.focus();return;}
  btn.disabled=true;btn.innerHTML='<span class="spin">⟳</span>';
  try{
    const device=await apiFetch('api/devices',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,mac,ip,port,tag})});
    if(notes){meta[device.device.id]={...meta[device.device.id],notes};saveMeta(meta);}
    devices.push(device.device);resetForm();renderAll();
    log('OK','"'+device.device.name+'" registered');toast(device.device.name+' added',false);
  }catch(e){log('ERR',e.message);toast(e.message,true);if(e.message.toLowerCase().includes('mac'))macEl.classList.add('err');}
  finally{btn.disabled=false;btn.textContent=t('btnSubmitAdd');}
}
function editDevice(id){
  if(!canAdmin())return;
  const d=devices.find(x=>x.id===id);if(!d)return;
  editingId=id;
  document.getElementById('f-id').value=id;
  document.getElementById('f-name').value=d.name;
  document.getElementById('f-mac').value=d.mac;
  document.getElementById('f-ip').value=d.ip||'';
  document.getElementById('f-port').value=d.port;
  document.getElementById('f-tag').value=d.tag;
  document.getElementById('f-notes').value=meta[id]?.notes||d.notes||'';
  document.getElementById('form-title').textContent=t('editMode');
  document.getElementById('edit-banner').classList.add('show');
  document.getElementById('btn-submit').textContent=t('btnSubmitSave');
  document.getElementById('f-name').focus();
}
// Guarda los cambios de un equipo en edición.
// EN: Save the changes of a device being edited.
async function saveEdit(){
  const{name,mac,ip,port,tag,notes}=readForm();
  const nameEl=document.getElementById('f-name'),macEl=document.getElementById('f-mac'),btn=document.getElementById('btn-submit');
  [nameEl,macEl].forEach(e=>e.classList.remove('err'));
  if(!name){nameEl.classList.add('err');nameEl.focus();return;}
  if(!mac){macEl.classList.add('err');macEl.focus();return;}
  btn.disabled=true;btn.innerHTML=`<span class="spin">⟳</span> ${t('saving')}`;
  try{
    const r1=await fetch('api/devices/'+editingId,{method:'DELETE'});
    if(!r1.ok)throw new Error(t('errDelete'));
    const d2=await apiFetch('api/devices',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,mac,ip,port,tag})});
    const updated=d2.device;
    const oldMeta=meta[editingId]||{};delete meta[editingId];
    meta[updated.id]={...oldMeta,notes:notes||''};saveMeta(meta);
    const idx=devices.findIndex(x=>x.id===editingId);
    if(idx!==-1)devices[idx]=updated;else devices=await apiFetch('api/devices').then(d=>d.devices);
    cancelEdit();renderAll();log('OK','Editado: "'+updated.name+'"');toast(updated.name+' actualizado',false);
  }catch(e){log('ERR',e.message);toast(e.message,true);}
  finally{btn.disabled=false;btn.textContent=t('btnSubmitSave');}
}
function cancelEdit(){
  editingId=null;
  document.getElementById('form-title').textContent=t('addDevice');
  document.getElementById('edit-banner').classList.remove('show');
  document.getElementById('btn-submit').textContent=t('btnSubmitAdd');
  resetForm();
}
function readForm(){
  return{name:document.getElementById('f-name').value.trim(),mac:document.getElementById('f-mac').value.trim(),ip:document.getElementById('f-ip').value.trim()||null,port:parseInt(document.getElementById('f-port').value)||9,tag:document.getElementById('f-tag').value,notes:document.getElementById('f-notes').value.trim()};
}
function resetForm(){
  ['f-name','f-mac','f-ip','f-notes'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('f-port').value='9';document.getElementById('f-tag').value='PC';document.getElementById('f-id').value='';
  const fn=document.getElementById('f-net');if(fn)fn.value='';
  if(typeof loadNetHosts==='function')loadNetHosts();
}
// Pide confirmación y borra un equipo (admin).
// EN: Ask for confirmation and delete a device (admin).
function confirmDelete(id){
  if(!canAdmin())return;
  const d=devices.find(x=>x.id===id);if(!d)return;
  document.getElementById('del-msg').textContent=t('deleteConfirm',d.name,d.mac);
  document.getElementById('del-btn').onclick=async()=>{
    closeModals();
    try{
      await fetch('api/devices/'+id,{method:'DELETE'});
      delete meta[id];saveMeta(meta);
      log('WARN','Eliminado: "'+d.name+'"');
      devices=devices.filter(x=>x.id!==id);
      if(editingId===id)cancelEdit();
      renderAll();loadNetHosts();toast(d.name+' eliminado',false);
    }catch(e){log('ERR',e.message);toast(e.message,true);}
  };
  document.getElementById('del-overlay').classList.add('show');
}
// Descarga la lista de equipos como archivo JSON.
// EN: Download the device list as a JSON file.
function exportJSON(){
  const data=devices.map(d=>({...d,notes:meta[d.id]?.notes||'',lastWoke:meta[d.id]?.lastWoke||null}));
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  a.download='wol-devices-'+new Date().toISOString().slice(0,10)+'.json';a.click();
  log('INFO','Exportados '+data.length+' dispositivos');
}
function sortBy(col){
  if(sortCol===col)sortAsc=!sortAsc;else{sortCol=col;sortAsc=true;}
  document.querySelectorAll('thead th').forEach(th=>{th.classList.remove('sorted');const a=th.querySelector('.sa');if(a)a.textContent='↕';});
  const th=document.querySelector('[data-col="'+col+'"]');
  if(th){th.classList.add('sorted');const a=th.querySelector('.sa');if(a)a.textContent=sortAsc?'↑':'↓';}
  renderTable();
}
function setFilter(el){document.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));el.classList.add('active');filterTag=el.dataset.filter;renderTable();}
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
  const pref=t==='system'?(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t;
  document.documentElement.setAttribute('data-theme',pref==='dark'?'dark':'light');
}
(()=>{
  const t=localStorage.getItem('pi-theme')||'system';
  applyTheme(t);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{
    if((localStorage.getItem('pi-theme')||'system')==='system') applyTheme('system');
  });
  setTimeout(()=>{
    ['light','dark','system'].forEach(x=>{
      document.getElementById('theme-'+x)?.classList.toggle('active',x===t);
    });
  },0);
})();

function closeModals(){document.querySelectorAll('.overlay').forEach(o=>o.classList.remove('show'));}
// Escapa HTML antes de insertar texto de usuarios, equipos o la red en la página: evita inyección de código (XSS).
// EN: Escape HTML before inserting text from users, devices or the network into the page: prevents code injection (XSS).
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
// Valor seguro dentro de un handler on*="…": literal JS entre comillas, escapado también para HTML.
function jsa(s){return esc(JSON.stringify(String(s)));}
// Lista de argumentos para data-on-*-args="…" (JSON escapado para HTML).
function jsargs(a){return esc(JSON.stringify(a));}
function relTime(ts){const d=Math.floor((Date.now()-ts)/1000);if(d<60)return t('ago',d+'s');if(d<3600)return t('ago',Math.floor(d/60)+'m');if(d<86400)return t('ago',Math.floor(d/3600)+'h');return new Date(ts).toLocaleDateString((_lang==='es'?'es-CL':'en-GB'),{day:'2-digit',month:'2-digit'});}
function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
function updateClock(){const el=document.getElementById('hclock');if(el)el.textContent=new Date().toTimeString().slice(0,8);}
function updateUptime(){const s=Math.floor((Date.now()-sessionStart)/1000);const el=document.getElementById('st-uptime');if(el)el.textContent=String(Math.floor(s/3600)).padStart(2,'0')+':'+String(Math.floor(s/60)%60).padStart(2,'0')+':'+String(s%60).padStart(2,'0');}
let _tt;
// Aviso emergente breve (error si isErr).
// EN: Short pop-up notice (error if isErr).
function toast(msg,isErr=false){const el=document.getElementById('toast');el.textContent=msg;el.className=isErr?'err':'';void el.offsetWidth;el.classList.add('show');clearTimeout(_tt);_tt=setTimeout(()=>el.classList.remove('show'),3400);}
// Línea en el registro de actividad de la pantalla (INFO, OK, ERR).
// EN: Line in the on-screen activity log (INFO, OK, ERR).
function log(level,msg){const out=document.getElementById('log-out'),ts=new Date().toTimeString().slice(0,8);const el=document.createElement('div');el.className='log-row';el.innerHTML='<span class="lt">'+ts+'</span><span class="lv '+level+'">'+level+'</span><span class="lm">'+esc(msg)+'</span>';out.appendChild(el);out.scrollTop=out.scrollHeight;while(out.children.length>120)out.removeChild(out.firstChild);}
function clearLog(){document.getElementById('log-out').innerHTML='';}
let _wakeLogData = [];
// Muestra el historial de encendidos guardado en el servidor (quién y cuándo).
// EN: Show the wake history stored on the server (who and when).
async function showWakeLog(){
  try{
    const r = await apiFetch('api/wake_log');
    _wakeLogData = r.log || [];
    const tbody = document.getElementById('wl-tbody');
    if(!_wakeLogData.length){
      tbody.innerHTML='<tr><td colspan="4" style="text-align:center;padding:20px;color:var(--text-dim)">'+t('wakeLogEmpty')+'</td></tr>';
    } else {
      tbody.innerHTML = _wakeLogData.map(e=>`
        <tr style="border-bottom:1px solid var(--border)">
          <td style="padding:8px 12px;font-size:12px;font-family:var(--mono);color:var(--text-dim)">${fmtTs(e.ts)}</td>
          <td style="padding:8px 12px;font-size:13px;font-weight:500">${esc(e.device_name)}</td>
          <td style="padding:8px 12px;font-size:11px;font-family:var(--mono);color:var(--text-dim)">${esc(e.mac)}</td>
          <td style="padding:8px 12px;font-size:12px;color:var(--blue)">${esc(e.user||'?')}</td>
        </tr>`).join('');
    }
    document.getElementById('wl-overlay').classList.add('show');
  }catch(e){ toast(t('errHistory')+': '+e.message, true); }
}
function fmtTs(ts){ const d=new Date(ts*1000); return d.toLocaleDateString((_lang==='es'?'es-CL':'en-GB'))+' '+d.toTimeString().slice(0,8); }
_i18nReady = true;
document.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('f-mac').addEventListener('input',function(){let v=this.value.replace(/[^0-9a-fA-F]/g,'');if(v.length>12)v=v.slice(0,12);const pos=this.selectionStart;this.value=(v.match(/.{1,2}/g)||[]).join(':').toUpperCase();try{this.setSelectionRange(pos,pos);}catch{}});
  document.getElementById('l-pass').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeModals();if(editingId)cancelEdit();}if((e.ctrlKey||e.metaKey)&&e.key==='f'){e.preventDefault();document.getElementById('search-input').focus();}});
document.querySelectorAll('.overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)closeModals();}));
// ── Boot ────────────────────────────────────────────────
// Arranque de la página: si hay sesión válida se inicia la aplicación; si no, se muestra el login.
// EN: Page boot: if there is a valid session the app starts; otherwise the login is shown.
(async()=>{
  const ok=await checkSession();
  if(ok){
    applyPermissions();
    await initApp();
    const ls=document.getElementById('login-screen');
    ls.style.opacity='0';
    setTimeout(()=>ls.style.display='none',150);
  } else {document.getElementById('login-screen').style.display='flex';}
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
