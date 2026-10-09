import test from 'node:test';
import assert from 'node:assert/strict';
import {createTrial} from '../src/trials.js';

test('a photo question and correction are timed without leaking inputs', () => {
  let now=100;
  const trial=createTrial(() => now);
  trial.start('developer trial','photo');trial.tap();trial.photo();trial.question();
  trial.correction();trial.select('private-item-text');trial.tap();now=2100;
  const row=trial.finish(true);
  assert.deepEqual(row,{trial_type:'developer trial',planned_method:'photo',method:'photo + question',duration_ms:2000,
    taps:2,corrections:1,manual_fallback:true,outcome:'confirmed route'});
  assert.equal(JSON.stringify(trial.snapshot()).includes('private-item-text'),false);
});
test('manual corrections, route gate, and aborted trials remain honest', () => {
  const trial=createTrial(() => 10);
  trial.start('household trial','manual');trial.select('one');trial.select('two');
  trial.condition('yes');trial.condition('no');
  assert.throws(() => trial.finish(false));
  assert.throws(() => trial.start('developer trial','photo'));
  const row=trial.abort();assert.equal(row.outcome,'aborted');assert.equal(row.corrections,2);
  assert.equal(trial.snapshot().results.length,1);
});
