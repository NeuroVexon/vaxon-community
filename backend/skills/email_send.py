"""
Axon Skill: E-Mail Senden

Sendet E-Mails ueber SMTP.
IMMER mit Approval — der User sieht Empfaenger, Betreff und Text vor dem Senden.
"""

SKILL_NAME = "email_send"
SKILL_DISPLAY_NAME = "E-Mail senden"
SKILL_DESCRIPTION = (
    "Sendet eine E-Mail (IMMER mit Genehmigung — zeigt Empfaenger, Betreff und Text)"
)
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "NeuroVexon"
SKILL_RISK_LEVEL = "high"

SKILL_PARAMETERS = {
    "to": {
        "type": "string",
        "description": "Empfaenger E-Mail-Adresse",
        "required": True,
    },
    "subject": {
        "type": "string",
        "description": "Betreff der E-Mail",
        "required": True,
    },
    "body": {
        "type": "string",
        "description": "Inhalt der E-Mail (Klartext)",
        "required": True,
    },
}


async def execute(params: dict) -> str:
    """E-Mail senden"""
    from sqlalchemy import select
    from db.database import async_session
    from db.models import Settings
    from integrations.email import get_email_client_from_settings

    to = params.get("to", "")
    subject = params.get("subject", "")
    body = params.get("body", "")

    if not to:
        return "Empfaenger-Adresse fehlt."
    if not subject:
        return "Betreff fehlt."
    if not body:
        return "E-Mail-Text fehlt."

    # Settings aus DB laden
    async with async_session() as db:
        result = await db.execute(select(Settings))
        db_settings = {s.key: s.value for s in result.scalars().all()}

    client = get_email_client_from_settings(db_settings)
    if not client:
        return "E-Mail ist nicht konfiguriert. Bitte SMTP-Einstellungen in den Einstellungen hinterlegen."

    if not client.smtp_host:
        return "SMTP ist nicht konfiguriert. Bitte SMTP-Einstellungen in den Einstellungen hinterlegen."

    try:
        result = await client.send_email(to=to, subject=subject, body=body)
        return result
    except Exception as e:
        return f"Fehler beim E-Mail-Versand: {str(e)}"
