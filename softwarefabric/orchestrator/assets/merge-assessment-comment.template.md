> [!NOTE]
> 🤖 **{verified_model} responding on behalf of {user}**

## Merge-Bewertung

Stand: Base `{base_sha}` · Head `{head_sha}` · Diff `{diff_sha256}`
Rollenprofil: `{profile_sha256}` · Council-Runde: {round}

| Mitglied | Mergerisiko /10 | Systemauswirkungen /10 | Begründung und Review |
| --- | --- | --- | --- |
| {worker_council_model} | {merge_risk} | {system_impact} | {reason_and_review_link} |
| {verifier_council_model} | {merge_risk} | {system_impact} | {reason_and_review_link} |
| **Maßgeblicher Höchstwert** | **{max_merge_risk}** | **{max_system_impact}** | Keine Mittelung |

1 = niedrig / eng begrenzt, 10 = hoch / systemweit. Unbekannt wird nicht als niedrig gewertet.

**Entscheidung: {Agent darf mergen / menschliche Merge-Prüfung nötig / blockiert}.**
{Begründung; sonstige Gate-Blocker und erforderliche nächste Aktion.}

## Prüfung

{Aktuelle Council-, CI-, Issue-/UX- und Repository-Gates mit Belegen.
Tatsächlich geprüfte Ebenen, verbleibende Unsicherheiten und Rollback.}

{Nach Erfolg separat ergänzender Kommentar: gemergter Head, Merge-Commit,
Zeitpunkt und verifizierter Merge-Link. Kein bloß geplanter Merge als erfolgt.}
