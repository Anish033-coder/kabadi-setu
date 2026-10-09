"""DynamoDB persistence; memory adapter is only for offline previews and unit tests."""
import copy
import json
import threading
import time
import random
import uuid
from .domain import Conflict, Problem


class MemoryRepository:
    def __init__(self):
        self.rows, self.lock = {}, threading.Lock()

    def get(self, key):
        with self.lock:
            return copy.deepcopy(self.rows.get(key))

    def put(self, key, value):
        with self.lock:
            self.rows[key] = copy.deepcopy(value)

    def create_request(self, doc, receipt_key, receipt):
        with self.lock:
            if receipt_key in self.rows:
                raise Conflict()
            self.rows['REQUEST#' + doc['id']] = copy.deepcopy(doc)
            self.rows[receipt_key] = copy.deepcopy(receipt)

    def transition(self, doc, version, receipt_key, receipt):
        with self.lock:
            if self.rows['REQUEST#' + doc['id']]['version'] != version or receipt_key in self.rows:
                raise Conflict()
            self.rows['REQUEST#' + doc['id']] = copy.deepcopy(doc)
            self.rows[receipt_key] = copy.deepcopy(receipt)


def ensure_table(client, table):
    """Create the local table with the same key schema as template.yaml (DynamoDB Local and tests only)."""
    if table in client.list_tables()['TableNames']:
        return
    client.create_table(TableName=table, BillingMode='PAY_PER_REQUEST',
                        AttributeDefinitions=[{'AttributeName': 'pk', 'AttributeType': 'S'}],
                        KeySchema=[{'AttributeName': 'pk', 'KeyType': 'HASH'}])
    client.get_waiter('table_exists').wait(TableName=table)


class DynamoRepository:
    def __init__(self, client, table, logger=None):
        self.client, self.table, self.logger = client, table, logger

    def capacity(self, operation, response):
        if self.logger is None:
            return
        entries = response.get("ConsumedCapacity", [])
        if isinstance(entries, dict):
            entries = [entries]
        self.logger.info("database_capacity", extra={
            "operation": operation, "capacity_reported": bool(entries),
            "read_units": sum(entry.get("ReadCapacityUnits", entry.get("CapacityUnits", 0) if operation == "get" else 0) for entry in entries),
            "write_units": sum(entry.get("WriteCapacityUnits", entry.get("CapacityUnits", 0) if operation == "put" else 0) for entry in entries),
        })

    def item(self, key, value):
        result = {'pk': {'S': key}, 'document': {'S': json.dumps(value, ensure_ascii=False)}}
        if 'version' in value:
            result['version'] = {'N': str(value['version'])}
        if isinstance(value.get('ttl'), int):
            result['ttl'] = {'N': str(value['ttl'])}
        return result

    def get(self, key):
        response = self.client.get_item(TableName=self.table, Key={'pk': {'S': key}}, ConsistentRead=True, ReturnConsumedCapacity='TOTAL')
        self.capacity('get', response)
        return json.loads(response['Item']['document']['S']) if 'Item' in response else None

    def put(self, key, value):
        response = self.client.put_item(TableName=self.table, Item=self.item(key, value), ReturnConsumedCapacity='TOTAL')
        self.capacity('put', response)

    def write(self, operations):
        # Reuse the exact transaction and token after temporary contention.
        # Never reload a newer version and apply an old user decision to it.
        token = str(uuid.uuid4())
        for attempt in range(4):
            try:
                response = self.client.transact_write_items(TransactItems=operations, ClientRequestToken=token, ReturnConsumedCapacity='TOTAL')
                self.capacity('transaction', response)
                return
            except self.client.exceptions.TransactionCanceledException as error:
                reasons = {reason.get('Code') for reason in error.response.get('CancellationReasons', [])}
                reasons -= {None, 'None'}
                if reasons and reasons <= {'ConditionalCheckFailed', 'TransactionConflict'}:
                    if 'ConditionalCheckFailed' in reasons:
                        raise Conflict() from error
                    if attempt < 3:
                        time.sleep(random.uniform(0.025, 0.05) * (2 ** attempt))
                        continue
                    raise Problem(503, 'The request is busy. Retry the same action in a moment.') from error
                # Validation, permissions and capacity failures are not stale user decisions.
                raise

    def create_request(self, doc, receipt_key, receipt):
        self.write([{'Put': {'TableName': self.table, 'Item': self.item('REQUEST#' + doc['id'], doc), 'ConditionExpression': 'attribute_not_exists(pk)'}},
                    {'Put': {'TableName': self.table, 'Item': self.item(receipt_key, receipt), 'ConditionExpression': 'attribute_not_exists(pk)'}}])

    def transition(self, doc, version, receipt_key, receipt):
        # Status and embedded history are one item; the durable action receipt commits with it.
        self.write([{'Put': {'TableName': self.table, 'Item': self.item('REQUEST#' + doc['id'], doc),
                            'ConditionExpression': '#v = :expected', 'ExpressionAttributeNames': {'#v': 'version'},
                            'ExpressionAttributeValues': {':expected': {'N': str(version)}}}},
                    {'Put': {'TableName': self.table, 'Item': self.item(receipt_key, receipt), 'ConditionExpression': 'attribute_not_exists(pk)'}}])
