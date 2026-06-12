"""
scrape_beacon.py — Fetch 2025 parcel data for Lake Lucerne from Beacon Schneidercorp
Forest County, WI (AppID=1198, LayerID=36063)

Uses Playwright (real Chrome) to pass Cloudflare's managed challenge.
Reads parcels.json, hits each parcel's Beacon Report page, parses the HTML,
and writes beacon_data.json — a dict keyed by TAXPARCELID.

Resume-safe: already-fetched parcels are skipped on re-run.

Usage:
    pip install playwright beautifulsoup4
    playwright install chromium
    python scrape_beacon.py
"""

import json
import os
import os.path
import re
import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

BEACON_URL = (
    "https://beacon.schneidercorp.com/Application.aspx"
    "?AppID=1198&LayerID=36063&PageTypeID=4&PageID=13680&KeyValue={key}"
)
INPUT   = "parcels.json"
OUTPUT  = "beacon_data.json"
DELAY   = 1.2   # seconds between parcels


def parse_money(s):
    if not s:
        return 0
    cleaned = re.sub(r"[^\d.]", "", str(s))
    try:
        return float(cleaned)
    except ValueError:
        return 0


def parse_float(s):
    if not s:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", str(s))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_page(html, parcel_id):
    soup = BeautifulSoup(html, "html.parser")
    data = {
        "owner":   "",
        "address": "",
        "acres":   0.0,
        "value":   0,
        "land":    0,
        "impr":    0,
        "fmv":     0,
    }

    # ── Build a flat label→value map from all table rows and labeled elements ──
    pairs = {}
    for row in soup.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in row.find_all(["th", "td"])]
        if len(cells) >= 2:
            pairs[cells[0].lower().rstrip(":")] = cells[1]

    for el in soup.find_all(attrs={"class": re.compile(r"label|field.label", re.I)}):
        label = el.get_text(" ", strip=True).lower().rstrip(":")
        nxt = el.find_next_sibling()
        if nxt:
            pairs[label] = nxt.get_text(" ", strip=True)

    # ── Owner ──
    for key in ("owner", "owner name", "property owner", "taxpayer", "taxpayer name"):
        if key in pairs:
            data["owner"] = pairs[key]
            break

    # ── Address ──
    for key in ("site address", "property address", "address", "location"):
        if key in pairs:
            data["address"] = pairs[key]
            break

    # ── Acreage ──
    for key in ("acres", "acreage", "total acres", "assessed acres", "net acres"):
        if key in pairs:
            data["acres"] = parse_float(pairs[key])
            break

    # ── Valuation — look for the 2025 row in any table ──
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        for row in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cells or cells[0] != "2025":
                continue

            col = {}
            for i, h in enumerate(headers):
                if i < len(cells):
                    col[h] = cells[i]

            for k in ("land", "land value"):
                if k in col: data["land"] = parse_money(col[k]); break
            for k in ("improvements", "improvement", "building", "bldg"):
                if k in col: data["impr"] = parse_money(col[k]); break
            for k in ("total", "total assessed", "assessed value", "total value"):
                if k in col: data["value"] = parse_money(col[k]); break
            for k in ("fair market", "fmv", "fair market value", "est. fair market"):
                if k in col: data["fmv"] = parse_money(col[k]); break

            # Positional fallback if headers didn't align
            if not data["value"] and len(cells) >= 4:
                data["land"]  = parse_money(cells[1])
                data["impr"]  = parse_money(cells[2])
                data["value"] = parse_money(cells[3])
                if len(cells) >= 5:
                    data["fmv"] = parse_money(cells[4])
            break

    # ── Fallback: generic pairs if no year table found ──
    if not data["value"]:
        for key in ("total assessed value", "assessed value", "total value", "total assessed"):
            if key in pairs: data["value"] = parse_money(pairs[key]); break
        for key in ("land value", "land"):
            if key in pairs: data["land"] = parse_money(pairs[key]); break
        for key in ("improvement value", "improvements", "building value"):
            if key in pairs: data["impr"] = parse_money(pairs[key]); break
        for key in ("fair market value", "estimated fair market value", "fmv"):
            if key in pairs: data["fmv"] = parse_money(pairs[key]); break

    return data


def main():
    with open(INPUT) as f:
        ids = json.load(f)

    results = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT) as f:
            results = json.load(f)
        print(f"Resuming — {len(results)} already fetched.")

    todo = [pid for pid in ids if pid not in results]
    print(f"{len(ids)} parcels total, {len(todo)} to fetch.\n")

    with sync_playwright() as p:
        # Find system Chrome; fall back to Playwright's Chromium with stealth args
        chrome_candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        chrome_exe = next((c for c in chrome_candidates if os.path.exists(c)), None)

        import tempfile
        tmp_profile = tempfile.mkdtemp(prefix="playwright_chrome_")

        launch_kwargs = {
            "headless": False,
            "viewport": {"width": 1280, "height": 800},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        }
        if chrome_exe:
            print(f"Using Chrome: {chrome_exe}")
            launch_kwargs["executable_path"] = chrome_exe
        else:
            print("System Chrome not found — using Playwright Chromium")

        # launch_persistent_context keeps a separate profile so it doesn't
        # merge into an already-running Chrome window
        ctx = p.chromium.launch_persistent_context(tmp_profile, **launch_kwargs)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Let the user navigate manually so Cloudflare sees a human.
        print("\nChrome is open.")
        print("  1. In the Chrome window, type this URL and press Enter:")
        print(f"     https://beacon.schneidercorp.com/Application.aspx?AppID=1198&LayerID=36063&PageTypeID=4&PageID=13680&KeyValue=020-00958-0001")
        print("  2. Solve the CAPTCHA if prompted.")
        print("  3. Wait for the parcel page to fully load.")
        print("  4. Come back here and press Enter to start the automated run.")
        input("\nPress Enter when the Beacon page is loaded > ")

        for i, pid in enumerate(todo, 1):
            url = BEACON_URL.format(key=pid)
            print(f"[{i:>4}/{len(todo)}] {pid} ...", end=" ", flush=True)

            try:
                page.goto(url, wait_until="commit", timeout=30000)
                page.wait_for_timeout(2500)  # let Cloudflare JS + page render
                html = page.content()
            except PlaywrightTimeout:
                print("TIMEOUT — skipping")
                continue
            except Exception as e:
                print(f"ERROR ({e}) — skipping")
                continue

            data = parse_page(html, pid)
            results[pid] = data

            owner_display = (data["owner"] or "?")[:35]
            print(f"owner={owner_display:<35}  value=${data['value']:>10,.0f}")

            with open(OUTPUT, "w") as f:
                json.dump(results, f, indent=2)

            time.sleep(DELAY)

        ctx.close()

    print(f"\nDone. {len(results)} parcels in {OUTPUT}")
    valued = [v for v in results.values() if v["value"] > 0]
    print(f"Parcels with value data: {len(valued)} / {len(results)}")
    if valued:
        print(f"Total assessed value:    ${sum(v['value'] for v in valued):,.0f}")


if __name__ == "__main__":
    main()
