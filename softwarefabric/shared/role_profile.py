"""Frozen, explicitly chosen roles shared by orchestrator and PR gates."""
import hashlib
import json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / 'orchestrator/assets/default-profile.json'


def validate(profile):
    if not isinstance(profile, dict) or profile.get('schema') != 1:
        raise ValueError('Unsupported role profile')
    def identity(target):
        if not isinstance(target, dict) or any(not isinstance(target.get(k), str) or not target[k].strip() for k in ('provider', 'model')):
            raise ValueError('Each role needs provider and model')
        if not isinstance(target.get('options'), dict):
            raise ValueError('Each role needs explicit options')
        return target['provider'], target['model']
    identities = [identity(profile.get(role)) for role in ('worker', 'verifier')]
    if identities[0] == identities[1]:
        raise ValueError('Worker and verifier must be different models')
    council = profile.get('council')
    if not isinstance(council, list) or len(council) != 2 or {x.get('role') for x in council if isinstance(x, dict)} != {'worker', 'verifier'}:
        raise ValueError('Exactly worker and verifier sit in council')
    for member in council:
        if identity(member) != identity(profile[member['role']]):
            raise ValueError('Council identity must match its pipeline role')
        key = {'codex':'reasoningEffort', 'claudeAgent':'effort'}.get(member['provider'])
        if key is None or member['options'] != {key:'high'}:
            raise ValueError('Council requires supported provider with high reasoning')
    if council[0]['model'] == council[1]['model']:
        raise ValueError('Council model names must be distinct')
    return profile


def load(path=None):
    return validate(json.loads(Path(path or DEFAULT).read_text(encoding='utf-8')))


def digest(profile):
    validate(profile)
    return hashlib.sha256(json.dumps(profile, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def members(profile):
    validate(profile)
    return {m['model']:(m['provider'], m['options']) for m in profile['council']}


def target(profile, phase):
    validate(profile)
    if phase in ('map-codebase','bug-report','security-report','prepare-pr','correct-pr'):
        value = profile['worker']
    elif phase == 'validate-findings':
        value = profile['verifier']
    elif phase in ('council-worker','council-verifier'):
        value = next(m for m in profile['council'] if m['role'] == phase.removeprefix('council-'))
    else:
        raise ValueError('Unknown delegated phase: ' + phase)
    return {key:value[key] for key in ('provider','model','options')}
