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
from backend.recognizers import make_recognizer, MAPPING_VERSION
from backend.images import validate_photo
from scripts.aws_identity import require_non_root


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--provider', choices=['rekognition','bedrock'], default='rekognition')
    parser.add_argument('--split',choices=['dev','heldout'],default='heldout')
    parser.add_argument('--sizes',type=int,nargs='+',choices=[256,512,768,1024],default=[512])
    parser.add_argument('--manifest', type=Path, default=ROOT/'eval/internet-sources.csv')
    parser.add_argument('--access-confirmed', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--allow-paid-calls',action='store_true')
    # A small own-photo check of frozen settings: reported as a spot check, never as a benchmark.
    parser.add_argument('--spot-check',action='store_true')
    args=parser.parse_args()
    if not args.dry_run and not args.allow_paid_calls: parser.error('Explicit --allow-paid-calls is required.')
    if args.provider == 'bedrock' and not args.dry_run and not args.access_confirmed:
        parser.error('Bedrock remains blocked. Confirm account access before using --access-confirmed.')
    if len(args.sizes) != len(set(args.sizes)): parser.error('Duplicate sizes would waste calls.')
    if args.split=='heldout' and len(args.sizes)!=1: parser.error('Freeze one size before the held-out run.')
    catalogue=json.loads((ROOT/'data/catalogue.json').read_text())
    allowed={i['id'] for i in catalogue['items']} | {'unknown'}
    rows=list(csv.DictReader(args.manifest.open()))
    if args.spot_check:
        if not 5<=len(rows)<30: parser.error('A spot check uses 5–29 photos; use the normal run for 30–50.')
        if args.split!='heldout': parser.error('A spot check only evaluates frozen settings; nothing is tuned on it.')
    elif not 30<=len(rows)<=50: parser.error('Supply 30–50 labelled real photos.')
    seen=set()
    for row in rows:
        path=(ROOT/'eval'/row['path']).resolve()
        if not path.is_relative_to(ROOT/'eval/photos'): parser.error('Keep photos under eval/photos/.')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen: parser.error('Duplicate image bytes found; split physical items consistently.')
        if row.get('sha256') and digest != row['sha256']: parser.error('Photo hash changed after the manifest was frozen.')
        seen.add(digest)
        if row['label'] not in allowed or row['split'] not in ('dev','heldout'): parser.error('Invalid label or split.')
    selected=[r for r in rows if r['split']==args.split]
    if not selected: parser.error('No photos in this split.')
    if args.dry_run:
        print(f'{args.provider}: {len(selected)} {args.split} photos, sizes {args.sizes}, {len(selected)*len(args.sizes)} planned calls. No AWS requests made.')
        return
    session=require_non_root()
    recognizer=make_recognizer(args.provider, session)
    results=[]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output=ROOT/'eval/results'/f'{stamp}-{"spotcheck" if args.spot_check else args.split}.json'
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
                result.update(predicted=suggestion.item_id,usage=suggestion.usage,status='complete',
                              clarification=suggestion.clarification,options=list(suggestion.options))
                if args.split == 'dev' and args.provider == 'rekognition':
                    result['labels'] = suggestion.labels
            except Exception as error: result.update(status='failed',error_type=type(error).__name__)
            result['latency_ms']=round((time.perf_counter()-started)*1000)
            results.append(result)
            output.write_text(json.dumps({'manifest_sha256':hashlib.sha256(args.manifest.read_bytes()).hexdigest(),'provider':args.provider,'model':recognizer.model_id,'region':'ap-south-1','split':args.split,
                                          'mapping_version':MAPPING_VERSION,'spot_check':args.spot_check,'results':results},indent=2)+'\n')
            if result['status']=='failed':
                print('Stopped after a failed call; partial result saved. Investigate before spending more.')
                return
    for size in args.sizes:
        subset=[r for r in results if r['size']==size]
        correct=sum(r['status']=='complete' and r['predicted']==r['expected'] for r in subset)
        asked=sum(bool(r.get('options')) for r in subset)
        # "Offered" = named outright, or in the short list the person chooses from. Unknowns excluded.
        known=[r for r in subset if r['expected']!='unknown']
        offered=sum(r['predicted']==r['expected'] or r['expected'] in r.get('options',()) for r in known)
        label='SPOT CHECK, not a benchmark — ' if args.spot_check else ''
        print(f'{label}{size}px: {correct}/{len(subset)} correct; {sum(r["predicted"]=="unknown" for r in subset)}/{len(subset)} unresolved; '
              f'{asked}/{len(subset)} showed a short list; right item offered for {offered}/{len(known)} known items (mapping {MAPPING_VERSION})')

if __name__=='__main__': main()
