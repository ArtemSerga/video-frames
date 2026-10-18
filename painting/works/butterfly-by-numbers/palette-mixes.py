import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 2400, 3394  # A4 portrait, 1 : 1.414
img = Image.new("RGB", (W, H), (236, 230, 218))
d = ImageDraw.Draw(img)

reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
boldp = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
f_title = ImageFont.truetype(boldp, 60)
f_zone = ImageFont.truetype(boldp, 42)
f_col = ImageFont.truetype(boldp, 42)
f_name = ImageFont.truetype(boldp, 44)
f_line = ImageFont.truetype(reg, 40)
f_num = ImageFont.truetype(boldp, 32)
f_edge = ImageFont.truetype(reg, 37)
f_small = ImageFont.truetype(reg, 40)
f_part = ImageFont.truetype(boldp, 30)

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

# Tubes this palette does not squeeze; drawn hollow.
HOLLOW = {3, 13}
BASE_RING = (226, 170, 40)

# Same code as the colour wheel: circle warm, square cold, hexagon cool or neutral.
TEMPERATURE = {
    1: "hex", 2: "hex", 3: "square", 4: "circle", 5: "circle", 6: "circle", 7: "hex",
    8: "square", 9: "circle", 10: "square", 11: "circle", 12: "square", 13: "square", 14: "hex",
}


def hexrgb(s):
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def ctext(x, y, s, font, fill):
    d.text((x - d.textlength(s, font=font) / 2, y), s, font=font, fill=fill)


def shape_points(kind, x, y, r):
    # Equal area with a circle of radius r, so no shape reads as a bigger share.
    if kind == "square":
        h = r * math.sqrt(math.pi) / 2
        return [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)]
    R = r * math.sqrt(2 * math.pi / (3 * math.sqrt(3)))
    return [(x + R * math.cos(math.radians(60 * i - 90)),
             y + R * math.sin(math.radians(60 * i - 90))) for i in range(6)]


def shape(kind, x, y, r, fill, outline=(35, 35, 35), width=3):
    if kind == "circle":
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=width)
    else:
        d.polygon(shape_points(kind, x, y, r), fill=fill, outline=outline, width=width)


def ink(color):
    lum = 0.3 * color[0] + 0.59 * color[1] + 0.11 * color[2]
    return (20, 20, 20) if lum > 150 else (245, 245, 245)


def parts_label(amount):
    return f"{amount:g}".replace(".", ",")


def mark(x, y, r, kind, color, amount, outline):
    shape(kind, x, y, r, color, outline=outline)
    d.text((x, y), parts_label(amount), font=f_part, fill=ink(color), anchor="mm")


def munsell_grey(v):
    # Munsell value is close to L*/10; L* to an sRGB grey.
    y = ((v * 10 + 16) / 116) ** 3 if v * 10 > 8 else v * 10 / 903.3
    s = 12.92 * y if y <= 0.0031308 else 1.055 * y ** (1 / 2.4) - 0.055
    g = round(max(0, min(1, s)) * 255)
    return (g, g, g)


d.text((40, 28), "Бабочка: три базы и что из них выводится", font=f_title, fill=(28, 28, 28))

kx = 40
LEGEND_Y = 132
for text, kind in [("тёплый", "circle"), ("холодный", "square"), ("нейтральный", "hex"),
                   ("число — части", None), ("пустая — не выдавливать", "hollow")]:
    if kind == "hollow":
        shape("square", kx + 24, LEGEND_Y, 24, None, outline=(40, 40, 40))
        kx += 60
    elif kind:
        shape(kind, kx + 24, LEGEND_Y, 24, (200, 200, 200))
        kx += 60
    d.text((kx, LEGEND_Y), text, font=f_small, fill=(55, 55, 55), anchor="lm")
    kx += d.textlength(text, font=f_small) + 46

d.rounded_rectangle((28, 184, W - 28, H - 24), radius=30, fill=(158, 160, 158), outline=(90, 90, 90), width=3)

R = 48
TUBE_Y = 262


