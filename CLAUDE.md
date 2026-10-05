# The Kyivan Rus Condominium · website repo

A static site: one click-through slideshow (the pitch) plus the op-ed. No framework, no build server. Forked on 5 Oct 2026 from the Islamabad Accords site (github.com/dhanna11/islamabad-accords) and trimmed to one deck.

## Files
- `index.html`: the slideshow, built from `deck/`. One self-contained page; it loads only Google Fonts from outside. Do not hand-edit it.
- `deck/`: `deck.json` (slide order and sections) and `slides/<id>.html` (one slide each). Unlike the Islamabad repo there is no upstream Slides artifact: the slide HTML here is the source, edited in place.
- `kyivan-rus-condominium.md`: the op-ed. The Op-ed button links it and the Ask buttons point the AI at it. `.nojekyll` keeps Pages from turning it into HTML.
- `build-slideshow.py`: regenerates `index.html` (and `preview.html`, never committed). Python 3 only.
- `.github/workflows/check.yml` and `tests/`: the check on every PR (see "Checks").

## Rules
- The words are the author's. Slide text is condensed from the op-ed; don't reword either without the author's say-so.
- The slides use EB Garamond because the deck shows Ukrainian and Russian (Київська Русь / Киевская Русь); keep a serif with Cyrillic.
- Every slide has a stable link (`index.html#<slide-id>`). When a slide id is removed or renamed, add it to `SLIDE_ALIASES` in `build-slideshow.py`; never delete an alias.
- The site is a DRAFT (author, 5 Oct 2026): `DRAFT = True` in `build-slideshow.py` adds the DRAFT title, badge, slide watermark and a noindex tag, and the op-ed carries a DRAFT line under the byline. Turn both off only when the author says it's final.
- `ASK_PROMPT`, `FEEDBACK`, `SECTION_LABEL` and `SLIDE_LABEL` in `build-slideshow.py` are the author's wording.
- Keep the site static and self-contained: no trackers, analytics or third-party scripts without asking.
- If the build warns about an icon missing from `ICONS`, add its 24px line paths to `ICONS`.

## Checks
1. `python3 build-slideshow.py` must print no warnings, and the `index.html` it writes must match the committed one.
2. `tests/smoke.mjs` opens `index.html` in Chromium and checks every slide link, content spilling off a slide, the Ask/Op-ed/feedback links, taps and keys, and that the control bar stays on one line from 1280px down to 320px.
Run locally: `cd tests && npm ci && npx playwright install chromium && node smoke.mjs` (skip the install where Chromium is preinstalled). Never loosen or skip a check to get green.
