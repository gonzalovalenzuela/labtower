/* LabTower — enlaza los atributos data-on-<evento> a funciones, sin JavaScript en línea (CSP sin 'unsafe-inline').
   Formato: data-on-click="funcion" data-on-click-args='[…JSON…]' data-on-click-stop="1".
   Argumentos especiales: {"@":"this"} (elemento), {"@":"event"} (evento), {"@":"value"} (this.value).
   EN: Binds data-on-<event> attributes to functions, with no inline JavaScript (CSP without 'unsafe-inline').

   Seguridad: solo se pueden invocar las funciones REGISTRADAS con cspRegister({nombre: función, …}) (cada app.js registra las suyas) y las
   internas «@…». Antes se buscaba cualquier nombre en window, así que un atributo inyectado (data-on-click="eval"/"fetch"…) habría podido llamar a cualquier función global.
   EN: Security: only functions REGISTERED with cspRegister({name: fn, …}) (each app.js registers its own) and the "@…" built-ins can be called.
       Before, any name was looked up on window, so an injected attribute (data-on-click="eval"/"fetch"…) could have called any global function. */
(function () {
  'use strict';
  var REG = Object.create(null);
  window.cspRegister = function (map) {
    for (var k in map) if (Object.prototype.hasOwnProperty.call(map, k) && typeof map[k] === 'function') REG[k] = map[k];
  };
  var EV = ['click', 'change', 'keydown', 'mousemove', 'mouseleave', 'mouseover', 'mouseout'];
  var SEL = EV.map(function (e) { return '[data-on-' + e + ']'; }).join(',');

  function val(a, el, ev) {
    if (a && typeof a === 'object' && a['@']) {
      var k = a['@'];
      return k === 'this' ? el : k === 'event' ? ev : k === 'value' ? el.value : undefined;
    }
    return a;
  }
  var BUILTIN = {
    '@stop': function (el, ev) { ev.stopPropagation(); },
    '@reload': function () { location.reload(); },
    '@click-id': function (el, ev, a) { var x = document.getElementById(a[0]); if (x) x.click(); },
    '@disable-unless-checked': function (el, ev, a) { var x = document.getElementById(a[0]); if (x) x.disabled = !el.checked; },
    '@self-only': function (el, ev, a) { if (ev.target === el && typeof REG[a[0]] === 'function') REG[a[0]](); },
    '@style': function (el, ev, a) { for (var k in a[0]) el.style[k] = a[0][k]; }
  };

  function bindOne(el, e) {
    var flag = '_piBound_' + e;
    if (el[flag]) return;
    el[flag] = true;
    var name = el.getAttribute('data-on-' + e);
    var raw = el.getAttribute('data-on-' + e + '-args');
    var stop = el.hasAttribute('data-on-' + e + '-stop');
    var args = [];
    try { args = raw ? JSON.parse(raw) : []; } catch (err) { console.error('data-on-' + e + '-args inválido', raw); return; }
    el.addEventListener(e, function (ev) {
      try {
        var fn = Object.prototype.hasOwnProperty.call(BUILTIN, name) ? BUILTIN[name] : REG[name];
        if (typeof fn !== 'function') { console.error('Función no registrada:', name); return; }
        if (Object.prototype.hasOwnProperty.call(BUILTIN, name)) fn(el, ev, args);
        else fn.apply(el, args.map(function (a) { return val(a, el, ev); }));
      } finally {
        if (stop) ev.stopPropagation();
      }
    });
  }
  function bindAll(el) { EV.forEach(function (e) { if (el.hasAttribute('data-on-' + e)) bindOne(el, e); }); }
  function scan(root) {
    if (!root || root.nodeType !== 1) return;
    if (root.matches(SEL)) bindAll(root);
    var l = root.querySelectorAll(SEL);
    for (var i = 0; i < l.length; i++) bindAll(l[i]);
  }
  window.cspBind = scan;
  new MutationObserver(function (muts) {
    muts.forEach(function (m) { for (var i = 0; i < m.addedNodes.length; i++) scan(m.addedNodes[i]); });
  }).observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { scan(document.documentElement); });
  else scan(document.documentElement);
})();
