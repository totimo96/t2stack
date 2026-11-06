"""Real temporary Git repositories exercise rotation and completion safety."""
import json
from pathlib import Path
import subprocess
import tempfile
import sys
from concurrent.futures import ThreadPoolExecutor
import unittest

from review_cycle import GATE, CycleError, block, read_block, start, end


class ReviewCycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.root / 'app.py').write_text('value = 1\n')
        folder = self.root / 'docs/code-map'
        folder.mkdir(parents=True)
        for name in ('alpha', 'beta', 'infra'):
            (folder / (name + '.md')).write_text('# ' + name + '\n')
        self.commit('Source and slice definitions')
        self.entries = [{'id': name, 'kind': 'technical' if name == 'infra' else 'vertical',
                         'document': f'docs/code-map/{name}.md'} for name in ('alpha', 'infra', 'beta')]
        self.map = self.root / 'CODE_MAP.md'
        checkpoint = GATE.check(self.root)['next_checkpoint']
        self.map.write_text('# Code Map\n' + GATE.START + '\n```json\n' + json.dumps(checkpoint)
                            + '\n```\n' + GATE.END + '\n' + block('slices', self.entries))

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self, text):
        self.git('add', '-A')
        self.git('commit', '-qm', text)

    def launch(self, mode='bug-report'):
        return start(self.root, mode)

    def progress(self):
        return read_block(self.map.read_text(), 'reviews')

    def report_ready(self, run):
        path = self.root / run['report']
        text = path.read_text()
        metadata = read_block(text, 'report')
        metadata['status'] = 'completed'
        text = text.replace(block('report', read_block(text, 'report')), block('report', metadata))
        path.write_text(text)

    def complete(self, run):
        self.report_ready(run)
        return end(self.root, run['run_file'])

    def test_never_reviewed_first_in_registry_order(self):
        first = self.launch()
        self.assertEqual(first['slice_id'], 'alpha')
        self.complete(first)
        second = self.launch()
        self.assertEqual(second['slice_id'], 'beta')

    def test_oldest_completed_slice_after_full_cycle(self):
        first = self.launch()
        self.complete(first)
        second = self.launch()
        self.complete(second)
        third = self.launch()
        self.assertEqual(third['slice_id'], 'alpha')
        self.complete(third)
        self.assertEqual(self.launch()['slice_id'], 'beta')

    def test_security_and_bug_queues_are_independent(self):
        self.complete(self.launch('bug-report'))
        self.assertEqual(self.launch('security-report')['slice_id'], 'alpha')
        self.assertEqual(self.launch('bug-report')['slice_id'], 'beta')

    def test_two_modes_finish_without_overwriting_each_other(self):
        bugs, security = self.launch('bug-report'), self.launch('security-report')
        self.complete(bugs)
        self.complete(security)
        progress = self.progress()['modes']
        self.assertIn('alpha', progress['bug-report']['completed'])
        self.assertIn('alpha', progress['security-report']['completed'])

    def test_one_active_claim_per_mode(self):
        self.launch()
        with self.assertRaisesRegex(CycleError, 'already active'):
            self.launch()

    def test_aborted_run_does_not_advance_rotation(self):
        run = self.launch()
        end(self.root, run['run_file'], abort_reason='Missing test fixture')
        self.assertEqual(self.progress()['modes']['bug-report']['completed'], {})
        self.assertEqual(self.launch()['slice_id'], 'alpha')

    def test_draft_report_cannot_complete(self):
        run = self.launch()
        with self.assertRaisesRegex(CycleError, 'metadata'):
            end(self.root, run['run_file'])
        self.assertEqual(self.progress()['modes']['bug-report']['completed'], {})

    def test_missing_report_does_not_mark_complete(self):
        run = self.launch()
        (self.root / run['report']).unlink()
        with self.assertRaises(OSError):
            end(self.root, run['run_file'])
        self.assertEqual(self.progress()['modes']['bug-report']['completed'], {})

    def test_new_uncommitted_source_blocks_finish(self):
        run = self.launch()
        self.report_ready(run)
        (self.root / 'app.py').write_text('value = 2\n')
        with self.assertRaisesRegex(CycleError, 'uncommitted_source'):
            end(self.root, run['run_file'])
        self.assertEqual(self.progress()['modes']['bug-report']['completed'], {})

    def test_new_head_blocks_finish(self):
        run = self.launch()
        self.report_ready(run)
        (self.root / 'app.py').write_text('value = 2\n')
        self.commit('Concurrent source change')
        with self.assertRaisesRegex(CycleError, 'head_changed'):
            end(self.root, run['run_file'])

    def test_changed_registry_blocks_finish(self):
        run = self.launch()
        self.report_ready(run)
        text = self.map.read_text()
        self.map.write_text(text.replace(block('slices', self.entries), block('slices', list(reversed(self.entries)))))
        with self.assertRaisesRegex(CycleError, 'registry changed'):
            end(self.root, run['run_file'])

    def test_changed_slice_document_blocks_finish(self):
        run = self.launch()
        self.report_ready(run)
        (self.root / run['document']).write_text('# Different scope\n')
        with self.assertRaisesRegex(CycleError, 'document changed'):
            end(self.root, run['run_file'])

    def test_finish_is_not_replayable(self):
        run = self.launch()
        self.complete(run)
        with self.assertRaisesRegex(CycleError, 'active claim'):
            end(self.root, run['run_file'])

    def test_report_commit_is_ignored_by_mapping_gate(self):
        self.complete(self.launch())
        self.commit('Save report and review state')
        self.assertEqual(GATE.check(self.root)['status'], 'unchanged')
        self.assertEqual(self.launch()['slice_id'], 'beta')

    def test_existing_source_checkpoint_is_preserved(self):
        before = self.map.read_text().split(GATE.END)[0]
        self.complete(self.launch())
        self.assertEqual(self.map.read_text().split(GATE.END)[0], before)

    def test_removed_slices_do_not_participate(self):
        self.complete(self.launch())
        text = self.map.read_text()
        keep = [item for item in self.entries if item['id'] != 'beta']
        self.map.write_text(text.replace(block('slices', self.entries), block('slices', keep)))
        self.assertEqual(self.launch()['slice_id'], 'alpha')

    def test_legacy_code_map_filename_is_supported(self):
        checkpoint = GATE.check(self.root)['head']
        content = self.map.read_text().replace('CODE_MAP.md', 'CODEMAP.md')
        self.map.unlink()
        self.map = self.root / 'CODEMAP.md'
        self.map.write_text(content)
        run = self.launch()
        self.assertEqual(run['map'], 'CODEMAP.md')
        self.assertEqual(run['head'], checkpoint)

    def test_outdated_map_blocks_start(self):
        (self.root / 'app.py').write_text('value = 2\n')
        self.commit('New source')
        with self.assertRaisesRegex(CycleError, 'Code map gate'):
            self.launch()
        self.assertIsNone(read_block(self.map.read_text(), 'reviews'))

    def test_cli_start_and_finish(self):
        helper = str(Path(__file__).with_name('review_cycle.py'))
        result = subprocess.run([sys.executable, helper, 'start', '--repo', str(self.root),
                                 '--mode', 'bug-report'], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        run = json.loads(result.stdout)
        self.report_ready(run)
        finished = subprocess.run([sys.executable, helper, 'finish', '--repo', str(self.root),
                                   '--run', run['run_file']], text=True, capture_output=True)
        self.assertEqual(finished.returncode, 0, finished.stdout + finished.stderr)
        self.assertEqual(json.loads(finished.stdout)['status'], 'completed')

    def test_concurrent_cli_modes_preserve_both_claims(self):
        helper = str(Path(__file__).with_name('review_cycle.py'))
        def launch(mode):
            return subprocess.run([sys.executable, helper, 'start', '--repo', str(self.root),
                                   '--mode', mode], text=True, capture_output=True)
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(launch, ['bug-report', 'security-report']))
        for result in results:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lanes = self.progress()['modes']
        self.assertEqual(lanes['bug-report']['active']['mode'], 'bug-report')
        self.assertEqual(lanes['security-report']['active']['mode'], 'security-report')

    def test_report_metadata_must_match_run(self):
        run = self.launch()
        self.report_ready(run)
        path = self.root / run['report']
        path.write_text(path.read_text().replace(run['head'], 'f' * 40))
        with self.assertRaisesRegex(CycleError, 'metadata'):
            end(self.root, run['run_file'])


if __name__ == '__main__':
    unittest.main()
