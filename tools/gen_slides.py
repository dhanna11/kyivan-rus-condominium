#!/usr/bin/env python3
"""Writes deck/deck.json and deck/slides/*.html: the survey-map deck (Nov 2026), built around the frozen-line redraft of the
op-ed. The maps come from maps/*.svg and the numbers from maps/stats.json (python3 maps/build_maps.py makes both).
Run from the repo root: python3 tools/gen_slides.py && python3 build-slideshow.py
The words are condensed from kyivan-rus-condominium.md; change the op-ed first, then the matching line here."""
import json, math, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPS, OUT = ROOT / "maps", ROOT / "deck"
ST = json.loads((MAPS / "stats.json").read_text())
SNAP = "9 NOV 2026" if ST["snapshot_now"] == "2026-11-09" else ST["snapshot_now"]

PAPER, PAPER2, INK, MUTED, RULE = "#efe8da", "#e5dac4", "#2a2620", "#6b6253", "#cdbfa6"
RUST, COAL, SALT, STONE, TEAL = "#a4492b", "#24211e", "#f7f3ea", "#cfc4b0", "#2f6f73"
SERIF = "'EB Garamond', Georgia, serif"
COND = "'IBM Plex Sans Condensed', 'Arial Narrow', sans-serif"
MONO = "'JetBrains Mono', 'Courier New', monospace"
A = f"color:{RUST}; text-decoration:underline; text-decoration-color:{RULE}; text-underline-offset:5px"

def a(t, href): return f'<a style="{A}" href="{href}" target="_blank" rel="noopener">{t}</a>'
def sqmi(n): return f"{n:,}"

ORDER = ["cover", "deadlock", "front", "plans", "condominium", "the-map", "trade", "legal", "revenue",
         "why-name", "putin", "kyivan-rus", "three-names", "other-map", "guarantees", "plebiscite", "limits", "close", "sources"]
N = len(ORDER)

# ---------------------------------------------------------------- the map-sheet frame every slide sits in
def frame(label, sid):
    ticks = "".join(f'<path d="M{64 + i * 1792 / 12:.0f},48 v16 M{64 + i * 1792 / 12:.0f},1016 v16" stroke="{MUTED}" stroke-width="1.5"/>' for i in range(1, 12))
    ticks += "".join(f'<path d="M48,{48 + i * 968 / 7:.0f} h16 M1856,{48 + i * 968 / 7:.0f} h16" stroke="{MUTED}" stroke-width="1.5"/>' for i in range(1, 7))
    return (f'<svg aria-hidden="true" viewBox="0 0 1920 1080" style="position:absolute; left:0; top:0; width:1920px; height:1080px">'
            f'<rect x="56" y="56" width="1808" height="968" fill="none" stroke="{INK}" stroke-width="2"/>'
            f'<rect x="64" y="64" width="1792" height="952" fill="none" stroke="{INK}" stroke-width=".8"/>{ticks}</svg>'
            f'<p style="position:absolute; left:96px; bottom:84px; font-family:{MONO}; font-size:20px; color:{MUTED}; letter-spacing:3px">{label}</p>'
            f'<p style="position:absolute; right:96px; bottom:84px; font-family:{MONO}; font-size:20px; color:{MUTED}; letter-spacing:3px">'
            f'SHEET {ORDER.index(sid) + 1} OF {N} · X.COM/THEKINGDAVIDJR</p>')

def section(sid, inner, label):
    return (f'<section id="{sid}" data-transition="fade" style="background:{PAPER}; color:{INK}; font-family:{COND}; padding:0">\n'
            f'{inner}\n{frame(label, sid)}\n</section>\n')

def at(x, y, w, inner, extra=""):
    return f'<div style="position:absolute; left:{x}px; top:{y}px; width:{w}px;{extra}">{inner}</div>'
def kicker(t, x=140, y=130): return f'<p style="position:absolute; left:{x}px; top:{y}px; font-family:{COND}; font-weight:600; font-size:28px; letter-spacing:6px; text-transform:uppercase; color:{RUST}">{t}</p>'
def title(t, x=140, y=176, size=76, w=1600): return f'<h2 style="position:absolute; left:{x}px; top:{y}px; width:{w}px; font-family:{SERIF}; font-weight:400; font-size:{size}px; line-height:1.02; color:{INK}">{t}</h2>'
def p(t, size=32, color=INK, italic=False, extra=""):
    it = " font-style:italic;" if italic else ""
    return f'<p style="font-family:{SERIF}; font-size:{size}px;{it} color:{color}; line-height:1.28; text-wrap:pretty{extra}">{t}</p>'
def label(t, color=RUST, size=22): return f'<p style="font-family:{COND}; font-weight:600; font-size:{size}px; letter-spacing:4px; text-transform:uppercase; color:{color}">{t}</p>'
def mono(t, size=17, color=MUTED): return f'<p style="font-family:{MONO}; font-size:{size}px; letter-spacing:1px; color:{color}; line-height:1.5">{t}</p>'
def col(*items, gap=14): return f'<div style="display:flex; flex-direction:column; gap:{gap}px">{"".join(items)}</div>'
def box(inner, pad=26, bg=SALT, border=f"1.5px solid {INK}", extra=""):
    return f'<div style="background:{bg}; border:{border}; padding:{pad}px; display:flex; flex-direction:column; gap:12px;{extra}">{inner}</div>'
def numbered(items, size=30, gap=16):
    return ('<div style="display:flex; flex-direction:column; gap:%dpx">' % gap + "".join(
        f'<div style="display:flex; gap:20px; align-items:baseline"><p style="font-family:{MONO}; font-size:22px; color:{RUST}; width:30px; flex:none">{i}</p>'
        f'<p style="flex:1; font-family:{SERIF}; font-size:{size}px; color:{INK}; line-height:1.28; text-wrap:pretty">{t}</p></div>'
        for i, t in enumerate(items, 1)) + '</div>')
