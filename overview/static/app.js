// ───────── Textos / texts ─────────
const TXT={
 en:{title:'Overview',home:'Home',kiosk:'Kiosk',logout:'Sign out',login:'Sign in',exitk:'Exit kiosk',ascroll:'Auto-scroll',updated:'Updated',allok:'All good',attn:'Attention',fail:'Failure',
  ups:'UPS Monitor',pve:'Proxmox',net:'Net Monitor',pi:'Raspberry Pi',ev:'Timeline',open:'Open →',noups:'No UPS servers configured',nopve:'No clusters configured',nonet:'No scan yet',noev:'No events yet',
  mains:'On mains',batt:'On battery',lowb:'Low battery',unreach:'Unreachable',battery:'Battery',load:'Load',runtime:'Runtime',power:'Power',nodes:'Nodes',vms:'VMs',cts:'CTs',cpu:'CPU',mem:'Memory',disk:'Disk',temp:'Temp',uptime:'Uptime',
  online:'Online',known:'Known',offline:'Offline',newdev:'New devices',lastscan:'Last scan',scanning:'Scanning…',ceph:'Ceph',types:'By device type',nonew:'No new devices',
  ago:'ago',now:'now',min:'min',h:'h',d:'d',s:'s',power_uv:'Under-voltage',power_th:'Throttled',power_ok:'Power supply OK',invalid:'Invalid credentials',
  issue_batt:'is running on battery',issue_lowb:'has low battery',issue_srv:'unreachable',issue_node:'node offline',issue_cl:'cluster unreachable',issue_cpu:'high CPU',issue_ram:'high memory',issue_ceph:'Ceph',
  issue_temp:'Pi temperature high',issue_disk:'Pi disk almost full',issue_mem:'Pi memory high',issue_pwr:'Pi power supply problem',issue_scan:'scan error',h_temp:'Temp',h_min:'min',h_max:'max',h_uv:'Under-voltage',h_nouv:'no under-voltage',h_utemp:'UPS temperature 24 h'},
 es:{title:'Resumen',home:'Inicio',kiosk:'Kiosko',logout:'Cerrar sesión',login:'Entrar',exitk:'Salir de kiosko',ascroll:'Auto-desplazar',updated:'Actualizado',allok:'Todo en orden',attn:'Atención',fail:'Falla',
  ups:'UPS Monitor',pve:'Proxmox',net:'Net Monitor',pi:'Raspberry Pi',ev:'Línea de tiempo',open:'Abrir →',noups:'Sin servidores UPS configurados',nopve:'Sin clusters configurados',nonet:'Aún sin escaneo',noev:'Sin eventos todavía',
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
  return Object.keys(b).map(Number).sort((x,y)=>x-y).map(k=>({cpu:b[k].c/b[k].n,mem:b[k].m/b[k].n}));
}
function donut(parts){ // parts: [{label,n,color}]
  const tot=parts.reduce((a,p)=>a+p.n,0);if(!tot)return '';
  const R=15.9155;let off=25,segs='';
  parts.forEach(p=>{const l=p.n/tot*100;segs+=`<circle cx="21" cy="21" r="${R}" fill="none" stroke="${p.color}" stroke-width="6" stroke-dasharray="${l} ${100-l}" stroke-dashoffset="${off}"/>`;off-=l});
  return `<svg width="84" height="84" viewBox="0 0 42 42"><circle cx="21" cy="21" r="${R}" fill="none" stroke="var(--track)" stroke-width="6"/>${segs}<text x="21" y="23.5" text-anchor="middle" font-size="9" font-weight="700" fill="var(--text)">${tot}</text></svg>`;
}
const PAL=['#4361ee','#16a34a','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899','#84cc16','#0ea5e9','#d946ef','#14b8a6','#94a3b8'];

// ───────── Estado / state ─────────
let me=null,issues=[],hist={},histTs=0,timer=null,piH=null,piHTs=0,pveH={},pveHTs=0;
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
      body+=`<div class="unit"><div class="uh">${esc(v['_desc']||name)} <span class="sub">${esc(name)}</span>${pill(m[0],m[1])}</div>
       <div class="row"><span class="l">${T('battery')}</span><div class="bar ${charge<=20?'c':charge<=50?'w':'g'}"><div style="width:${Math.max(0,Math.min(100,charge))}%"></div></div><span class="v">${charge.toFixed(0)}%</span></div>
       <div class="row"><span class="l">${T('load')}</span>${bar(load,70,90)}<span class="v">${load.toFixed(0)}%</span></div>
       <div class="kpis"><div class="kpi"><b>${run?dur(run):'—'}</b><span>${T('runtime')}</span></div><div class="kpi"><b>${last&&last.watts?Math.round(last.watts)+' W':'—'}</b><span>${T('power')}</span></div></div>${spark(h.map(r=>r.load))}${upsTemp(h)}</div>`;
    }
  }
  el.innerHTML=`<div class="ch"><h2>${T('ups')}</h2>${n?pill(sev,sev==='ok'?'OK':sev==='warn'?T('attn'):T('fail')):''}<a class="go" href="/nut/">${T('open')}</a></div>`+(n?body:`<div class="empty">${T('noups')}</div>`);
  return sev;
}
// ───────── Proxmox ─────────
function pveChart(id){
  const a=pveH[id]||[];if(a.length<3)return '';
  return '<div class="kp">'+lchart([{vals:a.map(p=>p.cpu),color:'var(--blue)'},{vals:a.map(p=>p.mem),color:'#8b5cf6'}])+
    `<div class="hc"><i style="background:var(--blue)"></i>${T('cpu')}<i style="background:#8b5cf6"></i>${T('mem')} · ${dur(a.length*300)}</div></div>`;
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
   <div><div class="sub" style="margin-bottom:5px;font-weight:600">${T('newdev')} (48 ${T('h')})</div>${fresh.length?`<div class="list">${fresh.slice(0,5).map(h=>`<div>${pill('warn','NEW')}<code>${esc(h.ip)}</code><span>${esc(h.alias||h.hostname||h.vendor||'')}</span></div>`).join('')}</div>`:`<div class="empty">${T('nonew')}</div>`}</div>`:`<div class="empty">${T('nonet')}</div>`);
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
  el.innerHTML=`<div class="ch"><h2>${T('pi')}</h2>${pill(sev,sev==='ok'?'OK':sev==='warn'?T('attn'):T('fail'))}</div>
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
  net_first:'First scan: {n} hosts found',net_new:'New device: {ip} {n} {v}',net_up:'Back online: {ip} {n}',net_down:'Went offline: {ip} {n}',net_new_n:'{n} new devices',net_up_n:'{n} hosts back online',net_down_n:'{n} hosts went offline'},
 es:{ups_lowb:'{n}: batería baja ({pct})',ups_batt:'{n}: funcionando con batería ({pct})',ups_mains:'{n}: volvió la red eléctrica ({pct})',ups_other:'{n}: estado {st}',ups_srv_down:'Servidor UPS {n} sin conexión: {e}',ups_srv_up:'Servidor UPS {n} otra vez disponible',
  pve_cl_down:'{c}: cluster sin conexión',pve_cl_up:'{c}: cluster otra vez disponible',pve_node_on:'{c}/{n}: nodo en línea',pve_node_off:'{c}/{n}: nodo {st}',pve_ceph:'{c}: Ceph {a} → {b}',
  net_first:'Primer escaneo: {n} equipos encontrados',net_new:'Equipo nuevo: {ip} {n} {v}',net_up:'Volvió a estar en línea: {ip} {n}',net_down:'Dejó de responder: {ip} {n}',net_new_n:'{n} equipos nuevos',net_up_n:'{n} equipos volvieron a estar en línea',net_down_n:'{n} equipos dejaron de responder'}
};
// Texto de un evento en el idioma actual; si la clave no se conoce, el texto en inglés guardado / Event text in the current language; unknown key → stored English text
function evText(e){const t=e.k&&EVT[lang][e.k];return t?t.replace(/\{(\w+)\}/g,(_,k)=>(e.p&&e.p[k]!=null?e.p[k]:'')).replace(/\s+/g,' ').trim():e.tx}
function renderEvents(list){
  $('c-ev').innerHTML=`<div class="ch"><h2>${T('ev')}</h2></div>`+(list.length?`<div class="tl">${list.map(e=>`<div class="ev"><i class="d ${esc(e.lv)}"></i><span class="m">${esc({nut:'UPS',pve:'PVE',net:'NET'}[e.m]||e.m)}</span><span>${esc(evText(e))}</span><span class="t" title="${new Date(e.t*1000).toLocaleString()}">${esc(ago(e.t))}</span></div>`).join('')}</div>`:`<div class="empty">${T('noev')}</div>`);
}

