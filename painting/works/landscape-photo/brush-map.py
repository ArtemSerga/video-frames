import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

# The source photo is a 258 px thumbnail. The finished frame shows the zones the brushes address.
src = Image.open(os.path.join(HERE, "00-15-03.jpg")).convert("RGB")
crop = src.crop((190, 4, 1116, 716))

W = 2400
S = W / crop.size[0]
RH = round(crop.size[1] * S)
GAP = 36
KEY_H = 520
H = RH + GAP + KEY_H
OX, OY = 0, 0
img = Image.new("RGB", (W, H), (40, 38, 36))
img.paste(crop.resize((W, RH), Image.LANCZOS), (0, 0))

boldp = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
f_num = ImageFont.truetype(boldp, 52)
f_head = ImageFont.truetype(boldp, 36)
f_key = ImageFont.truetype(boldp, 34)
f_keyl = ImageFont.truetype(reg, 32)
f_note = ImageFont.truetype(reg, 34)

# Same eight colours as the stage headings.
STEP_COLOUR = {1: (232, 48, 48), 2: (246, 138, 22), 3: (250, 214, 34), 4: (64, 178, 76),
               5: (46, 86, 222), 6: (152, 72, 204), 7: (232, 120, 168), 8: (150, 96, 52)}

FAMILY = {
    "sky": (155, 214, 235),
    "grass": (127, 190, 41),
    "crown": (41, 141, 63),
    "bush": (60, 83, 49),
    "road": (219, 162, 44),
    "dark": (52, 46, 42),
    "light": (236, 232, 220),
}

# shape, size label, brush, fill. A brush keeps one family; the spatula is the one shared tool.
BRUSH = {
    "golden": ("square", "12", "Night 12", ("sky",)),
    "artisan": ("square", "12", "Flat 12", ("grass",)),
    "aspen8": ("oval", "8", "Filbert 8", ("crown",)),
    "akoya4": ("square", "4", "Bright 4", ("bush",)),
    "cad2": ("circle", "2", "Round 2", ("bush",)),
    "akoya10": ("oval", "10", "Filbert 10", ("road",)),
    "spatula": ("diamond", "", "шпатель", ("sky", "grass")),
    "liner": ("triangle", "2", "Liner 2", ("dark",)),
    "akoya6": ("circle", "6", "Round 6", ("light",)),
    "cad1": ("circle", "1", "Round 1", ("dark",)),
}

KEY = [
    ("Небо", "sky", ["golden"]),
    ("Трава", "grass", ["artisan"]),
    ("Кроны", "crown", ["aspen8"]),
    ("Куст", "bush", ["akoya4", "cad2"]),
    ("Дорога", "road", ["akoya10"]),
    ("Шов", "sky", ["spatula"]),
    ("Ветки", "dark", ["liner", "cad1"]),
    ("Стволы", "light", ["akoya6"]),
]

# step, brush, (x, y) in pixels of the cropped finished frame
MARKS = [
    (1, "golden", (300, 90)),
    (2, "spatula", (140, 405)),
    (1, "artisan", (230, 540)),
    (2, "aspen8", (620, 180)),
    (3, "liner", (700, 250)),
    (3, "akoya4", (760, 380)),
    (6, "cad2", (680, 460)),
    (4, "akoya10", (470, 620)),
    (6, "akoya6", (400, 380)),
    (8, "cad1", (70, 450)),
]

R = 54


def outline(kind, cx, cy, r):
    if kind == "circle":
        return ("ellipse", (cx - r, cy - r, cx + r, cy + r))
    if kind == "oval":
        return ("ellipse", (cx - r * 1.4, cy - r * 0.82, cx + r * 1.4, cy + r * 0.82))
    if kind == "square":
        q = r * 0.9
        return ("poly", [(cx - q, cy - q), (cx + q, cy - q), (cx + q, cy + q), (cx - q, cy + q)])
    if kind == "triangle":
        return ("poly", [(cx + r * 1.15 * math.cos(math.radians(a)), cy + r * 0.25 + r * 1.15 * math.sin(math.radians(a)))
                         for a in (-90, 30, 150)])
    if kind == "diamond":
        return ("poly", [(cx, cy - r * 1.15), (cx + r * 1.0, cy), (cx, cy + r * 1.15), (cx - r * 1.0, cy)])
    pts = []
    for i in range(10):
        rr = r * 1.25 if i % 2 == 0 else r * 0.58
        a = math.radians(-90 + 36 * i)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return ("poly", pts)


