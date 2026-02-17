#!/usr/bin/env python3
"""
Axon CLI — Terminal-Steuerung fuer Axon by NeuroVexon
Standalone HTTP-Client mit SSE-Streaming und Tool-Approval.
"""

import json
import sys
import os
import uuid
from pathlib import Path
from typing import Optional

import typer
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.markup import escape

# ──────────────────────────────────────────────────────────────────────────────
# Constants + CLI Version
# ──────────────────────────────────────────────────────────────────────────────

CLI_VERSION = "1.0.0"
CONFIG_DIR = Path.home() / ".axon"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_CONFIG = {
    "url": "http://localhost:8000",
    "auth_user": None,
    "auth_password": None,
    "language": "de",
}

# ──────────────────────────────────────────────────────────────────────────────
# i18n — Translations (DE + EN)
# ──────────────────────────────────────────────────────────────────────────────

CLI_STRINGS = {
    "de": {
        "welcome": "Axon CLI v{version} — Verbunden mit {url}",
        "repl_hint": "Schreibe eine Nachricht oder /help fuer Hilfe. Beende mit /exit oder Ctrl+C.",
        "repl_help": (
            "/new          Neue Session starten\n"
            "/agent <name> Agent wechseln\n"
            "/exit         Beenden"
        ),
        "repl_new": "Neue Session gestartet.",
        "repl_agent": "Agent gewechselt zu: {name}",
        "repl_agent_not_found": "Agent nicht gefunden: {name}",
        "repl_exit": "Auf Wiedersehen!",
        "no_message": "Keine Nachricht angegeben. Nutze --help fuer Hilfe.",
        "connecting": "Verbinde mit {url}...",
        "connection_error": "Verbindung fehlgeschlagen: {error}",
        "auth_error": "Authentifizierung fehlgeschlagen (401). Pruefe 'axon config set auth'.",
        "server_error": "Server-Fehler ({code}): {detail}",
        "streaming": "Streaming...",
        "tool_request_title": "Tool-Anfrage",
        "tool_label": "Tool",
        "risk_label": "Risiko",
        "params_label": "Parameter",
        "approval_prompt": "[A]llow  [S]ession  [R]eject",
        "approved": "Genehmigt.",
        "rejected": "Abgelehnt.",
        "tool_result": "Tool-Ergebnis ({tool})",
        "tool_error": "Tool-Fehler ({tool}): {error}",
        "tool_blocked": "Tool blockiert: {tool}",
        "agents_title": "Agents",
        "no_agents": "Keine Agents gefunden.",
        "agent_detail_title": "Agent: {name}",
        "memory_title": "Memories",
        "no_memories": "Keine Memories gefunden.",
        "memory_added": "Memory hinzugefuegt: {key}",
        "memory_deleted": "Memory geloescht: {id}",
        "config_title": "Konfiguration",
        "config_saved": "Gespeichert: {key} = {value}",
        "config_invalid_key": "Unbekannter Key: {key}. Erlaubt: url, auth, language",
        "status_title": "Axon Status",
        "status_healthy": "Server erreichbar",
        "status_unhealthy": "Server nicht erreichbar",
        "version_title": "Version",
        "risk_low": "niedrig",
        "risk_medium": "mittel",
        "risk_high": "hoch",
        "pipe_reading": "Lese Eingabe von stdin...",
    },
    "en": {
        "welcome": "Axon CLI v{version} — Connected to {url}",
        "repl_hint": "Type a message or /help for help. Exit with /exit or Ctrl+C.",
        "repl_help": (
            "/new          Start new session\n"
            "/agent <name> Switch agent\n"
            "/exit         Quit"
        ),
        "repl_new": "New session started.",
        "repl_agent": "Switched agent to: {name}",
        "repl_agent_not_found": "Agent not found: {name}",
        "repl_exit": "Goodbye!",
        "no_message": "No message provided. Use --help for help.",
        "connecting": "Connecting to {url}...",
        "connection_error": "Connection failed: {error}",
        "auth_error": "Authentication failed (401). Check 'axon config set auth'.",
        "server_error": "Server error ({code}): {detail}",
        "streaming": "Streaming...",
        "tool_request_title": "Tool Request",
        "tool_label": "Tool",
        "risk_label": "Risk",
        "params_label": "Parameters",
        "approval_prompt": "[A]llow  [S]ession  [R]eject",
        "approved": "Approved.",
        "rejected": "Rejected.",
        "tool_result": "Tool result ({tool})",
        "tool_error": "Tool error ({tool}): {error}",
        "tool_blocked": "Tool blocked: {tool}",
        "agents_title": "Agents",
        "no_agents": "No agents found.",
        "agent_detail_title": "Agent: {name}",
        "memory_title": "Memories",
        "no_memories": "No memories found.",
        "memory_added": "Memory added: {key}",
        "memory_deleted": "Memory deleted: {id}",
        "config_title": "Configuration",
        "config_saved": "Saved: {key} = {value}",
        "config_invalid_key": "Unknown key: {key}. Allowed: url, auth, language",
        "status_title": "Axon Status",
        "status_healthy": "Server reachable",
        "status_unhealthy": "Server unreachable",
        "version_title": "Version",
        "risk_low": "low",
        "risk_medium": "medium",
        "risk_high": "high",
        "pipe_reading": "Reading input from stdin...",
    },
}


