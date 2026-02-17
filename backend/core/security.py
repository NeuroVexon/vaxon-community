"""
Axon by NeuroVexon - Security Utilities
"""

import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from cryptography.fernet import Fernet

from .config import settings

logger = logging.getLogger(__name__)


def generate_session_id() -> str:
    """Generate a secure random session ID"""
    return secrets.token_urlsafe(32)


def generate_secret_key() -> str:
    """Generate a secure secret key"""
    return secrets.token_hex(32)


def hash_string(value: str) -> str:
    """Hash a string using SHA-256"""
    return hashlib.sha256(value.encode()).hexdigest()


def _get_fernet() -> Fernet:
    """Get Fernet instance derived from secret_key"""
    # Derive a 32-byte key from the secret_key using SHA-256
    key_bytes = hashlib.sha256(settings.secret_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_value(value: str) -> str:
    """Encrypt a value using Fernet (derived from SECRET_KEY)"""
    if not value:
        return ""
    try:
        f = _get_fernet()
        return f.encrypt(value.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return ""


def decrypt_value(encrypted: str) -> str:
    """Decrypt a value using Fernet (derived from SECRET_KEY)"""
    if not encrypted:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return ""


def validate_path(path: str) -> bool:
    """
    Validate a file path for security.
    Returns False if path is suspicious.
    """
    # Normalize path
    path = path.replace("\\", "/").lower()

    # Block absolute paths to sensitive locations
    blocked_prefixes = [
        "/etc/",
        "/var/",
        "/root/",
        "/home/",
        "c:/windows/",
        "c:/program files/",
        "c:/users/",
        "/proc/",
        "/sys/",
    ]

    for prefix in blocked_prefixes:
        if path.startswith(prefix):
            return False

    # Block path traversal
    if ".." in path:
        return False

    # Block sensitive files
    blocked_files = [
        "passwd",
        "shadow",
        ".ssh",
        ".env",
        "credentials",
        "secrets",
        ".git/config",
        "id_rsa",
        "id_ed25519",
    ]

    for blocked in blocked_files:
        if blocked in path:
            return False

    return True


def validate_url(url: str) -> bool:
    """
    Validate a URL for security.
    Returns False if URL is suspicious.
    """
    url_lower = url.lower()

    # Block local/internal URLs
    blocked_hosts = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "169.254.",  # Link-local
        "10.",       # Private
        "172.16.",   # Private
        "172.17.",
        "172.18.",
        "172.19.",
        "172.20.",
        "172.21.",
        "172.22.",
        "172.23.",
        "172.24.",
        "172.25.",
        "172.26.",
        "172.27.",
        "172.28.",
        "172.29.",
        "172.30.",
        "172.31.",
        "192.168.", # Private
        "::1",      # IPv6 localhost
        "fe80:",    # IPv6 link-local
    ]

    for blocked in blocked_hosts:
        if blocked in url_lower:
            return False

    # Block file:// protocol
    if url_lower.startswith("file://"):
        return False

    return True


def validate_shell_command(command: str) -> tuple[bool, str]:
    """
    Validate a shell command against the whitelist.
    Returns (is_valid, error_message)
    """
    if not command or not command.strip():
        return False, "Empty command"

    # Block command chaining operators
    dangerous_operators = ["&&", "||", ";", "|", "`", "$(", "${"]
    for op in dangerous_operators:
        if op in command:
            return False, f"Command chaining not allowed: '{op}'"

    # Block redirects to sensitive locations
    if ">" in command and not command.strip().endswith(">"):
        return False, "Output redirection not allowed"

    # Get the base command (first word)
    parts = command.strip().split()
    base_cmd = parts[0].lower()

    # Check if command or base command is in whitelist
    whitelist = [cmd.lower() for cmd in settings.shell_whitelist]

    # Check exact match
    if command.lower() in whitelist:
        return True, ""

    # Check base command match (only first word)
    whitelist_bases = [cmd.split()[0] for cmd in whitelist]
    if base_cmd in whitelist_bases:
        return True, ""

    return False, f"Command '{base_cmd}' not in whitelist. Allowed: {', '.join(settings.shell_whitelist[:5])}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal.
    """
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")

    # Remove leading dots (hidden files)
    while filename.startswith("."):
        filename = filename[1:]

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")

    return filename or "unnamed"


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[datetime]] = {}

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Get requests for this key
        if key not in self._requests:
            self._requests[key] = []

        # Remove old requests
        self._requests[key] = [
            t for t in self._requests[key]
            if t > window_start
        ]

        # Check limit
        if len(self._requests[key]) >= self.max_requests:
            return False

        # Add this request
        self._requests[key].append(now)
        return True

    def reset(self, key: str) -> None:
        """Reset rate limit for a key"""
        self._requests.pop(key, None)


# Global rate limiter instance
rate_limiter = RateLimiter()
