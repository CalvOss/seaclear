"""BAG -> web assets: depth.png (mercator, terrain-RGB encoded), DEM tiles, contours.geojson, meta.json"""
import sys, os, json, math
import numpy as np, h5py
from pyproj import Transformer
from scipy import ndimage
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import LineString

SRC = sys.argv[1]
OUT = sys.argv[2]
PX = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0  # ground metres per output pixel
os.makedirs(OUT, exist_ok=True)

f = h5py.File(SRC, "r")
e = f["BAG_root/elevation"][:].astype(np.float32)
NODATA = 1e6
valid = e < NODATA
# grid geometry from metadata (pixel centres, row 0 = south)
X0, Y0, X1, Y1 = 243371.530575, 6838672.272129, 262093.005965, 6864114.241319
nr, nc = e.shape
dx = (X1 - X0) / (nc - 1); dy = (Y1 - Y0) / (nr - 1)

# nearest fill for interpolation
idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
filled = e[tuple(idx)]

utm2ll = Transformer.from_crs(28350, 4326, always_xy=True)
ll2utm = Transformer.from_crs(4326, 28350, always_xy=True)
R = 6378137.0
def merc(lon, lat):
    return np.radians(lon) * R, np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)) * R
def unmerc(mx, my):
    return np.degrees(mx / R), np.degrees(2 * np.arctan(np.exp(my / R)) - np.pi / 2)

def sample(lon, lat):
    ux, uy = ll2utm.transform(lon, lat)
    c = (ux - X0) / dx; r = (uy - Y0) / dy
    inside = (c >= 0) & (c <= nc - 1) & (r >= 0) & (r <= nr - 1)
    h = ndimage.map_coordinates(filled, [r, c], order=1, mode="nearest")
    m = ndimage.map_coordinates(valid.astype(np.uint8), [r, c], order=0, mode="constant", cval=0) > 0
    return h, m & inside

# bounding box of valid data
vr, vc = np.where(valid[::4, ::4])
cx = X0 + vc * 4 * dx; cy = Y0 + vr * 4 * dy
lon, lat = utm2ll.transform(cx, cy)
W_, S_, E_, N_ = lon.min(), lat.min(), lon.max(), lat.max()
latc = (S_ + N_) / 2
mpx = PX / math.cos(math.radians(latc))
mx0, my0 = merc(W_, S_); mx1, my1 = merc(E_, N_)
w = int(math.ceil((mx1 - mx0) / mpx)); h = int(math.ceil((my1 - my0) / mpx))
mx1 = mx0 + w * mpx; my1 = my0 + h * mpx
gx = mx0 + (np.arange(w) + 0.5) * mpx
gy = my1 - (np.arange(h) + 0.5) * mpx
MX, MY = np.meshgrid(gx, gy)
glon, glat = unmerc(MX, MY)
H, M = sample(glon.ravel(), glat.ravel())
H = H.reshape(h, w); M = M.reshape(h, w)
print("depth grid", w, h, "valid", M.mean())

def enc(hgt):
    v = np.clip(np.round((hgt + 10000) * 10), 0, 16777215).astype(np.uint32)
    return np.dstack([(v >> 16) & 255, (v >> 8) & 255, v & 255]).astype(np.uint8)

rgb = enc(H); rgb[~M] = 0
Image.fromarray(rgb, "RGB").save(f"{OUT}/depth.png", optimize=True)
lw, ls = unmerc(mx0, my0); le, ln = unmerc(mx1, my1)
meta = dict(bounds=[float(lw), float(ls), float(le), float(ln)], width=w, height=h, px_m=PX,
            min=float(e[valid].min()), max=float(e[valid].max()),
            source="PG2016_Mean_Lidar.bag", crs="GDA94 / MGA zone 50 (EPSG:28350)",
            vdatum="Instantaneous water level (EPSG:5829)", native_res_m=round(dx, 2),
            grid=[nc, nr])

# ---- contours (bathymetry, 1 m) ----
Hs = ndimage.gaussian_filter(np.where(M, H, np.nan if False else H), 1.2)
Hm = np.where(ndimage.binary_erosion(M, iterations=1), Hs, np.nan)
levels = np.arange(-30, 1, 1)
cs = plt.contour(np.arange(w), np.arange(h), Hm, levels=levels)
feats = []
for lev, segs in zip(cs.levels, cs.allsegs):
    d = int(round(-lev))
    for seg in segs:
        if len(seg) < 6: continue
        ls_ = LineString(seg).simplify(0.6)
        pts = np.asarray(ls_.coords)
        if len(pts) < 3: continue
        px_, py_ = pts[:, 0], pts[:, 1]
        cl, ca = unmerc(mx0 + (px_ + 0.5) * mpx, my1 - (py_ + 0.5) * mpx)
        coords = [[round(float(a), 6), round(float(b), 6)] for a, b in zip(cl, ca)]
        feats.append({"type": "Feature", "properties": {"d": d}, "geometry": {"type": "LineString", "coordinates": coords}})
json.dump({"type": "FeatureCollection", "features": feats}, open(f"{OUT}/contours.geojson", "w"), separators=(",", ":"))
print("contours", len(feats))

# ---- DEM tiles for hillshade / 3D (terrain-RGB, z10..ZMAX) ----
ZMIN, ZMAX = 10, int(sys.argv[4]) if len(sys.argv) > 4 else 14
def lon2t(lo, z): return (lo + 180) / 360 * 2 ** z
def lat2t(la, z): return (1 - math.log(math.tan(math.radians(la)) + 1 / math.cos(math.radians(la))) / math.pi) / 2 * 2 ** z
ntile = 0
for z in range(ZMIN, ZMAX + 1):
    tx0, tx1 = int(lon2t(W_, z)), int(lon2t(E_, z)); ty0, ty1 = int(lat2t(N_, z)), int(lat2t(S_, z))
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            n = 2 ** z; T = 256
            fx = (tx + (np.arange(T) + 0.5) / T) / n
            fy = (ty + (np.arange(T) + 0.5) / T) / n
            FX, FY = np.meshgrid(fx, fy)
            lo = FX * 360 - 180
            la = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * FY))))
            hh, mm = sample(lo.ravel(), la.ravel())
            if not mm.any(): continue
            hh = hh.reshape(T, T)
            os.makedirs(f"{OUT}/dem/{z}/{tx}", exist_ok=True)
            Image.fromarray(enc(hh), "RGB").save(f"{OUT}/dem/{z}/{tx}/{ty}.png", optimize=True)
            ntile += 1
print("tiles", ntile)
meta["dem_zoom"] = [ZMIN, ZMAX]
json.dump(meta, open(f"{OUT}/meta.json", "w"), indent=1)
print(meta)
