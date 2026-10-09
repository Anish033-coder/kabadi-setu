# AI versus manual trials

Open the app with `?trial=1`, sign in, and choose **developer trial** or **household trial**. The panel is opt-in. Start the assigned method before selecting an item or a photo. Finish only after the participant confirms the displayed route; otherwise record an aborted trial. Export JSON before refreshing or closing: records are kept only in page memory, up to 100 trials, with no server upload.

Use the same items for both methods and alternate which method comes first. Keep development and household results separate. Record every attempt, including unknown suggestions and manual fallback, rather than discarding slower failures. Do not label an automated browser check as a household trial or as physical-phone testing.

Each record contains trial type, assigned method, observed method (photo / photo + question / manual), elapsed milliseconds, in-app taps, correction events, manual fallback and completion/abort outcome. It contains no names, item IDs, free text, photos, account IDs or timestamps. The clock includes time in the file picker/camera, but taps outside the web page are not observable. The final confirmation tap is counted; the start tap is excluded.

A correction event is an explicit rejection of a photo suggestion, a change to a previously selected item, or a changed condition answer. These count interactions, not independently verified model errors. Report raw trial counts, completion counts and individual or median timings. Do not claim an AI speed advantage until real paired trials support it. No trial results have yet been collected by this tooling.