def legend(rows, w=330, src=""):
    out = ""
    for kind, t in rows:
        sw = {"held": f'<span style="width:14px; height:14px; background:{INK}; display:inline-block"></span>',
              "occ": f'<span style="width:14px; height:14px; border-radius:50%; border:2px solid {INK}; display:inline-block"></span>',
              "gray": f'<span style="width:28px; height:14px; display:inline-block; background:repeating-linear-gradient(45deg,{RUST} 0 4px,{SALT} 4px 9px); border:1px solid {RUST}"></span>',
              "stone": f'<span style="width:28px; height:14px; display:inline-block; background:{STONE}"></span>',
              "rust": f'<span style="width:28px; height:14px; display:inline-block; background:{RUST}cc"></span>',
              "teal": f'<span style="width:28px; height:14px; display:inline-block; background:{TEAL}cc"></span>',
              "salt": f'<span style="width:28px; height:14px; display:inline-block; background:{SALT}; border:1px solid {INK}"></span>'}[kind]
        out += f'<div style="display:flex; gap:12px; align-items:center; font-family:{COND}; font-size:20px">{sw}{t}</div>'
    if src: out += mono(src, 14)
    return f'<div style="background:{SALT}; border:1.5px solid {INK}; padding:16px 20px; display:flex; flex-direction:column; gap:8px; width:{w}px">{out}</div>'
def mapfile(name): return (MAPS / name).read_text()

def contours(w, h, n=16, seed=7):
    rnd, paths, cx, cy = random.Random(seed), [], w * .72, h * .38
    for i in range(n):
        r, ph = 120 + i * 70, [rnd.uniform(0, 6.28) for _ in range(3)]
        pts = [(cx + r * (1 + .12 * math.sin(3 * t + ph[0]) + .07 * math.sin(5 * t + ph[1]) + .04 * math.sin(7 * t + ph[2])) * 1.35 * math.cos(t),
                cy + r * (1 + .12 * math.sin(3 * t + ph[0]) + .07 * math.sin(5 * t + ph[1]) + .04 * math.sin(7 * t + ph[2])) * .8 * math.sin(t))
               for t in (k / 72 * 2 * math.pi for k in range(73))]
        pts = [(min(max(x, 0), w), min(max(y, 0), h)) for x, y in pts]   # keep every ring inside the slide
        d = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + "Z"
        paths.append(f'<path d="{d}" fill="none" stroke="{RULE}" stroke-width="{2.2 if i % 5 == 4 else 1.1}" opacity=".8"/>')
    return f'<svg aria-hidden="true" viewBox="0 0 {w} {h}" style="position:absolute; left:0; top:0; width:{w}px; height:{h}px">{"".join(paths)}</svg>'

S = {}

# ---------------------------------------------------------------- 1 cover
S["cover"] = section("cover", contours(1920, 1080)
    + f'<svg aria-hidden="true" viewBox="0 0 120 160" style="position:absolute; right:250px; top:150px; width:120px; height:160px"><path d="M60,10 L76,90 L60,78 L44,90 Z" fill="{INK}"/><path d="M60,150 L44,90 L60,102 L76,90 Z" fill="none" stroke="{INK}" stroke-width="2"/><circle cx="60" cy="90" r="38" fill="none" stroke="{INK}" stroke-width="1.2"/><text x="60" y="8" text-anchor="middle" font-family="IBM Plex Sans Condensed" font-weight="600" font-size="18" fill="{INK}">N</text></svg>'
    + at(160, 190, 1060, box(
        label("Naming the line the war has drawn", RUST, 24)
        + f'<h1 style="font-family:{SERIF}; font-weight:400; font-size:116px; line-height:.98; color:{INK}; margin-top:6px">The Kyivan Rus<br>Condominium</h1>'
        + f'<div style="display:flex; gap:26px; align-items:baseline"><p style="font-family:{SERIF}; font-style:italic; font-size:40px; color:{MUTED}">Київська Русь</p><p style="font-family:{MONO}; font-size:22px; color:{RULE}">|</p><p style="font-family:{SERIF}; font-style:italic; font-size:40px; color:{MUTED}">Киевская Русь</p></div>'
        + f'<div style="height:2px; background:{INK}; margin:16px 0 8px"></div>'
        + p("Freeze the war where the armies stand. Make the land Russia holds a condominium: recognized by the world, claimed by both, and paid for with a share to Ukraine.", 34)
        + f'<div style="display:flex; justify-content:space-between; margin-top:18px; font-family:{MONO}; font-size:20px; letter-spacing:2px; color:{MUTED}"><span>DAVID HANNA JR.</span><span>UNOFFICIAL · NOVEMBER 2026</span></div>',
        pad=52, extra=f" box-shadow:10px 10px 0 {PAPER2}"))
    + at(1440, 760, 340, box(label("Legend", MUTED, 17)
        + f'<div style="display:flex; gap:12px; align-items:center; font-size:21px"><span style="width:40px; height:18px; display:inline-block; background:repeating-linear-gradient(45deg,{RUST} 0 4px,{SALT} 4px 9px)"></span>The condominium</div>'
        + f'<div style="display:flex; gap:12px; align-items:center; font-size:21px"><span style="width:40px; border-top:3px dashed {INK}; display:inline-block"></span>Sovereignty: left ambiguous</div>'
        + f'<div style="display:flex; gap:12px; align-items:center; font-size:21px"><span style="width:40px; text-align:center; color:{MUTED}">⇄</span>Claims: both kept</div>', pad=22)),
    "A COMPANION TO THE ISLAMABAD ACCORDS")

