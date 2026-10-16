// Sesión actual {username, permissions}.
// EN: Current session {username, permissions}.
let me = null;

// ── i18n ──────────────────────────────────────────────────────────────────────
// Textos de la interfaz en inglés (en) y español (es). t('clave') devuelve el texto del idioma activo; si falta la clave en español, usa el inglés. Para agregar un idioma basta otro bloque con las mismas claves.
// EN: Interface texts in English (en) and Spanish (es). t('key') returns the text for the active language; if a Spanish key is missing, it falls back to English. Adding a language only takes another block with the same keys.
const LANG = {
  en: {
    loginTitle:'Admin access', loginSub:'Only administrators can access.',
    loginUser:'Username', loginPass:'Password', loginBtn:'Sign in',
    loginFill:'Fill in all fields', loginErr:'Invalid credentials', loginEntering:'Signing in…',
    navLabel:'Navigation', dragHandle:'Drag',
    userRole:'Administrator',
    logoutTitle:'Sign out',
    topbarTitle:'User management',
    statTotal:'Total users', statAdmins:'Administrators', statReadonly:'Read-only',
    cardTitle:'System users', btnNewUser:'New user',
    colUser:'User', colWOL:'WOL', colUPS:'UPS Monitor', colNET:'Net Monitor', colPVE:'Proxmox', colStatus:'Status', colCreated:'Created', colActions:'Actions',
    drawerNew:'New user', drawerEdit:'Edit — ',
    fieldUsername:'Username', fieldUsernameHint:'2-32 alphanumeric chars, dash or underscore',
    fieldPassword:'Password', fieldPasswordHint:'Minimum 8 characters',
    fieldMustChange:'Require password change on next login',
    permsLabel:'Permissions',
    permNone:'No access', permReadonly:'Read only', permExecute:'Execute', permAdmin:'Administrator',
    permHelpNone:'cannot access the dashboard',
    permHelpReadonly:'can view data, cannot execute actions',
    permHelpExecute:'can view and execute (e.g. Wake)',
    permHelpAdmin:'full access + device management',
    fieldNewPw:'New password (leave blank to keep current)',
    fieldNewPwPlaceholder:'New password',
    fieldCurPw:'Current password (required to change your own)', curPwNeeded:'Enter your current password to change it',
    btnCancel:'Cancel', btnCreate:'Create user', btnSave:'Save changes',
    modalDeleteTitle:'Delete user', modalDeleteBtn:'Delete',
    mustChangeBadge:'Change pwd',
    hlTitle:'System health', hl_ok:'All healthy', hl_degraded:'Degraded', hl_fail:'Failing', hlSystem:'system', hlDown:'Service not answering', hlUptime:'Running for',
    tpTitle:'Backup & restore', tpUpload:'Upload backup', tpCreate:'Create backup',
    tpHint:'Back up users, WOL devices, UPS servers and history, Net Monitor, Proxmox and the NUT configuration. To move to a new installation: install the package, sign in with the default user, upload the backup here and press Restore.',
    tpColName:'Backup', tpColType:'Type', tpColSize:'Size', tpColDate:'Date', tpEmpty:'No backups yet.',
    tpKindBackup:'Created here', tpKindUpload:'Uploaded',
    tpDownload:'Download', tpCheck:'Verify', tpRestore:'Restore', tpDelete:'Delete',
    tpCreating:'Creating…', tpCreated:'Backup created', tpFailed:'Operation failed',
    tpUploading:p=>`Uploading ${p}%`, tpUploaded:'Backup uploaded', tpTooBig:mb=>`File too large (limit ${mb} MB)`,
    tpChecking:'Verifying…', tpCheckOk:'Backup is valid', tpCheckBad:'Backup is NOT valid',
    tpNotAvailable:'teleporter.sh is not installed on this system.',
    tpRestoreTitle:'Restore backup',
    tpRestoreWarn:'This replaces the current users, devices, history and settings with the ones in the backup. A safety snapshot of the current state is saved first. The panel restarts and you will have to sign in again. The NUT and nginx configuration are not restored from here (command line only: teleporter restore --nut / --nginx).',
    tpOptOk:'I understand that the current data will be overwritten.',
    tpRestoreBtn:'Restore', tpConfirmDelete:n=>`Delete the backup "${n}"?`, tpDeleted:'Backup deleted',
    tpProgTitle:'Restoring…', tpProgMsg:'Do not close this page. The services restart during the restore.',
    tpProgOk:'Restore completed', tpProgOkMsg:'Sign in again with the users from the backup.',
    tpProgErr:'Restore finished with errors', tpProgErrMsg:'Review the log below. A snapshot of the previous state is in /var/backups/pi-console/.',
    tpProgFail:'Restore failed', tpProgFailMsg:'Nothing was lost: the services were restarted. Review the log below.',
    tpProgRestarted:'Panel restarted', tpProgRestartedMsg:'The restore finished and the panel restarted. Sign in again with the users from the backup.',
    tpProgDone:'Continue',
    toastCreated: u=>`User ${u} created`,
    toastUpdated: u=>`User ${u} updated`,
    toastDeleted:'User deleted',
    toastErrPw:'Error changing password',
    confirmDelete: u=>`Delete user "${u}"? This action cannot be undone.`,
    editTitle: u=>`Edit — ${u}`,
  },
  es: {
    loginTitle:'Acceso de administrador', loginSub:'Solo administradores pueden acceder.',
    loginUser:'Usuario', loginPass:'Contraseña', loginBtn:'Entrar',
    loginFill:'Completa todos los campos', loginErr:'Credenciales incorrectas', loginEntering:'Entrando…',
    navLabel:'Navegación', dragHandle:'Arrastrar',
    userRole:'Administrador',
    logoutTitle:'Cerrar sesión',
    topbarTitle:'Gestión de usuarios',
    statTotal:'Usuarios totales', statAdmins:'Administradores', statReadonly:'Solo lectura',
    cardTitle:'Usuarios del sistema', btnNewUser:'Nuevo usuario',
    colUser:'Usuario', colWOL:'WOL', colUPS:'UPS Monitor', colNET:'Net Monitor', colPVE:'Proxmox', colStatus:'Estado', colCreated:'Creado', colActions:'Acciones',
    drawerNew:'Nuevo usuario', drawerEdit:'Editar — ',
    fieldUsername:'Nombre de usuario', fieldUsernameHint:'2-32 caracteres alfanuméricos, guion o guion bajo',
    fieldPassword:'Contraseña', fieldPasswordHint:'Mínimo 8 caracteres',
    fieldMustChange:'Solicitar cambio de contraseña en el próximo login',
    permsLabel:'Permisos',
    permNone:'Sin acceso', permReadonly:'Solo lectura', permExecute:'Ejecución', permAdmin:'Administrador',
    permHelpNone:'no puede entrar al dashboard',
    permHelpReadonly:'puede ver datos, no ejecutar acciones',
    permHelpExecute:'puede ver y ejecutar (ej: Wake)',
    permHelpAdmin:'acceso total + gestión de dispositivos',
    fieldNewPw:'Nueva contraseña (dejar vacío para no cambiar)',
    fieldNewPwPlaceholder:'Nueva contraseña',
    fieldCurPw:'Contraseña actual (obligatoria para cambiar la tuya)', curPwNeeded:'Escribe tu contraseña actual para cambiarla',
    btnCancel:'Cancelar', btnCreate:'Crear usuario', btnSave:'Guardar cambios',
    modalDeleteTitle:'Eliminar usuario', modalDeleteBtn:'Eliminar',
    mustChangeBadge:'Cambiar pwd',
    hlTitle:'Salud del sistema', hl_ok:'Todo bien', hl_degraded:'Degradado', hl_fail:'Con fallas', hlSystem:'sistema', hlDown:'El servicio no responde', hlUptime:'Activo hace',
    tpTitle:'Respaldo y restauración', tpUpload:'Subir respaldo', tpCreate:'Crear respaldo',
    tpHint:'Respalda usuarios, dispositivos WOL, servidores UPS e historial, Net Monitor, Proxmox y la configuración de NUT. Para migrar a una instalación nueva: instala el paquete, entra con el usuario por defecto, sube el respaldo aquí y pulsa Restaurar.',
    tpColName:'Respaldo', tpColType:'Tipo', tpColSize:'Tamaño', tpColDate:'Fecha', tpEmpty:'Aún no hay respaldos.',
    tpKindBackup:'Creado aquí', tpKindUpload:'Subido',
    tpDownload:'Descargar', tpCheck:'Verificar', tpRestore:'Restaurar', tpDelete:'Eliminar',
    tpCreating:'Creando…', tpCreated:'Respaldo creado', tpFailed:'La operación falló',
    tpUploading:p=>`Subiendo ${p}%`, tpUploaded:'Respaldo subido', tpTooBig:mb=>`Archivo demasiado grande (límite ${mb} MB)`,
    tpChecking:'Verificando…', tpCheckOk:'El respaldo es válido', tpCheckBad:'El respaldo NO es válido',
    tpNotAvailable:'teleporter.sh no está instalado en este sistema.',
    tpRestoreTitle:'Restaurar respaldo',
    tpRestoreWarn:'Esto reemplaza los usuarios, dispositivos, historial y ajustes actuales por los del respaldo. Antes se guarda un snapshot de seguridad del estado actual. El panel se reinicia y tendrás que iniciar sesión de nuevo. La configuración de NUT y nginx no se restaura desde aquí (solo por consola: teleporter restore --nut / --nginx).',
    tpOptOk:'Entiendo que se sobrescribirán los datos actuales.',
    tpRestoreBtn:'Restaurar', tpConfirmDelete:n=>`¿Eliminar el respaldo "${n}"?`, tpDeleted:'Respaldo eliminado',
    tpProgTitle:'Restaurando…', tpProgMsg:'No cierres esta página. Los servicios se reinician durante la restauración.',
    tpProgOk:'Restauración completada', tpProgOkMsg:'Inicia sesión de nuevo con los usuarios del respaldo.',
    tpProgErr:'Restauración terminada con errores', tpProgErrMsg:'Revisa el registro. El snapshot del estado anterior está en /var/backups/pi-console/.',
    tpProgFail:'La restauración falló', tpProgFailMsg:'No se perdió nada: los servicios se reiniciaron. Revisa el registro.',
    tpProgRestarted:'Panel reiniciado', tpProgRestartedMsg:'La restauración terminó y el panel se reinició. Inicia sesión de nuevo con los usuarios del respaldo.',
    tpProgDone:'Continuar',
    toastCreated: u=>`Usuario ${u} creado`,
    toastUpdated: u=>`Usuario ${u} actualizado`,
    toastDeleted:'Usuario eliminado',
    toastErrPw:'Error cambiando contraseña',
    confirmDelete: u=>`¿Eliminar al usuario "${u}"? Esta acción no se puede deshacer.`,
    editTitle: u=>`Editar — ${u}`,
  }
};
// Idioma elegido, guardado en el navegador (clave pi-lang) y compartido por todas las páginas. Por defecto, inglés.
// EN: Chosen language, stored in the browser (key pi-lang) and shared by all pages. English by default.
let _lang = localStorage.getItem('pi-lang') || 'en';
// Traducción: busca la clave en el idioma activo (admite textos con función para incluir valores).
// EN: Translation: looks the key up in the active language (supports function texts that take values).
function t(k,...args){ const v=(LANG[_lang]||LANG.en)[k]||(LANG.en)[k]||k; return typeof v==='function'?v(...args):v; }
// Cambia el idioma, lo recuerda y vuelve a pintar los textos de la página.
// EN: Switch the language, remember it and repaint the page texts.
function setLang(l){
  _lang=l; localStorage.setItem('pi-lang',l); document.documentElement.lang=l;
  document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=t(el.getAttribute('data-i18n')));
  ['en','es'].forEach(x=>document.getElementById('lang-'+x)?.classList.toggle('active',x===l));
  // Update logout button title
  document.getElementById('btn-logout').title = t('logoutTitle');
  try{tpRender();}catch(e){}
  // Update new-pw placeholder
  const npw = document.getElementById('d-new-pw');
  if(npw) npw.placeholder = t('fieldNewPwPlaceholder');
  // Update password placeholder
  const dpw = document.getElementById('d-password');
  if(dpw) dpw.placeholder = t('fieldPasswordHint');
  // Update permission selects
  ['d-wol','d-nut','d-net','d-pve'].forEach(id=>{
    const sel = document.getElementById(id); if(!sel) return;
    const val = sel.value;
    sel.innerHTML = ['none','readonly','execute','admin'].map(v=>`<option value="${v}"${val===v?' selected':''}>${t('perm'+v.charAt(0).toUpperCase()+v.slice(1))}</option>`).join('');
  });
  // Update perm help box
  updatePermHelpBox();
  // Update drawer title/button if open
  const dTitle = document.getElementById('drawer-title');
  const dMode  = document.getElementById('d-mode');
  const dOrig  = document.getElementById('d-username-orig');
  if(dTitle && dMode){
    if(dMode.value==='create') dTitle.textContent=t('drawerNew');
    else if(dMode.value==='edit' && dOrig.value) dTitle.textContent=t('editTitle',dOrig.value);
  }
  const bSave = document.getElementById('btn-save');
  if(bSave && dMode){
    bSave.textContent = dMode.value==='edit' ? t('btnSave') : t('btnCreate');
  }
}
// Texto de ayuda que explica qué significa cada nivel de permiso (cambia con el idioma).
// EN: Help text explaining what each permission level means (changes with the language).
function updatePermHelpBox(){
  const box = document.getElementById('perm-help-box');
  if(!box) return;
  box.innerHTML =
    `<strong style="color:var(--text-mid)">${t('permNone')}</strong> — ${t('permHelpNone')}<br>`+
    `<strong style="color:var(--text-mid)">${t('permReadonly')}</strong> — ${t('permHelpReadonly')}<br>`+
    `<strong style="color:var(--text-mid)">${t('permExecute')}</strong> — ${t('permHelpExecute')}<br>`+
    `<strong style="color:var(--text-mid)">${t('permAdmin')}</strong> — ${t('permHelpAdmin')}`;
}
(()=>{ setLang(_lang); updatePermHelpBox(); })();

