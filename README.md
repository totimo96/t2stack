# t2stack

Wiederverwendbare Agent-Skills für eine organisierte Codeverbesserungspipeline.

## Softwarefabric

Die zusammengehörigen Skills liegen unter [`softwarefabric/`](softwarefabric/).
Sie bilden die ersten Stufen des Skillbaums „Automatic Security and Bugfixes“ ab:

| Skill | Aufgabe |
| --- | --- |
| [orchestrator](softwarefabric/orchestrator/SKILL.md) | Vollständiger Durchlauf mit konfigurierbaren Rollen: Karte → Reports aller Slices → unabhängige Validierung → Umsetzung → Council im PR. |
| [map-codebase](softwarefabric/map-codebase/SKILL.md) | Codebasis in Vertical Slices kartieren; bei Wiederholung nur Änderungen seit dem gespeicherten Git-Prüfstand untersuchen. |
| [bug-report](softwarefabric/bug-report/SKILL.md) | Einen fälligen Vertical Slice auf funktionale Bugs untersuchen und bewertete Befunde mit Lösungsvorschlägen dokumentieren. |
| [security-report](softwarefabric/security-report/SKILL.md) | Einen fälligen Vertical Slice auf Cyber-Sicherheitslücken untersuchen und bewertete Befunde mit Lösungsvorschlägen dokumentieren. |
| [validate-findings](softwarefabric/validate-findings/SKILL.md) | Reportbefunde unabhängig validieren, Schwere und UX-Auswirkungen bewerten und vollständige Issues mit Umsetzungsgates erstellen. |
| [implement-loop](softwarefabric/implement-loop/SKILL.md) | Freigegebene Issues nach Schwere umsetzen, Draft-PRs durch den Council prüfen und bestandene PRs zur manuellen Merge-Entscheidung bereitstellen. |
| [council](softwarefabric/council/SKILL.md) | Zwei unabhängige PR-Reviews durch GPT-6.1 Sol und Claude Opus 5.5; Noten, Befunde und Runden direkt im PR kommentieren. |
| [ui-polish-loop](softwarefabric/ui-polish-loop/SKILL.md) | UI/UX in Screenshot-Review-Runden mit demselben Council verbessern, bis beide die Zielnote vergeben; Abzugsrubrik, Befund- und Entscheidungsregister, Bestätigungsrunde mit Holdout. |

Die Report-Skills starten die Validierung nicht selbstständig. `validate-findings`
übernimmt Verifikation und Issue-Erstellung. `implement-loop` implementiert die
freigegebenen Issues und nutzt die Paketfassung von `council`. Merge und Deployment
bleiben außerhalb der automatischen Pipeline.

## Paket und Verwendung

Behalte das **gesamte Verzeichnis `softwarefabric` mit seinen relativen Pfaden**
zusammen. Beide Report-Skills verwenden denselben Ablauf, dieselbe Reportvorlage
und denselben Helfer in `shared/`; dieser nutzt das Git-Gate von `map-codebase`.
Beim Einbinden in einen Agent-Runner registriere die acht `SKILL.md` an ihrem
jeweiligen Pfad. Einzelne Skill-Ordner ohne die gemeinsamen Dateien zu kopieren
reicht für die Report-Skills nicht aus.

Beispielaufträge im Zielrepository:

```text
Nutze $map-codebase, um dieses Repository zu kartieren oder seine vorhandene
Code-Map anhand der Änderungen seit dem letzten Prüfstand zu aktualisieren.
```

```text
Nutze $bug-report, um genau einen fälligen Vertical Slice auf funktionale Bugs
zu prüfen und einen Report mit Evidenz, Bewertung und Lösungsvorschlägen zu erstellen.
```

```text
Nutze $security-report, um genau einen fälligen Vertical Slice auf Sicherheitslücken
zu prüfen und einen Report mit Evidenz, Bewertung und Lösungsvorschlägen zu erstellen.
```

## Gesamte Pipeline starten

```text
Nutze $orchestrator für dieses Repository und führe die gesamte Softwarefabric-Pipeline aus.
```