// ───────── Ciclo de actualización / refresh loop ─────────
async function refresh(){
  issues=[];let sevs=[];
  const jobs={};
  if(lvl('nut')){jobs.nut=jget('/nut/api/servers?range=none')}
  // El historial de Proxmox pesa más: se pide una vez por minuto / Proxmox history is heavier: requested once a minute
  const wantPH=Date.now()-pveHTs>60000;
  if(lvl('pve')){jobs.pve=jget('/pve/api/clusters'+(wantPH?'':'?hist=0'))}
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
  // Historial de temperatura y subtensión de la Pi (solo existe en una Raspberry Pi) / Pi history (Raspberry Pi only)
  if(R.sys.status==='fulfilled'&&Date.now()-piHTs>60000){
    piHTs=Date.now();
    try{const h=await jget('api/pihistory');piH=h&&h.pi?h:null}catch(e){}
  }
  const card=(id,show)=>$(id).classList.toggle('hide',!show);
  card('c-nut',!!R.nut);card('c-pve',!!R.pve);card('c-net',!!R.net);fitGrid();
  const fail=(id,name)=>{$(id).innerHTML=`<div class="ch"><h2>${name}</h2>${pill('crit',T('unreach'))}</div>`;issues.push({lv:'crit',m:name,t:`${name}: ${T('unreach')}`});return 'crit'};
  if(R.nut)sevs.push(R.nut.status==='fulfilled'?renderUPS(R.nut.value):fail('c-nut',T('ups')));
  if(R.pve)sevs.push(R.pve.status==='fulfilled'?renderPVE(R.pve.value):fail('c-pve',T('pve')));
  if(R.net)sevs.push(R.net.status==='fulfilled'?renderNet(R.net.value):fail('c-net',T('net')));
  if(R.sys.status==='fulfilled')sevs.push(renderPi(R.sys.value));
  if(R.ev.status==='fulfilled')renderEvents(R.ev.value.events||[]);
  const g=sevs.reduce((m,x)=>worst(m,x),'ok');
  const gp=$('gpill');gp.className='pill '+g;$('gtxt').textContent=g==='ok'?T('allok'):g==='warn'?T('attn'):T('fail');
  const at=$('attn');at.classList.toggle('show',issues.length>0);at.classList.toggle('c',issues.some(i=>i.lv==='crit'));
  issues.sort((a,b)=>LV[b.lv]-LV[a.lv]);
  $('attnl').innerHTML=issues.map(i=>`<li><b class="${i.lv}" style="background:none">${esc(String(i.m).toUpperCase())}</b>${i.href?`<a href="${esc(i.href)}">${esc(i.t)}</a>`:esc(i.t)}</li>`).join('');
  $('upd').textContent=T('updated')+' '+new Date().toLocaleTimeString();
}
function loop(){clearTimeout(timer);refresh().catch(()=>{}).finally(()=>{timer=setTimeout(loop,10000)})}

