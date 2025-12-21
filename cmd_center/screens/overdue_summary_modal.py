"""Overdue Summary Modal - CEO Radar for Overdue Deals."""

import httpx
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Button, DataTable


class OverdueSummaryModal(ModalScreen):
    """Modal screen showing CEO radar for overdue deals."""

    CSS = """
    OverdueSummaryModal {
        align: center middle;
    }

    #overdue-modal {
        width: 95%;
        height: 90%;
        border: thick $primary;
        background: $surface;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $warning;
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

    .metric-row {
        height: 1;
        margin-bottom: 1;
    }

    #pm-table {
        height: auto;
        margin: 1;
    }

    #intervention-table {
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
    """

    BINDINGS = [
        ("escape", "dismiss", "Close modal"),
    ]

    def __init__(self, api_url: str):
        super().__init__()
        self.api_url = api_url

    def compose(self) -> ComposeResult:
        """Create the modal layout."""
        with Vertical(id="overdue-modal"):
            yield Static("CEO RADAR: Overdue Deals", id="modal-title")
            yield Static("Loading...", classes="status-line", id="status-line")

            with VerticalScroll():
                # Executive Snapshot Section
                with Vertical(id="snapshot-section"):
                    yield Static("Executive Snapshot", classes="section-title")
                    yield Static("", id="snapshot-metrics")

                # PM Performance Table
                yield Static("PM Performance (sorted by Risk Score)", classes="section-title")
                yield DataTable(id="pm-table")

                # CEO Intervention List
                yield Static("CEO Intervention List (Top 10)", classes="section-title")
                yield DataTable(id="intervention-table")

                # Action Buttons Section
                with Vertical(id="action-buttons"):
                    yield Static("One-Click Actions", classes="section-title")
                    yield Button("Create Tasks for Due Soon (7d) - TODO", id="action-tasks", disabled=True)
                    yield Button("Message PMs with Top 3 - TODO", id="action-message", disabled=True)
                    yield Button("Send to Aramco - TODO", id="action-send", disabled=True)

            with Horizontal(id="footer"):
                yield Button("Close", id="close-button")

    async def on_mount(self) -> None:
        """Load data when modal mounts."""
        await self.load_summary()

    async def load_summary(self) -> None:
        """Load and display overdue summary data."""
        status_line = self.query_one("#status-line", Static)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/aramco/overdue_summary")
                response.raise_for_status()
                data = response.json()

            # Hide status line
            status_line.update("")

            # Populate Executive Snapshot
            self._populate_snapshot(data["snapshot"])

            # Populate PM Performance Table
            self._populate_pm_table(data["pm_performance"])

            # Populate Intervention List
            self._populate_intervention_table(data["intervention_list"])

        except httpx.HTTPStatusError as e:
            status_line.update(f"Error: HTTP {e.response.status_code}")
        except Exception as e:
            status_line.update(f"Error loading summary: {str(e)}")

    def _populate_snapshot(self, snapshot: dict) -> None:
        """Populate executive snapshot metrics."""
        metrics_widget = self.query_one("#snapshot-metrics", Static)

        # Format snapshot text
        text = f"""
Overdue Now: {snapshot['overdue_now_count']} deals | SAR {snapshot['overdue_now_sar']:,.0f}
Overdue Soon (next 7-14 days): {snapshot['overdue_soon_count']} deals | SAR {snapshot['overdue_soon_sar']:,.0f}

Worst Overdue (Top 5):"""

        for deal in snapshot['worst_overdue']:
            text += f"\n  - Deal #{deal['deal_id']}: {deal['title'][:40]} ({deal['days']} days, SAR {deal['sar']:,.0f})"

        metrics_widget.update(text)

    def _populate_pm_table(self, pm_performance: list) -> None:
        """Populate PM performance table."""
        table = self.query_one("#pm-table", DataTable)

        # Add columns
        table.add_columns(
            "PM Name",
            "Overdue Now",
            "SAR",
            "Due Soon",
            "SAR",
            "Avg Days",
            "Updated Week",
            "Has Activity",
            "Risk Score"
        )

        # Add rows
        for pm in pm_performance:
            table.add_row(
                pm["pm_name"],
                str(pm["overdue_now_count"]),
                f"{pm['overdue_now_sar']:,.0f}",
                str(pm["due_soon_count"]),
                f"{pm['due_soon_sar']:,.0f}",
                f"{pm['avg_days_overdue']:.1f}",
                str(pm["updated_this_week_count"]),
                str(pm["has_next_activity_count"]),
                f"{pm['risk_score']:.0f}"
            )

    def _populate_intervention_table(self, intervention_list: list) -> None:
        """Populate CEO intervention list table."""
        table = self.query_one("#intervention-table", DataTable)

        # Add columns
        table.add_columns(
            "Deal ID",
            "Title",
            "PM",
            "Stage",
            "Overdue",
            "Days Since Update",
            "Next Activity",
            "Last Note"
        )

        # Add rows
        for deal in intervention_list:
            next_activity = deal.get("next_activity_date", "None")
            if next_activity and next_activity != "None":
                next_activity = next_activity[:10]  # Just the date part

            last_note = deal.get("last_note_snippet", "N/A") or "N/A"
            if len(last_note) > 30:
                last_note = last_note[:27] + "..."

            table.add_row(
                str(deal["deal_id"]),
                deal["title"][:30],
                deal["pm_name"],
                deal["stage"][:20],
                f"{deal.get('overdue_by_days', 0)}d",
                f"{deal['days_since_update']}d",
                next_activity,
                last_note
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-button":
            self.dismiss()
        elif event.button.id in ["action-tasks", "action-message", "action-send"]:
            self.notify("This action will be implemented in a future update.", severity="info")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
