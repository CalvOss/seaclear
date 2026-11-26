"""Depth GeoTIFF (EPSG:3857, Float32, nodata set) -> RGBA GeoTIFF of shaded depth colours (Reef ramp 0-30 m).
Processes in row strips so 1 m grids of any size fit in memory.
usage: shade_rgba.py in_3857.tif out_rgba.tif"""
import sys, numpy as np, rasterio
from rasterio.windows import Window
from rasterio.warp import transform as wtrans

SRC, OUT = sys.argv[1], sys.argv[2]
DMIN, DMAX = 0.0, 30.0
STOPS = [(0, '#dcfcf3'), (.07, '#8ee8d8'), (.17, '#3cc6c9'), (.35, '#1793c2'), (.65, '#0f5a9b'), (1, '#0a2b62')]
XS = [s[0] for s in STOPS]
YS = [[int(s[1][1 + 2 * i:3 + 2 * i], 16) for s in STOPS] for i in range(3)]
STRIP = 1024

with rasterio.open(SRC) as src:
    W, H, tr, nd = src.width, src.height, src.transform, src.nodata
    lat_c = wtrans('EPSG:3857', 'EPSG:4326', [tr.c], [tr.f + tr.e * H / 2])[1][0]
    cs = tr.a * np.cos(np.radians(lat_c)) / 3          # ground cell size, z exaggeration 3
    prof = dict(driver='GTiff', width=W, height=H, count=4, dtype='uint8', crs=src.crs, transform=tr,
                compress='deflate', alpha='YES', tiled=True, blockxsize=512, blockysize=512, photometric='RGB', BIGTIFF='IF_SAFER')
    with rasterio.open(OUT, 'w', **prof) as dst:
        for y0 in range(0, H, STRIP):
            h = min(STRIP, H - y0)
            r0, r1 = max(0, y0 - 1), min(H, y0 + h + 1)
            z = src.read(1, window=Window(0, r0, W, r1 - r0)).astype(np.float32)
            valid = (z != nd) & np.isfinite(z) & (np.abs(z) < 1e5)
            if not valid.any():
                dst.write(np.zeros((4, h, W), np.uint8), window=Window(0, y0, W, h)); continue
            # fill nodata with the strip median so edges don't shade as cliffs
            fill = np.where(valid, z, np.median(z[valid]))
            p = np.pad(fill, ((1 if r0 == y0 else 0, 1 if r1 == y0 + h else 0), (1, 1)), mode='edge')
            a, b, c = p[:-2, :-2], p[:-2, 1:-1], p[:-2, 2:]
            d, f = p[1:-1, :-2], p[1:-1, 2:]
            g, hh, q = p[2:, :-2], p[2:, 1:-1], p[2:, 2:]
            dx = ((c + 2 * f + q) - (a + 2 * d + g)) / (8 * cs)
            dn = ((a + 2 * b + c) - (g + 2 * hh + q)) / (8 * cs)
            L = np.sqrt(.5)
            shade = (dx * .5 - dn * .5 + L) / np.sqrt(dx * dx + dn * dn + 1) - L
            off = y0 - r0
            zc, vc, sc = fill[off:off + h], valid[off:off + h], shade[:h]
            t = np.clip((-zc - DMIN) / (DMAX - DMIN), 0, 1)
            rgb = np.stack([np.interp(t, XS, YS[i]) for i in range(3)]).astype(np.float32)
            k = 1.3
            rgb = np.where(sc < 0, rgb * (1 + np.clip(sc * k, -0.85, 0)), rgb + (255 - rgb) * np.clip(sc * k * .6, 0, .5))
            water = vc & (zc < 0)
            out = np.zeros((4, h, W), np.uint8)
            out[:3] = np.where(water, np.clip(rgb, 0, 255), 0).astype(np.uint8)
            out[3] = np.where(water, 255, 0)
            dst.write(out, window=Window(0, y0, W, h))
        dst.colorinterp = [rasterio.enums.ColorInterp.red, rasterio.enums.ColorInterp.green,
                           rasterio.enums.ColorInterp.blue, rasterio.enums.ColorInterp.alpha]
print('wrote', OUT, W, H)
