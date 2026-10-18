import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 2300, 2030
img = Image.new("RGB", (W, H), (236, 230, 218))
d = ImageDraw.Draw(img)

reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
boldp = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
f_title = ImageFont.truetype(boldp, 40)
f_sub = ImageFont.truetype(reg, 23)
f_zone = ImageFont.truetype(boldp, 28)
f_col = ImageFont.truetype(boldp, 26)
f_name = ImageFont.truetype(boldp, 25)
f_line = ImageFont.truetype(reg, 20)
f_tiny = ImageFont.truetype(reg, 15)
f_num = ImageFont.truetype(boldp, 20)
f_edge = ImageFont.truetype(reg, 17)
f_small = ImageFont.truetype(reg, 18)
f_part = ImageFont.truetype(boldp, 15)

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

# Same code as the colour wheel: circle warm, square cold, hexagon cool or neutral.
TEMPERATURE = {
    1: "hex", 2: "hex", 3: "square", 4: "circle", 5: "circle", 6: "circle", 7: "hex",
    8: "square", 9: "circle", 10: "square", 11: "circle", 12: "square", 13: "square", 14: "hex",
}


def hexrgb(s):
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def ctext(x, y, s, font, fill):
    d.text((x - d.textlength(s, font=font) / 2, y), s, font=font, fill=fill)


def disc(x, y, r, color, outline=(45, 45, 45)):
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=outline, width=2)


def arrow(x, y0, y1, fill, width=4, head=14):
    d.line((x, y0, x, y1), fill=fill, width=width)
    tip = 1 if y1 > y0 else -1
    d.polygon([(x, y1), (x - head * 0.6, y1 - tip * head), (x + head * 0.6, y1 - tip * head)], fill=fill)


def shape_points(kind, x, y, r):
    # Equal area with a circle of radius r, so no shape reads as a bigger share.
    if kind == "square":
        h = r * math.sqrt(math.pi) / 2
        return [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)]
    R = r * math.sqrt(2 * math.pi / (3 * math.sqrt(3)))
    return [(x + R * math.cos(math.radians(60 * i - 90)),
             y + R * math.sin(math.radians(60 * i - 90))) for i in range(6)]


def shape(kind, x, y, r, fill, outline=(35, 35, 35), width=2):
    if kind == "circle":
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=width)
    else:
        d.polygon(shape_points(kind, x, y, r), fill=fill, outline=outline, width=width)


def ink(color):
    lum = 0.3 * color[0] + 0.59 * color[1] + 0.11 * color[2]
    return (20, 20, 20) if lum > 150 else (245, 245, 245)


def parts_label(amount):
    return f"{amount:g}".replace(".", ",")


def recipe(x, y, parts, fg):
    """Paint shapes as on the colour wheel; the number inside is parts."""
    r = 21
    edge = (35, 35, 35) if ink(fg) == (245, 245, 245) else (215, 215, 215)
    for key, amount in parts:
        color = PAINT[key][1]
        shape(TEMPERATURE[key], x + r, y, r, color, outline=edge)
        d.text((x + r, y), parts_label(amount), font=f_part, fill=ink(color), anchor="mm")
        x += 2 * r + 10
    return x


def pile(x, y, hexcol, name, line, fg, sub, parts=None, note=None):
    """A base carries its recipe; a branch is drawn smaller and gets its recipe from the arrow."""
    disc(x, y, 40 if parts else 32, hexrgb(hexcol), outline=(30, 30, 30))
    d.text((x + 62, y - 46), name, font=f_name, fill=fg)
    d.text((x + 62, y - 14), line, font=f_line, fill=sub)
    if parts:
        recipe(x + 62, y + 32, parts, fg)
    if note:
        d.text((x + 62, y + (66 if parts else 18)), note, font=f_small, fill=sub)


def branch(x, y_from, y_to, paint, fg):
    sgn = 1 if y_to > y_from else -1
    arrow(x, y_from + sgn * 44, y_to - sgn * 36, fg, width=3, head=12)
    y = (y_from + y_to) / 2
    d.text((x + 14, y), "+", font=f_small, fill=fg, anchor="lm")
    shape(TEMPERATURE[paint], x + 42, y, 11, PAINT[paint][1])
    d.text((x + 62, y), PAINT[paint][0], font=f_small, fill=fg, anchor="lm")


d.text((40, 24), "Бабочка: куда класть замесы", font=f_title, fill=(28, 28, 28))
d.text((40, 76), "Столбик — одно семейство. Пишешь снизу вверх, к белилам. Мешаешь сверху вниз, пока нож чистый.",
       font=f_sub, fill=(55, 55, 55))

key = [("круг — тёплый", "circle"), ("квадрат — холодный", "square"), ("шестиугольник — нейтральный", "hex"),
       ("число в фигуре — части", None)]
kx = W - 40 - sum(d.textlength(t, font=f_small) + (40 if k else 0) + 28 for t, k in key)
for text, kind in key:
    if kind:
        shape(kind, kx + 14, 88, 13, (200, 200, 200))
        kx += 34
    d.text((kx, 88), text, font=f_small, fill=(55, 55, 55), anchor="lm")
    kx += d.textlength(text, font=f_small) + 34

d.rounded_rectangle((28, 124, W - 28, H - 24), radius=26, fill=(158, 160, 158), outline=(90, 90, 90), width=3)

hx, hy, hr = 140, 1180, 70
d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=(236, 230, 218), outline=(70, 70, 70), width=4)
ctext(hx, hy - 10, "дырка", f_small, (70, 70, 70))

