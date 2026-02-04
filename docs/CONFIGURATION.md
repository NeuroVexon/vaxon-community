# Konfiguration

Detaillierte Konfigurationsoptionen für Axon.

## Umgebungsvariablen

### App Settings

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `APP_NAME` | "Axon by NeuroVexon" | App-Name |
| `APP_VERSION` | "1.0.0" | Version |
| `DEBUG` | false | Debug-Modus |

### Server

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `HOST` | "0.0.0.0" | Server-Host |
| `PORT` | 8000 | Server-Port |

### Database

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `DATABASE_URL` | "sqlite+aiosqlite:///./axon.db" | Datenbank-URL |

### LLM Provider

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `LLM_PROVIDER` | "ollama" | Provider: ollama, claude, openai |

### Ollama

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `OLLAMA_BASE_URL` | "http://localhost:11434" | Ollama API URL |
| `OLLAMA_MODEL` | "llama3.1:8b" | Modell |

### Claude (Anthropic)

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `ANTHROPIC_API_KEY` | - | API Key |
| `CLAUDE_MODEL` | "claude-sonnet-4-20250514" | Modell |

### OpenAI

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `OPENAI_API_KEY` | - | API Key |
| `OPENAI_MODEL` | "gpt-4o" | Modell |

### Security

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `SECRET_KEY` | "change-me..." | Secret für Sessions (ÄNDERN!) |

### Tool Execution

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `OUTPUTS_DIR` | "./outputs" | Output-Verzeichnis für file_write |
| `MAX_FILE_SIZE_MB` | 10 | Max. Dateigröße zum Lesen |
| `CODE_EXECUTION_TIMEOUT` | 30 | Timeout für Code in Sekunden |
| `CODE_EXECUTION_MEMORY_MB` | 256 | Memory-Limit für Code |

## Shell Whitelist

Die erlaubten Shell-Commands können in `backend/core/config.py` angepasst werden:

```python
shell_whitelist: list[str] = [
    "ls", "dir", "cat", "type", "head", "tail", "wc",
    "grep", "find", "date", "pwd", "echo",
    "python --version", "python3 --version",
    "node --version", "npm --version",
    "pip list", "pip freeze", "npm list"
]
```

## Modelle

### Empfohlene Ollama Modelle

| Modell | RAM | Beschreibung |
|--------|-----|--------------|
| `llama3.1:8b` | 8GB | Gute Balance |
| `llama3.1:70b` | 48GB | Beste Qualität |
| `mistral:7b` | 8GB | Schnell |
| `codellama:13b` | 16GB | Gut für Code |
| `mixtral:8x7b` | 32GB | MoE, sehr gut |

```bash
# Modell installieren
ollama pull llama3.1:8b

# In .env setzen
OLLAMA_MODEL=llama3.1:8b
```

### Claude Modelle

| Modell | Beschreibung |
|--------|--------------|
| `claude-sonnet-4-20250514` | Empfohlen |
| `claude-opus-4-20250514` | Beste Qualität |

### OpenAI Modelle

| Modell | Beschreibung |
|--------|--------------|
| `gpt-4o` | Empfohlen |
| `gpt-4-turbo` | Schneller |
| `gpt-3.5-turbo` | Günstig |

## Production Setup

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name axon.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name axon.example.com;

    ssl_certificate /etc/letsencrypt/live/axon.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/axon.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service

```ini
# /etc/systemd/system/axon-backend.service
[Unit]
Description=Axon Backend
After=network.target

[Service]
Type=simple
User=axon
WorkingDirectory=/opt/axon/backend
Environment=PATH=/opt/axon/backend/venv/bin
ExecStart=/opt/axon/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Production Checklist

- [ ] `SECRET_KEY` geändert
- [ ] `DEBUG=false`
- [ ] HTTPS aktiviert
- [ ] Firewall konfiguriert
- [ ] Backup eingerichtet
- [ ] Monitoring eingerichtet
- [ ] Log-Rotation konfiguriert
