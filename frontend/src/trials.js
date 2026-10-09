// Trial records stay on this browser and contain no names, item IDs or input text.
export function createTrial(clock = () => performance.now(), initial = []) {
  let active = null;
  const results = initial.slice(-100);
  function record(outcome) {
    if (!active) return null;
    const row = {
      trial_type: active.type,
      planned_method: active.planned,
      method: active.question ? 'photo + question' : active.photo ? 'photo' : 'manual',
      duration_ms: Math.max(0, Math.round(clock() - active.started)),
      taps: active.taps,
      corrections: active.corrections,
      manual_fallback: active.fallback,
      outcome,
    };
    results.push(row);
    if (results.length > 100) results.shift();
    active = null;
    return row;
  }
  return {
    start(type, planned) {
      if (active) throw new Error('Finish or abort the active trial first.');
      if (!['developer trial', 'household trial'].includes(type) || !['photo', 'manual'].includes(planned))
        throw new Error('Invalid trial setup.');
      active = {type, planned, started:clock(), taps:0, corrections:0, photo:false,
        question:false, fallback:false, selection:null, condition:null};
    },
    tap() { if (active) active.taps++; },
    photo() { if (active) active.photo = true; },
    question() { if (active) { active.photo = true; active.question = true; } },
    correction() { if (active) { active.corrections++; active.fallback = active.photo; } },
    select(id, source = 'manual') {
      if (!active) return;
      if (active.selection && active.selection !== id) active.corrections++;
      if (source === 'manual' && active.photo) active.fallback = true;
      active.selection = id;
    },
    condition(value) {
      if (!active) return;
      if (active.condition && active.condition !== value) active.corrections++;
      active.condition = value;
    },
    finish(hasRoute) {
      if (!hasRoute) throw new Error('A route must be shown and confirmed before finishing.');
      return record('confirmed route');
    },
    abort() { return record('aborted'); },
    snapshot() { return {active:!!active, results:[...results]}; },
  };
}
