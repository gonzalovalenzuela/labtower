// Pie con la versión instalada, leída de /api/version. Se repite igual en todas las páginas.
// EN: Footer with the installed version, read from /api/version. Repeated identically on every page.
/* Version footer (same snippet in every page): shows the installed Pi Console version */
(function(){
  // Estilos del pie: en app.css (sin <style> en línea).
  fetch('api/version',{cache:'no-store'}).then(function(r){return r.json()}).then(function(d){
    if(!d||!d.version) return;
    var txt='Pi Console v'+d.version;
    var main=document.querySelector('.main');
    if(main){var f=document.createElement('footer');f.className='pc-footer';f.textContent=txt;main.appendChild(f);}
    var box=document.querySelector('.login-box');
    if(box){var v=document.createElement('div');v.className='pc-ver';v.textContent=txt;box.appendChild(v);}
  }).catch(function(){});
})();
