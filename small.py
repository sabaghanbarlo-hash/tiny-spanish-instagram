#!/usr/bin/env python3
"""Tiny Spanish "Small" Reels: two friends sit in a place and chat; then words, a grammar tip, a quiz and a goodbye.

Script (.txt) -> 1080x1920 MP4 + .srt + .caption.txt + .cover.png + .json.
Free stack: edge-tts Spanish voices, Pillow drawing, FFmpeg.

Script format (see templates/reel.template.txt):
    title: Introducing Yourself
    episode: 1
    scene: cafe            (cafe, street, park, market, restaurant, airport, hotel, store, apartment/home, clinic ... or auto)
    cast: Emma, Mateo      (the two friends on screen: Emma, Mateo, Cami or Santi)
    hook: How do you introduce yourself in Spanish?     (optional big on-screen hook; default is the title)
    [hook] / [story] / [vocab] / [grammar] / [quiz] / [ending]    (optional section markers)
    Mateo: ¡Hola! ¿Cómo te llamas? | Hi! What's your name? | OH-lah. KOH-moh teh YAH-mahs
    vocab: me llamo | my name is | meh YAH-moh
    example: Me llamo Emma. | My name is Emma.
    grammar: Soy / eres (from ser) = I am / you are.
    quiz: How do you say "I'm from Chicago"? | Soy de Chicago | Me llamo Chicago | Eres de Chicago | A | Soy de + place.
"""
import argparse, asyncio, functools, glob, json, math, os, random, re, subprocess, sys, tempfile, time, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprites import sprite, CHARS  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 24000
CHAR_Y, TABLE_TOP, CARD_Y = 300, 885, 1040
BRAND = (214, 51, 108)
MAX_CHARS = 9000
SCENES = {
    "cafe": dict(top=(255, 244, 230), bot=(248, 228, 208), floor=(214, 170, 122), table=(224, 176, 126), edge=(190, 142, 98)),
    "bakery": dict(top=(255, 240, 226), bot=(250, 222, 200), floor=(206, 160, 116), table=(236, 196, 150), edge=(196, 150, 108)),
    "park": dict(top=(190, 226, 250), bot=(236, 248, 238), floor=(150, 204, 126), table=(196, 158, 114), edge=(150, 116, 82)),
    "classroom": dict(top=(240, 247, 236), bot=(250, 252, 244), floor=(206, 176, 136), table=(226, 196, 150), edge=(176, 142, 102)),
    "station": dict(top=(196, 224, 246), bot=(236, 246, 252), floor=(156, 156, 170), table=(238, 204, 100), edge=(126, 126, 140)),
    "store": dict(top=(232, 246, 255), bot=(246, 252, 255), floor=(214, 218, 226), table=(124, 198, 172), edge=(86, 152, 130)),
    "restaurant": dict(top=(252, 232, 214), bot=(246, 214, 190), floor=(150, 98, 72), table=(250, 246, 240), edge=(206, 64, 78)),
    "market": dict(top=(196, 228, 250), bot=(240, 248, 236), floor=(206, 190, 160), table=(214, 164, 110), edge=(158, 112, 76)),
    "library": dict(top=(246, 236, 220), bot=(238, 224, 204), floor=(172, 130, 96), table=(196, 146, 104), edge=(132, 92, 66)),
    "beach": dict(top=(150, 212, 248), bot=(250, 236, 204), floor=(240, 214, 160), table=(246, 200, 120), edge=(206, 160, 100)),
    "apartment": dict(top=(252, 240, 230), bot=(246, 228, 214), floor=(204, 164, 124), table=(150, 178, 212), edge=(118, 146, 184)),
    "airport": dict(top=(222, 236, 250), bot=(244, 248, 252), floor=(196, 200, 210), table=(238, 242, 248), edge=(60, 84, 134)),
    "museum": dict(top=(244, 238, 228), bot=(234, 226, 212), floor=(208, 198, 176), table=(226, 218, 206), edge=(162, 150, 128)),
    "hotel": dict(top=(250, 240, 228), bot=(244, 226, 206), floor=(176, 132, 100), table=(120, 86, 70), edge=(88, 60, 46)),
    "clinic": dict(top=(236, 248, 250), bot=(246, 252, 252), floor=(200, 214, 214), table=(236, 244, 244), edge=(150, 170, 172)),
    "street": dict(top=(188, 222, 248), bot=(244, 236, 226), floor=(184, 174, 164), table=(210, 164, 112), edge=(152, 112, 82)),
}
SCENE_KEYWORDS = {
    "bakery": ["panadería", "panaderia", "pan", "pastel", "bakery", "bread", "pastry"],
    "park": ["parque", "banca", "park", "garden", "bench", "picnic", "pasear"],
    "classroom": ["clase", "escuela", "profesor", "profesora", "maestra", "classroom", "school", "teacher", "lesson"],
    "station": ["estación", "estacion", "autobús", "autobus", "tren", "boleto", "station", "ticket", "platform", "bus"],
    "store": ["supermercado", "tienda", "compras", "ropa", "camisa", "talla", "zapatos", "supermarket", "store", "shop", "clothes", "bolsa"],
    "cafe": ["café", "cafe", "té", "coffee", "tea", "chocolate", "cortado", "latte"],
    "restaurant": ["restaurante", "carta", "cuenta", "mesero", "mesera", "cena", "almuerzo", "restaurant", "menu", "waiter", "dinner", "lunch", "propina"],
    "market": ["mercado", "frutas", "verduras", "queso", "precio", "cuánto cuesta", "cuanto cuesta", "pesos", "market", "price", "fruit", "vegetables", "caro", "barato"],
    "library": ["biblioteca", "libro", "libros", "leer", "library", "book", "books", "read"],
    "beach": ["playa", "mar", "sol", "nadar", "arena", "beach", "sea", "swim", "sand", "vacaciones"],
    "apartment": ["casa", "apartamento", "cocina", "sala", "familia", "rutina", "despierto", "home", "house", "kitchen", "living room", "family"],
    "airport": ["aeropuerto", "avión", "avion", "vuelo", "maleta", "pasaporte", "airport", "plane", "flight", "suitcase", "passport"],
    "museum": ["museo", "pintura", "cuadro", "museum", "painting", "statue"],
    "hotel": ["hotel", "reservación", "reservacion", "habitación", "habitacion", "llave", "recepción", "recepcion", "desayuno", "reservation", "room", "key", "check-in"],
    "clinic": ["médico", "medico", "doctor", "clínica", "clinica", "me duele", "fiebre", "dolor", "hospital", "fever", "pain", "medicine"],
    "street": ["calle", "ciudad", "dirección", "direccion", "derecha", "izquierda", "derecho", "esquina", "street", "city", "turn left", "turn right", "straight", "directions"],
}
ALIASES = {"supermarket": "store", "shop": "store", "metro": "station", "school": "classroom", "garden": "park", "bistro": "restaurant", "bookstore": "library", "bibliotheque": "library", "house": "apartment", "home": "apartment", "louvre": "museum", "road": "street", "sea": "beach"}
ALIASES.update({"home": "apartment", "casa": "apartment", "house": "apartment", "plaza": "park", "mercado": "market", "doctor": "clinic", "hospital": "clinic", "taxi": "street", "calle": "street",
                "aeropuerto": "airport", "estacion": "station", "estación": "station", "parque": "park", "panaderia": "bakery", "panadería": "bakery", "restaurante": "restaurant", "tienda": "store", "hotel": "hotel"})


