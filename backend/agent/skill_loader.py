"""
Axon by NeuroVexon - Skill Loader

Lädt, validiert und verwaltet Skills (Plugin-Module).
Jeder Skill ist eine Python-Datei mit definierter Struktur.

Sicherheit:
- Skills müssen explizit vom User approved werden
- File-Hash wird bei jedem Laden geprüft
- Änderungen am Skill-Code → automatische Revocation
"""

import hashlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import Skill

logger = logging.getLogger(__name__)

# Erwartete Skill-Struktur
REQUIRED_ATTRIBUTES = ["SKILL_NAME", "SKILL_DESCRIPTION", "SKILL_VERSION", "execute"]
SKILLS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills"
)


def compute_file_hash(file_path: str) -> str:
    """Berechnet SHA-256 Hash einer Datei"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_skill_module(file_path: str) -> tuple[bool, str, Optional[dict]]:
    """
    Validiert ob eine Datei ein gültiges Skill-Modul ist.
    Gibt (valid, error_msg, metadata) zurück.
    """
    if not os.path.isfile(file_path):
        return False, f"Datei nicht gefunden: {file_path}", None

    if not file_path.endswith(".py"):
        return False, "Skill muss eine .py Datei sein", None

    try:
        spec = importlib.util.spec_from_file_location("skill_check", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        return False, f"Fehler beim Laden: {e}", None

    missing = [attr for attr in REQUIRED_ATTRIBUTES if not hasattr(module, attr)]
    if missing:
        return False, f"Fehlende Attribute: {', '.join(missing)}", None

    if not callable(getattr(module, "execute", None)):
        return False, "execute muss eine Funktion sein", None

    metadata = {
        "name": getattr(module, "SKILL_NAME", ""),
        "description": getattr(module, "SKILL_DESCRIPTION", ""),
        "version": getattr(module, "SKILL_VERSION", "1.0.0"),
        "author": getattr(module, "SKILL_AUTHOR", None),
        "risk_level": getattr(module, "SKILL_RISK_LEVEL", "medium"),
        "display_name": getattr(
            module, "SKILL_DISPLAY_NAME", getattr(module, "SKILL_NAME", "")
        ),
        "parameters": getattr(module, "SKILL_PARAMETERS", {}),
    }

    return True, "", metadata


class SkillLoader:
    """Verwaltet das Laden und Ausführen von Skills"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._loaded_modules: dict[str, Any] = {}

    async def scan_skills_dir(self) -> list[dict]:
        """
        Scannt das Skills-Verzeichnis nach neuen/geänderten Skills.
        Gibt eine Liste von Skill-Infos zurück.
        """
        skills_path = Path(SKILLS_DIR)
        if not skills_path.exists():
            skills_path.mkdir(parents=True, exist_ok=True)
            return []

        found_skills = []
        for py_file in skills_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            valid, error, metadata = validate_skill_module(str(py_file))
            if not valid:
                logger.warning(f"Skill ungültig: {py_file.name} — {error}")
                continue

            file_hash = compute_file_hash(str(py_file))

            # Prüfen ob der Skill in der DB ist
            result = await self.db.execute(
                select(Skill).where(Skill.name == metadata["name"])
            )
            db_skill = result.scalar_one_or_none()

            if db_skill:
                # Hash-Check — hat sich die Datei geändert?
                if db_skill.file_hash != file_hash:
                    logger.warning(
                        f"Skill '{metadata['name']}' wurde geändert — Approval widerrufen"
                    )
                    db_skill.file_hash = file_hash
                    db_skill.approved = False
                    db_skill.enabled = False
                    await self.db.flush()

                found_skills.append(
                    {
                        "id": db_skill.id,
                        "name": db_skill.name,
                        "display_name": db_skill.display_name,
                        "description": db_skill.description,
                        "version": db_skill.version,
                        "enabled": db_skill.enabled,
                        "approved": db_skill.approved,
                        "risk_level": db_skill.risk_level,
                        "file_changed": db_skill.file_hash != file_hash,
                    }
                )
            else:
                # Neuer Skill — in DB registrieren (nicht approved)
                new_skill = Skill(
                    name=metadata["name"],
                    display_name=metadata.get("display_name", metadata["name"]),
                    description=metadata["description"],
                    file_path=str(py_file),
                    file_hash=file_hash,
                    version=metadata.get("version", "1.0.0"),
                    author=metadata.get("author"),
                    risk_level=metadata.get("risk_level", "medium"),
                    enabled=False,
                    approved=False,
                )
                self.db.add(new_skill)
                await self.db.flush()

                found_skills.append(
                    {
                        "id": new_skill.id,
                        "name": new_skill.name,
                        "display_name": new_skill.display_name,
                        "description": new_skill.description,
                        "version": new_skill.version,
                        "enabled": False,
                        "approved": False,
                        "risk_level": new_skill.risk_level,
                        "file_changed": False,
                    }
                )

        return found_skills

    async def load_skill(self, skill_name: str) -> Optional[Any]:
        """Lädt ein approved Skill-Modul in den Speicher"""
        result = await self.db.execute(select(Skill).where(Skill.name == skill_name))
        db_skill = result.scalar_one_or_none()

        if not db_skill:
            logger.warning(f"Skill nicht gefunden: {skill_name}")
            return None

        if not db_skill.approved or not db_skill.enabled:
            logger.warning(f"Skill nicht genehmigt oder deaktiviert: {skill_name}")
            return None

        # Integritätsprüfung
        current_hash = compute_file_hash(db_skill.file_path)
        if current_hash != db_skill.file_hash:
            logger.error(
                f"Skill '{skill_name}' — Datei-Hash stimmt nicht! Approval widerrufen."
            )
            db_skill.approved = False
            db_skill.enabled = False
            await self.db.flush()
            return None

        # Laden
        try:
            spec = importlib.util.spec_from_file_location(
                f"skill_{skill_name}", db_skill.file_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._loaded_modules[skill_name] = module
            return module
        except Exception as e:
            logger.error(f"Fehler beim Laden von Skill '{skill_name}': {e}")
            return None

    async def execute_skill(self, skill_name: str, params: dict) -> Any:
        """Führt einen Skill aus"""
        module = self._loaded_modules.get(skill_name)
        if not module:
            module = await self.load_skill(skill_name)

        if not module:
            raise RuntimeError(f"Skill '{skill_name}' konnte nicht geladen werden")

        execute_fn = getattr(module, "execute", None)
        if not execute_fn or not callable(execute_fn):
            raise RuntimeError(f"Skill '{skill_name}' hat keine execute-Funktion")

        # Async oder sync ausführen
        import asyncio

        if asyncio.iscoroutinefunction(execute_fn):
            return await execute_fn(params)
        return execute_fn(params)

    async def get_approved_skills(self) -> list[Skill]:
        """Gibt alle genehmigten und aktiven Skills zurück"""
        result = await self.db.execute(
            select(Skill).where(Skill.approved, Skill.enabled)
        )
        return list(result.scalars().all())
