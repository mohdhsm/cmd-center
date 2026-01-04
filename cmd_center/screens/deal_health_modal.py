"""Modal screen for displaying deal health analysis."""

import httpx
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Button, LoadingIndicator
from textual import log


class DealHealthModal(ModalScreen):
    """Modal for displaying deal health analysis results."""

    CSS = """
    DealHealthModal {
        align: center middle;
    }

    #health-modal {
        width: 90;
        height: 40;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #loading-container {
        align: center middle;
        height: 100%;
    }

    #content-scroll {
        height: 32;
        margin-bottom: 1;
    }

    .section-label {
        text-style: bold;
        margin-top: 1;
        color: $text-muted;
    }

    .section-content {
        margin-left: 2;
        margin-bottom: 1;
    }

    #health-badge-healthy {
        background: $success;
        color: $text;
        padding: 0 1;
        text-align: center;
        text-style: bold;
    }

    #health-badge-at_risk {
        background: $warning;
        color: $text;
        padding: 0 1;
        text-align: center;
        text-style: bold;
    }

    #health-badge-critical {
        background: $error;
        color: $text;
        padding: 0 1;
        text-align: center;
        text-style: bold;
    }

    #health-badge-unknown {
        background: $surface-darken-1;
        color: $text-muted;
        padding: 0 1;
        text-align: center;
        text-style: bold;
    }

    #status-flag {
        color: $warning;
        text-style: bold;
        margin-left: 2;
    }

    #summary-text {
        margin: 1 0;
        padding: 1;
        background: $surface-darken-1;
    }

    #recommended-action {
        margin: 1 0;
        padding: 1;
        background: $primary-darken-1;
        border: solid $primary;
    }

    #blockers-list {
        color: $error;
        margin-left: 2;
    }

    #button-row {
        height: 3;
        align: center middle;
    }

    #error-message {
        color: $error;
        text-align: center;
        margin: 2;
    }

    .metric-row {
        height: auto;
    }

    .metric-label {
        width: 30;
    }

    .metric-value {
        width: auto;
    }
    """

    BINDINGS = [
        ("escape", "close", "Close"),
    ]

    def __init__(self, api_url: str, deal_id: int):
        super().__init__()
        self.api_url = api_url
        self.deal_id = deal_id
        self.health_data = None
        self.error_message = None

    def compose(self) -> ComposeResult:
        """Create the modal layout."""
        with Vertical(id="health-modal"):
            yield Static(f"Deal Health Analysis - #{self.deal_id}", id="modal-title")

            with Vertical(id="loading-container"):
                yield LoadingIndicator()
                yield Static("Analyzing deal health...", id="loading-text")

            with Horizontal(id="button-row"):
                yield Button("Close", id="close-button", variant="default")

    def on_mount(self) -> None:
        """Fetch health data when modal is mounted."""
        self.run_worker(self._fetch_health_data(), exclusive=True)

    async def _fetch_health_data(self) -> None:
        """Fetch deal health analysis from API."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.api_url}/deals/{self.deal_id}/health-summary"
                )

                if response.status_code == 200:
                    self.health_data = response.json()
                    self._render_results()
                else:
                    try:
                        error_detail = response.json().get("detail", "Unknown error")
                    except Exception:
                        error_detail = f"HTTP {response.status_code}"
                    self.error_message = error_detail
                    self._render_error()

        except httpx.TimeoutException:
            self.error_message = "Request timed out - analysis may take longer for complex deals"
            self._render_error()
        except Exception as e:
            log(f"Error fetching health data: {e}")
            self.error_message = str(e)[:100]
            self._render_error()

    def _render_results(self) -> None:
        """Render the health analysis results."""
        loading = self.query_one("#loading-container")
        loading.remove()

        data = self.health_data
        health_status = data.get("health_status", "unknown")

        # Build content
        modal = self.query_one("#health-modal")
        button_row = self.query_one("#button-row")

        # Create scrollable content area
        scroll = VerticalScroll(id="content-scroll")
        modal.mount(scroll, before=button_row)

        # Health status badge
        badge_id = f"health-badge-{health_status}"
        badge_text = health_status.upper().replace("_", " ")
        status_flag = data.get("status_flag")
        flag_text = f" [{status_flag}]" if status_flag else ""

        scroll.mount(Static(f" {badge_text}{flag_text} ", id=badge_id))

        # Summary
        scroll.mount(Static("Summary", classes="section-label"))
        scroll.mount(Static(data.get("summary", "No summary available"), id="summary-text"))

        # Stage metrics
        scroll.mount(Static("Stage Metrics", classes="section-label"))
        days = data.get("days_in_stage", 0)
        warning = data.get("stage_threshold_warning", 0)
        critical = data.get("stage_threshold_critical", 0)
        scroll.mount(Static(
            f"  Days in stage: {days} (Warning: {warning}, Critical: {critical})",
            classes="section-content"
        ))

        # Communication
        scroll.mount(Static("Communication", classes="section-label"))
        comm_gap = data.get("communication_gap_days")
        comm_assessment = data.get("communication_assessment", "Unknown")
        gap_text = f"{comm_gap} days" if comm_gap is not None else "N/A"
        scroll.mount(Static(
            f"  Gap: {gap_text} - {comm_assessment}",
            classes="section-content"
        ))

        # Blockers
        blockers = data.get("blockers", [])
        if blockers:
            scroll.mount(Static("Blockers", classes="section-label"))
            blockers_text = "\n".join([f"  - {b}" for b in blockers])
            scroll.mount(Static(blockers_text, id="blockers-list"))

        # Attribution
        attribution = data.get("attribution", "none")
        if attribution and attribution != "none":
            scroll.mount(Static("Attribution", classes="section-label"))
            scroll.mount(Static(
                f"  {attribution.replace('_', ' ').title()}",
                classes="section-content"
            ))

        # Recommended action
        scroll.mount(Static("Recommended Action", classes="section-label"))
        scroll.mount(Static(
            data.get("recommended_action", "No recommendation available"),
            id="recommended-action"
        ))

        # Confidence
        confidence = data.get("confidence", 0)
        scroll.mount(Static(
            f"Confidence: {confidence:.0%}",
            classes="section-content"
        ))

    def _render_error(self) -> None:
        """Render error message."""
        loading = self.query_one("#loading-container")
        loading.remove()

        modal = self.query_one("#health-modal")
        button_row = self.query_one("#button-row")

        modal.mount(
            Static(f"Error: {self.error_message}", id="error-message"),
            before=button_row
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-button":
            self.dismiss(None)

    def action_close(self) -> None:
        """Close the modal."""
        self.dismiss(None)