def fill_shape(kind, cx, cy, r, fams):
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    how, geo = outline(kind, cx, cy, r)
    (md.ellipse if how == "ellipse" else md.polygon)(geo, fill=255)
    if len(fams) == 2:
        left = Image.new("L", img.size, 0)
        ImageDraw.Draw(left).rectangle((0, 0, cx, H), fill=255)
        img.paste(FAMILY[fams[0]], (0, 0), Image.composite(mask, left.point(lambda _: 0), left))
        right = left.point(lambda v: 255 - v)
        img.paste(FAMILY[fams[1]], (0, 0), Image.composite(mask, right.point(lambda _: 0), right))
    else:
        img.paste(FAMILY[fams[0]], (0, 0), mask)


def stroke_shape(dr, kind, cx, cy, r, colour, width):
    how, geo = outline(kind, cx, cy, r)
    if how == "ellipse":
        dr.ellipse(geo, outline=colour, width=width)
    else:
        dr.line(geo + [geo[0], geo[1]], fill=colour, width=width, joint="curve")


def marker(bid, cx, cy, r, ring, f):
    kind, label, _, fams = BRUSH[bid]
    dr = ImageDraw.Draw(img)
    if ring:
        stroke_shape(dr, kind, cx, cy, r, (16, 14, 12), 18)
    fill_shape(kind, cx, cy, r, fams)
    dr = ImageDraw.Draw(img)
    stroke_shape(dr, kind, cx, cy, r, ring or (214, 208, 196), 10 if ring else 4)
    if label:
        ty = cy + (r * 0.22 if kind == "triangle" else 0)
        ink = (30, 26, 22) if fams == ("light",) else (255, 255, 255)
        edge = (255, 255, 255) if fams == ("light",) else (16, 14, 12)
        dr.text((cx, ty), label, font=f, fill=ink, anchor="mm", stroke_width=3, stroke_fill=edge)


for step, bid, (x, y) in MARKS:
    marker(bid, OX + x * S, OY + y * S, R, STEP_COLOUR[step], f_num)

d = ImageDraw.Draw(img)
note = "1 небо и трава  ·  2 кроны, шов один раз  ·  3 куст и ветки  ·  4 дорога  ·  5 небо снова  ·  6 стволы  ·  7 кромка  ·  8 фигуры"
d.text((40, RH + 16), note, font=f_note, fill=(236, 230, 218))

f_knum = ImageFont.truetype(boldp, 28)
cw = (W - 40) // len(KEY)
top = RH + GAP + 56
rows = max(len(ids) for *_, ids in KEY)
rh = 118
for col, (title, fam, ids) in enumerate(KEY):
    x0 = 20 + col * cw
    d.rounded_rectangle((x0 + 8, top, x0 + 44, top + 36), radius=8, fill=FAMILY[fam],
                        outline=(214, 208, 196), width=2)
    d.text((x0 + 54, top + 18), title, font=f_head, fill=(236, 230, 218), anchor="lm")
    for row, bid in enumerate(ids):
        _, label, name, _ = BRUSH[bid]
        cx, cy = x0 + 40, top + 90 + row * rh
        marker(bid, cx, cy, 28, None, f_knum)
        d = ImageDraw.Draw(img)
        d.text((cx + 46, cy), name, font=f_keyl, fill=(236, 230, 218), anchor="lm")

out = os.path.join(HERE, "brush-map-1.jpg")
img.save(out, quality=90)
print(out, img.size)
