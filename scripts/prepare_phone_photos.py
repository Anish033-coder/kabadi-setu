"""Prepare private phone photos, then freeze a labelled, item-grouped split."""
import argparse
import csv
import hashlib
import random
import re
import warnings
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['path', 'label', 'group_id', 'split', 'sha256', 'source_file']


def clean_photo(path, max_side=1024):
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError('source exceeds 20 MB')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as source:
            if source.width * source.height > 40_000_000:
                raise ValueError('source exceeds 40 million pixels')
            image = ImageOps.exif_transpose(source).convert('RGB')
            image.thumbnail((max_side, max_side))
            # A fresh image carries pixels only: no EXIF, GPS or other source info.
            pixels = Image.new('RGB', image.size)
            pixels.paste(image)
            output = BytesIO()
            pixels.save(output, format='JPEG', quality=80)
    raw = output.getvalue()
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('prepared image exceeds 2 MB')
    return raw


def import_photos(source, name):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,50}', name):
        raise ValueError('Use a short lowercase name with optional hyphens.')
    source = source.resolve()
    if not source.is_dir():
        raise ValueError('Input must be a local folder.')
    destination = ROOT / 'eval/photos' / name
    if destination.resolve().is_relative_to(source):
        raise ValueError('Choose an input folder outside the destination.')
    files = sorted(p for p in source.rglob('*') if p.is_file() and not p.name.startswith('.'))
    destination.mkdir(parents=True, exist_ok=False)
    rows, rejected, seen = [], [], set()
    for path in files:
        if path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}:
            continue
        try:
            raw = clean_photo(path)
        except (ValueError, OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
            rejected.append({'source_file':str(path.relative_to(source)), 'reason':str(error)})
            continue
        digest = hashlib.sha256(raw).hexdigest()
        if digest in seen:
            rejected.append({'source_file':str(path.relative_to(source)), 'reason':'duplicate prepared pixels'})
            continue
        seen.add(digest)
        output = destination / (digest + '.jpg')
        output.write_bytes(raw)
        parent = path.relative_to(source).parent
        rows.append({'path':str(output.relative_to(ROOT/'eval')), 'label':'',
                     'group_id':str(parent) if parent != Path('.') else '',
                     'split':'', 'sha256':digest, 'source_file':str(path.relative_to(source))})
    for name, data, fields in [('labels.csv', rows, FIELDS), ('rejected.csv', rejected, ['source_file','reason'])]:
        with (destination/name).open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader(); writer.writerows(data)
    return destination, len(rows), len(rejected)


def freeze_split(labels_path, seed=20261010):
    import json
    labels_path = labels_path.resolve()
    if not labels_path.is_relative_to(ROOT/'eval/photos'):
        raise ValueError('Keep phone labels under ignored eval/photos/.')
    rows = list(csv.DictReader(labels_path.open()))
    if not rows:
        raise ValueError('No photos to split.')
    allowed = {i['id'] for i in json.loads((ROOT/'data/catalogue.json').read_text())['items']} | {'unknown'}
    seen = set()
    for row in rows:
        if row['label'] not in allowed or not row['group_id'].strip():
            raise ValueError('Fill label and physical-item group_id for every photo first.')
        path = (ROOT/'eval'/row['path']).resolve()
        if not path.is_relative_to(ROOT/'eval/photos'):
            raise ValueError('Photo path is outside the private photo directory.')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row['sha256'] or digest in seen:
            raise ValueError('Changed or duplicate photo; prepare a new cohort.')
        seen.add(digest)
    groups = sorted({r['group_id'] for r in rows})
    if len(groups) < 2:
        raise ValueError('At least two different physical items are needed for separate splits.')
    random.Random(seed).shuffle(groups)
    heldout = set(groups[:max(1, round(len(groups)*0.3))])
    for row in rows:
        row['split'] = 'heldout' if row['group_id'] in heldout else 'dev'
    manifest = labels_path.with_name('manifest.csv')
    # Never silently replace a split after someone may have seen its results.
    with manifest.open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(rows)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    importer = commands.add_parser('import')
    importer.add_argument('folder', type=Path)
    importer.add_argument('--name', required=True)
    splitter = commands.add_parser('split')
    splitter.add_argument('labels', type=Path)
    splitter.add_argument('--seed', type=int, default=20261010)
    args = parser.parse_args()
    try:
        if args.command == 'import':
            folder, accepted, rejected = import_photos(args.folder, args.name)
            print(f'{accepted} prepared; {rejected} rejected/duplicate. Fill {folder}/labels.csv before splitting.')
            print('HEIC support depends on Pillow. Export rejected HEIC photos as JPEG; originals are unchanged.')
        else:
            print('Frozen manifest:', freeze_split(args.labels, args.seed))
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
