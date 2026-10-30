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
       wolN: 'WOL Console', wolD: 'Wake-on-LAN — enciende equipos remotamente',
       admN: 'Admin Panel', admD: 'Usuarios y permisos, 2FA, respaldos y salud del sistema',
       chk: 'comprobando...', up: 'activo', down: 'sin respuesta'},
  en: {hero: 'Administration panel for your homelab.<br>UPS, network, Proxmox, NAS, Wake-on-LAN and administration',
       ovN: 'Overview', ovD: 'General status — UPS, Proxmox, network and the server on one screen',
       nutN: 'UPS Monitor', nutD: 'UPS — battery, load and runtime in real time',
       netN: 'Net Monitor', netD: 'Network scan — hosts, operating system and open ports',
       pveN: 'Proxmox Monitor', pveD: 'Dashboard of nodes, VMs, containers and Ceph',
       nasN: 'NAS Monitor', nasD: 'Synology, TrueNAS and OpenMediaVault — disks, volumes, temperature and network',
       dnsN: 'DNS Monitor', dnsD: 'Pi-hole and AdGuard Home — queries, blocking and DNS servers',
       wanN: 'WAN Monitor', wanD: 'Internet connection — latency, outages, public IP and speed',
       wolN: 'WOL Console', wolD: 'Wake-on-LAN — turn devices on remotely',
       admN: 'Admin Panel', admD: 'Users and permissions, 2FA, backups and system health',
       chk: 'checking...', up: 'active', down: 'no response'}
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

// Consulta una URL con 3 s de espera: si responde bien, el punto se pone verde y el texto dice «activo»; si no, «sin respuesta».
// EN: Query a URL with a 3 s timeout: if it answers fine, the dot turns green and the text says "active"; otherwise "no response".
async function checkService(url,dotId,lblId,name){
  try{
    const r=await fetch(url,{signal:AbortSignal.timeout(3000)});
    if(r.ok){
      document.getElementById(dotId).className='dot green';
      document.getElementById(lblId).textContent=name+' '+H[lang].up;
    }else throw new Error();
  }catch{
    document.getElementById(dotId).className='dot';
    document.getElementById(lblId).textContent=name+' '+H[lang].down;
  }
}
checkService('/wol/api/devices','dot-wol','lbl-wol','WOL');
checkService('/nut/api/config', 'dot-nut','lbl-nut','NUT');
