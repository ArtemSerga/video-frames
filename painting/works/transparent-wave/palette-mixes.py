import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 2300, 1720
img = Image.new("RGB", (W, H), (236, 230, 218))
d = ImageDraw.Draw(img)

reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
boldp = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
f_title = ImageFont.truetype(boldp, 40)
f_sub = ImageFont.truetype(reg, 23)
f_zone = ImageFont.truetype(boldp, 30)
f_name = ImageFont.truetype(boldp, 22)
f_tiny = ImageFont.truetype(reg, 15)
f_num = ImageFont.truetype(boldp, 20)
f_edge = ImageFont.truetype(reg, 17)
f_small = ImageFont.truetype(reg, 18)
f_op = ImageFont.truetype(boldp, 28)

PAINT = {
    1: ("белила", (246, 246, 242)),
    2: ("цинковые", (228, 232, 236)),
    3: ("лимонный", (246, 232, 40)),
    4: ("кадм. жёлтый", (250, 182, 20)),
    5: ("охра", (198, 148, 52)),
    6: ("сиена", (142, 62, 30)),
    7: ("умбра", (86, 56, 40)),
    8: ("краплак", (140, 20, 46)),
    9: ("кадм. красный", (214, 36, 34)),
    10: ("церулеум", (44, 142, 202)),
    11: ("ультрамарин", (36, 46, 152)),
    12: ("фтало синий", (16, 40, 110)),
    13: ("фтало зелёный", (0, 92, 72)),
    14: ("тёмный замес", (28, 30, 40)),
}


def ctext(x, y, s, font, fill):
    d.text((x - d.textlength(s, font=font) / 2, y), s, font=font, fill=fill)


def disc(x, y, r, color, outline=(45, 45, 45)):
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=outline, width=2)


def recipe(x, y, parts, fg):
    """Draw component circles; area is proportional to the share of each paint."""
    k = 10
    for key, amount in parts:
        color = PAINT[key][1] if isinstance(key, int) else key[1]
        r = max(5, k * math.sqrt(amount))
        disc(x + r, y, r, color)
        label = str(key) if isinstance(key, int) else key[0]
        ctext(x + r, y + r + 3, label, f_tiny, fg)
        x += 2 * r + 12
    return x


def mix(x, y, color, name, parts, fg):
    disc(x, y, 30, color)
    d.text((x + 44, y - 42), name, font=f_name, fill=fg)
    recipe(x + 44, y + 16, parts, fg)


d.text((40, 24), "Волна на закате: куда класть замесы", font=f_title, fill=(28, 28, 28))
d.text((40, 76), "Большой круг — замес. Маленькие кружки — из чего он: чем больше кружок, тем больше этой краски. Цифра под кружком — номер тюбика.",
       font=f_sub, fill=(55, 55, 55))

d.rounded_rectangle((28, 124, W - 28, H - 24), radius=26, fill=(158, 160, 158), outline=(90, 90, 90), width=3)

hx, hy, hr = 140, 1060, 70
d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=(236, 230, 218), outline=(70, 70, 70), width=4)
ctext(hx, hy - 10, "дырка", f_small, (70, 70, 70))


def zone(box, bg, fg, title):
    d.rounded_rectangle(box, radius=20, fill=bg)
    d.text((box[0] + 22, box[1] + 14), title, font=f_zone, fill=fg)


SKY = (242, 186, 42)
SUN = (255, 228, 120)
GLINT = (226, 176, 70)
FOAM = (246, 249, 252)

# lights: the yellow line, lightest next to the whites
lfg = (30, 30, 30)
zone((220, 380, 1500, 830), (232, 226, 210), lfg, "Света   ·   тон 7–9")
d.text((246, 428), "Жёлтая линия: один замес, светлее влево, глуше вправо", font=f_small, fill=(70, 70, 70))

