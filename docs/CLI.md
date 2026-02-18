# Axon CLI — Documentation

The Axon CLI is a standalone terminal client for Axon. It communicates via HTTP with the Axon backend and offers SSE streaming, tool approval, and pipe support.

## Installation

### Option 1: pip install (recommended)

```bash
cd axon-community
pip install -e ./cli
axon --help
```

This registers the `axon` command globally.

### Option 2: Run directly

```bash
python cli/axon_cli.py --help
```

### Option 3: Alias (PowerShell)

```powershell
Set-Alias axon "python C:\path\to\axon-community\cli\axon_cli.py"
```

### Option 3: Alias (Bash/Zsh)

```bash
alias axon="python3 /path/to/axon-community/cli/axon_cli.py"
```

### Dependencies

- Python 3.10+
- `typer` >= 0.9.0 — CLI framework
- `httpx` >= 0.27.0 — HTTP client with streaming
- `rich` >= 13.0.0 — Colored terminal output

## Configuration

The CLI stores its configuration in `~/.axon/config.json`. The file is automatically created with defaults on first startup.

### Set Server URL

```bash
axon config set url http://localhost:8000        # Local
axon config set url https://axon.example.com     # Remote
```

### Basic Auth (for deployments with Nginx auth)

```bash
axon config set auth username:password
```

### Language

```bash
axon config set language de    # German (default)
axon config set language en    # English
```

### Show Configuration

```bash
axon config show
```

```
+------------------------------- Configuration ------------------------------+
| URL:      https://axon.example.com                                         |
| Auth:     username:****                                                    |
| Language: de                                                               |
+----------------------------------------------------------------------------+
```

## Commands

### axon chat — Send Message

```bash
# Simple message
axon chat "What is Python?"

# With specific agent
axon chat --agent Research "Search for FastAPI tutorials"

# Continue session (use session ID from previous chat)
axon chat --session abc123 "And what else?"
```

The response is displayed live via SSE streaming — word by word, just like in the web UI.

### Pipe Support

The CLI automatically detects whether input comes through a pipe:

```bash
# Send file content
cat README.md | axon chat
type README.md | axon chat          # Windows CMD

# Analyze command output
git log --oneline -10 | axon chat
docker ps | axon chat --agent System

# Scripting
echo "Summarize: $(cat report.txt)" | axon chat
```

### Tool Approval

When the agent wants to use a tool, a colored panel appears:

```
+------------------------------- Tool Request --------------------------------+
| Tool:   web_search                                                          |
| Risk:   low                                                                 |
|   Searches the web using DuckDuckGo                                         |
|                                                                             |
|   query: FastAPI performance tips                                           |
+-----------------------------------------------------------------------------+
[A]llow  [S]ession  [R]eject (a):
```

- **A (Allow)**: Execute tool once
- **S (Session)**: Always allow tool for this session
- **R (Reject)**: Reject tool

The risk level is color-coded: green (low), yellow (medium), red (high).

### axon (REPL Mode)

Without a subcommand, interactive mode starts:

```bash
axon
```

```
+------------ Axon CLI v1.0.0 — Connected to https://axon.example.com ------+
Type a message or /help for help. Exit with /exit or Ctrl+C.

> Hello!
Hello! How can I help you?

> /agent Research
Agent switched to: Research

> Search for Python 3.13 features
[SSE Streaming...]

> /new
New session started.

> /exit
Goodbye!
```

**REPL Commands:**

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/new` | Start new session |
| `/agent <name>` | Switch agent |
| `/exit` or `Ctrl+C` | Quit |

### axon agents — Manage Agents

```bash
# List all agents
axon agents
```

```
                                    Agents
+----------+-------------------------+--------+------------+---------+-------+
| Name     | Description             | Model  | Risk Max   | Default | Active|
|----------+-------------------------+--------+------------+---------+-------|
| Assistant| General AI assistant    | -      | high       |   yes   |  yes  |
| Research | Web research            | -      | medium     |         |  yes  |
| System   | Shell access            | -      | high       |         |  yes  |
+----------+-------------------------+--------+------------+---------+-------+
```

```bash
# Agent details
axon agents show Research
```

### axon memory — Manage Memory

```bash
# List all memories
axon memory list

# Search memory
axon memory search "Python"

# Add memory
axon memory add "Project" "We use FastAPI and React" --category Tech

# Delete memory (full UUID from 'memory list')
axon memory delete 8ae2871e-2f40-4aff-860e-3e0bcdcaeed3
```

### axon status — Health Check

```bash
axon status
```

```
+-------------------------------- Axon Status --------------------------------+
| Server reachable  https://axon.example.com                                  |
| App:     Axon by NeuroVexon                                                 |
| Version: 2.0.0                                                              |
|                                                                             |
| LLM Provider:                                                               |
|   ollama: available                                                         |
|   claude: unavailable                                                       |
|                                                                             |
| Dashboard:                                                                  |
|   Conversations: 44                                                         |
|   Messages:      170                                                        |
|   Agents:        3                                                          |
|   Tool Calls:    21                                                         |
|   Approval Rate: 92.5%                                                      |
+-----------------------------------------------------------------------------+
```

### axon version — Version Information

```bash
axon version
```

```
+---------------------------------- Version ----------------------------------+
| Axon CLI:    v1.0.0                                                         |
| Axon Server: v2.0.0                                                         |
+-----------------------------------------------------------------------------+
```

## Scripting & Automation

The CLI is designed for automation:

```bash
# Health check in a script
axon status || echo "Server not reachable"

# Import memory from file
while IFS="|" read -r key content; do
  axon memory add "$key" "$content"
done < memories.csv

# Run daily (crontab)
0 9 * * * echo "Daily report for $(date)" | /usr/local/bin/axon chat >> /var/log/axon-daily.log
```

## Platform Compatibility

| Platform | Shell | Pipe | REPL | Status |
|----------|-------|------|------|--------|
| Windows 10/11 | PowerShell | Yes | Yes | Tested |
| Windows 10/11 | CMD | Yes | Yes | Tested |
| Linux | Bash/Zsh | Yes | Yes | Tested |
| macOS | Zsh/Bash | Yes | Yes | Compatible |

## Troubleshooting

### Connection Failed

```
Connection failed: [Errno 111] Connection refused
```

Check with `axon config show` whether the URL is correct and whether the server is running.

### Authentication Failed (401)

```
Authentication failed (401). Check 'axon config set auth'.
```

Set the correct credentials:
```bash
axon config set auth username:password
```

### Server Error (404)

Some endpoints only exist from certain server versions:
- `/api/v1/agents` — from v2.0.0
- `/api/v1/analytics/overview` — from v2.0.0

Check the server version with `axon version`.
