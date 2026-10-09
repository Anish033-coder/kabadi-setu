import { useState } from 'react';

type Props = {
  active: boolean;
  results: Record<string, unknown>[];
  hasRoute: boolean;
  onStart: (type: string, method: string) => void;
  onFinish: () => void;
  onAbort: () => void;
};
export function TrialPanel({active, results, hasRoute, onStart, onFinish, onAbort}: Props) {
  const [type, setType] = useState('developer trial');
  function download() {
    const blob = new Blob([JSON.stringify({schema:1, trials:results}, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = 'kabadi-trials.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section className="panel trial-panel" aria-label="Timing trial">
    <h2>Timing trial / समय परीक्षण</h2>
    <p>Start before choosing an item. Finish after reading and confirming its route. Results stay in page memory; download before refreshing. No names or photos are recorded.</p>
    {!active ? <>
      <label>Trial type<select value={type} onChange={e => setType(e.target.value)}>
        <option>developer trial</option><option>household trial</option>
      </select></label>
      <button className="secondary" onClick={() => onStart(type, 'manual')}>Start manual trial</button>
      <button className="secondary" onClick={() => onStart(type, 'photo')}>Start photo trial</button>
    </> : <>
      <p role="status">Trial running. Camera/file-picker time counts; only taps inside the app are counted.</p>
      <button className="primary" disabled={!hasRoute} onClick={onFinish}>Confirm this route and finish trial</button>
      <button className="secondary" onClick={onAbort}>Abort and record trial</button>
    </>}
    <p>{results.length} recorded trials. Aborted trials are retained.</p>
    <button className="secondary" disabled={!results.length || active} onClick={download}>Download trial results</button>
  </section>;
}
