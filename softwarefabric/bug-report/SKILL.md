---
name: bug-report
description: Prüft pro Aufruf genau einen fälligen Vertical Slice aus der Code-Map auf funktionale Bugs und erstellt einen bewerteten Markdown-Report mit Evidenz und Lösungsvorschlägen. Markiert nur vollständig abgeschlossene Prüfungen und rotiert danach zum ältesten Slice. Implementiert keine Fixes und erstellt keine Issues.
---

# Bugreport für einen Vertical Slice

Nutze den vollständigen [gemeinsamen Report-Ablauf](../shared/review-workflow.md)
und dessen Helfer mit `--mode bug-report`. Auswahl, Reservierung, Abdeckung,
Reportformat und Abschlussmarkierung sind mit `security-report` identisch.
Das gesamte `softwarefabric`-Verzeichnis muss mit seinen relativen Pfaden verfügbar sein.

## Suchperspektive: funktionale Fehler

Untersuche das tatsächlich implementierte Verhalten des gewählten Slices:

- falsche Geschäftsregeln, Berechnungen oder Zustandsübergänge;
- unbehandelte Eingaben, leere Ergebnisse, Grenzwerte und Fehlerpfade;
- verlorene oder widersprüchliche Daten und unvollständige Transaktionen;
- doppelte Seiteneffekte bei Wiederholung, Rennen oder fehlende Idempotenz;
- Datums-, Zeitzonen-, Serialisierungs- und Schnittstellenfehler;
- Abweichungen zwischen Oberfläche, API und nachweisbar geltenden Verträgen.

Wähle daraus die zum Slice passenden Fragen. Diese Liste ist kein Auftrag zu einer
zusätzlichen Gesamtprüfung. Ein langsamer Pfad ist nur dann ein Bugbefund, wenn
seine konkrete Fehlwirkung oder eine verletzte Anforderung belegt ist. Stilfragen,
Geschmacksurteile und hypothetische Refaktorierungswünsche sind keine Bugs.

## Belege und Bewertung

Belege pro Befund einen konkreten Auslöser, das erwartete Verhalten, das tatsächliche
Ergebnis und die Ursache. Suche nach Absicherungen in Aufrufern, Validierung und
Transaktionsgrenzen. Ein zufällig fehlgeschlagener Test oder ein nicht gestarteter
Worker ist allein kein Produktfehler.

Bewerte nach Auswirkung, Reichweite, Häufigkeit und Wiederherstellbarkeit. Ein
reproduzierbarer Datenverlust kann schwerer wiegen als ein häufiger Darstellungsfehler.
Trenne fachliche Unsicherheit von technischer Evidenz; fehlende Produktentscheidungen
gehören als offene Fragen in den Report.

Beschreibe einen konkreten Lösungsvorschlag und einen Regressionstest, der das
Fehlverhalten vor dem Fix sichtbar macht. Bei einer Sicherheitswirkung grenze den
Befund entsprechend ab und verweise auf die nötige Securityprüfung; starte dadurch
keinen weiteren Slice oder Securitylauf.

Der Erfolg dieses Skills ist ein belastbarer Report samt korrekter Bearbeitungsmarkierung,
nicht eine bestimmte Zahl von Befunden. Unabhängige Verifikation und Fixes sind spätere Stufen.
