"""Order Received Summary Modal - CEO Radar for Order Received Deals."""

import httpx
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Button, DataTable


class OrderReceivedSummaryModal(ModalScreen):
    """Modal screen showing CEO radar for Order Received deals."""

    CSS = """
    OrderReceivedSummaryModal {
        align: center middle;
    }

    #order-modal {
        width: 95%;
        height: 90%;
        border: thick $primary;
        background: $surface;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $success;
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

    #blockers-section {
        height: auto;
        margin: 1;
        padding: 1;
        border: solid $secondary;
        background: $panel;
    }

    #fast-wins-table {
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
        with Vertical(id="order-modal"):
            yield Static("CEO RADAR: Order Received", id="modal-title")
            yield Static("Loading...", classes="status-line", id="status-line")

            with VerticalScroll():
                # Executive Snapshot Section
                with Vertical(id="snapshot-section"):
                    yield Static("Executive Snapshot", classes="section-title")
                    yield Static("", id="snapshot-metrics")

                # PM Pipeline Acceleration Table
                yield Static("PM Pipeline Acceleration", classes="section-title")
                yield DataTable(id="pm-table")

                # Blockers Checklist
                with Vertical(id="blockers-section"):
                    yield Static("Blockers Checklist Summary", classes="section-title")
                    yield Static("", id="blockers-metrics")

                # Fast Wins List
                yield Static("Fast Wins This Week (Top 10)", classes="section-title")
                yield DataTable(id="fast-wins-table")

                # Action Buttons Section
                with Vertical(id="action-buttons"):
                    yield Static("One-Click Actions", classes="section-title")
                    yield Button("Create 'Identify End User' Tasks - TODO", id="action-enduser", disabled=True)
                    yield Button("Draft Email/WhatsApp Template - TODO", id="action-template", disabled=True)
                    yield Button("Send Aramco Reminder - TODO", id="action-reminder", disabled=True)

            with Horizontal(id="footer"):
                yield Button("Close", id="close-button")

    async def on_mount(self) -> None:
        """Load data when modal mounts."""
        await self.load_summary()

    async def load_summary(self) -> None:
        """Load and display Order Received summary data."""
        status_line = self.query_one("#status-line", Static)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/aramco/order_received_summary")
                response.raise_for_status()
                data = response.json()

            # Hide status line
            status_line.update("")

            # Populate sections
            self._populate_snapshot(data["snapshot"])
            self._populate_pm_table(data["pm_acceleration"])
            self._populate_blockers(data["blockers_checklist"])
            self._populate_fast_wins(data["fast_wins"])

        except httpx.HTTPStatusError as e:
            status_line.update(f"Error: HTTP {e.response.status_code}")
        except Exception as e:
            status_line.update(f"Error loading summary: {str(e)}")

    def _populate_snapshot(self, snapshot: dict) -> None:
        """Populate executive snapshot metrics."""
        metrics_widget = self.query_one("#snapshot-metrics", Static)

        oldest = snapshot.get("oldest_deal", {})
        oldest_str = f"Deal #{oldest.get('deal_id', 'N/A')}: {oldest.get('title', 'N/A')[:30]} ({oldest.get('age_days', 0)} days)"

        conversion = snapshot.get("conversion_rate_30d")
        conversion_str = f"{conversion:.1f}%" if conversion is not None else "TODO"

        text = f"""
Order Received Open: {snapshot['open_count']} deals | SAR {snapshot['open_sar']:,.0f}

Aging Buckets:
  0-7 days: {snapshot['bucket_0_7_count']} deals | SAR {snapshot['bucket_0_7_sar']:,.0f}
  8-14 days: {snapshot['bucket_8_14_count']} deals | SAR {snapshot['bucket_8_14_sar']:,.0f}
  15-30 days: {snapshot['bucket_15_30_count']} deals | SAR {snapshot['bucket_15_30_sar']:,.0f}
  30+ days: {snapshot['bucket_30_plus_count']} deals | SAR {snapshot['bucket_30_plus_sar']:,.0f}

Oldest Deal: {oldest_str}
Conversion Rate (30d): {conversion_str}"""

        metrics_widget.update(text)

    def _populate_pm_table(self, pm_acceleration: list) -> None:
        """Populate PM pipeline acceleration table."""
        table = self.query_one("#pm-table", DataTable)

        table.add_columns(
            "PM Name",
            "Open",
            "SAR",
            "Avg Age",
            "End User %",
            "Activity %",
            "Approved 30d",
            "SAR"
        )

        for pm in pm_acceleration:
            approved_count = pm.get("approved_30d_count")
            approved_count_str = str(approved_count) if approved_count is not None else "TODO"

            approved_sar = pm.get("approved_30d_sar")
            approved_sar_str = f"{approved_sar:,.0f}" if approved_sar is not None else "TODO"

            table.add_row(
                pm["pm_name"],
                str(pm["open_count"]),
                f"{pm['open_sar']:,.0f}",
                f"{pm['avg_age_days']:.1f}d",
                f"{pm['pct_end_user_identified']:.0f}%",
                f"{pm['pct_next_activity_scheduled']:.0f}%",
                approved_count_str,
                approved_sar_str
            )

    def _populate_blockers(self, blockers: dict) -> None:
        """Populate blockers checklist."""
        metrics_widget = self.query_one("#blockers-metrics", Static)

        site = blockers.get("missing_site_contact_count")
        site_str = str(site) if site is not None else "TODO"

        po = blockers.get("missing_po_count")
        po_str = str(po) if po is not None else "TODO"

        dates = blockers.get("missing_dates_count")
        dates_str = str(dates) if dates is not None else "TODO"

        product = blockers.get("missing_product_type_count")
        product_str = str(product) if product is not None else "TODO"

        quantity = blockers.get("missing_quantity_count")
        quantity_str = str(quantity) if quantity is not None else "TODO"

        text = f"""
Missing End User: {blockers['missing_end_user_count']} deals
Missing Site Contact: {site_str} deals
Missing PO/Contract: {po_str} deals
Missing Expected Dates: {dates_str} deals
Missing Product Type: {product_str} deals
Missing Quantity: {quantity_str} deals
Missing Next Activity: {blockers['missing_next_activity_count']} deals"""

        metrics_widget.update(text)

    def _populate_fast_wins(self, fast_wins: list) -> None:
        """Populate fast wins table."""
        table = self.query_one("#fast-wins-table", DataTable)

        table.add_columns(
            "Deal ID",
            "Title",
            "PM",
            "Value SAR",
            "Age",
            "Missing Items",
            "Suggested Action"
        )

        for deal in fast_wins:
            missing_str = ", ".join(deal["missing_items"])
            if len(missing_str) > 25:
                missing_str = missing_str[:22] + "..."

            action_str = deal["suggested_action"][:30]

            table.add_row(
                str(deal["deal_id"]),
                deal["title"][:20],
                deal["pm_name"],
                f"{deal['value_sar']:,.0f}",
                f"{deal['age_days']}d",
                missing_str,
                action_str
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-button":
            self.dismiss()
        elif event.button.id in ["action-enduser", "action-template", "action-reminder"]:
            self.notify("This action will be implemented in a future update.", severity="info")

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
