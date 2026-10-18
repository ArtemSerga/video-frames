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
    "dark": (92, 44, 72),
    "warm": (214, 118, 36),
    "warm_l": (250, 204, 140),
    "blue": (38, 78, 178),
    "blue_l": (150, 196, 242),
    "line": (18, 22, 40),
    "steel": (150, 150, 150),
}

# shape, size label, brush, fill (one family, or two for a blending brush)
BRUSH = {
    "artisan12": ("square", "12", "Artisan Short Flat", ("dark",)),
    "round6": ("circle", "6", "Akoya Round", ("dark",)),
    "filb10": ("oval", "10", "Akoya Filbert", ("warm",)),
    "filb4": ("oval", "4", "Akoya Filbert", ("warm",)),
    "dv6": ("oval", "6", "da Vinci 375 Filbert", ("warm_l",)),
    "round0": ("circle", "0", "Akoya Round", ("warm_l",)),
    "aspen8": ("star", "8", "Aspen Filbert, сухой", ("warm", "dark")),
    "mop10": ("star", "10", "мопик, сухой", ("warm", "dark")),
    "dv4": ("oval", "4", "da Vinci 375 Filbert", ("blue",)),
    "bright4": ("square", "4", "Akoya Bright", ("blue",)),
    "nova8": ("square", "8", "Nova Bright", ("blue_l",)),
    "nova4": ("square", "4", "Nova Bright", ("blue_l",)),
    "pony10": ("star", "10", "пони, сухой", ("blue", "dark")),
    "liner2": ("triangle", "2", "Aspen Liner", ("line",)),
    "cad2": ("circle", "2", "Cadence CA123", ("line",)),
    "cad1": ("circle", "1", "Cadence CA123", ("line",)),
    "knife": ("diamond", "", "мастихин, протираю", ("steel",)),
}

KEY = [
    ("Тёмное", "dark", ["artisan12", "round6"]),
    ("Тёплое", "warm", ["filb10", "filb4", "dv6", "round0", "aspen8", "mop10"]),
    ("Синее", "blue", ["dv4", "bright4", "nova8", "nova4", "pony10"]),
    ("Тело и линии", "line", ["liner2", "cad2", "cad1", "knife"]),
]

# step, brush, (x, y) in reference pixels
MARKS = [
    # 1 dark background, from the canvas edges toward the flowers
    (1, "artisan12", (70, 130)),
    (1, "artisan12", (480, 110)),
    (1, "artisan12", (60, 470)),
    (1, "round6", (428, 455)),
    (1, "round6", (330, 1040)),
    # 2 warm: shadows and warm background, then middles, then lights and sparks
    (2, "filb10", (330, 170)),
    (2, "aspen8", (220, 330)),
    (2, "filb4", (230, 760)),
    (2, "filb10", (820, 820)),
    (2, "filb4", (880, 380)),
    (2, "dv6", (560, 1200)),
    (2, "dv6", (100, 700)),
    (2, "round0", (330, 1180)),
    (2, "mop10", (1010, 1000)),
    # 3 blue: body and dark wing first, then middles, then lights
    (3, "dv4", (390, 770)),
    (3, "dv4", (462, 560)),
    (3, "cad2", (290, 880)),
    (3, "bright4", (640, 430)),
    (3, "bright4", (650, 1060)),
    (3, "dv4", (740, 560)),
    (3, "nova8", (660, 260)),
    (3, "nova4", (600, 175)),
    (3, "pony10", (520, 660)),
    # 4 lines
    (4, "liner2", (200, 600)),
    (4, "cad1", (700, 960)),
    # 5 knife texture
    (5, "knife", (150, 660)),
    (5, "knife", (480, 1150)),
    (5, "knife", (560, 410)),
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

out = os.path.join(HERE, "brush-map-2.jpg")
img.save(out, quality=90)
print(out, img.size)
