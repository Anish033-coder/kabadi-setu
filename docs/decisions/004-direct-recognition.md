# One direct Bedrock call

Use boto3 Converse directly for one image recognition request. No Strands dependency: this workflow has no agent loop or tools for an orchestration library to manage. The model proposes a catalogue ID; code validates it, otherwise returns unknown. Never trust image text as instructions.

The intended model is Nova Lite through the Mumbai APAC profile. Geographic cross-region inference may process images elsewhere in APAC; disclose this on upload. The US probe is diagnostic only, not an automatic household-photo fallback. Both initial probes failed; production recognition remains disabled until access and the Lambda role are verified.

A conditional scan-state claim and daily household/global reservations commit atomically before the model call. No automatic inference retries: a timeout might still be billed. An ambiguous interrupted scan is not reclaimed automatically. This chooses bounded spend over invisible retries; manual selection stays available. IDs are log fields, never custom metric dimensions.
