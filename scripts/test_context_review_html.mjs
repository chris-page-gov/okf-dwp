import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { Script } from 'node:vm';
import { test } from 'node:test';
import { renderContextReview, safeSourceUrl } from './context_review_html.mjs';

const fixture = () => ({ schema: 'okf-dwp-context-review.v1', question: 'Which evidence was retained?',
  status: 'candidate-not-deployed', identity: { source: 'fixed-source', engine: 'fixed-engine' },
  contexts: [{ id: 'baseline', label: 'Baseline', query: 'Which evidence was retained?',
    context_id: 'urn:sha256:abc', evidence_status: 'insufficient', assembly_truncated: true,
    retrieval_truncated: true, selected_records: 1, relationships: 0, package_bytes: 1000,
    delivery_complete: true, package_complete: true,
    records: [{ id: 'source/one', label: 'Source passage', kind: 'evidence', text: 'Exact retained passage.',
      authority: { class: 'derived' }, review_status: 'unreviewed',
      provenance: [{ url: 'https://www.gov.uk/source.pdf#page=2', source_sha256: 'a'.repeat(64), locator: 'PDF page 2' }],
      reasons: ['source-backed-navigation'], paths: [] }], diagnostics: { missing_evidence: [{ code: 'specialist-review' }] } }],
  recovery_plan: { max_subqueries: 3 }, limitations: ['Machine extraction remains unreviewed.'] });

function parts(html) {
  const data = html.match(/<script id="review-data" type="application\/json">([\s\S]*?)<\/script>/);
  const executable = html.match(/<script>([\s\S]*?)<\/script>/);
  const style = html.match(/<style>([\s\S]*?)<\/style>/);
  assert(data && executable && style);
  return { data: data[1], executable: executable[1], style: style[1] };
}

test('standalone inspector retains exact report identities and separate evidence boundaries', () => {
  const report = fixture();const html = renderContextReview(report);const extracted = parts(html);
  assert.deepEqual(JSON.parse(extracted.data), report);
  assert.match(html, /lang="en-GB"/);
  assert.match(html, /Complete delivery and sufficient evidence are separate findings/);
  assert.match(html, /No answer, award calculation or individual entitlement decision/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /connect-src &#39;none&#39;/);
  new Script(extracted.executable);
});

test('source HTML, script terminators and Unicode separators remain inert data', () => {
  const report = fixture();const attack = '</script><script>alert("injected")</script><img src=x onerror=alert(1)>\u2028\u2029&';
  report.question = attack;report.contexts[0].records[0].text = attack;
  report.contexts[0].records[0].label = attack;report.limitations = [attack];
  const html = renderContextReview(report);const extracted = parts(html);
  assert(!html.includes('<script>alert('));assert(!html.includes('<img src=x'));
  assert(!extracted.data.includes('<'));assert(!extracted.data.includes('\u2028'));
  assert.deepEqual(JSON.parse(extracted.data), report);
  assert(!extracted.executable.includes('innerHTML'));assert(!extracted.executable.includes('eval('));
  assert(!extracted.executable.includes('fetch('));new Script(extracted.executable);
});

test('CSP hashes bind the exact embedded code and stylesheet', () => {
  const html = renderContextReview(fixture());const extracted = parts(html);
  for(const value of [extracted.executable, extracted.style]) {
    const digest = createHash('sha256').update(value).digest('base64');
    assert(html.includes(`sha256-${digest}`));
  }
  assert(!html.includes('unsafe-inline'));
});

test('source links admit only explicit HTTP(S) URLs without credentials or control characters', () => {
  assert.equal(safeSourceUrl('https://www.gov.uk/example.pdf#page=2'), 'https://www.gov.uk/example.pdf#page=2');
  assert.equal(safeSourceUrl('http://example.org/source'), 'http://example.org/source');
  for(const value of ['javascript:alert(1)', 'data:text/html,attack', 'file:///tmp/source', '//example.org/source',
    '/source', 'https://user:password@example.org/source', ' https://example.org', 'https://example.org\n',
    'java\nscript:alert(1)', 'https://exa mple.org', '', null, {}, 'not a url']) {
    assert.equal(safeSourceUrl(value), null, String(value));
  }
});

test('empty contexts remain reviewable; malformed reports fail closed', () => {
  const report=fixture();report.contexts=[];assert.match(renderContextReview(report), /No evidence contexts were recorded/);
  for(const bad of [null, {}, {...fixture(), schema:'other'}, {...fixture(), question:null},
    {...fixture(), contexts:[{}]}, {...fixture(), limitations:[{}]}]) assert.throws(()=>renderContextReview(bad), /Invalid context review/);
});

test('completion is never inferred merely from a retained receipt', () => {
  const report=fixture();delete report.contexts[0].delivery_complete;report.contexts[0].receipt={calls:[]};
  const extracted=parts(renderContextReview(report));
  assert.match(extracted.executable, /context\.delivery_complete===true/);
  assert(!Object.hasOwn(JSON.parse(extracted.data).contexts[0], 'delivery_complete'));
});
