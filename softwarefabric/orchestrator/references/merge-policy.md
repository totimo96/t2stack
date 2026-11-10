# Mergerisiko und Systemauswirkungen

Diese Regel gilt für den **Orchestrator**, einschließlich seiner delegierten
Umsetzungen. Der eigenständig aufgerufene `implement-loop` bleibt standardmäßig
bei manueller Merge-Entscheidung. Die Ausführung des Orchestrators autorisiert
hiermit den direkten Merge qualifizierter eigener Pipeline-PRs im Zielrepository.
Ein ausdrückliches Merge-Verbot im konkreten Lauf hat Vorrang. Deployment ist
weiterhin nicht umfasst; kein Auto-Merge für einen späteren ungeprüften Stand.

## Unabhängige Bewertungen

Beide Council-Mitglieder bewerten zusätzlich zur Änderungsqualität zwei getrennte
Werte von **1 bis 10**. Hohe Werte bedeuten hier hohe Risiken beziehungsweise
Auswirkungen, während hohe Qualitätsnoten gute Änderungen bedeuten.

| Wert | Leitfrage | Orientierung |
| --- | --- | --- |
| Mergerisiko | Wie wahrscheinlich sind Regressionen, Integrationsfehler oder betriebliche Probleme beim Einspielen? | 1–3: lokal, gut belegt und leicht rückgängig; 4–6: mehrere geprüfte Verträge/Abhängigkeiten; 7–8: erhebliche Unsicherheit, Migration oder schwieriger Rollback; 9–10: breitreichend, kritisch oder kaum reversibel. |
| Systemauswirkungen | Wie groß ist der betroffene fachliche und technische Wirkungsbereich, auch wenn die Änderung korrekt ist? | 1–3: eng begrenzter Pfad; 4–6: mehrere Bereiche, begrenzter Nutzerkreis; 7–8: zentrale Abläufe, Datenmodelle oder viele Nutzer; 9–10: systemweite Kernfunktionen, Isolation, Authentisierung oder kritischer Datenbestand. |

Die Beispiele sind Anker, keine Dateipfad-Heuristik. Begründe den tatsächlichen
Wirkungsbereich anhand von Aufrufern, Datenflüssen, Schnittstellen, Zustands- und
Schemaänderungen, Berechtigungen, Kompatibilität, Tests, Ausrollung und Rollback.
Berücksichtige Wahrscheinlichkeit beim Risiko, Reichweite und Konsequenz bei der
Auswirkung. Ein nützlicher Fix kann große Systemauswirkungen haben. Keine Note
allein aus Diff-Größe, bestandener CI oder der ursprünglichen Befundschwere ableiten.
Unsicherheit und nicht geprüfte Bereiche offen nennen; unbekannt bleibt `null`.

Pro Bewertung liefert jedes Mitglied `merge_risk_score`, `merge_risk_reason`,
`system_impact_score`, `system_impact_reason` im vorhandenen Review-Datensatz.
Beide Bewertungen gehören in seinen PR-Kommentar. Die Verifizierung des
veröffentlichten Inhalts wird als `risk_comment_verified` im Review festgehalten. Sie beziehen sich auf dieselbe
aktuelle Runde, Base-/Head-SHA, Diff-Hash und Rollenbesetzung wie das Qualitätsreview.
Keine gesonderte Review-Runde nur zum Erzielen niedrigerer Zahlen. Bei vorhandenen
alten Reviews ohne diese Werte ergänzende unabhängige Bewertungen desselben Stands
anfordern; alte fehlende Werte nicht selbst rekonstruieren.

## Entscheidung und PR-Markierung

Der Controller übernimmt pro Kategorie den **höheren** der beiden Werte, ohne
Mittelung oder Abrundung:

- **Beide Werte < 7:** `softwarefabric:agent-merge-allowed`, sofern sämtliche
  bisherigen Qualitäts-, Issue-/UX-, CI- und Repository-Gates bestehen.
- **Mindestens ein Wert ≥ 7:** `softwarefabric:needs-human-merge-review`; der
  Agent mergt nicht. Das gilt ausdrücklich auch für genau **7/10**.
- **Fehlend, unklar, veraltet oder ein anderes Gate gesperrt:**
  `softwarefabric:merge-blocked`; bei hoher/ungeklärter Risikobewertung zusätzlich
  `softwarefabric:needs-human-merge-review`. Kein selbstständiger Merge.

Schon beim Erstellen des Draft-PRs `softwarefabric:merge-blocked` setzen; bis
zu vollständigen Bewertungen bleibt die Risikolage offen.

