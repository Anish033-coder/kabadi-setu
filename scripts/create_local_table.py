"""Create the DynamoDB Local table used by tests and the local adapter."""
import sys
import time
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import EndpointConnectionError, ConnectionClosedError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.repository import ensure_table

TABLE = 'kabadi-setu-local'

if __name__ == '__main__':
    client = boto3.client('dynamodb', endpoint_url='http://127.0.0.1:8000', region_name='ap-south-1',
                          aws_access_key_id='local', aws_secret_access_key='local',
                          config=Config(connect_timeout=1, read_timeout=1, retries={'max_attempts': 0}))
    # Docker can report a started container before Java is listening on the port.
    for attempt in range(20):
        try:
            ensure_table(client, TABLE)
            break
        except (EndpointConnectionError, ConnectionClosedError):
            if attempt == 19:
                raise
            time.sleep(0.5)
    print(f'{TABLE} is ready on DynamoDB Local.')
