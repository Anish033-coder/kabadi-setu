# Retrying a decision after a lost response

A collector may tap Accept, lose the response, then try again. The request ID, version and action now select the same browser-generated action ID for that page session. The backend stores an action receipt with the status/history transaction. Repeating that action returns its saved result; a competing cancel still cannot overwrite a completed acceptance using an old version.

DynamoDB transaction contention is different from a failed version condition. The repository retries only a transaction-conflict cancellation, at most three additional times with short jittered waits. It sends identical operations and the same transaction token. A failed condition becomes 409; prolonged contention becomes 503; unrelated errors are not disguised as conflicts. Tests cover those categories and actual DynamoDB Local races.

Action IDs stay in memory: a full reload refreshes the request status rather than persisting secret-bearing payloads. We do not promise offline delivery or recovery after closing the page.

Cognito refresh retries the original request with the same body/action ID. A rejected refresh clears in-memory credentials and returns the household to login. A network error preserves the session so a temporary outage does not force a new login. Concurrent expiry shares one refresh request.

Reference: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.html
