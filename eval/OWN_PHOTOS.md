# Own-photo spot check — October 10, 2026

**Not a benchmark.** Eight real photos Anish took at home in Jaipur on October 10, used to check the deployed settings on local objects. Too few for accuracy claims; reported as raw counts.

**Method.** Photos were imported with `scripts/prepare_phone_photos.py` (metadata removed, orientation fixed, long side capped at 1024). Labels came from Anish's file names, checked visually by Claude before any call and accepted by Anish; anything outside the catalogue, or showing two different objects, is labelled `unknown`. Each photo is a different object. All eight were treated as a held-out test because nothing was tuned on them: Rekognition `GENERAL_LABELS`, confidence 90, **mapping `2026-10-09.3` frozen**, 1024 px, one run, 8 calls. Photos and labels stay in the ignored `eval/photos/anish-oct10/`; the result file is `eval/results/20261010T071649Z-spotcheck.json`.

| Object | Expected | Result |
|---|---|---|
| Cardboard | cardboard | cardboard ✓ |
| Rusty axe head and iron weight | unknown | unknown ✓ |
| Steel stand with switches and wires | unknown | unknown ✓ |
| Newspaper | newspaper | unknown |
| Two plastic water bottles | pet-bottle | unknown |
| Plastic pot with a pipe | rigid-plastic | unknown |
| Used notebook | notebooks | unknown |
| Steel water bottle | steel-utensil | unknown, and asked "plastic or glass?" |

**Result.** 3/8 correct overall, but only **1/6 supported items** recognised; 7/8 unresolved; no wrong item suggested. One photo triggered the material question, and it was a steel bottle offered only plastic or glass, so the household would need "None of these, choose manually". Median provider latency was about 360 ms.

**What it means.** On real household photos, general labels rarely identify the item. The safety design held (no false suggestions), but the photo path mostly ends in manual choice. Manual selection and *Your usual items* are the main path; recognition is a helper. A model that can choose among the catalogue directly (Bedrock, once access is restored) would need the same test before any accuracy claim.

## Follow-up: the same photos as a development set (mapping `.4`)

After the result above was recorded, the eight photos were moved to the **dev** split and Rekognition's raw labels were fetched once at 512 px (8 calls; `eval/results/20261010T073418Z-own-photos-dev-labels.json`). The labels were mostly right *in kind* but never named the catalogue item:

| Object | Labels at ≥90% confidence |
|---|---|
| Newspaper | Advertisement, Poster |
| Used notebook | Book, Publication, Text, Document, Receipt |
| Two plastic water bottles | Bottle, Plastic |
| Steel water bottle | Aluminium, Bottle, Shaker |
| Plastic pot with a pipe | Cookware, Pot |
| Cardboard | Box (at 1024 px it was also labelled Cardboard) |
| Rusty axe head and iron weight | Ammunition, Grenade, Weapon |

Mapping **`2026-10-10.4`** turns label families (paper, box, bottle, plastic, can, container, metal, electronics) into **up to four catalogue choices**, ranked by how many families agree; the person picks one or searches. It was designed only on dev data (these eight photos and the 20 TrashNet dev photos), then frozen in commit `c720603`.

| Set | Use | Named outright | Right item offered (named or in the list) | Unsupported items given a list |
|---|---|---|---|---|
| These 8 own photos | **dev, designed on them** | 0/6 at 512 px | 6/6 | 0/2 |
| TrashNet dev, 512 px | dev | 5/13 | 10/13 | — |
| TrashNet held-out, 512 px | **second use of this set**, one run, frozen | 2/7 | **6/7** | 3/3 |

The own-photo figures are not evidence: the mapping was built from them. The TrashNet held-out set was used once before for mapping `.2`; nothing was changed after this run (`eval/results/20261010T081240Z-heldout.json`). The cost is visible too: every unsupported item got a short list, so the person taps "None of these" (average 2.3 choices shown). A fresh set of new household objects is needed before any Jaipur claim for `.4`.
