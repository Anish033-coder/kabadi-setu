"""DynamoDB persistence; memory adapter is only for offline previews and unit tests."""
import copy
import json
import threading
from .domain import Conflict


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


class DynamoRepository:
    def __init__(self, client, table):
        self.client, self.table = client, table

    def item(self, key, value):
        result = {'pk': {'S': key}, 'document': {'S': json.dumps(value, ensure_ascii=False)}}
        if 'version' in value:
            result['version'] = {'N': str(value['version'])}
        return result

    def get(self, key):
        response = self.client.get_item(TableName=self.table, Key={'pk': {'S': key}}, ConsistentRead=True)
        return json.loads(response['Item']['document']['S']) if 'Item' in response else None

    def put(self, key, value):
        self.client.put_item(TableName=self.table, Item=self.item(key, value))

    def write(self, operations):
        try:
            self.client.transact_write_items(TransactItems=operations)
        except self.client.exceptions.TransactionCanceledException as error:
            # Do not blindly replay a stale user decision. The caller reloads current state.
            raise Conflict() from error

    def create_request(self, doc, receipt_key, receipt):
        self.write([{'Put': {'TableName': self.table, 'Item': self.item('REQUEST#' + doc['id'], doc), 'ConditionExpression': 'attribute_not_exists(pk)'}},
                    {'Put': {'TableName': self.table, 'Item': self.item(receipt_key, receipt), 'ConditionExpression': 'attribute_not_exists(pk)'}}])

    def transition(self, doc, version, receipt_key, receipt):
        # Status and embedded history are one item; the durable action receipt commits with it.
        self.write([{'Put': {'TableName': self.table, 'Item': self.item('REQUEST#' + doc['id'], doc),
                            'ConditionExpression': '#v = :expected', 'ExpressionAttributeNames': {'#v': 'version'},
                            'ExpressionAttributeValues': {':expected': {'N': str(version)}}}},
                    {'Put': {'TableName': self.table, 'Item': self.item(receipt_key, receipt), 'ConditionExpression': 'attribute_not_exists(pk)'}}])
