# Services_and_Integrations.md
Command Center Services & Integrations Specification (for LLMs)

> ⚠️ IMPORTANT FOR LLMS  
> - Treat this file as the **source of truth for business logic and external clients**.  
> - When generating code, keep function names, responsibilities, and data flow consistent with this document, **Architecture.md**, **API_endpoints.md**, and **Models_and_Schema.md**.  
> - Services = business logic. Integrations = low-level API clients (Pipedrive, LLM, Email, etc.).

All functions below are Python, intended to live under:

- backend/services/
- backend/integrations/

---

## 0. Conventions

### 0.1 General

- All services should be pure business logic:
  - Fetch data via integration clients.
  - Transform/filter/aggregate.
  - Return Pydantic models defined in Models_and_Schema.md.
- Integrations:
  - Wrap external HTTP APIs or SMTP.
  - Return either DTO models or dicts that can be mapped to domain models.

### 0.2 Async vs Sync

- Use async for IO-bound functions where possible (httpx, FastAPI).
- Service functions that call async integration clients should also be async.

Example pattern:

```python
async def get_aramco_overdue(min_days: int = 7) -> list[OverdueDeal]:
    deals = await pipedrive_client.get_deals_in_pipeline("Aramco Projects")
    # filter & map...
    return overdue_deals
```

---

## 1. Service Layer Overview

Services live in backend/services/:

- deal_health_service.py – deal health, overdue, stuck, order received, commercial views.
- llm_analysis_service.py – all LLM calls & parsing.
- cashflow_service.py – cashflow projection and near-invoicing deals.
- owner_kpi_service.py – per-owner KPIs.
- email_service.py – generation & sending of follow-up emails.
- dashboard_service.py – aggregates other services for the Dashboard.

Each service file is documented below.

---

## 2. deal_health_service.py

