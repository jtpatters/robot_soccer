#!/usr/bin/env python3
"""Generate a 1024x1024 RGB app icon for Robot Soccer 3D.

Layout:
  - Background: sky → field gradient with subtle stripes
  - Robot character: upper-center, clearly visible (head + visor + eyes + antenna + body + arms)
  - Soccer ball: held in front of robot's chest, drawn with explicit black pentagon
    + white hexagon panels and dark seams (looks like a real Telstar pattern, not flat)
  - Title "ROBOT SOCCER" gold-gradient text at the bottom (fits the canvas width)
"""

import math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W = H = 1024

def lerp(a, b, t): return a + (b - a) * t

# ============================================================
# 1. Background
# ============================================================
img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
px = img.load()
for y in range(H):
    t = y / (H - 1)
    e = t * t
    r = int(lerp(0x5d, 0x2d, e))
    g = int(lerp(0xad, 0x6a, e))
    b = int(lerp(0xe2, 0x3e, e))
    for x in range(W):
        px[x, y] = (r, g, b, 255)

draw = ImageDraw.Draw(img, "RGBA")

# subtle field stripes near the bottom
FIELD_TOP = int(H * 0.62)
stripe_h = (H - FIELD_TOP) / 8
for i in range(8):
    y0 = FIELD_TOP + int(i * stripe_h)
    y1 = FIELD_TOP + int((i + 1) * stripe_h)
    color = (0x2d, 0x6a, 0x3e, 200) if i % 2 == 0 else (0x35, 0x7e, 0x4c, 200)
    draw.rectangle([0, y0, W, y1], fill=color)

# ============================================================
# 2. Robot character (upper-center)
# ============================================================
robot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(robot, "RGBA")

# Robot proportions
head_cx = W // 2
head_cy = int(H * 0.34)
head_w  = 360
head_h  = 320

body_cx = W // 2
body_cy = int(H * 0.62)
body_w  = 540
body_h  = 360

BLUE_DARK   = (0x14, 0x3e, 0x66, 255)
BLUE_MID    = (0x3a, 0x8f, 0xd6, 255)
BLUE_LIGHT  = (0x6c, 0xb8, 0xee, 255)
VISOR       = (0x10, 0x14, 0x20, 255)
EYE_GLOW    = (0,    0xe5, 0xff, 230)
EYE_BRIGHT  = (0xdc, 0xff, 0xff, 255)
ANT_YELLOW  = (0xff, 0xdc, 0x14, 255)
PANEL_LIGHT = (0x2e, 0xcc, 0x71, 255)

def rounded_rect(d, x0, y0, x1, y1, r, fill, outline=None, width=1):
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill,
                        outline=outline, width=width)

# --- antenna ---
ant_top_x = head_cx
ant_top_y = head_cy - head_h // 2 - 110
# pole
rd.rectangle([head_cx - 6, ant_top_y, head_cx + 6, head_cy - head_h // 2 + 10],
             fill=(0x99, 0x99, 0x99, 255))
# tip glow
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([ant_top_x - 60, ant_top_y - 60, ant_top_x + 60, ant_top_y + 60],
           fill=(255, 220, 20, 180))
glow = glow.filter(ImageFilter.GaussianBlur(radius=18))
robot = Image.alpha_composite(robot, glow)
rd = ImageDraw.Draw(robot, "RGBA")
# tip ball
rd.ellipse([ant_top_x - 24, ant_top_y - 24, ant_top_x + 24, ant_top_y + 24],
           fill=ANT_YELLOW, outline=(120, 100, 0, 255), width=3)
rd.ellipse([ant_top_x - 8, ant_top_y - 14, ant_top_x + 4, ant_top_y - 4],
           fill=(255, 255, 200, 230))

# --- head: rounded square with shadow on bottom-right ---
head_x0 = head_cx - head_w // 2
head_y0 = head_cy - head_h // 2
head_x1 = head_cx + head_w // 2
head_y1 = head_cy + head_h // 2
# drop shadow under head onto body
shd = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sdd = ImageDraw.Draw(shd)
sdd.rounded_rectangle([head_x0 + 12, head_y0 + 18, head_x1 + 12, head_y1 + 18],
                      radius=60, fill=(0, 0, 0, 110))
shd = shd.filter(ImageFilter.GaussianBlur(radius=14))
robot = Image.alpha_composite(robot, shd)
rd = ImageDraw.Draw(robot, "RGBA")
# head fill (vertical gradient blue)
head_grad = Image.new("RGBA", (head_w, head_h), (0, 0, 0, 0))
hgp = head_grad.load()
for yy in range(head_h):
    t = yy / max(1, head_h - 1)
    rr = int(lerp(BLUE_LIGHT[0], BLUE_DARK[0], t))
    gg = int(lerp(BLUE_LIGHT[1], BLUE_DARK[1], t))
    bb = int(lerp(BLUE_LIGHT[2], BLUE_DARK[2], t))
    for xx in range(head_w):
        hgp[xx, yy] = (rr, gg, bb, 255)
# mask gradient by rounded rect shape
hmask = Image.new("L", (head_w, head_h), 0)
ImageDraw.Draw(hmask).rounded_rectangle([0, 0, head_w, head_h], radius=60, fill=255)
robot.paste(head_grad, (head_x0, head_y0), hmask)
rd = ImageDraw.Draw(robot, "RGBA")
# head outline
rd.rounded_rectangle([head_x0, head_y0, head_x1, head_y1], radius=60,
                    outline=(10, 20, 35, 255), width=6)
# corner bolts
for (bx, by) in [(head_x0 + 28, head_y0 + 28), (head_x1 - 28, head_y0 + 28),
                  (head_x0 + 28, head_y1 - 28), (head_x1 - 28, head_y1 - 28)]:
    rd.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=(220, 220, 230, 255))
    rd.ellipse([bx - 5, by - 5, bx + 5, by + 5], fill=(70, 70, 90, 255))

