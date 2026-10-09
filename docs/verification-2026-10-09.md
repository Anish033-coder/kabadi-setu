# Verification — October 9, 2026

- 87 backend tests passed with DynamoDB Local; no skipped integration tests. Five frontend tests and TypeScript/Vite production build passed. Linux arm64 SAM build passed.
- Rekognition synthetic access probe succeeded in Mumbai: LabelModelVersion 3.0, one image request, unknown as expected for a solid-colour fixture.
- Deployed Lambda's policy was read back: the only recognition permission is DetectLabels with Resource * and aws:RequestedRegion=ap-south-1; no Bedrock invocation permission in this mode.
- Hosted synthetic upload/analyze/repeat test succeeded. After the upload-error fix, the same test first called analyze before upload and received the intended 409, then uploaded, received a complete result, and retrieved the identical saved result on repeat. Unit tests explicitly verify no quota reservation or recognition call before upload.
- Amplify deployment succeeded. /r HTTP 200 returned CSP frame-ancestors 'none', X-Frame-Options DENY, no-store, no-referrer and nosniff.
- Browser development-photo test used licensed TrashNet cardboard43.jpg. The app uploaded it, suggested Cardboard boxes, showed Yes/No confirmation, and after confirmation displayed the condition question. No basket item or pickup was automatically added. This was a development example, not another held-out observation.
- Development evaluation: 20 public photos at 256 and 512; 40 API calls. Baseline 11/20 correct and 16/20 unknown at both sizes. Offline replay with mapping .2 improved development counts to 13/20 at 256 and 14/20 at 512; no extra calls.
- Frozen held-out evaluation: 10 public photos at 512; 5/10 correct, 8/10 unresolved; only 2/7 supported items correctly recognised. The other three correct results were expected-unknown negatives. Mapping was not changed after this result. This is a weak, limited benchmark, not household validation.
- Real-phone/mobile-data testing, original Jaipur household photos, timed AI-versus-manual tasks, full cost reconciliation, video, Builder Center blog and submission remain outstanding. No real collector acceptance or physical collection is claimed. No GitHub push or submission tag was made.
