"""
get_parcels.py — Parcels around Lake Lucerne (Forest County, WI)

Uses a tight bounding envelope instead of a radial buffer so the query hugs
the lake's narrow N-S shape without pulling in large forest/farm parcels far
to the east and west.  Adjust the BBOX constants if you need to expand or
shrink the capture area.

Usage:
    pip install requests
    python get_parcels.py
"""

import json
import requests

API = ("https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/"
       "Wisconsin_Statewide_Parcels/FeatureServer/0/query")

# Bounding envelope around Lake Lucerne — Forest County, WI
# ~200-300 m buffer outside each shore; adjust if parcels are clipped.
BBOX = {
    "xmin": -88.857230,  # west  (NW corner)
    "ymin":  45.505176,  # south (SE corner)
    "xmax": -88.831060,  # east  (SE corner)
    "ymax":  45.554418,  # north (NW corner)
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
        "geometry":     json.dumps(BBOX),
        "geometryType": "esriGeometryEnvelope",
        "inSR":         "4326",
        "spatialRel":   "esriSpatialRelIntersects",
        "where":        "CONAME = 'FOREST'",
    }

    count_data = get_json({**spatial, "returnCountOnly": "true"})
    count = count_data.get("count", 0)
    print(f"{count} Forest County parcels within bounding envelope.")
    if count == 0:
        print("Zero parcels — double-check BBOX coordinates.")
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
