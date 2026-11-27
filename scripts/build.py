"""Rebuild ../index.html from src.html: inlines the Mapbox GL CSS and the hosted raster tileset list.
usage (from scripts/): python3 build.py"""
import os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CSS_URL = 'https://unpkg.com/mapbox-gl@3.9.0/dist/mapbox-gl.css'
CSS_CACHE = os.path.join(HERE, 'vendor', 'mapbox-gl-3.9.0.css')
HOSTED = ("[{id:'nt-darwin-harbour-bathy', maxzoom:18, bounds:[130.6941,-12.661,131.0135,-12.2929]}, "
          "{id:'nt-howard-channel-bathy', maxzoom:13, bounds:[130.8462,-12.1874,131.2577,-11.9805]}]")

if not os.path.exists(CSS_CACHE):
    os.makedirs(os.path.dirname(CSS_CACHE), exist_ok=True)
    urllib.request.urlretrieve(CSS_URL, CSS_CACHE)
css = open(CSS_CACHE).read().strip()
s = open(os.path.join(HERE, 'src.html')).read()
s = s.replace('/*HOSTED*/[]', HOSTED).replace('/*MAPBOX_CSS*/', css)
head = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<meta name="description" content="SeaClear: seabed depth maps for fishing and diving.">\n'
        '<style>[hidden]{display:none!important}html,body{height:100%;margin:0}</style>\n</head><body>\n')
open(os.path.join(HERE, '..', 'index.html'), 'w').write(head + s + '\n</body></html>\n')
print('wrote index.html')
