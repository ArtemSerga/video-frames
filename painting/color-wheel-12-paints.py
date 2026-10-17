import itertools
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
source = Image.open(os.path.join(HERE, "color-wheel-12-source.jpg")).convert("RGB")
SCX, SCY = 510, 507
S = 2
wheel = source.resize((source.width * S, source.height * S), Image.Resampling.LANCZOS)
HALF = 468
wheel = wheel.crop(((SCX - HALF) * S, (SCY - HALF) * S, (SCX + HALF) * S, (SCY + HALF) * S))

bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
f_leg = ImageFont.truetype(bold, 28)
f_dot = ImageFont.truetype(bold, 26)
DOT = 30

# Names sit above the wheel, in Itten order. Whites close the list.
legend = [
    "Lemon Yellow",
    "Cadmium Yellow Hue",
    "Yellow Ochre",
    "Burnt Sienna",
    "Cadmium Red Hue",
    "Permanent Alizarin Crimson",
    "French Ultramarine",
    "Phthalo Blue (Red Shade)",
    "Cerulean Blue Hue",
    "Phthalo Green (Blue Shade)",
    "Burnt Umber",
    "Titanium White",
    "Zinc White",
]
# Legend caption: temperature and transparency from the palette cards. The AA/A
# tube mark is lightfastness, not transparency.
TAGS = {
    "Lemon Yellow": "холодный · полупрозрачный",
    "Cadmium Yellow Hue": "тёплый · полупрозрачный",
    "Yellow Ochre": "тёплый · кроющий",
    "Burnt Sienna": "тёплый · прозрачный",
    "Cadmium Red Hue": "тёплый · полупрозрачный",
    "Permanent Alizarin Crimson": "холодный · прозрачный",
    "French Ultramarine": "тёплый, в фиолет · прозрачный",
    "Phthalo Blue (Red Shade)": "холодный · прозрачный",
    "Cerulean Blue Hue": "холодный · полукроющий",
    "Phthalo Green (Blue Shade)": "холодный · прозрачный",
    "Burnt Umber": "прохладный · прозрачный",
    "Titanium White": "нейтральный · кроющий",
    "Zinc White": "нейтральный · полупрозрачный",
}
f_tag = ImageFont.truetype(reg, 21)
f_code = ImageFont.truetype(bold, 26)
left_pad, right_pad = 40, 40
canvas_w = wheel.width + left_pad + right_pad
measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
legend_rows, row, used = [], [], 0
for name in legend:
    w = 2 * DOT + 12 + max(measure.textlength(name, font=f_leg), measure.textlength(TAGS[name], font=f_tag))
    if row and used + w > canvas_w - 40:
        legend_rows.append(row)
        row, used = [], 0
    row.append((name, w))
    used += w + 30
legend_rows.append(row)
LEG_STEP = 2 * DOT + 24
top_pad = 16 + len(legend_rows) * LEG_STEP + 56
bot_pad = 375 + 230
img = Image.new("RGB", (canvas_w, wheel.height + top_pad + bot_pad), (255, 255, 255))
img.paste(wheel, (left_pad, top_pad))

cx = left_pad + HALF * S
cy = top_pad + HALF * S

# The Spanish names sit outside the coloured disc. Keep the disc, paint the rest white.
keep = 466 * S
mask = Image.new("L", img.size, 0)
ImageDraw.Draw(mask).ellipse((cx - keep, cy - keep, cx + keep, cy + keep), fill=255)
img = Image.composite(img, Image.new("RGB", img.size, (255, 255, 255)), mask)
d = ImageDraw.Draw(img)

