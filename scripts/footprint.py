"""Survey footprint polygon from a raster's valid cells -> one GeoJSON line (EPSG:4326). usage: footprint.py in.tif out.geojsonl key=value ..."""
import sys, json, numpy as np, rasterio
from rasterio.enums import Resampling
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
src = rasterio.open(sys.argv[1]); f = max(1, int(max(src.width, src.height) / 2000))
a = src.read(1, out_shape=(src.height // f, src.width // f), resampling=Resampling.nearest, masked=True)
tr = src.transform * src.transform.scale(src.width / a.shape[1], src.height / a.shape[0])
m = (~np.ma.getmaskarray(a)) & (np.abs(a.filled(0)) < 1e5)
polys = [shape(g) for g, v in shapes(m.astype(np.uint8), mask=m, transform=tr) if v == 1]
u = unary_union(polys).buffer(tr.a * 2).buffer(-tr.a * 2).simplify(tr.a)
u = unary_union([p for p in getattr(u, 'geoms', [u]) if p.area > (tr.a * 20) ** 2])
props = dict(kv.split('=', 1) for kv in sys.argv[3:])
with open(sys.argv[2], 'a') as o:
    o.write(json.dumps({'type': 'Feature', 'properties': props, 'geometry': transform_geom(src.crs, 'EPSG:4326', mapping(u), precision=6)}) + '\n')
print('footprint', sys.argv[1], round(u.area / 1e6, 1) if src.crs.is_projected else '', 'km2')
