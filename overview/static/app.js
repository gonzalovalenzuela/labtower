// ───────── Textos / texts ─────────
const TXT={
 en:{title:'Overview',sortBtn:'Reorder',sortDone:'Done',sortReset:'Reset order',mvEarlier:'Move earlier',mvLater:'Move later',mvDrag:'Drag to move',home:'Home',kiosk:'Kiosk',logout:'Sign out',login:'Sign in',rememberMe:'Remember me',rem1d:'1 day',rem1w:'1 week',rem1m:'1 month',remForever:'Forever',exitk:'Exit kiosk',rint:'Refresh every',rman:'Manual',rnow:'Refresh now',ascroll:'Auto-scroll',updated:'Updated',allok:'All good',attn:'Attention',fail:'Failure',
  ups:'UPS Monitor',pve:'Proxmox',nas:'NAS Monitor',dns:'DNS Monitor',wan:'WAN Monitor',net:'Net Monitor',pi:'LabTower Server',ev:'Timeline',open:'Open →',noups:'No UPS servers configured',nopve:'No clusters configured',nonas:'No NAS configured',nodns:'No DNS servers configured',dnspct:'% blocked',issue_dnsdown:'DNS server unreachable',dnsq:'Queries',dnsblk:'Blocked',dnsms:'Response',dnsprot:'Blocking',protoff:'Paused',proton:'Active',protfail:'Failed',wanrtt:'Latency',wanloss:'Loss',wanup:'Uptime 24 h',wandown:'Download',wanip:'Public IP',wanstate:'Internet',wanon:'Online',wannet:'Down',wanlan:'No LAN',wanwait:'Measuring…',issue_wandown:'No internet access',issue_wanlan:'Local network unreachable',nasdisks:'Disks OK',nasvol:'Volume',issue_nasdown:'NAS unreachable',nonet:'No scan yet',noev:'No events yet',
  uptimeOnl:'Online',avail:'Availability',lastOut:'Last outage',noOut:'no outages recorded',onbattNow:'on battery now',
  mains:'On mains',batt:'On battery',lowb:'Low battery',unreach:'Unreachable',battery:'Battery',load:'Load',runtime:'Runtime',power:'Power',nodes:'Nodes',vms:'VMs',cts:'CTs',cpu:'CPU',mem:'Memory',disk:'Disk',temp:'Temp',uptime:'Uptime',
  online:'Online',known:'Known',offline:'Offline',newdev:'New devices',lastscan:'Last scan',scanning:'Scanning…',ceph:'Ceph',types:'By device type',nonew:'No new devices',
  ago:'ago',now:'now',min:'min',h:'h',d:'d',s:'s',power_uv:'Under-voltage',power_th:'Throttled',power_ok:'Power supply OK',invalid:'Invalid credentials',
  issue_batt:'is running on battery',issue_lowb:'has low battery',issue_srv:'unreachable',issue_node:'node offline',issue_cl:'cluster unreachable',issue_cpu:'high CPU',issue_ram:'high memory',issue_ceph:'Ceph',
  issue_temp:'Pi temperature high',issue_disk:'Pi disk almost full',issue_mem:'Pi memory high',issue_pwr:'Pi power supply problem',issue_scan:'scan error',h_temp:'Temp',h_min:'min',h_max:'max',h_uv:'Under-voltage',h_nouv:'no under-voltage',h_utemp:'UPS temperature 24 h'},
 es:{title:'Resumen',sortBtn:'Ordenar',sortDone:'Listo',sortReset:'Restablecer orden',mvEarlier:'Mover antes',mvLater:'Mover después',mvDrag:'Arrastra para mover',home:'Inicio',kiosk:'Kiosko',logout:'Cerrar sesión',login:'Entrar',rememberMe:'Recordarme',rem1d:'1 día',rem1w:'1 semana',rem1m:'1 mes',remForever:'Siempre',exitk:'Salir de kiosko',rint:'Actualizar cada',rman:'Manual',rnow:'Actualizar ahora',ascroll:'Auto-desplazar',updated:'Actualizado',allok:'Todo en orden',attn:'Atención',fail:'Falla',
  ups:'UPS Monitor',pve:'Proxmox',nas:'NAS Monitor',dns:'DNS Monitor',wan:'WAN Monitor',net:'Net Monitor',pi:'LabTower Server',ev:'Línea de tiempo',open:'Abrir →',noups:'Sin servidores UPS configurados',nopve:'Sin clusters configurados',nonas:'Sin NAS configurados',nodns:'Sin servidores DNS configurados',dnspct:'% bloqueado',issue_dnsdown:'Servidor DNS sin conexión',dnsq:'Consultas',dnsblk:'Bloqueadas',dnsms:'Respuesta',dnsprot:'Bloqueo',protoff:'Pausado',proton:'Activo',protfail:'Con falla',wanrtt:'Latencia',wanloss:'Pérdida',wanup:'Disponibilidad 24 h',wandown:'Bajada',wanip:'IP pública',wanstate:'Internet',wanon:'En línea',wannet:'Caído',wanlan:'Sin LAN',wanwait:'Midiendo…',issue_wandown:'Sin acceso a internet',issue_wanlan:'Red local sin respuesta',nasdisks:'Discos OK',nasvol:'Volumen',issue_nasdown:'NAS sin conexión',nonet:'Aún sin escaneo',noev:'Sin eventos todavía',
  uptimeOnl:'En línea',avail:'Disponibilidad',lastOut:'Último corte',noOut:'sin cortes registrados',onbattNow:'en batería ahora',
  mains:'En red eléctrica',batt:'Con batería',lowb:'Batería baja',unreach:'Sin conexión',battery:'Batería',load:'Carga',runtime:'Autonomía',power:'Consumo',nodes:'Nodos',vms:'VMs',cts:'CTs',cpu:'CPU',mem:'Memoria',disk:'Disco',temp:'Temp',uptime:'Encendida',
  online:'En línea',known:'Conocidos',offline:'Apagados',newdev:'Equipos nuevos',lastscan:'Último escaneo',scanning:'Escaneando…',ceph:'Ceph',types:'Por tipo de equipo',nonew:'Sin equipos nuevos',
  ago:'hace',now:'ahora',min:'min',h:'h',d:'d',s:'s',power_uv:'Subtensión',power_th:'Limitada',power_ok:'Fuente de poder OK',invalid:'Credenciales inválidas',
  issue_batt:'funciona con batería',issue_lowb:'tiene batería baja',issue_srv:'sin conexión',issue_node:'nodo caído',issue_cl:'cluster sin conexión',issue_cpu:'CPU alta',issue_ram:'memoria alta',issue_ceph:'Ceph',
  issue_temp:'temperatura alta de la Pi',issue_disk:'disco de la Pi casi lleno',issue_mem:'memoria de la Pi alta',issue_pwr:'problema de alimentación de la Pi',issue_scan:'error de escaneo',h_temp:'Temp.',h_min:'mín',h_max:'máx',h_uv:'Subtensión',h_nouv:'sin subtensión',h_utemp:'Temperatura UPS 24 h'}
};
let lang='en';try{lang=localStorage.getItem('pi-lang')||''}catch(e){}
if(!TXT[lang])lang=(navigator.language||'').toLowerCase().startsWith('es')?'es':'en';
const T=k=>TXT[lang][k]||k;
const $=id=>document.getElementById(id);
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// ───────── Utilidades / helpers ─────────
const LV={ok:0,none:0,warn:1,crit:2};
const worst=(...a)=>a.reduce((m,x)=>LV[x]>LV[m]?x:m,'ok');
const barCls=(p,w,c)=>p>=c?'c':p>=w?'w':'g';
const bar=(p,w,c)=>`<div class="bar ${barCls(p,w,c)}"><div style="width:${Math.max(0,Math.min(100,p))}%"></div></div>`;
const pill=(lv,txt)=>`<span class="pill ${lv}"><i></i>${esc(txt)}</span>`;
function dur(sec){sec=Math.floor(sec);if(sec<60)return sec+T('s');const m=Math.floor(sec/60);if(m<60)return m+' '+T('min');const h=Math.floor(m/60);if(h<24)return h+T('h')+(m%60?' '+(m%60)+T('min'):'');return Math.floor(h/24)+T('d')+' '+(h%24)+T('h')}
function ago(ts){const s=Math.floor(Date.now()/1000-ts);if(s<30)return T('now');return (lang==='es'?T('ago')+' ':'')+dur(s)+(lang==='es'?'':' '+T('ago'))}
async function jget(url){const r=await fetch(url,{credentials:'same-origin'});if(r.status===401||r.status===403){const e=new Error('auth');e.code=r.status;throw e}if(!r.ok)throw new Error(url+' '+r.status);return r.json()}
function spark(vals,cls){ // mini gráfico de línea / tiny line chart
  vals=vals.filter(v=>isFinite(v));if(vals.length<2)return '';
  const mx=Math.max(...vals,1),mn=0,W=300,H=40;
  const pts=vals.map((v,i)=>`${(i/(vals.length-1)*W).toFixed(1)},${(H-2-(v-mn)/(mx-mn)*(H-4)).toFixed(1)}`);
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><polyline points="${pts.join(' ')}" fill="none" stroke="var(--blue)" stroke-width="1.8" vector-effect="non-scaling-stroke"/><polyline points="0,${H} ${pts.join(' ')} ${W},${H}" fill="var(--blue-dim)" stroke="none"/></svg>`;
}
// Temperatura de la UPS (solo si el equipo la informa; NUT guarda 0 cuando no la tiene)
// EN: UPS temperature (only if the unit reports it; NUT stores 0 when it has none)
function upsTemp(h){
  const v=h.map(r=>r.temp).filter(x=>isFinite(x)&&x>0);if(v.length<2)return '';
  const lo=Math.floor(Math.min.apply(null,v)-1),hi=Math.max(Math.ceil(Math.max.apply(null,v)+1),lo+6),W=300,H=40,n=h.length;
  const pts=[];h.forEach((r,i)=>{if(r.temp>0)pts.push((i/(n-1)*W).toFixed(1)+','+(H-2-(r.temp-lo)/(hi-lo)*(H-4)).toFixed(1))});
  return `<div class="xh kp"><svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><polyline points="${pts.join(' ')}" fill="none" stroke="var(--amber)" stroke-width="1.6" vector-effect="non-scaling-stroke"/></svg><div class="hc"><i style="background:var(--amber)"></i>${T('h_utemp')} · ${v[v.length-1].toFixed(0)}° · ${T('h_min')} ${Math.min.apply(null,v).toFixed(0)}° · ${T('h_max')} ${Math.max.apply(null,v).toFixed(0)}°</div></div>`;
}
// Gráfico de varias líneas 0–100 % (CPU y memoria) / multi-line 0–100 % chart (CPU and memory)
function lchart(series){ // series: [{vals:[…],color}]
  const W=300,H=40,n=Math.max.apply(null,series.map(s=>s.vals.length));if(n<2)return '';
  const line=s=>s.vals.map((v,i)=>`${(i/(s.vals.length-1)*W).toFixed(1)},${(H-2-Math.max(0,Math.min(100,v))/100*(H-4)).toFixed(1)}`).join(' ');
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><line x1="0" y1="${H/2}" x2="${W}" y2="${H/2}" stroke="var(--border)" stroke-width="1" vector-effect="non-scaling-stroke"/>${series.map(s=>s.vals.length>1?`<polyline points="${line(s)}" fill="none" stroke="${s.color}" stroke-width="1.6" vector-effect="non-scaling-stroke"/>`:'').join('')}</svg>`;
}
// Temperatura de la Pi en 24 h con marcas de subtensión (rojo) y limitación (ámbar)
// EN: Pi temperature over 24 h with under-voltage (red) and throttling (amber) marks
function tchart(h){
  const S=(h&&h.samples)||[],every=h&&h.every||60;if(S.length<2)return '';
  const W=300,H=40,t1=Math.max(Date.now()/1000,S[S.length-1][0]),t0=Math.max(t1-86400,S[0][0]),span=Math.max(60,t1-t0);
  const tv=S.filter(s=>s[1]!=null).map(s=>s[1]);if(tv.length<2)return '';
  const lo=Math.floor(Math.min.apply(null,tv)-2),hi=Math.max(Math.ceil(Math.max.apply(null,tv)+2),lo+10);
  const X=t=>((t-t0)/span*W).toFixed(1),Y=v=>(H-2-(v-lo)/(hi-lo)*(H-4)).toFixed(1);
  let segs=[],cur=[],last=0,uv=0,pu=false,mark='';
  S.forEach(s=>{
    if(s[1]!=null){if(cur.length&&s[0]-last>Math.max(every*3,300)){segs.push(cur);cur=[]}cur.push(X(s[0])+','+Y(s[1]));last=s[0]}
    const u=!!(s[2]&9);if(u&&(!pu||(s[2]&8)))uv++;pu=u;
    if(u)mark+=`<line x1="${X(s[0])}" y1="0" x2="${X(s[0])}" y2="${H}" stroke="var(--red)" stroke-width="2" vector-effect="non-scaling-stroke"/>`;
    else if(s[2]&6)mark+=`<line x1="${X(s[0])}" y1="0" x2="${X(s[0])}" y2="${H}" stroke="var(--amber)" stroke-width="2" opacity=".55" vector-effect="non-scaling-stroke"/>`;
  });
  if(cur.length)segs.push(cur);
  const svg=`<svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${mark}${segs.map(p=>p.length>1?`<polyline points="${p.join(' ')}" fill="none" stroke="var(--blue)" stroke-width="1.6" vector-effect="non-scaling-stroke"/>`:'').join('')}</svg>`;
  const cap=`<div class="hc">${T('h_temp')} ${span>=82800?'24 h':dur(span)} · ${Math.min.apply(null,tv).toFixed(0)}–${Math.max.apply(null,tv).toFixed(0)}° · <i style="background:var(--red);margin-left:0"></i>${uv?`<b style="color:var(--red)">${T('h_uv')}: ${uv}</b>`:T('h_nouv')}</div>`;
  return `<div class="kp">${svg}${cap}</div>`;
}
// Une los historiales de los nodos de un cluster en tramos de 5 min / merge a cluster's node histories into 5-min buckets
function aggHist(c){
  const b={};((c.snap&&c.snap.data&&c.snap.data.nodes)||[]).forEach(n=>(n.history||[]).forEach(p=>{const k=Math.floor(p.ts/300),o=b[k]||(b[k]={c:0,m:0,n:0});o.c+=p.cpu;o.m+=p.mem;o.n++}));
  return Object.keys(b).map(Number).sort((x,y)=>x-y).map(k=>({cpu:b[k].c/b[k].n,mem:b[k].m/b[k].n,temp:b[k].tn?b[k].t/b[k].tn:null}));
}
function donut(parts){ // parts: [{label,n,color}]
  const tot=parts.reduce((a,p)=>a+p.n,0);if(!tot)return '';
  const R=15.9155;let off=25,segs='';
  parts.forEach(p=>{const l=p.n/tot*100;segs+=`<circle cx="21" cy="21" r="${R}" fill="none" stroke="${p.color}" stroke-width="6" stroke-dasharray="${l} ${100-l}" stroke-dashoffset="${off}"/>`;off-=l});
  return `<svg width="84" height="84" viewBox="0 0 42 42"><circle cx="21" cy="21" r="${R}" fill="none" stroke="var(--track)" stroke-width="6"/>${segs}<text x="21" y="23.5" text-anchor="middle" font-size="9" font-weight="700" fill="var(--text)">${tot}</text></svg>`;
}
const PAL=['#4361ee','#16a34a','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899','#84cc16','#0ea5e9','#d946ef','#14b8a6','#94a3b8'];