# Display colour, mixing colour and tinting strength. Strength scales how far
# one part pushes the mix: phthalos and alizarin are dyes, cerulean is weak.
PAINTS = {
    "Titanium White": ((250, 250, 247), (250, 250, 247), 1.0),
    # Zinc oxide tints far weaker than titanium dioxide; both Artisan tubes are
    # PW4/PW6 blends, so take the gap as about 2.5x rather than the pigment's 5-6x.
    "Zinc White": ((200, 212, 228), (246, 247, 248), 0.4),
    "Lemon Yellow": ((246, 232, 40), (247, 230, 30), 0.8),
    "Cadmium Yellow Hue": ((250, 182, 20), (250, 172, 12), 1.0),
    "Yellow Ochre": ((198, 148, 52), (196, 140, 50), 0.8),
    "Burnt Sienna": ((150, 66, 30), (150, 62, 28), 1.0),
    "Burnt Umber": ((86, 56, 40), (78, 54, 40), 1.2),
    # A PR188 scarlet: leans orange, so a true red needs a touch of alizarin.
    "Cadmium Red Hue": ((224, 50, 30), (226, 52, 26), 1.2),
    "Permanent Alizarin Crimson": ((150, 18, 52), (150, 14, 50), 2.0),
    "French Ultramarine": ((38, 50, 160), (32, 38, 150), 1.2),
    "Cerulean Blue Hue": ((44, 146, 210), (40, 145, 205), 0.6),
    "Phthalo Blue (Red Shade)": ((18, 36, 110), (12, 46, 130), 4.0),
    "Phthalo Green (Blue Shade)": ((0, 112, 84), (0, 112, 86), 4.0),
}
SOLVER = list(PAINTS)
WHITES = {SOLVER.index("Titanium White"), SOLVER.index("Zinc White")}
# Zinc matches Titanium at 2.5x the parts; the model cannot see its one advantage, chroma.
WHEEL_EXCLUDED = {SOLVER.index("Zinc White")}


def srgb_to_lin(c):
    c = np.asarray(c, dtype=float) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_lab(lin):
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


# Subtractive mixing as a weighted geometric mean of reflectance.
LOG_R = np.log(np.clip(srgb_to_lin([PAINTS[n][1] for n in SOLVER]), 0.004, 1))
STRENGTH = np.array([PAINTS[n][2] for n in SOLVER])
PARTS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20]

recipes, labs, sizes, complexity = [], [], [], []
for k in (1, 2, 3):
    for combo in itertools.combinations(range(len(SOLVER)), k):
        if WHEEL_EXCLUDED & set(combo):
            continue
        grids = itertools.product(PARTS, repeat=k) if k > 1 else [(1,)]
        for parts in grids:
            if k > 1 and math.gcd(*parts) != 1:
                continue
            # Only white is measured in large piles; a colour above 12 parts is a drop of the other.
            if any(p > 12 and j not in WHITES for j, p in zip(combo, parts)):
                continue
            w = np.array(parts, float) * STRENGTH[list(combo)]
            lr = (w[:, None] * LOG_R[list(combo)]).sum(0) / w.sum()
            recipes.append(tuple(zip(combo, parts)))
            labs.append(np.exp(lr))
            sizes.append(k)
            # Small round numbers are what can actually be measured on a palette.
            complexity.append(sum(0 if p in (1, 2, 3, 4) else 0.6 if p in (6, 8) else 1.2 for p in parts))
labs = lin_to_lab(np.array(labs))
chroma = np.hypot(labs[:, 1], labs[:, 2])
has_white = np.array([any(j in WHITES for j, _ in r) for r in recipes])
hue = np.degrees(np.arctan2(labs[:, 2], labs[:, 1])) % 360
sizes = np.array(sizes)
complexity = np.array(complexity)
print("candidate mixes", len(recipes))

# Ring bounds in source pixels, outer to inner.
RING_BOUNDS = [(401, 454), (346, 399), (292, 344), (234, 290), (187, 232), (132, 185), (62, 128)]
# Wedge bisectors measured on this image, clockwise from the top.
WEDGE_ANG = [312, 338, 12, 46, 72, 100, 132, 162, 192, 222, 250, 278]


def cell_sample(ang, rin, rout):
    px = source.load()
    vals = []
    for t in np.linspace(-9, 9, 7):
        for r in np.linspace(rin + 6, rout - 6, 5):
            a = math.radians(ang + t)
            x, y = int(SCX + r * math.sin(a)), int(SCY - r * math.cos(a))
            vals.append(px[x, y])
    return np.median(np.array(vals), axis=0)


L_FLOOR = float(labs[:, 0].min()) + 1
KNEE = 22.0
print("darkest mix L", round(L_FLOOR - 1, 1))


