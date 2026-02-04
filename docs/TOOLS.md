# Tools

Axon bietet verschiedene Tools, die die KI verwenden kann. Jedes Tool erfordert explizite Benutzer-Genehmigung.

## Übersicht

| Tool | Beschreibung | Risiko |
|------|--------------|--------|
| `file_read` | Datei lesen | Mittel |
| `file_write` | Datei schreiben | Mittel |
| `file_list` | Verzeichnis auflisten | Niedrig |
| `web_fetch` | URL abrufen | Mittel |
| `web_search` | Web-Suche | Niedrig |
| `shell_execute` | Shell-Command | Hoch |
| `code_execute` | Python-Code | Hoch |

## File Tools

### file_read

Liest den Inhalt einer Datei.

**Parameter:**
- `path` (string, required): Dateipfad
- `encoding` (string, optional): Encoding (Standard: utf-8)

**Einschränkungen:**
- Max. Dateigröße: 10MB (konfigurierbar)
- Blockierte Pfade: `/etc/passwd`, `/etc/shadow`, System-Verzeichnisse

**Beispiel:**
```
Lies die Datei config.json
```

### file_write

Schreibt Inhalt in eine Datei.

**Parameter:**
- `filename` (string, required): Dateiname (wird in /outputs/ gespeichert)
- `content` (string, required): Zu schreibender Inhalt

**Einschränkungen:**
- Dateien werden NUR in `/outputs/` gespeichert
- Pfad-Traversal wird blockiert

**Beispiel:**
```
Erstelle eine Datei namens ergebnis.txt mit dem Inhalt "Hallo Welt"
```

### file_list

Listet Dateien in einem Verzeichnis auf.

**Parameter:**
- `path` (string, required): Verzeichnispfad
- `recursive` (boolean, optional): Rekursiv auflisten (Standard: false)

**Einschränkungen:**
- Max. 100 Einträge bei rekursiver Auflistung

**Beispiel:**
```
Liste alle Dateien im aktuellen Ordner
```

## Web Tools

### web_fetch

Ruft Inhalte von einer URL ab.

**Parameter:**
- `url` (string, required): URL
- `method` (string, optional): HTTP-Methode (Standard: GET)

**Einschränkungen:**
- Blockierte Hosts: localhost, 127.0.0.1, interne IPs
- Timeout: 30 Sekunden
- Max. Response: 10.000 Zeichen

**Beispiel:**
```
Rufe die Seite https://example.com ab
```

### web_search

Durchsucht das Web mit DuckDuckGo.

**Parameter:**
- `query` (string, required): Suchbegriff
- `max_results` (integer, optional): Max. Ergebnisse (Standard: 5)

**Beispiel:**
```
Suche im Web nach "Python FastAPI Tutorial"
```

## Shell Tools

### shell_execute

Führt einen Shell-Befehl aus.

**Parameter:**
- `command` (string, required): Auszuführender Befehl

**Einschränkungen:**
- NUR Whitelist-Commands erlaubt
- Timeout: 30 Sekunden
- Output max. 5.000 Zeichen

**Whitelist:**
```
ls, dir, cat, type, head, tail, wc,
grep, find, date, pwd, echo,
python --version, node --version,
pip list, npm list
```

**Beispiel:**
```
Führe "ls -la" aus
```

## Code Tools

### code_execute

Führt Python-Code in einer Sandbox aus.

**Parameter:**
- `code` (string, required): Python-Code

**Einschränkungen:**
- RestrictedPython Sandbox
- Timeout: 30 Sekunden
- Memory: 256MB
- Kein Netzwerk-Zugriff
- Kein Dateisystem-Zugriff (außer /outputs/)

**Erlaubte Module:**
- math
- datetime
- json
- re

**Blockiert:**
- os, sys, subprocess
- open(), exec(), eval()
- Import beliebiger Module

**Beispiel:**
```
Berechne die Summe von 1 bis 100 mit Python
```

## Risiko-Level

### Niedrig (Low)
- file_list
- web_search

Diese Tools lesen nur Informationen und können keine Änderungen vornehmen.

### Mittel (Medium)
- file_read
- file_write
- web_fetch

Diese Tools können Daten lesen oder schreiben, aber nur in kontrollierten Bereichen.

### Hoch (High)
- shell_execute
- code_execute

Diese Tools können potenziell gefährliche Aktionen ausführen. Trotz Sandbox und Whitelist sollten sie mit Vorsicht genehmigt werden.

## Genehmigungsoptionen

Wenn ein Tool Genehmigung anfordert:

1. **Einmal erlauben**: Nur diese eine Ausführung
2. **Für Session erlauben**: Für die gesamte Chat-Session
3. **Ablehnen**: Tool wird nicht ausgeführt
4. **Nie erlauben**: Tool wird dauerhaft blockiert (für diese Session)

## Custom Tools

Custom Tools können in `backend/agent/tool_registry.py` hinzugefügt werden:

```python
self.register(ToolDefinition(
    name="my_custom_tool",
    description="Does something useful",
    description_de="Macht etwas Nützliches",
    parameters={
        "param1": {"type": "string", "required": True},
        "param2": {"type": "integer", "default": 10}
    },
    risk_level=RiskLevel.MEDIUM
))
```

Und der Handler in `backend/agent/tool_handlers.py`:

```python
async def handle_my_custom_tool(params: dict) -> str:
    param1 = params.get("param1")
    param2 = params.get("param2", 10)
    # Implementierung
    return result
```