// ───────── Estado / state ─────────
let me=null,issues=[],hist={},histTs=0,timer=null,piH=null,piHTs=0,pveH={},pveHTs=0,nasH={},nasHTs=0,dnsH={},dnsHTs=0,wanH=[],wanHTs=0;
const lvl=(m)=>({readonly:1,execute:2,admin:3})[(me.permissions||{})[m]]||0;

// ───────── UPS ─────────
function renderUPS(d){
  const el=$('c-nut');let sev='ok',body='',n=0;
  for(const srv0 of (d.servers||[])){
    const srv=srv0.status||{},sid=srv0.id,sname=srv0.name||sid,where=`${sname} (${srv0.host}:${srv0.port})`;
    if(srv.error&&!Object.keys(srv.ups||{}).length){sev='crit';issues.push({lv:'crit',m:'ups',t:`${lang==='es'?'Servidor UPS':'UPS server'} ${where} ${T('issue_srv')}: ${srv.error}`,href:'/nut/'});body+=`<div class="unit"><div class="uh">${esc(where)} ${pill('crit',T('unreach'))}</div><div class="sub">${esc(srv.error)}</div></div>`;n++;continue}
    for(const [name,v] of Object.entries(srv.ups||{})){
      n++;const st=(v['ups.status']||'').split(/\s+/);const lb=st.includes('LB'),ob=st.includes('OB');
      const charge=parseFloat(v['battery.charge'])||0,load=parseFloat(v['ups.load'])||0,run=parseInt(v['battery.runtime'])||0;
            const m=lb?['crit',T('lowb')]:ob?['warn',T('batt')]:['ok',T('mains')];
      if(lb){issues.push({lv:'crit',m:'ups',t:`${name} ${T('issue_lowb')} (${charge.toFixed(0)}%)`,href:'/nut/'})}
      else if(ob){issues.push({lv:'warn',m:'ups',t:`${name} ${T('issue_batt')} (${charge.toFixed(0)}%, ${dur(run)})`,href:'/nut/'})}
      sev=worst(sev,m[0]);
      const h=hist[sid+'|'+name]||[];const last=h.length?h[h.length-1]:null;
      const us=(srv.stats||{})[name],ua=us&&us.avail||{};
      const avTxt=us?`<div class="sub">${us.on_battery?T('onbattNow'):(us.last?`${T('lastOut')}: ${esc(ago(us.last.end||us.last.start))} · ${dur(us.last.dur)}`:T('noOut'))}${ua['30d']!=null?` · ${T('avail')} 30 ${T('d')}: ${ua['30d']>=99.995?'100':ua['30d'].toFixed(2)}%`:''}</div>`:'';
      body+=`<div class="unit"><div class="uh">${esc(v['_desc']||name)} <span class="sub">${esc(name)}</span>${pill(m[0],m[1])}</div>
       <div class="row"><span class="l">${T('battery')}</span><div class="bar ${charge<=20?'c':charge<=50?'w':'g'}"><div style="width:${Math.max(0,Math.min(100,charge))}%"></div></div><span class="v">${charge.toFixed(0)}%</span></div>
       <div class="row"><span class="l">${T('load')}</span>${bar(load,70,90)}<span class="v">${load.toFixed(0)}%</span></div>
       <div class="kpis"><div class="kpi"><b>${run?dur(run):'—'}</b><span>${T('runtime')}</span></div><div class="kpi"><b>${last&&last.watts?Math.round(last.watts)+' W':'—'}</b><span>${T('power')}</span></div>${us&&us.streak!=null?`<div class="kpi"><b>${us.on_battery?'—':dur(us.streak)}</b><span>${T('uptimeOnl')}</span></div>`:''}</div>${avTxt}${spark(h.map(r=>r.load))}${upsTemp(h)}</div>`;
    }
  }
  el.innerHTML=`<div class="ch"><h2>${T('ups')}</h2>${n?pill(sev,sev==='ok'?'OK':sev==='warn'?T('attn'):T('fail')):''}<a class="go" href="/nut/">${T('open')}</a></div>`+(n?body:`<div class="empty">${T('noups')}</div>`);
  return sev;
}

