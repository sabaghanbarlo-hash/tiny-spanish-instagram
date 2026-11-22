# Tiny Spanish: Instagram Reels

Script in, 9:16 Spanish video out, with **Emma, Mateo, Cami and Santi**. Free: GitHub Actions + Microsoft Edge neural voices + Pillow + ffmpeg. Sister system: `tiny-spanish-youtube`. Cloned from the Tiny Japanese video system (`tiny-japanese-video`), with a Spanish language layer and a new cast.

## Make a video
1. Add a script to `stories/`, e.g. `stories/02-at-the-market.txt` (format below).
2. Actions -> **Generate videos** -> Run workflow (story file or `all`). It renders the MP4 and cover, commits them to `output/`, deploys the site, and (if `post=true`) posts to Instagram.
3. Local: `pip install -r requirements.txt` (+ ffmpeg, fonts-dejavu-core), then `python tinyvideo.py stories/01-introducing-yourself.txt -o output/01.mp4`. Quick checks: `--dummy-audio` (no voices), `--preview frame.png` (one frame).

## Script format
```
title: Introducing Yourself
episode: 1
scene: auto           # cafe station restaurant store bookstore classroom home airport street park beach hospital arcade aquarium snow bakery rainy rooftop commute autumn sunset flowers (Spanish words work too: mercado, playa, ...)
weather: auto         # petals leaves snow rain wind none
cast: Emma, Mateo     # any two of Emma, Mateo, Cami, Santi (left, right)

Mateo: ¡Hola! ¿Cómo te llamas? | Hi! What's your name? | OH-lah. KOH-moh teh YAH-mahs
Emma: Me llamo Emma. | My name is Emma. | meh YAH-moh EH-mah

vocab: me llamo | my name is | meh YAH-moh
```
Dialogue: `Speaker: Spanish | English | pronunciation (optional)`. Vocab: `vocab: Spanish | English | pronunciation (optional)`. Section markers like `[story]` and the YouTube-only lines (`example:`, `grammar:`, `quiz:`) are accepted and ignored here. Check Spanish punctuation and cast with `python tools/validate_script.py <file>`.

## Formats and automation (same as Tiny Japanese)
| What | Where | Workflow |
|---|---|---|
| Dialogue reel (~30-40 s: chat, 3 key words said slowly) | `stories/` | Generate videos |
| Practice reel (~20 s: say it out loud, 3-2-1) | `practice/`, `bank-practice/` (`format: practice`) | Practice reel, Daily extra |
| Mistake and fix reel | `bank-mistake/` (`format: mistake`) | Daily extra |
| Daily post from the queue | `output/*.mp4` not yet in `posted.txt` | Daily reel (09:00 UTC) |
| Keep the queue 5 days ahead | `story-bank/NAME.txt` + `NAME.caption` | Daily refill |
| Lesson Reel with grammar tip and quiz (older format) | `episodes/instagram/` | Lesson Reel (quiz format) |

Posting needs the `COMPOSIO_API_KEY` repo secret and an Instagram account connected in Composio named `Tiny Spanish` (variable `IG_ACCOUNT` overrides). Nothing posts without that.

## Cast
`config/characters.json` + `docs/CHARACTER_BIBLE.md`. Drawn in code (`render_char` in `tinyvideo.py`): Emma (ponytail, mint hoodie), Mateo (short hair, terracotta shirt), Cami (space buns, magenta bomber), Santi (curly hair, teal vest, camera). Voices: es-US-Paloma, es-MX-Jorge, es-CO-Salome, es-CO-Gonzalo. `python portraits.py` makes a portrait sheet.

## Story mode (animated)
Add `format: story` to a script and it becomes an animated story: the two characters walk in, act, and talk, then the vocabulary (and an optional quiz). Plain dialogue is directed for you; or write your own directions (`> Emma enters left`, `& Mateo nods`, `@scene cafe`). Examples in `story-examples/`; check one with `python story.py FILE --check`. Pick the Story format on the studio page.

## Queue and posting times (UTC)
Every video you make with posting off goes to the queue (`docs/queue.html` shows it, with delete). Posting is automatic:
| Time | What | Why |
|---|---|---|
| 12:45 | next reel from the queue | 7:45 am EST / 8:45 am EDT, just before the weekday-morning learning window |
| 17:45 | practice reel | midday window |
| 23:45 | mistake and fix reel | 6:45 pm EST / 7:45 pm EDT, just before the evening window |
Best-time data for 2026 puts education accounts at weekday mornings and evenings (US Eastern). GitHub runs scheduled jobs a few minutes late.

## Cast and backgrounds
16 characters (`config/characters.json`): Emma, Mateo, Cami, Santi, Lucía, Diego, Valentina, Rosa, Pepe, Carlos, Sofía, Javi, Paula, Andrés, Marisol, Nico. 22 backgrounds for reels, with Spanish signs.

## Not ported yet
Tiny Japanese's Instagram Stories scheduler (`ig-stories`, `storystudio.py`, `publish_story.py`) and the story gallery page. Voices have only been tested with test tones locally; the first Actions run uses the real voices.
