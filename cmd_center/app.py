"""Main Textual application for Command Center."""

from textual.app import App
from textual.widgets import Header, Footer

from .screens import (
    DashboardScreen,
    AramcoPipelineScreen,
    CommercialPipelineScreen,
    OwnerKPIScreen,
    DealDetailScreen,
    EmailDraftsScreen,
)


class CommandCenterApp(App):
    """Command Center TUI Application."""
    
    CSS = """
    Screen {
        background: $background;
    }
    
    Header {
        background: $primary;
    }
    """
    
    TITLE = "Command Center"
    SUB_TITLE = "Sales & Project Management"
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "switch_screen('dashboard')", "Dashboard"),
        ("a", "switch_screen('aramco')", "Aramco"),
        ("c", "switch_screen('commercial')", "Commercial"),
        ("o", "switch_screen('owner_kpi')", "Owner KPIs"),
        ("e", "switch_screen('email_drafts')", "Emails"),
    ]
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
    
    def on_mount(self) -> None:
        """Set up the application on mount."""
        # Install all screens
        self.install_screen(DashboardScreen(self.api_url), name="dashboard")
        self.install_screen(AramcoPipelineScreen(self.api_url), name="aramco")
        self.install_screen(CommercialPipelineScreen(self.api_url), name="commercial")
        self.install_screen(OwnerKPIScreen(self.api_url), name="owner_kpi")
        self.install_screen(EmailDraftsScreen(self.api_url), name="email_drafts")
        
        # Start with dashboard
        self.push_screen("dashboard")
    
    def action_switch_screen(self, screen_name: str) -> None:
        """Switch to a different screen."""
        self.switch_screen(screen_name)


def main():
    """Run the Command Center TUI application."""
    app = CommandCenterApp()
    app.run()


if __name__ == "__main__":
    main()