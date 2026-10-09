"""Upload the static frontend to the configured Amplify app without a Git push."""
import json
import os
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
    # Keep the hosting policy versioned and reapply it on manual deployments.
    amplify.update_app(appId=hosting['app_id'], customHeaders=(ROOT/'frontend/customHttp.yml').read_text())
    pending=ROOT/'.local/pending-hosting-upload.json'
    if pending.exists():
        deployment=json.loads(pending.read_text())
    else:
        deployment=amplify.create_deployment(appId=hosting['app_id'],branchName=hosting['branch'])
        fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as file: json.dump(deployment,file)
    # The signed upload URL is kept in memory and never printed.
    # Same-object PUT retries are safe; keep signed URLs out of process arguments.
    subprocess.run(['curl','--fail','--silent','--show-error','--connect-timeout','10','--max-time','60',
                    '--retry','2','--retry-all-errors','--upload-file',str(archive),'--config','-'],
                   input='url = "'+deployment['zipUploadUrl']+'"\n',text=True,check=True)
    amplify.start_deployment(appId=hosting['app_id'],branchName=hosting['branch'],jobId=deployment['jobId'])
    (ROOT/'.local/hosting-job.json').write_text(json.dumps({'job_id':deployment['jobId']})+'\n')
    pending.unlink()
    print('Frontend deployment started:',hosting['origin'])

if __name__=='__main__': main()
