#!/usr/bin/env python3
"""
refresh_acs.py — Pull ACS 5-Year Estimates and aggregate to area boundaries.

This script:
1. Fetches tract-level ACS data for all CBSA counties
2. Downloads TIGER/Line tract shapefiles
3. Spatially joins tracts to area boundaries (neighborhood/town polygons)
4. Aggregates metrics (population-weighted) per area
5. Updates data/area-profiles.json with fresh numbers

Usage:
  pip install requests geopandas shapely
  python scripts/refresh_acs.py --year 2023 --api-key YOUR_CENSUS_KEY

Census API key: https://api.census.gov/data/key_signup.html (free)
"""

import argparse, json, os, sys, zipfile, tempfile
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

try:
    import geopandas as gpd
    from shapely.geometry import shape
except ImportError:
    sys.exit("pip install geopandas shapely")


CBSA_COUNTIES = {
    "charlotte": {
        "37": ["007","025","071","097","109","119","159","179"],
        "45": ["023","057","091"]
    },
    "raleigh": {
        "37": ["037","069","077","085","101","103","135","145","183"]
    }
}

ACS_VARS = "B19013_001E,B01002_001E,B11001_001E,B11001_002E,B15003_022E,B15003_023E,B15003_024E,B15003_025E,B15003_001E,B25077_001E,B01003_001E,NAME"


def fetch_tracts(year, state, county, key):
    url = f"https://api.census.gov/data/{year}/acs/acs5?get={ACS_VARS}&for=tract:*&in=state:{state}+county:{county}&key={key}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    rows = r.json()
    header, data = rows[0], rows[1:]
    return [dict(zip(header, row)) for row in data]


def process_tract(rec):
    def si(k):
        try: return int(rec.get(k, 0))
        except: return 0
    def sf(k):
        try: return float(rec.get(k, 0))
        except: return 0.0

    pop = si("B01003_001E")
    hh = si("B11001_001E")
    fam = si("B11001_002E")
    edu_tot = si("B15003_001E")
    ba_plus = si("B15003_022E") + si("B15003_023E") + si("B15003_024E") + si("B15003_025E")

    return {
        "geoid": f"{rec['state']}{rec['county']}{rec['tract']}",
        "pop": pop,
        "hh": hh,
        "income": si("B19013_001E"),
        "age": sf("B01002_001E"),
        "pct_fam": round(fam / hh * 100, 1) if hh > 0 else 0,
        "pct_ba": round(ba_plus / edu_tot * 100, 1) if edu_tot > 0 else 0,
        "home_val": si("B25077_001E"),
    }


def download_tiger(year, state, tmpdir):
    url = f"https://www2.census.gov/geo/tiger/TIGER{year}/TRACT/tl_{year}_{state}_tract.zip"
    print(f"    Downloading TIGER tracts for state {state}...")
    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()
    zp = os.path.join(tmpdir, f"tracts_{state}.zip")
    with open(zp, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    with zipfile.ZipFile(zp) as zf:
        zf.extractall(os.path.join(tmpdir, f"t_{state}"))
    return os.path.join(tmpdir, f"t_{state}", f"tl_{year}_{state}_tract.shp")


def aggregate_to_areas(tract_data, tract_gdf, area_gdf):
    """Spatially join tracts to areas, aggregate pop-weighted metrics."""
    results = {}
    for _, area_row in area_gdf.iterrows():
        aid = area_row["id"]
        area_geom = area_row.geometry
        matched = []
        for _, tract_row in tract_gdf.iterrows():
            if tract_row.geometry.intersects(area_geom):
                geoid = f"{tract_row['STATEFP']}{tract_row['COUNTYFP']}{tract_row['TRACTCE']}"
                if geoid in tract_data:
                    overlap = tract_row.geometry.intersection(area_geom).area / tract_row.geometry.area
                    td = tract_data[geoid].copy()
                    td["weight"] = overlap * td["pop"]
                    matched.append(td)

        if not matched:
            continue

        total_w = sum(t["weight"] for t in matched)
        if total_w == 0:
            continue

        results[aid] = {
            "total_population": int(sum(t["pop"] * (t["weight"] / t["pop"]) for t in matched if t["pop"] > 0)),
            "total_households": int(sum(t["hh"] * (t["weight"] / t["pop"]) for t in matched if t["pop"] > 0)),
            "median_household_income": int(sum(t["income"] * t["weight"] for t in matched) / total_w),
            "median_age": round(sum(t["age"] * t["weight"] for t in matched) / total_w, 1),
            "pct_family_households": round(sum(t["pct_fam"] * t["weight"] for t in matched) / total_w, 1),
            "pct_bachelors_or_higher": round(sum(t["pct_ba"] * t["weight"] for t in matched) / total_w, 1),
            "median_home_value": int(sum(t["home_val"] * t["weight"] for t in matched) / total_w),
        }
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2022)
    parser.add_argument("--api-key", required=True)
    args = parser.parse_args()

    data_dir = Path("data")

    # 1. Fetch ACS
    print("=== Fetching ACS data ===")
    all_tracts = {}
    for metro, states in CBSA_COUNTIES.items():
        print(f"\n  {metro}:")
        for state, counties in states.items():
            for county in counties:
                try:
                    rows = fetch_tracts(args.year, state, county, args.api_key)
                    for rec in rows:
                        t = process_tract(rec)
                        if t["pop"] > 0:
                            all_tracts[t["geoid"]] = t
                    print(f"    {state}-{county}: {len(rows)} tracts")
                except Exception as e:
                    print(f"    {state}-{county}: ERROR {e}")

    # 2. Download TIGER
    print("\n=== Downloading TIGER shapefiles ===")
    all_states = set()
    for states in CBSA_COUNTIES.values():
        all_states.update(states.keys())

    with tempfile.TemporaryDirectory() as tmpdir:
        state_gdfs = {}
        for st in all_states:
            shp = download_tiger(args.year, st, tmpdir)
            state_gdfs[st] = gpd.read_file(shp)

        tract_gdf = gpd.pd.concat(list(state_gdfs.values()), ignore_index=True)

        # 3. Load area boundaries
        print("\n=== Aggregating to areas ===")
        for metro in ["charlotte", "raleigh"]:
            geo_path = data_dir / f"areas-{metro}.geojson"
            area_gdf = gpd.read_file(geo_path)
            agg = aggregate_to_areas(all_tracts, tract_gdf, area_gdf)
            print(f"  {metro}: aggregated {len(agg)} areas")

            # 4. Update profiles
            profiles_path = data_dir / "area-profiles.json"
            with open(profiles_path) as f:
                profiles = json.load(f)

            for aid, metrics in agg.items():
                if aid in profiles["areas"]:
                    profiles["areas"][aid].update(metrics)

            profiles["vintage"] = str(args.year)
            with open(profiles_path, "w") as f:
                json.dump(profiles, f, indent=2)

    print("\n✓ ACS refresh complete. Commit data/ and deploy.")


if __name__ == "__main__":
    main()
