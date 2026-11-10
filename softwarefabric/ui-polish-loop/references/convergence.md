# Konvergenzregeln

Warum es diese Regeln gibt: In einem früheren Lauf blieb die Note über acht Runden
zwischen 8,3 und 8,7. Ursachen waren ein unkalibrierter Maßstab („es gibt immer
etwas“), Reviewer, die eigene Wünsche der Vorrunde umkehrten, halluzinierte
Defekte und ein Worker, der jeden Vorschlag umsetzte und dabei neue Fehler
einbaute. Jede Regel unten schließt eine dieser Lücken. Die Gegenrichtung ist
genauso wichtig: Die Note darf nicht steigen, nur weil Reviewer weniger suchen
oder der Worker Kritik per Entscheidung stilllegt.

## Abzugsrubrik

Die Note ist eine **Rechnung**, kein Eindruck: Start 10,0, minus der Abzüge aller
Befunde. Jeder Abzug hängt an genau einem Befund mit Datei und Stelle.

| Klasse | Abzug | Beobachtbares Kriterium |
| --- | ---: | --- |
| `blocker` | 1,0 | Information falsch, abgeschnitten oder unlesbar; Layout kaputt; Bedienung unmöglich |
| `defekt` | 0,3 | sichtbarer Fehler: dasselbe Element uneinheitlich, Fehlausrichtung, wichtige Kürzung, zu wenig Kontrast, doppelte oder widersprüchliche Angabe |
| `politur` | 0,1 | kleine Verbesserung mit klar benennbarem Nutzen |
| `geschmack` | 0,0 | andere Vorliebe ohne sichtbaren Fehler |

Die Rubrik gilt pro Screenshot und für die Gesamtnote (Summe aller verschiedenen
Befunde; derselbe Fehler auf mehreren Screens zählt einmal). Reviewer nennen
`geschmack` ausdrücklich als solchen, statt ihn als Abzug zu tarnen. So steigt die
Note genau dann, wenn Defekte verschwinden, und eine stabile Restnote bedeutet
offene Defekte, die sich benennen lassen.

Die Rubrik verrät keine Zielnote. Sie bleibt für den ganzen Lauf gleich
(Brief-Hash in `rounds.json`); eine Änderung mitten im Lauf macht frühere Noten
unvergleichbar und startet die Zählung neu.

## Befundregister (`ledger.json`)

```json
{"id": "sol-07-3", "member": "sol", "round": 7, "screen": "m-k01-entdecken",
 "location": "Betriebskarte, Preiszeile", "class": "defekt",
 "summary": "Leistung zu „Herrenhaar…“ gekürzt",
 "status": "offen|umgesetzt|behoben|verschlechtert|abgelehnt|zurückgestellt",
 "triage": "verifiziert|halluzination|umkehr|geschmack",
 "evidence": "Messung/Begründung", "reverses": "opus-05-2"}
```

- Jedes Mitglied sieht in der nächsten Runde nur **seine eigenen** offenen und
  zuletzt bearbeiteten Befunde und prüft sie nach (`behoben`, `offen`,
  `verschlechtert`). Das verankert die Prüfung an konkreten Stellen statt an einer
  neuen Gesamtsicht, ohne frühere Noten zu zeigen.
- Abgelehnte Befunde stehen mit Grund im Auszug. Ein Mitglied kann widersprechen,
  muss dann aber einen neuen sichtbaren Beleg nennen.
- `verschlechtert` hat Vorrang: zuerst die Regression beheben, bevor Neues kommt.

## Entscheidungsregister (`decisions.md`)

Festgelegte Gestaltungsentscheidungen, die Reviewer kennen und nur mit einem
konkreten, im Screenshot sichtbaren Fehler anfechten dürfen. Einträge entstehen
nur auf zwei Wegen:

1. Der Nutzer hat entschieden.
2. Ein Befund kehrt einen früheren Befund um (beide IDs im Eintrag) und die
   Umkehr wurde abgelehnt.

Der Worker trägt keine Entscheidung ein, um unbequeme Kritik ohne Umkehr
stillzulegen. Jeder neue Eintrag erscheint im PR-Kommentar der Runde, damit der
Nutzer ihn sehen und kippen kann.

## Gate (`scripts/gate.py`)

`rounds.json` ist eine Liste von Runden:

```json
{"round": 7, "commit": "abc1234", "brief_sha256": "…", "confirmation": false,
 "holdout": false, "scores": {"sol": 8.5, "opus": 8.7}}
```

- **`pass`**: In den beiden letzten Runden liegen beide Mitglieder auf oder über
  der Zielnote; die letzte ist eine Bestätigungsrunde mit Holdout und ohne
  Codeänderung seit der vorletzten (gleicher Commit); kein Befund mit Klasse
  `blocker` oder `defekt` ist `offen` oder `verschlechtert`.
- **`confirm`**: Die letzte Runde liegt bei beiden auf oder über der Zielnote,
  aber die Bestätigung fehlt. Ebenso, wenn ein Mitglied in einer Runde um mehr als
  0,5 steigt: Ein Sprung ohne entsprechend geschlossene Defekte ist Rauschen, bis
  eine zweite frische Runde ihn bestätigt.
- **`stagnation`**: Drei Runden in Folge steigt das Minimum beider Noten nicht um
  mindestens 0,1 über das bisherige Maximum dieses Minimums.
- **`continue`**: alles andere.

Fällt eine Bestätigungsrunde unter die Zielnote, gilt sie als normale Runde: Ihre
Befunde werden triagiert und umgesetzt, das Gate verlangt danach eine neue
Bestätigung.

## Arbeitsdisziplin des Workers

- Pro Runde verifizierte Befunde umsetzen, nicht die Wunschliste. Viele
  gleichzeitige Änderungen erhöhen das Regressionsrisiko; im Zweifel die Hälfte
  mit dem größten Abzug.
- Messen statt schätzen: Breiten, Abstände, Kontraste im Browser ermitteln.
  Fremdangaben von Reviewern („≈ 140 px“) sind Hinweise, keine Messwerte.
- Kontrastziele und Farbregeln als Tests festhalten, damit eine spätere Runde sie
  nicht unbemerkt bricht.
- Reviewer-Vorschläge mit konkreten Hexwerten gegen die eigenen Kontrastregeln
  prüfen; sie verfehlen sie oft.
