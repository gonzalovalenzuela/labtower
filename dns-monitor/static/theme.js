// ES: Tema común de LabTower (oscuro tipo NOC por defecto; claro y «sistema» siguen disponibles). Va en <head> para que no parpadee. La clave pi-theme ya la usaban los módulos.
// EN: Shared LabTower theme (dark NOC look by default; light and "system" remain available). Loaded in <head> so it does not flash. The pi-theme key was already used by the modules.
(function(){
  var d=document.documentElement;
  function pick(){var t='dark';try{t=localStorage.getItem('pi-theme')||'dark'}catch(e){}
    if(t==='system')t=(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';
    return t==='light'?'light':'dark'}
  d.setAttribute('data-theme',pick());
  document.addEventListener('click',function(e){
    var b=e.target&&e.target.closest?e.target.closest('[data-theme-toggle]'):null;if(!b)return;
    var n=d.getAttribute('data-theme')==='dark'?'light':'dark';
    try{localStorage.setItem('pi-theme',n)}catch(x){}
    d.setAttribute('data-theme',n);document.dispatchEvent(new Event('pi-theme'));
  });
})();
