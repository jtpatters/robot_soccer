#!/usr/bin/env python3
"""Convert the latest Grok illustration into a 1024x1024 iOS app icon.

The source is two robots + soccer ball on a solid green background with a
soft drop shadow. iOS app icons must be a fully-opaque square; iOS adds the
rounded corners on-device, so the artwork should fill the canvas edge-to-edge.
"""

import os, sys
from PIL import Image, ImageFilter
import numpy as np

# Detect the most recent grok-rendered image automatically.
ASSET_DIR = "/Users/jason/Documents/GitHub/Billy/ipad-app/ios/App/App/Assets.xcassets/AppIcon.appiconset"
SRC = sorted(
    [os.path.join(ASSET_DIR, f) for f in os.listdir(ASSET_DIR)
     if f.lower().startswith("grok image") and f.lower().endswith(".png")],
    key=os.path.getmtime,
)[-1]
DST = os.path.join(ASSET_DIR, "AppIcon-512@2x.png")
print("source:", SRC)

img = Image.open(SRC).convert("RGB")
W, H = img.size
print(f"size: {W}x{H}")

# ---------- 1. detect background color from corners ----------
samples = [img.getpixel((x, y)) for (x, y) in (
    (5, 5), (W // 2, 5), (W - 6, 5),
    (5, H // 2), (W - 6, H // 2),
    (5, H - 6), (W // 2, H - 6), (W - 6, H - 6)
)]
bg_r = sum(s[0] for s in samples) / len(samples)
bg_g = sum(s[1] for s in samples) / len(samples)
bg_b = sum(s[2] for s in samples) / len(samples)
print(f"detected bg ≈ ({bg_r:.0f}, {bg_g:.0f}, {bg_b:.0f})")

arr = np.asarray(img, dtype=np.int16)
dist = np.sqrt(
    (arr[..., 0] - bg_r) ** 2 +
    (arr[..., 1] - bg_g) ** 2 +
    (arr[..., 2] - bg_b) ** 2
)
# threshold liberal enough to catch dark-shaded shadow pixels but not field noise
fg_mask = dist > 22
print(f"foreground pixel count: {int(fg_mask.sum())}")

# ---------- 2. tight bounding box of the foreground (robots + ball + shadow) ----------
ys, xs = np.where(fg_mask)
left, right = int(xs.min()), int(xs.max())
top, bottom = int(ys.min()), int(ys.max())
print(f"foreground bbox: x=[{left}..{right}] y=[{top}..{bottom}]")

# ---------- 3. add padding so the icon doesn't feel cramped ----------
fg_w = right - left + 1
fg_h = bottom - top + 1
pad_x = int(fg_w * 0.06)
pad_y_top    = int(fg_h * 0.10)
pad_y_bottom = int(fg_h * 0.06)
left   = max(0,     left   - pad_x)
right  = min(W - 1, right  + pad_x)
top    = max(0,     top    - pad_y_top)
bottom = min(H - 1, bottom + pad_y_bottom)
print(f"padded bbox: x=[{left}..{right}] y=[{top}..{bottom}]")

icon = img.crop((left, top, right + 1, bottom + 1))
iw, ih = icon.size
print(f"cropped: {iw}x{ih}")

# ---------- 4. center on a square canvas filled with the source's bg color ----------
side = max(iw, ih)
square = Image.new("RGB", (side, side), (int(bg_r), int(bg_g), int(bg_b)))
square.paste(icon, ((side - iw) // 2, (side - ih) // 2))

# ---------- 5. resize to 1024 with high-quality filter ----------
final = square.resize((1024, 1024), Image.LANCZOS)
final.save(DST, "PNG", optimize=True)
print(f"wrote {DST} ({os.path.getsize(DST)} bytes)")
