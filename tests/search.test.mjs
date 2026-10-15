import test from 'node:test';
import assert from 'node:assert/strict';
import {exactEntry, searchEntries} from '../site/assets/search.mjs';

const records = [
  {tag:'AAAA1111',title:'Preface',search_title:'Preface',topic:'Analysis',text:'This introduces multiplier ideals.',aliases:[]},
  {tag:'BBBB2222',title:'Definition 1.2.3',search_title:'Multiplier ideals',topic:'Singularities',text:'A local integrability construction.',aliases:['def:multiplier_ideal','1234ABCD']},
];
test('exact source tags and internal labels resolve without exposing labels as titles', () => {
  assert.equal(exactEntry(records,'1234abcd')?.tag,'BBBB2222');
  assert.equal(exactEntry(records,'def:multiplier_ideal')?.title,'Definition 1.2.3');
  assert.equal(exactEntry(records,'multiplier'),null);
});
test('a named mathematical subject ranks above incidental full-text matches', () => {
  assert.deepEqual(searchEntries(records,'multiplier ideals').map(r=>r.tag),['BBBB2222','AAAA1111']);
});
test('ambiguous aliases do not jump to an arbitrary statement', () => {
  assert.equal(exactEntry([...records,{...records[0],aliases:['1234ABCD']}],'1234ABCD'),null);
});
test('empty and one-character queries do not list the whole collection', () => {
  assert.deepEqual(searchEntries(records,''),[]);
  assert.deepEqual(searchEntries(records,'a'),[]);
});

test('chunked search retains records and resolves chunk paths under the project root', async () => {
  const {loadSearchIndex} = await import('../site/assets/search.mjs');
  const root = 'https://mingchenxia.github.io/Pome/';
  const records = [{tag: 'A', title: 'First', aliases: [], topic: '', text: ''}, {tag: 'B', title: 'Second', aliases: [], topic: '', text: 'Kelvin transform'}];
  const calls = [];
  const request = async url => {calls.push(url); return {ok: true, json: async () => url.endsWith('search.json') ? {version: 2, chunks: ['search-data/000.json', 'search-data/001.json']} : [records[url.endsWith('000.json') ? 0 : 1]]};};
  const result = await loadSearchIndex(root + 'search.json', request);
  assert.deepEqual(result, records);
  assert.deepEqual(calls, [root + 'search.json', root + 'search-data/000.json', root + 'search-data/001.json']);
  assert.equal(exactEntry(result, 'B').tag, 'B');
  assert.equal(searchEntries(result, 'Kelvin')[0].tag, 'B');
});

test('a failed search chunk rejects the entire load', async () => {
  const {loadSearchIndex} = await import('../site/assets/search.mjs');
  await assert.rejects(loadSearchIndex('https://example.org/Pome/search.json', async url => ({ok: url.endsWith('search.json'), json: async () => ({version: 2, chunks: ['search-data/000.json']})})), /Search unavailable/);
});
