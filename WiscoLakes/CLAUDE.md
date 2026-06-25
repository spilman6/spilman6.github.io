# WiscoLakes — Claude Context

Private property-registry website for Wisconsin lakefront parcels. Hosted at `spilman6.github.io/WiscoLakes/`. Plain HTML/CSS/JS, no build step, no framework.

---

## Lakes (7 total)

| Directory | Lake | County/Counties | Parcel count |
|---|---|---|---|
| `ArbutusLake/` | Arbutus Lake | Forest | ~70 |
| `JungleLake/` | Jungle Lake | Forest | ~40 |
| `LakeLucerne/` | Lake Lucerne | Forest | ~90 |
| `LegendLake/` | Legend Lake | Forest | ~130 |
| `MetongaLake/` | Metonga Lake | Forest (City of Crandon + Town of Lincoln) | 296 |
| `PickerelLake/` | Pickerel Lake | Forest + Langlade | ~200 |
| `stJohns/` | St. Johns Lake | Forest | ~60 |

Hub page: `WiscoLakes/index.html` — shows a card grid with a "7 Lakes" badge.

---

## File structure per lake

```
LakeName/
  index.html        # Property registry table/grid view
  map.html          # Leaflet parcel map
  parcels.json      # Parcel ID list (see formats below)
  lake-facts.json   # Lake stats for modal (optional — Metonga lacks this)
  LakeName.png      # Lake silhouette image (optional)
  get_parcels.py    # Python script to re-run parcel discovery (personal machine)
  get_lake_facts.py # Python script to scrape DNR lake facts
```

---

## parcels.json format

**Single-county lakes** (flat array, used by most lakes):
```json
["022-01476-0000", "022-01478-0000", ...]
```

**Multi-county lakes** (keyed object, used by Pickerel and Metonga):
```json
{
  "langlade": ["0040929.002", ...],
  "forest":   ["020-00136-0000", ...]
}
```

Metonga uses `{ "forest": [...] }` only (no Langlade key).

### Parcel ID formats by county

| County | Format | Example | Township prefix |
|---|---|---|---|
| Forest — Town of Lincoln | `020-XXXXX-XXXX` | `020-00136-0000` | 020 |
| Forest — Town of Nashville | `022-XXXXX-XXXX` | `022-01476-0000` | 022 |
| Forest — City of Crandon | `211-XXXXX-XXXX` | `211-01540-0000` | 211 |
| Langlade | `XXXXXXX.XXX` | `0040929.002` | (no prefix) |

---

## PIN system

All lakes share the same 4-digit PIN. Each map/index has identical encoding:

```javascript
const CORRECT = [98, 100, 98, 100].map((n) => String.fromCharCode(n ^ 82)).join("");
```

The XOR key is `82`. Decoded: `[98^82, 100^82, 98^82, 100^82]` = `[48, 54, 48, 54]` → `"0606"`.

Each lake uses a unique `localStorage` key to cache 24-hour auth independently:

| Lake | CACHE_KEY |
|---|---|
| Arbutus | `al_pin_ts` |
| Jungle | `jl_pin_ts` |
| Lake Lucerne | `ll_pin_ts` |
| Legend | `lgl_pin_ts` |
| Metonga | `mtg_pin_ts` |
| Pickerel | `pkl_pin_ts` |
| St. Johns | `stj_pin_ts` |

---

## ArcGIS REST API

**Statewide Parcels endpoint:**
```
https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels/FeatureServer/0/query
```

Key query fields: `TAXPARCELID`, `PARCELID`, `OWNERNME1`, `OWNERNME2`, `SITEADRESS`, `ASSDACRES`, `CNTASSDVALUE`, `LNDVALUE`, `IMPVALUE`, `TAXROLLYEAR`, `CONAME`

- `CONAME = 'FOREST'` for Forest County
- `CONAME = 'LANGLADE'` for Langlade County
- Spatial reference: WKID 3071 (Wisconsin Transverse Mercator) — pass `inSR: 4326` when sending WGS84 geometry

**Important:** String equality queries (`TAXPARCELID = '...'`) fail on this service when the value contains hyphens. Use `IN (...)` lists or `LIKE '...'` instead.

