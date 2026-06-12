"""
get_parcels.py — Parcels around Legend Lake (Menominee County, WI)

Queries the Wisconsin Statewide Parcels FeatureServer with a spatial buffer.
Unlike the DNR layer, this service has real owner/value data for Menominee County.
Writes parcels.json as a sorted list of TAXPARCELID strings.

Usage:
    pip install requests
    python get_parcels.py
"""

import json
import requests

# Statewide parcels service — has Menominee County attribute data
API = ("https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/"
       "Wisconsin_Statewide_Parcels/FeatureServer/0/query")

# Legend Lake center — Menominee County, WI
LAT = 44.8980
LON = -88.5720

RADIUS_M = 7000       # Legend Lake is ~9km across; wider net catches all shores

OUTPUT = "parcels.json"
MAX_RETRIES = 5
PAGE_SIZE = 1000      # fetch in pages to bypass per-request record cap

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
        "geometry": json.dumps({"x": LON, "y": LAT,
                                "spatialReference": {"wkid": 4326}}),
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": str(RADIUS_M),
        "units": "esriSRUnit_Meter",
        "where": "CONAME = 'MENOMINEE'",
    }

    count_data = get_json({**spatial, "returnCountOnly": "true"})
    count = count_data.get("count", 0)
    print(f"{count} Menominee parcels within {RADIUS_M} m of ({LAT}, {LON}).")
    if count == 0:
        print("Zero parcels — double-check LAT/LON.")
        return
    if count >= 1000:
        print("WARNING: may hit record cap — add paging if ids look truncated.")

    # Page through all records to avoid the per-request cap
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
