"""
Axon by NeuroVexon - E-Mail Integration (IMAP/SMTP)

Kontrollierte E-Mail-Anbindung:
- IMAP: Ungelesene lesen, durchsuchen
- SMTP: E-Mails senden (nur mit Approval)
- BEWUSST NICHT: delete, move, mark_as_read — AXON veraendert den Posteingang nicht.
"""

import asyncio
import email
import imaplib
import logging
import smtplib
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, parsedate_to_datetime
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class EmailMessage:
    """Parsed E-Mail"""

    def __init__(
        self,
        uid: str,
        subject: str,
        sender: str,
        date: Optional[datetime],
        body_text: str,
        body_html: Optional[str] = None,
    ):
        self.uid = uid
        self.subject = subject
        self.sender = sender
        self.date = date
        self.body_text = body_text
        self.body_html = body_html

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "subject": self.subject,
            "sender": self.sender,
            "date": self.date.isoformat() if self.date else None,
            "body_text": self.body_text[:2000],  # Truncate
        }


def _decode_header_value(raw: str) -> str:
    """Decode MIME-encoded header value"""
    parts = decode_header(raw)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _extract_body(msg: email.message.Message) -> tuple[str, Optional[str]]:
    """Extract plain text and HTML body from email"""
    text_body = ""
    html_body = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    text_body = payload.decode(charset, errors="replace")
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html_body = payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text_body = payload.decode(charset, errors="replace")

    return text_body, html_body


