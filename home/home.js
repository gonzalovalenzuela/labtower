// Idioma de la portada: el mismo que eligió el usuario en los módulos (clave «pi-lang»); sin elección, el del navegador.
// EN: Home page language: the one chosen in the modules ("pi-lang" key); with no choice, the browser's.
const H = {
  es: {hero: 'Panel de administración para tu homelab.<br>UPS, red, Proxmox, NAS, Wake-on-LAN y administración',
       ovN: 'Resumen', ovD: 'Estado general — UPS, Proxmox, red y el servidor en una pantalla',
       nutN: 'UPS Monitor', nutD: 'UPS — batería, carga y autonomía en tiempo real',
       netN: 'Net Monitor', netD: 'Escaneo de red — equipos, sistema operativo y puertos abiertos',
       pveN: 'Proxmox Monitor', pveD: 'Panel de nodos, VMs, contenedores y Ceph',
       nasN: 'NAS Monitor', nasD: 'Synology, TrueNAS y OpenMediaVault — discos, volúmenes, temperatura y red',
       dnsN: 'DNS Monitor', dnsD: 'Pi-hole y AdGuard Home — consultas, bloqueo y servidores DNS',
       wanN: 'WAN Monitor', wanD: 'Salida a internet — latencia, cortes, IP pública y velocidad',
       vpnN: 'VPN Monitor', vpnD: 'Tailscale, OpenVPN y WireGuard — quién está conectado y desde cuándo',
       uptN: 'Uptime Monitor', uptD: 'Servicios HTTP(S), TCP y DNS — disponibilidad, latencia y certificados',
       wolN: 'WOL Console', wolD: 'Wake-on-LAN — enciende equipos remotamente',
       admN: 'Admin Panel', admD: 'Usuarios y permisos, 2FA, respaldos y salud del sistema',
       gPower: 'Energía y servidores', gNet: 'Red', gTools: 'Herramientas', gSys: 'Sistema',
       chk: 'comprobando...', up: 'activo', warn: 'con avisos', fail: 'con fallas', down: 'sin respuesta'},
  en: {hero: 'Administration panel for your homelab.<br>UPS, network, Proxmox, NAS, Wake-on-LAN and administration',
       ovN: 'Overview', ovD: 'General status — UPS, Proxmox, network and the server on one screen',
       nutN: 'UPS Monitor', nutD: 'UPS — battery, load and runtime in real time',
       netN: 'Net Monitor', netD: 'Network scan — hosts, operating system and open ports',
       pveN: 'Proxmox Monitor', pveD: 'Dashboard of nodes, VMs, containers and Ceph',
       nasN: 'NAS Monitor', nasD: 'Synology, TrueNAS and OpenMediaVault — disks, volumes, temperature and network',
       dnsN: 'DNS Monitor', dnsD: 'Pi-hole and AdGuard Home — queries, blocking and DNS servers',
       wanN: 'WAN Monitor', wanD: 'Internet connection — latency, outages, public IP and speed',
       vpnN: 'VPN Monitor', vpnD: 'Tailscale, OpenVPN and WireGuard — who is connected and since when',
       uptN: 'Uptime Monitor', uptD: 'HTTP(S), TCP and DNS services — uptime, latency and certificates',
       wolN: 'WOL Console', wolD: 'Wake-on-LAN — turn devices on remotely',
       admN: 'Admin Panel', admD: 'Users and permissions, 2FA, backups and system health',
       gPower: 'Power & servers', gNet: 'Network', gTools: 'Tools', gSys: 'System',
       chk: 'checking...', up: 'active', warn: 'warnings', fail: 'failing', down: 'no response'}
};
let lang = 'en';
try { lang = localStorage.getItem('pi-lang') || ((navigator.language || '').toLowerCase().startsWith('es') ? 'es' : 'en'); } catch (e) {}
if (!H[lang]) lang = 'en';
document.documentElement.lang = lang;
for (const el of document.querySelectorAll('[data-h]')) {
  const k = el.getAttribute('data-h'), v = H[lang][k];
  if (v == null) continue;
  const n = el.getAttribute('data-n');
  if (n) el.textContent = n + ' ' + v; else el.innerHTML = v;
}

// Estado de cada módulo, junto a la flecha de su tarjeta: consulta su /api/health público (sin sesión; solo trae el estado global) con 3 s de espera.
// ok → verde «activo», degraded → amarillo «con avisos», fail (503) → rojo «con fallas», sin respuesta → gris «sin respuesta».
// EN: Status of every module, next to the arrow of its card: it queries its public /api/health (no session; only the overall status) with a 3 s timeout.
//     ok → green "active", degraded → yellow "warnings", fail (503) → red "failing", no answer → grey "no response".
const SERVICES = ['overview', 'wol', 'nut', 'net', 'pve', 'nas', 'dns', 'wan', 'vpn', 'uptime', 'admin'];
const stateOf = {};
for (const card of document.querySelectorAll('.app-card')) {
  const id = (card.getAttribute('href') || '').split('/')[1];
  if (!SERVICES.includes(id)) continue;
  const st = document.createElement('span'); st.className = 'app-state'; st.title = H[lang].chk;
  const dot = document.createElement('span'); dot.className = 'dot gray';
  const txt = document.createElement('span'); txt.className = 'app-state-txt'; txt.textContent = H[lang].chk;
  st.append(dot, txt);
  card.insertBefore(st, card.querySelector('.app-arrow'));
  stateOf[id] = {dot, txt, st};
}
async function checkService(id) {
  let level = 'down';
  try {
    const r = await fetch('/' + id + '/api/health', {signal: AbortSignal.timeout(3000), cache: 'no-store'});
    const d = await r.json().catch(() => ({}));
    level = d.status === 'ok' ? 'up' : d.status === 'degraded' ? 'warn' : d.status === 'fail' || r.status === 503 ? 'fail' : 'down';
  } catch (e) { level = 'down'; }
  const o = stateOf[id];
  o.dot.className = 'dot ' + ({up: 'green', warn: 'yellow', fail: 'red'}[level] || 'gray');
  o.txt.textContent = o.st.title = H[lang][level];
}
// Módulos que el admin apagó: su tarjeta no se muestra y no se consulta. / EN: Modules the admin turned off: the card is hidden and not queried.
fetch('/admin/api/disabled', {signal: AbortSignal.timeout(3000), cache: 'no-store'}).then(r => r.ok ? r.json() : {}).catch(() => ({})).then(d => {
  const off = d.disabled || [];
  for (const card of document.querySelectorAll('.app-card')) {
    const id = (card.getAttribute('href') || '').split('/')[1];
    if (off.includes(id)) { card.hidden = true; delete stateOf[id]; }
  }
  for (const id of Object.keys(stateOf)) checkService(id);
});
