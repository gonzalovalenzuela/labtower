// LabTower — navegación compartida (la misma en la portada de cada módulo y en el Resumen).
// EN: LabTower — shared navigation (the same in every module and in the Overview).
// ES: Un solo orden y agrupación en todas partes. Muestra solo los módulos a los que tienes permiso y los que el admin no apagó,
//     con su estado junto al nombre (un único GET público a /admin/api/health, guardado 45 s en la pestaña).
// EN: One order and grouping everywhere. Shows only the modules you may use and the ones the admin did not turn off, with their
//     status next to the name (a single public GET to /admin/api/health, kept 45 s in the tab).
(function () {
  'use strict';
  var I = {
    home:     {href: '/',          es: 'Inicio',  en: 'Home',     svg: '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h5v-6h4v6h5V10"/>'},
    overview: {href: '/overview/', es: 'Resumen', en: 'Overview', svg: '<rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>'},
    nut: {href: '/nut/', label: 'UPS Monitor', svg: '<path d="M5 9V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v4"/><rect x="3" y="9" width="18" height="11" rx="2"/><line x1="12" y1="13" x2="12" y2="16"/>'},
    pve: {href: '/pve/', label: 'Proxmox',     svg: '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>'},
    nas: {href: '/nas/', label: 'NAS Monitor', svg: '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="7" y1="9" x2="17" y2="9"/><line x1="7" y1="14" x2="17" y2="14"/><line x1="16" y1="18" x2="16.01" y2="18"/>'},
    net: {href: '/net/', label: 'Net Monitor', svg: '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>'},
    dns: {href: '/dns/', label: 'DNS Monitor', svg: '<circle cx="12" cy="12" r="9"/><line x1="3" y1="12" x2="21" y2="12"/><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z"/>'},
    wan: {href: '/wan/', label: 'WAN Monitor', svg: '<path d="M5 12.55a11 11 0 0 1 14 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/>'},
    vpn: {href: '/vpn/', label: 'VPN Monitor', svg: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>'},
    wol: {href: '/wol/', label: 'WOL Console', svg: '<polygon points="13,2 3,14 12,14 11,22 21,10 12,10"/>'},
    admin: {href: '/admin/', label: 'Admin Panel', svg: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'}
  };
  var G = [
    {items: ['home', 'overview']},
    {es: 'Energía y servidores', en: 'Power & servers', items: ['nut', 'pve', 'nas']},
    {es: 'Red', en: 'Network', items: ['net', 'dns', 'wan', 'vpn']},
    {es: 'Herramientas', en: 'Tools', items: ['wol']},
    {es: 'Sistema', en: 'System', items: ['admin']}
  ];
  var LV = {readonly: 1, execute: 2, admin: 3};
  var health = null, last = null;

  function visible(id, me) {
    if (id === 'home' || id === 'overview') return true;
    if (!me || !me.permissions) return true;                                    // permisos aún desconocidos / permissions not known yet
    if ((me.disabled || []).indexOf(id) >= 0) return false;
    if (id === 'admin') return Object.keys(me.permissions).some(function (k) { return me.permissions[k] === 'admin'; });
    return !!LV[me.permissions[id]];
  }
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  function paint() {
    document.querySelectorAll('[data-nav-id] .nav-dot').forEach(function (d) {
      var s = health && health[d.parentNode.getAttribute('data-nav-id')];
      s = s && s.status;
      d.className = 'nav-dot' + (s === 'ok' ? ' up' : s === 'degraded' ? ' mid' : s ? ' down' : '');
      d.title = s === 'ok' ? '●' : s || '';
    });
  }
  function loadHealth() {
    try { var c = JSON.parse(sessionStorage.getItem('lt-nav-health') || 'null'); if (c && Date.now() - c.t < 45000) { health = c.m; paint(); return; } } catch (e) {}
    if (!window.fetch) return;
    fetch('/admin/api/health', {cache: 'no-store', signal: window.AbortSignal && AbortSignal.timeout ? AbortSignal.timeout(5000) : undefined})
      .then(function (r) { return r.json(); })
      .then(function (d) {
        health = d && d.modules || null; paint();
        try { sessionStorage.setItem('lt-nav-health', JSON.stringify({t: Date.now(), m: health})); } catch (e) {}
      }).catch(function () {});
  }
  function build(o, me) {
    var box = o.el || document.getElementById(o.mode === 'strip' ? 'navstrip' : 'nav-items');
    if (!box) return;
    var es = o.lang === 'es', strip = o.mode === 'strip';
    box.textContent = '';
    var first = true;
    G.forEach(function (g) {
      var ids = g.items.filter(function (id) { return visible(id, me); });
      if (!ids.length) return;
      if (strip) { if (!first) box.appendChild(el('span', 'nav-sep')); }
      else if (g.es) box.appendChild(el('div', 'nav-group-lbl', es ? g.es : g.en));
      first = false;
      ids.forEach(function (id) {
        var it = I[id], self = id === o.self;
        var a = el('a', (strip ? 'nav-chip' : 'nav-item') + (self ? ' active' : ''));
        a.href = it.href; a.setAttribute('data-nav-id', id);
        if (self) a.setAttribute('aria-current', 'page');
        var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 24 24'); svg.innerHTML = it.svg;          // constante propia / own constant
        a.appendChild(svg);
        a.appendChild(document.createTextNode(it.label || (es ? it.es : it.en)));
        if (I[id].label && id !== 'admin') a.appendChild(el('span', 'nav-dot'));
        box.appendChild(a);
      });
    });
    paint(); loadHealth();
    if (!last) last = setInterval(function () { try { sessionStorage.removeItem('lt-nav-health'); } catch (e) {} loadHealth(); }, 60000);
  }
  window.labNav = {
    // opts: {self, lang, me, mode: 'side'|'strip', fetchMe, el}
    render: function (o) {
      o = o || {};
      build(o, o.me || null);
      if (!o.me && o.fetchMe) fetch('api/me').then(function (r) { return r.json(); }).then(function (m) { if (m && m.permissions) build(o, m); }).catch(function () {});
    }
  };
})();
