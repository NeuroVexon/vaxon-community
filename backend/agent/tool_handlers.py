"""
Axon by NeuroVexon - Tool Handlers
"""

import os
import asyncio
import httpx
from pathlib import Path
from typing import Any
import logging

from core.config import settings
from core.security import validate_path, validate_url, validate_shell_command, sanitize_filename

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Error during tool execution"""
    pass


async def execute_tool(tool_name: str, params: dict, db_session=None) -> Any:
    """Execute a tool and return the result"""
    handlers = {
        "file_read": handle_file_read,
        "file_write": handle_file_write,
        "file_list": handle_file_list,
        "web_fetch": handle_web_fetch,
        "web_search": handle_web_search,
        "shell_execute": handle_shell_execute,
        "memory_save": handle_memory_save,
        "memory_search": handle_memory_search,
        "memory_delete": handle_memory_delete,
        # code_execute: Entfernt in v1.0 — Docker-Sandbox geplant für v1.1
    }

    # Memory tools need db_session
    if tool_name.startswith("memory_") and db_session:
        params["_db_session"] = db_session

    handler = handlers.get(tool_name)
    if not handler:
        raise ToolExecutionError(f"Unknown tool: {tool_name}")

    return await handler(params)


async def handle_file_read(params: dict) -> str:
    """Read a file"""
    path = params.get("path")
    encoding = params.get("encoding", "utf-8")

    if not path:
        raise ToolExecutionError("Missing 'path' parameter")

    # Security: Validate path using central security module
    if not validate_path(path):
        raise ToolExecutionError(f"Access denied: {path}")

    try:
        # Check file size
        file_size = os.path.getsize(path)
        max_size = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            raise ToolExecutionError(f"File too large: {file_size / 1024 / 1024:.2f}MB (max: {settings.max_file_size_mb}MB)")

        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        raise ToolExecutionError(f"File not found: {path}")
    except PermissionError:
        raise ToolExecutionError(f"Permission denied: {path}")
    except Exception as e:
        raise ToolExecutionError(f"Error reading file: {e}")


async def handle_file_write(params: dict) -> str:
    """Write to a file (only in outputs directory)"""
    filename = params.get("filename")
    content = params.get("content")

    if not filename or content is None:
        raise ToolExecutionError("Missing 'filename' or 'content' parameter")

    # Security: Only allow writing to outputs directory
    outputs_dir = Path(settings.outputs_dir).resolve()
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename using central security module
    safe_filename = sanitize_filename(filename)
    output_path = outputs_dir / safe_filename

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written: {output_path}"
    except Exception as e:
        raise ToolExecutionError(f"Error writing file: {e}")


async def handle_file_list(params: dict) -> list[dict]:
    """List files in a directory"""
    path = params.get("path", ".")
    recursive = params.get("recursive", False)

    # Security: Validate path
    if not validate_path(path):
        raise ToolExecutionError(f"Access denied: {path}")

    try:
        path_obj = Path(path)
        if not path_obj.exists():
            raise ToolExecutionError(f"Directory not found: {path}")
        if not path_obj.is_dir():
            raise ToolExecutionError(f"Not a directory: {path}")

        files = []
        if recursive:
            for item in path_obj.rglob("*"):
                if len(files) >= 100:  # Limit
                    break
                files.append({
                    "name": str(item.relative_to(path_obj)),
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
        else:
            for item in path_obj.iterdir():
                files.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })

        return files
    except Exception as e:
        raise ToolExecutionError(f"Error listing directory: {e}")


async def handle_web_fetch(params: dict) -> str:
    """Fetch content from a URL"""
    url = params.get("url")
    method = params.get("method", "GET").upper()

    if not url:
        raise ToolExecutionError("Missing 'url' parameter")

    # Security: Validate URL using central security module
    if not validate_url(url):
        raise ToolExecutionError(f"Access denied: {url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url)
            return response.text[:10000]  # Truncate large responses
    except Exception as e:
        raise ToolExecutionError(f"Error fetching URL: {e}")


async def handle_web_search(params: dict) -> list[dict]:
    """Search the web using DuckDuckGo"""
    query = params.get("query")
    max_results = params.get("max_results", 5)

    if not query:
        raise ToolExecutionError("Missing 'query' parameter")

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]
    except ImportError:
        raise ToolExecutionError("duckduckgo-search package not installed")
    except Exception as e:
        raise ToolExecutionError(f"Error searching: {e}")


async def handle_shell_execute(params: dict) -> str:
    """Execute a shell command (whitelist only)"""
    command = params.get("command")

    if not command:
        raise ToolExecutionError("Missing 'command' parameter")

    # Security: Validate command using central security module
    is_valid, error_msg = validate_shell_command(command)
    if not is_valid:
        raise ToolExecutionError(error_msg)

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30.0
        )

        output = stdout.decode("utf-8", errors="replace")
        if stderr:
            output += "\n[stderr]\n" + stderr.decode("utf-8", errors="replace")

        return output[:5000]  # Truncate
    except asyncio.TimeoutError:
        raise ToolExecutionError("Command timed out after 30 seconds")
    except Exception as e:
        raise ToolExecutionError(f"Error executing command: {e}")


    # code_execute: Entfernt in v1.0 — RestrictedPython ist keine sichere Sandbox.
    # Docker-basierte Sandbox geplant für v1.1


async def handle_memory_save(params: dict) -> str:
    """Save a fact to persistent memory"""
    from agent.memory import MemoryManager

    key = params.get("key")
    content = params.get("content")
    category = params.get("category")
    db_session = params.pop("_db_session", None)

    if not key:
        raise ToolExecutionError("Missing 'key' parameter")
    # Fallback: use key as content if model forgot to fill content
    if not content:
        content = key

    if not db_session:
        raise ToolExecutionError("Memory tools require a database session")

    manager = MemoryManager(db_session)
    memory = await manager.add(key=key, content=content, source="agent", category=category)
    await db_session.commit()
    return f"Gespeichert: '{key}' — {content[:100]}"


async def handle_memory_search(params: dict) -> str:
    """Search persistent memory"""
    from agent.memory import MemoryManager

    query = params.get("query")
    db_session = params.pop("_db_session", None)

    if not query:
        raise ToolExecutionError("Missing 'query' parameter")

    if not db_session:
        raise ToolExecutionError("Memory tools require a database session")

    manager = MemoryManager(db_session)
    results = await manager.search(query, limit=10)

    if not results:
        return "Keine Erinnerungen gefunden."

    lines = []
    for mem in results:
        cat = f" [{mem.category}]" if mem.category else ""
        lines.append(f"- {mem.key}{cat}: {mem.content}")
    return "\n".join(lines)


async def handle_memory_delete(params: dict) -> str:
    """Delete a memory entry by key"""
    from agent.memory import MemoryManager

    key = params.get("key")
    db_session = params.pop("_db_session", None)

    if not key:
        raise ToolExecutionError("Missing 'key' parameter")

    if not db_session:
        raise ToolExecutionError("Memory tools require a database session")

    manager = MemoryManager(db_session)
    deleted = await manager.remove_by_key(key)
    await db_session.commit()

    if deleted:
        return f"Erinnerung '{key}' gelöscht."
    return f"Keine Erinnerung mit Key '{key}' gefunden."
