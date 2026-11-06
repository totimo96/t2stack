{human_banner}

{issue_metadata}

## Validierter Befund

- Art: {kind}
- Befund-ID: `{finding_id}`
- Slice: `{slice_id}`
- Schwere: **{severity_score}/10** — {severity_reason}
- Aussage-Sicherheit: {confidence}
- Report: `{report_path}` (SHA-256 `{report_sha256}`, Lauf `{report_run_id}`)
- Report-Commit: `{report_commit}`
- Unabhängig validierter Commit: `{validation_commit}`

### Evidenz und Ursache

{evidence}

### Geprüfte Gegenargumente

{counter_evidence}

### Betroffene Codestellen

{locations}

### Reproduktion und Prüfungen

{reproduction}

## UX-Auswirkungen und Umsetzungsgate

- Bestehendes Problem: **{ux_existing_score}/10** — {ux_existing_reason}
- Vorgeschlagene Änderung: **{ux_change_score}/10** — {ux_change_reason}
- Menschliche Freigabe vor Umsetzung: **{human_required}**
- Gate-Begründung: {gate_reason}

{human_question}

## Umsetzungsvorschlag

{fix_plan}

### Weniger eingreifende Alternative

{alternative}

### Risiken, Kompatibilität und Rückfall

{risks}

### Akzeptanzkriterien

{acceptance_criteria}

### Regressionstests

{regression_tests}

## Arbeitsauftrag für den Umsetzungsagenten

1. Aktuellen Code und betroffene Verträge gegen den Validierungsstand prüfen.
2. Issue-Body und Labels live lesen. Bei `blocked`, widersprüchlichem Gate oder
   erforderlicher, nicht nachgewiesener menschlicher Freigabe keine Umsetzung starten.
3. Nur die belegte Ursache im angegebenen Umfang beheben und Akzeptanzkriterien prüfen.
4. Regressionstests ausführen; tatsächliche Ergebnisse und ungetestete Ebenen dokumentieren.
5. Veränderte Lösung oder UX-Auswirkung erneut validieren. Keine eigenständige
   Freigabe, keinen Merge und kein Deployment aus diesem Issue ableiten.
