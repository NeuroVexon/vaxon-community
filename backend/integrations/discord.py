"""
Axon by NeuroVexon - Discord Integration

Ermoeglicht die Nutzung von Axon ueber Discord.
Tool-Approvals werden ueber Discord Button-Components abgewickelt.

Konfiguration via .env oder Settings UI:
    DISCORD_ENABLED=true
    DISCORD_BOT_TOKEN=<dein-token>
    DISCORD_ALLOWED_CHANNELS=123456789,987654321  (optional, leer = alle)
    DISCORD_ALLOWED_USERS=123456789  (optional, leer = alle)

Start:
    python -m integrations.discord
"""

import asyncio
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

logger = logging.getLogger(__name__)

try:
    import discord
    from discord.ext import commands
    from discord import ui, app_commands
    HAS_DISCORD = True
except ImportError:
    HAS_DISCORD = False


from core.i18n import t


# --- In-Memory State ---

# Session mapping: discord_user_id -> axon_session_id
_user_sessions: dict[int, str] = {}

# Agent mapping: discord_user_id -> agent_id
_user_agents: dict[int, Optional[str]] = {}

# Pending approvals: approval_id -> {tool, channel_id, message_id}
_pending_approvals: dict[str, dict] = {}


def _get_config():
    """Discord config aus Environment laden"""
    token = os.getenv("DISCORD_BOT_TOKEN", "")
    allowed_channels_raw = os.getenv("DISCORD_ALLOWED_CHANNELS", "")
    allowed_users_raw = os.getenv("DISCORD_ALLOWED_USERS", "")

    allowed_channels = set()
    if allowed_channels_raw.strip():
        for cid in allowed_channels_raw.split(","):
            cid = cid.strip()
            if cid.isdigit():
                allowed_channels.add(int(cid))

    allowed_users = set()
    if allowed_users_raw.strip():
        for uid in allowed_users_raw.split(","):
            uid = uid.strip()
            if uid.isdigit():
                allowed_users.add(int(uid))

    return token, allowed_channels, allowed_users


def _is_allowed(
    user_id: int,
    channel_id: int,
    allowed_users: set[int],
    allowed_channels: set[int]
) -> bool:
    """Prueft ob User und Channel berechtigt sind"""
    if allowed_users and user_id not in allowed_users:
        return False
    if allowed_channels and channel_id not in allowed_channels:
        return False
    return True


# --- Approval View (Discord Buttons) ---

if HAS_DISCORD:
    class ApprovalView(ui.View):
        """Discord Button-View fuer Tool-Approvals"""

        def __init__(self, approval_id: str):
            super().__init__(timeout=120.0)
            self.approval_id = approval_id
            self.decision: Optional[str] = None

        @ui.button(label="Allow", style=discord.ButtonStyle.green, custom_id="approve_once")
        async def approve_once(self, interaction: discord.Interaction, button: ui.Button):
            await self._handle_decision(interaction, "once", t("bot.decision_once"))

        @ui.button(label="Session", style=discord.ButtonStyle.blurple, custom_id="approve_session")
        async def approve_session(self, interaction: discord.Interaction, button: ui.Button):
            await self._handle_decision(interaction, "session", t("bot.decision_session"))

        @ui.button(label="Reject", style=discord.ButtonStyle.red, custom_id="approve_never")
        async def approve_never(self, interaction: discord.Interaction, button: ui.Button):
            await self._handle_decision(interaction, "never", t("bot.decision_never"))

        async def _handle_decision(self, interaction: discord.Interaction, decision: str, label: str):
            try:
                import httpx

                async with httpx.AsyncClient(timeout=30.0) as client:
                    await client.post(
                        f"http://localhost:8000/api/v1/chat/approve/{self.approval_id}?decision={decision}"
                    )

                self.decision = decision
                _pending_approvals.pop(self.approval_id, None)

                # Buttons deaktivieren
                for item in self.children:
                    item.disabled = True
                await interaction.response.edit_message(view=self)
                await interaction.followup.send(
                    t("bot.decision_label", decision=label),
                    ephemeral=True
                )

            except Exception as e:
                logger.error(f"Discord approval error: {e}")
                await interaction.response.send_message(
                    t("bot.error", error=str(e)[:200]),
                    ephemeral=True
                )

        async def on_timeout(self):
            """Timeout — automatisch ablehnen"""
            if self.decision is None:
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        await client.post(
                            f"http://localhost:8000/api/v1/chat/approve/{self.approval_id}?decision=never"
                        )
                except Exception:
                    pass
                _pending_approvals.pop(self.approval_id, None)


# --- Bot Setup ---

