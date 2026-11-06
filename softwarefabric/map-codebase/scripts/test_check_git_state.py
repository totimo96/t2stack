"""Behavior tests in disposable Git repositories; no network or dependencies."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from check_git_state import check, START, END


class GitGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'app.py').write_text('value = 1\n')
        self.commit('Initial source')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def checkpoint(self):
        candidate = check(self.repo)['next_checkpoint']
        (self.repo / 'CODE_MAP.md').write_text(
            '# Code Map\n' + START + '\n```json\n' + json.dumps(candidate) + '\n```\n' + END + '\n'
        )
        return candidate['reviewed_commit']

    def test_initial_and_unchanged_with_untracked_outputs(self):
        self.assertEqual(check(self.repo)['status'], 'initial')
        baseline = self.checkpoint()
        result = check(self.repo)
        self.assertEqual(result['status'], 'unchanged')
        self.assertEqual(result['baseline'], baseline)

    def test_output_commit_does_not_trigger_code_review(self):
        self.checkpoint()
        folder = self.repo / 'docs/code-map'
        folder.mkdir(parents=True)
        (folder / 'app.md').write_text('Application slice\n')
        self.commit('Document mapping')
        self.assertEqual(check(self.repo)['reason'], 'only_mapping_outputs_changed')

    def test_only_changed_source_paths_are_reported(self):
        baseline = self.checkpoint()
        self.commit('Document mapping')
        (self.repo / 'app.py').write_text('value = 2\n')
        self.commit('Change source')
        result = check(self.repo)
        self.assertEqual(result['status'], 'changed')
        self.assertEqual(result['baseline'], baseline)
        self.assertEqual(result['changes'], [{'status': 'M', 'path': 'app.py'}])

    def test_rename_retains_old_and_new_paths(self):
        self.checkpoint()
        self.commit('Document mapping')
        self.git('mv', 'app.py', 'renamed app.py')
        self.commit('Rename source')
        paths = {entry['path'] for entry in check(self.repo)['changes']}
        self.assertEqual(paths, {'app.py', 'renamed app.py'})

    def test_uncommitted_source_never_skips(self):
        self.checkpoint()
        (self.repo / 'app.py').write_text('value = 2\n')
        self.assertEqual(check(self.repo)['reason'], 'uncommitted_source_changes')

    def test_staged_change_cancelled_in_worktree_still_blocks(self):
        self.checkpoint()
        (self.repo / 'app.py').write_text('value = 2\n')
        self.git('add', 'app.py')
        (self.repo / 'app.py').write_text('value = 1\n')
        self.assertEqual(check(self.repo)['reason'], 'uncommitted_source_changes')

    def test_untracked_source_blocks(self):
        self.checkpoint()
        (self.repo / 'new.py').write_text('value = 2\n')
        self.assertEqual(check(self.repo)['paths'], ['new.py'])

    def test_missing_baseline_does_not_silently_rescan(self):
        self.checkpoint()
        path = self.repo / 'CODE_MAP.md'
        content = path.read_text().replace(self.git('rev-parse', 'HEAD'), 'f' * 40)
        path.write_text(content)
        self.assertEqual(check(self.repo)['reason'], 'reviewed_commit_unavailable')

    def test_incomplete_review_cannot_skip(self):
        self.checkpoint()
        path = self.repo / 'CODE_MAP.md'
        path.write_text(path.read_text().replace('"complete": true', '"complete": false'))
        self.assertEqual(check(self.repo)['reason'], 'previous_review_incomplete')

    def test_changed_head_during_review_blocks_completion(self):
        head = self.checkpoint()
        self.commit('Document mapping')
        self.assertEqual(check(self.repo, expect_head=head)['reason'], 'head_changed_during_review')

    def test_rebased_history_compares_endpoint_trees(self):
        self.checkpoint()
        self.commit('Document mapping')
        self.git('checkout', '--orphan', 'replacement')
        (self.repo / 'app.py').write_text('value = 3\n')
        self.commit('Different history')
        self.assertEqual(check(self.repo)['changes'], [{'status': 'M', 'path': 'app.py'}])

    def test_first_review_can_complete_with_unfinished_output_block(self):
        head = self.git('rev-parse', 'HEAD')
        (self.repo / 'CODE_MAP.md').write_text('# New map\n' + START + '\nUnfinished output\n' + END)
        result = check(self.repo, expect_head=head)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['next_checkpoint']['reviewed_commit'], head)

    def test_completion_still_rejects_new_uncommitted_source(self):
        head = self.checkpoint()
        (self.repo / 'app.py').write_text('value = 4\n')
        self.assertEqual(check(self.repo, expect_head=head)['reason'], 'uncommitted_source_changes')

    def test_malformed_checkpoint_does_not_trigger_initial_scan(self):
        (self.repo / 'CODE_MAP.md').write_text(START + '\n```json\n{broken}\n```\n' + END)
        self.assertEqual(check(self.repo)['reason'], 'invalid_checkpoint_json')

    def test_report_output_commits_do_not_trigger_mapping(self):
        self.checkpoint()
        folder = self.repo / 'docs/softwarefabric/reports/bug-report'
        folder.mkdir(parents=True)
        (folder / 'report.md').write_text('Report output\n')
        self.commit('Save review output')
        self.assertEqual(check(self.repo)['reason'], 'only_mapping_outputs_changed')

    def test_legacy_checkpoint_without_report_output_remains_readable(self):
        self.checkpoint()
        path = self.repo / 'CODE_MAP.md'
        path.write_text(path.read_text().replace(', "docs/softwarefabric/reports/"', ''))
        self.assertEqual(check(self.repo)['status'], 'unchanged')

    def test_gate_does_not_write_files(self):
        self.checkpoint()
        path = self.repo / 'CODE_MAP.md'
        original = path.read_bytes()
        check(self.repo)
        self.assertEqual(path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
