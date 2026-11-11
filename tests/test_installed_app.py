"""LabTower instalado en la pantalla de inicio: etiquetas de app web en todas las páginas, barra de estado según el tema elegido, pantalla de
arranque clara u oscura, deslizar para recargar y la página «Sin conexión» del service worker (solo HTTPS, sin guardar datos).
EN: LabTower installed on the home screen: web-app tags on every page, status bar per the chosen theme, light or dark launch screen, pull to
refresh and the service worker's "No connection" page (HTTPS only, storing no data)."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = (ROOT / "assets/theme/theme.js").read_text(encoding="utf-8")
SW = (ROOT / "home/sw.js").read_text(encoding="utf-8")
TAGS = ('<link rel="manifest" href="/manifest.webmanifest">', '<link rel="apple-touch-icon"', '<meta name="apple-mobile-web-app-capable" content="yes">',
        '<meta name="apple-mobile-web-app-title" content="LabTower">', '<meta name="apple-mobile-web-app-status-bar-style" content="default">',
        '<meta name="theme-color" content="#f0f2f5" media="(prefers-color-scheme: light)">', '<meta name="theme-color" content="#0f1420" media="(prefers-color-scheme: dark)">')


class Pages(unittest.TestCase):
    def test_every_page_has_the_web_app_tags(self):
        pages = [ROOT / "home/index.html", *sorted(ROOT.glob("*/static/index.html"))]
        self.assertGreaterEqual(len(pages), 12)
        for p in pages:
            src = p.read_text(encoding="utf-8")
            for t in TAGS:
                self.assertIn(t, src, f"{p}: {t}")


class Shell(unittest.TestCase):
    def test_status_bar_follows_the_chosen_theme(self):
        self.assertIn("document.addEventListener('pi-theme',barColor);", THEME)
        self.assertIn("m.setAttribute('content',t==='system'?(dk?DARK:LIGHT):(d.getAttribute('data-theme')==='light'?LIGHT:DARK));", THEME)

    def test_light_and_dark_launch_screens(self):
        for k in ("l.rel='apple-touch-startup-image'", "(prefers-color-scheme: '+x[1]+')", "[[LIGHT,'light'],[DARK,'dark']]", "if(!ios||installed||"):
            self.assertIn(k, THEME, k)

    def test_pull_to_refresh_only_installed_and_from_the_top(self):
        for k in ("if(!installed||!document.body)return;", "window.scrollY<=2", "t.clientY>30", "dy>=GO", "location.reload()",
                  "document.addEventListener('touchcancel',end,{passive:true});"):
            self.assertIn(k, THEME, k)
        self.assertIn(".lt-ptr{position:fixed;", (ROOT / "assets/theme/theme.css").read_text(encoding="utf-8"))

    def test_pull_to_refresh_never_stays_stuck(self):
        # Instalada en iPhone, WebKit a veces ignora reload() en el mismo toque y el ícono quedaba girando.
        # EN: Installed on iPhone, WebKit sometimes ignores reload() in the same touch and the icon kept spinning.
        for k in ("if(y0!==null&&dy>=GO&&!busy)setTimeout(reload,0);",                       # outside the touch
                  "if(window.scrollY<0&&Date.now()-t0<800){requestAnimationFrame(go);return}",   # after the bounce
                  "setTimeout(function(){if(location.hash)location.reload();else location.replace(location.href)},4000)",   # second try, also with #switches
                  "setTimeout(stop,10000)",                                                      # never spins forever
                  "window.addEventListener('pageshow',function(e){if(e.persisted)stop()});",
                  "y0=(!busy&&window.scrollY<=2"):
            self.assertIn(k, THEME, k)

    def test_service_worker_only_over_https(self):
        self.assertIn("if('serviceWorker' in navigator&&location.protocol==='https:')", THEME)
        self.assertIn("navigator.serviceWorker.register('/sw.js',{scope:'/'})", THEME)


class OfflinePage(unittest.TestCase):
    def test_only_pages_fall_back_and_nothing_else_is_stored(self):
        self.assertIn('const FILES = ["/offline.html", "/offline.css", "/offline.js", "/icon-192.png"];', SW)
        self.assertIn('e.respondWith(fetch(req).catch(() => caches.match("/offline.html")));', SW)
        self.assertIn('if (req.method !== "GET") return;', SW)
        self.assertIn("if (url.origin !== self.location.origin) return;", SW)
        self.assertNotRegex(SW, r"cache\.put|\.put\(")                                  # never stores responses
        for f in ("offline.html", "offline.css", "offline.js", "icon-192.png"):
            self.assertTrue((ROOT / "home" / f).is_file(), f)

    def test_offline_page_respects_the_csp(self):
        html = (ROOT / "home/offline.html").read_text(encoding="utf-8")
        self.assertNotRegex(html, r"<script>|<style|\son\w+=|style=")
        self.assertIn('<script src="/offline.js" defer></script>', html)
        js = (ROOT / "home/offline.js").read_text(encoding="utf-8")
        self.assertIn('fetch("/manifest.webmanifest", { cache: "no-store" })', js)
        self.assertIn("setInterval(retry, 10000);", js)

    def test_nginx_serves_it_without_dropping_security_headers(self):
        conf = (ROOT / "etc/nginx/snippets/labtower-site.conf").read_text(encoding="utf-8")
        m = re.search(r"location = /sw\.js \{([^}]*)\}", conf)
        self.assertTrue(m)
        self.assertIn("expires epoch;", m.group(1))
        self.assertNotIn("add_header", m.group(1))


class Syntax(unittest.TestCase):
    def test_scripts_parse(self):
        if not shutil.which("node"): self.skipTest("node not installed")
        for f in ("assets/theme/theme.js", "home/sw.js", "home/offline.js"):
            r = subprocess.run(["node", "--check", str(ROOT / f)], capture_output=True, text=True, timeout=30, check=False)
            self.assertEqual(r.returncode, 0, f + r.stderr)


if __name__ == "__main__":
    unittest.main()
