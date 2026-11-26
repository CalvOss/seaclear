"""Create or update a per-state vector tileset <state>-bathy-vectors with layers contours + coverage.
usage: mts_state.py <state> <contours.geojsonl> <coverage.geojsonl> [append]
Sources are <state>-contours / <state>-coverage; 'append' adds files to existing sources instead of replacing."""
import os, sys, requests
T = os.environ['MAPBOX_SECRET_TOKEN']; U = 'calvoss'; A = {'access_token': T}; B = 'https://api.mapbox.com/tilesets/v1'
st, cf, vf = sys.argv[1], sys.argv[2], sys.argv[3]; append = len(sys.argv) > 4
for sid, path in [(f'{st}-contours', cf), (f'{st}-coverage', vf)]:
    m = requests.post if append else requests.put
    r = m(f'{B}/sources/{U}/{sid}', params=A, files={'file': open(path, 'rb')}); print(sid, r.status_code, r.text[:120])
tid = f'{U}.{st}-bathy-vectors'
recipe = {'version': 1, 'layers': {
  'contours': {'source': f'mapbox://tileset-source/{U}/{st}-contours', 'minzoom': 11, 'maxzoom': 16,
               'features': {'simplification': ['case', ['>=', ['zoom'], 15], 1, 4]}},
  'coverage': {'source': f'mapbox://tileset-source/{U}/{st}-coverage', 'minzoom': 3, 'maxzoom': 12}}}
r = requests.get(f'{B}/{tid}', params=A)
if r.status_code == 404:
    r = requests.post(f'{B}/{tid}', params=A, json={'recipe': recipe, 'name': f'{st.upper()} bathymetry contours and coverage', 'private': True}); print('create', r.status_code, r.text[:160])
else:
    r = requests.patch(f'{B}/{tid}/recipe', params=A, json=recipe); print('recipe', r.status_code, r.text[:160])
r = requests.post(f'{B}/{tid}/publish', params=A); print('publish', r.status_code, r.text[:160])
