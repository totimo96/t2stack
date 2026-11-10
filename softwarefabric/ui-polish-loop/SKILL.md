---
name: ui-polish-loop
description: Verbessert UI und UX einer Web-App in Runden, bis zwei unabhängige Design-Reviewer anhand von Screenshots die Zielnote vergeben. Pro Runde Screenshots, blindes Review mit Abzugsrubrik, Triage gegen Befund- und Entscheidungsregister, Umsetzung, Vergleichsbilder und PR-Kommentar. Verwenden für „UI polish“, Design-Review-Schleifen und Screenshot-Councils; nicht für Code-Reviews.
---

# UI-Polish-Loop

Hebe die sichtbare Qualität einer Oberfläche in **Runden**, bis beide Council-
Mitglieder die vom Nutzer genannte Zielnote erreichen. Konvergenz entsteht durch
geschlossene **Defekte**, nicht durch Überreden: Die Note sinkt nur für belegte
Abzüge, und jede Runde prüft offene Befunde nach. Ein zu frühes Bestehen
verhindern eine **Bestätigungsrunde** mit frischen Prüfern und ungesehenen
Screenshots.

Die Regeln zu Rubrik, Registern, Gate und Stagnation stehen in
[references/convergence.md](references/convergence.md). Lies sie vor Runde 1.
Besetzung und Delegationsregeln des Councils kommen aus
[../council/SKILL.md](../council/SKILL.md) (genau zwei Mitglieder, beide `high`).

## 0. Lauf einrichten

- Kläre mit dem Nutzer: Zielnote, Branch/PR, Seiten und Rollen (Demo-URLs),
  Viewports, Designsystem-Dokument (z. B. `DESIGN.md`), Prüfbefehle. Erfrage die
  Zielnote, wenn sie fehlt; sie bleibt nur bei dir.
- Lege im Zielrepository `docs/design-review/` an:
  - `decisions.md` aus [assets/decisions.template.md](assets/decisions.template.md)
  - `ledger.json` (Befundregister, anfangs `[]`)
  - `rounds.json` (Notenverlauf, anfangs `[]`)
  - `shots.config.json` nach dem Beispiel in [scripts/shoot.mjs](scripts/shoot.mjs)
- Screenshots unter `.design-review/shots/rNN/` speichern und `.design-review/`
  in `.gitignore` aufnehmen. Kein temporäres Verzeichnis: Register und Bilder
  müssen eine Sitzungsunterbrechung überleben.
- Lege einen **Holdout**-Satz fest (`holdout: true` in der Konfiguration): 3–5
  Ansichten, die im normalen Lauf nie gezeigt werden, etwa eine Zwischenbreite
  (1024 px), ein Leerzustand, ein Fehlerzustand, eine andere Datenlage.
- Erzeuge den Review-Brief einmal aus [assets/review-brief.md](assets/review-brief.md)
  und speichere seinen SHA-256 in `rounds.json`. Rubrik und Wortlaut bleiben für
  den ganzen Lauf eingefroren; pro Runde ändern sich nur Ordner, Register-Auszug
  und Entscheidungen.

## 1. Screenshots aufnehmen

`node scripts/shoot.mjs <config> .design-review/shots/rNN` gegen den lokalen
Dev-Server. Uhrzeit, Daten, Gerätefaktor und ausgeblendete Entwicklerpanels sind
in der Konfiguration fixiert; ohne feste Uhr wandert die Jetzt-Linie und jeder
Vergleich zeigt Scheinänderungen. Fertig, wenn jede Ansicht ein Bild hat und
keines eine Lade- oder Fehlerseite zeigt (Stichprobe ansehen).

## 2. Blind reviewen lassen

Pro Mitglied ein frischer `delegate_task` ohne Elternhistorie, nur lesend, Auftrag:
„Lies `<brief-rNN.md>` und führe ihn genau aus.“ Der Brief enthält:

- Produktkontext, Ordner, Dateilegende, Abzugsrubrik;
- `{OFFENE_BEFUNDE}`: offene und in der Vorrunde bearbeitete Befunde *dieses*
  Mitglieds mit ID, Stelle und Bearbeitungsstatus, ohne frühere Noten;
- `{ENTSCHEIDUNGEN}`: den Inhalt von `decisions.md`.

