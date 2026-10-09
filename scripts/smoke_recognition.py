"""Exercise hosted upload/analyze twice; one synthetic image, at most one inference.

Uses the private demo account. Leaves the scan under its one-day TTL and retains
quota usage. No image-recognition accuracy or physical pickup claim is made.
"""
import argparse
import csv
import time
import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from PIL import Image
from aws_identity import require_non_root

ROOT = Path(__file__).resolve().parents[1]


def http(config, expected=None, record=None):
    response = subprocess.run(
        ['curl', '--silent', '--show-error', '--connect-timeout', '5', '--max-time', '40',
         '--config', '-', '--write-out', '\n%{http_code}\n%header{apigw-requestid}'],
        input='\n'.join(config)+'\n', text=True, capture_output=True, check=True)
    body, status, request_id = response.stdout.rsplit('\n', 2)
    if record is not None:
        record.update(correlation_id=request_id.strip(), status=int(status))
    successful = int(status) == expected if expected is not None else 200 <= int(status) < 300
    if not successful:
        raise RuntimeError(f'HTTP {status}; response body withheld')
    return json.loads(body) if body else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-paid-call', action='store_true')
    parser.add_argument('--dev-photo', type=Path, help='An existing manifest development photo only')
    args = parser.parse_args()
    if not args.allow_paid_call:
        parser.error('One synthetic image inference may be billable; explicitly opt in.')
    if args.dev_photo:
        allowed = {str((ROOT/'eval'/r['path']).resolve()) for r in csv.DictReader((ROOT/'eval/internet-sources.csv').open()) if r['split'] == 'dev'}
        if str(args.dev_photo.resolve()) not in allowed:
            parser.error('Use a frozen development photo, never a held-out photo.')
    session = require_non_root()
    cloud = session.client('cloudformation', region_name='ap-south-1')
    outputs = {r['OutputKey']:r['OutputValue'] for r in cloud.describe_stacks(StackName='kabadi-setu')['Stacks'][0]['Outputs']}
    demo = json.loads((ROOT/'.local/demo-household.json').read_text())
    auth = session.client('cognito-idp', region_name='ap-south-1').initiate_auth(
        ClientId=outputs['UserPoolClientId'], AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={'USERNAME':demo['username'], 'PASSWORD':demo['password']})
    token = auth['AuthenticationResult']['AccessToken']

    measurement = {'started_ms':int(time.time()*1000), 'calls':[]}
    measurement_path = ROOT/'.local/recognition-smoke-requests.json'

    def api(path, payload, expected=None):
        record = {'step':path.rsplit('/',1)[-1]}
        measurement['calls'].append(record)
        response = http(['url = '+json.dumps(outputs['ApiUrl']+'/api'+path),
                     'header = '+json.dumps('Authorization: Bearer '+token),
                     'header = "Content-Type: application/json"',
                     'header = '+json.dumps('Idempotency-Key: '+str(uuid.uuid4())),
                     'data = '+json.dumps(json.dumps(payload))], expected=expected, record=record)
        measurement['ended_ms'] = int(time.time()*1000)
        measurement_path.write_text(json.dumps(measurement,indent=2)+'\n')
        return response

    scan = api('/scans', {})
    early = api('/scans/'+scan['id']+'/analyze', {}, expected=409)
    assert 'finished uploading' in early['error']
    with tempfile.TemporaryDirectory(prefix='kabadi-photo-smoke-') as directory:
        image = Path(directory)/'fixture.jpg'
        if args.dev_photo:
            from prepare_phone_photos import clean_photo
            image.write_bytes(clean_photo(args.dev_photo))
        else:
            Image.new('RGB', (128,128), (40,120,70)).save(image, format='JPEG')
        config = ['url = '+json.dumps(scan['upload']['url'])]
        config += ['form-string = '+json.dumps(k+'='+v) for k,v in scan['upload']['fields'].items()]
        config += ['form = '+json.dumps('file=@'+str(image)+';type=image/jpeg')]
        http(config)
    first = api('/scans/'+scan['id']+'/analyze', {})
    assert first['status'] == 'complete', 'Provider call failed; saved result prevents another charge'
    second = api('/scans/'+scan['id']+'/analyze', {})
    assert first == second, 'Repeated analysis should return the saved result'
    route = api('/decide', {'id':'glass-bottle' if args.dev_photo else 'newspaper', 'answers':{'clean':'yes'}})
    assert 'stream' in route
    print(json.dumps({'synthetic_probe':not bool(args.dev_photo), 'scan_id':scan['id'], 'status':first['status'],
                      'item_id':first['item_id'], 'clarification':first.get('clarification'), 'repeat_matches':True, 'early_analyze_status':409}))


if __name__ == '__main__':
    main()
