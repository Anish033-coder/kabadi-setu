# Cost controls and evidence

Status: manual backend deployed October 8 and Rekognition enabled October 9 in Mumbai; request counts and list-price inference estimates are recorded below; account-wide billing has a partial reconciliation; current recognition and infrastructure charges have not yet posted/been reconciled.

The manual path makes zero model calls. Rekognition is now enabled; Bedrock remains blocked. Do not turn this into a claim that the deployed app is free: API requests, Lambda, DynamoDB, logging, hosting and authentication can contribute costs.

## Controls active after the first deploy

- HTTP API default route limit: 5 requests/second, burst 10. This is a per-route target, not a whole-account hard cap.
- Lambda timeout: 28 seconds, memory: 512 MB. Live preflight found the Mumbai account concurrency quota is 10; keep it unchanged. No per-function reservation: AWS requires an unreserved pool that this small account quota cannot support. Traffic throttles remain in place.
- No provisioned concurrency, NAT gateway, dedicated server or scheduled inference.
- DynamoDB on-demand, with TTL for request records and action receipts after 90 days. Basket records currently persist; account deletion/cleanup is still future work.
- Application log retention: 14 days. No request bodies, secrets or photos logged; no unique request IDs as metric dimensions.
- Separate `infra/budget.yaml`: monthly account-wide, pre-credit alerts above $1, $5 and $10. This deliberately includes unrelated account spending and avoids depending on cost-tag activation. It does not replace or edit the existing account budget.
- The alert address is stored in ignored `.local/deploy-settings.json` and in the deployed budget configuration, not tracked source files.
- Model probe requires `--allow-paid-call` and refuses root credentials. It tests the caller, not the Lambda execution role.

**Budget thresholds, API route throttles and log retention have been verified live. Budgets are delayed notifications, not a spending cap.** Traffic throttles reduce exposure but do not guarantee a maximum bill. The disabled recognition configuration has no permission to invoke Bedrock.

## Measurement plan

Keep the first working recognition implementation as the baseline. For each actual inference, record model ID, region, input/output token counts, image dimensions, latency and success/failure. Keep identifiers in logs rather than metric dimensions. Count failed/retried calls as well as successful ones. Use dated regional list prices and label the result an estimate; reconcile with billing later.

Compare two image sizes for the available provider on development photos, then freeze mapping and settings before the held-out run. A second provider comparison is optional after Bedrock authorization is resolved. Record correct/total and unresolved/total, not just percentages. Include image preparation, API/storage costs and retries when reporting whole-flow cost; distinguish those from inference-only cost.

Report cost per scan, per request and per reported pickup separately. A pickup report is not independently verified collection. Project a clearly labelled scenario of 200,000 monthly scans without claiming those users exist. No numbers belong in the savings column until measured.

Sources checked 2026-10-08:
- https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-httpapi.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-budgets-budget.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-budgets-budget-costtypes.html


## Recognition implementation (awaiting account access)

Five household and fifty application inference reservations per UTC day; twenty household and two hundred application upload grants per day. Private JPEGs expire under S3 lifecycle after one day (deletion is asynchronous). No SDK inference retries. Bedrock token usage or Rekognition image-request usage is recorded for each recognition call; request summaries no longer incorrectly report zero calls for every route.

As of October 8, both availability probes failed and returned no usage. Model accuracy, tokens per real photo and inference dollar estimates are **not measured**. Infrastructure charges and failed-call billing are also not yet reconciled. Do not substitute projected figures for measured ones.

## Rekognition fallback — October 9

The user reports $240 in promotional credits with $0 used; this is user-reported, not a reconciled bill. Continue reporting gross costs before credits and verifying credit applicability/expiry separately.

DetectLabels GENERAL_LABELS is billed by images/requests rather than input/output tokens. Log `provider`, `image_requests`, `label_model_version`, `mapping_version` and duration. Count failed attempts conservatively pending billing reconciliation. Do not apply Nova token rates to this provider. Image resizing can save upload bytes/time but is not a per-image price discount. Use `eval/run.py --provider rekognition` for evaluation; freeze mapping and size before held-out tests. Mapping coverage/accuracy was subsequently measured below; the posted recognition bill remains pending.


## Measured public-photo run — October 9

The development run made 40 DetectLabels requests (20 photos at two sizes), and the held-out run made 10 requests. Offline mapping replay made zero extra calls. At AWS's Mumbai Group2 first-tier price of **$0.00125 per image** (price-list publication 2026-09-11; snapshot saved in eval/results/rekognition-mumbai-price.json), these 50 requests estimate **$0.0625 before credits/tax**. This is inference-only estimated gross cost, not the AWS bill. The price list also includes a legacy ImagesProcessed SKU; the estimate uses the current Group2 tier and must be reconciled against actual usage type.

