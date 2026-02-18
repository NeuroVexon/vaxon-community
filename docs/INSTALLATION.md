# Installation

This guide describes the installation of Axon by NeuroVexon.

## Prerequisites

### For Docker (recommended)

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM (8GB recommended)
- 10GB free disk space

### For Manual Installation

- Python 3.11+
- Node.js 18+
- npm 9+
- SQLite 3

## Option 1: Docker (Recommended)

The simplest method for installation.

```bash
# 1. Clone repository
git clone https://github.com/NeuroVexon/axon-community.git
cd axon-community

# 2. Create configuration
cp .env.example .env

# 3. Start containers
docker-compose up -d

# 4. Pull Ollama model (one-time)
docker exec axon-ollama ollama pull llama3.1:8b

# 5. Open in browser
# http://localhost:3000
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | React UI |
| backend | 8000 | FastAPI Server |
| ollama | 11434 | Local LLM |

### GPU Support (NVIDIA)

For GPU acceleration with Ollama:

```yaml
# In docker-compose.yml, at the ollama service:
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

## Option 2: Manual Installation

### Backend

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configuration
cp ../.env.example .env
# Edit .env and customize

# 6. Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm start

# Or production build:
npm run build
```

### Ollama (for local LLMs)

```bash
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download

# Pull model
ollama pull llama3.1:8b
```

## Configuration

### Environment Variables (.env)

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

# Security (IMPORTANT: Change in production!)
SECRET_KEY=change-me-in-production
```

### Switch LLM Provider

**Ollama (local, free):**
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

## Verification

After installation:

1. Open http://localhost:3000
2. Send a test message: "Hello!"
3. Test a tool: "List all files in the current directory"
4. Approve the tool in the modal
5. Check the audit log

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker logs axon-backend

# Or for manual installation:
cd backend
python main.py
```

### Ollama Not Reachable

```bash
# Check status
curl http://localhost:11434/api/tags

# Restart Ollama
docker restart axon-ollama
```

### Frontend Build Errors

```bash
cd frontend
rm -rf node_modules
npm install
npm start
```

### Port Already in Use

```bash
# Change ports in docker-compose.yml or .env
# Or find existing processes:
# Windows:
netstat -ano | findstr :3000
# Linux:
lsof -i :3000
```

## Next Steps

- [Configuration](CONFIGURATION.md) - Detailed settings
- [Tools](TOOLS.md) - Available tools and their usage
- [Security](SECURITY.md) - Security guidelines
