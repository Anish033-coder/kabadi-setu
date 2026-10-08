# Core architecture

The AI names the item. Code decides where it goes. People decide what happens.

One Python backend runs locally and on Lambda. A fixed catalogue bounds recognition; deterministic questions and rules decide guidance. The model has no application tools and cannot add a basket item, create a pickup or change status.

WhatsApp click-to-chat carries a household-reviewed request to a collector. The app does not claim message delivery or verified collection. The recipient uses a request-scoped fragment token with no login; conditional writes and action receipts enforce status transitions. Step Functions would add orchestration without a multi-step background workflow to justify it.

Cognito identifies households; code and Cedar enforce ownership and request-scoped actions. Private S3 photos are validated from one bounded read. DynamoDB quota reservations precede model calls. Manual search remains available when recognition is unavailable or uncertain.
