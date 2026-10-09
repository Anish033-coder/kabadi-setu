# Local verification — October 8, 2026

After the review fixes:

- Backend: 48 tests passed, including DynamoDB Local tests; no skips on the final run.
- Frontend: five request/session/action-ID tests passed; TypeScript and Vite production build passed.
- Application SAM template and separate budget template: cfn-lint passed; SAM validation passed.
- Lambda: Python 3.14 Linux arm64 container build succeeded. Packaged Pillow decoded a JPEG and packaged Cedar authorized an owned request inside that container with networking disabled.
- Git whitespace check passed. No GitHub pushes, AWS deployment, secret creation, alert activation or Bedrock inference performed.

One initial backend run could not reach Docker under the restricted network permissions and skipped integration cases. It is not used as evidence: after local networking was allowed, the complete suite passed without skips.

The first SAM command could not write its global metadata directory, but the build itself succeeded. Subsequent commands use a repository-local, ignored SAM configuration directory. This setting is now in the Makefile.

Still unverified: live Cognito, Lambda/API permissions, actual budget notifications, browser flow on a physical phone, photo-recognition accuracy and real AWS cost. A successful local container build is not a live deployment test.


## Subsequent live AWS verification

The user configured `kabadi-setu` through IAM Identity Center. STS confirmed a non-root AdministratorAccess assumed role. Created the separate `kabadi-setu-budget` stack and verified absolute-value email thresholds of $1, $5 and $10. This verifies configuration, not delivery of an actual alert email.

Created the SSM link secret without displaying its value. Reviewed a change set containing only 18 additions, then deployed the manual backend stack successfully. SAM also created its managed artifact bucket. The actual Mumbai concurrency quota is ten, so no per-function reservation or quota increase was applied.

Live smoke checks passed: Cognito sign-in with two temporary users, rejection without authentication, cross-household denial, deterministic sorting, basket save, duplicate request creation returning the same request, recipient-link view, acceptance and collection report. Temporary users (with email suppressed) and all known test records were removed afterward. These are test scenarios, not real pickups.

Live configuration verified: Python 3.14 arm64 Lambda active; HTTP route target two requests/second, burst five; detailed API metrics disabled; application log retention fourteen days. No Bedrock calls or GitHub pushes. Infrastructure is now active and can incur service charges; spend has not yet been reconciled with billing.

Public frontend hosting, physical-phone browser testing and image recognition remain pending.


## Bedrock availability probes — recorded 2026-10-08T21:57:54+05:30

- Mumbai `ap-south-1`, `apac.amazon.nova-lite-v1:0`: ValidationException, “Operation not allowed”.
- US fallback `us-east-1`, `amazon.nova-lite-v1:0`: same error.
- Both probes used a generated 64×64 solid-colour JPEG, max output 20 tokens; neither returned token usage or recognition output. Charges cannot be inferred from that absence. No accuracy conclusion is possible. No account upgrade or capacity purchase was made.


## Resumed implementation — 2026-10-08T23:02:27+05:30

- Eight additional topic commits were made locally after d67f042; no GitHub push.
- Recognition implementation: 63 backend tests pass, including DynamoDB Local concurrent quota tests, ownership, exact-byte input and saved results after ambiguous failure. Bedrock is mocked in these tests.
- Source and SAM-transformed IAM checks pass; permissions use exact resources apart from the necessary project-photo object prefix and project log streams. No wildcard actions or account-wide Resource:* permissions.
- A fresh local clone with a newly installed Python environment and npm ci passed all 63 backend tests, five frontend tests and the production build. No integration tests skipped.
- Lambda container build passed; AWS backend stack reached UPDATE_COMPLETE with recognition disabled. Amplify origin is configured and route throttles were raised to 5/10 in the deployed template.
- An email-suppressed demo user was created; credentials remain in ignored .local files.
- Amplify upload attempts hit TLS errors and left pending jobs; those pending jobs were stopped before a controlled retry. The in-app browser reported ERR_INTERNET_DISCONNECTED, so no successful browser walkthrough or physical-phone/mobile-data test is claimed.
- npm audit reports low-severity findings for esbuild and Vite, with no fix available in its report. No automatic dependency upgrade was attempted.
- Real-photo accuracy, inference cost, mobile-data behavior and final submission remain unverified. No submission tag yet.


## Hosting confirmed — 2026-10-08T23:04:29+05:30

Amplify reports SUCCEED for the frontend deployment. `https://main.d364mryjpwg6jn.amplifyapp.com/r` returns HTTP 200, text/html, Cache-Control: no-store and Referrer-Policy: no-referrer. The API health endpoint returns mode=aws, recognition=unavailable. The fresh-browser walkthrough remains unverified: the in-app browser displayed an offline error page and its error-page data URL was blocked by the browser tool. This is separate from the successful HTTP checks.

The first post-update smoke run stopped on a TLS timeout at /health before creating users. A subsequent run is recorded below when complete. No model calls beyond the two failed synthetic probes were attempted.


## Post-deployment smoke completed — recorded 2026-10-09

The final live smoke run passed sign-in, unauthenticated denial, cross-household denial, manual sorting, basket save, idempotent request creation, acceptance and collection reporting. Temporary users and known test records were removed; no email was sent. The HTTP test transport now uses curl with bounded retries and credentials provided over stdin after repeated Python TLS timeouts. These remain synthetic test scenarios, not real collections.


## Hosted browser walkthrough — 2026-10-09T08:38:04+05:30

A fresh in-app browser tab successfully signed in with the private demo household. Selected Newspapers, confirmed clean/dry condition, saved one item, and prepared a request. The usual-items shortcut appeared after adding the item. Opened the recipient test link: Hindi was the default, no collector login was requested, and Accept followed by Report collection produced the expected status/history. No WhatsApp message was sent and no collector was contacted. This demo record is synthetic; it is not evidence of physical collection.

Recognition displayed its unavailable/manual-fallback message. Physical-phone mobile-data testing, real-photo evaluation, cost reconciliation and Bedrock authorization remain outstanding. No submission tag or GitHub push was made.

## October 9 — submission preparation, local verification

- Clarification mapping `.3` committed with the mandatory manual escape. Published held-out numbers remain mapping `.2` only; `.3` is a post-benchmark UX change, not yet evaluated.
- Bedrock comparison dry run selected the frozen ten held-out images at 512 pixels without AWS requests. Real execution requires both paid-call opt-in and access confirmation. No Bedrock calls were made.
- Photo importer tests passed for orientation, metadata removal, duplicate handling, group-preserving splits, overwrite refusal and changed-photo rejection. Original household photos are still pending.
- Backend suite passed 100 tests before adding the cost calculator; the additional calculator test passed separately. Frontend passed seven tests; TypeScript/Vite and SAM Linux arm64 container builds succeeded. No database tests were skipped in the full run.
- TrialPanel is an extracted component. Timing records include aborted trials and have no names, item IDs or timestamps. They exist only in page memory until export. No human timing results were collected.
- Fresh AWS verification failed with an expired SSO token; renewal was requested. These local changes have not been deployed. The current live recognition mapping remains `.2` until a verified deployment.
- Responsive local-browser verification was attempted at 390×844, but the browser client refused the loopback page with ERR_BLOCKED_BY_CLIENT. The viewport override was reset. This is not a passed phone test, and no physical-phone/mobile-data check is claimed.
- Architecture, trial protocol, video shot list and factual blog sections are drafts. Blog publication, GitHub push/public visibility and submission tag remain unauthorised and were not performed.
