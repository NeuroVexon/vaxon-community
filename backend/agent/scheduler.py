"""
Axon by NeuroVexon - Task Scheduler

Proaktive Aufgaben mit Cron-Ausdruecken und Approval-Gate.
Sicherheit: Max 10 aktive Tasks, Timeout 5 Min, max 1/min pro Task.
"""

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from db.models import ScheduledTask
from llm.router import llm_router
from llm.provider import ChatMessage
from core.config import LLMProvider
from core.i18n import t, set_language

logger = logging.getLogger(__name__)

# Safety limits
MAX_ACTIVE_TASKS = 10
TASK_TIMEOUT_SECONDS = 300  # 5 Minuten
MAX_RESULT_LENGTH = 5000


class TaskScheduler:
    """Verwaltet und fuehrt geplante Tasks aus"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._running = False

    def start(self):
        """Scheduler starten"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            logger.info("TaskScheduler gestartet")

    def stop(self):
        """Scheduler stoppen"""
        if self._running:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("TaskScheduler gestoppt")

    async def sync_tasks(self):
        """Tasks aus DB laden und Scheduler synchronisieren"""
        from db.database import async_session

        async with async_session() as db:
            result = await db.execute(
                select(ScheduledTask).where(ScheduledTask.enabled)
            )
            tasks = result.scalars().all()

            # Alle bestehenden Jobs entfernen
            existing_jobs = {job.id for job in self.scheduler.get_jobs()}
            for job_id in existing_jobs:
                if job_id.startswith("task_"):
                    self.scheduler.remove_job(job_id)

            # Safety: Max 10 Tasks
            active_tasks = tasks[:MAX_ACTIVE_TASKS]
            if len(tasks) > MAX_ACTIVE_TASKS:
                logger.warning(
                    f"Zu viele Tasks ({len(tasks)}), nur die ersten {MAX_ACTIVE_TASKS} werden geplant"
                )

            for task in active_tasks:
                try:
                    trigger = CronTrigger.from_crontab(task.cron_expression)
                    self.scheduler.add_job(
                        self._execute_task,
                        trigger=trigger,
                        id=f"task_{task.id}",
                        args=[task.id],
                        replace_existing=True,
                        misfire_grace_time=60,
                    )
                    logger.info(f"Task '{task.name}' geplant: {task.cron_expression}")
                except Exception as e:
                    logger.error(f"Fehler beim Planen von Task '{task.name}': {e}")

    async def _execute_task(self, task_id: str):
        """Task ausfuehren (wird vom Scheduler aufgerufen)"""
        from db.database import async_session

        async with async_session() as db:
            task = await db.get(ScheduledTask, task_id)
            if not task or not task.enabled:
                return

            # Load language from settings for scheduled context
            from db.models import Settings as SettingsModel
            lang_result = await db.execute(
                select(SettingsModel).where(SettingsModel.key == "language")
            )
            lang_setting = lang_result.scalar_one_or_none()
            set_language(lang_setting.value if lang_setting else "de")

            logger.info(f"Fuehre Task '{task.name}' aus...")
            task.last_run = datetime.utcnow()

            try:
                result = await asyncio.wait_for(
                    self._run_prompt(task, db),
                    timeout=TASK_TIMEOUT_SECONDS
                )
                task.last_result = result[:MAX_RESULT_LENGTH] if result else t("scheduler.no_result")
                logger.info(f"Task '{task.name}' erfolgreich")
            except asyncio.TimeoutError:
                task.last_result = t("scheduler.timeout", seconds=TASK_TIMEOUT_SECONDS)
                logger.error(f"Task '{task.name}' Timeout")
            except Exception as e:
                task.last_result = t("scheduler.error", error=str(e)[:500])
                logger.error(f"Task '{task.name}' Fehler: {e}")

            await db.commit()

    async def _run_prompt(self, task: ScheduledTask, db) -> str:
        """Prompt an LLM senden und Antwort holen"""
        # Load settings for LLM provider
        from db.models import Settings as SettingsModel
        result = await db.execute(select(SettingsModel))
        db_settings = {s.key: s.value for s in result.scalars().all()}

        current_provider = db_settings.get("llm_provider", "ollama")
        llm_router.update_settings(db_settings)

        try:
            provider = llm_router.get_provider(LLMProvider(current_provider))
        except ValueError:
            return t("scheduler.invalid_provider", provider=current_provider)

        messages = [
            ChatMessage(
                role="assistant",
                content=t("scheduler.intro", name=task.name)
            ),
            ChatMessage(role="user", content=task.prompt)
        ]

        response = await provider.chat(messages)
        return response.content or t("scheduler.no_response")

    async def run_task_now(self, task_id: str) -> str:
        """Task sofort manuell ausfuehren"""
        await self._execute_task(task_id)

        from db.database import async_session
        async with async_session() as db:
            task = await db.get(ScheduledTask, task_id)
            return task.last_result if task else t("scheduler.not_found")


# Global instance
task_scheduler = TaskScheduler()
