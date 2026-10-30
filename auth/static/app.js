// Sesión actual {username, permissions}.
// EN: Current session {username, permissions}.
let me = null;

// ── i18n ──────────────────────────────────────────────────────────────────────
// Textos de la interfaz en inglés (en) y español (es). t('clave') devuelve el texto del idioma activo; si falta la clave en español, usa el inglés. Para agregar un idioma basta otro bloque con las mismas claves.
// EN: Interface texts in English (en) and Spanish (es). t('key') returns the text for the active language; if a Spanish key is missing, it falls back to English. Adding a language only takes another block with the same keys.
const LANG = {
  en: {
    loginTitle:'Admin access', loginSub:'Only administrators can access.',
    loginUser:'Username', loginPass:'Password', loginBtn:'Sign in',rememberMe:'Remember me',rem1d:'1 day',rem1w:'1 week',rem1m:'1 month',remForever:'Forever',
    loginFill:'Fill in all fields', themeLight:'Light', themeDark:'Dark', loginErr:'Invalid credentials', loginEntering:'Signing in…',
    navLabel:'Navigation', dragHandle:'Drag',
    userRole:'Administrator',
    logoutTitle:'Sign out',
    topbarTitle:'User management',
    statTotal:'Total users', statAdmins:'Administrators', statReadonly:'Read-only',
    cardTitle:'System users', btnNewUser:'New user',
    colUser:'User', colWOL:'WOL', colUPS:'UPS Monitor', colNET:'Net Monitor', colPVE:'Proxmox', colNAS:'NAS Monitor', colDNS:'DNS Monitor', colWAN:'WAN Monitor', colStatus:'Status', colCreated:'Created', colActions:'Actions',
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
    exTitle:'Download backup', exMsg:'The backup holds password hashes and API tokens, so it is downloaded encrypted (AES-256). Choose a passphrase and keep it: without it the file cannot be opened.', exPass:'Passphrase (12+ characters)', exPass2:'Repeat the passphrase', exAcct:'Your account password', exPlain:'Download WITHOUT encryption (not recommended)', exBtn:'Download', exShort:'The passphrase must have at least 12 characters', exMismatch:'The passphrases do not match', exNeedPw:'Enter your account password', upPassMsg:'This backup is encrypted. Enter its passphrase.',
    reauthTitle:'Confirm your password', reauthMsg:'This action is sensitive. Enter your current password to continue.', reauthBtn:'Confirm',
    fieldCurPw:'Current password (required to change your own)', curPwNeeded:'Enter your current password to change it',
    btnCancel:'Cancel', btnCreate:'Create user', btnSave:'Save changes',
    modalDeleteTitle:'Delete user', modalDeleteBtn:'Delete',
    mustChangeBadge:'Change pwd',
    hlTitle:'System health', hl_ok:'All healthy', hl_degraded:'Degraded', hl_fail:'Failing', hlSystem:'system', hlDown:'Service not answering', hlUptime:'Running for',
    ssTitle:'Active sessions', ssCloseOthers:'Close my other sessions', ssHint:'Devices signed in right now. Closing a session signs that device out immediately. Times are approximate.',
    ssDevice:'Device', ssIp:'IP', ssLast:'Last activity', ssExpires:'Expires', ssThis:'This session', ssClose:'Close session', ssOld:'Unknown', ssNone:'No active sessions.',
    ssConfirm:(u,d)=>`Close the session of "${u}" on ${d}?`, ssConfirmOthers:'Close all your other sessions?', ssClosed:'Session closed', ssClosedN:n=>`${n} session(s) closed`, ssNow:'now',
    upTitle:'Updates', upBanner:(n,c)=>`New LabTower version ${n} is available (installed: ${c}).`, upSee:'See release notes', upInstalled:'Installed', upLatest:'Latest published', upChecked:'Last checked', upCheck:'Check now',
    upOk:'You are up to date.', upOff:'Update check is turned off (LABTOWER_UPDATE_CHECK=0).', upErr:'Could not reach GitHub:', upNever:'not yet', upHow:'To update: download the .deb from the release page and run sudo apt install ./labtower_VERSION_all.deb',
    sfTitle:'Security: two-factor authentication', sfOff:'Two-factor authentication is OFF for your account.', sfOn:(n)=>`Two-factor authentication is ON for your account (${n} recovery codes left).`,
    sfEnable:'Turn on 2FA', sfDisable:'Turn off 2FA', sfStep1:'1. In your authenticator app (Google Authenticator, Aegis, 1Password…) choose «Scan QR code» and scan this:', sfManual:'Can’t scan it? Add the account by typing this key (type: time based):',
    sfOpen:'Open in authenticator', sfStep2:'2. Type the 6-digit code it shows:', sfConfirm:'Confirm', sfCode:'6-digit code', sfRecTitle:'Save these recovery codes now. Each works once if you lose your phone. They will not be shown again:',
    sfDone:'Done, I saved them', sfEnabled:'2FA is on', sfDisabled:'2FA is off', sfDisablePrompt:'Turn off two-factor authentication? You will need your password.', sfBadCode:'That code is not valid',
    sfReset:'Reset 2FA', sfResetConfirm:u=>`Reset two-factor authentication for "${u}"? They will sign in with the password only until they set it up again.`, sfResetDone:'2FA reset', sf2fa:'2FA',
    auTitle:'Audit log', auHint:'Who changed what: users, permissions, passwords, 2FA, sessions, backups and lockouts. The last 5,000 entries are kept.', auWhen:'When', auActor:'Who', auAction:'Action', auTarget:'Target', auDetail:'Detail', auNone:'No entries yet.', auRefresh:'Refresh',
    au_login:'Signed in', au_user_created:'User created', au_user_deleted:'User deleted', au_permissions_changed:'Permissions changed', au_password_changed:'Password changed', au_password_reset:'Password reset by admin',
    au_session_revoked:'Session closed', au_sessions_revoked:'Other sessions closed', au_2fa_enabled:'2FA turned on', au_2fa_disabled:'2FA turned off', au_2fa_reset:'2FA reset', au_2fa_failed:'Wrong 2FA code', au_2fa_recovery_used:'Recovery code used',
    au_lockout_ip:'IP locked out', au_lockout_account:'Account locked out', au_backup_created:'Backup created', au_backup_failed:'Backup failed', au_backup_downloaded:'Backup downloaded', au_backup_deleted:'Backup deleted', au_restore_started:'Restore started', au_restore_failed:'Restore failed',
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
    tpProgErr:'Restore finished with errors', tpProgErrMsg:'Review the log below. A snapshot of the previous state is in /var/backups/labtower/.',
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
    loginUser:'Usuario', loginPass:'Contraseña', loginBtn:'Entrar',rememberMe:'Recordarme',rem1d:'1 día',rem1w:'1 semana',rem1m:'1 mes',remForever:'Siempre',
    loginFill:'Completa todos los campos', themeLight:'Claro', themeDark:'Oscuro', loginErr:'Credenciales incorrectas', loginEntering:'Entrando…',
    navLabel:'Navegación', dragHandle:'Arrastrar',
    userRole:'Administrador',
    logoutTitle:'Cerrar sesión',
    topbarTitle:'Gestión de usuarios',
    statTotal:'Usuarios totales', statAdmins:'Administradores', statReadonly:'Solo lectura',
    cardTitle:'Usuarios del sistema', btnNewUser:'Nuevo usuario',
    colUser:'Usuario', colWOL:'WOL', colUPS:'UPS Monitor', colNET:'Net Monitor', colPVE:'Proxmox', colNAS:'NAS Monitor', colDNS:'DNS Monitor', colWAN:'WAN Monitor', colStatus:'Estado', colCreated:'Creado', colActions:'Acciones',
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
    exTitle:'Descargar respaldo', exMsg:'El respaldo contiene hashes de contraseñas y tokens de API, por eso se descarga cifrado (AES-256). Elige una frase y guárdala: sin ella el archivo no se puede abrir.', exPass:'Frase de cifrado (12 o más caracteres)', exPass2:'Repite la frase', exAcct:'La contraseña de tu cuenta', exPlain:'Descargar SIN cifrar (no recomendado)', exBtn:'Descargar', exShort:'La frase debe tener al menos 12 caracteres', exMismatch:'Las frases no coinciden', exNeedPw:'Escribe la contraseña de tu cuenta', upPassMsg:'Este respaldo está cifrado. Escribe su frase.',
    reauthTitle:'Confirma tu contraseña', reauthMsg:'Esta acción es sensible. Escribe tu contraseña actual para continuar.', reauthBtn:'Confirmar',
    fieldCurPw:'Contraseña actual (obligatoria para cambiar la tuya)', curPwNeeded:'Escribe tu contraseña actual para cambiarla',
    btnCancel:'Cancelar', btnCreate:'Crear usuario', btnSave:'Guardar cambios',
    modalDeleteTitle:'Eliminar usuario', modalDeleteBtn:'Eliminar',
    mustChangeBadge:'Cambiar pwd',
    hlTitle:'Salud del sistema', hl_ok:'Todo bien', hl_degraded:'Degradado', hl_fail:'Con fallas', hlSystem:'sistema', hlDown:'El servicio no responde', hlUptime:'Activo hace',
    ssTitle:'Sesiones activas', ssCloseOthers:'Cerrar mis otras sesiones', ssHint:'Dispositivos con sesión iniciada ahora. Cerrar una sesión desconecta ese dispositivo de inmediato. Las horas son aproximadas.',
    ssDevice:'Dispositivo', ssIp:'IP', ssLast:'Última actividad', ssExpires:'Vence', ssThis:'Esta sesión', ssClose:'Cerrar sesión', ssOld:'Desconocido', ssNone:'No hay sesiones activas.',
    ssConfirm:(u,d)=>`¿Cerrar la sesión de "${u}" en ${d}?`, ssConfirmOthers:'¿Cerrar todas tus otras sesiones?', ssClosed:'Sesión cerrada', ssClosedN:n=>`${n} sesión(es) cerrada(s)`, ssNow:'ahora',
    upTitle:'Actualizaciones', upBanner:(n,c)=>`Hay una versión nueva de LabTower: ${n} (instalada: ${c}).`, upSee:'Ver notas de la versión', upInstalled:'Instalada', upLatest:'Última publicada', upChecked:'Última consulta', upCheck:'Consultar ahora',
    upOk:'Estás al día.', upOff:'La consulta de versiones está desactivada (LABTOWER_UPDATE_CHECK=0).', upErr:'No se pudo consultar GitHub:', upNever:'aún no', upHow:'Para actualizar: descarga el .deb de la página de la versión y ejecuta sudo apt install ./labtower_VERSION_all.deb',
    sfTitle:'Seguridad: autenticación en dos pasos', sfOff:'La autenticación en dos pasos está DESACTIVADA en tu cuenta.', sfOn:(n)=>`La autenticación en dos pasos está ACTIVA en tu cuenta (te quedan ${n} códigos de recuperación).`,
    sfEnable:'Activar 2FA', sfDisable:'Desactivar 2FA', sfStep1:'1. En tu app de autenticación (Google Authenticator, Aegis, 1Password…) elige «Escanear código QR» y escanea este:', sfManual:'¿No puedes escanearlo? Agrega la cuenta escribiendo esta clave (tipo: basada en tiempo):',
    sfOpen:'Abrir en la app', sfStep2:'2. Escribe el código de 6 dígitos que muestra:', sfConfirm:'Confirmar', sfCode:'Código de 6 dígitos', sfRecTitle:'Guarda estos códigos de recuperación ahora. Cada uno sirve una vez si pierdes el teléfono. No se vuelven a mostrar:',
    sfDone:'Listo, ya los guardé', sfEnabled:'2FA activado', sfDisabled:'2FA desactivado', sfDisablePrompt:'¿Desactivar la autenticación en dos pasos? Necesitarás tu contraseña.', sfBadCode:'Ese código no es válido',
    sfReset:'Restablecer 2FA', sfResetConfirm:u=>`¿Restablecer la autenticación en dos pasos de "${u}"? Entrará solo con la contraseña hasta que la configure otra vez.`, sfResetDone:'2FA restablecido', sf2fa:'2FA',
    auTitle:'Registro de auditoría', auHint:'Quién cambió qué: usuarios, permisos, contraseñas, 2FA, sesiones, respaldos y bloqueos. Se conservan las últimas 5.000 entradas.', auWhen:'Cuándo', auActor:'Quién', auAction:'Acción', auTarget:'Objetivo', auDetail:'Detalle', auNone:'Aún no hay entradas.', auRefresh:'Actualizar',
    au_login:'Inicio de sesión', au_user_created:'Usuario creado', au_user_deleted:'Usuario eliminado', au_permissions_changed:'Permisos cambiados', au_password_changed:'Contraseña cambiada', au_password_reset:'Contraseña restablecida por un admin',
    au_session_revoked:'Sesión cerrada', au_sessions_revoked:'Otras sesiones cerradas', au_2fa_enabled:'2FA activado', au_2fa_disabled:'2FA desactivado', au_2fa_reset:'2FA restablecido', au_2fa_failed:'Código 2FA incorrecto', au_2fa_recovery_used:'Código de recuperación usado',
    au_lockout_ip:'IP bloqueada', au_lockout_account:'Cuenta bloqueada', au_backup_created:'Respaldo creado', au_backup_failed:'Respaldo fallido', au_backup_downloaded:'Respaldo descargado', au_backup_deleted:'Respaldo eliminado', au_restore_started:'Restauración iniciada', au_restore_failed:'Restauración fallida',
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
    tpProgErr:'Restauración terminada con errores', tpProgErrMsg:'Revisa el registro. El snapshot del estado anterior está en /var/backups/labtower/.',
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
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>el.placeholder=t(el.getAttribute('data-i18n-ph')));
  ['en','es'].forEach(x=>document.getElementById('lang-'+x)?.classList.toggle('active',x===l));
  // Update logout button title
  document.getElementById('btn-logout').title = t('logoutTitle');
  try{tpRender();}catch(e){}
  try{ssRender();}catch(e){}
  try{sfRender();auRender();upRender();}catch(e){}
  // Update new-pw placeholder
  const npw = document.getElementById('d-new-pw');
  if(npw) npw.placeholder = t('fieldNewPwPlaceholder');
  // Update password placeholder
  const dpw = document.getElementById('d-password');
  if(dpw) dpw.placeholder = t('fieldPasswordHint');
  // Update permission selects
  ['d-wol','d-nut','d-net','d-pve','d-nas','d-dns','d-wan'].forEach(id=>{
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
  {id:'overview', href:'/overview/', get label(){return _lang==='es'?'Resumen':'Overview'}, svg:'<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>'},
  {id:'nut',   href:'/nut/',   label:'UPS Monitor', svg:'<path d="M5 9V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v4"/><rect x="3" y="9" width="18" height="11" rx="2"/><line x1="12" y1="13" x2="12" y2="16"/>'},
  {id:'net',   href:'/net/',   label:'Net Monitor', svg:'<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>'},
  {id:'pve',   href:'/pve/',   label:'Proxmox',     svg:'<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>'},
  {id:'nas',   href:'/nas/',   label:'NAS Monitor',svg:'<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="7" y1="9" x2="17" y2="9"/><line x1="7" y1="14" x2="17" y2="14"/><line x1="16" y1="18" x2="16.01" y2="18"/>'},
  {id:'dns',  href:'/dns/',   label:'DNS Monitor', svg:'<circle cx="12" cy="12" r="9"/><line x1="3" y1="12" x2="21" y2="12"/><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z"/>'},
  {id:'wan',  href:'/wan/',   label:'WAN Monitor', svg:'<path d="M5 12.55a11 11 0 0 1 14 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/>'},
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
(()=>{setTheme(localStorage.getItem('pi-theme')||'dark');})();

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
      body: JSON.stringify({username:u, password:p, remember:remValue()})
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
  tpLoad(); ssLoad(); sfLoad(); auLoad(); upLoad();
  hlLoad(); if (!window._hlTimer) window._hlTimer = setInterval(hlLoad, 30000);
}

// ── System health ───────────────────────────────────────
// SALUD DEL SISTEMA: tarjetas con el estado de cada módulo (datos de /api/health). HL_DESC explica en palabras simples qué comprueba cada chequeo.
// EN: SYSTEM HEALTH: cards with the state of each module (data from /api/health). HL_DESC explains in plain words what each check verifies.
const HL_NAMES = {wol:'WOL Console', nut:'UPS Monitor', net:'Net Monitor', pve:'Proxmox', nas:'NAS Monitor', dns:'DNS Monitor', wan:'WAN Monitor', overview:'Overview'};
const HL_DESC = {
  en:{users:'User database (users.json) is readable and has accounts', sessions:'Session file is readable and its folder writable', disk:'Free disk space (warns below 100 MB, fails below 5 MB)',
      teleporter:'Backup tool (teleporter.sh) is installed', power:'Raspberry Pi power supply: no under-voltage or throttling (shown only on a Raspberry Pi)', devices:'Device list file is readable and writable', wake_log:'Wake log file is readable and writable',
      net_monitor:'Net Monitor host list can be read (optional)', network:'This machine has a LAN address for magic packets',
      servers_file:'UPS server list file is readable and writable', database:'History database opens and is not locked', history_write:'Buffered history rows are being written to disk',
      pollers:'Background threads that read the data are alive', upsd:'Every NUT server answers', history_fresh:'Recent readings are really stored in the history',
      hosts_file:'Host table file is readable and writable', config_file:'Configuration file is readable and writable', scanner:'The scan is not stuck', auto_scan:'Automatic scan timer is armed and scans are recent',
      clusters_file:'Cluster list file is readable and writable', clusters:'Every Proxmox cluster answers with fresh data', nas_file:'NAS list file is readable and writable', dns_file:'DNS server list file is readable and writable', dns_servers:'Every DNS server answers with fresh data', wan_file:'WAN settings file is readable and writable', ping_tool:'The ping command is installed', probe:'The internet checks run on time', snmp_tools:'The net-snmp tools (snmpget, snmpbulkwalk) are installed', nas_snmp:'Every NAS answers over SNMP with fresh data', events:'Event timeline file is readable and its folder writable',
      wol:'WOL Console service', nut:'UPS Monitor service', net:'Net Monitor service', pve:'Proxmox service', nas:'NAS Monitor service', dns:'DNS Monitor service', wan:'WAN Monitor service', overview:'Overview service'},
  es:{users:'Base de usuarios (users.json) legible y con cuentas', sessions:'Archivo de sesiones legible y carpeta escribible', disk:'Espacio libre en disco (avisa bajo 100 MB, falla bajo 5 MB)',
      teleporter:'Herramienta de respaldo (teleporter.sh) instalada', power:'Fuente de la Raspberry Pi: sin subtensión ni limitación (solo se muestra en una Raspberry Pi)', devices:'Archivo de dispositivos legible y escribible', wake_log:'Archivo del registro de encendidos legible y escribible',
      net_monitor:'Se puede leer la lista de hosts de Net Monitor (opcional)', network:'Este equipo tiene dirección LAN para los magic packets',
      servers_file:'Archivo de servidores UPS legible y escribible', database:'La base de historial abre y no está bloqueada', history_write:'Las filas de historial en memoria se escriben a disco',
      pollers:'Los hilos que leen los datos están vivos', upsd:'Todos los servidores NUT responden', history_fresh:'Las lecturas recientes realmente quedan guardadas en el historial',
      hosts_file:'Archivo de hosts legible y escribible', config_file:'Archivo de configuración legible y escribible', scanner:'El escaneo no está trabado', auto_scan:'El temporizador de auto-escaneo está armado y los escaneos son recientes',
      clusters_file:'Archivo de clusters legible y escribible', clusters:'Todos los clusters Proxmox responden con datos frescos', nas_file:'Archivo de la lista de NAS legible y escribible', dns_file:'Archivo de la lista de servidores DNS legible y escribible', dns_servers:'Todos los servidores DNS responden con datos frescos', wan_file:'Archivo de ajustes de WAN legible y escribible', ping_tool:'El comando ping está instalado', probe:'Las mediciones de internet corren a tiempo', snmp_tools:'Las herramientas net-snmp (snmpget, snmpbulkwalk) están instaladas', nas_snmp:'Todos los NAS responden por SNMP con datos frescos', events:'Archivo de la línea de tiempo legible y carpeta escribible',
      wol:'Servicio WOL Console', nut:'Servicio UPS Monitor', net:'Servicio Net Monitor', pve:'Servicio Proxmox', nas:'Servicio NAS Monitor', dns:'Servicio DNS Monitor', wan:'Servicio WAN Monitor', overview:'Servicio Resumen'}
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
      <td><span class="uname">${esc(u.username)}</span>${u.totp ? ` <span class="tp-kind" title="${esc(t('sfTitle'))}">${esc(t('sf2fa'))}</span>` : ''}</td>
      <td data-label="${esc(t('colWOL'))}">${permBadge(u.permissions.wol)}</td>
      <td data-label="${esc(t('colUPS'))}">${permBadge(u.permissions.nut)}</td>
      <td data-label="${esc(t('colNET'))}">${permBadge(u.permissions.net)}</td>
      <td data-label="${esc(t('colPVE'))}">${permBadge(u.permissions.pve)}</td>
      <td data-label="${esc(t('colNAS'))}">${permBadge(u.permissions.nas)}</td>
      <td data-label="${esc(t('colDNS'))}">${permBadge(u.permissions.dns)}</td>
      <td data-label="${esc(t('colWAN'))}">${permBadge(u.permissions.wan)}</td>
      <td data-label="${esc(t('colStatus'))}">${u.must_change_password ? `<span class="must-change">${t('mustChangeBadge')}</span>` : '<span style="font-size:11px;color:var(--text-dim)">—</span>'}</td>
      <td data-label="${esc(t('colCreated'))}"><span class="ucreated">${u.created ? new Date(u.created*1000).toLocaleDateString(locale) : '—'}</span></td>
      <td class="col-actions">
        <button class="btn-ri edit" data-on-click="editUser" data-on-click-args="${jsargs([u])}" title="Edit">✎</button>
        ${u.totp && u.username !== me?.username ? `<button class="btn-ri" data-on-click="sfResetUser" data-on-click-args="${jsargs([u.username])}" title="${esc(t('sfReset'))}">🔑</button>` : ''}
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
  return `<span class="perm-badge perm-${labels[perm]?perm:'none'}">${labels[perm]||'—'}</span>`;
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
  ['d-wol','d-nut','d-net','d-pve','d-nas','d-dns','d-wan'].forEach(id=>{
    const sel = document.getElementById(id); if(!sel) return;
    const key = id.slice(2), defs = {wol:'execute', nut:'readonly', net:'none', pve:'none', nas:'none', dns:'none', wan:'none'};
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
      const nas   = document.getElementById('d-nas').value;
      const dns   = document.getElementById('d-dns').value;
      const wan   = document.getElementById('d-wan').value;
      const must  = document.getElementById('d-must-change').checked;
      if (!uname || !pwd) { toast(t('loginFill'), true); return; }
      const apw = await askPassword(); if (!apw) return;
      const r = await fetch('api/users', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({username:uname, password:pwd, wol_permission:wol, nut_permission:nut, net_permission:net, pve_permission:pve, nas_permission:nas, dns_permission:dns, wan_permission:wan, must_change_password:must, current_password:apw})
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
      const nas   = document.getElementById('d-nas').value;
      const dns   = document.getElementById('d-dns').value;
      const wan   = document.getElementById('d-wan').value;
      const newPw = document.getElementById('d-new-pw').value;
      // Actualizar permisos
      const r = await fetch('api/users/'+uorig, {
        method: 'PUT', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({wol_permission:wol, nut_permission:nut, net_permission:net, pve_permission:pve, nas_permission:nas, dns_permission:dns, wan_permission:wan})
      });
      const d = await r.json();
      if (!r.ok) { toast(d.error||'Error', true); return; }
      // Cambiar contraseña si se ingresó
      if (newPw) {
        let curPw = document.getElementById('d-cur-pw').value;
        const own = me && uorig === me.username;
        if (own && !curPw) { toast(t('curPwNeeded'), true); return; }
        if (!own) { curPw = await askPassword(); if (!curPw) return; }
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

// Pide la contraseña actual en un diálogo y devuelve una promesa con ella (o null si se cancela). Acciones críticas: crear usuario, crear/restaurar respaldo, restablecer la clave de otro.
// EN: Ask for the current password in a dialog; returns a promise with it (or null when cancelled). Critical actions: create user, create/restore backup, reset someone else's password.
let _pwResolve = null;
function askPassword(titleKey, msgKey) {
  document.querySelector('#pw-overlay h3').textContent = t(titleKey || 'reauthTitle');
  document.querySelector('#pw-overlay p').textContent = t(msgKey || 'reauthMsg');
  return new Promise(res => {
    if (_pwResolve) _pwResolve(null);
    _pwResolve = res;
    const i = document.getElementById('pw-input'); i.value = '';
    document.getElementById('pw-overlay').classList.add('show'); i.focus();
  });
}
function _pwDone(v) {
  document.getElementById('pw-overlay').classList.remove('show');
  document.getElementById('pw-input').value = '';
  const r = _pwResolve; _pwResolve = null; if (r) r(v);
}
function reauthOk() { _pwDone(document.getElementById('pw-input').value || null); }
function reauthCancel() { _pwDone(null); }
document.getElementById('pw-input').addEventListener('keydown', e => { if (e.key === 'Enter') reauthOk(); if (e.key === 'Escape') reauthCancel(); });

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
  const full = ['wol','nut','net','pve','nas','dns','wan'].every(k => (me?.permissions||{})[k] === 'admin');
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
      <td><span class="ucreated">${PCT.ls(new Date(b.mtime*1000), locale)}</span></td>
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
// Descarga de un respaldo: pide la frase de cifrado y la contraseña de la cuenta, y baja el archivo ya cifrado (.gpg).
// EN: Backup download: asks for the encryption passphrase and the account password, and downloads the already encrypted (.gpg) file.
let _exName = '';
function tpDownload(name) {
  _exName = name;
  document.getElementById('tp-ex-name').textContent = name;
  ['tp-ex-pass','tp-ex-pass2','tp-ex-acct'].forEach(i => { const e = document.getElementById(i); e.value = ''; e.disabled = false; });
  document.getElementById('tp-ex-plain').checked = false;
  document.getElementById('tp-ex-overlay').classList.add('show');
}
function exPlainToggle() {
  const plain = document.getElementById('tp-ex-plain').checked;
  ['tp-ex-pass','tp-ex-pass2'].forEach(i => document.getElementById(i).disabled = plain);
}
function exCancel() { document.getElementById('tp-ex-overlay').classList.remove('show'); }
async function exGo() {
  const plain = document.getElementById('tp-ex-plain').checked;
  const pw = document.getElementById('tp-ex-pass').value, pw2 = document.getElementById('tp-ex-pass2').value;
  const acct = document.getElementById('tp-ex-acct').value;
  if (!acct) { toast(t('exNeedPw'), true); return; }
  if (!plain) {
    if (pw.length < 12) { toast(t('exShort'), true); return; }
    if (pw !== pw2) { toast(t('exMismatch'), true); return; }
  }
  try {
    const r = await fetch('api/teleporter/export', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name:_exName, current_password:acct, passphrase:plain?'':pw, plain})});
    if (!r.ok) { let d = {}; try { d = await r.json(); } catch(e) {} toast(d.error||t('tpFailed'), true); return; }
    const blob = await r.blob();
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = _exName + (plain ? '' : '.gpg');
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
    exCancel();
  } catch(e) { toast(t('tpFailed'), true); }
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
    else { toast(t('tpCreated')); tpShowOut(d.output||''); }
  } catch(e) { toast(t('tpFailed'), true); }
  finally { btn.disabled=false; btn.innerHTML=`<span>${t('tpCreate')}</span>`; tpLoad(); }
}
document.getElementById('tp-file').addEventListener('change', e => {
  const f = e.target.files[0]; e.target.value = '';
  if (f) tpUpload(f);
});
// Sube un respaldo .tar.gz; el servidor comprueba tamaño y formato.
// EN: Upload a .tar.gz backup; the server checks size and format.
async function tpUpload(file) {
  if (_tp.max && file.size > _tp.max) { toast(t('tpTooBig', Math.round(_tp.max/1048576)), true); return; }
  let pass = '';
  if (/\.gpg$/i.test(file.name)) { pass = await askPassword('exTitle', 'upPassMsg'); if (!pass) return; }
  const btn = document.getElementById('tp-upload-btn'); btn.disabled = true;
  const xhr = new XMLHttpRequest();
  xhr.open('POST', 'api/teleporter/upload');
  xhr.setRequestHeader('Content-Type', 'application/octet-stream');
  if (pass) xhr.setRequestHeader('X-Backup-Passphrase', pass);
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
  closeModals();
  const apw = await askPassword(); if (!apw) return;
  const body = {name:_tpName, confirm:true, current_password:apw};
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

// ───────── Recordarme / Remember me ─────────
// Devuelve la duración elegida ("day","week","month","forever") o "" si no se marcó. Recuerda la última elección en este navegador.
// EN: Returns the chosen duration ("day","week","month","forever") or "" if unchecked. Remembers the last choice in this browser.
function remValue(){const c=document.getElementById('l-rem'),s=document.getElementById('l-remsel');const v=c&&c.checked&&s?s.value:'';try{localStorage.setItem('pi-remember',v)}catch(e){}return v}
(function remInit(){try{const v=localStorage.getItem('pi-remember')||'';const c=document.getElementById('l-rem'),s=document.getElementById('l-remsel');if(c&&s&&['day','week','month','forever'].includes(v)){c.checked=true;s.disabled=false;s.value=v}}catch(e){}})();

// ── Sesiones activas ───────────────────────────────────
// Lista las sesiones abiertas (todas las cuentas) y permite cerrarlas.
// EN: List the open sessions (all accounts) and allow closing them.
let _ss = [];
async function ssLoad() {
  try {
    const r = await fetch('api/sessions');
    if (!r.ok) return;
    _ss = (await r.json()).sessions || [];
    ssRender();
  } catch(e) {}
}
// Resume el User-Agent en «Navegador · Sistema».
// EN: Summarize the User-Agent as "Browser · System".
function ssDevice(ua) {
  if (!ua) return t('ssOld');
  const os = /iPhone/.test(ua) ? 'iPhone' : /iPad/.test(ua) ? 'iPad' : /Android/.test(ua) ? 'Android' : /Mac OS X/.test(ua) ? 'macOS' : /Windows/.test(ua) ? 'Windows' : /CrOS/.test(ua) ? 'ChromeOS' : /Linux/.test(ua) ? 'Linux' : '';
  const br = /Edg\//.test(ua) ? 'Edge' : /OPR\/|Opera/.test(ua) ? 'Opera' : /Firefox\//.test(ua) ? 'Firefox' : /(Chrome|CriOS)\//.test(ua) ? 'Chrome' : /Safari\//.test(ua) ? 'Safari' : /curl/i.test(ua) ? 'curl' : ua.slice(0,24);
  return os ? br + ' · ' + os : br;
}
function ssAgo(ts) {
  const d = Math.max(0, Date.now()/1000 - ts);
  if (d < 90) return t('ssNow');
  const rtf = new Intl.RelativeTimeFormat(_lang === 'es' ? 'es' : 'en', {numeric:'auto'});
  if (d < 5400) return rtf.format(-Math.round(d/60), 'minute');
  if (d < 129600) return rtf.format(-Math.round(d/3600), 'hour');
  return rtf.format(-Math.round(d/86400), 'day');
}
function ssRender() {
  const tb = document.getElementById('ss-tbody'); if (!tb) return;
  tb.innerHTML = '';
  const locale = _lang === 'es' ? 'es-CL' : 'en-US';
  if (!_ss.length) { tb.innerHTML = `<tr><td colspan="6" class="tp-empty">${esc(t('ssNone'))}</td></tr>`; }
  _ss.forEach(s => {
    const tr = document.createElement('tr'), dev = ssDevice(s.ua);
    tr.innerHTML = `
      <td><b>${esc(s.username)}</b>${s.current ? ` <span class="tp-kind">${esc(t('ssThis'))}</span>` : ''}</td>
      <td><span class="ucreated" title="${esc(s.ua||'')}">${esc(dev)}</span></td>
      <td><span class="ucreated">${esc(s.ip||'—')}</span></td>
      <td><span class="ucreated">${esc(ssAgo(s.last))}</span></td>
      <td><span class="ucreated">${new Date(s.expires*1000).toLocaleDateString(locale)}</span></td>
      <td class="col-actions">${s.current ? '' : `<button class="btn-ri del" data-on-click="ssClose" data-on-click-args="${jsargs([s.id, s.username, dev])}" title="${esc(t('ssClose'))}">✕</button>`}</td>`;
    tb.appendChild(tr);
  });
  const o = document.getElementById('ss-others');
  const me = (_ss.find(x => x.current) || {}).username;
  if (o) o.disabled = !_ss.some(x => !x.current && x.username === me);
}
async function ssClose(id, user, dev) {
  if (!confirm(t('ssConfirm', user, dev))) return;
  const r = await fetch('api/sessions/'+encodeURIComponent(id), {method:'DELETE'});
  if (r.ok) toast(t('ssClosed')); else toast((await r.json().catch(()=>({}))).error || t('tpFailed'), true);
  ssLoad();
}
async function ssCloseOthers() {
  if (!confirm(t('ssConfirmOthers'))) return;
  const r = await fetch('api/sessions/others', {method:'DELETE'});
  if (r.ok) toast(t('ssClosedN', (await r.json()).closed)); else toast(t('tpFailed'), true);
  ssLoad();
}

// ── Seguridad: 2FA (TOTP) y registro de auditoría ──────
// EN: Security: 2FA (TOTP) and the audit log.
let _sf = {enabled:false, recovery_left:0}, _au = [], _sfSetup = null, _sfRec = null;
async function sfLoad() {
  try { const r = await fetch('api/2fa'); if (r.ok) { _sf = await r.json(); sfRender(); } } catch(e) {}
}
function sfRender() {
  const box = document.getElementById('sf-body'); if (!box) return;
  let h = `<div class="tp-hint" style="border:0">${esc(_sf.enabled ? t('sfOn', _sf.recovery_left) : t('sfOff'))}</div><div style="padding:0 18px 14px">`;
  if (_sfRec) {
    h += `<p style="font-size:12px;color:var(--text-mid)">${esc(t('sfRecTitle'))}</p><pre class="tp-out" style="display:block">${esc(_sfRec.join('\n'))}</pre>
      <button class="btn-primary" data-on-click="sfRecDone">${esc(t('sfDone'))}</button>`;
  } else if (_sfSetup) {
    const k = _sfSetup.secret.replace(/(.{4})/g, '$1 ').trim();
    const qr = /^<svg xmlns="http:\/\/www\.w3\.org\/2000\/svg"[^<]*><rect[^<]*\/><path d="[MhvzL0-9,\- .]*" fill="#000"\/><\/svg>$/.test(_sfSetup.qr || '') ? _sfSetup.qr : '';
    h += `<p style="font-size:12px;color:var(--text-mid)">${esc(t('sfStep1'))}</p>
      ${qr ? `<div style="width:200px;height:200px;margin:8px 0;border-radius:8px;overflow:hidden">${qr}</div>` : ''}
      <p style="font-size:12px;color:var(--text-mid)">${esc(t('sfManual'))}</p>
      <pre class="tp-out" style="display:block;font-size:15px;letter-spacing:1px">${esc(k)}</pre>
      <p style="font-size:12px"><a href="${esc(_sfSetup.uri)}">${esc(t('sfOpen'))}</a></p>
      <p style="font-size:12px;color:var(--text-mid)">${esc(t('sfStep2'))}</p>
      <input id="sf-code" inputmode="numeric" autocomplete="one-time-code" maxlength="8" placeholder="${esc(t('sfCode'))}" style="width:160px;margin-right:8px">
      <button class="btn-primary" data-on-click="sfConfirm">${esc(t('sfConfirm'))}</button>`;
  } else {
    h += _sf.enabled ? `<button class="btn-sec" data-on-click="sfDisable">${esc(t('sfDisable'))}</button>`
                     : `<button class="btn-primary" data-on-click="sfBegin">${esc(t('sfEnable'))}</button>`;
  }
  box.innerHTML = h + '</div>';
}
async function sfBegin() {
  const pw = await askPassword(); if (!pw) return;
  const r = await fetch('api/2fa/begin', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({current_password:pw})});
  const d = await r.json().catch(()=>({}));
  if (!r.ok) return toast(d.error || t('tpFailed'), true);
  _sfSetup = d; sfRender();
}
async function sfConfirm() {
  const c = (document.getElementById('sf-code') || {}).value || '';
  const r = await fetch('api/2fa/enable', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code:c})});
  const d = await r.json().catch(()=>({}));
  if (!r.ok) return toast(r.status === 400 ? t('sfBadCode') : (d.error || t('tpFailed')), true);
  _sfSetup = null; _sfRec = d.recovery || []; toast(t('sfEnabled'));
  await sfLoad(); sfRender(); loadUsers(); auLoad();
}
function sfRecDone() { _sfRec = null; sfRender(); }
async function sfDisable() {
  if (!confirm(t('sfDisablePrompt'))) return;
  const pw = await askPassword(); if (!pw) return;
  const r = await fetch('api/2fa/disable', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({current_password:pw})});
  const d = await r.json().catch(()=>({}));
  if (!r.ok) return toast(d.error || t('tpFailed'), true);
  toast(t('sfDisabled')); await sfLoad(); loadUsers(); auLoad();
}
async function sfResetUser(user) {
  if (!confirm(t('sfResetConfirm', user))) return;
  const pw = await askPassword(); if (!pw) return;
  const r = await fetch('api/2fa/reset', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({current_password:pw, username:user})});
  const d = await r.json().catch(()=>({}));
  if (!r.ok) return toast(d.error || t('tpFailed'), true);
  toast(t('sfResetDone')); loadUsers(); auLoad();
}
async function auLoad() {
  try { const r = await fetch('api/audit?limit=150'); if (r.ok) { _au = (await r.json()).audit || []; auRender(); } } catch(e) {}
}
function auRender() {
  const tb = document.getElementById('au-tbody'); if (!tb) return;
  const locale = _lang === 'es' ? 'es-CL' : 'en-US';
  if (!_au.length) { tb.innerHTML = `<tr><td colspan="5" class="tp-empty">${esc(t('auNone'))}</td></tr>`; return; }
  tb.innerHTML = _au.map(e => `<tr>
      <td><span class="ucreated">${esc(new Date(e.t*1000).toLocaleString(locale))}</span></td>
      <td><b>${esc(e.a||'')}</b></td>
      <td>${esc(t('au_' + e.x) === 'au_' + e.x ? e.x : t('au_' + e.x))}</td>
      <td><span class="ucreated">${esc(e.g||'')}</span></td>
      <td><span class="ucreated" title="${esc(e.ip||'')}">${esc([e.d, e.ip].filter(Boolean).join(' · '))}</span></td></tr>`).join('');
}

