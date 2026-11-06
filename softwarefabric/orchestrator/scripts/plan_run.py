#!/usr/bin/env python3
"""Produce a bounded pipeline plan; does not execute agents or attest completion."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'shared'))
from role_profile import load, digest, target


def plan(registry, profile):
    if not isinstance(registry, list) or any(not isinstance(x, dict) or not isinstance(x.get('id'), str) or not x['id'].strip() or x.get('kind') not in ('vertical','technical','shared') for x in registry):
        raise ValueError('Need valid slice registry')
    if len({x['id'] for x in registry}) != len(registry):
        raise ValueError('Duplicate slice IDs')
    if not any(x['kind'] == 'vertical' for x in registry):
        raise ValueError('No vertical slices available for a complete audit sweep')
    jobs = [{'id':'map','phase':'map-codebase','target':target(profile,'map-codebase'),'depends_on':[]}]
    reports = []
    for entry in registry:
        if entry['kind'] != 'vertical':
            continue
        for mode in ('bug-report','security-report'):
            job = {'id':f"{mode}:{entry['id']}",'phase':mode,'slice_id':entry['id'],
                   'target':target(profile, mode),'depends_on':['map']}
            jobs.append(job)
            reports.append(job)
    for report in reports:
        jobs.append({'id':'validate:' + report['id'],'phase':'validate-findings',
                     'source_job':report['id'],'target':target(profile,'validate-findings'),
                     'depends_on':[report['id']], 'phase_barrier':[x['id'] for x in reports]})
    jobs.append({'id':'implementation','phase':'implement-loop','controller_owned':True,
                 'depends_on':[], 'phase_barrier':[x['id'] for x in jobs if x['phase']=='validate-findings']})
    return {'schema':1,'profile_sha256':digest(profile),'profile':profile,'jobs':jobs,
            'note':'Plan only. Record actual evidence and live gates before completing jobs.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry',required=True,help='Extracted softwarefabric:slices JSON')
    parser.add_argument('--profile')
    args=parser.parse_args()
    try:
        result=plan(json.loads(Path(args.registry).read_text()),load(args.profile))
    except (ValueError, OSError, TypeError) as error:
        print(json.dumps({'status':'blocked','reason':str(error)}))
        return 2
    print(json.dumps(result,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