def reachable_lightness(lstar):
    # The screen goes down to black; the darkest tube mix stops near L_FLOOR.
    # Squeeze everything under KNEE into the reachable range so order survives.
    if lstar >= KNEE:
        return lstar
    return L_FLOOR + lstar * (KNEE - L_FLOOR) / KNEE


def gamut_distance(target):
    # Screen primaries are more saturated than any tube. Clip the target's chroma
    # to the most the owned paints reach at that hue and lightness, then match
    # normally: a mix that dulls below that reach is still penalised.
    tl, ta, tb = target
    tl = reachable_lightness(tl)
    tc = math.hypot(ta, tb)
    th = math.degrees(math.atan2(tb, ta)) % 360
    near = (np.abs((hue - th + 180) % 360 - 180) < 8) & (np.abs(labs[:, 0] - tl) < 8)
    reach = float(chroma[near].max()) if near.any() else tc
    tc = min(tc, reach)
    ta, tb = tc * math.cos(math.radians(th)), tc * math.sin(math.radians(th))
    dl = labs[:, 0] - tl
    dc = chroma - tc
    dh2 = np.clip((labs[:, 1] - ta) ** 2 + (labs[:, 2] - tb) ** 2 - dc ** 2, 0, None)
    sc = 1 + 0.045 * tc
    sh = 1 + 0.015 * tc
    return np.sqrt(dl ** 2 + (dc / sc) ** 2 + dh2 / sh ** 2)


def best_recipe(rgb, ring, darker_than=None, lighter_than=None, avoid=()):
    target = lin_to_lab(srgb_to_lin(rgb)[None])[0]
    cost = gamut_distance(target)
    de = cost.copy()
    # Prefer fewer tubes unless the extra one really earns its place.
    cost += (sizes - 1) * 1.2 + 0.5 * complexity
    # Outer three rings are tints. The pure ring and the shades take no white.
    if ring >= 3:
        cost[has_white] += 50
    if darker_than is not None:
        cost[labs[:, 0] > darker_than - 1.0] += 50
    if lighter_than is not None:
        cost[labs[:, 0] < lighter_than + 1.0] += 50
    for i in avoid:
        cost[i] += 3
    i = int(np.argmin(cost))
    parts = {SOLVER[j]: p for j, p in recipes[i]}
    return parts, de[i], labs[i], i


def outward(ang):
    a = math.radians(ang)
    return math.sin(a), -math.cos(a)


def cell_angle(x, y):
    return math.degrees(math.atan2(x - cx, -(y - cy))) % 360


def angle_off(a, b):
    v = (a - b) % 360
    return v - 360 if v > 180 else v


def in_cell(x, y, ang, rin, rout):
    radius = math.hypot(x - cx, y - cy) / S
    if not (rin + 3 <= radius <= rout - 3):
        return False
    return abs(angle_off(cell_angle(x, y), ang)) <= 13


def widest_horizontal(ang, rin, rout):
    reach = int(rout * S) + 4
    best = (0, cy, cx, cx)
    for y in range(int(cy - reach), int(cy + reach), 3):
        run, start = False, 0
        for x in range(int(cx - reach), int(cx + reach), 3):
            inside = in_cell(x, y, ang, rin, rout)
            if inside and not run:
                start, run = x, True
            elif run and not inside:
                if x - start > best[0]:
                    best = (x - start, y, start, x)
                run = False
    return best


def dot_ink(color):
    lum = 0.3 * color[0] + 0.59 * color[1] + 0.11 * color[2]
    return (25, 25, 25) if lum > 160 else (255, 255, 255)


# Shape is temperature: the one property that separates both lookalike groups.
# Circle warm, square cold, hexagon cool or neutral.
TEMPERATURE = {
    "Lemon Yellow": "square",
    "Cadmium Yellow Hue": "circle",
    "Yellow Ochre": "circle",
    "Burnt Sienna": "circle",
    "Cadmium Red Hue": "circle",
    "Permanent Alizarin Crimson": "square",
    "French Ultramarine": "circle",
    "Phthalo Blue (Red Shade)": "square",
    "Cerulean Blue Hue": "square",
    "Phthalo Green (Blue Shade)": "square",
    "Burnt Umber": "hex",
    "Titanium White": "hex",
    "Zinc White": "hex",
}


