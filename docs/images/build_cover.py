"""Generate viva-cover.png at 1600x900 with Pillow. No SVG rasterizer needed."""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1600, 900
OUT = Path(__file__).parent / "viva-cover.png"

# Palette (GitHub dark + accents)
BG_TOP = (10, 14, 26)
BG_MID = (13, 21, 37)
BG_BOT = (5, 8, 16)
FG = (240, 246, 252)
DIM = (139, 148, 158)
BORDER = (48, 54, 61)
PANEL = (22, 27, 34)
PANEL_HEAD = (33, 38, 45)
BLUE = (88, 166, 255)
ORANGE = (255, 166, 87)
GREEN = (126, 231, 135)
RED = (248, 81, 73)
YELLOW = (210, 153, 34)


def font(size: int) -> ImageFont.FreeTypeFont:
    for p in (
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
    ):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, txt: str, f: ImageFont.FreeTypeFont) -> int:
    return int(draw.textlength(txt, font=f))


# --- Build canvas ---
img = Image.new("RGB", (W, H), BG_MID)
draw = ImageDraw.Draw(img)

# Vertical gradient
for y in range(H):
    t = y / H
    if t < 0.5:
        u = t * 2
        r = int(BG_TOP[0] * (1 - u) + BG_MID[0] * u)
        g = int(BG_TOP[1] * (1 - u) + BG_MID[1] * u)
        b = int(BG_TOP[2] * (1 - u) + BG_MID[2] * u)
    else:
        u = (t - 0.5) * 2
        r = int(BG_MID[0] * (1 - u) + BG_BOT[0] * u)
        g = int(BG_MID[1] * (1 - u) + BG_BOT[1] * u)
        b = int(BG_MID[2] * (1 - u) + BG_BOT[2] * u)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Starfield (avoid the central title band 60-280)
random.seed(7)
for _ in range(160):
    x = random.randint(0, W - 1)
    y = random.randint(0, H - 1)
    if 280 < y < 380 and 200 < x < 1400:
        continue  # keep subtitle area clean
    r = random.choice([1, 1, 1, 2])
    a = random.randint(80, 220)
    s = Image.new("RGBA", (r * 3, r * 3), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse([0, 0, r * 2, r * 2], fill=(255, 255, 255, a))
    img.paste(s, (x, y), s)

# Glow halo around dome
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([920, 360, 1560, 940], fill=(88, 166, 255, 55))
glow = glow.filter(ImageFilter.GaussianBlur(70))
img.paste(glow, (0, 0), glow)

# --- Observatory (right) ---
ox, oy = 1260, 700
draw.rounded_rectangle([ox - 180, oy, ox + 180, oy + 50], radius=6, fill=PANEL, outline=BORDER, width=2)
draw.rectangle([ox - 165, oy - 10, ox - 145, oy + 60], fill=(31, 39, 51))
draw.rectangle([ox + 145, oy - 10, ox + 165, oy + 60], fill=(31, 39, 51))
draw.pieslice([ox - 160, oy - 160, ox + 160, oy + 160], 180, 360, fill=(31, 39, 51), outline=BLUE, width=3)
draw.polygon([(ox - 18, oy - 158), (ox + 18, oy - 158), (ox + 14, oy), (ox - 14, oy)], fill=BG_TOP)
draw.line([(ox - 18, oy - 158), (ox - 14, oy)], fill=BLUE, width=2)
draw.line([(ox + 18, oy - 158), (ox + 14, oy)], fill=BLUE, width=2)
# Telescope barrel
angle = math.radians(-25)
cx, cy = ox, oy - 80
tl, tw = 210, 18
dx, dy = math.cos(angle), math.sin(angle)
px, py = -math.sin(angle) * tw / 2, math.cos(angle) * tw / 2
ax, ay = cx + dx * tl, cy + dy * tl
draw.polygon(
    [(cx + px, cy + py), (cx - px, cy - py), (ax - px, ay - py), (ax + px, ay + py)],
    fill=PANEL,
    outline=ORANGE,
)
draw.ellipse([ax - 16, ay - 16, ax + 16, ay + 16], fill=BG_TOP, outline=ORANGE, width=3)
draw.ellipse([ax - 7, ay - 7, ax + 7, ay + 7], fill=ORANGE)


def panel(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    lines: list[tuple[str, tuple[int, int, int]]],
    line_h: int = 24,
    pad_top: int = 50,
) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=PANEL, outline=BORDER, width=2)
    draw.rounded_rectangle([x, y, x + w, y + 30], radius=10, fill=PANEL_HEAD)
    draw.rectangle([x, y + 20, x + w, y + 30], fill=PANEL_HEAD)
    draw.ellipse([x + 10, y + 10, x + 22, y + 22], fill=RED)
    draw.ellipse([x + 28, y + 10, x + 40, y + 22], fill=YELLOW)
    draw.ellipse([x + 46, y + 10, x + 58, y + 22], fill=GREEN)
    draw.text((x + 72, y + 9), title, fill=DIM, font=font(13))
    for i, (txt, col) in enumerate(lines):
        draw.text((x + 18, y + pad_top + i * line_h), txt, fill=col, font=font(14))


