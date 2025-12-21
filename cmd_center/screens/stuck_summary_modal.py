"""Stuck Summary Modal - CEO Radar for Stuck Deals."""

import httpx
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Button, DataTable


class StuckSummaryModal(ModalScreen):
    """Modal screen showing CEO radar for stuck deals."""

    CSS = """
    StuckSummaryModal {
        align: center middle;
    }

    #stuck-modal {
        width: 95%;
        height: 90%;
        border: thick $primary;
        background: $surface;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $error;
    }

    #snapshot-section {
        height: auto;
        margin: 1;
        padding: 1;
        border: solid $secondary;
        background: $panel;
    }

    .section-title {
        text-style: bold;
        margin-bottom: 1;
        color: $accent;
    }

    #pm-table {
        height: auto;
        margin: 1;
    }

    #worst-deals-table {
        height: auto;
        margin: 1;
    }

    #bottleneck-table {
        height: auto;
        margin: 1;
    }

    #action-buttons {
        height: auto;
        margin: 1;
        padding: 1;
        border: solid $secondary;
    }

    #footer {
        height: 3;
        align: center middle;
    }

    .status-line {
        text-align: center;
        margin: 1;
    }

    .highlight {
        text-style: bold;
        color: $warning;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close modal"),
    ]

    def __init__(self, api_url: str):
        super().__init__()
        self.api_url = api_url

    def compose(self) -> ComposeResult:
        """Create the modal layout."""
        with Vertical(id="stuck-modal"):
            yield Static("CEO RADAR: Stuck Deals", id="modal-title")
            yield Static("Loading...", classes="status-line", id="status-line")

            with VerticalScroll():
                # Executive Snapshot Section
                with Vertical(id="snapshot-section"):
                    yield Static("Executive Snapshot", classes="section-title")
                    yield Static("", id="snapshot-metrics")

                # PM Stuck Control Table
                yield Static("PM Stuck Control (sorted by SAR)", classes="section-title")
                yield DataTable(id="pm-table")

                # Worst Stuck Deals
                yield Static("Worst Stuck Deals (Top 10)", classes="section-title")
                yield DataTable(id="worst-deals-table")

                # Stage Bottleneck View
                yield Static("Stage Bottleneck Analysis", classes="section-title")
                yield Static("", id="top-bottleneck")
                yield DataTable(id="bottleneck-table")

                # Action Buttons Section
                with Vertical(id="action-buttons"):
                    yield Static("One-Click Actions", classes="section-title")
                    yield Button("Auto-create 'Update + Activity' Tasks - TODO", id="action-tasks", disabled=True)
                    yield Button("Send Email to Owners - TODO", id="action-email", disabled=True)

            with Horizontal(id="footer"):
                yield Button("Close", id="close-button")

    async def on_mount(self) -> None:
        """Load data when modal mounts."""
        await self.load_summary()

    async def load_summary(self) -> None:
        """Load and display stuck summary data."""
        status_line = self.query_one("#status-line", Static)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/aramco/stuck_summary")
                response.raise_for_status()
                data = response.json()

            # Hide status line
            status_line.update("")

            # Populate sections
            self._populate_snapshot(data["snapshot"])
            self._populate_pm_table(data["pm_control"])
            self._populate_worst_deals_table(data["worst_deals"])
            self._populate_bottleneck_analysis(data["stage_bottlenecks"], data["top_bottleneck_stage"])

        except httpx.HTTPStatusError as e:
            status_line.update(f"Error: HTTP {e.response.status_code}")
        except Exception as e:
            status_line.update(f"Error loading summary: {str(e)}")

    def _populate_snapshot(self, snapshot: dict) -> None:
        """Populate executive snapshot metrics."""
        metrics_widget = self.query_one("#snapshot-metrics", Static)

        text = f"""
Stuck >30d & No Updates: {snapshot['stuck_no_updates_count']} deals | SAR {snapshot['stuck_no_updates_sar']:,.0f}

Severity Buckets:
  30-45 days: {snapshot['bucket_30_45_count']} deals | SAR {snapshot['bucket_30_45_sar']:,.0f}
  46-60 days: {snapshot['bucket_46_60_count']} deals | SAR {snapshot['bucket_46_60_sar']:,.0f}
  60+ days: {snapshot['bucket_60_plus_count']} deals | SAR {snapshot['bucket_60_plus_sar']:,.0f}

No Next Activity: {snapshot['no_activity_count']} deals

Oldest Stuck (Top 5):"""

        for deal in snapshot['oldest_stuck']:
            text += f"\n  - Deal #{deal['deal_id']}: {deal['title'][:40]} ({deal['days_in_stage']} days, SAR {deal['sar']:,.0f})"

        metrics_widget.update(text)

    def _populate_pm_table(self, pm_control: list) -> None:
        """Populate PM stuck control table."""
        table = self.query_one("#pm-table", DataTable)

        table.add_columns(
            "PM Name",
            "Stuck Count",
            "Stuck SAR",
            "No Activity SAR",
            "Avg Days",
            "Median Update",
            "Recovery Rate"
        )

        for pm in pm_control:
            recovery = pm.get("recovery_rate_30d")
            recovery_str = f"{recovery:.1f}%" if recovery is not None else "TODO"

            table.add_row(
                pm["pm_name"],
                str(pm["stuck_count"]),
                f"{pm['stuck_sar']:,.0f}",
                f"{pm['stuck_no_activity_sar']:,.0f}",
                f"{pm['avg_days_in_stage']:.1f}",
                f"{pm['median_days_since_update']:.1f}",
                recovery_str
            )

    def _populate_worst_deals_table(self, worst_deals: list) -> None:
        """Populate worst stuck deals table."""
        table = self.query_one("#worst-deals-table", DataTable)

        table.add_columns(
            "Deal ID",
            "Title",
            "PM",
            "Stage",
            "Days Stuck",
            "Update Age",
            "Blocking",
            "Next Step",
            "Last Note"
        )

        for deal in worst_deals:
            blocking = deal.get("blocking_flag") or "TODO"
            next_step = deal.get("suggested_next_step") or "TODO"
            last_note = deal.get("last_note_snippet", "N/A") or "N/A"
            if len(last_note) > 20:
                last_note = last_note[:17] + "..."

            table.add_row(
                str(deal["deal_id"]),
                deal["title"][:25],
                deal["pm_name"],
                deal["stage"][:15],
                f"{deal['days_in_stage']}d",
                f"{deal['last_update_age']}d",
                blocking[:15],
                next_step[:20],
                last_note
            )

    def _populate_bottleneck_analysis(self, bottlenecks: list, top_stage: str) -> None:
        """Populate stage bottleneck analysis."""
        top_widget = self.query_one("#top-bottleneck", Static)
        top_widget.update(f"Top Bottleneck Stage: {top_stage}", classes="highlight")

        table = self.query_one("#bottleneck-table", DataTable)

        table.add_columns(
            "Stage Name",
            "Stuck Count",
            "Stuck SAR"
        )

        for bottleneck in bottlenecks:
            table.add_row(
                bottleneck["stage_name"],
                str(bottleneck["stuck_count"]),
                f"{bottleneck['stuck_sar']:,.0f}"
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-button":
            self.dismiss()
        elif event.button.id in ["action-tasks", "action-email"]:
            self.notify("This action will be implemented in a future update.", severity="info")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
