> [!NOTE]
> 🤖 **{model} responding on behalf of {user}**

Council-Review, Runde **{round}** — **{member}**

- PR: {pr_url}
- Geprüfte Base: `{base_sha}`
- Geprüfter Head: `{head_sha}`
- Diff SHA-256: `{diff_sha256}`
- Empfehlung: **{recommendation}**

| Aspekt | Note /10 | Begründung |
| --- | --- | --- |
| Richtigkeit | {score} | {evidence} |
| Cybersicherheit | {score} | {evidence} |
| Codequalität | {score} | {evidence} |
| Performance | {score} | {evidence} |
| Gesamtqualität | {overall_score} | {reason} |

## Befunde und verbleibende Blocker

{Konkrete Stelle, Ursache, Auswirkung und Evidenz je Befund; oder ausdrücklich
keine blockierenden Befunde im untersuchten Umfang. Keine absolute Fehlerfreiheit.}

## Prüfung und Grenzen

{Was wurde tatsächlich gelesen oder geprüft? Was wurde nicht ausgeführt oder
nicht erreicht? Tests, lokale Reproduktion, Browser, Deployment und Produktion
klar auseinanderhalten.}