# --- Three terminal panels (left side, vertically spaced, no overlap) ---
panel(
    80, 380, 380, 170, "observatory cost",
    [
        ("$ observatory cost --days 7", BLUE),
        ("263 sessions  $8,197 spent", FG),
        ("10 opus-on-trivial flagged", ORANGE),
        ("$443/mo savings available", GREEN),
    ],
)
panel(
    80, 570, 380, 170, "healthcheck suggest",
    [
        ("[model-downgrade]  conf 60%", BLUE),
        ("opus-4-7 -> sonnet-4-6", FG),
        ("est $46.73/mo", GREEN),
        ("[claude-md-rule]   conf 55%", BLUE),
        ("-> MUST / WILL / NEVER", ORANGE),
    ],
    line_h=22,
)

# Cache chart panel (bottom-left, distinct from terminal panels)
cx, cy, cw, ch = 80, 760, 380, 110
draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=10, fill=PANEL, outline=BORDER, width=2)
draw.text((cx + 16, cy + 14), "cache hit rate · 30d", fill=DIM, font=font(13))
# bars
bar_top, bar_base = cy + 40, cy + 92
bar_w, gap = 22, 14
heights = [28, 36, 44, 48, 46, 50, 52]
start_x = cx + 24
for i, h in enumerate(heights):
    x0 = start_x + i * (bar_w + gap)
    color = BLUE if i < 3 else GREEN
    draw.rounded_rectangle([x0, bar_base - h, x0 + bar_w, bar_base], radius=3, fill=color)
# 94.2% label — placed RIGHT of bars, not on top
label = "94.2%"
lf = font(20)
draw.text((cx + cw - text_width(draw, label, lf) - 18, cy + 50), label, fill=GREEN, font=lf)

# --- Title ---
kicker = "LOCAL-FIRST OBSERVABILITY FOR CLAUDE CODE"
kf = font(18)
kw = text_width(draw, kicker, kf)
draw.text(((W - kw) / 2, 90), kicker, fill=BLUE, font=kf)

title = "CLAUDE OBSERVATORY"
tf = font(80)
tw_ = text_width(draw, title, tf)
draw.text(((W - tw_) / 2, 150), title, fill=FG, font=tf)

sub = "See what your AI coding agent is doing.  Cut what you don't need."
sf = font(20)
sw = text_width(draw, sub, sf)
draw.text(((W - sw) / 2, 250), sub, fill=DIM, font=sf)

# --- Bottom pills (no emoji — fonts may not render glyphs) ---
def pill(cx_: int, y: int, label: str, color: tuple[int, int, int]) -> int:
    f = font(17)
    w = text_width(draw, label, f) + 40
    draw.rounded_rectangle([cx_, y, cx_ + w, y + 40], radius=20, fill=PANEL, outline=color, width=2)
    draw.text((cx_ + 20, y + 11), label, fill=color, font=f)
    return w


# Center the two pills horizontally
pf = font(17)
w1 = text_width(draw, "HealthDoctor  — live timeline", pf) + 40
w2 = text_width(draw, "HealthCheck  — auto-optimizer", pf) + 40
total = w1 + 24 + w2
x1 = (W - total) // 2
pill(x1, 820, "HealthDoctor  — live timeline", GREEN)
pill(x1 + w1 + 24, 820, "HealthCheck  — auto-optimizer", ORANGE)

# Footer (lighter, no overlap with right edge)
foot = "github.com/ao92265/claude-observatory  ·  v0.1.0"
ff = font(13)
draw.text((W - text_width(draw, foot, ff) - 30, H - 28), foot, fill=DIM, font=ff)

img.save(OUT, "PNG", optimize=True)
print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
