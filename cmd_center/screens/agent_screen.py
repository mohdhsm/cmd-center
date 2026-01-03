"""Agent chat screen for Omnious."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, Input, Footer
from textual import log

from ..agent import get_agent


class MessageWidget(Static):
    """Widget for displaying a chat message."""

    DEFAULT_CSS = """
    MessageWidget {
        padding: 1;
        margin: 0 1;
    }

    MessageWidget.user {
        background: $primary-darken-2;
        border: solid $primary;
    }

    MessageWidget.assistant {
        background: $surface;
        border: solid $secondary;
    }
    """

    def __init__(self, role: str, content: str = ""):
        super().__init__(content)
        self.role = role
        self._content = content
        self.add_class(role)

    def append_content(self, text: str) -> None:
        """Append text to the message content."""
        self._content += text
        self.update(self._content)

    def set_content(self, text: str) -> None:
        """Set the message content."""
        self._content = text
        self.update(self._content)


class AgentScreen(Screen):
    """Chat screen for Omnious agent."""

    CSS = """
    AgentScreen {
        layout: vertical;
    }

    #header {
        height: 3;
        background: $primary;
        color: $text;
        text-align: center;
        padding: 1;
    }

    #metrics {
        dock: right;
        width: auto;
        padding: 0 2;
    }

    #chat-container {
        height: 1fr;
        border: solid $primary;
    }

    #status-bar {
        height: 1;
        background: $surface-darken-1;
        color: $text-muted;
        padding: 0 1;
    }

    #input-container {
        height: 3;
        padding: 0 1;
    }

    #chat-input {
        width: 100%;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("ctrl+l", "clear_chat", "Clear"),
    ]

    def __init__(self):
        super().__init__()
        self.agent = get_agent()
        self._current_message: MessageWidget | None = None

    def compose(self) -> ComposeResult:
        yield Static("Omnious - The All-Knowing AI", id="header")
        yield Static(self.agent.metrics.format_display(), id="metrics")

        with VerticalScroll(id="chat-container"):
            yield MessageWidget(
                "assistant",
                "Greetings! The all-knowing Omnious is at your service. "
                "What would you like to know about today?"
            )

        yield Static("Ready", id="status-bar")

        with Vertical(id="input-container"):
            yield Input(placeholder="Ask Omnious anything...", id="chat-input")

        yield Footer()

    def on_mount(self) -> None:
        """Focus input on mount."""
        self.query_one("#chat-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value.strip()
        if not user_input:
            return

        # Clear input
        event.input.value = ""

        # Add user message
        chat = self.query_one("#chat-container", VerticalScroll)
        chat.mount(MessageWidget("user", user_input))

        # Create assistant message placeholder
        self._current_message = MessageWidget("assistant", "")
        chat.mount(self._current_message)

        # Update status
        self._set_status("Thinking...")

        # Stream response
        try:
            async for chunk in self.agent.chat_stream(user_input):
                if chunk.type == "text" and chunk.content:
                    self._append_to_current(chunk.content)
                elif chunk.type == "tool_call":
                    self._set_status(f"Using {chunk.tool_name}...")
                elif chunk.type == "error":
                    self._append_to_current(f"\n\nWarning: Error: {chunk.error}")
                    self._set_status("Error")
                elif chunk.type == "done":
                    self._set_status("Ready")
                    self._update_metrics()
        except Exception as e:
            log(f"Error in chat: {e}")
            error_message = (
                "Warning: **Something went wrong**\n\n"
                f"Error: {str(e)[:200]}\n\n"
                "I'll try my best to help - could you rephrase your question?"
            )
            if self._current_message:
                self._current_message.set_content(error_message)
            self._set_status("Error - Ready")

        # Scroll to bottom
        chat.scroll_end()

    def _append_to_current(self, text: str) -> None:
        """Append text to current message."""
        if self._current_message:
            self._current_message.append_content(text)

    def _set_status(self, status: str) -> None:
        """Update status bar."""
        self.query_one("#status-bar", Static).update(status)

    def _update_metrics(self) -> None:
        """Update metrics display."""
        self.query_one("#metrics", Static).update(
            self.agent.metrics.format_display()
        )

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_clear_chat(self) -> None:
        """Clear chat history."""
        self.agent.clear_conversation()
        chat = self.query_one("#chat-container", VerticalScroll)

        # Remove all messages except welcome
        for widget in list(chat.query(MessageWidget)):
            widget.remove()

        # Add fresh welcome
        chat.mount(MessageWidget(
            "assistant",
            "Chat cleared! The all-knowing Omnious awaits your questions."
        ))

        self.agent.metrics.reset()
        self._update_metrics()
