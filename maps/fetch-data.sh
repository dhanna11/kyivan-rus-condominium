#!/usr/bin/env bash
# Downloads the map inputs into the directory given (default maps/data, git-ignored), then: python3 maps/build_maps.py maps/data
set -euo pipefail
D="${1:-$(dirname "$0")/data}"; mkdir -p "$D"; cd "$D"
curl -sSf -A "Mozilla/5.0" -o deepstate_now.json "https://deepstatemap.live/api/history/last"
curl -sSf -A "Mozilla/5.0" -o hist.json "https://deepstatemap.live/api/history/public"
JAN=$(python3 -I -c "import json; print([x for x in json.load(open('hist.json')) if x['createdAt'].startswith('2026-01-01')][0]['id'])")
curl -sSf -A "Mozilla/5.0" -o deepstate_jan.json "https://deepstatemap.live/api/history/$JAN/geojson"
curl -sSf -A "kyivan-rus-condominium-maps" -o donetsk.json "https://nominatim.openstreetmap.org/search?q=Donetsk+Oblast&countrycodes=ua&format=geojson&polygon_geojson=1&polygon_threshold=0.005&limit=1"
curl -sSf -o ne_10m_land.geojson "https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_10m_land.geojson"
curl -sSf -o ne_50m_admin0.geojson "https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_50m_admin_0_countries.geojson"
echo "data in $D"
