// Formato de hora 24 h / 12 h. Se guarda en este navegador (clave pi-clock) y vale para todos los módulos. Por defecto, 24 h.
// EN: 24 h / 12 h time format. Stored in this browser (key pi-clock) and shared by all modules. Default: 24 h.
// Se repite igual en cada módulo. / Same file in every module.
(function(){
  function is12(){ try{ return localStorage.getItem('pi-clock')==='12'; }catch(e){ return false; } }
  function p2(n){ return (n<10?'0':'')+n; }
  // Hora de un Date: 24 h «HH:MM[:SS]» o 12 h «h:MM[:SS] AM/PM».
  function time(d, secs){
    var h=d.getHours(), m=p2(d.getMinutes()), s=secs?':'+p2(d.getSeconds()):'';
    if(!is12()) return p2(h)+':'+m+s;
    return ((h%12)||12)+':'+m+s+' '+(h<12?'AM':'PM');
  }
  // toLocaleString con el ciclo de horas elegido (las opciones sin hora no cambian).
  function ls(d, locale, opts){
    var o={}; for(var k in (opts||{})) o[k]=opts[k];
    if(is12()) o.hour12=true; else o.hourCycle='h23';
    return d.toLocaleString(locale, o);
  }
  window.PCT={is12:is12, time:time, ls:ls};

  // Botón «24H/12H»: junto a los botones de idioma (o antes del botón de idioma del Resumen). Al cambiar se recarga la página.
  function mount(){
    var b=document.createElement('button');
    b.type='button'; b.id='clk-btn';
    b.textContent=is12()?'12H':'24H';
    var es=((document.documentElement.lang||'en')==='es');
    b.title=es?'Formato de hora (24 h / 12 h)':'Time format (24 h / 12 h)';
    b.addEventListener('click',function(){
      try{ localStorage.setItem('pi-clock', is12()?'24':'12'); }catch(e){}
      location.reload();
    });
    var box=document.querySelector('.lang-btns'), bl=document.getElementById('bl');
    if(box){ b.className='lang-btn'; box.appendChild(b); }
    else if(bl && bl.parentNode){ b.className='btn nokiosk'; bl.parentNode.insertBefore(b, bl); }
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