# --- visor band across the head ---
visor_y0 = head_cy - 56
visor_y1 = head_cy + 56
visor_pad = 16
rd.rounded_rectangle([head_x0 + visor_pad, visor_y0,
                      head_x1 - visor_pad, visor_y1],
                     radius=30, fill=VISOR,
                     outline=(0, 0, 0, 255), width=4)

# eye glow underlay
eg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
egd = ImageDraw.Draw(eg)
eye_off = 75
for cx in (head_cx - eye_off, head_cx + eye_off):
    egd.ellipse([cx - 50, head_cy - 50, cx + 50, head_cy + 50],
                fill=EYE_GLOW)
eg = eg.filter(ImageFilter.GaussianBlur(radius=14))
robot = Image.alpha_composite(robot, eg)
rd = ImageDraw.Draw(robot, "RGBA")
# bright eye cores
for cx in (head_cx - eye_off, head_cx + eye_off):
    rd.ellipse([cx - 22, head_cy - 22, cx + 22, head_cy + 22], fill=EYE_BRIGHT)
    rd.ellipse([cx - 8, head_cy - 8, cx + 8, head_cy + 8], fill=(20, 30, 60, 255))
    # tiny highlight
    rd.ellipse([cx - 6, head_cy - 14, cx + 2, head_cy - 6], fill=(255, 255, 255, 230))

