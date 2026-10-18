/* Tarjeta con los datos de Net Monitor al pasar el ratón por una IP (o nombre de equipo).
   Uso: <span data-nethost="192.168.0.10">…</span>; con data-nethost-click el clic (o toque, en pantallas táctiles) abre/lleva al detalle.
   Todo se construye con textContent (nada de innerHTML): los datos de la red nunca se interpretan como HTML.
   EN: Card with Net Monitor data when hovering an IP (or host name).
   Usage: <span data-nethost="192.168.0.10">…</span>; with data-nethost-click a click (or tap on touch screens) opens / goes to the detail.
   Everything is built with textContent (no innerHTML): network data is never parsed as HTML. */
(function () {
  'use strict';
  var TTL = 20000, SHOW_MS = 280, HIDE_MS = 220;
  var TX = {
    en: { online: 'Online', offline: 'Offline', type: 'Type', os: 'OS', vendor: 'Vendor', mac: 'MAC', latency: 'Latency', ports: 'Open ports',
          seen: 'Last seen', loading: 'Loading…', full: 'Full details in Net Monitor →', none: 'Not in Net Monitor yet', open: 'Open Net Monitor →',
          noaccess: 'No access to Net Monitor', err: 'Could not load Net Monitor data', now: 'now', ago: ' ago', unknown: 'Unknown', manual: 'manual' },
    es: { online: 'En línea', offline: 'Sin conexión', type: 'Tipo', os: 'SO', vendor: 'Fabricante', mac: 'MAC', latency: 'Latencia', ports: 'Puertos abiertos',
          seen: 'Visto', loading: 'Cargando…', full: 'Ver detalle completo en Net Monitor →', none: 'Aún no está en Net Monitor', open: 'Abrir Net Monitor →',
          noaccess: 'Sin acceso a Net Monitor', err: 'No se pudieron cargar los datos de Net Monitor', now: 'ahora', ago: ' atrás', unknown: 'Desconocido', manual: 'manual' }
  };
  var TYPES = {
    computer: ['💻', 'Computer', 'Computador'], phone: ['📱', 'Phone', 'Teléfono'], router: ['🌐', 'Router', 'Router'], switch: ['🔀', 'Switch', 'Switch'],
    ap: ['📡', 'Wi-Fi AP', 'AP Wi-Fi'], storage: ['🗄️', 'Storage', 'Almacenamiento'], tv: ['📺', 'TV', 'TV'], camera: ['📷', 'Camera', 'Cámara'],
    appliance: ['🏠', 'Appliance', 'Electrodoméstico'], printer: ['🖨️', 'Printer', 'Impresora'], tablet: ['📲', 'Tablet', 'Tablet'],
    console: ['🎮', 'Game Console', 'Consola de juegos'], server: ['🖥️', 'Server', 'Servidor'], voip: ['☎️', 'IP Phone', 'Teléfono IP'],
    ups: ['🔋', 'UPS', 'UPS'], speaker: ['🔊', 'Smart Speaker', 'Altavoz inteligente'], other: ['❔', 'Other', 'Otro']
  };
  function lang() { try { return localStorage.getItem('pi-lang') === 'es' ? 'es' : 'en'; } catch (e) { return 'en'; } }
  function tx(k) { return TX[lang()][k]; }

  // ── Datos / data (una sola petición compartida, 20 s de caché) ──
  var cache = null, inflight = null;
  function load() {
    if (cache && Date.now() - cache.t < TTL) return Promise.resolve(cache);
    if (inflight) return inflight;
    inflight = fetch('/net/api/hosts', { credentials: 'same-origin', cache: 'no-store' }).then(function (r) {
      if (!r.ok) return { t: Date.now(), status: r.status, hosts: [] };
      return r.json().then(function (j) { return { t: Date.now(), status: 200, hosts: (j && j.hosts) || [] }; });
    }).catch(function () { return { t: Date.now(), status: 0, hosts: [] }; }).then(function (c) { cache = c; inflight = null; return c; });
    return inflight;
  }
  function find(list, q) {
    q = String(q || '').trim().toLowerCase().replace(/:\d+$/, '');
    if (!q) return null;
    var i, h;
    for (i = 0; i < list.length; i++) if (list[i].ip === q) return list[i];
    var isIp = /^\d{1,3}(\.\d{1,3}){3}$/.test(q), short = q.split('.')[0];
    if (isIp) return null;
    for (i = 0; i < list.length; i++) {
      h = list[i];
      var names = [h.hostname, h.alias];
      for (var j = 0; j < 2; j++) {
        var n = names[j] ? String(names[j]).toLowerCase() : '';
        if (n && (n === q || n.split('.')[0] === short)) return h;
      }
    }
    return null;
  }
  function detailUrl(ip) { return '/net/' + (ip ? '?ip=' + encodeURIComponent(ip) : ''); }

  // ── Tarjeta / card ──
  var card = null, cur = null, showT = null, hideT = null;
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function rel(ts) {
    if (!ts) return '—';
    var s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
    if (s < 45) return tx('now');
    var m = Math.floor(s / 60); if (m < 60) return m + ' min' + tx('ago');
    var h = Math.floor(m / 60); if (h < 24) return h + ' h' + tx('ago');
    var d = Math.floor(h / 24); return d + (lang() === 'es' ? ' d' : ' d') + tx('ago');
  }
  function row(k, v, mono) {
    var r = el('div', 'pi-ipc-row'); r.appendChild(el('span', 'pi-ipc-k', k)); r.appendChild(el('span', 'pi-ipc-v' + (mono ? ' mono' : ''), v)); return r;
  }
  function ensureCard() {
    if (card) return card;
    card = el('div', 'pi-ipcard'); card.setAttribute('role', 'dialog');
    card.addEventListener('mouseenter', function () { clearTimeout(hideT); });
    card.addEventListener('mouseleave', schedHide);
    document.body.appendChild(card);
    return card;
  }
  function place(target) {
    var r = target.getBoundingClientRect(), c = card, vw = window.innerWidth, vh = window.innerHeight;
    c.style.left = '0px'; c.style.top = '0px';
    var w = c.offsetWidth, h = c.offsetHeight;
    var x = Math.min(Math.max(8, r.left), Math.max(8, vw - w - 8));
    var y = r.bottom + 6; if (y + h > vh - 8) y = Math.max(8, r.top - h - 6);
    c.style.left = Math.round(x) + 'px'; c.style.top = Math.round(y) + 'px';
  }
  function fill(q, c) {
    var h = find(c.hosts, q), box = card;
    box.textContent = '';
    if (c.status === 401 || c.status === 403) { box.appendChild(el('div', 'pi-ipc-msg', tx('noaccess'))); return; }
    if (c.status !== 200) { box.appendChild(el('div', 'pi-ipc-msg', tx('err'))); return; }
    if (!h) {
      box.appendChild(el('div', 'pi-ipc-title', q)); box.appendChild(el('div', 'pi-ipc-msg', tx('none')));
      var a0 = el('a', 'pi-ipc-go', tx('open')); a0.href = detailUrl(''); box.appendChild(a0); return;
    }
    var head = el('div', 'pi-ipc-head');
    head.appendChild(el('span', 'pi-ipc-dot ' + (h.online ? 'on' : 'off')));
    var nm = el('div', 'pi-ipc-name'); nm.appendChild(el('b', null, h.alias || h.hostname || h.ip));
    nm.appendChild(el('span', 'pi-ipc-ip', h.ip)); head.appendChild(nm);
    head.appendChild(el('span', 'pi-ipc-st ' + (h.online ? 'on' : 'off'), h.online ? tx('online') : tx('offline')));
    box.appendChild(head);
    var ty = TYPES[h.device_type] || TYPES.other, li = lang() === 'es' ? 2 : 1;
    box.appendChild(row(tx('type'), ty[0] + ' ' + ty[li] + (h.type_manual ? ' (' + tx('manual') + ')' : '')));
    box.appendChild(row(tx('os'), !h.os || h.os === 'Desconocido' ? tx('unknown') : h.os));
    if (h.vendor) box.appendChild(row(tx('vendor'), h.vendor));
    if (h.mac) box.appendChild(row(tx('mac'), h.mac, true));
    if (h.online && h.latency) box.appendChild(row(tx('latency'), h.latency + ' ms', true));
    box.appendChild(row(tx('seen'), rel(h.last_seen)));
    var ps = h.ports || [];
    if (ps.length) {
      var pr = el('div', 'pi-ipc-ports'); pr.appendChild(el('span', 'pi-ipc-k', tx('ports')));
      var wrap = el('span', 'pi-ipc-chips');
      ps.slice(0, 10).forEach(function (p) { var ch = el('span', 'pi-ipc-chip', String(p.port)); if (p.service) ch.title = String(p.service); wrap.appendChild(ch); });
      if (ps.length > 10) wrap.appendChild(el('span', 'pi-ipc-chip', '+' + (ps.length - 10)));
      pr.appendChild(wrap); box.appendChild(pr);
    }
    var a = el('a', 'pi-ipc-go', tx('full')); a.href = detailUrl(h.ip); box.appendChild(a);
  }
  function show(target) {
    var q = target.getAttribute('data-nethost'); if (!q) return;
    cur = target; ensureCard(); card.textContent = ''; card.appendChild(el('div', 'pi-ipc-msg', tx('loading')));
    card.className = 'pi-ipcard show'; place(target);
    load().then(function (c) { if (cur !== target) return; fill(q, c); place(target); });
  }
  function hide() { clearTimeout(showT); clearTimeout(hideT); cur = null; if (card) card.className = 'pi-ipcard'; }
  function schedHide() { clearTimeout(showT); clearTimeout(hideT); hideT = setTimeout(hide, HIDE_MS); }
  function tgt(n) { return n && n.closest ? n.closest('[data-nethost]') : null; }
  var touch = window.matchMedia ? matchMedia('(hover: none)') : { matches: false };

  document.addEventListener('mouseover', function (e) {
    if (touch.matches) return;
    var t = tgt(e.target); if (!t) return;
    clearTimeout(hideT);
    if (t === cur) return;
    clearTimeout(showT); showT = setTimeout(function () { show(t); }, SHOW_MS);
  });
  document.addEventListener('mouseout', function (e) {
    if (touch.matches) return;                                   // los eventos de ratón sintetizados por el toque no deben cerrarla / mouse events synthesised by a tap must not close it
    var t = tgt(e.target); if (!t) return;
    if (e.relatedTarget && (t.contains(e.relatedTarget) || (card && card.contains(e.relatedTarget)))) return;
    schedHide();
  });
  document.addEventListener('click', function (e) {
    var t = tgt(e.target);
    if (card && card.contains(e.target)) return;                 // el enlace de la tarjeta navega solo / the card link navigates by itself
    // Táctil: cualquier IP marcada abre la tarjeta al tocarla; con ratón solo las marcadas con data-nethost-click (el resto muestran la tarjeta al pasar el ratón).
    // EN: Touch: any marked IP opens the card on tap; with a mouse only those marked data-nethost-click (the rest show the card on hover).
    if (!t || (!touch.matches && !t.hasAttribute('data-nethost-click'))) { if (touch.matches) hide(); return; }
    e.preventDefault(); e.stopPropagation();
    if (touch.matches) { if (cur === t) hide(); else show(t); return; }   // táctil: el toque abre la tarjeta / touch: tap opens the card
    var q = t.getAttribute('data-nethost');
    load().then(function (c) { var h = find(c.hosts, q); location.href = detailUrl(h ? h.ip : (/^\d{1,3}(\.\d{1,3}){3}$/.test(q) ? q : '')); });
  }, true);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hide(); });
  window.addEventListener('scroll', function () { if (cur && !touch.matches) hide(); }, true);
})();
