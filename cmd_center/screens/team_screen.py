"""TeamScreen - Employee directory and skill cards.

This screen provides employee management with:
- Employee list with task/log counts
- Skill card view for individual employees
- Quick access to employee logs
"""

from datetime import datetime, timezone
from typing import Any

import httpx
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
)


class TeamScreen(Screen):
    """Team screen for employee directory."""

    BINDINGS = [
        Binding("n", "new_employee", "New", show=True),
        Binding("F2", "edit_employee", "Edit", show=True),
        Binding("s", "view_skills", "Skills", show=True),
        Binding("g", "view_logs", "Logs", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("enter", "view_detail", "View", show=False),
        Binding("escape", "go_back", "Back"),
    ]

    CSS = """
    TeamScreen {
        layout: horizontal;
    }

    #sidebar {
        width: 22;
        background: $surface;
        padding: 1;
    }

    #sidebar Label {
        margin-bottom: 1;
    }

    #content {
        width: 1fr;
        padding: 1;
    }

    #screen-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #stats-bar {
        margin-bottom: 1;
        color: $text-muted;
    }

    #data-table {
        height: 1fr;
    }

    .filter-section {
        margin-top: 1;
    }

    .filter-label {
        margin-bottom: 0;
    }

    /* Department colors */
    .dept-sales { color: $primary; }
    .dept-engineering { color: $success; }
    .dept-operations { color: $warning; }
    .dept-executive { color: $error; }
    """

    def __init__(self, api_url: str) -> None:
        super().__init__()
        self.api_url = api_url
        self.employees: list[dict] = []
        self.department_filter = "all"
        self.active_filter = True

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Filters", classes="filter-label")

                yield Label("Department:", classes="filter-label")
                yield Select(
                    [
                        ("All Departments", "all"),
                        ("Sales", "sales"),
                        ("Engineering", "engineering"),
                        ("Operations", "operations"),
                        ("Executive", "executive"),
                    ],
                    id="dept-select",
                    value="all",
                )

                yield Label("Status:", classes="filter-label")
                yield Checkbox("Active Only", id="active-checkbox", value=True)

                yield Label("", classes="filter-section")

                yield Label("Quick Stats:", classes="filter-label")
                yield Static("Total: —", id="stat-total")
                yield Static("Active: —", id="stat-active")

                yield Label("", classes="filter-section")
                yield Button("Refresh", id="btn-refresh", variant="primary")

            with Vertical(id="content"):
                yield Static("Team Directory", id="screen-title")
                yield Static("", id="stats-bar")
                yield DataTable(id="data-table", cursor_type="row")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen."""
        self._load_data()

    def _load_data(self) -> None:
        """Load employee data."""
        self.run_worker(self._fetch_employees(), exclusive=True)

    async def _fetch_employees(self) -> None:
        """Fetch employees from API."""
        try:
            async with httpx.AsyncClient() as client:
                params = {}
                if self.department_filter != "all":
                    params["department"] = self.department_filter
                if self.active_filter:
                    params["is_active"] = "true"

                response = await client.get(
                    f"{self.api_url}/employees", params=params
                )
                if response.status_code == 200:
                    data = response.json()
                    self.employees = data.get("items", [])
                    await self._enrich_employees(client)
                    self._render_table()
                    self._update_stats()
        except Exception as e:
            self.query_one("#stats-bar", Static).update(f"Error: {e}")

    async def _enrich_employees(self, client: httpx.AsyncClient) -> None:
        """Enrich employee data with task and log counts."""
        for emp in self.employees:
            emp["open_tasks"] = 0
            emp["log_count"] = 0

            try:
                # Get open tasks count
                task_resp = await client.get(
                    f"{self.api_url}/tasks",
                    params={
                        "assignee_employee_id": emp["id"],
                        "status": "open",
                    },
                )
                if task_resp.status_code == 200:
                    emp["open_tasks"] = len(task_resp.json())

                # Get log count
                log_resp = await client.get(
                    f"{self.api_url}/employee-logs",
                    params={"employee_id": emp["id"]},
                )
                if log_resp.status_code == 200:
                    emp["log_count"] = len(log_resp.json())
            except Exception:
                pass

    def _render_table(self) -> None:
        """Render employees table."""
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)

        table.add_columns(
            "ID", "Name", "Role", "Department", "Email", "Tasks", "Logs", "Active"
        )

        for emp in self.employees:
            active_str = "Yes" if emp.get("is_active", True) else "No"

            table.add_row(
                str(emp["id"]),
                emp.get("full_name", "—"),
                emp.get("role_title", "—") or "—",
                emp.get("department", "—") or "—",
                emp.get("email", "—") or "—",
                str(emp.get("open_tasks", 0)),
                str(emp.get("log_count", 0)),
                active_str,
                key=str(emp["id"]),
            )

    def _update_stats(self) -> None:
        """Update sidebar statistics."""
        total = len(self.employees)
        active = sum(1 for e in self.employees if e.get("is_active", True))

        self.query_one("#stat-total", Static).update(f"Total: {total}")
        self.query_one("#stat-active", Static).update(f"Active: {active}")
        self.query_one("#stats-bar", Static).update(
            f"Showing {total} employees"
        )

    # Event handlers
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle filter selection changes."""
        if event.select.id == "dept-select":
            self.department_filter = str(event.value)
            self._load_data()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        if event.checkbox.id == "active-checkbox":
            self.active_filter = event.value
            self._load_data()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-refresh":
            self._load_data()

    # Actions
    def action_new_employee(self) -> None:
        """Create new employee."""
        self.app.push_screen(EmployeeCreateModal(self.api_url), self._on_modal_result)

    def action_edit_employee(self) -> None:
        """Edit selected employee."""
        table = self.query_one("#data-table", DataTable)
        if table.cursor_row is None or not self.employees:
            return

        try:
            row_key = table.get_row_at(table.cursor_row)
            emp_id = int(row_key[0]) if row_key else None
            if emp_id is None:
                return

            employee = next((e for e in self.employees if e["id"] == emp_id), None)
            if employee:
                self.app.push_screen(
                    EmployeeCreateModal(self.api_url, employee), self._on_modal_result
                )
        except Exception:
            pass

    def action_view_skills(self) -> None:
        """View skill card for selected employee."""
        table = self.query_one("#data-table", DataTable)
        if table.cursor_row is None or not self.employees:
            return

        try:
            row_key = table.get_row_at(table.cursor_row)
            emp_id = int(row_key[0]) if row_key else None
            if emp_id is None:
                return

            employee = next((e for e in self.employees if e["id"] == emp_id), None)
            if employee:
                self.app.push_screen(SkillCardModal(self.api_url, employee))
        except Exception:
            pass

    def action_view_logs(self) -> None:
        """View logs for selected employee."""
        table = self.query_one("#data-table", DataTable)
        if table.cursor_row is None or not self.employees:
            return

        try:
            row_key = table.get_row_at(table.cursor_row)
            emp_id = int(row_key[0]) if row_key else None
            if emp_id is None:
                return

            employee = next((e for e in self.employees if e["id"] == emp_id), None)
            if employee:
                self.app.push_screen(EmployeeLogsModal(self.api_url, employee))
        except Exception:
            pass

    def action_view_detail(self) -> None:
        """View employee detail (same as edit for now)."""
        self.action_edit_employee()

    def action_refresh(self) -> None:
        """Refresh data."""
        self._load_data()

    def action_go_back(self) -> None:
        """Go back to dashboard."""
        self.app.switch_screen("dashboard")

    def _on_modal_result(self, result: bool | None) -> None:
        """Handle modal result."""
        if result:
            self._load_data()


class EmployeeCreateModal(ModalScreen):
    """Modal for creating/editing employees."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+enter", "save", "Save"),
    ]

    CSS = """
    EmployeeCreateModal {
        align: center middle;
    }

    #modal-container {
        width: 65;
        height: auto;
        max-height: 85%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #modal-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .field-label {
        margin-top: 1;
    }

    Input, Select {
        width: 100%;
        margin-bottom: 1;
    }

    #button-row {
        margin-top: 1;
        align: right middle;
    }

    #button-row Button {
        margin-left: 1;
    }
    """

    def __init__(self, api_url: str, employee: dict | None = None) -> None:
        super().__init__()
        self.api_url = api_url
        self.employee = employee
        self.is_edit = employee is not None

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(
                "Edit Employee" if self.is_edit else "New Employee",
                id="modal-title",
            )

            yield Label("Full Name:", classes="field-label")
            yield Input(
                value=self.employee.get("full_name", "") if self.employee else "",
                id="name-input",
                placeholder="John Doe",
            )

            yield Label("Email:", classes="field-label")
            yield Input(
                value=self.employee.get("email", "") if self.employee else "",
                id="email-input",
                placeholder="john@company.com",
            )

            yield Label("Role Title:", classes="field-label")
            yield Input(
                value=self.employee.get("role_title", "") if self.employee else "",
                id="role-input",
                placeholder="Sales Manager",
            )

            yield Label("Department:", classes="field-label")
            yield Select(
                [
                    ("Sales", "sales"),
                    ("Engineering", "engineering"),
                    ("Operations", "operations"),
                    ("Executive", "executive"),
                ],
                id="dept-select",
                value=self.employee.get("department", "sales") if self.employee else "sales",
            )

            yield Label("Manager:", classes="field-label")
            yield Select(
                [("None", "none")],  # Will be populated on mount
                id="manager-select",
                value="none",
            )

            yield Checkbox(
                "Active",
                id="active-checkbox",
                value=self.employee.get("is_active", True) if self.employee else True,
            )

            with Horizontal(id="button-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.query_one("#name-input", Input).focus()
        self.run_worker(self._load_managers())

    async def _load_managers(self) -> None:
        """Load potential managers for dropdown."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/employees")
                if response.status_code == 200:
                    data = response.json()
                    employees = data.get("items", [])
                    options = [("None", "none")] + [
                        (e["full_name"], str(e["id"]))
                        for e in employees
                        if not self.employee or e["id"] != self.employee["id"]
                    ]
                    select = self.query_one("#manager-select", Select)
                    select._options = options

                    if self.employee and self.employee.get("manager_id"):
                        select.value = str(self.employee["manager_id"])
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.action_save()

    def action_dismiss(self) -> None:
        self.dismiss(False)

    def action_save(self) -> None:
        self.run_worker(self._save_employee())

    async def _save_employee(self) -> None:
        full_name = self.query_one("#name-input", Input).value.strip()
        if not full_name:
            return

        email = self.query_one("#email-input", Input).value.strip()
        role_title = self.query_one("#role-input", Input).value.strip()
        department = str(self.query_one("#dept-select", Select).value)
        manager_val = str(self.query_one("#manager-select", Select).value)
        is_active = self.query_one("#active-checkbox", Checkbox).value

        data = {
            "full_name": full_name,
            "is_active": is_active,
        }
        if email:
            data["email"] = email
        if role_title:
            data["role_title"] = role_title
        if department:
            data["department"] = department
        if manager_val != "none":
            data["manager_id"] = int(manager_val)

        try:
            async with httpx.AsyncClient() as client:
                if self.is_edit and self.employee:
                    response = await client.patch(
                        f"{self.api_url}/employees/{self.employee['id']}",
                        json=data,
                    )
                else:
                    response = await client.post(
                        f"{self.api_url}/employees",
                        json=data,
                    )

                if response.status_code in (200, 201):
                    self.dismiss(True)
        except Exception:
            pass


