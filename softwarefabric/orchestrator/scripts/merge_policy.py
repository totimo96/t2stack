#!/usr/bin/env python3
"""Read-only orchestrator merge decision. Live observations remain the caller's job."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'implement-loop/scripts'))
from loop_policy import issue_gate, numeric, review_gate, nonempty
from role_profile import load

THRESHOLD = 7


def decide(snapshot, profile):
    """Require current quality, issue and repository gates before agent merging."""
    quality = review_gate(snapshot, profile)
    reasons = list(quality['reasons'])
    issue = snapshot.get('issue')
    if not isinstance(issue, dict):
        reasons.append('current_issue_missing')
    else:
        gate = issue_gate(issue, snapshot.get('repository'))
        if gate['status'] != 'eligible' or issue.get('url') != snapshot.get('issue_url'):
            reasons.append('current_issue_gate_not_clear')
    if snapshot.get('is_draft') is not False:
        reasons.append('pr_still_draft')
    # These are externally verified observations, not permission granted by JSON.
    for key in ('repository_rules_verified', 'repository_allows_agent_merge',
                'required_human_reviews_satisfied', 'issue_plan_matches_current_code'):
        if snapshot.get(key) is not True:
            reasons.append(key + '_not_proven')
    risks, impacts = [], []
    reviews = snapshot.get('reviews', [])
    if not isinstance(reviews, list):
        reviews = []
    for review in reviews:
        if not isinstance(review, dict):
            continue
        if review.get('risk_comment_verified') is not True:
            reasons.append('risk_scores_not_verified_in_pr_comment')
        for field, values in (('merge_risk_score', risks), ('system_impact_score', impacts)):
            score = review.get(field)
            if not numeric(score, 1, 10) or not nonempty(review.get(field.removesuffix('_score') + '_reason')):
                reasons.append('missing_or_invalid_' + field)
            else:
                values.append(score)
    complete = len(reviews) == len(risks) == len(impacts) == 2
    if not complete:
        reasons.append('risk_assessment_incomplete')
    risk = max(risks) if complete else None
    impact = max(impacts) if complete else None
    if reasons:
        status = 'blocked'
    elif risk >= THRESHOLD or impact >= THRESHOLD:
        status = 'human_review_required'
    else:
        status = 'agent_merge_allowed'
    labels = ['softwarefabric:' + {'blocked':'merge-blocked',
              'human_review_required':'needs-human-merge-review',
              'agent_merge_allowed':'agent-merge-allowed'}[status]]
    if complete:
        labels += [f'softwarefabric:merge-risk-{risk:g}', f'softwarefabric:system-impact-{impact:g}']
    # Even when another gate blocks, a high/unknown risk visibly requires a human.
    if not complete or risk >= THRESHOLD or impact >= THRESHOLD:
        if 'softwarefabric:needs-human-merge-review' not in labels:
            labels.append('softwarefabric:needs-human-merge-review')
    return {'status':status, 'agent_may_merge':status == 'agent_merge_allowed',
            'merge_risk_score':risk, 'system_impact_score':impact,
            'reasons':sorted(set(reasons)), 'labels':labels,
            'base_sha':snapshot.get('base_sha'), 'head_sha':snapshot.get('head_sha'),
            'diff_sha256':snapshot.get('diff_sha256'), 'profile_sha256':snapshot.get('profile_sha256')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--profile', required=True)
    args = parser.parse_args()
    try:
        result = decide(json.loads(Path(args.input).read_text()), load(args.profile))
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as error:
        print(json.dumps({'status':'blocked','agent_may_merge':False,'reason':str(error)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
