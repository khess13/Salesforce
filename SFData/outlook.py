"""
Outlook email helper via win32com.
Reference: https://stackoverflow.com/questions/6332577/send-outlook-email-via-python
"""
from __future__ import annotations

from typing import Optional

import win32com.client as win32


class EmailMessage:
    """Compose and send an Outlook email."""

    def __init__(
        self,
        subject: str,
        to_address: str,
        email_body: Optional[str] = None,
        html_body: Optional[str] = None,
        attachment_path: Optional[str] = None,
    ) -> None:
        self.subject = subject
        self.to_address = to_address
        self.email_body = email_body
        self.html_body = html_body
        self.attachment_path = attachment_path
        self.outlook = win32.Dispatch('outlook.application')

    def send(self) -> None:
        """Send the email via Outlook."""
        mail = self.outlook.CreateItem(0)
        mail.To = self.to_address
        mail.Subject = self.subject

        if self.email_body is not None:
            mail.Body = self.email_body
        if self.html_body is not None:
            mail.HTMLBody = self.html_body
        if self.attachment_path is not None:
            mail.Attachments.Add(self.attachment_path)

        mail.Send()
