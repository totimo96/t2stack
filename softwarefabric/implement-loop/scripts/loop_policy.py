#!/usr/bin/env python3
"""Read-only Softwarefabric queue, neutral review payload and PR release gates."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from role_profile import load as load_profile, digest as profile_digest, members as profile_members
from urllib.parse import urlsplit

MIN_COUNCIL_SCORE = 9.5  # Parent-only policy; never part of review_payload().
MEMBERS = {
    'gpt-6.1-sol': ('codex', {'reasoningEffort': 'high'}),
    'claude-opus-5-5': ('claudeAgent', {'effort': 'high'}),
}


def numeric(value, low=0, high=10):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def sha(value, sizes=(40, 64)):
    return isinstance(value, str) and len(value) in sizes and re.fullmatch('[0-9a-f]+', value) is not None


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def issue_metadata(body):
    start, end = '<!-- softwarefabric:issue -->', '<!-- /softwarefabric:issue -->'
    if not isinstance(body, str) or body.count(start) != 1 or body.count(end) != 1:
        raise ValueError('Need one Softwarefabric issue block')
    match = re.search(re.escape(start) + r'\s*```json\s*([\s\S]*?)\s*```\s*' + re.escape(end), body)
    if not match:
        raise ValueError('Malformed Softwarefabric issue block')
    value = json.loads(match.group(1))
    if not isinstance(value, dict) or value.get('schema') != 1:
        raise ValueError('Unsupported Softwarefabric issue metadata')
    return value


def url_matches(value, repository, kind, number):
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return parsed.scheme == 'https' and parsed.netloc == 'github.com' and parsed.path.lower() == f'/{repository}/{kind}/{number}'.lower()


def review_payload(snapshot):
    """Allowlist task data. Caller must supply factual context, not target grades."""
    keys = ('repository', 'number', 'url', 'base_sha', 'head_sha', 'diff_sha256',
            'issue_url', 'diff_artifact', 'acceptance_criteria', 'change_summary', 'checks')
    payload = {key: snapshot[key] for key in keys if key in snapshot}
    if isinstance(payload.get('checks'), list):
        allowed = ('name', 'command', 'result', 'exit_code', 'head_sha', 'evidence_url')
        payload['checks'] = [{key: item[key] for key in allowed if key in item}
                             if isinstance(item, dict) else item for item in payload['checks']]
    return payload


def review_gate(snapshot, profile=None):
    reasons = []
    members = MEMBERS if profile is None else profile_members(profile)
    if profile is not None and snapshot.get("profile_sha256") != profile_digest(profile):
        reasons.append("role_profile_not_bound")
    repository, number = snapshot.get('repository'), snapshot.get('number')
    if type(number) is not int or number < 1 or not url_matches(snapshot.get('url'), repository, 'pull', number):
        reasons.append('invalid_pr_url')
    parsed_issue = urlsplit(snapshot.get('issue_url', ''))
    if (parsed_issue.scheme != 'https' or parsed_issue.netloc != 'github.com'
            or not re.fullmatch('/' + re.escape(str(repository)) + r'/issues/[1-9][0-9]*', parsed_issue.path, re.IGNORECASE)):
        reasons.append('invalid_issue_reference')
    for key in ('base_sha', 'head_sha'):
        if not sha(snapshot.get(key)):
            reasons.append('invalid_' + key)
    if not sha(snapshot.get('diff_sha256'), (64,)):
        reasons.append('invalid_diff_hash')
    if str(snapshot.get('state', '')).upper() != 'OPEN':
        reasons.append('pr_not_open')
    if snapshot.get('checks_passed') is not True or snapshot.get('required_checks_passed') is not True:
        reasons.append('checks_not_proven_passed')
    if snapshot.get('checks_head_sha') != snapshot.get('head_sha'):
        reasons.append('checks_not_for_current_head')
    if snapshot.get('unresolved_human_changes_requested') is not False:
        reasons.append('human_review_not_clear')
    if snapshot.get('mergeable') is not True:
        reasons.append('mergeability_not_clear')
    if snapshot.get('branch_up_to_date') is not True:
        reasons.append('branch_not_proven_current_with_base')
    if snapshot.get('known_blocking_findings') != []:
        reasons.append('known_blocking_findings_not_clear')
    if type(snapshot.get('latest_round')) is not int or snapshot['latest_round'] < 1:
        reasons.append('latest_round_unknown')
    reviews = snapshot.get('reviews')
    if not isinstance(reviews, list) or len(reviews) != len(members):
        return {'passed': False, 'reasons': reasons + ['need_exactly_two_council_reviews']}
    seen, rounds, scores = set(), set(), []
    for review in reviews:
        if not isinstance(review, dict):
            reasons.append('invalid_review_record')
            continue
        model = review.get('model')
        if model not in members or model in seen:
            reasons.append('missing_duplicate_or_unexpected_member')
            continue
        seen.add(model)
        provider, options = members[model]
        if review.get('provider') != provider or review.get('options') != options:
            reasons.append('wrong_member_configuration:' + model)
        if type(review.get('round')) is not int or review['round'] < 1:
            reasons.append('invalid_round:' + model)
        else:
            rounds.add(review['round'])
            if review['round'] != snapshot.get('latest_round'):
                reasons.append('not_latest_round:' + model)
        if any(review.get(key) != snapshot.get(key) for key in ('base_sha', 'head_sha', 'diff_sha256')):
            reasons.append('stale_review:' + model)
        score = review.get('score')
        if not numeric(score):
            reasons.append('missing_or_invalid_score:' + model)
        else:
            scores.append(score)
            if score < MIN_COUNCIL_SCORE:
                reasons.append('score_gate_not_met:' + model)
        if review.get('recommendation') != 'approve' or review.get('blocking_findings') != []:
            reasons.append('review_not_clear:' + model)
        parsed = urlsplit(review.get('comment_url', ''))
        if (not url_matches(review.get('comment_url'), repository, 'pull', number)
                or not parsed.fragment.startswith(('issuecomment-', 'pullrequestreview-', 'discussion_r'))
                or review.get('comment_verified') is not True):
            reasons.append('review_comment_not_verified:' + model)
    if seen != set(members) or len(rounds) != 1:
        reasons.append('members_or_round_incomplete')
    return {'passed': not reasons, 'reasons': reasons,
            'lowest_overall_score': min(scores) if len(scores) == len(members) else None}


def issue_gate(issue, repository):
    labels = {item['name'] if isinstance(item, dict) else item for item in issue.get('labels', [])}
    body = issue.get('body', '')
    if 'softwarefabric:validated' not in labels and '<!-- softwarefabric:issue -->' not in body:
        return {'status': 'ignored', 'reason': 'not_pipeline_issue'}
    if str(issue.get('state', '')).upper() != 'OPEN':
        return {'status': 'ignored', 'reason': 'issue_closed'}
    if (type(issue.get('number')) is not int or issue['number'] < 1
            or not url_matches(issue.get('url'), repository, 'issues', issue.get('number'))):
        return {'status': 'blocked', 'reason': 'wrong_repository_or_issue_url'}
    try:
        meta = issue_metadata(body)
    except (ValueError, TypeError):
        return {'status': 'blocked', 'reason': 'invalid_issue_metadata'}
    severity = meta.get('severity_score')
    if not numeric(severity) or severity == 0:
        return {'status': 'blocked', 'reason': 'invalid_severity'}
    if (meta.get('validation_decision') not in ('confirmed', 'duplicate')
            or meta.get('kind') not in ('bug', 'security')
            or not all(sha(meta.get(key), (64,)) for key in ('fingerprint', 'report_sha256', 'solution_sha256'))
            or not sha(meta.get('validation_commit')) or not nonempty(meta.get('finding_id'))):
        return {'status': 'blocked', 'reason': 'validation_provenance_incomplete'}
    expected_labels = {'softwarefabric:validated', 'softwarefabric:' + meta['kind']}
    if not expected_labels.issubset(labels):
        return {'status': 'blocked', 'reason': 'validation_labels_inconsistent'}
    ux = [meta.get('ux_existing_score'), meta.get('ux_change_score')]
    if any(value is not None and not numeric(value) for value in ux):
        return {'status': 'blocked', 'reason': 'invalid_ux_scores'}
    required = any(value is None or value >= 7 for value in ux)
    if meta.get('human_approval_required') is not required:
        return {'status': 'blocked', 'reason': 'ux_gate_inconsistent'}
    if ('softwarefabric:blocked' in labels or 'softwarefabric:needs-human-approval' in labels
            or 'softwarefabric:ready-for-implementation' not in labels
            or meta.get('implementation_status') != 'ready' or meta.get('publication_blockers') != []):
        return {'status': 'blocked', 'reason': 'implementation_gate_blocked'}
    if required:
        proof = issue.get('approval_evidence', {})
        if (meta.get('human_approval_status') != 'approved'
                or proof.get('verified_human_channel') is not True
                or proof.get('source') not in ('interactive-human', 'designated-human-review')
                or not all(nonempty(proof.get(key)) for key in ('actor', 'approved_at', 'evidence_ref'))
                or proof.get('solution_sha256') != meta['solution_sha256']
                or proof.get('validation_commit') != meta['validation_commit']
                or proof.get('issue_url') != issue['url']):
            return {'status': 'blocked', 'reason': 'human_approval_not_verified_for_this_plan'}
    elif meta.get('human_approval_status') != 'not_required':
        return {'status': 'blocked', 'reason': 'approval_status_inconsistent'}
    return {'status': 'eligible', 'severity_score': severity, 'metadata': meta}


def select_issue(snapshot, profile=None):
    repository = snapshot.get('repository')
    if not isinstance(repository, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Need explicit owner/repository')
    eligible, blocked, delivered, ignored = [], [], [], []
    for issue in snapshot.get('issues', []):
        result = issue_gate(issue, repository)
        entry = {'number': issue.get('number'), 'url': issue.get('url'), **result}
        if result['status'] == 'ignored':
            ignored.append(entry)
        elif result['status'] == 'blocked':
            blocked.append(entry)
        elif issue.get('deferred_for_current_snapshot') is True:
            blocked.append({**entry, 'status': 'blocked', 'reason': 'already_attempted_without_new_evidence'})
        else:
            pr = issue.get('linked_pr')
            if pr and (pr.get('repository', '').lower() != repository.lower() or pr.get('issue_url') != issue['url']):
                blocked.append({**entry, 'status': 'blocked', 'reason': 'linked_pr_not_bound_to_issue'})
                continue
            if pr and pr.get('state', '').upper() == 'OPEN' and review_gate(pr, profile)['passed'] and pr.get('is_draft') is False:
                delivered.append({**entry, 'status': 'awaiting_merge', 'pr_url': pr['url']})
            elif pr and pr.get('state', '').upper() == 'MERGED':
                blocked.append({**entry, 'status': 'blocked', 'reason': 'merged_pr_but_issue_still_open'})
            else:
                eligible.append({**entry, 'action': 'resume_pr' if pr and pr.get('state', '').upper() == 'OPEN' else 'implement',
                                 'pr_url': pr.get('url') if pr else None})
    eligible.sort(key=lambda entry: (-entry['severity_score'], entry['number']))
    status = 'selected' if eligible else 'blocked' if blocked else 'awaiting_merge' if delivered else 'complete'
    return {'status': status, 'next': eligible[0] if eligible else None,
            'eligible_count': len(eligible), 'blocked': blocked, 'awaiting_merge': delivered, 'ignored': ignored}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('select', 'review-gate', 'review-payload'))
    parser.add_argument('--input', required=True)
    parser.add_argument('--profile', help='Frozen orchestrator role profile')
    args = parser.parse_args()
    try:
        value = json.loads(Path(args.input).read_text(encoding='utf-8'))
        profile = load_profile(args.profile) if args.profile else None
        result = review_payload(value) if args.action == 'review-payload' else {'select':select_issue, 'review-gate':review_gate}[args.action](value, profile)
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as error:
        print(json.dumps({'status': 'blocked', 'reason': str(error)}))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
