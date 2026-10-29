// Textos en inglés y español; el idioma es el elegido en los módulos (pi-lang) y, si no hay, el del navegador.
// EN: English and Spanish texts; the language is the one chosen in the modules (pi-lang) and, if none, the browser's.
const TXT = {
  en:{title:'Set a new password',sub:'For security, you must choose a new password before using LabTower.',notice:'This account still has its initial or temporary password.',cur:'Current password',nw:'New password (min. 8 characters)',rep:'Repeat new password',btn:'Save and continue',out:'Sign out',
      mismatch:'The passwords do not match',short:'The password must be at least 8 characters',same:'The new password must be different from the current one',fill:'Fill in all the fields',saving:'Saving…',conn:'Connection error: '},
  es:{title:'Define una contraseña nueva',sub:'Por seguridad, debes elegir una contraseña nueva antes de usar LabTower.',notice:'Esta cuenta aún tiene su contraseña inicial o temporal.',cur:'Contraseña actual',nw:'Contraseña nueva (mín. 8 caracteres)',rep:'Repite la contraseña nueva',btn:'Guardar y continuar',out:'Cerrar sesión',
      mismatch:'Las contraseñas no coinciden',short:'La contraseña debe tener al menos 8 caracteres',same:'La contraseña nueva debe ser distinta de la actual',fill:'Completa todos los campos',saving:'Guardando…',conn:'Error de conexión: '}
};
let lang = 'en';
try { lang = localStorage.getItem('pi-lang') || ''; } catch(e) {}
if (!TXT[lang]) lang = (navigator.language || '').toLowerCase().startsWith('es') ? 'es' : 'en';
const T = TXT[lang];
document.documentElement.lang = lang;
document.title = 'LabTower — ' + T.title;
document.getElementById('t-title').textContent = T.title;
document.getElementById('t-sub').textContent = T.sub;
document.getElementById('t-notice').textContent = T.notice;
document.getElementById('t-cur').textContent = T.cur;
document.getElementById('t-new').textContent = T.nw;
document.getElementById('t-rep').textContent = T.rep;
document.getElementById('btn').textContent = T.btn;
document.getElementById('t-out').textContent = T.out;

// Destino tras el cambio: solo rutas internas del mismo sitio (nunca //host ni URLs absolutas).
// EN: Destination after the change: only internal paths of the same site (never //host or absolute URLs).
let next = new URLSearchParams(location.search).get('next') || '/';
// Solo rutas del mismo sitio: sin «//», «/\» ni caracteres de control (el navegador ignora tabulaciones y saltos, y «/%09/host» sería «//host»).
if (!/^\/(?![\/\\])[^\x00-\x1f\x7f]*$/.test(next)) next = '/';

// Sin sesión, vuelve al destino (que mostrará su pantalla de login). Si la cuenta ya no necesita cambiar, entra directo.
// EN: Without a session, go back to the destination (which shows its own login). If the account no longer needs a change, go straight in.
fetch('api/self').then(r => r.json()).then(d => {
  if (!d.username || !d.must_change_password) location.replace(next);
}).catch(() => {});

document.addEventListener('keydown', e => { if (e.key === 'Enter') save(); });

// Muestra un mensaje de error encima del formulario.
// EN: Show an error message above the form.
function showErr(m) { const e = document.getElementById('err'); e.textContent = m; e.className = 'error-msg show'; }

// Valida en el cliente solo por comodidad (el servidor vuelve a validar todo) y envía el cambio.
// EN: Validate on the client only for convenience (the server validates everything again) and send the change.
async function save() {
  const cur = document.getElementById('cur').value;
  const p1  = document.getElementById('pw1').value;
  const p2  = document.getElementById('pw2').value;
  const btn = document.getElementById('btn');
  document.getElementById('err').className = 'error-msg';
  if (!cur || !p1 || !p2) return showErr(T.fill);
  if (p1.trim().length < 8) return showErr(T.short);
  if (p1 !== p2) return showErr(T.mismatch);
  if (p1 === cur) return showErr(T.same);
  btn.disabled = true; btn.textContent = T.saving;
  try {
    const r = await fetch('api/self_password', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({current_password: cur, new_password: p1})
    });
    const d = await r.json();
    if (!r.ok || !d.ok) {
      if (r.status === 401) { location.replace(next); return; }   // session expired: back to the login
      showErr(d.error || 'Error'); btn.disabled = false; btn.textContent = T.btn; return;
    }
    location.replace(next);
  } catch (e) {
    showErr(T.conn + e.message); btn.disabled = false; btn.textContent = T.btn;
  }
}

// Cierra la sesión pendiente y vuelve al destino.
// EN: Close the pending session and go back to the destination.
async function logout() {
  try { await fetch('api/logout', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}); } catch(e) {}
  location.replace(next);
}

// Funciones que el HTML puede invocar con data-on-* (lista cerrada; ver csp-bind.js).
// EN: Functions the HTML may call through data-on-* (closed list; see csp-bind.js).
if (window.cspRegister) cspRegister({ logout, save });
