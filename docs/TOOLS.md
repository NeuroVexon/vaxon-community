# Tools

Axon offers various tools that the AI can use. Each tool requires explicit user approval.

## Overview

| Tool | Description | Risk |
|------|-------------|------|
| `file_read` | Read a file | Medium |
| `file_write` | Write a file | Medium |
| `file_list` | List a directory | Low |
| `web_fetch` | Fetch a URL | Medium |
| `web_search` | Web search | Low |
| `shell_execute` | Shell command | High |
| `memory_save` | Save a fact to memory | Low |
| `memory_search` | Search memory | Low |
| `memory_delete` | Delete an entry from memory | Low |

## File Tools

### file_read

Reads the content of a file.

**Parameters:**
- `path` (string, required): File path
- `encoding` (string, optional): Encoding (default: utf-8)

**Restrictions:**
- Max file size: 10MB (configurable)
- Blocked paths: `/etc/passwd`, `/etc/shadow`, system directories

**Example:**
```
Read the file config.json
```

### file_write

Writes content to a file.

**Parameters:**
- `filename` (string, required): Filename (saved in /outputs/)
- `content` (string, required): Content to write

**Restrictions:**
- Files are ONLY saved in `/outputs/`
- Path traversal is blocked

**Example:**
```
Create a file named result.txt with the content "Hello World"
```

### file_list

Lists files in a directory.

**Parameters:**
- `path` (string, required): Directory path
- `recursive` (boolean, optional): List recursively (default: false)

**Restrictions:**
- Max 100 entries for recursive listing

**Example:**
```
List all files in the current directory
```

## Web Tools

### web_fetch

Fetches content from a URL.

**Parameters:**
- `url` (string, required): URL
- `method` (string, optional): HTTP method (default: GET)

**Restrictions:**
- Blocked hosts: localhost, 127.0.0.1, internal IPs
- Timeout: 30 seconds
- Max response: 10,000 characters

**Example:**
```
Fetch the page https://example.com
```

### web_search

Searches the web using DuckDuckGo.

**Parameters:**
- `query` (string, required): Search term
- `max_results` (integer, optional): Max results (default: 5)

**Example:**
```
Search the web for "Python FastAPI Tutorial"
```

## Shell Tools

### shell_execute

Executes a shell command.

**Parameters:**
- `command` (string, required): Command to execute

**Restrictions:**
- ONLY whitelisted commands allowed
- Timeout: 30 seconds
- Output max 5,000 characters

**Whitelist:**
```
ls, dir, cat, type, head, tail, wc,
grep, find, date, pwd, echo,
python --version, node --version,
pip list, npm list
```

**Example:**
```
Run "ls -la"
```

## Risk Levels

### Low

- file_list
- web_search

These tools only read information and cannot make changes.

### Medium

- file_read
- file_write
- web_fetch

These tools can read or write data, but only in controlled areas.

### High

- shell_execute

This tool can potentially perform dangerous actions. Despite the whitelist, it should be approved with caution.

## Approval Options

When a tool requests approval:

1. **Allow once**: Only this single execution
2. **Allow for session**: For the entire chat session
3. **Reject**: Tool will not be executed
4. **Never allow**: Tool is permanently blocked (for this session)

## Memory Tools

### memory_save

Saves a fact to the persistent long-term memory.

**Parameters:**
- `key` (string, required): Short form / topic
- `content` (string, required): The actual fact
- `category` (string, optional): Category (e.g., "Preference", "Project")

**No approval required** — Memory tools have low risk.

**Example:**
```
Remember that I prefer Python
```

### memory_search

Searches the long-term memory for relevant facts.

**Parameters:**
- `query` (string, required): Search term

**Example:**
```
What do you know about my programming language?
```

### memory_delete

Deletes an entry from memory.

**Parameters:**
- `key` (string, required): The key of the memory to delete

**Example:**
```
Forget my favorite programming language
```

## Custom Tools

Custom tools can be added in `backend/agent/tool_registry.py`:

```python
self.register(ToolDefinition(
    name="my_custom_tool",
    description="Does something useful",
    description_de="Macht etwas Nützliches",
    parameters={
        "param1": {"type": "string", "required": True},
        "param2": {"type": "integer", "default": 10}
    },
    risk_level=RiskLevel.MEDIUM
))
```

And the handler in `backend/agent/tool_handlers.py`:

```python
async def handle_my_custom_tool(params: dict) -> str:
    param1 = params.get("param1")
    param2 = params.get("param2", 10)
    # Implementation
    return result
```
