# Code Map

## Zweck und Abdeckung

Diese Karte führt von Aufgaben und Symptomen zu relevanten Codestellen.
Vor einer Änderung sind die aktuellen Aufrufer und Schnittstellen zu prüfen.

- Untersucht am: {Datum}
- Git-Stand: {Commit oder Angabe, dass kein Git-Stand vorliegt}
- Arbeitsbaum: {für die Karte relevante Änderungen, falls vorhanden}
- Abgedeckt: {untersuchte Anwendungen, Pakete und Pfade}
- Noch nicht abgedeckt: {Bereiche und Grund oder keine bekannten Lücken}

## Programm und Laufzeitaufbau

{Kurze Beschreibung der Aufgaben des Programms, ausführbaren Komponenten,
wichtigsten Eingänge und ihres Zusammenspiels. Mit relativen Code-Links belegen.}

## Wo anfangen?

| Aufgabe oder Symptom | Primärer Bereich | Zusätzlich prüfen | Erster Einstieg |
| --- | --- | --- | --- |
| {konkreter Fall} | [{Slice-ID}](docs/code-map/{slice-id}.md) | {verlinkte Nachbarbereiche} | {Code-Link und Symbol} |

## Bereiche

| ID | Art | Verantwortung | Steckbrief |
| --- | --- | --- | --- |
| {slice-id} | {fachlich / gemeinsam / technisch} | {knappe Zuständigkeit} | [Details](docs/code-map/{slice-id}.md) |

## Bereichsübergreifende Zusammenhänge

{Wichtige Abhängigkeiten und geteilte Verträge mit Links zu ihren maßgeblichen
Steckbriefen. Bei Bedarf kurze Ablaufdarstellung; keine Verdopplung der Details.}

## Prüfungen und offene Grenzen

{Welche Kartierungsprüfungen wurden durchgeführt? Welche Teile sind ungeklärt?
Ausgeführte Prüfungen klar von vorhandenen oder empfohlenen Tests unterscheiden.}
