// Tokens stay in memory. A reload requires sign-in; pickup links use their own token.
export function createApi({
  endpoint,
  region,
  clientId,
  onSessionExpired,
  fetcher = fetch,
}) {
  let accessToken = "",
    refreshToken = "",
    renewal = null;

  function setSession(session) {
    accessToken = session.AccessToken || "";
    refreshToken = session.RefreshToken || "";
  }

  function cognito(action, payload) {
    return fetcher(`https://cognito-idp.${region}.amazonaws.com/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": `AWSCognitoIdentityProviderService.${action}`,
      },
      body: JSON.stringify(payload),
    });
  }

  async function renew() {
    if (!refreshToken) return false;
    // Several requests can discover expiry together. Share a single refresh call.
    if (!renewal)
      renewal = (async () => {
        const response = await cognito("InitiateAuth", {
          ClientId: clientId,
          AuthFlow: "REFRESH_TOKEN_AUTH",
          AuthParameters: { REFRESH_TOKEN: refreshToken },
        });
        const result = await response.json();
        if (!response.ok || !result.AuthenticationResult?.AccessToken)
          return false;
        accessToken = result.AuthenticationResult.AccessToken;
        return true;
      })().finally(() => {
        renewal = null;
      });
    return renewal;
  }

  async function api(path, body, key) {
    const send = () =>
      fetcher(endpoint + "/api" + path, {
        method: body === undefined ? "GET" : "POST",
        credentials: endpoint ? "omit" : "same-origin",
        headers: {
          "Content-Type": "application/json",
          ...(key ? { "Idempotency-Key": key } : {}),
          ...(accessToken ? { Authorization: "Bearer " + accessToken } : {}),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    let response = await send();
    if (endpoint && response.status === 401) {
      if (await renew()) response = await send();
      if (response.status === 401) {
        setSession({});
        onSessionExpired();
        throw new Error("Your session expired. Sign in again to continue.");
      }
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok)
      throw new Error(data.error || "Request failed. Please try again.");
    return data;
  }
  return { api, cognito, setSession };
}

export function actionIds() {
  const pending = new Map();
  return {
    get(id, version, action) {
      const operation = JSON.stringify([id, version, action]);
      if (!pending.has(operation)) pending.set(operation, crypto.randomUUID());
      return pending.get(operation);
    },
  };
}
