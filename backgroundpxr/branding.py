from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


def _font(size: int, bold: bool = True):
    candidates = [
        r"C:\Windows\Fonts\seguisb.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def _gradient(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            nx = x / max(1, size - 1)
            ny = y / max(1, size - 1)
            glow = max(0.0, 1.0 - math.hypot(nx - 0.28, ny - 0.25) * 1.7)
            violet = max(0.0, 1.0 - math.hypot(nx - 0.82, ny - 0.78) * 2.0)
            r = int(5 + 12 * glow + 40 * violet)
            g = int(12 + 76 * glow + 12 * violet)
            b = int(30 + 125 * glow + 120 * violet)
            px[x, y] = (min(r, 255), min(g, 255), min(b, 255))
    return img


def create_icon_png(size: int = 512) -> Image.Image:
    base = _gradient(size).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    radius = int(size * 0.20)
    md.rounded_rectangle((18, 18, size - 18, size - 18), radius=radius, fill=255)
    base.putalpha(mask)

    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for width, alpha in [(34, 40), (18, 90), (7, 230)]:
        gd.rounded_rectangle((24, 24, size - 24, size - 24), radius=radius - 4,
                             outline=(27, 205, 255, alpha), width=width)
    glow = glow.filter(ImageFilter.GaussianBlur(max(1, size // 90)))
    base = Image.alpha_composite(base, glow)
    draw = ImageDraw.Draw(base)

    tile = max(14, size // 18)
    x0, y0, x1, y1 = int(size * 0.55), int(size * 0.13), int(size * 0.87), int(size * 0.60)
    for yy in range(y0, y1, tile):
        for xx in range(x0, x1, tile):
            even = ((xx - x0) // tile + (yy - y0) // tile) % 2 == 0
            c = (239, 243, 250, 220) if even else (159, 172, 194, 205)
            draw.rectangle((xx, yy, min(xx + tile, x1), min(yy + tile, y1)), fill=c)

    subject = [(0.34, 0.68), (0.36, 0.57), (0.42, 0.52), (0.41, 0.43),
               (0.39, 0.34), (0.44, 0.24), (0.53, 0.20), (0.61, 0.23),
               (0.65, 0.30), (0.63, 0.38), (0.67, 0.47), (0.63, 0.53),
               (0.68, 0.59), (0.73, 0.68)]
    pts = [(int(x * size), int(y * size)) for x, y in subject]
    pts += [(int(0.34 * size), int(0.68 * size))]
    draw.polygon(pts, fill=(8, 47, 119, 250))
    draw.line(pts, fill=(95, 235, 255, 255), width=max(4, size // 70), joint="curve")

    dash_pts = [(int(x * size), int(y * size)) for x, y in subject[4:12]]
    for i in range(len(dash_pts) - 1):
        if i % 2 == 0:
            draw.line((dash_pts[i], dash_pts[i + 1]), fill=(255, 255, 255, 235), width=max(3, size // 90))

    font = _font(int(size * 0.205), bold=True)
    bbox = draw.textbbox((0, 0), "PXR", font=font)
    tw = bbox[2] - bbox[0]
    tx = (size - tw) // 2
    ty = int(size * 0.69)
    draw.text((tx + 3, ty + 4), "PXR", font=font, fill=(0, 0, 0, 120))
    draw.text((tx, ty), "PXR", font=font, fill=(246, 249, 255, 255))
    draw.line((int(size * 0.43), int(size * 0.86), int(size * 0.59), int(size * 0.70)),
              fill=(33, 224, 255, 255), width=max(5, size // 55))
    draw.line((int(size * 0.50), int(size * 0.88), int(size * 0.66), int(size * 0.72)),
              fill=(137, 73, 255, 230), width=max(3, size // 80))
    return base


def icon_directory() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".backgroundpxr")) / "BackgroundPXR" / "branding"
    base.mkdir(parents=True, exist_ok=True)
    return base


def ensure_app_icon(directory: str | Path | None = None) -> tuple[Path, Path]:
    target = Path(directory) if directory else icon_directory()
    target.mkdir(parents=True, exist_ok=True)
    png = target / "BackgroundPXR.png"
    ico = target / "BackgroundPXR.ico"
    if not png.exists() or not ico.exists():
        image = create_icon_png(512)
        image.save(png, "PNG", optimize=True)
        image.save(ico, "ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                      (64, 64), (128, 128), (256, 256)])
    return png, ico


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="build_assets")
    args = parser.parse_args()
    png, ico = ensure_app_icon(args.output)
    print(png)
    print(ico)


if __name__ == "__main__":
    main()
