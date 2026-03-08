"""
Email inbox processor — Extract PDF attachments from IMAP inbox.

Connects to an IMAP mailbox, finds emails with PDF attachments,
downloads them, and routes them to the OCR pipeline.
"""
import email
import imaplib
import logging
import tempfile
from datetime import datetime, timezone
from email.header import decode_header
from typing import Dict, List, Optional

from app.storage import get_storage

logger = logging.getLogger(__name__)


class InboxProcessor:
    """Process invoice PDFs from email inbox via IMAP."""

    def __init__(
        self,
        imap_host: str,
        imap_port: int = 993,
        username: str = "",
        password: str = "",
        folder: str = "INBOX",
        use_ssl: bool = True,
    ):
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.username = username
        self.password = password
        self.folder = folder
        self.use_ssl = use_ssl

    def fetch_pdf_attachments(
        self,
        since_date: Optional[str] = None,
        max_emails: int = 50,
        org_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Fetch PDF attachments from inbox.

        Args:
            since_date: Only fetch emails since this date (YYYY-MM-DD)
            max_emails: Maximum number of emails to process
            org_id: Organization ID for tenant-isolated storage paths

        Returns:
            List of dicts with: filename, storage_path, sender, subject, date, file_size
        """
        results: List[Dict] = []

        try:
            # Connect to IMAP
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            else:
                mail = imaplib.IMAP4(self.imap_host, self.imap_port)

            mail.login(self.username, self.password)
            mail.select(self.folder, readonly=True)

            # Build search criteria
            criteria = '(UNSEEN)'
            if since_date:
                # IMAP date format: DD-Mon-YYYY
                try:
                    dt = datetime.strptime(since_date, "%Y-%m-%d")
                    imap_date = dt.strftime("%d-%b-%Y")
                    criteria = f'(SINCE {imap_date} UNSEEN)'
                except ValueError:
                    pass

            # Search for emails
            status, message_ids = mail.search(None, criteria)
            if status != "OK":
                logger.warning("IMAP search failed: %s", status)
                return results

            ids = message_ids[0].split()
            if not ids:
                logger.info("No new emails found")
                return results

            # Process limited number of emails
            for msg_id in ids[:max_emails]:
                try:
                    email_result = self._process_email(mail, msg_id, org_id)
                    results.extend(email_result)
                except Exception as e:
                    logger.warning("Failed to process email %s: %s", msg_id, e)

            mail.logout()

        except imaplib.IMAP4.error as e:
            logger.error("IMAP connection failed: %s", e)
            raise ConnectionError(f"IMAP-Verbindung fehlgeschlagen: {e}")
        except Exception as e:
            logger.error("Email processing error: %s", e)
            raise

        logger.info("Fetched %d PDF attachments from inbox", len(results))
        return results

    def _process_email(
        self, mail: imaplib.IMAP4, msg_id: bytes, org_id: Optional[str] = None
    ) -> List[Dict]:
        """Process a single email and extract PDF attachments."""
        results = []

        status, data = mail.fetch(msg_id, "(RFC822)")
        if status != "OK":
            return results

        msg = email.message_from_bytes(data[0][1])

        # Decode headers
        subject = self._decode_header(msg.get("Subject", ""))
        sender = self._decode_header(msg.get("From", ""))
        date_str = msg.get("Date", "")

        storage = get_storage()

        # Walk through MIME parts
        for part in msg.walk():
            content_type = part.get_content_type()
            filename = part.get_filename()

            if filename and content_type == "application/pdf":
                # Decode filename
                filename = self._decode_header(filename)

                # Sanitize filename
                import re
                safe_name = re.sub(r"[^\w.\-]", "_", filename)
                if not safe_name.lower().endswith(".pdf"):
                    safe_name += ".pdf"

                # Save PDF
                pdf_content = part.get_payload(decode=True)
                if not pdf_content:
                    continue

                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                storage_filename = f"email_{timestamp}_{safe_name}"
                prefix = f"{org_id}" if org_id else "shared"
                storage_path = f"{prefix}/uploads/{storage_filename}"
                storage.save(storage_path, pdf_content)

                results.append({
                    "filename": safe_name,
                    "storage_path": storage_path,
                    "sender": sender,
                    "subject": subject,
                    "date": date_str,
                    "file_size": len(pdf_content),
                })

                logger.info(
                    "Extracted PDF: %s from %s (%d bytes)",
                    safe_name, sender, len(pdf_content),
                )

        return results

    @staticmethod
    def _decode_header(header_value: str) -> str:
        """Decode MIME encoded header value."""
        if not header_value:
            return ""
        decoded_parts = decode_header(header_value)
        parts = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                parts.append(part.decode(encoding or "utf-8", errors="replace"))
            else:
                parts.append(part)
        return " ".join(parts)
