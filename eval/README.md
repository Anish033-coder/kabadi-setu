# Recognition evaluation

A limited public-photo benchmark is now recorded in INTERNET_PHOTOS.md and results/. Bedrock remains blocked; Rekognition calls succeeded. No original household photo set has been supplied. A synthetic green square is an access test, not an accuracy example.

Collect 30–50 original item photos with no people, addresses or documents. Label each with an existing catalogue ID or unknown before running the model. Save photos under `eval/photos/` (ignored by Git). Create `eval/manifest.csv` with columns `path,label,split`, where path is relative to this directory and split is dev or heldout. Keep every image of the same physical item in the same split; the validator also rejects identical bytes appearing twice. Use development examples to choose photo size, then freeze the configuration before the held-out run.

The evaluator uses the same selected provider adapter and mapping/prompt as the application, strips metadata, and saves raw per-image results and provider usage. It makes one call per selected image/size, never automatically retries. It requires explicit paid-call opt-in and non-root credentials. Failures remain in the denominator; token totals for failed responses may be unknown. Do not claim measured cost until access works and region-specific prices have been recorded.

Examples after account access is resolved:

```sh
AWS_PROFILE=kabadi-setu .venv/bin/python eval/run.py --split dev --sizes 768 1024 --allow-paid-calls
# Freeze the chosen size in a decision note before evaluating held-out images.
AWS_PROFILE=kabadi-setu .venv/bin/python eval/run.py --split heldout --sizes 1024 --allow-paid-calls
```

Report correct/total and unresolved/total for each size, plus latency and provider usage. For Rekognition, inference cost estimate = image requests × dated Mumbai GENERAL_LABELS per-image price. For Bedrock, inference cost estimate = input_tokens × dated input price per million / 1,000,000 + output_tokens × dated output price per million / 1,000,000. Whole-flow cost also includes API, storage, compute and logs. Label estimates before credits; do not treat missing token usage as zero.

## Provider fallback

The runner now defaults to `--provider rekognition`; use `--provider bedrock` only once access is resolved. Freeze the label mapping on development photos before evaluating held-out photos. Rekognition reports per-image requests and its label-model/mapping versions, not token usage. Compare accuracy and latency at the two sizes; do not claim a per-request pricing discount from resizing. Evaluation makes direct, explicitly opted-in calls outside the web app quota, so keep the existing 30–50-photo limit and run only the planned sizes/split.

Development Rekognition results include the returned label names/confidences (at the configured >=90 threshold) for mapping review. These labels are not put in application logs or held-out evaluation output. Do not expand generic Bottle/Water Bottle into a material-specific catalogue item without sufficient evidence or an additional household question.
