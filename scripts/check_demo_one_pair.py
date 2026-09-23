#!/usr/bin/env python3
"""Offline mechanical observation of all four frozen responses; no retries or inference."""
import json
from pathlib import Path
import demo_one_pair as demo


def observe():
    demo.check()
    results = []
    for case in demo.CASES:
        _, _, package = demo.load_package(case)
        records = {x['record']['id']: x['record'] for x in package['selected']}
        for arm in demo.ARMS:
            directory = demo.OUT / f'{case}-{arm}'
            start = json.loads((directory / 'started.json').read_bytes())
            outcome = json.loads((directory / 'outcome.json').read_bytes())
            events = [json.loads(line) for line in (directory / 'stdout.txt').read_text().splitlines()]
            terminals = [x for x in events if x.get('type') == 'result']
            assert len(terminals) == 1
            terminal = terminals[0]
            tool_events = [x for x in events if x.get('type') == 'assistant' and any(
                b.get('type') in ['tool_use', 'server_tool_use'] for b in x.get('message', {}).get('content', []))]
            assert not tool_events and terminal['num_turns'] == 1 and not terminal['is_error']
            assert set(terminal['modelUsage']) == {'claude-opus-5'}
            assert outcome['returncode'] == 0 and not outcome['timed_out'] and not outcome['output_bound_exceeded']
            usage = terminal['usage']; text = terminal['result']; violations = []; citations = []
            try:
                answer = demo.runner.events.strict_json(text.encode(), 128 * 1024)
            except ValueError as error:
                answer = None; violations.append('invalid_json')
            if len(text.encode()) > 12 * 1024: violations.append('answer_byte_limit')
            if answer is not None:
                if set(answer) != {'summary', 'claims', 'gaps', 'limitations'}: violations.append('answer_keys')
                if len(answer.get('summary','')) > 1400: violations.append('summary_length')
                if len(answer.get('claims',[])) > 4: violations.append('claim_limit')
                for i, claim in enumerate(answer.get('claims', []), 1):
                    for citation in claim.get('citations', []):
                        record = records.get(citation.get('record_id'))
                        valid = bool(record and record['kind'] == 'evidence' and citation.get('quote') and citation['quote'] in record['text'])
                        citations.append({'claim': i, 'record_id': citation.get('record_id'),
                                          'quote': citation.get('quote'), 'exact_selected_source_quote': valid})
                        if not valid: violations.append('citation_mismatch')
                if arm == 'unassisted' and citations: violations.append('unsupplied_citation')
            results.append({'case': case, 'arm': arm, 'actual_model': list(terminal['modelUsage'])[0],
                'invocation_number': start['invocation_number'], 'client_completed': True,
                'prompt_bytes': start['prompt']['bytes'], 'response_bytes': len(text.encode()),
                'input_tokens': usage['input_tokens'], 'cache_creation_input_tokens': usage['cache_creation_input_tokens'],
                'cache_read_input_tokens': usage['cache_read_input_tokens'],
                'total_input_tokens': sum(usage[k] for k in ['input_tokens','cache_creation_input_tokens','cache_read_input_tokens']),
                'output_tokens': usage['output_tokens'], 'thinking_tokens': usage.get('output_tokens_details',{}).get('thinking_tokens'),
                'elapsed_seconds': outcome['elapsed_seconds'], 'tool_events': len(tool_events),
                'server_tool_use': usage.get('server_tool_use'), 'format_violations': sorted(set(violations)),
                'citations': citations, 'answer': answer, 'unparsed_answer': text if answer is None else None,
                'raw_files': {p.name: demo.identity(p.read_bytes()) for p in sorted(directory.iterdir()) if p.is_file()}})
    assert sorted(x['invocation_number'] for x in results) == [1,2,3,4]
    return {'schema':'okf-demo-one-observation.v1','new_answer_invocations':4,'additional_calls_permitted':0,
            'results':results,'boundary':'Mechanical output and exact quotation checks only; semantic claim review is separate. No actual subscription cost or token-saving claim.'}


if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    data=demo.encoded(observe());target=demo.OUT/'observations.json'
    if a.check: assert target.read_bytes()==data
    else: target.write_bytes(data)
    print(json.dumps({'status':'observations-reproduced' if a.check else 'observations-written','answer_calls':0}))
