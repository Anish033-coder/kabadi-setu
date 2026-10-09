import csv
import json
from io import BytesIO

import pytest
from PIL import Image
from scripts import prepare_phone_photos as prep


def test_prepared_photo_removes_metadata_and_preserves_orientation(tmp_path):
    photo = tmp_path / "original.jpg"
    exif = Image.Exif()
    exif[274] = 6
    exif[270] = "private location description"
    Image.new("RGB", (1200, 600), "red").save(photo, exif=exif)
    original = photo.read_bytes()
    with Image.open(BytesIO(prep.clean_photo(photo))) as cleaned:
        assert cleaned.size == (512, 1024)
        assert not cleaned.getexif()
        assert b"private location" not in prep.clean_photo(photo)
    assert photo.read_bytes() == original


def test_import_deduplicates_and_split_keeps_physical_items_together(tmp_path, monkeypatch):
    root = tmp_path / "project"
    (root / "data").mkdir(parents=True)
    (root / "data/catalogue.json").write_text(json.dumps({"items":[{"id":"pet-bottle"}]}))
    monkeypatch.setattr(prep, "ROOT", root)
    source = tmp_path / "incoming"
    for group, colors in {"bottle-a":["red", "pink"], "bottle-b":["blue"], "other":["green"]}.items():
        folder = source / group
        folder.mkdir(parents=True)
        for index, color in enumerate(colors):
            Image.new("RGB", (40, 30), color).save(folder / f"{index}.jpg")
    (source / "duplicate.jpg").write_bytes((source / "bottle-a/0.jpg").read_bytes())
    folder, accepted, rejected = prep.import_photos(source, "test-set")
    assert (accepted, rejected) == (4, 1)
    labels = folder / "labels.csv"
    rows = list(csv.DictReader(labels.open()))
    with pytest.raises(ValueError, match="Fill label"):
        prep.freeze_split(labels)
    for row in rows:
        row["label"] = "unknown" if row["group_id"] == "other" else "pet-bottle"
    with labels.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=prep.FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    manifest = prep.freeze_split(labels)
    frozen = list(csv.DictReader(manifest.open()))
    assert {r["split"] for r in frozen} == {"dev", "heldout"}
    assert len({r["split"] for r in frozen if r["group_id"] == "bottle-a"}) == 1
    with pytest.raises(FileExistsError):
        prep.freeze_split(labels)
    (root / "eval" / rows[0]["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="Changed"):
        prep.freeze_split(labels)