class ScriptProblem(Exception):
    pass


# ---------- text helpers ----------
@functools.lru_cache(None)
def font(size, bold=True):
    names = ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"] if bold else ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    for n in names:
        g = sorted(glob.glob(f"/usr/share/fonts/**/{n}", recursive=True))
        if g:
            return ImageFont.truetype(g[0], size)
    return ImageFont.load_default()


def wrap(text, f, maxw):
    out, cur = [], ""
    for t in text.split():
        trial = (cur + " " + t) if cur else t
        if f.getlength(trial) > maxw and cur:
            out.append(cur); cur = t
        else:
            cur = trial
    return out + [cur] if cur else out


# ---------- script ----------
SECTIONS = {"hook", "story", "vocab", "grammar", "quiz", "ending", "intro", "listening", "conclusion", "practice"}
HEADERS = r"(title|scene|episode|cover|cast|level|topic|variety|duration|hook|kind|weather|objective)"


def parse_story(text):
    if len(text) > MAX_CHARS:
        raise ScriptProblem(f"The script is too long ({len(text)} characters; limit {MAX_CHARS}).")
    meta, lines, vocab, gram, quiz, sec = {"title": "", "scene": "auto", "episode": ""}, [], [], None, None, "story"
    for n, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^\[(\w+)\]$", s)
        if m:
            sec = m[1].lower()
            if sec not in SECTIONS:
                raise ScriptProblem(f"line {n}: unknown section [{sec}].")
            continue
        m = re.match(r"^" + HEADERS + r"\s*:\s*(.+)$", s, re.I)
        if m:
            meta[m[1].lower()] = m[2].strip(); continue
        m = re.match(r"^vocab\s*:\s*(.+)$", s, re.I)
        if m:
            p = [x.strip() for x in m[1].split("|")]
            if len(p) not in (2, 3) or not p[0] or not p[1]:
                raise ScriptProblem(f"line {n}: vocab needs 'Spanish | English' (or 'Spanish | English | pronunciation').")
            vocab.append(dict(es=p[0], en=p[1], pron=p[2] if len(p) == 3 else "", ex=None)); continue
        m = re.match(r"^example\s*:\s*(.+)$", s, re.I)
        if m:
            p = [x.strip() for x in m[1].split("|")]
            if len(p) < 2 or not p[0] or not p[1]:
                raise ScriptProblem(f"line {n}: example needs 'Spanish | English'.")
            if sec == "grammar" and gram is not None:
                gram["examples"].append((p[0], p[1]))
            elif vocab:
                vocab[-1]["ex"] = (p[0], p[1])
            else:
                raise ScriptProblem(f"line {n}: an example needs a vocab: or grammar: line above it.")
            continue
        m = re.match(r"^grammar\s*:\s*(.+)$", s, re.I)
        if m:
            gram = dict(text=m[1].strip(), examples=[]); continue
        m = re.match(r"^quiz\s*:\s*(.+)$", s, re.I)
        if m:
            p = [x.strip() for x in m[1].split("|")]
            if len(p) < 5 or not all(p[:5]) or p[4].upper() not in ("A", "B", "C"):
                raise ScriptProblem(f"line {n}: quiz needs 'Question | option A | option B | option C | A, B or C' (and an optional explanation).")
            quiz = dict(q=p[0], opts=p[1:4], ans=p[4].upper(), expl=p[5] if len(p) > 5 else ""); continue
        m = re.match(r"^([A-Za-zÀ-ÿ]+)\s*[:：]\s*(.+)$", s)
        if m:
            speaker = m[1].strip()
            p = [x.strip() for x in m[2].split("|")]
            if len(p) < 2 or not p[0] or not p[1]:
                raise ScriptProblem(f"line {n}: add the English after a | sign, like 'Mateo: ¡Hola! | Hi!'.")
            lines.append(dict(speaker=speaker, es=p[0], en=p[1], pron=p[2] if len(p) > 2 else "", sec="ending" if sec in ("ending", "conclusion") else "main")); continue
        raise ScriptProblem(f"line {n}: can't read this line: {s[:60]}")
    if not meta["title"]:
        raise ScriptProblem("Add a 'title:' line at the top.")
    if not [l for l in lines if l["sec"] == "main"]:
        raise ScriptProblem("No dialogue lines found. Use lines like 'Mateo: ¡Hola! | Hi!'.")
    meta["_grammar"], meta["_quiz"] = gram, quiz
    return meta, lines, vocab[:6]


def pick_scene(meta, lines):
    sc = ALIASES.get(meta["scene"].lower(), meta["scene"].lower())
    if sc in SCENES:
        return sc
    if sc != "auto":
        raise ScriptProblem(f"unknown scene '{meta['scene']}'. Scenes: {', '.join(SCENES)} (or auto).")
    text = (meta["title"] + " " + " ".join(l["es"] + " " + l["en"] for l in lines)).lower()
    best, score = "cafe", 0
    for name, kws in SCENE_KEYWORDS.items():
        n = sum(len(re.findall(r"(?<!\w)" + re.escape(k) + r"(?!\w)", text)) for k in kws)   # whole words only
        if n > score:
            best, score = name, n
    return best


# ---------- audio ----------
def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def synth(text, voice, out_wav, rate, dummy=False, lang="es"):
    if dummy:
        n = int(max(1.0, len(text) * 0.08) * SR); t = np.arange(n) / SR
        write_wav(out_wav, 0.4 * np.sin(2 * np.pi * 220 * t) * np.abs(np.sin(2 * np.pi * 3.5 * t)) ** 0.7); return
    mp3, ok, last = out_wav + ".mp3", False, None
    for attempt in range(1, 6):
        try:
            import edge_tts
            asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(mp3)); ok = True; break
        except Exception as e:
            last = e; print(f"edge-tts attempt {attempt}/5 failed ({e})", file=sys.stderr)
            if attempt < 5:
                time.sleep(4 * attempt)
    if not ok:
        if os.environ.get("STRICT_VOICE") == "1":
            sys.exit("::error::The natural voice service is unavailable right now. Re-run in a little while.")
        print(f"::warning::edge-tts unavailable ({last}); using the lower-quality gTTS voice", file=sys.stderr)
        from gtts import gTTS
        gTTS(text, lang=lang).save(mp3)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", out_wav], check=True)


def mouth_levels(audio, n):
    spf = SR / FPS
    rms = np.array([np.sqrt(np.mean(audio[int(i * spf):int((i + 1) * spf)] ** 2) + 1e-12) if int(i * spf) < len(audio) else 0 for i in range(n)])
    ref = np.percentile(rms[rms > 1e-3], 90) if (rms > 1e-3).any() else 1
    lv = np.clip(rms / ref, 0, 1.2); sm = lv.copy(); sm[1:-1] = 0.5 * lv[1:-1] + 0.25 * (lv[:-2] + lv[2:])
    return np.where(sm < 0.15, 0, np.where(sm < 0.55, 1, 2))


