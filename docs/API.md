# API Reference

Axon Backend API documentation.

Base URL: `http://localhost:8000/api/v1`

## Authentication

Currently no authentication required (single-user mode).

## Endpoints

### Chat

#### Send Message

Sends a message and receives a response.

```http
POST /chat/send
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Hello!",
  "session_id": "optional-session-id",
  "system_prompt": "Optional system prompt"
}
```

**Response:**
```json
{
  "session_id": "abc123",
  "message": "Hello! How can I help you?",
  "tool_calls": null
}
```

#### Stream Message

Sends a message and streams the response.

```http
POST /chat/stream
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Explain Python to me",
  "session_id": "optional-session-id"
}
```

**Response (SSE Stream):**
```
data: {"type": "text", "content": "Python is "}
data: {"type": "text", "content": "a programming language..."}
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
      "content": "Hello!",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg2",
      "role": "assistant",
      "content": "Hello! How can I help you?",
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

Approves a tool execution.

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
- `once` - Allow once
- `session` - Allow for the entire session
- `never` - Block permanently

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
- `tool_requested` - Tool was requested
- `tool_approved` - Tool was approved
- `tool_rejected` - Tool was rejected
- `tool_executed` - Tool was executed
- `tool_failed` - Tool execution failed

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

All endpoints can return the following errors:

```json
{
  "detail": "Error message"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

## Rate Limiting

Currently no rate limiting implemented. For production, it is recommended to configure rate limiting via a reverse proxy (nginx, Traefik).

## WebSocket

A WebSocket endpoint for real-time tool approval is planned:

```
ws://localhost:8000/ws/{session_id}
```

*Coming soon in v1.1*
