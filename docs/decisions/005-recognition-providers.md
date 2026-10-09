# 005 — Rekognition fallback with the same scan safeguards

Date: 2026-10-09

## Evidence and decision

Our two Bedrock Converse probes returned `ValidationException: Operation not allowed`; the read-only availability check reported `NOT_AUTHORIZED`. The user reports matching CloudTrail events, an AISPL/India-billing restriction as the suspected cause, and an open AWS Support case. We have not independently inspected that case or received an AWS-confirmed cause. Do not describe the billing explanation as proven solely by the runtime error.

Use `Recognizer.recognize(bytes, catalogue)` for both providers. `RecognitionProvider=rekognition` selects `DetectLabels` with only `GENERAL_LABELS`; `bedrock` selects the existing Nova Lite Converse adapter when authorization is resolved. `RecognitionEnabled=false` remains the safe template default. Never fall through to a second provider after an error: an ambiguous call may already be billable.

The scan service still reads/validates S3 bytes once, reserves household/global quota atomically, makes at most one provider call, stores the result, and returns the saved result on repeats. Both providers have SDK retries disabled. The household explicitly confirms the suggested identity; deterministic condition checks still decide the stream. No recognition action adds to a basket or changes pickup state.

## Mapping and limits

The versioned code table maps only specific labels at confidence >=90 to existing catalogue IDs. Confidence is an initial threshold, not measured task accuracy. Different supported item IDs in one response produce `unknown`; aliases for one item agree. Broad labels (Paper, Bottle, Box, Metal) are deliberately omitted. DetectLabels cannot establish cleanliness, exact plastic chemistry, expiry, safe disposal or collector acceptance. Multiple objects, unmapped objects and background labels can still cause mistakes. Household confirmation and held-out evaluation remain necessary. Mapping coverage is deliberately narrower than the manual catalogue.

## IAM exception

AWS's [Rekognition IAM documentation](https://docs.aws.amazon.com/rekognition/latest/dg/security_iam_service-with-iam.html) shows `DetectLabels` using `Resource: "*"`. It does not support an image-resource ARN. Permit exactly `rekognition:DetectLabels`, only with `aws:RequestedRegion=ap-south-1`, only when the enabled provider is Rekognition. Bedrock permissions are absent in that mode. The IAM test rejects any other wildcard-resource action and checks both provider configurations, enabled and disabled.

## Cost evidence

Rekognition uses per-image/request pricing, not Bedrock token pricing. Request-count logs include provider, label-model version and mapping version; request attempts are logged even on failure, without assuming a failed call is free. Use only GENERAL_LABELS; IMAGE_PROPERTIES is not requested. Check the current Mumbai rate before estimating costs. Smaller JPEGs improve upload time/bytes, but do not imply lower DetectLabels per-image charges. Keep daily limits at 5 per household and 50 app-wide, with bounded upload grants.

The user reports $240 promotional credit and $0 used on October 9. This balance has not been independently reconciled; credits, eligible services and expiry do not change gross service cost. Existing $1/$5/$10 budget alerts stay in place. No credit amount is treated as a spending target.
