<p align="center">
  <img src="assets/axon-logo.png" alt="Axon by NeuroVexon" width="300">
</p>

<h1 align="center">Axon by NeuroVexon</h1>

<p align="center">
  <strong>Agentic AI - ohne Kontrollverlust.</strong>
</p>

<p align="center">
  <a href="https://github.com/neurovexon/axon-community/actions/workflows/ci.yml">
    <img src="https://github.com/neurovexon/axon-community/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://github.com/neurovexon/axon-community/releases">
    <img src="https://img.shields.io/github/v/release/neurovexon/axon-community?color=00d4ff" alt="Release">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License">
  </a>
  <a href="https://github.com/neurovexon/axon-community/stargazers">
    <img src="https://img.shields.io/github/stars/neurovexon/axon-community?style=social" alt="Stars">
  </a>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-schnellstart">Schnellstart</a> •
  <a href="#cli">CLI</a> •
  <a href="#-dokumentation">Docs</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-lizenz">Lizenz</a>
</p>

---

## Was ist Axon?

**Axon** ist ein Open-Source KI-Assistent mit kontrollierten Agent-Fähigkeiten. Anders als andere "Agentic AI" Tools behältst du bei Axon die volle Kontrolle:

- Jede Aktion wird **vor der Ausführung angezeigt**
- Du entscheidest: **Erlauben** oder **Ablehnen**
- Vollständiges **Audit-Log** aller Aktionen
- **100% On-Premise** möglich - keine Cloud erforderlich
- **Persistentes Gedächtnis** — Axon merkt sich Fakten über Konversationen hinweg
- **Erweiterbar mit Skills** — Community-Plugins mit Sicherheits-Gate

<p align="center">
  <img src="docs/images/screenshot.png" alt="Axon Screenshot" width="800">
</p>

## Features

| Feature | Beschreibung |
|---------|--------------|
| **Controlled Tools** | File, Web, Shell, Memory — alles mit expliziter Bestätigung |
| **Tool Approval UI** | Modales Fenster vor jeder Aktion mit Risiko-Anzeige |
| **Audit Dashboard** | Alle Tool-Calls sichtbar und als CSV exportierbar |
| **Multi-Provider LLM** | Ollama (lokal), Claude API, OpenAI API |
| **Agent Orchestrator** | Vollständige Agent-Loop mit Tool-Calls und Feedback |
| **Persistentes Memory** | KI merkt sich Fakten über Konversationen hinweg |
| **Skills System** | Erweiterbare Fähigkeiten mit Hash-basiertem Sicherheits-Gate |
| **Messenger Integration** | Telegram und Discord Bots mit Inline-Approval |
| **Verschlüsselte API-Keys** | Fernet-Verschlüsselung in der DB |
| **Chat mit Streaming** | SSE-basiertes Streaming mit Konversationshistorie |
| **CLI** | Terminal-Steuerung mit SSE-Streaming, Pipe-Support und Scripting |
| **Docker Deployment** | One-Command Setup |
| **DSGVO-konform** | On-Premise, keine externe Datenübertragung |
| **Dark Theme** | Modernes UI mit Cyan-Akzenten |

## Axon vs. OpenClaw / andere Agentic AI

| | Axon | OpenClaw | Typische Chat-UIs |
|---|---|---|---|
| Tool-Kontrolle | Jeder Call einzeln genehmigt | Automatisch | Keine Tools |
| Audit-Log | Vollständig, CSV-Export | Teilweise | Nein |
| On-Premise | Ja (Ollama) | Nur Cloud | Nur Cloud |
| Persistentes Memory | Ja (DB-basiert) | Nein | Nein |
| Skills/Plugins | Ja, mit Sicherheits-Gate | Ja, ohne Gate | Nein |
| Messenger-Bots | Telegram + Discord | Nein | Nein |
| CLI / Terminal | Ja (Pipe, Scripting) | Nein | Nein |
| Open Source | Apache 2.0 | Proprietär | Variiert |
| DSGVO-konform | Ja | Nein | Variiert |

## Schnellstart

### Mit Docker (empfohlen)

```bash
# Repository klonen
git clone https://github.com/neurovexon/axon-community.git
cd axon-community

# Konfiguration erstellen
cp .env.example .env

# Starten
docker-compose up -d

# Ollama Model laden (einmalig)
docker exec axon-ollama ollama pull llama3.1:8b
```

**Öffne http://localhost:3000**

### Manuelle Installation

<details>
<summary>Backend</summary>

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload
```
</details>

<details>
<summary>Frontend</summary>

```bash
cd frontend
npm install
npm start
```
</details>

## CLI

Axon bietet eine vollwertige CLI fuer Power-User — SSE-Streaming, Tool-Approval und Pipe-Support direkt im Terminal.

### Installation

```bash
# Option 1: pip install (empfohlen)
pip install -e ./cli
axon chat "Hallo"

# Option 2: Direkt ausfuehren
python cli/axon_cli.py chat "Hallo"
```

### Konfiguration

```bash
axon config set url http://localhost:8000   # Server-URL
axon config set auth user:password          # Basic Auth (optional)
axon config set language de                 # Sprache: de / en
axon config show                            # Aktuelle Config anzeigen
```

### Commands

```bash
# Chat (SSE-Streaming mit Live-Ausgabe)
axon chat "Nachricht"                       # Einzelne Nachricht
axon chat --agent Recherche "Nachricht"     # Mit spezifischem Agent
axon chat --session <id> "Nachricht"        # Session fortsetzen
cat datei.txt | axon chat                   # Pipe-Support