### IMPORTANT JSON Format
pipedrive will return this json format when it tried to get deals, so it will need to be normalize

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "creator_user_id": {
                "id": 9392342,
                "name": "Sufyan Almalathi",
                "email": "sufyan@gyptech.com.sa",
                "has_pic": 0,
                "pic_hash": null,
                "active_flag": false,
                "value": 9392342
            },
            "user_id": {
                "id": 9392342,
                "name": "Sufyan Almalathi",
                "email": "sufyan@gyptech.com.sa",
                "has_pic": 0,
                "pic_hash": null,
                "active_flag": false,
                "value": 9392342
            },
            "person_id": {
                "active_flag": true,
                "name": "Suhaibu",
                "email": [
                    {
                        "value": "",
                        "primary": true
                    }
                ],
                "phone": [
                    {
                        "value": "",
                        "primary": true
                    }
                ],
                "owner_id": 13285249,
                "company_id": 6191422,
                "value": 1
            },
            "org_id": {
                "name": "KITCHENO",
                "people_count": 4,
                "owner_id": 9392342,
                "address": null,
                "label_ids": [],
                "active_flag": true,
                "cc_email": "gyptech-568b5d@pipedrivemail.com",
                "owner_name": "Sufyan Almalathi",
                "value": 1
            },
            "stage_id": 5,
            "title": "GYP-SM190045 - third industry 18 toilet cubicles for Admins",
            "value": 25200,
            "acv": null,
            "mrr": null,
            "arr": null,
            "currency": "SAR",
            "add_time": "2019-06-11 10:56:47",
            "update_time": "2020-02-16 07:28:16",
            "stage_change_time": "2019-11-12 07:10:24",
            "active": false,
            "deleted": false,
            "status": "won",
            "probability": null,
            "next_activity_date": null,
            "next_activity_time": null,
            "next_activity_id": null,
            "last_activity_id": 2,
            "last_activity_date": "2019-06-11",
            "lost_reason": null,
            "visible_to": "3",
            "close_time": "2019-06-13 10:29:08",
            "pipeline_id": 1,
            "won_time": "2019-06-13 10:29:08",
            "first_won_time": "2019-06-11 10:59:25",
            "lost_time": null,
            "products_count": 0,
            "files_count": 0,
            "notes_count": 5,
            "followers_count": 1,
            "email_messages_count": 0,
            "activities_count": 2,
            "done_activities_count": 2,
            "undone_activities_count": 0,
            "participants_count": 2,
            "expected_close_date": "2019-06-15",
            "last_incoming_mail_time": null,
            "last_outgoing_mail_time": null,
            "label": null,
            "local_won_date": null,
            "local_lost_date": null,
            "local_close_date": null,
            "origin": "ManuallyCreated",
            "origin_id": null,
            "channel": null,
            "channel_id": null,
            "score": null,
            "is_archived": false,
            "archive_time": null,
            "sequence_enrollment": null,
            "source_lead_id": null,
            "stage_order_nr": 5,
            "person_name": "Suhaibu",
            "org_name": "KITCHENO",
            "next_activity_subject": null,
            "next_activity_type": null,
            "next_activity_duration": null,
            "next_activity_note": null,
            "formatted_value": "SAR 25,200",
            "weighted_value": 25200,
            "formatted_weighted_value": "SAR 25,200",
            "weighted_value_currency": "SAR",
            "rotten_time": null,
            "acv_currency": null,
            "mrr_currency": null,
            "arr_currency": null,
            "owner_name": "Sufyan Almalathi",
            "cc_email": "gyptech-568b5d+deal1@pipedrivemail.com",
            "4f2f060aaa56536fb78c5d1038ab56a24b8ebc63": null,
            "5ffea68859bd7089ce52f603ee5f88c14b3ff260": null,
            "aaff5efec614d2cd18aecdfa5f800af9167cac1d": null,
            "bd7bb3b2758ca81feebf015ca60bf528eafe47f0": null,
            "3625266375cf115cf1a0edb6924d5c2c2243d540": null,
            "56db4d96acbfa1e19d9d97c3821c3674d3fcaf94": null,
            "f71407beeb55195def1dce9326667e7c54f2cb42": null,
            "c0323a114651cc691e866bdb1d840971d60626ba": null,
            "d1e4bd92930d9b18d8bf44542310ab1bea9ad475": null,
            "b09660187f2c3c9df39c11439fb69ca9f582e383": null,
            "fdee83bde897e7e1477bb47e6d15bedb4272eb40": null,
            "04196647566da4208c39be12ecc6044ac3b1cef3": null,
            "org_hidden": false,
            "person_hidden": false
        }
}
```

### Pipedrive stage IDs, and pipeline IDs 
pipeline IDs from pipedrive:
{
    "Pipeline": 1,
    "Prospecting": 2,
    "Aramco Inquiries": 3,
    "Aramco PO": 4,
    "Aramco Projects": 5,
    "Bidding Projects": 6,
    "Design Development": 10,
    "Problematic & Stuck Orders": 11,
}
stages IDs:
{
    "Lead In": 1,
    "Enquiry": 2,
    "Quotation": 3,
    "Submittal": 4,
    "Production /Supplying": 5,
    "Target/Research": 9,
    "Second Meeting(Interested)": 10,
    "Second Follow up 2": 11,
    "Not Ready to buy": 12,
    "RFQ Recieved": 14,
    "RFQ Sent": 15,
    "Price Recieved": 16,
    "Extension": 17,
    "Proposal Submitted": 18,
    "Aramco Issued PO": 19,
    "PO Sent to Supplier": 20,
    "Awaiting Payment": 21,
    "in transit": 22,
    "Arrived ": 23,
    "ASN": 24,
    "Pending GR": 25,
    "Order Received": 27,
    "Approved": 28,
    "Awaiting Payment": 29,
    "Underprogress": 30,
    "In customs": 33,
    "Awaiting Shipping (PAID)": 34,
    "Bidding": 35,
    "ON HOLD": 36,
    "Contract Awarded": 37,
    "Initial Contact Made": 38,
    "Follow up 1": 39,
    "First Meeting ": 40,
    "Awaiting GCC": 42,
    "Awaiting GR": 43,
    "Awaiting Site Readiness": 44,
    "Everything Read but not started": 45,
    "Awaiting approval": 46,
    "Approved by Manager": 47,
    "HOLD": 48,
    "Stuck/To be Canceled": 49,
    "Lead In": 50,  # note: duplicate name, see comment below
    "Pre-design - Data collection": 78,
    "Revision and finalization": 79,
    "Cost Estimation & 2D Layout": 80,
    "Completed": 81,
    "Awaiting MDD": 82,
    "Underprogress": 83,
    "Awaiting Resolution": 84,
    "Gathering Documents": 85,
    "Almost Dead": 86,
}
Purpose: Provide deal-centric health views for Aramco and Commercial pipelines.

### 2.1 Dependencies

- backend.integrations.pipedrive_client
- backend.services.llm_analysis_service
- Models from:
  - deal_models.py (DealBase, OverdueDeal, StuckDeal, OrderReceivedAnalysis, DealSummary, ComplianceStatus, DealNote)

### 2.2 Functions

#### 2.2.1 get_aramco_overdue

```python
async def get_aramco_overdue(min_days: int = 7) -> list[OverdueDeal]:
    """
    1. Fetch all open deals in pipeline 'Aramco Projects'.
    2. Determine which are overdue by at least `min_days`.
    3. Return them as OverdueDeal models.
    """
