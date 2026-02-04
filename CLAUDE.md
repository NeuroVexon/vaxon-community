# CLAUDE.md - Axon by NeuroVexon

> Instruktionsdatei für Claude Code. Lies diese Datei vollständig bevor du am Projekt arbeitest.

---

## 1. Projekt-Übersicht

**Name:** Axon by NeuroVexon - Community Edition
**Typ:** Open-Source KI-Assistent mit kontrollierten Agent-Fähigkeiten
**Ziel:** Die sichere, kontrollierte Alternative für Agentic AI
**Tagline:** "Agentic AI - ohne Kontrollverlust."

### Mission

Axon bietet Agentic AI mit Leitplanken:
- Jede Aktion wird bestätigt, geloggt, nachvollzogen
- DSGVO-konform, On-Premise möglich
- Open Source und transparent

---

## 2. Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy + SQLite
- Pydantic

**Frontend:**
- React 18
- TypeScript
- Tailwind CSS
- Lucide Icons

**LLM:**
- Ollama (lokal)
- Claude API
- OpenAI API

---

## 3. Projektstruktur

```
axon-community/
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── chat.py
│   │   ├── audit.py
│   │   └── settings.py
│   ├── agent/
│   │   ├── orchestrator.py
│   │   ├── tool_registry.py
│   │   ├── tool_handlers.py
│   │   ├── permission_manager.py
│   │   └── audit_logger.py
│   ├── llm/
│   │   ├── provider.py
│   │   ├── router.py
│   │   ├── ollama.py
│   │   ├── claude.py
│   │   └── openai_provider.py
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   └── core/
│       └── config.py
├── frontend/
│   └── src/
│       ├── components/
│       ├── hooks/
│       └── services/
├── docs/
├── docker-compose.yml
└── README.md
```

---

## 4. Code Standards

### Python
- Type Hints überall
- Async wo sinnvoll
- Pydantic für Schemas
- Keine print(), nur logging

### TypeScript
- Functional Components
- Strict TypeScript
- Tailwind für Styling

### Allgemein
- Englische Variablen/Funktionen
- Deutsche UI-Texte
- Deutsche Docs

---

## 5. Starten

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start
```

---

## 6. Branding

- **Primärfarbe:** Cyan #00d4ff
- **Hintergrund:** #0a0a0a (Dark)
- **Logo:** Futuristischer Rabe mit Cyan-Akzenten
- **Font Display:** Orbitron
- **Font Sans:** Space Grotesk
- **Font Mono:** JetBrains Mono
