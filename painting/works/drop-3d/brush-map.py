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
    "canvas": (170, 164, 151),
    "umber": (92, 62, 44),
    "warm": (200, 174, 110),
    "warm_l": (228, 221, 192),
    "white": (250, 252, 248),
    "cool": (120, 128, 132),
    "cool_l": (194, 196, 200),
}

# shape, size label, brush, fill (one family, or two for a blending brush)
BRUSH = {
    "gn12": ("square", "12", "Golden Night Flat", ("canvas",)),
    "pony10": ("star", "10", "пони, сухой", ("cool", "canvas")),
    "cad2": ("circle", "2", "Cadence CA123", ("umber",)),
    "nova8": ("square", "8", "Nova Bright", ("umber",)),
    "liner2": ("triangle", "2", "Aspen Liner", ("umber",)),
    "filb4": ("oval", "4", "Akoya Filbert", ("warm",)),
    "cad1": ("circle", "1", "Cadence CA123", ("warm",)),
    "dv6": ("oval", "6", "da Vinci 375 Filbert", ("warm_l",)),
    "dv4": ("oval", "4", "da Vinci 375, блик", ("white",)),
    "aspen8": ("oval", "8", "Aspen Filbert", ("cool",)),
    "filb10": ("oval", "10", "Akoya Filbert", ("cool",)),
    "bright4": ("square", "4", "Akoya Bright", ("cool",)),
    "round6": ("circle", "6", "Akoya Round", ("cool_l",)),
    "mop10": ("star", "10", "мопик, сухой", ("cool", "warm")),
}

KEY = [
    ("Холст", "canvas", ["gn12", "pony10"]),
    ("Умбра", "umber", ["cad2", "nova8", "liner2"]),
    ("Тёплое дно", "warm", ["filb4", "cad1", "dv6", "dv4"]),
    ("Холодная капля", "cool", ["aspen8", "filb10", "bright4", "round6", "mop10"]),
]

# step, brush, (x, y) in reference pixels
MARKS = [
    # 1 tone the whole canvas with the canvas pile
    (1, "gn12", (80, 150)),
    (1, "gn12", (530, 430)),
    (1, "gn12", (100, 720)),
    # 2 umber drawing, then the cast shadow
    (2, "cad2", (222, 705)),
    (2, "nova8", (430, 805)),
    # 3 warm bottom of the drop: gold ring, glow, rim line
    (3, "filb4", (350, 770)),
    (3, "dv6", (290, 720)),
    (3, "cad1", (345, 400)),
    # 4 cool drop: haze, neck, edges, shadow side, reflex
    (4, "aspen8", (270, 140)),
    (4, "aspen8", (320, 290)),
    (4, "filb10", (250, 420)),
    (4, "bright4", (240, 566)),
    (4, "round6", (262, 505)),
    # 5 haze: dry soft brushes, seams only
    (5, "mop10", (305, 600)),
    (5, "pony10", (160, 250)),
    (5, "pony10", (440, 180)),
    # 6 highlight
    (6, "dv4", (240, 625)),
    # 7 signature
    (7, "liner2", (110, 820)),
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
