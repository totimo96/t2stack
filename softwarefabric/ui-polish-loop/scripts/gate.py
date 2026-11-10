"""Gate des UI-Polish-Loops: entscheidet aus Notenverlauf und Befundregister.

    python3 gate.py --rounds rounds.json --ledger ledger.json --target 9.5

Gibt eine Zeile JSON aus: {"decision": "pass|confirm|stagnation|continue", "reason": "..."}.
Nur lesend; startet keine Agents. Regeln: references/convergence.md.
"""
import argparse
import json
import sys

OFFENE_STATUS = {'offen', 'verschlechtert'}
SCHWERE_KLASSEN = {'blocker', 'defekt'}
SPRUNG = 0.5        # Anstieg je Mitglied, der eine Bestätigung verlangt
FORTSCHRITT = 0.1   # Mindestanstieg des Minimums gegen Stagnation
STAGNATION_RUNDEN = 3


def offene_defekte(ledger):
    return [b['id'] for b in ledger
            if b.get('class') in SCHWERE_KLASSEN and b.get('status') in OFFENE_STATUS]


def minimum(runde):
    return min(runde['scores'].values())


def alle_erreicht(runde, ziel):
    return bool(runde['scores']) and all(note >= ziel for note in runde['scores'].values())


def entscheide(rounds, ledger, ziel):
    if not rounds:
        return 'continue', 'Noch keine Runde erfasst.'
    letzte = rounds[-1]
    offen = offene_defekte(ledger)

    if len(rounds) >= 2:
        vorletzte = rounds[-2]
        if (alle_erreicht(letzte, ziel) and alle_erreicht(vorletzte, ziel)
                and letzte.get('confirmation') and letzte.get('holdout')
                and letzte.get('commit') == vorletzte.get('commit')
                and letzte.get('brief_sha256') == vorletzte.get('brief_sha256')):
            if offen:
                return 'continue', f'Zielnote bestätigt, aber offene Defekte: {", ".join(offen)}.'
            return 'pass', 'Zwei Runden auf Zielnote, die letzte als Bestätigung mit Holdout, keine offenen Defekte.'

    if alle_erreicht(letzte, ziel):
        if letzte.get('confirmation'):
            return 'confirm', 'Bestätigungsrunde unvollständig (Holdout, gleicher Commit oder Brief fehlt); wiederholen.'
        return 'confirm', 'Zielnote erreicht; Bestätigungsrunde mit frischen Prüfern und Holdout folgt.'

    if len(rounds) >= 2:
        vorletzte = rounds[-2]
        for mitglied, note in letzte['scores'].items():
            vorher = vorletzte['scores'].get(mitglied)
            if vorher is not None and note - vorher > SPRUNG:
                return 'confirm', f'{mitglied} springt um {note - vorher:.1f}; eine zweite frische Runde muss das bestätigen.'

    if len(rounds) > STAGNATION_RUNDEN:
        bisher = max(minimum(r) for r in rounds[:-STAGNATION_RUNDEN])
        juengste = [minimum(r) for r in rounds[-STAGNATION_RUNDEN:]]
        if all(m < bisher + FORTSCHRITT for m in juengste):
            return 'stagnation', (f'Seit {STAGNATION_RUNDEN} Runden kein Anstieg des Minimums über '
                                  f'{bisher:.1f} + {FORTSCHRITT}; Lauf anhalten und berichten.')

    return 'continue', f'Minimum {minimum(letzte):.1f} unter Zielnote.'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--rounds', required=True)
    p.add_argument('--ledger', required=True)
    p.add_argument('--target', required=True, type=float)
    a = p.parse_args(argv)
    with open(a.rounds, encoding='utf-8') as f:
        rounds = json.load(f)
    with open(a.ledger, encoding='utf-8') as f:
        ledger = json.load(f)
    decision, reason = entscheide(rounds, ledger, a.target)
    print(json.dumps({'decision': decision, 'reason': reason}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
