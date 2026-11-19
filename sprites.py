"""Drawn characters for Tiny Spanish: Emma, Mateo, Cami and Santi (chibi, soft flat colours), animated by code.
Same drawing technique as Tiny French (smoothed layers, lock_pts hair), with an original cast."""
import functools, math
from PIL import Image, ImageDraw, ImageFilter

CHAR_SCALE = 0.9
INK = (92, 52, 56)
CHARS = {
    "Emma": dict(voice="es-US-PalomaNeural", accent=(86, 190, 150), x=16),
    "Mateo": dict(voice="es-MX-JorgeNeural", accent=(226, 112, 58), x=560),
    "Cami": dict(voice="es-CO-SalomeNeural", accent=(214, 51, 108), x=16),
    "Santi": dict(voice="es-CO-GonzaloNeural", accent=(31, 159, 168), x=560),
}
CAST = tuple(CHARS)


def _bez(p0, p1, p2, n=14):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


def lock_pts(root, ctrl, tip, width, n=14):
    """Pointed hair lock along a curve: thick in the middle, sharp at the tip."""
    c = _bez(root, ctrl, tip, n)
    left, right = [], []
    for i, (x, y) in enumerate(c):
        a = c[min(i + 1, n)]; b = c[max(i - 1, 0)]
        dx, dy = a[0] - b[0], a[1] - b[1]; L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = width * math.sin(math.pi * (0.12 + 0.88 * i / n) ** 0.9) * (1 - 0.15 * i / n) / 2
        if i == n:
            w = 0
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def _smooth(layer, S, r=5, thr=120):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(r * S)).point(lambda v: 255 if v > thr else 0)
    layer.putalpha(a.filter(ImageFilter.GaussianBlur(0.8 * S)))
    return layer


def _eyes(d, P, S, blink, iris=((58, 30, 46), (108, 56, 70)), lash=False):
    for ex in (214, 346):
        if blink:
            d.arc(P(ex - 30, 346, ex + 30, 392), 200, 340, fill=(60, 34, 46), width=int(7 * S))
            continue
        d.ellipse(P(ex - 27, 318, ex + 27, 396), fill=iris[0])
        d.ellipse(P(ex - 20, 368, ex + 20, 394), fill=iris[1])
        d.ellipse(P(ex - 17, 328, ex + 4, 354), fill=(255, 255, 255))
        d.ellipse(P(ex + 6, 368, ex + 17, 380), fill=(255, 255, 255))
        d.arc(P(ex - 31, 312, ex + 31, 378), 195, 345, fill=(52, 28, 40), width=int(7 * S))


def _mouth(d, P, S, mouth, lip=None):
    if mouth == 0:
        d.arc(P(262, 410, 298, 436), 15, 165, fill=lip or INK, width=int((7 if lip else 5) * S))
    elif mouth == 1:
        d.ellipse(P(268, 414, 292, 438), fill=(128, 48, 62))
        if lip: d.arc(P(266, 412, 294, 440), 0, 360, fill=lip, width=int(3 * S))
    else:
        d.ellipse(P(260, 410, 300, 446), fill=(128, 48, 62)); d.ellipse(P(268, 430, 292, 444), fill=(238, 128, 140))
        if lip: d.arc(P(258, 408, 302, 448), 0, 360, fill=lip, width=int(4 * S))


