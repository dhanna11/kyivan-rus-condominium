# The Kyivan Rus Condominium · website

A pitch deck for a condominium over the Ukrainian-held strip of Donetsk Oblast: a demilitarized zone under joint civilian administration, sovereignty deferred, and a name both sides can take home. A companion to [The Islamabad Accords](https://dhanna11.github.io/islamabad-accords/), and forked from [its site](https://github.com/dhanna11/islamabad-accords).

- `index.html`: the slideshow. Click Next and Previous, use the arrow keys or the space bar, swipe on a phone, or click the left or right half of a slide. Each slide has its own link, for example `#three-names`.
- `kyivan-rus-condominium.md`: the op-ed, linked from the Op-ed button and read by the Ask Claude / Ask ChatGPT buttons.
- `deck/`: the slides (`deck.json` for order and sections, `slides/<id>.html` for one slide each). This is the source of `index.html`.
- `build-slideshow.py`: rebuilds `index.html` from `deck/`. Needs only Python 3.

## Publish on GitHub Pages
1. In the repository, go to Settings → Pages. Under Source, pick "Deploy from a branch", then choose `main` and `/ (root)`.
2. After a minute the site is at `https://dhanna11.github.io/kyivan-rus-condominium/`.

The only thing the page loads from outside is its fonts, from Google Fonts.

## Checks
Every PR and push to `main` runs `.github/workflows/check.yml`: the build must print no warnings and match the committed `index.html`, and `tests/smoke.mjs` checks every slide link, content spilling off a slide, the outbound links, taps and keys, and the control bar from 1280px down to 320px. Locally: `cd tests && npm ci && npx playwright install chromium && node smoke.mjs`.

## License
- **Text and design** (the slides and the op-ed): © 2026 David Hanna Jr., [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See `LICENSE-CONTENT.md`. Quoted material and sources belong to their authors.
- **Build scripts and code** (`build-slideshow.py`, `tests/`, `.github/`, and the page wrapper around the slides): [MIT](LICENSE).
