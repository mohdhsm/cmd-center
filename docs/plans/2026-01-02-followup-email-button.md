# Follow-up Email Button Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable the "Generate follow-up email" button in AramcoPipelineScreen to generate mode-specific emails, display them in an editable modal, send via MSGraph API, and log to intervention table.

**Architecture:** The button reads `selected_deal_id` and `current_mode` from the screen state, fetches deal details via API, generates a pre-filled email template based on mode, displays in an editable modal with TextArea inputs, sends via existing MSGraphEmailService, and logs via intervention_service.log_action().

**Tech Stack:** Textual (ModalScreen, TextArea, Button), FastAPI endpoints, MSGraphEmailService, InterventionService

---

## Task 1: Create Follow-up Email API Endpoint

**Files:**
- Modify: `cmd_center/backend/api/emails.py`
- Modify: `cmd_center/backend/models/email_models.py`

**Step 1: Add request/response models to email_models.py**

```python
# Add to cmd_center/backend/models/email_models.py

class FollowupEmailRequest(BaseModel):
    """Request to generate a follow-up email for a deal."""
    deal_id: int
    mode: str  # "overdue", "stuck", "order"
    recipient_email: str = "mohd@gyptech.com.sa"  # Default for testing


class FollowupEmailResponse(BaseModel):
    """Pre-filled email template response."""
    deal_id: int
    deal_title: str
    owner_name: str
    subject: str
    body: str
    recipient_email: str
```

**Step 2: Run test to verify models compile**

Run: `source venv/bin/activate && python -c "from cmd_center.backend.models.email_models import FollowupEmailRequest, FollowupEmailResponse; print('OK')"`
Expected: OK

**Step 3: Add generate_followup_for_deal endpoint to emails.py**

```python
# Add imports at top
from ..models.email_models import FollowupEmailRequest, FollowupEmailResponse
from ..services.db_queries import get_deal_by_id
from datetime import date

@router.post("/followup/generate", response_model=FollowupEmailResponse)
async def generate_followup_email(request: FollowupEmailRequest):
    """Generate a follow-up email template for a specific deal based on mode."""
    # Fetch deal from database
    deal = get_deal_by_id(request.deal_id)
    if not deal:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Deal {request.deal_id} not found")

    deal_title = deal.title
    owner_name = deal.owner_name or "Team Member"

    # Determine deadline from raw_json if available
    deadline_str = "N/A"
    is_overdue = False
    if deal.raw_json:
        import json
        raw = json.loads(deal.raw_json)
        deadline_str = raw.get("expected_close_date") or raw.get("close_time") or "N/A"
        if deadline_str and deadline_str != "N/A":
            try:
                from datetime import datetime
                deadline_date = datetime.fromisoformat(deadline_str.replace("Z", "+00:00")).date()
                is_overdue = deadline_date < date.today()
            except:
                pass

    last_update_str = str(deal.update_time)[:10] if deal.update_time else "Unknown"

    # Generate subject and body based on mode
    if request.mode == "overdue":
        if is_overdue:
            subject = f"CRITICAL {deal_title} is overdue, reach end user to change SDD"
            body = f"""Dear {owner_name},

The deadline for this deal is {deadline_str}, currently is overdue please contact the end user to change its SDD (Statistical Delivery Date) ASAP.

Once the date is updated, please update it in Pipedrive.
"""
        else:
            subject = f"{deal_title} is near overdue, contact end user to change SDD"
            body = f"""Dear {owner_name},

The deadline for this deal is near overdue, please contact the end user to extend the SDD (Statistical Delivery Date).

Once the date is updated, please update it in Pipedrive.
"""
    elif request.mode == "stuck":
        subject = f"Deal hasn't been updated in a while, please update it"
        body = f"""Dear {owner_name},

The following deal is stuck and hasn't been updated since {last_update_str}, please do the necessary and get more information and update it with the latest.

Log your activities and notes in Pipedrive.

Thanks,
"""
    elif request.mode == "order":
        subject = f"Activate {deal_title} ASAP"
        body = f"""Dear {owner_name},

It's important for us to complete the projects and push the projects from start to finish.

It's your responsibility to contact the end user. The deal {deal_title} has been stuck for a while, contact the end user, get information from them, move the deal through.

Log your activities and emails in Pipedrive.
"""
    else:
        subject = f"Follow-up needed: {deal_title}"
        body = f"""Dear {owner_name},

Please review and update the deal {deal_title} in Pipedrive.

Thanks,
"""

    return FollowupEmailResponse(
        deal_id=request.deal_id,
        deal_title=deal_title,
        owner_name=owner_name,
        subject=subject,
        body=body,
        recipient_email=request.recipient_email,
    )
```

**Step 4: Run server to verify endpoint registers**

