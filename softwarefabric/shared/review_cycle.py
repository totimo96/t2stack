#!/usr/bin/env python3
"""One-slice report rotation, claims and completion receipts for Softwarefabric."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

SPEC = importlib.util.spec_from_file_location('map_gate', Path(__file__).parents[1] / 'map-codebase/scripts/check_git_state.py')
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
MODES = ('bug-report', 'security-report')
OUTPUT = 'docs/softwarefabric/reports'


class CycleError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def block(name, value):
    return f'<!-- softwarefabric:{name} -->\n```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```\n<!-- /softwarefabric:{name} -->'


def read_block(text, name, default=None):
    start, end = f'<!-- softwarefabric:{name} -->', f'<!-- /softwarefabric:{name} -->'
    if start not in text and end not in text:
        return default
    pattern = re.escape(start) + r'\s*```json\s*([\s\S]*?)\s*```\s*' + re.escape(end)
    match = re.search(pattern, text)
    if text.count(start) != 1 or text.count(end) != 1 or not match:
        raise CycleError(f'Invalid {name} block')
    return json.loads(match.group(1))


def relative(root, value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts:
        raise CycleError('Expected a repository-relative path')
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise CycleError('Path escapes repository')
    return resolved


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked(root):
    # OS locks release even when a process crashes; the pending claim remains
    # explicit in CODE_MAP.md until resumed or aborted.
    name = Path(tempfile.gettempdir()) / ('softwarefabric-' + digest(str(root).encode()) + '.lock')
    with name.open('a+b') as stream:
        if os.name == 'nt':
            import msvcrt
            stream.seek(0)
            stream.write(b'0')
            stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == 'nt':
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def locate(repo, map_path=None):
    root = Path(GATE.git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    if map_path is None:
        existing = [name for name in ('CODE_MAP.md', 'CODEMAP.md') if (root / name).is_file()]
        if len(existing) != 1:
            raise CycleError('Need exactly one CODE_MAP.md or CODEMAP.md, or an explicit --map')
        map_path = existing[0]
    return root, relative(root, map_path)


def registry(root, text):
    entries = read_block(text, 'slices')
    if not isinstance(entries, list) or not entries:
        raise CycleError('Missing slice registry; add it from the existing code map first')
    ids = set()
    for entry in entries:
        if not isinstance(entry, dict) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', entry.get('id', '')):
            raise CycleError('Invalid slice ID')
        if entry['id'] in ids or entry.get('kind') not in ('vertical', 'shared', 'technical'):
            raise CycleError('Duplicate slice ID or invalid kind')
        ids.add(entry['id'])
        if not relative(root, entry.get('document', '')).is_file():
            raise CycleError('Slice document missing: ' + entry['id'])
    return entries


def state(text):
    value = read_block(text, 'reviews', {'schema': 1, 'modes': {}})
    if not isinstance(value, dict) or value.get('schema') != 1 or not isinstance(value.get('modes'), dict):
        raise CycleError('Invalid review state')
    for mode in MODES:
        value['modes'].setdefault(mode, {'completed': {}, 'active': None})
        if not isinstance(value['modes'][mode].get('completed'), dict):
            raise CycleError('Invalid completed slice state')
    return value


def write_state(path, before, value):
    replacement = block('reviews', value)
    pattern = r'<!-- softwarefabric:reviews -->[\s\S]*?<!-- /softwarefabric:reviews -->'
    after = re.sub(pattern, lambda _: replacement, before) if '<!-- softwarefabric:reviews -->' in before else before.rstrip() + '\n\n## Slice-Prüfstand\n\n' + replacement + '\n'
    if path.read_text(encoding='utf-8') != before:
        raise CycleError('Code map changed concurrently; retry without overwriting it')
    atomic(path, after)


def gate(root, map_path, slices_path, expected=None):
    result = GATE.check(root, map_path, slices_path, expected)
    if result['status'] not in (('ready',) if expected else ('unchanged',)):
        raise CycleError('Code map gate: ' + result.get('reason', result['status']))
    return result


def start(repo, mode, map_path=None, slices_path='docs/code-map', slice_id=None):
    root, path = locate(repo, map_path)
    with locked(root):
        checked = gate(root, str(path.relative_to(root)), slices_path)
        before = path.read_text(encoding='utf-8')
        entries, progress = registry(root, before), state(before)
        lane = progress['modes'][mode]
        if lane.get('active'):
            raise CycleError('Run already active: ' + lane['active']['run_file'])
        eligible = [entry for entry in entries if entry['kind'] == 'vertical']
        if not eligible:
            raise CycleError('No vertical slices registered')
        if slice_id is not None:
            eligible = [entry for entry in eligible if entry['id'] == slice_id]
            if not eligible:
                raise CycleError('Requested vertical slice not registered: ' + slice_id)
        completed = lane['completed']
        timestamps = {}
        for key, item in completed.items():
            instant = datetime.fromisoformat(item['last_completed_at'])
            if instant.utcoffset() is None:
                raise CycleError('Completion timestamps need a timezone')
            timestamps[key] = instant.timestamp()
        chosen = min(eligible, key=lambda entry: (
            entry['id'] in completed,
            timestamps.get(entry['id'], 0),
            eligible.index(entry),
        ))
        run_id, timestamp = uuid.uuid4().hex, now()
        prefix = f"{OUTPUT}/{mode}/{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{chosen['id']}-{run_id[:8]}"
        run = {'run_id': run_id, 'mode': mode, 'slice_id': chosen['id'],
               'head': checked['head'], 'map': str(path.relative_to(root)), 'slices_path': slices_path,
               'document': chosen['document'], 'document_sha256': digest(relative(root, chosen['document']).read_bytes()),
               'registry_sha256': digest(json.dumps(entries, sort_keys=True).encode()),
               'started_at': timestamp, 'run_file': prefix + '.run.json', 'report': prefix + '.md'}
        metadata = {'run_id': run_id, 'mode': mode, 'slice_id': chosen['id'],
                    'reviewed_commit': run['head'], 'status': 'draft', 'finding_count': 0}
        template = Path(__file__).with_name('report.template.md').read_text(encoding='utf-8')
        report = template.replace('{report_metadata}', block('report', metadata))
        for key, value in run.items():
            report = report.replace('{' + key + '}', str(value))
        atomic(relative(root, run['run_file']), json.dumps(run, indent=2) + '\n')
        atomic(relative(root, run['report']), report)
        lane['active'] = run
        write_state(path, before, progress)
        return run


def end(repo, run_file, abort_reason=None):
    root = Path(GATE.git(repo, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
    run = json.loads(relative(root, run_file).read_text(encoding='utf-8'))
    root, _ = locate(root, run['map'])
    with locked(root):
        path = relative(root, run['map'])
        before = path.read_text(encoding='utf-8')
        progress = state(before)
        lane = progress['modes'][run['mode']]
        if lane.get('active') != run:
            raise CycleError('Run does not match active claim; cannot finalize twice or replace another run')
        if abort_reason:
            lane['last_attempt'] = {'run_id': run['run_id'], 'slice_id': run['slice_id'],
                                    'status': 'aborted', 'at': now(), 'reason': abort_reason, 'report': run['report']}
        else:
            gate(root, run['map'], run['slices_path'], run['head'])
            entries = registry(root, before)
            if digest(json.dumps(entries, sort_keys=True).encode()) != run['registry_sha256']:
                raise CycleError('Slice registry changed during review')
            if digest(relative(root, run['document']).read_bytes()) != run['document_sha256']:
                raise CycleError('Slice document changed during review')
            report = relative(root, run['report'])
            metadata = read_block(report.read_text(encoding='utf-8'), 'report')
            expected = {'run_id': run['run_id'], 'mode': run['mode'], 'slice_id': run['slice_id'],
                        'reviewed_commit': run['head'], 'status': 'completed'}
            if not isinstance(metadata, dict) or any(metadata.get(k) != v for k, v in expected.items()):
                raise CycleError('Report metadata does not attest this completed run')
            count = metadata.get('finding_count')
            if type(count) is not int or count < 0:
                raise CycleError('Report needs a nonnegative finding_count')
            lane['completed'][run['slice_id']] = {'last_completed_at': now(),
                'reviewed_commit': run['head'], 'report': run['report'], 'run_id': run['run_id']}
        lane['active'] = None
        write_state(path, before, progress)
        return {'status': 'aborted' if abort_reason else 'completed', 'slice_id': run['slice_id'], 'report': run['report']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    begin = sub.add_parser('start')
    begin.add_argument('--repo', default='.')
    begin.add_argument('--mode', choices=MODES, required=True)
    begin.add_argument('--slice-id', help='Explicit slice for a bounded orchestrator sweep')
    begin.add_argument('--map', dest='map_path')
    begin.add_argument('--slices', default='docs/code-map', dest='slices_path')
    for name in ('finish', 'abort'):
        command = sub.add_parser(name)
        command.add_argument('--repo', default='.')
        command.add_argument('--run', required=True, dest='run_file')
        if name == 'abort':
            command.add_argument('--reason', required=True, dest='abort_reason')
    args = vars(parser.parse_args())
    action = args.pop('action')
    try:
        result = start(**args) if action == 'start' else end(**args)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'blocked', 'reason': str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
