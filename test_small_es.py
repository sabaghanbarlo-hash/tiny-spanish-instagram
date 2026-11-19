#!/usr/bin/env python3
"""Tests for the Tiny Spanish Reel engine. Run: python test_small_es.py  (no voices or network needed)."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import small, sprites

SAMPLE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "episodes/instagram/001-introducing-yourself.txt"), encoding="utf-8").read()


def raises(text, frag):
    try:
        small.parse_story(text)
    except small.ScriptProblem as e:
        assert frag in str(e), str(e)
        return
    raise AssertionError("expected ScriptProblem containing " + frag)


def test_sample_parses():
    meta, lines, vocab = small.parse_story(SAMPLE)
    assert meta["title"] == "Introducing Yourself" and meta["episode"] == "1"
    assert len(lines) == 7 and lines[-1]["sec"] == "ending"
    assert len(vocab) == 4 and vocab[0]["es"] == "me llamo" and vocab[0]["ex"][0] == "Me llamo Emma."
    assert meta["_grammar"]["examples"][0][0] == "Soy Emma."
    assert meta["_quiz"]["ans"] == "A" and len(meta["_quiz"]["opts"]) == 3


def test_bad_scripts():
    raises("Mateo: Hola | Hi", "title")
    raises("title: x\n[nope]\nMateo: Hola | Hi", "unknown section")
    raises("title: x\nMateo: Hola", "English")
    raises("title: x\nMateo: Hola | Hi\nquiz: Q? | a | b | c | D", "quiz needs")
    raises("title: x\nvocab: solo", "vocab needs")
    raises("title: x\n[vocab]\nexample: Hola | Hi", "example needs a vocab")


def test_scene_picking():
    for text, want in (("Reservación en el hotel | The hotel reservation", "hotel"), ("Me duele la cabeza, necesito un médico | I need a doctor", "clinic"),
                       ("¿Dónde está el aeropuerto? | Where is the airport?", "airport"), ("¿Cuánto cuesta? Es muy caro. | How much? Too expensive.", "market")):
        meta, lines, _ = small.parse_story("title: t\nMateo: " + text)
        assert small.pick_scene(meta, lines) == want, (text, small.pick_scene(meta, lines))
    meta, lines, _ = small.parse_story("title: t\nscene: home\nMateo: Hola | Hi")
    assert small.pick_scene(meta, lines) == "apartment"


def test_every_scene_draws():
    for sc in small.SCENES:
        bg, fg = small.make_scene(sc, {"title": "Test", "episode": "1"})
        assert bg.size == (small.W, small.H), sc


def test_cast_is_distinct_and_unknown_names_fall_back():
    imgs = {n: sprites.sprite(n, 0, False).tobytes() for n in sprites.CAST}
    assert len(set(imgs.values())) == 4
    assert sprites.sprite("Emma", 2, False).tobytes() != imgs["Emma"]       # mouth opens
    assert sprites.sprite("Emma", 0, True).tobytes() != imgs["Emma"]        # blink
    assert sprites.sprite("Pedro", 0, False).size == sprites.sprite("Emma", 0, False).size


def test_voices_are_spanish():
    for n, c in sprites.CHARS.items():
        assert c["voice"].startswith("es-"), n


def test_full_render_with_test_tones():
    with tempfile.TemporaryDirectory() as tmp:
        meta, lines, vocab, audio, n, frame = small.build(SAMPLE, "-8%", True, tmp)
        assert n / small.FPS > 30
        for t in (1.0, n / small.FPS - 2):
            assert frame(int(t * small.FPS)).size == (small.W, small.H)
        cap = small.caption(meta, vocab)
        assert "#tinyspanish" in cap and "me llamo" in cap and "French" not in cap


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print("ok  ", name)
            except Exception as e:
                fails += 1; print("FAIL", name, "-", repr(e)[:200])
    sys.exit(1 if fails else 0)
