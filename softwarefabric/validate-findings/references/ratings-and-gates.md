# Bewertung und menschliche Umsetzungsgates

## Drei voneinander unabhängige Werte

Alle Werte liegen zwischen **0 und 10**, wobei größere Werte mehr Auswirkung
bedeuten. Das ist keine Qualitätsnote, bei der 10 „gut“ bedeutet. Halbe Werte sind
möglich. Eine konkrete Begründung ist wichtiger als scheinbare Dezimalpräzision.

### Schwere des bestehenden Befunds

| Wert | Bedeutung |
| --- | --- |
| 0 | Kein belastbarer Fehler oder keine relevante Auswirkung; kein bestätigtes Issue |
| >0–3 | Lokal begrenzt, geringe Auswirkung, gut umgehbar oder wiederherstellbar |
| >3–6 | Relevanter Funktionsausfall oder begrenzte Integritäts-/Sicherheitswirkung |
| >6–8 | Hohe Reichweite, erheblicher Ausfall, Datenverlust oder erhebliche Sicherheitsverletzung |
| >8–10 | Kritische, breit wirksame oder schwer wiederherstellbare Auswirkung |

Begründe mit Erreichbarkeit, Voraussetzungen, betroffenen Nutzern/Daten,
Wahrscheinlichkeit, Reichweite und Wiederherstellbarkeit. Security zusätzlich
nach realistisch verfügbaren Angreiferrechten und tatsächlich verletzter Grenze
bewerten. Nicht erreichte Schwellen sind keine Begründung, einen validen Befund
zu verschweigen. Ein hoher Wert erzeugt keine automatische Freigabe.

Aussage-Sicherheit separat als hoch oder mittel begründen. Reicht die Evidenz
nicht aus, lautet die Entscheidung `inconclusive`; eine Zahl macht die Aussage
nicht belastbar. Dies ist keine CVSS-Berechnung und kein Ersatz dafür.

### UX-Auswirkung des Problems und der vorgeschlagenen Änderung

Vergib jeweils einen Wert und eine eigene Begründung:

- `ux_existing_score`: Wie beeinträchtigt das bestehende Problem die Nutzer?
- `ux_change_score`: Wie stark verändert oder gefährdet der vorgeschlagene Fix
  Abläufe, Erwartungen, Zugang, Bedienbarkeit oder Barrierefreiheit?

| Wert | Orientierung |
| --- | --- |
| 0–3 | Gering, lokal oder weitgehend transparent; vertraute Abläufe bleiben erhalten |
| >3 bis unter 7 | Spürbare Änderung oder Reibung in einzelnen Abläufen; gut begrenzbar |
| 7–10 | Hohe Auswirkung auf wichtige/breite Abläufe, Zugang, Daten, Kompatibilität oder Bedienbarkeit |

Prüfe etwa zusätzlichen Login, neue Pflichtfelder, geänderte Berechtigungen,
entfallende Funktionen, Datenmigrationen, bestehende Integrationen und
Barrierefreiheit. Ein technisch kleiner Patch kann eine hohe UX-Auswirkung haben.
Nicht feststellbare UX-Auswirkungen werden mit `null` und einer konkreten offenen
Frage erfasst; niemals ersatzweise 0 vergeben.

## Verbindlicher Standard-Gate

**Ab 7/10 in einem der beiden UX-Werte ist menschliche Freigabe vor Umsetzung
verpflichtend. Auch `null` in einem UX-Wert verlangt diese Freigabe.**
Dieser konservative Standard kann nur durch eine ausdrückliche Nutzervorgabe
geändert werden; der Skill senkt ihn nicht selbstständig.

| Fall eines bestätigten Befunds | Umsetzungsgate und Labels |
| --- | --- |
| Beide UX-Werte bekannt und kleiner als 7 | `softwarefabric:validated`, Art, `softwarefabric:ready-for-implementation` |
| Ein UX-Wert mindestens 7 oder unbekannt | `softwarefabric:validated`, Art, `softwarefabric:needs-human-approval`, `softwarefabric:blocked` |

Art ist `softwarefabric:bug` beziehungsweise `softwarefabric:security`.
`ready-for-implementation` und `blocked` dürfen nie gleichzeitig gesetzt sein.
Das Gate erscheint zusätzlich maschinenlesbar im Issue-Body. Widerspruch zwischen
Body und Labels bedeutet für nachfolgende Agents **blockiert**.

Bei zusätzlichen Blockern, etwa fehlender privater Übergabe sicherheitskritischer
Details, darf ebenfalls kein `ready` gesetzt werden. Die UX-Entscheidung allein
ist keine Aussage, dass andere Anforderungen automatisch erfüllt sind.

## Was der Mensch freigibt

Ein freigabepflichtiges Issue nennt:

- betroffene Nutzerabläufe und konkrete Vorher-/Nachher-Wirkung;
- die vorgeschlagene Lösung und eine weniger eingreifende Alternative;
- offene Produkt-/Berechtigungsentscheidungen, Migrations- und Rückfallbedarf;
- den geprüften Commit und den Hash des konkreten Lösungsplans;
- die ausdrückliche Frage, ob diese Umsetzung akzeptiert wird.

Die Validierung erzeugt keine menschliche Zustimmung. Eine spätere Freigabe
muss vom autorisierten Menschen über eine nachvollziehbare Freigabeinteraktion
oder einen dafür vorgesehenen menschlichen Review-Kanal stammen. Identität,
Zeitpunkt, Beleg und freigegebener Plan/Stand müssen dokumentiert sein.
Ein GitHub-Kommentar unter einem Benutzerkonto allein beweist nicht, dass ein
Mensch zugestimmt hat: Agents können dieselben Zugangsdaten verwenden.

Der spätere Umsetzungsskill muss Issue und Gate live lesen, echte Freigabe und
ihren Umfang verifizieren und die aktuelle Anwendbarkeit prüfen. Kein automatisches
Entfernen des Freigabe-Labels, kein Selbstgenehmigen, keine Freigabe aus Stille,
Emoji-Reaktion, Schweregrad oder einer alten Zustimmung ableiten. Ein veränderter
Lösungsplan, höhere UX-Auswirkung oder geänderte relevante Voraussetzungen
verlangen eine erneute menschliche Entscheidung. Rein sachfremde Commits machen
eine Freigabe nicht automatisch ungültig, müssen aber abgegrenzt werden.

`ready-for-implementation` bei niedriger UX-Auswirkung ersetzt weder Tests noch
Code-Review und ist keine Merge- oder Deployment-Freigabe.