# ---------------------------------------------------------------- 2 the impasse (Donetsk Oblast)
held = round(ST["donetsk_held_share"] * 100)
S["deadlock"] = section("deadlock", mapfile("oblast.svg")
    + kicker("The impasse") + title("Every negotiation collides with Donetsk", 140, 176, 80, 760)
    + at(140, 410, 740, col(
        f'<div style="display:flex; gap:22px; align-items:baseline"><p style="font-family:{SERIF}; font-size:120px; line-height:.9; color:{RUST}">⅕</p>'
        + p(f"of Donetsk Oblast is still held by Ukraine ({held}% on {SNAP.title().replace('Nov', 'November')}), including the four fortress cities", 32) + '</div>',
        f'<div style="border-top:2px solid {INK}; padding-top:20px; display:grid; grid-template-columns:1fr 1fr; gap:28px">'
        + col(label("Moscow"), p("Full control of the Donbas, by force or by concession", 29), gap=6)
        + col(label("Kyiv"), p("No handing over land Russia has failed to take", 29), gap=6) + '</div>',
        p("“There is no simple front in the Donbas today where it is enough to draw a single line on a map.” · A Ukrainian commander to the NYT, Oct 2026", 27, MUTED, True), gap=28))
    + at(1540, 640, 300, legend([("held", "City held by Ukraine"), ("occ", "City occupied"), ("gray", "Gray zone")], 290,
        f"BORDER: © OPENSTREETMAP CONTRIBUTORS<br>FRONT: DEEPSTATE, {SNAP}")),
    "THE IMPASSE")

# ---------------------------------------------------------------- 3 the front since January
def stat(n, t, c): return col(f'<p style="font-family:{SERIF}; font-size:96px; line-height:.95; color:{c}">{n}</p>', f'<p style="font-family:{COND}; font-size:23px; line-height:1.3">{t}</p>', gap=6)
share = round((ST["oblast_taken_by_russia_sqmi"] + ST["oblast_taken_back_by_ukraine_sqmi"]) / ST["donetsk_oblast_sqmi"] * 100)
S["front"] = section("front", mapfile("front-north.svg")
    + kicker("The northern Donbas") + title("Ten months, a few miles", 140, 176, 72, 780)
    + at(140, 320, 740, f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:36px">'
        + stat(ST["north_taken_by_russia_sqmi"], "square miles taken by Russia since 1 January, in the area shown", RUST)
        + stat(ST["north_taken_back_by_ukraine_sqmi"], "square miles taken back by Ukraine", TEAL) + '</div>')
    + at(140, 545, 690, p(f"Across all of Donetsk Oblast, about {share} percent of its {sqmi(ST['donetsk_oblast_sqmi'])} square miles changed hands. Ukraine’s counteroffensive pushed Russia back in the north; Russia’s gains came east of the fortress belt.", 27))
    + at(140, 730, 700, legend([("rust", "Taken by Russia since 1 Jan"), ("teal", "Taken back by Ukraine"), ("stone", "Occupied before 1 Jan"), ("gray", "Gray zone")], 520,
        f"DEEPSTATE, 1 JAN AND {SNAP} · BORDER: © OPENSTREETMAP CONTRIBUTORS")),
    "THE FRONT")

# ---------------------------------------------------------------- 4 Moscow's question
def plan(when, name, body, verdict):
    return box(label(when, MUTED, 19) + f'<p style="font-family:{SERIF}; font-size:40px; line-height:1.05">{name}</p>' + p(body, 26)
               + f'<div style="margin-top:auto; border-top:1.5px solid {INK}; padding-top:12px">{p(verdict, 25, RUST, True)}</div>', pad=26, extra=" flex:1")
S["plans"] = section("plans",
    kicker("Moscow’s question") + title("What do we get for stopping?")
    + at(140, 300, 1640, f'<div style="display:flex; gap:24px; align-items:stretch; height:430px">'
        + plan("October 2025", "Stop at the line", f"Trump: “cut and stop at the battle line.” Zelensky called it a good compromise.", "Moscow: no, not without the war’s “root causes.”")
        + plan("November 2025", "The 28-point plan", "Crimea, Luhansk and Donetsk recognized as de facto Russian, including by the U.S.; Ukraine withdraws from the rest of Donetsk.", "Answered with land Russia hadn’t taken.")
        + plan("December 2025", "The 20-point draft", "The line frozen in all four regions; by Kyiv’s account, the withdrawal and the recognition dropped; the Donbas left open.", "Froze the map. Moscow didn’t sign.")
        + '</div>')
    + at(140, 790, 1640, p("This proposal answers the question with something other than land.", 34, INK, True)),
    "MOSCOW’S QUESTION")

# ---------------------------------------------------------------- 5 the mechanism
def step(n, t):
    return box(f'<p style="font-family:{MONO}; font-size:22px; color:{RUST}">0{n}</p>' + p(t, 30), pad=24, extra=" flex:1")
arrow = f'<p style="font-family:{SERIF}; font-size:48px; color:{RUST}; align-self:center">→</p>'
S["condominium"] = section("condominium",
    kicker("The mechanism") + title("The " + a("condominium", "https://en.wikipedia.org/wiki/Condominium_(international_law)"))
    + at(140, 280, 1640, p("A territory jointly administered by two states without resolving final sovereignty.", 40, INK, True))
    + at(140, 380, 1640, f'<div style="display:flex; gap:16px; align-items:stretch">'
        + step(1, "The territory Russia holds") + arrow + step(2, "Russia administers; Ukraine holds defined rights") + arrow
        + step(3, "The world recognizes the status, while Russia keeps the terms") + arrow + step(4, "Sovereignty left ambiguous; both claims kept") + '</div>')
    + at(140, 640, 1640, numbered([
        "<b>Brčko</b>, Bosnia: placed under international supervision after the Yugoslav wars, precisely to defer the question of who owned it.",
        "<b>The New Hebrides</b>: run jointly by Britain and France for decades before becoming Vanuatu. Imperfect precedents: neither involved a nuclear-armed belligerent."], 30)),
    "THE MECHANISM")

