"""Small, explicitly paid evaluation runner; never manufactures evaluation data."""
import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps
from botocore.config import Config

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.recognizers import make_recognizer
from backend.images import validate_photo
from scripts.aws_identity import require_non_root


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--provider', choices=['rekognition','bedrock'], default='rekognition')
    parser.add_argument('--split',choices=['dev','heldout'],required=True)
    parser.add_argument('--sizes',type=int,nargs='+',choices=[256,512,768,1024],required=True)
    parser.add_argument('--allow-paid-calls',action='store_true')
    args=parser.parse_args()
    if not args.allow_paid_calls: parser.error('Explicit --allow-paid-calls is required.')
    if args.split=='heldout' and len(args.sizes)!=1: parser.error('Freeze one size before the held-out run.')
    catalogue=json.loads((ROOT/'data/catalogue.json').read_text())
    allowed={i['id'] for i in catalogue['items']} | {'unknown'}
    rows=list(csv.DictReader((ROOT/'eval/manifest.csv').open()))
    if not 30<=len(rows)<=50: parser.error('Supply 30–50 labelled real photos.')
    seen=set()
    for row in rows:
        path=(ROOT/'eval'/row['path']).resolve()
        if not path.is_relative_to(ROOT/'eval/photos'): parser.error('Keep photos under eval/photos/.')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen: parser.error('Duplicate image bytes found; split physical items consistently.')
        seen.add(digest)
        if row['label'] not in allowed or row['split'] not in ('dev','heldout'): parser.error('Invalid label or split.')
    selected=[r for r in rows if r['split']==args.split]
    if not selected: parser.error('No photos in this split.')
    session=require_non_root()
    recognizer=make_recognizer(args.provider, session)
    results=[]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output=ROOT/'eval/results'/f'{stamp}-{args.split}.json'
    output.parent.mkdir(exist_ok=True)
    for row in selected:
        for size in args.sizes:
            with Image.open(ROOT/'eval'/row['path']) as original:
                picture=ImageOps.exif_transpose(original).convert('RGB')
                picture.thumbnail((size,size))
                buffer=BytesIO(); picture.save(buffer,format='JPEG',quality=80)
            raw=validate_photo(buffer.getvalue())['bytes']
            started=time.perf_counter()
            result={'photo':row['path'],'expected':row['label'],'size':size,'predicted':'unknown','usage':None}
            try:
                suggestion=recognizer.recognize(raw,catalogue)
                result.update(predicted=suggestion.item_id,usage=suggestion.usage,status='complete')
                if args.split == 'dev' and args.provider == 'rekognition':
                    result['labels'] = suggestion.labels
            except Exception as error: result.update(status='failed',error_type=type(error).__name__)
            result['latency_ms']=round((time.perf_counter()-started)*1000)
            results.append(result)
            output.write_text(json.dumps({'provider':args.provider,'model':recognizer.model_id,'region':'ap-south-1','split':args.split,'results':results},indent=2)+'\n')
            if result['status']=='failed':
                print('Stopped after a failed call; partial result saved. Investigate before spending more.')
                return
    for size in args.sizes:
        subset=[r for r in results if r['size']==size]
        correct=sum(r['status']=='complete' and r['predicted']==r['expected'] for r in subset)
        print(f'{size}px: {correct}/{len(subset)} correct; {sum(r["predicted"]=="unknown" for r in subset)}/{len(subset)} unresolved')

if __name__=='__main__': main()
