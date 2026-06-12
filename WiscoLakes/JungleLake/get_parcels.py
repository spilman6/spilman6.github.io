"""
get_parcels.py — Parcels around Jungle Lake (Forest County, WI)

Queries the Wisconsin Statewide Parcel Map (V11) with a spatial buffer:
"every parcel within RADIUS_M meters of the lake's center point."
Writes parcels.json keyed by PARCELID (the dashed 022-... format):

{
  "022-01077-0000": {
    "owner": "...",
    "site_address": "...",
    ...
  }
}

Usage:
    pip install requests
    python get_parcels.py
"""

import json
import requests

LAYER_URL = ("https://dnrmaps.wi.gov/arcgis/rest/services/DW_Map_Dynamic/"
             "EN_County_Tax_Parcels_WTM_Ext_Dynamic_L16/MapServer/0")

# Jungle Lake center — verify/tweak by right-clicking the lake in Google Maps
LAT = 45.455202849623944
LON = -88.83247649309125       # <-- confirm this; the lake is just west of Pickerel

RADIUS_M = 1200       # meters from center; bump up to widen the net

OUTPUT = "parcels.json"
MAX_RETRIES = 5

# V11 schema fields (statewide-standardized)
FIELDS = ["TAXPARCELID"]

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (parcel-export)"


def get_json(params):
    params = dict(params, f="json")
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(f"{LAYER_URL}/query", params=params, timeout=120)
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
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "distance": RADIUS_M,
        "units": "esriSRUnit_Meter",
    }

    count = get_json({**spatial, "where": "1=1",
                      "returnCountOnly": "true"})["count"]
    print(f"{count} parcels within {RADIUS_M} m of ({LAT}, {LON}).")
    if count == 0:
        print("Zero parcels — double-check LAT/LON.")
        return
    if count >= 1000:
        print("WARNING: hit the 1000-record cap; shrink RADIUS_M or add paging.")

    page = get_json({**spatial,
                     "where": "1=1",
                     "outFields": ",".join(FIELDS),
                     "returnGeometry": "false"})

    ids = sorted(set(
        clean(feat["attributes"].get("TAXPARCELID"))
        for feat in page.get("features", [])
        if clean(feat["attributes"].get("TAXPARCELID"))
    ))

    with open(OUTPUT, "w") as f:
        json.dump(ids, f, indent=2)
    print(f"Done. {len(ids)} parcels -> {OUTPUT}")


if __name__ == "__main__":
    main()
