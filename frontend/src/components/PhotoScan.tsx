import { useState } from "react";
import { preparePhoto } from "../photo";

type Props = {
  enabled: boolean;
  provider: string;
  itemName: (id: string) => string;
  t: (en: string, hi: string) => string;
  api: (path: string, body?: unknown, key?: string) => Promise<any>;
  onSuggestion: (id: string) => void;
  onPhotoStart: () => void;
  onQuestion: () => void;
  onCorrection: () => void;
};
export function PhotoScan({ enabled, provider, itemName, t, api, onSuggestion, onPhotoStart, onQuestion, onCorrection }: Props) {
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const [clarification, setClarification] = useState<{kind: string; options: string[]} | null>(null);
  function choose(id: string) {
    onSuggestion(id);
    setSuggestion(null);
    setClarification(null);
  }
  function manual() {
    onCorrection();
    setSuggestion(null);
    setClarification(null);
    setMessage(t("Please search the catalogue or choose an item.", "कृपया सूची में सामान खोजें या चुनें।"));
  }
  async function scan(file: File) {
    onPhotoStart();
    setBusy(true);
    setMessage("");
    setSuggestion(null);
    setClarification(null);
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
      if (result.status === "complete" && result.clarification?.options?.length) {
        onQuestion();
        setClarification(result.clarification);
      } else if (result.status !== "complete" || result.item_id === "unknown") {
        setMessage(
          t(
            "Not sure about this photo. Please search the catalogue or choose an item.",
            "फोटो स्पष्ट नहीं है। कृपया सामान खुद चुनें।",
          ),
        );
      } else setSuggestion(result.item_id);
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
            {provider === "rekognition" ? t(
              "Only photograph the item. Recognition runs in AWS Mumbai. Photos are scheduled for deletion after one day.",
              "केवल सामान की फोटो लें। पहचान AWS मुंबई में होती है। एक दिन बाद फोटो हटाने की प्रक्रिया शुरू होगी।",
            ) : t(
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
      {suggestion && (
        <div>
          <p>{t("Does this look right?", "क्या यह सही है?")} {itemName(suggestion)}</p>
          <button className="primary" type="button" onClick={() => choose(suggestion)}>{t("Yes, check this item", "हाँ, इस सामान की जाँच करें")}</button>
          <button className="secondary" type="button" onClick={manual}>{t("No, choose manually", "नहीं, खुद चुनें")}</button>
        </div>
      )}
      {clarification && (
        <fieldset className="photo-choices">
          <legend>{clarification.kind === "bottle"
            ? t("Which kind of bottle is it?", "यह किस तरह की बोतल है?")
            : clarification.kind === "can"
              ? t("Is this an aluminium drink can?", "क्या यह एल्यूमिनियम का पेय कैन है?")
              : t("Which kind of container is it?", "यह किस तरह का डिब्बा है?")}</legend>
          <p>{t("The photo cannot confirm the material. Choose only if you know.", "फोटो से सामग्री की पुष्टि नहीं हो सकती। पता हो तभी चुनें।")}</p>
          {clarification.options.map((id) => (
            <button className="secondary" type="button" key={id} onClick={() => choose(id)}>{itemName(id)}</button>
          ))}
          <button className="secondary" type="button" onClick={manual}>{t("None of these, choose manually", "इनमें से नहीं / पता नहीं — खुद चुनें")}</button>
        </fieldset>
      )}
      <p role="status">{message}</p>
    </section>
  );
}
