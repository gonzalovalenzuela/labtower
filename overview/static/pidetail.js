// Vista detallada del servidor LabTower: se abre con «Abrir» en la tarjeta «LabTower Server» del Resumen.
// Pide /api/pidetail cada 5 s mientras está abierta. Usuarios conectados, procesos y servicios fallidos solo llegan para administradores.
// EN: Detailed LabTower Server view: opened with "Open" on the Overview's LabTower Server card.
//     It requests /api/pidetail every 5 s while open. Logged-in users, processes and failed services only arrive for administrators.
(function(){
const D={
 en:{title:'LabTower Server — details',close:'Close',sys:'System',host:'Host',os:'OS',kernel:'Kernel',arch:'Architecture',model:'Model',boot:'Booted',time:'Local time',
  uptime:'Uptime',temp:'Temperature',load:'Load (1/5/15 min)',cpu:'CPU',cores:'CPU per core',freq:'Frequency',gov:'Governor',mem:'Memory',ram:'RAM',swap:'Swap',
  avail:'Available',cached:'Cache',buffers:'Buffers',disks:'Storage',mount:'Mount',fs:'Type',size:'Size',used:'Used',net:'Network',iface:'Interface',state:'State',ip:'Addresses',
  rx:'Received',tx:'Sent',power:'Power and throttling',pwok:'Power supply OK, no throttling',uvNow:'Under-voltage now',fcNow:'Frequency capped now',thNow:'Throttled now',stNow:'Temperature limit now',
  uvB:'Under-voltage since boot',fcB:'Frequency capped since boot',thB:'Throttled since boot',stB:'Temperature limit since boot',thermal:'Temperature sensors',
  users:'Logged-in users',nousers:'Nobody logged in',user:'User',tty:'Terminal',from:'From',since:'Since',topcpu:'Top processes by CPU',topmem:'Top processes by memory',proc:'Process',pid:'PID',
  failed:'Failed services',nofail:'No failed services',failN:'failed',admin:'Users, processes and services are shown to administrators only.',err:'Could not load the details',loading:'Loading…',
  procs:'Processes',upd:'Updated'},
 es:{title:'LabTower Server — detalle',close:'Cerrar',sys:'Sistema',host:'Equipo',os:'Sistema operativo',kernel:'Kernel',arch:'Arquitectura',model:'Modelo',boot:'Encendido',time:'Hora local',
  uptime:'Tiempo encendido',temp:'Temperatura',load:'Carga (1/5/15 min)',cpu:'CPU',cores:'CPU por núcleo',freq:'Frecuencia',gov:'Gobernador',mem:'Memoria',ram:'RAM',swap:'Swap',
  avail:'Disponible',cached:'Caché',buffers:'Búferes',disks:'Almacenamiento',mount:'Montaje',fs:'Tipo',size:'Tamaño',used:'Usado',net:'Red',iface:'Interfaz',state:'Estado',ip:'Direcciones',
  rx:'Recibido',tx:'Enviado',power:'Energía y limitación',pwok:'Fuente de poder OK, sin limitación',uvNow:'Bajo voltaje ahora',fcNow:'Frecuencia limitada ahora',thNow:'Limitada ahora',stNow:'Límite de temperatura ahora',
  uvB:'Bajo voltaje desde el arranque',fcB:'Frecuencia limitada desde el arranque',thB:'Limitada desde el arranque',stB:'Límite de temperatura desde el arranque',thermal:'Sensores de temperatura',
  users:'Usuarios conectados',nousers:'Nadie conectado',user:'Usuario',tty:'Terminal',from:'Desde',since:'Desde',topcpu:'Procesos con más CPU',topmem:'Procesos con más memoria',proc:'Proceso',pid:'PID',
  failed:'Servicios con falla',nofail:'Sin servicios con falla',failN:'con falla',admin:'Usuarios, procesos y servicios solo los ven los administradores.',err:'No se pudo cargar el detalle',loading:'Cargando…',
  procs:'Procesos',upd:'Actualizado'}
};
const P=k=>(D[lang]||D.en)[k]||k;
const E=s=>esc(s==null?'':String(s));
const B=n=>{if(n==null)return'—';const u=['B','KB','MB','GB','TB'];let i=0;n=+n;while(n>=1024&&i<u.length-1){n/=1024;i++}return n.toFixed(i>=3?1:i?0:0)+' '+u[i]};
const dt=ts=>ts?PCT.ls(new Date(ts*1000)):'—';
const kv=(k,v)=>`<div class="pd-kv"><span>${E(k)}</span><b>${v==null||v===''?'—':v}</b></div>`;
const box=(t,inner,cls)=>`<section class="pd-box${cls?' '+cls:''}"><h3>${E(t)}</h3>${inner}</section>`;
const tbl=(head,rows)=>`<div class="pd-tw"><table class="pd-t"><thead><tr>${head.map(h=>`<th>${E(h)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
const PW={under_voltage:['uvNow','uvB'],freq_capped:['fcNow','fcB'],throttled:['thNow','thB'],soft_temp_limit:['stNow','stB']};
let modal=null,timer=null,busy=false,last=null;

function render(d){
  const h=d.host||{},m=d.mem_detail,fq=d.freq_mhz;
  const sys=box(P('sys'),kv(P('host'),E(h.hostname))+(d.model?kv(P('model'),E(d.model)):'')+kv(P('os'),E(h.os))+kv(P('kernel'),E(h.kernel)+' · '+E(h.arch))+kv(P('boot'),dt(d.boot))+kv(P('uptime'),d.uptime!=null?dur(d.uptime):'—')+kv(P('time'),dt(d.time)+' '+E(d.tz)));
  const cpu=box(P('cpu'),
    `<div class="row"><span class="l">CPU</span>${bar(d.cpu_total||0,75,92)}<span class="v">${(d.cpu_total||0).toFixed(0)}%</span></div>`+
    (d.cpu_cores||[]).map((c,i)=>`<div class="row"><span class="l">#${i}</span>${bar(c,75,92)}<span class="v">${c.toFixed(0)}%</span></div>`).join('')+
    kv(P('load'),d.load?d.load.join(' / '):'—')+(fq&&fq.cur!=null?kv(P('freq'),fq.cur+' MHz'+(fq.max?' / '+fq.max:'')):'')+(d.governor?kv(P('gov'),E(d.governor)):'')+
    (d.temp!=null?kv(P('temp'),d.temp+' °C'):'')+(d.procs_total!=null?kv(P('procs'),d.procs_total):''));
  let mem='';
  if(m&&m.total){
    const used=m.total-(m.available||0),pct=100*used/m.total;
    mem=box(P('mem'),`<div class="row"><span class="l">${P('ram')}</span>${bar(pct,80,92)}<span class="v">${pct.toFixed(0)}%</span></div>`+
      kv(P('used'),B(used)+' / '+B(m.total))+kv(P('avail'),B(m.available))+kv(P('cached'),B(m.cached))+kv(P('buffers'),B(m.buffers))+
      (m.swap_total?`<div class="row"><span class="l">${P('swap')}</span>${bar(100*m.swap_used/m.swap_total,50,80)}<span class="v">${(100*m.swap_used/m.swap_total).toFixed(0)}%</span></div>`+kv(P('swap'),B(m.swap_used)+' / '+B(m.swap_total)):kv(P('swap'),'—')));
  }
  const dk=(d.disks||[]).length?box(P('disks'),tbl([P('mount'),P('fs'),P('used'),'%'],d.disks.map(x=>`<tr><td title="${E(x.dev)}">${E(x.mount)}</td><td>${E(x.fs)}</td><td>${B(x.used)} / ${B(x.total)}</td><td>${bar(x.pct,85,95)}<span class="pd-n">${x.pct.toFixed(0)}%</span></td></tr>`)),'pd-wide'):'';
  const nt=(d.net||[]).length?box(P('net'),tbl([P('iface'),P('state'),P('ip'),P('rx'),P('tx')],d.net.map(x=>`<tr><td>${E(x.name)}${x.speed?` <span class="pd-dim">${x.speed} Mb/s</span>`:''}</td><td><span class="pd-dot ${x.state==='up'?'on':''}"></span>${E(x.state)}</td><td class="pd-mono">${x.addrs.length?x.addrs.map(E).join('<br>'):'—'}</td><td>${B(x.rx)}</td><td>${B(x.tx)}</td></tr>`)),'pd-wide'):'';
  let pw='';
  if(d.throttle){
    const items=[];for(const k of d.throttle.now)items.push(['crit',P(PW[k][0])]);for(const k of d.throttle.since_boot)if(!d.throttle.now.includes(k))items.push(['warn',P(PW[k][1])]);
    pw=box(P('power'),items.length?items.map(([c,t])=>`<div class="pd-pill ${c}">${E(t)}</div>`).join(''):`<div class="pd-pill ok">${P('pwok')}</div>`+'')
  }
  const th=(d.thermal||[]).length>1||(d.thermal||[]).length===1&&d.temp==null?box(P('thermal'),d.thermal.map(z=>kv(z.name,z.temp+' °C')).join('')):'';
  let adm='';
  if(d.full){
    const us=d.users||[];
    adm+=box(P('users'),us.length?tbl([P('user'),P('tty'),P('from'),P('since')],us.map(u=>`<tr><td>${E(u.user)}</td><td>${E(u.tty)}</td><td class="pd-mono">${E(u.host||'—')}</td><td>${dt(u.since)}</td></tr>`)):`<div class="pd-dim">${P('nousers')}</div>`);
    const pt=(l)=>tbl([P('proc'),P('pid'),P('user'),'CPU','RAM'],l.map(p=>`<tr><td>${E(p.name)}</td><td>${p.pid}</td><td>${E(p.user)}</td><td>${p.cpu.toFixed(1)}%</td><td>${B(p.rss)}</td></tr>`));
    adm+=box(P('topcpu'),pt(d.top_cpu||[]))+box(P('topmem'),pt(d.top_mem||[]));
    const f=d.failed_units;
    adm+=box(P('failed'),f==null?`<div class="pd-dim">—</div>`:f.length?f.map(u=>`<div class="pd-pill crit">${E(u)}</div>`).join(''):`<div class="pd-pill ok">${P('nofail')}</div>`);
  }
  return `<div class="pd-grid">${sys}${cpu}${mem}${pw}${th}${dk}${nt}${adm}</div>`+(d.full?'':`<div class="pd-dim pd-foot">${P('admin')}</div>`);
}

function paint(){
  if(!modal)return;
  modal.querySelector('.pd-h h2').textContent=P('title');
  modal.querySelector('.pd-x').textContent=P('close');
  const b=modal.querySelector('.pd-body');
  if(last&&last.err)b.innerHTML=`<div class="empty">${P('err')}</div>`;
  else if(last)b.innerHTML=render(last)+`<div class="pd-dim pd-foot">${P('upd')}: ${PCT.time(new Date(),true)}</div>`;
  else b.innerHTML=`<div class="empty">${P('loading')}</div>`;
}
async function load(){
  if(busy||!modal)return;busy=true;
  try{const r=await fetch('api/pidetail',{credentials:'same-origin'});if(!r.ok)throw 0;last=await r.json()}catch(e){last={err:1}}
  busy=false;
  if(modal){const sc=modal.querySelector('.pd-body').scrollTop;paint();modal.querySelector('.pd-body').scrollTop=sc}
}
function close(){if(timer)clearInterval(timer);timer=null;if(modal)modal.remove();modal=null;last=null;document.body.classList.remove('pd-open')}
function open(){
  if(modal)return;
  modal=document.createElement('div');modal.className='pd-modal';modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');
  modal.innerHTML='<div class="pd-card"><div class="pd-h"><h2></h2><button class="btn pd-x"></button></div><div class="pd-body"></div></div>';
  document.body.appendChild(modal);document.body.classList.add('pd-open');
  modal.addEventListener('click',e=>{if(e.target===modal||e.target.closest('.pd-x'))close()});
  paint();load();timer=setInterval(load,5000);
}
document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('[data-pi-open]');if(a){e.preventDefault();open()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&modal)close()});
// Al cambiar el idioma se vuelve a pintar / repaint when the language changes
document.addEventListener('pi-lang',paint);
})();
