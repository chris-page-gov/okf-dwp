#!/usr/bin/env node
import assert from 'node:assert/strict';
import {bytes, intersectionBytes, measureSourceCoverage, union} from './capital_pilot_metrics.mjs';

// Offsets are bytes: the first three bytes contain one £ character.
const source = Buffer.from('£abcdef');
assert.equal(source.length, 8);
const spans = [
  {locator: 'pages[0].text', source_start: 5, source_end: 8},
  {locator: 'pages[0].text', source_start: 0, source_end: 6},
  {locator: 'pages[0].text', source_start: 2, source_end: 4},
  {locator: 'pages[1].text', source_start: 0, source_end: 2},
];
assert.deepEqual(union(spans), [{page: 1, start: 0, end: 8}, {page: 2, start: 0, end: 2}]);
assert.equal(bytes(spans), 10);
assert.equal(intersectionBytes(spans, [{page: 1, start_utf8: 3, end_utf8: 9}]), 5);
const measured = measureSourceCoverage(spans, [
  {key: 'a', spans: [{page: 1, start_utf8: 0, end_utf8: 6}]},
  {key: 'b', spans: [{page: 1, start_utf8: 4, end_utf8: 9}]},
], [{page: 2, start_utf8: 1, end_utf8: 2}]);
assert.equal(measured.required_bytes, 10); // Overlapping group bytes count once.
assert.equal(measured.retained_bytes, 9);
assert.equal(measured.complete_groups, 1);
assert.equal(measured.additional_selected_source_bytes, 1);
assert.equal(measured.paragraph_retained_bytes, 1);
assert.equal(measured.groups[1].retained_bytes, 4);
console.log('Capital pilot source byte metrics: passed');
