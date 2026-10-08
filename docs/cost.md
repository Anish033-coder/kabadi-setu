# Cost controls and evidence

Status: manual backend deployed in Mumbai on October 8, 2026; no measured cloud cost or inference savings yet.

The manual path makes zero model calls. Recognition is not connected. Do not turn this into a claim that the deployed app is free: API requests, Lambda, DynamoDB, logging, hosting and authentication can contribute costs.

## Controls active after the first deploy

- HTTP API default route limit: 2 requests/second, burst 5. This is a per-route target, not a whole-account hard cap.
- Lambda timeout: 10 seconds, memory: 512 MB. Live preflight found the Mumbai account concurrency quota is 10; keep it unchanged. No per-function reservation: AWS requires an unreserved pool that this small account quota cannot support. Traffic throttles remain in place.
- No provisioned concurrency, NAT gateway, dedicated server or scheduled inference.
- DynamoDB on-demand, with TTL for request records and action receipts after 90 days. Basket records currently persist; account deletion/cleanup is still future work.
- Application log retention: 14 days. No request bodies, secrets or photos logged; no unique request IDs as metric dimensions.
- Separate `infra/budget.yaml`: monthly account-wide, pre-credit alerts above $1, $5 and $10. This deliberately includes unrelated account spending and avoids depending on cost-tag activation. It does not replace or edit the existing account budget.
- The alert address is stored in ignored `.local/deploy-settings.json` and in the deployed budget configuration, not tracked source files.
- Model probe requires `--allow-paid-call` and refuses root credentials. It tests the caller, not the Lambda execution role.

**Budget thresholds, API route throttles and log retention have been verified live. Budgets are delayed notifications, not a spending cap.** Traffic throttles reduce exposure but do not guarantee a maximum bill. The manual skeleton has no permission to invoke Bedrock.

## Measurement plan

Keep the first working recognition implementation as the baseline. For each actual inference, record model ID, region, input/output token counts, image dimensions, latency and success/failure. Keep identifiers in logs rather than metric dimensions. Count failed/retried calls as well as successful ones. Use dated regional list prices and label the result an estimate; reconcile with billing later.

Compare two models and two image sizes on development photos, then freeze settings before the held-out run. Record correct/total and unresolved/total, not just percentages. Include image preparation, API/storage costs and retries when reporting whole-flow cost; distinguish those from inference-only cost.

Report cost per scan, per request and per reported pickup separately. A pickup report is not independently verified collection. Project a clearly labelled scenario of 200,000 monthly scans without claiming those users exist. No numbers belong in the savings column until measured.

Sources checked 2026-10-08:
- https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-httpapi.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-budgets-budget.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-budgets-budget-costtypes.html
