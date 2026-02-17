"""
Axon by NeuroVexon - Telegram Integration

Ermoeglicht die Nutzung von Axon ueber Telegram.
Tool-Approvals werden ueber Inline-Keyboards abgewickelt.

Konfiguration via .env oder Settings UI:
    TELEGRAM_ENABLED=true
    TELEGRAM_BOT_TOKEN=<dein-token>
    TELEGRAM_ALLOWED_USERS=123456789,987654321  (optional, leer = alle)

Start:
    python -m integrations.telegram
"""

import asyncio
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

logger = logging.getLogger(__name__)

# Lazy import — nur wenn das Modul wirklich gestartet wird
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters,
    )
    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False


from core.i18n import t


# --- In-Memory State ---

# Pending approvals: approval_id -> {tool, params, description, risk_level, chat_id, message_id}
_pending_approvals: dict[str, dict] = {}

# Session mapping: telegram_user_id -> axon_session_id
_user_sessions: dict[int, str] = {}

# Agent mapping: telegram_user_id -> agent_id
_user_agents: dict[int, Optional[str]] = {}


def _get_config():
    """Telegram config aus Environment laden"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    allowed_raw = os.getenv("TELEGRAM_ALLOWED_USERS", "")
    allowed_users = set()
    if allowed_raw.strip():
        for uid in allowed_raw.split(","):
            uid = uid.strip()
            if uid.isdigit():
                allowed_users.add(int(uid))
    return token, allowed_users


def _is_allowed(user_id: int, allowed_users: set[int]) -> bool:
    """Prueft ob der User berechtigt ist (leer = alle erlaubt)"""
    if not allowed_users:
        return True
    return user_id in allowed_users


# --- Bot Handlers ---

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler fuer /start"""
    _, allowed_users = _get_config()
    if not _is_allowed(update.effective_user.id, allowed_users):
        await update.message.reply_text(t("bot.access_denied"))
        return

    welcome = t("bot.welcome") + "\n\n" + t("bot.commands")
    await update.message.reply_text(welcome)


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler fuer /new — neuen Chat starten"""
    user_id = update.effective_user.id
    _user_sessions.pop(user_id, None)
    await update.message.reply_text(t("bot.new_chat"))


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler fuer /status"""
    user_id = update.effective_user.id
    session_id = _user_sessions.get(user_id, "-")
    session_display = session_id[:8] + "..." if len(session_id) > 8 else session_id
    agent_id = _user_agents.get(user_id, "default")
    pending = len(_pending_approvals)
    await update.message.reply_text(
        t("bot.status", session=session_display, agent=agent_id or "default", pending=str(pending))
    )


