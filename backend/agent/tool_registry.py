"""
Axon by NeuroVexon - Tool Registry
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel
from core.i18n import get_language


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # Never auto-approve


class ToolDefinition(BaseModel):
    name: str
    description: str
    description_de: str  # German description for UI
    parameters: Dict[str, Any]
    risk_level: RiskLevel
    requires_approval: bool = True

    class Config:
        arbitrary_types_allowed = True

    def get_description(self, lang: str = None) -> str:
        """Return description in the given language"""
        if lang is None:
            lang = get_language()
        return self.description_de if lang == "de" else self.description


class ToolRegistry:
    """Registry for all available tools"""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register all built-in tools"""

        # File Tools
        self.register(
            ToolDefinition(
                name="file_read",
                description="Read the contents of a file",
                description_de="Liest den Inhalt einer Datei",
                parameters={
                    "path": {
                        "type": "string",
                        "description": "Path to the file",
                        "required": True,
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding",
                        "default": "utf-8",
                    },
                },
                risk_level=RiskLevel.MEDIUM,
            )
        )

        self.register(
            ToolDefinition(
                name="file_write",
                description="Write content to a file (only in /outputs/ directory)",
                description_de="Schreibt Inhalt in eine Datei (nur im /outputs/ Verzeichnis)",
                parameters={
                    "filename": {
                        "type": "string",
                        "description": "Filename (saved in /outputs/)",
                        "required": True,
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write",
                        "required": True,
                    },
                },
                risk_level=RiskLevel.MEDIUM,
            )
        )

        self.register(
            ToolDefinition(
                name="file_list",
                description="List files in a directory",
                description_de="Listet Dateien in einem Verzeichnis auf",
                parameters={
                    "path": {
                        "type": "string",
                        "description": "Directory path",
                        "required": True,
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "List recursively",
                        "default": False,
                    },
                },
                risk_level=RiskLevel.LOW,
            )
        )

        # Web Tools
        self.register(
            ToolDefinition(
                name="web_fetch",
                description="Fetch content from a URL",
                description_de="Ruft Inhalte von einer URL ab",
                parameters={
                    "url": {
                        "type": "string",
                        "description": "URL to fetch",
                        "required": True,
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method",
                        "default": "GET",
                    },
                },
                risk_level=RiskLevel.MEDIUM,
            )
        )

        self.register(
            ToolDefinition(
                name="web_search",
                description="Search the web using DuckDuckGo",
                description_de="Durchsucht das Web mit DuckDuckGo",
                parameters={
                    "query": {
                        "type": "string",
                        "description": "Search query",
                        "required": True,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 5,
                    },
                },
                risk_level=RiskLevel.LOW,
                requires_approval=False,
            )
        )

        # Shell Tools (Restricted)
        self.register(
            ToolDefinition(
                name="shell_execute",
                description="Execute a shell command (whitelist only)",
                description_de="Führt einen Shell-Befehl aus (nur Whitelist)",
                parameters={
                    "command": {
                        "type": "string",
                        "description": "Command to execute",
                        "required": True,
                    }
                },
                risk_level=RiskLevel.HIGH,
            )
        )

        # Memory Tools
        self.register(
            ToolDefinition(
                name="memory_save",
                description="Save a fact to persistent memory for future conversations",
                description_de="Speichert einen Fakt im Langzeitgedächtnis",
                parameters={
                    "key": {
                        "type": "string",
                        "description": "Short topic/title for the memory",
                        "required": True,
                    },
                    "content": {
                        "type": "string",
                        "description": "The fact or information to remember",
                        "required": True,
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category (e.g. 'preference', 'fact', 'project')",
                    },
                },
                risk_level=RiskLevel.LOW,
                requires_approval=False,
            )
        )

        self.register(
            ToolDefinition(
                name="memory_search",
                description="Search persistent memory for relevant facts",
                description_de="Durchsucht das Langzeitgedächtnis nach relevanten Fakten",
                parameters={
                    "query": {
                        "type": "string",
                        "description": "Search query",
                        "required": True,
                    }
                },
                risk_level=RiskLevel.LOW,
                requires_approval=False,
            )
        )

        self.register(
            ToolDefinition(
                name="memory_delete",
                description="Delete a memory entry by key",
                description_de="Löscht einen Eintrag aus dem Langzeitgedächtnis",
                parameters={
                    "key": {
                        "type": "string",
                        "description": "The key of the memory to delete",
                        "required": True,
                    }
                },
                risk_level=RiskLevel.LOW,
                requires_approval=False,
            )
        )

        # E-Mail Tools
        self.register(
            ToolDefinition(
                name="email_inbox",
                description="Read unread emails, search inbox, or read a specific email. Actions: 'unread', 'search', 'read'",
                description_de="Liest ungelesene E-Mails, durchsucht den Posteingang oder liest eine bestimmte E-Mail",
                parameters={
                    "action": {
                        "type": "string",
                        "description": "Action: 'unread', 'search', or 'read'",
                        "required": True,
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (for action=search)",
                    },
                    "uid": {
                        "type": "string",
                        "description": "Email UID (for action=read)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results",
                        "default": 10,
                    },
                },
                risk_level=RiskLevel.MEDIUM,
            )
        )

        self.register(
            ToolDefinition(
                name="email_send",
                description="Send an email. ALWAYS requires approval — shows recipient, subject, and body before sending.",
                description_de="Sendet eine E-Mail (IMMER mit Genehmigung)",
                parameters={
                    "to": {
                        "type": "string",
                        "description": "Recipient email address",
                        "required": True,
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject",
                        "required": True,
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body (plain text)",
                        "required": True,
                    },
                },
                risk_level=RiskLevel.HIGH,
            )
        )

        # Code Execution (Docker Sandbox)
        self.register(
            ToolDefinition(
                name="code_execute",
                description="Execute Python code in a secure Docker sandbox (no network, memory limited, read-only)",
                description_de="Fuehrt Python-Code in einer sicheren Docker-Sandbox aus (kein Netzwerk, isoliert)",
                parameters={
                    "code": {
                        "type": "string",
                        "description": "Python code to execute",
                        "required": True,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (max 60)",
                        "default": 30,
                    },
                },
                risk_level=RiskLevel.HIGH,
            )
        )

    def register(self, tool: ToolDefinition):
        """Register a tool"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools"""
        return list(self._tools.values())

    def get_tools_for_llm(self) -> list[dict]:
        """Format tools for LLM function calling (OpenAI format)"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            k: {
                                "type": v.get("type", "string"),
                                "description": v.get("description", ""),
                            }
                            for k, v in tool.parameters.items()
                        },
                        "required": [
                            k
                            for k, v in tool.parameters.items()
                            if v.get("required", False)
                        ],
                    },
                },
            }
            for tool in self._tools.values()
        ]


# Global registry instance
tool_registry = ToolRegistry()
