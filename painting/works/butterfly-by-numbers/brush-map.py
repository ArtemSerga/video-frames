import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
S = 2  # reference is 1116 x 1409; markers are placed in its pixels and drawn at S x

ref = Image.open(os.path.join(HERE, "reference.jpg")).convert("RGB")
RW, RH = ref.size[0] * S, ref.size[1] * S
W = RW
H = round(W * 1.414)  # A4, the same height as the palette scheme beside it
img = Image.new("RGB", (W, H), (40, 38, 36))
img.paste(ref.resize((RW, RH), Image.LANCZOS), (0, 0))

boldp = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
f_num = ImageFont.truetype(boldp, 60)
f_key = ImageFont.truetype(boldp, 44)
f_keyl = ImageFont.truetype(reg, 44)

STEP_COLOUR = {1: (232, 48, 48), 2: (246, 138, 22), 3: (250, 214, 34), 4: (64, 178, 76),
               5: (64, 170, 232), 6: (46, 86, 222), 7: (152, 72, 204)}

# shape, size label, brush
BRUSH = {
    "flat12": ("square", "12", "Artisan Short Flat"),
    "flat8": ("square", "8", "Nova Bright"),
    "flat4": ("square", "4", "Akoya Bright"),
    "filb10": ("oval", "10", "Akoya Filbert"),
    "filb4": ("oval", "4", "Akoya Filbert"),
    "round0": ("circle", "0", "Akoya Round"),
    "round1": ("circle", "1", "Cadence CA123"),
    "liner2": ("triangle", "2", "Aspen Liner"),
    "blend8": ("star", "8", "Aspen Filbert, сухой"),
    "mop10": ("star", "10", "мопик, сухой"),
    "knife": ("diamond", "", "мастихин"),
}

# step, brush, (x, y) in reference pixels
MARKS = [
    # 1 dark background, from the canvas edges toward the flowers
    (1, "flat12", (70, 130)),
    (1, "flat12", (480, 110)),
    (1, "flat12", (60, 470)),
    (1, "flat4", (428, 455)),
    (1, "round0", (330, 1040)),
    # 2 warm: shadows and warm background, then middles, then lights and sparks
    (2, "filb10", (330, 170)),
    (2, "blend8", (220, 330)),
    (2, "filb4", (230, 760)),
    (2, "filb10", (820, 820)),
    (2, "filb4", (880, 380)),
    (2, "filb10", (560, 1200)),
    (2, "filb4", (100, 700)),
    (2, "round0", (330, 1180)),
    (2, "mop10", (1010, 1000)),
    # 3 blue: body and dark wing first, then middles, then lights
    (3, "filb4", (390, 770)),
    (3, "filb4", (462, 560)),
    (3, "round0", (290, 880)),
    (3, "flat4", (640, 430)),
    (3, "filb4", (740, 560)),
    (3, "flat8", (660, 260)),
    (3, "flat4", (650, 1060)),
    (3, "blend8", (520, 660)),
    # 4 lines
    (4, "liner2", (200, 600)),
    (4, "round1", (700, 960)),
    # 5 knife texture
    (5, "knife", (150, 660)),
    (5, "knife", (480, 1150)),
    (5, "knife", (560, 410)),
]

R = 66


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


def draw_shape(dr, kind, cx, cy, r, colour, width, fill=None):
    how, geo = outline(kind, cx, cy, r)
    if how == "ellipse":
        dr.ellipse(geo, outline=colour, width=width, fill=fill)
    else:
        dr.polygon(geo, fill=fill)
        dr.line(geo + [geo[0], geo[1]], fill=colour, width=width, joint="curve")


def marker(kind, label, cx, cy, colour):
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    draw_shape(od, kind, cx, cy, R, (16, 14, 12, 255), 22, fill=(16, 14, 12, 160))
    img.paste(over, (0, 0), over)
    dr = ImageDraw.Draw(img)
    draw_shape(dr, kind, cx, cy, R, colour, 12)
    if label:
        ty = cy + (R * 0.22 if kind == "triangle" else 0) + (4 if kind == "star" else 0)
        dr.text((cx, ty), label, font=f_num, fill=(255, 255, 255), anchor="mm")


for step, bid, (x, y) in MARKS:
    kind, label, _ = BRUSH[bid]
    marker(kind, label, x * S, y * S, STEP_COLOUR[step])

d = ImageDraw.Draw(img)
KEY = [["flat12", "flat8", "flat4"],
       ["filb10", "filb4", "round0", "round1"],
       ["liner2", "blend8", "mop10", "knife"]]
cw = (W - 60) // len(KEY)
rh = (H - RH - 40) // max(len(c) for c in KEY)
for col, ids in enumerate(KEY):
    for row, bid in enumerate(ids):
        kind, label, name = BRUSH[bid]
        cx = 30 + col * cw + 50
        cy = RH + 20 + row * rh + rh // 2
        draw_shape(d, kind, cx, cy, 28, (214, 208, 196), 6)
        x = cx + 60
        if label:
            d.text((x, cy), label, font=f_key, fill=(236, 230, 218), anchor="lm")
            x += d.textlength(label + " ", font=f_key)
        d.text((x, cy), name, font=f_keyl, fill=(236, 230, 218), anchor="lm")

out = os.path.join(HERE, "brush-map-1.jpg")
img.save(out, quality=90)
print(out, img.size)