Run: `source venv/bin/activate && timeout 5 python -c "from cmd_center.backend.api.emails import router; print([r.path for r in router.routes])" || true`
Expected: List containing '/followup/generate'

**Step 5: Commit**

```bash
git add cmd_center/backend/api/emails.py cmd_center/backend/models/email_models.py
git commit -m "feat(api): add followup email generation endpoint

- Add FollowupEmailRequest/Response models
- Add POST /emails/followup/generate endpoint
- Generate mode-specific email templates (overdue, stuck, order)"
```

---

## Task 2: Add Send Follow-up Email Endpoint with Intervention Logging

**Files:**
- Modify: `cmd_center/backend/api/emails.py`
- Modify: `cmd_center/backend/models/email_models.py`

**Step 1: Add send request model to email_models.py**

```python
# Add to cmd_center/backend/models/email_models.py

class SendFollowupRequest(BaseModel):
    """Request to send a follow-up email."""
    deal_id: int
    recipient_email: str
    subject: str
    body: str
```

**Step 2: Add send_followup endpoint to emails.py**

```python
# Add imports at top if not present
from ..services.msgraph_email_service import get_msgraph_email_service
from ..services.intervention_service import log_action

@router.post("/followup/send")
async def send_followup_email(request: SendFollowupRequest):
    """Send a follow-up email and log the intervention."""
    from fastapi import HTTPException

    # Get the email service
    email_service = get_msgraph_email_service()

    # Send the email
    try:
        success = await email_service.send_email(
            from_mailbox="mohammed@gyptech.com.sa",
            to=[request.recipient_email],
            subject=request.subject,
            body=request.body,
            body_type="text",
            save_to_sent=True,
        )
    except Exception as e:
        # Log failed attempt
        log_action(
            actor="system",
            object_type="deal",
            object_id=request.deal_id,
            action_type="email_sent",
            summary=f"Failed to send follow-up email: {str(e)}",
            status="failed",
            details={
                "recipient": request.recipient_email,
                "subject": request.subject,
                "error": str(e),
            }
        )
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    if not success:
        log_action(
            actor="system",
            object_type="deal",
            object_id=request.deal_id,
            action_type="email_sent",
            summary=f"Failed to send follow-up email to {request.recipient_email}",
            status="failed",
            details={
                "recipient": request.recipient_email,
                "subject": request.subject,
            }
        )
        raise HTTPException(status_code=500, detail="Email sending failed")

    # Log successful intervention
    log_action(
        actor="system",
        object_type="deal",
        object_id=request.deal_id,
        action_type="email_sent",
        summary=f"Sent follow-up email to {request.recipient_email}: {request.subject}",
        status="done",
        details={
            "recipient": request.recipient_email,
            "subject": request.subject,
            "body_preview": request.body[:200] if request.body else "",
        }
    )

    return {"status": "sent", "deal_id": request.deal_id}
```

**Step 3: Verify models compile**

Run: `source venv/bin/activate && python -c "from cmd_center.backend.models.email_models import SendFollowupRequest; print('OK')"`
Expected: OK

**Step 4: Commit**

```bash
git add cmd_center/backend/api/emails.py cmd_center/backend/models/email_models.py
git commit -m "feat(api): add send followup email endpoint with intervention logging

- Add SendFollowupRequest model
- Add POST /emails/followup/send endpoint
- Log successful/failed sends to intervention table"
```

---

## Task 3: Add db_queries.get_deal_by_id Function

**Files:**
- Modify: `cmd_center/backend/services/db_queries.py`

**Step 1: Check if get_deal_by_id exists**

Run: `source venv/bin/activate && grep -n "def get_deal_by_id" cmd_center/backend/services/db_queries.py || echo "NOT FOUND"`

**Step 2: Add get_deal_by_id if not present**

```python
# Add to cmd_center/backend/services/db_queries.py

def get_deal_by_id(deal_id: int) -> Optional[Deal]:
    """Get a single deal by ID.

    Args:
        deal_id: The deal ID to fetch

    Returns:
        Deal object or None if not found
    """
    with Session(_get_engine()) as session:
        return session.get(Deal, deal_id)
```

**Step 3: Verify function works**

Run: `source venv/bin/activate && python -c "from cmd_center.backend.services.db_queries import get_deal_by_id; print('OK')"`
Expected: OK

**Step 4: Commit**

```bash
git add cmd_center/backend/services/db_queries.py
git commit -m "feat(db): add get_deal_by_id query function"
```

---

## Task 4: Create Follow-up Email Modal Screen

**Files:**
- Create: `cmd_center/screens/followup_email_modal.py`

**Step 1: Create the modal screen file**