Standard: Opus 5.5 `medium` für Karte, Reports und Umsetzung; Sol 6.1 `high` für
unabhängige Validierung. Beide sitzen mit `high` in frischen Council-Instanzen.
Das [Rollenprofil](softwarefabric/orchestrator/assets/default-profile.json) kann
vor dem Start ausdrücklich angepasst werden und wird pro Lauf eingefroren.
Ein Durchlauf prüft jeden Vertical Slice einmal pro Reportart und arbeitet danach
alle ausführbaren Pipeline-Issues bis zum geprüften PR ab. Menschliche Freigaben
und manueller Merge bleiben erhalten. Laufbelege erlauben Wiederaufnahme ohne
doppelte Reports, Issues oder PRs. Ein Skill ist eine ausführbare Agent-Anweisung;
der Plan-Helfer startet allein keine Modelle.

## Code-Map und Prüfstände

`map-codebase` legt im **Zielrepository** `CODE_MAP.md` und Steckbriefe unter
`docs/code-map/` an. Der maschinenlesbare Kartierungs-Prüfstand in `CODE_MAP.md`
enthält die vollständig geprüfte Git-SHA. Wiederholungen vergleichen zuerst Git:

- **Gleicher Quellstand:** keine erneute Kartierung und keine Dokumentänderungen.
- **Geänderter Quellstand:** nur den Diff seit der letzten vollständigen Kartierung
  und betroffene Einträge untersuchen.
- **Nur Karten- oder Report-Ausgaben geändert:** keine erneute Codekartierung.
- **Uncommittete Eingaben oder fehlender Basiscommit:** Blocker melden;
  vorhandene Arbeit weder committen noch verwerfen.

Der Prüfstand wird erst nach erfolgreichem Abschluss und abschließendem
Gitvergleich fortgeschrieben. Eine Teilprüfung erhält keinen vollständigen Prüfstand.
Alte Prüfstände ohne den neuen Report-Ausgabepfad bleiben lesbar.

Das Slice-Register der Karte enthält pro Bereich `id`, `kind` und `document`.
`kind: vertical` nimmt an der Report-Rotation teil. Gemeinsame Mechanismen
(`shared`) und technische Grundlagen (`technical`) sind bei Bedarf Kontext.
Bei älteren Karten lässt sich das Register einmal aus dem vorhandenen Verzeichnis
und den Steckbriefen ergänzen, ohne unveränderten Code erneut zu kartieren.
`CODEMAP.md` kann alternativ verwendet werden; zwei Karten müssen eindeutig
über `--map` aufgelöst werden.

## Gemeinsamer Report-Zyklus

Bug- und Securityreport laufen gleich ab und führen **getrennte Warteschlangen**:

1. Noch nie vollständig geprüfte Slices zuerst, in Registerreihenfolge.
2. Danach jeweils den Slice mit dem ältesten abgeschlossenen Prüfzeitpunkt.
3. Pro Aufruf genau einen Slice reservieren und untersuchen.
4. Markdown-Report mit allen belegten Befunden, Auswirkung, Evidenz, Bewertung,
   Lösungsvorschlag und Regressionstest im Zielrepository speichern.
5. Erst nach vollständigem Abschluss den Bearbeitungsstand in `CODE_MAP.md`
   markieren: Zeitpunkt, geprüfte SHA, Report-Pfad und Lauf-ID.

Ein gleicher Git-Stand überspringt die **Kartierung**, aber nicht den nächsten
Report-Slice. Neue Slices werden zuerst berücksichtigt. Teilprüfungen und
Abbrüche verschieben keinen erfolgreichen Prüfzeitpunkt. Null belegte Befunde
sind ein gültiges Ergebnis, wenn der vereinbarte Umfang tatsächlich geprüft wurde.

Die Reports liegen unter `docs/softwarefabric/reports/<Modus>/`. Markdown ist der
maßgebliche Befundbestand für folgende Agents; eine HTML-Ansicht kann daraus
abgeleitet werden. Ungeklärte Kandidaten sind von belegten Befunden getrennt;
eine unabhängige Verifikation wird nicht vorgetäuscht.

