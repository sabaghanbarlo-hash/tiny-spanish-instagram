"""Smoke tests for the queue/Reels engine (tinyvideo.py): parsing, casting, scenes, one preview frame. Run: python test_reels.py"""
import glob, os, subprocess, sys, tempfile
import tinyvideo as T

def test_roster():
    assert set(T.ROSTER) == {"emma", "mateo", "cami", "santi"}
    for c in T.ROSTER.values():
        assert c["voice"].startswith("es-"), c["label"]
        T.render_char(c, 1, False)                       # every character draws

def test_parse_and_cast():
    for f in sorted(glob.glob("stories/*.txt") + glob.glob("story-bank/*.txt") + glob.glob("practice/*.txt")):
        meta, lines, vocab = T.parse_story(f)
        assert lines and all(l["es"] for l in lines), f
        assert T.pick_scene(meta, lines) in T.SCENES, f

def test_cast_slots():
    p = os.path.join(tempfile.gettempdir(), "cast.txt")
    open(p, "w", encoding="utf-8").write("title: Test\ncast: cami, santi\nCami: ¡Hola! | Hi!\nSanti: ¡Hola! | Hi!\nvocab: hola | hi\n")
    T.parse_story(p)
    assert T.CHARS[T.SLOT_L]["id"] == "cami" and T.CHARS[T.SLOT_R]["id"] == "santi"

def test_preview_frame():
    out = os.path.join(tempfile.gettempdir(), "frame.png")
    r = subprocess.run([sys.executable, "tinyvideo.py", "stories/01-introducing-yourself.txt", "--dummy-audio", "--preview", out], capture_output=True, text=True)
    assert r.returncode == 0 and os.path.getsize(out) > 10000, r.stderr

if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