def s(msg_key: str, **kwargs) -> str:
    """Get translated string for current language."""
    lang = load_config().get("language", "de")
    text = CLI_STRINGS.get(lang, CLI_STRINGS["de"]).get(msg_key, msg_key)
    if kwargs:
        text = text.format(**kwargs)
    return text


# ──────────────────────────────────────────────────────────────────────────────
# Config Management
# ──────────────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load config from ~/.axon/config.json, create with defaults if missing."""
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    """Save config to ~/.axon/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# HTTP Helpers
# ──────────────────────────────────────────────────────────────────────────────

console = Console()
err_console = Console(stderr=True)


def _base_url() -> str:
    return load_config().get("url", "http://localhost:8000").rstrip("/")


def _auth() -> Optional[tuple[str, str]]:
    cfg = load_config()
    user = cfg.get("auth_user")
    pw = cfg.get("auth_password")
    if user and pw:
        return (user, pw)
    return None


def _client(**kwargs) -> httpx.Client:
    """Create a configured httpx client."""
    auth = _auth()
    return httpx.Client(
        base_url=_base_url(),
        auth=auth,
        timeout=30.0,
        **kwargs,
    )


def _handle_response(resp: httpx.Response) -> dict:
    """Handle HTTP response, raise on errors."""
    if resp.status_code == 401:
        err_console.print(f"[red]{s('auth_error')}[/red]")
        raise typer.Exit(1)
    if resp.status_code >= 400:
        detail = ""
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        err_console.print(f"[red]{s('server_error', code=resp.status_code, detail=detail)}[/red]")
        raise typer.Exit(1)
    return resp.json()


def _api_get(path: str, params: Optional[dict] = None) -> dict:
    """GET request to API."""
    try:
        with _client() as client:
            resp = client.get(f"/api/v1{path}", params=params)
            return _handle_response(resp)
    except httpx.ConnectError as e:
        err_console.print(f"[red]{s('connection_error', error=str(e))}[/red]")
        raise typer.Exit(1)


def _api_get_safe(path: str, params: Optional[dict] = None) -> Optional[dict]:
    """GET request that returns None on any error instead of exiting."""
    try:
        with _client() as client:
            resp = client.get(f"/api/v1{path}", params=params)
            if resp.status_code >= 400:
                return None
            return resp.json()
    except Exception:
        return None


def _api_post(path: str, json_data: Optional[dict] = None) -> dict:
    """POST request to API."""
    try:
        with _client() as client:
            resp = client.post(f"/api/v1{path}", json=json_data)
            return _handle_response(resp)
    except httpx.ConnectError as e:
        err_console.print(f"[red]{s('connection_error', error=str(e))}[/red]")
        raise typer.Exit(1)


def _api_delete(path: str) -> dict:
    """DELETE request to API."""
    try:
        with _client() as client:
            resp = client.delete(f"/api/v1{path}")
            return _handle_response(resp)
    except httpx.ConnectError as e:
        err_console.print(f"[red]{s('connection_error', error=str(e))}[/red]")
        raise typer.Exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# SSE Streaming + Event Handler + Tool Approval
# ──────────────────────────────────────────────────────────────────────────────

def _translate_risk(level: str) -> str:
    """Translate risk level to current language."""
    mapping = {"low": "risk_low", "medium": "risk_medium", "high": "risk_high"}
    return s(mapping.get(level, "risk_medium"))


def _show_tool_request(event: dict) -> str:
    """Display tool request panel and get user decision. Returns 'once'/'session'/'never'."""
    tool = event.get("tool", "?")
    risk = event.get("risk_level", "medium")
    description = event.get("description", "")
    params = event.get("params", {})

    # Build panel content
    lines = []
    lines.append(f"[bold]{s('tool_label')}:[/bold]   {escape(tool)}")
    lines.append(f"[bold]{s('risk_label')}:[/bold]  {_translate_risk(risk)}")
    if description:
        lines.append(f"  {escape(description)}")
    lines.append("")
    for k, v in params.items():
        lines.append(f"  [dim]{escape(k)}:[/dim] {escape(str(v))}")

    color = {"low": "green", "medium": "yellow", "high": "red"}.get(risk, "yellow")
    console.print(Panel(
        "\n".join(lines),
        title=f"[{color}]{s('tool_request_title')}[/{color}]",
        border_style=color,
    ))

    # Prompt for decision
    while True:
        choice = Prompt.ask(s("approval_prompt"), default="a").strip().lower()
        if choice in ("a", "allow"):
            return "once"
        elif choice in ("s", "session"):
            return "session"
        elif choice in ("r", "reject", "n"):
            return "never"


def _stream_chat(message: str, session_id: Optional[str] = None, agent_id: Optional[str] = None) -> Optional[str]:
    """
    Send message via SSE stream, handle events, return session_id.
    Returns the session_id from the 'done' event.
    """
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    if agent_id:
        payload["agent_id"] = agent_id

    auth = _auth()
    base = _base_url()
    returned_session_id = session_id

    try:
        with httpx.Client(base_url=base, auth=auth, timeout=None) as client:
            with client.stream("POST", "/api/v1/chat/agent", json=payload) as resp:
                if resp.status_code == 401:
                    err_console.print(f"[red]{s('auth_error')}[/red]")
                    return None
                if resp.status_code >= 400:
                    resp.read()
                    detail = ""
                    try:
                        detail = resp.json().get("detail", resp.text)
                    except Exception:
                        detail = resp.text
                    err_console.print(f"[red]{s('server_error', code=resp.status_code, detail=detail)}[/red]")
                    return None

                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    raw = line[6:]  # Strip "data: "
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    etype = event.get("type")

                    if etype == "text":
                        # Print text chunk immediately (no newline for streaming effect)
                        content = event.get("content", "")
                        console.print(content, end="", highlight=False)

                    elif etype == "tool_request":
                        # Newline before tool panel if we were streaming text
                        console.print()
                        approval_id = event.get("approval_id")
                        decision = _show_tool_request(event)

                        # Send approval decision
                        if approval_id:
                            try:
                                approve_resp = client.post(
                                    f"/api/v1/chat/approve/{approval_id}",
                                    params={"decision": decision},
                                )
                                if decision == "never":
                                    console.print(f"[dim]{s('rejected')}[/dim]")
                                else:
                                    console.print(f"[dim]{s('approved')}[/dim]")
                            except Exception:
                                pass

                    elif etype == "tool_result":
                        tool = event.get("tool", "?")
                        result = event.get("result", "")
                        time_ms = event.get("execution_time_ms", 0)
                        console.print()
                        console.print(Panel(
                            escape(str(result)[:1000]),
                            title=f"[green]{s('tool_result', tool=tool)}[/green] [dim]({time_ms}ms)[/dim]",
                            border_style="green",
                        ))

                    elif etype == "tool_error":
                        tool = event.get("tool", "?")
                        error = event.get("error", "?")
                        console.print()
                        console.print(f"[red]{s('tool_error', tool=tool, error=error)}[/red]")

                    elif etype == "tool_rejected":
                        tool = event.get("tool", "?")
                        console.print(f"[dim]{s('rejected')} ({tool})[/dim]")

                    elif etype == "tool_blocked":
                        tool = event.get("tool", "?")
                        console.print(f"[yellow]{s('tool_blocked', tool=tool)}[/yellow]")

                    elif etype == "warning":
                        msg = event.get("message", "")
                        console.print(f"\n[yellow]{escape(msg)}[/yellow]")

                    elif etype == "done":
                        returned_session_id = event.get("session_id", returned_session_id)
                        console.print()  # Final newline after streaming

                    elif etype == "error":
                        msg = event.get("message", "Unknown error")
                        console.print()
                        err_console.print(f"[red]Error: {escape(msg)}[/red]")

    except httpx.ConnectError as e:
        err_console.print(f"[red]{s('connection_error', error=str(e))}[/red]")
        return None
    except KeyboardInterrupt:
        console.print("\n[dim]Abgebrochen.[/dim]")
        return returned_session_id

    return returned_session_id


# ──────────────────────────────────────────────────────────────────────────────
# Interactive REPL
# ──────────────────────────────────────────────────────────────────────────────

def _repl():
    """Interactive REPL mode with persistent session."""
    cfg = load_config()
    console.print(Panel(
        s("welcome", version=CLI_VERSION, url=cfg.get("url", "?")),
        border_style="cyan",
    ))
    console.print(f"[dim]{s('repl_hint')}[/dim]\n")

    session_id = None
    agent_id = None

    try:
        while True:
            try:
                user_input = Prompt.ask("[bold cyan]>[/bold cyan]")
            except EOFError:
                break

            if not user_input.strip():
                continue

            text = user_input.strip()

            # REPL commands
            if text == "/exit" or text == "exit":
                console.print(s("repl_exit"))
                break
            elif text == "/help":
                console.print(s("repl_help"))
                continue
            elif text == "/new":
                session_id = None
                console.print(f"[dim]{s('repl_new')}[/dim]")
                continue
            elif text.startswith("/agent"):
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    console.print("[dim]/agent <name>[/dim]")
                    continue
                name = parts[1].strip()
                # Look up agent by name
                try:
                    agents = _api_get("/agents")
                    found = None
                    for a in agents:
                        if a["name"].lower() == name.lower():
                            found = a
                            break
                    if found:
                        agent_id = found["id"]
                        console.print(f"[dim]{s('repl_agent', name=found['name'])}[/dim]")
                    else:
                        console.print(f"[yellow]{s('repl_agent_not_found', name=name)}[/yellow]")
                except SystemExit:
                    pass
                continue

            # Send message
            console.print()
            session_id = _stream_chat(text, session_id=session_id, agent_id=agent_id)
            console.print()

    except KeyboardInterrupt:
        console.print(f"\n{s('repl_exit')}")


# ──────────────────────────────────────────────────────────────────────────────
# Typer App + Commands
# ──────────────────────────────────────────────────────────────────────────────

app = typer.Typer(
    name="axon",
    help="Axon CLI — Terminal-Steuerung fuer Axon by NeuroVexon",
    no_args_is_help=False,
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Axon CLI — ohne Subcommand startet der interaktive REPL-Modus."""
    if ctx.invoked_subcommand is None:
        _repl()


