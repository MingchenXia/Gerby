import test from 'node:test';
import assert from 'node:assert/strict';
import { badgeDetails } from '../site/assets/formalization.mjs';

test('unrecorded and network failure are distinct from verification', () => {
  assert.equal(badgeDetails().state, 'not-recorded');
  assert.equal(badgeDetails(undefined, true).state, 'unavailable');
});

test('pending records link to their proof repository', () => {
  const badge = badgeDetails({state: 'pending', repository: 'https://github.com/owner/proofs'});
  assert.equal(badge.state, 'pending');
  assert.equal(badge.href, 'https://github.com/owner/proofs');
});

test('verified records link to an immutable proof revision', () => {
  const commit = 'a'.repeat(40);
  const badge = badgeDetails({state: 'verified', repository: 'https://github.com/owner/proofs', commit, declaration: 'Book.theorem_one', file: 'Book.lean'});
  assert.equal(badge.text, '0 sorry');
  assert.equal(badge.href, `https://github.com/owner/proofs/tree/${commit}`);
  assert.match(badge.title, /Book.theorem_one/);
});

test('a verified label without an exact commit cannot produce a verified badge', () => {
  assert.equal(badgeDetails({state: 'verified', commit: 'main'}).state, 'pending');
});
