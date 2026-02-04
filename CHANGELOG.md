# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Geplant
- Multi-User Support
- RAG / Dokumentenverarbeitung
- Voice Input/Output
- Plugin System
- Mobile App

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
  - `code_execute` - Python-Code in Sandbox
- **Tool Approval Modal** - UI für Tool-Genehmigungen mit Risiko-Anzeige
- **Permission Manager** - Session-basierte Berechtigungen
- **Audit Dashboard** - Vollständiges Logging aller Tool-Ausführungen
- **Audit Export** - CSV-Export für Compliance
- **Docker Support** - One-Command Deployment mit docker-compose
- **Dark Theme** - Modernes Dark UI mit Cyan-Akzenten

### Security
- Shell-Commands nur über Whitelist
- File-Write nur in /outputs/ Verzeichnis
- Code-Execution in RestrictedPython Sandbox
- Audit-Trail für alle Aktionen

---

## Versioning

- **MAJOR**: Inkompatible API-Änderungen
- **MINOR**: Neue Features (abwärtskompatibel)
- **PATCH**: Bug Fixes (abwärtskompatibel)

## Links

- [GitHub Releases](https://github.com/neurovexon/axon-community/releases)
- [Dokumentation](https://github.com/neurovexon/axon-community/wiki)
