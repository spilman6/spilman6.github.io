"""
get_parcels.py — Parcels around Jungle Lake (Forest County, WI)

Uses a shoreline-hugging polygon (points traced around the lake in Google
Maps) so the query captures lakefront parcels without pulling in large
forest/farm parcels farther out.  Adjust RING coordinates to expand or
shrink the capture area.

Usage:
    pip install requests
    python get_parcels.py
"""

import json
import requests

API = ("https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/"
       "Wisconsin_Statewide_Parcels/FeatureServer/0/query")

# Shoreline polygon around Jungle Lake — Forest County, WI
# Points traced clockwise from the NW shore; (lon, lat) order for ArcGIS.
RING = [
    [-88.835018, 45.459189],  # NW shore
    [-88.831558, 45.460338],  # N
    [-88.828281, 45.459955],  # NE
    [-88.827128, 45.457784],  # E
    [-88.826369, 45.455357],  # E
    [-88.826824, 45.453144],  # SE
    [-88.828979, 45.451611],  # S
    [-88.832226, 45.450781],  # S
    [-88.835078, 45.450376],  # SW
    [-88.838507, 45.450844],  # SW
    [-88.841572, 45.452569],  # W
    [-88.835018, 45.459189],  # close ring
]

POLYGON = {
    "rings": [RING],
    "spatialReference": {"wkid": 4326},
}

OUTPUT = "parcels.json"
MAX_RETRIES = 5
PAGE_SIZE = 1000

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (parcel-export)"


def get_json(params):
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.post(API, data={**params, "f": "json"}, timeout=120)
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                raise RuntimeError(f"ArcGIS error: {data['error']}")
            return data
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.Timeout,
                requests.exceptions.JSONDecodeError) as e:
            last_err = e
            print(f"    retry {attempt}/{MAX_RETRIES} ({type(e).__name__})")
    raise last_err


def clean(v):
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def main():
    spatial = {
        "geometry":     json.dumps(POLYGON),
        "geometryType": "esriGeometryPolygon",
        "inSR":         "4326",
        "spatialRel":   "esriSpatialRelIntersects",
        "where":        "CONAME = 'FOREST'",
    }

    count_data = get_json({**spatial, "returnCountOnly": "true"})
    count = count_data.get("count", 0)
    print(f"{count} Forest County parcels intersecting shoreline polygon.")
    if count == 0:
        print("Zero parcels — double-check RING coordinates.")
        return
    if count >= 1000:
        print("WARNING: may hit record cap — add paging if ids look truncated.")

    feats = []
    offset = 0
    while True:
        data = get_json({**spatial,
                         "outFields": "TAXPARCELID,OWNERNME1",
                         "returnGeometry": "false",
                         "resultRecordCount": str(PAGE_SIZE),
                         "resultOffset": str(offset)})
        page = data.get("features", [])
        feats.extend(page)
        print(f"  fetched {len(feats)} / {count} ...")
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    print(f"  sample: {feats[0]['attributes'] if feats else 'none'}")

    ids = sorted(set(
        clean(f["attributes"].get("TAXPARCELID"))
        for f in feats
        if clean(f["attributes"].get("TAXPARCELID"))
    ))

    with open(OUTPUT, "w") as f:
        json.dump(ids, f, indent=2)
    print(f"Done. {len(ids)} parcels -> {OUTPUT}")


if __name__ == "__main__":
    main()
