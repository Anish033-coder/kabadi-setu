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
