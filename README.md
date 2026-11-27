# SeaClear

Seabed depth maps for fishing and diving, built on Mapbox GL JS.

- `index.html` - the site (static, no build step). Served by GitHub Pages.
- `data/` - PG2016 (WA) depth grid, terrain tiles and contours that the page colours in the browser.
- Hosted layers (NT depth, contours and survey outlines) come from Mapbox tilesets in the `calvoss` account.
- `scripts/` - processing: BAG/GeoTIFF -> shaded depth tilesets, contours, survey outlines. `src.html` + `build.py` rebuild the page.

## Map

- Left menu: survey settings (opacity, hillshade strength, contour interval, 3D), depth profile results, data and admin, and Settings (light / dark / auto mode, mini map, depth colour ramp).
- Right panel: base map (Bathymetry, Nautical chart, Satellite, Outdoors), survey layer toggles, survey quality filter and reference layers (ocean depth from `mapbox.mapbox-bathymetry-v2`, labels, roads, boundaries, marine parks).
- Right tool bar: move, zoom, measure, depth profile, reset north, mini map, layers.
- Marine parks: set `MARINE_PARKS` in `scripts/src.html` once a boundary tileset exists.

Survey quality stars come from grid resolution: 5 m or better 5 stars, 5 to 10 m 4, 10 to 30 m 3, 30 to 50 m 2, coarser than 50 m 1.

## Processing rules

- Hillshade is applied to bathymetry only (below sea level). Nothing above sea level is hillshaded.

Depths are relative to each survey's vertical datum and are not for navigation.
