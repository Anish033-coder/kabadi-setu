# 007 — Ask about ambiguous material

Mapping `2026-10-09.3` is a **post-benchmark UX change, not yet evaluated**. Only mapping `.2` owns the published held-out numbers in decision 006. Do not transfer those numbers to this version or tune using that held-out set.

Rekognition can identify a bottle, jar or can without identifying its material. Keep item_id=unknown and return a small, catalogue-scoped clarification instead. A single recognised family can offer plastic/glass bottle, container, or aluminium drink-can choices. Conflicting recognised objects still fall back to manual selection. The user must always have **“None of these, choose manually”**, including when aluminium-can is the only offered candidate. A steel tin is never forced into that choice.

Removed the Beer Bottle → glass-bottle shortcut: the bottle question now asks the person rather than inferring material from the drink. A question is not a correct automatic recognition, and choosing an option is not confirmation of recycling or collector acceptance.

The clarification makes no additional model call. It uses the existing saved scan result, quotas and ownership checks. A choice then follows the same deterministic condition/route flow as manual selection. Tests verify conservative questions, candidate scoping and one-call saved-result behaviour. Phone and household usability measurements are separate pending evidence.
