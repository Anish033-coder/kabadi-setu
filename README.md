# KabadiSetu

**The AI names the item. Code decides where it goes. People decide what happens.**

A Jaipur prototype for sorting household items, keeping a scrap basket and asking a collector for a pickup through the household's own WhatsApp.

**Live prototype:** [Open KabadiSetu](https://main.d364mryjpwg6jn.amplifyapp.com/)

**Evidence:** [Architecture](docs/architecture.md) · [Evaluation](eval/INTERNET_PHOTOS.md) · [Costs](docs/cost.md) · [Problem log](docs/problem-log.md) · [Timing protocol](docs/timing-trials.md)

**Honest limits:** no collector validation or verified pickups; no measured household impact. Rekognition named only 2/7 supported held-out items outright (mapping `.2`), and 1/6 in an 8-photo spot check of Anish's own Jaipur photos (mapping `.3`). Mapping `.4` offers a ranked short list of up to four items instead: on a second, frozen use of the public held-out set the right item was offered for 6/7, but every unsupported item also got a list ([eval/OWN_PHOTOS.md](eval/OWN_PHOTOS.md)). Not yet tested on new Jaipur photos. Bedrock remains blocked. Physical-phone and household timing results are pending. Local changes are not automatically live; see the verification log.

## Try it as a judge

Open https://main.d364mryjpwg6jn.amplifyapp.com on a phone or laptop and **create an account with any email address**: Amazon Cognito emails a verification code, then you sign in. Each account is its own household. (A shared demo login can also be supplied privately; credentials are never committed.)

1. Open a fresh browser session, create an account or sign in, and choose Hindi or English.
2. Select Newspaper manually, confirm it is clean and dry, and add it to the basket. Photo recognition may be unavailable; that is disclosed rather than simulated.
3. Prepare a pickup request and review its message. Open the recipient test page without sending a WhatsApp message to a real person.
4. On the Hindi collector page, accept the request, then report it collected. Return to the household page and refresh to see its history. This is a test report, not verified collection.
5. Return to sorting: Newspaper appears under Your usual items. Select it without an AI call and answer the condition question again. Optionally save a collector number on this browser only, after reviewing the number yourself.

## What works today

Manual catalogue selection, deterministic sorting guidance, baskets, pickup requests and recipient-link responses. Household ownership and Cedar policies restrict actions; DynamoDB transactions protect status changes and action receipts. English and Hindi are available for the main flow.

No collector has validated rates or minimum quantities, so the app prepares a quote request. Sending a WhatsApp link does not prove delivery. A link response is not identity verification or proof of physical collection/recycling.

The manual backend is deployed in Mumbai and its Cognito/API workflow passed live smoke tests. The frontend is hosted on Amplify; its recipient route and privacy headers have been verified over HTTP. A hosted-browser demo also passed sign-in, manual sorting, basket saving, request creation and the Hindi recipient acceptance/collection-report flow. Rekognition recognition is now enabled in Mumbai; Bedrock remains unavailable for this account. Authenticated scan routes use size-bounded uploads, one-read image validation and atomic daily quotas; the feature can be disabled without changing the manual path. A small public-photo benchmark is recorded in eval/INTERNET_PHOTOS.md; no real-world impact or model-cost savings is claimed.

## Run locally

Use Python 3.14, Node 22.13+ and Docker Desktop. From the project root:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt -r requirements-dev.txt
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

The model probe is intentionally opt-in, and its result proves only that the calling AWS identity can use that model. Provider-specific runtime permissions and quotas are implemented; Bedrock access and its live Lambda integration remain unverified.

See [cost controls](docs/cost.md) and [retry decisions](docs/decisions/002-retries-and-sessions.md).





## Recognition limits and evaluation

Recognition is disabled by default and has no Bedrock permission while disabled. Set `RecognitionProvider=rekognition` for one DetectLabels call with a conservative code mapping, or `bedrock` for one direct Nova Lite call after its authorization is resolved. The household must confirm the suggested item before condition checks. Invalid output becomes unknown; no model tools can change a basket or pickup. The daily UTC limits are five inference reservations per household and fifty for the whole app. Upload grants are also limited. Errors do not automatically refund a possibly billed call. A new scan of the same photo is not yet deduplicated by hash across scans.

See `eval/README.md` for the 30–50-photo plan. A 30-image public-photo benchmark is complete: 20 development and 10 held out. Mapping `.2` held-out results were 5/10 correct including expected-unknown negatives, with only 2/7 supported items recognised. Mapping `.4` (short list, designed on dev photos only) offered the right item for 6/7 on a second use of that held-out set; see `eval/OWN_PHOTOS.md`. It does not establish Jaipur-user performance; no recognition cost savings is claimed. The shortcut count measures selections on that browser, not a proven counterfactual reduction in spending.

GitHub Actions checks local DynamoDB integration, IAM policies, Python tests, frontend tests and the frontend build. Its workflow is committed locally but has not run on GitHub while pushes are paused.

## Recognition fallback status — October 9

The Rekognition and Bedrock adapters share the same scan ownership, validation, quota and saved-result flow. The template defaults to Rekognition with recognition **disabled**. Enable only after a successful account probe and reviewed deployment. The IAM test permits one documented global-resource exception: `rekognition:DetectLabels`, restricted to Mumbai. See [decision 005](docs/decisions/005-recognition-providers.md). Rekognition is deployed and the synthetic hosted upload/analyze/repeat check passed. This proves connectivity and saved-result reuse, not accuracy on real items.

## Authorship and event timeline

Developed by Anish Kumawat for WeMakeDevs × AWS Environmental Hacks (Waste and Energy track). AI assistance, as the event rules require us to disclose: **Codex** wrote most of the implementation; **Claude** did research, code review and review fixes, and took over the remaining work from October 9 after Codex's usage limit was reached. Each commit message says who wrote the change. Dependencies keep their upstream licences; the TrashNet evaluation photos are MIT-licensed and credited in `eval/`.

The official schedule lists kickoff as Thursday, October 8, 2026, without a specific hour. The earliest project files were created on October 8 at about 11:40 IST, and the Git history starts the same day. Nothing was built before the event.
