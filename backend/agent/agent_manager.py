"""
Axon by NeuroVexon - Agent Manager

Verwaltet Multi-Agent Profile mit unterschiedlichen Rollen, Modellen und Berechtigungen.
"""

from typing import Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import Agent

logger = logging.getLogger(__name__)

# Default Agents — werden beim ersten Start erstellt
DEFAULT_AGENTS = [
    {
        "name": "Assistent",
        "description": "Allgemeiner KI-Assistent mit Zugriff auf alle Tools. Jede Aktion erfordert Genehmigung.",
        "system_prompt": None,
        "model": None,  # Nutzt globale Einstellung
        "allowed_tools": None,  # Alle Tools
        "allowed_skills": None,  # Alle Skills
        "risk_level_max": "high",
        "auto_approve_tools": None,  # Nichts auto-approved
        "is_default": True,
    },
    {
        "name": "Recherche",
        "description": "Spezialisiert auf Web-Recherche und Informationssuche. Web-Suche ohne Approval.",
        "system_prompt": "Du bist ein Recherche-Assistent. Nutze web_search und web_fetch um Informationen zu finden. Fasse Ergebnisse klar und strukturiert zusammen.",
        "model": None,
        "allowed_tools": [
            "web_search",
            "web_fetch",
            "file_read",
            "memory_save",
            "memory_search",
        ],
        "allowed_skills": None,
        "risk_level_max": "medium",
        "auto_approve_tools": ["web_search", "memory_search"],
        "is_default": False,
    },
    {
        "name": "System",
        "description": "System-Agent mit Shell-Zugriff. Alle Aktionen erfordern Genehmigung.",
        "system_prompt": "Du bist ein System-Administrator-Assistent. Du kannst Shell-Befehle ausfuehren und Dateien verwalten. Erklaere immer was du vorhast bevor du etwas ausfuehrst.",
        "model": None,
        "allowed_tools": None,  # Alle Tools inkl. shell_execute
        "allowed_skills": None,
        "risk_level_max": "high",
        "auto_approve_tools": None,  # Alles braucht Approval
        "is_default": False,
    },
]


class AgentManager:
    """Verwaltet Agent-Profile"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_defaults(self) -> None:
        """Erstelle Default-Agents falls noch keine existieren"""
        result = await self.db.execute(select(Agent).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # Agents existieren bereits

        logger.info("Erstelle Default-Agents...")
        for agent_data in DEFAULT_AGENTS:
            agent = Agent(**agent_data)
            self.db.add(agent)

        await self.db.commit()
        logger.info(f"{len(DEFAULT_AGENTS)} Default-Agents erstellt")

    async def list_agents(self, enabled_only: bool = False) -> list[Agent]:
        """Alle Agents auflisten"""
        query = select(Agent).order_by(Agent.is_default.desc(), Agent.name.asc())
        if enabled_only:
            query = query.where(Agent.enabled.is_(True))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Agent nach ID holen"""
        return await self.db.get(Agent, agent_id)

    async def get_default_agent(self) -> Optional[Agent]:
        """Default-Agent holen"""
        result = await self.db.execute(
            select(Agent).where(Agent.is_default.is_(True)).limit(1)
        )
        return result.scalar_one_or_none()

    async def create_agent(
        self,
        name: str,
        description: str = "",
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        allowed_tools: Optional[list[str]] = None,
        allowed_skills: Optional[list[str]] = None,
        risk_level_max: str = "high",
        auto_approve_tools: Optional[list[str]] = None,
    ) -> Agent:
        """Neuen Agent erstellen"""
        agent = Agent(
            name=name,
            description=description,
            system_prompt=system_prompt,
            model=model,
            allowed_tools=allowed_tools,
            allowed_skills=allowed_skills,
            risk_level_max=risk_level_max,
            auto_approve_tools=auto_approve_tools,
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def update_agent(self, agent_id: str, **kwargs) -> Optional[Agent]:
        """Agent aktualisieren"""
        agent = await self.db.get(Agent, agent_id)
        if not agent:
            return None

        for key, value in kwargs.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        """Agent loeschen (Default-Agent kann nicht geloescht werden)"""
        agent = await self.db.get(Agent, agent_id)
        if not agent:
            return False
        if agent.is_default:
            return False

        await self.db.delete(agent)
        await self.db.commit()
        return True

    @staticmethod
    def is_tool_allowed(agent: Agent, tool_name: str) -> bool:
        """Prueft ob ein Tool fuer diesen Agent erlaubt ist"""
        if agent.allowed_tools is None:
            return True  # None = alle erlaubt
        return tool_name in agent.allowed_tools

    @staticmethod
    def is_auto_approved(agent: Agent, tool_name: str) -> bool:
        """Prueft ob ein Tool fuer diesen Agent auto-approved ist"""
        if agent.auto_approve_tools is None:
            return False  # None = nichts auto-approved
        return tool_name in agent.auto_approve_tools

    @staticmethod
    def check_risk_level(agent: Agent, tool_risk: str) -> bool:
        """Prueft ob das Risiko-Level innerhalb des Agent-Limits liegt"""
        levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        agent_max = levels.get(agent.risk_level_max, 2)
        tool_level = levels.get(tool_risk, 1)
        return tool_level <= agent_max
