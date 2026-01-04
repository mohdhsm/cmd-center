"""Modal screen for adding notes to deals."""

import asyncio

import httpx
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, Button, TextArea, Checkbox, Input
from textual import log


class AddNoteModal(ModalScreen):
    """Modal for adding a note to a deal."""

    CSS = """
    AddNoteModal {
        align: center middle;
    }

    #note-modal {
        width: 80;
        height: 36;
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

    #content-input {
        height: 12;
        margin-bottom: 1;
    }

    #tags-input {
        height: 3;
        margin-bottom: 1;
    }

    #options-row {
        height: 3;
        margin-bottom: 1;
    }

    #button-row {
        height: 3;
        align: center middle;
    }

    #save-button {
        margin-right: 2;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, api_url: str, deal_id: int):
        super().__init__()
        self.api_url = api_url
        self.deal_id = deal_id

    def compose(self) -> ComposeResult:
        """Create the modal layout."""
        with Vertical(id="note-modal"):
            yield Static(f"Add Note for Deal #{self.deal_id}", id="modal-title")
            yield Static("", id="status-line")

            yield Static("Note Content:", classes="field-label")
            yield TextArea(id="content-input")

            yield Static("Tags (comma-separated, optional):", classes="field-label")
            yield Input(placeholder="e.g. followup, important", id="tags-input")

            with Horizontal(id="options-row"):
                yield Checkbox("Pin this note", id="pinned-checkbox")

            with Horizontal(id="button-row"):
                yield Button("Save", id="save-button", variant="primary")
                yield Button("Cancel", id="cancel-button", variant="default")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-button":
            self.dismiss(False)
        elif event.button.id == "save-button":
            await self._save_note()

    async def _save_note(self) -> None:
        """Save the note via API."""
        status_line = self.query_one("#status-line", Static)
        content_input = self.query_one("#content-input", TextArea)
        tags_input = self.query_one("#tags-input", Input)
        pinned_checkbox = self.query_one("#pinned-checkbox", Checkbox)

        content = content_input.text.strip()
        tags = tags_input.value.strip() or None
        pinned = pinned_checkbox.value

        if not content:
            status_line.update("Error: Note content cannot be empty")
            return

        status_line.update("Saving...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/notes",
                    params={"actor": "user"},
                    json={
                        "content": content,
                        "target_type": "deal",
                        "target_id": self.deal_id,
                        "pinned": pinned,
                        "tags": tags,
                    }
                )

                if response.status_code == 201:
                    status_line.update("Note saved successfully!")
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
            log(f"Error saving note: {e}")
            status_line.update(f"Error: {str(e)[:50]}")

    def action_cancel(self) -> None:
        """Cancel and close modal."""
        self.dismiss(False)
