# SeaClear

Seabed depth maps for fishing and diving, built on Mapbox GL JS.

- `index.html` - the site (static, no build step). Served by GitHub Pages.
- `data/` - PG2016 (WA) depth grid, terrain tiles and contours that the page colours in the browser.
- Hosted layers (NT depth, contours and survey outlines) come from Mapbox tilesets in the `calvoss` account.
- `scripts/` - processing: BAG/GeoTIFF -> shaded depth tilesets, contours, survey outlines. `src.html` + `build.py` rebuild the page.

Depths are relative to each survey's vertical datum and are not for navigation.
