import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";
import { createApi, actionIds } from "./api.js";

import type { Item, Row, RequestRecord, Route } from "./types";
import { RequestView } from "./components/RequestView";
import { PhotoScan } from "./components/PhotoScan";
import { TrialPanel } from "./components/TrialPanel";
import { createTrial } from "./trials.js";
const env = (import.meta as any).env;
const endpoint = env.VITE_API_URL || "";
const client = createApi({
  endpoint,
  region: env.VITE_AWS_REGION,
  clientId: env.VITE_COGNITO_CLIENT_ID,
  onSessionExpired: () => window.dispatchEvent(new Event("session-expired")),
});
const { api, cognito } = client;
function Icon({ kind = "leaf" }: { kind?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <g
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {kind === "paper" ? (
          <>
            <path d="M8 5h13l4 4v18H8zM21 5v5h4M12 14h9M12 18h9M12 22h6" />
          </>
        ) : kind === "box" ? (
          <>
            <path d="m4 11 12-6 12 6v15H4zM4 11l12 6 12-6M16 17v9M10 8l12 6" />
          </>
        ) : kind === "bottle" ? (
          <>
            <path d="M13 4h6v7l4 5v11H9V16l4-5zM13 8h6M9 19h14" />
          </>
        ) : kind === "can" ? (
          <>
            <ellipse cx="16" cy="7" rx="8" ry="3" />
            <path d="M8 7v18c0 4 16 4 16 0V7M12 12v11M20 12v11" />
          </>
        ) : kind === "care" ? (
          <>
            <path d="m16 4 13 23H3zM16 12v7M16 23h.01" />
          </>
        ) : (
          <>
            <path d="M26 5C8 3 4 11 8 21c10 4 18-2 18-16ZM6 27 22 10M12 20v-7M17 15h6" />
          </>
        )}
      </g>
    </svg>
  );
}
const names: Record<string, [string, string]> = {
  awaiting_response: ["Awaiting response", "जवाब की प्रतीक्षा"],
  accepted: ["Accepted", "स्वीकार किया"],
  rejected: ["Declined", "मना किया"],
  cancelled: ["Cancelled", "रद्द किया"],
  expired: ["Expired", "समय समाप्त"],
  collection_reported: ["Collection reported", "संग्रह की सूचना"],
  wet: ["Wet waste", "गीला कचरा"],
  dry: ["Dry waste", "सूखा कचरा"],
  sanitary: ["Sanitary waste", "सैनिटरी कचरा"],
  special_care: ["Special care", "विशेष देखभाल"],
  e_waste: ["E-waste", "ई-कचरा"],
  unresolved: ["Needs a closer look", "और जाँच ज़रूरी"],
};
function App() {
  const [lang, setLang] = useState<"en" | "hi">(
    location.pathname === "/r" ? "hi" : "en",
  );
  const t = (en: string, hi: string) => (lang === "en" ? en : hi);
  const [items, setItems] = useState<Item[]>([]),
    [basket, setBasket] = useState<Row[]>([]),
    [search, setSearch] = useState(""),
    [group, setGroup] = useState("All");
  const [chosen, setChosen] = useState<Item | null>(null),
    [condition, setCondition] = useState(""),
    [route, setRoute] = useState<Route | null>(null);
  const chosenId = useRef("");
  const sheetHeading = useRef<HTMLHeadingElement>(null);
  const [justAdded, setJustAdded] = useState("");
  const [tab, setTab] = useState("sort"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const [request, setRequest] = useState<RequestRecord | null>(null),
    [phone, setPhone] = useState(""),
    [consent, setConsent] = useState(false);
  const [mode, setMode] = useState("loading"),
    [signedIn, setSignedIn] = useState(!endpoint),
    [authMode, setAuthMode] = useState("login");
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [code, setCode] = useState("");
  const [requestIds, setRequestIds] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("ks-requests") || "[]");
    } catch {
      return [];
    }
  });
  const trialEnabled = new URLSearchParams(location.search).get("trial") === "1";
  const trial = useRef(createTrial());
  const [, refreshTrial] = useState(0);
  const [trialRun, setTrialRun] = useState(0);
  const trialState = trial.current.snapshot();
  function trialChanged() { refreshTrial((n) => n + 1); }
  const [recognitionEnabled, setRecognitionEnabled] = useState(false);
  const [recognitionProvider, setRecognitionProvider] = useState("");
  const [householdKey, setHouseholdKey] = useState(endpoint ? "" : "local");
  const [usual, setUsual] = useState<string[]>([]);
  const [shortcutCount, setShortcutCount] = useState(0);
  useEffect(() => {
    if (!householdKey) return;
    try {
      const saved = JSON.parse(
        localStorage.getItem(householdKey + ":usual") || "[]",
      );
      setUsual(
        Array.isArray(saved)
          ? saved.filter((x) => typeof x === "string").slice(0, 30)
          : [],
      );
      setPhone(localStorage.getItem(householdKey + ":collector") || "");
      setShortcutCount(
        Number(localStorage.getItem(householdKey + ":shortcuts")) || 0,
      );
    } catch {
      setUsual([]);
    }
  }, [householdKey]);
  const createKey = useRef(crypto.randomUUID());
  const pendingActions = useRef(actionIds());
  const linkState = useRef(new URLSearchParams(location.hash.slice(1)));
  const recipient = location.pathname === "/r";
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  useEffect(() => {
    const expired = () => {
      setSignedIn(false);
      setAuthMode("login");
      setBasket([]);
      setRequest(null);
      setError("Your session expired. Sign in again to continue.");
    };
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, []);
  useEffect(() => {
    api("/health")
      .then((x) => {
        setMode(x.mode);
        setRecognitionEnabled(x.recognition === "enabled");
        setRecognitionProvider(x.recognition_provider || "");
      })
      .catch(() => setMode("unavailable"));
    api("/catalogue")
      .then((x) => setItems(x.items))
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (signedIn && !recipient)
      api("/basket")
        .then((x) => setBasket(x.items))
        .catch((e) => setError(e.message));
  }, [signedIn]);
  useEffect(() => {
    if (recipient)
      run(async () =>
        setRequest(
          await api("/pickup/view", {
            id: linkState.current.get("id"),
            token: linkState.current.get("t"),
          }),
        ),
      );
  }, []);
  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Please try again.");
    } finally {
      setBusy(false);
    }
  }
  async function auth() {
    await run(async () => {
      const region = env.VITE_AWS_REGION,
        clientId = env.VITE_COGNITO_CLIENT_ID;
      if (!region || !clientId)
        throw new Error("Cloud sign-in is not configured yet.");
      const action =
        authMode === "signup"
          ? "SignUp"
          : authMode === "verify"
            ? "ConfirmSignUp"
            : "InitiateAuth";
      const payload =
        authMode === "signup"
          ? {
              ClientId: clientId,
              Username: email,
              Password: password,
              UserAttributes: [{ Name: "email", Value: email }],
            }
          : authMode === "verify"
            ? { ClientId: clientId, Username: email, ConfirmationCode: code }
            : {
                ClientId: clientId,
                AuthFlow: "USER_PASSWORD_AUTH",
                AuthParameters: { USERNAME: email, PASSWORD: password },
              };
      const response = await cognito(action, payload);
      const result = await response.json();
      if (!response.ok) throw new Error(result.message || "Sign-in failed.");
      if (authMode === "signup") {
        setAuthMode("verify");
        setNotice("Check your email for the verification code.");
      } else if (authMode === "verify") {
        setAuthMode("login");
        setNotice("Email verified. You can sign in.");
      } else {
        if (!result.AuthenticationResult?.AccessToken)
          throw new Error("This account needs an additional sign-in step.");
        client.setSession(result.AuthenticationResult);
        setHouseholdKey("ks:" + email.trim().toLowerCase());
        setSignedIn(true);
        setPassword("");
      }
    });
  }
  useEffect(() => {
    // On phones the check panel is a bottom sheet: keep the list still behind it.
    document.body.classList.toggle("sheet-open", !!chosen);
    if (!chosen) return;
    sheetHeading.current?.focus({ preventScroll: true });
    const close = (e: KeyboardEvent) => e.key === "Escape" && setChosen(null);
    addEventListener("keydown", close);
    return () => removeEventListener("keydown", close);
  }, [chosen]);
  useEffect(() => {
    if (!justAdded) return;
    const timer = setTimeout(() => setJustAdded(""), 2500);
    return () => clearTimeout(timer);
  }, [justAdded]);
  function select(item: Item, source = "manual") {
    chosenId.current = item.id;
    trial.current.select(item.id, source);
    setChosen(item);
    setCondition("");
    setRoute(null);
    setError("");
    // Nothing to check by eye: show the rules' guidance straight away.
    if (!item.check_clean) void decide("unsure", item);
  }
  async function decide(value: string, item = chosen) {
    trial.current.condition(value);
    setCondition(value);
    if (item)
      await run(async () => {
        const next = await api("/decide", { id: item.id, answers: { clean: value } });
        // Ignore a slow answer for an item the person has already moved away from.
        if (chosenId.current === item.id) setRoute(next);
      });
  }
  async function updateBasket(next: Row[]) {
    await run(async () => {
      const saved = await api("/basket", { items: next });
      setBasket(saved.items);
      createKey.current = crypto.randomUUID();
    });
  }
  async function add() {
    if (!chosen || !route?.eligible) return;
    const existing = basket.find((i) => i.id === chosen.id);
    if (existing) {
      setNotice(
        t(
          "Already in your basket. Adjust the count there.",
          "पहले से टोकरी में है। वहीं मात्रा बदलें।",
        ),
      );
      return;
    }
    await run(async () => {
      const saved = await api("/basket", {
        items: [
          ...basket,
          {
            id: chosen.id,
            en: chosen.en,
            hi: chosen.hi,
            quantity: 1,
            answers: { clean: condition },
          },
        ],
      });
      setBasket(saved.items);
      createKey.current = crypto.randomUUID();
      const next = [chosen.id, ...usual.filter((id) => id !== chosen.id)].slice(
        0,
        30,
      );
      setUsual(next);
      try {
        localStorage.setItem(householdKey + ":usual", JSON.stringify(next));
      } catch {
        /* Saving preferences is optional. */
      }
      setChosen(null);
      setJustAdded(t(chosen.en, chosen.hi));
      setNotice(t("Added to your basket.", "टोकरी में जोड़ दिया।"));
    });
  }

  async function create() {
    await run(async () => {
      const result = await api(
        "/requests",
        { items: basket, language: lang },
        createKey.current,
      );
      setRequest(result);
      setTab("request");
      const ids = [result.id, ...requestIds.filter((id) => id !== result.id)];
      setRequestIds(ids);
      localStorage.setItem("ks-requests", JSON.stringify(ids));
      setConsent(false);
    });
  }
  async function action(action: string) {
    if (!request) return;
    await run(async () => {
      const key = pendingActions.current.get(
        request.id,
        request.version,
        action,
      );
      setRequest(
        await api(
          recipient ? "/pickup/action" : `/requests/${request.id}/actions`,
          {
            id: request.id,
            token: recipient ? linkState.current.get("t") : undefined,
            action,
            version: request.version,
          },
          key,
        ),
      );
    });
  }
  async function refresh() {
    if (!request) return;
    await run(async () =>
      setRequest(
        recipient
          ? await api("/pickup/view", {
              id: request.id,
              token: linkState.current.get("t"),
            })
          : await api(`/requests/${request.id}`),
      ),
    );
  }
  const link = request?.token
    ? `${location.origin}/r#id=${request.id}&t=${request.token}`
    : "";
  const message = request
    ? [
        t(
          "Hello! I have these clean, dry scrap items in Jaipur:",
          "नमस्ते! जयपुर में मेरे पास यह साफ़ और सूखा कबाड़ है:",
        ),
        ...request.items.map(
          (i) => `• ${lang === "en" ? i.en : i.hi} × ${i.quantity}`,
        ),
        t(
          "Counts are estimates. Do you take these items? Please confirm rates and a suitable time. We can arrange the address in this chat.",
          "मात्रा अनुमानित है। क्या आप ये चीज़ें लेते हैं? कृपया दर और समय बताएँ। पता इसी चैट में तय करेंगे।",
        ),
        link ? t("View and respond: ", "अनुरोध देखें: ") + link : "",
      ]
        .filter(Boolean)
        .join("\n")
    : "";
  const digits = phone.replace(/[\s()+-]/g, "");
  const validPhone = /^[1-9]\d{7,14}$/.test(digits);
  const visible = items.filter(
    (i) =>
      (group === "All" || i.group === group) &&
      `${i.en} ${i.hi}`.toLowerCase().includes(search.toLowerCase()),
  );
  const label = (value: string) =>
    names[value]?.[lang === "en" ? 0 : 1] || value;
  return (
    <div className="app">
      <header>
        <a className="brand" href="/">
          <span className="brand-icon">
            <Icon />
          </span>
          Kabadi<span>Setu</span>
          <small>कबाड़ी सेतु</small>
        </a>
        <div className="header-right">
          <span className="locality">
            ● {t("Jaipur · prototype", "जयपुर · प्रोटोटाइप")}
          </span>
          <button
            className="language"
            onClick={() => setLang(lang === "en" ? "hi" : "en")}
          >
            {lang === "en" ? "हिन्दी" : "English"} <span>↔</span>
          </button>
        </div>
      </header>
      <div className="environment">
        {mode === "local"
          ? t(
              "LOCAL TEST · No AWS calls. Pickup links work only on this computer.",
              "स्थानीय परीक्षण · AWS कॉल नहीं। लिंक केवल इसी कंप्यूटर पर काम करते हैं।",
            )
          : mode === "aws"
            ? t(
                "PROTOTYPE · Collector acceptance and physical collection are unverified.",
                "प्रोटोटाइप · कबाड़ी की स्वीकृति और वास्तविक संग्रह की पुष्टि नहीं हुई है।",
              )
            : t("Connecting to the application…", "ऐप से जुड़ रहे हैं…")}
      </div>
      {!recipient && (
        <nav aria-label="Main navigation">
          {[
            ["sort", "01", t("Sort an item", "सामान छाँटें")],
            ["basket", "02", t("Your basket", "आपकी टोकरी")],
            ["request", "03", t("Pickup requests", "अनुरोध")],
          ].map(([id, n, title]) => (
            <button
              className={tab === id ? "active" : ""}
              key={id}
              onClick={() => setTab(id)}
            >
              <span>{n}</span>
              {title}
              {id === "basket" && <b>{basket.length}</b>}
            </button>
          ))}
        </nav>
      )}
      <main onClickCapture={() => { if (trialEnabled) trial.current.tap(); }}>
        {trialEnabled && signedIn && !recipient && <TrialPanel
          active={trialState.active} results={trialState.results} hasRoute={!!route}
          onStart={(type, method) => {
            trial.current.start(type, method); setChosen(null); setRoute(null); setCondition("");
            setTab("sort"); setTrialRun((n) => n + 1); trialChanged();
          }}
          onFinish={() => { trial.current.finish(!!route); trialChanged(); }}
          onAbort={() => { trial.current.abort(); trialChanged(); }}
        />}
        <div role="alert" className={error ? "alert error" : "hidden"}>
          {error}
        </div>
        <div role="status" className={notice ? "alert" : "hidden"}>
          {notice}
        </div>
        {!signedIn && !recipient ? (
          <section className="panel login">
            <p className="eyebrow">YOUR HOUSEHOLD, YOUR BASKET</p>
            <h1>
              {authMode === "signup"
                ? "Create your account"
                : authMode === "verify"
                  ? "Verify your email"
                  : "Welcome back."}
            </h1>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                auth();
              }}
            >
              <label>
                Email
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>
              {authMode === "verify" ? (
                <label>
                  Verification code
                  <input
                    required
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                  />
                </label>
              ) : (
                <label>
                  Password
                  <input
                    type="password"
                    required
                    minLength={12}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </label>
              )}
              <button className="primary" disabled={busy}>
                Continue →
              </button>
            </form>
            <button
              className="text-button"
              onClick={() =>
                setAuthMode(authMode === "login" ? "signup" : "login")
              }
            >
              {authMode === "login"
                ? "New here? Create an account"
                : "Back to sign in"}
            </button>
          </section>
        ) : recipient ? (
          <section className="request-layout">
            <div>
              <p className="eyebrow">
                {t("PICKUP REQUEST", "कबाड़ लेने का अनुरोध")}
              </p>
              <h1>
                {t(
                  "A little scrap.\nA useful next stop.",
                  "थोड़ा कबाड़।\nएक उपयोगी अगला कदम।",
                )}
              </h1>
              <p className="intro">
                {t(
                  "Review the items below. Arrange rates, location and timing directly in your WhatsApp conversation.",
                  "सामान देखें। दर, पता और समय अपनी WhatsApp चैट में तय करें।",
                )}
              </p>
            </div>
            {request && (
              <RequestView
                request={request}
                recipient
                busy={busy}
                label={label}
                t={t}
                action={action}
                refresh={refresh}
              />
            )}
          </section>
        ) : tab === "sort" ? (
          <>
            <section className="hero">
              <div>
                <p className="eyebrow">
                  {t(
                    "SMALL HABITS. LESS MIXED WASTE.",
                    "छोटी आदतें। कम मिला-जुला कचरा।",
                  )}
                </p>
                <h1>
                  {t(
                    "Give your scrap\na better next stop.",
                    "अपने कबाड़ को\nसही जगह पहुँचाएँ।",
                  )}
                </h1>
                <p className="intro">
                  {t(
                    "Know what goes where. Keep the useful things together. Ask your kabadiwala when they can collect.",
                    "जानें क्या कहाँ जाएगा। उपयोगी सामान अलग रखें। अपने कबाड़ी से लेने का समय पूछें।",
                  )}
                </p>
                <div className="hero-notes">
                  <span>✓ {t("Simple sorting", "आसान छँटाई")}</span>
                  <span>✓ {t("Your own WhatsApp", "आपका WhatsApp")}</span>
                </div>
              </div>
              <div className="illustration" aria-hidden="true">
                <span className="orbit">↗</span>
                <div className="scrap paper">
                  <Icon kind="paper" />
                </div>
                <div className="scrap bottle">
                  <Icon kind="bottle" />
                </div>
                <div className="scrap box">
                  <Icon kind="box" />
                </div>
                <div className="basket-art">
                  <span>कबाड़ी सेतु</span>
                  <strong>
                    GOOD THINGS
                    <br />
                    GO AROUND.
                  </strong>
                </div>
                <span className="art-note">sort today. save for later.</span>
              </div>
            </section>
            <section className="workspace">
              <div className="catalogue panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">
                      {t("START WITH ONE ITEM", "एक सामान से शुरू करें")}
                    </p>
                    <h2>
                      {t("What are you sorting?", "आप क्या छाँट रहे हैं?")}
                    </h2>
                  </div>
                  <span className="count">
                    {items.length} {t("items", "वस्तुएँ")}
                  </span>
                </div>
                <label className="search">
                  <span>⌕</span>
                  <input
                    aria-label={t("Search items", "सामान खोजें")}
                    placeholder={t(
                      "Try newspaper, bottle, battery…",
                      "अख़बार, बोतल, बैटरी खोजें…",
                    )}
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </label>
                <div className="filters">
                  {["All", "Paper", "Plastic", "Metal", "Glass", "Other"].map(
                    (g, i) => (
                      <button
                        key={g}
                        className={group === g ? "selected" : ""}
                        onClick={() => setGroup(g)}
                      >
                        {t(
                          g,
                          ["सभी", "कागज़", "प्लास्टिक", "धातु", "काँच", "अन्य"][
                            i
                          ],
                        )}
                      </button>
                    ),
                  )}
                </div>
                <div className="item-grid">
                  {visible.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => select(item)}
                      className={
                        "item-card " + (chosen?.id === item.id ? "chosen" : "")
                      }
                    >
                      <span className={"item-icon " + item.group.toLowerCase()}>
                        <Icon kind={item.icon} />
                      </span>
                      <strong>{lang === "en" ? item.en : item.hi}</strong>
                      {basket.some((row) => row.id === item.id) && (
                        <small className="in-basket">
                          ✓ {t("In basket", "टोकरी में")}
                        </small>
                      )}
                      <span className="item-arrow">↗</span>
                    </button>
                  ))}
                </div>
                {!visible.length && (
                  <p>
                    {t(
                      "No matching item. Choose “Something else / unsure”.",
                      "सामान नहीं मिला। “कुछ और / पता नहीं” चुनें।",
                    )}
                  </p>
                )}
              </div>
              <aside>
                {usual.length > 0 && (
                  <section className="panel usual-items">
                    <h2>{t("Your usual items", "आपका नियमित सामान")}</h2>
                    {usual
                      .map((id) => items.find((i) => i.id === id))
                      .filter((i): i is Item => !!i)
                      .map((item) => (
                        <button
                          className="secondary"
                          key={item.id}
                          onClick={() => {
                            select(item);
                            const count = shortcutCount + 1;
                            setShortcutCount(count);
                            try {
                              localStorage.setItem(
                                householdKey + ":shortcuts",
                                String(count),
                              );
                            } catch {}
                          }}
                        >
                          {lang === "hi" ? item.hi : item.en}
                        </button>
                      ))}
                    <p className="fine">
                      {shortcutCount}{" "}
                      {t(
                        "shortcut selections on this browser; no model calls for these. Check condition each time.",
                        "बार इस ब्राउज़र पर शॉर्टकट चुना; इनमें AI कॉल नहीं हुई। हर बार स्थिति जाँचें।",
                      )}
                    </p>
                  </section>
                )}

                {chosen ? (
                  <>
                  <div
                    className="sheet-backdrop"
                    onClick={() => setChosen(null)}
                  />
                  <section
                    className="panel review"
                    aria-labelledby="review-heading"
                  >
                    <button
                      className="sheet-close"
                      aria-label={t("Close", "बंद करें")}
                      onClick={() => setChosen(null)}
                    >
                      ×
                    </button>
                    <p className="eyebrow">
                      {t("CHECK BEFORE YOU ADD", "जोड़ने से पहले जाँचें")}
                    </p>
                    <h2 id="review-heading" ref={sheetHeading} tabIndex={-1}>
                      {lang === "en" ? chosen.en : chosen.hi}
                    </h2>
                    {chosen.check_clean ? (
                      <>
                        <p>
                          {t(
                            "Is it empty, clean and dry? Only select yes if it did not contain hazardous material.",
                            "क्या यह खाली, साफ़ और सूखा है? खतरनाक सामग्री थी तो हाँ न चुनें।",
                          )}
                        </p>
                        <div className="answers">
                          {[
                            ["yes", "Yes", "हाँ"],
                            ["no", "No", "नहीं"],
                            ["unsure", "Unsure", "पता नहीं"],
                          ].map(([v, en, hi]) => (
                            <button
                              disabled={busy}
                              className={condition === v ? "selected" : ""}
                              onClick={() => decide(v)}
                              key={v}
                            >
                              {t(en, hi)}
                            </button>
                          ))}
                        </div>
                      </>
                    ) : (
                      !route && <p>{t("Checking the rules…", "नियम देख रहे हैं…")}</p>
                    )}
                    {route && (
                      <div
                        className={
                          "guidance " + (route.eligible ? "positive" : "")
                        }
                      >
                        <span className="eyebrow">{label(route.stream)}</span>
                        {!route.eligible && (
                          <strong>
                            {chosen.check_clean
                              ? t("Not ready for the basket", "अभी टोकरी के लिए नहीं")
                              : t("Not for the scrap basket", "कबाड़ टोकरी के लिए नहीं")}
                          </strong>
                        )}
                        <p>{lang === "en" ? route.reason : route.reason_hi}</p>
                        {route.eligible &&
                          (basket.some((row) => row.id === chosen.id) ? (
                            <button
                              className="secondary"
                              onClick={() => {
                                setChosen(null);
                                setTab("basket");
                              }}
                            >
                              ✓ {t("Already in your basket · View", "पहले से टोकरी में · देखें")}
                            </button>
                          ) : (
                            <button
                              className="primary"
                              disabled={busy}
                              onClick={add}
                            >
                              {t("Add to basket", "टोकरी में जोड़ें")} +
                            </button>
                          ))}
                      </div>
                    )}
                    <button
                      className="text-button"
                      onClick={() => setChosen(null)}
                    >
                      {t("Choose a different item", "दूसरा सामान चुनें")}
                    </button>
                  </section>
                  </>
                ) : (
                  <section className="panel how">
                    <div className="round-leaf">
                      <Icon />
                    </div>
                    <h2>
                      {t(
                        "A basket,\nnot a mixed bin.",
                        "एक टोकरी,\nमिला-जुला कचरा नहीं।",
                      )}
                    </h2>
                    <p>
                      {t(
                        "Choose an item to see where it belongs. Only suitable, confirmed items can join your pickup basket.",
                        "सामान चुनकर उसका सही तरीका जानें। केवल उपयुक्त और जाँचा हुआ सामान टोकरी में जोड़ें।",
                      )}
                    </p>
                    <ol>
                      <li>{t("Identify and check", "पहचानें और जाँचें")}</li>
                      <li>{t("Keep it separate", "अलग रखें")}</li>
                      <li>{t("Ask before pickup", "लेने से पहले पूछें")}</li>
                    </ol>
                  </section>
                )}
                <PhotoScan
                  key={trialRun}
                  enabled={recognitionEnabled}
                  provider={recognitionProvider}
                  itemName={(id) => {
                    const item = items.find((i) => i.id === id);
                    return item ? t(item.en, item.hi) : id;
                  }}
                  t={t}
                  api={api}
                  onPhotoStart={() => trial.current.photo()}
                  onQuestion={() => trial.current.question()}
                  onCorrection={() => trial.current.correction()}
                  onSuggestion={(id) => {
                    const item = items.find((i) => i.id === id);
                    if (item) {
                      select(item, "photo");
                      setNotice(
                        t(
                          "Item chosen. Now check its condition.",
                          "सामान चुना गया। अब उसकी स्थिति जाँचें।",
                        ),
                      );
                    }
                  }}
                />
              </aside>
            </section>
            {basket.length > 0 && !chosen && (
              <button className="basket-bar" onClick={() => setTab("basket")}>
                <span>
                  {justAdded
                    ? `✓ ${justAdded} ${t("added", "जोड़ा गया")}`
                    : `${basket.length} ${t(basket.length === 1 ? "item in basket" : "items in basket", "सामान टोकरी में")}`}
                </span>
                <span>{t("View basket", "टोकरी देखें")} →</span>
              </button>
            )}
          </>
        ) : tab === "basket" ? (
          <section className="basket-layout">
            <div>
              <p className="eyebrow">
                {t("SET ASIDE, READY TO ASK", "अलग रखा, पूछने के लिए तैयार")}
              </p>
              <h1>{t("Your little\ncollection.", "आपका छोटा\nसंग्रह।")}</h1>
              <p className="intro">
                {t(
                  "Counts are estimates, not weights. Your collector confirms acceptance, rates and the final amount.",
                  "ये अनुमानित गिनती हैं, वजन नहीं। कबाड़ी स्वीकृति, दर और अंतिम राशि बताएँगे।",
                )}
              </p>
              <button className="text-button" onClick={() => setTab("sort")}>
                ← {t("Add more items", "और सामान जोड़ें")}
              </button>
            </div>
            <section className="panel">
              {!basket.length ? (
                <div className="empty">
                  <Icon kind="box" />
                  <h2>{t("Start with one item.", "एक सामान से शुरू करें।")}</h2>
                  <p>{t("Your basket is empty.", "आपकी टोकरी खाली है।")}</p>
                  <button className="primary" onClick={() => setTab("sort")}>
                    {t("Find an item", "सामान खोजें")} →
                  </button>
                </div>
              ) : (
                <>
                  <h2>{t("Saved for pickup", "उठवाने के लिए रखा")}</h2>
                  {basket.map((row) => (
                    <div className="basket-row" key={row.id}>
                      <div>
                        <strong>{lang === "en" ? row.en : row.hi}</strong>
                        <small>
                          {t(
                            "Clean & dry · estimated count",
                            "साफ़ और सूखा · अनुमानित गिनती",
                          )}
                        </small>
                      </div>
                      <input
                        aria-label={`${row.en} count`}
                        type="number"
                        min={1}
                        max={99}
                        value={row.quantity}
                        disabled={busy}
                        onChange={(e) => {
                          const q = Number(e.target.value);
                          if (q >= 1 && q <= 99)
                            updateBasket(
                              basket.map((i) =>
                                i.id === row.id ? { ...i, quantity: q } : i,
                              ),
                            );
                        }}
                      />
                      <button
                        aria-label={"Remove " + row.en}
                        className="remove"
                        disabled={busy}
                        onClick={() =>
                          updateBasket(basket.filter((i) => i.id !== row.id))
                        }
                      >
                        ×
                      </button>
                    </div>
                  ))}
                  <div className="quote-note">
                    {t(
                      "Rates and minimums are unknown. We’ll prepare a quote request, not promise a sale.",
                      "दर और न्यूनतम मात्रा अज्ञात हैं। हम दर पूछने का अनुरोध बनाएँगे, बिक्री का वादा नहीं।",
                    )}
                  </div>
                  <button
                    className="primary wide"
                    onClick={create}
                    disabled={busy}
                  >
                    {busy
                      ? t("Saving…", "सहेज रहे हैं…")
                      : t("Prepare pickup request", "अनुरोध तैयार करें")}{" "}
                    →
                  </button>
                </>
              )}
            </section>
          </section>
        ) : (
          <section>
            <div className="section-heading">
              <div>
                <p className="eyebrow">
                  {t("KEEP THE LOOP VISIBLE", "अनुरोध की स्थिति जानें")}
                </p>
                <h1>{t("Pickup requests.", "कबाड़ लेने के अनुरोध।")}</h1>
              </div>
            </div>
            {request ? (
              <div className="request-columns">
                <RequestView
                  request={request}
                  busy={busy}
                  label={label}
                  t={t}
                  action={action}
                  refresh={refresh}
                />
                <section className="panel">
                  <h2>{t("Review, then send.", "देखें, फिर भेजें।")}</h2>
                  {link ? (
                    <>
                      <label>
                        {t(
                          "Collector’s WhatsApp number",
                          "कबाड़ी का WhatsApp नंबर",
                        )}
                        <input
                          inputMode="tel"
                          placeholder="91…"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                        />
                      </label>
                      <small>
                        {t(
                          "Include country code. This number is not saved on our server.",
                          "देश कोड जोड़ें। यह नंबर सर्वर पर नहीं सहेजा जाएगा।",
                        )}
                      </small>
                      <button
                        className="secondary"
                        disabled={!validPhone}
                        onClick={() => {
                          try {
                            localStorage.setItem(
                              householdKey + ":collector",
                              digits,
                            );
                            setNotice(
                              t(
                                "Collector saved on this browser.",
                                "कबाड़ी का नंबर इस ब्राउज़र पर सहेजा गया।",
                              ),
                            );
                          } catch {
                            setError(
                              t(
                                "Could not save on this browser.",
                                "इस ब्राउज़र पर सहेजा नहीं जा सका।",
                              ),
                            );
                          }
                        }}
                      >
                        {t("Save this kabadiwala", "इस कबाड़ी का नंबर सहेजें")}
                      </button>
                      <pre className="message">{message}</pre>
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={consent}
                          onChange={(e) => setConsent(e.target.checked)}
                        />
                        {t(
                          "I reviewed the recipient and message. Sending from WhatsApp shares my number with them.",
                          "मैंने प्राप्तकर्ता और संदेश जाँचा है। WhatsApp से भेजने पर मेरा नंबर उन्हें दिखेगा।",
                        )}
                      </label>
                      {mode === "aws" && validPhone && consent ? (
                        <a
                          className="primary wide"
                          href={`https://wa.me/${digits}?text=${encodeURIComponent(message)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {t("Open WhatsApp", "WhatsApp खोलें")} ↗
                        </a>
                      ) : (
                        <button className="primary wide" disabled>
                          {mode === "local"
                            ? t(
                                "WhatsApp sharing needs deployment",
                                "WhatsApp शेयरिंग के लिए डिप्लॉय करें",
                              )
                            : t(
                                "Review recipient and consent first",
                                "पहले प्राप्तकर्ता और सहमति जाँचें",
                              )}
                        </button>
                      )}
                      <a
                        className="secondary wide"
                        href={link}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {t(
                          "Open recipient test page",
                          "प्राप्तकर्ता परीक्षण पेज खोलें",
                        )}{" "}
                        ↗
                      </a>
                      <p className="fine">
                        {t(
                          "Opening WhatsApp does not prove sending or delivery. Reply within 48 hours; accepting opens a seven-day collection window.",
                          "WhatsApp खोलना भेजने या पहुँचने का प्रमाण नहीं है। 48 घंटे में जवाब दें; स्वीकार करने पर संग्रह के लिए सात दिन मिलेंगे।",
                        )}
                      </p>
                    </>
                  ) : (
                    <p>
                      {t(
                        "The share link is shown when a request is created. Saved requests retain their status and history.",
                        "अनुरोध बनाते समय शेयर लिंक दिखता है। सहेजे अनुरोध में स्थिति और इतिहास रहता है।",
                      )}
                    </p>
                  )}
                </section>
              </div>
            ) : (
              <div className="panel empty">
                <h2>{t("No request selected", "कोई अनुरोध नहीं चुना")}</h2>
                <p>
                  {t(
                    "Prepare a basket, or open a saved request below.",
                    "टोकरी तैयार करें या नीचे सहेजा अनुरोध खोलें।",
                  )}
                </p>
              </div>
            )}
            {requestIds.length > 0 && (
              <section className="saved">
                <h3>{t("Saved on this browser", "इस ब्राउज़र पर सहेजे गए")}</h3>
                {requestIds.map((id) => (
                  <button
                    className="secondary"
                    key={id}
                    onClick={() =>
                      run(async () => setRequest(await api(`/requests/${id}`)))
                    }
                  >
                    {id.slice(0, 8)} ↗
                  </button>
                ))}
              </section>
            )}
          </section>
        )}
      </main>
      <footer>
        <span>
          KabadiSetu <span>·</span>{" "}
          {t(
            "Made for a more thoughtful everyday.",
            "हर दिन बेहतर छँटाई के लिए।",
          )}
        </span>
        <span>
          {t(
            "Prototype · No verified recycling claims",
            "प्रोटोटाइप · रीसाइक्लिंग का सत्यापित दावा नहीं",
          )}
        </span>
      </footer>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