Nie im Brief: Zielnote, frühere Noten, Rundennummer, Existenz eines Gates, Namen
des anderen Mitglieds oder dessen Befunde. Warte mit `t3_thread_wait`, lies die
Ergebnisse mit `task_status`. Fertig, wenn beide Antworten den JSON-Block der
Rubrik enthalten; fehlt er oder fehlen Screenshots, die Runde wiederholen statt
Noten zu raten.

## 3. Noten und Befunde erfassen

Trage beide Gesamtnoten, Noten je Screenshot und Befunde unverändert in
`rounds.json` und `ledger.json` ein. Neue Befunde erhalten eine ID
(`<Mitglied>-<Runde>-<n>`); Nachprüfungen (`behoben`, `offen`, `verschlechtert`)
aktualisieren bestehende Einträge. Dann `python3 scripts/gate.py --rounds
docs/design-review/rounds.json --ledger docs/design-review/ledger.json --target <Note>`
und dem Ergebnis folgen:

- `pass` → Schritt 7.
- `confirm` → nächste Runde als **Bestätigungsrunde** (frische Instanzen,
  Holdout-Ansichten zusätzlich), ohne Änderungen am Code dazwischen.
- `stagnation` → Schritt 7 mit Stagnationsbericht.
- `continue` → Schritt 4.

## 4. Triage

Ordne **jeden** neuen Befund genau einer Klasse zu und vermerke sie im Register:

- **verifiziert**: am Screenshot oder per Messung im Browser bestätigt → umsetzen.
- **Halluzination**: im Bild nicht vorhanden (z. B. „abgeschnitten“, obwohl
  vollständig) → `abgelehnt` mit Messwert als Beleg.
- **Umkehr**: verlangt das Gegenteil eines früheren Befunds oder einer Entscheidung
  → `abgelehnt`, frühere ID zitieren; bei wiederholter Umkehr einen Eintrag in
  `decisions.md` mit beiden IDs.
- **Geschmack**: kein sichtbarer Fehler, nur eine andere Vorliebe → umsetzen nur,
  wenn beide Mitglieder es unabhängig nennen; sonst `zurückgestellt`.

Fertig, wenn kein neuer Befund ohne Klasse und Begründung ist. Entscheidungen, die
das Produkt verändern (Funktionen, Inhalte, Reihenfolge ganzer Seiten), dem Nutzer
vorlegen statt selbst eintragen.

## 5. Umsetzen

Setze die verifizierten Befunde nach Abzugshöhe um, die größten zuerst, bei
großen Runden über Subagents mit genauem Auftrag (Dateien, Designregeln, Messziel,
Prüfbefehle, was unverändert bleibt). Jede Änderung mit Messwert vorher/nachher
belegen. Danach die Prüfbefehle des Repos (Typen, Lint, Tests) vollständig grün.
Fertig, wenn jeder umgesetzte Befund im Register `umgesetzt` mit Messwert trägt
und kein Prüfbefehl rot ist.

## 6. Dokumentieren und nächste Runde

- Commit pro Runde („Act on round NN of the design review“), Push in den PR-Branch.
- Neue Screenshots aufnehmen (Schritt 1), dann
  `python3 scripts/compare.py .design-review/shots/rPREV .design-review/shots/rNN .design-review/compare/rPREV-rNN`
  und dem Nutzer die aussagekräftigsten Vergleichsbilder (rot markierte Bereiche)
  eingebettet schicken, mit je einem Satz, was sich geändert hat.
- PR-Kommentar nach [assets/pr-round-comment.template.md](assets/pr-round-comment.template.md)
  mit dem Attributions-Callout aus `leaving-pr-comments`: Notenverlauf, Noten je
  Screenshot, abgelehnte Befunde mit Grund, neue Entscheidungen. URL zurücklesen.
- Deployment nur nach ausdrücklicher Freigabe des Nutzers für genau diesen Stand.

Weiter mit Schritt 2.

## 7. Abschluss

Bei `pass`: PR-Kommentar mit Endstand, Bestätigungsrunde und Holdout-Noten; PR
bleibt zur menschlichen Entscheidung offen, kein Merge.

Bei `stagnation`: Lauf anhalten und dem Nutzer berichten: Notenverlauf, Anteil
Umkehrungen/Geschmack/Halluzinationen der letzten Runden, die drei größten offenen
Defekte und eine Empfehlung (Entscheidungen festlegen, Zielnote prüfen, Tests mit
echten Nutzern). Nicht weiterdrehen, nur weil eine Zielnote fehlt.