def tube_lines(n):
    name = PAINT[n][0]
    return name.split(" ", 1) if d.textlength(name, font=f_edge) > 150 else [name]


def tube_width(n):
    return max(2 * R, max(d.textlength(s, font=f_edge) for s in tube_lines(n)))


def blob(x, y, n):
    name, color = PAINT[n]
    kind = TEMPERATURE[n]
    if n in HOLLOW:
        shape(kind, x, y, R, None, outline=(40, 40, 40))
        d.text((x, y), str(n), font=f_num, fill=(30, 30, 30), anchor="mm")
    else:
        shape(kind, x, y, R, color)
        d.text((x, y), str(n), font=f_num, fill=ink(color), anchor="mm")
    ty = y + R + 8
    for s in tube_lines(n):
        ctext(x, ty, s, f_edge, (25, 25, 25))
        ty += 42


# Pack tubes by label width, then spread the slack evenly; the divider sits between 9 and 10.
TUBES, DIVIDER, LEFT, RIGHT = list(range(1, 14)), 70, 60, W - 60
gaps = [(tube_width(a) + tube_width(b)) / 2 + (DIVIDER if a == 9 else 0) for a, b in zip(TUBES, TUBES[1:])]
used = sum(gaps) + (tube_width(1) + tube_width(13)) / 2
extra = (RIGHT - LEFT - used) / len(gaps)
x = LEFT + tube_width(1) / 2
for i, n in enumerate(TUBES):
    blob(x, TUBE_Y, n)
    if n == 9:
        sep_x = x + (gaps[i] + extra) / 2
        d.line([(sep_x, TUBE_Y - 60), (sep_x, TUBE_Y + 140)], fill=(70, 70, 70), width=4)
    if i < len(gaps):
        x += gaps[i] + extra

SCALE_X, BAND_L, BAND_R, BAND_H, BAND_GAP, SLOT = 112, 180, 2340, 920, 15, 280
BANDS = [
    (560, (232, 226, 210), (30, 30, 30), (80, 80, 80), "Света   ·   тон 6–9", (9, 6)),
    (1495, (190, 168, 142), (28, 26, 24), (60, 52, 44), "Средние   ·   тон 3–6", (6, 3)),
    (2430, (54, 52, 50), (236, 232, 224), (196, 192, 186), "Тени   ·   тон 1–3", (3, 1)),
]
for top, bg, fg, _sub, title, _rng in BANDS:
    d.rounded_rectangle((BAND_L, top, BAND_R, top + BAND_H), radius=24, fill=bg)
    d.text((BAND_R - 26 - d.textlength(title, font=f_zone), top + 18), title, font=f_zone, fill=fg)

ctext(SCALE_X, BANDS[0][0] - 52, "тон", f_small, (30, 30, 30))
for top, _bg, _fg, _sub, _t, (hi, lo) in BANDS:
    values = list(range(hi, lo - 1, -1))
    step = (BAND_H - 40) / len(values)
    for i, v in enumerate(values):
        cy = top + 20 + step * (i + 0.5)
        grey = munsell_grey(v)
        d.rounded_rectangle((SCALE_X - 44, cy - 44, SCALE_X + 44, cy + 44), radius=10, fill=grey,
                            outline=(60, 60, 60), width=2)
        d.text((SCALE_X, cy), str(v), font=f_name, fill=ink(grey), anchor="mm")


def slot_y(band, slot):
    return BANDS[band][0] + 160 + slot * SLOT


def text_on(y):
    for top, _bg, fg, _sub, _t, _r in BANDS:
        if top <= y <= top + BAND_H:
            return fg
    return (25, 25, 25)


WX, DX, BX = 270, 900, 1640
d.text((WX - 70, 440), "Тёплое · сеанс 2", font=f_col, fill=(30, 30, 30))
d.text((DX - 70, 440), "Тёмное · сеанс 1", font=f_col, fill=(30, 30, 30))
d.text((BX - 70, 440), "Синее · сеанс 3", font=f_col, fill=(30, 30, 30))
d.text((BX - 70, 494), "Тело и Край — сеанс 1", font=f_small, fill=(55, 55, 55))

