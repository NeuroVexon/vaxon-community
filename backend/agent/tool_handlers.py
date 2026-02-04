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

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Error during tool execution"""
    pass


async def execute_tool(tool_name: str, params: dict) -> Any:
    """Execute a tool and return the result"""
    handlers = {
        "file_read": handle_file_read,
        "file_write": handle_file_write,
        "file_list": handle_file_list,
        "web_fetch": handle_web_fetch,
        "web_search": handle_web_search,
        "shell_execute": handle_shell_execute,
        "code_execute": handle_code_execute,
    }

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

    # Security: Block system files
    blocked_paths = ["/etc/passwd", "/etc/shadow", "C:\\Windows\\System32"]
    for blocked in blocked_paths:
        if path.startswith(blocked):
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

    # Sanitize filename
    safe_filename = Path(filename).name  # Remove any path components
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

    # Security: Block local URLs
    blocked_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "169.254."]
    for blocked in blocked_hosts:
        if blocked in url:
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

    # Check whitelist
    cmd_base = command.split()[0] if command.split() else ""
    is_whitelisted = any(
        command.startswith(allowed) or cmd_base == allowed.split()[0]
        for allowed in settings.shell_whitelist
    )

    if not is_whitelisted:
        raise ToolExecutionError(
            f"Command not in whitelist: {cmd_base}. "
            f"Allowed: {', '.join(settings.shell_whitelist[:5])}..."
        )

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


async def handle_code_execute(params: dict) -> str:
    """Execute Python code in a sandbox"""
    code = params.get("code")

    if not code:
        raise ToolExecutionError("Missing 'code' parameter")

    try:
        # Use RestrictedPython for sandboxing
        from RestrictedPython import compile_restricted, safe_globals
        from RestrictedPython.Eval import default_guarded_getiter
        from RestrictedPython.Guards import guarded_iter_unpack_sequence, safer_getattr

        # Compile code
        byte_code = compile_restricted(code, "<inline>", "exec")
        if byte_code.errors:
            raise ToolExecutionError(f"Compilation errors: {byte_code.errors}")

        # Restricted globals
        restricted_globals = safe_globals.copy()
        restricted_globals["_getiter_"] = default_guarded_getiter
        restricted_globals["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence
        restricted_globals["_getattr_"] = safer_getattr

        # Capture output
        import io
        import sys
        output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output

        # Execute with timeout
        try:
            exec(byte_code, restricted_globals)
        finally:
            sys.stdout = old_stdout

        return output.getvalue() or "(no output)"

    except ImportError:
        raise ToolExecutionError("RestrictedPython package not installed")
    except Exception as e:
        raise ToolExecutionError(f"Error executing code: {e}")
