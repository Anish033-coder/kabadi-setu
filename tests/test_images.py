from io import BytesIO
import pytest
from PIL import Image
from backend.images import validate_photo, read_photo, MAX_BYTES
from backend.domain import Problem

def jpeg():
    output = BytesIO()
    Image.new('RGB', (40, 30), 'green').save(output, format='JPEG')
    return output.getvalue()

def test_validated_buffer_is_preserved():
    raw = jpeg()
    result = validate_photo(raw)
    assert result['bytes'] is raw
    assert (result['width'], result['height']) == (40, 30)

def test_invalid_or_oversized_bytes_rejected():
    for raw in (b'not a photo', b'x' * (MAX_BYTES + 1), b''):
        with pytest.raises(Problem): validate_photo(raw)

def test_single_s3_read_even_if_key_changes():
    class S3:
        calls = 0
        def get_object(self, **kwargs):
            self.calls += 1
            return {'Body': BytesIO(jpeg() if self.calls == 1 else b'replacement')}
    s3 = S3()
    assert read_photo(s3, 'bucket', 'key')['width'] == 40
    assert s3.calls == 1

def test_metadata_rejected():
    output = BytesIO()
    exif = Image.Exif(); exif[270] = 'private description'
    Image.new('RGB', (10, 10)).save(output, format='JPEG', exif=exif)
    with pytest.raises(Problem, match='metadata'): validate_photo(output.getvalue())
