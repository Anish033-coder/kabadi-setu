# KabadiSetu

**The AI names the item. Code decides where it goes. People decide what happens.**

A Jaipur prototype for sorting household items, keeping a scrap basket and asking a collector for a pickup through the household's own WhatsApp.

## What works today

Manual catalogue selection, deterministic sorting guidance, baskets, pickup requests and recipient-link responses. Household ownership and Cedar policies restrict actions; DynamoDB transactions protect status changes and action receipts. English and Hindi are available for the main flow.

No collector has validated rates or minimum quantities, so the app prepares a quote request. Sending a WhatsApp link does not prove delivery. A link response is not identity verification or proof of physical collection/recycling.

The manual backend is deployed in Mumbai and its Cognito/API workflow passed live smoke tests. Amplify hosting is being verified. Recognition is implemented behind a disabled flag because Bedrock reports this account is not authorized. Authenticated scan routes use size-bounded uploads, one-read image validation and atomic daily quotas; they reject requests while recognition is disabled. No model savings or real-world impact has been measured.

## Run locally

Use Python 3.14, Node 22.13+ and Docker Desktop. From the project root:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt pytest
make local-db
TABLE_NAME=kabadi-setu-local DYNAMODB_ENDPOINT=http://127.0.0.1:8000 .venv/bin/python -m backend.local
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. The local adapter creates temporary browser sessions instead of Cognito logins. Restarting it changes the local session/link secret; existing local links and household sessions should not be treated as durable. WhatsApp sharing stays disabled locally because another phone cannot reach a loopback URL.

```sh
make test
cd frontend
npm test
npm run build
```

DynamoDB integration tests require the local container; pytest reports skips when it cannot connect. Do not report a skipped run as database validation.

## Before AWS deployment

1. Configure a non-root AWS session. `make preflight` checks the identity without changing resources. Do not share credentials or put them in this repository.
2. Install AWS SAM CLI. `make build` uses the Linux arm64 build container for native dependencies.
3. Deploy `infra/budget.yaml` as a separate budget stack with the `AlertEmail` parameter. Verify all three notifications before deploying the app. This account-wide alert is not a spending cap.
4. Create the SSM link secret once with `make secret`. It refuses root and never prints its value. Do not rotate it casually: rotation invalidates existing links.
5. Review the SAM change set and set `AllowedOrigins` to the exact frontend origin. The initial localhost default is for development, not public hosting. The current Mumbai account concurrency quota is 10; no increase or per-function reservation is requested.
6. After deploying the manual app, use stack outputs in `frontend/.env.local` (see `.env.example`). Configure the host to return the app for `/r` and send `Cache-Control: no-store` and `Referrer-Policy: no-referrer` on the recipient page.
7. Verify household sign-in, cross-household denial, link expiry and the full request flow live before connecting Bedrock.

The model probe is intentionally opt-in, and its result proves only that the calling AWS identity can use that model. Bedrock runtime permissions and an application-level usage quota must be added and tested before public recognition is enabled.

See [cost controls](docs/cost.md) and [retry decisions](docs/decisions/002-retries-and-sessions.md).

## Authorship and event timeline

Developed by Anish Kumawat with Codex for implementation and Claude for research/review and implementation fixes. AI assistance must also be disclosed in the submission writeup. Dependencies retain their upstream licenses. There is no claim that generated code is guaranteed unique or plagiarism-free; changes are reviewed and should be explainable by the author.

The earliest recorded project files were created on October 8, 2026 around 11:40 IST. The exact official kickoff hour still needs confirmation against the organizers' announcement. Local commit timestamps alone do not resolve eligibility; preserve the original timeline and ask organizers if the times overlap.


## Try it as a judge

Use the shared demo credentials supplied privately by the author; they are never committed. The author’s copy is `.local/demo-household.json`. Hosting URL: https://main.d364mryjpwg6jn.amplifyapp.com (check the verification log for deployment status).

1. Open a fresh browser session and sign in with the demo household. Choose Hindi or English.
2. Select Newspaper manually, confirm it is clean and dry, and add it to the basket. Photo recognition may be unavailable; that is disclosed rather than simulated.
3. Prepare a pickup request and review its message. Open the recipient test page without sending a WhatsApp message to a real person.
4. On the Hindi collector page, accept the request, then report it collected. Return to the household page and refresh to see its history. This is a test report, not verified collection.
5. Return to sorting: Newspaper appears under Your usual items. Select it without an AI call and answer the condition question again. Optionally save a collector number on this browser only, after reviewing the number yourself.

## Recognition limits and evaluation

Recognition is disabled by default and has no Bedrock permission while disabled. Once authorized, one direct Nova Lite call suggests a catalogue ID. Invalid output becomes unknown; no model tools can change a basket or pickup. The daily UTC limits are five inference reservations per household and fifty for the whole app. Upload grants are also limited. Errors do not automatically refund a possibly billed call. A new scan of the same photo is not yet deduplicated by hash across scans.

See `eval/README.md` for the 30–50-photo plan. No real held-out dataset or measured recognition savings exists yet. The shortcut count measures selections on that browser, not a proven counterfactual reduction in spending.

GitHub Actions checks local DynamoDB integration, IAM policies, Python tests, frontend tests and the frontend build. Its workflow is committed locally but has not run on GitHub while pushes are paused.
