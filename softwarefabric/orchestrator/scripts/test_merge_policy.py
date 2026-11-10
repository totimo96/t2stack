"""Merge authority boundaries. No network, GitHub writes or real merges."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'implement-loop/scripts'))
from test_loop_policy import pr, issue
from merge_policy import decide
from role_profile import load, digest


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.profile = load()
        self.snapshot = pr()
        self.snapshot.update(is_draft=False, profile_sha256=digest(self.profile),
                             issue=issue(), repository_rules_verified=True,
                             repository_allows_agent_merge=True,
                             required_human_reviews_satisfied=True,
                             issue_plan_matches_current_code=True)
        for review in self.snapshot['reviews']:
            review.update(risk_comment_verified=True, merge_risk_score=3, merge_risk_reason='Bounded integration; reproduced and tested.',
                          system_impact_score=4, system_impact_reason='One user flow with known callers.')

    def decision(self):
        return decide(self.snapshot, self.profile)

    def test_low_scores_allow_agent_after_existing_gates(self):
        result = self.decision()
        self.assertTrue(result['agent_may_merge'])
        self.assertEqual(result['status'], 'agent_merge_allowed')
        self.assertIn('softwarefabric:merge-risk-3', result['labels'])
        self.assertEqual(result['head_sha'], self.snapshot['head_sha'])

    def test_exact_seven_requires_human_in_either_dimension(self):
        for field in ('merge_risk_score', 'system_impact_score'):
            with self.subTest(field=field):
                snapshot = deepcopy(self.snapshot)
                snapshot['reviews'][0][field] = 7
                result = decide(snapshot, self.profile)
                self.assertFalse(result['agent_may_merge'])
                self.assertEqual(result['status'], 'human_review_required')
                self.assertIn('softwarefabric:needs-human-merge-review', result['labels'])

    def test_higher_member_score_not_mean_or_favorable_member(self):
        self.snapshot['reviews'][0].update(merge_risk_score=1, system_impact_score=8)
        self.snapshot['reviews'][1].update(merge_risk_score=9, system_impact_score=1)
        result = self.decision()
        self.assertEqual((result['merge_risk_score'], result['system_impact_score']), (9, 8))
        self.assertFalse(result['agent_may_merge'])

    def test_decimal_just_below_boundary_allowed(self):
        self.snapshot['reviews'][0]['merge_risk_score'] = 6.9
        self.assertTrue(self.decision()['agent_may_merge'])

    def test_invalid_unknown_and_out_of_range_scores_fail_closed(self):
        for value in (None, True, 0, 10.1, -1, '2', math.nan, math.inf):
            with self.subTest(value=value):
                snapshot = deepcopy(self.snapshot)
                snapshot['reviews'][1]['merge_risk_score'] = value
                result = decide(snapshot, self.profile)
                self.assertFalse(result['agent_may_merge'])
                self.assertEqual(result['status'], 'blocked')
                self.assertIn('softwarefabric:needs-human-merge-review', result['labels'])

    def test_unpublished_risk_scores_do_not_authorize_merge(self):
        self.snapshot['reviews'][0].pop('risk_comment_verified')
        self.assertFalse(self.decision()['agent_may_merge'])

    def test_missing_reason_blocks(self):
        self.snapshot['reviews'][0]['system_impact_reason'] = ' '
        self.assertFalse(self.decision()['agent_may_merge'])

    def test_stale_review_blocks(self):
        self.snapshot['head_sha'] = 'd' * 40
        self.assertFalse(self.decision()['agent_may_merge'])

    def test_wrong_profile_blocks(self):
        self.snapshot['profile_sha256'] = 'a' * 64
        self.assertFalse(self.decision()['agent_may_merge'])

    def test_quality_gate_still_applies(self):
        self.snapshot['reviews'][0]['score'] = 9.4
        self.assertFalse(self.decision()['agent_may_merge'])

    def test_repository_and_live_gates_unknown_or_false_block(self):
        for field in ('repository_rules_verified', 'repository_allows_agent_merge',
                      'required_human_reviews_satisfied', 'issue_plan_matches_current_code',
                      'checks_passed', 'required_checks_passed', 'mergeable', 'branch_up_to_date'):
            for value in (False, None):
                with self.subTest(field=field, value=value):
                    snapshot = deepcopy(self.snapshot)
                    snapshot[field] = value
                    self.assertFalse(decide(snapshot, self.profile)['agent_may_merge'])

    def test_human_changes_requested_blocks(self):
        self.snapshot['unresolved_human_changes_requested'] = True
        self.assertFalse(self.decision()['agent_may_merge'])

    def test_draft_or_closed_pr_blocks(self):
        self.snapshot['is_draft'] = True
        self.assertFalse(self.decision()['agent_may_merge'])
        self.snapshot.update(is_draft=False, state='CLOSED')
        self.assertFalse(self.decision()['agent_may_merge'])

    def test_ux_gate_not_overridden_by_low_merge_scores(self):
        self.snapshot['issue'] = issue(ux=8)
        self.assertFalse(self.decision()['agent_may_merge'])

    def test_missing_wrong_or_closed_issue_blocks(self):
        for value in (None, issue(2), {**issue(), 'state':'CLOSED'}):
            with self.subTest(value=value):
                self.snapshot['issue'] = value
                self.assertFalse(self.decision()['agent_may_merge'])

    def test_absent_or_partial_review_blocks(self):
        for value in (None, [], self.snapshot['reviews'][:1]):
            self.snapshot['reviews'] = value
            self.assertFalse(self.decision()['agent_may_merge'])

    def test_high_risk_still_visible_when_ci_blocks(self):
        self.snapshot['reviews'][0]['merge_risk_score'] = 9
        self.snapshot['checks_passed'] = False
        result = self.decision()
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('softwarefabric:needs-human-merge-review', result['labels'])
        self.assertNotIn('softwarefabric:agent-merge-allowed', result['labels'])

    def test_pure_decision_does_not_modify_snapshot(self):
        before = deepcopy(self.snapshot)
        self.decision()
        self.assertEqual(self.snapshot, before)
