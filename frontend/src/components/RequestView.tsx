import type { RequestRecord } from "../types";
export function RequestView({
  request,
  recipient = false,
  busy,
  label,
  t,
  action,
  refresh,
}: {
  request: RequestRecord;
  recipient?: boolean;
  busy: boolean;
  label: (s: string) => string;
  t: (a: string, b: string) => string;
  action: (a: string) => void;
  refresh: () => void;
}) {
  return (
    <section
      className={"panel request-card" + (recipient ? " collector-card" : "")}
    >
      <div className="section-heading">
        <span className={"status " + request.status}>
          {label(request.status)}
        </span>
        <button className="text-button" onClick={refresh} disabled={busy}>
          {t("Refresh", "रीफ़्रेश")} ↻
        </button>
      </div>
      <h2>{t("The pickup basket", "कबाड़ की टोकरी")}</h2>
      {request.items.map((i) => (
        <div className="basket-row" key={i.id}>
          <strong>{t(i.en, i.hi)}</strong>
          <span>× {i.quantity}</span>
        </div>
      ))}
      <p className="fine">
        {t(
          "Estimated counts. Acceptance and rates need confirmation.",
          "अनुमानित गिनती। स्वीकृति और दर की पुष्टि ज़रूरी है।",
        )}
      </p>
      <div className="action-buttons">
        {recipient && request.status === "awaiting_response" && (
          <>
            <button
              className="primary"
              disabled={busy}
              onClick={() => action("accept")}
            >
              {t("Accept request", "स्वीकार करें")}
            </button>
            <button
              className="secondary"
              disabled={busy}
              onClick={() => action("reject")}
            >
              {t("Decline", "मना करें")}
            </button>
          </>
        )}
        {request.status === "accepted" && (
          <button
            className="primary"
            disabled={busy}
            onClick={() => action("collect")}
          >
            {t("Report collected", "संग्रह की सूचना दें")}
          </button>
        )}
        {!recipient &&
          ["awaiting_response", "accepted"].includes(request.status) && (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => action("cancel")}
            >
              {t("Cancel request", "अनुरोध रद्द करें")}
            </button>
          )}
      </div>
      <h3>{t("Activity", "गतिविधि")}</h3>
      <ol className="timeline">
        {request.events.map((event, i) => (
          <li key={i}>
            <strong>
              {
                (
                  {
                    created: t("Request created", "अनुरोध बना"),
                    accept: t("Accepted", "स्वीकार किया"),
                    reject: t("Declined", "मना किया"),
                    collect: t("Collection reported", "संग्रह की सूचना"),
                    cancel: t("Cancelled", "रद्द किया"),
                  } as Record<string, string>
                )[event.action]
              }
            </strong>
            <small>
              {event.source === "pickup_link"
                ? t("Through pickup link", "पिकअप लिंक से")
                : t("By household", "घर के सदस्य द्वारा")}{" "}
              · {new Date(event.at * 1000).toLocaleString()}
            </small>
          </li>
        ))}
      </ol>
      <p className="fine">
        {t(
          "Link possession is not identity verification. Collection reports are not proof of recycling.",
          "लिंक होना पहचान का सत्यापन नहीं है। संग्रह की सूचना रीसाइक्लिंग का प्रमाण नहीं है।",
        )}
      </p>
    </section>
  );
}
