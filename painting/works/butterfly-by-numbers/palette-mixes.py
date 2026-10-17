import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 2300, 1980
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

# Lemon and phthalo green are not in this picture.
HOLLOW = {3, 13}


def ctext(x, y, s, font, fill):
    d.text((x - d.textlength(s, font=font) / 2, y), s, font=font, fill=fill)


def disc(x, y, r, color, outline=(45, 45, 45)):
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=outline, width=2)


def recipe(x, y, parts, fg):
    """Draw component circles; area is proportional to the share of each paint."""
    k = 10
    for key, amount in parts:
        color = PAINT[key][1]
        r = max(5, k * math.sqrt(amount))
        disc(x + r, y, r, color)
        ctext(x + r, y + r + 3, str(key), f_tiny, fg)
        x += 2 * r + 12
    return x


def mix(x, y, color, name, parts, fg):
    disc(x, y, 30, color)
    d.text((x + 44, y - 42), name, font=f_name, fill=fg)
    recipe(x + 44, y + 16, parts, fg)


def value_line(y, items, fg, base_parts):
    """One base in the middle, lighter to the left, duller to the right."""
    xs = [400, 900, 1400]
    for (col, name, tone, _label), x in zip(items, xs):
        disc(x, y, 46 if "база" in tone else 36, col, outline=(30, 30, 30))
        ctext(x, y + 54, name, f_name, fg)
        ctext(x, y + 82, tone, f_small, (70, 70, 70))
    for a, b, label in ((xs[1], xs[0], items[0][3]), (xs[1], xs[2], items[2][3])):
        sx = a - 60 if b < a else a + 60
        ex = b + 50 if b < a else b - 50
        d.line((sx, y, ex, y), fill=(70, 70, 70), width=4)
        tip = -1 if b < a else 1
        d.polygon([(ex, y), (ex - tip * 16, y - 9), (ex - tip * 16, y + 9)], fill=(70, 70, 70))
        ctext((sx + ex) / 2, y - 34, label, f_small, (50, 50, 50))
    ctext(xs[1], y + 118, "база:", f_small, (70, 70, 70))
    recipe(xs[1] - 34, y + 156, base_parts, fg)


d.text((40, 24), "Бабочка: куда класть замесы", font=f_title, fill=(28, 28, 28))
d.text((40, 76), "Большой круг — замес. Маленькие кружки — из чего он: чем больше кружок, тем больше этой краски. Цифра под кружком — номер тюбика.",
       font=f_sub, fill=(55, 55, 55))

d.rounded_rectangle((28, 124, W - 28, H - 24), radius=26, fill=(158, 160, 158), outline=(90, 90, 90), width=3)

hx, hy, hr = 140, 1180, 70
d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=(236, 230, 218), outline=(70, 70, 70), width=4)
ctext(hx, hy - 10, "дырка", f_small, (70, 70, 70))


def zone(box, bg, fg, title):
    d.rounded_rectangle(box, radius=20, fill=bg)
    d.text((box[0] + 22, box[1] + 14), title, font=f_zone, fill=fg)


lfg = (30, 30, 30)
zone((220, 360, 1620, 1180), (232, 226, 210), lfg, "Света   ·   тон 6,5–9")
d.text((246, 408), "Две линии от одной кучи: светлее влево, гуще вправо", font=f_small, fill=(70, 70, 70))

value_line(500, [
    ((168, 214, 242), "Блик крыла", "тон 9", "+ белила 1"),
    ((104, 172, 214), "Свет крыла", "тон 8, база", ""),
    ((58, 112, 180), "Полоса крыла", "тон 7", "+ ультрамарин 11"),
], lfg, [(10, 2), (2, 2), (12, 0.25)])

value_line(860, [
    ((252, 198, 92), "Блик цветка", "тон 8,5", "+ белила 1"),
    ((226, 136, 40), "Цветок", "тон 7, база", ""),
    ((214, 96, 28), "Пятна на крыле", "тон 6,5", "+ красный 9"),
], lfg, [(4, 3), (9, 1), (2, 1)])

mfg = (28, 26, 24)
zone((390, 1220, 1720, 1580), (190, 168, 142), mfg, "Средние тона   ·   тон 4–6")
mids = [
    ((38, 78, 148), "Крыло", [(11, 3), (1, 1), (12, 0.3)]),
    ((168, 78, 30), "Тень лепестка", [(4, 2), (6, 1.2), (5, 0.5)]),
    ((118, 58, 30), "Тёплый фон", [(7, 2), (6, 1.5), (4, 0.4)]),
]
for i, (col, name, parts) in enumerate(mids):
    mix(460 + i * 430, 1380, col, name, parts, mfg)

dfg = (236, 232, 224)
zone((600, 1620, 1960, 1920), (54, 52, 50), dfg, "Тени   ·   тон 1,5–3")
darks = [
    ((20, 30, 64), "Край крыла", [(14, 2), (11, 2), (12, 0.3)]),
    ((26, 28, 42), "Тело", [(14, 2), (11, 1)]),
    ((46, 30, 32), "Фон", [(14, 3), (7, 1), (8, 0.3)]),
]
for i, (col, name, parts) in enumerate(darks):
    mix(660 + i * 440, 1760, col, name, parts, dfg)

R = 26


def blob(x, y, n):
    name, color = PAINT[n]
    if n in HOLLOW:
        d.ellipse((x - R, y - R, x + R, y + R), outline=(40, 40, 40), width=2)
        ctext(x, y - 12, str(n), f_num, (30, 30, 30))
        ctext(x, y + R + 6, name, f_edge, (25, 25, 25))
        ctext(x, y + R + 26, "не выдавливать", f_edge, (25, 25, 25))
    else:
        disc(x, y, R, color, outline=(35, 35, 35))
        lum = 0.3 * color[0] + 0.59 * color[1] + 0.11 * color[2]
        ctext(x, y - 12, str(n), f_num, (20, 20, 20) if lum > 150 else (245, 245, 245))
        ctext(x, y + R + 6, name, f_edge, (25, 25, 25))


for i in range(9):
    blob(250 + i * 198, 200, i + 1)

for n, y in zip(range(10, 15), [430, 700, 980, 1320, 1700]):
    blob(2125, y, n)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "palette-mixes.jpg")
img.save(out, quality=93)
print(out)
