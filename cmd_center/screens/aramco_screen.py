"""Aramco pipeline screen with multiple modes."""

import asyncio
import httpx
from collections import defaultdict
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, DataTable, Input, Footer, Select
from textual.widgets._data_table import RowDoesNotExist
from textual import log
from .notes_modal_screen import NotesModalScreen
from .overdue_summary_modal import OverdueSummaryModal
from .stuck_summary_modal import StuckSummaryModal
from .order_received_summary_modal import OrderReceivedSummaryModal


class AramcoPipelineScreen(Screen):
    """Aramco pipeline screen with different analysis modes."""
    
    CSS = """
    Screen {
        layout: vertical;
    }

    #main-row {
        height: 1fr;
    }

    #sidebar {
        width: 32;
        border: solid grey;
        padding: 1;
    }

    #content {
        border: solid grey;
        padding: 1;
    }

    #sidebar-title, #content-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #cashflow-buckets-container {
        height: 40%;
        border-bottom: solid grey;
    }

    #cashflow-deals-container {
        height: 60%;
    }

    #cashflow-deals-label {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
        color: yellow;
    }

    .hidden {
        display: none;
    }
    """
    
    BINDINGS = [
        ("1", "mode_overdue", "Overdue"),
        ("2", "mode_stuck", "Stuck"),
        ("3", "mode_order", "Order Received"),
        ("4", "mode_compliance", "Compliance"),
        ("5", "mode_cashflow", "Cashflow"),
        ("r", "reload", "Reload"),
        ("t", "focus_table", "Focus Table"),
        ("s", "focus_sidebar", "Focus Sidebar"),
    ]
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
        self.current_mode = "overdue"
        self.selected_deal_id: str | None = None
        self._items_cache = []  # Cache for last fetched items to enable client-side sorting/grouping
        self._cashflow_deals_cache = []  # Cache for cashflow critical deals
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Command Center - Aramco Pipeline", id="header")
        
        with Horizontal(id="main-row"):
            # Sidebar
            with Vertical(id="sidebar"):
                yield Static("Options", id="sidebar-title")
                yield Static("Group By:")
                # Add "None" option for no grouping, set initial value to "none"
                yield Select(options=[("— None —", "none"), ("Owner", "owner"), ("Stage", "stage")], value="none", allow_blank=False, id="groupby-select")
                yield Static("Sort By:")
                # Set initial value and allow_blank=False to prevent NoSelection errors
                yield Select(options=[("Overdue Days","overdue"),("Value","value"),("Last Updated","last_updated")], value="overdue", allow_blank=False, id="sortby-select")
                yield Button("View Summary", id="view-summary-button")
                yield Static("-----------")
                yield (Static("Deal Specfic Actions:", id="sidebar-title2"))
                yield Button("Check last 5 notes", id="check-notes-button")
                yield Button("Generate follo-up email",id="generate-followup-button")
                yield Button("Get Summary", id="get-summary-button")
                yield Button("Add Note", id="add-note-button")
                yield Button("Check Compliance", id="check-compliance-button")
                             
                 
            
            # Content
            with Vertical(id="content"):
                yield Static("Aramco Pipeline", id="content-title")
                yield Static("[1] Overdue  [2] Stuck  [3] Order  [4] Compliance  [5] Cashflow", id="tab-hints")
                # Main table (used for all modes)
                yield DataTable(id="aramco-table")
                # Cashflow critical deals section (hidden by default)
                with Vertical(id="cashflow-deals-container", classes="hidden"):
                    yield Static("Critical Deals (Next 2 Weeks)", id="cashflow-deals-label")
                    yield DataTable(id="cashflow-deals-table")
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Load data when screen is mounted."""
        await self.load_mode_data()
    
    async def load_mode_data(self) -> None:
        """Load data based on current mode."""
        table = self.query_one("#aramco-table", DataTable)
        table.clear(columns=True)  # Clear both rows AND columns

        # Show/hide cashflow deals container based on mode
        cashflow_container = self.query_one("#cashflow-deals-container", Vertical)
        if self.current_mode == "cashflow":
            cashflow_container.remove_class("hidden")
        else:
            cashflow_container.add_class("hidden")

        # Set columns based on mode
        if self.current_mode == "overdue":
            table.add_columns("ID", "Title", "Owner", "Stage", "Overdue days", "Value SAR")
            endpoint = "/aramco/overdue"
        elif self.current_mode == "stuck":
            table.add_columns("ID", "Title", "Owner", "Stage", "Days in stage", "Last activity")
            endpoint = "/aramco/stuck"
        elif self.current_mode == "order":
            table.add_columns("ID", "Title", "Owner", "stage", "Days in stage")
            endpoint = "/aramco/order_received"
        elif self.current_mode == "compliance":
            table.add_columns("ID", "Title", "Stage", "Survey?", "Quality docs?", "Comment")
            endpoint = "/aramco/compliance"
        elif self.current_mode == "cashflow":
            table.add_columns("Period", "Expected SAR", "# Deals", "Comment")
            endpoint = "/aramco/cashflow_projection"
            # Also setup the critical deals table
            deals_table = self.query_one("#cashflow-deals-table", DataTable)
            deals_table.clear(columns=True)
            deals_table.add_columns("ID", "Title", "Owner", "Stage", "Invoice Date", "Conf%", "Value SAR")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if self.current_mode == "cashflow":
                    # Fetch both buckets and critical deals in parallel
                    buckets_resp, deals_resp = await asyncio.gather(
                        client.get(f"{self.api_url}/aramco/cashflow_projection"),
                        client.get(f"{self.api_url}/aramco/cashflow_critical_deals"),
                        return_exceptions=True
                    )

                    # Handle buckets response
                    if isinstance(buckets_resp, Exception):
                        items = []
                        table.add_row("Error", str(buckets_resp), "", "", key="error")
                    else:
                        buckets_resp.raise_for_status()
                        items = buckets_resp.json()

                    # Handle critical deals response
                    if isinstance(deals_resp, Exception):
                        self._cashflow_deals_cache = []
                    else:
                        deals_resp.raise_for_status()
                        self._cashflow_deals_cache = deals_resp.json()

                    self._items_cache = items
                    self.render_table(items)
                    self._render_cashflow_deals()
                else:
                    response = await client.get(f"{self.api_url}{endpoint}")
                    response.raise_for_status()
                    items = response.json()
                    self._items_cache = items  # Cache items for client-side sorting/grouping
                    self.render_table(items)

        except Exception as e:
            # Match error row columns to the current mode's column count
            error_msg = str(e)[:80]  # Truncate long errors
            if self.current_mode == "cashflow":
                table.add_row("Error", error_msg, "", "")
            elif self.current_mode == "order":
                table.add_row("Error", error_msg, "", "", "")
            else:
                table.add_row("Error", error_msg, "", "", "", "")

    def render_table(self, items):
        """Render the table with optional sorting and grouping for overdue mode."""
        table = self.query_one("#aramco-table", DataTable)

        # Capture cursor state before re-rendering
        cursor_row, cursor_col = table.cursor_coordinate
        # Capture stable row key as string from current cursor coordinate
        cursor_key = None
        if table.row_count > 0 and cursor_row < table.row_count:
            cell_key = table.coordinate_to_cell_key((cursor_row, cursor_col))
            cursor_key = str(cell_key.row_key) if cell_key and cell_key.row_key else None

        table.clear()  # Clear rows, keep columns

        if self.current_mode == "overdue":
            # Get current select values with safe defaults (should not be NoSelection due to allow_blank=False)
            groupby_select = self.query_one("#groupby-select", Select)
            sortby_select = self.query_one("#sortby-select", Select)
            groupby = groupby_select.value if groupby_select.value else "owner"
            sortby = sortby_select.value if sortby_select.value else "overdue"

            # Apply sorting
            if sortby == "overdue":
                items = sorted(items, key=lambda x: x.get("overdue_days", 0))
            elif sortby == "value":
                items = sorted(items, key=lambda x: x.get("value_sar", 0))
            elif sortby == "last_updated":
                if all("last_updated" in item for item in items):
                    items = sorted(items, key=lambda x: x["last_updated"])
                # Else ignore sorting for this field

            # Apply grouping only if not "none"
            if groupby == "none":
                # No grouping: just add sorted rows directly
                for item in items:
                    table.add_row(
                        str(item["id"]),
                        item["title"],
                        item["owner"],
                        item["stage"],
                        str(item["overdue_days"]),
                        str(item.get("value_sar", 0)),
                        key=str(item["id"])
                    )
            else:
                # Apply grouping
                groups = defaultdict(list)
                for item in items:
                    key = item.get(groupby, "Unknown")
                    groups[key].append(item)

                # Populate table with groups and headers
                for group_key, group_items in groups.items():
                    # Add group header row with key=None so it's not selectable
                    header_text = f"=== {groupby.title()}: {group_key} ==="
                    table.add_row(header_text, "", "", "", "", "", key=None)
                    # Add data rows for this group
                    for item in group_items:
                        table.add_row(
                            str(item["id"]),
                            item["title"],
                            item["owner"],
                            item["stage"],
                            str(item["overdue_days"]),
                            str(item.get("value_sar", 0)),
                            key=str(item["id"])
                        )
        else:
            # For other modes, populate normally without sorting/grouping
            for item in items:
                if self.current_mode == "stuck":
                    table.add_row(
                        str(item["id"]),
                        item["title"],
                        item["owner"],
                        item["stage"],
                        str(item["days_in_stage"]),
                        str(item.get("last_activity_time", "N/A")),
                        key=str(item["id"]),
                    )
                elif self.current_mode == "order":
                    table.add_row(
                        str(item["id"]),
                        item["title"],
                        item["owner"],
                        item["stage"],
                        str(item["days_in_stage"]),
                        key=str(item["id"])
                    )
                elif self.current_mode == "compliance":
                    table.add_row(
                        str(item["id"]),
                        item["title"],
                        item["stage"],
                        str(item.get("survey", "N/A")),
                        str(item.get("quality_docs", "N/A")),
                        str(item.get("comment", "")),
                        key=str(item["id"])
                    )
                elif self.current_mode == "cashflow":
                    table.add_row(
                        item["period"],
                        f"{item.get('expected_invoice_value_sar', 0):,.0f}",
                        str(item.get("deal_count", 0)),
                        str(item.get("comment", "")),
                        key=item["period"]
                    )

        # Restore cursor: prefer by key, fallback to clamped row index
        self._restore_cursor(table, cursor_key, cursor_row, cursor_col)

    def _restore_cursor(self, table: DataTable, cursor_key, cursor_row, cursor_col):
        """Restore cursor position after table re-render."""
        if cursor_key is not None and table.row_count > 0:
            try:
                # Try to find the same row key in the new table
                new_row = table.get_row_index(cursor_key)
                table.move_cursor(row=new_row, column=min(cursor_col, len(table.ordered_columns) - 1))
            except RowDoesNotExist:
                # Key not found, fallback to clamped row index
                new_row = min(cursor_row, table.row_count - 1)
                table.move_cursor(row=new_row, column=min(cursor_col, len(table.ordered_columns) - 1))
        elif table.row_count > 0:
            # No previous key, just clamp the row index
            new_row = min(cursor_row, table.row_count - 1)
            table.move_cursor(row=new_row, column=min(cursor_col, len(table.ordered_columns) - 1))

    def _render_cashflow_deals(self):
        """Render the cashflow critical deals table."""
        deals_table = self.query_one("#cashflow-deals-table", DataTable)
        deals_table.clear()  # Clear rows, keep columns

        if not self._cashflow_deals_cache:
            deals_table.add_row("No deals", "predicted to invoice", "in next 2 weeks", "", "", "", "", key="empty")
            return

        for deal in self._cashflow_deals_cache:
            # Format the predicted invoice date
            invoice_date = deal.get("predicted_invoice_date", "")
            if invoice_date:
                # Handle ISO format datetime string
                invoice_date = invoice_date[:10] if len(invoice_date) > 10 else invoice_date

            # Format confidence as percentage
            confidence = deal.get("confidence", 0)
            conf_str = f"{confidence * 100:.0f}%"

            # Truncate title if too long
            title = deal.get("deal_title", "")[:35]

            deals_table.add_row(
                str(deal.get("deal_id", "")),
                title,
                str(deal.get("owner_name", "Unknown"))[:15] if deal.get("owner_name") else "Unknown",
                str(deal.get("stage", ""))[:15] if deal.get("stage") else "",
                invoice_date,
                conf_str,
                f"{deal.get('value_sar', 0):,.0f}" if deal.get("value_sar") else "0",
                key=str(deal.get("deal_id", ""))
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        mode_map = {
            "mode-overdue": "overdue",
            "mode-stuck": "stuck",
            "mode-order": "order",
            "mode-compliance": "compliance",
            "mode-cashflow": "cashflow",
        }

        if event.button.id in mode_map:
            self.current_mode = mode_map[event.button.id]
            await self.load_mode_data()
        elif event.button.id == "btn-reload":
            await self.load_mode_data()
        elif event.button.id == "check-notes-button":
            # Show notes modal for selected deal
            table = self.query_one("#aramco-table", DataTable)
            cursor_row, cursor_col = table.cursor_coordinate
            cell_key = table.coordinate_to_cell_key((cursor_row, cursor_col))
            row_key = cell_key.row_key if cell_key else None
            row_key_obj = cell_key.row_key if cell_key else None
            row_key_value = row_key_obj.value if row_key_obj is not None else None
            log(f"row_key_obj={row_key_obj!r} row_key_value={row_key_value!r} type={type(row_key_value)}")
            if row_key is None:
                self.notify("Select a deal row (not a group header).", severity="warning")
            else:
                try:
                    deal_id_int = int(row_key_value)
                    self.selected_deal_id = str(deal_id_int)
                    modal = NotesModalScreen(self.api_url, deal_id_int)
                    self.app.push_screen(modal)
                except ValueError:
                    self.notify("Invalid deal ID.", severity="warning")
        elif event.button.id == "view-summary-button":
            # Route to correct modal based on current mode
            if self.current_mode == "overdue":
                modal = OverdueSummaryModal(api_url=self.api_url)
            elif self.current_mode == "stuck":
                modal = StuckSummaryModal(api_url=self.api_url)
            elif self.current_mode == "order":
                modal = OrderReceivedSummaryModal(api_url=self.api_url)
            elif self.current_mode == "compliance":
                self.notify("Summary not yet implemented for Compliance.", severity="info")
                return
            elif self.current_mode == "cashflow":
                self.notify("Summary not available for Cashflow view.", severity="info")
                return

            self.notify("Loading summary...", severity="info")
            self.app.push_screen(modal)
    
    def action_mode_overdue(self) -> None:
        """Switch to overdue mode."""
        self.current_mode = "overdue"
        self.run_worker(self.load_mode_data())
    
    def action_mode_stuck(self) -> None:
        """Switch to stuck mode."""
        self.current_mode = "stuck"
        self.run_worker(self.load_mode_data())
    
    def action_mode_order(self) -> None:
        """Switch to order received mode."""
        self.current_mode = "order"
        self.run_worker(self.load_mode_data())
    
    def action_mode_compliance(self) -> None:
        """Switch to compliance mode."""
        self.current_mode = "compliance"
        self.run_worker(self.load_mode_data())
    
    def action_mode_cashflow(self) -> None:
        """Switch to cashflow mode."""
        self.current_mode = "cashflow"
        self.run_worker(self.load_mode_data())
    
    def action_reload(self) -> None:
        """Reload current mode data."""
        self.run_worker(self.load_mode_data())

    def action_focus_table(self) -> None:
        """Focus the data table."""
        table = self.query_one("#aramco-table", DataTable)
        table.focus()

    def action_focus_sidebar(self) -> None:
        """Focus the first focusable widget in sidebar (preferably groupby-select)."""
        # Try to focus groupby-select first
        try:
            groupby_select = self.query_one("#groupby-select", Select)
            groupby_select.focus()
        except Exception:
            # Fallback: focus the sidebar container or first button
            try:
                sidebar = self.query_one("#sidebar", Vertical)
                sidebar.focus()
            except Exception:
                # Last resort: focus first button
                try:
                    button = self.query_one("#view-summary-button", Button)
                    button.focus()
                except Exception:
                    pass  # No focusable widget found

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes for groupby and sortby to re-render table."""
        if event.select.id in ["groupby-select", "sortby-select"]:
            if self._items_cache:
                self.render_table(self._items_cache)  # Re-render with cached data

    def on_key(self, event) -> None:
        """Handle Enter key on focused DataTable to select deal."""
        if event.key == "enter":
            table = self.query_one("#aramco-table", DataTable)
            if table.has_focus and table.row_count > 0:
                cursor_row, cursor_col = table.cursor_coordinate
                # Use coordinate_to_cell_key to get row key at cursor
                cell_key = table.coordinate_to_cell_key((cursor_row, cursor_col))
                row_key = cell_key.row_key if cell_key and cell_key.row_key else None
                # Set selected_deal_id to row key string if not None (group headers have key=None)
                self.selected_deal_id = str(row_key) if row_key is not None else None