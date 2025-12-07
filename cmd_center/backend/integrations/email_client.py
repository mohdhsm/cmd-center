"""Email client for sending follow-up emails."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from .config import get_config


class EmailClient:
    """Client for sending emails via SMTP."""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email: str,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        body_html: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # Attach plain text version
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)
            
            # Attach HTML version if provided
            if body_html:
                html_part = MIMEText(body_html, "html")
                msg.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            return False
    
    async def send_bulk_emails(
        self,
        emails: list[tuple[str, str, str]],  # [(to_email, subject, body), ...]
    ) -> dict[str, bool]:
        """Send multiple emails and return status for each."""
        results = {}
        
        for to_email, subject, body in emails:
            success = await self.send_email(to_email, subject, body)
            results[to_email] = success
        
        return results


# Global client instance
_email_client: Optional[EmailClient] = None


def get_email_client() -> EmailClient:
    """Get or create email client singleton."""
    global _email_client
    if _email_client is None:
        config = get_config()
        _email_client = EmailClient(
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            smtp_username=config.smtp_username,
            smtp_password=config.smtp_password,
            from_email=config.smtp_from_email,
        )
    return _email_client