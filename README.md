# t2stack

Wiederverwendbare Agent-Skills für eine organisierte Codeverbesserungspipeline.

## Skills

| Skill | Aufgabe |
| --- | --- |
| [map-codebase](skills/map-codebase/SKILL.md) | Kartiert ein Repository in fachliche Vertical Slices und dokumentiert Suchwege, Zuständigkeiten, Abhängigkeiten und Prüfungen. |

## map-codebase verwenden

Das Verzeichnis `skills/map-codebase` kann in das Skill-Verzeichnis des verwendeten
Agents kopiert werden, bei Codex üblicherweise nach `~/.codex/skills/map-codebase`.

Im zu untersuchenden Repository aufrufen:

```text
Nutze $map-codebase, um dieses Repository in fachliche Vertical Slices
zu kartieren. Erstelle CODE_MAP.md und die zugehörigen Markdown-Steckbriefe
unter docs/code-map/. Belege die Zuständigkeiten anhand des vorhandenen Codes.
```

Der Skill erstellt Dokumentation im Zielrepository. Er baut den Programmcode
nicht um und veröffentlicht die erzeugten Dokumente nicht selbstständig.

Die Hauptkarte enthält eine Routing-Tabelle für typische Aufgaben. Die
Steckbriefe dokumentieren konkrete Einstiegspunkte, repräsentative Abläufe,
Daten und Verträge, Abhängigkeiten, zu erhaltendes Verhalten und Prüfungen.
Gemeinsame Mechanismen und technische Grundlagen werden gesondert ausgewiesen.

## Regelmäßige Ausführung

`map-codebase` vergleicht vor jeder Untersuchung den in `CODE_MAP.md`
gespeicherten Prüfstand mit Git:

- **Gleicher Stand:** keine erneute Untersuchung und keine Dokumentänderungen.
- **Geänderter Stand:** nur den Diff seit der letzten vollständigen Prüfung und
  dessen Auswirkungen auf betroffene Slices untersuchen.
- **Nur Kartendokumente geändert:** ebenfalls keine erneute Codeprüfung.
- **Uncommittete Eingaben, fehlender Basiscommit oder unvollständiger Prüfstand:**
  Blocker melden; den alten Prüfstand nicht als erfolgreich fortschreiben.

Der neue Prüfstand wird erst nach erfolgreichem Abschluss eingetragen. Ein
abschließender Vergleich verhindert, dass zwischenzeitliche Codeänderungen
versehentlich als mitgeprüft gelten. Die Wiederholungsprüfung bezieht sich auf
committete Quellen; der Skill committet oder verwirft keinen vorhandenen Code.

Den nur lesenden Prüfer kannst du auch direkt aufrufen:

```bash
python3 skills/map-codebase/scripts/check_git_state.py --repo /pfad/zum/zielrepo
```

Er gibt `initial`, `unchanged`, `changed` oder `blocked` als JSON aus.
Der Abschlussaufruf mit `--expect-head <Start-SHA>` liefert bei stabilem
Quellstand `ready`; die inhaltliche Prüfung muss der Agent selbst abschließen.
Bei `blocked` liefert er Exit-Code 2, sonst 0. Er benötigt Python 3.10+ und Git;
zusätzliche Pakete sind nicht erforderlich.

## Struktur

```text
skills/
  map-codebase/
    SKILL.md
    agents/openai.yaml
    assets/CODE_MAP.template.md
    assets/slice.template.md
    scripts/check_git_state.py
    scripts/test_check_git_state.py
```

Prüfer testen:

```bash
python3 -m unittest discover -s skills/map-codebase/scripts -p 'test_*.py' -v
```
