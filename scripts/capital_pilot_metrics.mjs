/** Half-open UTF-8 source byte accounting for the bounded capital pilot. */
import assert from 'node:assert/strict';

function page(span) {
  if (Number.isSafeInteger(span.page) && span.page > 0) return span.page;
  const match = /^pages\[(\d+)\]\.text$/.exec(span.locator || '');
  assert(match, 'Evidence span has no page-text locator');
  return Number(match[1]) + 1;
}

export function sourceIntervals(spans) {
  assert(Array.isArray(spans));
  return spans.map(span => {
    const start = span.start_utf8 ?? span.source_start ?? span.start;
    const end = span.end_utf8 ?? span.source_end ?? span.end;
    assert(Number.isSafeInteger(start) && Number.isSafeInteger(end) && start >= 0 && end > start, 'Invalid UTF-8 source span');
    return {page: page(span), start, end};
  });
}

export function union(spans) {
  const ordered = sourceIntervals(spans).sort((a, b) => a.page - b.page || a.start - b.start || a.end - b.end);
  const merged = [];
  for (const item of ordered) {
    const last = merged.at(-1);
    if (last && last.page === item.page && item.start <= last.end) last.end = Math.max(last.end, item.end);
    else merged.push({...item});
  }
  return merged;
}

export function bytes(spans) {
  return union(spans).reduce((total, span) => total + span.end - span.start, 0);
}

export function intersectionBytes(left, right) {
  const a = union(left), b = union(right);
  let i = 0, j = 0, total = 0;
  while (i < a.length && j < b.length) {
    if (a[i].page === b[j].page) total += Math.max(0, Math.min(a[i].end, b[j].end) - Math.max(a[i].start, b[j].start));
    if (a[i].page < b[j].page || a[i].page === b[j].page && a[i].end <= b[j].end) i++;
    else j++;
  }
  return total;
}

export function measureSourceCoverage(selectedSpans, requiredGroups, paragraphSpans = []) {
  const selected = union(selectedSpans);
  const groups = requiredGroups.map(group => {
    const required = union(group.spans);
    const required_bytes = bytes(required);
    const retained_bytes = intersectionBytes(required, selected);
    return {id: group.key ?? group.id, required_bytes, retained_bytes, complete: retained_bytes === required_bytes};
  });
  const required = union([...requiredGroups.flatMap(group => group.spans), ...paragraphSpans]);
  const required_bytes = bytes(required);
  const retained_bytes = intersectionBytes(required, selected);
  return {required_bytes, retained_bytes, complete_groups: groups.filter(group => group.complete).length,
    required_groups: groups.length, groups, unique_source_bytes: bytes(selected),
    additional_selected_source_bytes: bytes(selected) - retained_bytes,
    paragraph_required_bytes: bytes(paragraphSpans), paragraph_retained_bytes: intersectionBytes(paragraphSpans, selected)};
}