// ───────── Franja de indicadores / KPI strip ─────────
// ───────── Proxmox ─────────
function pveChart(id){
  const a=pveH[id]||[];if(a.length<3)return '';
  return '<div class="kp">'+lchart([{vals:a.map(p=>p.cpu),color:'var(--blue)'},{vals:a.map(p=>p.mem),color:'#8b5cf6'},...(a.some(p=>p.temp!=null)?[{vals:(l=>a.map(p=>l=p.temp!=null?p.temp:l))(0),color:'var(--red)'}]:[])])+
    `<div class="hc"><i style="background:var(--blue)"></i>${T('cpu')}<i style="background:#8b5cf6"></i>${T('mem')}${a.some(p=>p.temp!=null)?`<i style="background:var(--red)"></i>${T('temp')}`:''} · ${dur(a.length*300)}</div></div>`;
}
function renderPVE(d){
  const el=$('c-pve');let sev='ok',body='';const cl=d.clusters||[];
  cl.forEach(c=>{
    const sn=c.snap||{},data=sn.data||{},nodes=data.nodes||[];let s='ok';
    const on=nodes.filter(x=>x.status==='online'),off=nodes.filter(x=>x.status!=='online');
    let vm=0,vmT=0,ct=0,ctT=0,cpuN=0,cpuD=0,mem=0,memD=0;
    on.forEach(x=>{(x.vms||[]).filter(v=>!v.template).forEach(v=>{vmT++;if(v.status==='running')vm++});(x.cts||[]).filter(v=>!v.template).forEach(v=>{ctT++;if(v.status==='running')ct++});cpuN+=(x.cpu||0)*(x.maxcpu||0);cpuD+=x.maxcpu||0;mem+=x.mem||0;memD+=x.maxmem||0});
    const cpu=cpuD?cpuN/cpuD*100:0,mp=memD?mem/memD*100:0;
    if(sn.error&&!nodes.length){s='crit';issues.push({lv:'crit',m:'pve',t:`${c.name}: ${T('issue_cl')}`,href:'/pve/'})}
    off.forEach(x=>{s='crit';issues.push({lv:'crit',m:'pve',t:`${c.name}/${x.name}: ${T('issue_node')}`,href:'/pve/'})});
    (c.alerts||[]).forEach(a=>{s=worst(s,'warn');issues.push({lv:'warn',m:'pve',t:`${c.name}/${a.node}: ${a.type==='cpu'?T('issue_cpu'):T('issue_ram')} (${a.value}%)`,href:'/pve/'})});
    const cs=data.ceph&&data.ceph.health&&data.ceph.health.status;
    if(cs&&cs!=='HEALTH_OK'){const l=cs==='HEALTH_ERR'?'crit':'warn';s=worst(s,l);issues.push({lv:l,m:'pve',t:`${c.name}: ${T('issue_ceph')} ${cs}`,href:'/pve/'})}
    sev=worst(sev,s);
    body+=`<div class="unit"><div class="uh">${esc(c.name)} ${pill(s,sn.error&&!nodes.length?T('unreach'):s==='ok'?'OK':s==='warn'?T('attn'):T('fail'))}</div>
     <div class="kpis"><div class="kpi"><b>${on.length}/${nodes.length}</b><span>${T('nodes')}</span></div><div class="kpi"><b>${vm}/${vmT}</b><span>${T('vms')}</span></div><div class="kpi"><b>${ct}/${ctT}</b><span>${T('cts')}</span></div>${cs?`<div class="kpi"><b style="font-size:1rem">${esc(cs.replace('HEALTH_',''))}</b><span>${T('ceph')}</span></div>`:''}</div>
     <div class="row"><span class="l">${T('cpu')}</span>${bar(cpu,70,90)}<span class="v">${cpu.toFixed(0)}%</span></div>
     <div class="row"><span class="l">${T('mem')}</span>${bar(mp,80,92)}<span class="v">${mp.toFixed(0)}%</span></div>${pveChart(c.id)}</div>`;
  });
  el.innerHTML=`<div class="ch"><h2>${T('pve')}</h2>${cl.length?pill(sev,sev==='ok'?'OK':sev==='warn'?T('attn'):T('fail')):''}<a class="go" href="/pve/">${T('open')}</a></div>`+(cl.length?body:`<div class="empty">${T('nopve')}</div>`);
  return sev;
}
// ───────── NAS ─────────
// Resumen de cada NAS Synology: estado, CPU, memoria, volumen más lleno y discos. Las alertas las calcula nas-monitor; aquí solo se traducen.
// EN: Summary of every Synology NAS: status, CPU, memory, fullest volume and disks. The alerts are computed by nas-monitor; here they are only translated.
const NAS_AL={
 en:{system:'system partition failure',power:'power supply failure',fan:'fan failure',temp:'high temperature',cpu:'high CPU',mem:'high memory',disk:'disk problem',disk_temp:'disk too hot',raid:'volume problem',vol_full:'volume almost full',upgrade:'DSM update available'},
 es:{system:'falla en la partición del sistema',power:'falla en la fuente de poder',fan:'falla en un ventilador',temp:'temperatura alta',cpu:'CPU alta',mem:'memoria alta',disk:'problema en un disco',disk_temp:'disco muy caliente',raid:'problema en un volumen',vol_full:'volumen casi lleno',upgrade:'hay una actualización de DSM'}
};
function nasAl(a){
  const w=(NAS_AL[lang]||NAS_AL.en)[a.type]||a.type;
  const unit={temp:' °C',disk_temp:' °C',cpu:'%',mem:'%',vol_full:'%'}[a.type];
  return (a.item?a.item+': ':'')+w+(unit!==undefined&&a.value!=null?` (${a.value}${unit})`:'');
}
// Une el historial de un NAS en tramos de 5 min / merge a NAS history into 5-min buckets
function aggNas(n){
  const b={};(n.history||[]).forEach(p=>{if(p.cpu==null&&p.mem==null)return;const k=Math.floor(p.ts/300),o=b[k]||(b[k]={c:0,m:0,t:0,tn:0,n:0});o.c+=p.cpu||0;o.m+=p.mem||0;if(p.temp!=null){o.t+=p.temp;o.tn++}o.n++});
  return Object.keys(b).map(Number).sort((x,y)=>x-y).map(k=>({cpu:b[k].c/b[k].n,mem:b[k].m/b[k].n}));
}
function nasChart(id){
  const a=nasH[id]||[];if(a.length<3)return '';
  return '<div class="kp">'+lchart([{vals:a.map(p=>p.cpu),color:'var(--blue)'},{vals:a.map(p=>p.mem),color:'#8b5cf6'},...(a.some(p=>p.temp!=null)?[{vals:(l=>a.map(p=>l=p.temp!=null?p.temp:l))(0),color:'var(--red)'}]:[])])+
    `<div class="hc"><i style="background:var(--blue)"></i>${T('cpu')}<i style="background:#8b5cf6"></i>${T('mem')}${a.some(p=>p.temp!=null)?`<i style="background:var(--red)"></i>${T('temp')}`:''} · ${dur(a.length*300)}</div></div>`;
}
function renderNAS(d){
  const el=$('c-nas');let sev='ok',body='';const L=d.nas||[];
  L.forEach(n=>{
    const sn=n.snap||{},data=sn.data||{},sy=data.system||{};let s='ok';
    if(sn.error){s='crit';issues.push({lv:'crit',m:'nas',t:`${n.name}: ${T('issue_nasdown')}`,href:'/nas/'})}
    (data.alerts||[]).forEach(a=>{if(a.lv==='info')return;s=worst(s,a.lv);issues.push({lv:a.lv,m:'nas',t:`${n.name}: ${nasAl(a)}`,href:'/nas/'})});
    sev=worst(sev,s);
    const disks=data.disks||[],dOk=disks.filter(x=>x.lv==='ok').length,vols=(data.raids||[]).filter(x=>x.pct!=null&&!x.pool),vmax=vols.reduce((m,x)=>x.pct>m.pct?x:m,{pct:-1});
    const cpu=data.cpu&&data.cpu.pct,mem=data.mem&&data.mem.pct;
    body+=`<div class="unit"><div class="uh">${esc(n.name)} <span class="sub">${esc(sy.model||'')}</span>${pill(s,sn.error&&!data.system?T('unreach'):s==='ok'?'OK':s==='warn'?T('attn'):T('fail'))}</div>
     <div class="kpis"><div class="kpi"><b>${disks.length?dOk+'/'+disks.length:'—'}</b><span>${T('nasdisks')}</span></div><div class="kpi"><b>${sy.temp!=null?sy.temp+'°':'—'}</b><span>${T('temp')}</span></div><div class="kpi"><b>${sy.uptime?dur(sy.uptime):'—'}</b><span>${T('uptime')}</span></div></div>
     ${cpu!=null?`<div class="row"><span class="l">${T('cpu')}</span>${bar(cpu,70,90)}<span class="v">${cpu.toFixed(0)}%</span></div>`:''}
     ${mem!=null?`<div class="row"><span class="l">${T('mem')}</span>${bar(mem,80,92)}<span class="v">${mem.toFixed(0)}%</span></div>`:''}
     ${vmax.pct>=0?`<div class="row"><span class="l">${T('nasvol')}</span>${bar(vmax.pct,80,90)}<span class="v">${vmax.pct.toFixed(0)}%</span></div>`:''}${nasChart(n.id)}</div>`;
  });
  el.innerHTML=`<div class="ch"><h2>${T('nas')}</h2>${L.length?pill(sev,sev==='ok'?'OK':sev==='warn'?T('attn'):T('fail')):''}<a class="go" href="/nas/">${T('open')}</a></div>`+(L.length?body:`<div class="empty">${T('nonas')}</div>`);
  return sev;
}
// ───────── DNS (Pi-hole / AdGuard) ─────────
// EN: Summary of every DNS server (Pi-hole / AdGuard Home): status, queries, % blocked, response and blocking. Alerts are computed by dns-monitor; here they are only translated.
const DNS_AL={
 en:{blocking_off:'blocking is paused',blocking_failed:'blocking failed',no_lists:'no domains in the block lists',slow_upstream:'slow upstream DNS'},
 es:{blocking_off:'el bloqueo está pausado',blocking_failed:'el bloqueo falló',no_lists:'no hay dominios en las listas de bloqueo',slow_upstream:'DNS de salida lento'}
};
function dnsAl(a){const w=(DNS_AL[lang]||DNS_AL.en)[a.type]||a.type;return w+(a.type==='slow_upstream'&&a.value!=null?` (${a.value} ms)`:'')}
// Historial de % bloqueado de un servidor DNS en tramos de 5 min / merge a DNS server's % blocked history into 5-min buckets
function aggDns(n){
  const b={};(n.history||[]).forEach(p=>{if(p.pct==null)return;const k=Math.floor(p.ts/300),o=b[k]||(b[k]={v:0,n:0});o.v+=p.pct;o.n++});
  return Object.keys(b).map(Number).sort((x,y)=>x-y).map(k=>b[k].v/b[k].n);
}
function dnsChart(id){
  const a=dnsH[id]||[];if(a.length<3)return '';
  // El % bloqueado ronda valores bajos: se amplía al rango real para que se vea la variación / zoomed to the real range so the variation is visible
  let lo=Math.min.apply(null,a),hi=Math.max.apply(null,a);if(hi-lo<4){const m=(hi+lo)/2;lo=m-2;hi=m+2}
  const v=a.map(x=>(x-lo)/(hi-lo)*100),f=x=>Math.max(0,Math.round(x));
  return '<div class="kp">'+lchart([{vals:v,color:'#10b981'}])+`<div class="hc"><i style="background:#10b981"></i>${T('dnspct')} ${f(lo)}–${f(hi)}% · ${dur(a.length*300)}</div></div>`;
}
function renderDNS(d){
  const el=$('c-dns');let sev='ok',body='';const L=d.servers||[];
  L.forEach(n=>{
    const sn=n.snap||{},data=sn.data,off=!!sn.error;let s='ok';
    if(off){s='crit';issues.push({lv:'crit',m:'dns',t:`${n.name}: ${T('issue_dnsdown')}`,href:'/dns/'})}
    ((data&&data.alerts)||[]).forEach(a=>{if(a.lv==='info')return;s=worst(s,a.lv);issues.push({lv:a.lv,m:'dns',t:`${n.name}: ${dnsAl(a)}`,href:'/dns/'})});
    sev=worst(sev,s);
    const pr=data?({enabled:T('proton'),disabled:T('protoff'),failed:T('protfail')}[data.blocking]||'—'):'—';
    body+=`<div class="unit"><div class="uh">${esc(n.name)} <span class="sub">${esc(n.type==='adguard'?'AdGuard':'Pi-hole')}</span>${pill(s,off&&!data?T('unreach'):s==='ok'?'OK':s==='warn'?T('attn'):T('fail'))}</div>
     <div class="kpis"><div class="kpi"><b>${data?esc(Number(data.queries||0).toLocaleString(lang==='es'?'es-CL':'en-GB')):'—'}</b><span>${T('dnsq')}</span></div><div class="kpi"><b>${data&&data.pct!=null?esc(data.pct)+'%':'—'}</b><span>${T('dnsblk')}</span></div><div class="kpi"><b>${data&&data.ms!=null?esc(data.ms)+' ms':'—'}</b><span>${T('dnsms')}</span></div></div>
     <div class="row"><span class="l">${T('dnsprot')}</span><span class="v">${esc(pr)}</span></div>${dnsChart(n.id)}</div>`;
  });
  el.innerHTML=`<div class="ch"><h2>${T('dns')}</h2>${L.length?pill(sev,sev==='ok'?'OK':sev==='warn'?T('attn'):T('fail')):''}<a class="go" href="/dns/">${T('open')}</a></div>`+(L.length?body:`<div class="empty">${T('nodns')}</div>`);
  return sev;
}
// ───────── WAN (internet) ─────────
const WAN_AL={
 en:{loss:'packet loss',latency:'high latency',dns_slow:'slow DNS lookup',dns_fail:'DNS lookup failed'},
 es:{loss:'pérdida de paquetes',latency:'latencia alta',dns_slow:'resolución DNS lenta',dns_fail:'falló la resolución DNS'}
};
function wanAl(a){const w=(WAN_AL[lang]||WAN_AL.en)[a.type]||a.type;const u={loss:'%',latency:' ms',dns_slow:' ms'}[a.type];return w+(u!==undefined&&a.value!=null?` (${Math.round(a.value*10)/10}${u})`:'')}
// Latencia de WAN de las últimas 24 h: línea azul con espacios donde no hubo respuesta y franjas rojas donde se cayó el enlace
// EN: WAN latency over the last 24 h: blue line with gaps where there was no reply and red bands where the link was down
function wanChart(){
  const a=wanH;if(a.length<3)return '';
  const v=a.map(r=>r.rtt).filter(x=>x!=null&&isFinite(x));if(v.length<2)return '';
  const W=300,H=40,mx=Math.max.apply(null,v)*1.15||1,n=a.length,segs=[];let cur=[];
  a.forEach((r,i)=>{if(r.rtt!=null&&isFinite(r.rtt))cur.push([(i/(n-1)*W).toFixed(1),(H-2-r.rtt/mx*(H-4)).toFixed(1)]);else if(cur.length){segs.push(cur);cur=[]}});if(cur.length)segs.push(cur);
  const down=a.map((r,i)=>r.up===0?`<rect x="${(i/(n-1)*W-1).toFixed(1)}" y="0" width="2.5" height="${H}" fill="var(--red)" opacity=".35"/>`:'').join('');
  const pl=segs.map(g=>g.length>1?`<polygon points="${g[0][0]},${H} ${g.map(q=>q.join(',')).join(' ')} ${g[g.length-1][0]},${H}" fill="var(--blue-dim)"/><polyline points="${g.map(q=>q.join(',')).join(' ')}" fill="none" stroke="var(--blue)" stroke-width="1.6" vector-effect="non-scaling-stroke"/>`:'').join('');
  const lo=Math.min.apply(null,v),hi=Math.max.apply(null,v),f=x=>Math.round(x*10)/10;
  return `<div class="kp"><svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${down}${pl}</svg><div class="hc"><i style="background:var(--blue)"></i>${T('wanrtt')} ${f(lo)}–${f(hi)} ms · ${dur(a[n-1].ts-a[0].ts)}</div></div>`;
}
function renderWAN(d){
  const el=$('c-wan'),s0=d.snap;let sev='ok',body='';
  if(!s0){body=`<div class="empty">${T('wanwait')}</div>`}
  else{
    if(!s0.up){sev='crit';issues.push({lv:'crit',m:'wan',t:T(s0.scope==='lan'?'issue_wanlan':'issue_wandown'),href:'/wan/'})}
    (s0.alerts||[]).forEach(a=>{if(a.lv==='info'||a.type.indexOf('down_')===0)return;sev=worst(sev,a.lv);issues.push({lv:a.lv,m:'wan',t:wanAl(a),href:'/wan/'})});
    const sp=(d.speed||[]).filter(x=>!x.error&&x.down!=null),ls=sp.length?sp[sp.length-1]:null,up=(d.uptime||{})['24h'];
    body=`<div class="unit"><div class="uh">${T('wanstate')} ${pill(sev,!s0.up?T(s0.scope==='lan'?'wanlan':'wannet'):sev==='ok'?T('wanon'):T('attn'))}</div>
     <div class="kpis"><div class="kpi"><b>${s0.rtt!=null?Math.round(s0.rtt*10)/10+' ms':'—'}</b><span>${T('wanrtt')}</span></div><div class="kpi"><b>${s0.loss!=null?Math.round(s0.loss*10)/10+'%':'—'}</b><span>${T('wanloss')}</span></div><div class="kpi"><b>${ls?Math.round(ls.down)+' Mb/s':'—'}</b><span>${T('wandown')}</span></div></div>
     ${wanChart()}
     ${up!=null?`<div class="row"><span class="l">${T('wanup')}</span><span class="v">${up}%</span></div>`:''}
     <div class="row"><span class="l">${T('wanip')}</span><span class="v">${esc(s0.public_ip||'—')}</span></div></div>`;
  }
  el.innerHTML=`<div class="ch"><h2>${T('wan')}</h2>${s0?pill(sev,sev==='ok'?'OK':sev==='warn'?T('attn'):T('fail')):''}<a class="go" href="/wan/">${T('open')}</a></div>`+body;
  return sev;
}
// ───────── Net ─────────
const TYPE_SH_EN={computer:'PC',phone:'Phone',router:'Router',switch:'Switch',ap:'Wi-Fi',storage:'NAS',tv:'TV',camera:'Cam',appliance:'Appl.',printer:'Print.',tablet:'Tablet',console:'Console',server:'Server',voip:'VoIP',ups:'UPS',speaker:'Speaker',other:'Other'};
const TYPE_SH_ES={computer:'PC',phone:'Teléf.',router:'Router',switch:'Switch',ap:'Wi-Fi',storage:'NAS',tv:'TV',camera:'Cám.',appliance:'Electro.',printer:'Impres.',tablet:'Tablet',console:'Consola',server:'Servidor',voip:'Tel. IP',ups:'UPS',speaker:'Altavoz',other:'Otro'};
const TYPE_ES={computer:'Computador',phone:'Teléfono',router:'Router',switch:'Switch',ap:'AP Wi-Fi',storage:'Almacenamiento',tv:'TV',camera:'Cámara',appliance:'Electrodoméstico',printer:'Impresora',tablet:'Tablet',console:'Consola de juegos',server:'Servidor',voip:'Teléfono IP',ups:'UPS',speaker:'Altavoz inteligente',other:'Otro'};
const TYPE_EN={computer:'Computer',phone:'Phone',router:'Router',switch:'Switch',ap:'Wi-Fi AP',storage:'Storage',tv:'TV',camera:'Camera',appliance:'Appliance',printer:'Printer',tablet:'Tablet',console:'Game Console',server:'Server',voip:'IP Phone',ups:'UPS',speaker:'Smart Speaker',other:'Other'};
function renderNet(d){
  const el=$('c-net'),hosts=d.hosts||[],sc=d.scan||{};let sev='ok';
  const on=hosts.filter(h=>h.online),off=hosts.length-on.length;
  const now=Date.now()/1000;
  const fresh=hosts.filter(h=>h.new_device&&now-(h.first_seen||0)<48*3600).sort((a,b)=>b.first_seen-a.first_seen);
  if(sc.error){sev='warn';issues.push({lv:'warn',m:'net',t:`${T('issue_scan')}: ${sc.error}`,href:'/net/'})}
  const cnt={};on.forEach(h=>{const k=h.device_type||'other';cnt[k]=(cnt[k]||0)+1});
  const parts=Object.entries(cnt).sort((a,b)=>b[1]-a[1]).map(([k,n],i)=>({label:(lang==='es'?TYPE_ES:TYPE_EN)[k]||k,short:(lang==='es'?TYPE_SH_ES:TYPE_SH_EN)[k]||k,n,color:PAL[Math.min(i,PAL.length-1)]}));
  const scanTxt=sc.running?T('scanning'):sc.finished?dur(Date.now()/1000-sc.finished):'—';
  el.innerHTML=`<div class="ch"><h2>${T('net')}</h2>${hosts.length?pill(sev,sev==='ok'?'OK':T('attn')):''}<a class="go" href="/net/">${T('open')}</a></div>`+
   (hosts.length?`<div class="kpis"><div class="kpi"><b>${on.length}</b><span>${T('online')}</span></div><div class="kpi"><b>${hosts.length}</b><span>${T('known')}</span></div><div class="kpi"><b>${off}</b><span>${T('offline')}</span></div><div class="kpi"><b style="font-size:1rem;white-space:nowrap">${esc(scanTxt)}</b><span>${T('lastscan')}</span></div></div>
   <div class="donutbox">${donut(parts)}<div class="legend${parts.length>5?' lg2':''}">${parts.map(p=>`<div><i style="background:${p.color}"></i><span class="lb"><span class="lf">${esc(p.label)}</span><span class="ls">${esc(p.short)}</span></span><span class="ln">· ${p.n}</span></div>`).join('')}</div></div>
   <div><div class="sub" style="margin-bottom:5px;font-weight:600">${T('newdev')} (48 ${T('h')})</div>${fresh.length?`<div class="list">${fresh.slice(0,5).map(h=>`<div>${pill('warn','NEW')}<code data-nethost="${esc(h.ip)}" data-nethost-click="1">${esc(h.ip)}</code><span>${esc(h.alias||h.hostname||h.vendor||'')}</span></div>`).join('')}</div>`:`<div class="empty">${T('nonew')}</div>`}</div>`:`<div class="empty">${T('nonet')}</div>`);
  return hosts.length?sev:'ok';
}
// ───────── Pi ─────────
function renderPi(s){
  let sev='ok';const el=$('c-pi');
  if(s.temp!=null){const l=s.temp>=80?'crit':s.temp>=70?'warn':'ok';sev=worst(sev,l);if(l!=='ok')issues.push({lv:l,m:'pi',t:`${T('issue_temp')} (${s.temp}°C)`})}
  if(s.disk){const l=s.disk.pct>=95?'crit':s.disk.pct>=90?'warn':'ok';sev=worst(sev,l);if(l!=='ok')issues.push({lv:l,m:'pi',t:`${T('issue_disk')} (${s.disk.pct}%)`})}
  if(s.mem&&s.mem.pct>=92){sev=worst(sev,'warn');issues.push({lv:'warn',m:'pi',t:`${T('issue_mem')} (${s.mem.pct}%)`})}
  if(s.power&&(s.power.under_voltage||s.power.throttled||s.power.temp_limit)){sev=worst(sev,'warn');issues.push({lv:'warn',m:'pi',t:T('issue_pwr')})}
  const cpu=s.cpu==null?0:s.cpu;
  el.innerHTML=`<div class="ch"><h2>${T('pi')}</h2>${pill(sev,sev==='ok'?'OK':sev==='warn'?T('attn'):T('fail'))}<a class="go" href="#" data-pi-open="1">${T('open')}</a></div>
   ${s.model?`<div class="sub">${esc(s.model)}</div>`:''}
   <div class="kpis">${s.temp!=null?`<div class="kpi"><b>${s.temp}°</b><span>${T('temp')}</span></div>`:''}<div class="kpi"><b>${s.uptime!=null?dur(s.uptime):'—'}</b><span>${T('uptime')}</span></div>${s.load?`<div class="kpi"><b>${s.load[0]}</b><span>load</span></div>`:''}</div>
   ${piH?tchart(piH):''}
   <div class="row"><span class="l">${T('cpu')}</span>${bar(cpu,75,92)}<span class="v">${cpu.toFixed(0)}%</span></div>
   ${s.mem?`<div class="row"><span class="l">${T('mem')}</span>${bar(s.mem.pct,80,92)}<span class="v">${s.mem.pct.toFixed(0)}%</span></div>`:''}
   ${s.disk?`<div class="row"><span class="l">${T('disk')}</span>${bar(s.disk.pct,85,95)}<span class="v">${s.disk.pct.toFixed(0)}%</span></div>`:''}
   ${s.power?`<div class="sub">${s.power.under_voltage?pill('warn',T('power_uv'))+' ':''}${s.power.throttled?pill('warn',T('power_th'))+' ':''}${!s.power.under_voltage&&!s.power.throttled?pill('ok',T('power_ok')):''}</div>`:''}`;
  return sev;
}
// ───────── Eventos / timeline ─────────
const EVT={
 en:{ups_lowb:'{n}: low battery ({pct})',ups_batt:'{n}: on battery ({pct})',ups_mains:'{n}: mains power restored ({pct})',ups_other:'{n}: status {st}',ups_srv_down:'UPS server {n} unreachable: {e}',ups_srv_up:'UPS server {n} reachable again',
  pve_cl_down:'{c}: cluster unreachable',pve_cl_up:'{c}: cluster reachable again',pve_node_on:'{c}/{n}: node online',pve_node_off:'{c}/{n}: node {st}',pve_ceph:'{c}: Ceph {a} → {b}',
  dns_off:'{n}: blocking paused',dns_on:'{n}: blocking active',dns_fail:'{n}: blocking failed',dns_down:'{n}: DNS server unreachable',dns_up:'{n}: DNS server reachable again',
  wan_down_internet:'Internet connection down',wan_down_lan:'Internet down (local network too)',wan_up:'Internet connection restored after {d} s',wan_ip:'Public IP changed to {ip}',
  nas_down:'{n}: NAS unreachable',nas_up:'{n}: NAS reachable again',nas_sys:'{n}: system or power failure',nas_raid:'{n}/{v}: volume status {st}',nas_disk:'{n}/{d}: disk status {st}',
  net_first:'First scan: {n} hosts found',net_new:'New device: {ip} {n} {v}',net_up:'Back online: {ip} {n}',net_down:'Went offline: {ip} {n}',net_new_n:'{n} new devices',net_up_n:'{n} hosts back online',net_down_n:'{n} hosts went offline'},
 es:{ups_lowb:'{n}: batería baja ({pct})',ups_batt:'{n}: funcionando con batería ({pct})',ups_mains:'{n}: volvió la red eléctrica ({pct})',ups_other:'{n}: estado {st}',ups_srv_down:'Servidor UPS {n} sin conexión: {e}',ups_srv_up:'Servidor UPS {n} otra vez disponible',
  pve_cl_down:'{c}: cluster sin conexión',pve_cl_up:'{c}: cluster otra vez disponible',pve_node_on:'{c}/{n}: nodo en línea',pve_node_off:'{c}/{n}: nodo {st}',pve_ceph:'{c}: Ceph {a} → {b}',
  dns_off:'{n}: bloqueo pausado',dns_on:'{n}: bloqueo activo',dns_fail:'{n}: el bloqueo falló',dns_down:'{n}: servidor DNS sin conexión',dns_up:'{n}: servidor DNS otra vez disponible',
  wan_down_internet:'Se cayó la conexión a internet',wan_down_lan:'Internet caído (la red local también)',wan_up:'Volvió internet tras {d} s',wan_ip:'La IP pública cambió a {ip}',
  nas_down:'{n}: NAS sin conexión',nas_up:'{n}: NAS otra vez disponible',nas_sys:'{n}: falla del sistema o de la fuente de poder',nas_raid:'{n}/{v}: estado del volumen {st}',nas_disk:'{n}/{d}: estado del disco {st}',
  net_first:'Primer escaneo: {n} equipos encontrados',net_new:'Equipo nuevo: {ip} {n} {v}',net_up:'Volvió a estar en línea: {ip} {n}',net_down:'Dejó de responder: {ip} {n}',net_new_n:'{n} equipos nuevos',net_up_n:'{n} equipos volvieron a estar en línea',net_down_n:'{n} equipos dejaron de responder'}
};
// Texto de un evento en el idioma actual; si la clave no se conoce, el texto en inglés guardado / Event text in the current language; unknown key → stored English text
function evText(e){const t=e.k&&EVT[lang][e.k];return t?t.replace(/\{(\w+)\}/g,(_,k)=>(e.p&&e.p[k]!=null?e.p[k]:'')).replace(/\s+/g,' ').trim():e.tx}
// Texto del evento con la IP (si la trae) marcada para la tarjeta de Net Monitor. Todo va escapado; el span lo crea este código.
// EN: Event text with the IP (if any) marked for the Net Monitor card. Everything is escaped; the span is created by this code.
function evHtml(e){const s=esc(evText(e)),ip=e.m==='net'&&e.p&&/^\d{1,3}(\.\d{1,3}){3}$/.test(String(e.p.ip||''))?String(e.p.ip):'';return ip&&s.includes(ip)?s.replace(ip,`<span data-nethost="${ip}" data-nethost-click="1">${ip}</span>`):s}
function renderEvents(list){
  $('c-ev').innerHTML=`<div class="ch"><h2>${T('ev')}</h2></div>`+(list.length?`<div class="tl">${list.map(e=>`<div class="ev"><i class="d ${esc(e.lv)}"></i><span class="m">${esc({nut:'UPS',pve:'PVE',nas:'NAS',dns:'DNS',wan:'WAN',net:'NET'}[e.m]||e.m)}</span><span>${evHtml(e)}</span><span class="t" title="${PCT.ls(new Date(e.t*1000))}">${esc(ago(e.t))}</span></div>`).join('')}</div>`:`<div class="empty">${T('noev')}</div>`);
}

