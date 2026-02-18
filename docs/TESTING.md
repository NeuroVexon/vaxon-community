# Axon — Testing

Axon uses **pytest** with pytest-asyncio for automated tests.

## Quick Start

```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Test Categories

### Unit Tests (locally runnable, no external dependencies)

| File | Tests | Description |
|------|-------|-------------|
| `test_security.py` | 37 | Path traversal, SSRF, shell injection, encryption, sanitization |
| `test_tools.py` | 9 | ToolRegistry, PermissionManager |
| `test_models.py` | 16 | All 11 DB models: creation, defaults, relationships |
| `test_memory.py` | 18 | MemoryManager CRUD, search, prompt building, embedding serialization |
| `test_agents.py` | 25 | AgentManager CRUD, defaults, permissions, risk levels |
| `test_embeddings.py` | 14 | Cosine similarity, EmbeddingProvider behavior |
| `test_rate_limiter.py` | 7 | Rate limiting: limits, windows, reset |
| `test_tool_handlers.py` | 36 | All tool handlers: security, parameters, error handling |
| `test_orchestrator.py` | 28 | Agent loop: approval flow, auto-approve, permissions, iterations, audit |

### Integration Tests (server dependencies required)

| File | Tests | Description |
|------|-------|-------------|
| `test_api.py` | 5 | Health, settings, audit endpoints |
| `test_api_extended.py` | 22 | Agents, memory, conversations, analytics API |

Integration tests are automatically skipped when dependencies are missing (e.g., `apscheduler`).

**Total: 230 tests** (203 unit + 27 integration)

## Architecture

### Fixtures (`conftest.py`)

```python
# In-memory SQLite for isolated tests
@pytest.fixture
async def db():
    # Creates temporary DB, rollback after each test

# Mock for Ollama embedding provider
@pytest.fixture
def mock_embedding():
    # Prevents Ollama dependency in tests

# FastAPI TestClient
@pytest.fixture
def client():
    # TestClient for API endpoint tests
```

### Patterns

**Async DB Tests:**
```python
@pytest.mark.asyncio
async def test_create_memory(self, db, mock_embedding):
    manager = MemoryManager(db)
    mem = await manager.add("Key", "Value")
    assert mem.key == "Key"
```

**Security Tests (no DB needed):**
```python
def test_path_traversal_blocked(self):
    assert validate_path("../../etc/passwd") is False
```

**API Integration Tests:**
```python
def test_list_agents(self, client):
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
```

## What Is Tested?

### Security (OWASP Top 10)

- **Path Traversal** — `../../etc/passwd`, Windows paths, sensitive files (.env, .ssh, credentials)
- **SSRF** — localhost, 127.0.0.1, internal IPs (10.x, 172.x, 192.168.x), AWS IMDS (169.254.169.254), IPv6
- **Command Injection** — Chaining (`&&`, `||`, `;`, `|`), substitution (`` ` ``, `$()`, `${}`), whitelist
- **Encryption** — Fernet roundtrip, empty values, invalid ciphertexts
- **Sanitization** — Filenames: path separators, leading dots, null bytes, length limits

### Agent System

- Default agents are correctly created (Assistant, Research, System)
- CRUD: Create, read, update, delete
- Default agent cannot be deleted
- Tool permissions: `allowed_tools`, `auto_approve_tools`
- Risk levels: low < medium < high < critical

### Memory System

- CRUD: Add, read, update (upsert), delete
- Key/content truncation on overflow
- ILIKE search (fallback without embeddings)
- Case-insensitive search
- Prompt building: Markdown and plain text format
- Embedding serialization: float32 roundtrip

### Rate Limiting

- Allows requests up to the limit
- Blocks on exceeding the limit
- Different keys are independent
- Window expiry: old requests do not count
- Reset clears the counter

### Tool Handlers

- **file_read**: Existing files, missing parameters, path traversal, sensitive files blocked
- **file_write**: Creation, correct content, missing parameters, path traversal sanitized
- **file_list**: Directory listing, type detection, blocked paths
- **web_fetch**: SSRF protection (localhost, internal IPs, AWS IMDS, Docker, file://)
- **shell_execute**: Command injection (&&, ||, ;, |, backticks, $() substitution), whitelist
- **memory_save/search/delete**: Parameter validation, DB session check, CRUD

### Orchestrator (Agent Loop)

- **Basic Flow**: Text response without tools, empty content, LLM receives tool definitions
- **Auto-Approve**: Tools with `requires_approval=False` are executed automatically
- **Approval Flow**: Approval, rejection, `approval_id` and `risk_level` in the request
- **Session Permissions**: Second call skips approval after session approval
- **Agent Permissions**: Blocked tools, agent auto-approve, default agent allows everything
- **Iterations**: Max iterations warning, custom limits, multi-tool responses
- **Error Handling**: ToolExecutionError, unexpected exceptions
- **Audit Logging**: Tool requests, executions, rejections, errors are logged

### API Endpoints

- Health check: `/` and `/health`
- Settings: App info, provider status, API key masking
- Agents: CRUD, default protection
- Memory: CRUD, search
- Analytics: Overview statistics

## CI

Tests run automatically in the CI workflow (`.github/workflows/ci.yml`):

```yaml
- name: Run tests
  run: |
    cd backend
    pytest tests/ -v || echo "No tests found yet"
```

## Running Tests on the Server

```bash
ssh root@78.46.106.190
cd /opt/axon/backend
pip3 install pytest pytest-asyncio
python3 -m pytest tests/ -v
```
