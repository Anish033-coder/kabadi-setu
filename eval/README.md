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

## Frozen Bedrock comparison (prepared, not run)

The default manifest is now `eval/internet-sources.csv`, the frozen public set used for mapping `.2`, and the default is its ten held-out photos at 512 pixels. Preview without AWS requests:

```sh
.venv/bin/python eval/run.py --provider bedrock --dry-run
```

Only after AWS Support/account access is confirmed:

```sh
AWS_PROFILE=kabadi-setu .venv/bin/python eval/run.py --provider bedrock --allow-paid-calls --access-confirmed
```

Both switches are intentional safeguards. The manifest's photo hashes are checked, and its own hash is saved with results. Do not tune a prompt on these held-out results. Compare with the archived `.2` results, not a rerun using `.3`. Mapping `.3` is a **post-benchmark UX change, not yet evaluated**; a classification-only run also cannot measure how households answer clarification questions.

The SAM template already selects provider-exclusive permissions using `RecognitionProvider` and `RecognitionEnabled`. Leave the deployed provider on Rekognition. Once access is confirmed, review a change set with `RecognitionProvider=bedrock RecognitionEnabled=true`; retain the configured model/profile and exact Amplify origin. An evaluator call uses the developer identity and does not prove the Lambda role works.

## Import Anish's own photos

Use 30–50 photos across different physical items. Put different angles of the same object in one subfolder, for example `incoming/bottle-01/`. Avoid people, addresses and personal documents. Run from the project root:

```sh
.venv/bin/python scripts/prepare_phone_photos.py import /absolute/path/to/incoming --name anish-oct10
# Fill label and group_id in eval/photos/anish-oct10/labels.csv.
.venv/bin/python scripts/prepare_phone_photos.py split eval/photos/anish-oct10/labels.csv
.venv/bin/python eval/run.py --manifest eval/photos/anish-oct10/manifest.csv --split dev --sizes 256 512 --dry-run
```

Use catalogue IDs from `data/catalogue.json`, or `unknown` for unsupported items. A group identifies a physical object, not a material class. Splitting is deterministic by group (about 30% held out) and refuses to overwrite a manifest. Finish labels and freeze the split **before any provider run**. Use only dev photos to tune mapping. A new held-out set is needed to evaluate the post-benchmark clarification flow with people.

The importer leaves originals unchanged, re-encodes pixels without EXIF/GPS, corrects orientation, caps the long side at 1024 and hashes the result. Duplicate prepared bytes and unreadable files appear in `rejected.csv`. Export unsupported HEIC files as JPEG. All photos, labels, original filenames and manifests produced by this workflow remain under ignored `eval/photos/`. Do not force-add them to Git. Photo contents can still reveal personal details even after metadata removal; inspect them yourself.
