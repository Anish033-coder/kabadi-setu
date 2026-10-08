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
