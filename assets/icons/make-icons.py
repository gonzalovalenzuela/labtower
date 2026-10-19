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
print("ok")