# ---------------------------------------------------------------- 6 the map: the whole line
S["the-map"] = section("the-map", mapfile("line.svg")
    + kicker("The map") + title("Freeze the line. The land Russia holds becomes the condominium.", 140, 176, 52, 540)
    + at(140, 420, 520, col(
        p(f"About {round(ST['condominium_share'] * 100)}% of Ukraine, {sqmi(round(ST['condominium_sqmi'], -3))} square miles, from Luhansk to Crimea. Ukraine keeps everything it holds, the fortress belt included. No army withdraws; no city is evacuated.", 26),
        f'<div style="border-top:1.5px solid {INK}; padding-top:12px">{label("Annexes", MUTED, 18)}</div>',
        numbered(["<b>Crimea and the fleet</b>: basing rights, as under the 1997 lease (to 2017) and the 2010 extension (to 2042).",
                  "<b>The Zaporizhzhia plant</b>: international operation, IAEA supervision.",
                  "<b>Water and the Dnipro line</b>: a technical annex."], 23, 10),
        p("If Moscow won’t include Crimea, it goes to a separate protocol.", 22, MUTED, True), gap=14))
    + at(140, 880, 520, mono(f"OCCUPIED AREA: DEEPSTATE, {SNAP} · OUTLINE: NATURAL EARTH; CRIMEA FROM DEEPSTATE", 13)),
    "THE MAP")

# ---------------------------------------------------------------- 7 the trade
def party(name, gives, gets):
    return box(f'<p style="font-family:{SERIF}; font-size:46px; line-height:1">{name}</p>'
               + label("Gives", MUTED, 18) + p(gives, 27) + f'<div style="border-top:1.5px solid {INK}; margin:4px 0"></div>'
               + label("Gets", RUST, 18) + p(gets, 27), pad=28, extra=" flex:1")
S["trade"] = section("trade",
    kicker("The trade") + title("A step back at home, a step forward abroad")
    + at(140, 300, 1640, f'<div style="display:flex; gap:24px; align-items:stretch">'
        + party("Moscow", "Its exclusive claim, which only Russia recognizes; the fighting; and a share of the territory’s revenue.",
                "A status the world accepts, renewed while it keeps the terms. Reconnection with Europe and the West, earned over years of good faith. A breach costs both.")
        + party("Kyiv", "Exclusive sovereignty on paper, over land it does not control.",
                "Its defensive line; an end to the fighting; rights and a revenue share inside the territory; its claim intact.")
        + party("The West", "Recognition, as the price of ending the war, through a resolution that must be renewed. Reconnection. Both only while Russia performs.",
                "A settlement Kyiv can sign, and a lesson for the next war: conquest doesn’t pay.") + '</div>')
    + at(140, 870, 1640, p("Recognition ends the war, and lasts only while Russia keeps the terms. Reconnection is earned, for decades. A war of conquest must not pay.", 30, RUST, True)),
    "THE TRADE")

# ---------------------------------------------------------------- 8 the law on both sides
def law(country, art, quote, answer, href):
    return box(label(f"{country} · {art}", MUTED, 19) + p(f"“{a(quote, href)}”", 36, INK, True)
               + f'<div style="border-top:1.5px solid {INK}; padding-top:14px">{p(answer, 29)}</div>', pad=32, extra=" flex:1")
S["legal"] = section("legal",
    kicker("Both constitutions") + title("Nothing is ceded, so nothing breaks")
    + at(140, 300, 1640, f'<div style="display:flex; gap:28px; align-items:stretch">'
        + law("Russia", "Article 67(2.1), since 2020", "Actions aimed at alienating part of the territory of the Russian Federation … are not permitted.",
              "A condominium alienates nothing. Russia renounces no claim, and the treaty never says the land is anyone else’s.",
              "https://wilsoncenter.org/blog-post/2020-amendment-russian-constitution-another-sign-putins-invasion-isnt-going-planned")
        + law("Ukraine", "Article 73", "Issues of altering the territory of Ukraine are resolved exclusively by an All-Ukrainian referendum.",
              "Nothing is altered on paper, and the referendum this proposal requires is the route the constitution prescribes.",
              "https://www.idea.int/node/57655") + '</div>')
    + at(140, 860, 1640, p("Ukraine can’t hold a referendum under martial law, so its vote follows the ceasefire.", 28, MUTED, True)),
    "THE LAW")

# ---------------------------------------------------------------- 9 the revenue
def node(head, body, w, bg=SALT, color=INK):
    return f'<div style="width:{w}px; background:{bg}; border:1.5px solid {INK}; padding:22px; color:{color}">{label(head, RUST if bg == SALT else SALT, 19)}{p(body, 26, color)}</div>'
S["revenue"] = section("revenue",
    kicker("Sharing the revenue") + title("No payment, no relief")
    + at(140, 300, 1640, f'<div style="display:flex; align-items:center; gap:18px">'
        + node("The territory", "Mining royalties and state income; the nuclear plant’s power sales", 430) + arrow
        + node("A neutral trustee", "Audited by the same monitors who watch the line", 380) + arrow
        + col(node("Ukraine’s share", "Large enough to be real, small enough not to be tribute: for negotiators", 470, COAL, SALT),
              node("Russia", "The rest. Reconnection with Europe continues only while payments are verified", 470), gap=14) + '</div>')
    + at(140, 680, 800, col(label("Precedents", MUTED, 19), numbered([
        f"{a('The Timor Gap Treaty', 'https://en.wikipedia.org/wiki/Timor_Gap')}, 1989: Australia and Indonesia split the central zone’s revenue equally without agreeing a border; from 2002, 90:10 for East Timor.",
        f"{a('The Saudi–Kuwaiti Neutral Zone', 'https://en.wikipedia.org/wiki/Saudi_Arabian%E2%80%93Kuwaiti_neutral_zone')}: oil revenue shared equally for decades."], 24, 10), gap=10))
    + at(1000, 680, 780, col(p("Recognition is what lets the territory’s coal, steel and electricity sell legally at market prices, so Russia’s share of a legal economy can be worth more than all of a sanctioned one.", 26),
        p("A strike on the territory, or a breach of its terms, costs the side responsible its share.", 26, RUST, True), gap=14)),
    "THE REVENUE")

