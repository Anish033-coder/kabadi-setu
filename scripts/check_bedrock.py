"""Day-one gate: can this account call an image model? Sends one tiny generated JPEG and prints usage.

Run with a non-root profile. Exact model or inference-profile IDs differ by Region; list them with
`aws bedrock list-inference-profiles --region <region>` and `aws bedrock list-foundation-models --region <region>`.
"""
import argparse
import time
from io import BytesIO
import boto3
from PIL import Image
from aws_identity import require_non_root

parser = argparse.ArgumentParser()
parser.add_argument('--model', default='apac.amazon.nova-lite-v1:0')
parser.add_argument('--region', default='ap-south-1')
parser.add_argument('--allow-paid-call', action='store_true', help='Explicitly enable this one billable test call')
args = parser.parse_args()
if not args.allow_paid_call:
    parser.error('Model calls can cost money. Add --allow-paid-call only after reviewing billing controls.')
session = require_non_root()

image = BytesIO()
Image.new('RGB', (64, 64), (40, 120, 70)).save(image, format='JPEG')
client = session.client('bedrock-runtime', region_name=args.region)
started = time.perf_counter()
try:
    response = client.converse(modelId=args.model, inferenceConfig={'maxTokens': 20},
                               messages=[{'role': 'user', 'content': [
                                   {'image': {'format': 'jpeg', 'source': {'bytes': image.getvalue()}}},
                                   {'text': 'Reply with one word: the main colour of this image.'}]}])
except Exception as error:
    print(f'FAILED {args.model} in {args.region}: {type(error).__name__}: {error}')
    raise SystemExit(1)
usage = response['usage']
print(f"OK {args.model} in {args.region} | {round((time.perf_counter() - started) * 1000)} ms | "
      f"input {usage['inputTokens']} / output {usage['outputTokens']} tokens | "
      f"reply: {response['output']['message']['content'][0]['text'].strip()}")
