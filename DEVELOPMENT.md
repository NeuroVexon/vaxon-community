# DEVELOPMENT.md - Axon by NeuroVexon

> Developer documentation. Read this file completely before working on the project.

---

## 1. Project Overview

**Name:** Axon by NeuroVexon - Community Edition
**Type:** Open-source agentic AI with controlled tool capabilities
**Goal:** The safe, controlled alternative for agentic AI
**Tagline:** "Agentic AI - without losing control."

### Mission

The core feature is the **controlled agent system**: Every tool action is presented to the user for
approval, logged, and traceable. GDPR compliant, on-premise capable.

---

## 2. Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy + aiosqlite (SQLite)
- Pydantic

**Frontend:**
- React 18
- TypeScript
- Tailwind CSS
- Lucide Icons

**LLM:**
- Ollama (local)
- Claude API (Anthropic)
- OpenAI API

---

## 3. Project Structure

```
axon-community/
├── backend/
│   ├── main.py                    # FastAPI Entry Point
│   ├── api/
│   │   ├── chat.py                # Chat Endpoints (send, stream, agent)
│   │   ├── audit.py               # Audit Log Endpoints + CSV Export
│   │   ├── settings.py            # Settings CRUD + Health Check
│   │   ├── tools.py               # Tool Approval + Permissions API
│   │   ├── agents.py              # Multi-Agent CRUD
│   │   ├── scheduler.py           # Scheduled Tasks API
│   │   ├── workflows.py           # Workflow Chains API
│   │   ├── analytics.py           # Dashboard & Cost Tracking
│   │   ├── upload.py              # Document Upload API
│   │   └── mcp.py                 # MCP Server Endpoint
│   ├── agent/
│   │   ├── orchestrator.py        # ⭐ Agent Loop: LLM → Tool → Approval → Execute → Feedback
│   │   ├── agent_manager.py       # Multi-Agent Management + Permissions
│   │   ├── tool_registry.py       # Tool Definitions + LLM Format Conversion
│   │   ├── tool_handlers.py       # Concrete Tool Implementations
│   │   ├── permission_manager.py  # Session-based Permissions + Blocking
│   │   ├── audit_logger.py        # DB-based Audit Logging
│   │   ├── memory.py              # Persistent Memory
│   │   ├── scheduler.py           # Task Scheduler (APScheduler)
│   │   ├── workflows.py           # Workflow Engine
│   │   ├── skills.py              # Skill Manager
│   │   ├── skill_loader.py        # Skill Discovery + Hash Verification
│   │   └── document_handler.py    # Document Extraction + Context Loading
│   ├── llm/
│   │   ├── provider.py            # Base Class + Data Models
│   │   ├── router.py              # Provider Routing + Runtime Switching
│   │   ├── ollama.py              # Ollama Provider
│   │   ├── anthropic_provider.py   # Anthropic Claude Provider
│   │   └── openai_provider.py     # OpenAI Provider
│   ├── integrations/
│   │   ├── telegram.py            # Telegram Bot
│   │   ├── discord.py             # Discord Bot
│   │   └── email.py               # IMAP/SMTP Client
│   ├── mcp/
│   │   ├── server.py              # MCP Server (SSE Transport)
│   │   └── protocol.py            # JSON-RPC 2.0 Message Format
│   ├── sandbox/
│   │   ├── executor.py            # Docker-based Code Sandbox
│   │   └── Dockerfile.sandbox     # Sandbox Container Image
│   ├── db/
│   │   ├── database.py            # Async Engine + Session Management
│   │   └── models.py              # All DB Models
│   └── core/
│       ├── config.py              # Pydantic Settings + Env Config
│       └── security.py            # Path/URL/Shell Validation, Encryption, Rate Limiter
├── frontend/
│   └── src/
│       ├── App.tsx                # Root + Routing
│       ├── components/
│       │   ├── Chat/              # ChatContainer, MessageList, MessageInput, StreamingMessage
│       │   ├── Layout/            # Sidebar, Header, SettingsPanel
│       │   ├── Tools/             # ToolApprovalModal, ToolExecutionBadge
│       │   ├── Monitoring/        # AuditDashboard, AuditTable, AuditExport
│       │   ├── Dashboard/         # Dashboard, AgentStats, CostTracker, TaskOverview
│       │   ├── Agents/            # AgentList, AgentEditor
│       │   ├── Workflows/         # WorkflowList, WorkflowEditor, StepBuilder
│       │   └── Skills/            # SkillList, SkillReview
│       ├── hooks/                 # useChat, useToolApproval, useAudit, useAgents, useWorkflows
│       ├── services/api.ts        # API Client
│       └── types/index.ts         # TypeScript Definitions
├── skills/                        # Community Skills (with skill.yaml + handler.py)
├── docs/
├── docker-compose.yml
└── README.md
```

---

## 4. Code Standards

### Python
- Type hints everywhere
- Async where appropriate
- Pydantic for schemas
- No print(), only logging
- Use security functions from `core/security.py` — do NOT reimplement in handlers

### TypeScript
- Functional components with hooks
- Strict TypeScript
- Tailwind for styling
- German UI texts

### General
- English variables/functions
- German UI texts and docs
- Commits: Conventional Commits (`feat:`, `fix:`, `refactor:`)

---

## 5. Getting Started

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start
```

---

## 6. Branding

- **Primary Color:** Cyan `#00d4ff`
- **Background:** `#0a0a0a` (Dark)
- **Logo:** Futuristic raven with cyan accents
- **Font Display:** Orbitron
- **Font Sans:** Space Grotesk
- **Font Mono:** JetBrains Mono
- **CSS Variables:** `nv-accent`, `nv-black`, `nv-black-lighter`, `nv-gray-light`, `nv-success`

---

## 7. Notes for Developers

- **Always read the affected files first** before making changes
- **No breaking changes** to existing API endpoints — add new endpoints instead
- **German comments** in the code are OK, variables/functions in English
- **Audit trail for everything** — every new action is logged
- **German UI texts** for all new views
- **Encryption** for all new credentials — use `encrypt_value`/`decrypt_value` from `security.py`
- Do not commit `__pycache__` and `.pyc`
- When in doubt: Better to ask than to break things