Two synthetic application checks, one direct synthetic access probe and one browser development-photo check add four known requests, or an estimated $0.005 at the same rate. Total known Rekognition requests in this implementation sequence: 54, estimated $0.0675. Earlier failed Bedrock calls and other users' activity are not included. Hosting, API, Lambda, S3, DynamoDB and logging remain additional costs.

The estimate is $0.125 per 100 recognition scans or $1.25 per 1,000, regardless of the tested 256/512 dimensions. Manual selections make no image request. A purely illustrative 200,000-recognition-scan month would be $250 inference-only at this tier, before credits/tax and other service costs; it is not a forecast of users or spending. Existing daily application quotas prevent that scenario in the current configuration.

Development median provider latency was 155 ms at 256 and 171 ms at 512; held-out median was 173 ms at 512. These exclude upload, login and full user interaction. No statistical significance or per-image price saving is inferred from those small latency differences.


## Partial billing reconciliation — October 9

One Cost Explorer query, saved privately in `.local/cost-reconciliation.json`, covered October 8–9 and grouped by service and record type. October 8 showed $0.0003132446 in gross account-wide charges and -$0.0003132453 in credits: net approximately zero (rounding). October 9 returned no posted groups. Both days were marked estimated. These are account-wide figures, including unrelated services, not a project-attributed bill. They do **not** establish zero recognition cost or the remaining promotional-credit balance. The reported $240 balance remains user-reported.

Keep three separate quantities: estimated pre-credit usage cost, credits actually posted by billing, and the resulting net bill. Do not subtract the advertised credit balance from estimated scan costs. Cost Explorer API queries themselves cost money; the one query adds $0.01 at list price and is not polled repeatedly. Billing refreshes can take over 24 hours.

Sources: [Cost Explorer data timing](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html), [Cost Explorer pricing](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/).

## Whole-scan calculation: measurement gate

`eval/results/infrastructure-mumbai-prices.json` records current regional list-price dimensions for Lambda arm64, HTTP API and DynamoDB Standard. New repository instrumentation requests returned consumed capacity and logs read/write units without keys, table names or unique metric dimensions. It does not add a database request. Successful response usage is measured; unreported failed-attempt usage must remain a reconciliation gap, not zero.

For an isolated test flow, sum its HTTP API requests, Lambda REPORT billed milliseconds at 512 MB, database read/write units and actual image requests. Then compute:

- Rekognition: image requests × $0.00125.
- HTTP API: metered requests × the recorded regional per-request rate.
- Lambda: invocations × request rate + total billed milliseconds / 1000 × 0.5 GB × arm64 GB-second rate.
- DynamoDB: returned read units × read-unit rate + returned write units × write-unit rate. Transaction capacity is already included in returned units; do not double it again.

Multiply the measured flow cost by 100 for a per-100 equivalent. This is a list-price estimate, not 100 measured scans. Include failures and retries. Keep S3, logs, hosting, Cognito, bandwidth and account-wide fixed usage separate; the four-service subtotal is not the entire app bill. Use Lambda's billed duration, not recognition latency or browser elapsed time.

**Pending:** the new capacity logs must be deployed and an isolated flow measured. The AWS session expired during preparation. No full-stack per-100 figure is presented as measured yet. The existing $0.125/100 and $250/200,000 figures remain explicitly inference-only estimates. The 200,000/month scenario is a projection, not current traffic, and exceeds today's application quotas. Manual selection has zero AI calls but still incurs its API/compute/storage activity.


Current first-tier Mumbai rates in that snapshot (USD, before credits/tax):

| Component | Unit rate |
|---|---:|
| HTTP API | $1.05 / million metered requests |
| Lambda arm64 requests | $0.20 / million invocations |
| Lambda arm64 duration | $0.0000133334 / GB-second |
| DynamoDB Standard reads | $0.1425 / million read units |
| DynamoDB Standard writes | $0.71 / million write units |

Regional price sources are embedded in the saved snapshot: [Lambda](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSLambda/current/ap-south-1/index.json), [HTTP API](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonApiGateway/current/ap-south-1/index.json), [DynamoDB](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonDynamoDB/current/ap-south-1/index.json). Use exact usage types (not Lambda web requests, managed instances or replicated DynamoDB writes).

To reproduce the subtotal after collecting one isolated flow, write `.local/scan-counts.json` with numeric `scans`, `image_requests`, `api_requests`, `lambda_invocations`, `lambda_billed_ms`, `ddb_read_units`, and `ddb_write_units`. Use sums from the same measurement window; do not combine direct evaluation calls with unrelated app activity. Run:

```sh
.venv/bin/python scripts/estimate_scan_cost.py .local/scan-counts.json
```

The calculator makes no AWS calls and uses the committed price snapshot. It emits per-100 and 200,000-scan equivalents, both explicitly estimated subtotals. Its unit test uses invented arithmetic fixtures, which are not project measurements. Record source log references privately and publish only aggregate counts.
