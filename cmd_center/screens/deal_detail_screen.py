"""Deal detail screen."""

import httpx
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, DataTable, Footer


class DealDetailScreen(Screen):
    """Deal detail screen showing comprehensive deal information."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #deal-main {
        height: 1fr;
    }
    
    #deal-body {
        height: 1fr;
    }
    
    #deal-notes, #deal-llm {
        border: solid grey;
        padding: 1;
    }
    """
    
    BINDINGS = [
        ("b", "back", "Back"),
        ("e", "add_to_email", "Add to Email"),
    ]
    
    def __init__(self, deal_id: int, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.deal_id = deal_id
        self.api_url = api_url
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical(id="deal-main"):
            yield Static("Deal Detail", id="deal-header")
            
            with Horizontal(id="deal-summary-row"):
                yield Static("Loading deal...", id="deal-summary")
            
            with Horizontal(id="deal-body"):
                with Vertical(id="deal-notes"):
                    yield Static("Notes", id="notes-title")
                    table = DataTable(id="notes-table")
                    table.add_columns("Date", "Author", "Note (short)")
                    yield table
                
                with Vertical(id="deal-llm"):
                    yield Static("AI Summary", id="llm-title")
                    yield Static("Loading...", id="llm-summary")
                    yield Static("Compliance checks:", id="llm-compliance-title")
                    yield Static("", id="llm-compliance")
            
            yield Static("[B] Back   [E] Add to follow-up email", id="deal-footer")
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Load deal data when mounted."""
        await self.load_deal_data()
    
    async def load_deal_data(self) -> None:
        """Load deal detail and notes from API."""
        try:
            async with httpx.AsyncClient() as client:
                # Get deal detail
                response = await client.get(f"{self.api_url}/deals/{self.deal_id}/detail")
                response.raise_for_status()
                deal = response.json()
                
                # Update summary
                summary = self.query_one("#deal-summary", Static)
                summary.update(
                    f"Pipeline: {deal['pipeline']} | Stage: {deal['stage']} | "
                    f"Owner: {deal['owner']} | Value: {deal.get('value_sar', 0):,.0f} SAR"
                )
                
                # Get notes
                notes_response = await client.get(f"{self.api_url}/deals/{self.deal_id}/notes")
                notes_response.raise_for_status()
                notes = notes_response.json()
                
                # Populate notes table
                notes_table = self.query_one("#notes-table", DataTable)
                notes_table.clear()
                
                for note in notes:
                    notes_table.add_row(
                        str(note["date"])[:10],
                        note.get("author", "Unknown"),
                        note["content"][:50],
                    )
                
                # Update LLM summary
                llm_summary = self.query_one("#llm-summary", Static)
                llm_summary.update("Deal summary will be generated here...")
        
        except Exception as e:
            summary = self.query_one("#deal-summary", Static)
            summary.update(f"Error loading deal: {str(e)}")
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_add_to_email(self) -> None:
        """Add this deal to follow-up email list."""
        # This would typically update a state/database
        self.app.notify("Deal added to follow-up list")