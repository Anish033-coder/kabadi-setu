# 006 — Freeze a small public-photo benchmark

Date: 2026-10-09. Written before any held-out provider calls.

Source: Gary Thung and Mindy Yang's [TrashNet](https://github.com/garythung/trashnet), downloaded from the [publisher's Hugging Face dataset](https://huggingface.co/datasets/garythung/trashnet). The publisher labels the dataset MIT; preserve `eval/licenses/trashnet-MIT.txt` and attribution. Archive SHA256: `c060e8abfe5d6de0578ca15be1ed8ad0794a865d333c3473d53d1d9ad6e38b8c`.

A seeded sample (20261009) selected six photos from each of six source classes before inference. Six paper/document candidates were excluded during visual review, leaving 30 photos. Catalogue labels were assigned visually, using the dataset's material label as supporting evidence. Unsupported objects (wine glass, food tins, foil, cups, tissue and lids) are labelled unknown. These are assistant annotations, not independently reviewed ground truth. Paths, original source classes, expected catalogue IDs, hashes, licences and splits are recorded in `eval/internet-sources.csv`.

Split: 20 development, 10 held out. Obvious similar bottles/containers were grouped in one split; no identical bytes cross the split. Physical-object identity is not available in the source dataset, so complete object-level independence cannot be guaranteed. Do not tune from held-out outputs. The set has no batteries, electronics, medicines or sanitary waste; it cannot validate those routes.

The resized source photos are 512×384. Compare 256 and 512 maximum dimensions; do not upscale to simulate high-resolution phone photos. Both baseline sizes returned 11/20 correct and 16/20 unresolved. Seven development examples are expected unknown: baseline recognised only 4/13 supported items. Always report supported-item coverage alongside overall correct counts.

Only two mapping changes were supported by development observations:
- Beer Bottle becomes a tentative glass-bottle suggestion, based on two development photos. This is not material verification; household confirmation is mandatory and glass bottles cannot enter the pickup basket.
- Jar plus Plastic, both above the existing confidence threshold, suggests rigid-plastic. Jar alone remains unknown.

Can/Tin/Aluminium, Bottle alone, Ice and Foil remain unmapped. A food tin received Aluminium and plastic boxes received Ice; indiscriminate mapping would introduce false confidence.

Replay of the stored development labels costs no new calls. Mapping 2026-10-09.2 yields 13/20 correct, 14/20 unresolved at 256; 14/20 correct, 13/20 unresolved at 512. Freeze **Rekognition GENERAL_LABELS, confidence 90, mapping 2026-10-09.2, JPEG quality 80, max side 512** for the held-out run. These are development improvements, not independent accuracy estimates. Production keeps its existing 1024 upload maximum until phone-photo evidence supports changing it.

This is a public, controlled-background smoke benchmark. Provider pretraining exposure is unknown. It is not Jaipur-user validation, a full-catalogue benchmark, or proof of environmental impact. Follow it with the user's own phone photos and timed AI-versus-manual tasks.
