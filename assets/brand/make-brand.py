#!/usr/bin/env python3
"""Genera el kit de marca: un icono por módulo (SVG + PNG) y la paleta (palette.css / palette.json).
EN: Generates the brand kit: one icon per module (SVG + PNG) and the palette (palette.css / palette.json).

    python3 assets/brand/make-brand.py     (needs playwright + chromium for the PNGs)

Todos los iconos usan la construcción de la marca: baldosa pizarra azulada y una plataforma de dos losas isométricas (las de la marca) teñidas con el color del módulo y un símbolo sólido de dos tonos encima.
EN: Every icon uses the brand's construction: slate-blue tile and a two-slab isometric platform (the brand mark's slabs) tinted with the module colour and a bold two-tone symbol standing on it.
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
    ("dns",      "DNS Monitor",             "#d946ef"),
    ("wan",      "WAN Monitor",             "#0ea5e9"),
    ("wol",      "WOL Console",             "#4361ee"),
    ("admin",    "Admin Panel",             "#f0527a"),
]

def mix(hexc, to, t):
    a = [int(hexc[i:i+2], 16) for i in (1, 3, 5)]; b = [int(to[i:i+2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

def slab(cy, top, left, right, t=28, hw=104, hh=50):
    """Isometric slab, the brand mark's building block: top rhombus plus two sides."""
    return (f'<path d="M{256-hw} {cy} L256 {cy+hh} L256 {cy+hh+t} L{256-hw} {cy+t} Z" fill="{left}"/>'
            f'<path d="M{256+hw} {cy} L256 {cy+hh} L256 {cy+hh+t} L{256+hw} {cy+t} Z" fill="{right}"/>'
            f'<path d="M256 {cy-hh} L{256+hw} {cy} L256 {cy+hh} L{256-hw} {cy} Z" fill="{top}" stroke="{top}" stroke-width="6" stroke-linejoin="round"/>')

def solid(name, dark):
    """Bold two-tone version of each module's original symbol (the Feather-style glyphs used in the app from earlier versions), drawn on its 24 grid.
    F = main fill, S = soft secondary tone, D = cut-outs.   EN: solid two-tone take on the symbols the app already uses."""
    F, S, D = "url(#gf)", "url(#gs)", dark
    if name == "overview":      # layout / dashboard
        g = (f'<rect x="3" y="3" width="7" height="9" rx="1.8" fill="{F}"/><rect x="14" y="3" width="7" height="5" rx="1.8" fill="{S}"/>'
             f'<rect x="14" y="12" width="7" height="9" rx="1.8" fill="{F}"/><rect x="3" y="16" width="7" height="5" rx="1.8" fill="{S}"/>')
    elif name == "ups":         # box with handle and a line
        g = (f'<path d="M5.6 9 V5.2 a1.6 1.6 0 0 1 1.6-1.6 h9.6 a1.6 1.6 0 0 1 1.6 1.6 V9" fill="none" stroke="{S}" stroke-width="2.4" stroke-linecap="round"/>'
             f'<rect x="3" y="9" width="18" height="11.5" rx="2.6" fill="{F}"/><path d="M12 12.6 V16.4" stroke="{D}" stroke-width="2.2" stroke-linecap="round"/>')
    elif name == "net":         # two stacked servers
        g = (f'<rect x="2" y="2" width="20" height="8.4" rx="2.4" fill="{F}"/><rect x="2" y="13.6" width="20" height="8.4" rx="2.4" fill="{S}"/>'
             f'<circle cx="6.2" cy="6.2" r="1.3" fill="{D}"/><circle cx="6.2" cy="17.8" r="1.3" fill="{D}"/>'
             f'<path d="M10.5 6.2 H18 M10.5 17.8 H18" stroke="{D}" stroke-width="1.6" stroke-linecap="round" opacity=".5"/>')
    elif name == "proxmox":     # monitor on a stand
        g = (f'<path d="M8 21 H16 M12 17 V21" stroke="{S}" stroke-width="2.4" stroke-linecap="round"/>'
             f'<rect x="2" y="3" width="20" height="14.4" rx="2.6" fill="{F}"/><rect x="4.4" y="5.4" width="15.2" height="9.6" rx="1.4" fill="{D}" opacity=".38"/>')
    elif name == "nas":         # storage unit with two bays and an LED
        g = (f'<rect x="3" y="3" width="18" height="18" rx="3" fill="{F}"/><path d="M7 9 H17 M7 14 H17" stroke="{D}" stroke-width="2" stroke-linecap="round" opacity=".5"/>'
             f'<circle cx="16" cy="18" r="1.3" fill="{D}"/>')
    elif name == "dns":         # globe
        g = (f'<circle cx="12" cy="12" r="10" fill="{F}"/><path d="M2.4 12 H21.6" stroke="{D}" stroke-width="1.8" opacity=".5"/>'
             f'<path d="M12 2.4 a14 14 0 0 1 0 19.2 a14 14 0 0 1 0-19.2" fill="none" stroke="{D}" stroke-width="1.8" opacity=".5"/>')
    elif name == "wan":         # wifi arcs
        g = (f'<path d="M2 9.2 a14.5 14.5 0 0 1 20 0" fill="none" stroke="{S}" stroke-width="2.6" stroke-linecap="round"/>'
             f'<path d="M5.6 13 a9.4 9.4 0 0 1 12.8 0" fill="none" stroke="{F}" stroke-width="2.6" stroke-linecap="round"/>'
             f'<path d="M9 16.6 a4.6 4.6 0 0 1 6 0" fill="none" stroke="{F}" stroke-width="2.6" stroke-linecap="round"/><circle cx="12" cy="20" r="1.8" fill="{F}"/>')
    elif name == "wol":         # lightning bolt
        g = f'<path d="M13 2 L3.6 13.6 H11.6 L10.8 22 L20.6 10.2 H12.4 Z" fill="{F}" stroke="{F}" stroke-width="1.2" stroke-linejoin="round"/>'
    elif name == "admin":       # shield
        g = (f'<path d="M12 22 s8-4 8-10 V5 l-8-3 -8 3 v7 c0 6 8 10 8 10 z" fill="{F}"/>'
             f'<path d="M8.4 11.8 l2.5 2.5 L15.8 9.2" fill="none" stroke="{D}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>')
    else:
        raise ValueError(name)
    return f'<g transform="translate(128 76) scale(10.667)">{g}</g>'

