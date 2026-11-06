---
name: map-codebase
description: Kartiert ein Repository anhand seines Codes in fachliche Vertical Slices und erstellt oder aktualisiert CODE_MAP.md sowie Markdown-Steckbriefe im betroffenen Repository. Verwenden, wenn Agents einen belegten Wegweiser zu Zuständigkeiten, Einstiegspunkten, Abhängigkeiten und Prüfungen benötigen. Führt keine Refaktorierung durch.
---

# Codebasis in Vertical Slices kartieren

Erstelle einen kompakten Wegweiser, mit dem zukünftige Agents eine Aufgabe dem
richtigen Codebereich zuordnen, ihre Suche beginnen und Auswirkungen prüfen
können. Beschreibe die vorhandene Architektur. Erfinde keine gewünschte Architektur.

## Ergebnis und Umfang

Schreibe die Dokumentation **in das untersuchte Repository**, nicht in das
Skill-Verzeichnis:

- `CODE_MAP.md`: Projektüberblick, Aufgaben-Routing und verlinktes Slice-Verzeichnis.
- `docs/code-map/<slice-id>.md`: ein Steckbrief je eigenständig erklärbarem Bereich.

Nutze vorhandene gleichwertige Dokumentation, statt eine zweite widersprüchliche
Karte anzulegen. Erhalte manuelle Ergänzungen und beachte die Dokumentationssprache
des Repositories; ohne erkennbare Konvention verwende die Sprache des Nutzers.
Ist nur ein Teil des Repositories untersuchbar, dokumentiere Abdeckung und
Auslassungen ausdrücklich. Stelle das Ergebnis dann als Teilkarte dar.

Der Auftrag erlaubt Dokumentationsänderungen. Verändere keine Anwendung,
Abhängigkeiten, Datenbank, CI-Konfiguration oder bestehenden Agent-Anweisungen.
Commit, Push, PR und Veröffentlichung gehören nur bei entsprechendem Nutzerauftrag
zum Umfang. Übernimm keine Geheimnisse, Zugangsdaten oder personenbezogenen
Beispieldaten in die Dokumentation.

## 1. Repository und tatsächliche Abläufe erfassen

Lies die geltenden `AGENTS.md` und vorhandene Architektur- und Domänendokumente.
Prüfe den Arbeitsbaum und erhalte bestehende Änderungen. Ermittle anschließend:

- Anwendungen, Pakete und ausführbare Einstiegspunkte;
- Routen, Commands, Events und Hintergrundaufgaben;
- fachliche Regeln, Datenzugriffe, externe Schnittstellen und Tests;
- Build- und Prüfkommandos aus Manifesten, Konfiguration und CI.

Nutze zunächst `rg --files` und gezielte Symbol- und Aufrufersuchen. Lies bei
unklaren Grenzen repräsentative Abläufe vom Eingang über Geschäftsregeln und
Seiteneffekte bis zu den zugehörigen Tests. Ordnernamen allein belegen keine
fachliche Zuständigkeit. Generierte Dateien, vendorte Bibliotheken und Build-Ausgaben
sind gewöhnlich keine eigenen Slices; nenne bei Bedarf ihre Quellen und Generatoren.

## 2. Verantwortlichkeiten schneiden

Ein **fachlicher Vertical Slice** beschreibt eine zusammenhängende Fähigkeit
oder einen Anwendungsfall, beispielsweise „Buchung erstellen und stornieren“.
Ordne ihm die tatsächlich beteiligten Oberflächen, Schnittstellen, Geschäftsregeln,
Datenzugriffe und Tests zu. Ein Slice darf mehrere Ordner und Pakete durchqueren.
Ein Backend oder eine Bibliothek benötigt keine künstliche UI-Schicht.

Unterscheide im Verzeichnis:

| Art | Bedeutung |
| --- | --- |
| Fachlicher Slice | Fähigkeit oder Anwendungsfall mit erkennbarem Verhalten |
| Gemeinsamer Mechanismus | Etwa Identität, Berechtigungen, Benachrichtigungen oder Zeitbehandlung |
| Technische Grundlage | Etwa Datenbankzugriff, Konfiguration oder Deployment |

Bezeichne gemeinsame Mechanismen und technische Grundlagen nicht pauschal als
fachliche Vertical Slices. Auch sie brauchen auffindbare Zuständigkeiten und Grenzen.

Wähle stabile, kurze IDs wie `booking`, `identity` oder `database-access`.
Häufig genügen zunächst 6–12 Hauptbereiche; erzwinge diese Zahl nicht. Teile einen
Bereich weiter auf, wenn darin unabhängig erklärbare Anwendungsfälle verborgen
bleiben. Fasse Bereiche zusammen, wenn ihre Abgrenzung keinen Suchaufwand spart.
Erzeuge keine allgemeine Restkategorie wie „Sonstiges“ für ungeklärten Code.