// ── Nav reordenable ───────────────────────────────────────────────────────────
// Barra lateral común: los mismos accesos en todas las páginas. El usuario puede reordenarlos arrastrando (el orden se guarda en el navegador, clave pi-nav-order). «Admin» solo se muestra a administradores.
// EN: Common sidebar: the same links on every page. The user can reorder them by dragging (the order is stored in the browser, key pi-nav-order). "Admin" is shown to administrators only.
const _NAV_ITEMS=[
  {id:'overview', href:'/overview/', label:'Overview', svg:'<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>'},
  {id:'nut',   href:'/nut/',   label:'UPS Monitor', svg:'<path d="M5 9V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v4"/><rect x="3" y="9" width="18" height="11" rx="2"/><line x1="12" y1="13" x2="12" y2="16"/>'},
  {id:'net',   href:'/net/',   label:'Net Monitor', svg:'<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>'},
  {id:'pve',   href:'/pve/',   label:'Proxmox',     svg:'<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>'},
  {id:'wol',   href:'/wol/',   label:'WOL Console', svg:'<polygon points="13,2 3,14 12,14 11,22 21,10 12,10"/>'},
  {id:'admin', href:'/admin/', label:'Admin Panel', svg:'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'},
];
// Identificador de esta página en la barra lateral (se marca como activa).
// EN: Identifier of this page in the sidebar (shown as active).
const _NAV_SELF='admin';
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
  const order=_navOrder();
  wrap.innerHTML='';
  order.forEach(id=>{
    const item=_NAV_ITEMS.find(i=>i.id===id);if(!item)return;
    const isSelf=item.id===_NAV_SELF;
    const a=document.createElement('a');
    a.className='nav-item nav-drag-item'+(isSelf?' active':'');
    a.href=isSelf?'#':item.href;a.dataset.navId=item.id;a.draggable=true;
    a.innerHTML=`<span class="nav-drag-handle" title="${t('dragHandle')}">⠿</span><svg viewBox="0 0 24 24">${item.svg}</svg>${item.label}`;
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
// Admin siempre ve todos los items — renderizar inmediatamente
renderNav();

// ── Theme ──────────────────────────────────────────────
// Elige el tema (claro, oscuro o automático según el sistema) y lo recuerda (clave pi-theme).
// EN: Choose the theme (light, dark or automatic following the system) and remember it (key pi-theme).
function setTheme(th){
  localStorage.setItem('pi-theme',th);
  const dark=th==='dark'||(th==='system'&&matchMedia('(prefers-color-scheme:dark)').matches);
  document.documentElement.setAttribute('data-theme',dark?'dark':'light');
  ['light','dark','system'].forEach(x=>document.getElementById('theme-'+x)?.classList.toggle('active',x===th));
}
(()=>{setTheme(localStorage.getItem('pi-theme')||'system');})();

// ── Login ──────────────────────────────────────────────
document.getElementById('l-pass').addEventListener('keydown', e => { if(e.key==='Enter') doLogin(); });

// Inicio de sesión. La cookie la fija el servidor (HttpOnly): el JavaScript nunca guarda el token.
// EN: Login. The cookie is set by the server (HttpOnly): the JavaScript never stores the token.
async function doLogin() {
  const btn = document.getElementById('btn-l');
  const err = document.getElementById('login-err');
  const u   = document.getElementById('l-user').value.trim();
  const p   = document.getElementById('l-pass').value;
  err.className = 'login-err';
  if (!u || !p) { err.textContent=t('loginFill'); err.className='login-err show'; return; }
  btn.disabled = true; btn.innerHTML = `<span class="spin">⟳</span> ${t('loginEntering')}`;
  try {
    const r = await fetch('api/login', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({username:u, password:p})
    });
    const d = await r.json();
    if (!r.ok || !d.ok) { err.textContent = d.error||t('loginErr'); err.className='login-err show'; return; }
    // Contraseña por cambiar (admin/admin inicial): pantalla obligatoria antes de entrar.
    // EN: Password to change (initial admin/admin): mandatory screen before entering.
    if (d.must_change_password) { location.href = 'change-password?next=' + encodeURIComponent(location.pathname); return; }
    await loadMe();
    await loadUsers();
    document.getElementById('login-screen').style.display = 'none';
  } catch(e) {
    err.textContent = 'Error: '+e.message; err.className='login-err show';
  } finally {
    btn.disabled=false; btn.textContent=t('loginBtn');
  }
}

// Recarga los datos de la sesión actual.
// EN: Reload the current session data.
async function loadMe() {
  const r = await fetch('api/me');
  if (!r.ok) return;
  me = await r.json();
  if (!me.username) return;
  document.getElementById('me-name').textContent = me.username;
  document.getElementById('avatar').textContent  = me.username[0].toUpperCase();
}

// Cierra la sesión en el servidor y recarga la página.
// EN: Close the session on the server and reload the page.
async function logout() {
  await fetch('api/logout', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
  location.reload();
}

// ── Users ──────────────────────────────────────────────
// Descarga la lista de usuarios y repinta tabla y estadísticas.
// EN: Download the user list and repaint the table and statistics.
async function loadUsers() {
  const r = await fetch('api/users');
  if (!r.ok) { if(r.status===401) location.reload(); return; }
  const d = await r.json();
  const users = d.users || [];
  renderUsers(users);
  updateStats(users);
  tpLoad();
  hlLoad(); if (!window._hlTimer) window._hlTimer = setInterval(hlLoad, 30000);
}

// ── System health ───────────────────────────────────────
// SALUD DEL SISTEMA: tarjetas con el estado de cada módulo (datos de /api/health). HL_DESC explica en palabras simples qué comprueba cada chequeo.
// EN: SYSTEM HEALTH: cards with the state of each module (data from /api/health). HL_DESC explains in plain words what each check verifies.
const HL_NAMES = {wol:'WOL Console', nut:'UPS Monitor', net:'Net Monitor', pve:'Proxmox', overview:'Overview'};
const HL_DESC = {
  en:{users:'User database (users.json) is readable and has accounts', sessions:'Session file is readable and its folder writable', disk:'Free disk space (warns below 100 MB, fails below 5 MB)',
      teleporter:'Backup tool (teleporter.sh) is installed', power:'Raspberry Pi power supply: no under-voltage or throttling (shown only on a Raspberry Pi)', devices:'Device list file is readable and writable', wake_log:'Wake log file is readable and writable',
      net_monitor:'Net Monitor host list can be read (optional)', network:'This machine has a LAN address for magic packets',
      servers_file:'UPS server list file is readable and writable', database:'History database opens and is not locked', history_write:'Buffered history rows are being written to disk',
      pollers:'Background threads that read the data are alive', upsd:'Every NUT server answers', history_fresh:'Recent readings are really stored in the history',
      hosts_file:'Host table file is readable and writable', config_file:'Configuration file is readable and writable', scanner:'The scan is not stuck', auto_scan:'Automatic scan timer is armed and scans are recent',
      clusters_file:'Cluster list file is readable and writable', clusters:'Every Proxmox cluster answers with fresh data', events:'Event timeline file is readable and its folder writable',
      wol:'WOL Console service', nut:'UPS Monitor service', net:'Net Monitor service', pve:'Proxmox service', overview:'Overview service'},
  es:{users:'Base de usuarios (users.json) legible y con cuentas', sessions:'Archivo de sesiones legible y carpeta escribible', disk:'Espacio libre en disco (avisa bajo 100 MB, falla bajo 5 MB)',
      teleporter:'Herramienta de respaldo (teleporter.sh) instalada', power:'Fuente de la Raspberry Pi: sin subtensión ni limitación (solo se muestra en una Raspberry Pi)', devices:'Archivo de dispositivos legible y escribible', wake_log:'Archivo del registro de encendidos legible y escribible',
      net_monitor:'Se puede leer la lista de hosts de Net Monitor (opcional)', network:'Este equipo tiene dirección LAN para los magic packets',
      servers_file:'Archivo de servidores UPS legible y escribible', database:'La base de historial abre y no está bloqueada', history_write:'Las filas de historial en memoria se escriben a disco',
      pollers:'Los hilos que leen los datos están vivos', upsd:'Todos los servidores NUT responden', history_fresh:'Las lecturas recientes realmente quedan guardadas en el historial',
      hosts_file:'Archivo de hosts legible y escribible', config_file:'Archivo de configuración legible y escribible', scanner:'El escaneo no está trabado', auto_scan:'El temporizador de auto-escaneo está armado y los escaneos son recientes',
      clusters_file:'Archivo de clusters legible y escribible', clusters:'Todos los clusters Proxmox responden con datos frescos', events:'Archivo de la línea de tiempo legible y carpeta escribible',
      wol:'Servicio WOL Console', nut:'Servicio UPS Monitor', net:'Servicio Net Monitor', pve:'Servicio Proxmox', overview:'Servicio Resumen'}
};
const _hlOpen = new Set();
// Consulta /api/health y arma una tarjeta por módulo más la del propio panel (usuarios, sesiones, disco, respaldo y fuente de la Pi). Cada tarjeta se despliega para ver cada chequeo y recuerda si estaba abierta entre refrescos.
// EN: Query /api/health and build one card per module plus the panel's own (users, sessions, disk, backup and Pi power supply). Each card expands to show each check and remembers whether it was open between refreshes.
async function hlLoad() {
  try {
    const r = await fetch('api/health', {cache:'no-store'});
    const d = await r.json();
    const badge = document.getElementById('hl-badge');
    badge.className = 'hl-badge ' + (d.status === 'ok' ? '' : d.status);
    badge.textContent = t('hl_' + d.status);
    const grid = document.getElementById('hl-grid'); grid.innerHTML = '';
    const esc = x => String(x).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
    const worst = cs => Object.values(cs).some(v=>v.level==='fail') ? 'fail' : Object.values(cs).some(v=>v.level==='warn') ? 'warn' : 'ok';
    const desc = k => (HL_DESC[_lang]||HL_DESC.en)[k] || '';
    const item = (id, title, level, checks, note) => {
      const el = document.createElement('div'); el.className = 'hl-item' + (_hlOpen.has(id) ? ' open' : '');
      const bad = Object.entries(checks||{}).filter(([k,v]) => v.level !== 'ok');
      const rows = Object.entries(checks||{}).map(([k,v]) =>
        `<div class="hl-row"><span class="hl-dot ${v.level==='ok'?'':v.level}"></span><div><div class="hl-ck">${esc(k)}</div>` +
        (desc(k) ? `<div class="hl-cd">${esc(desc(k))}</div>` : '') +
        (v.detail ? `<div class="hl-cv">${esc(v.detail)}</div>` : '') + `</div></div>`).join('');
      el.innerHTML = `<div class="hl-top" tabindex="0" role="button" aria-expanded="${_hlOpen.has(id)}"><span class="hl-dot ${level==='ok'?'':level}"></span>${esc(title)}<span class="hl-chev">▾</span></div>` +
        (bad.length ? `<div class="hl-det">${bad.map(([k,v])=>esc(k + (v.detail ? ': ' + v.detail : ''))).join('<br>')}</div>` : '') +
        `<div class="hl-all">${note ? `<div class="hl-cv">${esc(note)}</div>` : ''}${rows}</div>`;
      const toggle = () => { _hlOpen.has(id) ? _hlOpen.delete(id) : _hlOpen.add(id); el.classList.toggle('open'); el.firstChild.setAttribute('aria-expanded', _hlOpen.has(id)); };
      el.firstChild.addEventListener('click', toggle);
      el.firstChild.addEventListener('keydown', e => { if (e.key==='Enter' || e.key===' ') { e.preventDefault(); toggle(); } });
      grid.appendChild(el);
    };
    const own = {}; for (const k of ['users','sessions','disk','teleporter','power']) if (d.checks[k]) own[k] = d.checks[k];
    item('admin', 'Admin / ' + t('hlSystem'), worst(own), own);
    for (const m of Object.keys(HL_NAMES)) {
      const mh = (d.modules||{})[m];
      if (!mh) { item(m, HL_NAMES[m], 'fail', {[m]: {level:'fail', detail:t('hlDown')}}); continue; }
      const lvl = mh.status === 'ok' ? 'ok' : mh.status === 'degraded' ? 'warn' : 'fail';
      item(m, HL_NAMES[m], lvl, mh.checks, t('hlUptime') + ' ' + hlDur(mh.uptime));
    }
  } catch(e) { /* panel keeps its last state */ }
}
// Segundos a texto corto (días, horas, minutos).
// EN: Seconds to short text (days, hours, minutes).
function hlDur(s) { s = s|0; const d = Math.floor(s/86400), h = Math.floor(s%86400/3600), m = Math.floor(s%3600/60);
  return d ? d+'d '+h+'h' : h ? h+'h '+m+'m' : m+'m '+(s%60)+'s'; }

// Contadores de la cabecera: total de usuarios y administradores.
// EN: Header counters: total users and administrators.
function updateStats(users) {
  document.getElementById('st-total').textContent   = users.length;
  document.getElementById('st-admins').textContent  = users.filter(u=>u.permissions.wol==='admin'||u.permissions.nut==='admin').length;
  document.getElementById('st-readonly').textContent= users.filter(u=>u.permissions.wol==='readonly'&&u.permissions.nut==='readonly').length;
}

// Tabla de usuarios con una columna por módulo (WOL, UPS, Net, Proxmox) y acciones de editar y borrar.
// EN: User table with a column per module (WOL, UPS, Net, Proxmox) and edit and delete actions.
function renderUsers(users) {
  const tbody = document.getElementById('users-tbody');
  tbody.innerHTML = '';
  const locale = _lang === 'es' ? 'es-CL' : 'en-US';
  users.forEach(u => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="uname">${esc(u.username)}</span></td>
      <td data-label="${esc(t('colWOL'))}">${permBadge(u.permissions.wol)}</td>
      <td data-label="${esc(t('colUPS'))}">${permBadge(u.permissions.nut)}</td>
      <td data-label="${esc(t('colNET'))}">${permBadge(u.permissions.net)}</td>
      <td data-label="${esc(t('colPVE'))}">${permBadge(u.permissions.pve)}</td>
      <td data-label="${esc(t('colStatus'))}">${u.must_change_password ? `<span class="must-change">${t('mustChangeBadge')}</span>` : '<span style="font-size:11px;color:var(--text-dim)">—</span>'}</td>
      <td data-label="${esc(t('colCreated'))}"><span class="ucreated">${u.created ? new Date(u.created*1000).toLocaleDateString(locale) : '—'}</span></td>
      <td class="col-actions">
        <button class="btn-ri edit" data-on-click="editUser" data-on-click-args="${jsargs([u])}" title="Edit">✎</button>
        ${u.username !== me?.username
          ? `<button class="btn-ri del" data-on-click="confirmDelete" data-on-click-args="${jsargs([u.username])}" title="Delete">✕</button>`
          : '<span style="width:30px;display:inline-block"></span>'}
      </td>`;
    tbody.appendChild(tr);
  });
}

// Etiqueta de color para el nivel de permiso.
// EN: Colored badge for the permission level.
function permBadge(perm) {
  const labels = {admin:t('permAdmin'),execute:t('permExecute'),readonly:t('permReadonly'),none:t('permNone')};
  return `<span class="perm-badge perm-${perm||'none'}">${labels[perm]||'—'}</span>`;
}

// ── Drawer ─────────────────────────────────────────────
// Abre el cajón lateral para crear un usuario o editar uno existente (el nombre no se puede cambiar al editar).
// EN: Open the side drawer to create a user or edit an existing one (the name cannot be changed when editing).
function openDrawer(user) {
  const isEdit = !!user;
  document.getElementById('d-mode').value          = isEdit ? 'edit' : 'create';
  document.getElementById('d-username-orig').value = isEdit ? user.username : '';
  document.getElementById('d-username').value      = isEdit ? user.username : '';
  document.getElementById('d-password').value      = '';
  document.getElementById('d-must-change').checked = isEdit ? user.must_change_password : false;

  // Rebuild selects with translated options at current perm values
  ['d-wol','d-nut','d-net','d-pve'].forEach(id=>{
    const sel = document.getElementById(id); if(!sel) return;
    const key = id.slice(2), defs = {wol:'execute', nut:'readonly', net:'none', pve:'none'};
    const val = isEdit ? (user.permissions[key]||'none') : defs[key];
    sel.innerHTML = ['none','readonly','execute','admin'].map(v=>`<option value="${v}"${val===v?' selected':''}>${t('perm'+v.charAt(0).toUpperCase()+v.slice(1))}</option>`).join('');
  });

  document.getElementById('d-new-pw').value = '';
  document.getElementById('d-new-pw').placeholder = t('fieldNewPwPlaceholder');
  document.getElementById('d-cur-pw').value = '';
  // Para cambiar la PROPIA contraseña se pide la actual.
  // EN: To change one's OWN password the current one is asked for.
  document.getElementById('field-cur-pw').style.display = (isEdit && me && user.username === me.username) ? '' : 'none';

  document.getElementById('drawer-title').textContent  = isEdit ? t('editTitle', user.username) : t('drawerNew');
  document.getElementById('btn-save').textContent       = isEdit ? t('btnSave') : t('btnCreate');
  document.getElementById('field-username').style.display  = isEdit ? 'none' : '';
  document.getElementById('field-password').style.display  = isEdit ? 'none' : '';
  document.getElementById('field-must-change').style.display = isEdit ? 'none' : '';
  document.getElementById('field-change-pw').style.display  = isEdit ? '' : 'none';

  updatePermHelpBox();
  document.getElementById('drawer-overlay').classList.add('show');
}

function editUser(u) { openDrawer(u); }

function closeDrawer() {
  document.getElementById('drawer-overlay').classList.remove('show');
}

// Crea o actualiza: alta con contraseña y los cuatro niveles; edición cambia los niveles y, si se escribió una contraseña nueva, también la contraseña (lo que cierra las sesiones de ese usuario).
// EN: Create or update: creation takes a password and the four levels; editing changes the levels and, if a new password was typed, the password too (which closes that user's sessions).
async function saveUser() {
  const mode = document.getElementById('d-mode').value;
  const btn  = document.getElementById('btn-save');
  btn.disabled = true; btn.innerHTML = '<span class="spin">⟳</span>';

  try {
    if (mode === 'create') {
      const uname = document.getElementById('d-username').value.trim();
      const pwd   = document.getElementById('d-password').value;
      const wol   = document.getElementById('d-wol').value;
      const nut   = document.getElementById('d-nut').value;
      const net   = document.getElementById('d-net').value;
      const pve   = document.getElementById('d-pve').value;
      const must  = document.getElementById('d-must-change').checked;
      if (!uname || !pwd) { toast(t('loginFill'), true); return; }
      const r = await fetch('api/users', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({username:uname, password:pwd, wol_permission:wol, nut_permission:nut, net_permission:net, pve_permission:pve, must_change_password:must})
      });
      const d = await r.json();
      if (!r.ok) { toast(d.error||'Error', true); return; }
      toast(t('toastCreated', uname), false);
    } else {
      const uorig = document.getElementById('d-username-orig').value;
      const wol   = document.getElementById('d-wol').value;
      const nut   = document.getElementById('d-nut').value;
      const net   = document.getElementById('d-net').value;
      const pve   = document.getElementById('d-pve').value;
      const newPw = document.getElementById('d-new-pw').value;
      // Actualizar permisos
      const r = await fetch('api/users/'+uorig, {
        method: 'PUT', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({wol_permission:wol, nut_permission:nut, net_permission:net, pve_permission:pve})
      });
      const d = await r.json();
      if (!r.ok) { toast(d.error||'Error', true); return; }
      // Cambiar contraseña si se ingresó
      if (newPw) {
        const curPw = document.getElementById('d-cur-pw').value;
        if (me && uorig === me.username && !curPw) { toast(t('curPwNeeded'), true); return; }
        const r2 = await fetch('api/change_password', {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({username:uorig, new_password:newPw, current_password:curPw})
        });
        const d2 = await r2.json();
        if (!r2.ok) { toast(d2.error||t('toastErrPw'), true); return; }
      }
      toast(t('toastUpdated', uorig), false);
    }
    closeDrawer(); await loadUsers();
  } catch(e) { toast(e.message, true); }
  finally { btn.disabled=false; btn.textContent= mode==='create'?t('btnCreate'):t('btnSave'); }
}

// ── Delete ─────────────────────────────────────────────
// Pide confirmación antes de borrar un usuario.
// EN: Ask for confirmation before deleting a user.
function confirmDelete(username) {
  document.getElementById('del-msg').textContent = t('confirmDelete', username);
  document.getElementById('del-btn').onclick = async () => {
    closeModals();
    const r = await fetch('api/users/'+username, {method:'DELETE'});
    const d = await r.json();
    if (!r.ok) { toast(d.error||'Error', true); return; }
    toast(t('toastDeleted'), false);
    await loadUsers();
  };
  document.getElementById('del-overlay').classList.add('show');
}

function closeModals() { document.querySelectorAll('.overlay:not(.noclose)').forEach(o=>o.classList.remove('show')); }

// ── Teleporter (backup & restore) ───────────────────────
// RESPALDOS (Teleporter): lista, crear, descargar, subir, verificar, restaurar y borrar. El trabajo real lo hace el servidor; la página solo lo dispara y muestra el resultado.
// EN: BACKUPS (Teleporter): list, create, download, upload, verify, restore and delete. The server does the real work; the page only triggers it and shows the result.
let _tp = {backups:[], max:0, available:true}, _tpPoll = null, _tpName = null;
function tpFmtSize(b){ return b>=1048576 ? (b/1048576).toFixed(1)+' MB' : Math.max(1,Math.round(b/1024))+' KB'; }
// Descarga la lista de respaldos y el estado de la última restauración.
// EN: Download the backup list and the state of the last restore.
async function tpLoad() {
  // Los respaldos solo los maneja quien es admin de todos los módulos: para el resto se oculta la tarjeta.
  // EN: Backups are handled only by an admin of every module: for everyone else the card is hidden.
  const full = ['wol','nut','net','pve'].every(k => (me?.permissions||{})[k] === 'admin');
  document.getElementById('tp-card').style.display = full ? '' : 'none';
  if (!full) return;
  try {
    const r = await fetch('api/teleporter');
    if (!r.ok) return;
    const d = await r.json();
    _tp = {backups:d.backups||[], max:d.max_upload||0, available:d.available!==false};
    tpRender();
    if (d.restore && d.restore.state==='running' && !_tpPoll) tpShowProgress(d.restore);
  } catch(e) {}
}
// Dibuja la lista de respaldos con sus acciones.
// EN: Draw the backup list with its actions.
function tpRender() {
  const tb = document.getElementById('tp-tbody'); tb.innerHTML = '';
  const locale = _lang === 'es' ? 'es-CL' : 'en-US';
  document.getElementById('tp-empty').style.display = _tp.backups.length ? 'none' : 'block';
  document.getElementById('tp-empty').textContent = _tp.available ? t('tpEmpty') : t('tpNotAvailable');
  ['tp-create','tp-upload-btn'].forEach(id=>document.getElementById(id).disabled = !_tp.available);
  _tp.backups.forEach(b => {
    const n = esc(b.name), tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="tp-name">${n}</span></td>
      <td><span class="tp-kind ${b.kind==='upload'?'upload':''}">${t(b.kind==='upload'?'tpKindUpload':'tpKindBackup')}</span></td>
      <td><span class="ucreated">${tpFmtSize(b.size)}</span></td>
      <td><span class="ucreated">${new Date(b.mtime*1000).toLocaleString(locale)}</span></td>
      <td class="col-actions">
        <button class="btn-ri edit" data-on-click="tpDownload" data-on-click-args="${jsargs([b.name])}" title="${t('tpDownload')}">⬇</button>
        <button class="btn-ri edit" data-on-click="tpCheck" data-on-click-args="${jsargs([b.name])}" title="${t('tpCheck')}">✔</button>
        <button class="btn-ri edit" data-on-click="tpRestoreOpen" data-on-click-args="${jsargs([b.name])}" title="${t('tpRestore')}">⟲</button>
        <button class="btn-ri del" data-on-click="tpDelete" data-on-click-args="${jsargs([b.name])}" title="${t('tpDelete')}">✕</button>
      </td>`;
    tb.appendChild(tr);
  });
}
function tpShowOut(text, bad) {
  const o = document.getElementById('tp-out');
  o.textContent = text; o.className = 'tp-out show' + (bad?' bad':'');
  o.scrollTop = 0;
}
function tpDownload(name) {
  const a = document.createElement('a'); a.href = 'api/teleporter/download/'+encodeURIComponent(name); a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
}
// Crea un respaldo nuevo en el servidor.
// EN: Create a new backup on the server.
async function tpCreate() {
  const btn = document.getElementById('tp-create'); btn.disabled = true;
  btn.innerHTML = `<span class="spin">⟳</span> ${t('tpCreating')}`;
  try {
    const r = await fetch('api/teleporter/backup', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    const d = await r.json();
    if (!r.ok || !d.ok) { toast(d.error||t('tpFailed'), true); tpShowOut(d.output||'', true); }
    else { toast(t('tpCreated')); tpShowOut(d.output||''); tpDownload(d.name); }
  } catch(e) { toast(t('tpFailed'), true); }
  finally { btn.disabled=false; btn.innerHTML=`<span>${t('tpCreate')}</span>`; tpLoad(); }
}
document.getElementById('tp-file').addEventListener('change', e => {
  const f = e.target.files[0]; e.target.value = '';
  if (f) tpUpload(f);
});
// Sube un respaldo .tar.gz; el servidor comprueba tamaño y formato.
// EN: Upload a .tar.gz backup; the server checks size and format.
function tpUpload(file) {
  if (_tp.max && file.size > _tp.max) { toast(t('tpTooBig', Math.round(_tp.max/1048576)), true); return; }
  const btn = document.getElementById('tp-upload-btn'); btn.disabled = true;
  const xhr = new XMLHttpRequest();
  xhr.open('POST', 'api/teleporter/upload');
  xhr.setRequestHeader('Content-Type', 'application/octet-stream');
  xhr.upload.onprogress = ev => { if (ev.lengthComputable) btn.textContent = t('tpUploading', Math.round(ev.loaded*100/ev.total)); };
  xhr.onload = async () => {
    btn.disabled = false; btn.textContent = t('tpUpload');
    let d = {}; try { d = JSON.parse(xhr.responseText); } catch(e) {}
    if (xhr.status === 201 && d.name) { toast(t('tpUploaded')); await tpLoad(); tpCheck(d.name); }
    else toast(d.error || t('tpFailed'), true);
  };
  xhr.onerror = () => { btn.disabled = false; btn.textContent = t('tpUpload'); toast(t('tpFailed'), true); };
  xhr.send(file);
}
// Verifica un respaldo sin cambiar nada.
// EN: Verify a backup without changing anything.
async function tpCheck(name) {
  tpShowOut(t('tpChecking'));
  try {
    const r = await fetch('api/teleporter/check', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})});
    const d = await r.json();
    tpShowOut((d.ok ? '✓ '+t('tpCheckOk') : '✕ '+t('tpCheckBad')) + '\n\n' + (d.output||d.error||''), !d.ok);
    toast(d.ok ? t('tpCheckOk') : t('tpCheckBad'), !d.ok);
  } catch(e) { toast(t('tpFailed'), true); }
}
async function tpDelete(name) {
  if (!confirm(t('tpConfirmDelete', name))) return;
  const r = await fetch('api/teleporter/'+encodeURIComponent(name), {method:'DELETE'});
  if (r.ok) toast(t('tpDeleted')); else toast(t('tpFailed'), true);
  tpLoad();
}
// Abre la confirmación de restauración, que avisa que NUT y nginx solo se restauran por consola.
// EN: Open the restore confirmation, which warns that NUT and nginx are restored from the command line only.
function tpRestoreOpen(name) {
  _tpName = name;
  document.getElementById('tp-rs-name').textContent = name;
  document.getElementById('tp-opt-ok').checked = false;
  document.getElementById('tp-rs-go').disabled = true;
  document.getElementById('tp-rs-overlay').classList.add('show');
}
// Confirma y lanza la restauración en el servidor; luego sigue su avance.
// EN: Confirm and start the restore on the server; then follow its progress.
async function tpRestoreGo() {
  const body = {name:_tpName, confirm:true};
  closeModals();
  try {
    const r = await fetch('api/teleporter/restore', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const d = await r.json();
    if (!r.ok || !d.ok) { toast(d.error||t('tpFailed'), true); tpShowOut(d.output||'', true); return; }
    tpShowProgress({state:'running', log:''});
  } catch(e) { toast(t('tpFailed'), true); }
}
// Muestra el avance consultando cada 2 s. Durante la restauración el panel se reinicia: errores de conexión o un 401 (la sesión ya no existe) significan «reiniciado», no «falló».
// EN: Show progress by polling every 2 s. During the restore the panel restarts: connection errors or a 401 (the session no longer exists) mean "restarted", not "failed".
function tpShowProgress(st) {
  const ov = document.getElementById('tp-pg-overlay'); ov.classList.add('show');
  tpProgUpdate(st);
  if (_tpPoll) return;
  let lost = 0;
  _tpPoll = setInterval(async () => {
    try {
      const r = await fetch('api/teleporter', {cache:'no-store'});
      if (r.status === 401) return tpProgEnd('restarted');   // our session no longer exists: the restore replaced it
      if (!r.ok) { lost++; return; }
      const d = await r.json(); lost = 0;
      tpProgUpdate(d.restore || {state:'running', log:''});
    } catch(e) { lost++; }                                      // panel restarting
  }, 2000);
}
// Actualiza el texto y el registro del avance.
// EN: Update the progress text and log.
function tpProgUpdate(st) {
  const log = document.getElementById('tp-pg-log');
  if (st.log) { log.textContent = st.log; log.scrollTop = log.scrollHeight; }
  if (st.state && st.state !== 'running' && st.state !== 'idle') tpProgEnd(st.state);
}
// Fin de la restauración: muestra el resultado (ok, con errores o fallida).
// EN: End of the restore: show the result (ok, with errors or failed).
function tpProgEnd(state) {
  clearInterval(_tpPoll); _tpPoll = null;
  const map = {ok:['tpProgOk','tpProgOkMsg'], errors:['tpProgErr','tpProgErrMsg'], failed:['tpProgFail','tpProgFailMsg'], restarted:['tpProgRestarted','tpProgRestartedMsg']};
  const [a,b] = map[state] || map.failed;
  document.getElementById('tp-pg-title').textContent = t(a);
  document.getElementById('tp-pg-msg').textContent = t(b);
  document.getElementById('tp-pg-btn').style.display = '';
}

// ── Helpers ────────────────────────────────────────────
// Escapa HTML antes de insertar texto de usuarios, equipos o la red en la página: evita inyección de código (XSS).
// EN: Escape HTML before inserting text from users, devices or the network into the page: prevents code injection (XSS).
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
// Valor seguro dentro de un handler on*="…": literal JS entre comillas, escapado también para HTML.
function jsa(s){return esc(JSON.stringify(String(s)));}
// Lista de argumentos para data-on-*-args="…" (JSON escapado para HTML).
function jsargs(a){return esc(JSON.stringify(a));}
let _tt;
// Aviso emergente breve (error si isErr).
// EN: Short pop-up notice (error if isErr).
function toast(msg, isErr=false) {
  const el = document.getElementById('toast');
  el.textContent = msg; el.className = isErr?'err':'';
  void el.offsetWidth; el.classList.add('show');
  clearTimeout(_tt); _tt = setTimeout(()=>el.classList.remove('show'), 3400);
}

document.querySelectorAll('.overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o&&!o.classList.contains('noclose'))closeModals();}));
document.getElementById('drawer-overlay').addEventListener('click', e=>{ if(e.target===document.getElementById('drawer-overlay')) closeDrawer(); });
document.addEventListener('keydown', e=>{ if(e.key==='Escape'){closeModals();closeDrawer();} });
document.getElementById('l-pass').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin();});

// ── Check session on load ──────────────────────────────
// Al cargar: si hay sesión de administrador válida se muestra el panel; si no, el login.
// EN: On load: if there is a valid administrator session the panel is shown; otherwise the login.
(async()=>{
  try {
    const r = await fetch('api/me');
    if (r.ok) {
      const d = await r.json();
      if (d.username) {
        me = d;
        document.getElementById('me-name').textContent = d.username;
        document.getElementById('avatar').textContent  = d.username[0].toUpperCase();
        await loadUsers();
        document.getElementById('login-screen').style.display='none';
        return;
      }
    }
  } catch{}
  document.getElementById('login-screen').style.display='flex';
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
