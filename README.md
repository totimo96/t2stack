# t2stack

Wiederverwendbare Agent-Skills für eine organisierte Codeverbesserungspipeline.

## Softwarefabric

Die zusammengehörigen Skills liegen unter [`softwarefabric/`](softwarefabric/).
Sie bilden die ersten Stufen des Skillbaums „Automatic Security and Bugfixes“ ab:

| Skill | Aufgabe |
| --- | --- |
| [map-codebase](softwarefabric/map-codebase/SKILL.md) | Codebasis in Vertical Slices kartieren; bei Wiederholung nur Änderungen seit dem gespeicherten Git-Prüfstand untersuchen. |
| [bug-report](softwarefabric/bug-report/SKILL.md) | Einen fälligen Vertical Slice auf funktionale Bugs untersuchen und bewertete Befunde mit Lösungsvorschlägen dokumentieren. |
| [security-report](softwarefabric/security-report/SKILL.md) | Einen fälligen Vertical Slice auf Cyber-Sicherheitslücken untersuchen und bewertete Befunde mit Lösungsvorschlägen dokumentieren. |
| [validate-findings](softwarefabric/validate-findings/SKILL.md) | Reportbefunde unabhängig validieren, Schwere und UX-Auswirkungen bewerten und vollständige Issues mit Umsetzungsgates erstellen. |

Die Report-Skills starten die Validierung nicht selbstständig. `validate-findings`
übernimmt Verifikation und Issue-Erstellung; Fixes und Council-Freigaben bleiben
spätere Stufen.

## Paket und Verwendung

Behalte das **gesamte Verzeichnis `softwarefabric` mit seinen relativen Pfaden**
zusammen. Beide Report-Skills verwenden denselben Ablauf, dieselbe Reportvorlage
und denselben Helfer in `shared/`; dieser nutzt das Git-Gate von `map-codebase`.
Beim Einbinden in einen Agent-Runner registriere die vier `SKILL.md` an ihrem
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
```

## Struktur

```text
softwarefabric/
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
  shared/
    review-workflow.md
    report.template.md
    review_cycle.py
    test_review_cycle.py
```
