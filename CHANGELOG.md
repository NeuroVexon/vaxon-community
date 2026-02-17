# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Geplant
- Multi-User Support mit Rollen und Berechtigungen
- RAG / Vektor-Suche ueber Dokumente
- Voice Input/Output
- Mobile App (React Native)
- Plugin-Marketplace

## [2.0.0] - 2026-02-17

### Added

- **Multi-Agent System** — Mehrere Agents mit eigenen Rollen, Permissions und Modellen
  - 3 Default-Agents: Assistent (alle Tools), Recherche (Web-fokussiert), System (Shell)
  - Per-Agent: erlaubte Tools, Auto-Approve-Liste, Risiko-Level
  - Agent-Switcher im Chat, Agent-Editor im Frontend
  - API: CRUD unter `/api/v1/agents`

- **Scheduled Tasks** — Proaktive Aufgaben mit Cron und Approval-Gate
  - APScheduler-basiert mit Cron-Expressions
  - Approval ueber Web/Telegram/Discord vor Ausfuehrung
  - Sicherheit: Max 10 aktive Tasks, 5min Timeout, max 1/min
  - API: CRUD + manueller Run unter `/api/v1/tasks`

- **E-Mail Integration** — IMAP/SMTP mit bewussten Einschraenkungen
  - Lesen: Ungelesene auflisten, suchen, einzelne lesen
  - Senden: Immer mit Approval (zeigt Empfaenger + Text)
  - Bewusst NICHT: delete, move, mark_as_read — Axon veraendert den Posteingang nicht
  - Verschluesselte Credentials in DB

- **Workflow-Chains** — Mehrstufige Ablaeufe mit Template-Variablen
  - Steps mit `{{variable}}` Kontext-Weitergabe
  - Trigger-Phrases fuer automatische Aktivierung
  - Approval-Modes: each_step / once_at_start / never
  - API: CRUD + Run + History unter `/api/v1/workflows`

- **MCP-Server** — Axon als kontrollierter Tool-Provider fuer externe AI-Clients
  - JSON-RPC 2.0 Protokoll (initialize, tools/list, tools/call)
  - SSE-Transport mit Bearer Token Auth
  - Tool-Calls laufen durch Axon Approval-System
  - Kompatibel mit Claude Desktop, Cursor, etc.
  - Endpoint: `GET /mcp/v1/sse`

- **Dashboard & Analytics** — Admin-Uebersicht mit Kernmetriken
  - Overview: Conversations, Messages, Agents, Tool Calls, Approval Rate
  - Tool-Statistiken: Nutzung, Fehlerrate, Ausfuehrungszeit
  - Timeline: 30-Tage Verlauf
  - Agent-Statistiken
  - API unter `/api/v1/analytics`

- **Code-Sandbox** — Docker-basierte Code-Ausfuehrung
  - Netzwerk-Isolation (`--network none`)
  - Resource-Limits: 256MB RAM, 0.5 CPU, 60s Timeout
  - Read-only Filesystem, kein Host-Zugriff
  - `code_execute` Tool zurueck mit risk_level: high

- **Dokument-Upload** — Dateien hochladen und im Chat analysieren
  - PDF (PyMuPDF), Text, Code, CSV, Bilder
  - Max 10 MB, automatische Text-Extraktion
  - Context-Injection in Agent-Prompt
  - Drag & Drop im Frontend
  - API: `POST /api/v1/upload`

- **CLI** — Terminal-Steuerung fuer Power-User
  - SSE-Streaming mit Live-Textausgabe
  - Tool-Approval direkt im Terminal
  - Interaktiver REPL-Modus mit persistenter Session
  - Pipe-Support: `cat datei.txt | axon chat`
  - Commands: chat, agents, memory, config, status, version
  - Standalone HTTP-Client (typer + httpx + rich)
  - Cross-Platform: Windows, macOS, Linux

- **6 LLM-Provider** — Ollama, Claude, OpenAI, Gemini, Groq, OpenRouter
  - Runtime-Switching ueber Settings
  - Per-Agent Model-Konfiguration
  - Health-Check fuer alle Provider

- **i18n** — Deutsch + Englisch im Frontend und CLI

### Changed
- Agent-Orchestrator nutzt per-Agent Permissions und Auto-Approve
- Chat-Endpoint akzeptiert `agent_id` Parameter
- Frontend: Sidebar mit Dashboard, Agents, Workflows, Skills, Zeitplan
- Telegram/Discord: `/agent` und `/agents` Commands

### Security
- Docker-Sandbox: Netzwerk-Isolation, Memory-Limits, Read-only FS
- MCP-Server: Bearer Token Auth + Rate Limiting
- E-Mail: Kein Delete/Move/Mark — nur lesen und senden
- Scheduled Tasks: Max 10, Timeout 5min, Audit-Trail
- Workflows: Stopp bei Fehler, Audit-Trail pro Step

