"""Exercise hosted upload/analyze twice; one synthetic image, at most one inference.

Uses the private demo account. Leaves the scan under its one-day TTL and retains
quota usage. No image-recognition accuracy or physical pickup claim is made.
"""
import argparse
import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from PIL import Image
from aws_identity import require_non_root

ROOT = Path(__file__).resolve().parents[1]


def http(config, expected=None):
    response = subprocess.run(
        ['curl', '--silent', '--show-error', '--connect-timeout', '5', '--max-time', '40',
         '--config', '-', '--write-out', '\n%{http_code}'],
        input='\n'.join(config)+'\n', text=True, capture_output=True, check=True)
    body, status = response.stdout.rsplit('\n', 1)
    successful = int(status) == expected if expected is not None else 200 <= int(status) < 300
    if not successful:
        raise RuntimeError(f'HTTP {status}; response body withheld')
    return json.loads(body) if body else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-paid-call', action='store_true')
    args = parser.parse_args()
    if not args.allow_paid_call:
        parser.error('One synthetic image inference may be billable; explicitly opt in.')
    session = require_non_root()
    cloud = session.client('cloudformation', region_name='ap-south-1')
    outputs = {r['OutputKey']:r['OutputValue'] for r in cloud.describe_stacks(StackName='kabadi-setu')['Stacks'][0]['Outputs']}
    demo = json.loads((ROOT/'.local/demo-household.json').read_text())
    auth = session.client('cognito-idp', region_name='ap-south-1').initiate_auth(
        ClientId=outputs['UserPoolClientId'], AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={'USERNAME':demo['username'], 'PASSWORD':demo['password']})
    token = auth['AuthenticationResult']['AccessToken']

    def api(path, payload, expected=None):
        return http(['url = '+json.dumps(outputs['ApiUrl']+'/api'+path),
                     'header = '+json.dumps('Authorization: Bearer '+token),
                     'header = "Content-Type: application/json"',
                     'header = '+json.dumps('Idempotency-Key: '+str(uuid.uuid4())),
                     'data = '+json.dumps(json.dumps(payload))], expected=expected)

    scan = api('/scans', {})
    early = api('/scans/'+scan['id']+'/analyze', {}, expected=409)
    assert 'finished uploading' in early['error']
    with tempfile.TemporaryDirectory(prefix='kabadi-photo-smoke-') as directory:
        image = Path(directory)/'fixture.jpg'
        Image.new('RGB', (128,128), (40,120,70)).save(image, format='JPEG')
        config = ['url = '+json.dumps(scan['upload']['url'])]
        config += ['form-string = '+json.dumps(k+'='+v) for k,v in scan['upload']['fields'].items()]
        config += ['form = '+json.dumps('file=@'+str(image)+';type=image/jpeg')]
        http(config)
    first = api('/scans/'+scan['id']+'/analyze', {})
    assert first['status'] == 'complete', 'Provider call failed; saved result prevents another charge'
    second = api('/scans/'+scan['id']+'/analyze', {})
    assert first == second, 'Repeated analysis should return the saved result'
    print(json.dumps({'synthetic_probe':True, 'scan_id':scan['id'], 'status':first['status'],
                      'item_id':first['item_id'], 'repeat_matches':True, 'early_analyze_status':409}))


if __name__ == '__main__':
    main()
