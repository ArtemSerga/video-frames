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
    "yellow": (247, 209, 28),
    "yellow_l": (249, 238, 148),
    "shade": (179, 109, 62),
    "violet_l": (188, 157, 199),
    "violet": (67, 25, 92),
    "pink": (220, 136, 169),
}

# shape, size label, brush, fill (one family, or two for a blending brush)
BRUSH = {
    "filb10": ("oval", "10", "Akoya Filbert", ("yellow",)),
    "filb4": ("oval", "4", "Akoya Filbert", ("yellow",)),
    "dv4": ("oval", "4", "da Vinci 375 Filbert", ("yellow_l",)),
    "cad1": ("circle", "1", "Cadence CA123", ("yellow_l",)),
    "bright4": ("square", "4", "Akoya Bright", ("shade",)),
    "cad2": ("circle", "2", "Cadence CA123", ("shade",)),
    "mop10": ("star", "10", "мопик, сухой", ("yellow", "shade")),
    "gn12": ("square", "12", "Golden Night Flat", ("violet_l",)),
    "nova8": ("square", "8", "Nova Bright", ("violet_l",)),
    "fan6": ("star", "6", "веер, сухой", ("violet_l",)),
    "artisan12": ("square", "12", "Artisan Short Flat", ("violet",)),
    "round6": ("circle", "6", "Akoya Round", ("violet",)),
    "pony10": ("star", "10", "пони, сухой", ("violet", "violet_l")),
    "liner2": ("triangle", "2", "Aspen Liner", ("pink",)),
}

KEY = [
    ("Лимон", "yellow", ["filb10", "filb4", "dv4", "cad1"]),
    ("Тень лимона", "shade", ["bright4", "cad2", "mop10"]),
    ("Фон", "violet_l", ["gn12", "nova8", "fan6"]),
    ("Тень и подпись", "violet", ["artisan12", "round6", "pony10", "liner2"]),
]

# step, brush, (x, y) in reference pixels
MARKS = [
    # 1 the chopped yellow spot
    (1, "filb10", (420, 850)),
    (1, "filb10", (780, 830)),
    # 2 background over everything, up to the lemon edge
    (2, "gn12", (170, 260)),
    (2, "gn12", (860, 330)),
    (2, "gn12", (800, 1370)),
    (2, "nova8", (560, 560)),
    (2, "nova8", (1010, 760)),
    # 3 own shadow, then the cast shadow
    (3, "bright4", (420, 1150)),
    (3, "bright4", (780, 1140)),
    (3, "artisan12", (130, 1190)),
    (3, "artisan12", (330, 1340)),
    (3, "round6", (560, 1285)),
    # 4 mosaic of tints, then the highlight
    (4, "filb4", (300, 990)),
    (4, "filb4", (840, 1010)),
    (4, "dv4", (614, 790)),
    # 5 valeur: dry soft brushes
    (5, "mop10", (590, 1040)),
    (5, "pony10", (560, 1420)),
    (5, "fan6", (160, 640)),
    # 6 nibs and pores
    (6, "cad2", (950, 960)),
    (6, "cad2", (160, 880)),
    (6, "cad1", (330, 760)),
    # 7 signature
    (7, "liner2", (930, 1440)),
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