// ───────── Ciclo de actualización / refresh loop ─────────
async function refresh(){
  issues=[];let sevs=[];
  const jobs={};
  if(lvl('nut')){jobs.nut=jget('/nut/api/servers?range=none')}
  // El historial de Proxmox pesa más: se pide una vez por minuto / Proxmox history is heavier: requested once a minute
  const wantPH=Date.now()-pveHTs>60000;
  if(lvl('pve')){jobs.pve=jget('/pve/api/clusters'+(wantPH?'':'?hist=0'))}
  const wantNH=Date.now()-nasHTs>60000;
  if(lvl('nas')){jobs.nas=jget('/nas/api/nas'+(wantNH?'':'?hist=0'))}
  const wantDH=Date.now()-dnsHTs>60000;
  if(lvl('dns')){jobs.dns=jget('/dns/api/dns'+(wantDH?'':'?hist=0'))}
  const wantWH=Date.now()-wanHTs>60000;
  if(lvl('wan')){jobs.wan=jget('/wan/api/wan?hist=0');if(wantWH)jobs.wanh=jget('/wan/api/wan/history?range=1d')}
  if(lvl('net')){jobs.net=jget('/net/api/hosts')}
  jobs.sys=jget('api/system');jobs.ev=jget('api/events?limit=40');
  const keys=Object.keys(jobs),res=await Promise.allSettled(Object.values(jobs));
  const R={};keys.forEach((k,i)=>R[k]=res[i]);
  if(res.some(r=>r.status==='rejected'&&r.reason&&r.reason.code===401)){return showLogin()}
  // Historial de UPS (carga y vatios): cada 60 s basta / UPS history (load and watts): every 60 s is enough
  if(R.nut&&R.nut.status==='fulfilled'&&Date.now()-histTs>60000){
    histTs=Date.now();
    const q=[];for(const sv of (R.nut.value.servers||[])){const sid=sv.id;for(const name of Object.keys((sv.status||{}).ups||{}))q.push(jget(`/nut/api/history?srv=${encodeURIComponent(sid)}&ups=${encodeURIComponent(name)}&range=1d`).then(h=>{hist[sid+'|'+name]=h.history||[]}).catch(()=>{}))}
    await Promise.all(q);
  }
  if(wantPH&&R.pve&&R.pve.status==='fulfilled'){pveHTs=Date.now();pveH={};(R.pve.value.clusters||[]).forEach(c=>{pveH[c.id]=aggHist(c)})}
  if(wantNH&&R.nas&&R.nas.status==='fulfilled'){nasHTs=Date.now();nasH={};(R.nas.value.nas||[]).forEach(n=>{nasH[n.id]=aggNas(n)})}
  if(wantDH&&R.dns&&R.dns.status==='fulfilled'){dnsHTs=Date.now();dnsH={};(R.dns.value.servers||[]).forEach(n=>{dnsH[n.id]=aggDns(n)})}
  if(wantWH&&R.wanh&&R.wanh.status==='fulfilled'){wanHTs=Date.now();wanH=R.wanh.value.history||[]}
  // Historial de temperatura y subtensión de la Pi (solo existe en una Raspberry Pi) / Pi history (Raspberry Pi only)
  if(R.sys.status==='fulfilled'&&Date.now()-piHTs>60000){
    piHTs=Date.now();
    try{const h=await jget('api/pihistory');piH=h&&h.pi?h:null}catch(e){}
  }
  const card=(id,show)=>$(id).classList.toggle('hide',!show);
  card('c-nut',!!R.nut);card('c-pve',!!R.pve);card('c-nas',!!R.nas);card('c-dns',!!R.dns);card('c-wan',!!R.wan);card('c-net',!!R.net);fitGrid();
  const fail=(id,name)=>{$(id).innerHTML=`<div class="ch"><h2>${name}</h2>${pill('crit',T('unreach'))}</div>`;issues.push({lv:'crit',m:name,t:`${name}: ${T('unreach')}`});return 'crit'};
  if(R.nut)sevs.push(R.nut.status==='fulfilled'?renderUPS(R.nut.value):fail('c-nut',T('ups')));
  if(R.pve)sevs.push(R.pve.status==='fulfilled'?renderPVE(R.pve.value):fail('c-pve',T('pve')));
  if(R.nas)sevs.push(R.nas.status==='fulfilled'?renderNAS(R.nas.value):fail('c-nas',T('nas')));
  if(R.dns)sevs.push(R.dns.status==='fulfilled'?renderDNS(R.dns.value):fail('c-dns',T('dns')));
  if(R.wan)sevs.push(R.wan.status==='fulfilled'?renderWAN(R.wan.value):fail('c-wan',T('wan')));
  if(R.net)sevs.push(R.net.status==='fulfilled'?renderNet(R.net.value):fail('c-net',T('net')));
  if(R.sys.status==='fulfilled')sevs.push(renderPi(R.sys.value));
  if(R.ev.status==='fulfilled')renderEvents(R.ev.value.events||[]);
  fitGrid();   // ES: con el contenido ya pintado (el mosaico del kiosko mide las tarjetas) / EN: with the content painted (kiosk masonry measures the cards)
  const g=sevs.reduce((m,x)=>worst(m,x),'ok');
  const gp=$('gpill');gp.className='pill '+g;$('gtxt').textContent=g==='ok'?T('allok'):g==='warn'?T('attn'):T('fail');
  const at=$('attn');at.classList.toggle('show',issues.length>0);at.classList.toggle('c',issues.some(i=>i.lv==='crit'));
  issues.sort((a,b)=>LV[b.lv]-LV[a.lv]);
  $('attnl').innerHTML=issues.map(i=>`<li><b class="${i.lv}" style="background:none">${esc(String(i.m).toUpperCase())}</b>${i.href?`<a href="${esc(i.href)}">${esc(i.t)}</a>`:esc(i.t)}</li>`).join('');
  $('upd').textContent=T('updated')+' '+PCT.time(new Date(),true);
  decorate();
}
// Intervalo de actualización elegible (se guarda en este navegador). Solo cambia cuánto se redibuja ESTA pantalla: los módulos siguen vigilando y anotando eventos en el servidor aunque nadie mire, y los eventos quedan en la línea de tiempo.
// EN: Selectable refresh interval (stored in this browser). It only changes how often THIS screen redraws: the modules keep watching and recording events on the server even when nobody looks, and events stay in the timeline.
const RI=[10,30,60,120,300,0];            // segundos; 0 = manual / seconds; 0 = manual
let riSec=10;try{const v=parseInt(localStorage.getItem('pi-refresh'),10);if(RI.includes(v))riSec=v}catch(e){}
let lastRef=0;
const riLabel=v=>v===0?T('rman'):v<60?v+' s':(v/60)+' min';
function riFill(){const s=$('ri');if(!s)return;s.title=T('rint');s.setAttribute('aria-label',T('rint'));s.innerHTML='';RI.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=riLabel(v);if(v===riSec)o.selected=true;s.appendChild(o)});const b=$('rr');if(b){b.title=T('rnow');b.setAttribute('aria-label',T('rnow'))}}
function riNext(){clearTimeout(timer);timer=null;if(riSec>0)timer=setTimeout(loop,Math.max(0,lastRef+riSec*1000-Date.now()))}
// Con la pestaña oculta no se consulta nada (ahorra CPU de la Pi); al volver se actualiza si ya tocaba.
// EN: With the tab hidden nothing is queried (saves the Pi's CPU); on return it refreshes if it was due.
function loop(){clearTimeout(timer);timer=null;
  if(document.hidden){if(riSec>0)timer=setTimeout(loop,Math.max(riSec,10)*1000);return}
  refresh().catch(()=>{}).finally(()=>{lastRef=Date.now();riNext()})}
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&me&&me.username&&(riSec===0?false:Date.now()-lastRef>riSec*1000))loop()});

