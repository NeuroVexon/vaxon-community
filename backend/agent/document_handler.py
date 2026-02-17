"""
Axon by NeuroVexon - Document Handler

Extrahiert Text aus hochgeladenen Dateien fuer den Chat-Kontext.
Unterstuetzte Formate: PDF, Text, Code, CSV, JSON, YAML, HTML, XML
"""

import csv
import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Erlaubte MIME-Types
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".xml",
    ".yaml",
    ".yml",
    ".png",
    ".jpg",
    ".jpeg",
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/csv",
    "text/html",
    "text/xml",
    "application/json",
    "application/xml",
    "text/x-python",
    "text/javascript",
    "text/typescript",
    "application/x-yaml",
    "text/yaml",
    "image/png",
    "image/jpeg",
}

MAX_TEXT_LENGTH = 8000  # Zeichen fuer Context


def is_allowed_file(filename: str) -> bool:
    """Prueft ob der Dateityp erlaubt ist"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def extract_text(file_path: str, mime_type: Optional[str] = None) -> str:
    """
    Extrahiert Text aus einer Datei.
    Gibt den extrahierten Text zurueck.
    """
    ext = Path(file_path).suffix.lower()

    try:
        # PDF
        if ext == ".pdf":
            return _extract_pdf(file_path)

        # Bilder — kein Text, nur Hinweis
        if ext in (".png", ".jpg", ".jpeg"):
            return f"[Bild: {os.path.basename(file_path)}]"

        # CSV
        if ext == ".csv":
            return _extract_csv(file_path)

        # JSON
        if ext == ".json":
            return _extract_json(file_path)

        # Alle anderen: als UTF-8 Text lesen
        return _extract_text(file_path)

    except Exception as e:
        logger.error(f"Text-Extraktion fehlgeschlagen fuer {file_path}: {e}")
        return f"[Konnte Text nicht extrahieren: {str(e)[:200]}]"


def _extract_pdf(file_path: str) -> str:
    """PDF Text extrahieren"""
    try:
        import fitz  # pymupdf

        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
            if len(text) > MAX_TEXT_LENGTH:
                break
        doc.close()
        return text[:MAX_TEXT_LENGTH]
    except ImportError:
        # Fallback wenn pymupdf nicht installiert
        return "[PDF-Extraktion benoetigt pymupdf. Bitte installieren: pip install pymupdf]"


def _extract_csv(file_path: str) -> str:
    """CSV als Tabelle extrahieren (erste 100 Zeilen)"""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        lines = []
        for i, row in enumerate(reader):
            if i >= 100:
                lines.append(f"... ({i}+ Zeilen insgesamt)")
                break
            lines.append(" | ".join(row))
    return "\n".join(lines)[:MAX_TEXT_LENGTH]


def _extract_json(file_path: str) -> str:
    """JSON formatiert ausgeben"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, indent=2, ensure_ascii=False)[:MAX_TEXT_LENGTH]


def _extract_text(file_path: str) -> str:
    """Plaintext/Code lesen"""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()[:MAX_TEXT_LENGTH]


def truncate_text(text: str, max_chars: int = MAX_TEXT_LENGTH) -> str:
    """Text kuerzen mit Hinweis"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[... gekuerzt, {len(text)} Zeichen insgesamt]"


def format_for_context(filename: str, extracted_text: str) -> str:
    """Formatiert ein Dokument als Context-Block fuer den LLM"""
    return (
        f"--- Dokument: {filename} ---\n"
        f"{truncate_text(extracted_text)}\n"
        f"--- Ende: {filename} ---"
    )