// ───────── Sesión / session ─────────
function showLogin(){clearTimeout(timer);$('app').classList.add('hide');$('loginbox').classList.remove('hide');$('lu').focus()}
async function start(){
  try{me=await jget('api/me')}catch(e){me={}}
  if(!me.username)return showLogin();
  $('loginbox').classList.add('hide');$('app').classList.remove('hide');loop();
}
async function doLogin(){
  $('lerr').textContent='';
  const r=await fetch('api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:$('lu').value,password:$('lp').value})});
  const d=await r.json().catch(()=>({}));
  if(!r.ok||!d.ok){$('lerr').textContent=d.error||T('invalid');return}
  if(d.must_change_password){location.href='/admin/change-password?next='+encodeURIComponent('/overview/');return}
  $('lp').value='';start();
}
$('lgo').onclick=doLogin;$('lp').addEventListener('keydown',e=>{if(e.key==='Enter')doLogin()});
$('bo').onclick=async()=>{await fetch('api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});me={};showLogin()};

// ───────── Idioma / language ─────────
function applyLang(){
  document.documentElement.lang=lang;document.title='Pi Console — '+T('title');
  document.querySelectorAll('[data-i]').forEach(e=>e.textContent=T(e.dataset.i));
  $('bl').textContent=lang==='es'?'EN':'ES';
  $('lu').placeholder=lang==='es'?'Usuario':'User';$('lp').placeholder=lang==='es'?'Contraseña':'Password';
}
$('bl').onclick=()=>{lang=lang==='es'?'en':'es';try{localStorage.setItem('pi-lang',lang)}catch(e){}applyLang();if(me&&me.username){histTs=0;refresh()}};

// ES: Reparto equilibrado de las tarjetas: si no caben todas en una fila, se reparten en filas parejas (4 tarjetas con sitio para 3 → 2×2) en vez de dejar una sola tarjeta huérfana con un hueco a su derecha.
// EN: Balanced card layout: if they do not all fit in one row they are spread over even rows (4 cards with room for 3 → 2×2) instead of leaving one orphan card with a gap to its right.
function fitGrid(){
  const g=$('grid');if(!g)return;
  g.style.gridTemplateColumns='';
  const n=[...g.children].filter(c=>!c.classList.contains('hide')).length;
  const t=getComputedStyle(g).gridTemplateColumns.split(' ').length;
  if(n>t&&t>0){const rows=Math.ceil(n/t);g.style.gridTemplateColumns='repeat('+Math.ceil(n/rows)+',minmax(0,1fr))'}
}
window.addEventListener('resize',fitGrid);

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
