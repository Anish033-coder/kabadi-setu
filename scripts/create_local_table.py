"""Create the DynamoDB Local table used by tests and the local adapter."""
import sys
from pathlib import Path
import boto3

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.repository import ensure_table

TABLE = 'kabadi-setu-local'

if __name__ == '__main__':
    client = boto3.client('dynamodb', endpoint_url='http://127.0.0.1:8000', region_name='ap-south-1',
                          aws_access_key_id='local', aws_secret_access_key='local')
    ensure_table(client, TABLE)
    print(f'{TABLE} is ready on DynamoDB Local.')
