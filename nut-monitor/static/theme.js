// ES: Tema común de LabTower (oscuro tipo NOC por defecto; claro y «sistema» siguen disponibles). Va en <head> para que no parpadee. La clave pi-theme ya la usaban los módulos.
// EN: Shared LabTower theme (dark NOC look by default; light and "system" remain available). Loaded in <head> so it does not flash. The pi-theme key was already used by the modules.
(function(){
  var d=document.documentElement,ORDER=['dark','light','system'],NAME={dark:'Oscuro / Dark',light:'Claro / Light',system:'Auto'};
  function mode(){var t='dark';try{t=localStorage.getItem('pi-theme')||'dark'}catch(e){}return ORDER.indexOf(t)<0?'dark':t}
  function pick(){var t=mode();
    if(t==='system')t=(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';
    return t==='light'?'light':'dark'}
  function mark(){var m=mode();document.querySelectorAll('[data-theme-toggle]').forEach(function(b){b.setAttribute('data-mode',m);b.title='Tema / Theme: '+NAME[m];b.setAttribute('aria-label','Theme: '+NAME[m])})}
  d.setAttribute('data-theme',pick());
  document.addEventListener('DOMContentLoaded',mark);
  if(window.matchMedia)try{matchMedia('(prefers-color-scheme: dark)').addEventListener('change',function(){if(mode()==='system'){d.setAttribute('data-theme',pick());document.dispatchEvent(new Event('pi-theme'))}})}catch(e){}
  document.addEventListener('click',function(e){
    var b=e.target&&e.target.closest?e.target.closest('[data-theme-toggle]'):null;if(!b)return;
    var n=ORDER[(ORDER.indexOf(mode())+1)%ORDER.length];
    try{localStorage.setItem('pi-theme',n)}catch(x){}
    d.setAttribute('data-theme',pick());mark();document.dispatchEvent(new Event('pi-theme'));
  });
})();
