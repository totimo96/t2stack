# {mode}: {slice_id}

{report_metadata}

- Lauf: `{run_id}`
- Quellstand: `{head}`
- Begonnen: {started_at}
- Slice-Steckbrief: `{document}`
- Unabhängige Verifikation: ausstehend

## Zusammenfassung

{Anzahl belegter Befunde nach Schweregrad. Bei null Befunden den begrenzten
Untersuchungsumfang ausdrücklich nennen.}

## Umfang und Abdeckung

{Untersuchte Abläufe, konkrete Pfade/Symbole, Datenflüsse und hinzugezogene
Nachbarbereiche mit Grund. Offene Abläufe und Grenzen getrennt benennen.}

## Belegte Befunde

{Für jeden belegten Befund den folgenden Abschnitt ausfüllen. Bei null Befunden
keine leeren Befundabschnitte anlegen.}

### {stabile Befund-ID} — {konkreter Titel}

- Bewertung: {critical / high / medium / low mit Begründung}
- Aussage-Sicherheit: {hoch / mittel mit Begründung; ungestützte Vermutung gehört zu Kandidaten}
- Nachweisart: {Codepfad / lokale Reproduktion / Test; tatsächlich beobachtetes Ergebnis}
- Vergleich zu früheren Reports: {neu / weiterhin vorhanden / verändert und Link}
- Stelle: {repo-relativer Pfad, Symbol, bei Bedarf SHA-bezogene Zeilen}

**Erwartetes Verhalten oder Sicherheitsgrenze:** {Beleg der Regel}

**Tatsächlicher Fehler und Ursache:** {Konkreter Codepfad vom Auslöser bis zur Wirkung}

**Voraussetzungen und Auswirkung:** {Wer oder was ist unter welchen Bedingungen betroffen?}

**Reproduktion und Gegenprüfung:** {Sichere Schritte oder vollständige statische
Beweiskette, Ergebnis, geprüfte Gegenargumente; ausgeführte und nicht ausgeführte
Prüfungen unterscheiden. Keine produktiven Daten oder Geheimnisse einfügen.}

**Lösungsvorschlag:** {Ansatz, betroffene Stellen und zu erhaltende Verträge;
keine bereits erfolgte Implementierung behaupten.}

**Regressionstest:** {Konkreter Auslöser und erwartete Assertion}

## Ungeklärte Kandidaten

{Beobachtung, fehlende Evidenz, nächster sinnvoller Prüfschritt. Diese Kandidaten
sind keine bestätigten Befunde und zählen nicht zu finding_count.}

## Frühere Befunde

{Referenzen auf weiterhin bestehende oder aktuell nicht nachweisbare Ursachen;
keine alten Befunde ohne erneute Prüfung als behoben markieren.}

## Prüfungen und Grenzen

| Prüfung | Arbeitsverzeichnis und Kommando | Ergebnis / nicht ausgeführter Teil |
| --- | --- | --- |
| {Prüfung} | {tatsächlich verwendetes Kommando} | {Beobachtung und Grenze} |

## Übergabe an die Verifikation

{Welche Befunde sind unabhängig nachzuprüfen? Welche Evidenz fehlt noch?
Keine Issue-Erstellung, Codeänderung oder Freigabe durch diesen Report.}
