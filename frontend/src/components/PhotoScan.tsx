import { useState } from "react";
import { preparePhoto } from "../photo";

type Props = {
  enabled: boolean;
  t: (en: string, hi: string) => string;
  api: (path: string, body?: unknown, key?: string) => Promise<any>;
  onSuggestion: (id: string) => void;
};
export function PhotoScan({ enabled, t, api, onSuggestion }: Props) {
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  async function scan(file: File) {
    setBusy(true);
    setMessage("");
    try {
      const image = await preparePhoto(file);
      const grant = await api("/scans", {}, crypto.randomUUID());
      const form = new FormData();
      for (const [key, value] of Object.entries(grant.upload.fields))
        form.append(key, String(value));
      form.append("file", image, "item.jpg");
      const upload = await fetch(grant.upload.url, {
        method: "POST",
        body: form,
      });
      if (!upload.ok)
        throw new Error(
          t(
            "Upload failed. Try manual search.",
            "फोटो नहीं भेजी जा सकी। सामान खोजकर चुनें।",
          ),
        );
      const result = await api(`/scans/${grant.id}/analyze`, {});
      if (result.status !== "complete" || result.item_id === "unknown") {
        setMessage(
          t(
            "Not sure about this photo. Please choose the item below.",
            "फोटो स्पष्ट नहीं है। कृपया सामान खुद चुनें।",
          ),
        );
      } else onSuggestion(result.item_id);
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Please use manual search.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel photo-scan">
      <h2>{t("Identify from a photo", "फोटो से पहचानें")}</h2>
      {enabled ? (
        <>
          <p>
            {t(
              "Only photograph the item. Photo processing may occur across APAC. Photos are scheduled for deletion after one day.",
              "केवल सामान की फोटो लें। पहचान के लिए फोटो APAC क्षेत्रों में भेजी जा सकती है। एक दिन बाद फोटो हटाने की प्रक्रिया शुरू होगी।",
            )}
          </p>
          <label>
            {busy
              ? t("Checking photo…", "फोटो जाँच रहे हैं…")
              : t("Choose a photo", "फोटो चुनें")}
            <input
              type="file"
              accept="image/*"
              capture="environment"
              disabled={busy}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void scan(f);
                e.target.value = "";
              }}
            />
          </label>
        </>
      ) : (
        <p>
          {t(
            "Photo recognition is unavailable. Manual search works without an AI call.",
            "फोटो पहचान अभी उपलब्ध नहीं है। सामान खुद चुनें—AI कॉल नहीं होगी।",
          )}
        </p>
      )}
      <p role="status">{message}</p>
    </section>
  );
}