```python
"""Modal screen for editing and sending follow-up emails."""

import httpx
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input, TextArea
from textual import log


class FollowupEmailModal(ModalScreen):
    """Modal for editing and sending a follow-up email."""

    CSS = """
    FollowupEmailModal {
        align: center middle;
    }

    #email-modal {
        width: 90;
        height: 35;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #status-line {
        height: 1;
        margin-bottom: 1;
        text-align: center;
        color: $warning;
    }

    .field-label {
        margin-top: 1;
        margin-bottom: 0;
    }

    #subject-input {
        height: 3;
        margin-bottom: 1;
    }

    #body-input {
        height: 15;
        margin-bottom: 1;
    }

    #button-row {
        height: 3;
        align: center middle;
    }

    #send-button {
        margin-right: 2;
    }

    #cancel-button {
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        api_url: str,
        deal_id: int,
        subject: str,
        body: str,
        recipient_email: str,
    ):
        super().__init__()
        self.api_url = api_url
        self.deal_id = deal_id
        self.initial_subject = subject
        self.initial_body = body
        self.recipient_email = recipient_email

    def compose(self) -> ComposeResult:
        """Create the modal layout."""
        with Vertical(id="email-modal"):
            yield Static(f"Follow-up Email for Deal #{self.deal_id}", id="modal-title")
            yield Static("", id="status-line")

            yield Static(f"To: {self.recipient_email}", classes="field-label")

            yield Static("Subject:", classes="field-label")
            yield Input(value=self.initial_subject, id="subject-input")

            yield Static("Message:", classes="field-label")
            yield TextArea(self.initial_body, id="body-input")

            with Horizontal(id="button-row"):
                yield Button("Send", id="send-button", variant="primary")
                yield Button("Cancel", id="cancel-button", variant="default")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-button":
            self.dismiss(False)
        elif event.button.id == "send-button":
            await self._send_email()

    async def _send_email(self) -> None:
        """Send the email via API."""
        status_line = self.query_one("#status-line", Static)
        subject_input = self.query_one("#subject-input", Input)
        body_input = self.query_one("#body-input", TextArea)

        subject = subject_input.value
        body = body_input.text

        if not subject.strip():
            status_line.update("Error: Subject cannot be empty")
            return

        if not body.strip():
            status_line.update("Error: Message cannot be empty")
            return

        status_line.update("Sending...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/emails/followup/send",
                    json={
                        "deal_id": self.deal_id,
                        "recipient_email": self.recipient_email,
                        "subject": subject,
                        "body": body,
                    }
                )

                if response.status_code == 200:
                    status_line.update("Email sent successfully!")
                    # Wait briefly so user sees success message
                    import asyncio
                    await asyncio.sleep(1)
                    self.dismiss(True)
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    status_line.update(f"Error: {error_detail}")

        except httpx.TimeoutException:
            status_line.update("Error: Request timed out")
        except Exception as e:
            log(f"Error sending email: {e}")
            status_line.update(f"Error: {str(e)[:50]}")

    def action_cancel(self) -> None:
        """Cancel and close modal."""
        self.dismiss(False)
```

**Step 2: Verify syntax is correct**

Run: `source venv/bin/activate && python -c "from cmd_center.screens.followup_email_modal import FollowupEmailModal; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add cmd_center/screens/followup_email_modal.py
git commit -m "feat(ui): add follow-up email modal screen

- Editable subject and body fields
- Send/Cancel buttons
- Status feedback for send operation
- Calls /emails/followup/send API"
```

---

## Task 5: Wire Up the Generate Follow-up Button in AramcoScreen

**Files:**
- Modify: `cmd_center/screens/aramco_screen.py`

**Step 1: Add import for the modal at top of file**

```python
# Add after other imports
from .followup_email_modal import FollowupEmailModal
```

**Step 2: Add handler for generate-followup-button in on_button_pressed method**

Find the `elif event.button.id == "view-summary-button":` section and add a new elif before it:

```python
        elif event.button.id == "generate-followup-button":
            # Get selected deal ID from table cursor
            table = self.query_one("#aramco-table", DataTable)
            cursor_row, cursor_col = table.cursor_coordinate
            cell_key = table.coordinate_to_cell_key((cursor_row, cursor_col))
            row_key_obj = cell_key.row_key if cell_key else None
            row_key_value = row_key_obj.value if row_key_obj is not None else None

            if row_key_value is None:
                self.notify("Select a deal row first (not a group header).", severity="warning")
                return

            try:
                deal_id_int = int(row_key_value)
            except ValueError:
                self.notify("Invalid deal ID.", severity="warning")
                return

            # Generate email via API
            self.notify("Generating email...", severity="info")
            await self._show_followup_modal(deal_id_int)
```

**Step 3: Add the _show_followup_modal method to the class**

