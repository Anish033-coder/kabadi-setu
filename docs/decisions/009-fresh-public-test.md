# 009 — A fresh 30-photo public test of the short list

Date: 2026-10-10. Written before any photo in this set was labelled or sent to Rekognition.

The short list (mapping `2026-10-10.4`, decision 008) was measured on only 7 known items, and that held-out set had been used twice. This is a new test of the same frozen mapping, with no changes allowed after the run.

**Photos.** 30 TrashNet photos from the archive recorded in decision 006 (same SHA256), five from each source class (cardboard, glass, metal, paper, plastic, trash), drawn with seed `20261010`. Every photo used or reviewed for decision 006 was excluded first. All 30 are held out; none is used for tuning.

**Labelling rules,** applied by looking at each photo before any recognition call:

- Use the catalogue item the photo clearly shows. If it fits no catalogue item, shows more than one kind of object, or could be either of two items, label it `unknown`.
- `pet-bottle` (Drink bottles): plastic water and soft-drink bottles. Other rigid plastic (detergent or shampoo bottles, tubs, jars, boxes) is `rigid-plastic`.
- `glass-bottle`: intact glass bottles and jars. Broken glass is `broken-glass`.
- `aluminium-can`: drink cans. Food tins are steel and not in the catalogue, so `unknown`.
- `steel-utensil`: steel kitchen items such as pots, plates, cutlery and bottles.
- `newspaper`: newsprint. `notebooks`: notebooks and books. `office-paper`: loose printed or plain sheets and envelopes. Magazines, paper bags, cups and tissue are `unknown`.
- `cardboard`: corrugated boxes and thick paperboard cartons.
- From the trash class: chips or snack packets are `wrapper`, food is `food`, anything else `unknown`.

**Run.** Rekognition `GENERAL_LABELS`, confidence 90, 512 px, one call per photo, through `eval/run.py` with the committed manifest `eval/public-fresh-sources.csv`. Reported as raw counts: named outright, right item offered (named or in the short list) out of the known items, and how many unsupported items got a list.

**Result, added after the run.** Right item offered for 12 of 19 catalogue items; 3 named outright, none wrong; 9 of 11 unsupported items still received a list. Details in `eval/INTERNET_PHOTOS.md`. The labels were committed in `ccd0a70` before the run.
