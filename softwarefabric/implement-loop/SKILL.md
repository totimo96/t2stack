---
name: implement-loop
description: Arbeitet freigegebene Softwarefabric-Issues nach Schwere ab, implementiert eng begrenzte Fixes in eigenen Branches und erstellt Draft-PRs. Lässt den Council direkt im PR reviewen, dokumentiert Korrekturrunden und stellt erst nach bestandenen Gates PRs zur manuellen Merge-Entscheidung bereit. Mergt nicht selbst.
---

# Softwarefabric-Umsetzungsloop

Bearbeite die Issues der vorherigen Pipeline-Stufen im **Zielrepository** bis
für alle ausführbaren Aufgaben geprüfte PRs bereitstehen. Erhalte menschliche
Freigaben, Review-Verlauf und offene Blocker. Dieser Auftrag umfasst Umsetzung,
Draft-PRs und Council-Reviews, aber keinen Merge oder Deployment.

Benötigt werden das gesamte `softwarefabric`-Paket, GitHub-Schreibzugriff und die
beiden benannten Council-Mitglieder. Lies
[references/loop-contract.md](references/loop-contract.md), die
[Freigaberegeln](../validate-findings/references/ratings-and-gates.md) und vor
Reviews [../council/SKILL.md](../council/SKILL.md).

## 1. Live-Warteschlange aufbauen

- Lies `AGENTS.md`, Repository-Konventionen, Zielrepository, Default-Branch und
  Arbeitsbaum. Vorhandene Änderungen erhalten. Kein Stash, Reset oder Verwerfen
  fremder Arbeit. Bei Bedarf eine eigene isolierte Arbeitskopie verwenden.
- Lade alle offenen Issues der Pipeline mit vollständiger Pagination, Body,
  Labels, Verknüpfungen, Review- und Freigabebelegen. Nur nachweislich durch
  Softwarefabric validierte Issues mit konsistentem Metadatenblock bearbeiten.
  Ein normales `bug`-Label oder die bloße Erwähnung eines Reports genügt nicht.
- Lade bestehende PRs und den dauerhaften Loop-Fortschritt. Vorhandene passende
  Draft-PRs fortsetzen. Bereits geprüfte PRs auf ihrem weiterhin aktuellen Stand
  nicht nochmals implementieren oder erneut zur Bewertung einreichen.
- Wähle den höchsten **Schweregrad des Problems** unter den aktuell ausführbaren
  Issues. Gleichstand: kleinere Issue-Nummer zuerst. Blockierte Issues sichtbar
  zurückstellen und anschließend das nächste ausführbare Issue wählen.

Der nur lesende Helfer kann normalisierte Live-Snapshots prüfen:

```bash
python3 /pfad/zu/softwarefabric/implement-loop/scripts/loop_policy.py select --input <queue.json>
```

Er ersetzt weder Live-Abfragen noch die Prüfung menschlicher Identität oder
inhaltlicher Evidenz. Die Snapshot-Felder beschreibt der Loop-Vertrag.

## 2. Freigabe vor jeder Umsetzung prüfen

Lies das ausgewählte Issue unmittelbar vor Arbeitsbeginn erneut. Body, Labels,
Scores, aktueller Lösungsplan und Freigabebelege müssen zusammenpassen. Ab einem
UX-Wert von 7/10 oder bei unbekannter UX-Auswirkung ist echte menschliche
Zustimmung zu genau diesem Plan erforderlich. Keine Zustimmung aus einem
Benutzerkonto, Label, Score oder der Existenz eines PRs ableiten.

Bei notwendiger Zustimmung müssen der menschliche Kanal, die berechtigte Person,
Zeitpunkt, Beleg, Issue und freigegebener Plan nachgewiesen sein. Der Agent darf
keine Freigabe erfinden, selbst erteilen oder Freigabesperren eigenmächtig entfernen.
Ist die Freigabe unklar, veraltet oder widerrufen, kein Fix dieses Issues.
Ist bereits ein PR vorhanden, eine frühere Merge-Review-Markierung zurücknehmen,
den PR bei Bedarf wieder als Draft kennzeichnen und den Freigabeblocker im
Verlauf dokumentieren. Bestehende Council-Noten ersetzen diese Zustimmung nicht.

