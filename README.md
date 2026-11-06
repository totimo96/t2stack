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

## Struktur

```text
skills/
  map-codebase/
    SKILL.md
    agents/openai.yaml
    assets/CODE_MAP.template.md
    assets/slice.template.md
```
