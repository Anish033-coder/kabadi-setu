# Public-photo evaluation set

30 real photos from **TrashNet — Gary Thung and Mindy Yang** are saved locally in `eval/photos/trashnet/`. No generated image is included. The photos are ignored by Git; `internet-sources.csv` retains their archive paths, labels, splits, hashes and licence attribution. See `licenses/trashnet-MIT.txt`.

Original publisher: https://github.com/garythung/trashnet
Dataset card and MIT licence declaration: https://huggingface.co/datasets/garythung/trashnet
Archive: https://huggingface.co/datasets/garythung/trashnet/resolve/main/dataset-resized.zip

To reproduce, download that archive, verify its SHA256 against decision 006, and extract only the `source_path` entries in `internet-sources.csv` to their corresponding `path` under `eval/`. Check each image hash. Create `manifest.csv` with the `path,label,split` columns from the source CSV. Do not execute dataset scripts or copy its model code. Six additional review candidates may remain locally but are excluded from the manifest.

The set contains 20 development and 10 held-out images. Selection and catalogue labels were frozen before inference. Source images are 512×384, so the development size comparison is 256/512. These photos cannot measure performance on high-resolution phone uploads or all 18 catalogue categories. Some catalogue labels are assistant judgements and need human review. This benchmark includes unsupported-item negatives; overall accuracy alone overstates useful item recognition.

## Results on the 10 held-out photos

| Mapping | Named outright | Right item offered (named or in the short list) | Unsupported items given a list |
|---|---|---|---|
| `2026-10-09.2`, exact names only | 2 of 7 | 2 of 7 | none |
| `2026-10-10.4`, short list of up to four | 2 of 7 | 6 of 7 | 3 of 3 |

The short list was designed on development photos only and frozen before this run ([decision 008](../docs/decisions/008-short-list.md)). It was the second use of the held-out set, and nothing was changed after it. Result files: `eval/results/20261009T093136Z-heldout.json` and `eval/results/20261010T081240Z-heldout.json`.

## Fresh test: 30 new public photos (10 October)

Thirty more TrashNet photos, never used or reviewed before, five per source class, labelled by eye and committed before any recognition call ([decision 009](../docs/decisions/009-fresh-public-test.md), manifest `eval/public-fresh-sources.csv`). Frozen mapping `2026-10-10.4`, one run, 30 calls, no failures (`eval/results/20261010T115237Z-heldout.json`).

| | Result |
|---|---|
| Catalogue items in the set | 19 (11 unsupported) |
| Named outright | 3 of 19, all correct; no wrong item was named |
| Right item offered, named or in the short list | **12 of 19** |
| Unsupported items that still got a short list | 9 of 11 |
| Average choices in a list | 2.3 |

The seven misses: three snack wrappers (the short list never offers wrappers), a milk jug and a food tub (offered drink or glass bottle instead of rigid plastic), a glass bottle (offered a can) and a white box lid (no list). Nothing was changed after this run.