Ein veränderter Lösungsplan, höhere UX-Auswirkung oder neue relevante Voraussetzung
verlangt erneute Validierung und gegebenenfalls erneute menschliche Zustimmung.
Das gilt auch während späterer Council-Korrekturen. Andere ausführbare Issues
können weiterbearbeitet werden.

## 3. Eng begrenzten Fix beweisen und Draft-PR erstellen

1. Bringe den eigenen Branch gemäß Repository-Konvention auf die aktuelle
   Default-Branch-Basis; keine fremden Branches umschreiben. Prüfe den Befund
   am aktuellen Code und grenze relevante Änderungen seit der
   Validierung ab. Bereits behoben, falsch bewertet oder durch fremde Arbeit
   überholt: Evidenz festhalten und an die Validierung zurückgeben, keinen
   künstlichen Fix und kein vorschnelles Schließen des Issues.
2. Verwende pro unabhängig umsetzbarer Ursache einen eigenen Branch und PR.
   Reproduziere das Problem sicher, implementiere den kleinsten vollständigen
   Fix und ergänze einen aussagekräftigen Regressionstest, wenn die Teststruktur
   das zulässt. Prüfe Akzeptanzkriterien und betroffene Nachbarverträge.
3. Führe passende lokale Tests, Typprüfung und Lint gemäß Repository aus. Bei
   UI-Verhalten die sichtbare Wirkung prüfen, wenn die Umgebung das ermöglicht.
   Grenze fehlende Browser-, Deployment- oder Produktionsbelege ehrlich ab.
4. Committe und pushe den tatsächlichen Arbeitsstand. Erstelle **jetzt einen
   Draft-PR**, noch vor dem Council, mit [assets/pr.template.md](assets/pr.template.md).
   Verknüpfe das Issue über die übliche Closing-Referenz für den späteren Merge;
   schließe es nicht bereits jetzt. Prüfe vorher, ob ein passender PR existiert.
5. Nutze vorhandene Host-Werkzeuge zum Verknüpfen des PRs mit dem Thread; in
   T3 Code unmittelbar nach Erstellen oder Push `link_pull_request` beziehungsweise
   `link_pull_requests` mit den vollständigen URLs aufrufen. Bestehende Links
   über Pushes hinweg erhalten. Kein Auto-Merge aktivieren.

Anwendungscode, Tests und tatsächlich nötige vorhandene Build-Werkzeuge gehören
zum Auftrag. Neue Abhängigkeiten oder zusätzliche privilegierte Aktionen nur mit
entsprechender Autorisierung. Repository-Schutzregeln niemals umgehen. Bei
Abhängigkeit von einem noch nicht gemergten PR den Zusammenhang dokumentieren
und blockieren, statt unbemerkt Änderungen fremder PRs zu übernehmen.

## 4. Council bezieht sich auf den PR

Rufe `$council` für genau diesen PR auf und lade ausdrücklich die Paketfassung
`softwarefabric/council/SKILL.md`; eine anderslautende globale Fassung nicht
stillschweigend an ihrer Stelle verwenden. Prüfen lassen:
Base-SHA, Head-SHA und vollständigen Diff-Hash sowie Issue, Akzeptanzkriterien und
Testbelege. Die beiden Mitglieder prüfen unabhängig und nur lesend.

**Die Mindest-Gesamtnote ist 9,5/10 für jedes der beiden Mitglieder einzeln.**
Nicht mitteln, aufrunden oder ein fehlendes Ergebnis durch ein anderes ersetzen.
Dieser Wert ist interne Orchestrierung: Er darf weder im Council-Briefing noch
als gewünschtes Ergebnis, Druck oder Bestehenshinweis mitgegeben werden. Delegiere
keine Elternhistorie und keine internen Gate-Dateien. Nutze für die freigegebenen
Kontextfelder gegebenenfalls:

```bash
python3 /pfad/zu/softwarefabric/implement-loop/scripts/loop_policy.py review-payload --input <pr-snapshot.json>
```

Der PR bleibt der gemeinsame Bezugspunkt. Beide Originalreviews werden direkt
im PR kommentiert, mit Runde, Noten, geprüften SHAs, Befunden und Kommentar-URLs.
Die PR-Beschreibung enthält zusätzlich die Übersicht aus dem Council-Skill.