# ---------------------------------------------------------------- 10 why the name matters
S["why-name"] = section("why-name",
    kicker("Why the name matters") + title("A name is a specification")
    + at(140, 300, 1640, p("“There are two hard problems in computer science: cache invalidation and naming things.”", 46, MUTED, True))
    + at(140, 450, 1500, numbered([
        "It’s told as a joke, but a name says what a thing is for before the thing exists.",
        "The proposals on the table use bureaucratic language: demilitarized zones, civilian administrations, free economic zones. That gives neither side a story to tell its own people.",
        "Each country ratifies by plebiscite, so the name is what each electorate will understand itself to be voting on."], 34, 22)),
    "THE NAME")

# ---------------------------------------------------------------- 11a what Putin believes
ESSAY = "http://en.kremlin.ru/events/president/news/66181"
KI = "https://kyivindependent.com/putin-lectured-nordic-leaders-on-russian-history-during-latest-call-ft-reports/"
def quote(q, src, size=44):
    return col(f'<p style="font-family:{SERIF}; font-size:{size}px; line-height:1.15; color:{INK}">“{q}”</p>', mono(src, 16), gap=8)
def when(d, t): return col(label(d, RUST, 18), p(t, 25), gap=4)
S["putin"] = section("putin",
    kicker("What Putin believes") + title("The war he says he is fighting")
    + at(140, 290, 1040, col(
        quote("Russians and Ukrainians were one people – a single whole. … It is what I have said on numerous occasions and what I firmly believe.", "PUTIN, “ON THE HISTORICAL UNITY OF RUSSIANS AND UKRAINIANS,” 12 JULY 2021", 40),
        quote("Russians, Ukrainians, and Belarusians are all descendants of Ancient Rus.", "THE SAME ESSAY", 40),
        quote("The throne of Kiev held a dominant position in Ancient Rus.", "THE SAME ESSAY, WHICH QUOTES THE CHRONICLE ON KIEV: “LET IT BE THE MOTHER OF ALL RUSSIAN CITIES”", 40),
        gap=30) + f'<p style="margin-top:14px; font-family:{COND}; font-size:20px">{a("Read the essay on the Kremlin’s English site", ESSAY)}</p>')
    + at(1250, 290, 530, box(label("He still brings it to the table", MUTED, 18)
        + when("August 2025 · Alaska", "Reportedly lectures Trump on Rurik, Yaroslav the Wise and Bohdan Khmelnytsky.")
        + when("27 October 2026 · Finland, Norway", f"Spends most of a 90-minute call on medieval Slavic history; the ceasefire barely comes up ({a('FT', KI)}).")
        + when("December 2014", "Calls Crimea, “the ancient Korsun or Chersonesus,” sacred to Russia, like the Temple Mount."), pad=28))
    + at(140, 850, 1640, p("The name concedes the reason he gave for this war. To him, that is worth more than the land or the money now on the table.", 34, RUST, True)),
    "WHAT PUTIN BELIEVES")

# ---------------------------------------------------------------- 11 the Kyivan Rus name on this map
def fact(head, body): return box(label(head, RUST, 19) + p(body, 27), pad=24, extra=" flex:1")
S["kyivan-rus"] = section("kyivan-rus",
    kicker("The Kyivan Rus Condominium") + title("A name that gives each side something")
    + at(140, 290, 1640, p("Kyivan Rus was the medieval state, centered on Kyiv, from which both Ukrainians and Russians trace their origins.", 32, MUTED, True))
    + at(140, 380, 1640, f'<div style="display:flex; gap:22px; align-items:stretch">'
        + fact("Its strongest ground", f"By the Primary Chronicle’s account, Volodymyr of Kyiv was baptized at Chersonesus, in Crimea, in 988. Putin has called Crimea {a('Russia’s Temple Mount', 'https://www.rferl.org/a/putin-crimea-orthodox-vladimir-great-religion-ukraine-russia/26725761.html')}: a place more than one faith holds sacred.")
        + fact("For Kyiv", f"Russia’s school history standard {a('dropped “Kievan Rus”', 'https://www.mk.ru/social/2022/05/23/avtor-novogo-uchebnika-istorii-obyasnil-otsutstvie-kievskoy-rusi.html')} for “the state of Rus.” So “Kyivan” in the treaty is a real concession from Moscow, and a permanent marker of Kyiv’s claim on land Russia runs.")
        + '</div>')
    + at(140, 790, 1640, f'<div style="display:flex; gap:40px; align-items:baseline">'
        + col(label("In the Ukrainian text", MUTED, 17), f'<p style="font-family:{SERIF}; font-size:54px">Київська Русь</p>', gap=4)
        + col(label("In the Russian text", MUTED, 17), f'<p style="font-family:{SERIF}; font-size:54px">Киевская Русь</p>', gap=4)
        + p("Each plebiscite campaign in its own language.", 26, MUTED, True, "; align-self:flex-end; margin-bottom:10px") + '</div>'),
    "THE NAME")

# ---------------------------------------------------------------- 12 the names: strata + where each can be sold
STRATA = [("Donets", "from 1869 · the coal basin", "JOINTLY BUILT", COAL, SALT, 140),
          ("Wild Field", "15th–18th c. · the open steppe", "JOINTLY WITHHELD", "#b9a582", INK, 120),
          ("Kyivan Rus", "9th–13th c. · the common cradle", "JOINTLY INHERITED", RUST, SALT, 140)]
