"""Home-screen assets for iOS, generated from app/icons/mark.svg.

    python tools/make_ios_assets.py

iOS does not scale one icon well and, without a launch image of the exact device size, shows a blank screen
while a home-screen web app starts. So this writes:

  app/icons/apple-touch-icon-<n>.png   the icon, at the sizes iOS asks for
  app/splash/<w>x<h>.png               a launch image per current iPhone and iPad, portrait and landscape

The mark is pure M/L/Z polygons (see tools/make_logo.py), so it rasterises here without a font or an SVG library.
Re-run after changing the mark, then `python tools/export_static.py` (or copy app/ to docs/).
"""
import re
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
MARK = ROOT / "app/icons/mark.svg"
ICONS = ROOT / "app/icons"
SPLASH = ROOT / "app/splash"

TILE = (0x16, 0x18, 0x1D)   # the Standard base; a launch image cannot follow a setting
INK = (0xF2, 0xF3, 0xF5)
ACCENT = (0xF0, 0xA0, 0x4A)

ICON_SIZES = [180, 167, 152, 120]  # iPhone, iPad Pro, iPad, older iPhone

# Portrait logical sizes and scale factors for the iPhones and iPads in use. iOS matches a launch image by
# device-width/height and -webkit-device-pixel-ratio, so each one needs its own file.
DEVICES = [
    (320, 568, 2), (375, 667, 2), (414, 736, 3),           # SE 1st gen, SE/8, 8 Plus
    (375, 812, 3), (414, 896, 2), (414, 896, 3),           # X/XS/11 Pro, XR/11, XS Max/11 Pro Max
    (360, 780, 3), (390, 844, 3), (428, 926, 3),           # 12/13 mini, 12/13/14, 12/13 Pro Max
    (393, 852, 3), (430, 932, 3),                          # 14 Pro/15/16, 14 Pro Max/15 Plus/16 Plus
    (402, 874, 3), (440, 956, 3),                          # 16 Pro, 16 Pro Max
    (768, 1024, 2), (810, 1080, 2), (834, 1112, 2),        # iPad, iPad 10.2, iPad Air 10.5
    (820, 1180, 2), (834, 1194, 2), (1024, 1366, 2),       # iPad Air 10.9, iPad Pro 11, iPad Pro 12.9
]


def polygons():
    """The mark as [(polygon, fill)], in viewBox coordinates."""
    svg = MARK.read_text(encoding="utf-8")
    x0, y0, w, h = (float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split())
    out = []
    for d in re.findall(r'<path[^>]*\sd="([^"]+)"', svg):
        for part in filter(None, (p.strip() for p in d.split("Z"))):
            pts = [tuple(float(v) for v in pair.split()) for pair in re.findall(r'[ML]\s*([-\d.]+\s+[-\d.]+)', part)]
            if len(pts) > 2:
                out.append((pts, INK))
    for points in re.findall(r'<polygon[^>]*\spoints="([^"]+)"', svg):
        out.append(([tuple(float(v) for v in p.split(",")) for p in points.split()], ACCENT))
    return out, (x0, y0, max(w, h))


POLYS, (VX, VY, VSPAN) = polygons()


def draw_mark(img, cx, cy, span):
    """Draw the mark centred on (cx, cy), scaled so the viewBox spans `span` pixels."""
    d = ImageDraw.Draw(img)
    k = span / VSPAN
    ox, oy = cx - (VX + VSPAN / 2) * k, cy - (VY + VSPAN / 2) * k
    for pts, fill in POLYS:
        d.polygon([(ox + x * k, oy + y * k) for x, y in pts], fill=fill)


def icon(size):
    """Square, full-bleed: iOS rounds the corners itself and never wants transparency."""
    s = size * 4
    img = Image.new("RGB", (s, s), TILE)
    draw_mark(img, s / 2, s / 2, s * 0.62)
    img.resize((size, size), Image.LANCZOS).save(ICONS / f"apple-touch-icon-{size}.png", optimize=True)


def splash(w, h):
    img = Image.new("RGB", (w, h), TILE)
    draw_mark(img, w / 2, h / 2, min(w, h) * 0.34)
    img.save(SPLASH / f"{w}x{h}.png", optimize=True)


def main():
    SPLASH.mkdir(parents=True, exist_ok=True)
    for s in ICON_SIZES:
        icon(s)
    seen = set()
    for lw, lh, scale in DEVICES:
        for w, h in ((lw * scale, lh * scale), (lh * scale, lw * scale)):  # portrait and landscape
            if (w, h) not in seen:
                seen.add((w, h))
                splash(w, h)
    print(f"{len(ICON_SIZES)} icons, {len(seen)} launch images")
    print(links())


def links():
    """The <link> tags these files need, printed so index.html can be kept in step."""
    out = [f'<link rel="apple-touch-icon" sizes="{s}x{s}" href="icons/apple-touch-icon-{s}.png">' for s in ICON_SIZES]
    seen = set()
    for lw, lh, scale in DEVICES:
        for w, h, orient in ((lw * scale, lh * scale, "portrait"), (lh * scale, lw * scale, "landscape")):
            if (w, h) in seen:
                continue
            seen.add((w, h))
            dw, dh = (lw, lh) if orient == "portrait" else (lh, lw)
            out.append(
                f'<link rel="apple-touch-startup-image" href="splash/{w}x{h}.png" '
                f'media="(device-width: {dw}px) and (device-height: {dh}px) and '
                f'(-webkit-device-pixel-ratio: {scale}) and (orientation: {orient})">')
    return "\n".join(out)


if __name__ == "__main__":
    main()
