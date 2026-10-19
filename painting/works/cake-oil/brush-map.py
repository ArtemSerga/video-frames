import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

ref = Image.open(os.path.join(HERE, "reference.jpg")).convert("RGB")
W = 2232
H = round(W * 1.414)  # A4, the same height as the palette scheme beside it
KEY_H = 560
S = (H - KEY_H) / ref.size[1]  # markers are placed in reference pixels
RW, RH = round(ref.size[0] * S), H - KEY_H
OX = (W - RW) // 2
img = Image.new("RGB", (W, H), (40, 38, 36))
img.paste(ref.resize((RW, RH), Image.LANCZOS), (OX, 0))

boldp = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
f_num = ImageFont.truetype(boldp, 58)
f_head = ImageFont.truetype(boldp, 44)
f_key = ImageFont.truetype(boldp, 40)
f_keyl = ImageFont.truetype(reg, 40)

STEP_COLOUR = {1: (232, 48, 48), 2: (246, 138, 22), 3: (250, 214, 34), 4: (64, 178, 76),
               5: (64, 170, 232), 6: (46, 86, 222), 7: (152, 72, 204)}

# The paint a brush carries all session. A brush never leaves its family.
FAMILY = {
    "dark": (75, 39, 55),
    "dark_l": (108, 103, 135),
    "cream": (175, 58, 27),
    "cream_l": (214, 130, 80),
    "cherry": (160, 18, 45),
    "cherry_l": (228, 157, 178),
    "grey": (200, 198, 210),
    "steel": (150, 150, 150),
}

# shape, size label, brush, fill (one family, or two for a blending brush)
BRUSH = {
    "artisan12": ("square", "12", "Artisan Short Flat", ("dark",)),
    "bright4": ("square", "4", "Akoya Bright", ("dark",)),
    "nova4": ("square", "4", "Nova Bright, глянец", ("dark_l",)),
    "filb4": ("oval", "4", "Akoya Filbert", ("cream",)),
    "cad2": ("circle", "2", "Cadence CA123", ("cream_l",)),
    "dv4": ("oval", "4", "da Vinci 375 Filbert", ("cherry",)),
    "cad1": ("circle", "1", "Cadence CA123", ("cherry_l",)),
    "bright12": ("square", "12", "Akoya Bright", ("grey",)),
    "filb10": ("oval", "10", "Akoya Filbert", ("grey",)),
    "nova8": ("square", "8", "Nova Bright", ("grey",)),
    "liner2": ("triangle", "2", "Aspen Liner", ("grey",)),
    "spatula": ("diamond", "", "силикон. лопатка", ("steel",)),
}

KEY = [
    ("Шоколад", "dark", ["artisan12", "bright4", "nova4"]),
    ("Крем", "cream", ["filb4", "cad2"]),
    ("Вишня", "cherry", ["dv4", "cad1"]),
    ("Фон", "grey", ["bright12", "filb10", "nova8", "liner2", "spatula"]),
]

# step, brush, (x, y) in reference pixels
MARKS = [
    # 1 dark mass: side, then the top
    (1, "artisan12", (300, 1180)),
    (1, "artisan12", (300, 880)),
    (1, "bright4", (850, 1060)),
    (1, "bright4", (230, 1340)),
    # 2 cream layers, thick
    (2, "filb4", (420, 1150)),
    # 3 cherry and its reflection on the glaze
    (3, "dv4", (520, 690)),
    (3, "cad1", (530, 840)),
    # 4 background greys, then the cast shadow
    (4, "bright12", (115, 290)),
    (4, "bright12", (800, 160)),
    (4, "filb10", (950, 480)),
    (4, "filb10", (100, 800)),
    (4, "nova8", (650, 1330)),
    (4, "nova8", (970, 1180)),
    # 5 stem, background pressed with the spatula
    (5, "liner2", (560, 430)),
    (5, "spatula", (130, 580)),
    # 6 highlights of different hues
    (6, "nova4", (860, 800)),
    (6, "cad1", (415, 630)),
    (6, "cad2", (760, 1050)),
    # 7 accents and signature
    (7, "cad1", (750, 1400)),
]

R = 62


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
    if kind == "star":
        pts = []
        for i in range(10):
            rr = r * 1.25 if i % 2 == 0 else r * 0.58
            a = math.radians(-90 + 36 * i)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        return ("poly", pts)


def fill_shape(kind, cx, cy, r, fams):
    """Fill the shape with its family colour; a blending brush is split between two."""
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
        stroke_shape(dr, kind, cx, cy, r, (16, 14, 12), 22)
    fill_shape(kind, cx, cy, r, fams)
    dr = ImageDraw.Draw(img)
    stroke_shape(dr, kind, cx, cy, r, ring or (214, 208, 196), 12 if ring else 4)
    if label:
        ty = cy + (r * 0.22 if kind == "triangle" else 0) + (r * 0.06 if kind == "star" else 0)
        dr.text((cx, ty), label, font=f, fill=(255, 255, 255), anchor="mm",
                stroke_width=4, stroke_fill=(16, 14, 12))


for step, bid, (x, y) in MARKS:
    marker(bid, OX + x * S, y * S, R, STEP_COLOUR[step], f_num)

d = ImageDraw.Draw(img)
f_knum = ImageFont.truetype(boldp, 32)
cw = (W - 40) // len(KEY)
top = RH + 26
rh = (H - top - 100) // max(len(ids) for *_, ids in KEY)
for col, (title, fam, ids) in enumerate(KEY):
    x0 = 20 + col * cw
    d.rounded_rectangle((x0 + 10, top, x0 + 50, top + 40), radius=8, fill=FAMILY[fam],
                        outline=(214, 208, 196), width=2)
    d.text((x0 + 64, top + 20), title, font=f_head, fill=(236, 230, 218), anchor="lm")
    for row, bid in enumerate(ids):
        _, label, name, _ = BRUSH[bid]
        cx, cy = x0 + 44, top + 70 + row * rh + rh // 2
        marker(bid, cx, cy, 31, None, f_knum)
        d = ImageDraw.Draw(img)
        d.text((cx + 54, cy), name, font=f_keyl, fill=(236, 230, 218), anchor="lm")

out = os.path.join(HERE, "brush-map-1.jpg")
img.save(out, quality=90)
print(out, img.size)
