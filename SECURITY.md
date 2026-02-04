# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

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

## Sicherheitsmaßnahmen in Axon

### Tool Execution

- **Shell Whitelist**: Nur vordefinierte Commands sind erlaubt
- **File Write Restriction**: Schreiben nur in `/outputs/` möglich
- **Code Sandbox**: Python-Code läuft in RestrictedPython mit Timeout
- **Explicit Approval**: Jede Tool-Ausführung erfordert User-Bestätigung

### Data Protection

- **Local First**: Alle Daten bleiben lokal (SQLite)
- **No Telemetry**: Keine Daten werden an externe Server gesendet
- **Audit Log**: Alle Aktionen werden protokolliert

### API Security

- **CORS**: Strikte Origin-Kontrolle
- **Input Validation**: Pydantic-Schemas für alle Inputs
- **Rate Limiting**: Empfohlen für Production

## Best Practices für Deployment

### Production Checklist

- [ ] `SECRET_KEY` ändern (generiere mit `openssl rand -hex 32`)
- [ ] `DEBUG=false` setzen
- [ ] HTTPS aktivieren (Reverse Proxy)
- [ ] Firewall konfigurieren
- [ ] Regelmäßige Updates installieren

### Empfohlene Reverse Proxy Config (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name axon.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Bekannte Einschränkungen

1. **Code Execution**: Trotz Sandbox können bestimmte Angriffsvektoren existieren. Für hochsensible Umgebungen empfehlen wir, `code_execute` zu deaktivieren.

2. **Web Fetch**: URLs werden nicht vollständig validiert. Interne Netzwerk-URLs (localhost, 127.0.0.1) sind blockiert, aber andere interne IPs könnten erreichbar sein.

3. **File Read**: Systemdateien sind blockiert, aber die Liste ist nicht erschöpfend.

## Responsible Disclosure

Wir erkennen Sicherheitsforscher an, die Sicherheitslücken verantwortungsvoll melden. Nach Absprache werden wir:

- Deinen Namen in den Release Notes erwähnen (falls gewünscht)
- Ein Dankeschön aussprechen

---

Vielen Dank, dass du Axon sicherer machst! 🛡️
