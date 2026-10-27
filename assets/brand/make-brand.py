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
    """Bold two-tone symbol standing on the platform. F = glyph fill, D = cut-outs, S = soft secondary tone."""
    F, S, D = "url(#gf)", "url(#gs)", dark
    if name == "overview":
        return (f'<rect x="164" y="104" width="86" height="86" rx="24" fill="{F}"/><rect x="262" y="104" width="86" height="86" rx="24" fill="{S}"/>'
                f'<rect x="164" y="202" width="86" height="86" rx="24" fill="{S}"/><rect x="262" y="202" width="86" height="86" rx="24" fill="{F}"/>')
    if name == "ups":
        return (f'<rect x="226" y="86" width="60" height="30" rx="10" fill="{S}"/><rect x="186" y="106" width="140" height="196" rx="36" fill="{F}"/>'
                f'<path d="M270 138 L222 224 H252 L240 276 L292 190 H262 Z" fill="{D}"/>')
    if name == "net":
        pts = [(176, 128), (336, 128), (176, 290), (336, 290)]
        lines = "".join(f'<path d="M{x} {y} L256 209" stroke="{S}" stroke-width="14" stroke-linecap="round"/>' for x, y in pts)
        return lines + "".join(f'<circle cx="{x}" cy="{y}" r="28" fill="{S}"/>' for x, y in pts) + f'<circle cx="256" cy="209" r="44" fill="{F}"/><circle cx="256" cy="209" r="16" fill="{D}"/>'
    if name == "proxmox":
        return (f'<path d="M256 168 L190 252 M256 168 L322 252" stroke="{S}" stroke-width="14" stroke-linecap="round"/>'
                f'<rect x="196" y="92" width="120" height="82" rx="24" fill="{F}"/><rect x="132" y="236" width="120" height="82" rx="24" fill="{S}"/><rect x="260" y="236" width="120" height="82" rx="24" fill="{S}"/>'
                f'<circle cx="290" cy="133" r="10" fill="{D}"/><circle cx="226" cy="277" r="10" fill="{D}"/><circle cx="354" cy="277" r="10" fill="{D}"/>')
    if name == "nas":
        return "".join(f'<rect x="156" y="{y}" width="200" height="62" rx="20" fill="{F if i == 0 else S}"/><circle cx="324" cy="{y+31}" r="9" fill="{D}"/><rect x="180" y="{y+25}" width="74" height="12" rx="6" fill="{D}" opacity=".55"/>'
                       for i, y in enumerate((96, 172, 248)))
    if name == "wol":
        return (f'<path d="M184 150 A98 98 0 1 0 328 150" fill="none" stroke="{F}" stroke-width="30" stroke-linecap="round"/>'
                f'<path d="M256 96 V204" stroke="{F}" stroke-width="30" stroke-linecap="round"/><circle cx="256" cy="244" r="0" fill="{D}"/>')
    if name == "admin":
        return (f'<path d="M256 90 L366 134 V224 C366 276 322 312 256 332 C190 312 146 276 146 224 V134 Z" fill="{F}"/>'
                f'<path d="M204 216 L242 254 L312 176" fill="none" stroke="{D}" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>')
    raise ValueError(name)

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
