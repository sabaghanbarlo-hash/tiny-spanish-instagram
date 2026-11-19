# Tiny Spanish: Instagram Reels

Paste a script, get a 9:16 Spanish lesson Reel with Emma, Mateo, Cami and Santi. Instagram-only system with its own site and its own episode numbering (`state/instagram.json`). Sister system: `tiny-spanish-youtube`. Brand hub and shared docs: `tiny-spanish`.

Engine: adapted from `tiny-french-story` (`small.py` Reel renderer). The French repo is untouched.

## Make a Reel
1. Copy `templates/reel.template.txt` to `episodes/instagram/002-your-title.txt` and fill it in (or ask Claude to write it from the curriculum in `curriculum/a1-instagram.json`).
2. Run `python tools/validate_script.py episodes/instagram/002-your-title.txt` (checks ¿ ¡ marks, Latin American rules, cast names).
3. GitHub: Actions -> **Generate Reel** -> Run workflow (script path). Download the MP4, .srt, .cover.png and .caption.txt from the run's `reel` artifact.
4. Locally: `pip install -r requirements.txt` (plus ffmpeg and fonts-dejavu-core), then `python small.py episodes/instagram/002-your-title.txt -o output`.

Quick checks: `--check` validates only, `--preview frame.png` saves one frame, `--cover cover.png` saves only the cover, `--dummy-audio` uses test tones instead of voices (tests only).

## What a Reel contains (about 55 s)
hook banner, dialogue between two characters, 3-4 vocabulary cards (Spanish said slowly, then English, with an example), one grammar tip, a quiz with a 3-2-1 countdown and the answer, and a short goodbye. Scenes: cafe, bakery, park, classroom, station, store, restaurant, market, library, beach, apartment/home, airport, museum, hotel, clinic, street.

## Script format
See `templates/reel.template.txt` and the sample `episodes/instagram/001-introducing-yourself.txt`. Dialogue lines are `Character: Spanish | English | pronunciation (optional)`. Characters: Emma, Mateo, Cami, Santi (`cast:` picks the two on screen).

## Status (19 Nov 2026)
| Works and tested | Not done yet |
|---|---|
| Parser (sections, vocab+examples, grammar, quiz), 7 automated tests (`python test_small_es.py`) | Real Spanish voices: the render was tested with test tones only, because voice synthesis needs the internet. The first GitHub run uses the real voices and fails loudly if they are unavailable |
| Four new characters drawn in code, mouth and blink animation | Native-speaker review of the sample script |
| 1080x1920 render with hook, cards, countdown, SRT, caption, cover | Posting to Instagram and the queue/schedule (needs the @tinyspanish account and your approval) |
| Hotel and clinic scenes, Spanish signs | Studio page (paste a script in the browser); use the Actions button for now |

Caption note: captions are English plus Spanish hashtags; edit before posting.
