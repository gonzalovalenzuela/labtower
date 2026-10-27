#!/usr/bin/env python3
"""Genera el kit de marca: un icono por módulo (SVG + PNG) y la paleta (palette.css / palette.json).
EN: Generates the brand kit: one icon per module (SVG + PNG) and the palette (palette.css / palette.json).

    python3 assets/brand/make-brand.py     (needs playwright + chromium for the PNGs)

Todos los iconos comparten la misma construcción que la marca: baldosa pizarra azulada, trazo de línea con degradado y «nodos» (anillo con punto) como terminales.
EN: Every icon shares the brand's construction: slate-blue tile, gradient line stroke and "nodes" (ring with a dot) as terminals.
"""
import json, pathlib
here = pathlib.Path(__file__).resolve().parent
icons = here / "icons"; icons.mkdir(exist_ok=True)

BRAND = {"night": "#191e32", "night-2": "#222a45", "ice": "#b4dcff", "sky": "#4aa8f5", "blue": "#1b6db8", "slate": "#4e6bb0", "ink": "#eef0f6"}
# acento por módulo = el color que ya usa la tarjeta de cada módulo en la página de inicio
MODULES = [
    ("overview", "Resumen / Overview",      "#8b5cf6"),
    ("ups",      "UPS Monitor",             "#eab308"),
    ("net",      "Net Monitor",             "#14b8a6"),
    ("proxmox",  "Proxmox Monitor",         "#e15c00"),
    ("nas",      "NAS Monitor",             "#0e9aa7"),
    ("wol",      "WOL Console",             "#4361ee"),
    ("admin",    "Admin Panel",             "#f0527a"),
]

def mix(hexc, to, t):
    a = [int(hexc[i:i+2], 16) for i in (1, 3, 5)]; b = [int(to[i:i+2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

def node(x, y, r=20):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="url(#g)" stroke-width="11"/>'
            f'<circle cx="{x}" cy="{y}" r="{round(r*.38)}" fill="{{hi}}"/>')

def glyph(name):
    L = 'fill="none" stroke="url(#g)" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"'
    if name == "overview":
        return (f'<rect x="132" y="132" width="106" height="106" rx="24" {L}/><rect x="274" y="132" width="106" height="106" rx="24" {L}/>'
                f'<rect x="132" y="274" width="106" height="106" rx="24" {L}/>' + node(327, 327, 38))
    if name == "ups":
        return (f'<rect x="164" y="206" width="184" height="226" rx="34" {L}/>'
                f'<path d="M222 206 V156 M290 206 V156" {L}/>' + node(222, 134, 22) + node(290, 134, 22) +
                '<path d="M276 250 L224 338 H258 L242 400 L296 308 H262 Z" fill="url(#g)"/>')
    if name == "net":
        pts = [(142, 150), (370, 150), (142, 362), (370, 362)]
        lines = "".join(f'<path d="M{x} {y} L256 256" {L}/>' for x, y in pts)
        return lines + "".join(node(x, y, 30) for x, y in pts) + node(256, 256, 34)
    if name == "proxmox":
        return (f'<path d="M256 214 L168 330 M256 214 L344 330 M232 380 H280" {L}/>'
                f'<rect x="196" y="118" width="120" height="84" rx="22" {L}/><rect x="108" y="338" width="120" height="84" rx="22" {L}/><rect x="284" y="338" width="120" height="84" rx="22" {L}/>'
                '<circle cx="288" cy="160" r="9" fill="{hi}"/><circle cx="200" cy="380" r="9" fill="{hi}"/><circle cx="376" cy="380" r="9" fill="{hi}"/>')
    if name == "nas":
        return (f'<rect x="124" y="140" width="264" height="210" rx="34" {L}/>'
                f'<path d="M190 176 V314 M256 176 V314 M322 176 V314" {L}/>'
                f'<path d="M256 350 V396" {L}/>' + node(256, 424, 22))
    if name == "wol":
        return (f'<path d="M180 176 A116 116 0 1 0 332 176" {L}/><path d="M256 232 V142" {L}/>' + node(256, 112, 24))
    if name == "admin":
        return (f'<path d="M256 112 L378 160 V262 C378 336 326 384 256 408 C186 384 134 336 134 262 V160 Z" {L}/>'
                f'<path d="M200 262 L242 304 L318 220" {L}/>')
    raise ValueError(name)

def svg(name, accent):
    hi = mix(accent, "#ffffff", .55); lo = accent
    body = glyph(name).replace("{hi}", hi)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">'
            f'<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="120" y1="100" x2="400" y2="420"><stop offset="0" stop-color="{hi}"/><stop offset="1" stop-color="{lo}"/></linearGradient>'
            f'<radialGradient id="glow" cx=".5" cy=".38" r=".62"><stop offset="0" stop-color="{accent}" stop-opacity=".30"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient></defs>'
            f'<rect width="512" height="512" rx="112" fill="{BRAND["night"]}"/><rect width="512" height="512" rx="112" fill="url(#glow)"/>{body}</svg>\n')

for n, _, a in MODULES:
    (icons / f"{n}.svg").write_text(svg(n, a))

tokens = {"brand": BRAND, "modules": {n: {"name": t, "accent": a, "accent-light": mix(a, "#ffffff", .55), "accent-dim": mix(a, BRAND["night"], .82)} for n, t, a in MODULES},
          "gradient": f"linear-gradient(135deg, {BRAND['ice']}, {BRAND['sky']} 55%, {BRAND['blue']})"}
(here / "palette.json").write_text(json.dumps(tokens, indent=2, ensure_ascii=False) + "\n")
css = ["/* LabTower: paleta de marca / brand palette (generado por make-brand.py) */", ":root{"]
css += [f"  --lt-{k}: {v};" for k, v in BRAND.items()]
for n, m in tokens["modules"].items():
    css += [f"  --lt-{n}: {m['accent']};", f"  --lt-{n}-light: {m['accent-light']};", f"  --lt-{n}-dim: {m['accent-dim']};"]
css += [f"  --lt-gradient: {tokens['gradient']};", "}"]
(here / "palette.css").write_text("\n".join(css) + "\n")

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for n, _, _ in MODULES:
            s = (icons / f"{n}.svg").read_text()
            for size in (512, 192, 64):
                pg = b.new_page(viewport={"width": size, "height": size})
                pg.set_content(f'<body style="margin:0;background:transparent">{s.replace(chr(10), " ").replace("width=\"512\" height=\"512\"", f"width=\"{size}\" height=\"{size}\"", 1)}</body>')
                pg.screenshot(path=str(icons / f"{n}-{size}.png"), omit_background=True, clip={"x": 0, "y": 0, "width": size, "height": size}); pg.close()
        b.close()
except ImportError:
    print("playwright no instalado: solo SVG / playwright missing: SVG only")
print("ok")
