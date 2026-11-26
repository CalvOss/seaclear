import os, json, sys, boto3, requests
T = os.environ['MAPBOX_SECRET_TOKEN']; U = 'calvoss'
c = requests.post(f'https://api.mapbox.com/uploads/v1/{U}/credentials', params={'access_token': T}).json()
s3 = boto3.client('s3', aws_access_key_id=c['accessKeyId'], aws_secret_access_key=c['secretAccessKey'], aws_session_token=c['sessionToken'], region_name='us-east-1')
s3.upload_file(sys.argv[1], c['bucket'], c['key'])
r = requests.post(f'https://api.mapbox.com/uploads/v1/{U}', params={'access_token': T},
    json={'url': c['url'], 'tileset': f'{U}.{sys.argv[2]}', 'name': sys.argv[3]})
print(r.status_code, {k: v for k, v in r.json().items() if k in ('id', 'complete', 'error', 'progress', 'tileset', 'message')})