Zusätzlich `softwarefabric:merge-risk-<Wert>` und
`softwarefabric:system-impact-<Wert>` setzen, sobald beide gültigen Bewertungen
vorliegen. In PR-Beschreibung und einem neuen, attribuierten Kommentar die beiden
Einzelbewertungen mit Reviewlinks, verwendete Maximalwerte, Begründungen,
Prüfstand und Entscheidung dokumentieren. Nutze
[../assets/merge-assessment-comment.template.md](../assets/merge-assessment-comment.template.md).
Lies Kommentar, Beschreibung und Labels zurück. `risk_comment_verified: true`
pro Review erst setzen, wenn die beiden Werte und Begründungen im richtigen
PR-Kommentar für genau diesen Stand zurückgelesen wurden. Lokale Bewertungen
ohne veröffentlichten Beleg erlauben keinen Agent-Merge. Fehlende Labels nach bestehenden
Repo-Konventionen anlegen. Vorherige Softwarefabric-Risikowerte und widersprüchliche
Merge-Entscheidungslabels entfernen; fachfremde Labels erhalten. Review-Kommentare
als historische Nachweise erhalten. Bei jeder Änderung sofort die frühere
Agent-Merge-Erlaubnis zurücknehmen und aktuelle Prüfung verlangen.

Ein Label/Kommentar oder der Datensatz selbst ist **keine** menschliche Freigabe.
Eine vorherige UX-Freigabe ist keine menschliche Merge-Prüfung. Hoch eingestufte
PRs bleiben zur Prüfung und manuellen Entscheidung beim Nutzer; nicht selbst durch
Umlabeln, ein Bot-Approve oder eine pauschale Zustimmung freigeben.

Bereits geprüfte offene Pipeline-PRs benötigen diese Merge-Phase ebenfalls.
`awaiting_merge` aus dem bisherigen Queue-Helfer bedeutet keine automatische
Befreiung von der Bewertung. Bei Wiederaufnahme Belege und aktuellen Stand
vergleichen, identische Kommentare nicht doppelt schreiben und keine günstiger
bewertete Runde ohne neue fachliche Evidenz suchen.

## Maschinelles Gate und tatsächlicher Merge

```bash
python3 /pfad/softwarefabric/orchestrator/scripts/merge_policy.py \
  --input <live-pr-snapshot.json> --profile <frozen-profile.json>
```

Der Snapshot erweitert den Vertrag von `implement-loop` um die oben beschriebenen
Reviewfelder einschließlich `risk_comment_verified` sowie `issue` (vollständiger live gelesener Issue-Snapshot für
`issue_gate`) und vier extern belegte Wahrheitswerte:

- `repository_rules_verified`: aktuelle Branch-/Ruleset-/Merge-Regeln gelesen;
- `repository_allows_agent_merge`: gewählte Merge-Art mit Agent-Identität nach
  diesen Regeln erlaubt; kein ausdrückliches Merge-Verbot im laufenden Auftrag;
- `required_human_reviews_satisfied`: tatsächlich erforderliche menschliche
  Repository-/CODEOWNERS-Freigaben liegen vor oder nachweislich nicht erforderlich;
- `issue_plan_matches_current_code`: Plan/UX-Freigabe weiterhin für die Änderung gültig.

Der Helfer liest nur JSON. Er beweist keine Identität, CI oder Berechtigung und
führt keinen Merge aus. `agent_may_merge` erfordert zusätzlich beide Council-Noten
≥ 9,5, klare Reviews, aktuellen Base/Head/Diff/Profile, grüne Prüfungen,
mergebaren aktuellen Branch, keine menschlichen Änderungswünsche, keinen Draft
und ein weiterhin gültiges Issue-/UX-Gate. Unbekannte Felder nicht günstig setzen.

Unmittelbar vor dem Merge Issue, PR, Base, Head, Diff, Reviews, Regeln und Checks
neu laden. Entscheidung und Markierung müssen noch genau diesen Stand betreffen.
Direkten Merge über den normalen GitHub-Weg mit **erwarteter Head-SHA** ausführen;
niemals Schutzregeln umgehen oder Admin-Bypass verwenden. Base-Änderungen erfordern
neue Prüfungen. Strikte aktuelle Branch-/CI-Regeln respektieren. Falls der erlaubte
Weg eine hier nicht freigegebene Queue/Berechtigung erfordert, blockieren und melden.
Kein zeitversetztes Auto-Merge aktivieren. Bei einem Konflikt oder abgelehnten
Merge neu lesen und den Blocker dokumentieren; nicht blind erneut versuchen.

Nach Erfolg tatsächlichen `MERGED`-Zustand, gemergte Head-SHA, Merge-Commit und
Zeitpunkt zurücklesen. Abschlusskommentar mit Entscheidung, Prüfstand und Mergebeleg
schreiben, Erlaubnislabel durch `softwarefabric:agent-merged` ersetzen und
`ready-for-merge-review` entfernen. Issue nur nach tatsächlichem Merge/Closingnachweis
als erledigt behandeln. Nach jedem eigenen Merge neue Base für die nächsten PRs
laden; alte Reviews und Noten gelten nicht automatisch weiter. Kein Deployment.