class SkillCardModal(ModalScreen):
    """Modal showing employee skill ratings."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("r", "rate_skill", "Rate"),
    ]

    CSS = """
    SkillCardModal {
        align: center middle;
    }

    #modal-container {
        width: 55;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #modal-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .category-title {
        text-style: bold;
        margin-top: 1;
        color: $primary;
    }

    .skill-row {
        margin-left: 2;
    }

    .skill-bar {
        color: $success;
    }

    #button-row {
        margin-top: 2;
        align: center middle;
    }
    """

    def __init__(self, api_url: str, employee: dict) -> None:
        super().__init__()
        self.api_url = api_url
        self.employee = employee
        self.ratings: list[dict] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(
                f"Skill Card: {self.employee['full_name']}", id="modal-title"
            )
            yield Static("Loading...", id="skills-content")

            with Horizontal(id="button-row"):
                yield Button("[R]ate Skill", id="btn-rate")
                yield Button("Close", id="btn-close", variant="primary")

    def on_mount(self) -> None:
        self.run_worker(self._load_skills())

    async def _load_skills(self) -> None:
        """Load skill ratings for employee."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/employees/{self.employee['id']}/skills"
                )
                if response.status_code == 200:
                    self.ratings = response.json()
                    self._render_skills()
                else:
                    self.query_one("#skills-content", Static).update(
                        "No skills rated yet"
                    )
        except Exception as e:
            self.query_one("#skills-content", Static).update(f"Error: {e}")

    def _render_skills(self) -> None:
        """Render skill ratings."""
        if not self.ratings:
            self.query_one("#skills-content", Static).update("No skills rated yet")
            return

        # Group by category
        by_category: dict[str, list] = {}
        for rating in self.ratings:
            cat = rating.get("skill", {}).get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(rating)

        lines = []
        for category, ratings in sorted(by_category.items()):
            lines.append(f"\n[bold]{category.title()} Skills:[/bold]")
            for r in ratings:
                skill_name = r.get("skill", {}).get("name", "Unknown")
                level = r.get("rating", 0)
                bar = "█" * level + "░" * (5 - level)
                lines.append(f"  {skill_name:<20} {bar} {level}/5")

        self.query_one("#skills-content", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.dismiss()
        elif event.button.id == "btn-rate":
            self.action_rate_skill()

    def action_dismiss(self) -> None:
        self.dismiss()

    def action_rate_skill(self) -> None:
        """Open skill rating modal."""
        self.app.push_screen(
            SkillRatingModal(self.api_url, self.employee),
            self._on_rate_complete,
        )

    def _on_rate_complete(self, result: bool | None) -> None:
        if result:
            self.run_worker(self._load_skills())


class SkillRatingModal(ModalScreen):
    """Modal for rating an employee's skill."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+enter", "save", "Save"),
    ]

    CSS = """
    SkillRatingModal {
        align: center middle;
    }

    #modal-container {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #modal-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .field-label {
        margin-top: 1;
    }

    Select {
        width: 100%;
        margin-bottom: 1;
    }

    #button-row {
        margin-top: 1;
        align: right middle;
    }

    #button-row Button {
        margin-left: 1;
    }
    """

    def __init__(self, api_url: str, employee: dict) -> None:
        super().__init__()
        self.api_url = api_url
        self.employee = employee
        self.skills: list[dict] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(
                f"Rate Skill: {self.employee['full_name']}", id="modal-title"
            )

            yield Label("Skill:", classes="field-label")
            yield Select(
                [("Loading...", "loading")],
                id="skill-select",
                value="loading",
            )

            yield Label("Rating:", classes="field-label")
            yield Select(
                [
                    ("1 - Beginner", "1"),
                    ("2 - Basic", "2"),
                    ("3 - Intermediate", "3"),
                    ("4 - Advanced", "4"),
                    ("5 - Expert", "5"),
                ],
                id="rating-select",
                value="3",
            )

            with Horizontal(id="button-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.run_worker(self._load_skills())

    async def _load_skills(self) -> None:
        """Load available skills."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/skills")
                if response.status_code == 200:
                    self.skills = response.json()
                    options = [(s["name"], str(s["id"])) for s in self.skills]
                    select = self.query_one("#skill-select", Select)
                    select._options = options
                    if options:
                        select.value = options[0][1]
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.action_save()

    def action_dismiss(self) -> None:
        self.dismiss(False)

    def action_save(self) -> None:
        self.run_worker(self._save_rating())

    async def _save_rating(self) -> None:
        skill_id = int(self.query_one("#skill-select", Select).value)
        rating = int(self.query_one("#rating-select", Select).value)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/employees/{self.employee['id']}/skills/{skill_id}/rate",
                    json={"rating": rating},
                )
                if response.status_code in (200, 201):
                    self.dismiss(True)
        except Exception:
            pass


