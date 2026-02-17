"""
Axon by NeuroVexon - Workflow Engine

Mehrstufige Agent-Aufgaben mit Template-Variablen und Approval-Modes.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Workflow, WorkflowRun, Settings as SettingsModel
from llm.router import llm_router
from llm.provider import ChatMessage
from core.config import LLMProvider
from core.i18n import t

logger = logging.getLogger(__name__)

# Safety limits
MAX_STEPS = 20
STEP_TIMEOUT_SECONDS = 120
MAX_CONTEXT_SIZE = 50000  # Zeichen


class WorkflowEngine:
    """Fuehrt Workflows mit Variablen-Kontext aus"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_trigger(self, message: str) -> Optional[Workflow]:
        """Pruefen ob eine Nachricht einen Workflow-Trigger enthaelt"""
        result = await self.db.execute(
            select(Workflow).where(
                Workflow.enabled,
                Workflow.trigger_phrase.isnot(None)
            )
        )
        workflows = result.scalars().all()

        message_lower = message.lower().strip()
        for wf in workflows:
            if wf.trigger_phrase and wf.trigger_phrase.lower() in message_lower:
                return wf
        return None

    async def execute_workflow(
        self,
        workflow_id: str,
        on_step_start: Optional[callable] = None,
        on_step_result: Optional[callable] = None,
    ) -> WorkflowRun:
        """Workflow ausfuehren"""
        workflow = await self.db.get(Workflow, workflow_id)
        if not workflow:
            raise ValueError(t("wf.not_found", id=workflow_id))

        if not workflow.steps or len(workflow.steps) == 0:
            raise ValueError(t("wf.no_steps"))

        if len(workflow.steps) > MAX_STEPS:
            raise ValueError(t("wf.too_many_steps", max=MAX_STEPS))

        # Run-Eintrag erstellen
        run = WorkflowRun(
            workflow_id=workflow.id,
            status="running",
            current_step=0,
            context={},
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)

        # LLM Provider laden
        result = await self.db.execute(select(SettingsModel))
        db_settings = {s.key: s.value for s in result.scalars().all()}
        current_provider = db_settings.get("llm_provider", "ollama")
        llm_router.update_settings(db_settings)

        try:
            provider = llm_router.get_provider(LLMProvider(current_provider))
        except ValueError:
            run.status = "failed"
            run.error = t("wf.invalid_provider", provider=current_provider)
            await self.db.commit()
            return run

        # Steps ausfuehren
        context = {}
        sorted_steps = sorted(workflow.steps, key=lambda s: s.get("order", 0))

        for i, step in enumerate(sorted_steps):
            run.current_step = i + 1
            await self.db.commit()

            prompt = step.get("prompt", "")
            store_as = step.get("store_as", f"step_{i+1}")

            # Template-Variablen ersetzen: {{variable}}
            resolved_prompt = self._resolve_variables(prompt, context)

            if on_step_start:
                try:
                    await on_step_start(i + 1, len(sorted_steps), resolved_prompt, store_as)
                except Exception:
                    pass

            logger.info(f"Workflow '{workflow.name}' Step {i+1}/{len(sorted_steps)}: {store_as}")

            try:
                messages = [
                    ChatMessage(
                        role="assistant",
                        content=t("wf.step_intro", name=workflow.name, step=i+1, total=len(sorted_steps))
                    ),
                    ChatMessage(role="user", content=resolved_prompt)
                ]
                response = await provider.chat(messages)
                result_text = response.content or t("wf.no_response")

                # Im Kontext speichern
                context[store_as] = result_text[:MAX_CONTEXT_SIZE]
                run.context = context

                if on_step_result:
                    try:
                        await on_step_result(i + 1, store_as, result_text)
                    except Exception:
                        pass

            except Exception as e:
                logger.error(f"Workflow '{workflow.name}' Step {i+1} Fehler: {e}")
                run.status = "failed"
                run.error = f"Step {i+1} ({store_as}): {str(e)[:500]}"
                run.context = context
                await self.db.commit()
                return run

        # Erfolgreich abgeschlossen
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        run.context = context
        await self.db.commit()
        await self.db.refresh(run)

        logger.info(f"Workflow '{workflow.name}' abgeschlossen")
        return run

    def _resolve_variables(self, template: str, context: dict) -> str:
        """Ersetzt {{variable}} mit Werten aus dem Kontext"""
        def replace(match):
            var_name = match.group(1).strip()
            return context.get(var_name, t("wf.var_missing", var=var_name))

        return re.sub(r"\{\{(.+?)\}\}", replace, template)


def workflow_to_dict(wf: Workflow) -> dict:
    return {
        "id": wf.id,
        "name": wf.name,
        "description": wf.description,
        "trigger_phrase": wf.trigger_phrase,
        "agent_id": wf.agent_id,
        "steps": wf.steps or [],
        "approval_mode": wf.approval_mode,
        "enabled": wf.enabled,
        "created_at": wf.created_at.isoformat(),
        "updated_at": wf.updated_at.isoformat(),
    }


def run_to_dict(run: WorkflowRun) -> dict:
    return {
        "id": run.id,
        "workflow_id": run.workflow_id,
        "status": run.status,
        "current_step": run.current_step,
        "context": run.context,
        "error": run.error,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }
