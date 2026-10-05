// Smoke test for the built slideshow. Opens ../index.html in Chromium at desktop and phone widths and checks what has
// broken or could break: page errors, the control bar, every slide link, the outbound links, content spilling off a
// slide, and the files the page links to. Run from this folder: npm ci && npx playwright install chromium && node smoke.mjs
// Forked from the Islamabad Accords site's test (one page here instead of two).
import { chromium, devices } from 'playwright';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PAGE = 'file://' + path.join(ROOT, 'index.html');
const deck = JSON.parse(readFileSync(path.join(ROOT, 'deck', 'deck.json'), 'utf8'));
const TEXT = 'kyivan-rus-condominium.md';
const MD_URL = 'https://dhanna11.github.io/kyivan-rus-condominium/' + TEXT;
// a slide in the middle of the deck, for the navigation checks
const MID = deck.order[Math.floor(deck.order.length / 2)];

const failures = [];
const check = (ok, what) => { console.log(`${ok ? 'ok  ' : 'FAIL'}  ${what}`); if (!ok) failures.push(what); };

// files the page links to, and the one that keeps Pages from turning the .md into HTML
for (const f of [TEXT, '.nojekyll'])
  check(existsSync(path.join(ROOT, f)) && (f === '.nojekyll' || statSync(path.join(ROOT, f)).size > 1000), `${f} is present`);

const browser = await chromium.launch();

async function open(contextOptions, hash = '') {
  const ctx = await browser.newContext(contextOptions);
  // never let a test click reach the real sites
  await ctx.route(/claude\.ai|chatgpt\.com|x\.com/, r => r.fulfill({ body: 'ok', contentType: 'text/plain' }));
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(PAGE + hash);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  return { ctx, page, errors };
}

