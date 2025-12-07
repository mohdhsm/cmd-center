"""Dashboard screen for Today's Focus."""

import httpx
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, DataTable, Footer


class DashboardScreen(Screen):
    """Dashboard screen showing today's focus items."""
    
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
        ("r", "refresh", "Refresh"),
    ]
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Command Center - Dashboard", id="header")
        
        with Horizontal(id="main-row"):
            # Sidebar
            with Vertical(id="sidebar"):
                yield Static("Dashboard Filters", id="sidebar-title")
                yield Button("Today", id="period-today", variant="primary")
                yield Button("Last 7 days", id="period-7")
                yield Button("Last 30 days", id="period-30")
                yield Static("")
                yield Static("Pipelines:")
                yield Button("Aramco ✓", id="pipe-aramco", variant="success")
                yield Button("Commercial ✓", id="pipe-commercial", variant="success")
                yield Static("")
                yield Button("Refresh", id="btn-refresh")
            
            # Content
            with Vertical(id="content"):
                yield Static("Today's Focus", id="content-title")
                table = DataTable(id="dashboard-table")
                # Columns will be added in load_dashboard_data()
                yield table
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Load data when screen is mounted."""
        await self.load_dashboard_data()
    
    async def load_dashboard_data(self) -> None:
        """Load dashboard data from API."""
        table = self.query_one("#dashboard-table", DataTable)
        table.clear(columns=True)  # Clear both rows AND columns
        
        # Re-add columns after clearing
        table.add_columns("Type", "Pipeline", "Deal", "Owner", "Stage", "Days", "Flag")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/dashboard/today")
                response.raise_for_status()
                items = response.json()
            
            for item in items:
                deal_title = item.get("deal", {}).get("title", "N/A") if item.get("deal") else "Multiple"
                owner = item.get("deal", {}).get("owner", "N/A") if item.get("deal") else "N/A"
                stage = item.get("deal", {}).get("stage", "N/A") if item.get("deal") else "N/A"
                
                table.add_row(
                    item["type"],
                    item["pipeline"],
                    deal_title,
                    owner,
                    stage,
                    "-",
                    item["flag"],
                )
        
        except Exception as e:
            table.add_row("Error", str(e), "", "", "", "", "")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-refresh":
            await self.load_dashboard_data()
    
    def action_refresh(self) -> None:
        """Refresh dashboard data."""
        self.run_worker(self.load_dashboard_data())