# friendly mouth (small line on visor)
mouth_w = 70
rd.rounded_rectangle([head_cx - mouth_w // 2, visor_y1 - 22,
                      head_cx + mouth_w // 2, visor_y1 - 12],
                     radius=4, fill=(0xff, 0xed, 0x4a, 220))

# --- body: big rounded rectangle ---
body_x0 = body_cx - body_w // 2
body_y0 = body_cy - body_h // 2
body_x1 = body_cx + body_w // 2
body_y1 = body_cy + body_h // 2

# body gradient
body_grad = Image.new("RGBA", (body_w, body_h), (0, 0, 0, 0))
bgp = body_grad.load()
for yy in range(body_h):
    t = yy / max(1, body_h - 1)
    rr = int(lerp(BLUE_MID[0], BLUE_DARK[0], t))
    gg = int(lerp(BLUE_MID[1], BLUE_DARK[1], t))
    bb = int(lerp(BLUE_MID[2], BLUE_DARK[2], t))
    for xx in range(body_w):
        bgp[xx, yy] = (rr, gg, bb, 255)
bmask = Image.new("L", (body_w, body_h), 0)
ImageDraw.Draw(bmask).rounded_rectangle([0, 0, body_w, body_h], radius=80, fill=255)
robot.paste(body_grad, (body_x0, body_y0), bmask)
rd = ImageDraw.Draw(robot, "RGBA")
rd.rounded_rectangle([body_x0, body_y0, body_x1, body_y1], radius=80,
                    outline=(10, 20, 35, 255), width=6)

# Arms — two cylinders at the sides hugging the ball area
arm_w = 80
arm_h = 220
# left arm
arm_l_x0 = body_x0 - 30
arm_l_y0 = body_cy - 40
rd.rounded_rectangle([arm_l_x0, arm_l_y0, arm_l_x0 + arm_w, arm_l_y0 + arm_h],
                    radius=arm_w // 2, fill=BLUE_DARK,
                    outline=(10, 20, 35, 255), width=4)
# right arm
arm_r_x0 = body_x1 - arm_w + 30
arm_r_y0 = body_cy - 40
rd.rounded_rectangle([arm_r_x0, arm_r_y0, arm_r_x0 + arm_w, arm_r_y0 + arm_h],
                    radius=arm_w // 2, fill=BLUE_DARK,
                    outline=(10, 20, 35, 255), width=4)

img = Image.alpha_composite(img, robot)

# ============================================================
# 3. Soccer ball — held in front of body
# ============================================================
ball_cx = W // 2
ball_cy = body_cy + 10
ball_r  = 175

ball = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(ball, "RGBA")

# white sphere base
bd.ellipse([ball_cx - ball_r, ball_cy - ball_r,
            ball_cx + ball_r, ball_cy + ball_r],
           fill=(245, 245, 245, 255))

# Helper: regular polygon points
def reg_polygon(cx, cy, r, sides=5, rot=0.0):
    return [
        (cx + math.cos(rot + i * 2 * math.pi / sides) * r,
         cy + math.sin(rot + i * 2 * math.pi / sides) * r)
        for i in range(sides)
    ]

PEN = (16, 16, 22, 255)

# Central black pentagon (point-up)
pent_r = ball_r * 0.26
center_pts = reg_polygon(ball_cx, ball_cy, pent_r, 5, -math.pi / 2)
bd.polygon(center_pts, fill=PEN, outline=(0, 0, 0, 255))

# 5 outer pentagons — vertex points outward, flat edge faces center
outer_dist = pent_r * 2.45
outer_r = pent_r * 0.95
outer_groups = []
for i in range(5):
    a = i * 2 * math.pi / 5 - math.pi / 2 + math.pi / 5
    cx = ball_cx + math.cos(a) * outer_dist
    cy = ball_cy + math.sin(a) * outer_dist
    pts = reg_polygon(cx, cy, outer_r, 5, a + math.pi / 2)
    bd.polygon(pts, fill=PEN, outline=(0, 0, 0, 255))
    outer_groups.append((cx, cy, pts, a))

# White hexagons between center pentagon and outer pentagons.
# A hex is bounded by: 2 center pentagon vertices + 2 outer pentagon vertices + ...
# Approximate by drawing thin dark seam lines, which read as hexagon panel boundaries.
# Seam from each center pentagon vertex out toward the rim through a midpoint.
SEAM = (35, 35, 45, 255)
SEAM_W = 5
for i in range(5):
    p_cur = center_pts[i]
    p_next = center_pts[(i + 1) % 5]
    # adjacent outer pentagons share two vertices with this hex
    a = i * 2 * math.pi / 5 - math.pi / 2 + math.pi / 5
    cx = ball_cx + math.cos(a) * outer_dist
    cy = ball_cy + math.sin(a) * outer_dist
    outer_pts = reg_polygon(cx, cy, outer_r, 5, a + math.pi / 2)
    # the two outer-pentagon vertices "facing" the central pentagon edge
    o_a = outer_pts[3]
    o_b = outer_pts[2]
    # seam lines connecting: center-vertex -> outer-vertex (panel boundaries)
    bd.line([p_cur, o_a],  fill=SEAM, width=SEAM_W)
    bd.line([p_next, o_b], fill=SEAM, width=SEAM_W)
# seam lines off the outer pentagons toward the rim (where another hex would be)
for cx, cy, pts, a in outer_groups:
    rim_x = ball_cx + math.cos(a) * (ball_r - 4)
    rim_y = ball_cy + math.sin(a) * (ball_r - 4)
    # the outer pentagon's tip vertex points outward at index 0 (we rotated by +pi/2 so apex is at angle a)
    bd.line([pts[0], (rim_x, rim_y)], fill=SEAM, width=SEAM_W)

# Soft sphere shading
shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shade, "RGBA")
for i in range(60):
    rr = ball_r - i * 1.5
    if rr <= 0: break
    cx_off = ball_cx + i * 0.5
    cy_off = ball_cy + i * 0.5
    a = max(0, int(2 + i * 0.85))
    sd.ellipse([cx_off - rr, cy_off - rr, cx_off + rr, cy_off + rr],
               outline=(0, 0, 0, a), width=2)
shade = shade.filter(ImageFilter.GaussianBlur(radius=5))
mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(mask).ellipse([ball_cx - ball_r, ball_cy - ball_r,
                              ball_cx + ball_r, ball_cy + ball_r], fill=255)
