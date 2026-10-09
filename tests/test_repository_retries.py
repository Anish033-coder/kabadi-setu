from unittest.mock import Mock
import boto3
import pytest
from backend.domain import Conflict, Problem
from backend.repository import DynamoRepository

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr('backend.repository.time.sleep', lambda _: None)
    client = boto3.client('dynamodb', region_name='ap-south-1', aws_access_key_id='local', aws_secret_access_key='local')
    client.transact_write_items = Mock()
    return client

def cancelled(client, code):
    return client.exceptions.TransactionCanceledException(
        {'Error': {'Code': 'TransactionCanceledException'}, 'CancellationReasons': [{'Code': code}]}, 'TransactWriteItems')

def test_temporary_contention_retries_same_transaction(client):
    client.transact_write_items.side_effect = [cancelled(client, 'TransactionConflict'), {}]
    DynamoRepository(client, 'test').write([{'test': 'unchanged'}])
    first, second = client.transact_write_items.call_args_list
    assert first == second
    assert first.kwargs['ClientRequestToken']

def test_condition_failure_is_not_retried(client):
    client.transact_write_items.side_effect = cancelled(client, 'ConditionalCheckFailed')
    with pytest.raises(Conflict):
        DynamoRepository(client, 'test').write([])
    assert client.transact_write_items.call_count == 1

def test_repeated_contention_is_bounded_and_retryable(client):
    client.transact_write_items.side_effect = cancelled(client, 'TransactionConflict')
    with pytest.raises(Problem) as error:
        DynamoRepository(client, 'test').write([])
    assert error.value.status == 503
    assert client.transact_write_items.call_count == 4

@pytest.mark.parametrize('code', ['ValidationError', 'ProvisionedThroughputExceeded', None])
def test_other_failures_are_not_misreported_as_stale_actions(client, code):
    client.transact_write_items.side_effect = cancelled(client, code)
    with pytest.raises(client.exceptions.TransactionCanceledException):
        DynamoRepository(client, 'test').write([])
    assert client.transact_write_items.call_count == 1


def test_capacity_log_uses_returned_units_without_keys_or_table_names(client):
    logger = Mock()
    client.transact_write_items.return_value = {'ConsumedCapacity':[
        {'TableName':'private-table', 'ReadCapacityUnits':0, 'WriteCapacityUnits':6}]}
    DynamoRepository(client, 'private-table', logger).write([])
    assert client.transact_write_items.call_args.kwargs['ReturnConsumedCapacity'] == 'TOTAL'
    assert logger.info.call_args.kwargs['extra'] == {
        'operation':'transaction', 'capacity_reported':True, 'read_units':0, 'write_units':6}
