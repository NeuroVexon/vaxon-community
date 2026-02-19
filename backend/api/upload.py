"""
Axon by NeuroVexon - Document Upload API
"""

import os
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from db.database import get_db
from db.models import UploadedDocument, User
from core.dependencies import get_current_active_user
from agent.document_handler import is_allowed_file, extract_text, ALLOWED_EXTENSIONS
from core.security import sanitize_filename
from core.i18n import t, set_language, get_lang_from_header

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = "data/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("")
async def upload_document(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Dokument hochladen und Text extrahieren"""
    set_language(get_lang_from_header(request.headers.get("accept-language")))

    if not file.filename:
        raise HTTPException(status_code=400, detail=t("upload.no_filename"))

    if not is_allowed_file(file.filename):
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=400, detail=t("upload.type_not_allowed", allowed=allowed)
        )

    # Datei lesen und Groesse pruefen
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=t("upload.too_large", max_mb=MAX_FILE_SIZE // 1024 // 1024),
        )

    # Speicherpfad erstellen
    safe_name = sanitize_filename(file.filename)
    upload_subdir = conversation_id or "general"
    upload_path = Path(UPLOAD_DIR) / upload_subdir
    upload_path.mkdir(parents=True, exist_ok=True)
    file_path = upload_path / safe_name

    # Datei speichern
    with open(file_path, "wb") as f:
        f.write(content)

    # Text extrahieren
    extracted = extract_text(str(file_path), file.content_type)

    # In DB speichern
    doc = UploadedDocument(
        conversation_id=conversation_id,
        filename=safe_name,
        mime_type=file.content_type,
        file_size=len(content),
        extracted_text=extracted,
        file_path=str(file_path),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "file_size": doc.file_size,
        "has_text": bool(extracted and not extracted.startswith("[")),
        "text_preview": extracted[:200] if extracted else "",
    }


@router.get("")
async def list_documents(
    current_user: User = Depends(get_current_active_user),
    conversation_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Dokumente auflisten"""
    query = select(UploadedDocument).order_by(UploadedDocument.created_at.desc())
    if conversation_id:
        query = query.where(UploadedDocument.conversation_id == conversation_id)
    query = query.limit(50)

    result = await db.execute(query)
    docs = result.scalars().all()

    return [
        {
            "id": d.id,
            "filename": d.filename,
            "mime_type": d.mime_type,
            "file_size": d.file_size,
            "conversation_id": d.conversation_id,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Dokument loeschen"""
    set_language(get_lang_from_header(request.headers.get("accept-language")))
    doc = await db.get(UploadedDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=t("upload.not_found"))

    # Datei loeschen
    try:
        if os.path.exists(doc.file_path):
            os.unlink(doc.file_path)
    except Exception as e:
        logger.warning(f"Konnte Datei nicht loeschen: {e}")

    await db.delete(doc)
    await db.commit()
    return {"status": "deleted"}
