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
      if(r.status!==401){clr();if(r.ok){var e=document.getElementById('lt-code');if(e&&e.parentNode&&e.parentNode.parentNode)e.parentNode.parentNode.removeChild(e.parentNode)}return r}
      return r.clone().json().then(function(d){
        if(!d||d.error!=='2FA code required'){clr();return r}
        var pw=document.querySelector('input[type=password]');
        if(pw&&!document.getElementById('lt-code')){
          var w=document.createElement('div');w.style.cssText='margin-top:10px';
          w.innerHTML='<label style="display:block;font-size:12px;margin-bottom:4px"></label><input id="lt-code" inputmode="numeric" autocomplete="one-time-code" maxlength="12" style="width:100%;box-sizing:border-box;font:inherit;padding:10px;border-radius:8px;border:1px solid var(--border,#555);background:var(--bg-input,transparent);color:inherit">';
          w.firstChild.textContent=L().lbl;
          var host=pw.closest('.field,.lfield,.fld')||pw;host.parentNode.insertBefore(w,host.nextSibling);
          var ci=w.querySelector('input');ci.addEventListener('keydown',function(e){if(e.key==='Enter'){pw.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))}});
          ci.focus();
        } else if(document.getElementById('lt-code')){document.getElementById('lt-code').focus()}
        return new Response(JSON.stringify({error:L().err,need_code:true}),{status:401,headers:{'Content-Type':'application/json'}});
      }).catch(function(){return r});
    });
  };
})();