// ───────── Sesión / session ─────────
function showLogin(){clearTimeout(timer);$('app').classList.add('hide');$('loginbox').classList.remove('hide');$('lu').focus()}
async function start(){
  try{me=await jget('api/me')}catch(e){me={}}
  if(!me.username)return showLogin();
  $('loginbox').classList.add('hide');$('app').classList.remove('hide');loop();
}
async function doLogin(){
  $('lerr').textContent='';
  const r=await fetch('api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:$('lu').value,password:$('lp').value,remember:remValue()})});
  const d=await r.json().catch(()=>({}));
  if(!r.ok||!d.ok){$('lerr').textContent=d.error||T('invalid');return}
  if(d.must_change_password){location.href='/admin/change-password?next='+encodeURIComponent('/overview/');return}
  $('lp').value='';start();
}
$('lgo').onclick=doLogin;$('lp').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin()});
$('bo').onclick=async()=>{await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});me={};showLogin()};

// ───────── Idioma / language ─────────
function applyLang(){
  document.documentElement.lang=lang;document.title='LabTower — '+T('title');
  document.querySelectorAll('[data-i]').forEach(e=>e.textContent=T(e.dataset.i));
  $('bl').textContent=lang==='es'?'EN':'ES';riFill();
  paintSort();
  $('lu').placeholder=lang==='es'?'Usuario':'User';$('lp').placeholder=lang==='es'?'Contraseña':'Password';
}
$('ri').onchange=e=>{riSec=parseInt(e.target.value,10);try{localStorage.setItem('pi-refresh',String(riSec))}catch(x){}if(me&&me.username){riNext();if(riSec>0&&Date.now()-lastRef>riSec*1000)loop()}};
$('rr').onclick=()=>{if(me&&me.username)loop()};
$('bl').onclick=()=>{lang=lang==='es'?'en':'es';try{localStorage.setItem('pi-lang',lang)}catch(e){}applyLang();document.dispatchEvent(new Event('pi-lang'));if(me&&me.username){histTs=0;refresh()}};

