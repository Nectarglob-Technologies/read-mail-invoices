import base64
import os
import requests
from typing import List

from app.core.config import ATTACHMENTS_DIR, settings
from app.core.security import EmailAuth


class EmailReader:
    def __init__(self):
        self.auth = EmailAuth()
        self.graph_base = "https://graph.microsoft.com/v1.0"
        self.mailbox = settings.OUTLOOK_USER  # invoices@company.com

    # -----------------------------
    # Headers
    # -----------------------------
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.auth.get_token()}",
            "Accept": "application/json",
        }

    # -----------------------------
    # STEP 1: Fetch Inbox messages
    # -----------------------------
    def fetch_messages(self, max_messages: int = 5):
        """
        Fetch latest Inbox messages (newest first)
        """
        url = (
            f"{self.graph_base}/users/"
            f"{self.mailbox}/mailFolders/inbox/messages"
        )

        params = {
            "$top": max_messages,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,receivedDateTime,hasAttachments",
        }

        response = requests.get(
            url,
            headers=self._headers(),
            params=params,
        )
        response.raise_for_status()

        messages = response.json().get("value", [])
        print(f"📩 Messages fetched: {len(messages)}")
        return messages

    # -----------------------------
    # STEP 2: Fetch attachments
    # -----------------------------
    def fetch_attachments_for_message(self, message_id: str):
        """
        Fetch attachments for a single message
        """
        url = (
            f"{self.graph_base}/users/"
            f"{self.mailbox}/messages/"
            f"{message_id}/attachments"
        )

        response = requests.get(url, headers=self._headers())
        response.raise_for_status()

        return response.json().get("value", [])

    # -----------------------------
    # STEP 3: Save attachments
    # -----------------------------
    def save_attachments(self, attachments) -> List[str]:
        """
        Save PDF / image attachments to disk
        """
        saved_files = []
        os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

        for att in attachments:
            content_type = att.get("@odata.mediaContentType")
            content_bytes = att.get("contentBytes")

            if not content_bytes:
                continue

            if content_type not in (
                "application/pdf",
                "image/png",
                "image/jpeg",
            ):
                continue

            file_path = os.path.join(ATTACHMENTS_DIR, att["name"])

            with open(file_path, "wb") as f:
                f.write(base64.b64decode(content_bytes))

            print(f"✅ Saved attachment: {file_path}")
            saved_files.append(file_path)

        return saved_files

    # -----------------------------
    # STEP 4: Full pipeline
    # -----------------------------
    def fetch_latest_invoice_attachments(self, max_messages: int = 5):
        """
        Fetch latest emails → extract attachments
        """
        messages = self.fetch_messages(max_messages)
        all_files = []

        for msg in messages:
            if not msg.get("hasAttachments"):
                continue

            print(
                f"📧 Processing: {msg['subject']} "
                f"({msg['receivedDateTime']})"
            )

            attachments = self.fetch_attachments_for_message(msg["id"])
            files = self.save_attachments(attachments)
            all_files.extend(files)

        return all_files
