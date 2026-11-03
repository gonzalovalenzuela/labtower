// LabTower — navegación compartida: barra superior con selector de módulo (escritorio y tablet) y barra inferior (móvil).
// EN: LabTower — shared navigation: top bar with a module switcher (desktop and tablet) and a bottom bar (phones).
// ES: El mismo orden y agrupación en todos los módulos y en el Resumen. El selector muestra solo los módulos a los que tienes permiso y los
//     que el admin no apagó, con su estado (forma + texto, nunca solo color). El estado sale de un único GET público a /admin/api/health,
//     guardado 45 s en la pestaña. La barra del módulo (idioma, tema, usuario) y su panel lateral (listas del módulo) no cambian.
// EN: Same order and grouping everywhere. The switcher lists only the modules you may use and the ones the admin did not turn off, with their
//     status (shape + text, never colour alone). Status comes from one public GET to /admin/api/health, kept 45 s in the tab. The module's own
//     bar (language, theme, user) and its side panel (module lists) are unchanged.
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
  var T = {
    es: {mods: 'Módulos', opts: 'Opciones', main: 'Principal', switchTo: 'Cambiar de módulo', up: 'Activo', mid: 'Con avisos', down: 'Con fallas', home: 'Inicio de LabTower'},
    en: {mods: 'Modules', opts: 'Options', main: 'Main', switchTo: 'Switch module', up: 'Active', mid: 'Warnings', down: 'Failing', home: 'LabTower home'}
  };
  var SHAPE = {
    up:   '<circle cx="5" cy="5" r="4.5" fill="#15803d"/>',
    mid:  '<path d="M5 .5l4.5 8.5h-9z" fill="#b45309"/>',
    down: '<rect x=".5" y=".5" width="9" height="9" rx="1.5" fill="#b91c1c"/>'
  };
  var LV = {readonly: 1, execute: 2, admin: 3};
  var health = null, timer = null, st = null;      // st: {box parts, opts, me}

  function visible(id, me) {
    if (id === 'home' || id === 'overview') return true;
    if (!me || !me.permissions) return true;                                    // permisos aún desconocidos / permissions not known yet
    if ((me.disabled || []).indexOf(id) >= 0) return false;
    if (id === 'admin') return Object.keys(me.permissions).some(function (k) { return me.permissions[k] === 'admin'; });
    return !!LV[me.permissions[id]];
  }
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  function icon(path, size) {
    var s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('aria-hidden', 'true');
    if (size) { s.setAttribute('width', size); s.setAttribute('height', size); }
    s.innerHTML = path;                                                           // constante propia / own constant
    return s;
  }
  function name(id, lang) { var it = I[id]; return it.label || (lang === 'es' ? it.es : it.en); }
  function level(id) {
    var s = health && health[id]; s = s && s.status;
    return s === 'ok' ? 'up' : s === 'degraded' ? 'mid' : s ? 'down' : '';
  }
  function paint() {
    if (!st) return;
    var tr = T[st.lang];
    document.querySelectorAll('.gt[data-nav-id] .gt-st').forEach(function (box) {
      var lv = level(box.parentNode.getAttribute('data-nav-id'));
      box.textContent = '';
      if (!lv) return;
      var sv = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      sv.setAttribute('width', '10'); sv.setAttribute('height', '10'); sv.setAttribute('viewBox', '0 0 10 10'); sv.setAttribute('aria-hidden', 'true');
      sv.innerHTML = SHAPE[lv];                                                   // constante propia / own constant
      box.appendChild(sv); box.appendChild(document.createTextNode(tr[lv]));
    });
    var cur = document.querySelector('.gsw-st');
    if (cur) { var l2 = level(st.opts.self); cur.className = 'gsw-st' + (l2 ? ' ' + l2 : ''); cur.title = l2 ? tr[l2] : ''; }
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

  // ── Estructura (se crea una vez) / structure (created once) ──
  function ensure() {
    if (st && st.bar && document.body.contains(st.bar)) return;
    var bar = el('header', 'gbar'), nav = el('nav', 'gbar-in');
    nav.appendChild(el('a', 'gbar-logo', 'LT')); nav.lastChild.href = '/';
    nav.appendChild(el('span', 'gbar-sep', '/'));
    var crumb = el('span', 'gbar-grp'); nav.appendChild(crumb);
    var sw = el('button', 'gsw'); sw.type = 'button'; sw.setAttribute('aria-haspopup', 'dialog'); sw.setAttribute('aria-expanded', 'false'); sw.setAttribute('aria-controls', 'gpanel');
    nav.appendChild(sw); bar.appendChild(nav);
    var panel = el('div', 'gpanel'); panel.id = 'gpanel'; panel.setAttribute('role', 'dialog'); panel.hidden = true;
    var back = el('div', 'gback'); back.hidden = true;
    var tab = el('nav', 'gtab');
    document.body.insertBefore(bar, document.body.firstChild);
    document.body.appendChild(panel); document.body.appendChild(back); document.body.appendChild(tab);
    document.body.classList.add('has-gbar');
    st = {bar: bar, nav: nav, crumb: crumb, sw: sw, panel: panel, back: back, tab: tab, lang: 'en', opts: {}, me: null};
    sw.addEventListener('click', function () { toggle(); });
    back.addEventListener('click', function () { toggle(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !st.panel.hidden) { toggle(false); st.sw.focus(); } });
    document.addEventListener('mousedown', function (e) {
      if (st.panel.hidden) return;
      if (st.panel.contains(e.target) || st.sw.contains(e.target) || st.tab.contains(e.target)) return;
      toggle(false);
    });
  }
  function toggle(on) {
    var open = on === undefined ? st.panel.hidden : on;
    st.panel.hidden = !open; st.back.hidden = !open;
    st.sw.setAttribute('aria-expanded', open ? 'true' : 'false');
    var m = st.tab.querySelector('[data-gtab="mods"]'); if (m) m.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) { var a = st.panel.querySelector('a[aria-current="page"]') || st.panel.querySelector('a'); if (a) a.focus(); }
  }

  function fill() {
    var o = st.opts, lang = st.lang, tr = T[lang], me = st.me, self = o.self;
    // barra superior: ruta + selector / top bar: crumb + switcher
    st.nav.setAttribute('aria-label', tr.main);
    st.nav.querySelector('.gbar-logo').setAttribute('aria-label', tr.home);
    var grp = G.filter(function (g) { return g.es && g.items.indexOf(self) >= 0; })[0];
    st.crumb.textContent = ''; st.crumb.hidden = !grp;
    if (grp) { st.crumb.appendChild(document.createTextNode(lang === 'es' ? grp.es : grp.en)); st.crumb.appendChild(el('span', 'gbar-sep', '›')); }
    st.sw.textContent = '';
    st.sw.appendChild(icon(I[self] ? I[self].svg : I.overview.svg, 16));
    st.sw.appendChild(document.createTextNode(I[self] ? name(self, lang) : ''));
    st.sw.appendChild(el('span', 'gsw-st'));
    st.sw.appendChild(icon('<path d="M6 9l6 6 6-6"/>', 12)); st.sw.lastChild.setAttribute('class', 'gsw-chev');
    st.sw.setAttribute('aria-label', tr.switchTo + ': ' + (I[self] ? name(self, lang) : ''));
    // panel / panel
    st.panel.setAttribute('aria-label', tr.switchTo);
    st.panel.textContent = '';
    G.forEach(function (g) {
      var ids = g.items.filter(function (id) { return visible(id, me); });
      if (!ids.length) return;
      var wrap = el('div', g.es ? 'gg' : 'gg gg-top');
      if (g.es) wrap.appendChild(el('div', 'gg-lbl', lang === 'es' ? g.es : g.en));
      var grid = el('div', g.es ? 'gg-grid' : 'gg-pills');
      ids.forEach(function (id) {
        var a = el('a', g.es ? 'gt' : 'gp' + (id === self ? ' on' : ''));
        a.href = I[id].href; a.setAttribute('data-nav-id', id);
        if (id === self) { a.setAttribute('aria-current', 'page'); if (g.es) a.className += ' on'; }
        if (g.es) {
          a.appendChild(icon(I[id].svg, 18));
          a.appendChild(el('span', 'gt-n', name(id, lang)));
          a.appendChild(el('span', 'gt-st'));
        } else {
          a.appendChild(icon(I[id].svg, 15)); a.appendChild(document.createTextNode(name(id, lang)));
        }
        grid.appendChild(a);
      });
      wrap.appendChild(grid); st.panel.appendChild(wrap);
    });
    // barra inferior (móvil) / bottom bar (phones)
    st.tab.textContent = ''; st.tab.setAttribute('aria-label', tr.main);
    function tabItem(id, label, svgPath, href, on) {
      var a = el(href ? 'a' : 'button', 'gtab-i' + (on ? ' on' : ''));
      if (href) a.href = href; else a.type = 'button';
      if (on) a.setAttribute('aria-current', 'page');
      var ic = el('span', 'gtab-ic'); ic.appendChild(icon(svgPath, 22)); a.appendChild(ic); a.appendChild(el('span', 'gtab-t', label));
      st.tab.appendChild(a); return a;
    }
    tabItem('home', name('home', lang), I.home.svg, '/', false);
    tabItem('overview', name('overview', lang), I.overview.svg, '/overview/', self === 'overview');
    var m = tabItem('mods', tr.mods, '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>', null, false);
    m.setAttribute('data-gtab', 'mods'); m.setAttribute('aria-haspopup', 'dialog'); m.setAttribute('aria-expanded', st.panel.hidden ? 'false' : 'true');
    m.addEventListener('click', function () { toggle(); });
    if (document.querySelector('.sidebar')) {                                       // módulos: abre el panel propio (listas, filtros) / modules: opens their own panel
      var op = tabItem('opts', tr.opts, '<line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/>', null, false);
      op.addEventListener('click', function () { toggle(false); var b = document.getElementById('nav-toggle'); if (b) b.click(); });
    }
    // el menú lateral viejo ya no se usa / the old side menu is gone
    var old = document.getElementById('nav-items'); if (old) { var sec = old.closest('.sb-sec'); (sec || old).hidden = true; }
    paint(); loadHealth();
    if (!timer) timer = setInterval(function () { try { sessionStorage.removeItem('lt-nav-health'); } catch (e) {} loadHealth(); }, 60000);
  }

  window.labNav = {
    // opts: {self, lang, me, fetchMe}
    render: function (o) {
      o = o || {};
      ensure();
      st.opts = o; st.lang = o.lang === 'es' ? 'es' : 'en'; st.me = o.me || st.me || null;
      document.documentElement.setAttribute('data-gbar', '1');
      fill();
      if (!o.me && o.fetchMe && !st.me && !st.fetching) {
        st.fetching = true;
        fetch('api/me').then(function (r) { return r.json(); }).then(function (m) { st.fetching = false; if (m && m.permissions) { st.me = m; fill(); } }).catch(function () { st.fetching = false; });
      }
    }
  };
})();
