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
    <img src="https://img.shields.io/badge/license-BSL%201.1-blue" alt="License">
  </a>
  <a href="https://github.com/neurovexon/axon-community/stargazers">
    <img src="https://img.shields.io/github/stars/neurovexon/axon-community?style=social" alt="Stars">
  </a>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-schnellstart">Schnellstart</a> •
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

<p align="center">
  <img src="docs/images/screenshot.png" alt="Axon Screenshot" width="800">
</p>

## ✨ Features

| Feature | Beschreibung |
|---------|--------------|
| 🔧 **Controlled Tools** | File, Web, Shell - alles mit expliziter Bestätigung |
| 🛡️ **Tool Approval UI** | Modales Fenster vor jeder Aktion mit Risiko-Anzeige |
| 📊 **Audit Dashboard** | Alle Tool-Calls sichtbar und als CSV exportierbar |
| 🤖 **Multi-Provider LLM** | Ollama (lokal), Claude API, OpenAI API |
| 💬 **Chat Interface** | Modernes React UI mit Streaming |
| 🐳 **Docker Deployment** | One-Command Setup |
| 🔒 **DSGVO-konform** | On-Premise, keine externe Datenübertragung |
| 🌙 **Dark Theme** | Modernes UI mit Cyan-Akzenten |

## 🆚 Warum Axon?

| Problem bei anderen Tools | Lösung bei Axon |
|---------------------------|-----------------|
| ❌ Keine Logs/Kontrolle | ✅ Vollständiges Audit-Log |
| ❌ Tools laufen automatisch | ✅ Explizite Genehmigung für jeden Call |
| ❌ Nur Cloud APIs | ✅ Ollama lokal möglich |
| ❌ US-Server | ✅ 100% On-Premise |
| ❌ Keine Transparenz | ✅ Open Source, lesbar |

## 🚀 Schnellstart

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

**Öffne http://localhost:3000** 🎉

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

## 🔧 Verfügbare Tools

| Tool | Beschreibung | Risiko |
|------|--------------|--------|
| `file_read` | Datei lesen | 🟡 Mittel |
| `file_write` | Datei schreiben (nur /outputs/) | 🟡 Mittel |
| `file_list` | Verzeichnis auflisten | 🟢 Niedrig |
| `web_fetch` | URL abrufen | 🟡 Mittel |
| `web_search` | Web-Suche (DuckDuckGo) | 🟢 Niedrig |
| `shell_execute` | Shell-Command (Whitelist) | 🔴 Hoch |
| `code_execute` | Python in Sandbox | 🔴 Hoch |

## ⚙️ Konfiguration

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
```

Siehe [docs/CONFIGURATION.md](docs/CONFIGURATION.md) für alle Optionen.

## 📖 Dokumentation

- [Installation](docs/INSTALLATION.md)
- [Konfiguration](docs/CONFIGURATION.md)
- [Tools](docs/TOOLS.md)
- [Security](SECURITY.md)
- [API Reference](docs/API.md)

## 🔐 Sicherheit

- **Shell Whitelist**: Nur vordefinierte Commands
- **File Restriction**: Schreiben nur in /outputs/
- **Code Sandbox**: RestrictedPython mit Timeout
- **Audit Trail**: Jede Aktion wird geloggt

Sicherheitslücken? → [SECURITY.md](SECURITY.md)

## 🤝 Contributing

Beiträge sind willkommen! Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'feat: Add AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

## 📜 Lizenz

**Business Source License 1.1** - siehe [LICENSE](LICENSE)

| Nutzung | Erlaubt? |
|---------|----------|
| Private Nutzung | ✅ Ja |
| Lernen & Forschung | ✅ Ja |
| Evaluation (90 Tage) | ✅ Ja |
| Non-Profit (bis 5 User) | ✅ Ja |
| Forken & Pull Requests | ✅ Ja |
| Produktive Geschäftsnutzung | ❌ Lizenz erforderlich |
| SaaS / Hosting | ❌ Lizenz erforderlich |

**Ab Februar 2030:** Apache License 2.0

## 🏢 Enterprise

Für kommerzielle Nutzung:

- **Axon Pro** - Für Einzelpersonen und kleine Teams
- **Axon Enterprise** - Für Unternehmen

→ [neurovexon.de/pricing](https://neurovexon.de/pricing)

## 💬 Community

- [GitHub Discussions](https://github.com/neurovexon/axon-community/discussions)
- [GitHub Issues](https://github.com/neurovexon/axon-community/issues)
- Email: support@neurovexon.de

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neurovexon/axon-community&type=Date)](https://star-history.com/#neurovexon/axon-community&Date)

---

<p align="center">
  <strong>Axon by NeuroVexon</strong><br>
  <em>Agentic AI - ohne Kontrollverlust.</em>
</p>

<p align="center">
  Made with ❤️ in Germany
</p>