// ES: Reparto equilibrado de las tarjetas: si no caben todas en una fila, se reparten en filas parejas (4 tarjetas con sitio para 3 → 2×2) en vez de dejar una sola tarjeta huérfana con un hueco a su derecha.
// EN: Balanced card layout: if they do not all fit in one row they are spread over even rows (4 cards with room for 3 → 2×2) instead of leaving one orphan card with a gap to its right.
function fitGrid(){
  const g=$('grid');if(!g)return;
  g.style.gridTemplateColumns='';
  if(document.body.classList.contains('kiosk')){masonry(g);return}
  [...g.children].forEach(c=>{c.style.gridRowEnd=''});
  const n=[...g.children].filter(c=>!c.classList.contains('hide')).length;
  const t=getComputedStyle(g).gridTemplateColumns.split(' ').length;
  if(n>t&&t>0){const rows=Math.ceil(n/t);g.style.gridTemplateColumns='repeat('+Math.ceil(n/rows)+',minmax(0,1fr))'}
}
window.addEventListener('resize',fitGrid);
// ES: Modo kiosko: las tarjetas se apilan por columnas (tipo mosaico) en vez de en filas de igual altura, así una tarjeta corta no deja un hueco bajo ella. Cada tarjeta ocupa tantas filas de 4 px como mide; el orden elegido se respeta (la siguiente va a la columna más baja). Funciona con CSS grid (iOS 10.3+), sin ResizeObserver.
// EN: Kiosk mode: cards stack by column (masonry) instead of equal-height rows, so a short card leaves no gap under it. Each card spans as many 4 px rows as it is tall; the chosen order is kept (the next one goes to the shortest column). Uses CSS grid (iOS 10.3+), no ResizeObserver needed.
function masonry(g){
  const cs=getComputedStyle(g),gap=parseFloat(cs.columnGap||cs.gridColumnGap)||0,cards=[...g.children].filter(c=>!c.classList.contains('hide'));
  cards.forEach(c=>{c.style.gridRowEnd=''});
  const hs=cards.map(c=>c.getBoundingClientRect().height);
  cards.forEach((c,i)=>{c.style.gridRowEnd='span '+Math.max(1,Math.ceil((hs[i]+gap)/4))});
}
// ES: Los datos cambian de tamaño al refrescar (gráficos, listas); se recalcula cada 2 s solo en kiosko.
// EN: Content changes size on refresh (charts, lists); recomputed every 2 s in kiosk only.
setInterval(()=>{if(document.body.classList.contains('kiosk'))fitGrid()},2000);