def run_bot():
    """Startet den Discord Bot"""
    if not HAS_DISCORD:
        logger.error("discord.py nicht installiert. pip install discord.py")
        return

    token, allowed_channels, allowed_users = _get_config()
    if not token:
        logger.error(t("bot.no_token", channel="Discord"))
        return

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(t("bot.started", channel="Discord"))

    @bot.command(name="new")
    async def cmd_new(ctx: commands.Context):
        """Neuen Chat starten"""
        if not _is_allowed(ctx.author.id, ctx.channel.id, allowed_users, allowed_channels):
            return
        _user_sessions.pop(ctx.author.id, None)
        await ctx.send(t("bot.new_chat"))

    @bot.command(name="status")
    async def cmd_status(ctx: commands.Context):
        """Status anzeigen"""
        if not _is_allowed(ctx.author.id, ctx.channel.id, allowed_users, allowed_channels):
            return
        session_id = _user_sessions.get(ctx.author.id, "-")
        sid_display = session_id[:8] + "..." if len(session_id) > 8 else session_id
        agent_id = _user_agents.get(ctx.author.id, "default")
        pending = len(_pending_approvals)
        await ctx.send(
            t("bot.status", session=sid_display, agent=agent_id or "default", pending=str(pending))
        )

    @bot.command(name="agents")
    async def cmd_agents(ctx: commands.Context):
        """Verfuegbare Agents auflisten"""
        if not _is_allowed(ctx.author.id, ctx.channel.id, allowed_users, allowed_channels):
            return
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get("http://localhost:8000/api/v1/agents")
                if resp.status_code == 200:
                    agents = resp.json()
                    if not agents:
                        await ctx.send(t("bot.no_agents"))
                        return
                    lines = []
                    for a in agents:
                        default_marker = " (default)" if a.get("is_default") else ""
                        enabled = "on" if a.get("enabled") else "off"
                        lines.append(f"  {a['name']}{default_marker} [{enabled}]")
                    await ctx.send(t("bot.agents_list", agents="\n".join(lines)))
        except Exception as e:
            await ctx.send(t("bot.error", error=str(e)[:200]))

    @bot.command(name="agent")
    async def cmd_agent(ctx: commands.Context, *, name: str = ""):
        """Agent wechseln"""
        if not _is_allowed(ctx.author.id, ctx.channel.id, allowed_users, allowed_channels):
            return
        if not name:
            await ctx.send(t("bot.commands"))
            return

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get("http://localhost:8000/api/v1/agents")
                if resp.status_code == 200:
                    agents = resp.json()
                    match = None
                    for a in agents:
                        if a["name"].lower() == name.lower():
                            match = a
                            break
                    if match:
                        _user_agents[ctx.author.id] = match["id"]
                        _user_sessions.pop(ctx.author.id, None)
                        await ctx.send(t("bot.agent_switched", name=match["name"]))
                    else:
                        await ctx.send(t("bot.agent_not_found", name=name))
        except Exception as e:
            await ctx.send(t("bot.error", error=str(e)[:200]))

    @bot.event
    async def on_message(message: discord.Message):
        """Verarbeitet Nachrichten"""
        # Eigene Nachrichten ignorieren
        if message.author == bot.user:
            return

        # Commands zuerst verarbeiten
        await bot.process_commands(message)

        # Nur auf Nachrichten ohne Prefix reagieren
        if message.content.startswith("!"):
            return

        if not _is_allowed(message.author.id, message.channel.id, allowed_users, allowed_channels):
            return

        msg_text = message.content.strip()
        if not msg_text:
            return

        user_id = message.author.id
        session_id = _user_sessions.get(user_id)
        agent_id = _user_agents.get(user_id)

        # Typing-Indikator
        async with message.channel.typing():
            try:
                import httpx

                request_body = {
                    "message": msg_text,
                    "session_id": session_id,
                }
                if agent_id:
                    request_body["agent_id"] = agent_id

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

                                params_str = "\n".join(f"  {k}: {v}" for k, v in params.items())

                                embed = discord.Embed(
                                    title=f"{risk_emoji} {t('bot.tool_request', tool=tool_name)}",
                                    description=description,
                                    color={"low": 0x00ff00, "medium": 0xffaa00, "high": 0xff0000, "critical": 0xff0000}.get(risk_level, 0xffaa00)
                                )
                                if params_str:
                                    embed.add_field(name="Parameter", value=f"```\n{params_str}\n```", inline=False)

                                view = ApprovalView(approval_id)
                                approval_msg = await message.channel.send(embed=embed, view=view)

                                _pending_approvals[approval_id] = {
                                    "tool": tool_name,
                                    "channel_id": message.channel.id,
                                    "message_id": approval_msg.id,
                                }

                            elif event_type == "tool_result":
                                tool_name = event.get("tool", "?")
                                result_text = str(event.get("result", ""))[:1500]
                                exec_time = event.get("execution_time_ms", 0)

                                embed = discord.Embed(
                                    title=t("bot.tool_executed", tool=tool_name, time=str(exec_time)),
                                    description=f"```\n{result_text}\n```",
                                    color=0x00d4ff
                                )
                                await message.channel.send(embed=embed)

                            elif event_type == "tool_rejected":
                                await message.channel.send(
                                    t("bot.tool_rejected", tool=event.get("tool", "?"))
                                )

                            elif event_type == "done":
                                new_session = event.get("session_id")
                                if new_session:
                                    _user_sessions[user_id] = new_session

                # Antwort senden
                if full_text.strip():
                    # Discord hat 2000 Zeichen Limit
                    for chunk in _split_text(full_text, 1900):
                        await message.channel.send(chunk)

            except Exception as e:
                logger.error(f"Discord message handler error: {e}")
                await message.channel.send(t("bot.error", error=str(e)[:200]))


    logger.info(t("bot.started", channel="Discord"))
    bot.run(token)


def _split_text(text: str, max_length: int = 1900) -> list[str]:
    """Teilt langen Text in Discord-kompatible Chunks"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip('\n')
    return chunks


if __name__ == "__main__":
    run_bot()