## [1.1.0] - 2026-02-16

### Added
- **Persistentes Memory** — KI merkt sich Fakten über Konversationen hinweg
  - Memory-Tools: `memory_save`, `memory_search`, `memory_delete`
  - Memory wird automatisch in den System-Prompt injiziert
  - Frontend: Gedächtnis-View mit Suche, Kategorien, CRUD
  - API: Vollständige CRUD-Endpoints unter `/api/v1/memory`

- **Skills System** — Erweiterbare Fähigkeiten mit Sicherheits-Gate
  - Plugin-basierte Architektur (`backend/skills/`)
  - SHA-256 Hash-Prüfung bei jedem Laden
  - Automatische Revocation bei Dateiänderungen
  - Frontend: Skills-View mit Approve/Toggle/Delete
  - 3 mitgelieferte Skills: `summarize`, `word_count`, `json_formatter`
  - Dokumentation: [docs/SKILLS.md](docs/SKILLS.md)

- **Telegram Integration** — Bot mit Inline-Keyboard für Tool-Approvals
  - SSE-Stream Anbindung an den Agent-Endpoint
  - User-Whitelist und Session-Management
  - Befehle: `/start`, `/new`, `/status`

- **Discord Integration** — Bot mit Button-Components für Tool-Approvals
  - Embeds mit farbcodiertem Risiko-Level
  - Channel- und User-Whitelist
  - Auto-Timeout (120s) für ausstehende Approvals
  - Dokumentation: [docs/MESSENGER.md](docs/MESSENGER.md)

- **Agent-Endpoint** — Neuer SSE-Endpoint `/api/v1/chat/agent`
  - Nutzt AgentOrchestrator mit Tool-Approval Loop
  - Frontend komplett auf Agent-Streaming umgestellt

- **Konversationshistorie** — Letzte 50 Messages werden geladen
- **Konversations-Sidebar** — History mit klickbaren Einträgen, Delete-Button
- **ExamplePrompts** — Klickbar, senden direkt eine Nachricht
- **Verschlüsselte API-Keys** — Fernet-Verschlüsselung in der SQLite DB

### Changed
- Frontend nutzt jetzt ausschließlich den Agent-Endpoint (SSE)
- Security-Funktionen zentralisiert in `core/security.py`
- Tool-Handlers nutzen jetzt zentrale Validierungsfunktionen

### Removed
- `code_execute` Tool — RestrictedPython ist keine sichere Sandbox
- `RestrictedPython` Dependency

### Security
- Command-Chaining blockiert (`&&`, `||`, `;`, `|`, Backticks, `$()`)
- Path-Traversal Schutz über `validate_path()`
- SSRF-Schutz über `validate_url()` (localhost, interne IPs, AWS IMDS)
- API-Keys verschlüsselt in DB (Fernet)
- Skills: Hash-basiertes Sicherheits-Gate mit Auto-Revocation
- 30+ Security-Tests

## [1.0.0] - 2026-02-04

### Added
- **Chat Interface** - Modernes React UI mit Streaming-Support
- **Multi-Provider LLM** - Unterstützung für Ollama, Claude API und OpenAI API
- **Controlled Tools** - Tool-System mit expliziter Benutzer-Genehmigung
  - `file_read` - Dateien lesen
  - `file_write` - Dateien schreiben (nur in /outputs/)
  - `file_list` - Verzeichnisse auflisten
  - `web_fetch` - URLs abrufen
  - `web_search` - Web-Suche mit DuckDuckGo
  - `shell_execute` - Shell-Commands (Whitelist)
- **Tool Approval Modal** - UI für Tool-Genehmigungen mit Risiko-Anzeige
- **Permission Manager** - Session-basierte Berechtigungen
- **Audit Dashboard** - Vollständiges Logging aller Tool-Ausführungen
- **Audit Export** - CSV-Export für Compliance
- **Docker Support** - One-Command Deployment mit docker-compose
- **Dark Theme** - Modernes Dark UI mit Cyan-Akzenten

### Security
- Shell-Commands nur über Whitelist
- File-Write nur in /outputs/ Verzeichnis
- Audit-Trail für alle Aktionen

---

## Versioning

- **MAJOR**: Inkompatible API-Änderungen
- **MINOR**: Neue Features (abwärtskompatibel)
- **PATCH**: Bug Fixes (abwärtskompatibel)

## Links

- [GitHub Releases](https://github.com/neurovexon/axon-community/releases)
- [Dokumentation](https://github.com/neurovexon/axon-community/wiki)
