# 008 — A ranked short list from broad labels

Date: 2026-10-10. Supersedes the single material question in 007.

Mapping `.3` named 1 of 6 supported items in an 8-photo held-out spot check of Anish's own photos. After that result was recorded, the same photos became development data and their raw labels were read once. Rekognition was usually right about the kind of thing but not the catalogue item: Book/Text for a notebook, Advertisement/Poster for a newspaper, Aluminium/Bottle for a steel bottle.

Mapping `2026-10-10.4` keeps exact matches, and otherwise turns label families (paper, box, bottle, plastic, can, container, metal, electronics) into up to four catalogue choices, ranked by how many families agree. Two different specific items in one photo are both offered; code never picks between them. The person chooses an item or "None of these", and the choice follows the same condition questions and rules as manual selection. No extra model call is made.

It was designed only on development photos and frozen in commit `4d60f99` before one run on the public held-out set, which had already been used once for mapping `.2`. The right item was offered for 6 of 7 known items (named outright: 2 of 7), but all 3 unsupported items also received a list. Results and caveats: `eval/OWN_PHOTOS.md`. No Jaipur accuracy claim is made for `.4`.
