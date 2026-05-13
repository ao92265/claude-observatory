"""Generate viva-cover.png at 1600x900 directly with Pillow (no SVG rasterizer needed)."""
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


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/Library/Fonts/Menlo.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


# --- Build canvas ---
img = Image.new("RGB", (W, H), BG_MID)
draw = ImageDraw.Draw(img)

# Vertical gradient background
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

# Starfield
import random
random.seed(7)
for _ in range(140):
    x = random.randint(0, W - 1)
    y = random.randint(0, H - 1)
    r = random.choice([1, 1, 1, 2])
    alpha = random.randint(80, 220)
    c = (255, 255, 255, alpha)
    star = Image.new("RGBA", (r * 3, r * 3), (0, 0, 0, 0))
    sd = ImageDraw.Draw(star)
    sd.ellipse([0, 0, r * 2, r * 2], fill=c)
    img.paste(star, (x, y), star)

# Glow halo around dome (right side)
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([900, 280, 1580, 960], fill=(88, 166, 255, 60))
glow = glow.filter(ImageFilter.GaussianBlur(60))
img.paste(glow, (0, 0), glow)

# --- Observatory (right) ---
ox, oy = 1240, 620
# Base platform
draw.rounded_rectangle([ox - 180, oy, ox + 180, oy + 50], radius=6, fill=PANEL, outline=BORDER, width=2)
# Pillars
draw.rectangle([ox - 165, oy - 10, ox - 145, oy + 60], fill=(31, 39, 51))
draw.rectangle([ox + 145, oy - 10, ox + 165, oy + 60], fill=(31, 39, 51))
# Dome (half-circle on top)
draw.pieslice([ox - 160, oy - 160, ox + 160, oy + 160], 180, 360, fill=(31, 39, 51), outline=BLUE, width=3)
# Dome slit
draw.polygon([(ox - 18, oy - 158), (ox + 18, oy - 158), (ox + 14, oy), (ox - 14, oy)], fill=BG_TOP)
draw.line([(ox - 18, oy - 158), (ox - 14, oy)], fill=BLUE, width=2)
draw.line([(ox + 18, oy - 158), (ox + 14, oy)], fill=BLUE, width=2)
# Telescope barrel (tilted)
import math
angle = math.radians(-22)
cx, cy = ox, oy - 80
tl = 200
tw = 18
dx, dy = math.cos(angle), math.sin(angle)
px, py = -math.sin(angle) * tw / 2, math.cos(angle) * tw / 2
ax, ay = cx + dx * tl, cy + dy * tl
draw.polygon(
    [
        (cx + px, cy + py),
        (cx - px, cy - py),
        (ax - px, ay - py),
        (ax + px, ay + py),
    ],
    fill=PANEL,
    outline=ORANGE,
)
draw.ellipse([ax - 16, ay - 16, ax + 16, ay + 16], fill=BG_TOP, outline=ORANGE, width=3)
draw.ellipse([ax - 7, ay - 7, ax + 7, ay + 7], fill=ORANGE)


def panel(x: int, y: int, w: int, h: int, title: str, lines: list[tuple[str, tuple[int, int, int]]]) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=PANEL, outline=BORDER, width=2)
    draw.rounded_rectangle([x, y, x + w, y + 30], radius=10, fill=PANEL_HEAD)
    draw.rectangle([x, y + 20, x + w, y + 30], fill=PANEL_HEAD)
    draw.ellipse([x + 10, y + 10, x + 22, y + 22], fill=RED)
    draw.ellipse([x + 28, y + 10, x + 40, y + 22], fill=YELLOW)
    draw.ellipse([x + 46, y + 10, x + 58, y + 22], fill=GREEN)
    draw.text((x + 72, y + 9), title, fill=DIM, font=font(13))
    for i, (txt, col) in enumerate(lines):
        draw.text((x + 16, y + 50 + i * 22), txt, fill=col, font=font(14))


# --- Three terminal panels ---
panel(
    80, 250, 360, 170, "observatory cost",
    [
        ("$ observatory cost --days 7", BLUE),
        ("263 sessions  $8,197.05 spent", FG),
        ("10 opus-on-trivial flagged", ORANGE),
        ("$443.10/mo savings available", GREEN),
        ("─────────────────────────────", DIM),
    ],
)
panel(
    150, 450, 400, 195, "healthcheck suggest",
    [
        ("[model-downgrade]   conf 60%", BLUE),
        ("opus-4-7 → sonnet-4-6", FG),
        ("est $46.73/mo", GREEN),
        ("", FG),
        ("[claude-md-rule]    conf 55%", BLUE),
        ("→ MUST/WILL/NEVER", ORANGE),
    ],
)

# Cache hit bar chart
cx, cy = 60, 690
panel(cx, cy, 300, 150, "cache hit rate · 30d", [])
bars = [60, 80, 100, 110, 106, 114, 116]
for i, h in enumerate(bars):
    x0 = cx + 28 + i * 36
    color = BLUE if i < 3 else GREEN
    draw.rounded_rectangle([x0, cy + 140 - h, x0 + 24, cy + 140], radius=3, fill=color)
draw.text((cx + 230, cy + 80), "94.2%", fill=GREEN, font=font(16))

# --- Title block ---
# Top kicker
kicker = "— LOCAL-FIRST OBSERVABILITY FOR CLAUDE CODE —"
kf = font(18)
kw = draw.textlength(kicker, font=kf)
draw.text(((W - kw) / 2, 70), kicker, fill=BLUE, font=kf)

# Main title
title = "CLAUDE OBSERVATORY"
tf = font(80, bold=True)
tw = draw.textlength(title, font=tf)
draw.text(((W - tw) / 2, 130), title, fill=FG, font=tf)

# Subtitle
sub = "See what your AI coding agent is doing. Cut what you don't need."
sf = font(20)
sw = draw.textlength(sub, font=sf)
draw.text(((W - sw) / 2, 220), sub, fill=DIM, font=sf)

# --- Bottom pills ---
def pill(x: int, y: int, label: str, color: tuple[int, int, int]) -> None:
    w = int(draw.textlength(label, font=font(16)) + 36)
    draw.rounded_rectangle([x, y, x + w, y + 36], radius=18, fill=PANEL, outline=color, width=2)
    draw.text((x + 18, y + 9), label, fill=color, font=font(16))


pill(620, 820, "🩺 HealthDoctor", GREEN)
pill(820, 820, "❤  HealthCheck", ORANGE)

# Bottom-right footer
foot = "github.com/ao92265/claude-observatory · v0.1.0"
ff = font(13)
fw = draw.textlength(foot, font=ff)
draw.text((W - fw - 30, H - 30), foot, fill=DIM, font=ff)

img.save(OUT, "PNG", optimize=True)
print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