Die CODE_MAP-Blöcke für Kartierungs-Prüfstand, Slice-Register und Report-Fortschritt
sind voneinander getrennt. Der gemeinsame Helfer schützt Zustandsänderungen im
selben Checkout vor gegenseitigem Überschreiben. Aktive Läufe können fortgesetzt
oder bei nachgewiesenem Abbruch freigegeben werden. Mehrere entfernte Checkouts
benötigen Koordination durch den aufrufenden Runner.

## Validierung und Issue-Übergabe

`validate-findings` bearbeitet einen fertigen Report pro Aufruf. Der Agent prüft
jeden Befund erneut am aktuellen Code und kann ihn bestätigen, widerlegen, als
unklar, nachweisbar behoben oder bereits erfasst einordnen. Quellreport und
Slice-Bearbeitungsstand bleiben erhalten; die Validierung erhält ein eigenes
Markdown-Ergebnis und Fortschrittsnachweise im Report-Ausgabeverzeichnis.

```text
Nutze $validate-findings, um den nächsten abgeschlossenen Report unabhängig
zu validieren und belegte, noch offene Befunde als vollständige GitHub-Issues
im untersuchten Repository zu erfassen.
```

Für bestätigte Befunde werden drei Werte mit getrennten Begründungen vergeben:
Schweregrad **0–10**, UX-Auswirkung des Problems und UX-Auswirkung der Änderung.
**10 bedeutet hohe Auswirkung. Ab 7/10 in einem UX-Wert oder bei unbekannter
UX-Auswirkung verlangt die Umsetzung menschliche Freigabe.**

Diese Issues tragen `softwarefabric:validated`, die Befundart,
`softwarefabric:needs-human-approval` und `softwarefabric:blocked`; der Titel
nennt die Freigabepflicht. Sie erhalten kein `ready-for-implementation`.
Niedrige bekannte UX-Auswirkungen erlauben `softwarefabric:ready-for-implementation`,
sofern keine anderen Blocker bestehen. Body und Labels müssen übereinstimmen.

Die Issue-Übergabe enthält Evidenz, Scores, aktuellen Git-Stand, betroffene Stellen,
Reproduktion, Lösung, Alternative, Risiken, Akzeptanzkriterien und Regressionstests.
Ein maschinenlesbarer Block bindet das Gate an Befund, geprüften Commit und
Lösungsplan. Der Validierungsagent kann menschliche Zustimmung nicht selbst
vergeben. Der spätere Umsetzungsskill muss Gate und Freigabebeleg live prüfen.

Duplikate werden über offene und geschlossene Issues geprüft. Unklare oder
zurückgewiesene Punkte erzeugen keine Umsetzungs-Issues; gescheiterte Publikation
bleibt als Blocker erhalten. Sensible Sicherheitsdetails folgen den zulässigen
privaten Disclosure-Kanälen des Zielrepositories. Das Skill-Repository `t2stack`
ist nicht automatisch das Zielrepository eines Befunds.

Der nur lesende [Policy-Helfer](softwarefabric/validate-findings/scripts/issue_policy.py)
bereitet Inhalt und Labels vor und verhindert widersprüchliche Gates. Er bewertet
keinen Code und nimmt keine GitHub-Schreibzugriffe vor. Die inhaltliche Prüfung,
Duplikatsuche, Publikation und das Rücklesen erfolgen durch den Agenten:

```bash
python3 softwarefabric/validate-findings/scripts/issue_policy.py --record <Datensatz.json> --repository <owner/repo>
```

Details: [Bewertungs- und Freigaberegeln](softwarefabric/validate-findings/references/ratings-and-gates.md).

## Umsetzungsloop mit sichtbarem Council-Verlauf

```text
Nutze $implement-loop, um freigegebene Softwarefabric-Issues nach Schwere
umzusetzen. Erstelle Draft-PRs, lasse den Council genau diese PRs reviewen und
stelle bestandene PRs zur manuellen Merge-Entscheidung bereit. Nicht selbst mergen.
```

