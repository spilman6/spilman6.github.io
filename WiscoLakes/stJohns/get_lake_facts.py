"""
get_lake_facts.py — DNR lake facts for Saint Johns Lake (Forest County, WI)

Scrapes the Wisconsin DNR "Find A Lake" pages (no public JSON API exists)
and the statewide public water access sites layer, then writes
lake-facts.json for the Lake Facts modal.

Usage:
    pip install requests
    python get_lake_facts.py
"""

import datetime
import json
import re
import requests

WBIC = 388700
DETAIL_URL = f"https://apps.dnr.wi.gov/lakes/lakepages/LakeDetail.aspx?wbic={WBIC}"
FACTS_URL = DETAIL_URL + "&page=facts"
ACCESS_API = ("https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/"
              "accesssites_shp/FeatureServer/0/query")
ACCESS_RADIUS_M = 1500
OUTPUT = "lake-facts.json"

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (lake-facts-export)"


def text_of(url):
    html = session.get(url, timeout=60).text
    html = re.sub(r"(?s)<script.*?</script>", " ", html)
    html = re.sub(r"(?s)<style.*?</style>", " ", html)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", html)


def grab(pattern, text, cast=str):
    m = re.search(pattern, text, re.I)
    return cast(m.group(1).strip()) if m else None


def main():
    overview = text_of(DETAIL_URL)
    facts = text_of(FACTS_URL)

    lat = grab(r"Latitude, Longitude ([\d.\-]+),", facts, float)
    lon = grab(r"Latitude, Longitude [\d.\-]+,\s*([\d.\-]+)", facts, float)

    fish = [
        {"species": s.strip(), "status": st.strip()}
        for s, st in re.findall(
            r"(?:Fish )?([A-Z][A-Za-z ]+?) \((Common|Present|Abundant|Rare)\)",
            overview)
    ]

    launches = []
    if lat and lon:
        body = {
            "geometry": json.dumps({"x": lon, "y": lat,
                                    "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": str(ACCESS_RADIUS_M),
            "units": "esriSRUnit_Meter",
            "where": "1=1",
            "outFields": "Site_Name,Boat_Ramp,Carryin_Ac,Parking,Fishing,Access_Typ",
            "returnGeometry": "false",
            "f": "json",
        }
        r = session.post(ACCESS_API, data=body, timeout=60).json()
        for feat in r.get("features", []):
            a = feat["attributes"]
            launches.append({
                "name": a.get("Site_Name"),
                "boat_ramp": a.get("Boat_Ramp"),
                "carry_in": a.get("Carryin_Ac"),
                "type": a.get("Access_Typ"),
            })

    out = {
        "name": grab(r"Name ([A-Za-z .']+?) Waterbody", facts) or "Saint Johns Lake",
        "wbic": WBIC,
        "county": grab(r"County (\w+) Region", facts) or "Forest",
        "surface_acres": grab(r"Area (\d+) ACRES", facts, int),
        "max_depth_ft": grab(r"Maximum Depth (\d+) feet", facts, int),
        "mean_depth_ft": grab(r"Mean Depth (\d+) FEET", facts, int),
        "water_clarity": grab(r"water clarity is (\w+)", overview,
                              lambda s: s.capitalize()),
        "trophic_status": grab(r"Trophic Status (\w+)", facts),
        "lake_type": grab(r"Hydrologic Lake Type (\w+)", facts,
                          lambda s: s.capitalize()),
        "bottom": grab(r"Bottom ([\d%,a-z ]+?) Waterbody Type", facts),
        "latitude": lat,
        "longitude": lon,
        "fish": fish,
        "boat_launches": launches,
        "source": DETAIL_URL,
        "retrieved": datetime.date.today().isoformat(),
    }

    with open(OUTPUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Done -> {OUTPUT}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
