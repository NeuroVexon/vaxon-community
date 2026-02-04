# Axon vs OpenClaw - Vergleich

Warum Axon die bessere Alternative zu OpenClaw ist.

## Was ist OpenClaw?

OpenClaw ist ein virales "Agentic AI" Tool, das KI-Assistenten ermöglicht, selbstständig Aktionen auszuführen - Dateien lesen, im Web suchen, Code ausführen. Das Problem: **Null Kontrolle, null Sicherheit**.

## Die Probleme mit OpenClaw

### 1. Keine Kontrolle

OpenClaw führt Tools automatisch aus. Du siehst oft erst nachher, was passiert ist.

**Axon:** Jede Aktion erfordert deine explizite Genehmigung. Du siehst genau, was ausgeführt werden soll, bevor es passiert.

### 2. Kein Audit-Log

Bei OpenClaw gibt es keine Aufzeichnung, was wann ausgeführt wurde. Compliance? Fehleranalyse? Vergiss es.

**Axon:** Vollständiges Audit-Log mit:
- Timestamp
- Tool-Name und Parameter
- Deine Entscheidung
- Ergebnis oder Fehler
- Ausführungszeit

### 3. Nur Cloud-APIs

OpenClaw funktioniert nur mit Cloud-APIs (OpenAI, etc.). Deine Daten gehen immer über US-Server.

**Axon:**
- Ollama-Support für 100% lokale LLMs
- Keine Daten verlassen deinen Rechner
- DSGVO-konform

### 4. Keine Sicherheit

OpenClaw hat keine Einschränkungen. Die KI kann theoretisch jeden Shell-Befehl ausführen.

**Axon:**
- Shell-Commands nur aus Whitelist
- File-Write nur in /outputs/
- Code-Execution in Sandbox
- Kritische Pfade blockiert

### 5. Chaos-Ökosystem

OpenClaw hat unzählige Forks, viele davon Scams oder Malware. Keine zentrale, vertrauenswürdige Quelle.

**Axon:**
- Professionell entwickelt
- Open Source und auditierbar
- Deutsche Firma, deutsche Docs
- Klare Lizenz (BSL 1.1)

## Feature-Vergleich

| Feature | OpenClaw | Axon |
|---------|----------|------|
| Tool-Ausführung | Automatisch | Mit Genehmigung |
| Audit-Log | ❌ | ✅ Vollständig |
| Lokale LLMs | ❌ | ✅ Ollama |
| Shell-Sicherheit | ❌ | ✅ Whitelist |
| File-Sicherheit | ❌ | ✅ Restricted |
| Code-Sandbox | ❌ | ✅ RestrictedPython |
| DSGVO-konform | ❌ | ✅ On-Premise |
| Open Source | Teilweise | ✅ Vollständig |
| Deutsche Docs | ❌ | ✅ |
| Docker-Support | Teilweise | ✅ One-Command |
| Professioneller Support | ❌ | ✅ (Pro/Enterprise) |

## Risiko-Level Vergleich

### OpenClaw: Alles oder Nichts

```
User: "Lösche alle .tmp Dateien"
OpenClaw: *führt rm -rf aus ohne zu fragen*
```

### Axon: Kontrollierte Macht

```
User: "Lösche alle .tmp Dateien"

┌─────────────────────────────────────┐
│      TOOL-GENEHMIGUNG ERFORDERLICH  │
│                                     │
│  Tool: shell_execute                │
│  Command: find . -name "*.tmp"      │
│           -delete                   │
│  Risiko: HOCH                       │
│                                     │
│  ⚠️ Diese Aktion kann Dateien       │
│     unwiderruflich löschen!         │
│                                     │
│  [Ablehnen]  [Einmal]  [Session]    │
└─────────────────────────────────────┘
```

## Migration von OpenClaw

Wenn du bereits OpenClaw nutzt, ist der Wechsel einfach:

1. Installiere Axon (Docker oder manuell)
2. Konfiguriere deinen LLM-Provider
3. Fertig - gleiche Prompts, mehr Kontrolle

## Fazit

**OpenClaw** ist ein interessantes Experiment, aber für produktiven Einsatz ungeeignet:
- Keine Kontrolle
- Keine Sicherheit
- Keine Compliance

**Axon** bietet die gleiche Power, aber mit Leitplanken:
- Volle Kontrolle über jede Aktion
- Enterprise-ready Sicherheit
- Compliance-fähiges Audit-Log

---

**Tagline:**

> "Agentic AI – ohne Kontrollverlust."

---

## Links

- [Axon GitHub](https://github.com/neurovexon/axon-community)
- [Dokumentation](https://github.com/neurovexon/axon-community/wiki)
- [Installation](INSTALLATION.md)
