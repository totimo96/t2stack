---
name: council
description: Prüft einen Pull Request mit zwei vorab festgelegten Council-Mitgliedern unabhängig und nur lesend; standardmäßig GPT-6.1 Sol und Claude Opus 5.5. Dokumentiert jede Review-Runde mit Befunden, begründeten Qualitätsnoten und geprüftem Git-Stand direkt im PR. Verwenden bei Council-Reviews; implementiert keine Fixes und entscheidet nicht über Merge oder Deployment.
---

# Council: nachvollziehbares PR-Review

Diese Paketfassung folgt der benannten Besetzung des Nutzers. Es gibt **genau
zwei Mitglieder**, beide mit hoher Reasoning-Einstellung:

| Mitglied | Provider in T3 Code | Modell | `target.options` |
| --- | --- | --- | --- |
| GPT-6.1 Sol | `codex` | `gpt-6.1-sol` | `{"reasoningEffort":"high"}` |
| Claude Opus 5.5 | `claudeAgent` | `claude-opus-5-5` | `{"effort":"high"}` |

Kein drittes Mitglied suchen. Ist ein benanntes Mitglied oder seine Einstellung
nicht verfügbar, den konkreten Blocker melden und nichts ersetzen. Unvollständige
Reviews nicht als vollständigen Council ausgeben.

## Vorbereitung

- Der Umsetzungsagent hat bekannte Fehler und zutreffende offene Kommentare
  bereits bearbeitet und passende Prüfungen ausgeführt. Der PR existiert und
  enthält den tatsächlich zu prüfenden aktuellen Commit.
- Lies PR, Issue-Verknüpfung, Beschreibung, aktuellen Diff, relevante Regeln und
  bestehende Review-Historie. Erfasse Repository, PR-URL, Base-SHA, Head-SHA und
  SHA-256 des vollständigen Base-zu-Head-Diffs. Stelle diesen Diff als
  unveränderliches Artefakt bereit; Hash und Review müssen dieselben Bytes
  beziehungsweise denselben nachvollziehbaren Base/Head-Kontext betreffen.
- Änderungen nur lesen. Keine Anwendung ändern, keine Zustimmung im Namen eines
  Menschen abgeben und keinen PR mergen oder zur Veröffentlichung freigeben.

## Unabhängige Reviews starten

Verwende [assets/review-brief.md](assets/review-brief.md) als neutrales Briefing.
Übermittle nur fachlichen Auftrag, Issue, Akzeptanzkriterien, aktuelle PR-Daten,
prüfbare Testbelege und die relevanten Codekontexte. Interne Freigabepolitik,
Zielnoten, Mindestwerte und gewünschtes Bestehen gehören nicht in das Briefing.
Keine vollständige Unterhaltung oder übergeordneten Agent-Anweisungen weitergeben.
Bewertbare Codeinhalte oder ungünstige Testergebnisse nicht aus dem Diff entfernen.

In T3 Code einmal pro Thread vor der ersten Delegation
`orchestrator_capabilities` aufrufen. Die benannten Modelle und Optionen prüfen,
dann pro Mitglied einen `delegate_task` ohne Elternhistorie mit den Einstellungen
in `target.options` starten. Für parallele unabhängige Reviews sind diese zwei
Delegationen Teil des Council-Auftrags. Die Delegates prüfen nur und starten
keine weiteren Agents. Bei fehlendem Provider keine CLI-, Modell- oder
Workflow-Ersatzlösung verwenden.

Jeder neue Review oder Re-Check ist ein neuer `delegate_task`; nicht durch eine
Nachricht an einen alten Review-Thread ersetzen. Folge der vom laufenden Delegate
zurückgegebenen `next`-Anweisung; keine Status-Pollschleifen. Andere Hosts dürfen
nur gleichwertige verfügbare Delegation mit exakt den benannten Modellen nutzen.

Bitte jedes Mitglied um:

- nachvollziehbare Befunde mit Stelle, Ursache, Auswirkung und Evidenz;
- getrennte Qualitätsbewertungen für Richtigkeit, Cybersicherheit, Codequalität
  und Performance sowie eine begründete Gesamtnote von 0 bis 10;
