import copy
import unittest
from plan_run import plan
from role_profile import load, digest, target, validate


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.profile=load()
        self.registry=[{'id':'a','kind':'vertical'}, {'id':'infra','kind':'technical'}, {'id':'b','kind':'vertical'}]

    def test_bounded_sweep_and_roles(self):
        result=plan(self.registry,self.profile)
        reports=[x for x in result['jobs'] if x['phase'] in ('bug-report','security-report')]
        self.assertEqual([(x['phase'],x['slice_id']) for x in reports], [('bug-report','a'),('security-report','a'),('bug-report','b'),('security-report','b')])
        self.assertTrue(all(x['target']['options']=={'effort':'medium'} for x in reports))
        validations=[x for x in result['jobs'] if x['phase']=='validate-findings']
        self.assertEqual(len(validations),4)
        self.assertTrue(all(x['target']['model']=='gpt-6.1-sol' for x in validations))
        self.assertEqual(result['jobs'][-1]['phase_barrier'],[x['id'] for x in validations])
        self.assertTrue(result['jobs'][-1]['controller_owned'])
        self.assertTrue(all('status' not in x for x in result['jobs']))

    def test_council_high_and_same_identities(self):
        for role in ('worker','verifier'):
            value=target(self.profile,'council-'+role)
            self.assertEqual(value['model'], self.profile[role]['model'])
            self.assertEqual(list(value['options'].values()),['high'])

    def test_profile_hash_sensitive_to_role_options(self):
        other=copy.deepcopy(self.profile)
        other['worker']['options']['effort']='high'
        self.assertNotEqual(digest(other),digest(self.profile))
        self.assertEqual(digest(dict(reversed(list(self.profile.items())))),digest(self.profile))

    def test_reject_wrong_council_identity(self):
        self.profile['council'][0]['model']='other'
        with self.assertRaises(ValueError):validate(self.profile)

    def test_reject_medium_council(self):
        self.profile['council'][0]['options']['effort']='medium'
        with self.assertRaises(ValueError):validate(self.profile)

    def test_reject_same_model_for_verifier(self):
        self.profile['verifier']=self.profile['worker']
        with self.assertRaises(ValueError):validate(self.profile)

    def test_reject_third_council_member(self):
        self.profile['council'].append(copy.deepcopy(self.profile['council'][0]))
        with self.assertRaises(ValueError):validate(self.profile)

    def test_reject_duplicate_slice(self):
        with self.assertRaises(ValueError):plan([self.registry[0],self.registry[0]],self.profile)

    def test_empty_audit_scope_is_not_a_successful_sweep(self):
        with self.assertRaises(ValueError):plan([],self.profile)
        with self.assertRaises(ValueError):plan([self.registry[1]],self.profile)

    def test_reject_unknown_phase(self):
        with self.assertRaises(ValueError):target(self.profile,'arbitrary-agent')

    def test_explicit_alternative_models(self):
        self.profile['worker']['model']='user-chosen-opus'
        self.profile['council'][0]['model']='user-chosen-opus'
        self.assertEqual(target(validate(self.profile),'prepare-pr')['model'],'user-chosen-opus')