Ein technischer Bereich wie `controllers`, `frontend` oder `services` ist allein
noch kein fachlicher Slice. In einem Monorepo sind Paketgrenzen zunächst
Orientierungspunkte, keine automatisch richtigen fachlichen Grenzen.

Ordne jedem relevanten Einstiegspunkt eine primäre Zuständigkeit zu.
Dokumentiere gemeinsam verwendeten Code zentral und verlinke ihn aus den
betroffenen Slices. Benenne bestehende Kopplung und unklare Grenzen, ohne sie
durch eine scheinbar saubere Aufteilung zu verdecken.

## 3. Karte und Steckbriefe schreiben

Verwende [assets/CODE_MAP.template.md](assets/CODE_MAP.template.md) für die
Hauptkarte und [assets/slice.template.md](assets/slice.template.md) für die
Steckbriefe. Passe sie an das Repository an; entferne nicht zutreffende Abschnitte.

Die Hauptkarte muss einen Agenten schnell von einer **Aufgabe oder einem Symptom**
zum primären Slice und den zusätzlich zu prüfenden Bereichen führen. Beschreibe
kurz den tatsächlichen Laufzeitaufbau und nenne den untersuchten Git-Stand,
das Datum und relevante uncommittete Änderungen, soweit verfügbar.

Jeder Steckbrief braucht konkrete Antworten auf diese Fragen:

- Wofür ist der Bereich zuständig, und wofür ausdrücklich ein anderer Bereich?
- An welchen vorhandenen Dateien und Symbolen beginnt die Suche?
- Wie verläuft ein repräsentativer Ablauf einschließlich wichtiger Seiteneffekte?
- Welche Daten und Schnittstellen liest, verändert oder bedient der Bereich?
- Was ruft ihn auf, und welche Bereiche verwendet er selbst?
- Welches bestehende Verhalten muss eine spätere Änderung erhalten?
- Welche Tests und Prüfkommandos sind für Änderungen relevant?
- Was wurde noch nicht untersucht oder ist im Code nicht eindeutig belegt?

Verlinke konkrete Dateien relativ zum erzeugten Dokument und ergänze stabile
Symbolnamen. Vermeide vollständige Dateiinventare und leicht veraltende
Zeilennummern. Belege Verträge und Verhaltensregeln durch Code oder Tests;
kennzeichne reine Dokumentationsaussagen und Schlussfolgerungen entsprechend.
Eine vermutete Regel ist keine bestätigte Invariante.

Unterscheide bei Prüfungen zwischen **vorhanden**, **als Kommando ermittelt** und
**in diesem Durchlauf erfolgreich ausgeführt**. Installiere für eine Code-Karte
keine Abhängigkeiten und starte keine vollständige Testsuite ohne sachlichen
Grund. Ein vorhandener Test beweist weder seinen aktuellen Erfolg noch eine
Prüfung im Browser, im Deployment oder in Produktion.

## 4. Ergebnis gegen den Code prüfen

- Prüfe alle genannten Pfade, Dokumentlinks und Symbole auf Existenz.
- Prüfe die Zuordnung wichtiger Einstiegspunkte und benenne Abdeckungslücken.
- Verfolge für jeden fachlichen Slice mindestens einen repräsentativen Ablauf;
  bei mehreren unabhängigen Abläufen ergänze diese oder verfeinere den Zuschnitt.
- Prüfe ermittelte Prüfkommandos und ihre notwendigen Arbeitsverzeichnisse.
- Probiere typische Aufgaben an der Routing-Tabelle aus: Ist der Suchbeginn klar,
  und werden die wichtigsten Nachbarbereiche erreicht?
- Prüfe den abschließenden Diff: Er muss sich auf die beauftragte Dokumentation
  beschränken und vorhandene Änderungen erhalten.

Beende die Arbeit mit Links auf die erzeugte Hauptkarte und die Steckbriefe sowie
einer kurzen Angabe zu Abdeckung, durchgeführten Prüfungen und offenen Grenzen.

## Verwendung und Pflege durch spätere Agents

Die Karte ist eine Suchhilfe. Vor einer Änderung müssen Agents aktuelle Aufrufer,
Tests und Schnittstellen prüfen; eine Slice-Grenze begrenzt keine tatsächlichen
Auswirkungen. Für einen Verbesserungsauftrag sollten primärer Slice, betroffene
Nachbarbereiche, belegtes Problem und passende Prüfungen konkret benannt werden.

Aktualisiere bei späteren Kartierungsaufträgen die betroffenen Einträge anhand
des aktuellen Codes. Erhalte stabile IDs und Links, soweit die Verantwortung
gleich bleibt. Ändert sich eine Grenze, aktualisiere auch Routing und Querverweise.
Ein Git-Stand oder Datum macht eine Karte überprüfbar, aber nicht automatisch aktuell.
