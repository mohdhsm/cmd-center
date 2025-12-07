"""Owner KPI screen."""

import httpx
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, DataTable, Footer


class OwnerKPIScreen(Screen):
    """Owner KPI screen showing metrics per salesperson."""
    
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
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Command Center - Owner KPIs", id="header")
        
        with Horizontal(id="main-row"):
            with Vertical(id="sidebar"):
                yield Static("Owner KPI Filters", id="sidebar-title")
                yield Static("Period:")
                yield Button("This week", id="period-week")
                yield Button("This month", id="period-month", variant="primary")
                yield Button("Last 60 days", id="period-60")
                yield Static("")
                yield Static("Pipelines:")
                yield Button("Aramco ✓", id="pipe-aramco", variant="success")
                yield Button("Commercial ✓", id="pipe-commercial", variant="success")
                yield Static("")
                yield Button("Refresh", id="btn-refresh")
            
            with Vertical(id="content"):
                yield Static("Owner KPIs", id="content-title")
                table = DataTable(id="owner-table")
                # Columns will be added in load_kpi_data()
                yield table
                yield Static("LLM commentary will appear here…", id="owner-commentary")
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Load data when screen is mounted."""
        await self.load_kpi_data()
    
    async def load_kpi_data(self) -> None:
        """Load KPI data from API."""
        table = self.query_one("#owner-table", DataTable)
        table.clear(columns=True)  # Clear both rows AND columns
        
        # Add columns
        table.add_columns(
            "Owner",
            "# Activities",
            "# Projects",
            "Est. value SAR",
            "# to Production",
            "# Overdue",
            "# Stuck",
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/owners/kpis")
                response.raise_for_status()
                kpis = response.json()
            
            for kpi in kpis:
                table.add_row(
                    kpi["owner"],
                    str(kpi["activities_count"]),
                    str(kpi["projects_count"]),
                    f"{kpi['estimated_value_sar']:,.0f}",
                    str(kpi["moved_to_production_count"]),
                    str(kpi["overdue_deals_count"]),
                    str(kpi["stuck_deals_count"]),
                )
        
        except Exception as e:
            table.add_row("Error", str(e), "", "", "", "", "")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-refresh":
            await self.load_kpi_data()