# ── chat ─────────────────────────────────────────────────────────────────────

@app.command()
def chat(
    message: Optional[str] = typer.Argument(None, help="Nachricht an den Agent"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent-Name"),
    session: Optional[str] = typer.Option(None, "--session", "-s", help="Session-ID fortsetzen"),
):
    """Nachricht senden (SSE-Streaming). Pipe-Support: cat file.txt | axon chat"""
    # Pipe support: read from stdin if not a TTY
    if message is None and not sys.stdin.isatty():
        message = sys.stdin.read().strip()

    if not message:
        err_console.print(f"[yellow]{s('no_message')}[/yellow]")
        raise typer.Exit(1)

    # Resolve agent name to ID
    agent_id = None
    if agent:
        try:
            agents = _api_get("/agents")
            for a in agents:
                if a["name"].lower() == agent.lower():
                    agent_id = a["id"]
                    break
            if not agent_id:
                err_console.print(f"[yellow]{s('repl_agent_not_found', name=agent)}[/yellow]")
                raise typer.Exit(1)
        except SystemExit:
            raise

    result_session = _stream_chat(message, session_id=session, agent_id=agent_id)

    # Print session ID for scripting
    if result_session and not sys.stdout.isatty():
        pass  # In pipe mode, only output the response text


# ── agents ───────────────────────────────────────────────────────────────────

agents_app = typer.Typer(name="agents", help="Agents verwalten", invoke_without_command=True)
app.add_typer(agents_app)


@agents_app.callback(invoke_without_command=True)
def agents_list(ctx: typer.Context):
    """Alle Agents auflisten."""
    if ctx.invoked_subcommand is not None:
        return

    data = _api_get("/agents")
    if not data:
        console.print(f"[dim]{s('no_agents')}[/dim]")
        return

    table = Table(title=s("agents_title"), border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Beschreibung")
    table.add_column("Modell")
    table.add_column("Risiko Max")
    table.add_column("Default", justify="center")
    table.add_column("Aktiv", justify="center")

    for a in data:
        is_default = "[green]ja[/green]" if a.get("is_default") else ""
        enabled = "[green]ja[/green]" if a.get("enabled") else "[red]nein[/red]"
        table.add_row(
            a.get("name", "?"),
            a.get("description", ""),
            a.get("model", "-") or "-",
            a.get("risk_level_max", "?"),
            is_default,
            enabled,
        )

    console.print(table)


@agents_app.command("show")
def agents_show(name: str = typer.Argument(..., help="Agent-Name")):
    """Agent-Details anzeigen."""
    agents = _api_get("/agents")
    agent = None
    for a in agents:
        if a["name"].lower() == name.lower():
            agent = a
            break

    if not agent:
        err_console.print(f"[yellow]{s('repl_agent_not_found', name=name)}[/yellow]")
        raise typer.Exit(1)

    lines = []
    lines.append(f"[bold]ID:[/bold]            {agent['id']}")
    lines.append(f"[bold]Name:[/bold]          {agent['name']}")
    lines.append(f"[bold]Beschreibung:[/bold] {agent.get('description', '-')}")
    lines.append(f"[bold]System-Prompt:[/bold] {agent.get('system_prompt', '-') or '-'}")
    lines.append(f"[bold]Modell:[/bold]        {agent.get('model', '-') or '-'}")
    lines.append(f"[bold]Risiko Max:[/bold]    {agent.get('risk_level_max', '?')}")
    lines.append(f"[bold]Default:[/bold]       {'ja' if agent.get('is_default') else 'nein'}")
    lines.append(f"[bold]Aktiv:[/bold]         {'ja' if agent.get('enabled') else 'nein'}")

    tools = agent.get("allowed_tools")
    lines.append(f"[bold]Erlaubte Tools:[/bold] {', '.join(tools) if tools else 'alle'}")

    auto = agent.get("auto_approve_tools")
    lines.append(f"[bold]Auto-Approve:[/bold]  {', '.join(auto) if auto else 'keine'}")

    console.print(Panel(
        "\n".join(lines),
        title=f"[cyan]{s('agent_detail_title', name=agent['name'])}[/cyan]",
        border_style="cyan",
    ))


# ── memory ───────────────────────────────────────────────────────────────────

memory_app = typer.Typer(name="memory", help="Memory verwalten")
app.add_typer(memory_app)


@memory_app.command("list")
def memory_list():
    """Alle Memories auflisten."""
    data = _api_get("/memory")
    if not data:
        console.print(f"[dim]{s('no_memories')}[/dim]")
        return

    table = Table(title=s("memory_title"), border_style="cyan")
    table.add_column("ID", style="dim", max_width=8)
    table.add_column("Key", style="bold")
    table.add_column("Content", max_width=50)
    table.add_column("Quelle")
    table.add_column("Kategorie")

    for m in data:
        table.add_row(
            m["id"][:8],
            m["key"],
            m["content"][:50] + ("..." if len(m["content"]) > 50 else ""),
            m.get("source", "-"),
            m.get("category", "-") or "-",
        )

    console.print(table)


@memory_app.command("search")
def memory_search(query: str = typer.Argument(..., help="Suchbegriff")):
    """Memory durchsuchen."""
    data = _api_get("/memory", params={"search": query})
    if not data:
        console.print(f"[dim]{s('no_memories')}[/dim]")
        return

    table = Table(title=f"{s('memory_title')} — \"{query}\"", border_style="cyan")
    table.add_column("Key", style="bold")
    table.add_column("Content", max_width=60)
    table.add_column("Kategorie")

    for m in data:
        table.add_row(
            m["key"],
            m["content"][:60] + ("..." if len(m["content"]) > 60 else ""),
            m.get("category", "-") or "-",
        )

    console.print(table)


@memory_app.command("add")
def memory_add(
    key: str = typer.Argument(..., help="Memory-Key"),
    content: str = typer.Argument(..., help="Memory-Inhalt"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Kategorie"),
):
    """Memory hinzufuegen."""
    payload = {"key": key, "content": content, "source": "cli"}
    if category:
        payload["category"] = category
    _api_post("/memory", json_data=payload)
    console.print(f"[green]{s('memory_added', key=key)}[/green]")


@memory_app.command("delete")
def memory_delete(memory_id: str = typer.Argument(..., help="Memory-ID")):
    """Memory loeschen."""
    _api_delete(f"/memory/{memory_id}")
    console.print(f"[green]{s('memory_deleted', id=memory_id)}[/green]")


# ── config ───────────────────────────────────────────────────────────────────

config_app = typer.Typer(name="config", help="CLI-Konfiguration")
app.add_typer(config_app)


@config_app.command("show")
def config_show():
    """Konfiguration anzeigen."""
    cfg = load_config()

    lines = []
    lines.append(f"[bold]URL:[/bold]      {cfg.get('url', '-')}")
    user = cfg.get("auth_user")
    if user:
        lines.append(f"[bold]Auth:[/bold]     {user}:****")
    else:
        lines.append("[bold]Auth:[/bold]     [dim]nicht gesetzt[/dim]")
    lines.append(f"[bold]Sprache:[/bold]  {cfg.get('language', 'de')}")

    console.print(Panel(
        "\n".join(lines),
        title=f"[cyan]{s('config_title')}[/cyan]",
        border_style="cyan",
    ))


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Key: url, auth, language"),
    value: str = typer.Argument(..., help="Wert"),
):
    """Konfigurationswert setzen."""
    cfg = load_config()

    if key == "url":
        cfg["url"] = value.rstrip("/")
    elif key == "auth":
        if ":" not in value:
            err_console.print("[yellow]Format: user:password[/yellow]")
            raise typer.Exit(1)
        parts = value.split(":", 1)
        cfg["auth_user"] = parts[0]
        cfg["auth_password"] = parts[1]
    elif key == "language":
        if value not in ("de", "en"):
            err_console.print("[yellow]Erlaubt: de, en[/yellow]")
            raise typer.Exit(1)
        cfg["language"] = value
    else:
        err_console.print(f"[yellow]{s('config_invalid_key', key=key)}[/yellow]")
        raise typer.Exit(1)

    save_config(cfg)
    display_value = "****" if key == "auth" else value
    console.print(f"[green]{s('config_saved', key=key, value=display_value)}[/green]")


# ── status ───────────────────────────────────────────────────────────────────

@app.command()
def status():
    """Health Check + Dashboard-Statistiken."""
    cfg = load_config()

    # Health
    try:
        health = _api_get("/settings/health")
        health_ok = True
    except SystemExit:
        health_ok = False
        health = {}

    # Analytics (optional, endpoint may not exist on older servers)
    stats = _api_get_safe("/analytics/overview") if health_ok else None

    lines = []
    if health_ok:
        lines.append(f"[green]{s('status_healthy')}[/green]  {cfg.get('url', '?')}")
        lines.append(f"[bold]App:[/bold]     {health.get('app_name', '?')}")
        lines.append(f"[bold]Version:[/bold] {health.get('version', '?')}")

        providers = health.get("providers", {})
        if providers:
            lines.append("")
            lines.append("[bold]LLM Provider:[/bold]")
            for name, info in providers.items():
                if isinstance(info, bool):
                    status_str = "available" if info else "unavailable"
                elif isinstance(info, dict):
                    status_str = info.get("status", "?")
                else:
                    status_str = str(info)
                color = "green" if status_str == "available" else "red"
                lines.append(f"  [{color}]{name}: {status_str}[/{color}]")
    else:
        lines.append(f"[red]{s('status_unhealthy')}[/red]  {cfg.get('url', '?')}")

    if stats:
        lines.append("")
        lines.append("[bold]Dashboard:[/bold]")
        lines.append(f"  Conversations: {stats.get('conversations', 0)}")
        lines.append(f"  Messages:      {stats.get('messages', 0)}")
        lines.append(f"  Agents:        {stats.get('agents', 0)}")
        lines.append(f"  Tool Calls:    {stats.get('tool_calls', 0)}")
        lines.append(f"  Approval Rate: {stats.get('approval_rate', 0)}%")
        lines.append(f"  Tasks:         {stats.get('active_tasks', 0)}")
        lines.append(f"  Workflows:     {stats.get('workflows', 0)}")
        lines.append(f"  Skills:        {stats.get('active_skills', 0)}")

    console.print(Panel(
        "\n".join(lines),
        title=f"[cyan]{s('status_title')}[/cyan]",
        border_style="cyan",
    ))


# ── version ──────────────────────────────────────────────────────────────────

@app.command()
def version():
    """CLI- und Server-Version anzeigen."""
    lines = [f"[bold]Axon CLI:[/bold]    v{CLI_VERSION}"]

    try:
        health = _api_get("/settings/health")
        lines.append(f"[bold]Axon Server:[/bold] v{health.get('version', '?')}")
    except SystemExit:
        lines.append("[bold]Axon Server:[/bold] [red]nicht erreichbar[/red]")

    console.print(Panel(
        "\n".join(lines),
        title=f"[cyan]{s('version_title')}[/cyan]",
        border_style="cyan",
    ))


# ──────────────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
