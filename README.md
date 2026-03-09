# NC Metro Dashboard

Static neighborhood explorer for the **Charlotte** and **Raleigh** metro areas. Click any area to view ACS demographics, housing market notes, and top-rated restaurants from Google.

**Live demo:** Deploy to GitHub Pages or Cloudflare Pages — no build step, no backend.

## File Structure

```
index.html                    ← Single-file dashboard (Leaflet + vanilla JS)
data/
  area-profiles.json          ← Blurbs, ACS metrics, market notes per area
  areas-charlotte.geojson     ← Boundary polygons for Charlotte areas
  areas-raleigh.geojson       ← Boundary polygons for Raleigh areas
  restaurants.json             ← Google Places restaurant data per area
scripts/
  refresh_acs.py              ← Annual ACS data refresh (Census API)
  refresh_restaurants.py      ← Restaurant data refresh (Google Places API)
```

## Areas Covered

**Charlotte neighborhoods:** Uptown, South End, NoDa, Plaza Midwood, Dilworth, Myers Park, Elizabeth, Montford, Wesley Heights, Eastway/Shamrock, University Area, Ballantyne

**Charlotte outer ring:** Lake Norman (Davidson/Cornelius/Huntersville), Mooresville/Statesville, Concord/Kannapolis, Matthews/Mint Hill, Indian Trail/Stallings, Gastonia/Belmont

**Raleigh neighborhoods:** Downtown, North Hills, Five Points/Hayes Barton, Oakwood/Mordecai, Cameron Village, Glenwood South, Boylan Heights, Warehouse District

**Raleigh outer ring:** Cary/Morrisville, Apex, Holly Springs/Fuquay-Varina, Wake Forest, Garner, Knightdale/Wendell, Clayton

## Restaurant Filtering

- **Map markers:** 4+ stars AND 50+ Google reviews
- **Sidebar blurb stat:** Count of restaurants with 4+ stars AND 100+ reviews
- **Sidebar list:** All restaurants meeting the map marker threshold

## Deployment

### GitHub Pages
1. Push this repo to GitHub
2. Settings → Pages → Deploy from branch: `main`, folder: `/`
3. Live in ~60 seconds

### Cloudflare Pages
```bash
npx wrangler pages deploy . --project-name nc-metro-dashboard
```

### Local
```bash
python3 -m http.server 8000
```

## Annual Data Refresh

### ACS Metrics (free Census API key)
```bash
pip install requests geopandas shapely
python scripts/refresh_acs.py --year 2023 --api-key YOUR_CENSUS_KEY
```

### Restaurants (Google Places API key, ~$5-10 per refresh)
```bash
pip install requests
python scripts/refresh_restaurants.py --api-key YOUR_GOOGLE_KEY
```

Refresh a single area:
```bash
python scripts/refresh_restaurants.py --api-key KEY --areas clt-south-end ral-downtown
```

## Adding New Areas

1. Add a polygon to `data/areas-charlotte.geojson` or `data/areas-raleigh.geojson`
2. Add a profile entry to `data/area-profiles.json` (blurb, metrics, market notes)
3. Add a center coordinate to `AREA_CENTERS` in `scripts/refresh_restaurants.py`
4. Run the restaurant refresh for that area
5. Commit and deploy

## Editing Boundaries

The current boundaries are simplified approximations. For production use:
- **Charlotte neighborhoods:** Download from `data.charlottenc.gov`
- **Raleigh neighborhoods:** Download from `data-ral.opendata.arcgis.com`
- **Town boundaries:** Download from NC OneMap (`nconemap.gov`)

Replace the GeoJSON features with official polygons, keeping the `id` and `name` properties intact.

## Data Sources

- **ACS 5-Year Estimates** — U.S. Census Bureau (free)
- **TIGER/Line Shapefiles** — U.S. Census Bureau (free)
- **Restaurant data** — Google Places API (paid, ~$17/1000 requests)
- **Base map** — CartoDB Dark Matter tiles (free, no API key)
- **Blurbs & market notes** — Editorially curated