```

Used by /aramco/overdue.

---

#### 2.2.2 get_aramco_stuck

```python
async def get_aramco_stuck(min_days: int = 30) -> list[StuckDeal]:
    """
    1. Fetch open deals in 'Aramco Projects'.
    2. Compute how many days they've been in their current stage.
    3. Filter deals with days_in_stage >= min_days.
    4. Return them as StuckDeal models.
    """
```

Used by /aramco/stuck.

---

#### 2.2.3 get_aramco_order_received_analysis

```python
async def get_aramco_order_received_analysis(
    min_days: int = 30,
) -> list[OrderReceivedAnalysis]:
    """
    1. Fetch deals in pipeline 'Aramco Projects' in stage 'Order received'.
    2. Compute days_in_stage and filter by min_days.
    3. For each deal:
       - Fetch notes via pipedrive_client.
       - Call llm_analysis_service.analyze_order_received(notes).
    4. Build and return list[OrderReceivedAnalysis].
    """
```

Used by /aramco/order_received.

---

#### 2.2.4 get_aramco_compliance_status

```python
async def get_aramco_compliance_status() -> list[ComplianceStatus]:
    """
    1. Fetch relevant deals in 'Aramco Projects' (e.g., post-purchase, post-MDD).
    2. For each deal:
       - Fetch notes via pipedrive_client.
       - Call llm_analysis_service.check_compliance(notes, stage).
    3. Return list[ComplianceStatus].
    """
```

Used by /aramco/compliance.

---

#### 2.2.5 get_commercial_inactive

```python
async def get_commercial_inactive(min_days: int = 60) -> list[StuckDeal]:
    """
    1. Fetch deals in 'pipeline' (commercial).
    2. Compute days_in_stage and last_activity_time.
    3. Filter deals that have had no movement for >= min_days.
    4. Return as StuckDeal models.
    """
```

Used by /commercial/inactive.

---

#### 2.2.6 get_recent_commercial_summaries

```python
async def get_recent_commercial_summaries(
    days: int = 60,
) -> list[DealSummary]:
    """
    1. Fetch deals in commercial pipeline with activity in the last `days`.
    2. For each deal:
       - Fetch notes via pipedrive_client.
       - Call llm_analysis_service.summarize_recent_activity(notes).
    3. Build DealSummary objects and return.
    """
```

Used by /commercial/recent_summary.

---

#### 2.2.7 get_deal_detail

```python
async def get_deal_detail(deal_id: int) -> dict:
    """
    1. Fetch deal by ID via pipedrive_client.
    2. Fetch all notes for that deal.
    3. Use llm_analysis_service to compute:
       - llm_summary
       - sdd_requested (bool | None)
       - end_user_identified (bool | None)
       - compliance status (ComplianceStatus | None)
    4. Return a dict shaped like /deals/{id}/detail response.
    """
```

Used by /deals/{deal_id}/detail.

---

## 3. llm_analysis_service.py

Purpose: Centralize all LLM interactions and enforce consistent prompts + JSON schemas.

### 3.1 Dependencies

- backend.integrations.llm_client
- Models from Models_and_Schema.md.

### 3.2 Functions

#### 3.2.1 detect_sdd_requested

```python
async def detect_sdd_requested(notes: list[DealNote]) -> bool:
    """
    Use LLM to determine if an SDD has been requested in the deal's notes.
    """
