"""Local policy tests; no GitHub issues or network calls are made."""
from copy import deepcopy
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from issue_policy import prepare


class IssuePolicyTests(unittest.TestCase):
    def setUp(self):
        example = Path(__file__).parents[1] / 'assets/validation-record.example.json'
        self.record = json.loads(example.read_text())

    def plan(self, **updates):
        record = deepcopy(self.record)
        record.update(updates)
        return prepare(record, 'example/project')

    def metadata(self, plan):
        match = re.search(r'<!-- softwarefabric:issue -->\s*```json\s*(.*?)\s*```', plan['body'], re.S)
        return json.loads(match.group(1))

    def test_low_ux_confirmed_finding_is_ready(self):
        plan = self.plan()
        self.assertTrue(plan['create_issue'])
        self.assertFalse(plan['human_approval_required'])
        self.assertIn('softwarefabric:ready-for-implementation', plan['required_labels'])
        self.assertNotIn('softwarefabric:blocked', plan['required_labels'])

    def test_fix_ux_at_seven_requires_human(self):
        plan = self.plan(ux_change_score=7, human_decision='Darf der Anmeldeablauf geändert werden?')
        self.assertTrue(plan['create_issue'])
        self.assertTrue(plan['human_approval_required'])
        self.assertIn('softwarefabric:needs-human-approval', plan['required_labels'])
        self.assertIn('softwarefabric:blocked', plan['required_labels'])
        self.assertNotIn('softwarefabric:ready-for-implementation', plan['required_labels'])
        self.assertTrue(plan['title'].startswith('[MENSCHLICHE FREIGABE ERFORDERLICH]'))

    def test_high_existing_ux_also_requires_human(self):
        plan = self.plan(ux_existing_score=9, human_decision='Bitte Nutzerwirkung und Plan freigeben.')
        self.assertTrue(plan['human_approval_required'])

    def test_ux_below_seven_does_not_trigger_human_gate(self):
        plan = self.plan(ux_change_score=6.5)
        self.assertFalse(plan['human_approval_required'])
        self.assertIn('softwarefabric:ready-for-implementation', plan['required_labels'])

    def test_unknown_ux_cannot_be_treated_as_zero(self):
        for field in ('ux_change_score', 'ux_existing_score'):
            with self.subTest(field=field):
                plan = self.plan(**{field: None, 'human_decision': 'Offene UX-Frage entscheiden.'})
                self.assertTrue(plan['human_approval_required'])
                self.assertEqual(self.metadata(plan)['human_approval_status'], 'pending')

    def test_missing_ux_is_invalid(self):
        self.record.pop('ux_change_score')
        with self.assertRaises(ValueError):
            prepare(self.record, 'example/project')

    def test_human_question_is_required_for_blocked_ux(self):
        with self.assertRaisesRegex(ValueError, 'human_decision'):
            self.plan(ux_change_score=8)

    def test_agent_supplied_approval_cannot_bypass_gate(self):
        plan = self.plan(ux_change_score=8, human_decision='Freigabe erforderlich.',
                         human_approval_status='approved', human_approval_required=False)
        metadata = self.metadata(plan)
        self.assertTrue(metadata['human_approval_required'])
        self.assertEqual(metadata['human_approval_status'], 'pending')
        self.assertEqual(metadata['implementation_status'], 'blocked')

    def test_high_severity_is_not_high_ux_by_itself(self):
        plan = self.plan(severity_score=10)
        self.assertFalse(plan['human_approval_required'])
        self.assertIn('softwarefabric:severity-critical', plan['required_labels'])

    def test_nonconfirmed_decisions_never_create_issues(self):
        for decision in ('rejected', 'inconclusive', 'obsolete'):
            with self.subTest(decision=decision):
                plan = self.plan(decision=decision)
                self.assertFalse(plan['create_issue'])
                self.assertEqual(plan['action'], 'record_only')
                self.assertNotIn('body', plan)

    def test_duplicate_links_existing_target_issue(self):
        plan = self.plan(decision='duplicate', existing_issue='https://github.com/example/project/issues/12')
        self.assertFalse(plan['create_issue'])
        self.assertEqual(plan['action'], 'link_existing')
        self.assertIn('existing_issue', plan)

    def test_duplicate_cannot_link_a_different_repository(self):
        with self.assertRaises(ValueError):
            self.plan(decision='duplicate', existing_issue='https://github.com/other/project/issues/12')

    def test_publication_blocker_never_emits_ready(self):
        plan = self.plan(kind='security', publication_blockers=['Private Übergabe nicht verfügbar.'])
        self.assertFalse(plan['create_issue'])
        self.assertEqual(plan['action'], 'publication_blocked')
        self.assertIn('softwarefabric:blocked', plan['required_labels'])
        self.assertNotIn('softwarefabric:ready-for-implementation', plan['required_labels'])

    def test_scores_reject_booleans_nonfinite_strings_and_out_of_range(self):
        for value in (True, False, -1, 11, math.nan, math.inf, '7'):
            for field in ('severity_score', 'ux_existing_score', 'ux_change_score'):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        self.plan(**{field: value})

    def test_zero_severity_cannot_be_confirmed(self):
        with self.assertRaises(ValueError):
            self.plan(severity_score=0)

    def test_repository_must_match_record(self):
        with self.assertRaisesRegex(ValueError, 'repository differ'):
            prepare(self.record, 'different/project')

    def test_missing_evidence_rejects_publication_plan(self):
        self.record['evidence'] = ' '
        with self.assertRaisesRegex(ValueError, 'evidence'):
            prepare(self.record, 'example/project')

    def test_source_paths_must_stay_in_repository(self):
        for value in ('/etc/passwd', '../other/file.py', 'C:\\secrets.txt'):
            with self.subTest(path=value):
                with self.assertRaises(ValueError):
                    self.plan(locations=[{'path': value, 'symbol': 'handler'}])

    def test_fingerprint_survives_score_changes_and_cross_report_kind(self):
        first = self.plan()
        second = self.plan(severity_score=5, kind='security', finding_id='SEC-001')
        self.assertEqual(first['fingerprint'], second['fingerprint'])

    def test_different_root_causes_have_different_fingerprints(self):
        self.assertNotEqual(self.plan()['fingerprint'], self.plan(cause_key='different-cause')['fingerprint'])

    def test_solution_change_invalidates_plan_binding(self):
        self.assertNotEqual(self.plan()['solution_sha256'], self.plan(fix_plan='Eine andere Umsetzung.')['solution_sha256'])

    def test_template_markers_in_evidence_are_not_interpreted(self):
        plan = self.plan(evidence='Literal {human_banner} remains evidence.')
        self.assertIn('Literal {human_banner} remains evidence.', plan['body'])

    def test_issue_body_and_labels_agree_on_gate(self):
        plan = self.plan(ux_change_score=8, human_decision='UX prüfen.')
        metadata = self.metadata(plan)
        self.assertEqual(metadata['implementation_status'], plan['implementation_status'])
        self.assertEqual(metadata['human_approval_required'], plan['human_approval_required'])
        self.assertEqual(metadata['severity_score'], self.record['severity_score'])

    def test_cli_does_not_modify_input_and_returns_machine_output(self):
        helper = str(Path(__file__).with_name('issue_policy.py'))
        with tempfile.TemporaryDirectory() as folder:
            record = Path(folder) / 'record.json'
            record.write_text(json.dumps(self.record))
            before = record.read_bytes()
            result = subprocess.run([sys.executable, helper, '--record', str(record),
                                     '--repository', 'example/project'], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(json.loads(result.stdout)['create_issue'])
            self.assertEqual(record.read_bytes(), before)

    def test_invalid_cli_record_is_blocked_with_exit_two(self):
        helper = str(Path(__file__).with_name('issue_policy.py'))
        with tempfile.TemporaryDirectory() as folder:
            record = Path(folder) / 'record.json'
            record.write_text('{}')
            result = subprocess.run([sys.executable, helper, '--record', str(record),
                                     '--repository', 'example/project'], text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stdout)['create_issue'])


if __name__ == '__main__':
    unittest.main()
