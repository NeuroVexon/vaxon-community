"""
Axon by NeuroVexon - Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROQ = "groq"
    OPENROUTER = "openrouter"


class Settings(BaseSettings):
    # App
    app_name: str = "Axon by NeuroVexon"
    app_version: str = "2.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./axon.db"

    # LLM Provider
    llm_provider: LLMProvider = LLMProvider.OLLAMA

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Claude API
    anthropic_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-20250514"

    # OpenAI API
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"

    # Google Gemini API
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"

    # Groq API (OpenAI-compatible)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    # OpenRouter API (OpenAI-compatible)
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "anthropic/claude-sonnet-4"

    # Security
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"

    # Tool Execution
    outputs_dir: str = "./outputs"
    max_file_size_mb: int = 10
    code_execution_timeout: int = 30
    code_execution_memory_mb: int = 256

    # E-Mail Integration
    email_enabled: bool = False
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Telegram Integration
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_allowed_users: str = ""

    # Discord Integration
    discord_enabled: bool = False
    discord_bot_token: Optional[str] = None
    discord_allowed_channels: str = ""
    discord_allowed_users: str = ""

    # Shell Whitelist
    shell_whitelist: list[str] = [
        "ls",
        "dir",
        "cat",
        "type",
        "head",
        "tail",
        "wc",
        "grep",
        "find",
        "date",
        "pwd",
        "echo",
        "python --version",
        "python3 --version",
        "node --version",
        "npm --version",
        "pip list",
        "pip freeze",
        "npm list",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