```

---

#### 3.2.2 analyze_order_received

```python
async def analyze_order_received(
    notes: list[DealNote],
) -> tuple[Optional[bool], Optional[int]]:
    """
    Returns:
      - end_user_identified: bool | None
      - end_user_requests_count: int | None
    """
```

---

#### 3.2.3 check_compliance

```python
async def check_compliance(
    notes: list[DealNote],
    stage: str,
) -> ComplianceStatus:
    """
    LLM checks for:
      - Survey checklist (if after materials purchased)
      - Quality inspection docs (if after MDD signed)
    """
```

---

#### 3.2.4 summarize_recent_activity

```python
async def summarize_recent_activity(
    notes: list[DealNote],
) -> tuple[str, Optional[str]]:
    """
    Summarize the latest updates and recommend next action.
    Returns:
      - summary: str
      - next_action: Optional[str]
    """
```

---

#### 3.2.5 build_email_body_for_owner

```python
async def build_email_body_for_owner(
    owner: str,
    issues: list[DealIssue],
) -> str:
    """
    Use LLM to write a concise, professional email body addressed to `owner`,
    listing each deal issue and suggested next steps.
    """
```

---

## 4. cashflow_service.py

Purpose: Provide cashflow-oriented views based on Pipedrive deal stages.

### 4.1 Dependencies

- backend.integrations.pipedrive_client
- cashflow_models.py, deal_models.py.

### 4.2 Functions

#### 4.2.1 get_aramco_cashflow_projection

```python
async def get_aramco_cashflow_projection(
    bucket: str = "week",
) -> list[CashflowBucket]:
    """
    1. Fetch open deals from 'Aramco Projects'.
    2. Map stages to approximate invoicing timelines.
    3. Group projected invoice values into weekly or monthly buckets.
    4. Return list[CashflowBucket].
    """
```

---

#### 4.2.2 identify_near_invoicing_deals

```python
async def identify_near_invoicing_deals() -> list[DealBase]:
    """
    Identify deals in stages close to invoicing (e.g. 'under progress', 'awaiting GR').
    """
```

---

## 5. owner_kpi_service.py

Purpose: Aggregate KPIs by salesperson.

### 5.1 Dependencies

- backend.integrations.pipedrive_client
- kpi_models.py, deal_models.py.

### 5.2 Functions

#### 5.2.1 get_owner_kpis

```python
async def get_owner_kpis(
    period: str = "this_month",
    pipelines: list[str] | None = None,
) -> list[OwnerKPI]:
    """
    1. Determine date range based on `period`.
    2. Fetch deals and activities for the given pipelines.
    3. Aggregate metrics per owner.
    4. Return list[OwnerKPI].
    """
```

---

## 6. email_service.py

Purpose: Create and send follow-up emails per salesperson.

### 6.1 Dependencies

- backend.integrations.email_client
- backend.services.llm_analysis_service
- backend.services.deal_health_service
- email_models.py, deal_models.py.

### 6.2 Functions

#### 6.2.1 generate_followup_drafts

```python
class FollowupConditions(BaseModel):
    include_overdue: bool = True
    include_stuck: bool = True
    include_missing_compliance: bool = True
    min_overdue_days: int = 7
    min_stuck_days: int = 30

async def generate_followup_drafts(
    conditions: FollowupConditions,
    pipelines: list[str],
) -> list[EmailDraft]:
    """
    1. Use deal_health_service to fetch:
       - Overdue deals
       - Stuck deals
       - Compliance issues
    2. Convert each relevant deal into a DealIssue with issue_summary and next_action.
    3. Group DealIssue items by owner.
    4. For each owner:
       - Determine email address via Pipedrive or config.
       - Use llm_analysis_service.build_email_body_for_owner(owner, issues).
       - Build EmailDraft object.
    5. Return list[EmailDraft].
    """
```

---

#### 6.2.2 send_email_draft

```python
async def send_email_draft(draft: EmailDraft) -> None:
    """
    Sends a single EmailDraft using email_client.
    """
```

---

#### 6.2.3 send_multiple_email_drafts

```python
async def send_multiple_email_drafts(drafts: list[EmailDraft]) -> dict:
    """
    Sends multiple drafts.
    Returns a dict summarizing results (e.g., sent_to list).
    """
