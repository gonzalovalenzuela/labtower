// Pantalla de 2FA obligatorio: contraseña → QR y código → códigos de recuperación → al destino. El servidor solo acepta, para esta sesión
// pendiente, empezar y confirmar el propio 2FA.
// EN: Mandatory 2FA screen: password → QR and code → recovery codes → to the destination. For this pending session the server only accepts
//     starting and confirming one's own 2FA.
const TXT = {
  en:{title:'Turn on two-factor authentication',sub:'Administrators must use two-factor authentication. Turn it on to continue to LabTower.',cur:'Your password',btn1:'Continue',
      scan:'In your authenticator app (Google Authenticator, Aegis, 1Password…) choose «Scan QR code» and scan this:',manual:'Can’t scan it? Type this key:',code:'6-digit code it shows',btn2:'Confirm',
      rec:'Save these recovery codes now. Each works once if you lose the phone.',btn3:'Done, I saved them',out:'Sign out',fill:'Type your password',bad:'That code is not valid',conn:'Connection error: '},
  es:{title:'Activa la autenticación en dos pasos',sub:'Los administradores deben usar autenticación en dos pasos. Actívala para seguir a LabTower.',cur:'Tu contraseña',btn1:'Continuar',
      scan:'En tu app de autenticación (Google Authenticator, Aegis, 1Password…) elige «Escanear código QR» y escanea esto:',manual:'¿No puedes escanearlo? Escribe esta clave:',code:'Código de 6 dígitos que muestra',btn2:'Confirmar',
      rec:'Guarda ahora estos códigos de recuperación. Cada uno sirve una vez si pierdes el teléfono.',btn3:'Listo, los guardé',out:'Cerrar sesión',fill:'Escribe tu contraseña',bad:'Ese código no es válido',conn:'Error de conexión: '}
};
let lang = 'en';
try { lang = localStorage.getItem('pi-lang') || ''; } catch(e) {}
if (!TXT[lang]) lang = (navigator.language || '').toLowerCase().startsWith('es') ? 'es' : 'en';
const T = TXT[lang], $ = id => document.getElementById(id);
document.documentElement.lang = lang;
document.title = 'LabTower — ' + T.title;
[['t-title','title'],['t-sub','sub'],['t-cur','cur'],['btn1','btn1'],['t-scan','scan'],['t-manual','manual'],['t-code','code'],['btn2','btn2'],['t-rec','rec'],['btn3','btn3'],['t-out','out']]
  .forEach(([id, k]) => { $(id).textContent = T[k]; });

// Destino: solo rutas internas del mismo sitio (igual que el cambio de contraseña). / EN: Destination: same-site internal paths only.
let next = new URLSearchParams(location.search).get('next') || '/';
if (!/^\/(?![\/\\])[^\x00-\x1f\x7f]*$/.test(next)) next = '/';

// Sin sesión pendiente de 2FA, vuelve al destino. / EN: Without a session pending 2FA, go back to the destination.
fetch('api/self').then(r => r.json()).then(d => { if (!d.username || !d.must_setup_2fa) location.replace(next); }).catch(() => {});

function showErr(m) { const e = $('err'); e.textContent = m; e.className = 'error-msg show'; }
function clearErr() { $('err').className = 'error-msg'; }
async function post(url, body) {
  const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  return {r, d: await r.json().catch(() => ({}))};
}
// El QR lo genera el servidor (qrsvg); solo se acepta si tiene exactamente esa forma. / EN: The server draws the QR; only accepted with that exact shape.
const QR_OK = /^<svg xmlns="http:\/\/www\.w3\.org\/2000\/svg"[^<]*><rect[^<]*\/><path d="[MhvzL0-9,\- .]*" fill="#000"\/><\/svg>$/;

async function begin() {
  clearErr();
  const pw = $('cur').value; if (!pw) return showErr(T.fill);
  $('btn1').disabled = true;
  try {
    const {r, d} = await post('api/2fa/begin', {current_password: pw});
    if (r.status === 401) { location.replace(next); return; }
    if (!r.ok) { showErr(d.error || 'Error'); return; }
    if (QR_OK.test(d.qr || '')) $('qr').innerHTML = d.qr;
    $('key').textContent = String(d.secret || '').replace(/(.{4})/g, '$1 ').trim();
    $('step1').hidden = true; $('step2').hidden = false; $('code').focus();
  } catch (e) { showErr(T.conn + e.message); }
  finally { $('btn1').disabled = false; }
}
async function confirmCode() {
  clearErr();
  $('btn2').disabled = true;
  try {
    const {r, d} = await post('api/2fa/enable', {code: $('code').value.trim()});
    if (r.status === 401) { location.replace(next); return; }
    if (!r.ok) { showErr(r.status === 400 ? T.bad : (d.error || 'Error')); return; }
    $('rec').textContent = (d.recovery || []).join('\n');
    $('step2').hidden = true; $('step3').hidden = false;
  } catch (e) { showErr(T.conn + e.message); }
  finally { $('btn2').disabled = false; }
}
function done() { location.replace(next); }
async function logout() {
  try { await fetch('api/logout', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}); } catch(e) {}
  location.replace(next);
}
document.addEventListener('keydown', e => { if (e.key === 'Enter') { if (!$('step1').hidden) begin(); else if (!$('step2').hidden) confirmCode(); } });

// Funciones que el HTML puede invocar con data-on-* (lista cerrada; ver csp-bind.js). / EN: Functions the HTML may call (closed list).
if (window.cspRegister) cspRegister({ begin, confirmCode, done, logout });
