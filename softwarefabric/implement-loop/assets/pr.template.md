## Problem und Änderung

{Konkreter Auslöser und Fehlverhalten. Beschreibe die resultierende Korrektur und
wesentliche fachliche Grenzen; keine reine Datei-Inventarliste.}

Fixes #{issue_number}

## Umfang und Freigabe

- Befund: `{finding_id}` / `{fingerprint}`
- Validierungsstand: `{validation_commit}`
- Lösungsplan: `{solution_sha256}`
- UX-/Mensch-Gate: {nicht erforderlich oder nachvollziehbarer Freigabebeleg}
- Abgrenzung: {betroffene Verträge, nicht zum Fix gehörende Themen}

## Prüfung

{Tatsächlich ausgeführte Reproduktion und Prüfkommandos mit Ergebnissen.
Aussagekräftiger Regressionstest. Browser, Deployment und Produktion nur nennen,
wenn geprüft; fehlende Ebenen und aktuelle CI-Ergebnisse ehrlich abgrenzen.}

## Council review

Rounds: {Anzahl vollständiger Runden; unvollständige Runden getrennt benennen}

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| GPT-6.1 Sol | {Originalnote / Kommentarlink / geprüfter Stand} | {Originalnote / Kommentarlink / geprüfter Stand} |
| Claude Opus 5.5 | {Originalnote / Kommentarlink / geprüfter Stand} | {Originalnote / Kommentarlink / geprüfter Stand} |

## Risiken und Merge-Entscheidung

{Restrisiken, notwendige Migrationen und Rollback. Bei Draft: konkrete offene
Befunde oder fehlende Checks. Bei Übergabe: geprüfter Head und noch erforderliche
Repository-/CODEOWNERS-Freigaben. Im Orchestrator zusätzlich beide Risikobewertungen,
Höchstwerte, Reviewlinks und Merge-Entscheidung gemäß dessen Policy; eigenständiger
Loop: manueller Merge. Kein Deployment.}

Created with {tatsächlich verwendete Modelle} in {Harness}.
