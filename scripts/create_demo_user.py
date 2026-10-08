"""Create an email-suppressed demo login; save its password only in ignored local files."""
import json
import os
import secrets
from pathlib import Path
from aws_identity import require_non_root

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'.local/demo-household.json'
if path.exists():
    raise SystemExit('Demo credentials already exist. Keep the existing login; no password rotated.')
session=require_non_root()
outputs={r['OutputKey']:r['OutputValue'] for r in session.client('cloudformation',region_name='ap-south-1').describe_stacks(StackName='kabadi-setu')['Stacks'][0]['Outputs']}
c=session.client('cognito-idp',region_name='ap-south-1')
username='demo-household@example.invalid'
password=secrets.token_urlsafe(24)+'Aa1!'
c.admin_create_user(UserPoolId=outputs['UserPoolId'],Username=username,MessageAction='SUPPRESS',UserAttributes=[{'Name':'email','Value':username}])
c.admin_set_user_password(UserPoolId=outputs['UserPoolId'],Username=username,Password=password,Permanent=True)
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as file: json.dump({'username':username,'password':password},file,indent=2)
print('Demo login created without email; credentials saved to .local/demo-household.json.')
