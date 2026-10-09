"""One explicitly opted-in synthetic call; verifies access, never accuracy."""
import argparse
import json
import sys
import time
from io import BytesIO
from pathlib import Path
from PIL import Image
from botocore.exceptions import ClientError
from aws_identity import require_non_root

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.recognizers import make_recognizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-paid-call', action='store_true')
    args = parser.parse_args()
    if not args.allow_paid_call:
        parser.error('This sends one billable image request; add --allow-paid-call explicitly.')
    session = require_non_root()
    catalogue = json.loads((ROOT / 'data/catalogue.json').read_text())
    image = BytesIO()
    Image.new('RGB', (128, 128), (40, 120, 70)).save(image, format='JPEG')
    started = time.perf_counter()
    try:
        result = make_recognizer('rekognition', session).recognize(image.getvalue(), catalogue)
    except ClientError as error:
        print('FAILED:', error.response['Error']['Code'])
        return 1
    print(json.dumps({'provider':'rekognition', 'region':'ap-south-1',
                      'synthetic_probe':True, 'item_id':result.item_id,
                      'duration_ms':round((time.perf_counter()-started)*1000), **result.usage}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