def svg(name, accent):
    """Modern family icon: slate tile, a two-slab platform in the module colour (the brand mark's slabs) and a bold symbol standing on it."""
    N = BRAND["night"]; W = "#ffffff"; uid = "s" + name
    dark = mix(accent, N, .62)
    defs = (f'<defs><linearGradient id="gf" gradientUnits="userSpaceOnUse" x1="0" y1="80" x2="0" y2="340"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="{mix(accent, W, .72)}"/></linearGradient>'
            f'<linearGradient id="gs" gradientUnits="userSpaceOnUse" x1="0" y1="80" x2="0" y2="340"><stop offset="0" stop-color="{mix(accent, W, .55)}"/><stop offset="1" stop-color="{mix(accent, W, .3)}"/></linearGradient>'
            f'<linearGradient id="pl1"><stop offset="0" stop-color="{mix(accent, W, .35)}"/><stop offset="1" stop-color="{accent}"/></linearGradient>'
            f'<linearGradient id="pr1"><stop offset="0" stop-color="{accent}"/><stop offset="1" stop-color="{mix(accent, N, .35)}"/></linearGradient>'
            f'<linearGradient id="pl2"><stop offset="0" stop-color="{mix(accent, N, .35)}"/><stop offset="1" stop-color="{mix(accent, N, .55)}"/></linearGradient>'
            f'<linearGradient id="pr2"><stop offset="0" stop-color="{mix(accent, N, .6)}"/><stop offset="1" stop-color="{mix(accent, N, .8)}"/></linearGradient>'
            f'<radialGradient id="glow" cx=".5" cy=".4" r=".62"><stop offset="0" stop-color="{accent}" stop-opacity=".34"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>'
            f'<filter id="sh" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="10" stdDeviation="9" flood-color="#000" flood-opacity=".38"/></filter></defs>')
    platform = slab(398, mix(accent, N, .45), "url(#pl2)", "url(#pr2)", t=24) + slab(372, mix(accent, W, .82), "url(#pl1)", "url(#pr1)", t=26)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">{defs}'
            f'<rect width="512" height="512" rx="112" fill="{N}"/><rect width="512" height="512" rx="112" fill="url(#glow)"/>'
            f'{platform}<g filter="url(#sh)">{solid(name, dark)}</g></svg>\n')

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
