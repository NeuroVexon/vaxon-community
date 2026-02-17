# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :white_check_mark: (Security Fixes) |

## Reporting a Vulnerability

Wir nehmen die Sicherheit von Axon sehr ernst. Wenn du eine Sicherheitslücke findest, melde sie bitte verantwortungsvoll.

### Wie melden?

**Bitte erstelle KEIN öffentliches GitHub Issue für Sicherheitslücken.**

Stattdessen sende eine E-Mail an: **security@neurovexon.de**

Bitte füge folgende Informationen hinzu:

1. **Beschreibung** der Sicherheitslücke
2. **Schritte zur Reproduktion**
3. **Betroffene Versionen**
4. **Mögliche Auswirkungen**
5. **Vorgeschlagene Lösung** (falls vorhanden)

### Was passiert nach der Meldung?

1. **Bestätigung** - Wir bestätigen den Erhalt innerhalb von 48 Stunden
2. **Bewertung** - Wir bewerten die Schwere und Auswirkung
3. **Fix** - Wir entwickeln einen Fix
4. **Disclosure** - Nach dem Fix veröffentlichen wir ein Security Advisory

### Zeitrahmen

- Kritische Sicherheitslücken: Fix innerhalb von 7 Tagen
- Hohe Sicherheitslücken: Fix innerhalb von 14 Tagen
- Mittlere Sicherheitslücken: Fix innerhalb von 30 Tagen

## Sicherheitsarchitektur

### Tool Execution — Approval-System

- **Explicit Approval**: Jede Tool-Ausführung erfordert User-Bestätigung
- **Per-Agent Permissions**: Jeder Agent hat eigene erlaubte Tools und Risiko-Level
- **Auto-Approve**: Nur fuer risikoarme Tools konfigurierbar (z.B. `web_search`)
- **Session-basierte Permissions**: "Allow once" oder "Allow for session"
- **Audit-Trail**: Jede Anfrage, Genehmigung, Ausfuehrung und Ablehnung wird geloggt

### Tool-Sicherheit

- **Shell Whitelist**: Nur vordefinierte Commands sind erlaubt, Chaining blockiert (`&&`, `||`, `;`, `|`, Backticks, `$()`)
- **File Write Restriction**: Schreiben nur in `/outputs/` moeglich
- **Path-Traversal Schutz**: `validate_path()` blockiert `..`, absolute Pfade, Symlinks
- **SSRF-Schutz**: `validate_url()` blockiert localhost, interne IPs, AWS IMDS
- **Skills Gate**: SHA-256 Hash-Pruefung, automatische Revocation bei Dateiänderungen

### Code-Sandbox (Docker)

- **Netzwerk-Isolation**: `--network none` — kein Internet, kein LAN
- **Resource-Limits**: 256 MB RAM, 0.5 CPU, 60s Timeout
- **Read-only Filesystem**: Container kann nichts persistent schreiben
- **Unprivilegierter User**: Code laeuft als `sandbox` User, nicht als root
- **Kein Host-Zugriff**: Keine Volume-Mounts zum Host-Filesystem
- **Max 3 gleichzeitige Container**, max 10.000 Zeichen Output
- **Immer Approval**: `code_execute` ist risk_level: high, erfordert immer Genehmigung

### E-Mail-Sicherheit

- **Read-Only Inbox**: Axon kann E-Mails lesen und suchen, aber NICHT loeschen, verschieben oder als gelesen markieren
- **Send mit Approval**: E-Mail-Versand zeigt immer Empfaenger, Betreff und Text zur Genehmigung
- **Verschluesselte Credentials**: IMAP/SMTP-Passwoerter werden mit Fernet verschluesselt in der DB gespeichert

### MCP-Server

- **Bearer Token Auth**: Zugriff nur mit konfiguriertem Token
- **Rate Limiting**: Schutz gegen Missbrauch
- **Approval-System**: Externe AI-Clients (Claude Desktop, Cursor) laufen durch das gleiche Approval-System
- **Standardmaessig deaktiviert**: `MCP_ENABLED=false`

### Scheduled Tasks

- **Max 10 aktive Tasks**: Verhindert Ressourcen-Missbrauch
- **Timeout 5 Minuten**: Kein Task laeuft unbegrenzt
- **Max 1/min pro Task**: Rate-Limiting gegen Spam
- **Approval-Gate**: Optional Genehmigung vor jeder Ausfuehrung
- **Fehler im Audit-Log**: Jeder Fehler wird protokolliert

### Data Protection

- **Local First**: Alle Daten bleiben lokal (SQLite)
- **No Telemetry**: Keine Daten werden an externe Server gesendet
- **Verschluesselte API-Keys**: Fernet-Verschluesselung in der SQLite DB
- **Audit Log**: Alle Aktionen werden protokolliert und als CSV exportierbar
- **DSGVO-konform**: On-Premise Betrieb moeglich, keine Cloud-Abhaengigkeit

### API Security

- **CORS**: Strikte Origin-Kontrolle
- **Input Validation**: Pydantic-Schemas fuer alle Inputs
- **Rate Limiting**: Empfohlen fuer Production (Nginx)
- **Basic Auth**: Fuer oeffentliche Deployments via Reverse Proxy

### CLI-Sicherheit

- **Credentials lokal**: Auth-Daten in `~/.axon/config.json` (nur User-lesbar)
- **HTTPS**: Unterstuetzt TLS-Verbindungen zum Server
- **Keine Secrets im Output**: Passwoerter werden maskiert angezeigt

## Best Practices fuer Deployment

### Production Checklist

- [ ] `SECRET_KEY` aendern (generiere mit `openssl rand -hex 32`)
- [ ] `DEBUG=false` setzen
- [ ] HTTPS aktivieren (Reverse Proxy mit SSL)
- [ ] Basic Auth oder anderes Auth-System vor dem Frontend
- [ ] Firewall konfigurieren (nur 80/443 oeffentlich)
- [ ] MCP-Server nur aktivieren wenn benoetigt (`MCP_ENABLED=false`)
- [ ] Code-Sandbox nur aktivieren wenn benoetigt (`SANDBOX_ENABLED=false`)
- [ ] E-Mail nur aktivieren wenn benoetigt (`EMAIL_ENABLED=false`)
- [ ] Regelmaessige Updates installieren
- [ ] Audit-Logs regelmaessig pruefen

### Empfohlene Reverse Proxy Config (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name axon.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Basic Auth fuer oeffentliche Instanzen
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
        auth_basic off;  # API Auth separat handhaben
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE-Streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

## Bekannte Einschraenkungen

1. **Code-Sandbox**: Docker-basiert mit Netzwerk-Isolation. Fuer hochsensible Umgebungen kann `SANDBOX_ENABLED=false` gesetzt werden.

2. **Web Fetch**: SSRF-Schutz blockiert localhost und private IPs. Andere interne Dienste koennten ueber Hostnamen erreichbar sein — Netzwerk-Segmentierung empfohlen.

3. **File Read**: Systemdateien und bekannte sensitive Pfade sind blockiert. Die Blocklist ist nicht erschoepfend.

4. **SQLite**: Single-Writer — bei hoher Last koennen `database is locked` Fehler auftreten. WAL-Modus und `busy_timeout=30000` sind konfiguriert.

## Responsible Disclosure

Wir erkennen Sicherheitsforscher an, die Sicherheitsluecken verantwortungsvoll melden. Nach Absprache werden wir:

- Deinen Namen in den Release Notes erwaehnen (falls gewuenscht)
- Ein Dankeschoen aussprechen

---

Vielen Dank, dass du Axon sicherer machst!
