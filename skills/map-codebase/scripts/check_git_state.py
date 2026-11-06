#!/usr/bin/env python3
"""Read-only Git gate for map-codebase. Requires Python 3.10+ and Git."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

START = '<!-- map-codebase:checkpoint -->'
END = '<!-- /map-codebase:checkpoint -->'


def git(repo, *args):
    return subprocess.check_output(
        ['git', '--no-optional-locks', '-C', str(repo), *args], stderr=subprocess.PIPE
    )


def relative_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) == '.' or ':' in value:
        raise ValueError('Output paths must be nonempty repository-relative paths.')
    return str(path)


def check(repo, map_path='CODE_MAP.md', slices_path='docs/code-map', expect_head=None):
    root = Path(git(repo, 'rev-parse', '--show-toplevel').decode().strip())
    head = git(root, 'rev-parse', '--verify', 'HEAD').decode().strip()
    map_path, slices_path = relative_path(map_path), relative_path(slices_path)
    outputs = [map_path, slices_path + '/']
    result = {'repository': str(root), 'head': head, 'map': map_path}

    def blocked(reason):
        return {**result, 'status': 'blocked', 'reason': reason}

    if expect_head is not None and head != expect_head:
        return blocked('head_changed_during_review')

    def is_output(path):
        return path == map_path or path == slices_path or path.startswith(slices_path + '/')

    # Check index and working tree separately: their changes may cancel out in
    # a direct HEAD-to-working-tree diff while the next commit still differs.
    dirty = set()
    for args in [
        ('diff', '--name-only', '-z', '--no-ext-diff'),
        ('diff', '--cached', '--name-only', '-z', '--no-ext-diff', 'HEAD'),
        ('ls-files', '--others', '--exclude-standard', '-z'),
    ]:
        dirty.update(p.decode('utf-8', 'surrogateescape') for p in git(root, *args).split(b'\0') if p)
    relevant_dirty = sorted(p for p in dirty if not is_output(p))
    if relevant_dirty:
        return {**blocked('uncommitted_source_changes'), 'paths': relevant_dirty}

    candidate = {
        'schema': 1, 'reviewed_commit': head, 'scope': ['.'],
        'excluded_outputs': outputs, 'complete': True,
        'reviewed_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
    if expect_head is not None:
        # The new map may still have a placeholder checkpoint at completion.
        # Verify the captured source target, not that unfinished output block.
        return {**result, 'status': 'ready', 'reason': 'review_target_stable',
                'next_checkpoint': candidate}

    document = root / map_path
    content = document.read_text(encoding='utf-8') if document.exists() else ''
    checkpoint = None
    if START in content or END in content:
        if content.count(START) != 1 or content.count(END) != 1:
            return blocked('invalid_checkpoint_block')
        match = re.search(re.escape(START) + r'\s*```json\s*([\s\S]*?)\s*```\s*' + re.escape(END), content)
        if not match:
            return blocked('invalid_checkpoint_block')
        try:
            checkpoint = json.loads(match.group(1))
        except json.JSONDecodeError:
            return blocked('invalid_checkpoint_json')
        if not isinstance(checkpoint, dict) or checkpoint.get('schema') != 1:
            return blocked('unsupported_checkpoint_schema')
        if checkpoint.get('scope') != ['.'] or checkpoint.get('excluded_outputs') != outputs:
            return blocked('checkpoint_scope_or_outputs_differ')
        if checkpoint.get('complete') is not True:
            return blocked('previous_review_incomplete')

    if checkpoint is None:
        return {**result, 'status': 'initial', 'reason': 'no_checkpoint', 'next_checkpoint': candidate}

    baseline = checkpoint.get('reviewed_commit', '')
    if not isinstance(baseline, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', baseline):
        return blocked('invalid_reviewed_commit')
    try:
        git(root, 'cat-file', '-e', baseline + '^{commit}')
    except subprocess.CalledProcessError:
        return {**blocked('reviewed_commit_unavailable'), 'baseline': baseline}

    result['baseline'] = baseline
    if baseline == head:
        return {**result, 'status': 'unchanged', 'reason': 'same_commit', 'changes': []}

    # A two-endpoint tree diff also works after rebases and branch switches.
    # Renames become deletion + addition, retaining both paths for routing.
    fields = git(root, 'diff', '--name-status', '-z', '--no-renames',
                 '--no-ext-diff', '--no-textconv', baseline, head, '--').split(b'\0')
    changes = []
    for index in range(0, len(fields) - 1, 2):
        status, path = (field.decode('utf-8', 'surrogateescape') for field in fields[index:index + 2])
        if not is_output(path):
            changes.append({'status': status, 'path': path})
    if not changes:
        return {**result, 'status': 'unchanged', 'reason': 'only_mapping_outputs_changed', 'changes': []}
    return {**result, 'status': 'changed', 'changes': changes, 'next_checkpoint': candidate}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--map', default='CODE_MAP.md', dest='map_path')
    parser.add_argument('--slices', default='docs/code-map', dest='slices_path')
    parser.add_argument('--expect-head', help='At completion, require the Git commit captured at the start.')
    args = parser.parse_args()
    try:
        result = check(**vars(args))
    except (subprocess.CalledProcessError, OSError, ValueError) as error:
        result = {'status': 'blocked', 'reason': 'git_or_input_error', 'error': str(error)}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 2 if result['status'] == 'blocked' else 0


if __name__ == '__main__':
    raise SystemExit(main())
