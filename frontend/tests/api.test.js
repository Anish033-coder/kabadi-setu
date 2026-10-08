import test from "node:test";
import assert from "node:assert/strict";
import { createApi, actionIds } from "../src/api.js";

const response = (status, data = {}) =>
  new Response(JSON.stringify(data), { status });
function setup(fetcher) {
  let expired = 0;
  const client = createApi({
    endpoint: "https://example.test",
    region: "ap-south-1",
    clientId: "test",
    fetcher,
    onSessionExpired: () => expired++,
  });
  client.setSession({ AccessToken: "old", RefreshToken: "refresh" });
  return { ...client, expired: () => expired };
}

test("refresh retries the identical action with a new access token", async () => {
  const calls = [],
    replies = [
      response(401),
      response(200, { AuthenticationResult: { AccessToken: "new" } }),
      response(200, { version: 2 }),
    ];
  const client = setup(async (url, options) => {
    calls.push({ url, ...options });
    return replies.shift();
  });
  assert.deepEqual(
    await client.api("/pickup/action", { action: "accept" }, "same-action"),
    { version: 2 },
  );
  assert.equal(calls[0].body, calls[2].body);
  assert.equal(calls[2].headers["Idempotency-Key"], "same-action");
  assert.equal(calls[2].headers.Authorization, "Bearer new");
  assert.equal(client.expired(), 0);
});

test("rejected refresh returns the household to sign-in", async () => {
  const replies = [response(401), response(400)];
  const client = setup(async () => replies.shift());
  await assert.rejects(client.api("/basket"), /Sign in again/);
  assert.equal(client.expired(), 1);
});

test("network failure during refresh keeps session available for retry", async () => {
  let calls = 0;
  const client = setup(async () => {
    if (++calls === 1) return response(401);
    throw new TypeError("offline");
  });
  await assert.rejects(client.api("/basket"), /offline/);
  assert.equal(client.expired(), 0);
});

test("second unauthorized response stops rather than looping", async () => {
  const replies = [
    response(401),
    response(200, { AuthenticationResult: { AccessToken: "new" } }),
    response(401),
  ];
  const client = setup(async () => replies.shift());
  await assert.rejects(client.api("/basket"), /Sign in again/);
  assert.equal(replies.length, 0);
  assert.equal(client.expired(), 1);
});

test("retry keeps its ID; another decision or version gets a different ID", () => {
  const ids = actionIds();
  assert.equal(
    ids.get("request", 1, "accept"),
    ids.get("request", 1, "accept"),
  );
  assert.notEqual(
    ids.get("request", 1, "accept"),
    ids.get("request", 1, "reject"),
  );
  assert.notEqual(
    ids.get("request", 1, "accept"),
    ids.get("request", 2, "collect"),
  );
});