// ── Aviso de versión nueva ─────────────────────────────
// EN: New-version notice (from the releases published on GitHub; read only).
let _up = null;
async function upLoad(force) {
  try { const r = await fetch(force ? 'api/update/check' : 'api/update', force ? {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'} : undefined);
        if (r.ok) { _up = await r.json(); upRender(); if (force) setTimeout(() => upLoad(), 3000); } } catch(e) {}
}
function upRender() {
  const u = _up, b = document.getElementById('up-banner'), box = document.getElementById('up-body'); if (!u) return;
  const safe = /^https:\/\/github\.com\/gonzalovalenzuela\/labtower\//.test(u.url || '');
  if (b) {
    b.style.display = u.newer ? 'block' : 'none';
    b.innerHTML = u.newer ? `${esc(t('upBanner', u.latest, u.current))} ${safe ? `<a href="${esc(u.url)}" target="_blank" rel="noopener noreferrer">${esc(t('upSee'))}</a>` : ''}` : '';
  }
  if (!box) return;
  const when = u.checked ? new Date(u.checked*1000).toLocaleString(_lang === 'es' ? 'es-CL' : 'en-US') : t('upNever');
  const msg = !u.enabled ? t('upOff') : u.error ? `${t('upErr')} ${u.error}` : u.newer ? t('upHow') : u.latest ? t('upOk') : '';
  box.innerHTML = `<div class="tp-hint" style="border:0">${esc(t('upInstalled'))}: <b>${esc(u.current)}</b> · ${esc(t('upLatest'))}: <b>${esc(u.latest || '—')}</b> · ${esc(t('upChecked'))}: ${esc(when)}<br>${esc(msg)}</div>
    <div style="padding:0 18px 14px"><button class="btn-sec" data-on-click="upCheck" ${u.enabled ? '' : 'disabled'}>${esc(t('upCheck'))}</button></div>`;
}
function upCheck() { upLoad(true); }

// Funciones que el HTML puede invocar con data-on-* (lista cerrada; ver csp-bind.js).
// EN: Functions the HTML may call through data-on-* (closed list; see csp-bind.js).
if (window.cspRegister) cspRegister({ closeDrawer, closeModals, confirmDelete, doLogin, editUser, exCancel, exGo, exPlainToggle, logout, openDrawer, reauthCancel, reauthOk, saveUser, setLang, setTheme, upCheck, sfBegin, sfConfirm, sfDisable, sfRecDone, sfResetUser, auLoad, ssClose, ssCloseOthers, toggleNav, tpCheck, tpCreate, tpDelete, tpDownload, tpRestoreGo, tpRestoreOpen });
