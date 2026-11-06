"""Queue, permission and review binding tests. No live PRs or agents are started."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from loop_policy import issue_gate, review_gate, review_payload, select_issue

ROOT = Path(__file__).parents[2]
SPEC = importlib.util.spec_from_file_location('issue_policy', ROOT / 'validate-findings/scripts/issue_policy.py')
ISSUE_POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ISSUE_POLICY)


def issue(number=1, severity=6, ux=2):
    record = json.loads((ROOT / 'validate-findings/assets/validation-record.example.json').read_text())
    record.update(severity_score=severity, ux_change_score=ux, human_decision='Mensch muss den Plan freigeben.')
    plan = ISSUE_POLICY.prepare(record, 'example/project')
    return {'number': number, 'url': f'https://github.com/example/project/issues/{number}',
            'state': 'OPEN', 'body': plan['body'], 'labels': plan['required_labels']}


def pr(issue_number=1):
    data = {'repository': 'example/project', 'number': 10,
            'url': 'https://github.com/example/project/pull/10',
            'issue_url': f'https://github.com/example/project/issues/{issue_number}',
            'base_sha': 'a' * 40, 'head_sha': 'b' * 40, 'diff_sha256': 'c' * 64,
            'state': 'OPEN', 'is_draft': True, 'checks_passed': True,
            'required_checks_passed': True, 'checks_head_sha': 'b' * 40,
            'mergeable': True, 'branch_up_to_date': True, 'unresolved_human_changes_requested': False,
            'known_blocking_findings': [], 'latest_round': 1, 'reviews': []}
    for model, provider, options in (
        ('gpt-6.1-sol', 'codex', {'reasoningEffort': 'high'}),
        ('claude-opus-5-5', 'claudeAgent', {'effort': 'high'}),
    ):
        data['reviews'].append({'model': model, 'provider': provider, 'options': options,
            'round': 1, 'base_sha': data['base_sha'], 'head_sha': data['head_sha'],
            'diff_sha256': data['diff_sha256'], 'score': 9.5,
            'recommendation': 'approve', 'blocking_findings': [],
            'comment_url': data['url'] + '#issuecomment-' + str(len(data['reviews']) + 1),
            'comment_verified': True})
    return data


class QueueTests(unittest.TestCase):
    def select(self, *items):
        return select_issue({'repository': 'example/project', 'issues': list(items)})

    def test_highest_severity_first(self):
        self.assertEqual(self.select(issue(1, 4), issue(2, 9), issue(3, 7))['next']['number'], 2)

    def test_severity_tie_uses_smallest_issue_number(self):
        self.assertEqual(self.select(issue(9, 8), issue(2, 8))['next']['number'], 2)

    def test_high_severity_blocked_issue_does_not_starve_others(self):
        result = self.select(issue(1, 10, ux=9), issue(2, 6))
        self.assertEqual(result['next']['number'], 2)
        self.assertEqual(result['blocked'][0]['number'], 1)

    def test_required_approval_cannot_be_replaced_by_ready_label(self):
        item = issue(ux=9)
        item['labels'] = [value for value in item['labels'] if value not in ('softwarefabric:blocked', 'softwarefabric:needs-human-approval')]
        item['labels'].append('softwarefabric:ready-for-implementation')
        self.assertEqual(issue_gate(item, 'example/project')['status'], 'blocked')

    def test_consistent_external_human_receipt_allows_approved_plan(self):
        item = issue(ux=9)
        meta = __import__('loop_policy').issue_metadata(item['body'])
        updated = deepcopy(meta)
        updated.update(implementation_status='ready', human_approval_status='approved')
        item['body'] = item['body'].replace(json.dumps(meta, ensure_ascii=False, indent=2), json.dumps(updated, ensure_ascii=False, indent=2))
        item['labels'] = ['softwarefabric:validated', 'softwarefabric:bug', 'softwarefabric:ready-for-implementation']
        item['approval_evidence'] = {'verified_human_channel': True, 'source': 'interactive-human',
            'actor': 'authorized-user', 'approved_at': '2026-11-06T12:00:00Z', 'evidence_ref': 'interaction:approval-1',
            'issue_url': item['url'], 'solution_sha256': meta['solution_sha256'], 'validation_commit': meta['validation_commit']}
        self.assertEqual(issue_gate(item, 'example/project')['status'], 'eligible')
        item['approval_evidence']['solution_sha256'] = 'f' * 64
        self.assertEqual(issue_gate(item, 'example/project')['status'], 'blocked')

    def test_unknown_ux_stays_blocked(self):
        self.assertEqual(self.select(issue(ux=None))['status'], 'blocked')

    def test_other_issues_and_closed_issues_are_not_worked(self):
        ordinary = {'number': 4, 'state': 'OPEN', 'labels': ['bug'], 'body': 'ordinary'}
        closed = issue(2)
        closed['state'] = 'CLOSED'
        result = self.select(ordinary, closed)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(result['ignored']), 2)

    def test_malformed_metadata_fails_closed(self):
        item = issue()
        item['body'] = '<!-- softwarefabric:issue -->invalid'
        self.assertEqual(self.select(item)['status'], 'blocked')

    def test_already_reviewed_pr_awaits_merge_instead_of_reimplementation(self):
        item = issue()
        data = pr()
        data['is_draft'] = False
        item['linked_pr'] = data
        result = self.select(item)
        self.assertEqual(result['status'], 'awaiting_merge')
        self.assertIsNone(result['next'])

    def test_existing_draft_is_resumed(self):
        item = issue()
        item['linked_pr'] = pr()
        self.assertEqual(self.select(item)['next']['action'], 'resume_pr')

    def test_another_issues_pr_cannot_satisfy_delivery(self):
        item = issue(2)
        item['linked_pr'] = pr(1)
        self.assertEqual(self.select(item)['status'], 'blocked')

    def test_unchanged_failed_attempt_is_not_immediately_repeated(self):
        item = issue()
        item['deferred_for_current_snapshot'] = True
        self.assertEqual(self.select(item)['status'], 'blocked')


class ReviewGateTests(unittest.TestCase):
    def test_both_members_at_threshold_pass(self):
        self.assertTrue(review_gate(pr())['passed'])

    def test_average_cannot_hide_a_lower_individual_score(self):
        data = pr()
        data['reviews'][0]['score'], data['reviews'][1]['score'] = 9, 10
        self.assertFalse(review_gate(data)['passed'])

    def test_scores_are_not_rounded_up(self):
        data = pr()
        data['reviews'][0]['score'] = 9.49
        self.assertFalse(review_gate(data)['passed'])

    def test_missing_member_or_third_member_does_not_pass(self):
        for count in (1, 3):
            data = pr()
            data['reviews'] = data['reviews'][:1] if count == 1 else data['reviews'] + [deepcopy(data['reviews'][0])]
            self.assertFalse(review_gate(data)['passed'])

    def test_replacement_model_or_wrong_effort_does_not_pass(self):
        for field, value in (('model', 'replacement'), ('provider', 'other'), ('options', {'reasoningEffort': 'low'})):
            data = pr()
            data['reviews'][0][field] = value
            self.assertFalse(review_gate(data)['passed'])

    def test_old_head_base_or_diff_never_passes(self):
        for key, value in (('head_sha', 'd' * 40), ('base_sha', 'd' * 40), ('diff_sha256', 'd' * 64)):
            data = pr()
            data[key] = value
            self.assertFalse(review_gate(data)['passed'])

    def test_mixed_or_old_rounds_do_not_pass(self):
        data = pr()
        data['reviews'][0]['round'] = 2
        self.assertFalse(review_gate(data)['passed'])
        data = pr()
        data['latest_round'] = 2
        self.assertFalse(review_gate(data)['passed'])

    def test_unposted_or_wrong_pr_review_does_not_pass(self):
        data = pr()
        data['reviews'][0]['comment_verified'] = False
        self.assertFalse(review_gate(data)['passed'])
        data = pr()
        data['reviews'][0]['comment_url'] = 'https://github.com/example/project/pull/99#issuecomment-1'
        self.assertFalse(review_gate(data)['passed'])

    def test_high_score_does_not_override_findings_or_checks(self):
        changes = [('required_checks_passed', False), ('checks_passed', False), ('mergeable', False), ('branch_up_to_date', False),
                   ('unresolved_human_changes_requested', True), ('known_blocking_findings', ['regression'])]
        for key, value in changes:
            data = pr()
            data[key] = value
            self.assertFalse(review_gate(data)['passed'])
        data = pr()
        data['reviews'][0]['blocking_findings'] = ['bug']
        self.assertFalse(review_gate(data)['passed'])

    def test_missing_invalid_or_nonnumeric_scores_do_not_pass(self):
        for value in (None, True, '9.5', float('nan'), 11):
            data = pr()
            data['reviews'][0]['score'] = value
            self.assertFalse(review_gate(data)['passed'])

    def test_payload_excludes_internal_target_and_parent_history(self):
        data = pr()
        data.update(target_grade=9.5, parent_history='private internal policy', acceptance_criteria=['Functional numeric threshold is 9.5.'])
        data['checks'] = [{'command': 'pytest', 'result': 'passed', 'internal_target_grade': 9.5}]
        payload = review_payload(data)
        self.assertNotIn('target_grade', payload)
        self.assertNotIn('parent_history', payload)
        self.assertNotIn('internal_target_grade', payload['checks'][0])
        self.assertEqual(payload['acceptance_criteria'], data['acceptance_criteria'])

    def test_cli_is_read_only(self):
        helper = str(Path(__file__).with_name('loop_policy.py'))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'pr.json'
            source.write_text(json.dumps(pr()))
            original = source.read_bytes()
            result = subprocess.run([sys.executable, helper, 'review-gate', '--input', str(source)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)['passed'])
            self.assertEqual(source.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