Bei berechtigten Befunden: Korrigieren, Tests erneut prüfen, auf denselben PR
pushen und im PR auf die Befunde antworten. Nenne jeweils Review-Runde,
behobenen Punkt, neuen Commit und konkreten Prüfnachweis. Erst nach erfolgreicher
Antwort einen Review-Thread als erledigt markieren. Alte Kommentare bleiben stehen.
Alle agentverfassten Antworten tragen den Attribution-Callout aus dem Council-Skill.

Nach Codeänderungen beide Mitglieder frisch über den neuen Stand reviewen lassen.
Bei unverändertem Base/Head/Diff keine erneute Bewertungsrunde allein für eine
höhere Note starten. Unklare oder falsche Review-Annahmen sachlich mit Evidenz
klären; keine kosmetischen Scheinänderungen oder Notenverhandlung.

Nach drei aufeinanderfolgenden Korrektur-/Review-Runden ohne überprüfbaren
Fortschritt, fehlenden umsetzbaren Hinweisen oder einem nicht lösbaren Blocker
den Draft erhalten, die Ursache dokumentieren und mit
anderen ausführbaren Issues fortfahren. Fehlende Council-Mitglieder nicht ersetzen.
Solange belegter Fortschritt möglich ist, weiter korrigieren und prüfen.
Ein späterer Lauf setzt den gespeicherten Zustand fort; kein Endlos-Neustart
unveränderter blockierter Issues.

## 5. Erst nach bestandenem Gate zur Merge-Entscheidung bereitstellen

Prüfe erneut Issue-Freigabe, aktuellen PR-Head und Base sowie CI und Reviews.
Erforderlich sind passende aktuelle Prüfbelege, zwei vollständige Reviews der
selben Runde auf genau demselben Base/Head/Diff, beide Gesamtnoten mindestens
9,5, beide Empfehlungen `approve` und keine offenen blockierenden Befunde.
Menschliche `changes requested`, Konflikte oder ungeklärte Pflichtchecks sperren
auch bei hohen Council-Noten.

```bash
python3 /pfad/zu/softwarefabric/implement-loop/scripts/loop_policy.py review-gate --input <pr-snapshot.json>
```

Nur wenn inhaltliche und maschinelle Gates bestehen: Draft in einen normalen PR
umwandeln, `softwarefabric:ready-for-merge-review` setzen, Übersicht aktualisieren
und einen nachvollziehbaren Übergabekommentar mit PR-Head und Review-Links schreiben.
Vorhandene passende Labels erhalten. Das bedeutet **bereit zur manuellen
Merge-Entscheidung**, nicht automatisch alle menschlichen Branch-Protection-
Pflichten erfüllt. Verbleibende CODEOWNERS-/Repository-Freigaben explizit nennen.

Jeder Push, Rebase oder relevante Base-/Diff-Wechsel entwertet die alte
PR-Freigabe für den neuen Stand. Markierung zurücknehmen und aktuelle Prüfung
nachholen. Erforderliche Checks nicht als grün behaupten, solange sie laufen.

## 6. Bis zum ehrlichen Endzustand weiterarbeiten

Speichere nach jedem Schritt Issue, Branch, PR, SHAs, Review-Runden/-URLs,
Prüfungen, aktuellen Gate- und Blockerstatus unter
`docs/softwarefabric/reports/implementation/`. Operative Fortschrittsdateien
nicht nach dem Review als zusätzlichen Commit in den geprüften PR einschleusen.
Der PR-Verlauf bleibt die von Menschen direkt lesbare Review-Historie.

Lade danach die Warteschlange erneut und bearbeite das nächste ausführbare Issue.
Ein fertiger offener PR zählt als `awaiting_merge`, nicht als gemergt. Ein
fehlgeschlagener oder abgebrochener Versuch ist kein erledigtes Issue.

Sind nur menschlich blockierte, abhängige oder unverändert festgefahrene Issues
übrig, beende den aktiven Lauf mit konkreten Blockern. Warten auf CI/Reviews mit
verfügbaren Host-Watchern und gespeicherter Fortsetzung behandeln; keine Sleep-
oder Pollschleifen. Bei späterer Fortsetzung erst Änderungen und Gates neu lesen.

Abschluss: alle PR-Links, geprüfte Stände, Council-Verlauf, noch offene Issues,
Blocker und nötige menschliche Entscheidungen aufführen. Nur bei tatsächlich
leerer Issue-Warteschlange „alles erledigt“ sagen. Nie Merge, Auto-Merge,
Deployment oder ein Schließen vor dem tatsächlichen Merge veranlassen.
