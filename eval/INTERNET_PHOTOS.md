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
