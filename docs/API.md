# API Reference

Axon Backend API Dokumentation.

Base URL: `http://localhost:8000/api/v1`

## Authentication

Aktuell keine Authentifizierung erforderlich (Single-User Mode).

## Endpoints

### Chat

#### Send Message

Sendet eine Nachricht und erhält eine Antwort.

```http
POST /chat/send
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Hallo!",
  "session_id": "optional-session-id",
  "system_prompt": "Optional system prompt"
}
```

**Response:**
```json
{
  "session_id": "abc123",
  "message": "Hallo! Wie kann ich dir helfen?",
  "tool_calls": null
}
```

#### Stream Message

Sendet eine Nachricht und streamt die Antwort.

```http
POST /chat/stream
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Erkläre mir Python",
  "session_id": "optional-session-id"
}
```

**Response (SSE Stream):**
```
data: {"type": "text", "content": "Python ist "}
data: {"type": "text", "content": "eine Programmiersprache..."}
data: {"type": "done", "session_id": "abc123"}
```

#### List Conversations

```http
GET /chat/conversations?limit=50
```

**Response:**
```json
[
  {
    "id": "abc123",
    "title": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
]
```

#### Get Conversation

```http
GET /chat/conversations/{conversation_id}
```

**Response:**
```json
{
  "id": "abc123",
  "title": null,
  "system_prompt": null,
  "created_at": "2024-01-15T10:30:00Z",
  "messages": [
    {
      "id": "msg1",
      "role": "user",
      "content": "Hallo!",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg2",
      "role": "assistant",
      "content": "Hallo! Wie kann ich dir helfen?",
      "created_at": "2024-01-15T10:30:01Z"
    }
  ]
}
```

#### Delete Conversation

```http
DELETE /chat/conversations/{conversation_id}
```

**Response:**
```json
{
  "status": "deleted"
}
```

### Tools

#### Approve Tool

Genehmigt eine Tool-Ausführung.

```http
POST /tools/approve
Content-Type: application/json
```

**Request Body:**
```json
{
  "session_id": "abc123",
  "tool": "file_read",
  "params": {"path": "/home/user/file.txt"},
  "decision": "once"
}
```

**Decision Options:**
- `once` - Einmal erlauben
- `session` - Für die gesamte Session erlauben
- `never` - Dauerhaft blockieren

### Audit

#### List Audit Logs

```http
GET /audit?session_id=abc123&event_type=tool_executed&limit=100&offset=0
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | string | Filter by session |
| event_type | string | Filter by event type |
| tool_name | string | Filter by tool |
| limit | integer | Max results (default: 100) |
| offset | integer | Skip results (default: 0) |

**Response:**
```json
[
  {
    "id": "log1",
    "session_id": "abc123",
    "timestamp": "2024-01-15T10:30:00Z",
    "event_type": "tool_executed",
    "tool_name": "file_read",
    "tool_params": {"path": "/home/user/file.txt"},
    "result": "File content here...",
    "error": null,
    "user_decision": "once",
    "execution_time_ms": 15
  }
]
```

**Event Types:**
- `tool_requested` - Tool wurde angefordert
- `tool_approved` - Tool wurde genehmigt
- `tool_rejected` - Tool wurde abgelehnt
- `tool_executed` - Tool wurde ausgeführt
- `tool_failed` - Tool-Ausführung fehlgeschlagen

#### Get Audit Stats

```http
GET /audit/stats?session_id=abc123
```

**Response:**
```json
{
  "total": 42,
  "by_event_type": {
    "tool_requested": 20,
    "tool_approved": 18,
    "tool_executed": 17,
    "tool_failed": 1
  },
  "by_tool": {
    "file_read": 10,
    "web_search": 5,
    "shell_execute": 3
  },
  "avg_execution_time_ms": 125.5
}
```

#### Export Audit Logs

```http
GET /audit/export?format=csv&session_id=abc123
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | `csv` or `json` (default: csv) |
| session_id | string | Filter by session (optional) |

**Response:** CSV file download or JSON array

### Settings

#### Get Settings

```http
GET /settings
```

**Response:**
```json
{
  "app_name": "Axon by NeuroVexon",
  "app_version": "1.0.0",
  "llm_provider": "ollama",
  "theme": "dark",
  "system_prompt": "",
  "available_providers": ["ollama", "claude", "openai"]
}
```

#### Update Settings

```http
PUT /settings
Content-Type: application/json
```

**Request Body:**
```json
{
  "llm_provider": "claude",
  "theme": "dark"
}
```

**Response:**
```json
{
  "status": "updated",
  "changes": {
    "llm_provider": "claude"
  }
}
```

#### Health Check

```http
GET /settings/health
```

**Response:**
```json
{
  "status": "healthy",
  "app_name": "Axon by NeuroVexon",
  "version": "1.0.0",
  "providers": {
    "ollama": true,
    "claude": false,
    "openai": false
  }
}
```

## Error Responses

Alle Endpoints können folgende Fehler zurückgeben:

```json
{
  "detail": "Error message"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Ungültige Parameter |
| 404 | Not Found - Ressource nicht gefunden |
| 500 | Internal Server Error |

## Rate Limiting

Aktuell kein Rate Limiting implementiert. Für Production wird empfohlen, Rate Limiting über einen Reverse Proxy (nginx, Traefik) zu konfigurieren.

## WebSocket

Für Real-Time Tool Approval ist ein WebSocket-Endpoint geplant:

```
ws://localhost:8000/ws/{session_id}
```

*Coming soon in v1.1*
