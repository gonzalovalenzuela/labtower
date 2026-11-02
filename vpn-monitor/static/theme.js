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

// ES: Segundo factor en TODOS los formularios de acceso. Si la cuenta tiene 2FA, el servidor responde «2FA code required» y aquí se agrega un campo de código
//     bajo la contraseña; el código se manda con el siguiente intento. Sin 2FA no cambia nada. EN: Second factor on EVERY login form. If the account has 2FA the
//     server answers "2FA code required" and a code field is added under the password; the code travels with the next attempt. Without 2FA nothing changes.
(function(){
  if(!window.fetch||window.__ltTotp)return;window.__ltTotp=1;
  var T={es:{err:'Escribe el código de 6 dígitos de tu app de autenticación (o un código de recuperación).',lbl:'Código de verificación',bad:'Código no válido'},
         en:{err:'Enter the 6-digit code from your authenticator app (or a recovery code).',lbl:'Verification code',bad:'Invalid code'}};
  function L(){return T[(document.documentElement.lang||'en').slice(0,2)==='es'?'es':'en']}
  var f0=window.fetch;
  window.fetch=function(u,o){
    var isLogin=typeof u==='string'&&/(^|\/)api\/login$/.test(u)&&o&&o.method==='POST'&&typeof o.body==='string';
    if(isLogin){var c=document.getElementById('lt-code');if(c&&c.value.trim()){try{var b=JSON.parse(o.body);b.code=c.value.trim();o=Object.assign({},o,{body:JSON.stringify(b)})}catch(e){}}}
    var p=f0.call(this,u,o);
    if(!isLogin)return p;
    function clr(){var q=document.getElementById('lt-code');if(q)q.value=''}
    return p.then(function(r){
      if(r.status!==401){clr();return r}
      return r.clone().json().then(function(d){
        if(!d||d.error!=='2FA code required'){clr();return r}
        var pw=document.querySelector('input[type=password]');
        if(pw&&!document.getElementById('lt-code')){
          var w=document.createElement('div');w.style.cssText='margin-top:10px';
          w.innerHTML='<label style="display:block;font-size:12px;margin-bottom:4px"></label><input id="lt-code" inputmode="numeric" autocomplete="one-time-code" maxlength="12" style="width:100%;box-sizing:border-box;font:inherit;padding:10px;border-radius:8px;border:1px solid var(--border,#555);background:var(--bg-input,transparent);color:inherit">';
          w.firstChild.textContent=L().lbl;
          var host=pw.closest('.field,.lfield,.fld')||pw.parentNode;host.parentNode.insertBefore(w,host.nextSibling);
          var ci=w.querySelector('input');ci.addEventListener('keydown',function(e){if(e.key==='Enter'){pw.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))}});
          ci.focus();
        } else if(document.getElementById('lt-code')){document.getElementById('lt-code').focus()}
        return new Response(JSON.stringify({error:L().err,need_code:true}),{status:401,headers:{'Content-Type':'application/json'}});
      }).catch(function(){return r});
    });
  };
})();
