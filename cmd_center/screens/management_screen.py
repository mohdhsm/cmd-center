"""Management screen for Tasks and Notes."""

from datetime import datetime, timezone
from typing import Optional

import httpx
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, DataTable, Footer, Select, Input
from textual.binding import Binding


class ManagementScreen(Screen):
    """Task and Note management screen."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #header {
        height: 3;
        background: $primary;
        color: $text;
        text-align: center;
        padding: 1;
        text-style: bold;
    }

    #main-row {
        height: 1fr;
    }

    #sidebar {
        width: 28;
        border: solid $primary;
        padding: 1;
    }

    #sidebar-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .sidebar-section {
        margin-top: 1;
        margin-bottom: 1;
    }

    .sidebar-label {
        margin-top: 1;
        color: $text-muted;
    }

    #content {
        border: solid $primary;
        padding: 1;
    }

    #content-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #mode-indicator {
        margin-bottom: 1;
        color: $text-muted;
    }

    #main-table {
        height: 1fr;
    }

    #action-hints {
        height: 1;
        margin-top: 1;
        color: $text-muted;
    }

    #stats-line {
        height: 1;
        color: $text-muted;
    }

    .mode-button {
        margin: 0 1 0 0;
        min-width: 12;
    }

    .mode-active {
        background: $primary;
    }

    .priority-high {
        color: $error;
        text-style: bold;
    }

    .priority-medium {
        color: $warning;
    }

    .priority-low {
        color: $success;
    }

    .status-done {
        color: $success;
    }

    .status-overdue {
        color: $error;
    }
    """

    BINDINGS = [
        Binding("1", "mode_tasks", "Tasks", show=True),
        Binding("2", "mode_notes", "Notes", show=True),
        Binding("n", "new_item", "New", show=True),
        Binding("e", "edit_item", "Edit", show=True),
        Binding("c", "complete_task", "Complete", show=True),
        Binding("d", "delete_item", "Delete", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("enter", "view_detail", "View", show=False),
    ]

    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
        self.current_mode = "tasks"
        self._tasks_cache = []
        self._notes_cache = []
        self._employees_cache = []

        # Filter state
        self.task_status_filter = "all"
        self.task_priority_filter = "all"
        self.task_assignee_filter = "all"
        self.note_target_filter = "all"
        self.note_pinned_filter = "all"

    def compose(self) -> ComposeResult:
        yield Static("Command Center - Management", id="header")

        with Horizontal(id="main-row"):
            with Vertical(id="sidebar"):
                yield Static("Mode", id="sidebar-title")

                with Horizontal(classes="sidebar-section"):
                    yield Button("1 Tasks", id="btn-tasks", classes="mode-button mode-active")
                    yield Button("2 Notes", id="btn-notes", classes="mode-button")

                yield Static("Filters", classes="sidebar-label")

                # Task filters (shown by default)
                with Vertical(id="task-filters"):
                    yield Static("Status:", classes="sidebar-label")
                    yield Select(
                        options=[
                            ("All", "all"),
                            ("Open", "open"),
                            ("In Progress", "in_progress"),
                            ("Done", "done"),
                        ],
                        value="all",
                        id="filter-status",
                        allow_blank=False,
                    )

                    yield Static("Priority:", classes="sidebar-label")
                    yield Select(
                        options=[
                            ("All", "all"),
                            ("High", "high"),
                            ("Medium", "medium"),
                            ("Low", "low"),
                        ],
                        value="all",
                        id="filter-priority",
                        allow_blank=False,
                    )

                    yield Static("Assignee:", classes="sidebar-label")
                    yield Select(
                        options=[("All", "all")],
                        value="all",
                        id="filter-assignee",
                        allow_blank=False,
                    )

                # Note filters (hidden by default)
                with Vertical(id="note-filters", classes="hidden"):
                    yield Static("Target Type:", classes="sidebar-label")
                    yield Select(
                        options=[
                            ("All", "all"),
                            ("Deal", "deal"),
                            ("Employee", "employee"),
                            ("Document", "document"),
                        ],
                        value="all",
                        id="filter-target",
                        allow_blank=False,
                    )

                    yield Static("Pinned:", classes="sidebar-label")
                    yield Select(
                        options=[
                            ("All", "all"),
                            ("Pinned Only", "true"),
                        ],
                        value="all",
                        id="filter-pinned",
                        allow_blank=False,
                    )

                yield Static("", classes="sidebar-section")
                yield Button("Refresh (r)", id="btn-refresh")

            with Vertical(id="content"):
                yield Static("Tasks", id="content-title")
                yield Static("[1] Tasks  [2] Notes", id="mode-indicator")
                yield DataTable(id="main-table")
                yield Static("", id="stats-line")
                yield Static("[n] New  [e] Edit  [c] Complete  [d] Delete  [r] Refresh", id="action-hints")

        yield Footer()

    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        await self._load_employees()
        await self.load_data()

    async def _load_employees(self) -> None:
        """Load employees for assignee filter."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/employees?is_active=true")
                response.raise_for_status()
                data = response.json()
                self._employees_cache = data.get("items", [])

                # Update assignee filter
                assignee_select = self.query_one("#filter-assignee", Select)
                options = [("All", "all")]
                for emp in self._employees_cache:
                    options.append((emp["full_name"], str(emp["id"])))
                assignee_select._options = options
        except Exception:
            pass

    async def load_data(self) -> None:
        """Load data based on current mode."""
        if self.current_mode == "tasks":
            await self._load_tasks()
        else:
            await self._load_notes()

    async def _load_tasks(self) -> None:
        """Load and display tasks."""
        table = self.query_one("#main-table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Title", "Assignee", "Priority", "Due", "Status")

        # Build query params
        params = {}
        if self.task_status_filter != "all":
            params["status"] = self.task_status_filter
        if self.task_priority_filter != "all":
            params["priority"] = self.task_priority_filter
        if self.task_assignee_filter != "all":
            params["assignee_employee_id"] = self.task_assignee_filter

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/tasks", params=params)
                response.raise_for_status()
                data = response.json()
                self._tasks_cache = data.get("items", [])

                for task in self._tasks_cache:
                    # Format priority with color hint
                    priority = task.get("priority", "medium").upper()

                    # Format due date
                    due_str = "—"
                    if task.get("due_at"):
                        try:
                            due_dt = datetime.fromisoformat(task["due_at"].replace("Z", "+00:00"))
                            # Ensure timezone-aware for comparison
                            if due_dt.tzinfo is None:
                                due_dt = due_dt.replace(tzinfo=timezone.utc)
                            now = datetime.now(timezone.utc)
                            days = (due_dt - now).days
                            if days < 0:
                                due_str = f"{days}d"
                            elif days == 0:
                                due_str = "Today"
                            else:
                                due_str = f"{days}d"
                        except (ValueError, TypeError):
                            due_str = "—"

                    # Format status with icon
                    status = task.get("status", "open")
                    status_icon = {"open": "○", "in_progress": "◐", "done": "●", "cancelled": "✕"}.get(status, "?")

                    # Get assignee name
                    assignee = "Unassigned"
                    if task.get("assignee_employee_id"):
                        for emp in self._employees_cache:
                            if emp["id"] == task["assignee_employee_id"]:
                                assignee = emp["full_name"]
                                break

                    table.add_row(
                        str(task["id"]),
                        task["title"][:30],
                        assignee[:15],
                        priority,
                        due_str,
                        status_icon,
                        key=str(task["id"]),
                    )

                # Update stats
                stats = self.query_one("#stats-line", Static)
                total = len(self._tasks_cache)
                open_count = sum(1 for t in self._tasks_cache if t.get("status") == "open")
                stats.update(f"Total: {total} | Open: {open_count}")

        except Exception as e:
            table.add_row("Error", str(e)[:40], "", "", "", "")
            self._tasks_cache = []

    async def _load_notes(self) -> None:
        """Load and display notes."""
        table = self.query_one("#main-table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Content", "Target", "Review", "Pin", "Tags")

        # Build query params
        params = {}
        if self.note_target_filter != "all":
            params["target_type"] = self.note_target_filter
        if self.note_pinned_filter == "true":
            params["pinned"] = "true"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/notes", params=params)
                response.raise_for_status()
                data = response.json()
                self._notes_cache = data.get("items", [])

                for note in self._notes_cache:
                    # Format content (first 40 chars)
                    content = note.get("content", "")[:40]
                    if len(note.get("content", "")) > 40:
                        content += "..."

                    # Format target
                    target = "—"
                    if note.get("target_type"):
                        target = f"{note['target_type']}:{note.get('target_id', '?')}"

                    # Format review date
                    review = "—"
                    if note.get("review_at"):
                        try:
                            review_dt = datetime.fromisoformat(note["review_at"].replace("Z", "+00:00"))
                            review = review_dt.strftime("%Y-%m-%d")
                        except (ValueError, TypeError):
                            pass

                    # Pinned indicator
                    pinned = "📌" if note.get("pinned") else ""

                    # Tags
                    tags = note.get("tags", "") or ""

                    table.add_row(
                        str(note["id"]),
                        content,
                        target[:15],
                        review,
                        pinned,
                        tags[:15],
                        key=str(note["id"]),
                    )

                # Update stats
                stats = self.query_one("#stats-line", Static)
                total = len(self._notes_cache)
                pinned_count = sum(1 for n in self._notes_cache if n.get("pinned"))
                stats.update(f"Total: {total} | Pinned: {pinned_count}")

        except Exception as e:
            table.add_row("Error", str(e)[:40], "", "", "", "")
            self._notes_cache = []

    def _switch_mode(self, mode: str) -> None:
        """Switch between tasks and notes mode."""
        self.current_mode = mode

        # Update button styles
        btn_tasks = self.query_one("#btn-tasks", Button)
        btn_notes = self.query_one("#btn-notes", Button)

        if mode == "tasks":
            btn_tasks.add_class("mode-active")
            btn_notes.remove_class("mode-active")
            self.query_one("#task-filters").remove_class("hidden")
            self.query_one("#note-filters").add_class("hidden")
            self.query_one("#content-title", Static).update("Tasks")
            self.query_one("#action-hints", Static).update("[n] New  [e] Edit  [c] Complete  [d] Delete  [r] Refresh")
        else:
            btn_notes.add_class("mode-active")
            btn_tasks.remove_class("mode-active")
            self.query_one("#note-filters").remove_class("hidden")
            self.query_one("#task-filters").add_class("hidden")
            self.query_one("#content-title", Static).update("Notes")
            self.query_one("#action-hints", Static).update("[n] New  [e] Edit  [d] Archive  [r] Refresh")

        self.run_worker(self.load_data())

    def action_mode_tasks(self) -> None:
        """Switch to tasks mode."""
        self._switch_mode("tasks")

    def action_mode_notes(self) -> None:
        """Switch to notes mode."""
        self._switch_mode("notes")

    def action_refresh(self) -> None:
        """Refresh current data."""
        self.run_worker(self.load_data())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-tasks":
            self._switch_mode("tasks")
        elif event.button.id == "btn-notes":
            self._switch_mode("notes")
        elif event.button.id == "btn-refresh":
            await self.load_data()

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle filter changes."""
        if event.select.id == "filter-status":
            self.task_status_filter = str(event.value) if event.value else "all"
        elif event.select.id == "filter-priority":
            self.task_priority_filter = str(event.value) if event.value else "all"
        elif event.select.id == "filter-assignee":
            self.task_assignee_filter = str(event.value) if event.value else "all"
        elif event.select.id == "filter-target":
            self.note_target_filter = str(event.value) if event.value else "all"
        elif event.select.id == "filter-pinned":
            self.note_pinned_filter = str(event.value) if event.value else "all"

        await self.load_data()

    def action_new_item(self) -> None:
        """Open create modal for new item."""
        if self.current_mode == "tasks":
            from .ceo_modals import TaskCreateModal
            self.app.push_screen(TaskCreateModal(self.api_url, on_save=self._on_task_saved))
        else:
            from .ceo_modals import NoteCreateModal
            self.app.push_screen(NoteCreateModal(self.api_url, on_save=self._on_note_saved))

    def _on_task_saved(self) -> None:
        """Callback when task is saved."""
        self.run_worker(self.load_data())

    def _on_note_saved(self) -> None:
        """Callback when note is saved."""
        self.run_worker(self.load_data())

    def action_edit_item(self) -> None:
        """Edit selected item."""
        table = self.query_one("#main-table", DataTable)
        if table.row_count == 0:
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key is None:
            return

        item_id = int(row_key.value)

        if self.current_mode == "tasks":
            # Find task in cache
            task = next((t for t in self._tasks_cache if t["id"] == item_id), None)
            if task:
                from .ceo_modals import TaskCreateModal
                self.app.push_screen(TaskCreateModal(
                    self.api_url,
                    task=task,
                    on_save=self._on_task_saved
                ))
        else:
            # Find note in cache
            note = next((n for n in self._notes_cache if n["id"] == item_id), None)
            if note:
                from .ceo_modals import NoteCreateModal
                self.app.push_screen(NoteCreateModal(
                    self.api_url,
                    note=note,
                    on_save=self._on_note_saved
                ))

    def action_complete_task(self) -> None:
        """Mark selected task as complete."""
        if self.current_mode != "tasks":
            return

        table = self.query_one("#main-table", DataTable)
        if table.row_count == 0:
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key is None:
            return

        task_id = int(row_key.value)
        self.run_worker(self._complete_task(task_id))

    async def _complete_task(self, task_id: int) -> None:
        """Complete a task via API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_url}/tasks/{task_id}/complete")
                response.raise_for_status()
                await self.load_data()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def action_delete_item(self) -> None:
        """Delete/archive selected item."""
        table = self.query_one("#main-table", DataTable)
        if table.row_count == 0:
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if row_key is None:
            return

        item_id = int(row_key.value)

        if self.current_mode == "tasks":
            self.run_worker(self._delete_task(item_id))
        else:
            self.run_worker(self._archive_note(item_id))

    async def _delete_task(self, task_id: int) -> None:
        """Delete a task via API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self.api_url}/tasks/{task_id}")
                response.raise_for_status()
                await self.load_data()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def _archive_note(self, note_id: int) -> None:
        """Archive a note via API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self.api_url}/notes/{note_id}")
                response.raise_for_status()
                await self.load_data()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def action_view_detail(self) -> None:
        """View detail of selected item."""
        # For now, just edit - can add detail modal later
        self.action_edit_item()
