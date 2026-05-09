#!/usr/bin/env python3
"""Build Capacitor splash images (2732x2732) from the processed icon.

Capacitor uses a square splash that's center-fit on every device size, so
one image at 2732x2732 (≥ iPad Pro 12.9" portrait long-edge) covers all
devices. We make three identical files for the imageset's 1x/2x/3x slots.

Design: solid field-green background, the icon artwork centered ~58 %, and
the title "ROBOT SOCCER 3D" set in a gold-gradient stroked font beneath it.
"""

import os, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

ASSET_DIR = "/Users/jason/Documents/GitHub/Billy/ipad-app/ios/App/App/Assets.xcassets/Splash.imageset"
ICON      = "/Users/jason/Documents/GitHub/Billy/ipad-app/ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png"

W = H = 2732

# ---------- 1. Field-green background ----------
icon = Image.open(ICON).convert("RGB")
# Sample bg color from the icon's corners (its padding) to match exactly.
arr = np.asarray(icon)
samples = [arr[0, 0], arr[0, -1], arr[-1, 0], arr[-1, -1]]
bg = tuple(int(c) for c in np.mean(samples, axis=0).round())
print(f"icon bg color: {bg}")
canvas = Image.new("RGB", (W, H), bg)

# Subtle vertical gradient so the splash isn't flat
gp = canvas.load()
top    = (max(0, bg[0] - 12), max(0, bg[1] - 8),  max(0, bg[2] - 12))
bottom = (max(0, bg[0] - 28), max(0, bg[1] - 22), max(0, bg[2] - 24))
for y in range(H):
    t = y / (H - 1)
    r = int(top[0] + (bottom[0] - top[0]) * t)
    g = int(top[1] + (bottom[1] - top[1]) * t)
    b = int(top[2] + (bottom[2] - top[2]) * t)
    for x in range(W):
        gp[x, y] = (r, g, b)

# ---------- 2. Place the icon centered, scaled to 64% of canvas ----------
# (No title text — icon stands on its own and sits dead-center.)
scale = 0.64
art_size = int(W * scale)
art = icon.resize((art_size, art_size), Image.LANCZOS)
ax = (W - art_size) // 2
ay = (H - art_size) // 2

# Drop shadow under the art
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
shadow_pad = int(art_size * 0.08)
sd.rounded_rectangle([ax + shadow_pad, ay + art_size - shadow_pad // 2,
                      ax + art_size - shadow_pad,
                      ay + art_size + shadow_pad // 2],
                     radius=art_size // 6, fill=(0, 0, 0, 130))
shadow = shadow.filter(ImageFilter.GaussianBlur(radius=40))

canvas_rgba = canvas.convert("RGBA")
canvas_rgba = Image.alpha_composite(canvas_rgba, shadow)
# round-corner the icon when pasted (matches iOS auto-rounded look)
mask = Image.new("L", (art_size, art_size), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, art_size, art_size],
                                       radius=art_size // 5, fill=255)
canvas_rgba.paste(art, (ax, ay), mask)
canvas = canvas_rgba.convert("RGB")

# (Title text intentionally omitted — splash is just the icon on green.)

# ---------- 4. Save into all three Splash imageset slots ----------
out_paths = [
    os.path.join(ASSET_DIR, "splash-2732x2732.png"),
    os.path.join(ASSET_DIR, "splash-2732x2732-1.png"),
    os.path.join(ASSET_DIR, "splash-2732x2732-2.png"),
]
for p in out_paths:
    canvas.save(p, "PNG", optimize=True)
    print(f"wrote {p} ({os.path.getsize(p)} bytes)")