console.log(`index.html (deck/, ${deck.order.length} slides)`);
// desktop: slides, links, spill
{
  const { ctx, page, errors } = await open({ viewport: { width: 1280, height: 800 } });

  const ids = await page.evaluate(() => [...document.querySelectorAll('.stage')].map(s => s.dataset.id));
  check(JSON.stringify(ids) === JSON.stringify(deck.order), `the page has all ${deck.order.length} slides, in deck.json order`);

  const wrong = [];
  for (const id of deck.order) {
    await page.evaluate(i => { location.hash = i; }, id);
    await page.waitForFunction(i => document.querySelector('.stage.on')?.dataset.id === i, id, { timeout: 2000 }).catch(() => wrong.push(id));
  }
  check(wrong.length === 0, `every slide link #<id> opens its slide${wrong.length ? ': ' + wrong.join(', ') : ''}`);

  // retired ids (SLIDE_ALIASES in build-slideshow.py) must still open the slide that took over their content
  const aliases = JSON.parse(readFileSync(path.join(ROOT, 'index.html'), 'utf8').match(/const ALIASES = (\{.*?\});/)[1]);
  const badAlias = [];
  for (const [old, now] of Object.entries(aliases)) {
    await page.goto(PAGE + '#' + old);
    await page.waitForFunction(i => document.querySelector('.stage.on')?.dataset.id === i && location.hash === '#' + i, now, { timeout: 2000 })
      .catch(() => badAlias.push(`${old} -> ${now}`));
  }
  check(badAlias.length === 0, `old slide links redirect to their new slides (${Object.keys(aliases).length})${badAlias.length ? ': ' + badAlias.join(', ') : ''}`);
  await page.goto(PAGE);

  // content drawn outside the 1920x1080 slide is cut off; padding past the edge is harmless, so measure the elements
  const spill = await page.evaluate(() => [...document.querySelectorAll('.stage section')].flatMap(sec => {
    const box = sec.getBoundingClientRect(), k = box.width / 1920, out = [];
    for (const el of sec.querySelectorAll('*')) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      const over = Math.max(r.right - box.right, r.bottom - box.bottom, box.left - r.left, box.top - r.top) / k;
      if (over > 2) { out.push(`${sec.id} (${Math.round(over)}px)`); break; }
    }
    return out;
  }));
  check(spill.length === 0, `no slide content spills past the slide edge${spill.length ? ': ' + spill.join(', ') : ''}`);

  // links on the slides themselves open in a new tab and never turn the page
  const slideLinks = await page.evaluate(() => [...document.querySelectorAll('.stage section a')].map(a => ({ href: a.getAttribute('href'), target: a.target, rel: a.rel })));
  check(slideLinks.length > 0 && slideLinks.every(l => l.target === '_blank' && l.rel.includes('noopener')), `slide links open a new tab with rel=noopener (${slideLinks.length})`);
  check(slideLinks.filter(l => !/^https?:\/\//.test(l.href)).every(l => existsSync(path.join(ROOT, l.href))), 'relative slide links point at files in the repo');

  // the bar's own links (the section menu, also inside the bar, holds phone copies of the Ask links and the note)
  const links = await page.evaluate(() => [...document.querySelectorAll('.bar > .ask a, .bar > .pdf, .viewport > .note')].map(a => ({
    text: a.textContent.trim(), href: a.href, target: a.target, rel: a.rel })));
  const ask = links.filter(l => /^Ask /.test(l.text));
  check(ask.length === 2 && ask[0].href.startsWith('https://claude.ai/new?q=') && ask[1].href.startsWith('https://chatgpt.com/?q='),
    'the Ask buttons point to claude.ai/new?q= and chatgpt.com/?q=');
  check(ask.every(l => decodeURIComponent(new URL(l.href).searchParams.get('q') || '').includes(MD_URL)),
    'both Ask prompts point the AI at the op-ed');
  check(links.some(l => l.text === 'Op-ed' && l.href.endsWith('/' + TEXT)), `the Op-ed button links to ${TEXT}`);
  check(links.some(l => l.href === 'https://x.com/thekingdavidjr'), 'the feedback note links to x.com/thekingdavidjr');
  const menuLinks = await page.evaluate(() => [...document.querySelectorAll('#menu li a')].map(a => ({ href: a.href, target: a.target, rel: a.rel })));
  check(menuLinks.length === 3 && menuLinks.slice(0, 2).map(l => l.href).join() === ask.map(l => l.href).join(),
    "the section menu's phone copies of the Ask links match the bar's");
  check([...links, ...menuLinks].every(l => l.target === '_blank' && l.rel.includes('noopener')), 'outbound links open a new tab with rel=noopener');

  await page.evaluate(id => { location.hash = id; }, MID);
  const [tab] = await Promise.all([ctx.waitForEvent('page'), page.locator('.ask a').first().click()]);
  await tab.waitForLoadState().catch(() => {});
  check(tab.url().startsWith('https://claude.ai/new?q=') && (await page.evaluate(() => location.hash)) === '#' + MID,
    'clicking Ask Claude opens a new tab and the slideshow stays on its slide');

  await page.keyboard.press('ArrowRight');
  await page.waitForTimeout(200);
  check((await page.evaluate(() => document.querySelector('.stage.on').dataset.id)) === deck.order[deck.order.indexOf(MID) + 1],
    'the right arrow key moves one slide forward');
  check(errors.length === 0, `no page errors on desktop${errors.length ? ': ' + errors.join('; ') : ''}`);
  await ctx.close();
}

// every width: the bar stays one line and the section menu button keeps room to be read and tapped
for (const width of [1280, 801, 800, 761, 760, 600, 480, 479, 390, 320]) {
  const phone = width <= 760;
  const { ctx, page, errors } = await open(phone ? { ...devices['iPhone 13'], viewport: { width, height: 800 } } : { viewport: { width, height: 800 } }, '#' + MID);
  const m = await page.evaluate(() => {
    const bar = document.querySelector('.bar'), vis = e => e.offsetParent !== null;
    const inBar = [...bar.querySelectorAll('a')].filter(vis).map(a => a.textContent.trim());
    const inMenu = [...document.querySelectorAll('#menu .menu-ask')].filter(li => getComputedStyle(li).display !== 'none').length;
    return { overflow: bar.scrollWidth - bar.clientWidth, sect: document.getElementById('sect').getBoundingClientRect().width,
             minH: Math.min(...[...bar.querySelectorAll('.ask a, .bar > .pdf, .btn')].filter(vis).map(e => e.getBoundingClientRect().height)),
             askReachable: inBar.filter(t => /Claude|ChatGPT/.test(t)).length === 2 || inMenu === 2, oped: inBar.includes('Op-ed') };
  });
  check(m.overflow <= 0 && m.sect >= 100 && m.minH >= 28 && m.askReachable && m.oped,
    `${width}px: bar fits on one line, section button ${Math.round(m.sect)}px wide, controls tappable, both Ask links and the Op-ed link reachable`);

  if (width === 390) {
    const before = await page.evaluate(() => document.querySelector('.stage.on').dataset.id);
    const vp = await page.locator('#vp').boundingBox();
    await page.touchscreen.tap(vp.x + vp.width * 0.8, vp.y + vp.height / 2);
    await page.waitForTimeout(300);
    const after = await page.evaluate(() => document.querySelector('.stage.on').dataset.id);
    check(after === deck.order[deck.order.indexOf(before) + 1], '390px: tapping the right half of a slide moves one slide forward');
  }
  check(errors.length === 0, `${width}px: no page errors${errors.length ? ': ' + errors.join('; ') : ''}`);
  await ctx.close();
}

await browser.close();
console.log(failures.length ? `\n${failures.length} check(s) failed` : '\nall checks passed');
process.exit(failures.length ? 1 : 0);