def shape_at(kind, x, y, r):
    # Equal area with a circle of radius r, so no shape reads as a bigger share.
    if kind == "square":
        h = r * math.sqrt(math.pi) / 2
        return [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)]
    R = r * math.sqrt(2 * math.pi / (3 * math.sqrt(3)))
    return [(x + R * math.cos(math.radians(60 * i - 90)),
             y + R * math.sin(math.radians(60 * i - 90))) for i in range(6)]


def draw_outline(kind, x, y, r, color, width, fill=None):
    if kind == "circle":
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=color, width=width)
    else:
        d.polygon(shape_at(kind, x, y, r), fill=fill, outline=color, width=width)


def draw_mark(x, y, name, label, font, r):
    color = PAINTS[name][0]
    draw_outline(TEMPERATURE[name], x, y, r, (25, 25, 25), 2, fill=color)
    if label:
        d.text((x, y), str(label), font=font, fill=dot_ink(color), anchor="mm")


PLACED = []


def paint_dot(x, y, name, share):
    PLACED.append((x, y, CURRENT_CELL))
    draw_mark(x, y, name, share, f_dot, DOT)


def wrap(words, font, limit):
    lines, line = [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if line and d.textlength(trial, font=font) > limit:
            lines.append(line)
            line = w
        else:
            line = trial
    lines.append(line)
    return lines


def write_name(name, x0, x1, y_line, rgb):
    limit = (x1 - x0) * 0.86
    for size in range(26, 13, -1):
        font = ImageFont.truetype(bold, size)
        lines = wrap(name.split(), font, limit)
        if max(d.textlength(t, font=font) for t in lines) <= limit:
            break
    lum = 0.3 * rgb[0] + 0.59 * rgb[1] + 0.11 * rgb[2]
    ink, halo = ((20, 20, 20), (255, 255, 255)) if lum > 150 else ((255, 255, 255), (15, 15, 15))
    line_h = size + 4
    y = y_line - line_h * len(lines) / 2
    for t in lines:
        d.text(((x0 + x1) / 2, y + line_h / 2), t, font=font, fill=ink, anchor="mm",
               stroke_width=2, stroke_fill=halo)
        y += line_h


def draw_cell(ang, ring, parts, rgb):
    rin, rout = RING_BOUNDS[ring]
    span, y_line, x0, x1 = widest_horizontal(ang, rin, rout)
    if len(parts) == 1:
        write_name(next(iter(parts)), x0, x1, y_line, rgb)
        return
    items = sorted(parts.items(), key=lambda kv: -kv[1])
    n = len(items)
    step = 2 * DOT + 5
    rmid = (rin + rout) / 2 * S
    ox, oy = outward(ang)
    tx, ty = -oy, ox

    layouts = []
    width = n * step - 5
    if width <= span * 0.92:
        x = (x0 + x1) / 2 - width / 2 + DOT
        layouts.append([(x + j * step, y_line) for j in range(n)])
    # Rows along the arc, stacked along the radius, nudged in and out.
    for per_row in range(n, 0, -1):
        rows = [list(range(i, min(i + per_row, n))) for i in range(0, n, per_row)]
        for shift in (0, -8, 8, -16, 16, -24, 24, -32, 32):
            for tshift in (0, -12, 12, -24, 24):
                pts = []
                r0 = rmid + (len(rows) - 1) * (step - 2) / 2 + shift
                for k, row in enumerate(rows):
                    rr = r0 - k * (step - 2)
                    for j in range(len(row)):
                        t = (j - (len(row) - 1) / 2) * step + tshift
                        pts.append((cx + rr * ox + t * tx, cy + rr * oy + t * ty))
                layouts.append(pts)

    def score(pts):
        clash = sum(1 for x, y in pts for px, py, _ in PLACED if math.hypot(x - px, y - py) < 2 * DOT + 2)
        outside = sum(1 for x, y in pts if not in_cell(x, y, ang, rin - 6, rout + 6))
        rx, ry = cx + rmid * ox, cy + rmid * oy
        drift = sum(math.hypot(x - rx, y - ry) for x, y in pts) / len(pts)
        return clash * 1000 + outside * 40 + drift * 0.1

    best = min(layouts, key=score)
    for (x, y), (name, share) in zip(best, items):
        paint_dot(x, y, name, share)


report = []
used = {}
for ang in WEDGE_ANG:
    prev_target, prev_mix = None, None
    for ring, (rin, rout) in enumerate(RING_BOUNDS):
        rgb = cell_sample(ang, rin, rout)
        target = lin_to_lab(srgb_to_lin(rgb)[None])[0]
        # Rings run light to dark; a visibly darker ring must get a darker mix.
        darker = prev_mix if prev_target is not None and target[0] < prev_target - 2 else None
        # A recipe already given to a visibly different cell is discouraged here.
        avoid = [i for i, lab in used.items() if np.linalg.norm(lab - target) > 4]
        parts, err, mix, idx = best_recipe(rgb, ring, darker_than=darker, avoid=avoid)
        used.setdefault(idx, target)
        prev_target, prev_mix = target[0], mix[0]
        report.append((ang, ring, tuple(int(v) for v in rgb), parts, round(float(err), 1),
                       round(float(target[0])), round(float(mix[0]))))
        CURRENT_CELL = (ang, ring)
        draw_cell(ang, ring, parts, rgb)

for i, (x1, y1, c1) in enumerate(PLACED):
    for x2, y2, c2 in PLACED[i + 1:]:
        if math.hypot(x1 - x2, y1 - y2) < 2 * DOT - 2:
            print("OVERLAP", c1, c2, round(math.hypot(x1 - x2, y1 - y2)))

# Two cells that look different on the wheel must not share a recipe.
seen = {}
for ang, ring, rgb, parts, err, tl, ml in report:
    key = tuple(sorted(parts.items()))
    seen.setdefault(key, []).append((ang, ring, rgb))
for key, cells in seen.items():
    if len(cells) > 1:
        labs_c = [lin_to_lab(srgb_to_lin(c[2])[None])[0] for c in cells]
        spread = max(np.linalg.norm(a - b) for a in labs_c for b in labs_c)
        print("SHARED", dict(key), [(a, r) for a, r, _ in cells], "spread dE", round(float(spread), 1))

y = 16 + DOT
for row in legend_rows:
    x = (img.width - (sum(w for _, w in row) + 30 * (len(row) - 1))) / 2
    for name, w in row:
        draw_mark(x + DOT, y, name, None, f_dot, DOT)
        d.text((x + 2 * DOT + 12, y - 12), name, font=f_leg, fill=(20, 20, 20), anchor="lm")
        d.text((x + 2 * DOT + 12, y + 18), TAGS[name], font=f_tag, fill=(95, 95, 95), anchor="lm")
        x += w + 30
    y += LEG_STEP

# Shape key, drawn with the shapes themselves.
key = [("Форма — теплота:", None), ("тёплый", "circle"), ("холодный", "square"),
       ("прохладный и нейтральный", "hex")]
widths = [d.textlength(t, font=f_code) + (44 if k else 0) for t, k in key]
x = (img.width - sum(widths) - 36 * (len(key) - 1)) / 2
ky = y - DOT + 12
for (text, kind), w in zip(key, widths):
    if kind:
        draw_outline(kind, x + 15, ky, 15, (25, 25, 25), 2, fill=(200, 200, 200))
        d.text((x + 44, ky), text, font=f_code, fill=(40, 40, 40), anchor="lm")
    else:
        d.text((x, ky), text, font=f_code, fill=(40, 40, 40), anchor="lm")
    x += w + 36

# Ten-step grey scale from Titanium White and the umber-ultramarine black.
# Single-constant Kubelka-Munk: K/S mixes linearly with the share of paint.
def v_to_y(v):
    lstar = 10 * v
    return ((lstar + 16) / 116) ** 3


def y_to_v(y):
    return (116 * np.cbrt(y) - 16) / 10


def ks(y):
    return (1 - y) ** 2 / (2 * y)


def ks_to_y(k):
    return 1 + k - math.sqrt(k * k + 2 * k)


def grey_rgb(y):
    c = 12.92 * y if y <= 0.0031308 else 1.055 * y ** (1 / 2.4) - 0.055
    g = int(round(255 * min(1, c)))
    return (g, g, g)


def best_pair(ks_a, ks_b, target_v, top=8, top_a=None):
    best = None
    for a in range(1, (top_a or top) + 1):
        for b in range(1, top + 1):
            if math.gcd(a, b) != 1:
                continue
            v = y_to_v(ks_to_y((a * ks_a + b * ks_b) / (a + b)))
            score = abs(v - target_v) + 0.008 * (a + b)
            if best is None or score < best[0]:
                best = (score, a, b, v)
    return best[1:]


TARGETS = [9.5, 8.6, 7.7, 6.8, 5.9, 5.0, 4.2, 3.3, 2.4, 1.5]
NAMES = ["белый", "почти белый", "очень светлый серый", "светло-серый", "светлый средний серый",
         "серый", "тёмный средний серый", "тёмно-серый", "очень тёмный серый", "чёрный"]
KS_W, KS_B = ks(v_to_y(TARGETS[0])), ks(v_to_y(TARGETS[-1]))
mid_w, mid_b, mid_v = best_pair(KS_W, KS_B, 5.0, top=12)
KS_G = ks(v_to_y(mid_v))

WHITE_DOT = PAINTS["Titanium White"][0]
BLACK_DOT = (30, 30, 34)
GREY_DOT = grey_rgb(v_to_y(mid_v))
steps = []
for i, tv in enumerate(TARGETS):
    if i == 0:
        steps.append((TARGETS[0], [("Titanium White", WHITE_DOT, 1)]))
    elif i == 9:
        steps.append((TARGETS[-1], [("чёрный", BLACK_DOT, 1)]))
    elif i == 5:
        steps.append((mid_v, [("Titanium White", WHITE_DOT, mid_w), ("чёрный", BLACK_DOT, mid_b)]))
    elif i < 5:
        a, b, v = best_pair(KS_W, KS_G, tv, top=4, top_a=24)
        steps.append((v, [("Titanium White", WHITE_DOT, a), ("серый 6", GREY_DOT, b)]))
    else:
        a, b, v = best_pair(KS_G, KS_B, tv, top=4, top_a=24)
        steps.append((v, [("серый 6", GREY_DOT, a), ("чёрный", BLACK_DOT, b)]))


def table_dot(x, y, r, color, label, font, name=None):
    if name in PAINTS:
        draw_mark(x, y, name, label, font, r)
        return
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=(25, 25, 25), width=2)
    if label:
        d.text((x, y), str(label), font=font, fill=dot_ink(color), anchor="mm")


