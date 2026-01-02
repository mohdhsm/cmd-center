"""Modal screen for editing and sending follow-up emails."""

import asyncio

import httpx
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input, TextArea
from textual import log


class FollowupEmailModal(ModalScreen):
    """Modal for editing and sending a follow-up email."""

    CSS = """
    FollowupEmailModal {
        align: center middle;
    }

    #email-modal {
        width: 90;
        height: 35;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #status-line {
        height: 1;
        margin-bottom: 1;
        text-align: center;
        color: $warning;
    }

    .field-label {
        margin-top: 1;
        margin-bottom: 0;
    }

    #subject-input {
        height: 3;
        margin-bottom: 1;
    }

    #body-input {
        height: 15;
        margin-bottom: 1;
    }

    #button-row {
        height: 3;
        align: center middle;
    }

    #send-button {
        margin-right: 2;
    }

    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        api_url: str,
        deal_id: int,
        subject: str,
        body: str,
        recipient_email: str,
    ):
        super().__init__()
        self.api_url = api_url
        self.deal_id = deal_id
        self.initial_subject = subject
        self.initial_body = body
        self.recipient_email = recipient_email

    def compose(self) -> ComposeResult:
        """Create the modal layout."""
        with Vertical(id="email-modal"):
            yield Static(f"Follow-up Email for Deal #{self.deal_id}", id="modal-title")
            yield Static("", id="status-line")

            yield Static(f"To: {self.recipient_email}", classes="field-label")

            yield Static("Subject:", classes="field-label")
            yield Input(value=self.initial_subject, id="subject-input")

            yield Static("Message:", classes="field-label")
            yield TextArea(self.initial_body, id="body-input")

            with Horizontal(id="button-row"):
                yield Button("Send", id="send-button", variant="primary")
                yield Button("Cancel", id="cancel-button", variant="default")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-button":
            self.dismiss(False)
        elif event.button.id == "send-button":
            await self._send_email()

    async def _send_email(self) -> None:
        """Send the email via API."""
        status_line = self.query_one("#status-line", Static)
        subject_input = self.query_one("#subject-input", Input)
        body_input = self.query_one("#body-input", TextArea)

        subject = subject_input.value
        body = body_input.text

        if not subject.strip():
            status_line.update("Error: Subject cannot be empty")
            return

        if not body.strip():
            status_line.update("Error: Message cannot be empty")
            return

        status_line.update("Sending...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/emails/followup/send",
                    json={
                        "deal_id": self.deal_id,
                        "recipient_email": self.recipient_email,
                        "subject": subject,
                        "body": body,
                    }
                )

                if response.status_code == 200:
                    status_line.update("Email sent successfully!")
                    # Wait briefly so user sees success message
                    await asyncio.sleep(1)
                    self.dismiss(True)
                else:
                    try:
                        error_detail = response.json().get("detail", "Unknown error")
                    except Exception:
                        error_detail = f"HTTP {response.status_code}"
                    status_line.update(f"Error: {error_detail}")

        except httpx.TimeoutException:
            status_line.update("Error: Request timed out")
        except Exception as e:
            log(f"Error sending email: {e}")
            status_line.update(f"Error: {str(e)[:50]}")

    def action_cancel(self) -> None:
        """Cancel and close modal."""
        self.dismiss(False)
