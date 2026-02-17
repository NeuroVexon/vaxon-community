# Axon CLI — Dokumentation

Die Axon CLI ist ein standalone Terminal-Client fuer Axon. Sie kommuniziert ueber HTTP mit dem Axon-Backend und bietet SSE-Streaming, Tool-Approval und Pipe-Support.

## Installation

### Option 1: pip install (empfohlen)

```bash
cd axon-community
pip install -e ./cli
axon --help
```

Dies registriert den `axon` Command global.

### Option 2: Direkt ausfuehren

```bash
python cli/axon_cli.py --help
```

### Option 3: Alias (PowerShell)

```powershell
Set-Alias axon "python C:\pfad\zu\axon-community\cli\axon_cli.py"
```

### Option 3: Alias (Bash/Zsh)

```bash
alias axon="python3 /pfad/zu/axon-community/cli/axon_cli.py"
```

### Dependencies

- Python 3.10+
- `typer` >= 0.9.0 — CLI-Framework
- `httpx` >= 0.27.0 — HTTP-Client mit Streaming
- `rich` >= 13.0.0 — Farbige Terminal-Ausgabe

## Konfiguration

Die CLI speichert ihre Konfiguration in `~/.axon/config.json`. Die Datei wird beim ersten Start automatisch mit Defaults erstellt.

### Server-URL setzen

```bash
axon config set url http://localhost:8000        # Lokal
axon config set url https://axon.example.com     # Remote
```

### Basic Auth (fuer Deployments mit Nginx Auth)

```bash
axon config set auth benutzername:passwort
```

### Sprache

```bash
axon config set language de    # Deutsch (Standard)
axon config set language en    # English
```

### Konfiguration anzeigen

```bash
axon config show
```

```
+------------------------------- Konfiguration -------------------------------+
| URL:      https://axon.example.com                                          |
| Auth:     benutzername:****                                                 |
| Sprache:  de                                                                |
+-----------------------------------------------------------------------------+
```

## Commands

### axon chat — Nachricht senden

```bash
# Einfache Nachricht
axon chat "Was ist Python?"

# Mit spezifischem Agent
axon chat --agent Recherche "Suche nach FastAPI Tutorials"

# Session fortsetzen (nutze Session-ID aus vorherigem Chat)
axon chat --session abc123 "Und was noch?"
```

Die Antwort wird live per SSE-Streaming angezeigt — Wort fuer Wort, wie im Web-UI.

### Pipe-Support

Die CLI erkennt automatisch, ob Input ueber eine Pipe kommt:

```bash
# Datei-Inhalt senden
cat README.md | axon chat
type README.md | axon chat          # Windows CMD

# Command-Output analysieren
git log --oneline -10 | axon chat
docker ps | axon chat --agent System

# Scripting
echo "Fasse zusammen: $(cat report.txt)" | axon chat
```

### Tool-Approval

Wenn der Agent ein Tool nutzen will, erscheint ein farbiges Panel:

```
+------------------------------- Tool-Anfrage --------------------------------+
| Tool:   web_search                                                          |
| Risiko: niedrig                                                             |
|   Durchsucht das Web mit DuckDuckGo                                         |
|                                                                             |
|   query: FastAPI Performance Tipps                                          |
+-----------------------------------------------------------------------------+
[A]llow  [S]ession  [R]eject (a):
```

- **A (Allow)**: Tool einmalig ausfuehren
- **S (Session)**: Tool fuer diese Session immer erlauben
- **R (Reject)**: Tool ablehnen

Das Risiko-Level wird farblich markiert: gruen (niedrig), gelb (mittel), rot (hoch).

### axon (REPL-Modus)

Ohne Subcommand startet der interaktive Modus:

```bash
axon
```

```
+------------ Axon CLI v1.0.0 — Verbunden mit https://axon.example.com ------+
Schreibe eine Nachricht oder /help fuer Hilfe. Beende mit /exit oder Ctrl+C.

> Hallo!
Hallo! Wie kann ich dir helfen?

> /agent Recherche
Agent gewechselt zu: Recherche

> Suche nach Python 3.13 Features
[SSE-Streaming...]

> /new
Neue Session gestartet.

> /exit
Auf Wiedersehen!
```

