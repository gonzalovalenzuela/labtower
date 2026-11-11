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
    uptime: {href: '/uptime/', label: 'Uptime Monitor', svg: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'},
    wol: {href: '/wol/', label: 'WOL Console', svg: '<polygon points="13,2 3,14 12,14 11,22 21,10 12,10"/>'},
    admin: {href: '/admin/', label: 'Admin Panel', svg: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'}
  };
  var G = [
    {items: ['home', 'overview']},
    {es: 'Energía y servidores', en: 'Power & servers', items: ['nut', 'pve', 'nas']},
    {es: 'Red', en: 'Network', items: ['net', 'dns', 'wan', 'vpn', 'uptime']},
    {es: 'Herramientas', en: 'Tools', items: ['wol']},
    {es: 'Sistema', en: 'System', items: ['admin']}
  ];
  var T = {
    es: {mods: 'Módulos', opts: 'Opciones', out: 'Salir', main: 'Principal', switchTo: 'Cambiar de módulo', up: 'Activo', mid: 'Con avisos', down: 'Con fallas', home: 'Inicio de LabTower',
      warn: 'Atención', menuType: 'Tipo de menú', wizTitle: 'Elige cómo quieres navegar',
      wizText: 'Puedes cambiarlo cuando quieras desde «Tipo de menú». Se guarda en este navegador.',
      optBar: 'Barra superior con selector', optBarD: 'Un selector con todos los módulos y su estado. En el móvil, una barra inferior.',
      optSide: 'Menú lateral clásico', optSideD: 'Los módulos agrupados en el panel lateral, como antes.', current: 'Actual', ok: 'Listo'},
    en: {mods: 'Modules', opts: 'Options', out: 'Sign out', main: 'Main', switchTo: 'Switch module', up: 'Active', mid: 'Warnings', down: 'Failing', home: 'LabTower home',
      warn: 'Attention', menuType: 'Menu type', wizTitle: 'Choose how you want to navigate',
      wizText: 'You can change it any time from “Menu type”. It is saved in this browser.',
      optBar: 'Top bar with switcher', optBarD: 'One switcher with every module and its status. On phones, a bottom bar.',
      optSide: 'Classic side menu', optSideD: 'Modules grouped in the side panel, as before.', current: 'Current', ok: 'Done'}
  };
  var SHAPE = {
    up:   '<circle cx="5" cy="5" r="4.5" fill="#15803d"/>',
    mid:  '<path d="M5 .5l4.5 8.5h-9z" fill="#b45309"/>',
    down: '<rect x=".5" y=".5" width="9" height="9" rx="1.5" fill="#b91c1c"/>'
  };
  var LV = {readonly: 1, execute: 2, admin: 3};
  var health = null, timer = null, st = null;      // st: {box parts, opts, me}
  var MODE_KEY = 'lt-nav-mode';                    // 'bar' (nuevo / new) | 'side' (clásico / classic)
  function getMode() { try { var m = localStorage.getItem(MODE_KEY); return m === 'side' || m === 'bar' ? m : null; } catch (e) { return null; } }
  function setMode(m) { try { localStorage.setItem(MODE_KEY, m); } catch (e) {} }
  function mode() { return getMode() || 'bar'; }

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
    document.querySelectorAll('.nav-item[data-nav-id] .nav-dot, .nav-chip[data-nav-id] .nav-dot').forEach(function (d) {
      var lv = level(d.parentNode.getAttribute('data-nav-id'));
      d.className = 'nav-dot' + (lv ? ' ' + lv : ''); d.title = lv ? tr[lv] : '';
    });
    warnStrip();
    var cur = document.querySelector('.gsw-st');
    if (cur) { var l2 = level(st.opts.self); cur.className = 'gsw-st' + (l2 ? ' ' + l2 : ''); cur.title = l2 ? tr[l2] : ''; }
  }
  // Aviso arriba del contenido, bajo el menú / notice at the top of the content, under the menu
  function warnStrip() {
    var host = st.opts.self === 'overview' ? null : document.querySelector('.main'), box = document.getElementById('gwarn'), tr = T[st.lang];
    var bad = [];
    if (host && health) Object.keys(I).forEach(function (id) {
      var lv = level(id);
      if ((lv === 'mid' || lv === 'down') && visible(id, st.me)) bad.push([id, lv]);
    });
    if (!bad.length) { if (box) box.remove(); return; }
    if (!box) { box = el('div', 'gwarn'); box.id = 'gwarn'; box.setAttribute('role', 'status'); }
    var tbar = host.querySelector(':scope > .topbar'), at = tbar ? tbar.nextSibling : host.firstChild;   // bajo la barra del módulo, no encima / under the module bar, not above it
    if (box.parentNode !== host || (tbar ? box.previousSibling !== tbar : host.firstChild !== box)) host.insertBefore(box, at);
    box.className = 'gwarn ' + (bad.some(function (b) { return b[1] === 'down'; }) ? 'down' : 'mid');
    box.textContent = '';
    box.appendChild(el('b', 'gwarn-t', tr.warn));
    bad.forEach(function (b) {
      var a = el('a', 'gwarn-i'); a.href = I[b[0]].href;
      var sv = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      sv.setAttribute('width', '11'); sv.setAttribute('height', '11'); sv.setAttribute('viewBox', '0 0 10 10'); sv.setAttribute('aria-hidden', 'true');
      sv.innerHTML = SHAPE[b[1]];                                                 // constante propia / own constant
      a.appendChild(sv); a.appendChild(document.createTextNode(name(b[0], st.lang) + ' · ' + tr[b[1]]));
      var why = detail(b[0]);
      if (why) { var dd = el('span', 'gwarn-d', why.length > 180 ? why.slice(0, 179) + '…' : why); dd.title = why; a.appendChild(dd); }
      box.appendChild(a);
    });
  }
  // Detalle de lo que falla en un módulo: el texto de cada chequeo que no está OK (solo llega con sesión).
  // EN: Detail of what fails in a module: the text of every check that is not OK (only sent with a session).
  function detail(id) {
    var ch = health && health[id] && health[id].checks, out = [];
    if (ch) Object.keys(ch).forEach(function (k) { var c = ch[k]; if (c && c.level !== 'ok' && c.detail) out.push(String(c.detail)); });
    return out.join(' · ');
  }
  function loadHealth() {
    try { var c = JSON.parse(sessionStorage.getItem('lt-nav-health') || 'null'); if (c && Date.now() - c.t < 45000) { health = c.m; hAt = c.t; paint(); return; } } catch (e) {}
    if (!window.fetch) return;
    hAt = Date.now();
    fetch('/admin/api/health', {cache: 'no-store', signal: window.AbortSignal && AbortSignal.timeout ? AbortSignal.timeout(5000) : undefined})
      .then(function (r) { return r.json(); })
      .then(function (d) {
        health = d && d.modules || null; paint();
        try { sessionStorage.setItem('lt-nav-health', JSON.stringify({t: Date.now(), m: health})); } catch (e) {}
      }).catch(function () {});
  }

  // Aviso al día con la página: cada vez que el módulo rearma su contenido (sus propias lecturas) y al volver a la pestaña, el estado se
  // vuelve a pedir si tiene más de 15 s. Antes solo se pedía cada 60 s y Safari detiene ese temporizador en segundo plano: el aviso seguía
  // aunque la página ya mostraba el problema resuelto.
  // EN: Notice in step with the page: whenever the module rebuilds its content (its own readings) and when the tab comes back, the status
  // is fetched again if it is older than 15 s. It used to be fetched only every 60 s and Safari stops that timer in the background: the
  // notice stayed although the page already showed the problem solved.
  var hAt = 0, hWait = null;
  function healthSoon() {
    if (!st || Date.now() - hAt < 15000) return;
    try { sessionStorage.removeItem('lt-nav-health'); } catch (e) {}
    loadHealth();
  }
  function own(ns) { for (var j = 0; j < ns.length; j++) if (ns[j].id !== 'gwarn') return false; return true; }
  function healthSync() {
    if (window.MutationObserver) new MutationObserver(function (recs) {
      for (var i = 0; i < recs.length; i++) {
        var r = recs[i];
        if (r.target.closest && r.target.closest('#gwarn, .gbar')) continue;      // own changes / cambios propios
        if (!r.addedNodes.length && !r.removedNodes.length) continue;
        if (own(r.addedNodes) && own(r.removedNodes)) continue;                      // solo el aviso entra o sale / only the notice comes or goes
        // Una sola espera pendiente: si se reiniciara, una página que redibuja cada segundo nunca llegaría a pedirlo.
        // EN: One pending wait only: if it were restarted, a page that redraws every second would never fetch it.
        if (!hWait) hWait = setTimeout(function () { hWait = null; healthSoon(); }, 1000);
        return;
      }
    }).observe(document.body, { childList: true, subtree: true });
    document.addEventListener('visibilitychange', function () { if (!document.hidden) healthSoon(); });
    window.addEventListener('pageshow', function (e) { if (e.persisted) healthSoon(); });
  }

  // ── Estructura (se crea una vez) / structure (created once) ──
  function ensure() {
    if (st && st.bar && document.body.contains(st.bar)) return;
    var bar = el('header', 'gbar'), nav = el('nav', 'gbar-in');
    var lg = el('a', 'gbar-logo'), im = el('img'); im.src = '/logo.png'; im.alt = ''; im.width = 30; im.height = 30; lg.appendChild(im); lg.href = '/'; nav.appendChild(lg);
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
    ['(min-width:768px)', '(min-width:961px)'].forEach(function (q) { try { window.matchMedia(q).addEventListener('change', function () { apply(); }); } catch (e) {} });
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
    // ES: Salir en toda sección (menos el kiosco, que no tiene barra): usa el botón de salir propio del módulo, aunque su barra esté oculta en el móvil.
    // EN: Sign out in every section (except the kiosk, which has no bar): it uses the module's own sign-out button, even when its bar is hidden on phones.
    var lo = tabItem('out', tr.out, '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>', null, false);
    lo.setAttribute('data-gtab', 'out');
    lo.addEventListener('click', function () { toggle(false); var x = document.querySelector('.btn-logout'); if (x) x.click(); });
  }

  // ── Menú clásico (lateral; tira en el Resumen) / classic menu (side; strip in the Overview) ──
  function classic() {
    var o = st.opts, me = st.me, es = st.lang === 'es', tr = T[st.lang];
    var box = document.getElementById('nav-items'), strip = false;
    if (!box && o.self === 'overview') {
      box = document.getElementById('navstrip');
      if (!box) { box = el('nav', 'navstrip nokiosk'); box.id = 'navstrip'; var at = document.getElementById('attn'), w = at ? at.parentNode : document.getElementById('app'); if (w) w.insertBefore(box, at || w.children[1] || null); }
      strip = true;
    }
    if (!box) return;
    var sec = box.closest('.sb-sec'); (sec || box).hidden = false; box.hidden = false;
    box.textContent = '';
    var first = true;
    G.forEach(function (g) {
      var ids = g.items.filter(function (id) { return visible(id, me); });
      if (!ids.length) return;
      var host2 = box;
      if (strip) { host2 = el('span', 'nav-grp'); box.appendChild(host2); }   // el salto de línea cae entre grupos / line breaks fall between groups
      else if (g.es) box.appendChild(el('div', 'nav-group-lbl', es ? g.es : g.en));
      first = false;
      ids.forEach(function (id) {
        var it = I[id], self = id === o.self;
        var a = el('a', (strip ? 'nav-chip' : 'nav-item') + (self ? ' active' : '')), name = it.label || (es ? it.es : it.en);
        a.href = it.href; a.setAttribute('data-nav-id', id);
        if (self) a.setAttribute('aria-current', 'page');
        a.appendChild(icon(it.svg, strip ? 14 : null));
        // ES: En la tira el nombre va corto («UPS», «WOL») para que quepa en una línea; el completo queda en el título.
        // EN: In the strip the name is short ("UPS", "WOL") so it fits on one line; the full one stays in the title.
        var shown = strip ? name.replace(/ (Monitor|Console|Panel)$/, '') : name;
        if (shown !== name) { a.title = name; a.setAttribute('aria-label', name); }
        a.appendChild(document.createTextNode(shown));
        if (it.label && id !== 'admin') a.appendChild(el('span', 'nav-dot'));
        host2.appendChild(a);
      });
    });
  }
  function unclassic() {
    var box = document.getElementById('nav-items'), strip = document.getElementById('navstrip');
    if (box) { box.textContent = ''; var sec = box.closest('.sb-sec'); (sec || box).hidden = true; }
    if (strip) strip.remove();
  }

  // ── Asistente: elegir el tipo de menú / wizard: choose the menu type ──
  var PREV = {
    bar:  '<rect x="1" y="1" width="118" height="78" rx="6" fill="none" stroke="currentColor" stroke-width="2"/><rect x="1" y="1" width="118" height="14" rx="6" fill="currentColor" opacity=".18"/><rect x="8" y="5" width="8" height="6" rx="2" fill="currentColor"/><rect x="22" y="4.5" width="34" height="7" rx="3.5" fill="currentColor" opacity=".55"/><rect x="8" y="24" width="48" height="20" rx="4" fill="currentColor" opacity=".25"/><rect x="62" y="24" width="48" height="20" rx="4" fill="currentColor" opacity=".25"/><rect x="8" y="50" width="102" height="22" rx="4" fill="currentColor" opacity=".15"/>',
    side: '<rect x="1" y="1" width="118" height="78" rx="6" fill="none" stroke="currentColor" stroke-width="2"/><rect x="1" y="1" width="30" height="78" rx="6" fill="currentColor" opacity=".18"/><rect x="6" y="10" width="20" height="5" rx="2.5" fill="currentColor" opacity=".6"/><rect x="6" y="20" width="20" height="5" rx="2.5" fill="currentColor" opacity=".35"/><rect x="6" y="30" width="20" height="5" rx="2.5" fill="currentColor" opacity=".35"/><rect x="6" y="40" width="20" height="5" rx="2.5" fill="currentColor" opacity=".35"/><rect x="38" y="10" width="34" height="22" rx="4" fill="currentColor" opacity=".25"/><rect x="78" y="10" width="34" height="22" rx="4" fill="currentColor" opacity=".25"/><rect x="38" y="40" width="74" height="30" rx="4" fill="currentColor" opacity=".15"/>'
  };
  function wizard(firstRun) {
    if (document.getElementById('gwiz')) return;
    var tr = T[st.lang], cur = mode(), prev = document.activeElement;
    var ov = el('div', 'gwiz'); ov.id = 'gwiz';
    var dlg = el('div', 'gwiz-box'); dlg.setAttribute('role', 'dialog'); dlg.setAttribute('aria-modal', 'true'); dlg.setAttribute('aria-labelledby', 'gwiz-h');
    var h = el('h2', null, tr.wizTitle); h.id = 'gwiz-h';
    dlg.appendChild(h); dlg.appendChild(el('p', 'gwiz-p', tr.wizText));
    var opts = el('div', 'gwiz-opts'), sel = cur;
    function close() { setMode(sel); ov.remove(); document.removeEventListener('keydown', key, true); apply(); try { if (prev && prev.focus) prev.focus(); } catch (e) {} }
    function key(e) {
      if (e.key === 'Escape') { e.preventDefault(); close(); return; }
      if (e.key === 'Tab') {                                                      // el foco no sale del diálogo / keep focus inside
        var f = dlg.querySelectorAll('button'), a = f[0], z = f[f.length - 1];
        if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus(); }
        else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); }
      }
    }
    [['bar', tr.optBar, tr.optBarD], ['side', tr.optSide, tr.optSideD]].forEach(function (o) {
      var b = el('button', 'gwiz-opt' + (o[0] === sel ? ' on' : '')); b.type = 'button'; b.setAttribute('aria-pressed', o[0] === sel ? 'true' : 'false');
      var sv = icon(PREV[o[0]], null); sv.setAttribute('viewBox', '0 0 120 80'); sv.setAttribute('class', 'gwiz-prev'); sv.removeAttribute('aria-hidden');
      b.appendChild(sv); b.appendChild(el('b', null, o[1])); b.appendChild(el('span', null, o[2]));
      if (o[0] === cur && !firstRun) b.appendChild(el('i', 'gwiz-cur', tr.current));
      b.addEventListener('click', function () {
        sel = o[0]; opts.querySelectorAll('.gwiz-opt').forEach(function (x) { var on = x === b; x.className = 'gwiz-opt' + (on ? ' on' : ''); x.setAttribute('aria-pressed', on ? 'true' : 'false'); });
      });
      opts.appendChild(b);
    });
    dlg.appendChild(opts);
    var ok = el('button', 'gwiz-ok', tr.ok); ok.type = 'button'; ok.addEventListener('click', close);
    dlg.appendChild(ok); ov.appendChild(dlg); document.body.appendChild(ov);
    document.addEventListener('keydown', key, true);
    opts.querySelector('.on').focus();
  }

  // Botón «Tipo de menú» junto a las demás opciones (idioma, tema) / the menu-type button next to the other options (language, theme)
  function placeBtn() {
    var tr = T[st.lang], b = document.getElementById('gmt');
    var ref = document.querySelector('.lang-btns') || document.getElementById('bl');
    if (!ref) return;
    if (!b) {
      b = el('button', 'gmt' + (ref.id === 'bl' ? ' btn nokiosk' : '')); b.id = 'gmt'; b.type = 'button';
      b.appendChild(icon('<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/>', 14));
      b.appendChild(el('span', 'gmt-t'));
      b.addEventListener('click', function () { wizard(false); });
    }
    b.querySelector('.gmt-t').textContent = tr.menuType; b.title = tr.menuType; b.setAttribute('aria-label', tr.menuType);
    if (b.nextSibling !== ref || b.parentNode !== ref.parentNode) ref.parentNode.insertBefore(b, ref);
  }
  // Barra superior: el encabezado del panel lateral sobra; si el panel solo tenía el menú, se oculta y el usuario pasa a la barra.
  // Además, idioma, tema, reloj y usuario de la barra del módulo suben a esta barra y la del módulo se oculta si no le queda nada propio.
  // EN: Top bar: the side panel header is redundant; if the panel only held the menu it is hidden and the user badge moves to the bar.
  //     Also the module bar's language, theme, clock and user move up into this bar, and the module bar is hidden if nothing of its own is left.
  var STD = '#gmt, .lang-btns, .theme-btns, #clock, #hclock, div[style*="width:1px"], .topbar-user, .btn-logout';
  function barRight() { var r = st.bar.querySelector('.gbar-r'); if (!r) { r = el('div', 'gbar-r'); st.bar.appendChild(r); } return r; }
  // ¿Queda algo propio del módulo en su barra (botones, campos, enlaces)? / Is anything of the module's own left in its bar (buttons, fields, links)?
  function ownControls(tb) {
    return Array.prototype.some.call(tb.querySelectorAll('button, input, select, a'), function (n) { return !n.classList.contains('nav-toggle'); });
  }
  function sideLayout(bar) {
    var sb = document.querySelector('.sidebar'), tb = document.querySelector('.topbar');
    var wide = window.matchMedia('(min-width:768px)').matches, full = window.matchMedia('(min-width:961px)').matches;
    // 1) devolver lo movido / put back what was moved
    (st.moved || []).reverse().forEach(function (m) { try { m.parent.insertBefore(m.node, m.next && m.next.parentNode === m.parent ? m.next : null); } catch (e) {} });
    st.moved = [];
    var oldR = st.bar.querySelector('.gbar-r'); if (oldR) oldR.remove();
    var oldA = st.bar.querySelector('.gbar-act'); if (oldA) oldA.remove();
    document.body.classList.remove('gside-none', 'gtb-none', 'gtb-merged');
    if (!bar) return;
    // 2) panel lateral / side panel
    var none = false, foot = null;
    if (sb) {
      var own = Array.prototype.some.call(sb.querySelectorAll('.sb-sec'), function (x) {       // listas propias visibles / visible own lists
        return !x.querySelector('#nav-items') && x.id !== 'sb-ip' && !x.hidden && x.style.display !== 'none';   // #sb-ip repite la tarjeta «IP pública» / repeats the Public IP card
      });
      if (!sb.gobs && window.MutationObserver) {                                  // las listas aparecen o se ocultan después / lists show or hide later
        sb.gobs = new MutationObserver(function () { if (st) sideLayout(mode() === 'bar'); });
        sb.gobs.observe(sb, {attributes: true, attributeFilter: ['hidden', 'style'], subtree: true});
      }
      none = wide && !own; foot = sb.querySelector('.sb-footer');
      if (none && foot) { st.moved.push({node: foot, parent: sb, next: foot.nextSibling}); barRight().appendChild(foot); }
    }
    document.body.classList.toggle('gside-none', none);
    // 3) barra del módulo / module bar
    if (tb && (full || (wide && (none || !sb)))) {
      var nodes = Array.prototype.slice.call(tb.querySelectorAll(STD)).filter(function (n, i, a) { return !a.some(function (o) { return o !== n && o.contains(n); }); });
      // Los botones de acción del módulo (p. ej. «Escanear red», «Ajustes») suben junto al selector de módulo, así la barra del módulo desaparece y todas las pantallas se ven iguales.
      // EN: The module's action buttons (e.g. "Scan network", "Settings") go up next to the module selector, so the module bar disappears and every screen looks the same.
      var acts = tb.querySelector('.tb-actions');
      if (acts) {
        var ga = el('div', 'gbar-act'); st.bar.insertBefore(ga, st.bar.querySelector('.gbar-r') || null);
        st.moved.push({node: acts, parent: acts.parentNode, next: acts.nextSibling}); ga.appendChild(acts);
      }
      if (nodes.length) {
        var r = barRight();
        nodes.forEach(function (n) { st.moved.push({node: n, parent: n.parentNode, next: n.nextSibling}); r.appendChild(n); });
        document.body.classList.add('gtb-merged');
        document.body.classList.toggle('gtb-none', !ownControls(tb));
      }
      // Los botones propios pueden crearse después (p. ej. «Ajustes» al llegar los datos): se vuelve a evaluar al cambiar la barra.
      // EN: Own buttons may be created later (e.g. "Settings" once the data arrives): re-evaluate when the bar changes.
      if (!tb.gobs && window.MutationObserver) {
        tb.gobs = new MutationObserver(function () {
          if (st && document.body.classList.contains('gtb-merged') && ownControls(tb) === document.body.classList.contains('gtb-none')) sideLayout(mode() === 'bar');
        });
        tb.gobs.observe(tb, {childList: true, subtree: true});
      }
    }
    var f2 = st.bar.querySelector('.gbar-r .sb-footer'); if (f2) f2.parentNode.appendChild(f2);   // el usuario al final / user badge last
  }

  // aplica el tipo de menú elegido / apply the chosen menu type
  function apply() {
    var m = mode();
    placeBtn(); sideLayout(m === 'bar');
    document.body.classList.toggle('has-gbar', m === 'bar');
    document.documentElement.setAttribute('data-navmode', m);
    if (m === 'bar') { fill(); } else { toggle(false); classic(); }
    if (m === 'bar') unclassic();
    paint(); loadHealth();
    if (!timer) { timer = setInterval(function () { try { sessionStorage.removeItem('lt-nav-health'); } catch (e) {} loadHealth(); }, 60000); healthSync(); }
  }

  // Mantener la vista cuando el contenido cambia: los módulos rearman su contenido en cada lectura y la página saltaba.
  // El «scroll anchoring» del navegador no basta: no existe en Safari antiguo y, donde existe, se pierde cuando el elemento
  // de referencia se elimina y se crea de nuevo, que es justo lo que hace un refresco. Aquí se anota qué elemento está bajo
  // la barra superior y a qué altura; tras cada cambio del contenido se busca ese mismo elemento (o el que ocupa su lugar:
  // mismo id o misma posición en el árbol) y se corrige el desplazamiento. Si el navegador tiene anchoring propio y el
  // elemento sigue en la página, se revisa un cuadro después: si el navegador ya lo dejó en su lugar no se hace nada
  // (no se corrige dos veces); si no (Safari lo omite en algunos diseños), se corrige aquí.
  // EN: Keep the view when the content changes: modules rebuild their content on every reading and the page jumped.
  // Browser scroll anchoring is not enough: older Safari lacks it and, where it exists, it is lost when the reference
  // element is removed and created again, which is exactly what a refresh does. Here we note which element sits under the
  // top bar and how high; after every content change we find that element (or the one that took its place: same id or
  // same position in the tree) and correct the scroll. If the browser has its own anchoring and the element is still on
  // the page, it is checked one frame later: if the browser already kept it in place nothing is done (no double
  // correction); otherwise (Safari skips it in some layouts) it is corrected here.
  function anchorTake(root) {
    if (window.scrollY < 1) return null;                                       // at the top there is nothing to keep
    var tb = document.querySelector('.topbar'), y = Math.max(0, tb ? tb.getBoundingClientRect().bottom : 0) + 8;
    var el = document.elementFromPoint(Math.round(window.innerWidth / 2), Math.round(Math.min(y, window.innerHeight - 1)));
    if (!el || el === root || !root.contains(el)) return null;
    var path = [], n = el;
    while (n && n !== root && !n.id) { path.unshift(Array.prototype.indexOf.call(n.parentNode.children, n)); n = n.parentNode; }
    return { el: el, id: n && n !== root ? n.id : null, path: path, top: el.getBoundingClientRect().top };
  }
  function anchorFind(root, a) {
    if (a.el.isConnected) return a.el;
    var n = a.id ? document.getElementById(a.id) : root;
    for (var i = 0; n && i < a.path.length; i++) n = n.children[a.path[i]];
    return n && root.contains(n) ? n : null;
  }
  function keepView() {
    if (!window.MutationObserver) return;
    var native = !!(window.CSS && CSS.supports && CSS.supports('overflow-anchor', 'auto'));
    var root = document.body, a = null, busy = false, later = false;
    function take() { a = anchorTake(root); }
    function fix() {
      var n = a && anchorFind(root, a);
      // Oculto (otra vista, sección cerrada): no hay dónde mantenerse. / EN: Hidden (another view, closed section): nothing to keep.
      if (n && n.getClientRects().length) {
        var d = n.getBoundingClientRect().top - a.top;
        if (Math.abs(d) >= 1) { busy = true; window.scrollBy(0, d); busy = false; }
      }
      take();
    }
    var mo = new MutationObserver(function (recs) {
      // Solo cambios de elementos (no el texto del reloj ni de un contador). / EN: Element changes only (not clock or counter text).
      var el = false;
      for (var i = 0; i < recs.length && !el; i++) {
        var r = recs[i], k;
        for (k = 0; k < r.addedNodes.length && !el; k++) el = r.addedNodes[k].nodeType === 1;
        for (k = 0; k < r.removedNodes.length && !el; k++) el = r.removedNodes[k].nodeType === 1;
      }
      if (!el || !a || busy || later) { if (el && !a) take(); return; }
      if (native && a.el.isConnected) {                                        // let the browser act first, then check
        later = true;
        requestAnimationFrame(function () { later = false; fix(); });
        return;
      }
      fix();
    });
    mo.observe(root, { childList: true, subtree: true });
    window.addEventListener('scroll', function () { if (!busy) take(); }, { passive: true });
    window.addEventListener('resize', take, { passive: true });
    take();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', keepView); else keepView();

  window.labNav = {
    // opts: {self, lang, me, fetchMe}
    render: function (o) {
      o = o || {};
      ensure();
      st.opts = o; st.lang = o.lang === 'es' ? 'es' : 'en'; st.me = o.me || st.me || null;
      document.documentElement.setAttribute('data-gbar', '1');
      apply();
      if (!getMode() && st.me && (st.me.username || st.me.permissions) && !document.body.classList.contains('kiosk')) wizard(true);
      if (!o.me && o.fetchMe && !st.me && !st.fetching) {
        st.fetching = true;
        fetch('api/me').then(function (r) { return r.json(); }).then(function (m) { st.fetching = false; if (m && m.permissions) { st.me = m; apply(); if (!getMode() && !document.body.classList.contains('kiosk')) wizard(true); } }).catch(function () { st.fetching = false; });
      }
    }
  };
})();
