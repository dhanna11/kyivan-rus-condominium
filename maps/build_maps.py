#!/usr/bin/env python3
"""Builds the deck's maps from open data. Run: python3 maps/build_maps.py <data-dir>
(maps/fetch-data.sh downloads the inputs). Writes, beside this script:
  oblast.svg      Donetsk Oblast: held by Ukraine, gray zone, occupied (the impasse slide)
  front-north.svg the northern Donbas, 1 January vs the latest snapshot (the front slide)
  line.svg        all of Ukraine: the territory Russia holds, drawn as the condominium (the map slide)
  stats.json      every number the slides quote, with the snapshot dates
Each SVG is a 1920x1080 overlay that a slide places as its first layer.

Sources: Donetsk Oblast border from OpenStreetMap via Nominatim (ODbL, © OpenStreetMap contributors); coastline and
Ukraine's outline from Natural Earth (public domain), with Crimea added from DeepState's own polygon because Natural
Earth's default world file draws Crimea outside Ukraine; occupied and unknown-status areas from DeepState
(deepstatemap.live), a Ukrainian volunteer project. Shares are measured on a local equal-area approximation
(longitude scaled by cos of the map's middle latitude), good to about a percent at this scale."""
import json, math, sys, datetime
from pathlib import Path
from shapely.geometry import shape, box, Point, MultiPoint
from shapely.ops import unary_union
from shapely import affinity

D = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
INK, MUTED, RUST, SALT, STONE, TEAL = "#2a2620", "#6b6253", "#a4492b", "#f7f3ea", "#cfc4b0", "#2f6f73"
LAB = 'font-family="IBM Plex Sans Condensed" font-weight="600"'

def load(name): return json.loads((D / name).read_text())

def layer(feats, prefixes):
    gs = [shape(f["geometry"]).buffer(0) for f in feats if f["geometry"]["type"] in ("Polygon", "MultiPolygon")
          and f["properties"].get("name", "").startswith(prefixes)]
    return unary_union(gs)

OCC = ("Окуповано", "ОРДЛО", "Окупований Крим", "Острів Тузла")
now_doc = load("deepstate_now.json")
NOW = datetime.datetime.fromtimestamp(now_doc["id"], datetime.UTC).date()
now, jan = now_doc["map"]["features"], load("deepstate_jan.json")["features"]
occ_now, occ_jan = layer(now, OCC), layer(jan, OCC)
unk_now = layer(now, ("Статус невідомий",)).difference(occ_now)

bounds_ua = box(21.5, 44.0, 41.0, 52.6)
land = unary_union([shape(f["geometry"]).buffer(0).intersection(bounds_ua) for f in load("ne_10m_land.geojson")["features"]
                    if shape(f["geometry"]).intersects(bounds_ua)])
ukr = next(shape(f["geometry"]) for f in load("ne_50m_admin0.geojson")["features"] if f["properties"].get("ADM0_A3") == "UKR")
crimea = layer(now, ("Окупований Крим", "Острів Тузла"))
ukraine = unary_union([ukr.buffer(0), crimea]).intersection(land)
oblast = shape(load("donetsk.json")["features"][0]["geometry"]).buffer(0).intersection(land)   # the admin line runs into the Azov Sea
if oblast.geom_type != "Polygon": oblast = max(oblast.geoms, key=lambda g: g.area)

def km2(g, lat):
    k = math.cos(math.radians(lat))
    return affinity.scale(g, 111.32 * k, 111.32, origin=(0, 0)).area
SQMI = 2.589988

def flat(g):
    if g.is_empty: return []
    if g.geom_type == "Polygon": return [g]
    return [q for sub in getattr(g, "geoms", []) for q in flat(sub)]

class Proj:
    """Equirectangular projection of a lon/lat window into a pixel box, longitude scaled by cos(middle latitude)."""
    def __init__(self, bounds, height, right=None, left=None, top=120):
        x0, y0, x1, y1 = bounds
        self.b, self.k = bounds, math.cos(math.radians((y0 + y1) / 2))
        self.ky = height / (y1 - y0); self.kx = self.ky * self.k
        w = (x1 - x0) * self.kx
        self.ox = left if left is not None else right - w
        self.oy, self.w, self.h = top, w, height
    def __call__(self, lon, lat): return (self.ox + (lon - self.b[0]) * self.kx, self.oy + (self.b[3] - lat) * self.ky)
    def path(self, g, tol=0.002):
        out = []
        for p in flat(g.simplify(tol, preserve_topology=True)):
            for ring in [p.exterior, *p.interiors]:
                pts = [self(x, y) for x, y, *_ in ring.coords]
                if len(pts) > 2: out.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
        return " ".join(out)
    def miles(self, mi): return mi * 1.609 / (111.32 * self.k) * self.kx

