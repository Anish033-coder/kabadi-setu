"""Exercise the deployed manual flow using two temporary users; suppress all email.

Deletes the temporary users and known test records afterwards. Never prints tokens
or passwords. This invokes normal AWS services but never calls a model.
"""
import json
import secrets
import subprocess
import uuid
from aws_identity import require_non_root


def main():
    session = require_non_root()
    cloud = session.client('cloudformation', region_name='ap-south-1')
    stack = cloud.describe_stacks(StackName='kabadi-setu')['Stacks'][0]
    outputs = {item['OutputKey']: item['OutputValue'] for item in stack['Outputs']}
    resources = cloud.list_stack_resources(StackName='kabadi-setu')['StackResourceSummaries']
    table = next(item['PhysicalResourceId'] for item in resources if item['LogicalResourceId'] == 'Table')
    cognito = session.client('cognito-idp', region_name='ap-south-1')
    database = session.client('dynamodb', region_name='ap-south-1')
    users, keys = [], []

    def call(path, body=None, token=None, key=None, expected=200):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if key:
            headers['Idempotency-Key'] = key
        # Pass credentials through stdin, never command arguments or output.
        config = ['url = '+json.dumps(outputs['ApiUrl']+'/api'+path)]
        config += ['header = '+json.dumps(name+': '+value) for name,value in headers.items()]
        if body is not None:
            config += ['request = "POST"', 'data = '+json.dumps(json.dumps(body))]
        response = subprocess.run(['curl','--silent','--show-error','--connect-timeout','5','--max-time','20',
                                   '--retry','2','--retry-all-errors','--config','-','--write-out','\n%{http_code}'],
                                  input='\n'.join(config)+'\n',text=True,capture_output=True)
        if response.returncode:
            raise ConnectionError('HTTP transport failed before a response could be verified.')
        raw, status_text = response.stdout.rsplit('\n',1)
        status = int(status_text)
        if status != expected:
            # Don't print the body: a future endpoint could return sensitive fields.
            raise AssertionError(f'{path.split("/")[1]} returned {status}; expected {expected}')
        return json.loads(raw) if raw else {}

    def household():
        username = f'smoke-{uuid.uuid4()}@example.invalid'
        password = secrets.token_urlsafe(32) + 'aA1!'
        created = cognito.admin_create_user(UserPoolId=outputs['UserPoolId'], Username=username,
                                            MessageAction='SUPPRESS', UserAttributes=[{'Name':'email','Value':username}])
        users.append(created['User']['Username'])
        owner = next(a['Value'] for a in created['User']['Attributes'] if a['Name'] == 'sub')
        cognito.admin_set_user_password(UserPoolId=outputs['UserPoolId'], Username=username,
                                        Password=password, Permanent=True)
        auth = cognito.initiate_auth(ClientId=outputs['UserPoolClientId'], AuthFlow='USER_PASSWORD_AUTH',
                                     AuthParameters={'USERNAME':username, 'PASSWORD':password})
        return owner, auth['AuthenticationResult']['AccessToken']

    try:
        assert call('/health')['recognition'] in ('unavailable','enabled')
        call('/basket', expected=401)
        owner, token = household()
        _, other_token = household()
        rows = [{'id':'newspaper', 'quantity':2, 'answers':{'clean':'yes'}}]
        assert call('/decide', {'id':'newspaper','answers':{'clean':'yes'}}, token)['eligible']
        keys.append('BASKET#' + owner)
        call('/basket', {'items':rows}, token)
        create_key = str(uuid.uuid4())
        keys.append(f'CREATE#{owner}#{create_key}')
        created = call('/requests', {'items':rows}, token, create_key)
        request_id, link_token = created['id'], created['token']
        keys.append('REQUEST#' + request_id)
        repeated = call('/requests', {'items':rows}, token, create_key)
        assert repeated['id'] == request_id
        call('/requests/' + request_id, token=other_token, expected=404)
        call('/pickup/view', {'id':request_id,'token':link_token})
        for action, version, expected in [('accept',1,'accepted'), ('collect',2,'collection_reported')]:
            action_id = str(uuid.uuid4())
            keys.append(f'ACTION#{request_id}#pickup_link#{action_id}')
            result = call('/pickup/action', {'id':request_id,'token':link_token,'action':action,'version':version}, key=action_id)
            assert result['status'] == expected
        print('PASS: live sign-in, auth denial, ownership, manual sorting, basket, duplicate create, accept and collection report.')
    finally:
        failures = []
        for key in keys:
            try:
                database.delete_item(TableName=table, Key={'pk':{'S':key}})
            except Exception as error:
                failures.append(type(error).__name__)
        for username in users:
            try:
                cognito.admin_delete_user(UserPoolId=outputs['UserPoolId'], Username=username)
            except Exception as error:
                failures.append(type(error).__name__)
        if failures:
            raise RuntimeError('Temporary-data cleanup needs attention: ' + ', '.join(failures))
        print('Temporary users and known test records removed; no email sent.')


if __name__ == '__main__':
    main()
