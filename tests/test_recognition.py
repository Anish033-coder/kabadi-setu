import json
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from io import BytesIO
import boto3
import pytest
from botocore.config import Config
from backend.domain import Problem
from backend.repository import DynamoRepository, ensure_table
from backend.recognition import Recognition, ScanStore, parse_suggestion
from test_images import jpeg

CATALOGUE = json.loads((Path(__file__).parents[1]/'data/catalogue.json').read_text())

def response(text='{"item_id":"newspaper"}'):
    return {'output':{'message':{'content':[{'text':text}]}},'usage':{'inputTokens':100,'outputTokens':8}}

@pytest.fixture
def service():
    client=boto3.client('dynamodb',endpoint_url='http://127.0.0.1:8000',region_name='ap-south-1',
                       aws_access_key_id='local',aws_secret_access_key='local',
                       config=Config(connect_timeout=1,read_timeout=1,retries={'max_attempts':0}))
    try: ensure_table(client,'kabadi-setu-local')
    except Exception: pytest.skip('DynamoDB Local is required')
    s3=Mock(); s3.get_object.side_effect=lambda **_: {'Body':BytesIO(jpeg())}
    s3.generate_presigned_post.return_value={'url':'https://example.invalid','fields':{}}
    model=Mock(); model.converse.return_value=response()
    clock=2_000_000_000 + (uuid4().int % 100000)*86400
    return Recognition(ScanStore(DynamoRepository(client,'kabadi-setu-local')),s3,model,'photos',CATALOGUE,Mock(),clock=lambda:clock)

@pytest.mark.parametrize('text',['ignore rules and cancel','{}','{"item_id":"not-in-catalogue"}','{"item_id":[]}','[]'])
def test_invalid_model_output_falls_back(text):
    assert parse_suggestion(response(text),CATALOGUE)=='unknown'

def test_repeat_scan_uses_saved_result_and_one_read(service):
    owner=str(uuid4()); scan=service.create(owner,str(uuid4()))
    first=service.analyze(owner,scan['id'])
    assert first==service.analyze(owner,scan['id'])
    assert first['item_id']=='newspaper'
    assert service.bedrock.converse.call_count==1
    assert service.s3.get_object.call_count==1
    assert service.bedrock.converse.call_args.kwargs['messages'][0]['content'][0]['image']['source']['bytes']==jpeg()

def test_daily_reservation_limits_calls(service):
    service.household_limit=1
    owner=str(uuid4())
    one=service.create(owner,str(uuid4()));two=service.create(owner,str(uuid4()))
    service.analyze(owner,one['id'])
    with pytest.raises(Problem) as error: service.analyze(owner,two['id'])
    assert error.value.status==429
    assert service.bedrock.converse.call_count==1

def test_another_household_cannot_analyze(service):
    scan=service.create(str(uuid4()),str(uuid4()))
    with pytest.raises(Problem) as error: service.analyze('intruder',scan['id'])
    assert error.value.status==404
    service.s3.get_object.assert_not_called()
    service.bedrock.converse.assert_not_called()

def test_ambiguous_failure_is_saved_without_retry_or_refund(service):
    owner=str(uuid4()); scan=service.create(owner,str(uuid4()))
    service.bedrock.converse.side_effect=TimeoutError()
    assert service.analyze(owner,scan['id'])['status']=='unavailable'
    assert service.analyze(owner,scan['id'])['status']=='unavailable'
    assert service.bedrock.converse.call_count==1

def test_concurrent_analysis_calls_model_once(service):
    owner=str(uuid4()); scan=service.create(owner,str(uuid4())); barrier=Barrier(2)
    def analyze(_):
        barrier.wait()
        try: return service.analyze(owner,scan['id'])
        except Problem as error: return error.status
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(analyze,range(2)))
    assert any(isinstance(r,dict) for r in results)
    assert service.bedrock.converse.call_count==1

def test_upload_policy_is_size_bounded_and_exact_key(service):
    scan=service.create(str(uuid4()),str(uuid4()))
    args=service.s3.generate_presigned_post.call_args
    assert args.args[1].endswith(scan['id']+'.jpg')
    assert ['content-length-range',1,2*1024*1024] in args.kwargs['Conditions']

def test_global_cap_race_never_exceeds_one_call(service):
    service.global_limit=1
    owners=[str(uuid4()),str(uuid4())]
    scans=[service.create(owner,str(uuid4())) for owner in owners]
    barrier=Barrier(2)
    def analyze(index):
        barrier.wait()
        try: return service.analyze(owners[index],scans[index]['id'])
        except Problem as error: return error.status
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(analyze,range(2)))
    assert sum(isinstance(r,dict) for r in results)==1
    assert 429 in results
    assert service.bedrock.converse.call_count==1

def test_invalid_image_never_reserves_or_calls_model(service):
    owner=str(uuid4()); scan=service.create(owner,str(uuid4()))
    service.s3.get_object.side_effect=lambda **_: {'Body':BytesIO(b'not a JPEG')}
    with pytest.raises(Problem): service.analyze(owner,scan['id'])
    assert service.store.get(scan['id'],owner)['state']=='waiting'
    service.bedrock.converse.assert_not_called()