async def cmd_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler fuer /agents — listet verfuegbare Agents"""
    _, allowed_users = _get_config()
    if not _is_allowed(update.effective_user.id, allowed_users):
        return

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("http://localhost:8000/api/v1/agents")
            if resp.status_code == 200:
                agents = resp.json()
                if not agents:
                    await update.message.reply_text(t("bot.no_agents"))
                    return
                lines = []
                for a in agents:
                    default_marker = " (default)" if a.get("is_default") else ""
                    enabled = "on" if a.get("enabled") else "off"
                    lines.append(f"  {a['name']}{default_marker} [{enabled}]")
                await update.message.reply_text(
                    t("bot.agents_list", agents="\n".join(lines))
                )
    except Exception as e:
        await update.message.reply_text(t("bot.error", error=str(e)[:200]))


async def cmd_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler fuer /agent <name> — Agent wechseln"""
    _, allowed_users = _get_config()
    if not _is_allowed(update.effective_user.id, allowed_users):
        return

    if not context.args:
        await update.message.reply_text(t("bot.commands"))
        return

    agent_name = " ".join(context.args).strip()
    user_id = update.effective_user.id

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("http://localhost:8000/api/v1/agents")
            if resp.status_code == 200:
                agents = resp.json()
                match = None
                for a in agents:
                    if a["name"].lower() == agent_name.lower():
                        match = a
                        break

                if match:
                    _user_agents[user_id] = match["id"]
                    _user_sessions.pop(user_id, None)  # Neuer Chat mit neuem Agent
                    await update.message.reply_text(
                        t("bot.agent_switched", name=match["name"])
                    )
                else:
                    await update.message.reply_text(
                        t("bot.agent_not_found", name=agent_name)
                    )
    except Exception as e:
        await update.message.reply_text(t("bot.error", error=str(e)[:200]))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verarbeitet normale Text-Nachrichten → leitet an Axon Agent weiter"""
    _, allowed_users = _get_config()
    user_id = update.effective_user.id

    if not _is_allowed(user_id, allowed_users):
        await update.message.reply_text(t("bot.access_denied"))
        return

    message_text = update.message.text
    if not message_text:
        return

    # Group-Chat: Nur auf Mentions reagieren
    if update.effective_chat.type in ("group", "supergroup"):
        bot_username = context.bot.username
        if bot_username and f"@{bot_username}" not in message_text:
            return
        # @mention entfernen
        message_text = message_text.replace(f"@{bot_username}", "").strip()
        if not message_text:
            return

    # "Denkt nach..." Indikator
    thinking_msg = await update.message.reply_text(t("bot.thinking"))

    session_id = _user_sessions.get(user_id)
    agent_id = _user_agents.get(user_id)

    try:
        import httpx

        request_body = {
            "message": message_text,
            "session_id": session_id,
        }
        if agent_id:
            request_body["agent_id"] = agent_id

        # Agent-Endpoint aufrufen (SSE stream)
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "http://localhost:8000/api/v1/chat/agent",
                json=request_body,
                headers={"Content-Type": "application/json"}
            ) as response:
                full_text = ""

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type")

                    if event_type == "text":
                        full_text += event.get("content", "")

                    elif event_type == "tool_request":
                        tool_name = event.get("tool", "?")
                        description = event.get("description", "")
                        risk_level = event.get("risk_level", "medium")
                        approval_id = event.get("approval_id", "")
                        params = event.get("params", {})

                        risk_emoji = {"low": "\U0001f7e2", "medium": "\U0001f7e1", "high": "\U0001f534", "critical": "\u26d4"}.get(risk_level, "\U0001f7e1")

                        keyboard = InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton(t("bot.allow_once"), callback_data=f"approve:{approval_id}:once"),
                                InlineKeyboardButton(t("bot.allow_session"), callback_data=f"approve:{approval_id}:session"),
                                InlineKeyboardButton(t("bot.reject"), callback_data=f"approve:{approval_id}:never"),
                            ]
                        ])

                        params_str = "\n".join(f"  {k}: {v}" for k, v in params.items())
                        approval_msg = await update.message.reply_text(
                            f"{risk_emoji} *Tool\\-Anfrage:* `{_escape_md(tool_name)}`\n"
                            f"{_escape_md(description)}\n\n"
                            f"Parameter:\n```\n{params_str}\n```",
                            parse_mode="MarkdownV2",
                            reply_markup=keyboard
                        )

                        _pending_approvals[approval_id] = {
                            "tool": tool_name,
                            "chat_id": update.effective_chat.id,
                            "message_id": approval_msg.message_id,
                        }

                    elif event_type == "tool_result":
                        tool_name = event.get("tool", "?")
                        result_text = str(event.get("result", ""))[:500]
                        exec_time = event.get("execution_time_ms", 0)
                        try:
                            await update.message.reply_text(
                                f"Tool `{_escape_md(tool_name)}` ausgefuehrt \\({exec_time}ms\\):\n```\n{_escape_md(result_text)}\n```",
                                parse_mode="MarkdownV2"
                            )
                        except Exception:
                            await update.message.reply_text(
                                t("bot.tool_executed", tool=tool_name, time=str(exec_time))
                            )

                    elif event_type == "tool_rejected":
                        await update.message.reply_text(
                            t("bot.tool_rejected", tool=event.get("tool", "?"))
                        )

                    elif event_type == "done":
                        new_session = event.get("session_id")
                        if new_session:
                            _user_sessions[user_id] = new_session

                # Denk-Nachricht loeschen und Antwort senden
                await thinking_msg.delete()
                if full_text.strip():
                    # Telegram hat 4096 Zeichen Limit
                    for chunk in _split_text(full_text, 4000):
                        await update.message.reply_text(chunk)

    except Exception as e:
        logger.error(f"Telegram message handler error: {e}")
        await thinking_msg.edit_text(t("bot.error", error=str(e)[:200]))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verarbeitet Inline-Keyboard Callbacks fuer Tool-Approvals"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data or not data.startswith("approve:"):
        return

    parts = data.split(":")
    if len(parts) != 3:
        return

    _, approval_id, decision = parts

    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"http://localhost:8000/api/v1/chat/approve/{approval_id}?decision={decision}"
            )

        decision_labels = {
            "once": t("bot.decision_once"),
            "session": t("bot.decision_session"),
            "never": t("bot.decision_never"),
        }
        decision_text = decision_labels.get(decision, decision)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            t("bot.decision_label", decision=decision_text)
        )

        # Cleanup
        _pending_approvals.pop(approval_id, None)

    except Exception as e:
        logger.error(f"Telegram callback error: {e}")
        await query.message.reply_text(t("bot.approval_error", error=str(e)[:200]))


# --- Utilities ---

def _escape_md(text: str) -> str:
    """Escaped spezielle MarkdownV2 Zeichen"""
    special = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special:
        text = text.replace(char, f'\\{char}')
    return text


def _split_text(text: str, max_length: int = 4000) -> list[str]:
    """Teilt langen Text in Telegram-kompatible Chunks"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        # Am naechsten Newline vor dem Limit splitten
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip('\n')
    return chunks


# --- Main ---

def run_bot():
    """Startet den Telegram Bot"""
    if not HAS_TELEGRAM:
        logger.error("python-telegram-bot nicht installiert. pip install python-telegram-bot")
        return

    token, _ = _get_config()
    if not token:
        logger.error(t("bot.no_token", channel="Telegram"))
        return

    logger.info(t("bot.started", channel="Telegram"))

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("agents", cmd_agents))
    app.add_handler(CommandHandler("agent", cmd_agent))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


async def start_bot_async():
    """Start bot in background (called from main.py lifespan)"""
    if not HAS_TELEGRAM:
        return

    token, _ = _get_config()
    if not token:
        return

    logger.info(t("bot.started", channel="Telegram"))

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("agents", cmd_agents))
    app.add_handler(CommandHandler("agent", cmd_agent))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
