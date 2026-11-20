"""Light-zone map for the Asaro head. Letters mark what the photo actually does."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ref = Image.open(os.path.join(HERE, "reference.jpg")).convert("RGB")
SCALE = 2000 / ref.size[0]
RW, RH = 2000, round(ref.size[1] * SCALE)
LEGEND_H = 280
W = RW
img = Image.new("RGB", (W, RH + LEGEND_H), (28, 26, 24))
img.paste(ref.resize((RW, RH), Image.LANCZOS), (0, 0))

bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
f_letter = ImageFont.truetype(bold, 36)
f_legend = ImageFont.truetype(bold, 32)
f_small = ImageFont.truetype(reg, 28)
f_arrow = ImageFont.truetype(bold, 32)

# Plate colour separates the letters. It is not the paint.
ZONE = {
    "С": ((232, 210, 160), (40, 32, 24)),
    "П": ((86, 118, 138), (255, 255, 255)),
    "Т": ((62, 54, 72), (255, 255, 255)),
    "Р": ((46, 78, 112), (255, 255, 255)),
    "Пд": ((28, 26, 32), (255, 255, 255)),
}

# (letter, x, y) in reference pixels, 904×1024.
# Light from above and from the front-left. No блик: the lit planes are even.
MARKS = [
    ("С", 370, 140),   # forehead
    ("С", 330, 450),   # front of the nose
    ("С", 345, 370),   # front of the cheek
    ("С", 310, 558),   # chin, the bright plane; 575 is already the turn
    ("С", 460, 745),   # front of the neck
    ("С", 430, 870),   # top of the pedestal
    ("С", 678, 360),   # ear plane facing the lamp
    ("П", 285, 390),   # side of the nose
    ("П", 570, 185),   # side of the cranium
    ("П", 555, 715),   # side of the neck
    ("Т", 400, 282),   # eye socket
    ("Т", 545, 430),   # shadow side of the cheek
    ("Т", 405, 608),   # underside of the jaw
    ("Т", 658, 298),   # ear hole
    ("Т", 634, 868),   # shadow rim of the pedestal
    ("Пд", 352, 230),  # brow cast into the socket
    ("Пд", 265, 485),  # nose cast on the lip
    ("Пд", 262, 535),  # lip cast on the chin
    ("Пд", 632, 792),  # neck cast on the pedestal's right shoulder
    ("Р", 636, 908),   # weak lift on that same shadow side
]


def plate(letter, x, y):
    fill, ink = ZONE[letter]
    cx, cy = x * SCALE, y * SCALE
    d = ImageDraw.Draw(img)
    tw = d.textlength(letter, font=f_letter)
    w, h = tw + 22, 48
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    d.rounded_rectangle(box, radius=8, fill=fill, outline=(255, 255, 255), width=2)
    d.text((cx, cy), letter, font=f_letter, fill=ink, anchor="mm")


for letter, x, y in MARKS:
    plate(letter, x, y)

# Arrow in the empty ground, pointing at the forehead.
d = ImageDraw.Draw(img)
start = (70 * SCALE, 36 * SCALE)
end = (230 * SCALE, 118 * SCALE)
d.line([start, end], fill=(245, 220, 150), width=8)
ex, ey = end
sx, sy = start
dx, dy = ex - sx, ey - sy
length = (dx * dx + dy * dy) ** 0.5
ux, uy = dx / length, dy / length
px, py = -uy, ux
head = 28
d.polygon([
    (ex, ey),
    (ex - ux * head + px * head * 0.55, ey - uy * head + py * head * 0.55),
    (ex - ux * head - px * head * 0.55, ey - uy * head - py * head * 0.55),
], fill=(245, 220, 150))
d.text((78 * SCALE, 18 * SCALE), "сверху, спереди слева", font=f_arrow,
       fill=(245, 220, 150), anchor="lt")

legend = [
    ("Б", "блик — на этой голове нет", None),
    ("С", "свет", ZONE["С"][0]),
    ("П", "полусвет", ZONE["П"][0]),
    ("Т", "собственная тень", ZONE["Т"][0]),
    ("Р", "рефлекс — только низ постамента", ZONE["Р"][0]),
    ("Пд", "падающая тень", ZONE["Пд"][0]),
]
top = RH + 28
col_w = W / 2
for i, (letter, name, colour) in enumerate(legend):
    col, row = i % 2, i // 2
    x = 36 + col * col_w
    y = top + row * 70
    if colour:
        d.rounded_rectangle((x, y, x + 64, y + 48), radius=8, fill=colour,
                            outline=(255, 255, 255), width=2)
        ink = ZONE[letter][1]
        d.text((x + 32, y + 24), letter, font=f_letter, fill=ink, anchor="mm")
    else:
        d.rounded_rectangle((x, y, x + 64, y + 48), radius=8, outline=(180, 170, 150), width=2)
        d.text((x + 32, y + 24), letter, font=f_letter, fill=(180, 170, 150), anchor="mm")
    d.text((x + 80, y + 24), name, font=f_legend, fill=(236, 230, 218), anchor="lm")

note = "Фон чёрный — это не падающая тень. Рефлекс только внизу теневого бока постамента, слабый."
d.text((36, RH + LEGEND_H - 36), note, font=f_small, fill=(190, 182, 170), anchor="lm")

out = os.path.join(HERE, "light-zones-1.jpg")
img.save(out, quality=90)
print(out, img.size)
