# Configuration

Detailed configuration options for Axon.

## Environment Variables

### App Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | "Axon by NeuroVexon" | App name |
| `APP_VERSION` | "1.0.0" | Version |
| `DEBUG` | false | Debug mode |

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | "0.0.0.0" | Server host |
| `PORT` | 8000 | Server port |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | "sqlite+aiosqlite:///./axon.db" | Database URL |

### LLM Provider

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | "ollama" | Provider: ollama, claude, openai |

### Ollama

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | "http://localhost:11434" | Ollama API URL |
| `OLLAMA_MODEL` | "llama3.1:8b" | Model |

### Claude (Anthropic)

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | - | API Key |
| `CLAUDE_MODEL` | "claude-sonnet-4-20250514" | Model |

### OpenAI

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | API Key |
| `OPENAI_MODEL` | "gpt-4o" | Model |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | "change-me..." | Secret for sessions (CHANGE THIS!) |

### Tool Execution

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUTS_DIR` | "./outputs" | Output directory for file_write |
| `MAX_FILE_SIZE_MB` | 10 | Max file size for reading |
| `CODE_EXECUTION_TIMEOUT` | 30 | Timeout for code in seconds |
| `CODE_EXECUTION_MEMORY_MB` | 256 | Memory limit for code |

## Shell Whitelist

The allowed shell commands can be customized in `backend/core/config.py`:

```python
shell_whitelist: list[str] = [
    "ls", "dir", "cat", "type", "head", "tail", "wc",
    "grep", "find", "date", "pwd", "echo",
    "python --version", "python3 --version",
    "node --version", "npm --version",
    "pip list", "pip freeze", "npm list"
]
```

## Models

### Recommended Ollama Models

| Model | RAM | Description |
|-------|-----|-------------|
| `llama3.1:8b` | 8GB | Good balance |
| `llama3.1:70b` | 48GB | Best quality |
| `mistral:7b` | 8GB | Fast |
| `codellama:13b` | 16GB | Good for code |
| `mixtral:8x7b` | 32GB | MoE, very good |

```bash
# Install model
ollama pull llama3.1:8b

# Set in .env
OLLAMA_MODEL=llama3.1:8b
```

### Claude Models

| Model | Description |
|-------|-------------|
| `claude-sonnet-4-20250514` | Recommended |
| `claude-opus-4-20250514` | Best quality |

### OpenAI Models

| Model | Description |
|-------|-------------|
| `gpt-4o` | Recommended |
| `gpt-4-turbo` | Faster |
| `gpt-3.5-turbo` | Budget-friendly |

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

- [ ] `SECRET_KEY` changed
- [ ] `DEBUG=false`
- [ ] HTTPS enabled
- [ ] Firewall configured
- [ ] Backup set up
- [ ] Monitoring set up
- [ ] Log rotation configured