class EmailClient:
    """IMAP/SMTP Client fuer Axon"""

    def __init__(
        self,
        imap_host: str,
        imap_port: int,
        imap_user: str,
        imap_password: str,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        smtp_from: str = "",
    ):
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_user = imap_user
        self.imap_password = imap_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from or smtp_user

    # ------------------------------------------------------------------
    # IMAP — read-only operations
    # ------------------------------------------------------------------

    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server"""
        conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        conn.login(self.imap_user, self.imap_password)
        return conn

    async def list_unread(self, limit: int = 20) -> list[dict]:
        """Liste ungelesene E-Mails (readonly — markiert NICHTS als gelesen)"""

        def _fetch():
            conn = self._connect_imap()
            try:
                conn.select("INBOX", readonly=True)
                _, data = conn.search(None, "UNSEEN")
                uids = data[0].split()
                if not uids:
                    return []

                # Neueste zuerst, limitieren
                uids = uids[-limit:][::-1]
                results = []
                for uid in uids:
                    _, msg_data = conn.fetch(
                        uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
                    )
                    if msg_data and msg_data[0]:
                        raw = msg_data[0][1]
                        msg = email.message_from_bytes(raw)
                        subject = _decode_header_value(
                            msg.get("Subject", "(kein Betreff)")
                        )
                        sender = _decode_header_value(msg.get("From", "unbekannt"))
                        date_str = msg.get("Date")
                        date = None
                        if date_str:
                            try:
                                date = parsedate_to_datetime(date_str)
                            except Exception:
                                pass
                        results.append(
                            {
                                "uid": uid.decode(),
                                "subject": subject,
                                "sender": sender,
                                "date": date.isoformat() if date else None,
                            }
                        )
                return results
            finally:
                conn.logout()

        return await asyncio.to_thread(_fetch)

    async def read_email(self, uid: str) -> Optional[dict]:
        """Liest eine E-Mail vollstaendig (readonly — PEEK)"""

        def _fetch():
            conn = self._connect_imap()
            try:
                conn.select("INBOX", readonly=True)
                _, msg_data = conn.fetch(uid.encode(), "(BODY.PEEK[])")
                if not msg_data or not msg_data[0]:
                    return None

                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subject = _decode_header_value(msg.get("Subject", "(kein Betreff)"))
                sender = _decode_header_value(msg.get("From", "unbekannt"))
                date_str = msg.get("Date")
                date = None
                if date_str:
                    try:
                        date = parsedate_to_datetime(date_str)
                    except Exception:
                        pass

                text_body, html_body = _extract_body(msg)
                return EmailMessage(
                    uid=uid,
                    subject=subject,
                    sender=sender,
                    date=date,
                    body_text=text_body,
                    body_html=html_body,
                ).to_dict()
            finally:
                conn.logout()

        return await asyncio.to_thread(_fetch)

    async def search_emails(self, query: str, limit: int = 10) -> list[dict]:
        """Durchsucht E-Mails nach Betreff (readonly)"""

        def _fetch():
            conn = self._connect_imap()
            try:
                conn.select("INBOX", readonly=True)
                # IMAP SUBJECT search
                _, data = conn.search(None, f'(SUBJECT "{query}")')
                uids = data[0].split()
                if not uids:
                    return []

                uids = uids[-limit:][::-1]
                results = []
                for uid in uids:
                    _, msg_data = conn.fetch(
                        uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
                    )
                    if msg_data and msg_data[0]:
                        raw = msg_data[0][1]
                        msg = email.message_from_bytes(raw)
                        subject = _decode_header_value(
                            msg.get("Subject", "(kein Betreff)")
                        )
                        sender = _decode_header_value(msg.get("From", "unbekannt"))
                        date_str = msg.get("Date")
                        date = None
                        if date_str:
                            try:
                                date = parsedate_to_datetime(date_str)
                            except Exception:
                                pass
                        results.append(
                            {
                                "uid": uid.decode(),
                                "subject": subject,
                                "sender": sender,
                                "date": date.isoformat() if date else None,
                            }
                        )
                return results
            finally:
                conn.logout()

        return await asyncio.to_thread(_fetch)

    # ------------------------------------------------------------------
    # SMTP — send (requires Approval in Agent flow)
    # ------------------------------------------------------------------

    async def send_email(
        self, to: str, subject: str, body: str, html: bool = False
    ) -> str:
        """Sendet eine E-Mail via SMTP"""

        def _send():
            msg = MIMEMultipart("alternative")
            msg["From"] = self.smtp_from
            msg["To"] = to
            msg["Subject"] = subject
            msg["Date"] = formatdate(localtime=True)

            if html:
                msg.attach(MIMEText(body, "html", "utf-8"))
            else:
                msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            return f"E-Mail gesendet an {to}: {subject}"

        return await asyncio.to_thread(_send)

    # ------------------------------------------------------------------
    # Bewusst NICHT implementiert:
    # - delete_email
    # - move_email
    # - mark_as_read
    # AXON veraendert den Posteingang nicht.
    # ------------------------------------------------------------------

    async def test_connection(self) -> dict:
        """Testet IMAP und SMTP Verbindung"""
        result = {"imap": False, "smtp": False, "imap_error": None, "smtp_error": None}

        # IMAP Test
        try:

            def _test_imap():
                conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
                conn.login(self.imap_user, self.imap_password)
                conn.logout()

            await asyncio.to_thread(_test_imap)
            result["imap"] = True
        except Exception as e:
            result["imap_error"] = str(e)

        # SMTP Test
        if self.smtp_host:
            try:

                def _test_smtp():
                    with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        server.login(self.smtp_user, self.smtp_password)

                await asyncio.to_thread(_test_smtp)
                result["smtp"] = True
            except Exception as e:
                result["smtp_error"] = str(e)

        return result


def get_email_client_from_settings(db_settings: dict) -> Optional[EmailClient]:
    """Erstellt einen EmailClient aus DB-Settings (mit Entschluesselung)"""
    from core.security import decrypt_value

    imap_host = db_settings.get("imap_host", "")
    if not imap_host:
        return None

    return EmailClient(
        imap_host=imap_host,
        imap_port=int(db_settings.get("imap_port", "993")),
        imap_user=db_settings.get("imap_user", ""),
        imap_password=decrypt_value(db_settings.get("imap_password", "")),
        smtp_host=db_settings.get("smtp_host", ""),
        smtp_port=int(db_settings.get("smtp_port", "587")),
        smtp_user=db_settings.get("smtp_user", ""),
        smtp_password=decrypt_value(db_settings.get("smtp_password", "")),
        smtp_from=db_settings.get("smtp_from", ""),
    )
