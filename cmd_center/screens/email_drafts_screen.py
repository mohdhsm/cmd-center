"""Email drafts screen."""

import httpx
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, ListView, ListItem, Footer


class EmailDraftsScreen(Screen):
    """Email drafts screen for managing follow-up emails."""
    
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
        ("s", "send_email", "Send"),
        ("r", "regenerate", "Regenerate"),
        ("b", "back", "Back"),
    ]
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
        self.drafts = []
        self.selected_draft = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Command Center - Email Drafts", id="header")
        
        with Horizontal(id="main-row"):
            with Vertical(id="sidebar"):
                yield Static("Salespeople", id="sidebar-title")
                yield ListView(id="sales-list")
            
            with Vertical(id="content"):
                yield Static("Email Draft", id="content-title")
                yield Static("To: ", id="email-to")
                yield Static("Subject: ", id="email-subject")
                yield Static("Email body preview here…", id="email-body")
                yield Static("[S] Send   [R] Regenerate   [B] Back", id="email-footer")
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Load email drafts when mounted."""
        await self.load_drafts()
    
    async def load_drafts(self) -> None:
        """Load email drafts from API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_url}/emails/followups/generate")
                response.raise_for_status()
                self.drafts = response.json()
            
            # Populate sales list
            sales_list = self.query_one("#sales-list", ListView)
            sales_list.clear()
            
            for draft in self.drafts:
                deals_count = len(draft.get("deals", []))
                item = ListItem(Static(f"{draft['salesperson']} ({deals_count})"))
                sales_list.append(item)
        
        except Exception as e:
            self.app.notify(f"Error loading drafts: {str(e)}")
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle salesperson selection."""
        index = event.list_view.index
        if 0 <= index < len(self.drafts):
            self.selected_draft = self.drafts[index]
            self.display_draft(self.selected_draft)
    
    def display_draft(self, draft: dict) -> None:
        """Display the selected email draft."""
        self.query_one("#email-to", Static).update(f"To: {draft['to_email']}")
        self.query_one("#email-subject", Static).update(f"Subject: {draft['subject']}")
        self.query_one("#email-body", Static).update(draft['body'])
    
    def action_send_email(self) -> None:
        """Send the currently selected email."""
        if self.selected_draft:
            # Would call send API here
            self.app.notify(f"Email sent to {self.selected_draft['salesperson']}")
        else:
            self.app.notify("No email selected")
    
    def action_regenerate(self) -> None:
        """Regenerate the current email."""
        if self.selected_draft:
            self.app.notify("Regenerating email...")
            # Would call regenerate API here
        else:
            self.app.notify("No email selected")
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()