# Interaktiver Modus
axon                                        # REPL starten

# Agents
axon agents                                 # Alle Agents auflisten
axon agents show <name>                     # Agent-Details

# Memory
axon memory list                            # Alle Memories
axon memory search "query"                  # Memory durchsuchen
axon memory add "key" "content"             # Memory hinzufuegen
axon memory delete <id>                     # Memory loeschen

# System
axon status                                 # Health Check + Dashboard-Stats
axon version                                # CLI + Server Version
```

### Tool-Approval

Wenn der Agent ein Tool nutzen will, erscheint ein Approval-Prompt:

```
╭─ Tool-Anfrage ───────────────────────────╮
│ Tool:   web_search                       │
│ Risiko: niedrig                          │
│                                          │
│   query: Python Tutorials                │
╰──────────────────────────────────────────╯
[A]llow  [S]ession  [R]eject  > a
```

## Verfügbare Tools

| Tool | Beschreibung | Risiko |
|------|--------------|--------|
| `file_read` | Datei lesen | Mittel |
| `file_write` | Datei schreiben (nur /outputs/) | Mittel |
| `file_list` | Verzeichnis auflisten | Niedrig |
| `web_fetch` | URL abrufen | Mittel |
| `web_search` | Web-Suche (DuckDuckGo) | Niedrig |
| `shell_execute` | Shell-Command (Whitelist) | Hoch |
| `memory_save` | Fakt im Gedächtnis speichern | Niedrig |
| `memory_search` | Gedächtnis durchsuchen | Niedrig |
| `memory_delete` | Eintrag aus Gedächtnis löschen | Niedrig |

## Konfiguration

```env
# LLM Provider: ollama, claude, openai
LLM_PROVIDER=ollama

# Ollama (lokal)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Claude API (optional)
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI API (optional)
OPENAI_API_KEY=sk-...

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_ALLOWED_USERS=  # Komma-getrennte User-IDs, leer = alle

# Discord Bot (optional)
DISCORD_BOT_TOKEN=MTIz...
DISCORD_ALLOWED_CHANNELS=  # Komma-getrennte Channel-IDs
```

Siehe [docs/CONFIGURATION.md](docs/CONFIGURATION.md) für alle Optionen.

## Dokumentation

- [Installation](docs/INSTALLATION.md)
- [Konfiguration](docs/CONFIGURATION.md)
- [CLI](docs/CLI.md)
- [Tools](docs/TOOLS.md)
- [Skills](docs/SKILLS.md)
- [Messenger Integration](docs/MESSENGER.md)
- [Security](SECURITY.md)
- [Testing](docs/TESTING.md)
- [API Reference](docs/API.md)
- [Changelog](CHANGELOG.md)
- [Drittlizenzen](THIRD_PARTY_LICENSES.md)

## Sicherheit

- **Shell Whitelist**: Nur vordefinierte Commands, Chaining blockiert
- **File Restriction**: Schreiben nur in /outputs/, Path-Traversal blockiert
- **URL Validation**: SSRF-Schutz (localhost, interne IPs, AWS IMDS blockiert)
- **Verschlüsselte API-Keys**: Fernet-Verschlüsselung in der SQLite DB
- **Skills Gate**: File-Hash Prüfung, automatische Revocation bei Änderung
- **Audit Trail**: Jede Aktion wird geloggt

Sicherheitslücken? [SECURITY.md](SECURITY.md)

## Contributing

Beiträge sind willkommen! Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'feat: Add AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

## Lizenz

**Apache License 2.0** — siehe [LICENSE](LICENSE)

Du kannst AXON frei nutzen, modifizieren, verbreiten und kommerziell einsetzen.
Einzige Bedingung: Copyright-Hinweis und Lizenztext beibehalten.

| Nutzung | Erlaubt? |
|---------|----------|
| Private Nutzung | Ja |
| Kommerzielle Nutzung | Ja |
| Modifikation | Ja |
| Distribution | Ja |
| Patent-Nutzung | Ja |
| Haftungsausschluss | Software wird "as is" bereitgestellt |

## Enterprise

AXON Community Edition ist frei nutzbar — auch kommerziell.

Für erweiterte Anforderungen bietet NeuroVexon:

- **NeuroVexon Assistant** — Enterprise KI-Plattform mit RAG, Multi-User, Admin-Panels
- **Support & SLA** — Professioneller Support für produktive Umgebungen
- **On-Premise Deployment** — Beratung und Einrichtung

> [neurovexon.com](https://neurovexon.com)

## Community

- [GitHub Discussions](https://github.com/neurovexon/axon-community/discussions)
- [GitHub Issues](https://github.com/neurovexon/axon-community/issues)
- Email: service@neurovexon.com

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neurovexon/axon-community&type=Date)](https://star-history.com/#neurovexon/axon-community&Date)

---

<p align="center">
  <strong>Axon by NeuroVexon</strong><br>
  <em>Agentic AI - ohne Kontrollverlust.</em>
</p>

<p align="center">
  Made with Liebe in Germany
</p>