sw_, rnd = 780, random.Random(11)
st = f'<svg aria-hidden="true" viewBox="0 0 {sw_} 480" style="position:absolute; left:140px; top:300px; width:{sw_}px; height:480px"><path d="M0,40 C120,22 220,52 340,34 S600,18 {sw_},38 V70 H0Z" fill="#9c8b6c"/>'
y = 70
for name, era, claim, fill, tc, h in STRATA:
    top = f"M0,{y} " + " ".join(f"L{x},{y + rnd.uniform(-6, 6):.0f}" for x in range(60, sw_ - 59, 60)) + f" L{sw_},{y}"
    bot = f"L{sw_},{y + h} " + " ".join(f"L{x},{y + h + rnd.uniform(-6, 6):.0f}" for x in range(sw_ - 60, -1, -60))
    st += f'<path d="{top} {bot}Z" fill="{fill}"/>'
    if name == "Donets":
        st += "".join(f'<path d="M0,{y+38+k*34} C200,{y+28+k*34} 500,{y+50+k*34} {sw_},{y+36+k*34}" stroke="#3a3530" stroke-width="5" fill="none"/>' for k in range(3))
    st += (f'<text x="28" y="{y + h/2 - 6:.0f}" font-family="EB Garamond" font-size="50" fill="{tc}">{name}</text>'
           f'<text x="30" y="{y + h/2 + 30:.0f}" font-family="JetBrains Mono" font-size="18" fill="{tc}" opacity=".85">{era.upper()}</text>'
           f'<text x="{sw_-28}" y="{y + h/2 + 8:.0f}" text-anchor="end" font-family="IBM Plex Sans Condensed" font-weight="600" font-size="21" letter-spacing="4" fill="{tc}">{claim}</text>')
    y += h
st += '</svg>'
gx, gy, gs = 1110, 300, 560
def dot(px, py, name, sub, kind="", left=False, pos=""):
    x, y = gx + px * gs, gy + (1 - py) * gs
    tx, ta = (x - 30, "end") if left else (x + 30, "start")
    if pos: tx, ta = x, "middle"
    ly = {"above": -62, "below": 66}.get(pos, 0)
    c = {"lead": RUST, "ghost": SALT}.get(kind, INK)
    ring = f'<circle cx="{x:.0f}" cy="{y:.0f}" r="30" fill="none" stroke="{RUST}" stroke-width="2"/>' if kind == "lead" else ""
    stroke = f' stroke="{RUST}" stroke-width="2" stroke-dasharray="4 3"' if kind == "ghost" else ""
    return (ring + f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{20 if kind else 15}" fill="{c}"{stroke}/>'
            f'<text x="{tx:.0f}" y="{y-2+ly:.0f}" text-anchor="{ta}" font-family="EB Garamond" font-size="34" fill="{MUTED if kind == "ghost" else INK}">{name}</text>'
            f'<text x="{tx:.0f}" y="{y+24+ly:.0f}" text-anchor="{ta}" font-family="IBM Plex Sans Condensed" font-size="19" fill="{MUTED}">{sub}</text>')
g0, g1 = (gx + .2 * gs, gy + (1 - .8) * gs), (gx + .72 * gs, gy + (1 - .62) * gs)
grid = (f'<svg role="img" aria-label="Where each name can be sold: Kyivan Rus over the demilitarized strip sells in Moscow but costs Kyiv; over the frozen line it moves toward selling in both; Donets sells in Kyiv; Wild Field in neither" viewBox="0 0 1920 1080" style="position:absolute; left:0; top:0; width:1920px; height:1080px">'
        f'<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{RUST}"/></marker></defs>'
        f'<rect x="{gx}" y="{gy}" width="{gs}" height="{gs}" fill="{SALT}" stroke="{INK}" stroke-width="2"/>'
        f'<path d="M{gx+gs/2},{gy} V{gy+gs} M{gx},{gy+gs/2} H{gx+gs}" stroke="{INK}" stroke-width="1" stroke-dasharray="6 6"/>'
        f'<path d="M{g0[0]+26:.0f},{g0[1]:.0f} L{g1[0]-28:.0f},{g1[1]:.0f}" stroke="{RUST}" stroke-width="3" marker-end="url(#ah)"/>'
        f'<text x="{gx+gs/2:.0f}" y="{gy+gs+44}" text-anchor="middle" font-family="IBM Plex Sans Condensed" font-weight="600" font-size="21" letter-spacing="4" fill="{INK}">SELLABLE IN KYIV →</text>'
        f'<text transform="translate({gx-30},{gy+gs/2}) rotate(-90)" text-anchor="middle" font-family="IBM Plex Sans Condensed" font-weight="600" font-size="21" letter-spacing="4" fill="{INK}">SELLABLE IN MOSCOW →</text>'
        + dot(.2, .8, "Kyivan Rus", "over the strip", "ghost", pos="above") + dot(.72, .62, "Kyivan Rus", "over the frozen line", "lead", pos="below")
        + dot(.84, .3, "Donets", "fits the Donbas, not Crimea", left=True) + dot(.1, .14, "Wild Field", "honest; neither can sell it") + '</svg>')
S["three-names"] = section("three-names",
    kicker("Three candidates") + title("Each name claims a different layer of the ground", 140, 176, 64, 1640)
    + st + grid
    + at(140, 800, 780, p("If the name doesn’t hold, split the instruments, as Camp David did in 1978: a treaty named for the ground, and a separate declaration of shared heritage.", 24, MUTED, True)),
    "THE NAME")

# ---------------------------------------------------------------- 13 the other map
rows = [("Ukraine withdraws", "From its part of Donetsk", "No"), ("The fortress belt", "Handed over", "Kept"),
        ("Moscow gets", "The ground it asked for", "Recognition and staged relief"),
        ("Kyiv’s answer", "“Unrealistic and unacceptable” (Geneva, Feb 2026)", "A freeze at the current line is its minimum")]