clipped_shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
clipped_shade.paste(shade, (0, 0), mask)
ball = Image.alpha_composite(ball, clipped_shade)
bd = ImageDraw.Draw(ball, "RGBA")

# Specular highlight (top-left)
spec = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd2 = ImageDraw.Draw(spec, "RGBA")
hx = ball_cx - ball_r * 0.40
hy = ball_cy - ball_r * 0.55
sd2.ellipse([hx - ball_r * 0.30, hy - ball_r * 0.10,
             hx + ball_r * 0.30, hy + ball_r * 0.10],
            fill=(255, 255, 255, 200))
spec = spec.filter(ImageFilter.GaussianBlur(radius=10))
clipped_spec = Image.new("RGBA", (W, H), (0, 0, 0, 0))
clipped_spec.paste(spec, (0, 0), mask)
ball = Image.alpha_composite(ball, clipped_spec)
bd = ImageDraw.Draw(ball, "RGBA")
# bright glint
bd.ellipse([hx - 14, hy - 6, hx + 6, hy + 4], fill=(255, 255, 255, 240))

# Ball outline
bd.ellipse([ball_cx - ball_r, ball_cy - ball_r,
            ball_cx + ball_r, ball_cy + ball_r],
           outline=(15, 15, 22, 255), width=4)

# Drop shadow
ball_shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bsd = ImageDraw.Draw(ball_shadow, "RGBA")
sx, sy = ball_cx, ball_cy + ball_r + 18
bsd.ellipse([sx - ball_r * 0.95, sy - ball_r * 0.18,
             sx + ball_r * 0.95, sy + ball_r * 0.18],
            fill=(0, 0, 0, 130))
ball_shadow = ball_shadow.filter(ImageFilter.GaussianBlur(radius=12))
img = Image.alpha_composite(img, ball_shadow)
img = Image.alpha_composite(img, ball)

# ============================================================
# 4. Title text — gold gradient "ROBOT SOCCER" at the bottom
# ============================================================
def find_font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

title = "ROBOT SOCCER"
tdraw = ImageDraw.Draw(img, "RGBA")

# auto-fit font: shrink until the text + stroke fit within max_w
max_w = int(W * 0.86)
font_size = 130
font = find_font(font_size)
stroke_w = 10
while True:
    bbox = tdraw.textbbox((0, 0), title, font=font, stroke_width=stroke_w)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    if tw <= max_w or font_size <= 60: break
    font_size -= 4
    font = find_font(font_size)

text_y_center = int(H * 0.93)
text_x = (W - tw) // 2 - bbox[0]
text_y = text_y_center - th // 2 - bbox[1]

# 1. White-fill base + black stroke
base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(base).text((text_x, text_y), title, font=font,
                          fill=(255, 255, 255, 255),
                          stroke_width=stroke_w, stroke_fill=(20, 20, 20, 255))
# 2. Gold vertical gradient (top: light gold, bottom: deep amber)
y_top = text_y - 4
y_bot = text_y + th + 4
grad_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gp = grad_layer.load()
for yy in range(H):
    if yy < y_top:
        c = (255, 240, 150, 255)
    elif yy > y_bot:
        c = (180, 110, 14, 255)
    else:
        t = (yy - y_top) / max(1, y_bot - y_top)
        r = int(lerp(255, 180, t))
        g = int(lerp(240, 110, t))
        b = int(lerp(150, 14, t))
        c = (r, g, b, 255)
    for xx in range(W):
        gp[xx, yy] = c

# 3. Mask the gradient by base's *interior* (white pixels only) — leaves
#    stroke + AA edges as-is, fills interior with gradient.
base_px  = base.load()
grad_px  = grad_layer.load()
out_text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
out_px   = out_text.load()
for yy in range(max(0, text_y - 30), min(H, text_y + th + 30)):
    for xx in range(W):
        br, bg, bb, ba = base_px[xx, yy]
        if ba == 0:
            continue
        # white interior of glyphs → fill with gradient (preserve alpha)
        if br > 235 and bg > 235 and bb > 235:
            gr, gg2, gb, _ = grad_px[xx, yy]
            out_px[xx, yy] = (gr, gg2, gb, ba)
        else:
            # stroke / antialiased edge — keep as-is (black + white AA blend stays)
            out_px[xx, yy] = (br, bg, bb, ba)
img = Image.alpha_composite(img, out_text)

# ============================================================
# Save
# ============================================================
out_path = sys.argv[1] if len(sys.argv) > 1 else "AppIcon-512@2x.png"
img.convert("RGB").save(out_path, "PNG", optimize=True)
print(f"wrote {out_path} ({W}x{H}) {os.path.getsize(out_path)} bytes")
