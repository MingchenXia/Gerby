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