// ───────── Orden de las tarjetas / card order ─────────
// ES: Las tarjetas se pueden reordenar con el botón «Ordenar» (flechas o arrastrando). El orden se guarda en este navegador (clave pi-card-order); por defecto es el de siempre: UPS, Proxmox, Red, Pi. La línea de tiempo siempre va debajo.
// EN: Cards can be reordered with the "Reorder" button (arrows or drag). The order is stored in this browser (key pi-card-order); the default is the usual one: UPS, Proxmox, Network, Pi. The timeline always stays below.
const CARDS=['c-nut','c-pve','c-nas','c-dns','c-wan','c-net','c-pi'];
let ord=CARDS.slice(),sortMode=false,dragId=null;
try{const v=JSON.parse(localStorage.getItem('pi-card-order')||'[]');if(Array.isArray(v)){const k=v.filter((x,i)=>CARDS.includes(x)&&v.indexOf(x)===i);ord=k.concat(CARDS.filter(x=>!k.includes(x)))}}catch(e){}
function saveOrd(){try{if(ord.join()===CARDS.join())localStorage.removeItem('pi-card-order');else localStorage.setItem('pi-card-order',JSON.stringify(ord))}catch(e){}}
function applyOrder(){ord.forEach((id,i)=>{const c=$(id);if(c)c.style.order=i})}
const visCards=()=>ord.filter(id=>$(id)&&!$(id).classList.contains('hide'));
function moveCard(id,dir){const v=visCards(),j=v.indexOf(id)+dir;if(j<0||j>=v.length)return;const a=ord.indexOf(id),b=ord.indexOf(v[j]);[ord[a],ord[b]]=[ord[b],ord[a]];saveOrd();applyOrder();decorate()}
function dropCard(src,dst){if(!src||src===dst)return;ord.splice(ord.indexOf(src),1);ord.splice(ord.indexOf(dst),0,src);saveOrd();applyOrder();decorate()}
function mkBtn(txt,title,fn,off){const b=document.createElement('button');b.type='button';b.className='otool';b.textContent=txt;b.title=title;b.setAttribute('aria-label',title);b.disabled=!!off;b.addEventListener('click',fn);return b}
// Las tarjetas se reescriben en cada actualización, así que las herramientas se vuelven a poner al final de cada una.
// EN: The cards are rewritten on every refresh, so the tools are put back at the end of each one.
function decorate(){
  const g=$('grid');if(!g)return;
  g.querySelectorAll('.otools').forEach(e=>e.remove());
  CARDS.forEach(id=>{const c=$(id);if(c){c.classList.toggle('sorting',sortMode);c.draggable=false}});
  if(!sortMode)return;
  const v=visCards();
  v.forEach((id,i)=>{
    const c=$(id),t=document.createElement('div');t.className='otools';
    const grab=document.createElement('span');grab.className='otool grab';grab.textContent='⠿';grab.title=T('mvDrag');
    grab.addEventListener('mousedown',()=>{c.draggable=true});grab.addEventListener('mouseup',()=>{c.draggable=false});
    t.appendChild(mkBtn('‹',T('mvEarlier'),()=>moveCard(id,-1),i===0));t.appendChild(grab);t.appendChild(mkBtn('›',T('mvLater'),()=>moveCard(id,1),i===v.length-1));
    c.appendChild(t);
  });
}
CARDS.forEach(id=>{const c=$(id);if(!c)return;
  c.addEventListener('dragstart',e=>{if(!sortMode||!c.draggable){e.preventDefault();return}dragId=id;e.dataTransfer.effectAllowed='move';try{e.dataTransfer.setData('text/plain',id)}catch(x){}c.classList.add('dragging')});
  c.addEventListener('dragend',()=>{c.draggable=false;c.classList.remove('dragging');CARDS.forEach(k=>$(k)&&$(k).classList.remove('dragover'));dragId=null});
  c.addEventListener('dragover',e=>{if(!sortMode||!dragId)return;e.preventDefault();e.dataTransfer.dropEffect='move';c.classList.add('dragover')});
  c.addEventListener('dragleave',()=>c.classList.remove('dragover'));
  c.addEventListener('drop',e=>{if(!sortMode||!dragId)return;e.preventDefault();c.classList.remove('dragover');dropCard(dragId,id)});
});
function paintSort(){const b=$('bs'),r=$('bs0');if(!b)return;b.textContent=sortMode?T('sortDone'):T('sortBtn');b.classList.toggle('on',sortMode);r.textContent=T('sortReset');r.classList.toggle('hide',!sortMode)}
$('bs').onclick=()=>{sortMode=!sortMode;paintSort();decorate()};
$('bs0').onclick=()=>{ord=CARDS.slice();saveOrd();applyOrder();decorate()};
applyOrder();

