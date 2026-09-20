#!/usr/bin/env python3
"""Offline integrity of model-authored critique; never validate semantic opinions.

Reads only this retained experiment's explicit public paths. No model, network,
Git or frozen runner/helper execution is performed.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SPEC = 'evaluation/model-comparison/household-compact-v2-candidate'
ORIGINAL = 'evaluation/model-comparison/household-2026-09-21/frozen'
OUTPUT = 'validation/model-comparison/household-compact-v2'
FREEZE = SPEC + '/frozen-manifest.json'
RESULTS = OUTPUT + '/results.json'
CRITIQUE = OUTPUT + '/claim-level-model-critique.json'
FREEZE_SHA = 'faefc7f42282c2f8dfdee119ff6d30f26b537b73b43b1b9ed133c3befbef4678'
SOURCE_COMMIT = '78a8beea97242d646eb9159860dea190ca5e2998'
CASES = ('control-unknown', 'staff-005', 'staff-008', 'staff-012', 'staff-020', 'staff-026')
ATTEMPTS = {('codex-subscription', c, 'attempt-01') for c in CASES} | {
    ('claude-subscription', c, 'attempt-01') for c in ('control-unknown', 'staff-012', 'staff-020')}
ACCEPTED = {('codex-subscription', c, 'attempt-01') for c in CASES} | {('claude-subscription', 'control-unknown', 'attempt-01')}
HELPERS = ('evaluate_fixed_answers.py', 'monday_cli_events_v2.py', 'project_monday_model_contexts.py',
           'run_monday_compact_trials.py', 'run_monday_model_trials.py', 'run_staff_model_trials.py')
FROZEN_PATHS = {'evaluation/answer-review/answer.schema.json', ORIGINAL + '/manifest.json'} | {
    ORIGINAL + '/contexts/' + c + '.json' for c in CASES} | {SPEC + '/packets/' + c + '.json' for c in CASES} | {
    SPEC + '/' + name for name in ('byte-census.json', 'candidate-manifest.json', 'protocol.json', 'system-prompt.txt', 'user-prompt.txt')} | {'scripts/' + name for name in HELPERS}
LIMITS = {p: 262144 for p in FROZEN_PATHS}
LIMITS.update({FREEZE:65536, RESULTS:65536, CRITIQUE:262144})
for provider, case, attempt in ATTEMPTS:
    for name, limit in [('receipt.json',262144),('answer.json',131072),('model-output.json',2097152)]:
        LIMITS[f'{OUTPUT}/{provider}/{case}/{attempt}/{name}'] = limit
MAX_TOTAL = 16 * 1024 * 1024


def require(condition, message):
    if not condition: raise ValueError(message)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def keys(value, expected, label):
    require(isinstance(value, dict) and set(value) == set(expected), label + ' fields differ')

def checked_directory(path):
    path = Path(path).absolute()
    for part in [*reversed(path.parents), path]:
        require(stat.S_ISDIR(part.lstat().st_mode), 'Directory or parent is not a real directory; symlinks forbidden')
    return path


def bounded_read(path, limit):
    checked_directory(path.parent)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), 'File must be regular; symlinks forbidden')
    require(before.st_size <= limit, 'File exceeds byte bound')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode) and opened.st_size <= limit, 'Opened file exceeds bound')
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and len(raw) == before.st_size == opened.st_size, 'File changed or exceeded bound')
    return raw


class Reader:
    def __init__(self, root):
        self.root = checked_directory(root); self.cache = {}; self.total = 0
    def read(self, name):
        require(name in LIMITS, 'Path is not in the explicit public experiment allowlist')
        if name not in self.cache:
            value = bounded_read(self.root/name, LIMITS[name]); self.total += len(value)
            require(self.total <= MAX_TOTAL, 'Total read bound exceeded')
            self.cache[name] = value
        return self.cache[name]
    def json(self, name): return json.loads(self.read(name))


def text(value, label):
    require(isinstance(value,str) and 0 < len(value) <= 12000, label + ' must be bounded nonempty prose')

def prose_list(value, label):
    require(isinstance(value,list) and len(value) <= 32, label + ' list exceeds bound')
    for item in value: text(item,label)

def pending(value):
    require(value.get('human_review') == 'pending', 'Human review must remain pending')
    require(value.get('specialist_accepted') is False, 'Specialist acceptance must remain false')
    for field in ('answer_quality_score','unsupported_claim_rate'):
        require(value.get(field) is None, 'A scalar quality judgement must not be introduced')


def citation_diagnostic(citation, record):
    quote = citation['quote']; literal = record['text']
    return {'record_id':citation['record_id'], 'exact_quote':quote in literal,
        'whitespace_normalised_match':' '.join(quote.split()) in ' '.join(literal.split()),
        'locator':citation['locator'],'source_url':citation['source_url'],
        'source_pair_in_package':any(p.get('url') == citation['source_url'] and p.get('locator') == citation['locator'] for p in record['provenance']),
        'record_text_sha256':sha(literal.encode()),'source_provenance':record['provenance']}


def validate(root=ROOT):
    reader = Reader(root)
    freeze_raw = reader.read(FREEZE); require(sha(freeze_raw) == FREEZE_SHA, 'Approved freeze fingerprint differs')
    freeze = json.loads(freeze_raw)
    require(freeze['schema'] == 'okf-compact-model-trial-freeze.v2' and freeze['source_commit'] == SOURCE_COMMIT, 'Freeze identity differs')
    require(freeze['historical_contexts_unchanged'] is True and freeze['model_calls'] == 0, 'Freeze boundary differs')
    frozen = {}
    for row in freeze['inputs']:
        require(row['path'] in FROZEN_PATHS and row['path'] not in frozen, 'Unregistered or duplicate frozen input')
        raw = reader.read(row['path']); require(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Frozen input hash/size differs: ' + row['path'])
        frozen[row['path']] = row
    require(set(frozen) == FROZEN_PATHS, 'Frozen input census differs')
    critique = reader.json(CRITIQUE); results_raw = reader.read(RESULTS); results = json.loads(results_raw)
    keys(critique, ('schema','review_type','reviewer','basis','freeze_manifest_sha256','results_sha256','human_review','specialist_accepted','unsupported_claim_rate','answer_quality_score','limitations','reviews'), 'Critique')
    require(critique['schema'] == 'okf-staff-claim-model-critique.v1' and critique['review_type'] == 'separately-authored-model-critique-not-gold', 'Model critique boundary differs')
    pending(critique); text(critique['reviewer'],'Reviewer label'); text(critique['basis'],'Review basis'); prose_list(critique['limitations'],'Limitations')
    require(critique['freeze_manifest_sha256'] == FREEZE_SHA == results['freeze_manifest_sha256'], 'Critique/results freeze binding differs')
    require(critique['results_sha256'] == sha(results_raw), 'Critique/results digest differs')
    keys(results, ('attempts','comparative_accuracy_established','freeze_manifest_sha256','pairs','schema','specialist_accepted'), 'Results')
    require(results['schema'] == 'okf-compact-model-results.v2' and results['specialist_accepted'] is False and results['comparative_accuracy_established'] is False, 'Results overstate acceptance')
    require(isinstance(results['attempts'],list) and len(results['attempts']) == len(ATTEMPTS), 'Nine-attempt census differs')
    attempts = {}; answers = {}; contexts = {}
    schema = reader.json('evaluation/answer-review/answer.schema.json'); validator = Draft202012Validator(schema)
    for row in results['attempts']:
        key = (row['provider'], row['case_id'], row['attempt'])
        require(key in ATTEMPTS and key not in attempts, 'Unknown or duplicate attempt')
        prefix = '/'.join((OUTPUT,*key)); require(row['receipt'] == prefix + '/receipt.json', 'Receipt path differs')
        receipt_raw = reader.read(row['receipt']); require(sha(receipt_raw) == row['receipt_sha256'], 'Receipt digest differs')
        receipt = json.loads(receipt_raw); pending(receipt)
        require(receipt['schema'] == 'okf-compact-model-attempt.v2' and receipt['source_commit'] == SOURCE_COMMIT, 'Receipt source identity differs')
        require(tuple(receipt[k] for k in ('provider','case_id','attempt')) == key, 'Receipt identity differs')
        for name in ('inputs','status','answer_present','mechanical_assessment'):
            require(receipt.get(name) == row.get(name), 'Ledger/receipt disagreement: ' + name)
        context_path = ORIGINAL + '/contexts/' + row['case_id'] + '.json'
        packet_path = SPEC + '/packets/' + row['case_id'] + '.json'
        context = reader.json(context_path); contexts[key] = context
        require(row['inputs']['freeze_manifest_sha256'] == FREEZE_SHA and row['inputs']['original_context_sha256'] == frozen[context_path]['sha256'] and row['inputs']['packet_sha256'] == frozen[packet_path]['sha256'], 'Attempt/context/packet binding differs')
        require(row['inputs']['context_id'] == context['context_id'] and context['evidence_status'] == 'insufficient' and context['ai_answer'] is None, 'Original context identity or boundary differs')
        require(isinstance(receipt['artefacts'],dict) and set(receipt['artefacts']) <= {'answer.json','model-output.json'}, 'Unknown output artefact')
        for name,digest in receipt['artefacts'].items():
            require(sha(reader.read(prefix+'/'+name)) == digest, 'Output artefact digest differs: ' + name)
        accepted = key in ACCEPTED
        require(row['answer_present'] is accepted and (row['status'] == 'actual-model-response-retained') is accepted, 'Accepted-answer census differs')
        if accepted:
            require('answer.json' in receipt['artefacts'], 'Accepted answer artefact missing')
            answer = reader.json(prefix+'/answer.json')
            try: validator.validate(answer)
            except ValidationError as error: raise ValueError('Retained answer schema differs') from error
            require(answer['context_id'] == context['context_id'] and answer['package_evidence_status'] == 'insufficient' and answer['answer_disposition'] != 'bounded_source_answer', 'Answer boundaries differ')
            answers[key] = answer
        else:
            require('answer.json' not in receipt['artefacts'], 'Rejected attempt contains an accepted answer')
        attempts[key] = row
    require(set(attempts) == ATTEMPTS and set(answers) == ACCEPTED and len(answers) == 7, 'Accepted-answer census differs')
    require(isinstance(results['pairs'],list) and len(results['pairs']) == len(CASES), 'Pair census differs')
    pair_cases = set()
    for pair in results['pairs']:
        keys(pair, ('case_id','both_responses_retained','same_public_inputs'), 'Pair result')
        case = pair['case_id']; require(case in CASES and case not in pair_cases, 'Unknown or duplicate pair case'); pair_cases.add(case)
        complete = all((provider,case,'attempt-01') in answers for provider in ('claude-subscription','codex-subscription'))
        require(pair['both_responses_retained'] is complete and pair['same_public_inputs'] is complete, 'Pair completion differs from accepted-answer census')
    require(isinstance(critique['reviews'],list) and len(critique['reviews']) == 7, 'Critique review census differs')
    reviews = set(); claims_count = citations_count = additional_count = incorrect_pairs = 0
    for review in critique['reviews']:
        keys(review, ('provider','case_id','attempt','answer_path','answer_sha256','context_path','context_sha256','event_recognition_status','mechanical_status','claim_reviews','additional_selected_evidence_reviewed','answer_level_findings','control_observation','human_review'), 'Answer review')
        key = (review['provider'],review['case_id'],review['attempt']); require(key in ACCEPTED and key not in reviews, 'Missing, duplicate or unaccepted answer review'); reviews.add(key)
        require(review['human_review'] == 'pending', 'Answer review acceptance must remain pending')
        expected_answer = '/'.join((OUTPUT,*key,'answer.json')); expected_context = ORIGINAL+'/contexts/'+key[1]+'.json'
        require(review['answer_path'] == expected_answer and review['context_path'] == expected_context, 'Review path differs')
        require(review['answer_sha256'] == sha(reader.read(expected_answer)) and review['context_sha256'] == sha(reader.read(expected_context)), 'Reviewed answer/context digest differs')
        row = attempts[key]; require(review['event_recognition_status'] == row['status'] and review['mechanical_status'] == row['mechanical_assessment']['status'], 'Reviewed event/mechanical status differs')
        prose_list(review['answer_level_findings'],'Answer-level model findings')
        answer = answers[key]; context = contexts[key]
        records = {x['record']['id']:x['record'] for x in context['selected']}
        require(len(records) == len(context['selected']), 'Duplicate selected record')
        claims = {x['id']:x for x in answer['claims']}; require(len(claims) == len(answer['claims']), 'Duplicate answer claim')
        require(isinstance(review['claim_reviews'],list) and len(review['claim_reviews']) == len(claims), 'Claim review census differs')
        seen = set(); literal_failures = []
        for claim_review in review['claim_reviews']:
            keys(claim_review, ('claim_id','model_review_observation','explanation','citation_diagnostics','human_acceptance'), 'Claim review')
            claim_id = claim_review['claim_id']; require(claim_id in claims and claim_id not in seen, 'Unknown or duplicate claim review'); seen.add(claim_id)
            require(claim_review['human_acceptance'] == 'pending', 'Claim acceptance must remain pending')
            text(claim_review['model_review_observation'],'Model opinion label'); text(claim_review['explanation'],'Model opinion')
            evidence = claims[claim_id]['evidence']; require(isinstance(claim_review['citation_diagnostics'],list) and len(claim_review['citation_diagnostics']) == len(evidence), 'Citation census differs')
            for supplied,citation in zip(claim_review['citation_diagnostics'],evidence):
                record = records.get(citation['record_id']); require(record is not None, 'Cited record is not selected')
                expected = citation_diagnostic(citation,record)
                for flag in ('exact_quote','whitespace_normalised_match','source_pair_in_package'):
                    require(type(supplied.get(flag)) is bool, 'Citation diagnostic must be boolean')
                require(supplied == expected, 'Citation diagnostic differs from selected evidence')
                if not expected['exact_quote']:literal_failures.append(claim_id+':quote_not_verbatim')
                if not expected['source_pair_in_package']:literal_failures.append(claim_id+':source_locator_not_in_package');incorrect_pairs += 1
                citations_count += 1
            claims_count += 1
        require(seen == set(claims), 'Claim review census differs')
        assessment = row['mechanical_assessment']
        require(assessment['failures'] == literal_failures, 'Retained literal failures differ')
        require(assessment['status'] == ('failed-mechanical-controls' if literal_failures else 'passed-mechanical-controls'), 'Mechanical status differs')
        require(assessment['claims'] == len(claims) and assessment['citations_checked'] == sum(len(c['evidence']) for c in claims.values()), 'Mechanical counts differ')
        require(assessment['specialist_accepted'] is False and assessment['answer_quality_score'] is None and assessment['unsupported_claim_rate'] is None, 'Mechanical result overstates quality')
        additional = review['additional_selected_evidence_reviewed']; require(isinstance(additional,list) and len(additional) <= 64, 'Additional evidence census exceeds bound')
        additional_ids = set()
        for item in additional:
            keys(item, ('record_id','text_sha256','authority','assertion_status','review_status','provenance'), 'Additional source review')
            record = records.get(item['record_id']); require(record is not None and item['record_id'] not in additional_ids, 'Unknown or duplicate additional selected evidence'); additional_ids.add(item['record_id'])
            require(item['text_sha256'] == sha(record['text'].encode()), 'Additional selected text digest differs')
            require(all(item[k] == record[k] for k in ('authority','assertion_status','review_status','provenance')), 'Additional selected source metadata differs')
            additional_count += 1
        if key[1] == 'control-unknown':
            text(review['control_observation'],'Control observation')
            require(not records and not claims and answer['answer_disposition'] == 'cannot_establish', 'Unknown control did not abstain')
        else:require(review['control_observation'] is None, 'Substantive answer labelled as control')
    require(reviews == ACCEPTED, 'Accepted-answer review coverage differs')
    return {'status':'verified-offline-structure-and-citation-diagnostics','accepted_answers_checked':len(reviews),
        'claim_reviews_checked':claims_count,'citation_diagnostics_checked':citations_count,
        'additional_selected_records_checked':additional_count,'retained_invalid_source_pairs':incorrect_pairs,
        'human_review':'pending','specialist_accepted':False,'semantic_opinions_validated':False,
        'answer_quality_score':None,'unsupported_claim_rate':None,
        'freeze_manifest_sha256':FREEZE_SHA,'critique_sha256':sha(reader.read(CRITIQUE)),
        'network_model_or_git_calls':0,
        'limitation':'Verifies retained identities and recomputed literal diagnostics. It does not establish entailment, complete qualifications, legal applicability, quality scores or correctness of model-authored opinions.'}

if __name__ == '__main__': print(json.dumps(validate(),indent=2))
