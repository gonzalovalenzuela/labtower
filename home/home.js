// Consulta una URL con 3 s de espera: si responde bien, el punto se pone verde y el texto dice «activo»; si no, «sin respuesta».
// EN: Query a URL with a 3 s timeout: if it answers fine, the dot turns green and the text says "active"; otherwise "no response".
async function checkService(url,dotId,lblId,name){
  try{
    const r=await fetch(url,{signal:AbortSignal.timeout(3000)});
    if(r.ok){
      document.getElementById(dotId).className='dot green';
      document.getElementById(lblId).textContent=name+' activo';
    }else throw new Error();
  }catch{
    document.getElementById(dotId).className='dot';
    document.getElementById(lblId).textContent=name+' sin respuesta';
  }
}
checkService('/wol/api/devices','dot-wol','lbl-wol','WOL');
checkService('/nut/api/config', 'dot-nut','lbl-nut','NUT');