line_y = 520
xs = [330, 760, 1190]
line = [
    (SUN, "Солнце", "тон 9"),
    (SKY, "Жёлтое небо", "тон 8, база"),
    (GLINT, "Блик на воде", "тон 7"),
]
for (col, name, tone), x in zip(line, xs):
    disc(x, line_y, 46 if name == "Жёлтое небо" else 36, col, outline=(30, 30, 30))
    ctext(x, line_y + 54, name, f_name, lfg)
    ctext(x, line_y + 82, tone, f_small, (70, 70, 70))
for a, b, label in ((xs[1], xs[0], "+ белила 1"), (xs[1], xs[2], "+ охра 5")):
    sx = a - 60 if b < a else a + 60
    ex = b + 50 if b < a else b - 50
    d.line((sx, line_y, ex, line_y), fill=(70, 70, 70), width=4)
    tip = -1 if b < a else 1
    d.polygon([(ex, line_y), (ex - tip * 16, line_y - 9), (ex - tip * 16, line_y + 9)], fill=(70, 70, 70))
    ctext((sx + ex) / 2, line_y - 34, label, f_small, (50, 50, 50))

ctext(xs[1], 650, "база:", f_small, (70, 70, 70))
recipe(xs[1] - 34, 690, [(4, 2), (2, 1)], lfg)
mix(290, 740, FOAM, "Пена", [(1, 5), (10, 0.25)], lfg)

# middles
mfg = (28, 26, 24)
zone((390, 870, 1720, 1340), (190, 168, 142), mfg, "Средние тона   ·   тон 4–6")
mids = [
    ((224, 118, 42), "Оранжевое небо", [(4, 3), (9, 1), (1, 0.5)]),
    ((86, 168, 180), "Бирюза неба", [(10, 3), (1, 2), (3, 0.3)]),
    ((148, 162, 172), "Лицо волны", [(10, 2), (1, 2), (14, 0.3)]),
    ((198, 142, 52), "Золото гребня", [(4, 2), (5, 2), (1, 1)]),
    ((64, 150, 122), "Зелёная вода", [(3, 3), (1, 1), (13, 0.25)]),
    ((138, 116, 148), "Фиолетовое облако", [(11, 2), (1, 1.5), (8, 0.3)]),
]
for i, (col, name, parts) in enumerate(mids):
    mix(440 + (i % 2) * 640, 970 + (i // 2) * 128, col, name, parts, mfg)

# shadows
dfg = (236, 232, 224)
zone((600, 1380, 1960, 1676), (54, 52, 50), dfg, "Тени   ·   тон 1,5–3")
darks = [
    ((52, 34, 26), "Нутро волны", [(14, 3), (6, 1)]),
    ((78, 30, 34), "Тёмная вода", [(14, 3), (8, 0.4)]),
    ((78, 90, 98), "Тень пены", [(14, 2), (10, 1), (1, 0.7)]),
]
for i, (col, name, parts) in enumerate(darks):
    mix(650 + i * 440, 1500, col, name, parts, dfg)

# pure colours on the edges
R = 26


def blob(x, y, n, hollow=False):
    name, color = PAINT[n]
    if hollow:
        d.ellipse((x - R, y - R, x + R, y + R), outline=(40, 40, 40), width=2)
        ctext(x, y - 12, str(n), f_num, (30, 30, 30))
    else:
        disc(x, y, R, color, outline=(35, 35, 35))
        lum = 0.3 * color[0] + 0.59 * color[1] + 0.11 * color[2]
        ctext(x, y - 12, str(n), f_num, (20, 20, 20) if lum > 150 else (245, 245, 245))
    ctext(x, y + R + 6, name, f_edge, (25, 25, 25))


for i in range(9):
    blob(250 + i * 198, 200, i + 1)

rx = 2125
for n, y in zip(range(10, 15), [390, 620, 860, 1120, 1440]):
    blob(rx, y, n, hollow=(n == 12))
ctext(rx, 860 + R + 26, "не выдавливать", f_edge, (25, 25, 25))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "palette-mixes.jpg")
img.save(out, quality=93)
print(out)