Der Loop wählt das schwerwiegendste aktuell ausführbare Pipeline-Issue. Menschliche
UX-Freigaben aus der Validierungsstufe bleiben verbindlich; blockierte Issues
werden nicht durch hohe Schwere oder einen PR übergangen. Andere ausführbare
Issues können weiterbearbeitet werden.

Der Ablauf pro Issue ist **Fix und Tests → Draft-PR → Council-Kommentare im PR →
Korrekturen und neue Review-Runden im selben PR → geprüfter normaler PR**.
Beide Council-Mitglieder müssen in der aktuellen Runde unabhängig mindestens
**9,5/10 Gesamtqualität** vergeben, ohne offene Blocker. Der Review-Auftrag nennt
diese Mindestnote nicht; der Aufrufer übermittelt keine Elternhistorie oder interne
Gate-Politik. Qualitätsnoten werden weder gemittelt noch aufgerundet.

| Mitglied | Provider | Modell | Einstellung |
| --- | --- | --- | --- |
| GPT-6.1 Sol | `codex` | `gpt-6.1-sol` | `reasoningEffort: high` |
| Claude Opus 5.5 | `claudeAgent` | `claude-opus-5-5` | `effort: high` |

Die Paketfassung von `council` ist ausdrücklich zu laden; eine abweichende globale
Fassung darf sie nicht unbemerkt ersetzen. Fehlt eines der benannten Mitglieder,
wird der Blocker gemeldet. Kein drittes Modell und keine unangefragte Ersetzung.

Jedes Mitglied kommentiert jede Runde mit Befunden, vier Einzelnoten, Gesamtnote,
Base-/Head-SHA und Diff-Hash. Der Umsetzungsagent dokumentiert seine Korrekturen
und Testergebnisse als Antworten im PR. Eine Übersicht in der Beschreibung
verlinkt die Runden. Der Verlauf bleibt beim manuellen Mergen lesbar.

Alte Reviews gelten nicht für neue Commits oder einen veränderten Base-/Diff-Stand.
Gute Council-Noten überschreiben keine fehlenden Checks, Konflikte, menschlichen
Änderungswünsche oder fehlenden UX-Freigaben. Nach drei aufeinanderfolgenden
Runden ohne belegbaren Fortschritt wird ein Issue mit seinem Draft und Blocker
zurückgestellt; produktive Korrekturrunden dürfen weiterlaufen.

Bereitgestellte PRs tragen `softwarefabric:ready-for-merge-review` und bleiben
**unmerged**. `awaiting_merge` ist nicht „Issue erledigt“. Keine automatische
Issue-Schließung vor dem Merge, kein Auto-Merge und kein Deployment. Sind nur
blockierte Issues übrig, endet der aktive Lauf mit den konkreten offenen Punkten
statt einer Endlosschleife. Bereits geprüfte aktuelle PRs werden nicht doppelt erstellt.

Der [nur lesende Loop-Helfer](softwarefabric/implement-loop/scripts/loop_policy.py)
prüft Snapshots der Warteschlange, filtert neutrale Review-Kontextfelder und prüft
die Bindung beider Reviews an den aktuellen PR-Stand. Er führt selbst keine
Agents oder GitHub-Aktionen aus und ersetzt keine tatsächliche Prüfung menschlicher
Freigaben. Details: [Loop-Vertrag](softwarefabric/implement-loop/references/loop-contract.md).

## UI-Polish-Loop

```text
Nutze $ui-polish-loop, um die Oberfläche dieses Repositorys in Review-Runden zu
verbessern, bis der Council die Zielnote vergibt. Zielnote: 9,5.
```

Der Loop arbeitet mit Screenshots statt Diffs: aufnehmen, blind durch beide
Council-Mitglieder bewerten lassen, Befunde triagieren, umsetzen, Vergleichsbilder
und PR-Kommentar, nächste Runde. Damit Worker und Council auf die Zielnote
zulaufen, aber nicht zu früh dort ankommen:

