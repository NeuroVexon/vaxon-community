# Messenger Integration

Axon can be controlled via Telegram and Discord. Tool approvals are handled through inline keyboards (Telegram) or button components (Discord).

## Architecture

```
Telegram/Discord User
        │
        ▼
  Messenger Bot (Python)
        │
        ▼
  Axon Backend (localhost:8000)
        │
        ├── /api/v1/chat/agent (SSE Stream)
        └── /api/v1/chat/approve/{id} (Tool Approval)
```

The bots connect **locally** to the Axon backend. No additional exposed port required.

## Telegram

### Prerequisites

1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Enter the token in `.env`
3. `python-telegram-bot` installed (included in requirements.txt)

### Configuration

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrstUVWxyz
TELEGRAM_ALLOWED_USERS=123456789,987654321
```

- `TELEGRAM_BOT_TOKEN`: Token from BotFather
- `TELEGRAM_ALLOWED_USERS`: Comma-separated Telegram user IDs (empty = all allowed)

### Starting

```bash
cd backend
python -m integrations.telegram
```

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and help |
| `/new` | Start a new chat |
| `/status` | Current session info |

### Tool Approvals

When a tool needs to be executed, a message appears with three buttons:

- **Allow** — Once for this call
- **Session** — For the entire chat session
- **Reject** — Tool will not be executed

## Discord

### Prerequisites

1. Create a bot in the [Discord Developer Console](https://discord.com/developers/applications)
2. Bot permissions: `Send Messages`, `Read Message History`, `Message Content Intent`
3. Enter the token in `.env`
4. `discord.py` installed (included in requirements.txt)

### Configuration

```env
DISCORD_BOT_TOKEN=MTIz...
DISCORD_ALLOWED_CHANNELS=123456789012345678
DISCORD_ALLOWED_USERS=123456789012345678
```

- `DISCORD_BOT_TOKEN`: Bot token from the Developer Console
- `DISCORD_ALLOWED_CHANNELS`: Comma-separated channel IDs (empty = all)
- `DISCORD_ALLOWED_USERS`: Comma-separated user IDs (empty = all)

### Starting

```bash
cd backend
python -m integrations.discord
```

### Commands

| Command | Description |
|---------|-------------|
| `!new` | Start a new chat |
| `!status` | Current session info |

Regular messages (without `!` prefix) are forwarded to Axon as chat messages.

### Tool Approvals

Tool requests are displayed as Discord embeds with color-coded risk levels.
Three buttons for the decision:

- **Allow** (green) — Once
- **Session** (blue) — For the session
- **Reject** (red) — Do not execute

Timeout: 120 seconds — after which it is automatically rejected.

## Notes

- The bots are **separate processes** — they run independently from the web frontend
- Multiple bots can run simultaneously (Telegram + Discord + Web UI)
- Each messenger user has their own session
- The audit log also captures actions via messenger bots
- For production: Start bots as systemd service or Docker container
