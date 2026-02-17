"""
Axon by NeuroVexon - Code Sandbox (Docker)

Docker-basierte Code-Ausfuehrung mit Isolation:
- Kein Netzwerk (--network none)
- Memory-Limit (256MB)
- CPU-Limit (0.5 CPUs)
- Read-only Filesystem
- Non-root User
- Auto-Remove Container
"""

import asyncio
import logging
import os
import tempfile
import time

logger = logging.getLogger(__name__)

# Safety limits
MAX_TIMEOUT = 60  # Sekunden
MAX_OUTPUT_LENGTH = 10000  # Zeichen
MAX_CONCURRENT = 3
DEFAULT_MEMORY = "256m"
DEFAULT_CPUS = "0.5"

SANDBOX_IMAGE = "axon-sandbox:latest"

# Semaphore fuer max gleichzeitige Container
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)


class SandboxResult:
    """Ergebnis einer Sandbox-Ausfuehrung"""

    def __init__(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        execution_time_ms: int,
        timed_out: bool = False,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.execution_time_ms = execution_time_ms
        self.timed_out = timed_out

    def to_dict(self) -> dict:
        return {
            "stdout": self.stdout[:MAX_OUTPUT_LENGTH],
            "stderr": self.stderr[:MAX_OUTPUT_LENGTH],
            "exit_code": self.exit_code,
            "execution_time_ms": self.execution_time_ms,
            "timed_out": self.timed_out,
        }

    def __str__(self) -> str:
        output = self.stdout
        if self.stderr:
            output += f"\n[stderr]\n{self.stderr}"
        if self.timed_out:
            output += f"\n[Timeout nach {self.execution_time_ms}ms]"
        return output[:MAX_OUTPUT_LENGTH]


async def _check_docker() -> bool:
    """Prueft ob Docker verfuegbar ist"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "info",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0
    except Exception:
        return False


async def _check_image_exists() -> bool:
    """Prueft ob das Sandbox-Image existiert"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "image",
            "inspect",
            SANDBOX_IMAGE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0
    except Exception:
        return False


async def build_sandbox_image() -> bool:
    """Baut das Sandbox Docker Image"""
    dockerfile_path = os.path.join(os.path.dirname(__file__), "Dockerfile.sandbox")
    if not os.path.exists(dockerfile_path):
        logger.error("Dockerfile.sandbox nicht gefunden")
        return False

    try:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "build",
            "-t",
            SANDBOX_IMAGE,
            "-f",
            dockerfile_path,
            os.path.dirname(dockerfile_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, _stderr = await proc.wait(), None
        return proc.returncode == 0
    except Exception as e:
        logger.error(f"Sandbox Image Build fehlgeschlagen: {e}")
        return False


async def execute_code(
    code: str,
    language: str = "python",
    timeout: int = 30,
    memory: str = DEFAULT_MEMORY,
    cpus: str = DEFAULT_CPUS,
) -> SandboxResult:
    """
    Fuehrt Code in einer Docker-Sandbox aus.

    Args:
        code: Der auszufuehrende Code
        language: Programmiersprache (aktuell: python)
        timeout: Timeout in Sekunden (max 60)
        memory: Memory-Limit (z.B. "256m")
        cpus: CPU-Limit (z.B. "0.5")
    """
    if not await _check_docker():
        return SandboxResult(
            stdout="",
            stderr="Docker ist nicht verfuegbar. Code-Sandbox deaktiviert.",
            exit_code=1,
            execution_time_ms=0,
        )

    if not await _check_image_exists():
        return SandboxResult(
            stdout="",
            stderr=f"Sandbox Image '{SANDBOX_IMAGE}' nicht gefunden. Bitte mit 'docker build' erstellen.",
            exit_code=1,
            execution_time_ms=0,
        )

    timeout = min(timeout, MAX_TIMEOUT)

    # Fork-Bomb Detection
    dangerous_patterns = [
        ":(){ :|:& };:",
        "fork()",
        "os.fork",
        "while True: os.",
        "import subprocess; subprocess.Popen",
    ]
    code_lower = code.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in code_lower:
            return SandboxResult(
                stdout="",
                stderr=f"Sicherheitswarnung: Verdaechtiger Code erkannt ({pattern})",
                exit_code=1,
                execution_time_ms=0,
            )

    async with _semaphore:
        # Code in temporaere Datei schreiben
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix="axon_sandbox_"
        ) as f:
            f.write(code)
            code_file = f.name

        try:
            start_time = time.time()

            cmd = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                memory,
                "--cpus",
                cpus,
                "--read-only",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=64m",
                "--pids-limit",
                "50",
                "-v",
                f"{code_file}:/home/sandbox/code.py:ro",
                SANDBOX_IMAGE,
                "python3",
                "/home/sandbox/code.py",
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            timed_out = False
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                timed_out = True
                proc.kill()
                stdout_bytes, stderr_bytes = b"", b""
                # Kill container
                try:
                    await asyncio.create_subprocess_exec(
                        "docker",
                        "kill",
                        f"axon-sandbox-{os.getpid()}",
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                except Exception:
                    pass

            execution_time_ms = int((time.time() - start_time) * 1000)

            stdout = stdout_bytes.decode("utf-8", errors="replace")[:MAX_OUTPUT_LENGTH]
            stderr = stderr_bytes.decode("utf-8", errors="replace")[:MAX_OUTPUT_LENGTH]

            return SandboxResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=proc.returncode or 0,
                execution_time_ms=execution_time_ms,
                timed_out=timed_out,
            )

        finally:
            # Temporaere Datei loeschen
            try:
                os.unlink(code_file)
            except Exception:
                pass