tbl = (f'<div style="display:grid; grid-template-columns:300px 1fr 1fr; border:1.5px solid {INK}; background:{SALT}">'
       + f'<div style="padding:18px"></div>' + f'<div style="padding:18px; border-left:1.5px solid {INK}">{label("The strip", MUTED, 21)}{p("A demilitarized zone over the part of Donetsk Ukraine holds", 24, MUTED)}</div>'
       + f'<div style="padding:18px; border-left:1.5px solid {INK}; background:{PAPER2}">{label("The frozen line", RUST, 21)}{p("The condominium over the land Russia holds", 24)}</div>'
       + "".join(f'<div style="padding:16px 18px; border-top:1.5px solid {INK}">{label(r, INK, 18)}</div>'
                 f'<div style="padding:16px 18px; border-top:1.5px solid {INK}; border-left:1.5px solid {INK}">{p(s, 27, MUTED)}</div>'
                 f'<div style="padding:16px 18px; border-top:1.5px solid {INK}; border-left:1.5px solid {INK}; background:{PAPER2}">{p(f, 27)}</div>' for r, s, f in rows)
       + '</div>')
S["other-map"] = section("other-map",
    kicker("The other map") + title("The version on the table costs Kyiv more")
    + at(140, 300, 1640, tbl)
    + at(140, 840, 1640, p(f"“We cannot leave these fortified districts of Donetsk Oblast and essentially hand them over.” · Oleksandr Merezhko, chair of the Ukrainian parliament’s foreign affairs committee ({a('Kyiv Independent', 'https://kyivindependent.com/joint-rule-with-russia-in-donbas/')})", 26, MUTED, True)),
    "THE OTHER MAP")

# ---------------------------------------------------------------- 14 guarantees
S["guarantees"] = section("guarantees",
    kicker("What a name can’t do") + title("Two kinds of guarantee")
    + at(140, 290, 1640, f'<div style="display:flex; gap:28px; align-items:stretch">'
        + box(label("1 · Ukraine itself", RUST, 21) + f'<p style="font-family:{SERIF}; font-size:40px; line-height:1.05">The U.S., Europe and NATO</p>'
              + p("Already under negotiation, and the main subject of the Miami talks. They should rest on a treaty, not on any one government’s goodwill. A condominium doesn’t replace them; it depends on them.", 27), pad=30, extra=" flex:1")
        + box(label("2 · The condominium", RUST, 21) + f'<p style="font-family:{SERIF}; font-size:40px; line-height:1.05">Monitors and arbiters</p>'
              + p("From states both sides can accept. The UAE, which has hosted trilateral talks and prisoner exchanges, is an obvious candidate; Turkey, India and Serbia are further possibilities. A naive first pass.", 27), pad=30, extra=" flex:1")
        + '</div>')
    + at(140, 790, 1640, p("Without credible guarantors, any condominium becomes what Minsk was: a piece of paper that buys time for the next invasion.", 32, INK, True)),
    "GUARANTEES")

# ---------------------------------------------------------------- 15 the plebiscite
def ballot(country, q_native, q_en, name):
    return box(label(f"Ballot · {country}", MUTED, 19) + f'<p style="font-family:{SERIF}; font-size:34px; line-height:1.2">{q_native}</p>'
               + p(q_en, 22, MUTED, True)
               + f'<div style="display:flex; gap:40px; margin-top:8px; font-family:{COND}; font-size:24px">'
               + '<span>☐ ' + ("Так" if country == "Ukraine" else "Да") + '</span><span>☐ ' + ("Ні" if country == "Ukraine" else "Нет") + '</span></div>',
               pad=30, extra=f" flex:1; border:2px dashed {INK}")
S["plebiscite"] = section("plebiscite",
    kicker("Ratification") + title("A plebiscite in both nations")
    + at(140, 290, 1640, f'<div style="display:flex; gap:28px; align-items:stretch">'
        + ballot("Ukraine", "Чи схвалюєте ви договір про Кондомініум «Київська Русь»?", "Do you approve the treaty establishing the Kyivan Rus Condominium?", "")
        + ballot("Russia", "Одобряете ли вы договор о Кондоминиуме «Киевская Русь»?", "Do you approve the treaty establishing the Kyivan Rus Condominium?", "")
        + '</div>')
    + at(140, 640, 1640, numbered([
        "Ukraine’s constitution requires a referendum for any change to its territory, and Kyiv has accepted one in principle.",
        "Russians deserve a vote on whether they continue to throw their countrymen away as lambs to the slaughter.",
        "Both votes fall inside the ceasefire, with no strikes on either side’s cities while the polls are open."], 28, 12)),
    "RATIFICATION")

# ---------------------------------------------------------------- 16 limits
S["limits"] = section("limits",
    kicker("What this proposal doesn’t do") + title("Limits, stated up front")
    + at(140, 300, 1640, numbered([
        "If Putin values “we took it” more than the world’s acceptance, the trade fails. Russia has lived with the non-recognition of Crimea since 2014.",
        "Covering the whole line turns a Donbas proposal into a settlement of the war, a larger claim than one essay can carry.",
        "It doesn’t settle how enforcement would work, or how Ukraine’s rights inside the condominium would be protected in practice."], 34, 22))
    + at(140, 800, 1640, p("I’m a security engineer, not a historian of the Slavic world; I expect specialists to refine the history. The argument depends on one observation: the compromise has a mechanism but no name.", 27, MUTED, True)),
    "LIMITS")

# ---------------------------------------------------------------- 17 close
S["close"] = section("close", contours(1920, 1080, 12, 3)
    + at(240, 340, 1440, p("What it offers is simpler: a name and a narrative for a compromise that currently has neither.", 64, INK, False, "; text-align:center; line-height:1.15"))
    + at(240, 580, 1440, p("Maybe that is what allows a deal to move from technically possible to politically survivable.", 38, MUTED, True, "; text-align:center"))
    + at(240, 800, 1440, f'<p style="font-family:{COND}; font-size:26px; color:{MUTED}; text-align:center">The op-ed · {a("kyivan-rus-condominium.md", "kyivan-rus-condominium.md")} · the companion plan · {a("The Islamabad Accords", "https://dhanna11.github.io/islamabad-accords/")}</p>'),
    "THE KYIVAN RUS CONDOMINIUM")

