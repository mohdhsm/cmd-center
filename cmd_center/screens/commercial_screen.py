"""Commercial pipeline screen."""

import httpx
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, DataTable, Footer


class CommercialPipelineScreen(Screen):
    """Commercial pipeline screen with inactive and summary modes."""
    
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
    """
    
    BINDINGS = [
        ("1", "mode_inactive", "Inactive"),
        ("2", "mode_summary", "Summary"),
        ("r", "reload", "Reload"),
    ]
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
        self.current_mode = "inactive"
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Command Center - Commercial Pipeline", id="header")
        
        with Horizontal(id="main-row"):
            with Vertical(id="sidebar"):
                yield Static("Commercial Filters", id="sidebar-title")
                yield Static("Mode:")
                yield Button("1 Inactive (60+ days)", id="mode-inactive", variant="primary")
                yield Button("2 Recent summary", id="mode-summary")
                yield Static("")
                yield Button("Reload", id="btn-reload")
            
            with Vertical(id="content"):
                yield Static("Commercial Pipeline", id="content-title")
                yield Static("[1] Inactive  [2] Recent summary", id="tab-hints")
                table = DataTable(id="commercial-table")
                yield table
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Load data when screen is mounted."""
        await self.load_mode_data()
    
    async def load_mode_data(self) -> None:
        """Load data based on current mode."""
        table = self.query_one("#commercial-table", DataTable)
        table.clear(columns=True)  # Clear both rows AND columns
        
        if self.current_mode == "inactive":
            table.add_columns("ID", "Title", "Owner", "Stage", "Days in stage", "Last activity")
            endpoint = "/commercial/inactive"
        else:
            table.add_columns("ID", "Title", "Owner", "Org", "Last activity", "LLM summary")
            endpoint = "/commercial/recent_summary"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}{endpoint}")
                response.raise_for_status()
                items = response.json()
            
            for item in items:
                if self.current_mode == "inactive":
                    table.add_row(
                        str(item["id"]),
                        item["title"],
                        item["owner"],
                        item["stage"],
                        str(item["days_in_stage"]),
                        str(item.get("last_activity_time", "N/A")),
                    )
                else:
                    table.add_row(
                        str(item["id"]),
                        item["title"],
                        item["owner"],
                        item.get("org_name", "N/A"),
                        str(item.get("last_activity_date", "N/A")),
                        item.get("llm_summary", "")[:50],
                    )
        
        except Exception as e:
            table.add_row("Error", str(e), "", "", "", "")
    
    def action_mode_inactive(self) -> None:
        """Switch to inactive mode."""
        self.current_mode = "inactive"
        self.run_worker(self.load_mode_data())
    
    def action_mode_summary(self) -> None:
        """Switch to summary mode."""
        self.current_mode = "summary"
        self.run_worker(self.load_mode_data())
    
    def action_reload(self) -> None:
        """Reload data."""
        self.run_worker(self.load_mode_data())