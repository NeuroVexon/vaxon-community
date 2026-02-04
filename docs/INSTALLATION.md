# Installation

Diese Anleitung beschreibt die Installation von Axon by NeuroVexon.

## Voraussetzungen

### Für Docker (empfohlen)

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM (8GB empfohlen)
- 10GB freier Speicherplatz

### Für manuelle Installation

- Python 3.11+
- Node.js 18+
- npm 9+
- SQLite 3

## Option 1: Docker (Empfohlen)

Die einfachste Methode zur Installation.

```bash
# 1. Repository klonen
git clone https://github.com/neurovexon/axon-community.git
cd axon-community

# 2. Konfiguration erstellen
cp .env.example .env

# 3. Container starten
docker-compose up -d

# 4. Ollama Model laden (einmalig)
docker exec axon-ollama ollama pull llama3.1:8b

# 5. Öffne im Browser
# http://localhost:3000
```

### Docker Compose Services

| Service | Port | Beschreibung |
|---------|------|--------------|
| frontend | 3000 | React UI |
| backend | 8000 | FastAPI Server |
| ollama | 11434 | Lokales LLM |

### GPU-Support (NVIDIA)

Für GPU-Beschleunigung mit Ollama:

```yaml
# In docker-compose.yml, bei ollama service:
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

## Option 2: Manuelle Installation

### Backend

```bash
# 1. In Backend-Verzeichnis wechseln
cd backend

# 2. Virtual Environment erstellen
python -m venv venv

# 3. Aktivieren
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Dependencies installieren
pip install -r requirements.txt

# 5. Konfiguration
cp ../.env.example .env
# .env bearbeiten und anpassen

# 6. Server starten
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
# 1. In Frontend-Verzeichnis wechseln
cd frontend

# 2. Dependencies installieren
npm install

# 3. Development Server starten
npm start

# Oder Production Build:
npm run build
```

### Ollama (für lokale LLMs)

```bash
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download von https://ollama.com/download

# Model laden
ollama pull llama3.1:8b
```

## Konfiguration

### Umgebungsvariablen (.env)

```env
# LLM Provider: ollama, claude, openai
LLM_PROVIDER=ollama

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Claude API (optional)
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI API (optional)
OPENAI_API_KEY=sk-...

# Security (WICHTIG: In Production ändern!)
SECRET_KEY=change-me-in-production
```

### LLM Provider wechseln

**Ollama (lokal, kostenlos):**
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
```

**Claude API:**
```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-sonnet-4-20250514
```

**OpenAI API:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

## Verifizierung

Nach der Installation:

1. Öffne http://localhost:3000
2. Sende eine Test-Nachricht: "Hallo!"
3. Teste ein Tool: "Liste alle Dateien im aktuellen Ordner"
4. Genehmige das Tool im Modal
5. Prüfe das Audit Log

## Troubleshooting

### Backend startet nicht

```bash
# Logs prüfen
docker logs axon-backend

# Oder bei manueller Installation:
cd backend
python main.py
```

### Ollama nicht erreichbar

```bash
# Status prüfen
curl http://localhost:11434/api/tags

# Ollama neu starten
docker restart axon-ollama
```

### Frontend Build-Fehler

```bash
cd frontend
rm -rf node_modules
npm install
npm start
```

### Port bereits belegt

```bash
# Ports ändern in docker-compose.yml oder .env
# Oder bestehende Prozesse finden:
# Windows:
netstat -ano | findstr :3000
# Linux:
lsof -i :3000
```

## Nächste Schritte

- [Konfiguration](CONFIGURATION.md) - Detaillierte Einstellungen
- [Tools](TOOLS.md) - Verfügbare Tools und ihre Verwendung
- [Security](SECURITY.md) - Sicherheitsrichtlinien