f_key = ImageFont.truetype(bold, 24)
f_small = ImageFont.truetype(reg, 20)
f_step = ImageFont.truetype(bold, 21)
f_tdot = ImageFont.truetype(bold, 22)
margin = 28
top = top_pad + wheel.height + 18

# Key: how the black and the middle grey are made.
x, y = margin, top + 20
d.text((x, y), "чёрный =", font=f_key, fill=(20, 20, 20), anchor="lm")
x += d.textlength("чёрный =", font=f_key) + 30
for name in ("Burnt Umber", "French Ultramarine"):
    table_dot(x, y, 20, PAINTS[name][0], 1, f_tdot, name)
    d.text((x + 28, y), name, font=f_key, fill=(20, 20, 20), anchor="lm")
    x += 28 + d.textlength(name, font=f_key) + 40
x += 30
d.text((x, y), "серый 6 =", font=f_key, fill=(20, 20, 20), anchor="lm")
x += d.textlength("серый 6 =", font=f_key) + 30
for name, color, share in (("Titanium White", WHITE_DOT, mid_w), ("чёрный", BLACK_DOT, mid_b)):
    table_dot(x, y, 20, color, share, f_tdot, name)
    d.text((x + 28, y), name, font=f_key, fill=(20, 20, 20), anchor="lm")
    x += 28 + d.textlength(name, font=f_key) + 40

