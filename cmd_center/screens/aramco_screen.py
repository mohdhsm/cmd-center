"""Aramco pipeline screen with multiple modes."""

import httpx
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, DataTable, Input, Footer


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
    """
    
    BINDINGS = [
        ("1", "mode_overdue", "Overdue"),
        ("2", "mode_stuck", "Stuck"),
        ("3", "mode_order", "Order Received"),
        ("4", "mode_compliance", "Compliance"),
        ("5", "mode_cashflow", "Cashflow"),
        ("r", "reload", "Reload"),
    ]
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
        self.current_mode = "overdue"
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Command Center - Aramco Pipeline", id="header")
        
        with Horizontal(id="main-row"):
            # Sidebar
            with Vertical(id="sidebar"):
                yield Static("Aramco Filters", id="sidebar-title")
                yield Static("Mode:")
                yield Button("1 Overdue", id="mode-overdue", variant="primary")
                yield Button("2 Stuck", id="mode-stuck")
                yield Button("3 Order received", id="mode-order")
                yield Button("4 Compliance", id="mode-compliance")
                yield Button("5 Cashflow proj.", id="mode-cashflow")
                yield Static("")
                yield Static("Min days in stage:")
                yield Input(value="30", id="min-days")
                yield Static("")
                yield Button("Reload (R)", id="btn-reload")
            
            # Content
            with Vertical(id="content"):
                yield Static("Aramco Pipeline", id="content-title")
                yield Static("[1] Overdue  [2] Stuck  [3] Order  [4] Compliance  [5] Cashflow", id="tab-hints")
                table = DataTable(id="aramco-table")
                yield table
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Load data when screen is mounted."""
        await self.load_mode_data()
    
    async def load_mode_data(self) -> None:
        """Load data based on current mode."""
        table = self.query_one("#aramco-table", DataTable)
        table.clear(columns=True)  # Clear both rows AND columns
        
        # Set columns based on mode
        if self.current_mode == "overdue":
            table.add_columns("ID", "Title", "Owner", "Stage", "Overdue days", "Value SAR")
            endpoint = "/aramco/overdue"
        elif self.current_mode == "stuck":
            table.add_columns("ID", "Title", "Owner", "Stage", "Days in stage", "Last activity")
            endpoint = "/aramco/stuck"
        elif self.current_mode == "order":
            table.add_columns("ID", "Title", "Owner", "stage","Days in stage")
            endpoint = "/aramco/order_received"
        elif self.current_mode == "compliance":
            table.add_columns("ID", "Title", "Stage", "Survey?", "Quality docs?", "Comment")
            endpoint = "/aramco/compliance"
        elif self.current_mode == "cashflow":
            table.add_columns("Period", "Expected invoice SAR", "# deals", "Comment")
            endpoint = "/aramco/cashflow_projection"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}{endpoint}")
                response.raise_for_status()
                items = response.json()
            
            for item in items:
                if self.current_mode == "overdue":
                    table.add_row(
                        str(item["id"]),
                        item["title"],
                        item["owner"],
                        item["stage"],
                        str(item["overdue_days"]),
                        str(item.get("value_sar", 0)),
                    )
                elif self.current_mode == "stuck":
                    table.add_row(
                        str(item["id"]),
                        item["title"],
                        item["owner"],
                        item["stage"],
                        str(item["days_in_stage"]),
                        str(item.get("last_activity_time", "N/A")),
                    )
                elif self.current_mode == "order":
                    table.add_row(
                        str(item["id"]),
                        item["title"],
                        item["owner"],
                        item["stage"],
                        str(item["days_in_stage"]),
                    )
                # Add other modes similarly...
        
        except Exception as e:
            table.add_row("Error loading data", str(e), "", "", "", "")
    
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