**Access sites layer** (for boat launches in lake-facts):
```
https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/accesssites_shp/FeatureServer/0/query
```

---

## Beacon (Schneidercorp) parcel viewer

Forest County Beacon URL for a parcel detail page:
```
https://beacon.schneidercorp.com/Application.aspx?AppID=1198&LayerID=36063&PageTypeID=1&PageID=13677&KeyValue=<TAXPARCELID>
```

Beacon displays parcel IDs without hyphens and zero-padded to 12 digits (e.g. `211015400000`). Map to TAXPARCELID by splitting: county(3) + parcel(5) + suffix(4) → `211-01540-0000`.

---

## Python scripts (run on personal machine, not work laptop)

### get_parcels.py

Uses a hand-traced shoreline polygon to spatially intersect the ArcGIS parcels layer. Outputs `parcels.json`. Template:

```python
RING = [
    [-88.xxx, 45.xxx],  # NW  (lon, lat order for ArcGIS)
    ...
    [-88.xxx, 45.xxx],  # close ring — same as first point
]
POLYGON = {"rings": [RING], "spatialReference": {"wkid": 4326}}

params = {
    "geometry":     json.dumps(POLYGON),
    "geometryType": "esriGeometryPolygon",
    "inSR":         "4326",
    "spatialRel":   "esriSpatialRelIntersects",
    "where":        "CONAME = 'FOREST'",
    "outFields":    "TAXPARCELID,OWNERNME1",
    "returnGeometry": "false",
    "f": "json",
}
```

Posts to the statewide parcels endpoint. Pages through results with `resultOffset` / `resultRecordCount=1000`.

### get_lake_facts.py

Scrapes Wisconsin DNR "Find A Lake" pages using the WBIC (Waterbody Identification Code):
```
https://apps.dnr.wi.gov/lakes/lakepages/LakeDetail.aspx?wbic=<WBIC>
```

Outputs `lake-facts.json` with: name, wbic, county, surface_acres, max_depth_ft, mean_depth_ft, water_clarity, trophic_status, lake_type, bottom, fish species list, boat launches.

---

## Metonga Lake — specific notes

- **Center:** `[45.542218, -88.903582]`
- **Counties:** Forest only (no Langlade)
- **Parcel prefix split:** Town of Lincoln (`020-`), City of Crandon (`211-`)
- **Parcels discovered via address query** (no `get_parcels.py` yet) because the DNR lake polygon for Metonga is not individually queryable from the statewide water layer — the `002_WATER` feature contains all Wisconsin water bodies as one 1236-ring multipolygon
- **Known lakeshore streets:**
  - Town of Lincoln (020-): E Lakeview St, Strawberry Bluff Ln, Timber Ln, Sportsman's Ln, Smiths Ln, Plank Rd, Resch Ln, N Farmers Bay Ln
  - City of Crandon (211-): W/E Lakeview St, Zinzer Rd, Keeler St, Wescott Ave, Risser Rd, Teschner Rd, Tracy Rd, Strawberry Bluff Ln
- **No `lake-facts.json`** yet (WBIC unknown; needs to be looked up)
- **No `get_parcels.py`** yet — to do: trace a shoreline polygon and run on personal machine to verify/replace the address-based list
- **`Metonga-Lake.png`** exists in the directory

### Excluded parcel ranges (not lakefront)
- `006-` prefix Sportsman Ln — 40-acre parcels in a different township
- `022-` prefix Timber Ln — Nashville township, different location
- `211-` N Lake Ave — downtown Crandon commercial, not waterfront
- `211-` S Lake Ave 100–619 — mixed commercial downtown, not shoreline
- `211-01548-0000` (711 W Pioneer St) and `211-01549-0000` (801 W Pioneer St) — not confirmed lakefront

---

## DNR lake facts source

```
https://apps.dnr.wi.gov/lakes/lakepages/LakeDetail.aspx?wbic=<WBIC>
```

Find WBIC at: `https://apps.dnr.wi.gov/lakes/lakefinder/`

---

## Work environment note

The FVTC work laptop has group policies that block PowerShell `Invoke-RestMethod` mid-execution. Use `curl` via Bash as a workaround, or do heavy ArcGIS spatial queries from the personal laptop where there are no restrictions.
