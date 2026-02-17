"""
Axon Skill: E-Mail Posteingang

Liest ungelesene E-Mails und durchsucht den Posteingang.
Veraendert NICHTS am Posteingang (readonly).
"""

SKILL_NAME = "email_inbox"
SKILL_DISPLAY_NAME = "E-Mail Posteingang"
SKILL_DESCRIPTION = "Liest ungelesene E-Mails und durchsucht den Posteingang (readonly)"
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "NeuroVexon"
SKILL_RISK_LEVEL = "medium"

SKILL_PARAMETERS = {
    "action": {
        "type": "string",
        "description": "Aktion: 'unread' (ungelesene), 'search' (suchen), 'read' (eine lesen)",
        "required": True,
    },
    "query": {"type": "string", "description": "Suchbegriff (fuer action=search)"},
    "uid": {"type": "string", "description": "E-Mail UID (fuer action=read)"},
    "limit": {
        "type": "integer",
        "description": "Maximale Anzahl Ergebnisse",
        "default": 10,
    },
}


async def execute(params: dict) -> str:
    """E-Mail Posteingang abfragen"""
    from sqlalchemy import select
    from db.database import async_session
    from db.models import Settings
    from integrations.email import get_email_client_from_settings

    action = params.get("action", "unread")
    query = params.get("query", "")
    uid = params.get("uid", "")
    limit = params.get("limit", 10)

    # Settings aus DB laden
    async with async_session() as db:
        result = await db.execute(select(Settings))
        db_settings = {s.key: s.value for s in result.scalars().all()}

    client = get_email_client_from_settings(db_settings)
    if not client:
        return "E-Mail ist nicht konfiguriert. Bitte IMAP-Einstellungen in den Einstellungen hinterlegen."

    try:
        if action == "unread":
            emails = await client.list_unread(limit=limit)
            if not emails:
                return "Keine ungelesenen E-Mails."
            lines = [f"📬 {len(emails)} ungelesene E-Mail(s):\n"]
            for e in emails:
                date = e.get("date", "")
                if date:
                    date = date[:16].replace("T", " ")
                lines.append(
                    f"- **{e['subject']}** von {e['sender']} ({date}) [UID: {e['uid']}]"
                )
            return "\n".join(lines)

        elif action == "search":
            if not query:
                return "Bitte einen Suchbegriff angeben (query)."
            emails = await client.search_emails(query, limit=limit)
            if not emails:
                return f"Keine E-Mails gefunden fuer '{query}'."
            lines = [f"🔍 {len(emails)} Treffer fuer '{query}':\n"]
            for e in emails:
                date = e.get("date", "")
                if date:
                    date = date[:16].replace("T", " ")
                lines.append(
                    f"- **{e['subject']}** von {e['sender']} ({date}) [UID: {e['uid']}]"
                )
            return "\n".join(lines)

        elif action == "read":
            if not uid:
                return "Bitte eine E-Mail UID angeben."
            email_data = await client.read_email(uid)
            if not email_data:
                return f"E-Mail mit UID {uid} nicht gefunden."
            date = email_data.get("date", "")
            if date:
                date = date[:16].replace("T", " ")
            return (
                f"📧 **{email_data['subject']}**\n"
                f"Von: {email_data['sender']}\n"
                f"Datum: {date}\n\n"
                f"{email_data['body_text']}"
            )

        else:
            return (
                f"Unbekannte Aktion: {action}. Verwende 'unread', 'search' oder 'read'."
            )

    except Exception as e:
        return f"Fehler beim E-Mail-Zugriff: {str(e)}"
