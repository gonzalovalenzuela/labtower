#!/usr/bin/env python3
"""Regenera los PNG de home/ desde los SVG de esta carpeta (requiere playwright + chromium).
EN: Regenerates the home/ PNGs from the SVGs in this folder (needs playwright + chromium).

    python3 assets/icons/make-icons.py

icon.svg         → icon-192.png, icon-512.png (esquinas redondeadas, transparente / rounded corners, transparent)
icon-square.svg  → apple-touch-icon.png (180, sin transparencia: iOS pone su propia máscara / no transparency: iOS applies its own mask)
icon-maskable.svg → icon-maskable-512.png
"""
import pathlib
from playwright.sync_api import sync_playwright
here = pathlib.Path(__file__).resolve().parent
out = here.parent.parent / "home"
jobs = [("icon.svg", "icon-192.png", 192, True), ("icon.svg", "icon-512.png", 512, True),
        ("icon-square.svg", "apple-touch-icon.png", 180, False), ("icon-maskable.svg", "icon-maskable-512.png", 512, False)]
with sync_playwright() as p:
    b = p.chromium.launch()
    for src, name, size, transparent in jobs:
        pg = b.new_page(viewport={"width": size, "height": size})
        svg = (here / src).read_text()
        pg.set_content(f'<body style="margin:0;background:transparent"><div style="width:{size}px;height:{size}px">{svg.replace(chr(10)," ").replace("width=\"512\" height=\"512\"", f"width=\"{size}\" height=\"{size}\"",1)}</div></body>')
        pg.screenshot(path=str(out / name), omit_background=transparent, clip={"x": 0, "y": 0, "width": size, "height": size})
        pg.close()
    b.close()

# iOS vuelve a descargar el icono al añadir la app a la pantalla de inicio con un proceso aparte que puede fallar (certificado propio, redirección…) y pone una «P». Por eso el apple-touch-icon va incrustado (data:) en cada página: no hay segunda descarga.
# EN: iOS downloads the icon again when adding the app to the home screen, in a separate process that can fail (own certificate, redirect…) and shows a "P". That is why the apple-touch-icon is embedded (data:) in every page: there is no second download.
import base64, io, re
from PIL import Image
buf = io.BytesIO(); Image.open(out / "apple-touch-icon.png").convert("RGB").save(buf, "PNG", optimize=True)
uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
root = out.parent
pages = [out / "index.html"] + [root / m / "static" / "index.html" for m in ("auth", "wol-console", "nut-monitor", "net-monitor", "proxmox-monitor", "overview")]
for f in pages:
    t = f.read_text()
    n = re.sub(r'<link rel="apple-touch-icon" href="[^"]*">', lambda m: f'<link rel="apple-touch-icon" href="{uri}">', t, count=1)
    if n != t: f.write_text(n)
print("ok", len(uri), "bytes de icono incrustado")
