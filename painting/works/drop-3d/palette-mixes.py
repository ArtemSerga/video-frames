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
    15: ("медиум", (236, 224, 188)),
}

# Tubes this palette does not squeeze; drawn hollow.
HOLLOW = {2, 6, 8, 10, 12, 13}

# Millilitres to squeeze for an A6 canvas: thin darks, thick lights.
ML = {1: "3 мл", 3: "след", 4: "0,2 мл", 5: "1,5 мл", 7: "0,7 мл", 9: "след", 11: "0,7 мл"}
BASE_RING = (226, 170, 40)

# Same code as the colour wheel: circle warm, square cold, hexagon cool or neutral.
TEMPERATURE = {
    1: "hex", 2: "hex", 3: "square", 4: "circle", 5: "circle", 6: "circle", 7: "hex",
    8: "square", 9: "circle", 10: "square", 11: "circle", 12: "square", 13: "square", 14: "hex",
    15: "hex",
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


d.text((40, 28), "Капля: три базы и что из них выводится · A6", font=f_title, fill=(28, 28, 28))

d.rounded_rectangle((28, 110, W - 28, H - 24), radius=30, fill=(158, 160, 158), outline=(90, 90, 90), width=3)

R = 48
TUBE_Y = 188


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
    if n in ML:
        ctext(x, ty, ML[n], f_num, (150, 40, 20))


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

WX, DX, BX = 170, 980, 1660
BAND_L, BAND_R = 60, 2340
FIRST_BAND_TOP = 420

# id: (column x, value used for height, colour, name, line, base recipe or None, note)
PILES = {
    "glow": (WX, 8.6, "E4DDC0", "Сияние", "тон 8,5–8,7 · дно капли", None, "густо"),
    "gold": (WX, 7.1, "C8AE6E", "Золото", "тон 7 · кольцо на дне", None, "из холста: 6 + 1 кадм. жёлт."),
    "rim": (WX, 6.0, "AE8C62", "Рыжий край", "тон 6 · правый край", None, None),
    "flash": (DX, 9.9, "FAFCF8", "Блик", "тон 9,9 · белила, густо", None, None),
    "canvas": (DX, 6.8, "AAA497", "Холст", "тон 6,8 · тонировка", [(1, 5), (5, 3), (11, 1)], "с водой — втереть"),
    "umber": (DX, 2.5, "4E3628", "Умбра", "тон 2,5 · рисунок, хвост", [(7, 1)], "медиум 1 : 1 — лессировка"),
    "core": (DX, 2.0, "34271C", "Ядро тени", "тон 1,7–2 · у касания", None, None),
    "reflex": (BX, 7.8, "C2C4C4", "Рефлекс", "тон 7,8 · левый край", None, "кроет, без медиума"),
    "lav": (BX, 6.2, "98959E", "Лаванда", "тон 6,2 · дымка сверху", None, "из холста: 12 + 1 ультрам."),
    "bluegrey": (BX, 6.1, "929690", "Серо-голубой", "тон 6,1 · шейка", None, "обе: медиум 1 : 2 — вуаль"),
    "grey": (BX, 4.5, "6A6D66", "Серый край", "тон 4,5 · края шейки", None, None),
    "dshade": (BX, 2.7, "343932", "Тень капли", "тон 2,5–3 · левый бок", None, None),
    "dark": (BX, 1.75, "1C1E28", "Тёмный замес", "тон 1,5–2 · без белил", [(7, 1), (11, 1)], "до нейтрального"),
}

# A pile added to another pile is drawn as its own colour with this short name.
LABEL = {"dark": "тёмный", "umber": "умбра"}

# Steps of one sitting, rainbow order: step 1 red ... step 7 violet.
STEP_COLOUR = {1: (232, 48, 48), 2: (246, 138, 22), 3: (250, 214, 34), 4: (64, 178, 76),
                  5: (64, 170, 232), 6: (46, 86, 222), 7: (152, 72, 204)}
STEPS = {"canvas": (1,), "umber": (2, 7), "core": (2,), "dark": (2, 4), "gold": (3,), "glow": (3,),
         "rim": (3,), "dshade": (4,), "grey": (4,), "bluegrey": (4,), "lav": (4,), "reflex": (4, 6),
         "flash": (6,)}

# parent, child, parent parts, [(added paint or pile, parts)], lane offset, lane label side
LINKS = [
    ("gold", "glow", 1, [(1, 2)], 0, None),
    ("gold", "rim", 3, [(9, 0.3), ("umber", 0.3)], 0, None),
    ("umber", "core", 2, [("dark", 1)], 0, None),
    ("lav", "reflex", 1, [(1, 1)], 0, None),
    ("lav", "bluegrey", 20, [(3, 1)], 0, None),
    ("dark", "dshade", 1, [(15, 1)], 0, None),
    ("dshade", "grey", 1, [(15, 2)], 0, None),
]

BAND_STYLE = [
    ((232, 226, 210), (30, 30, 30), (80, 80, 80), "Света   ·   тон 6–9"),
    ((190, 168, 142), (28, 26, 24), (60, 52, 44), "Средние   ·   тон 3–6"),
    ((54, 52, 50), (236, 232, 224), (196, 192, 186), "Тени   ·   тон 1–3"),
]

NAME_UP, LABEL_ROOM, TITLE_ROOM, BAND_PAD, BAND_GAP = 82, 86, 70, 30, 15
SAME_ROW, CROSS_STEP, CROSS_ROOM = 0.12, 30, 90


def band_of(v):
    return 0 if v >= 6 else 1 if v >= 3 else 2


# A link that crosses into the next band carries its label at the foot of the upper band.
CROSSERS = {max(a, b, key=lambda k: PILES[k][1]) for a, b, _p, _a, lane, _s in LINKS
            if not lane and band_of(PILES[a][1]) != band_of(PILES[b][1])}


def below(pid):
    parts, note = PILES[pid][5], PILES[pid][6]
    if parts:
        return 172 if note else 115
    return 66 if note else 14


def layout(pad):
    # Lighter is always higher, in every column; near-equal values share a row.
    ys, last_in_col, prev = {}, {}, None
    for pid in sorted(PILES, key=lambda k: -PILES[k][1]):
        x, v = PILES[pid][:2]
        if prev is None:
            y = FIRST_BAND_TOP + TITLE_ROOM + NAME_UP
        else:
            py, pv = prev
            y = py + (CROSS_STEP if pv - v > SAME_ROW else 0)
            if band_of(v) != band_of(pv):
                lowest = max(yy + below(k) + (CROSS_ROOM if k in CROSSERS else 0) for k, yy in ys.items())
                y = max(y, lowest + BAND_PAD + BAND_GAP + TITLE_ROOM + NAME_UP)
        if x in last_in_col:
            k = last_in_col[x]
            y = max(y, ys[k] + below(k) + LABEL_ROOM + pad + NAME_UP)
        ys[pid] = y
        last_in_col[x] = pid
        prev = (y, v)
    return ys


def band_rects(ys):
    tops, bottoms = [], []
    for b in range(3):
        members = [k for k in ys if band_of(PILES[k][1]) == b]
        tops.append(min(ys[k] for k in members) - NAME_UP - TITLE_ROOM)
        bottoms.append(max(ys[k] + below(k) + (CROSS_ROOM if k in CROSSERS else 0) for k in members) + BAND_PAD)
    for b in range(2):
        bottoms[b] = tops[b + 1] - BAND_GAP
    return list(zip(tops, bottoms))


pad = max(p for p in range(0, 300, 5) if band_rects(layout(p))[2][1] <= H - 50)
Y = layout(pad)
BANDS = [(t, b) + BAND_STYLE[i] for i, (t, b) in enumerate(band_rects(Y))]
for top, bottom, bg, fg, _sub, title in BANDS:
    d.rounded_rectangle((BAND_L, top, BAND_R, bottom), radius=24, fill=bg)
    d.text((BAND_R - 26 - d.textlength(title, font=f_zone), top + 18), title, font=f_zone, fill=fg)


def text_on(y):
    for top, bottom, _bg, fg, _sub, _t in BANDS:
        if top <= y <= bottom:
            return fg
    return (25, 25, 25)


LINK_R = 33


def pos(pid):
    return PILES[pid][0], Y[pid]


def pile_radius(pid):
    return 60 if PILES[pid][5] else 48


def halo_line(points, width=4):
    d.line(points, fill=(240, 240, 236), width=width + 5, joint="curve")
    d.line(points, fill=(45, 45, 45), width=width, joint="curve")


def halo_head(x, y, up):
    s = -1 if up else 1
    tri = [(x, y), (x - 14, y - s * 22), (x + 14, y - s * 22)]
    d.polygon(tri, fill=(45, 45, 45), outline=(240, 240, 236))


def added_look(p):
    if isinstance(p, str):
        return LABEL[p], "circle", hexrgb(PILES[p][2])
    return PAINT[p][0], TEMPERATURE[p], PAINT[p][1]


def link_label_width(added):
    return 2 * LINK_R + sum(48 + 2 * LINK_R + 12 + d.textlength(added_look(p)[0], font=f_small) for p, _ in added)


def link(parent, child, p_parts, added, lane, side):
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
        if side == "left":
            lab_x, lab_y = lx - link_label_width(added) - 34, cy + 270
        else:
            lab_x, lab_y = lx + 34, (py + cy) / 2
    else:
        halo_line([(px, y0), (px, y1)])
        halo_head(px, y1, up)
        upper, lower = (child, parent) if up else (parent, child)
        lab_x, lab_y = px + 22, (Y[upper] + below(upper) + Y[lower] - NAME_UP) / 2
        if upper in CROSSERS:
            lab_y = (Y[upper] + below(upper) + BANDS[band_of(PILES[upper][1])][1]) / 2
    fg = text_on(lab_y)
    edge = (35, 35, 35) if ink(fg) == (245, 245, 245) else (215, 215, 215)
    if lane:
        d.rounded_rectangle((lab_x - 12, lab_y - 44, lab_x + link_label_width(added) + 12, lab_y + 44),
                            radius=16, fill=(54, 52, 50))
        fg, edge = (236, 232, 224), (215, 215, 215)
    mark(lab_x + LINK_R, lab_y, LINK_R, "circle", hexrgb(PILES[parent][2]), p_parts, edge)
    x = lab_x + 2 * LINK_R
    for paint, a_parts in added:
        name, kind, colour = added_look(paint)
        d.text((x + 24, lab_y), "+", font=f_name, fill=fg, anchor="mm")
        mark(x + 48 + LINK_R, lab_y, LINK_R, kind, colour, a_parts, edge)
        x += 48 + 2 * LINK_R + 12
        d.text((x, lab_y), name, font=f_small, fill=fg, anchor="lm")
        x += d.textlength(name, font=f_small)


def step_tag(x, y, steps):
    parts = [(f"шаг {steps[0]}", STEP_COLOUR[steps[0]])]
    for n in steps[1:]:
        parts += [(" и ", (200, 196, 190)), (str(n), STEP_COLOUR[n])]
    width = sum(d.textlength(t, font=f_name) for t, _ in parts)
    top, bottom = d.textbbox((x, y), "сеанс", font=f_name)[1::2]
    d.rounded_rectangle((x - 12, top - 8, x + width + 12, bottom + 8), radius=14, fill=(54, 52, 50))
    for text, colour in parts:
        d.text((x, y), text, font=f_name, fill=colour)
        x += d.textlength(text, font=f_name)


def pile(pid):
    x, v, hexcol, name, line, parts, note = PILES[pid]
    y = Y[pid]
    fg, sub = BANDS[band_of(v)][3], BANDS[band_of(v)][4]
    r = pile_radius(pid)
    if parts:
        d.ellipse((x - r - 14, y - r - 14, x + r + 14, y + r + 14), outline=BASE_RING, width=10)
    edge = (35, 35, 35) if ink(fg) == (245, 245, 245) else (215, 215, 215)
    d.ellipse((x - r, y - r, x + r, y + r), fill=hexrgb(hexcol), outline=edge, width=3)
    tx = x + 96
    d.text((tx, y - NAME_UP), name, font=f_name, fill=fg)
    step_tag(tx + d.textlength(name, font=f_name) + 28, y - NAME_UP, STEPS[pid])
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

for i, s in enumerate(["Тёмные капли — лессировка:", "без белил, тон даёт медиум.",
                       "Больше медиума — светлее,", "сквозь неё виден холст."]):
    d.text((DX - 30, BANDS[1][0] + 85 + i * 48), s, font=f_small, fill=BANDS[1][4])

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "palette-tree-2.jpg")
img.save(out, quality=93)
print(out, "pad", pad)