def defs(tag):
    return (f'<defs><pattern id="hatch-{tag}" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="9" height="9" fill="{SALT}"/><path d="M0,0 V9" stroke="{RUST}" stroke-width="4"/></pattern>'
            f'<pattern id="stone-{tag}" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="{STONE}"/>'
            f'<circle cx="5" cy="5" r="1" fill="{MUTED}" opacity=".4"/></pattern></defs>')

def svg(aria, body):
    return (f'<svg role="img" aria-label="{aria}" viewBox="0 0 1920 1080" style="position:absolute; left:0; top:0; width:1920px; height:1080px">'
            + body + '</svg>')

def text(x, y, s, size=21, anchor="start", fill=INK, weight="", spacing=0, halo=True):
    w = ' font-weight="600"' if weight else ""
    h = f' paint-order="stroke" stroke="{SALT}" stroke-width="5" stroke-linejoin="round"' if halo else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-family="IBM Plex Sans Condensed"{w} font-size="{size}"{ls} '
            f'fill="{fill}"{h}>{s}</text>')

def city(P, name, lon, lat, side="r", size=21):
    x, y = P(lon, lat)
    held = not occ_now.contains(Point(lon, lat))
    mark = (f'<rect x="{x-6:.0f}" y="{y-6:.0f}" width="12" height="12" fill="{INK}"/>' if held else
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="6" fill="{SALT}" stroke="{INK}" stroke-width="2"/>')
    return mark + (text(x + 13, y + 7, name, size) if side == "r" else text(x - 13, y + 7, name, size, "end")), held

def scale_bar(x, y, px, label):
    return (f'<path d="M{x:.0f},{y:.0f} h{px:.0f}" stroke="{INK}" stroke-width="6"/>'
            f'<path d="M{x:.0f},{y-10:.0f} v20 M{x+px:.0f},{y-10:.0f} v20" stroke="{INK}" stroke-width="2"/>'
            f'<text x="{x:.0f}" y="{y-18:.0f}" font-family="JetBrains Mono" font-size="18" fill="{INK}">{label}</text>')

stats = {"snapshot_now": str(NOW), "snapshot_jan": "2026-01-01", "status": {}}

# ---- 1. Donetsk Oblast ---------------------------------------------------------------------------------------------
P = Proj(oblast.bounds, 820, right=1880 - 330, top=130)
occ_d, unk_d = occ_now.intersection(oblast), unk_now.intersection(oblast)
held_d = oblast.difference(occ_d).difference(unk_d)
lat0 = (oblast.bounds[1] + oblast.bounds[3]) / 2
stats["donetsk_oblast_sqmi"] = round(km2(oblast, lat0) / SQMI)
stats["donetsk_held_share"] = round(km2(held_d, lat0) / km2(oblast, lat0), 3)
stats["donetsk_gray_share"] = round(km2(unk_d, lat0) / km2(oblast, lat0), 3)
cities = ""
for name, lon, lat, side in [("Lyman", 37.802, 48.989, "r"), ("Siversk", 38.098, 48.866, "r"), ("Sloviansk", 37.605, 48.852, "r"),
                             ("Kramatorsk", 37.584, 48.738, "r"), ("Druzhkivka", 37.556, 48.630, "l"), ("Kostiantynivka", 37.707, 48.527, "l"),
                             ("Bakhmut", 38.000, 48.595, "r"), ("Dobropillia", 37.085, 48.467, "l"), ("Pokrovsk", 37.176, 48.282, "l"),
                             ("Donetsk", 37.803, 48.016, "r"), ("Mariupol", 37.543, 47.097, "r")]:
    s, held = city(P, name, lon, lat, side); cities += s; stats["status"][name] = "held" if held else "occupied"
hx, hy = P(36.78, 49.22); lx, ly = P(37.25, 48.98); ox, oy = P(37.95, 47.75)
bx, by = P(oblast.bounds[0] + 0.05, oblast.bounds[1] + 0.35)
(HERE / "oblast.svg").write_text(svg(
    "Map of Donetsk Oblast: the part still held by Ukraine in the north-west, the contested gray zone along the front, and the occupied rest",
    defs("o") + f'<path d="{P.path(occ_d)}" fill="url(#stone-o)" fill-rule="evenodd"/>'
    f'<path d="{P.path(held_d)}" fill="{SALT}" fill-rule="evenodd"/>'
    f'<path d="{P.path(unk_d, 0.001)}" fill="url(#hatch-o)" fill-rule="evenodd"/>'
    f'<path d="{P.path(oblast, 0.001)}" fill="none" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>' + cities
    + f'<path d="M{hx+40:.0f},{hy+34:.0f} L{lx:.0f},{ly:.0f}" stroke="{RUST}" stroke-width="2"/><circle cx="{lx:.0f}" cy="{ly:.0f}" r="4" fill="{RUST}"/>'
    + f'<text x="{hx:.0f}" y="{hy:.0f}" text-anchor="middle" {LAB} font-size="22" letter-spacing="4" fill="{RUST}"><tspan x="{hx:.0f}">HELD BY</tspan><tspan x="{hx:.0f}" dy="26">UKRAINE</tspan></text>'
    + text(ox, oy, "OCCUPIED", 24, "middle", MUTED, True, 5, False)
    + scale_bar(bx, by, P.miles(25), "25 MI")))

# ---- 2. The northern Donbas, January to now --------------------------------------------------------------------
W = box(37.25, 48.40, 38.35, 49.25)
P = Proj(W.bounds, 800, right=1880 - 120, top=120)
advance = occ_now.difference(occ_jan)
reclaimed = occ_jan.difference(occ_now).difference(unk_now)          # occupied in January, now neither occupied nor gray
lat0 = 48.8
stats["north_window"] = list(W.bounds)
stats["north_taken_by_russia_sqmi"] = round(km2(advance.intersection(W), lat0) / SQMI)
stats["north_taken_back_by_ukraine_sqmi"] = round(km2(reclaimed.intersection(W), lat0) / SQMI)
stats["oblast_taken_by_russia_sqmi"] = round(km2(advance.intersection(oblast), 48.4) / SQMI)
stats["oblast_taken_back_by_ukraine_sqmi"] = round(km2(reclaimed.intersection(oblast), 48.4) / SQMI)
clip = lambda g: g.intersection(W)
x0, y0 = P(W.bounds[0], W.bounds[3]); x1, y1 = P(W.bounds[2], W.bounds[1])
cities = ""
for name, lon, lat, side in [("Lyman", 37.802, 48.989, "r"), ("Siversk", 38.098, 48.866, "r"), ("Sloviansk", 37.605, 48.852, "l"),
                             ("Kramatorsk", 37.584, 48.738, "l"), ("Druzhkivka", 37.556, 48.630, "l"), ("Kostiantynivka", 37.707, 48.527, "r"),
                             ("Bakhmut", 38.000, 48.595, "r"), ("Yampil", 37.958, 48.930, "r")]:
    cities += city(P, name, lon, lat, side, 22)[0]
belt = MultiPoint([(37.605, 48.852), (37.584, 48.738), (37.556, 48.630), (37.707, 48.527)]).convex_hull.buffer(0.045)
bl = P(37.40, 48.53)
IX, IY = x1 - 130, y0 + 24
PI = Proj(oblast.bounds, 150, left=IX, top=IY)                      # the locator inset
IKX = PI.kx
wa, wb = PI(W.bounds[0], W.bounds[3]), PI(W.bounds[2], W.bounds[1])
(HERE / "front-north.svg").write_text(svg(
    "The northern Donbas front, January to November 2026: areas Russia took and areas Ukraine took back",
    defs("n") + f'<clipPath id="win-n"><rect x="{x0:.0f}" y="{y0:.0f}" width="{x1-x0:.0f}" height="{y1-y0:.0f}"/></clipPath>'
    f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{x1-x0:.0f}" height="{y1-y0:.0f}" fill="{SALT}"/><g clip-path="url(#win-n)">'
    f'<path d="{P.path(clip(occ_now.intersection(occ_jan)), 0.0015)}" fill="url(#stone-n)" fill-rule="evenodd"/>'
    f'<path d="{P.path(clip(advance), 0.0015)}" fill="{RUST}" fill-opacity=".8" fill-rule="evenodd"/>'
    f'<path d="{P.path(clip(reclaimed), 0.0015)}" fill="{TEAL}" fill-opacity=".8" fill-rule="evenodd"/>'
    f'<path d="{P.path(clip(unk_now), 0.0015)}" fill="url(#hatch-n)" fill-rule="evenodd"/>'
    f'<path d="{P.path(clip(oblast.boundary.buffer(0.0008)), 0.0005)}" fill="{INK}" opacity=".5"/>'
    f'<path d="{P.path(belt)}" fill="none" stroke="{INK}" stroke-width="2.5" stroke-dasharray="10 7"/>'
    + text(bl[0], bl[1], "FORTRESS", 19, "middle", INK, True, 3) + text(bl[0], bl[1] + 23, "BELT", 19, "middle", INK, True, 3)
    + cities + text(*P(37.30, 49.20), "KHARKIV OBLAST", 17, "start", MUTED, True, 3) + text(*P(37.30, 49.02), "DONETSK OBLAST", 17, "start", MUTED, True, 3)
    + f'</g><rect x="{x0:.0f}" y="{y0:.0f}" width="{x1-x0:.0f}" height="{y1-y0:.0f}" fill="none" stroke="{INK}" stroke-width="2"/>'
    f'<rect x="{IX-10:.0f}" y="{IY-10:.0f}" width="{(oblast.bounds[2]-oblast.bounds[0])*IKX+20:.0f}" height="170" fill="{SALT}" stroke="{INK}" stroke-width="1.2"/>'
    f'<path d="{PI.path(oblast, 0.01)}" fill="{STONE}" stroke="{INK}" stroke-width="1"/>'
    f'<rect x="{wa[0]:.0f}" y="{wa[1]:.0f}" width="{wb[0]-wa[0]:.0f}" height="{wb[1]-wa[1]:.0f}" fill="none" stroke="{RUST}" stroke-width="2.5"/>'
    + scale_bar(x0 + 30, y0 + 110, P.miles(5), "5 MI")))

# ---- 3. The whole line: the territory Russia holds, as the condominium -------------------------------------------
P = Proj(ukraine.bounds, 760, right=1880 - 70, top=150)
zone = occ_now.intersection(ukraine)
held_ua = ukraine.difference(zone)
lat0 = 48.5
stats["ukraine_sqmi"] = round(km2(ukraine, lat0) / SQMI)
stats["condominium_sqmi"] = round(km2(zone, lat0) / SQMI)
stats["condominium_share"] = round(km2(zone, lat0) / km2(ukraine, lat0), 3)
marks = ""
for name, lon, lat, side in [("Kyiv", 30.52, 50.45, "r"), ("Kharkiv", 36.23, 49.99, "l"), ("Dnipro", 35.05, 48.46, "l"),
                             ("Zaporizhzhia", 35.14, 47.84, "l"), ("Kherson", 32.62, 46.64, "l"), ("Odesa", 30.72, 46.48, "l"),
                             ("Kramatorsk", 37.584, 48.738, "l"), ("Donetsk", 37.80, 48.02, "r"), ("Luhansk", 39.31, 48.57, "r"),
                             ("Mariupol", 37.54, 47.10, "r"), ("Simferopol", 34.10, 44.95, "r")]:
    marks += city(P, name, lon, lat, side, 19)[0]
annex = ""
for n, lon, lat, dx, dy, label in [(1, 33.52, 44.62, -34, 22, "Sevastopol · the fleet"), (2, 34.66, 47.50, -34, -10, "Enerhodar · the nuclear plant"),
                                   (3, 33.37, 46.75, -34, -26, "Nova Kakhovka · the Dnipro and water")]:
    x, y = P(lon, lat)
    annex += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="15" fill="{RUST}" stroke="{SALT}" stroke-width="3"/>'
              f'<text x="{x:.0f}" y="{y+6:.0f}" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" font-size="17" fill="{SALT}">{n}</text>')
zx, zy = P(35.75, 46.95)
(HERE / "line.svg").write_text(svg(
    "Map of Ukraine: the territory Russia now holds, from Luhansk to Crimea, drawn as the Kyivan Rus Condominium; the rest held by Ukraine",
    defs("l") + f'<path d="{P.path(held_ua, 0.01)}" fill="{SALT}" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>'
    f'<path d="{P.path(zone, 0.006)}" fill="url(#hatch-l)" stroke="{RUST}" stroke-width="2.5" stroke-linejoin="round"/>'
    f'<path d="{P.path(ukraine, 0.01)}" fill="none" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
    + marks + annex
    + f'<text x="{zx:.0f}" y="{zy:.0f}" text-anchor="middle" {LAB} font-size="22" letter-spacing="4" fill="{RUST}" paint-order="stroke" stroke="{SALT}" stroke-width="6"><tspan x="{zx:.0f}">THE KYIVAN RUS</tspan><tspan x="{zx:.0f}" dy="26">CONDOMINIUM</tspan></text>'
    + text(*P(29.2, 49.3), "UKRAINE", 26, "middle", MUTED, True, 8, False)
    + scale_bar(P.ox + 20, P.oy + P.h - 10, P.miles(100), "100 MI")))

(HERE / "stats.json").write_text(json.dumps(stats, indent=1) + "\n")
print(json.dumps(stats, indent=1))
