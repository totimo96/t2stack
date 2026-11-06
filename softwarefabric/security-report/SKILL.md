---
name: security-report
description: Prüft pro Aufruf genau einen fälligen Vertical Slice aus der Code-Map auf Cyber-Sicherheitslücken und erstellt einen bewerteten Markdown-Report mit Evidenz und Lösungsvorschlägen. Markiert nur vollständig abgeschlossene Prüfungen und rotiert danach zum ältesten Slice. Implementiert keine Fixes und erstellt keine Issues.
---

# Securityreport für einen Vertical Slice

Nutze den vollständigen [gemeinsamen Report-Ablauf](../shared/review-workflow.md)
und dessen Helfer mit `--mode security-report`. Auswahl, Reservierung, Abdeckung,
Reportformat und Abschlussmarkierung sind mit `bug-report` identisch.
Das gesamte `softwarefabric`-Verzeichnis muss mit seinen relativen Pfaden verfügbar sein.

## Suchperspektive: Sicherheitslücken

Ermittle für den gewählten Slice relevante Akteure, nicht vertrauenswürdige Eingaben,
geschützte Daten, privilegierte Operationen und tatsächliche Vertrauensgrenzen.
Lies vorhandene `SECURITY.md` und Sicherheitsverträge als Kontext. Prüfe passend zum Slice:

- fehlende Authentifizierung, Autorisierung oder Mandantentrennung;
- unkontrollierte Datenflüsse zu Datenbank, Shell, Dateisystem, Templates oder URLs;
- Datenoffenlegung, unsichere Sitzungen, Tokens und Geheimnisbehandlung;
- Umgehungen von Integritätsprüfungen, Validierung oder Geschäftsgrenzen;
- auslösbare Ressourcenerschöpfung und sicherheitsrelevante Nebenläufigkeit.

Diese Fragen erweitern den Auftrag nicht auf das ganze Repository oder externe Ziele.
Eine Abhängigkeit oder ein riskantes API allein ist noch keine nachgewiesene Lücke.
Bei konkreten Versions- oder Advisory-Aussagen prüfe die maßgebliche Quelle, wenn
Netzzugriff erlaubt ist; leite aus einer Paketmeldung keine Erreichbarkeit oder
Ausnutzbarkeit ohne Untersuchung ab.

## Belege und Bewertung

Dokumentiere pro Befund den Akteur und seine tatsächlichen Rechte, Voraussetzungen,
den erreichbaren Eingabepunkt, den Pfad bis zur sicherheitsrelevanten Operation,
die fehlende Schutzmaßnahme und die konkrete Verletzung einer Sicherheitsgrenze.
Prüfe vorgeschaltete Kontrollen, Kontext, Sanitizer und Annahmen als Gegenargumente.

Ein vollständiger statischer Nachweis kann genügen; eine nicht ausgeführte lokale
Reproduktion muss als solche erkennbar sein. Validiere nur in autorisierten lokalen
Testumgebungen mit synthetischen Daten. Keine produktiven Exploits, externen Scans,
Zugriffserweiterungen oder Veröffentlichung sensibler Details. Geheimnisse gehören
auch nicht in Reproduktionsausgaben oder Reports.

Bewerte Auswirkung und realistische Ausnutzbarkeit einschließlich benötigter Rechte,
Erreichbarkeit und Reichweite. Trenne Schweregrad von Aussage-Sicherheit; unbelegte
Angriffsszenarien gehören in den Kandidatenabschnitt. Keine erfundenen CVEs oder
CVSS-Werte und keine pauschale Sicherheitsfreigabe aus einem befundlosen Durchlauf.

Beschreibe einen Lösungsvorschlag an der wirksamen Vertrauensgrenze und einen
Regressionstest, der den unzulässigen Zugriff oder Datenfluss vor dem Fix zeigt.
Die spätere unabhängige Verifikation entscheidet über die weitere Bearbeitung;
dieser Skill startet weder Issue-Erstellung noch Fixes oder zusätzliche Scanläufe.