class EmployeeLogsModal(ModalScreen):
    """Modal showing employee logs."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("n", "new_log", "New Log"),
    ]

    CSS = """
    EmployeeLogsModal {
        align: center middle;
    }

    #modal-container {
        width: 70;
        height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #modal-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #logs-table {
        height: 1fr;
    }

    #button-row {
        margin-top: 1;
        align: center middle;
    }

    #button-row Button {
        margin-left: 1;
    }
    """

    def __init__(self, api_url: str, employee: dict) -> None:
        super().__init__()
        self.api_url = api_url
        self.employee = employee
        self.logs: list[dict] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(
                f"Logs: {self.employee['full_name']}", id="modal-title"
            )
            yield DataTable(id="logs-table", cursor_type="row")

            with Horizontal(id="button-row"):
                yield Button("[N]ew Log", id="btn-new")
                yield Button("Close", id="btn-close", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#logs-table", DataTable)
        table.add_columns("Date", "Category", "Severity", "Summary")
        self.run_worker(self._load_logs())

    async def _load_logs(self) -> None:
        """Load logs for employee."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/employee-logs",
                    params={"employee_id": self.employee["id"]},
                )
                if response.status_code == 200:
                    self.logs = response.json()
                    self._render_logs()
        except Exception:
            pass

    def _render_logs(self) -> None:
        """Render logs table."""
        table = self.query_one("#logs-table", DataTable)
        table.clear()

        for log in self.logs:
            date_str = "—"
            if log.get("logged_at"):
                logged = datetime.fromisoformat(log["logged_at"].replace("Z", ""))
                date_str = logged.strftime("%Y-%m-%d")

            table.add_row(
                date_str,
                log.get("category", "—"),
                log.get("severity", "—"),
                (log.get("summary") or "—")[:50],
                key=str(log["id"]),
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.dismiss()
        elif event.button.id == "btn-new":
            self.action_new_log()

    def action_dismiss(self) -> None:
        self.dismiss()

    def action_new_log(self) -> None:
        """Create new log for this employee."""
        # Import here to avoid circular import
        from .tracker_screen import LogCreateModal

        self.app.push_screen(
            LogCreateModal(
                self.api_url,
                {self.employee["id"]: self.employee["full_name"]},
            ),
            self._on_log_created,
        )

    def _on_log_created(self, result: bool | None) -> None:
        if result:
            self.run_worker(self._load_logs())
