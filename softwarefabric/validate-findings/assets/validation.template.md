# Validierung: {Quellreport}

- Zielrepository: {owner/repo}
- Quellreport: {Pfad, Lauf-ID und SHA-256 des unveränderten Reports}
- Report-Commit: {vollständige SHA}
- Validierter aktueller Commit: {vollständige SHA}
- Status: {completed / partial / publication_blocked}

## Übersicht

| Befund-ID | Entscheidung | Schwere /10 | UX Problem /10 | UX Änderung /10 | Mensch erforderlich | Issue / Blocker |
| --- | --- | --- | --- | --- | --- | --- |
| {ID} | {confirmed / rejected / inconclusive / obsolete / duplicate} | {Wert oder nicht belastbar} | {Wert oder unklar} | {Wert oder unklar} | {ja/nein} | {URL oder Grund} |

## {Befund-ID}: {Titel}

### Unabhängige Prüfung

{Aktueller Codepfad, Erwartung/Sicherheitsgrenze, tatsächliches Verhalten und
Ursache. Gegenargumente und deren Ergebnis. Bei Zurückweisung konkrete Widerlegung;
bei veraltetem Befund Fix und Gegenprüfung belegen. Keine automatische Übernahme
der Reportbewertung und keine erfundene unabhängige Bestätigung.}

### Evidenz und Grenzen

{Pfade, Symbole, SHA-bezogene Quellen, sichere Reproduktion, tatsächlich ausgeführte
Tests mit Ergebnis. Fehlende Evidenz und nicht ausgeführte Prüfungen getrennt.}

### Bewertung

{Schwere, Aussage-Sicherheit und beide UX-Werte jeweils begründen. Auswirkungen
auf Nutzerabläufe, Berechtigungen, Kompatibilität und Migration berücksichtigen.}

### Entscheidung und Übergabe

{Valide, widerlegt, unklar, behoben oder bereits erfasst? Lösung, Alternative,
Regressionstest und Akzeptanzkriterien. Menschliche Entscheidung konkret formulieren.
Issue-URL nach Rücklesen oder Publikationsblocker nennen.}

## Fortschrittsnachweis

{Pro Befund Report-Hash, geprüfte SHA, Entscheidung, Datensatz-/Plan-Hash,
Publikationsstatus und Issue-URL festhalten. Bei Teilstand unbearbeitete Befunde
explizit aufführen. Erfolgreiche Issues bei Wiederholung nicht nochmals anlegen.}
