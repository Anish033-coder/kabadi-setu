import json
import os
import time
from pathlib import Path
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from .domain import Service, Problem
from .repository import DynamoRepository, MemoryRepository

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = json.loads((ROOT / 'data/catalogue.json').read_text())
logger = Logger(service='kabadi-setu')
app = APIGatewayHttpResolver()
_service = None

def link_secret():
    # Local runs set LINK_SECRET directly. On AWS the secret lives in SSM Parameter Store, not in the template.
    if os.getenv('LINK_SECRET'):
        return os.environ['LINK_SECRET']
    import boto3
    ssm = boto3.client('ssm', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
    return ssm.get_parameter(Name=os.environ['LINK_SECRET_PARAM'], WithDecryption=True)['Parameter']['Value']

def service():
    global _service
    if _service is None:
        secret = link_secret()
        if os.getenv('LOCAL_MEMORY') == '1':
            repo = MemoryRepository()
        else:
            import boto3
            options = {'region_name': os.getenv('AWS_REGION', 'ap-south-1')}
            if os.getenv('DYNAMODB_ENDPOINT'):
                options.update(endpoint_url=os.environ['DYNAMODB_ENDPOINT'], aws_access_key_id='local', aws_secret_access_key='local')
            repo = DynamoRepository(boto3.client('dynamodb', **options), os.environ['TABLE_NAME'])
        _service = Service(repo, CATALOGUE, secret)
    return _service

def owner():
    claims = app.current_event.raw_event.get('requestContext', {}).get('authorizer', {}).get('jwt', {}).get('claims', {})
    if claims.get('token_use') != 'access' or not isinstance(claims.get('sub'), str) or not claims['sub']:
        raise Problem(401, 'Sign in with a valid access token.')
    return claims['sub']

def body():
    try:
        value = app.current_event.json_body
    except (ValueError, TypeError):
        raise Problem(400, 'Invalid JSON.')
    if not isinstance(value, dict):
        raise Problem(400, 'Expected a JSON object.')
    return value

def key():
    return app.current_event.get_header_value('idempotency-key', '')

@app.exception_handler(Problem)
def problem(error):
    return Response(status_code=error.status, content_type='application/json', body=json.dumps({'error': str(error)}))

@app.get('/api/health')
def health():
    return {'mode': 'local' if os.getenv('LOCAL_DEV') == '1' else 'aws', 'recognition': 'enabled' if os.getenv('RECOGNITION_ENABLED') == 'true' else 'unavailable',
            'recognition_provider': os.getenv('RECOGNITION_PROVIDER', 'rekognition')}

@app.get('/api/catalogue')
def catalogue():
    return CATALOGUE

@app.post('/api/decide')
def decide():
    owner()
    data = body()
    return service().route(data.get('id'), data.get('answers', {}))

@app.get('/api/basket')
def get_basket():
    return service().repo.get('BASKET#' + owner()) or {'items': []}

@app.post('/api/basket')
def save_basket():
    return service().save_basket(owner(), body().get('items'))

@app.post('/api/requests')
def create_request():
    return service().create(owner(), body(), key())

@app.get('/api/requests/<request_id>')
def request_details(request_id):
    return service().get(request_id, owner=owner())

@app.post('/api/requests/<request_id>/actions')
def household_action(request_id):
    return service().act(request_id, body(), key(), owner=owner())

@app.post('/api/pickup/view')
def pickup_view():
    data = body()
    return service().get(str(data.get('id', '')), token=data.get('token'))

@app.post('/api/pickup/action')
def pickup_action():
    data = body()
    return service().act(str(data.get('id', '')), data, key(), token=data.get('token'))

def recognition():
    if os.getenv('RECOGNITION_ENABLED') != 'true':
        raise Problem(503, 'Photo recognition is unavailable. Please select the item manually.')
    import boto3
    from .recognition import Recognition, ScanStore
    from .recognizers import make_recognizer
    return Recognition(ScanStore(service().repo), boto3.client('s3'),
                       make_recognizer(os.getenv('RECOGNITION_PROVIDER', 'rekognition'), boto3),
                       os.environ['PHOTO_BUCKET'], CATALOGUE, logger,
                       int(os.getenv('HOUSEHOLD_SCAN_LIMIT','5')), int(os.getenv('GLOBAL_SCAN_LIMIT','50')))

@app.post('/api/scans')
def create_scan():
    household = owner()
    return recognition().create(household, key())

@app.post('/api/scans/<scan_id>/analyze')
def analyze_scan(scan_id):
    household = owner()
    return recognition().analyze(household, scan_id)

def handler(event, context):
    started = time.perf_counter()
    # One ID per request ties together its timing, errors and (later) model usage.
    logger.set_correlation_id(event.get('requestContext', {}).get('requestId'))
    try:
        response = app.resolve(event, context)
    except Exception as error:
        # Only the exception class is logged: no request body, credentials, token, phone number or full URL.
        logger.error('unhandled_request_error', extra={'error_type': type(error).__name__})
        response = {'statusCode': 500, 'body': json.dumps({'error': 'Something went wrong. Please try again.'})}
    response.setdefault('headers', {}).update({'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer', 'Content-Type': 'application/json'})
    logger.info('request_completed', extra={'route': event.get('routeKey', 'unknown'), 'status': response['statusCode'],
                'duration_ms': round((time.perf_counter() - started) * 1000, 2)})
    return response
