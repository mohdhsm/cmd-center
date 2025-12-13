"""Modal screen to display notes for a selected deal."""

import httpx
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Label


class NotesModalScreen(ModalScreen):
    """Modal screen showing the latest notes for a deal."""

    CSS = """
    NotesModalScreen {
        align: center middle;
    }

    #notes-modal {
        width: 80;
        height: 30;
        border: thick $primary;
        background: $surface;
    }

    #notes-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #status-line {
        height: 3;
        margin-bottom: 1;
        text-align: center;
    }

    #notes-scroll {
        height: 1fr;
        border: solid $secondary;
        margin-bottom: 1;
    }

    #footer {
        height: 3;
        align: center middle;
    }

    .note-item {
        margin: 1;
        padding: 1;
        border: solid $secondary;
        background: $panel;
    }

    .note-header {
        text-style: bold;
        margin-bottom: 1;
    }

    .note-content {
        margin-left: 1;
        max-height: 10;
        overflow: auto;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close modal"),
    ]

    def __init__(self, api_url: str, deal_id: int | None = None):
        super().__init__()
        self.api_url = api_url
        self.deal_id = deal_id
        self.limit = 5

    def compose(self) -> ComposeResult:
        """Create the modal layout."""
        with Vertical(id="notes-modal"):
            yield Static(f"Notes for Deal {self.deal_id or 'N/A'}", id="notes-title")
            yield Static("Loading...", id="status-line")

            with ScrollableContainer(id="notes-scroll"):
                # Notes will be added here dynamically
                pass

            with Horizontal(id="footer"):
                yield Button("Close", id="close-button")

    async def on_mount(self) -> None:
        """Load notes when modal mounts."""
        await self.load_notes()

    async def load_notes(self) -> None:
        """Load and display notes for the deal."""
        status_line = self.query_one("#status-line", Static)
        scroll_view = self.query_one("#notes-scroll", ScrollableContainer)

        # Clear previous content safely
        for child in list(scroll_view.children):
            await child.remove()

        if not self.deal_id:
            status_line.update("No deal selected")
            return

        status_line.update("Loading...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/deals/{self.deal_id}/notes",
                    params={"limit": self.limit}
                )

                if response.status_code == 404:
                    status_line.update("No notes found")
                    return

                response.raise_for_status()
                notes = response.json()

                if not notes:
                    status_line.update("No notes found")
                    return

                status_line.update(f"Showing {len(notes)} notes")

                # Add notes to scroll view using correct runtime API
                for note in notes:
                    note_date = note.get("date", "Unknown date")
                    author = note.get("author", "Unknown author")
                    content = note.get("content", "")

                    # Create note item
                    note_item = Vertical(classes="note-item")
                    note_item.border_title = f"Note #{note['id']}"

                    header = Static(f"{note_date} by {author}", classes="note-header")
                    content_widget = Static(content, classes="note-content")

                    # Mount children using correct runtime API
                    await note_item.mount(header, content_widget)
                    await scroll_view.mount(note_item)

        except httpx.HTTPStatusError as e:
            status_line.update(f"Error: HTTP {e.response.status_code}")
        except Exception as e:
            status_line.update(f"Error: {str(e)}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-button":
            self.dismiss()

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()