# id: (column x, band, slot, colour, name, line, base recipe or None, note)
PILES = {
    "flash": (WX, 0, 0, "FFC75B", "Блик цветка", "тон 8,3 · искры, тычинки", None, None),
    "flower": (WX, 0, 1, "D58529", "Цветок", "тон 5,8–6,9 · лепестки на свету", None,
               "тусклее: + охра · глубже: + сиена"),
    "orange": (WX, 0, 2, "F0901E", "Оранжевая база", "сама на холст не идёт", [(4, 3), (9, 1)], None),
    "spots": (WX, 1, 0, "BA6B2E", "Пятна на крыле", "тон 5,3", None, None),
    "shade_l": (WX, 1, 1, "A5572F", "Тень лепестка светлая", "тон 4,6–4,9", None, None),
    "shade": (WX, 1, 2, "823C1A", "Тень лепестка", "тон 3,1–3,8", None, None),
    "warm_bg": (WX, 2, 0, "573224", "Тёплый фон", "тон 2,5–3,2", None, None),
    "plum_l": (DX, 2, 0, "55474F", "Слива светлая", "тон около 3 · пятна фона", None,
               "лиловит: + капля умбры"),
    "bg": (DX, 2, 1, "30222B", "Фон · слива", "тон 1,2–1,5", None, "у цветов: + умбра, до 1,8"),
    "dark": (DX, 2, 2, "1C1E28", "Тёмный замес", "мой чёрный · тон 1,5–2", [(7, 1), (11, 1)],
             "до нейтрального"),
    "light": (BX, 0, 1, "6196E4", "Свет крыла", "тон 6,2–6,8", None, "зеленит: + синяя база"),
    "stripe": (BX, 1, 0, "007ECC", "Полоса крыла", "тон 5,1", None, None),
    "wing_l": (BX, 1, 1, "0066BA", "Крыло светлое", "тон 3,5–4,3", None, None),
    "wing": (BX, 1, 2, "0B3B8B", "Крыло", "тон 2,7–2,8", None, "сероватое: + тёплый фон"),
    "blue": (BX, 2, 0, "1E2A8A", "Синяя база", "тон около 2,3", [(11, 3), (12, 0.3)], None),
    "edge": (BX, 2, 1, "112E4C", "Край крыла", "тон 1,8", None, None),
    "body": (BX, 2, 2, "121C30", "Тело", "тон 1,0 · усики, лапки", None, None),
}

# parent, child, parent parts, [(added paint, parts)], lane offset for links that skip piles
LINKS = [
    ("orange", "flower", 4, [(2, 1)], 0),
    ("flower", "flash", 1, [(1, 1)], 0),
    ("orange", "spots", 2, [(6, 1)], 0),
    ("spots", "shade_l", 3, [(6, 1)], 0),
    ("shade_l", "shade", 1, [(7, 1)], 0),
    ("shade", "warm_bg", 1, [(7, 1)], 0),
    ("dark", "bg", 3, [(7, 1), (8, 0.3)], 0),
    ("bg", "plum_l", 3, [(1, 1)], 0),
    ("blue", "wing", 3, [(1, 1)], 0),
    ("wing", "wing_l", 2, [(1, 1)], 0),
    ("blue", "edge", 1, [(14, 1)], 0),
    ("edge", "body", 1, [(14, 1)], 0),
    ("blue", "stripe", 1, [(10, 10)], -115),
    ("stripe", "light", 2, [(2, 1)], 0),
]

LINK_R = 33


def pos(pid):
    x, band, slot = PILES[pid][:3]
    return x, slot_y(band, slot)


def pile_radius(pid):
    return 60 if PILES[pid][6] else 48


def halo_line(points, width=4):
    d.line(points, fill=(240, 240, 236), width=width + 5, joint="curve")
    d.line(points, fill=(45, 45, 45), width=width, joint="curve")


