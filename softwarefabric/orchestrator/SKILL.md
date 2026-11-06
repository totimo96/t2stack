---
name: orchestrator
description: Führt die Softwarefabric-Pipeline mit vorab festgelegten Agent-Rollen aus. Kartiert Code, prüft alle Vertical Slices auf Bugs und Sicherheit, lässt Befunde unabhängig validieren und setzt freigegebene Issues mit sichtbaren Council-Reviews bis zu geprüften PRs um. Verwenden für einen vollständigen Pipeline-Durchlauf oder dessen Fortsetzung.
---

# Softwarefabric-Orchestrator

Steuere das gesamte Paket im ausdrücklich benannten **Zielrepository**. Ein Aufruf
umfasst einen vollständigen, begrenzten Prüfdurchlauf und anschließend die
Umsetzung aller ausführbaren validierten Pipeline-Issues bis zu geprüften PRs.
Merge und Deployment bleiben menschliche Entscheidungen. Lies die folgenden
Skills jeweils vor ihrer Phase; führe ihre Facharbeit durch die zugewiesenen Agents aus.

## Rollen vor Beginn festlegen

Nutze [assets/default-profile.json](assets/default-profile.json), sofern der Nutzer
kein anderes Profil vorgibt. Nenne beim Start Zielrepo und aufgelöste Rollen:

| Arbeit | Standard |
| --- | --- |
| Code-Map, Bugreport, Securityreport, Implementierung und Korrekturen | `claudeAgent` / `claude-opus-5-5`, `effort: medium` |
| Unabhängige Befundvalidierung und Issue-Erstellung | `codex` / `gpt-6.1-sol`, `reasoningEffort: high` |
| Council, frische Instanz des Arbeitstiers | Opus 5.5, `effort: high` |
| Council, frische Instanz des Verifiers | Sol 6.1, `reasoningEffort: high` |

Das Profil kann **vor** dem Lauf explizit gewählt werden. Ohne weitere Vorgabe
ist der Scope das aktuelle Git-Repository; kläre nur fehlende oder mehrdeutige Ziele. Genau zwei unterschiedliche
Modelle übernehmen Worker und Verifier und bilden gemeinsam den Council; im Council
prüfen beide mit `high`. Eine andere Modellwahl ist eine ausdrückliche Nutzerwahl,
kein automatischer Ersatz. Prüfe das Profil mit `shared/role_profile.py` beziehungsweise
dem Plan-Helfer und seine tatsächliche Verfügbarkeit über `orchestrator_capabilities`
einmal pro Thread vor der ersten Delegation. Fehlt ein Modell oder eine Einstellung,
melde den Blocker. Keine stillen Fallbacks, CLI- oder Workflow-Ersatzmodelle.

Delegiere in T3 über `delegate_task`, genaue Einstellungen in `target.options`.
Jeder Auftrag erhält Rolle, absoluten Skillpfad, Zielrepo, begrenzten Umfang,
Eingabeartefakte und verlangte Rückgabe. Keine Elternhistorie weiterreichen.
Children starten keine weiteren Agents. Folge `next`; keine Status-Pollschleifen.
Der Controller bleibt für Reihenfolge, Evidenzprüfung und Freigabegates verantwortlich.

## Dauerhafter Lauf und Wiederaufnahme

Lege unter `docs/softwarefabric/reports/orchestrator/<run-id>/` im Zielrepo an:

- `profile.json`: unverändertes aufgelöstes Profil; SHA-256 gemäß `role_profile.digest`;
- `run.json`: Run-ID, Zielrepo/Remote, Quell-HEAD, Kartenpfad, Registry-Hash,
  eingefrorene Slice-Liste, Profilhash, Jobs mit Status und Artefaktbelegen;
- pro Job: Phase/Slice/Quellreport, tatsächliche Provider/Modell/Optionen,
  Delegate-ID, Start/Ende, Eingabehashes, Ausgabe- und Issue-/PR-/Kommentarlinks,
  geprüfter Stand, konkrete Blocker und nächste Aktion.

Speichere atomar nach jedem Übergang. Plane Schreibarbeit sequenziell; kein zweiter
Orchestrator schreibt gleichzeitig in dasselbe Zielrepo. Bei vorhandenen aktiven
Läufen zuerst Zustand und lebende Delegates prüfen, keine Doppelstarts. Setze einen
unterbrochenen Lauf mit demselben Profil fort; eine Profiländerung verlangt einen
neuen explizit gestarteten Lauf. Erfolg nie aus einem Delegate-Status allein ableiten:
Artefakte zurücklesen, Hashes, tatsächliche Rolle, Umfang und fachliche Gates prüfen.
Ein Plan ist kein Ausführungsnachweis.

Bei Wiederaufnahme bereits belegte abgeschlossene Jobs nicht wiederholen. Laufende
Report-Claims über den Report-Helfer fortsetzen oder nach nachgewiesenem Abbruch
abbrechen. Veraltete Quellstände invalidieren die betroffenen offenen Jobs; keine
Reports unterschiedlicher Quellstände als denselben vollständigen Sweep ausgeben.
Fremde uncommittete Arbeit erhalten. Bei veränderter Registry/Quelle vor Abschluss
der Prüfphasen den Lauf als unterbrochen markieren und einen neuen Quell-Snapshot
kartieren; abgeschlossene Reports bleiben historische Belege.

## Phasen in dieser Reihenfolge

1. **Kartieren – Worker.** Rufe [map-codebase](../map-codebase/SKILL.md) auf.
   Unveränderter Code ist ein gültiger belegter No-op. Erst bei gültiger Karte
   fortfahren. Danach Quell-HEAD und Registry einfrieren.