```python
    async def _show_followup_modal(self, deal_id: int) -> None:
        """Fetch email template and show the modal."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/emails/followup/generate",
                    json={
                        "deal_id": deal_id,
                        "mode": self.current_mode,
                        "recipient_email": "mohd@gyptech.com.sa",
                    }
                )

                if response.status_code == 404:
                    self.notify("Deal not found.", severity="error")
                    return

                response.raise_for_status()
                data = response.json()

                modal = FollowupEmailModal(
                    api_url=self.api_url,
                    deal_id=deal_id,
                    subject=data["subject"],
                    body=data["body"],
                    recipient_email=data["recipient_email"],
                )

                def on_dismiss(result: bool) -> None:
                    if result:
                        self.notify("Email sent successfully!", severity="information")
                    # else cancelled, no message needed

                self.app.push_screen(modal, on_dismiss)

        except httpx.TimeoutException:
            self.notify("Request timed out.", severity="error")
        except Exception as e:
            log(f"Error generating email: {e}")
            self.notify(f"Error: {str(e)[:40]}", severity="error")
```

**Step 4: Verify imports work**

Run: `source venv/bin/activate && python -c "from cmd_center.screens.aramco_screen import AramcoPipelineScreen; print('OK')"`
Expected: OK

**Step 5: Commit**

```bash
git add cmd_center/screens/aramco_screen.py
git commit -m "feat(ui): wire up generate follow-up email button

- Handle generate-followup-button press
- Fetch email template from API based on current_mode
- Show FollowupEmailModal with pre-filled content
- Notify user of success/failure"
```

---

## Task 6: Add MSGraph Email Service Singleton Getter

**Files:**
- Modify: `cmd_center/backend/services/msgraph_email_service.py`

**Step 1: Check if get_msgraph_email_service exists**

Run: `source venv/bin/activate && grep -n "def get_msgraph_email_service" cmd_center/backend/services/msgraph_email_service.py || echo "NOT FOUND"`

**Step 2: Add singleton getter if not present**

Add at the bottom of the file:

```python
# Singleton pattern
_msgraph_email_service: Optional[MSGraphEmailService] = None


def get_msgraph_email_service() -> MSGraphEmailService:
    """Get or create MSGraph email service singleton."""
    global _msgraph_email_service
    if _msgraph_email_service is None:
        _msgraph_email_service = MSGraphEmailService()
    return _msgraph_email_service
```

**Step 3: Verify import works**

Run: `source venv/bin/activate && python -c "from cmd_center.backend.services.msgraph_email_service import get_msgraph_email_service; print('OK')"`
Expected: OK

**Step 4: Commit**

```bash
git add cmd_center/backend/services/msgraph_email_service.py
git commit -m "feat(services): add get_msgraph_email_service singleton getter"
```

---

## Task 7: Integration Test - Manual Testing Checklist

**Files:**
- None (manual testing)

**Step 1: Start the backend server**

Run: `source venv/bin/activate && cd cmd_center && python -m uvicorn backend.main:app --reload &`

**Step 2: Test the generate endpoint with curl**

Run: `curl -X POST http://127.0.0.1:8000/emails/followup/generate -H "Content-Type: application/json" -d '{"deal_id": 1, "mode": "overdue", "recipient_email": "mohd@gyptech.com.sa"}' | python -m json.tool`

Expected: JSON with subject, body, deal_id, owner_name

**Step 3: Start the TUI app and test interactively**

Run: `source venv/bin/activate && python -m cmd_center.app`

Manual checks:
1. Press 1 to go to Overdue mode
2. Select a deal row with arrow keys
3. Press Tab or s to focus sidebar
4. Click "Generate follo-up email" button
5. Verify modal appears with pre-filled subject and body
6. Edit the message if desired
7. Click Send
8. Verify success notification appears

**Step 4: Verify intervention was logged**

Run: `sqlite3 pipedrive_cache.db "SELECT * FROM intervention WHERE action_type='email_sent' ORDER BY created_at DESC LIMIT 5;"`

Expected: Row(s) showing the sent email with deal_id and details

**Step 5: Commit any fixes found during testing**

```bash
git add -A
git commit -m "fix: address issues found during integration testing"
```

---

## Summary

| Task | Description | Files Modified |
|------|-------------|----------------|
| 1 | Create generate followup endpoint | emails.py, email_models.py |
| 2 | Create send followup endpoint with logging | emails.py, email_models.py |
| 3 | Add get_deal_by_id query | db_queries.py |
| 4 | Create followup email modal | followup_email_modal.py (new) |
| 5 | Wire up button in aramco screen | aramco_screen.py |
| 6 | Add msgraph service singleton | msgraph_email_service.py |
| 7 | Integration testing | Manual testing |

**Dependencies:**
- Tasks 1, 2, 3 can be done in parallel (API layer)
- Task 4 can be done in parallel with API tasks
- Task 5 depends on Tasks 1, 2, 4
- Task 6 may already be complete (verify first)
- Task 7 depends on all previous tasks
