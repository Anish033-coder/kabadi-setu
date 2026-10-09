# Problem log

Entries below are recorded at 2026-10-08T21:57:54+05:30. Earlier incidents are retrospective; no earlier incident time is inferred.

| Recorded | Problem | Evidence and response | Status |
|---|---|---|---|
| 2026-10-08T21:57:54+05:30 | Repeated pickup action could appear to fail | Stable browser action IDs plus atomic DynamoDB receipts; transaction contention has bounded retries | Fixed; tests pass |
| 2026-10-08T21:57:54+05:30 | Expired login could strand a household | Failed refresh clears credentials and returns to login | Fixed; frontend tests pass |
| 2026-10-08T21:57:54+05:30 | Lambda reservation exceeded this account's usable quota | Mumbai quota is 10; retained quota and omitted incompatible reservation | Deployed |
| 2026-10-08T21:57:54+05:30 | Git metadata write blocked by sandbox | Explicit permission for the relocated .git directory; four topic commits created | Fixed; local only |
| 2026-10-08T21:57:54+05:30 | Bedrock recognition unavailable | Both requested synthetic probes returned ValidationException: Operation not allowed | Blocked; recognition stays disabled, manual path works |

Use each incident as a demo explanation: show the user-visible problem, the smallest fix, the test evidence and the remaining limitation. Do not claim measured impact before measurement.

## 2026-10-08T22:43:40+05:30 — new implementation checks

- Found an API-client variable shadowed by the Cognito client ID inside browser sign-in; renamed the ID variable. Backend smoke tests alone had not exercised this browser error.
- Fixed a syntax error in the new quota transaction builder before any deployment.
- The IAM test initially attempted to transform a local CodeUri; SAM packaging normally converts it to S3. The test now uses a dummy artifact URI while preserving the actual policies.
- Read-only Bedrock metadata reports region and entitlement AVAILABLE but authorization NOT_AUTHORIZED. Recognition remains disabled; no plan upgrade was attempted.
- Some AWS HTTPS requests timed out during hosting setup. Reads and deployment status are checked before retrying mutations; no duplicate app was created.

## 2026-10-08T23:02:27+05:30 — hosting recovery and clean installation

The first Amplify uploader lost its signed-upload state after a TLS failure. Re-running created another pending job, which prevented a third deployment. Both unstarted jobs were explicitly stopped. The uploader now saves pending upload state locally with mode 0600 and uses bounded retries of the same object upload; nothing sensitive is committed.

A fresh clone installed and passed the full tests/build. The browser tool reported ERR_INTERNET_DISCONNECTED while some shell-based AWS operations still completed, so browser availability is tracked separately from AWS stack status.


## 2026-10-09 — browser and live transport verification

The live smoke test now uses curl with bounded retries after Python HTTPS connections repeatedly timed out. Credentials are supplied via stdin and response bodies are omitted from failure messages. The final API smoke passed and removed temporary users/records. A fresh hosted browser tab also completed the manual household-to-recipient flow in Hindi; the earlier offline browser error no longer reproduced. Bedrock authorization is still unresolved, so recognition stays disabled.

## 2026-10-09 — Bedrock escalation and provider fallback

User reports CloudTrail confirms Converse failures (`ValidationException: Operation not allowed`), suspects the known AISPL/India-billing restriction, and has opened an AWS Support case. This supplements our failed probes; the cause remains pending support confirmation. Added a shared Recognizer interface, a conservative DetectLabels mapping, explicit household confirmation, and a config-selected Bedrock adapter. Retained single-call quotas, exact-byte validation and no automatic cross-provider retry. See decision 005 for the narrowly scoped IAM exception and cost accounting.

## 2026-10-09 — unfinished upload and frame protection

The user reproduced an early analyze call returning a generic error. AWS GetObject documentation confirms that without ListBucket, a missing key can return AccessDenied. The scan service now translates NoSuchKey, AccessDenied and 404 around the single S3 read into a helpful 409. The scan remains waiting and quota/model calls are untouched. It logs the S3 code for distinguishing persistent IAM faults; no ListBucket permission was added. Regression tests cover all three codes, successful retry after upload, and unrelated S3 errors.

Amplify header configuration is now versioned in frontend/customHttp.yml and reapplied by the manual deployment script. Live /r HTTP checks confirmed Content-Security-Policy: frame-ancestors 'none' and X-Frame-Options: DENY alongside the existing privacy headers.


## 2026-10-09 — clarification and evidence boundaries

Committed mapping `.3` after the `.2` held-out benchmark. Generic can labels now offer clarification with an unconditional manual escape, so a steel tin is not forced into aluminium. The earlier Beer Bottle-to-glass shortcut was removed. `.3` is a post-benchmark UX change, not yet evaluated; archived `.2` numbers remain unchanged.

Prepared a no-call Bedrock comparison preview, private phone-photo preparation with group-preserving splits, and opt-in anonymous timing-trial export. An expired AWS SSO session blocked deployment and new usage-log measurement; local testing and documentation continued. Added returned DynamoDB capacity logging to close a measurement gap without inventing infrastructure costs.

## 2026-10-09 evening — handover and measurement

- **Bedrock cause narrowed.** CloudTrail recorded both probe calls failing with `ValidationException: Operation not allowed` (ap-south-1 16:26:03 UTC, us-east-1 16:26:29 UTC). The APAC Nova Lite profile exists and is active; availability checks show every model checked as `NOT_AUTHORIZED`; the account is the Organizations management account with only `FullAWSAccess`. This matches the public re:Post report for AISPL accounts. AWS has not confirmed the cause; the support case remains open. Recognition stays on Rekognition.
- **Builder handover.** Codex's weekly limit was reached on October 9; Claude continues the remaining work. Commits from here say which assistant wrote them.
- **Isolated cost measured.** One photo flow cost about $0.00129 at list prices, 97% of it the image request (see `docs/cost.md`).
