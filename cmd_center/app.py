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
    ManagementScreen,
    TrackerScreen,
    TeamScreen,
    LoopMonitorScreen,
    CEODashboardScreen,
)
from .screens.agent_screen import AgentScreen


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
        ("d", "switch_screen('ceo_dashboard')", "Dashboard"),
        ("a", "switch_screen('aramco')", "Aramco"),
        ("c", "switch_screen('commercial')", "Commercial"),
        ("o", "switch_screen('owner_kpi')", "Owner KPIs"),
        ("e", "switch_screen('email_drafts')", "Emails"),
        ("m", "switch_screen('management')", "Management"),
        ("t", "switch_screen('tracker')", "Tracker"),
        ("p", "switch_screen('team')", "Team"),
        ("l", "switch_screen('loops')", "Loops"),
        ("w", "switch_screen('dashboard')", "War Room"),  # Old dashboard as "War Room"
        ("i", "open_agent", "Omnious"),
    ]
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.api_url = api_url
    
    def on_mount(self) -> None:
        """Set up the application on mount."""
        # Install all screens
        self.install_screen(CEODashboardScreen(self.api_url), name="ceo_dashboard")
        self.install_screen(DashboardScreen(self.api_url), name="dashboard")  # Old dashboard as "War Room"
        self.install_screen(AramcoPipelineScreen(self.api_url), name="aramco")
        self.install_screen(CommercialPipelineScreen(self.api_url), name="commercial")
        self.install_screen(OwnerKPIScreen(self.api_url), name="owner_kpi")
        self.install_screen(EmailDraftsScreen(self.api_url), name="email_drafts")
        self.install_screen(ManagementScreen(self.api_url), name="management")
        self.install_screen(TrackerScreen(self.api_url), name="tracker")
        self.install_screen(TeamScreen(self.api_url), name="team")
        self.install_screen(LoopMonitorScreen(self.api_url), name="loops")

        # Start with CEO Dashboard (default on launch)
        self.push_screen("ceo_dashboard")
    
    def action_switch_screen(self, screen_name: str) -> None:
        """Switch to a different screen."""
        self.switch_screen(screen_name)

    def action_open_agent(self) -> None:
        """Open Omnious agent screen."""
        self.push_screen(AgentScreen())


def main():
    """Run the Command Center TUI application."""
    app = CommandCenterApp()
    app.run()


if __name__ == "__main__":
    main()