// ───────── Modo kiosko / kiosk mode ─────────
let wl=null;
// Como app web (iPad: «Añadir a pantalla de inicio») la página ya ocupa toda la pantalla; pedir pantalla completa además hace que iPadOS dibuje un botón X para salir.
// EN: As a web app (iPad "Add to Home Screen") the page already fills the screen; also asking for fullscreen makes iPadOS draw an exit X button.
const isStandalone=()=>navigator.standalone===true||(window.matchMedia&&matchMedia('(display-mode: standalone)').matches);
async function setKiosk(on){
  document.body.classList.toggle('kiosk',on);document.documentElement.classList.toggle('kiosk',on);fitGrid();if(on&&typeof asOn!=='undefined'){asOn=false;asPaint()}
  try{const u=new URL(location.href);on?u.searchParams.set('kiosk','1'):u.searchParams.delete('kiosk');history.replaceState(null,'',u)}catch(e){}
  try{
    if(on){if(!isStandalone()&&document.documentElement.requestFullscreen&&!document.fullscreenElement)await document.documentElement.requestFullscreen();if(navigator.wakeLock)wl=await navigator.wakeLock.request('screen')}
    else{if(document.fullscreenElement)await document.exitFullscreen();if(wl){wl.release();wl=null}}
  }catch(e){}
}
$('bk').onclick=()=>setKiosk(true);$('kx').onclick=()=>{if(kbarReady())setKiosk(false)};
document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement&&document.body.classList.contains('kiosk')){document.body.classList.remove('kiosk');document.documentElement.classList.remove('kiosk')}});
// La barra de botones del kiosko aparece al mover el mouse o tocar la pantalla; el primer toque solo la muestra (no pulsa un botón aún invisible).
// EN: The kiosk button bar shows up on mouse move or touch; the first touch only reveals it (it doesn't press a still-invisible button).
let mv=null,kShown=0;
const kbarReady=()=>Date.now()-kShown>350;
const showKx=()=>{
  if(!document.body.classList.contains('moved'))kShown=Date.now();
  const el=document.scrollingElement||document.documentElement;$('ka').classList.toggle('hide',el.scrollHeight-el.clientHeight<=8);
  document.body.classList.add('moved');clearTimeout(mv);mv=setTimeout(()=>document.body.classList.remove('moved'),4000)};
document.addEventListener('mousemove',showKx);document.addEventListener('touchstart',showKx,{passive:true});
document.addEventListener('visibilitychange',async()=>{if(document.visibilityState==='visible'&&document.body.classList.contains('kiosk')&&navigator.wakeLock){try{wl=await navigator.wakeLock.request('screen')}catch(e){}}});

// Desplazamiento automático en modo kiosko, para cuando el contenido no cabe en la pantalla (tablets chicas).
// Viene APAGADO: se activa con el botón «Auto-desplazar» que aparece al tocar la pantalla (o abriendo con ?autoscroll=1).
// Sube y baja despacio, hace pausa arriba y abajo, y se detiene 30 s si se toca la pantalla.
// EN: Automatic scrolling in kiosk mode, for when the content doesn't fit the screen (small tablets).
// It starts OFF: turn it on with the "Auto-scroll" button that shows up when the screen is touched (or open with ?autoscroll=1).
// It moves slowly up and down, pauses at the top and bottom, and stops for 30 s on touch.
let asDir=1,asHold=Date.now()+8000;
let asOn=new URLSearchParams(location.search).get('autoscroll')==='1';
const asPaint=()=>{$('ka').classList.toggle('on',asOn);$('ka').setAttribute('aria-pressed',asOn?'true':'false')};
$('ka').onclick=()=>{if(!kbarReady())return;asOn=!asOn;asDir=1;asHold=Date.now()+1500;asPaint()};
asPaint();
const asTouch=()=>{asHold=Date.now()+30000};
['touchstart','wheel','keydown'].forEach(ev=>document.addEventListener(ev,asTouch,{passive:true}));
setInterval(()=>{
  if(!asOn||!document.body.classList.contains('kiosk')||Date.now()<asHold)return;
  const el=document.scrollingElement||document.documentElement,max=el.scrollHeight-el.clientHeight;
  if(max<=8)return;
  const y=el.scrollTop;
  if(asDir>0&&y>=max-1){asDir=-1;asHold=Date.now()+8000;return}
  if(asDir<0&&y<=0){asDir=1;asHold=Date.now()+8000;return}
  window.scrollBy(0,asDir);
},50);

applyLang();
try{const z=parseFloat(new URLSearchParams(location.search).get('zoom'));if(z>=0.5&&z<=2)document.documentElement.style.setProperty('--kz',z)}catch(e){}
if(new URLSearchParams(location.search).get('kiosk')==='1'){document.body.classList.add('kiosk');document.documentElement.classList.add('kiosk')}
start();

// ───────── Recordarme / Remember me ─────────
// Devuelve la duración elegida ("day","week","month","forever") o "" si no se marcó. Recuerda la última elección en este navegador.
// EN: Returns the chosen duration ("day","week","month","forever") or "" if unchecked. Remembers the last choice in this browser.
function remValue(){const c=document.getElementById('l-rem'),s=document.getElementById('l-remsel');const v=c&&c.checked&&s?s.value:'';try{localStorage.setItem('pi-remember',v)}catch(e){}return v}
(function remInit(){try{const v=localStorage.getItem('pi-remember')||'';const c=document.getElementById('l-rem'),s=document.getElementById('l-remsel');if(c&&s&&['day','week','month','forever'].includes(v)){c.checked=true;s.disabled=false;s.value=v}}catch(e){}})();
{const c=$('l-rem'),sl=$('l-remsel');if(c&&sl)c.onchange=()=>{sl.disabled=!c.checked}}
