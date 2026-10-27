#!/usr/bin/env python3
"""Regenera los iconos de la app desde assets/icons/icon-source.png (necesita Pillow).
EN: Regenerates the app icons from assets/icons/icon-source.png (needs Pillow).

    python3 assets/icons/make-icons.py

icon-192.png / icon-512.png  → esquinas redondeadas, transparente / rounded corners, transparent
apple-touch-icon.png (180)   → cuadrado, sin transparencia: iOS pone su propia máscara / square, no transparency: iOS applies its own mask
icon-maskable-512.png        → ilustración más pequeña dentro de la zona segura / artwork inside the safe zone
logo.png (256)               → logo de la cabecera de inicio y Resumen / logo of the home and Overview headers
docs/logo.png (512)          → logo del README
"""
import base64, io, pathlib, re
from PIL import Image, ImageDraw
here = pathlib.Path(__file__).resolve().parent
root = here.parent.parent
out = root / "home"
src = Image.open(here / "icon-source.png").convert("RGB")
BG = src.getpixel((4, 4))

def rounded(size, radius):
    img = src.resize((size, size), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1), radius=radius * 4, fill=255)
    img.putalpha(m.resize((size, size), Image.LANCZOS))
    return img

rounded(192, 36).save(out / "icon-192.png", optimize=True)
rounded(512, 96).save(out / "icon-512.png", optimize=True)
rounded(256, 48).save(out / "logo.png", optimize=True)
rounded(512, 96).save(root / "docs" / "logo.png", optimize=True)
src.resize((180, 180), Image.LANCZOS).save(out / "apple-touch-icon.png", optimize=True)
mask = Image.new("RGB", (512, 512), BG)                       # maskable: el sistema recorta hasta un 20 % por lado
mask.paste(src.resize((360, 360), Image.LANCZOS), (76, 76))
mask.save(out / "icon-maskable-512.png", optimize=True)

def data_uri(img, fmt="PNG"):
    buf = io.BytesIO(); img.save(buf, fmt, optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# iOS vuelve a descargar el icono al añadir la app a la pantalla de inicio con un proceso aparte que puede fallar (certificado propio, redirección…) y pone una «P». Por eso el apple-touch-icon va incrustado (data:) en cada página: no hay segunda descarga. El favicon también va incrustado.
# EN: iOS downloads the icon again when adding the app to the home screen, in a separate process that can fail (own certificate, redirect…). That is why the apple-touch-icon is embedded (data:) in every page: there is no second download. The favicon is embedded too.
touch = data_uri(Image.open(out / "apple-touch-icon.png").convert("RGB"))
fav = data_uri(rounded(64, 12))
pages = [out / "index.html"] + [root / m / "static" / "index.html" for m in ("auth", "wol-console", "nut-monitor", "net-monitor", "proxmox-monitor", "nas-monitor", "dns-monitor", "wan-monitor", "overview")]
for f in pages:
    t = f.read_text()
    n = re.sub(r'<link rel="apple-touch-icon" href="[^"]*">', lambda m: f'<link rel="apple-touch-icon" href="{touch}">', t, count=1)
    n = re.sub(r'<link rel="icon" type="image/[a-z+]+" href="[^"]*">', lambda m: f'<link rel="icon" type="image/png" href="{fav}">', n, count=1)
    if n != t: f.write_text(n)
print("ok")