# ---------- drawing ----------
def vgrad(w, h, a, b):
    arr = np.zeros((h, w, 3), np.uint8)
    for i in range(3):
        arr[:, :, i] = np.linspace(a[i], b[i], h)[:, None]
    return Image.fromarray(arr).convert("RGBA")


def pill(text, fill, fg=(255, 255, 255), size=32):
    f = font(size); tw = int(f.getlength(text)) + 56; hh = int(size * 1.8)
    im = Image.new("RGBA", (tw, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw - 1, hh - 1), radius=hh // 2, fill=fill)
    d.text((tw / 2, hh / 2), text, font=f, fill=fg, anchor="mm"); return im


def eiffel(d, cx, base, h, col):
    """A colonial bell tower with a small dome (the view outside the window); name kept from the French engine so scene code is unchanged."""
    w = h * 0.26; lite = tuple(min(255, v + 34) for v in col)
    d.rectangle((cx - w / 2, base - h * 0.62, cx + w / 2, base), fill=col)
    d.rectangle((cx - w * 0.42, base - h * 0.86, cx + w * 0.42, base - h * 0.62), fill=col)
    d.ellipse((cx - w * 0.42, base - h * 1.0, cx + w * 0.42, base - h * 0.72), fill=col)
    d.rectangle((cx - 2, base - h * 1.1, cx + 2, base - h * 0.96), fill=col); d.rectangle((cx - h * 0.04, base - h * 1.06, cx + h * 0.04, base - h * 1.03), fill=col)
    d.ellipse((cx - w * 0.16, base - h * 0.82, cx + w * 0.16, base - h * 0.66), fill=lite)
    d.ellipse((cx - w * 0.14, base - h * 0.5, cx + w * 0.14, base - h * 0.36), fill=lite)


def make_scene(scene, meta):
    sc = SCENES[scene]
    bg = vgrad(W, H, sc["top"], sc["bot"]); d = ImageDraw.Draw(bg)
    if scene in ("cafe", "bakery", "classroom", "station", "store"):
        d.rounded_rectangle((220, 250, 880, 800), radius=30, fill=(190, 198, 232))
        d.rounded_rectangle((240, 270, 860, 780), radius=18, fill=(196, 230, 250))
        d.rounded_rectangle((240, 530, 860, 780), radius=0, fill=(176, 214, 176))
        for x, y, r in ((300, 600, 60), (400, 640, 70), (700, 610, 64), (800, 650, 74)):
            d.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=(150, 200, 152))
        for cx, cy in ((330, 360), (700, 340)):
            d.ellipse((cx - 60, cy - 20, cx + 60, cy + 20), fill=(236, 246, 254))
        eiffel(d, 540, 700, 430, (140, 176, 222))
        d.rectangle((534, 270, 546, 780), fill=(190, 198, 232)); d.rectangle((240, 520, 860, 532), fill=(190, 198, 232))
    if scene in ("cafe", "bakery"):
        d.rectangle((0, 560, 90, 640), fill=(196, 140, 96)); d.rectangle((0, 640, 120, 660), fill=(196, 140, 96))
        for cx, cy, r in ((40, 470, 70), (90, 420, 56), (20, 380, 50)):
            d.ellipse((cx - r * 0.5, cy - r, cx + r * 0.5, cy + r * 0.6), fill=(116, 160, 120))
        d.rounded_rectangle((990, 180, 1080, 760), radius=8, fill=(118, 92, 72)); d.rectangle((1000, 192, 1080, 748), fill=(58, 62, 66))
        eiffel(d, 1050, 400, 150, (220, 220, 224))
    if scene == "bakery":
        d.polygon([(220, 190), (880, 190), (920, 260), (180, 260)], fill=(236, 120, 130))
        for x in range(180, 920, 80):
            d.polygon([(x, 190), (x + 40, 190), (x + 40, 260), (x, 260)], fill=(255, 250, 246))
    elif scene == "park":
        d.ellipse((140, 280, 320, 460), fill=(252, 234, 150))
        for x in (760, 960):
            d.rectangle((x - 18, 520, x + 18, 820), fill=(122, 88, 66)); d.ellipse((x - 150, 300, x + 150, 600), fill=(96, 176, 108))
        for cx, cy in ((420, 360), (580, 300)):
            d.ellipse((cx - 80, cy - 30, cx + 80, cy + 30), fill=(255, 255, 255)); d.ellipse((cx - 30, cy - 55, cx + 50, cy + 10), fill=(255, 255, 255))
        eiffel(d, 540, 700, 330, (150, 184, 220))
    elif scene == "classroom":
        d.rounded_rectangle((100, 240, 980, 640), radius=18, fill=(150, 112, 78)); d.rounded_rectangle((120, 260, 960, 620), radius=10, fill=(52, 98, 80))
        d.text((540, 380), "¡Hola!", font=font(110), fill=(244, 244, 236), anchor="mm"); d.text((540, 520), "a  b  c  d  ñ", font=font(70), fill=(244, 230, 140), anchor="mm")
    elif scene == "station":
        d.rounded_rectangle((300, 258, 780, 340), radius=24, fill=(60, 80, 120)); d.text((540, 299), "ESTACIÓN", font=font(54), fill="white", anchor="mm")
    elif scene == "store":
        d.rectangle((0, 256, W, 336), fill=(52, 160, 120)); d.text((540, 296), "SUPERMERCADO  ·  ABIERTO", font=font(48), fill="white", anchor="mm")
    elif scene == "restaurant":
        d.rounded_rectangle((120, 250, 420, 520), radius=14, fill=(120, 80, 58)); d.rounded_rectangle((136, 266, 404, 504), radius=8, fill=(236, 208, 160)); d.ellipse((190, 330, 350, 460), fill=(206, 96, 84))
        d.rounded_rectangle((640, 270, 960, 560), radius=14, fill=(118, 92, 72)); d.rounded_rectangle((654, 284, 946, 546), radius=8, fill=(52, 60, 62))
        d.text((800, 350), "Menú del día", font=font(40), fill=(244, 244, 236), anchor="mm"); d.text((800, 430), "Sopa  ·  Tacos", font=font(34, False), fill=(244, 230, 150), anchor="mm"); d.text((800, 490), "Café  ·  Té", font=font(34, False), fill=(244, 230, 150), anchor="mm")
        for x in (200, 480):
            d.line([(x, 240), (x, 330)], fill=(90, 70, 60), width=4); d.pieslice((x - 52, 318, x + 52, 400), 180, 360, fill=(250, 196, 96)); d.ellipse((x - 20, 372, x + 20, 410), fill=(255, 244, 190))
        d.rectangle((0, 560, W, 640), fill=(174, 56, 66))
        for xx in range(0, W, 70):
            d.rectangle((xx, 560, xx + 35, 640), fill=(250, 244, 236))
    elif scene == "market":
        for bx, bw, bh, col in ((0, 220, 420, (232, 214, 190)), (210, 260, 520, (222, 200, 170)), (560, 240, 460, (236, 220, 196)), (780, 300, 560, (226, 204, 176))):
            d.rectangle((bx, 780 - bh, bx + bw, 780), fill=col)
            for wy in range(780 - bh + 50, 740, 110):
                for wx in range(bx + 30, bx + bw - 40, 80):
                    d.rectangle((wx, wy, wx + 40, wy + 60), fill=(150, 176, 206))
        d.rectangle((60, 190, 1020, 215), fill=(120, 88, 66)); d.text((540, 150), "MERCADO", font=font(70), fill=(52, 54, 66), anchor="mm")
        for i, x in enumerate(range(40, 1040, 130)):
            d.polygon([(x, 250), (x + 130, 250), (x + 130, 330), (x, 330)], fill=(214, 66, 72) if i % 2 == 0 else (250, 246, 240))
        for cx, col in ((170, (214, 56, 56)), (320, (246, 160, 52)), (470, (130, 190, 84)), (620, (232, 196, 64)), (770, (176, 66, 120)), (920, (214, 56, 56))):
            d.rounded_rectangle((cx - 70, 620, cx + 70, 720), radius=8, fill=(176, 130, 86))
            for dx in range(-52, 60, 30):
                d.ellipse((cx + dx - 18, 590, cx + dx + 18, 626), fill=col)
    elif scene == "library":
        cols = [(196, 84, 84), (84, 128, 176), (230, 184, 84), (96, 150, 110), (150, 100, 160), (210, 130, 86), (70, 90, 130)]
        for sx in (0, 790):
            d.rectangle((sx, 200, sx + 290, 800), fill=(120, 84, 60))
            for ry in range(220, 780, 120):
                d.rectangle((sx + 10, ry + 100, sx + 280, ry + 112), fill=(92, 62, 44))
                x = sx + 18
                for k in range(11):
                    bw = 18 + (k * 7) % 12; bh = 70 + (k * 13) % 26
                    d.rectangle((x, ry + 100 - bh, x + bw, ry + 100), fill=cols[(k + ry // 120) % len(cols)]); x += bw + 3
        d.rounded_rectangle((330, 280, 750, 780), radius=200, fill=(120, 84, 60)); d.rounded_rectangle((350, 300, 730, 780), radius=190, fill=(196, 226, 248))
        d.line([(540, 300), (540, 780)], fill=(120, 84, 60), width=10); d.line([(350, 520), (730, 520)], fill=(120, 84, 60), width=10)
        d.line([(540, 200), (540, 250)], fill=(90, 70, 60), width=5); d.pieslice((488, 240, 592, 322), 180, 360, fill=(70, 120, 90))
    elif scene == "beach":
        d.rectangle((0, 520, W, 800), fill=(70, 160, 214)); d.rectangle((0, 520, W, 560), fill=(118, 196, 232))
        for y in range(580, 790, 50):
            for x in range(-40 + (y // 50 % 2) * 60, W, 120):
                d.arc((x, y, x + 80, y + 22), 200, 340, fill=(206, 236, 250), width=5)
        d.rectangle((0, 780, W, 885), fill=(244, 222, 170)); d.ellipse((820, 150, 980, 310), fill=(252, 232, 130))
        d.polygon([(300, 470), (300, 380), (400, 470)], fill=(252, 250, 244)); d.polygon([(290, 480), (410, 480), (380, 505), (310, 505)], fill=(214, 84, 84))
        for cx, cy in ((150, 260), (640, 230)):
            d.ellipse((cx - 70, cy - 22, cx + 70, cy + 22), fill=(255, 255, 255)); d.ellipse((cx - 30, cy - 46, cx + 36, cy + 8), fill=(255, 255, 255))
        d.line([(900, 600), (900, 790)], fill=(120, 88, 66), width=10)
        for k in range(8):
            d.pieslice((790, 520, 1010, 700), 180 + k * 22.5, 202.5 + k * 22.5, fill=(214, 66, 72) if k % 2 == 0 else (250, 246, 240))
    elif scene in ("apartment", "hotel", "clinic"):
        d.rounded_rectangle((250, 250, 830, 760), radius=20, fill=(210, 190, 170)); d.rectangle((270, 270, 810, 740), fill=(190, 220, 244)); d.rectangle((270, 560, 810, 740), fill=(186, 170, 176))
        for rx, rw, rh in ((280, 120, 90), (420, 150, 130), (590, 110, 80), (710, 90, 110)):
            d.polygon([(rx, 640), (rx + rw / 2, 640 - rh), (rx + rw, 640)], fill=(150, 150, 170)); d.rectangle((rx, 640, rx + rw, 740), fill=(166, 160, 176))
        eiffel(d, 540, 700, 330, (130, 150, 190))
        d.rectangle((536, 270, 544, 740), fill=(210, 190, 170)); d.rectangle((270, 500, 810, 508), fill=(210, 190, 170))
        d.polygon([(190, 230), (270, 230), (270, 780), (170, 780)], fill=(238, 150, 164)); d.polygon([(890, 230), (810, 230), (810, 780), (910, 780)], fill=(238, 150, 164))
        for x, y, w_, h_, col in ((60, 330, 120, 160, (232, 196, 120)), (900, 340, 110, 140, (150, 190, 170))):
            d.rounded_rectangle((x, y, x + w_, y + h_), radius=6, fill=(120, 84, 60)); d.rectangle((x + 10, y + 10, x + w_ - 10, y + h_ - 10), fill=col)
        d.rectangle((0, 780, W, 800), fill=(180, 140, 104))
        d.line([(980, 480), (980, 780)], fill=(90, 80, 74), width=8); d.polygon([(930, 480), (1030, 480), (1010, 410), (950, 410)], fill=(252, 226, 150))
    elif scene == "airport":
        d.rectangle((0, 230, W, 780), fill=(196, 222, 246)); d.rectangle((0, 600, W, 780), fill=(150, 156, 166))
        d.rectangle((0, 690, W, 700), fill=(240, 240, 240))
        d.ellipse((330, 520, 760, 600), fill=(248, 250, 252)); d.polygon([(700, 540), (800, 470), (810, 480), (740, 570)], fill=(60, 84, 134)); d.polygon([(470, 560), (560, 640), (600, 640), (540, 560)], fill=(208, 214, 224))
        for x in range(360, 720, 52):
            d.ellipse((x, 540, x + 18, 556), fill=(120, 150, 190))
        for x in (0, 270, 540, 810):
            d.rectangle((x, 230, x + 14, 780), fill=(236, 240, 246))
        d.rounded_rectangle((250, 120, 830, 230), radius=16, fill=(40, 52, 90))
        d.text((540, 150), "SALIDAS", font=font(40), fill=(255, 220, 90), anchor="mm"); d.text((540, 202), "Bogotá  ·  Lima  ·  México", font=font(30, False), fill=(240, 240, 250), anchor="mm")
        for x in range(60, 1040, 120):
            d.rectangle((x, 60, x + 70, 74), fill=(255, 250, 230))
    elif scene == "museum":
        fr = ((90, 270, 280, 440, (206, 120, 90), (240, 196, 120)), (400, 250, 330, 480, (96, 140, 180), (236, 226, 190)), (800, 280, 190, 380, (130, 170, 120), (220, 120, 120)))
        for x, y, w_, h_, c1, c2 in fr:
            d.rounded_rectangle((x - 16, y - 16, x + w_ + 16, y + h_ + 16), radius=8, fill=(176, 132, 70)); d.rectangle((x, y, x + w_, y + h_), fill=c1)
            d.ellipse((x + w_ * 0.2, y + h_ * 0.2, x + w_ * 0.8, y + h_ * 0.7), fill=c2); d.polygon([(x, y + h_), (x + w_ * 0.5, y + h_ * 0.55), (x + w_, y + h_)], fill=tuple(int(v * 0.7) for v in c1))
        d.rectangle((0, 780, W, 800), fill=(176, 160, 132))
        d.rectangle((60, 700, 200, 780), fill=(212, 204, 190)); d.ellipse((90, 560, 170, 650), fill=(224, 218, 206)); d.rectangle((105, 640, 155, 700), fill=(224, 218, 206))
        d.line([(900, 740), (900, 790)], fill=(180, 140, 70), width=10); d.line([(1000, 740), (1000, 790)], fill=(180, 140, 70), width=10); d.arc((900, 750, 1000, 800), 0, 180, fill=(170, 50, 60), width=8)
    elif scene == "street":
        d.rectangle((0, 780, W, 885), fill=(172, 162, 152))
        for bx, bw, col in ((0, 380, (238, 226, 204)), (380, 330, (230, 216, 190)), (710, 370, (240, 230, 210))):
            d.rectangle((bx, 230, bx + bw, 780), fill=col); d.polygon([(bx, 230), (bx + bw, 230), (bx + bw - 30, 170), (bx + 30, 170)], fill=(120, 130, 150))
            for wy in (300, 480, 640):
                for wx in range(bx + 40, bx + bw - 70, 110):
                    d.rectangle((wx, wy, wx + 60, wy + 110), fill=(160, 188, 214)); d.rectangle((wx - 18, wy, wx - 4, wy + 110), fill=(96, 130, 120)); d.rectangle((wx + 64, wy, wx + 78, wy + 110), fill=(96, 130, 120))
                    d.rectangle((wx - 8, wy + 100, wx + 70, wy + 112), fill=(60, 60, 66))
        d.line([(540, 400), (540, 790)], fill=(50, 56, 60), width=12); d.ellipse((510, 360, 570, 420), fill=(252, 226, 150)); d.rectangle((520, 330, 560, 360), fill=(50, 56, 60))
        d.rounded_rectangle((60, 700, 300, 790), radius=14, fill=(206, 84, 90)); d.text((180, 745), "CAFÉ", font=font(46), fill="white", anchor="mm")
        for x in range(0, W, 90):
            d.line([(x, 790), (x + 45, 885)], fill=(150, 140, 132), width=3)
    if scene == "hotel":
        d.rounded_rectangle((300, 150, 780, 230), radius=22, fill=(60, 40, 36)); d.text((540, 190), "HOTEL  ·  RECEPCIÓN", font=font(40), fill=(255, 226, 150), anchor="mm")
    elif scene == "clinic":
        d.rounded_rectangle((300, 150, 780, 230), radius=22, fill=(255, 255, 255)); d.text((590, 190), "CLÍNICA", font=font(50), fill=(31, 159, 168), anchor="mm")
        d.rectangle((356, 172, 388, 208), fill=(214, 51, 70)); d.rectangle((342, 186, 402, 194), fill=(214, 51, 70)); d.rectangle((368, 160, 376, 220), fill=(214, 51, 70))
    d.rectangle((0, TABLE_TOP, W, H), fill=sc["floor"])
    for y in range(TABLE_TOP + 150, H, 100):
        d.line([(0, y), (W, y)], fill=tuple(int(v * 0.93) for v in sc["floor"]), width=3)
    if not meta.get("_cover"):   # the cover draws its own title, so it skips this header bar
        ep = f"Ep.{meta['episode']}  ·  " if meta.get("episode") else ""
        d.rounded_rectangle((60, 78, 1020, 232), radius=62, fill=(250, 247, 242, 245))
        d.text((112, 106), "TINY SPANISH", font=font(30), fill=BRAND)
        size = 54
        while size > 28 and font(size).getlength(ep + meta["title"]) > 860:
            size -= 2
        d.text((112, 152), ep + meta["title"], font=font(size), fill=(52, 54, 66))
    fg = Image.new("RGBA", (W, 175), (0, 0, 0, 0)); g = ImageDraw.Draw(fg)
    g.rectangle((0, 55, W, 125), fill=sc["table"]); g.rectangle((0, 125, W, 175), fill=sc["edge"])
    for x in (170, 830):
        if scene in ("cafe", "bakery"):
            g.rounded_rectangle((x, 6, x + 96, 66), radius=20, fill=(255, 252, 248)); g.ellipse((x + 78, 20, x + 122, 52), outline=(255, 252, 248), width=9)
            g.ellipse((x + 12, 10, x + 84, 24), fill=(226, 210, 196))
    if scene == "restaurant":
        for x in (150, 810):
            g.ellipse((x, 8, x + 130, 52), fill=(255, 255, 255)); g.ellipse((x + 22, 16, x + 108, 44), fill=(238, 232, 224)); g.rectangle((x + 168, 8, x + 176, 56), fill=(240, 246, 250))
    elif scene == "library":
        for x, cols_ in ((150, ((196, 84, 84), (84, 128, 176), (230, 184, 84))), (820, ((96, 150, 110), (150, 100, 160), (210, 130, 86)))):
            for k, c_ in enumerate(cols_):
                g.rectangle((x + (k % 2) * 6, 56 - 14 * (k + 1), x + 120 - (k % 2) * 6, 56 - 14 * k), fill=c_)
    elif scene == "market":
        for x, c_ in ((150, (214, 56, 56)), (840, (246, 160, 52))):
            for dx in (0, 34, 68):
                g.ellipse((x + dx, 18, x + dx + 38, 56), fill=c_)
    elif scene == "airport":
        g.rectangle((140, 12, 260, 56), fill=(60, 84, 134)); g.rectangle((820, 20, 940, 56), fill=(60, 84, 134))
    return bg, fg


def card_image(tag, tag_color, parts, min_h=380):
    body = sum(p[3] for p in parts); h = max(min_h, body + 150); cw = 960
    size = (cw + 80, h + 80)
    m = Image.new("L", size, 0); ImageDraw.Draw(m).rounded_rectangle((40, 52, 40 + cw, 52 + h), radius=56, fill=90)
    sh_ = Image.new("RGBA", size, (120, 90, 70, 0)); sh_.putalpha(m.filter(ImageFilter.GaussianBlur(16)))
    img = Image.alpha_composite(Image.new("RGBA", size, (0, 0, 0, 0)), sh_); d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 40, 40 + cw, 40 + h), radius=56, fill=(250, 248, 243, 247))
    y = 40 + 56 + (h - 56 - 36 - body) / 2
    for text, f, color, adv in parts:
        if f:
            d.text((40 + cw / 2, y), text, font=f, fill=color, anchor="ma")
        y += adv
    p = pill(tag, tag_color); img.paste(p, (84, 14), p); return img


def line_card(ln):
    maxw = 840
    big = next((font(s) for s in (64, 58, 52, 46) if len(wrap(ln["es"], font(s), maxw)) <= 2), font(46))
    pr, en = font(36, False), font(40, False)
    parts = [(t, big, (46, 48, 60), 80) for t in wrap(ln["es"], big, maxw)]
    if ln["pron"]:
        parts += [("", None, None, 10)] + [(t, pr, (214, 51, 108), 48) for t in wrap(ln["pron"], pr, maxw)]
    parts += [("", None, None, 16)] + [(t, en, (84, 86, 96), 54) for t in wrap(ln["en"], en, maxw)]
    return card_image(ln["speaker"], CHARS[ln["speaker"]]["accent"], parts)


def vocab_card(vocab, active):
    parts = []
    for i, v in enumerate(vocab):
        pron = f'   ({v["pron"]})' if v["pron"] else ""
        if i == active:   # the word being taught: Spanish big, meaning big and coloured, plus the example sentence
            parts.append((v["es"], font(58), (46, 48, 60), 72)); parts.append(("= " + v["en"] + pron, font(44), BRAND, 62))
            if v.get("ex"):
                parts.append((v["ex"][0], font(36, False), (84, 86, 96), 46)); parts.append((v["ex"][1], font(32, False), (130, 132, 142), 42))
        else:             # the others stay readable but quieter
            parts.append((v["es"], font(40), (122, 124, 138), 52)); parts.append((v["en"] + pron, font(32, False), (118, 122, 136), 46))
    return card_image("Today's tiny words", BRAND, parts, min_h=420)


def grammar_card(g):
    maxw = 840; f, eg, en = font(40, False), font(46), font(34, False)
    parts = [(t, f, (46, 48, 60), 54) for t in wrap(g["text"], f, maxw)[:6]]
    for e in g["examples"][:2]:
        parts += [("", None, None, 14)] + [(t, eg, BRAND, 60) for t in wrap(e[0], eg, maxw)[:2]] + [(t, en, (84, 86, 96), 46) for t in wrap(e[1], en, maxw)[:2]]
    return card_image("Tiny grammar", BRAND, parts, min_h=420)


def quiz_card(q, stage, count=None):
    maxw = 840; fq, fo, fs = font(44), font(44, False), font(34, False)
    parts = [(t, fq, (46, 48, 60), 58) for t in wrap(q["q"], fq, maxw)[:3]] + [("", None, None, 14)]
    for i, o in enumerate(q["opts"]):
        letter = "ABC"[i]; ok = letter == q["ans"]
        col = ((30, 140, 90) if ok else (150, 152, 162)) if stage == "answer" else (46, 48, 60)
        parts += [(t, fo, col, 54) for t in wrap(("✓ " if stage == "answer" and ok else "") + f"{letter}   {o}", fo, maxw)[:2]]
    if stage == "count":
        parts += [("", None, None, 10), (str(count), font(96), BRAND, 110)]
    if stage == "answer" and q.get("expl"):
        parts += [("", None, None, 12)] + [(t, fs, (96, 98, 108), 44) for t in wrap(q["expl"], fs, maxw)[:3]]
    return card_image("Quick quiz", BRAND, parts, min_h=460)


# ---------- cover (thumbnail) ----------
COVER_INK, COVER_SOFT = (46, 48, 60), (116, 120, 134)


def cover_title(text, maxw=860):
    """Biggest bold size (up to 112 px) that fits the title on 2 lines; falls back to 3 lines at 60 px."""
    for size in range(112, 63, -8):
        f = font(size); ls = wrap(text, f, maxw)
        if len(ls) <= 2 and all(f.getlength(x) <= maxw for x in ls):
            return f, ls, size
    f = font(60); ls = wrap(text, f, maxw)
    if len(ls) > 3:
        ls = ls[:3]; ls[-1] = ls[-1].rstrip(" .,;:!?") + "…"
    return f, ls, 60


def cover_chips(words, maxw=860, size=34):
    """Rounded 'word' chips, centred, at most two rows."""
    f = font(size); pad, gap, h = 28, 14, int(size * 1.9)
    rows, x = [[]], 0
    for w in words:
        tw = int(f.getlength(w)) + 2 * pad
        if rows[-1] and x + gap + tw > maxw:
            if len(rows) == 2:
                break
            rows.append([]); x = 0
        x += (gap if rows[-1] else 0) + tw; rows[-1].append((w, tw))
    im = Image.new("RGBA", (maxw, len(rows) * h + (len(rows) - 1) * gap), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for r, row in enumerate(rows):
        x = (maxw - (sum(tw for _, tw in row) + gap * (len(row) - 1))) // 2; y = r * (h + gap)
        for w, tw in row:
            d.rounded_rectangle((x, y, x + tw, y + h), radius=h // 2, fill=(253, 232, 240), outline=(240, 190, 208), width=2)
            d.text((x + tw / 2, y + h / 2), w, font=f, fill=(168, 34, 84), anchor="mm"); x += tw + gap
    return im


def cover_wordmark():
    f = font(46); label = "Tiny Spanish"; fw = 66
    w, h = int(f.getlength(label)) + 56 + fw + 18, 84
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=(255, 255, 255, 238))
    for i, col in enumerate(((214, 51, 108), (255, 212, 59), (31, 159, 168))):      # brand stripes
        d.rectangle((30 + i * 20, 22, 49 + i * 20, 62), fill=col)
    d.rounded_rectangle((30, 22, 89, 62), radius=6, outline=(190, 198, 214), width=2)
    d.text((30 + fw + 18, h / 2 + 1), label, font=f, fill=COVER_INK, anchor="lm")
    return im


def cover_scene(scene, meta):
    """Same room as the video, without the header bar (the cover has its own title)."""
    return make_scene(scene, dict(meta, _cover=True))


def make_cover(meta, lines, vocab, bg, fg):
    """Reel cover / thumbnail (1080x1920): the two friends at the table, brand tag, big title and today's words.
    Everything that matters sits between y=240 and y=1500, so it survives Instagram's 3:4 profile-grid crop and its Reel buttons."""
    img = bg.copy().convert("RGBA")
    cast = [n.strip() for n in meta.get("cast", "").split(",") if n.strip()] or list(dict.fromkeys(ln["speaker"] for ln in lines))
    if len(cast) == 1:
        partner = "Mateo" if cast[0] != "Mateo" else "Emma"
        cast.append(partner)
        pass
    for idx, nm in enumerate(cast):
        x = 16 if idx == 0 else 560; s = sprite(nm, 0, False); img.paste(s, (x, CHAR_Y), s)
    img.paste(fg, (0, TABLE_TOP - 55), fg)
    wm = cover_wordmark(); img.paste(wm, ((W - wm.width) // 2, 250), wm)

    title = (meta.get("cover") or meta["title"]).strip()
    tf, tl, ts = cover_title(title); lh = int(ts * 1.16)
    chips = cover_chips([v["es"] for v in vocab[:5]]) if vocab else None
    body = lh * len(tl) + 34 + 52 + (40 + chips.height if chips else 0)
    pw, ph, px = 960, body + 150, 60
    py = 1490 - ph
    shade = Image.new("L", (W, H), 0); ImageDraw.Draw(shade).rounded_rectangle((px, py + 12, px + pw, py + ph + 12), radius=56, fill=95)
    shadow = Image.new("RGBA", (W, H), (120, 90, 70, 0)); shadow.putalpha(shade.filter(ImageFilter.GaussianBlur(18)))
    img = Image.alpha_composite(img, shadow); d = ImageDraw.Draw(img)
    d.rounded_rectangle((px, py, px + pw, py + ph), radius=56, fill=(250, 248, 243, 250))
    ep = str(meta.get("episode", "")).strip()
    tag = pill(f"EPISODE {ep}  ·  LEARN SPANISH" if ep else "LEARN SPANISH", BRAND)
    img.paste(tag, (px + 44, py - tag.height // 2), tag)
    y = py + 96
    for ln in tl:
        d.text((W / 2, y), ln, font=tf, fill=COVER_INK, anchor="ma"); y += lh
    d.rounded_rectangle((W / 2 - 60, y + 6, W / 2 + 60, y + 14), radius=4, fill=BRAND); y += 34
    d.text((W / 2, y), "Learn Spanish with " + " & ".join(cast), font=font(36, False), fill=COVER_SOFT, anchor="ma"); y += 52
    if chips:
        img.paste(chips, ((W - chips.width) // 2, y + 40), chips)
    return img.convert("RGB")


# ---------- build ----------
LEAD = float(os.environ.get("LEAD_IN", "0.25"))           # silent lead-in before the first line (was 0.6s)
LINE_GAP = float(os.environ.get("LINE_GAP", "0.3"))        # pause between spoken lines (was 0.5s)
HOOK_SECONDS = float(os.environ.get("HOOK_SECONDS", "3.0"))  # how long the on-screen hook stays up


def hook_banner(meta, tag):
    """Big on-screen hook for the first seconds, so a scroller sees what the reel is about before the first line ends."""
    maxw = W - 160; title = meta.get("hook") or meta["title"]
    f = next((font(s) for s in (66, 58, 50) if len(wrap(title, font(s), maxw)) <= 2), font(50))
    sub = font(36, False)
    rows = wrap(title, f, maxw)[:2]
    h = 30 + 76 * len(rows) + 64
    img = Image.new("RGBA", (W - 80, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, h - 1), radius=40, fill=(255, 255, 255, 228))
    y = 26
    for r in rows:
        w = d.textlength(r, font=f); d.text(((img.width - w) / 2, y), r, font=f, fill=(46, 48, 60)); y += 76
    w = d.textlength(tag, font=sub); d.text(((img.width - w) / 2, y + 6), tag, font=sub, fill=BRAND)
    return img


def build(text, rate, dummy, tmp):
    meta, lines, vocab = parse_story(text)
    gram, quiz = meta.get("_grammar"), meta.get("_quiz")
    main_lines = [l for l in lines if l["sec"] == "main"]; ending = [l for l in lines if l["sec"] == "ending"]
    cast = [n.strip() for n in meta.get("cast", "").split(",") if n.strip()] or list(dict.fromkeys(ln["speaker"] for ln in lines))
    # Unfamiliar names keep their spelling in subtitles and covers but get a safe look and voice.
    for idx, name in enumerate(dict.fromkeys(cast + [ln["speaker"] for ln in lines])):
        if name not in CHARS:
            base = CHARS["Emma"] if idx % 2 == 0 else CHARS["Mateo"]
            palette = [(86, 190, 150), (226, 112, 58), (214, 51, 108), (31, 159, 168)]
            CHARS[name] = dict(base, accent=palette[idx % len(palette)])
    meta["scene"] = pick_scene(meta, lines)
    cast = (cast[:2] if cast else ["Emma", "Mateo"])
    if len(cast) == 1:
        cast.append("Mateo" if cast[0] != "Mateo" else "Emma")
    chunks, t = [np.zeros(int(LEAD * SR), np.float32)], LEAD
    count = [0]; talk, timeline = [], []

    def say(txt, voice, rate_, lang="es"):
        nonlocal t
        count[0] += 1; wav = os.path.join(tmp, f"s{count[0]}.wav")
        synth(txt, voice, wav, rate_, dummy, lang=lang); x = read_wav(wav)
        s0 = t; chunks.append(x); t += len(x) / SR
        return s0, t

    def gap(sec):
        nonlocal t
        chunks.append(np.zeros(int(sec * SR), np.float32)); t += sec

    NARRATOR = "en-US-AriaNeural"
    for ln in main_lines:
        ln["start"], ln["end"] = say(ln["es"], CHARS[ln["speaker"]]["voice"], rate); gap(LINE_GAP)
        talk.append(ln); timeline.append((ln["start"], line_card(ln)))
    vocab = vocab[:int(os.environ.get("MAX_VOCAB", "4"))]
    vcards = [vocab_card(vocab, j) for j in range(len(vocab))]
    vstart = t
    for j, v in enumerate(vocab):
        v["start"] = t
        s0, e0 = say(v["es"], CHARS[cast[0]]["voice"], "-25%"); talk.append(dict(speaker=cast[0], start=s0, end=e0)); gap(0.35)
        say(v["en"], NARRATOR, "+0%", lang="en"); gap(0.7)
        v["end"] = t; timeline.append((v["start"], vcards[j]))
    if gram:
        g0 = t; timeline.append((g0, grammar_card(gram)))
        say(gram["text"][:260], NARRATOR, "+0%", lang="en"); gap(0.5)
        for e in gram["examples"][:2]:
            s0, e0 = say(e[0], CHARS[cast[0]]["voice"], "-20%"); talk.append(dict(speaker=cast[0], start=s0, end=e0)); gap(0.6)
    if quiz:
        say("Quick quiz! " + quiz["q"], NARRATOR, "+0%", lang="en")
        timeline.append((t - 0.01, quiz_card(quiz, "q")))
        for k in (3, 2, 1):
            timeline.append((t, quiz_card(quiz, "count", k))); gap(1.0)
        timeline.append((t, quiz_card(quiz, "answer")))
        say("The answer is " + quiz["ans"] + ".", NARRATOR, "+0%", lang="en"); gap(0.3)
        ans = quiz["opts"]["ABC".index(quiz["ans"])]
        if re.search(r"\b(what does|what do|mean|in english|translate)\b", quiz["q"], re.I):
            say(ans, NARRATOR, "+0%", lang="en")
        else:
            s0, e0 = say(ans, CHARS[cast[0]]["voice"], "-20%"); talk.append(dict(speaker=cast[0], start=s0, end=e0))
        gap(0.5)
        if quiz.get("expl"):
            say(quiz["expl"][:200], NARRATOR, "+0%", lang="en"); gap(0.4)
    for ln in ending:
        gap(0.2); ln["start"], ln["end"] = say(ln["es"], CHARS[ln["speaker"]]["voice"], rate); gap(0.3)
        talk.append(ln); timeline.append((ln["start"], line_card(ln)))
    total = t + 1.2
    chunks.append(np.zeros(int((total - t) * SR) + SR, np.float32))
    audio = np.concatenate(chunks); audio = audio / max(0.01, np.abs(audio).max()) * 0.9
    n = int(total * FPS); mouth = mouth_levels(audio, n)
    timeline.sort(key=lambda x: x[0])
    bg, fg = make_scene(meta["scene"], meta)
    banner = hook_banner(meta, "Say it like a local")
    pills = {(nm, a): pill(nm, CHARS[nm]["accent"] if a else (226, 214, 206), (255, 255, 255) if a else (130, 112, 108)) for nm in cast for a in (0, 1)}

    def frame(i):
        tt = i / FPS; fr = bg.copy()
        cur = next((k for k, l in enumerate(talk) if l["start"] - 0.02 <= tt <= l["end"] + 0.1), None)
        for idx, nm in enumerate(cast):
            x = 16 if idx == 0 else 560
            sp = cur is not None and talk[cur]["speaker"] == nm
            bob = 5 * abs(math.sin(tt * 7)) if sp and mouth[i] else 2 * math.sin(tt * 2 + (0 if nm == cast[0] else 1.7))
            blink = ((i + (0 if nm == cast[0] else 41)) % 97) < 4
            s = sprite(nm, int(mouth[i]) if sp else 0, blink)
            fr.paste(s, (x, int(CHAR_Y - bob)), s)
            p = pills[(nm, int(sp))]; fr.paste(p, (x + s.width // 2 - p.width // 2, 322), p)
        fr.paste(fg, (0, TABLE_TOP - 55), fg)
        card, t0 = None, 0
        for st, cd in timeline:
            if tt >= st - 0.02: card, t0 = cd, st
            else: break
        if card:
            f = min(1, (tt - t0) / 0.2); dy = int(24 * (1 - f))
            if f < 1:
                card = card.copy(); card.putalpha(card.getchannel("A").point(lambda v: int(v * f)))
            fr.paste(card, (20, CARD_Y - 40 + dy), card)
        if tt < HOOK_SECONDS:
            a = min(1.0, tt / 0.15, (HOOK_SECONDS - tt) / 0.35)
            if a > 0:
                b = banner if a >= 1 else banner.copy()
                if a < 1: b.putalpha(b.getchannel("A").point(lambda v: int(v * a)))
                fr.paste(b, (40, 130), b)
        return fr.convert("RGB")

    return meta, lines, vocab, audio, n, frame


def srt_time(t):
    ms = int(round(t * 1000)); return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def caption(meta, vocab):
    cast = [n.strip() for n in meta.get("cast", "").split(",") if n.strip()] or ["Emma", "Mateo"]
    out = f"Learn Spanish with {' & '.join(cast)} 🇲🇽 — {meta['title']}\n\n"
    if vocab:
        out += "Today's tiny Spanish:\n" + "\n".join(f"• {v['es']} — {v['en']}" for v in vocab) + "\n"
    return out + "\nYour turn: write your answer in the comments 👇\nSave this to practice later! 💌\nSmall steps. Big dreams.\n\n#learnspanish #spanishforbeginners #spanish #spanishlessons #languagelearning #tinyspanish"


def main():
    ap = argparse.ArgumentParser(description="Tiny Spanish Reel")
    ap.add_argument("script"); ap.add_argument("-o", "--out", default="output")
    ap.add_argument("--rate", default="-8%"); ap.add_argument("--dummy-audio", action="store_true", help="TEST ONLY: tones instead of voices")
    ap.add_argument("--check", action="store_true", help="only check the script")
    ap.add_argument("--preview", help="save one PNG frame and exit"); ap.add_argument("--progress-file")
    ap.add_argument("--cover", help="save only the cover/thumbnail PNG (no voices, no video) and exit")
    a = ap.parse_args()
    text = open(a.script, encoding="utf-8").read()
    try:
        meta, lines, vocab = parse_story(text); pick_scene(meta, lines)
    except ScriptProblem as e:
        print("::error title=Script problem::" + str(e).replace("\n", "%0A")); sys.exit(1)
    if a.check:
        print(f"Script OK: {meta['title']} ({len(lines)} lines, scene {pick_scene(meta, lines)})"); return
    if a.cover:
        meta["scene"] = pick_scene(meta, lines); bg, fg = cover_scene(meta["scene"], meta)
        make_cover(meta, lines, vocab, bg, fg).save(a.cover); print(f"Wrote {a.cover}"); return
    stem = os.path.splitext(os.path.basename(a.script))[0]; os.makedirs(a.out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        meta, lines, vocab, audio, n, frame = build(text, a.rate, a.dummy_audio, tmp)
        if a.preview:
            l = lines[min(1, len(lines) - 1)]; frame(int((l["start"] + 0.5) * FPS)).save(a.preview); return
        wav = os.path.join(tmp, "final.wav"); write_wav(wav, audio)
        mp4 = os.path.join(a.out, stem + ".mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", mp4], stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(frame(i).tobytes())
            if a.progress_file and i % 30 == 0:
                open(a.progress_file, "w").write(json.dumps({"done": i, "total": n}))
        p.stdin.close()
        if p.wait() != 0:
            sys.exit("::error::FFmpeg failed while encoding the video.")
        cover_png = os.path.join(a.out, stem + ".cover.png")
        try:
            cbg, cfg = cover_scene(meta["scene"], meta); make_cover(meta, lines, vocab, cbg, cfg).save(cover_png)
        except Exception as e:   # never lose a finished video over a thumbnail: fall back to a video frame
            print(f"::warning::Could not draw the cover ({e}); using a video frame instead.")
            l = lines[min(1, len(lines) - 1)]; frame(int((l["start"] + 0.6) * FPS)).save(cover_png)
    with open(os.path.join(a.out, stem + ".srt"), "w", encoding="utf-8") as f:
        for i, l in enumerate(sorted(lines, key=lambda z: z.get('start', 0)), 1):
            f.write(f"{i}\n{srt_time(l['start'])} --> {srt_time(l['end'])}\n{l['es']}\n{l['en']}\n\n")
    open(os.path.join(a.out, stem + ".caption.txt"), "w", encoding="utf-8").write(caption(meta, vocab))
    json.dump(dict(title=meta["title"], episode=meta["episode"], scene=meta["scene"], seconds=round(n / FPS, 1), width=W, height=H, fps=FPS, lines=len(lines), vocab=len(vocab)),
              open(os.path.join(a.out, stem + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Wrote {mp4} ({n / FPS:.1f}s)")


if __name__ == "__main__":
    main()
