// Pie con la versión instalada, leída de /api/version. Se repite igual en todas las páginas.
// EN: Footer with the installed version, read from /api/version. Repeated identically on every page.
/* Version footer (same snippet in every page): shows the installed LabTower version */
(function(){
  // Estilos del pie: en app.css (sin <style> en línea).
  // ES: En la página de inicio (ruta «/») la versión la da el módulo de administración.
  // EN: On the home page (path "/") the version comes from the admin module.
  var api=location.pathname.replace(/[^\/]*$/,'')==='/'?'/admin/api/version':'api/version';
  fetch(api,{cache:'no-store'}).then(function(r){return r.json()}).then(function(d){
    if(!d||!d.version) return;
    var txt='LabTower v'+d.version;
    var main=document.querySelector('.main')||document.querySelector('.ov-in')||document.querySelector('.container');
    if(main){var f=document.createElement('footer');f.className='pc-footer';f.textContent=txt;main.appendChild(f);}
    var box=document.querySelector('.login-box')||(main?null:document.querySelector('.box'));
    if(box){var v=document.createElement('div');v.className='pc-ver';v.textContent=txt;box.appendChild(v);}
  }).catch(function(){});
})();
