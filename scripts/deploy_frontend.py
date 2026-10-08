"""Upload the static frontend to the configured Amplify app without a Git push."""
import json
import subprocess
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
from aws_identity import require_non_root

ROOT=Path(__file__).resolve().parents[1]

def main():
    session=require_non_root()
    hosting=json.loads((ROOT/'.local/hosting.json').read_text())
    outputs={r['OutputKey']:r['OutputValue'] for r in session.client('cloudformation',region_name='ap-south-1').describe_stacks(StackName='kabadi-setu')['Stacks'][0]['Outputs']}
    (ROOT/'frontend/.env.local').write_text(f"VITE_API_URL={outputs['ApiUrl']}\nVITE_AWS_REGION=ap-south-1\nVITE_COGNITO_CLIENT_ID={outputs['UserPoolClientId']}\n")
    subprocess.run(['npm','run','build'],cwd=ROOT/'frontend',check=True)
    archive=ROOT/'.local/frontend.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as bundle:
        for path in (ROOT/'frontend/dist').rglob('*'):
            if path.is_file(): bundle.write(path,path.relative_to(ROOT/'frontend/dist'))
    amplify=session.client('amplify',region_name='ap-south-1')
    deployment=amplify.create_deployment(appId=hosting['app_id'],branchName=hosting['branch'])
    # The signed upload URL is kept in memory and never printed.
    request=Request(deployment['zipUploadUrl'],data=archive.read_bytes(),method='PUT',headers={'Content-Type':'application/zip'})
    with urlopen(request,timeout=60) as response:
        assert response.status==200
    amplify.start_deployment(appId=hosting['app_id'],branchName=hosting['branch'],jobId=deployment['jobId'])
    (ROOT/'.local/hosting-job.json').write_text(json.dumps({'job_id':deployment['jobId']})+'\n')
    print('Frontend deployment started:',hosting['origin'])

if __name__=='__main__': main()
