"""CEODashboardScreen - Main executive dashboard for Command Center.

This screen provides a comprehensive view of:
- Cash health and collections
- Urgent deals requiring attention
- Pipeline velocity metrics
- Strategic priority progress
- Sales scorecard
"""

from typing import Any, Optional

import httpx
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Label,
    ProgressBar,
    Static,
)


class CEODashboardScreen(Screen):
    """Main CEO Dashboard screen."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
        Binding("a", "go_aramco", "Aramco", show=True),
        Binding("c", "go_commercial", "Commercial", show=True),
        Binding("o", "go_owners", "Owners", show=True),
        Binding("e", "go_emails", "Emails", show=True),
        Binding("m", "go_management", "Mgmt", show=True),
        Binding("t", "go_tracker", "Tracker", show=True),
        Binding("?", "show_help", "Help"),
    ]

    CSS = """
    CEODashboardScreen {
        layout: vertical;
    }

    #main-content {
        height: 1fr;
        padding: 1;
    }

    /* Section titles */
    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    /* Cash Health Section */
    #cash-health {
        height: 7;
        border: solid $primary;
        padding: 0 1;
        margin-bottom: 1;
    }

    #cash-health .section-title {
        margin-bottom: 0;
    }

    .cash-row {
        height: 1;
    }

    .runway-green { color: $success; text-style: bold; }
    .runway-yellow { color: $warning; text-style: bold; }
    .runway-red { color: $error; text-style: bold; }

    /* Middle Row - Attention + Velocity */
    #middle-row {
        height: 12;
        margin-bottom: 1;
    }

    #attention-section {
        width: 1fr;
        border: solid $warning;
        padding: 0 1;
        margin-right: 1;
    }

    #velocity-section {
        width: 1fr;
        border: solid $primary;
        padding: 0 1;
    }

    #attention-table {
        height: 8;
    }

    .velocity-row {
        height: 1;
    }

    .stage-bar {
        width: 20;
    }

    .trend-better { color: $success; }
    .trend-worse { color: $error; }
    .trend-stable { color: $text-muted; }

    /* Strategic Priorities */
    #priorities-section {
        height: 5;
        border: solid $success;
        padding: 0 1;
        margin-bottom: 1;
    }

    #priorities-row {
        height: 3;
    }

    .priority-card {
        width: 1fr;
        padding: 0 1;
    }

    .priority-label {
        text-style: bold;
    }

    .status-green { color: $success; }
    .status-yellow { color: $warning; }
    .status-red { color: $error; }

    /* Sales Scorecard */
    #scorecard-section {
        height: 4;
        border: solid $secondary;
        padding: 0 1;
    }

    .scorecard-row {
        height: 2;
    }

    .metric-value {
        text-style: bold;
    }

    /* Status bar */
    #status-bar {
        height: 1;
        background: $surface;
        padding: 0 1;
        color: $text-muted;
    }
    """

    def __init__(self, api_url: str) -> None:
        super().__init__()
        self.api_url = api_url
        self.metrics: Optional[dict] = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="main-content"):
            # Cash Health Section
            with Vertical(id="cash-health"):
                yield Static("CASH HEALTH", classes="section-title")
                yield Static("Loading...", id="runway-display", classes="cash-row")
                yield Static("", id="collections-display", classes="cash-row")
                yield Static("", id="velocity-display", classes="cash-row")

            # Middle Row: Attention Required + Pipeline Velocity
            with Horizontal(id="middle-row"):
                # Attention Required (Left)
                with Vertical(id="attention-section"):
                    yield Static("ATTENTION REQUIRED", classes="section-title")
                    yield DataTable(id="attention-table", cursor_type="row")

                # Pipeline Velocity (Right)
                with Vertical(id="velocity-section"):
                    yield Static("PIPELINE VELOCITY", classes="section-title")
                    yield Static("", id="velocity-stage-1", classes="velocity-row")
                    yield Static("", id="velocity-stage-2", classes="velocity-row")
                    yield Static("", id="velocity-stage-3", classes="velocity-row")
                    yield Static("", id="velocity-stage-4", classes="velocity-row")
                    yield Static("", id="velocity-cycle", classes="velocity-row")

            # Strategic Priorities
            with Vertical(id="priorities-section"):
                yield Static("STRATEGIC PRIORITIES", classes="section-title")
                with Horizontal(id="priorities-row"):
                    with Vertical(classes="priority-card"):
                        yield Static("", id="priority-1-label", classes="priority-label")
                        yield Static("", id="priority-1-value")
                    with Vertical(classes="priority-card"):
                        yield Static("", id="priority-2-label", classes="priority-label")
                        yield Static("", id="priority-2-value")
                    with Vertical(classes="priority-card"):
                        yield Static("", id="priority-3-label", classes="priority-label")
                        yield Static("", id="priority-3-value")

            # Sales Scorecard
            with Vertical(id="scorecard-section"):
                yield Static("SALES SCORECARD", classes="section-title")
                with Horizontal(classes="scorecard-row"):
                    yield Static("", id="scorecard-pipeline")
                    yield Static("", id="scorecard-won")
                    yield Static("", id="scorecard-status")

            # Status bar
            yield Static("Press [R] to refresh | Last updated: --", id="status-bar")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen."""
        # Set up the attention table
        table = self.query_one("#attention-table", DataTable)
        table.add_columns("Deal", "Reason", "Value", "Owner")

        # Load data
        self._load_data()

    def _load_data(self) -> None:
        """Load dashboard data from API."""
        self.run_worker(self._fetch_data(), exclusive=True)

    async def _fetch_data(self) -> None:
        """Fetch data from CEO Dashboard API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.api_url}/ceo-dashboard/metrics")
                if response.status_code == 200:
                    self.metrics = response.json()
                    self._render_dashboard()
                else:
                    self._show_error(f"API error: {response.status_code}")
        except httpx.TimeoutException:
            self._show_error("Request timed out")
        except Exception as e:
            self._show_error(f"Error: {e}")

    def _show_error(self, message: str) -> None:
        """Display error message."""
        self.query_one("#status-bar", Static).update(f"Error: {message}")

    def _render_dashboard(self) -> None:
        """Render all dashboard sections."""
        if not self.metrics:
            return

        self._render_cash_health()
        self._render_attention()
        self._render_velocity()
        self._render_priorities()
        self._render_scorecard()

        # Update status bar
        last_updated = self.metrics.get("last_updated", "--")
        if last_updated != "--":
            # Format the timestamp
            last_updated = last_updated[:19].replace("T", " ")
        self.query_one("#status-bar", Static).update(
            f"Press [R] to refresh | Last updated: {last_updated}"
        )

    def _render_cash_health(self) -> None:
        """Render cash health section."""
        cash = self.metrics.get("cash_health", {})

        # Runway display
        runway = cash.get("runway_months", 0)
        runway_status = cash.get("runway_status", "red")
        runway_class = f"runway-{runway_status}"

        runway_bar = self._create_progress_bar(runway / 6 * 100, 20)  # 6 months = 100%
        runway_text = f"Runway: {runway:.1f} months {runway_bar}"
        runway_widget = self.query_one("#runway-display", Static)
        runway_widget.update(runway_text)
        runway_widget.set_classes(f"cash-row {runway_class}")

        # Collections display
        collected = cash.get("total_collected_week", 0)
        target = cash.get("total_target_week", 0)
        pct = cash.get("collection_pct", 0)
        predicted = cash.get("predicted_14d", 0)

        collections_text = (
            f"This Week: {self._format_sar(collected)} / {self._format_sar(target)} ({pct:.0f}%) | "
            f"14d Forecast: {self._format_sar(predicted)}"
        )
        self.query_one("#collections-display", Static).update(collections_text)

        # Velocity display
        velocity_pct = cash.get("velocity_pct", 0)
        velocity_status = cash.get("velocity_status", "red")
        velocity_bar = self._create_progress_bar(velocity_pct, 30)
        velocity_class = f"status-{velocity_status}"

        velocity_widget = self.query_one("#velocity-display", Static)
        velocity_widget.update(f"Velocity: {velocity_bar} {velocity_pct:.0f}%")

    def _render_attention(self) -> None:
        """Render attention required section."""
        table = self.query_one("#attention-table", DataTable)
        table.clear()

        urgent_deals = self.metrics.get("urgent_deals", [])

        for deal in urgent_deals[:5]:
            table.add_row(
                deal.get("title", "")[:25],
                deal.get("reason", ""),
                self._format_sar(deal.get("value_sar", 0)),
                deal.get("owner", "")[:10],
            )

    def _render_velocity(self) -> None:
        """Render pipeline velocity section."""
        velocity = self.metrics.get("pipeline_velocity", {})
        stages = velocity.get("stages", [])

        # Render up to 4 stages
        for i, stage in enumerate(stages[:4], 1):
            stage_id = f"velocity-stage-{i}"
            widget = self.query_one(f"#{stage_id}", Static)

            name = stage.get("name", "")[:15]
            avg_days = stage.get("avg_days", 0)
            deal_count = stage.get("deal_count", 0)

            # Create a simple bar chart
            bar_width = min(int(avg_days), 20)
            bar = "█" * bar_width + "░" * (20 - bar_width)

            widget.update(f"{name:15} {bar} {avg_days:.0f}d ({deal_count})")

        # Clear unused stage slots
        for i in range(len(stages) + 1, 5):
            stage_id = f"velocity-stage-{i}"
            self.query_one(f"#{stage_id}", Static).update("")

        # Cycle time and trend
        current = velocity.get("current_cycle_days", 0)
        target = velocity.get("target_cycle_days", 21)
        trend = velocity.get("trend", "stable")

        trend_symbol = {"better": "↓", "worse": "↑", "stable": "→"}.get(trend, "→")
        trend_class = f"trend-{trend}"

        cycle_widget = self.query_one("#velocity-cycle", Static)
        cycle_widget.update(f"Cycle: {current:.0f}d (Target: {target:.0f}d) {trend_symbol} {trend.upper()}")
        cycle_widget.set_classes(f"velocity-row {trend_class}")

    def _render_priorities(self) -> None:
        """Render strategic priorities section."""
        priorities = self.metrics.get("strategic_priorities", [])

        for i, priority in enumerate(priorities[:3], 1):
            name = priority.get("name", "")
            current = priority.get("current", 0)
            target = priority.get("target", 0)
            pct = priority.get("pct", 0)
            unit = priority.get("unit", "")
            status = priority.get("status", "red")

            label_widget = self.query_one(f"#priority-{i}-label", Static)
            value_widget = self.query_one(f"#priority-{i}-value", Static)

            label_widget.update(f"[{name}]")

            bar = self._create_progress_bar(min(pct, 100), 15)
            status_class = f"status-{status}"

            value_widget.update(f"{current:.0f}/{target:.0f}{unit} {bar}")
            value_widget.set_classes(status_class)

    def _render_scorecard(self) -> None:
        """Render sales scorecard section."""
        scorecard = self.metrics.get("department_scorecard", {})
        sales = scorecard.get("sales", {})

        pipeline = sales.get("pipeline_value", 0)
        won = sales.get("won_value", 0)
        active = sales.get("active_deals_count", 0)
        overdue = sales.get("overdue_count", 0)
        status = sales.get("status", "red")

        status_symbol = {"green": "●", "yellow": "●", "red": "●"}.get(status, "●")
        status_class = f"status-{status}"

        self.query_one("#scorecard-pipeline", Static).update(
            f"Pipeline: {self._format_sar(pipeline)} | Active: {active}"
        )
        self.query_one("#scorecard-won", Static).update(
            f"Won (Month): {self._format_sar(won)} | Overdue: {overdue}"
        )

        status_widget = self.query_one("#scorecard-status", Static)
        status_widget.update(f"{status_symbol} {status.upper()}")
        status_widget.set_classes(status_class)

    def _format_sar(self, value: float) -> str:
        """Format SAR value with K/M suffix."""
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M SAR"
        elif value >= 1_000:
            return f"{value / 1_000:.0f}K SAR"
        else:
            return f"{value:.0f} SAR"

    def _create_progress_bar(self, pct: float, width: int = 20) -> str:
        """Create ASCII progress bar."""
        filled = int(pct / 100 * width)
        filled = max(0, min(filled, width))
        empty = width - filled
        return f"[{'=' * filled}{' ' * empty}]"

    # Actions
    def action_refresh(self) -> None:
        """Refresh dashboard data."""
        self._load_data()

    def action_go_aramco(self) -> None:
        """Switch to Aramco screen."""
        self.app.switch_screen("aramco")

    def action_go_commercial(self) -> None:
        """Switch to Commercial screen."""
        self.app.switch_screen("commercial")

    def action_go_owners(self) -> None:
        """Switch to Owner KPI screen."""
        self.app.switch_screen("owner_kpi")

    def action_go_emails(self) -> None:
        """Switch to Email Drafts screen."""
        self.app.switch_screen("email_drafts")

    def action_go_management(self) -> None:
        """Switch to Management screen."""
        self.app.switch_screen("management")

    def action_go_tracker(self) -> None:
        """Switch to Tracker screen."""
        self.app.switch_screen("tracker")

    def action_show_help(self) -> None:
        """Show help modal."""
        # TODO: Implement help modal
        pass
