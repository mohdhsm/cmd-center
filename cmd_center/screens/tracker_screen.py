"""TrackerScreen - Documents, Bonuses, Employee Logs, Skills tracking.

This screen provides compliance and HR tracking with 4 tab modes:
- Documents: Track licenses, contracts, insurance with expiry dates
- Bonuses: Track employee bonuses and payments
- Logs: View employee logs (achievements, issues, feedback)
- Skills: View skill ratings across employees
"""

from datetime import datetime, timezone
from typing import Any

import httpx
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Select,
    Static,
)

from .ceo_modals import ConfirmModal


class TrackerScreen(Screen):
    """Tracker screen for Documents, Bonuses, Logs, and Skills."""

    BINDINGS = [
        Binding("1", "mode_documents", "Docs", show=True),
        Binding("2", "mode_bonuses", "Bonuses", show=True),
        Binding("3", "mode_logs", "Logs", show=True),
        Binding("4", "mode_skills", "Skills", show=True),
        Binding("n", "new_item", "New", show=True),
        Binding("e", "edit_item", "Edit", show=True),
        Binding("$", "record_payment", "Payment", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("escape", "go_back", "Back"),
    ]

    CSS = """
    TrackerScreen {
        layout: horizontal;
    }

    #sidebar {
        width: 20;
        background: $surface;
        padding: 1;
    }

    #sidebar Label {
        margin-bottom: 1;
    }

    #sidebar .mode-button {
        width: 100%;
        margin-bottom: 1;
    }

    #sidebar .mode-button.active {
        background: $primary;
    }

    #content {
        width: 1fr;
        padding: 1;
    }

    #mode-title {
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

    /* Priority and status colors */
    .status-active { color: $success; }
    .status-expired { color: $error; text-style: bold; }
    .status-pending { color: $warning; }
    .status-paid { color: $success; }
    .status-partial { color: $warning; }

    /* Severity colors for logs */
    .severity-critical { color: $error; text-style: bold; }
    .severity-high { color: $error; }
    .severity-medium { color: $warning; }
    .severity-low { color: $success; }

    /* Expiry warning colors */
    .expiring-critical { color: $error; text-style: bold; }
    .expiring-warning { color: $warning; }
    """

    def __init__(self, api_url: str) -> None:
        super().__init__()
        self.api_url = api_url
        self.current_mode = "documents"
        self.items: list[dict] = []
        self.employees: dict[int, str] = {}

        # Filter states
        self.doc_type_filter = "all"
        self.doc_status_filter = "all"
        self.bonus_status_filter = "all"
        self.bonus_employee_filter = "all"
        self.log_category_filter = "all"
        self.log_employee_filter = "all"
        self.skill_category_filter = "all"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Mode:", classes="filter-label")
                yield Button("1 Documents", id="btn-documents", classes="mode-button active")
                yield Button("2 Bonuses", id="btn-bonuses", classes="mode-button")
                yield Button("3 Logs", id="btn-logs", classes="mode-button")
                yield Button("4 Skills", id="btn-skills", classes="mode-button")

                yield Label("", classes="filter-section")

                # Document filters (shown by default)
                with Container(id="doc-filters"):
                    yield Label("Type:", classes="filter-label")
                    yield Select(
                        [
                            ("All Types", "all"),
                            ("License", "license"),
                            ("Contract", "contract"),
                            ("Insurance", "insurance"),
                            ("Certification", "certification"),
                        ],
                        id="doc-type-select",
                        value="all",
                    )
                    yield Label("Status:", classes="filter-label")
                    yield Select(
                        [
                            ("All", "all"),
                            ("Active", "active"),
                            ("Expired", "expired"),
                            ("Pending", "pending_renewal"),
                        ],
                        id="doc-status-select",
                        value="all",
                    )

                # Bonus filters (hidden by default)
                with Container(id="bonus-filters", classes="hidden"):
                    yield Label("Status:", classes="filter-label")
                    yield Select(
                        [
                            ("All", "all"),
                            ("Pending", "pending"),
                            ("Partial", "partial"),
                            ("Paid", "paid"),
                        ],
                        id="bonus-status-select",
                        value="all",
                    )
                    yield Label("Employee:", classes="filter-label")
                    yield Select(
                        [("All Employees", "all")],
                        id="bonus-employee-select",
                        value="all",
                    )

                # Log filters (hidden by default)
                with Container(id="log-filters", classes="hidden"):
                    yield Label("Category:", classes="filter-label")
                    yield Select(
                        [
                            ("All", "all"),
                            ("Achievement", "achievement"),
                            ("Issue", "issue"),
                            ("Feedback", "feedback"),
                            ("Performance", "performance_review"),
                        ],
                        id="log-category-select",
                        value="all",
                    )
                    yield Label("Employee:", classes="filter-label")
                    yield Select(
                        [("All Employees", "all")],
                        id="log-employee-select",
                        value="all",
                    )

                # Skill filters (hidden by default)
                with Container(id="skill-filters", classes="hidden"):
                    yield Label("Category:", classes="filter-label")
                    yield Select(
                        [
                            ("All", "all"),
                            ("Technical", "technical"),
                            ("Soft", "soft"),
                            ("Domain", "domain"),
                        ],
                        id="skill-category-select",
                        value="all",
                    )

                yield Button("Refresh", id="btn-refresh", variant="primary")

            with Vertical(id="content"):
                yield Static("Documents", id="mode-title")
                yield Static("", id="stats-bar")
                yield DataTable(id="data-table", cursor_type="row")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen."""
        self._load_employees()
        self._switch_mode("documents")

    def _load_employees(self) -> None:
        """Load employee list for filter dropdowns."""
        self.run_worker(self._fetch_employees(), exclusive=True)

    async def _fetch_employees(self) -> None:
        """Fetch employees from API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/employees")
                if response.status_code == 200:
                    employees = response.json()
                    self.employees = {e["id"]: e["full_name"] for e in employees}
                    self._update_employee_selects()
        except Exception:
            pass

    def _update_employee_selects(self) -> None:
        """Update employee select options."""
        options = [("All Employees", "all")] + [
            (name, str(id)) for id, name in self.employees.items()
        ]

        bonus_select = self.query_one("#bonus-employee-select", Select)
        bonus_select._options = options
        bonus_select.value = "all"

        log_select = self.query_one("#log-employee-select", Select)
        log_select._options = options
        log_select.value = "all"

    def _switch_mode(self, mode: str) -> None:
        """Switch between document/bonus/log/skill modes."""
        self.current_mode = mode

        # Update button states
        for btn_id in ["btn-documents", "btn-bonuses", "btn-logs", "btn-skills"]:
            btn = self.query_one(f"#{btn_id}", Button)
            btn.remove_class("active")

        mode_btn_map = {
            "documents": "btn-documents",
            "bonuses": "btn-bonuses",
            "logs": "btn-logs",
            "skills": "btn-skills",
        }
        self.query_one(f"#{mode_btn_map[mode]}", Button).add_class("active")

        # Show/hide filter sections
        for filter_id in ["doc-filters", "bonus-filters", "log-filters", "skill-filters"]:
            container = self.query_one(f"#{filter_id}", Container)
            container.add_class("hidden")

        filter_map = {
            "documents": "doc-filters",
            "bonuses": "bonus-filters",
            "logs": "log-filters",
            "skills": "skill-filters",
        }
        self.query_one(f"#{filter_map[mode]}", Container).remove_class("hidden")

        # Update title
        title_map = {
            "documents": "Documents",
            "bonuses": "Bonuses",
            "logs": "Employee Logs",
            "skills": "Skills",
        }
        self.query_one("#mode-title", Static).update(title_map[mode])

        # Reload data
        self._load_data()

    def _load_data(self) -> None:
        """Load data for current mode."""
        self.run_worker(self._fetch_data(), exclusive=True)

    async def _fetch_data(self) -> None:
        """Fetch data from API based on current mode."""
        try:
            async with httpx.AsyncClient() as client:
                if self.current_mode == "documents":
                    await self._fetch_documents(client)
                elif self.current_mode == "bonuses":
                    await self._fetch_bonuses(client)
                elif self.current_mode == "logs":
                    await self._fetch_logs(client)
                elif self.current_mode == "skills":
                    await self._fetch_skills(client)
        except Exception as e:
            self.query_one("#stats-bar", Static).update(f"Error: {e}")

    async def _fetch_documents(self, client: httpx.AsyncClient) -> None:
        """Fetch documents."""
        params = {}
        if self.doc_type_filter != "all":
            params["document_type"] = self.doc_type_filter
        if self.doc_status_filter != "all":
            params["status"] = self.doc_status_filter

        response = await client.get(f"{self.api_url}/documents", params=params)
        if response.status_code == 200:
            self.items = response.json()
            self._render_documents()

    def _render_documents(self) -> None:
        """Render documents table."""
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)

        table.add_columns("ID", "Title", "Type", "Expiry", "Status", "Responsible")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expiring_soon = 0
        critical = 0

        for doc in self.items:
            expiry_str = "—"
            expiry_class = ""

            if doc.get("expiry_date"):
                expiry = datetime.fromisoformat(doc["expiry_date"].replace("Z", ""))
                days_until = (expiry - now).days

                if days_until < 0:
                    expiry_str = f"-{abs(days_until)}d EXPIRED"
                    expiry_class = "expiring-critical"
                    critical += 1
                elif days_until <= 7:
                    expiry_str = f"{days_until}d"
                    expiry_class = "expiring-critical"
                    critical += 1
                elif days_until <= 30:
                    expiry_str = f"{days_until}d"
                    expiry_class = "expiring-warning"
                    expiring_soon += 1
                else:
                    expiry_str = f"{days_until}d"

            responsible = self.employees.get(doc.get("responsible_employee_id"), "—")

            table.add_row(
                str(doc["id"]),
                doc["title"][:30],
                doc.get("document_type", "—"),
                expiry_str,
                doc.get("status", "—"),
                responsible,
                key=str(doc["id"]),
            )

        stats = f"Total: {len(self.items)}"
        if expiring_soon > 0:
            stats += f" | Expiring soon: {expiring_soon}"
        if critical > 0:
            stats += f" | Critical: {critical}"
        self.query_one("#stats-bar", Static).update(stats)

    async def _fetch_bonuses(self, client: httpx.AsyncClient) -> None:
        """Fetch bonuses."""
        params = {}
        if self.bonus_status_filter != "all":
            params["status"] = self.bonus_status_filter
        if self.bonus_employee_filter != "all":
            params["employee_id"] = self.bonus_employee_filter

        response = await client.get(f"{self.api_url}/bonuses", params=params)
        if response.status_code == 200:
            self.items = response.json()
            self._render_bonuses()

    def _render_bonuses(self) -> None:
        """Render bonuses table."""
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)

        table.add_columns("ID", "Title", "Employee", "Amount", "Due", "Status", "Paid")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        total_pending = 0
        total_amount = 0

        for bonus in self.items:
            employee = self.employees.get(bonus.get("employee_id"), "—")

            amount = bonus.get("amount", 0)
            currency = bonus.get("currency", "SAR")
            amount_str = f"{amount:,.0f} {currency}"

            due_str = "—"
            if bonus.get("due_date"):
                due = datetime.fromisoformat(bonus["due_date"].replace("Z", ""))
                days_until = (due - now).days
                if days_until < 0:
                    due_str = f"-{abs(days_until)}d"
                else:
                    due_str = f"{days_until}d"

            paid_amount = bonus.get("paid_amount", 0)
            paid_str = f"{paid_amount:,.0f}/{amount:,.0f}"

            status = bonus.get("status", "pending")

            if status == "pending":
                total_pending += amount
            total_amount += amount

            table.add_row(
                str(bonus["id"]),
                bonus["title"][:25],
                employee[:15],
                amount_str,
                due_str,
                status,
                paid_str,
                key=str(bonus["id"]),
            )

        stats = f"Total: {len(self.items)} | Amount: {total_amount:,.0f} SAR"
        if total_pending > 0:
            stats += f" | Pending: {total_pending:,.0f} SAR"
        self.query_one("#stats-bar", Static).update(stats)

    async def _fetch_logs(self, client: httpx.AsyncClient) -> None:
        """Fetch employee logs."""
        params = {}
        if self.log_category_filter != "all":
            params["category"] = self.log_category_filter
        if self.log_employee_filter != "all":
            params["employee_id"] = self.log_employee_filter

        response = await client.get(f"{self.api_url}/employee-logs", params=params)
        if response.status_code == 200:
            self.items = response.json()
            self._render_logs()

    def _render_logs(self) -> None:
        """Render employee logs table."""
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)

        table.add_columns("ID", "Date", "Employee", "Category", "Severity", "Summary")

        category_icons = {
            "achievement": "trophy",
            "issue": "warning",
            "feedback": "speech",
            "performance_review": "chart",
        }

        for log in self.items:
            employee = self.employees.get(log.get("employee_id"), "—")

            date_str = "—"
            if log.get("logged_at"):
                logged = datetime.fromisoformat(log["logged_at"].replace("Z", ""))
                date_str = logged.strftime("%Y-%m-%d")

            category = log.get("category", "—")
            icon = category_icons.get(category, "")
            category_display = f"{icon} {category}" if icon else category

            summary = log.get("summary", "")[:40]

            table.add_row(
                str(log["id"]),
                date_str,
                employee[:15],
                category_display,
                log.get("severity", "—"),
                summary,
                key=str(log["id"]),
            )

        stats = f"Total: {len(self.items)} logs"
        self.query_one("#stats-bar", Static).update(stats)

    async def _fetch_skills(self, client: httpx.AsyncClient) -> None:
        """Fetch skills."""
        params = {}
        if self.skill_category_filter != "all":
            params["category"] = self.skill_category_filter

        response = await client.get(f"{self.api_url}/skills", params=params)
        if response.status_code == 200:
            self.items = response.json()
            self._render_skills()

    def _render_skills(self) -> None:
        """Render skills table."""
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)

        table.add_columns("ID", "Skill", "Category", "Description")

        for skill in self.items:
            table.add_row(
                str(skill["id"]),
                skill["name"],
                skill.get("category", "—"),
                (skill.get("description") or "—")[:40],
                key=str(skill["id"]),
            )

        stats = f"Total: {len(self.items)} skills"
        self.query_one("#stats-bar", Static).update(stats)

    # Event handlers
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-documents":
            self._switch_mode("documents")
        elif button_id == "btn-bonuses":
            self._switch_mode("bonuses")
        elif button_id == "btn-logs":
            self._switch_mode("logs")
        elif button_id == "btn-skills":
            self._switch_mode("skills")
        elif button_id == "btn-refresh":
            self._load_data()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle filter selection changes."""
        select_id = event.select.id
        value = str(event.value)

        if select_id == "doc-type-select":
            self.doc_type_filter = value
        elif select_id == "doc-status-select":
            self.doc_status_filter = value
        elif select_id == "bonus-status-select":
            self.bonus_status_filter = value
        elif select_id == "bonus-employee-select":
            self.bonus_employee_filter = value
        elif select_id == "log-category-select":
            self.log_category_filter = value
        elif select_id == "log-employee-select":
            self.log_employee_filter = value
        elif select_id == "skill-category-select":
            self.skill_category_filter = value

        self._load_data()

    # Actions
    def action_mode_documents(self) -> None:
        """Switch to documents mode."""
        self._switch_mode("documents")

    def action_mode_bonuses(self) -> None:
        """Switch to bonuses mode."""
        self._switch_mode("bonuses")

    def action_mode_logs(self) -> None:
        """Switch to logs mode."""
        self._switch_mode("logs")

    def action_mode_skills(self) -> None:
        """Switch to skills mode."""
        self._switch_mode("skills")

    def action_new_item(self) -> None:
        """Create new item based on current mode."""
        if self.current_mode == "documents":
            self.app.push_screen(DocumentCreateModal(self.api_url), self._on_item_created)
        elif self.current_mode == "bonuses":
            self.app.push_screen(
                BonusCreateModal(self.api_url, self.employees), self._on_item_created
            )
        elif self.current_mode == "logs":
            self.app.push_screen(
                LogCreateModal(self.api_url, self.employees), self._on_item_created
            )
        elif self.current_mode == "skills":
            self.app.push_screen(SkillCreateModal(self.api_url), self._on_item_created)

    def action_edit_item(self) -> None:
        """Edit selected item."""
        table = self.query_one("#data-table", DataTable)
        if table.cursor_row is None or not self.items:
            return

        try:
            row_key = table.get_row_at(table.cursor_row)
            item_id = int(row_key[0]) if row_key else None
            if item_id is None:
                return

            item = next((i for i in self.items if i["id"] == item_id), None)
            if not item:
                return

            if self.current_mode == "documents":
                self.app.push_screen(
                    DocumentCreateModal(self.api_url, item), self._on_item_created
                )
            elif self.current_mode == "bonuses":
                self.app.push_screen(
                    BonusCreateModal(self.api_url, self.employees, item),
                    self._on_item_created,
                )
            elif self.current_mode == "logs":
                self.app.push_screen(
                    LogCreateModal(self.api_url, self.employees, item),
                    self._on_item_created,
                )
            elif self.current_mode == "skills":
                self.app.push_screen(
                    SkillCreateModal(self.api_url, item), self._on_item_created
                )
        except Exception:
            pass

    def action_record_payment(self) -> None:
        """Record payment for bonus (only in bonus mode)."""
        if self.current_mode != "bonuses":
            return

        table = self.query_one("#data-table", DataTable)
        if table.cursor_row is None or not self.items:
            return

        try:
            row_key = table.get_row_at(table.cursor_row)
            item_id = int(row_key[0]) if row_key else None
            if item_id is None:
                return

            bonus = next((i for i in self.items if i["id"] == item_id), None)
            if not bonus:
                return

            self.app.push_screen(
                BonusPaymentModal(self.api_url, bonus), self._on_item_created
            )
        except Exception:
            pass

    def action_refresh(self) -> None:
        """Refresh data."""
        self._load_data()

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.switch_screen("dashboard")

    def _on_item_created(self, result: bool | None) -> None:
        """Handle modal result."""
        if result:
            self._load_data()


# Modal classes for creating/editing items
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea


class DocumentCreateModal(ModalScreen):
    """Modal for creating/editing documents."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+enter", "save", "Save"),
    ]

    CSS = """
    DocumentCreateModal {
        align: center middle;
    }

    #modal-container {
        width: 60;
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

    def __init__(self, api_url: str, document: dict | None = None) -> None:
        super().__init__()
        self.api_url = api_url
        self.document = document
        self.is_edit = document is not None

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(
                "Edit Document" if self.is_edit else "New Document",
                id="modal-title",
            )

            yield Label("Title:", classes="field-label")
            yield Input(
                value=self.document.get("title", "") if self.document else "",
                id="title-input",
                placeholder="Document title",
            )

            yield Label("Type:", classes="field-label")
            yield Select(
                [
                    ("License", "license"),
                    ("Contract", "contract"),
                    ("Insurance", "insurance"),
                    ("Certification", "certification"),
                ],
                id="type-select",
                value=self.document.get("document_type", "license") if self.document else "license",
            )

            yield Label("Expiry Date (YYYY-MM-DD or +30d):", classes="field-label")
            expiry_val = ""
            if self.document and self.document.get("expiry_date"):
                expiry_val = self.document["expiry_date"][:10]
            yield Input(value=expiry_val, id="expiry-input", placeholder="2025-12-31")

            yield Label("Status:", classes="field-label")
            yield Select(
                [
                    ("Active", "active"),
                    ("Pending Renewal", "pending_renewal"),
                    ("Expired", "expired"),
                ],
                id="status-select",
                value=self.document.get("status", "active") if self.document else "active",
            )

            with Horizontal(id="button-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.query_one("#title-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.action_save()

    def action_dismiss(self) -> None:
        self.dismiss(False)

    def action_save(self) -> None:
        self.run_worker(self._save_document())

    async def _save_document(self) -> None:
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            return

        doc_type = str(self.query_one("#type-select", Select).value)
        status = str(self.query_one("#status-select", Select).value)
        expiry_str = self.query_one("#expiry-input", Input).value.strip()

        expiry_date = None
        if expiry_str:
            expiry_date = self._parse_date(expiry_str)

        data = {
            "title": title,
            "document_type": doc_type,
            "status": status,
        }
        if expiry_date:
            data["expiry_date"] = expiry_date

        try:
            async with httpx.AsyncClient() as client:
                if self.is_edit and self.document:
                    response = await client.patch(
                        f"{self.api_url}/documents/{self.document['id']}",
                        json=data,
                    )
                else:
                    response = await client.post(
                        f"{self.api_url}/documents",
                        json=data,
                    )

                if response.status_code in (200, 201):
                    self.dismiss(True)
        except Exception:
            pass

    def _parse_date(self, date_str: str) -> str | None:
        if date_str.startswith("+") and date_str.endswith("d"):
            try:
                days = int(date_str[1:-1])
                from datetime import timedelta

                future = datetime.now(timezone.utc) + timedelta(days=days)
                return future.strftime("%Y-%m-%dT00:00:00Z")
            except ValueError:
                return None
        else:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return f"{date_str}T00:00:00Z"
            except ValueError:
                return None


class BonusCreateModal(ModalScreen):
    """Modal for creating/editing bonuses."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+enter", "save", "Save"),
    ]

    CSS = """
    BonusCreateModal {
        align: center middle;
    }

    #modal-container {
        width: 60;
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

    def __init__(
        self, api_url: str, employees: dict[int, str], bonus: dict | None = None
    ) -> None:
        super().__init__()
        self.api_url = api_url
        self.employees = employees
        self.bonus = bonus
        self.is_edit = bonus is not None

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(
                "Edit Bonus" if self.is_edit else "New Bonus",
                id="modal-title",
            )

            yield Label("Title:", classes="field-label")
            yield Input(
                value=self.bonus.get("title", "") if self.bonus else "",
                id="title-input",
                placeholder="Bonus title",
            )

            yield Label("Employee:", classes="field-label")
            emp_options = [(name, str(id)) for id, name in self.employees.items()]
            current_emp = str(self.bonus.get("employee_id", "")) if self.bonus else ""
            yield Select(
                emp_options,
                id="employee-select",
                value=current_emp if current_emp else (emp_options[0][1] if emp_options else ""),
            )

            yield Label("Amount:", classes="field-label")
            yield Input(
                value=str(self.bonus.get("amount", "")) if self.bonus else "",
                id="amount-input",
                placeholder="5000",
            )

            yield Label("Currency:", classes="field-label")
            yield Select(
                [("SAR", "SAR"), ("USD", "USD")],
                id="currency-select",
                value=self.bonus.get("currency", "SAR") if self.bonus else "SAR",
            )

            yield Label("Due Date (YYYY-MM-DD or +30d):", classes="field-label")
            due_val = ""
            if self.bonus and self.bonus.get("due_date"):
                due_val = self.bonus["due_date"][:10]
            yield Input(value=due_val, id="due-input", placeholder="2025-01-15")

            with Horizontal(id="button-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.query_one("#title-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.action_save()

    def action_dismiss(self) -> None:
        self.dismiss(False)

    def action_save(self) -> None:
        self.run_worker(self._save_bonus())

    async def _save_bonus(self) -> None:
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            return

        employee_id = int(self.query_one("#employee-select", Select).value)
        amount_str = self.query_one("#amount-input", Input).value.strip()
        currency = str(self.query_one("#currency-select", Select).value)
        due_str = self.query_one("#due-input", Input).value.strip()

        try:
            amount = float(amount_str)
        except ValueError:
            return

        due_date = None
        if due_str:
            due_date = self._parse_date(due_str)

        data = {
            "title": title,
            "employee_id": employee_id,
            "amount": amount,
            "currency": currency,
        }
        if due_date:
            data["due_date"] = due_date

        try:
            async with httpx.AsyncClient() as client:
                if self.is_edit and self.bonus:
                    response = await client.patch(
                        f"{self.api_url}/bonuses/{self.bonus['id']}",
                        json=data,
                    )
                else:
                    response = await client.post(
                        f"{self.api_url}/bonuses",
                        json=data,
                    )

                if response.status_code in (200, 201):
                    self.dismiss(True)
        except Exception:
            pass

    def _parse_date(self, date_str: str) -> str | None:
        if date_str.startswith("+") and date_str.endswith("d"):
            try:
                days = int(date_str[1:-1])
                from datetime import timedelta

                future = datetime.now(timezone.utc) + timedelta(days=days)
                return future.strftime("%Y-%m-%dT00:00:00Z")
            except ValueError:
                return None
        else:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return f"{date_str}T00:00:00Z"
            except ValueError:
                return None


class BonusPaymentModal(ModalScreen):
    """Modal for recording bonus payment."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+enter", "save", "Save"),
    ]

    CSS = """
    BonusPaymentModal {
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

    .info-row {
        margin-bottom: 1;
    }

    .field-label {
        margin-top: 1;
    }

    Input {
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

    def __init__(self, api_url: str, bonus: dict) -> None:
        super().__init__()
        self.api_url = api_url
        self.bonus = bonus

    def compose(self) -> ComposeResult:
        amount = self.bonus.get("amount", 0)
        paid = self.bonus.get("paid_amount", 0)
        remaining = amount - paid
        currency = self.bonus.get("currency", "SAR")

        with Vertical(id="modal-container"):
            yield Label("Record Payment", id="modal-title")

            yield Label(f"Bonus: {self.bonus['title']}", classes="info-row")
            yield Label(f"Total: {amount:,.0f} {currency}", classes="info-row")
            yield Label(f"Paid: {paid:,.0f} {currency}", classes="info-row")
            yield Label(f"Remaining: {remaining:,.0f} {currency}", classes="info-row")

            yield Label("Payment Amount:", classes="field-label")
            yield Input(
                value=str(remaining),
                id="payment-input",
                placeholder=str(remaining),
            )

            with Horizontal(id="button-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Record", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.query_one("#payment-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.action_save()

    def action_dismiss(self) -> None:
        self.dismiss(False)

    def action_save(self) -> None:
        self.run_worker(self._record_payment())

    async def _record_payment(self) -> None:
        payment_str = self.query_one("#payment-input", Input).value.strip()
        try:
            payment = float(payment_str)
        except ValueError:
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/bonuses/{self.bonus['id']}/payment",
                    json={"amount": payment},
                )

                if response.status_code == 200:
                    self.dismiss(True)
        except Exception:
            pass


class LogCreateModal(ModalScreen):
    """Modal for creating/editing employee logs."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+enter", "save", "Save"),
    ]

    CSS = """
    LogCreateModal {
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

    Input, Select, TextArea {
        width: 100%;
        margin-bottom: 1;
    }

    TextArea {
        height: 5;
    }

    #button-row {
        margin-top: 1;
        align: right middle;
    }

    #button-row Button {
        margin-left: 1;
    }
    """

    def __init__(
        self, api_url: str, employees: dict[int, str], log: dict | None = None
    ) -> None:
        super().__init__()
        self.api_url = api_url
        self.employees = employees
        self.log = log
        self.is_edit = log is not None

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(
                "Edit Log" if self.is_edit else "New Employee Log",
                id="modal-title",
            )

            yield Label("Employee:", classes="field-label")
            emp_options = [(name, str(id)) for id, name in self.employees.items()]
            current_emp = str(self.log.get("employee_id", "")) if self.log else ""
            yield Select(
                emp_options,
                id="employee-select",
                value=current_emp if current_emp else (emp_options[0][1] if emp_options else ""),
            )

            yield Label("Category:", classes="field-label")
            yield Select(
                [
                    ("Achievement", "achievement"),
                    ("Issue", "issue"),
                    ("Feedback", "feedback"),
                    ("Performance Review", "performance_review"),
                ],
                id="category-select",
                value=self.log.get("category", "feedback") if self.log else "feedback",
            )

            yield Label("Severity:", classes="field-label")
            yield Select(
                [
                    ("Low", "low"),
                    ("Medium", "medium"),
                    ("High", "high"),
                    ("Critical", "critical"),
                ],
                id="severity-select",
                value=self.log.get("severity", "medium") if self.log else "medium",
            )

            yield Label("Summary:", classes="field-label")
            yield Input(
                value=self.log.get("summary", "") if self.log else "",
                id="summary-input",
                placeholder="Brief summary",
            )

            yield Label("Details:", classes="field-label")
            yield TextArea(
                self.log.get("details", "") if self.log else "",
                id="details-input",
            )

            with Horizontal(id="button-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.query_one("#summary-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.action_save()

    def action_dismiss(self) -> None:
        self.dismiss(False)

    def action_save(self) -> None:
        self.run_worker(self._save_log())

    async def _save_log(self) -> None:
        summary = self.query_one("#summary-input", Input).value.strip()
        if not summary:
            return

        employee_id = int(self.query_one("#employee-select", Select).value)
        category = str(self.query_one("#category-select", Select).value)
        severity = str(self.query_one("#severity-select", Select).value)
        details = self.query_one("#details-input", TextArea).text.strip()

        data = {
            "employee_id": employee_id,
            "category": category,
            "severity": severity,
            "summary": summary,
        }
        if details:
            data["details"] = details

        try:
            async with httpx.AsyncClient() as client:
                if self.is_edit and self.log:
                    response = await client.patch(
                        f"{self.api_url}/employee-logs/{self.log['id']}",
                        json=data,
                    )
                else:
                    response = await client.post(
                        f"{self.api_url}/employee-logs",
                        json=data,
                    )

                if response.status_code in (200, 201):
                    self.dismiss(True)
        except Exception:
            pass


class SkillCreateModal(ModalScreen):
    """Modal for creating/editing skills."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+enter", "save", "Save"),
    ]

    CSS = """
    SkillCreateModal {
        align: center middle;
    }

    #modal-container {
        width: 55;
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

    def __init__(self, api_url: str, skill: dict | None = None) -> None:
        super().__init__()
        self.api_url = api_url
        self.skill = skill
        self.is_edit = skill is not None

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label(
                "Edit Skill" if self.is_edit else "New Skill",
                id="modal-title",
            )

            yield Label("Name:", classes="field-label")
            yield Input(
                value=self.skill.get("name", "") if self.skill else "",
                id="name-input",
                placeholder="Skill name",
            )

            yield Label("Category:", classes="field-label")
            yield Select(
                [
                    ("Technical", "technical"),
                    ("Soft", "soft"),
                    ("Domain", "domain"),
                ],
                id="category-select",
                value=self.skill.get("category", "technical") if self.skill else "technical",
            )

            yield Label("Description:", classes="field-label")
            yield Input(
                value=self.skill.get("description", "") if self.skill else "",
                id="description-input",
                placeholder="Optional description",
            )

            with Horizontal(id="button-row"):
                yield Button("Cancel", variant="default", id="btn-cancel")
                yield Button("Save", variant="primary", id="btn-save")

    def on_mount(self) -> None:
        self.query_one("#name-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-save":
            self.action_save()

    def action_dismiss(self) -> None:
        self.dismiss(False)

    def action_save(self) -> None:
        self.run_worker(self._save_skill())

    async def _save_skill(self) -> None:
        name = self.query_one("#name-input", Input).value.strip()
        if not name:
            return

        category = str(self.query_one("#category-select", Select).value)
        description = self.query_one("#description-input", Input).value.strip()

        data = {
            "name": name,
            "category": category,
        }
        if description:
            data["description"] = description

        try:
            async with httpx.AsyncClient() as client:
                if self.is_edit and self.skill:
                    response = await client.patch(
                        f"{self.api_url}/skills/{self.skill['id']}",
                        json=data,
                    )
                else:
                    response = await client.post(
                        f"{self.api_url}/skills",
                        json=data,
                    )

                if response.status_code in (200, 201):
                    self.dismiss(True)
        except Exception:
            pass
