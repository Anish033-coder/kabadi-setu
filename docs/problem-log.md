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
