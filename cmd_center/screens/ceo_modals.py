"""Shared modal components for CEO Dashboard screens."""

from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Dict, Any

import httpx
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, Input, Select, Checkbox, TextArea
from textual.binding import Binding


class TaskCreateModal(ModalScreen):
    """Modal for creating or editing a task."""

    CSS = """
    TaskCreateModal {
        align: center middle;
    }

    #modal-container {
        width: 70;
        height: auto;
        max-height: 35;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #modal-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }

    .form-row {
        height: auto;
        margin-bottom: 1;
    }

    .form-label {
        width: 12;
        color: $text-muted;
    }

    .form-input {
        width: 1fr;
    }

    #button-row {
        margin-top: 1;
        height: 3;
    }

    #button-row Button {
        margin: 0 1;
    }

    .error-text {
        color: $error;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+enter", "save", "Save"),
    ]

    def __init__(
        self,
        api_url: str,
        task: Optional[Dict[str, Any]] = None,
        on_save: Optional[Callable] = None,
    ):
        super().__init__()
        self.api_url = api_url
        self._task_data = task  # None for create, dict for edit
        self.on_save = on_save
        self._employees = []

    def compose(self) -> ComposeResult:
        title = "Edit Task" if self._task_data else "New Task"

        with Vertical(id="modal-container"):
            yield Static(title, id="modal-title")

            with Horizontal(classes="form-row"):
                yield Static("Title:", classes="form-label")
                yield Input(
                    value=self._task_data.get("title", "") if self._task_data else "",
                    placeholder="Task title",
                    id="input-title",
                    classes="form-input",
                )

            with Horizontal(classes="form-row"):
                yield Static("Description:", classes="form-label")
                yield Input(
                    value=self._task_data.get("description", "") if self._task_data else "",
                    placeholder="Optional description",
                    id="input-description",
                    classes="form-input",
                )

            with Horizontal(classes="form-row"):
                yield Static("Priority:", classes="form-label")
                yield Select(
                    options=[
                        ("High", "high"),
                        ("Medium", "medium"),
                        ("Low", "low"),
                    ],
                    value=self._task_data.get("priority", "medium") if self._task_data else "medium",
                    id="select-priority",
                    allow_blank=False,
                )

            with Horizontal(classes="form-row"):
                yield Static("Assignee:", classes="form-label")
                yield Select(
                    options=[("Unassigned", "")],
                    value="",
                    id="select-assignee",
                    allow_blank=False,
                )

            with Horizontal(classes="form-row"):
                yield Static("Due:", classes="form-label")
                yield Input(
                    value=self._format_date(self._task_data.get("due_at")) if self._task_data else "",
                    placeholder="YYYY-MM-DD or +7d",
                    id="input-due",
                    classes="form-input",
                )

            with Horizontal(classes="form-row"):
                yield Static("Critical:", classes="form-label")
                yield Checkbox(
                    "Mark as critical",
                    value=self._task_data.get("is_critical", False) if self._task_data else False,
                    id="check-critical",
                )

            yield Static("", id="error-message", classes="error-text")

            with Horizontal(id="button-row"):
                yield Button("Save [Ctrl+Enter]", id="btn-save", variant="primary")
                yield Button("Cancel [Esc]", id="btn-cancel")

    def _format_date(self, date_str: Optional[str]) -> str:
        """Format date string for display."""
        if not date_str:
            return ""
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return ""

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date input to ISO format."""
        if not date_str.strip():
            return None

        date_str = date_str.strip()

        # Handle relative dates like +7d
        if date_str.startswith("+") and date_str.endswith("d"):
            try:
                days = int(date_str[1:-1])
                dt = datetime.now(timezone.utc) + timedelta(days=days)
                return dt.isoformat()
            except ValueError:
                return None

        # Handle YYYY-MM-DD format
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            return None

    async def on_mount(self) -> None:
        """Load employees and set initial values."""
        await self._load_employees()
        self.query_one("#input-title", Input).focus()

    async def _load_employees(self) -> None:
        """Load employees for assignee select."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/employees?is_active=true")
                response.raise_for_status()
                data = response.json()
                self._employees = data.get("items", [])

                select = self.query_one("#select-assignee", Select)
                options = [("Unassigned", "")]
                for emp in self._employees:
                    options.append((emp["full_name"], str(emp["id"])))
                select._options = options

                # Set current value if editing
                if self._task_data and self._task_data.get("assignee_employee_id"):
                    select.value = str(self._task_data["assignee_employee_id"])
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            await self._save()
        elif event.button.id == "btn-cancel":
            self.dismiss()

    def action_save(self) -> None:
        """Save action from keybinding."""
        self.run_worker(self._save())

    async def _save(self) -> None:
        """Save the task."""
        title = self.query_one("#input-title", Input).value.strip()
        description = self.query_one("#input-description", Input).value.strip()
        priority = self.query_one("#select-priority", Select).value
        assignee = self.query_one("#select-assignee", Select).value
        due_str = self.query_one("#input-due", Input).value
        is_critical = self.query_one("#check-critical", Checkbox).value

        error_msg = self.query_one("#error-message", Static)

        # Validation
        if not title:
            error_msg.update("Title is required")
            return

        # Parse due date
        due_at = self._parse_date(due_str) if due_str else None

        # Build payload
        payload = {
            "title": title,
            "description": description or None,
            "priority": priority,
            "is_critical": is_critical,
        }

        if assignee:
            payload["assignee_employee_id"] = int(assignee)
        if due_at:
            payload["due_at"] = due_at

        try:
            async with httpx.AsyncClient() as client:
                if self._task_data:
                    # Update existing
                    response = await client.put(
                        f"{self.api_url}/tasks/{self._task_data['id']}",
                        json=payload,
                    )
                else:
                    # Create new
                    response = await client.post(
                        f"{self.api_url}/tasks",
                        json=payload,
                    )

                response.raise_for_status()

                if self.on_save:
                    self.on_save()
                self.dismiss()

        except httpx.HTTPStatusError as e:
            error_msg.update(f"Error: {e.response.text[:50]}")
        except Exception as e:
            error_msg.update(f"Error: {str(e)[:50]}")


class NoteCreateModal(ModalScreen):
    """Modal for creating or editing a note."""

    CSS = """
    NoteCreateModal {
        align: center middle;
    }

    #modal-container {
        width: 70;
        height: auto;
        max-height: 45;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #modal-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }

    .form-row {
        height: auto;
        margin-bottom: 1;
    }

    .form-label {
        width: 12;
        color: $text-muted;
    }

    .form-input {
        width: 1fr;
    }

    #input-content {
        height: 5;
    }

    #button-row {
        margin-top: 2;
        height: 3;
    }

    #button-row Button {
        margin: 0 1;
    }

    .error-text {
        color: $error;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+enter", "save", "Save"),
    ]

    def __init__(
        self,
        api_url: str,
        note: Optional[Dict[str, Any]] = None,
        on_save: Optional[Callable] = None,
    ):
        super().__init__()
        self.api_url = api_url
        self.note = note  # None for create, dict for edit
        self.on_save = on_save

    def compose(self) -> ComposeResult:
        title = "Edit Note" if self.note else "New Note"

        with Vertical(id="modal-container"):
            yield Static(title, id="modal-title")

            with Horizontal(classes="form-row"):
                yield Static("Content:", classes="form-label")
                yield Input(
                    value=self.note.get("content", "") if self.note else "",
                    placeholder="Note content",
                    id="input-content",
                    classes="form-input",
                )

            with Horizontal(classes="form-row"):
                yield Static("Target Type:", classes="form-label")
                yield Select(
                    options=[
                        ("None", ""),
                        ("Deal", "deal"),
                        ("Employee", "employee"),
                        ("Document", "document"),
                        ("Task", "task"),
                    ],
                    value=self.note.get("target_type", "") if self.note else "",
                    id="select-target-type",
                    allow_blank=False,
                )

            with Horizontal(classes="form-row"):
                yield Static("Target ID:", classes="form-label")
                yield Input(
                    value=str(self.note.get("target_id", "")) if self.note and self.note.get("target_id") else "",
                    placeholder="ID of target entity",
                    id="input-target-id",
                    classes="form-input",
                )

            with Horizontal(classes="form-row"):
                yield Static("Review At:", classes="form-label")
                yield Input(
                    value=self._format_date(self.note.get("review_at")) if self.note else "",
                    placeholder="YYYY-MM-DD or +7d",
                    id="input-review",
                    classes="form-input",
                )

            with Horizontal(classes="form-row"):
                yield Static("Tags:", classes="form-label")
                yield Input(
                    value=self.note.get("tags", "") if self.note else "",
                    placeholder="Comma-separated tags",
                    id="input-tags",
                    classes="form-input",
                )

            with Horizontal(classes="form-row"):
                yield Static("Pinned:", classes="form-label")
                yield Checkbox(
                    "Pin this note",
                    value=self.note.get("pinned", False) if self.note else False,
                    id="check-pinned",
                )

            yield Static("", id="error-message", classes="error-text")

            with Horizontal(id="button-row"):
                yield Button("Save [Ctrl+Enter]", id="btn-save", variant="primary")
                yield Button("Cancel [Esc]", id="btn-cancel")

    def _format_date(self, date_str: Optional[str]) -> str:
        """Format date string for display."""
        if not date_str:
            return ""
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return ""

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date input to ISO format."""
        if not date_str.strip():
            return None

        date_str = date_str.strip()

        # Handle relative dates like +7d
        if date_str.startswith("+") and date_str.endswith("d"):
            try:
                days = int(date_str[1:-1])
                dt = datetime.now(timezone.utc) + timedelta(days=days)
                return dt.isoformat()
            except ValueError:
                return None

        # Handle YYYY-MM-DD format
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            return None

    async def on_mount(self) -> None:
        """Focus first input."""
        self.query_one("#input-content", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            await self._save()
        elif event.button.id == "btn-cancel":
            self.dismiss()

    def action_save(self) -> None:
        """Save action from keybinding."""
        self.run_worker(self._save())

    async def _save(self) -> None:
        """Save the note."""
        content = self.query_one("#input-content", Input).value.strip()
        target_type = self.query_one("#select-target-type", Select).value
        target_id_str = self.query_one("#input-target-id", Input).value.strip()
        review_str = self.query_one("#input-review", Input).value
        tags = self.query_one("#input-tags", Input).value.strip()
        pinned = self.query_one("#check-pinned", Checkbox).value

        error_msg = self.query_one("#error-message", Static)

        # Validation
        if not content:
            error_msg.update("Content is required")
            return

        # Parse target ID
        target_id = None
        if target_id_str:
            try:
                target_id = int(target_id_str)
            except ValueError:
                error_msg.update("Target ID must be a number")
                return

        # Parse review date
        review_at = self._parse_date(review_str) if review_str else None

        # Build payload
        payload = {
            "content": content,
            "pinned": pinned,
        }

        if target_type:
            payload["target_type"] = target_type
        if target_id:
            payload["target_id"] = target_id
        if review_at:
            payload["review_at"] = review_at
        if tags:
            payload["tags"] = tags

        try:
            async with httpx.AsyncClient() as client:
                if self.note:
                    # Update existing
                    response = await client.put(
                        f"{self.api_url}/notes/{self.note['id']}",
                        json=payload,
                    )
                else:
                    # Create new
                    response = await client.post(
                        f"{self.api_url}/notes",
                        json=payload,
                    )

                response.raise_for_status()

                if self.on_save:
                    self.on_save()
                self.dismiss()

        except httpx.HTTPStatusError as e:
            error_msg.update(f"Error: {e.response.text[:50]}")
        except Exception as e:
            error_msg.update(f"Error: {str(e)[:50]}")


class ConfirmModal(ModalScreen):
    """Simple confirmation modal."""

    CSS = """
    ConfirmModal {
        align: center middle;
    }

    #confirm-container {
        width: 50;
        height: auto;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }

    #confirm-message {
        text-align: center;
        margin-bottom: 1;
    }

    #confirm-buttons {
        margin-top: 1;
        height: 3;
        align: center middle;
    }

    #confirm-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, message: str, on_confirm: Optional[Callable] = None):
        super().__init__()
        self.message = message
        self.on_confirm = on_confirm

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-container"):
            yield Static(self.message, id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button("[Y]es", id="btn-yes", variant="warning")
                yield Button("[N]o", id="btn-no")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-yes":
            if self.on_confirm:
                self.on_confirm()
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        if self.on_confirm:
            self.on_confirm()
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
