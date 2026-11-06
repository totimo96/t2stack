#!/usr/bin/env python3
"""Prepare an issue plan; enforce numeric scores and human UX gates. No network writes."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from urllib.parse import quote

UX_THRESHOLD = 7
DECISIONS = {'confirmed', 'rejected', 'inconclusive', 'obsolete', 'duplicate'}


def require_text(record, key):
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Missing nonempty text: ' + key)
    return value


def score(record, key, unknown=False):
    value = record.get(key)
    if unknown and key in record and value is None:
        return None
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 10:
        raise ValueError(key + ' must be a finite number from 0 to 10' + (' or null' if unknown else ''))
    return value


def sha(record, key, sizes):
    value = require_text(record, key)
    if len(value) not in sizes or not re.fullmatch('[0-9a-f]+', value):
        raise ValueError('Invalid hash: ' + key)
    return value


def path(value):
    if not isinstance(value, str) or not value:
        raise ValueError('Missing relative path')
    item = PurePosixPath(value)
    if item.is_absolute() or '..' in item.parts or str(item) == '.' or '\\' in value:
        raise ValueError('Expected repository-relative path: ' + value)
    return str(item)


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()


def text_list(record, key):
    values = record.get(key)
    if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
        raise ValueError('Need a nonempty text list: ' + key)
    return values


def prepare(record, repository):
    if not isinstance(record, dict) or record.get('schema') != 1:
        raise ValueError('Unsupported validation record')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*', repository):
        raise ValueError('Expected explicit owner/repository')
    if record.get('repository', '').lower() != repository.lower():
        raise ValueError('Record and target repository differ')
    decision = record.get('decision')
    if decision not in DECISIONS:
        raise ValueError('Unsupported decision')
    kind = record.get('kind')
    if kind not in ('bug', 'security'):
        raise ValueError('Unsupported finding kind')
    for key in ('finding_id', 'slice_id', 'report_run_id', 'reason'):
        require_text(record, key)
    for key in ('report_commit', 'validation_commit'):
        sha(record, key, (40, 64))
    sha(record, 'report_sha256', (64,))
    path(record.get('report_path'))
    result = {'schema': 1, 'repository': repository, 'decision': decision,
              'finding_id': record['finding_id'], 'create_issue': False,
              'reason': record['reason'], 'required_labels': []}
    if decision in ('rejected', 'inconclusive', 'obsolete'):
        return {**result, 'action': 'record_only'}

    for key in ('title', 'cause_key', 'evidence', 'counter_evidence', 'reproduction',
                'severity_reason', 'ux_existing_reason', 'ux_change_reason',
                'fix_plan', 'alternative', 'risks'):
        require_text(record, key)
    if record.get('confidence') not in ('high', 'medium'):
        raise ValueError('A validated finding needs high or medium evidence confidence')
    severity = score(record, 'severity_score')
    if severity == 0:
        raise ValueError('A validated finding must have a nonzero severity')
    existing = score(record, 'ux_existing_score', unknown=True)
    change = score(record, 'ux_change_score', unknown=True)
    human = existing is None or change is None or max(existing, change) >= UX_THRESHOLD
    gate_reason = ('Hohe oder unklare UX-Auswirkung; explizite menschliche Freigabe vor Umsetzung erforderlich.'
                   if human else 'Beide UX-Auswirkungen bekannt und unter 7/10; keine UX-bedingte menschliche Freigabe erforderlich.')
    locations = record.get('locations')
    if not isinstance(locations, list) or not locations:
        raise ValueError('Need concrete source locations')
    normalized = []
    for item in locations:
        if not isinstance(item, dict):
            raise ValueError('Invalid source location')
        normalized.append({'path': path(item.get('path')), 'symbol': require_text(item, 'symbol')})
    acceptance = text_list(record, 'acceptance_criteria')
    regression = text_list(record, 'regression_tests')
    blockers = record.get('publication_blockers', [])
    if not isinstance(blockers, list) or any(not isinstance(v, str) or not v.strip() for v in blockers):
        raise ValueError('publication_blockers must be a list of nonempty text')
    if human:
        require_text(record, 'human_decision')
    if decision == 'duplicate':
        url = require_text(record, 'existing_issue')
        if not re.fullmatch(r'https://github\.com/' + re.escape(repository) + r'/issues/[1-9][0-9]*', url, re.IGNORECASE):
            raise ValueError('Duplicate must reference an issue in the target repository')
        result['existing_issue'] = url

    fingerprint = canonical_hash({'repository': repository.lower(), 'cause_key': record['cause_key'],
                                  'locations': sorted(normalized, key=lambda x: (x['path'], x['symbol']))})
    plan_hash = canonical_hash({key: record[key] for key in (
        'fix_plan', 'alternative', 'risks', 'acceptance_criteria', 'regression_tests',
        'ux_existing_score', 'ux_existing_reason', 'ux_change_score', 'ux_change_reason')})
    severity_name = 'critical' if severity > 8 else 'high' if severity > 6 else 'medium' if severity > 3 else 'low'
    labels = ['softwarefabric:validated', 'softwarefabric:' + kind, 'softwarefabric:severity-' + severity_name]
    if human:
        labels.append('softwarefabric:needs-human-approval')
    labels.append('softwarefabric:blocked' if human or blockers else 'softwarefabric:ready-for-implementation')
    metadata = {'schema': 1, 'finding_id': record['finding_id'], 'fingerprint': fingerprint,
                'slice_id': record['slice_id'], 'kind': kind, 'validation_decision': decision,
                'report_sha256': record['report_sha256'], 'validation_commit': record['validation_commit'],
                'severity_score': severity, 'ux_existing_score': existing, 'ux_change_score': change,
                'solution_sha256': plan_hash, 'ux_threshold': UX_THRESHOLD,
                'human_approval_required': human, 'human_approval_status': 'pending' if human else 'not_required',
                'implementation_status': 'blocked' if human or blockers else 'ready',
                'publication_blockers': blockers}
    encoded = json.dumps(metadata, ensure_ascii=False, indent=2).replace('<', '\\u003c')
    issue_metadata = '<!-- softwarefabric:issue -->\n```json\n' + encoded + '\n```\n<!-- /softwarefabric:issue -->'
    values = {key: str(value) for key, value in record.items()}
    values.update({
        'human_banner': '**MENSCHLICHE FREIGABE ERFORDERLICH — Umsetzung gesperrt.**' if human else '',
        'issue_metadata': issue_metadata, 'human_required': 'ja' if human else 'nein', 'gate_reason': gate_reason,
        'human_question': '**An den Menschen:** ' + record['human_decision'] if human else 'Andere Umsetzungsblocker weiterhin prüfen.',
        'ux_existing_score': 'unklar' if existing is None else str(existing),
        'ux_change_score': 'unklar' if change is None else str(change),
        'locations': '\n'.join('- [' + item['path'].replace(']', '\\]') + '](https://github.com/' + repository + '/blob/'
                               + record['validation_commit'] + '/' + quote(item['path'], safe='/') + ') — `' + item['symbol'].replace('`', '') + '`'
                               for item in normalized),
        'acceptance_criteria': '\n'.join('- [ ] ' + value for value in acceptance),
        'regression_tests': '\n'.join('- ' + value for value in regression),
    })
    template = Path(__file__).parents[1] / 'assets/issue.template.md'
    # One substitution pass prevents user text from expanding template markers.
    body = re.sub(r'\{([a-z_]+)\}', lambda match: values[match.group(1)], template.read_text(encoding='utf-8'))
    title = ('[MENSCHLICHE FREIGABE ERFORDERLICH] ' if human else '') + f'[{kind}][{severity:g}/10] ' + record['title']
    return {**result, 'action': 'publication_blocked' if blockers else 'link_existing' if decision == 'duplicate' else 'create',
            'create_issue': decision == 'confirmed' and not blockers, 'fingerprint': fingerprint,
            'human_approval_required': human, 'implementation_status': metadata['implementation_status'],
            'solution_sha256': plan_hash, 'required_labels': labels, 'title': title[:240], 'body': body}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', required=True)
    parser.add_argument('--repository', required=True)
    args = parser.parse_args()
    try:
        record = json.loads(Path(args.record).read_text(encoding='utf-8'))
        result = prepare(record, args.repository)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({'status': 'blocked', 'create_issue': False, 'reason': str(error)}))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