def halo_head(x, y, up):
    s = -1 if up else 1
    tri = [(x, y), (x - 14, y - s * 22), (x + 14, y - s * 22)]
    d.polygon(tri, fill=(45, 45, 45), outline=(240, 240, 236))


def link_label_width(added):
    return 2 * LINK_R + sum(48 + 2 * LINK_R + 12 + d.textlength(PAINT[p][0], font=f_small) for p, _ in added)


def link(parent, child, p_parts, added, lane):
    px, py = pos(parent)
    cx, cy = pos(child)
    up = cy < py
    s = -1 if up else 1
    y0 = py + s * (pile_radius(parent) + 6)
    y1 = cy - s * (pile_radius(child) + 8)
    if lane:
        lx = px + lane
        halo_line([(px - pile_radius(parent), py), (lx, py), (lx, cy), (cx - pile_radius(child) - 24, cy)])
        tip = cx - pile_radius(child) - 6
        d.polygon([(tip, cy), (tip - 22, cy - 14), (tip - 22, cy + 14)], fill=(45, 45, 45), outline=(240, 240, 236))
        lab_x, lab_y = lx - link_label_width(added) - 34, cy + 140
    else:
        halo_line([(px, y0), (px, y1)])
        halo_head(px, y1, up)
        lab_x, lab_y = px + 22, (y0 + y1) / 2
        if PILES[parent][6] and not up:
            lab_y = max(lab_y, py + 159)
    fg = text_on(lab_y)
    edge = (35, 35, 35) if ink(fg) == (245, 245, 245) else (215, 215, 215)
    if lane:
        d.rounded_rectangle((lab_x - 12, lab_y - 44, lab_x + link_label_width(added) + 12, lab_y + 44),
                            radius=16, fill=(54, 52, 50))
        fg, edge = (236, 232, 224), (215, 215, 215)
    mark(lab_x + LINK_R, lab_y, LINK_R, "circle", hexrgb(PILES[parent][3]), p_parts, edge)
    x = lab_x + 2 * LINK_R
    for paint, a_parts in added:
        d.text((x + 24, lab_y), "+", font=f_name, fill=fg, anchor="mm")
        mark(x + 48 + LINK_R, lab_y, LINK_R, TEMPERATURE[paint], PAINT[paint][1], a_parts, edge)
        x += 48 + 2 * LINK_R + 12
        d.text((x, lab_y), PAINT[paint][0], font=f_small, fill=fg, anchor="lm")
        x += d.textlength(PAINT[paint][0], font=f_small)


def pile(pid):
    x, band, slot, hexcol, name, line, parts, note = PILES[pid]
    y = slot_y(band, slot)
    fg, sub = BANDS[band][2], BANDS[band][3]
    r = pile_radius(pid)
    if parts:
        d.ellipse((x - r - 14, y - r - 14, x + r + 14, y + r + 14), outline=BASE_RING, width=10)
    edge = (35, 35, 35) if ink(fg) == (245, 245, 245) else (215, 215, 215)
    d.ellipse((x - r, y - r, x + r, y + r), fill=hexrgb(hexcol), outline=edge, width=3)
    tx = x + 96
    d.text((tx, y - 82), name, font=f_name, fill=fg)
    d.text((tx, y - 28), line, font=f_line, fill=sub)
    ny = y + 26
    if parts:
        rx = tx
        for key, amount in parts:
            mark(rx + 45, y + 70, 45, TEMPERATURE[key], PAINT[key][1], amount, edge)
            rx += 108
        ny = y + 132
    if note:
        d.text((tx, ny), note, font=f_small, fill=sub)


for args in LINKS:
    link(*args)
for pid in PILES:
    pile(pid)

for i, s in enumerate(["Светлее 6,8 на крыле нет —", "отдельного блика не мешать.",
                       "Мастихин: Свет крыла + белила."]):
    d.text((BX - 30, slot_y(0, 0) - 84 + i * 48), s, font=f_small, fill=BANDS[0][3])

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "palette-tree-5.jpg")
img.save(out, quality=93)
print(out)