cols = 10
col_w = (img.width - 2 * margin) / cols
sw_top = top + 50
sw_h = 150
for i, (v, recipe) in enumerate(steps):
    x0 = margin + i * col_w
    shade = grey_rgb(v_to_y(v))
    d.rectangle((x0 + 4, sw_top, x0 + col_w - 4, sw_top + sw_h), fill=shade, outline=(120, 120, 120), width=1)
    ink = (20, 20, 20) if shade[0] > 128 else (245, 245, 245)
    xm = x0 + col_w / 2
    d.text((xm, sw_top + 26), str(i + 1), font=f_key, fill=ink, anchor="mm")
    lines = wrap(NAMES[i].split(), f_step, col_w - 24)
    for j, t in enumerate(lines):
        d.text((xm, sw_top + 66 + j * 26), t, font=f_step, fill=ink, anchor="mm")
    d.text((xm, sw_top + sw_h - 20), f"V {v:.1f}", font=f_small, fill=ink, anchor="mm")

    dy = sw_top + sw_h + 42
    r = 22
    gap = 12
    width = len(recipe) * 2 * r + (len(recipe) - 1) * gap
    dx = xm - width / 2 + r
    for name, color, share in recipe:
        table_dot(dx, dy, r, color, share, f_tdot, name)
        dx += 2 * r + gap
    for j, (name, color, share) in enumerate(recipe):
        d.text((xm, dy + 44 + j * 26), f"{name} {share}" if len(recipe) > 1 else name,
               font=f_small, fill=(40, 40, 40), anchor="mm")


