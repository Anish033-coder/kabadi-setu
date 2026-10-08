import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4
import pytest
from backend.domain import Service, Problem, REPLY_WINDOW, PICKUP_WINDOW
from backend.repository import MemoryRepository, DynamoRepository, ensure_table

CATALOGUE = json.loads((Path(__file__).parents[1] / 'data/catalogue.json').read_text())
ITEM = {'id': 'newspaper', 'quantity': 2, 'answers': {'clean': 'yes'}}

@pytest.fixture(params=['memory', 'dynamodb'])
def service(request):
    if request.param == 'memory':
        repo = MemoryRepository()
    else:
        import boto3
        client = boto3.client('dynamodb', endpoint_url='http://127.0.0.1:8000', region_name='ap-south-1', aws_access_key_id='local', aws_secret_access_key='local')
        try:
            client.list_tables()
        except Exception:
            pytest.skip('DynamoDB Local must be running on port 8000')
        ensure_table(client, 'kabadi-setu-local')
        repo = DynamoRepository(client, 'kabadi-setu-local')
    return Service(repo, CATALOGUE, 'test-secret', clock=lambda: 1000)

def create(service):
    return service.create('alice', {'items': [ITEM]}, str(uuid4()))

def test_other_household_cannot_read_or_change(service):
    doc = create(service)
    with pytest.raises(Problem, match='not found'):
        service.get(doc['id'], owner='mallory')
    with pytest.raises(Problem):
        service.act(doc['id'], {'action': 'cancel', 'version': 1}, str(uuid4()), owner='mallory')

def test_unsupported_and_unconfirmed_items_cannot_be_smuggled_into_basket(service):
    for row in [{'id': 'battery', 'quantity': 1, 'answers': {'clean': 'yes'}}, {**ITEM, 'answers': {'clean': 'no'}}, {**ITEM, 'quantity': True}]:
        with pytest.raises(Problem):
            service.create('alice', {'items': [row]}, str(uuid4()))

def test_link_reads_do_not_mutate(service):
    doc = create(service)
    for _ in range(3):
        result = service.get(doc['id'], token=doc['token'])
        assert result['status'] == 'awaiting_response'
        assert len(result['events']) == 1
        assert 'owner' not in result and 'token_hash' not in result

def test_accept_then_collect_and_duplicate_accept(service):
    doc = create(service)
    key = str(uuid4())
    accepted = service.act(doc['id'], {'action': 'accept', 'version': 1}, key, token=doc['token'])
    assert accepted == service.act(doc['id'], {'action': 'accept', 'version': 1}, key, token=doc['token'])
    collected = service.act(doc['id'], {'action': 'collect', 'version': 2}, str(uuid4()), token=doc['token'])
    assert collected['status'] == 'collection_reported'
    assert len(collected['events']) == 3
    assert collected['events'][-1]['source'] == 'pickup_link'

def test_collection_before_acceptance_is_rejected(service):
    doc = create(service)
    with pytest.raises(Problem):
        service.act(doc['id'], {'action': 'collect', 'version': 1}, str(uuid4()), token=doc['token'])

def test_expired_link_fails_even_while_record_exists(service):
    doc = create(service)
    service.clock = lambda: doc['expires_at']
    with pytest.raises(Problem, match='expired'):
        service.get(doc['id'], token=doc['token'])
    assert service.get(doc['id'], owner='alice')['status'] == 'expired'

def test_cancellation_revokes_link(service):
    doc = create(service)
    service.act(doc['id'], {'action': 'cancel', 'version': 1}, str(uuid4()), owner='alice')
    with pytest.raises(Problem, match='cancelled'):
        service.get(doc['id'], token=doc['token'])

def test_duplicate_creation_reuses_snapshot_and_rejects_changed_payload(service):
    key = str(uuid4())
    first = service.create('alice', {'items': [ITEM]}, key)
    assert first == service.create('alice', {'items': [ITEM]}, key)
    with pytest.raises(Problem, match='different items'):
        service.create('alice', {'items': [{**ITEM, 'quantity': 3}]}, key)

def test_accept_cancel_race_has_one_winner(service):
    doc = create(service)
    barrier = Barrier(2)
    def compete(action):
        barrier.wait()
        try:
            return service.act(doc['id'], {'action': action, 'version': 1}, str(uuid4()),
                               **({'owner': 'alice'} if action == 'cancel' else {'token': doc['token']}))
        except Problem:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, ['accept', 'cancel']))
    assert sum(result is not None for result in results) == 1
    final = service.get(doc['id'], owner='alice')
    assert final['version'] == 2 and len(final['events']) == 2

def test_pickup_token_does_not_authorize_household_cancel(service):
    doc = create(service)
    with pytest.raises(Problem):
        service.act(doc['id'], {'action': 'cancel', 'version': 1}, str(uuid4()), token=doc['token'])

def test_accepted_request_can_be_collected_after_the_reply_window(service):
    doc = create(service)
    accepted = service.act(doc['id'], {'action': 'accept', 'version': 1}, str(uuid4()), token=doc['token'])
    assert accepted['pickup_until'] == 1000 + PICKUP_WINDOW
    service.clock = lambda: 1000 + REPLY_WINDOW + 3600
    collected = service.act(doc['id'], {'action': 'collect', 'version': 2}, str(uuid4()), token=doc['token'])
    assert collected['status'] == 'collection_reported'

def test_accepted_request_expires_after_the_pickup_window(service):
    doc = create(service)
    service.act(doc['id'], {'action': 'accept', 'version': 1}, str(uuid4()), token=doc['token'])
    service.clock = lambda: 1000 + PICKUP_WINDOW
    assert service.get(doc['id'], owner='alice')['status'] == 'expired'
    with pytest.raises(Problem, match='expired'):
        service.get(doc['id'], token=doc['token'])

def test_simultaneous_duplicate_action_returns_one_result(service):
    doc = create(service)
    key, barrier = str(uuid4()), Barrier(2)
    def tap(_):
        barrier.wait()
        return service.act(doc['id'], {'action': 'accept', 'version': 1}, key, token=doc['token'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.map(tap, range(2))
    assert first == second
    assert len(service.get(doc['id'], owner='alice')['events']) == 2

def test_simultaneous_duplicate_create_returns_one_request(service):
    key, barrier = str(uuid4()), Barrier(2)
    def tap(_):
        barrier.wait()
        return service.create('alice', {'items': [ITEM]}, key)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.map(tap, range(2))
    assert first['id'] == second['id'] and first['token'] == second['token']