**REPL-Commands:**

| Command | Beschreibung |
|---------|-------------|
| `/help` | Hilfe anzeigen |
| `/new` | Neue Session starten |
| `/agent <name>` | Agent wechseln |
| `/exit` oder `Ctrl+C` | Beenden |

### axon agents — Agents verwalten

```bash
# Alle Agents auflisten
axon agents
```

```
                                    Agents
+----------+-------------------------+--------+------------+---------+-------+
| Name     | Beschreibung            | Modell | Risiko Max | Default | Aktiv |
|----------+-------------------------+--------+------------+---------+-------|
| Assistent| Allgemeiner KI-Assistent| -      | high       |   ja    |  ja   |
| Recherche| Web-Recherche           | -      | medium     |         |  ja   |
| System   | Shell-Zugriff           | -      | high       |         |  ja   |
+----------+-------------------------+--------+------------+---------+-------+
```

```bash
# Agent-Details
axon agents show Recherche
```

### axon memory — Memory verwalten

```bash
# Alle Memories auflisten
axon memory list

# Memory durchsuchen
axon memory search "Python"

# Memory hinzufuegen
axon memory add "Projekt" "Wir nutzen FastAPI und React" --category Technik

# Memory loeschen (volle UUID aus 'memory list')
axon memory delete 8ae2871e-2f40-4aff-860e-3e0bcdcaeed3
```

### axon status — Health Check

```bash
axon status
```

```
+-------------------------------- Axon Status --------------------------------+
| Server erreichbar  https://axon.example.com                                 |
| App:     Axon by NeuroVexon                                                 |
| Version: 2.0.0                                                              |
|                                                                             |
| LLM Provider:                                                               |
|   ollama: available                                                         |
|   claude: unavailable                                                       |
|                                                                             |
| Dashboard:                                                                  |
|   Conversations: 44                                                         |
|   Messages:      170                                                        |
|   Agents:        3                                                          |
|   Tool Calls:    21                                                         |
|   Approval Rate: 92.5%                                                      |
+-----------------------------------------------------------------------------+
```

### axon version — Versionsinformation

```bash
axon version
```

```
+---------------------------------- Version ----------------------------------+
| Axon CLI:    v1.0.0                                                         |
| Axon Server: v2.0.0                                                         |
+-----------------------------------------------------------------------------+
```

## Scripting & Automation

Die CLI ist fuer Automatisierung ausgelegt:

```bash
# Health-Check in einem Skript
axon status || echo "Server nicht erreichbar"

# Memory aus Datei importieren
while IFS="|" read -r key content; do
  axon memory add "$key" "$content"
done < memories.csv

# Taeglich ausfuehren (crontab)
0 9 * * * echo "Tagesbericht fuer $(date)" | /usr/local/bin/axon chat >> /var/log/axon-daily.log
```

## Plattform-Kompatibilitaet

| Plattform | Shell | Pipe | REPL | Status |
|-----------|-------|------|------|--------|
| Windows 10/11 | PowerShell | Ja | Ja | Getestet |
| Windows 10/11 | CMD | Ja | Ja | Getestet |
| Linux | Bash/Zsh | Ja | Ja | Getestet |
| macOS | Zsh/Bash | Ja | Ja | Kompatibel |

## Fehlerbehebung

### Verbindung fehlgeschlagen

```
Verbindung fehlgeschlagen: [Errno 111] Connection refused
```

Pruefe mit `axon config show` ob die URL korrekt ist und ob der Server laeuft.

### Authentifizierung fehlgeschlagen (401)

```
Authentifizierung fehlgeschlagen (401). Pruefe 'axon config set auth'.
```

Setze die korrekten Zugangsdaten:
```bash
axon config set auth benutzername:passwort
```

### Server-Fehler (404)

Einige Endpoints existieren erst ab bestimmten Server-Versionen:
- `/api/v1/agents` — ab v2.0.0
- `/api/v1/analytics/overview` — ab v2.0.0

Pruefe die Server-Version mit `axon version`.