- Empfehlung `approve`, `request_changes` oder `abstain`;
- explizite Liste noch blockierender Befunde und nicht geprüfter Ebenen;
- Bestätigung von Base-SHA, Head-SHA und Diff-Hash des geprüften PR-Stands.

Hier bedeutet eine hohe Note **hohe Änderungsqualität**, nicht hohe Problemschwere.
Eine fehlende Note als `no score` festhalten. Keine Zahl erfinden, aufrunden,
verhandeln oder aus anderen Teilnoten nachträglich konstruieren.

## Ergebnisse direkt im Pull Request festhalten

Nach jedem Mitgliedsreview einen eigenen Kommentar beziehungsweise Review im
**betroffenen PR** veröffentlichen. Bei Proxy-Publikation den tatsächlichen
Urheber nennen. Alle agentverfassten Kommentare beginnen entsprechend der
Kommentar-Konvention mit:

```markdown
> [!NOTE]
> 🤖 **{verifiziertes Modell} responding on behalf of {Nutzername oder GitHub-Login}**

{Review-Inhalt}
```

Nutze [assets/pr-review-comment.template.md](assets/pr-review-comment.template.md).
Der Kommentar enthält Runde, Mitglied, geprüfte SHAs/Diff-Hash, vier Einzelnoten,
Gesamtnote, Empfehlung, konkrete Befunde und Grenzen. Sensible Daten vor der
Veröffentlichung entfernen beziehungsweise den zulässigen privaten Kanal verwenden.
Kommentar oder Review anschließend zurücklesen und seine URL speichern.

Bereits vorhandene identische Ergebnisse für Mitglied und Base/Head/Diff nicht
nochmals posten. Alte Bewertungen und Antworten nicht überschreiben oder löschen,
um eine bessere Historie vorzutäuschen. Eine neue Runde nach Änderungen bleibt
als neue Runde im Verlauf sichtbar.

Ergänze die PR-Beschreibung um eine kompakte Übersicht; sie ersetzt die Kommentare nicht:

```markdown
## Council review

Rounds: {Anzahl}

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| GPT-6.1 Sol | {Note und Kommentarlink} | {Note und Kommentarlink} |
| Claude Opus 5.5 | {Note und Kommentarlink} | {Note und Kommentarlink} |
```

Die Tabelle hat nur diese beiden Mitglieder. Falls die PR-Konvention eine Modell-
und Harnesszeile verlangt, steht die Übersicht davor. Attribution-Callouts gehören
in Kommentare, nicht in die PR-Beschreibung.

## Rückgabe und neue Runden

Gib beide unveränderten Originalbewertungen, Review-URLs, geprüfte SHAs,
Diff-Hash, Runde und verbleibende Befunde an den aufrufenden Agenten zurück.
Eine komplette Prüfung beider Mitglieder zählt als eine Runde; eine abgebrochene
Runde bleibt unvollständig. Uneinigkeit sichtbar erhalten und sachlich prüfen.

Der Umsetzungsagent entscheidet über Korrekturen und startet danach ein frisches
Review des neuen PR-Stands. Keine erneuten Reviews unveränderter Stände allein
zum Erzielen günstigerer Noten. Bei geänderter Base, Head oder Diff können alte
Noten nicht als Prüfung des neuen Stands gelten. Der Council kennt keinen
vom aufrufenden Ablauf gewünschten Zielwert und entscheidet nicht über dessen Gate.

## Vorab gewähltes Orchestrator-Profil

Wird dieser Skill durch die Paketfassung von `orchestrator` mit einem ausdrücklich
vor dem Lauf gewählten Rollenprofil aufgerufen, verwende dessen genau zwei
Council-Mitglieder: dieselben Identitäten wie Worker und Verifier, jeweils mit
`high`. Prüfe es über `../shared/role_profile.py`. Ohne dieses explizite Profil
bleibt die obige Standardbesetzung verbindlich. Kein drittes Mitglied oder Ersatz.
Die PR-Tabelle enthält die zwei tatsächlich gewählten Mitglieder; Profilhash und
exakte Konfiguration gehören in die dauerhaften Review-Belege. Der Controller
startet pro Mitglied eine frische Instanz, auch wenn dieses Modell zuvor Code
implementiert oder Befunde validiert hat. Implementierungsverlauf und interne
Zielnote gehören nicht in den Review-Kontext.
