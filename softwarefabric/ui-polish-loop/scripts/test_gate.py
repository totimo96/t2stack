import unittest

from gate import entscheide

ZIEL = 9.5


def runde(n, sol, opus, commit=None, confirmation=False, holdout=False, brief='b1'):
    return {'round': n, 'commit': commit or f'c{n}', 'brief_sha256': brief,
            'confirmation': confirmation, 'holdout': holdout,
            'scores': {'sol': sol, 'opus': opus}}


class GateTest(unittest.TestCase):
    def test_leerer_verlauf_laeuft_weiter(self):
        self.assertEqual(entscheide([], [], ZIEL)[0], 'continue')

    def test_erste_runde_auf_ziel_verlangt_bestaetigung(self):
        self.assertEqual(entscheide([runde(1, 9.6, 9.5)], [], ZIEL)[0], 'confirm')

    def test_bestaetigung_mit_holdout_auf_gleichem_commit_besteht(self):
        r = [runde(1, 9.6, 9.5, commit='x'), runde(2, 9.5, 9.7, commit='x', confirmation=True, holdout=True)]
        self.assertEqual(entscheide(r, [], ZIEL)[0], 'pass')

    def test_bestaetigung_ohne_holdout_besteht_nicht(self):
        r = [runde(1, 9.6, 9.5, commit='x'), runde(2, 9.5, 9.7, commit='x', confirmation=True)]
        self.assertEqual(entscheide(r, [], ZIEL)[0], 'confirm')

    def test_codeaenderung_zwischen_den_runden_verlangt_neue_bestaetigung(self):
        r = [runde(1, 9.6, 9.5, commit='x'), runde(2, 9.5, 9.7, commit='y', confirmation=True, holdout=True)]
        self.assertEqual(entscheide(r, [], ZIEL)[0], 'confirm')

    def test_geaenderter_brief_zaehlt_nicht_als_bestaetigung(self):
        r = [runde(1, 9.6, 9.5, commit='x'), runde(2, 9.5, 9.7, commit='x', confirmation=True, holdout=True, brief='b2')]
        self.assertEqual(entscheide(r, [], ZIEL)[0], 'confirm')

    def test_offener_defekt_blockiert_trotz_noten(self):
        r = [runde(1, 9.6, 9.5, commit='x'), runde(2, 9.5, 9.7, commit='x', confirmation=True, holdout=True)]
        ledger = [{'id': 'sol-2-1', 'class': 'defekt', 'status': 'offen'}]
        self.assertEqual(entscheide(r, ledger, ZIEL)[0], 'continue')

    def test_offene_politur_blockiert_nicht(self):
        r = [runde(1, 9.6, 9.5, commit='x'), runde(2, 9.5, 9.7, commit='x', confirmation=True, holdout=True)]
        ledger = [{'id': 'sol-2-1', 'class': 'politur', 'status': 'offen'}]
        self.assertEqual(entscheide(r, ledger, ZIEL)[0], 'pass')

    def test_ein_mitglied_unter_ziel_laeuft_weiter(self):
        self.assertEqual(entscheide([runde(1, 9.6, 9.3)], [], ZIEL)[0], 'continue')

    def test_grosser_sprung_verlangt_bestaetigung(self):
        r = [runde(1, 8.4, 8.5), runde(2, 9.1, 8.6)]
        self.assertEqual(entscheide(r, [], ZIEL)[0], 'confirm')

    def test_drei_runden_ohne_fortschritt_sind_stagnation(self):
        r = [runde(1, 8.5, 8.7), runde(2, 8.3, 8.3), runde(3, 8.4, 8.5), runde(4, 8.5, 8.3)]
        self.assertEqual(entscheide(r, [], ZIEL)[0], 'stagnation')

    def test_stetiger_fortschritt_ist_keine_stagnation(self):
        r = [runde(1, 8.0, 8.1), runde(2, 8.2, 8.3), runde(3, 8.4, 8.4), runde(4, 8.6, 8.7)]
        self.assertEqual(entscheide(r, [], ZIEL)[0], 'continue')


if __name__ == '__main__':
    unittest.main()