2. **Reports – Worker.** Rufe [bug-report](../bug-report/SKILL.md) und
   [security-report](../security-report/SKILL.md) für **jeden Vertical Slice einmal**
   auf. Registerreihenfolge genügt. Verwende beim Reservieren `review_cycle.py start
   --slice-id <id>` plus richtigen Modus/Kartenpfad. Jeder Aufruf bearbeitet nur den
   geplanten Slice. Bestehende erfolgreiche Einzel-Skill-Läufe sind kein Ersatz für
   neue Sweep-Jobs, außer sie gehören nachweislich genau zu diesem fortgesetzten Lauf.
   Kein Endloswechsel zum jeweils ältesten Slice innerhalb desselben Durchlaufs.
3. **Verifizieren – Verifier.** Nach Ende der Reportphase rufe
   [validate-findings](../validate-findings/SKILL.md) pro erfolgreich abgeschlossenem
   Report mit dessen exaktem Pfad/Hash auf. Auch Nullbefunde erhalten einen knappen
   Validierungsnachweis. Der Verifier liest Report und aktuellen Code eigenständig;
   übernimmt keine Worker-Behauptung als Beweis. Zurückweisen ist erlaubt.
   Veröffentlichte Issues zurücklesen und protokollieren. Die Ausführung dieses
   Orchestrators umfasst Reports und Issue-Erstellung im Zielrepo, keine Publikation
   vertraulicher Befunde in einem unzulässigen öffentlichen Kanal.
4. **Umsetzen – Controller + Worker.** Lade
   [implement-loop](../implement-loop/SKILL.md). Der Controller lädt die gesamte
   aktuelle Pipeline-Warteschlange, prüft menschliche Freigaben und wählt nach
   Schweregrad. Delegiere dem Worker pro Issue nur `prepare-pr` beziehungsweise
   `correct-pr` gemäß dem dortigen Orchestrator-Modus. Der Worker erstellt Fix,
   passende Tests und Draft-PR beziehungsweise Korrekturcommits im bestehenden PR.
   Keine Council-Aufrufe im Worker und keine gesamte Loop-Policy im Review-Briefing.
5. **Council – beide, frische Kontexte.** Der Controller lädt die Paketfassung
   [council](../council/SKILL.md) und startet die zwei im eingefrorenen Profil
   benannten Mitglieder mit neutralem Briefing für den exakten PR-Stand. Die beiden
   unabhängigen Reviews dürfen parallel laufen. Schreibe jede Runde/Mitglied mit
   Attribution und Evidenz direkt in denselben PR, lies Kommentare zurück und
   aktualisiere die zweizeilige Council-Tabelle mit den tatsächlichen Mitgliedern.
   Der Controller prüft das Gate des Umsetzungsloops mit `--profile <profile.json>`
   und `profile_sha256` im PR-Snapshot. Mindestnote und interne Freigabepolitik
   bleiben ausschließlich beim Controller; niemals an Council-Delegates weitergeben.
   Bei Korrekturen zurück zu Worker, anschließend frische Reviews beider Mitglieder.
6. **Nächstes Issue.** Nach bestandenem Gate PR zur manuellen Merge-Entscheidung
   bereitstellen und das nächste ausführbare Issue bearbeiten. Keine eigenen Merges,
   kein Auto-Merge, keine Issue-Schließung vor Merge. Kein erneuter Council auf
   unverändertem Stand nur für eine bessere Note. Fortschritts- und Abbruchregeln
   des Umsetzungsloops gelten unverändert.

Reportfehler blockieren ihre Validierung, nicht unabhängige übrige Slices. Nach
Abschluss aller versuchten Reportjobs können erfolgreiche Reports validiert und
daraus ausführbare Issues umgesetzt werden. Ein solcher Lauf bleibt **unvollständig**;
abhängige Jobs als blockiert kennzeichnen, nie als erfolgreich überspringen.
Fehlt die Code-Map oder ändern sich relevante Quellen, keine abhängigen Prüfungen.
Menschlich gesperrte Issues zurückstellen und übrige ausführbare Issues abarbeiten.

## Plan-Helfer und Abschluss

Nach der Kartierung den JSON-Inhalt des `softwarefabric:slices`-Blocks extrahieren:

```bash
python3 /pfad/softwarefabric/orchestrator/scripts/plan_run.py \
  --registry <slices.json> --profile <profile.json>
```

Der Helfer liefert einen festen Jobplan und exakte Delegationsziele. `depends_on`
verlangt erfolgreich belegte Vorgänger; `phase_barrier` verlangt, dass alle genannten
Jobs beendet oder konkret blockiert sind. Er führt keine Agents aus und schreibt
keine Erfolgseinträge. Vor dem Registry-Snapshot wird der Map-Job bereits separat
ausgeführt; seinen Beleg in den generierten Plan übernehmen, nicht erneut starten.

Gib am Ende Rollen/Profilhash, Slice-Abdeckung, validierte/zurückgewiesene Befunde,
Issue-/PR-Links, Council-Ergebnisse und ausstehende menschliche Entscheidungen an.
Unterscheide `completed_no_findings`, `awaiting_merge`, `blocked` und
`partial_blocked`. „Pipeline abgeschlossen“ bedeutet abgeschlossene Prüfjobs und
keine noch ausführbaren Umsetzungsschritte; es bedeutet niemals „alles gemergt“.
Nenne zum Fortsetzen Laufpfad und nächste konkrete Aktion. Kein neuer Sweep allein,
um nach bereits bereitgestellten PRs beschäftigt zu bleiben.