// ES: LabTower instalado en la pantalla de inicio (iPhone, iPad, Android). (1) La barra de estado sigue el tema elegido en LabTower, no solo el del
//     equipo. (2) La pantalla de arranque usa el fondo claro u oscuro según el tema del equipo (iOS la toma al «Agregar a pantalla de inicio»).
//     (3) Sin el botón de recarga del navegador: deslizar hacia abajo desde arriba del todo recarga la página. (4) Con HTTPS, un service worker
//     muestra «Sin conexión» cuando el servidor no responde; solo guarda esa página, nunca datos.
// EN: LabTower installed on the home screen (iPhone, iPad, Android). (1) The status bar follows the theme chosen in LabTower, not only the
//     device one. (2) The launch screen uses the light or dark background per the device theme (iOS takes it on "Add to Home Screen").
//     (3) Without the browser's reload button: pulling down from the very top reloads the page. (4) Over HTTPS, a service worker shows
//     "No connection" when the server does not answer; it only stores that page, never data.
(function(){
  var d=document.documentElement,LIGHT='#f0f2f5',DARK='#0f1420';
  function theme(){var t='dark';try{t=localStorage.getItem('pi-theme')||'dark'}catch(e){}return t}
  function barColor(){
    var t=theme();
    Array.prototype.forEach.call(document.querySelectorAll('meta[name="theme-color"]'),function(m){
      var dk=/dark/.test(m.getAttribute('media')||'');
      m.setAttribute('content',t==='system'?(dk?DARK:LIGHT):(d.getAttribute('data-theme')==='light'?LIGHT:DARK));
    });
  }
  barColor();document.addEventListener('DOMContentLoaded',barColor);document.addEventListener('pi-theme',barColor);

  var ios=/iP(hone|od|ad)/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  var installed=navigator.standalone===true||(window.matchMedia&&matchMedia('(display-mode: standalone)').matches);

  // (2) Pantallas de arranque generadas para el tamaño exacto de este equipo, clara y oscura. / EN: Launch screens made for this device's exact size, light and dark.
  function splash(){
    if(!ios||installed||document.querySelector('link[rel="apple-touch-startup-image"]'))return;
    var ic=document.querySelector('link[rel="apple-touch-icon"]');if(!ic)return;
    var img=new Image();
    img.onload=function(){
      var r=window.devicePixelRatio||1,w=screen.width,h=screen.height;
      [[LIGHT,'light'],[DARK,'dark']].forEach(function(x){
        var c=document.createElement('canvas');c.width=w*r;c.height=h*r;var g=c.getContext('2d');if(!g)return;
        g.fillStyle=x[0];g.fillRect(0,0,c.width,c.height);
        var s=Math.round(Math.min(c.width,c.height)*0.28);g.drawImage(img,(c.width-s)/2,(c.height-s)/2,s,s);
        var l=document.createElement('link');l.rel='apple-touch-startup-image';l.href=c.toDataURL('image/png');
        l.media='(device-width: '+w+'px) and (device-height: '+h+'px) and (-webkit-device-pixel-ratio: '+r+') and (orientation: portrait) and (prefers-color-scheme: '+x[1]+')';
        document.head.appendChild(l);
      });
    };
    img.src=ic.getAttribute('href');
  }

  // (3) Deslizar para recargar, solo instalado. / EN: Pull to refresh, installed only.
  // Clases propias (lt-go, lt-spin): «spin» ya existe en el app.css de cada módulo y su animación pisaba el translate del ícono,
  // que giraba en órbita y parecía aparecer varias veces. / EN: Own classes (lt-go, lt-spin): "spin" already exists in each module's
  // app.css and its animation overrode the icon's translate, so it orbited and seemed to appear several times.
  function pull(){
    if(!installed||!document.body)return;
    var y0=null,dy=0,el=null,GO=70,MAX=96;
    function ind(){if(!el){el=document.createElement('div');el.className='lt-ptr';el.setAttribute('aria-hidden','true');el.innerHTML='<span><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><polyline points="21 3 21 9 15 9"/></svg></span>';document.body.appendChild(el)}return el}
    function hide(){if(el){el.style.opacity='0';el.style.transform='';el.classList.remove('lt-go')}}
    function inner(t){for(var n=t;n&&n.nodeType===1&&n!==document.body;n=n.parentNode)if(n.scrollTop>0)return true;return false}
    // Arriba del todo (2 px de margen por el rebote) y no desde el borde superior, que abre el Centro de Notificaciones.
    // EN: At the very top (2 px margin for the bounce) and not from the top edge, which opens Notification Center.
    document.addEventListener('touchstart',function(e){var t=e.touches[0];y0=(!busy&&window.scrollY<=2&&e.touches.length===1&&t.clientY>30&&!inner(e.target))?t.clientY:null;dy=0},{passive:true});
    document.addEventListener('touchmove',function(e){
      if(y0===null)return;dy=e.touches[0].clientY-y0;if(dy<=0){hide();return}
      var k=Math.min(dy,MAX),i=ind();i.style.opacity=String(Math.min(1,k/GO));i.style.transform='translate(-50%,'+k+'px)';
      i.firstChild.style.transform='rotate('+(k*4)+'deg)';i.classList.toggle('lt-go',dy>=GO);
    },{passive:true});
    // Recarga a prueba de iOS: instalada, WebKit a veces ignora location.reload() si llega en el mismo toque o mientras la página
    // todavía rebota, y el ícono quedaba girando. Se recarga al terminar el rebote; si a los 4 s la página sigue aquí se reintenta con
    // location.replace y, si tampoco, a los 10 s se esconde el ícono para poder deslizar de nuevo.
    // EN: iOS-proof reload: when installed, WebKit sometimes ignores location.reload() if it comes in the same touch or while the page is
    // still bouncing, and the icon kept spinning. It reloads once the bounce ends; if the page is still here after 4 s it retries with
    // location.replace and, if that fails too, the icon is hidden after 10 s so you can pull again.
    // Con #ancla (p. ej. #switches) replace a la misma dirección no recarga, así que se usa reload.
    // EN: With a #fragment (e.g. #switches) replacing with the same address does not reload, so reload is used.
    var busy=false,tries=[];
    function stop(){busy=false;tries.forEach(clearTimeout);tries=[];if(el)el.classList.remove('lt-spin');hide()}
    function reload(){
      busy=true;ind().classList.add('lt-spin');
      var t0=Date.now();
      (function go(){if(window.scrollY<0&&Date.now()-t0<800){requestAnimationFrame(go);return}location.reload()})();
      tries=[setTimeout(function(){if(location.hash)location.reload();else location.replace(location.href)},4000),setTimeout(stop,10000)];
    }
    function end(){
      if(y0!==null&&dy>=GO&&!busy)setTimeout(reload,0);else if(!busy)hide();
      y0=null;dy=0;
    }
    // iOS a veces cancela el toque en vez de terminarlo; cuenta igual. / EN: iOS sometimes cancels the touch instead of ending it; it counts the same.
    document.addEventListener('touchend',end,{passive:true});document.addEventListener('touchcancel',end,{passive:true});
    // Página restaurada desde la caché de iOS con el ícono aún girando. / EN: Page restored from the iOS cache with the icon still spinning.
    window.addEventListener('pageshow',function(e){if(e.persisted)stop()});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){splash();pull()});else{splash();pull()}

  // (4) Página «Sin conexión» (solo HTTPS: el navegador no permite service workers sin él). / EN: "No connection" page (HTTPS only).
  if('serviceWorker' in navigator&&location.protocol==='https:')
    window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js',{scope:'/'}).catch(function(){})});
})();
