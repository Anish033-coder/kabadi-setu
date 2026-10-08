"""Validate one bounded S3 read; the returned bytes are the exact inference input."""
import hashlib
from io import BytesIO
import warnings
from PIL import Image, UnidentifiedImageError
from .domain import Problem

MAX_BYTES = 2 * 1024 * 1024
MAX_PIXELS = 8_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

def validate_photo(raw):
    if not raw or len(raw) > MAX_BYTES:
        raise Problem(400, 'Use a JPEG smaller than 2 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format != 'JPEG' or image.width * image.height > MAX_PIXELS:
                    raise Problem(400, 'Use a JPEG with at most 8 million pixels.')
                image.load()
                if image.getexif():
                    raise Problem(400, 'Please export this photo without metadata before uploading.')
                dimensions = (image.width, image.height)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise Problem(400, 'This image cannot be safely decoded.') from error
    return {'bytes': raw, 'sha256': hashlib.sha256(raw).hexdigest(), 'width': dimensions[0], 'height': dimensions[1]}

def read_photo(s3, bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    stream = response['Body']
    try:
        raw = stream.read(MAX_BYTES + 1)
    finally:
        stream.close()
    return validate_photo(raw)