# Titanium against zinc, from the same mixing model.
def mix_lin(parts):
    idx = [SOLVER.index(n) for n in parts]
    w = np.array(list(parts.values()), float) * STRENGTH[idx]
    return np.exp((w[:, None] * LOG_R[idx]).sum(0) / w.sum())


def lin_to_rgb(lin):
    c = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    return tuple(int(round(255 * min(1, max(0, v)))) for v in c)


base = "French Ultramarine"
ti_parts = 4
ti_l = lin_to_lab(mix_lin({base: 1, "Titanium White": ti_parts})[None])[0][0]
zn_match = min(range(1, 25), key=lambda n: abs(lin_to_lab(mix_lin({base: 1, "Zinc White": n})[None])[0][0] - ti_l))
ratio = zn_match / ti_parts
ratio_ru = f"{ratio:.1f}".replace(".", ",")

zt = sw_top + sw_h + 160
d.text((margin, zt), "Titanium White или Zinc White", font=f_key, fill=(20, 20, 20), anchor="lm")
swatches = [
    ({base: 1, "Titanium White": ti_parts}, "Titanium"),
    ({base: 1, "Zinc White": ti_parts}, "Zinc, столько же"),
    ({base: 1, "Zinc White": zn_match}, "Zinc, тот же тон"),
]
sx, sy, sw, sh = margin, zt + 30, 250, 110
for parts, caption in swatches:
    d.rectangle((sx, sy, sx + sw, sy + sh), fill=lin_to_rgb(mix_lin(parts)), outline=(120, 120, 120))
    dx = sx + 30
    for name, share in parts.items():
        table_dot(dx, sy + 34, 22, PAINTS[name][0], share, f_tdot, name)
        dx += 56
    d.text((sx + sw / 2, sy + sh - 22), caption, font=f_small, fill=(255, 255, 255), anchor="mm",
           stroke_width=2, stroke_fill=(30, 30, 30))
    sx += sw + 18
notes = [
    f"Titanium разбеливает примерно в {ratio_ru} раза сильнее: 1 часть Titanium ≈ {ratio_ru} части Zinc.",
    "Titanium — света, блики, перекрыть. Кроет и делает цвет «мелованным».",
    "В круге везде Titanium: малые доли легче отмерить. Zinc — полупрозрачный, меньше гасит",
    f"насыщенность. Если светлый замес выглядит мелово, замените Titanium на Zinc ×{ratio_ru}.",
]
for i, t in enumerate(notes):
    d.text((sx + 10, sy + 12 + i * 28), t, font=f_small, fill=(40, 40, 40), anchor="lm")

out = os.path.join(HERE, "color-wheel-12-paints.jpg")
img.save(out, quality=93)
print(out, img.size)
for row in report:
    print(row)