BANDS = [
    (360, (232, 226, 210), (30, 30, 30), (80, 80, 80), "Света   ·   тон 6–9"),
    (900, (190, 168, 142), (28, 26, 24), (60, 52, 44), "Средние   ·   тон 4–6"),
    (1440, (54, 52, 50), (236, 232, 224), (196, 192, 186), "Тени   ·   тон 1–3"),
]
BAND_H = 520
for top, bg, fg, _sub, title in BANDS:
    d.rounded_rectangle((240, top, 1990, top + BAND_H), radius=20, fill=bg)
    d.text((1990 - 22 - d.textlength(title, font=f_zone), top + 14), title, font=f_zone, fill=fg)


def row(band, i):
    return BANDS[band][0] + (150 if i == 0 else 385)


def colors(band):
    return BANDS[band][2], BANDS[band][3]


WX, BX = 340, 1190

d.text((WX - 60, 300), "Тёплое · сеанс 2, Фон — сеанс 1", font=f_col, fill=(30, 30, 30))
d.text((BX - 60, 300), "Синее · сеанс 3, Тело и Край крыла — сеанс 1", font=f_col, fill=(30, 30, 30))

for x in (WX - 60, BX - 60):
    arrow(x, H - 70, 400, (90, 90, 90), width=5, head=20)

# Warm column, bottom to top.
fg, sub = colors(2)
pile(WX, row(2, 1), "252024", "Фон", "тон 1,2–1,5 · на холсте 1, 32, 28, 15", fg, sub,
     [(14, 3), (7, 1), (8, 0.3)], "№ 15 — плюс умбра, до 1,8")
pile(WX, row(2, 0), "573224", "Тёплый фон", "тон 2,5–3 · на холсте 6, 29, 14, 30", fg, sub,
     [(7, 2), (6, 1.5), (4, 0.4)])
fg, sub = colors(1)
pile(WX, row(1, 1), "8B4718", "Тень лепестка", "тон 3–4,9 · на холсте 4, 23, 31, 10 · 21, 22, 25", fg, sub,
     [(4, 2), (6, 1.2), (5, 0.5)], "темнее: + тёплый фон, до 3")
pile(WX, row(1, 0), "CE5E00", "Пятна на крыле", "тон 5,3 · на холсте 2, 13", fg, sub)
fg, sub = colors(0)
pile(WX, row(0, 1), "D79D46", "Цветок", "тон 5,8–6,9 · на холсте 19, 12, 26, 5", fg, sub,
     [(4, 3), (9, 1), (2, 1)], "№ 19 — плюс капля сиены, 5,8")
pile(WX, row(0, 0), "FFC75B", "Блик цветка", "тон 8,3 · на холсте 27", fg, sub)
branch(WX, row(0, 1), row(0, 0), 1, colors(0)[0])
branch(WX, row(0, 1), row(1, 0), 9, colors(0)[0])

# Blue column, bottom to top.
fg, sub = colors(2)
pile(BX, row(2, 1), "121C30", "Тело", "тон 1,0 · на холсте 7, усики и лапки", fg, sub,
     [(14, 2), (11, 1)])
pile(BX, row(2, 0), "112E4C", "Край крыла", "тон 1,8 · на холсте 17", fg, sub,
     [(14, 2), (11, 2), (12, 0.3)])
fg, sub = colors(1)
pile(BX, row(1, 1), "005494", "Крыло", "тон 2,7–4,3 · на холсте 8, 11, 20 · 3, 16", fg, sub,
     [(11, 3), (1, 1), (12, 0.3)], "светлее: + белила. № 11 — капля тёплого фона")
pile(BX, row(1, 0), "007ECC", "Полоса крыла", "тон 5,1 · на холсте 18", fg, sub)
fg, sub = colors(0)
pile(BX, row(0, 1), "6196E4", "Свет крыла", "тон 6,2–6,8 · на холсте 9, 24", fg, sub,
     [(10, 2), (2, 2), (12, 0.25)])
d.text((BX - 20, row(0, 0) - 40), "Светлее 6,8 на крыле ничего нет — отдельного блика не мешать.",
       font=f_small, fill=colors(0)[1])
d.text((BX - 20, row(0, 0) - 14), "Для мастихина: Свет крыла + капля белил.", font=f_small, fill=colors(0)[1])
branch(BX, row(0, 1), row(1, 0), 11, colors(0)[0])

R = 26


def blob(x, y, n):
    name, color = PAINT[n]
    kind = TEMPERATURE[n]
    if n in HOLLOW:
        shape(kind, x, y, R, None, outline=(40, 40, 40))
        ctext(x, y - 12, str(n), f_num, (30, 30, 30))
        ctext(x, y + R + 6, name, f_edge, (25, 25, 25))
        ctext(x, y + R + 26, "не выдавливать", f_edge, (25, 25, 25))
    else:
        shape(kind, x, y, R, color)
        ctext(x, y - 12, str(n), f_num, ink(color))
        ctext(x, y + R + 6, name, f_edge, (25, 25, 25))
    if n == 14:
        ctext(x, y + R + 26, "умбра 1 : ультрамарин 1", f_edge, (25, 25, 25))
        ctext(x, y + R + 46, "тон 1,5–2", f_edge, (25, 25, 25))


for i in range(9):
    blob(250 + i * 198, 200, i + 1)

for n, y in zip(range(10, 15), [470, 760, 1060, 1380, 1760]):
    blob(2125, y, n)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "palette-shapes.jpg")
img.save(out, quality=93)
print(out)