- **Abzugsrubrik:** Die Note startet bei 10 und sinkt nur für belegte Befunde
  (`blocker` 1,0, `defekt` 0,3, `politur` 0,1, `geschmack` 0). Sie steigt, wenn
  Defekte verschwinden, und eine stabile Restnote hat benennbare Gründe.
- **Befundregister:** Jedes Mitglied prüft seine eigenen offenen Befunde nach,
  ohne frühere Noten zu sehen. Halluzinationen und Umkehrungen werden mit Beleg
  abgelehnt.
- **Entscheidungsregister:** Abgewogene Entscheidungen stehen im Brief; Einträge
  nur durch den Nutzer oder bei belegter Umkehr, nie zum Stilllegen von Kritik.
- **Blindheit:** Kein Brief nennt Zielnote, frühere Noten oder das Gate; Rubrik
  und Wortlaut bleiben pro Lauf eingefroren (Hash).
- **Bestätigung:** Bestanden ist erst nach zwei Runden auf Zielnote, die zweite
  mit frischen Instanzen, gleichem Commit und zusätzlichen Holdout-Ansichten,
  ohne offene Defekte. Sprünge über 0,5 verlangen ebenfalls Bestätigung.
- **Stagnation:** Drei Runden ohne Anstieg des Minimums halten den Lauf an und
  gehen mit Bericht an den Menschen.

Das [Gate](softwarefabric/ui-polish-loop/scripts/gate.py) entscheidet nur lesend
aus `rounds.json` und `ledger.json`. Screenshots und Vergleichsbilder liefern
[`shoot.mjs`](softwarefabric/ui-polish-loop/scripts/shoot.mjs) (Playwright,
feste Uhrzeit) und [`compare.py`](softwarefabric/ui-polish-loop/scripts/compare.py)
(Pillow, NumPy). Details: [Konvergenzregeln](softwarefabric/ui-polish-loop/references/convergence.md).

## Helfer und Tests

Benötigt werden Python 3.10+ und Git, keine zusätzlichen Python-Pakete.
Der Git-Prüfer schreibt keine Dateien:

```bash
python3 softwarefabric/map-codebase/scripts/check_git_state.py --repo /pfad/zum/zielrepo
```

Der Report-Helfer erzeugt ausschließlich reservierte Report-Ausgaben und den
getrennten Report-Fortschritt in der Ziel-Code-Map:

```bash
python3 softwarefabric/shared/review_cycle.py start --repo /pfad/zum/zielrepo --mode bug-report
python3 softwarefabric/shared/review_cycle.py finish --repo /pfad/zum/zielrepo --run <relative-.run.json>
python3 softwarefabric/shared/review_cycle.py abort --repo /pfad/zum/zielrepo --run <relative-.run.json> --reason 'Konkreter Abbruchgrund'
```

Details: [gemeinsamer Ablauf](softwarefabric/shared/review-workflow.md),
[Reportvorlage](softwarefabric/shared/report.template.md).

```bash
python3 -m unittest discover -s softwarefabric/map-codebase/scripts -p 'test_*.py' -v
python3 -m unittest discover -s softwarefabric/shared -p 'test_*.py' -v
python3 -m unittest discover -s softwarefabric/validate-findings/scripts -p 'test_*.py' -v
python3 -m unittest discover -s softwarefabric/implement-loop/scripts -p 'test_*.py' -v
python3 -m unittest discover -s softwarefabric/ui-polish-loop/scripts -p 'test_*.py' -v
```

## Struktur

```text
softwarefabric/
  orchestrator/
    SKILL.md
    assets/default-profile.json
    scripts/
  map-codebase/
    SKILL.md
    agents/
    assets/
    scripts/
  bug-report/
    SKILL.md
    agents/
  security-report/
    SKILL.md
    agents/
  validate-findings/
    SKILL.md
    agents/
    assets/
    references/
    scripts/
  implement-loop/
    SKILL.md
    agents/
    assets/
    references/
    scripts/
  council/
    SKILL.md
    agents/
    assets/
  shared/
    review-workflow.md
    report.template.md
    review_cycle.py
    test_review_cycle.py
```