```

---

## 7. dashboard_service.py

Purpose: Provide a unified “Today’s Focus” view combining multiple signals.

### 7.1 Dependencies

- deal_health_service
- cashflow_service
- dashboard_models.py, deal_models.py.

### 7.2 Functions

#### 7.2.1 get_today_focus

```python
async def get_today_focus(
    period: str = "7d",
) -> list[DashboardItem]:
    """
    1. Fetch:
       - Overdue Aramco deals
       - Stuck Aramco deals
       - Compliance issues
       - Near-invoicing deals (cashflow_service)
    2. Map each to DashboardItem:
       - type: "overdue" | "stuck" | "compliance" | "cashflow"
       - pipeline: "Aramco" or "Commercial"
       - priority: based on type/severity
       - flag: short label
       - deal: DealBase or None
    3. Sort by priority and return.
    """
```

---

## 8. Integration Layer

Integrations live in backend/integrations/:

- pipedrive_client.py
- llm_client.py
- email_client.py
- config.py
- (future) sharepoint_client.py, whatsapp_client.py, supabase_client.py

### 8.1 pipedrive_client.py

Purpose: Encapsulate calls to Pipedrive API.

#### 8.1.1 Functions

```python
async def get_deals_in_pipeline(pipeline_name: str) -> list[PipedriveDealDTO]:
    """Fetch all deals for the given pipeline_name (handles pagination)."""
```

```python
async def get_deal_by_id(deal_id: int) -> PipedriveDealDTO:
    """Fetch a single deal by ID."""
```

```python
async def get_deal_notes(deal_id: int) -> list[PipedriveNoteDTO]:
    """Fetch all notes for a deal."""
```

```python
async def get_deal_activities(deal_id: int) -> list[PipedriveActivityDTO]:
    """Optional: Fetch activities for KPI calculations."""
```

```python
async def get_owner_email(owner_name: str) -> str | None:
    """Return email address for given owner/salesperson."""
```

---

### 8.2 llm_client.py

Purpose: Provide a thin, safe wrapper around the LLM provider (OpenRouter).

#### 8.2.1 Functions

```python
async def complete_json(prompt: str, schema: type[BaseModel]) -> BaseModel:
    """
    1. Send prompt to LLM with instructions to return valid JSON.
    2. Parse and validate against schema.
    3. Retry or raise on failure.
    """
```

```python
async def complete_text(prompt: str) -> str:
    """
    Simple text completion for use cases like email body.
    """
```

---

### 8.3 email_client.py

Purpose: Encapsulate email sending.

#### 8.3.1 Functions

```python
async def send_email(to: str, subject: str, body: str) -> None:
    """
    Sends an email via SMTP or an email provider API.
    """
```

---

### 8.4 config.py

Purpose: Centralized configuration using Pydantic settings.

#### 8.4.1 Settings

```python
class Settings(BaseSettings):
    pipedrive_api_token: str
    pipedrive_base_url: str = "https://api.pipedrive.com/v1"

    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True

    environment: str = "dev"  # "dev" | "prod"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### 8.5 Future Integrations (placeholders)

- sharepoint_client.py
- whatsapp_client.py
- supabase_client.py

Follow the same pattern:
- Thin wrappers around external APIs.
- Config from Settings.
- DTOs separate from domain models.

---

## 9. Mapping Services to API Endpoints

Quick reference:

- /aramco/overdue → deal_health_service.get_aramco_overdue
- /aramco/stuck → deal_health_service.get_aramco_stuck
- /aramco/order_received → deal_health_service.get_aramco_order_received_analysis
- /aramco/compliance → deal_health_service.get_aramco_compliance_status
- /aramco/cashflow_projection → cashflow_service.get_aramco_cashflow_projection
- /commercial/inactive → deal_health_service.get_commercial_inactive
- /commercial/recent_summary → deal_health_service.get_recent_commercial_summaries
- /owners/kpis → owner_kpi_service.get_owner_kpis
- /dashboard/today → dashboard_service.get_today_focus
- /deals/{id}/detail → deal_health_service.get_deal_detail
- /emails/followups/generate → email_service.generate_followup_drafts
- /emails/followups/send → email_service.send_multiple_email_drafts

---

End of Services_and_Integrations.md
