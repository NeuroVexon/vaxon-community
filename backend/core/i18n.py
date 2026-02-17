"""
Axon by NeuroVexon - Backend i18n Module

Simple translation module for backend strings.
Uses Accept-Language header from frontend requests.
"""

from typing import Optional
from contextvars import ContextVar

_current_language: ContextVar[str] = ContextVar("lang", default="de")

TRANSLATIONS = {
    "de": {
        # Orchestrator
        "orch.agent_no_access": "Agent '{agent}' hat keinen Zugriff auf {tool}",
        "orch.tool_not_allowed": "Tool {tool} ist fuer diesen Agent nicht erlaubt.",
        "orch.tool_blocked": "Tool wurde vom Benutzer blockiert",
        "orch.tool_blocked_msg": "Tool {tool} wurde blockiert.",
        "orch.user_rejected": "Benutzer hat {tool} abgelehnt.",
        # Chat
        "chat.agent_not_found": "Agent nicht gefunden oder deaktiviert",
        "chat.intro_default": "Ich bin Axon, dein KI-Assistent.",
        "chat.intro_agent": "Ich bin {name}, dein KI-Assistent.",
        "chat.docs_uploaded": "Der User hat folgende Dokumente hochgeladen:",
        # Upload
        "upload.no_filename": "Kein Dateiname",
        "upload.type_not_allowed": "Dateityp nicht erlaubt. Erlaubt: {allowed}",
        "upload.too_large": "Datei zu gross (max {max_mb} MB)",
        "upload.not_found": "Dokument nicht gefunden",
        # Settings
        "settings.not_configured": "Nicht konfiguriert",
        # Scheduler
        "scheduler.started": "TaskScheduler gestartet",
        "scheduler.stopped": "TaskScheduler gestoppt",
        "scheduler.too_many": "Zu viele Tasks ({count}), nur die ersten {max} werden geplant",
        "scheduler.task_scheduled": "Task '{name}' geplant: {cron}",
        "scheduler.task_schedule_error": "Fehler beim Planen von Task '{name}': {error}",
        "scheduler.executing": "Fuehre Task '{name}' aus...",
        "scheduler.success": "Task '{name}' erfolgreich",
        "scheduler.timeout": "Timeout nach {seconds}s",
        "scheduler.error": "Fehler: {error}",
        "scheduler.no_result": "Kein Ergebnis",
        "scheduler.invalid_provider": "Ungueltiger LLM Provider: {provider}",
        "scheduler.intro": "Ich bin Axon. Ich fuehre jetzt den geplanten Task '{name}' aus.",
        "scheduler.no_response": "Keine Antwort vom LLM",
        "scheduler.not_found": "Task nicht gefunden",
        # Tool handlers
        "tool.memory_saved": "Gespeichert: '{key}' — {content}",
        "tool.memory_not_found": "Keine Erinnerungen gefunden.",
        "tool.memory_deleted": "Erinnerung '{key}' geloescht.",
        "tool.memory_key_not_found": "Keine Erinnerung mit Key '{key}' gefunden.",
        # Workflows
        "wf.not_found": "Workflow {id} nicht gefunden",
        "wf.no_steps": "Workflow hat keine Steps",
        "wf.too_many_steps": "Workflow hat zu viele Steps (max {max})",
        "wf.invalid_provider": "Ungueltiger LLM Provider: {provider}",
        "wf.step_intro": "Ich fuehre Workflow '{name}' aus, Step {step}/{total}.",
        "wf.no_response": "Keine Antwort",
        "wf.var_missing": "[{var} nicht vorhanden]",
        # Tool descriptions (DE)
        "tool.desc.file_read": "Liest den Inhalt einer Datei",
        "tool.desc.file_write": "Schreibt Inhalt in eine Datei (nur im /outputs/ Verzeichnis)",
        "tool.desc.file_list": "Listet Dateien in einem Verzeichnis auf",
        "tool.desc.web_fetch": "Ruft Inhalte von einer URL ab",
        "tool.desc.web_search": "Durchsucht das Web mit DuckDuckGo",
        "tool.desc.shell_execute": "Fuehrt einen Shell-Befehl aus (nur Whitelist)",
        "tool.desc.memory_save": "Speichert einen Fakt im Langzeitgedaechtnis",
        "tool.desc.memory_search": "Durchsucht das Langzeitgedaechtnis nach relevanten Fakten",
        "tool.desc.memory_delete": "Loescht einen Eintrag aus dem Langzeitgedaechtnis",
        "tool.desc.email_inbox": "Liest ungelesene E-Mails, durchsucht den Posteingang oder liest eine bestimmte E-Mail",
        "tool.desc.email_send": "Sendet eine E-Mail (IMMER mit Genehmigung)",
        "tool.desc.code_execute": "Fuehrt Python-Code in einer sicheren Docker-Sandbox aus (kein Netzwerk, isoliert)",
        # Telegram / Discord Bot
        "bot.access_denied": "Zugriff verweigert.",
        "bot.welcome": "Willkommen bei Axon by NeuroVexon!\n\nSende mir eine Nachricht und ich leite sie an die KI weiter.\nWenn ein Tool ausgefuehrt werden soll, bekommst du Buttons zur Genehmigung.",
        "bot.commands": "Befehle:\n/new - Neuer Chat\n/status - Aktueller Status\n/agents - Agent-Liste\n/agent <name> - Agent wechseln",
        "bot.new_chat": "Neuer Chat gestartet.",
        "bot.thinking": "Axon denkt nach...",
        "bot.error": "Fehler: {error}",
        "bot.approval_error": "Fehler bei Approval: {error}",
        "bot.allow_once": "Erlauben",
        "bot.allow_session": "Session",
        "bot.reject": "Ablehnen",
        "bot.decision_once": "Einmal erlaubt",
        "bot.decision_session": "Fuer Session erlaubt",
        "bot.decision_never": "Abgelehnt",
        "bot.decision_label": "Entscheidung: {decision}",
        "bot.tool_request": "Tool-Anfrage: {tool}",
        "bot.tool_executed": "Tool {tool} ausgefuehrt ({time}ms)",
        "bot.tool_rejected": "Tool {tool} abgelehnt.",
        "bot.status": "Session: {session}\nAgent: {agent}\nOffene Approvals: {pending}",
        "bot.agents_list": "Verfuegbare Agents:\n{agents}",
        "bot.agent_switched": "Agent gewechselt: {name}",
        "bot.agent_not_found": "Agent '{name}' nicht gefunden. Nutze /agents fuer eine Liste.",
        "bot.no_agents": "Keine Agents konfiguriert.",
        "bot.started": "Axon {channel} Bot gestartet",
        "bot.no_token": "{channel} Bot Token nicht gesetzt.",
    },
    "en": {
        # Orchestrator
        "orch.agent_no_access": "Agent '{agent}' does not have access to {tool}",
        "orch.tool_not_allowed": "Tool {tool} is not allowed for this agent.",
        "orch.tool_blocked": "Tool was blocked by the user",
        "orch.tool_blocked_msg": "Tool {tool} was blocked.",
        "orch.user_rejected": "User rejected {tool}.",
        # Chat
        "chat.agent_not_found": "Agent not found or disabled",
        "chat.intro_default": "I am Axon, your AI assistant.",
        "chat.intro_agent": "I am {name}, your AI assistant.",
        "chat.docs_uploaded": "The user has uploaded the following documents:",
        # Upload
        "upload.no_filename": "No filename provided",
        "upload.type_not_allowed": "File type not allowed. Allowed: {allowed}",
        "upload.too_large": "File too large (max {max_mb} MB)",
        "upload.not_found": "Document not found",
        # Settings
        "settings.not_configured": "Not configured",
        # Scheduler
        "scheduler.started": "TaskScheduler started",
        "scheduler.stopped": "TaskScheduler stopped",
        "scheduler.too_many": "Too many tasks ({count}), only the first {max} will be scheduled",
        "scheduler.task_scheduled": "Task '{name}' scheduled: {cron}",
        "scheduler.task_schedule_error": "Error scheduling task '{name}': {error}",
        "scheduler.executing": "Executing task '{name}'...",
        "scheduler.success": "Task '{name}' completed successfully",
        "scheduler.timeout": "Timeout after {seconds}s",
        "scheduler.error": "Error: {error}",
        "scheduler.no_result": "No result",
        "scheduler.invalid_provider": "Invalid LLM provider: {provider}",
        "scheduler.intro": "I am Axon. I am now executing the scheduled task '{name}'.",
        "scheduler.no_response": "No response from LLM",
        "scheduler.not_found": "Task not found",
        # Tool handlers
        "tool.memory_saved": "Saved: '{key}' — {content}",
        "tool.memory_not_found": "No memories found.",
        "tool.memory_deleted": "Memory '{key}' deleted.",
        "tool.memory_key_not_found": "No memory with key '{key}' found.",
        # Workflows
        "wf.not_found": "Workflow {id} not found",
        "wf.no_steps": "Workflow has no steps",
        "wf.too_many_steps": "Workflow has too many steps (max {max})",
        "wf.invalid_provider": "Invalid LLM provider: {provider}",
        "wf.step_intro": "I am executing workflow '{name}', step {step}/{total}.",
        "wf.no_response": "No response",
        "wf.var_missing": "[{var} not available]",
        # Tool descriptions (EN)
        "tool.desc.file_read": "Read the contents of a file",
        "tool.desc.file_write": "Write content to a file (only in /outputs/ directory)",
        "tool.desc.file_list": "List files in a directory",
        "tool.desc.web_fetch": "Fetch content from a URL",
        "tool.desc.web_search": "Search the web using DuckDuckGo",
        "tool.desc.shell_execute": "Execute a shell command (whitelist only)",
        "tool.desc.memory_save": "Save a fact to persistent memory",
        "tool.desc.memory_search": "Search persistent memory for relevant facts",
        "tool.desc.memory_delete": "Delete an entry from persistent memory",
        "tool.desc.email_inbox": "Read unread emails, search inbox, or read a specific email",
        "tool.desc.email_send": "Send an email (ALWAYS requires approval)",
        "tool.desc.code_execute": "Execute Python code in a secure Docker sandbox (no network, isolated)",
        # Telegram / Discord Bot
        "bot.access_denied": "Access denied.",
        "bot.welcome": "Welcome to Axon by NeuroVexon!\n\nSend me a message and I'll forward it to the AI.\nWhen a tool needs to run, you'll get approval buttons.",
        "bot.commands": "Commands:\n/new - New chat\n/status - Current status\n/agents - Agent list\n/agent <name> - Switch agent",
        "bot.new_chat": "New chat started.",
        "bot.thinking": "Axon is thinking...",
        "bot.error": "Error: {error}",
        "bot.approval_error": "Approval error: {error}",
        "bot.allow_once": "Allow",
        "bot.allow_session": "Session",
        "bot.reject": "Reject",
        "bot.decision_once": "Allowed once",
        "bot.decision_session": "Allowed for session",
        "bot.decision_never": "Rejected",
        "bot.decision_label": "Decision: {decision}",
        "bot.tool_request": "Tool request: {tool}",
        "bot.tool_executed": "Tool {tool} executed ({time}ms)",
        "bot.tool_rejected": "Tool {tool} rejected.",
        "bot.status": "Session: {session}\nAgent: {agent}\nPending approvals: {pending}",
        "bot.agents_list": "Available agents:\n{agents}",
        "bot.agent_switched": "Agent switched: {name}",
        "bot.agent_not_found": "Agent '{name}' not found. Use /agents for a list.",
        "bot.no_agents": "No agents configured.",
        "bot.started": "Axon {channel} bot started",
        "bot.no_token": "{channel} bot token not set.",
    },
}


def set_language(lang: str):
    """Set language for the current request/coroutine"""
    _current_language.set(lang)


def get_language() -> str:
    """Get current language (default: de)"""
    return _current_language.get()


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Translate a key to the given language.

    Args:
        key: Translation key (e.g. 'upload.no_filename')
        lang: Language code ('de' or 'en'). Uses current thread language if None.
        **kwargs: Variables for string interpolation

    Returns:
        Translated string
    """
    lang = lang or get_language()
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["de"])
    text = translations.get(key, TRANSLATIONS["de"].get(key, key))

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return text


def get_lang_from_header(accept_language: Optional[str]) -> str:
    """Parse Accept-Language header and return 'de' or 'en'"""
    if not accept_language:
        return "de"
    lang = accept_language.strip().lower().split(",")[0].split("-")[0]
    return lang if lang in ("de", "en") else "de"
