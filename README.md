# SeaClear

Seabed depth maps for fishing and diving, built on Mapbox GL JS.

- `index.html` - the site (static, no build step). Served by GitHub Pages.
- `data/` - PG2016 (WA) depth grid, terrain tiles and contours that the page colours in the browser.
- Hosted layers (NT depth, contours and survey outlines) come from Mapbox tilesets in the `calvoss` account.
- `scripts/` - processing: BAG/GeoTIFF -> shaded depth tilesets, contours, survey outlines. `src.html` + `build.py` rebuild the page.

## Map

- Top left: menu and current area. Left rail: Select area (country, state, area, with survey details), Map layers, Base map, and the survey quality filter. Bottom left: map configuration (depth colours, shading, contours, display mode, 3D exaggeration) and the coordinates readout.
- Top right: account (sign-in and billing are placeholders until identity management and payments are set up). Right tool bar: move, zoom, north, 3D, measure, depth profile, coordinates, mini map.
- Survey bathymetry only shows once an area is chosen. Areas are presets in `REGIONS` and surveys in `SURVEYS` in `scripts/src.html`; add entries there to extend them.
- Marine parks: set `MARINE_PARKS` in `scripts/src.html` once a boundary tileset exists.

Survey quality stars come from grid resolution: 5 m or better 5 stars, 5 to 10 m 4, 10 to 30 m 3, 30 to 50 m 2, coarser than 50 m 1.

## Processing rules

- Hillshade is applied to bathymetry only (below sea level). Nothing above sea level is hillshaded.

Depths are relative to each survey's vertical datum and are not for navigation.
