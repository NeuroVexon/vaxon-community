# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :white_check_mark: (Security Fixes) |

## Reporting a Vulnerability

We take the security of Axon very seriously. If you find a security vulnerability, please report it responsibly.

### How to Report?

**Please do NOT create a public GitHub Issue for security vulnerabilities.**

Instead, send an email to: **service@neurovexon.com**

Please include the following information:

1. **Description** of the vulnerability
2. **Steps to reproduce**
3. **Affected versions**
4. **Potential impact**
5. **Suggested fix** (if available)

### What Happens After Reporting?

1. **Acknowledgment** - We will confirm receipt within 48 hours
2. **Assessment** - We will assess the severity and impact
3. **Fix** - We will develop a fix
4. **Disclosure** - After the fix, we will publish a Security Advisory

### Timeline

- Critical vulnerabilities: Fix within 7 days
- High vulnerabilities: Fix within 14 days
- Medium vulnerabilities: Fix within 30 days

## Security Architecture

### Tool Execution — Approval System

- **Explicit Approval**: Every tool execution requires user confirmation
- **Per-Agent Permissions**: Each agent has its own allowed tools and risk levels
- **Auto-Approve**: Only configurable for low-risk tools (e.g., `web_search`)
- **Session-based Permissions**: "Allow once" or "Allow for session"
- **Audit Trail**: Every request, approval, execution, and rejection is logged

### Tool Security

- **Shell Whitelist**: Only predefined commands are allowed, chaining is blocked (`&&`, `||`, `;`, `|`, backticks, `$()`)
- **File Write Restriction**: Writing only possible in `/outputs/`
- **Path Traversal Protection**: `validate_path()` blocks `..`, absolute paths, symlinks
- **SSRF Protection**: `validate_url()` blocks localhost, internal IPs, AWS IMDS
- **Skills Gate**: SHA-256 hash verification, automatic revocation on file changes

### Code Sandbox (Docker)

- **Network Isolation**: `--network none` — no internet, no LAN
- **Resource Limits**: 256 MB RAM, 0.5 CPU, 60s timeout
- **Read-only Filesystem**: Container cannot write anything persistently
- **Unprivileged User**: Code runs as `sandbox` user, not root
- **No Host Access**: No volume mounts to the host filesystem
- **Max 3 concurrent containers**, max 10,000 characters output
- **Always Approval**: `code_execute` is risk_level: high, always requires approval

### Email Security

- **Read-Only Inbox**: Axon can read and search emails, but CANNOT delete, move, or mark them as read
- **Send with Approval**: Email sending always shows recipient, subject, and body for approval
- **Encrypted Credentials**: IMAP/SMTP passwords are stored encrypted with Fernet in the database

### MCP Server

- **Bearer Token Auth**: Access only with configured token
- **Rate Limiting**: Protection against abuse
- **Approval System**: External AI clients (Claude Desktop, Cursor) go through the same approval system
- **Disabled by Default**: `MCP_ENABLED=false`

### Scheduled Tasks

- **Max 10 active tasks**: Prevents resource abuse
- **Timeout 5 minutes**: No task runs indefinitely
- **Max 1/min per task**: Rate limiting against spam
- **Approval Gate**: Optional approval before each execution
- **Errors in Audit Log**: Every error is logged

### Data Protection

- **Local First**: All data stays local (SQLite)
- **No Telemetry**: No data is sent to external servers
- **Encrypted API Keys**: Fernet encryption in the SQLite database
- **Audit Log**: All actions are logged and exportable as CSV
- **GDPR Compliant**: On-premise operation possible, no cloud dependency

### API Security

- **CORS**: Strict origin control
- **Input Validation**: Pydantic schemas for all inputs
- **Rate Limiting**: Recommended for production (Nginx)
- **Basic Auth**: For public deployments via reverse proxy

### CLI Security

- **Local Credentials**: Auth data in `~/.axon/config.json` (user-readable only)
- **HTTPS**: Supports TLS connections to the server
- **No Secrets in Output**: Passwords are displayed masked

## Best Practices for Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` (generate with `openssl rand -hex 32`)
- [ ] Set `DEBUG=false`
- [ ] Enable HTTPS (reverse proxy with SSL)
- [ ] Basic Auth or other auth system in front of the frontend
- [ ] Configure firewall (only 80/443 public)
- [ ] Only enable MCP server if needed (`MCP_ENABLED=false`)
- [ ] Only enable code sandbox if needed (`SANDBOX_ENABLED=false`)
- [ ] Only enable email if needed (`EMAIL_ENABLED=false`)
- [ ] Install regular updates
- [ ] Review audit logs regularly

### Recommended Reverse Proxy Config (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name axon.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Basic Auth for public instances
    auth_basic "Axon";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        auth_basic off;  # Handle API auth separately
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE Streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

## Known Limitations

1. **Code Sandbox**: Docker-based with network isolation. For highly sensitive environments, `SANDBOX_ENABLED=false` can be set.

2. **Web Fetch**: SSRF protection blocks localhost and private IPs. Other internal services may be reachable via hostnames — network segmentation recommended.

3. **File Read**: System files and known sensitive paths are blocked. The blocklist is not exhaustive.

4. **SQLite**: Single-writer — under high load, `database is locked` errors may occur. WAL mode and `busy_timeout=30000` are configured.

## Responsible Disclosure

We acknowledge security researchers who responsibly report vulnerabilities. Upon agreement, we will:

- Mention your name in the release notes (if desired)
- Express our gratitude

---

Thank you for helping make Axon more secure!