# ---------------------------------------------------------------- 18 sources
SOURCES = [
    ("DeepState map data, 1 Jan and 9 Nov 2026", "https://deepstatemap.live/"),
    ("OpenStreetMap: Donetsk Oblast border (© contributors, ODbL)", "https://www.openstreetmap.org/"),
    ("Natural Earth: coastline and borders", "https://www.naturalearthdata.com/"),
    ("NYT, 18 Feb 2026: demilitarized zone talks", "https://www.nytimes.com/2026/02/18/world/europe/ukraine-russia-peace-talks-demilitarized-zone.html"),
    ("Kyiv Independent: joint rule with Russia in Donbas", "https://kyivindependent.com/joint-rule-with-russia-in-donbas/"),
    ("Euronews, Oct 2025: freezing at the front line", "https://www.euronews.com/2025/10/23/freezing-the-war-at-current-frontlines-is-a-good-compromise-zelenskyy-says"),
    ("Al Jazeera: the 28-point plan in full", "https://www.aljazeera.com/news/2025/11/21/trumps-28-point-ukraine-plan-in-full-what-it-means-could-it-work"),
    ("Kyiv Independent: the 20-point draft", "https://kyivindependent.com/zelensky-reveals-20-point-peace-plan-draft-backed-by-ukraine-us/"),
    ("Kremlin, 2021: “On the Historical Unity of Russians and Ukrainians”", "http://en.kremlin.ru/events/president/news/66181"),
    ("Kyiv Independent / FT, Oct 2026: Putin’s history lecture to Nordic leaders", "https://kyivindependent.com/putin-lectured-nordic-leaders-on-russian-history-during-latest-call-ft-reports/"),
    ("RFE/RL: Putin on Crimea as Russia’s Temple Mount (2014)", "https://www.rferl.org/a/putin-crimea-orthodox-vladimir-great-religion-ukraine-russia/26725761.html"),
    ("MK, 2022: why the textbook dropped “Kievan Rus”", "https://www.mk.ru/social/2022/05/23/avtor-novogo-uchebnika-istorii-obyasnil-otsutstvie-kievskoy-rusi.html"),
    ("Wilson Center: Russia’s 2020 constitutional amendment", "https://wilsoncenter.org/blog-post/2020-amendment-russian-constitution-another-sign-putins-invasion-isnt-going-planned"),
    ("International IDEA: Ukraine’s Article 73", "https://www.idea.int/node/57655"),
    ("The 1997 Partition Treaty (Black Sea Fleet)", "https://en.wikipedia.org/wiki/Partition_Treaty_on_the_Status_and_Conditions_of_the_Black_Sea_Fleet"),
    ("The 2010 Kharkiv Pact", "https://en.wikipedia.org/wiki/Kharkiv_Pact"),
    ("The Timor Gap Treaty", "https://en.wikipedia.org/wiki/Timor_Gap"),
    ("The Saudi–Kuwaiti Neutral Zone", "https://en.wikipedia.org/wiki/Saudi_Arabian%E2%80%93Kuwaiti_neutral_zone"),
    ("Russia’s 2022 annexations and the UN vote", "https://en.wikipedia.org/wiki/Russian_annexation_of_Donetsk,_Kherson,_Luhansk_and_Zaporizhzhia_oblasts"),
    ("Axios, Oct 2026: the diesel deal", "https://www.axios.com/2026/10/10/trump-zelensky-putin-diesel-deal-war"),
    ("Condominium (international law)", "https://en.wikipedia.org/wiki/Condominium_(international_law)"),
]
half = (len(SOURCES) + 1) // 2
lst = lambda items: col(*[f'<p style="font-family:{SERIF}; font-size:23px; line-height:1.2">{a(t, h)}</p>' for t, h in items], gap=9)
S["sources"] = section("sources",
    kicker("Sources") + title("Where the facts come from", 140, 176, 64)
    + at(140, 280, 800, lst(SOURCES[:half])) + at(980, 280, 800, lst(SOURCES[half:]))
    + at(140, 860, 1640, mono("AI DISCLOSURE · THE ARGUMENT IS THE AUTHOR’S · CLAUDE HELPED RESEARCH AND REFINE THE DRAFT, AND BUILT THIS DECK AND ITS MAPS · "
        + a("GITHUB.COM/DHANNA11/KYIVAN-RUS-CONDOMINIUM", "https://github.com/dhanna11/kyivan-rus-condominium"), 16)),
    "SOURCES")

assert set(ORDER) == set(S), set(ORDER) ^ set(S)
(OUT / "slides").mkdir(parents=True, exist_ok=True)
for old in (OUT / "slides").glob("*.html"):
    if old.stem not in S: old.unlink()
for sid in ORDER: (OUT / "slides" / f"{sid}.html").write_text(S[sid])
(OUT / "deck.json").write_text(json.dumps({"title": "The Kyivan Rus Condominium", "order": ORDER, "sections": {
    "open": {"description": "Title.", "start": "cover"},
    "problem": {"description": "The impasse, the front since January, and the plans that came before.", "start": "deadlock"},
    "proposal": {"description": "The mechanism, the map, the trade, the law, and the revenue.", "start": "condominium"},
    "name": {"description": "Why the name matters, the Kyivan Rus name on this map, and the candidates.", "start": "why-name"},
    "alternatives": {"description": "The demilitarized-strip version, compared.", "start": "other-map"},
    "make-it-real": {"description": "Guarantees and ratification.", "start": "guarantees"},
    "close": {"description": "Limits, the close and sources.", "start": "limits"}}}, indent=1, ensure_ascii=False) + "\n")
print("wrote", N, "slides")