@functools.lru_cache(None)
def _character(name, mouth, blink):
    S = 2 * CHAR_SCALE
    w, h = int(560 * S), int(760 * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda *v: [int(x * S) for x in v]
    PP = lambda pts: [(x * S, y * S) for x, y in pts]
    ell = lambda box, fill, dd=None: (dd or d).ellipse(P(*box), fill=fill)
    poly = lambda pts, fill, dd=None: (dd or d).polygon(PP(pts), fill=fill)
    mir = lambda pts: [(560 - x, y) for x, y in pts]

    def layer(draw_fn, color, r=5):
        L = Image.new("RGBA", (w, h), color + (0,)); dd = ImageDraw.Draw(L); draw_fn(dd)
        L = Image.composite(Image.new("RGBA", (w, h), color + (255,)), L, L.getchannel("A"))
        return _smooth(L, S, r)

    def put(L):
        nonlocal im, d
        im = Image.alpha_composite(im, L); d = ImageDraw.Draw(im)

    def line(pts, col, width):
        d.line(PP(pts), fill=col, width=int(width * S), joint="curve")

    def blob(pts, col, r=5):
        put(layer(lambda dd: poly(pts, col, dd), col, r))

    def locks(specs, col, r=2, base_poly=None):
        def f(dd):
            if base_poly: poly(base_poly, col, dd)
            for root, ctrl, tip, wd in specs:
                poly(lock_pts(root, ctrl, tip, wd), col, dd)
        put(layer(f, col, r))

    def streaks(specs, col, wd=5):
        for root, ctrl, tip in specs:
            line(_bez(root, ctrl, tip, 10), col, wd)

    def brows(col, y=298, wd=5):
        d.arc(P(178, y, 244, y + 28), 200, 340, fill=col, width=int(wd * S)); d.arc(P(316, y, 382, y + 28), 200, 340, fill=col, width=int(wd * S))

    BOY_BODY = [(112, 600), (124, 540), (160, 494), (226, 466), (334, 466), (400, 494), (436, 540), (448, 600), (452, 760), (108, 760)]
    SLIM_BODY = [(128, 600), (138, 544), (170, 498), (230, 466), (330, 466), (390, 498), (422, 544), (432, 600), (436, 760), (124, 760)]
    GIRL_BODY = [(150, 610), (160, 548), (186, 498), (240, 466), (320, 466), (374, 498), (400, 548), (410, 610), (414, 760), (146, 760)]
    CROWN = [(118, 262), (124, 190), (196, 126), (330, 116), (432, 184), (442, 262), (430, 226), (300, 214), (180, 226)]
    BOY_FRINGE = (((400, 150), (420, 215), (392, 262), 66), ((340, 140), (330, 225), (296, 276), 70), ((276, 132), (240, 215), (206, 282), 76),
                  ((206, 140), (166, 220), (150, 310), 74), ((140, 190), (118, 240), (124, 300), 50))
    GIRL_CROWN = [(112, 270), (118, 196), (196, 124), (330, 114), (436, 186), (448, 270), (430, 250), (300, 240), (170, 255)]
    after = []
    iris, lip = ((58, 30, 46), (108, 56, 70)), None

    def neck(skin):
        ell((246, 446, 314, 520), skin); poly([(244, 462), (316, 462), (306, 500), (254, 500)], skin)

    def ears(skin):
        ell((130, 316, 180, 396), skin); ell((380, 316, 430, 396), skin)

    if name == "Emma":
        skin = (252, 224, 205)
        hair, hair_d, hair_l = (217, 178, 111), (176, 136, 74), (242, 216, 152)
        mint, mint_d, cream, strap = (126, 214, 178), (86, 170, 136), (255, 243, 214), (138, 96, 64)
        iris = ((48, 118, 84), (118, 196, 142))
        def back(dd):
            ell((112, 112, 448, 440), hair, dd)
            poly(lock_pts((410, 196), (548, 250), (492, 470), 96), hair, dd)          # ponytail
            poly(lock_pts((420, 190), (520, 330), (440, 500), 60), hair, dd)
        put(layer(back, hair, 6))
        ell((384, 168, 428, 212), (232, 112, 120))                                      # hair tie
        blob(GIRL_BODY, mint, 6)                                                       # hoodie
        for x0, x1 in ((190, 176), (370, 384)): line([(x0, 496), (x1, 760)], strap, 22)   # backpack straps
        blob([(196, 466), (364, 466), (378, 524), (280, 566), (182, 524)], mint_d, 5)   # hood
        for sx in (250, 310):
            line([(sx, 520), (sx - 4 + (sx - 280) // 10, 612)], cream, 5); ell((sx - 6 + (sx - 280) // 10, 608, sx + 6 + (sx - 280) // 10, 622), cream)
        ell((396, 612, 424, 640), (255, 190, 120)); ell((402, 618, 418, 634), (232, 112, 120))   # travel patch
        neck(skin); ears(skin); ell((136, 154, 424, 462), skin)
        locks((((404, 140), (330, 160), (206, 290), 92), ((330, 126), (250, 170), (170, 300), 84), ((262, 126), (190, 180), (150, 310), 80), ((176, 132), (140, 220), (148, 310), 70)),
              hair, 2, base_poly=GIRL_CROWN)
        streaks((((390, 140), (320, 168), (216, 270)), ((300, 130), (240, 160), (186, 250))), hair_l, 6)
        brows(hair_d)
        for fx, fy in ((176, 410), (190, 420), (204, 412), (356, 412), (370, 420), (384, 410), (196, 402), (364, 402)):
            ell((fx - 3, fy - 3, fx + 3, fy + 3), (206, 140, 112))                     # freckles

    elif name == "Mateo":
        skin = (196, 140, 100)
        hair, hair_d, hair_l = (43, 29, 22), (26, 18, 14), (92, 66, 52)
        terra, terra_d, cream = (226, 112, 58), (178, 80, 38), (247, 230, 204)
        iris = ((52, 30, 22), (112, 72, 52))
        def back(dd):
            ell((112, 112, 448, 440), hair, dd)
            for b in ((140, 120, 230, 200), (210, 92, 320, 170), (300, 98, 410, 176), (364, 130, 440, 214)): ell(b, hair, dd)
        put(layer(back, hair, 6))
        blob(BOY_BODY, terra, 6)                                                       # shirt
        poly([(236, 474), (324, 474), (338, 760), (222, 760)], cream)                  # tee
        blob([(204, 466), (252, 470), (246, 536), (196, 504)], terra_d, 4); blob([(356, 466), (308, 470), (314, 536), (364, 504)], terra_d, 4)
        for by in (600, 650, 700): ell((274, by, 286, by + 12), (214, 190, 160))
        neck(skin); ears(skin); ell((136, 154, 424, 462), skin)
        for k in range(34):                                                            # light stubble on the jaw and chin only
            a = math.radians(48 + k * 2.6); r = 0.84 + 0.1 * ((k * 5) % 3) / 2
            sx, sy = 280 + 144 * r * math.cos(a), 308 + 154 * r * math.sin(a)
            if not (244 < sx < 316 and sy < 456) and sy > 414: ell((sx - 2.5, sy - 2.5, sx + 2.5, sy + 2.5), (122, 84, 62))
        locks(BOY_FRINGE, hair, 2, base_poly=CROWN)
        streaks((((390, 150), (360, 196), (330, 226)), ((300, 140), (250, 186), (214, 230))), hair_l, 5)
        brows(hair_d, 296, 7)

    elif name == "Cami":
        skin = (222, 168, 124)
        hair, hair_d, hair_l = (30, 20, 22), (18, 12, 14), (88, 62, 66)
        mag, mag_d, yel, gold = (214, 51, 108), (168, 34, 84), (255, 212, 59), (236, 184, 56)
        lip = (200, 30, 60)
        iris = ((52, 28, 28), (116, 66, 52))
        def back(dd):
            ell((108, 108, 452, 440), hair, dd)
            ell((128, 30, 252, 154), hair, dd); ell((308, 30, 432, 154), hair, dd)    # two high space buns
            poly(lock_pts((128, 250), (84, 330), (124, 420), 64), hair, dd); poly(lock_pts((432, 250), (476, 330), (436, 420), 64), hair, dd)
            for cx, cy in ((112, 404), (448, 404), (126, 436), (434, 436)): ell((cx - 26, cy - 26, cx + 26, cy + 26), hair, dd)   # loose curls
        put(layer(back, hair, 6))
        for bx in (170, 346): ell((bx, 138, bx + 44, 166), yel)                         # scrunchies
        blob(GIRL_BODY, mag, 6)                                                        # bomber
        poly([(238, 474), (322, 474), (336, 760), (224, 760)], yel)                    # yellow top
        blob([(206, 466), (254, 470), (248, 530), (198, 498)], mag_d, 4); blob([(354, 466), (306, 470), (312, 530), (362, 498)], mag_d, 4)
        for k in range(8):                                                             # sunflower pin
            a = k * math.pi / 4; px, py = 200 + 26 * math.cos(a), 640 + 26 * math.sin(a)
            ell((px - 14, py - 14, px + 14, py + 14), yel)
        ell((186, 626, 214, 654), (120, 70, 30))
        neck(skin); ears(skin); ell((136, 154, 424, 462), skin)
        locks((((176, 134), (140, 220), (168, 320), 70), ((262, 126), (232, 190), (236, 250), 80), ((330, 126), (352, 190), (330, 250), 80), ((404, 140), (432, 210), (412, 300), 64)),
              hair, 2, base_poly=GIRL_CROWN)
        streaks((((176, 140), (140, 214), (166, 280)), ((330, 130), (360, 190), (340, 250))), hair_l, 5)
        brows(hair, 290, 8)
        def hoops():
            for cx in (126, 434): d.ellipse(P(cx - 30, 392, cx + 30, 462), outline=gold, width=int(6 * S))
        after.append(hoops)

    elif name == "Santi":
        skin = (176, 120, 84)
        hair, hair_d, hair_l = (35, 26, 20), (20, 14, 10), (88, 70, 56)
        teal, teal_d, mustard, strap = (31, 159, 168), (20, 120, 128), (224, 165, 38), (62, 52, 46)
        iris = ((46, 28, 20), (104, 68, 46))
        def back(dd):
            ell((106, 100, 454, 440), hair, dd)
            for k in range(15):                                                        # curly outline
                a = math.radians(188 + k * 12.5); ell((280 + 186 * math.cos(a) - 34, 300 + 196 * math.sin(a) - 34, 280 + 186 * math.cos(a) + 34, 300 + 196 * math.sin(a) + 34), hair, dd)
        put(layer(back, hair, 6))
        blob(SLIM_BODY, mustard, 6)                                                    # tee
        blob([(138, 544), (170, 498), (226, 470), (246, 482), (240, 760), (128, 760), (126, 600)], teal, 6)   # utility vest
        blob([(422, 544), (390, 498), (334, 470), (314, 482), (320, 760), (432, 760), (434, 600)], teal, 6)
        for bx in ((150, 620, 226, 690), (334, 620, 410, 690)):
            d.rounded_rectangle(P(*bx), radius=int(10 * S), fill=teal_d)
        line([(176, 496), (392, 760)], strap, 14)                                      # camera strap
        d.rounded_rectangle(P(318, 660, 398, 726), radius=int(10 * S), fill=(48, 48, 56)); ell((340, 668, 376, 704), (150, 170, 182)); ell((348, 676, 368, 696), (40, 44, 52))
        neck(skin); ears(skin); ell((136, 154, 424, 462), skin)
        put(layer(lambda dd: poly([(146, 372), (148, 430), (190, 464), (280, 478), (370, 464), (412, 430), (414, 372), (392, 398), (356, 424), (318, 444), (280, 448), (242, 444), (204, 424), (168, 398)], hair, dd), hair, 4))   # short beard
        put(layer(lambda dd: poly([(238, 398), (280, 388), (322, 398), (300, 409), (280, 402), (260, 409)], hair, dd), hair, 2))   # moustache
        def curls(dd):
            for cx, cy, r in ((176, 170, 34), (226, 150, 36), (284, 142, 38), (342, 150, 36), (394, 172, 34), (150, 216, 28), (420, 216, 28), (200, 200, 24), (370, 204, 24)):
                ell((cx - r, cy - r, cx + r, cy + r), hair, dd)
        put(layer(curls, hair, 4))
        brows(hair_d, 298, 7)
        def shades():
            for cx in (216, 344): d.ellipse(P(cx - 38, 96, cx + 38, 168), fill=(56, 66, 78), outline=(30, 30, 36), width=int(8 * S)); d.arc(P(cx - 26, 106, cx - 6, 128), 200, 260, fill=(190, 214, 226), width=int(4 * S))
            line([(254, 128), (306, 128)], (30, 30, 36), 7)
        after.append(shades)

    else:
        raise KeyError(name)

    _eyes(d, P, S, blink, iris)
    ell((166, 398, 210, 422), (252, 188, 188)); ell((350, 398, 394, 422), (252, 188, 188))
    _mouth(d, P, S, mouth, lip)
    for fn in after: fn()
    return im.resize((int(560 * CHAR_SCALE), int(760 * CHAR_SCALE)), Image.LANCZOS)


@functools.lru_cache(maxsize=128)
def sprite(name, mouth, blink):
    """Render one of the four Tiny Spanish characters. An unknown speaker name gets Emma or Mateo's drawing (voice and colour come from CHARS)."""
    if name not in CAST:
        name = "Mateo" if str(CHARS.get(name, {}).get("voice", "")).endswith(("JorgeNeural", "GonzaloNeural")) else "Emma"
    return _character(name, int(mouth), bool(blink))
