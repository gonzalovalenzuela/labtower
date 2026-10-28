// ES: Tema común de LabTower (oscuro tipo NOC por defecto; claro y «sistema» siguen disponibles). Va en <head> para que no parpadee. La clave pi-theme ya la usaban los módulos.
// EN: Shared LabTower theme (dark NOC look by default; light and "system" remain available). Loaded in <head> so it does not flash. The pi-theme key was already used by the modules.
(function(){
  var d=document.documentElement,ORDER=['dark','light','system'],NAME={dark:'Oscuro / Dark',light:'Claro / Light',system:'Auto'};
  function mode(){var t='dark';try{t=localStorage.getItem('pi-theme')||'dark'}catch(e){}return ORDER.indexOf(t)<0?'dark':t}
  function pick(){var t=mode();
    if(t==='system')t=(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';
    return t==='light'?'light':'dark'}
  var LBL={es:{dark:'OSCURO',light:'CLARO',system:'AUTO'},en:{dark:'DARK',light:'LIGHT',system:'AUTO'}};
  function mark(){var m=mode(),l=LBL[(d.lang||'en').slice(0,2)==='es'?'es':'en'];
    Array.prototype.slice.call(document.querySelectorAll('[data-theme-toggle]')).forEach(function(b){
      if(!b.classList.contains('theme-lbl')){
        // ES: Junto al icono se agrega un botón con el modo elegido (como «24H» o «ES»). EN: next to the icon, a button showing the selected mode (like "24H" or "ES").
        var n=b.nextElementSibling;
        if(!n||!n.classList.contains('theme-lbl')){n=document.createElement('button');n.type='button';n.className='theme-lbl'+(b.classList.contains('nokiosk')?' nokiosk':'');n.setAttribute('data-theme-toggle','');b.parentNode.insertBefore(n,b.nextSibling)}
      }
    });
    document.querySelectorAll('[data-theme-toggle]').forEach(function(b){
      b.setAttribute('data-mode',m);b.title='Tema / Theme: '+NAME[m];b.setAttribute('aria-label','Theme: '+NAME[m]);
      if(b.classList.contains('theme-lbl'))b.textContent=l[m]})}
  d.setAttribute('data-theme',pick());
  document.addEventListener('DOMContentLoaded',function(){mark();try{new MutationObserver(mark).observe(d,{attributes:true,attributeFilter:['lang']})}catch(e){}});
  if(window.matchMedia)try{matchMedia('(prefers-color-scheme: dark)').addEventListener('change',function(){if(mode()==='system'){d.setAttribute('data-theme',pick());document.dispatchEvent(new Event('pi-theme'))}})}catch(e){}
  document.addEventListener('click',function(e){
    var b=e.target&&e.target.closest?e.target.closest('[data-theme-toggle]'):null;if(!b)return;
    var n=ORDER[(ORDER.indexOf(mode())+1)%ORDER.length];
    try{localStorage.setItem('pi-theme',n)}catch(x){}
    d.setAttribute('data-theme',pick());mark();document.dispatchEvent(new Event('pi-theme'));
  });
})();
