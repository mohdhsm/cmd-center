# Models_and_Schema.md
Command Center Models & Schema Specification (for LLMs)

> ⚠️ IMPORTANT FOR LLMS  
> - Treat this file as the **source of truth for data models**.  
> - When generating code, keep these model names and fields stable unless the user explicitly asks to change them.  
> - These models back the contracts in **API_endpoints.md** and the architecture in **Architecture.md**.

All models below are intended as **Pydantic models** (for FastAPI) and may also be used in services and the TUI client code.

---

## 0. Conventions

- Use **Pydantic BaseModel** for all API-facing models.
- Use **snake_case** for field names.
- Use **timezone-aware** datetimes where possible (but you can start with naive if easier and regularize later).
- Monetary values are in **SAR** (float or Decimal), labelled with `_sar`.

Example import:

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional, List
```

When generating code, LLMs should **reuse** these exact names and fields.

---

## 1. Shared Types

These helper types are not strict, but recommended:

```python
from typing import Literal

PipelineName = str  # e.g. "Aramco Projects", "pipeline"
StageName = str
OwnerName = str
OrgName = str
PeriodLabel = str  # e.g. "2026-W01" or "2026-01"
```

---

## 2. Core Deal Models

### 2.1 DealBase

Represents the **common fields** of a Pipedrive deal as used in this app.

```python
class DealBase(BaseModel):
    id: int
    title: str
    pipeline: PipelineName
    stage: StageName
    owner: OwnerName
    org_name: Optional[OrgName] = None
    value_sar: Optional[float] = None

    add_time: Optional[datetime] = None          # created time
    update_time: Optional[datetime] = None       # last updated in Pipedrive
    last_activity_time: Optional[datetime] = None
```

Used in:

- `DashboardItem.deal`
- `/deals/search`
- As a base for all specialized deal views.

---

## 3. Specialized Deal Views

These models **extend** `DealBase` to add fields for different screens/use cases.

### 3.1 OverdueDeal

Used by `/aramco/overdue`.

```python
class OverdueDeal(DealBase):
    overdue_days: int
```

---

### 3.2 StuckDeal

Used for deals that are stuck in the same stage (Aramco & Commercial).

- `/aramco/stuck`
- `/commercial/inactive`

```python
class StuckDeal(DealBase):
    days_in_stage: int
```

---

### 3.3 OrderReceivedAnalysis

Used by `/aramco/order_received` to include LLM analysis.

```python
class OrderReceivedAnalysis(DealBase):
    days_in_stage: int
    end_user_identified: Optional[bool] = None
    end_user_requests_count: Optional[int] = None
```

---

### 3.4 ComplianceStatus

Used by `/aramco/compliance` and also inside `/deals/{id}/detail`.

```python
class ComplianceStatus(DealBase):
    survey_checklist_present: Optional[bool] = None
    quality_docs_present: Optional[bool] = None
    comment: Optional[str] = None
```

---

### 3.5 DealSummary

Used by `/commercial/recent_summary` to show LLM summaries for recent deals.

```python
class DealSummary(DealBase):
    last_activity_date: Optional[datetime] = None
    llm_summary: str
    next_action: Optional[str] = None
```

---

## 4. Notes & Activities

### 4.1 DealNote

Used by `/deals/{id}/detail` and in LLM analysis.

```python
class DealNote(BaseModel):
    id: int
    date: datetime
    author: Optional[str] = None
    content: str
```

If you later need activities, you may define:

```python
class DealActivity(BaseModel):
    id: int
    type: str
    subject: Optional[str] = None
    due_date: Optional[datetime] = None
    done: Optional[bool] = None
```

(Activities are optional for MVP.)

---

## 5. Cashflow & Under-Progress Models

### 5.1 CashflowBucket

Used by `/aramco/cashflow_projection`.

```python
class CashflowBucket(BaseModel):
    period: PeriodLabel                # e.g. "2026-W01" or "2026-01"
    expected_invoice_value_sar: float
    deal_count: int
    comment: Optional[str] = None
```

**Note:** The logic for mapping deals → buckets lives in `cashflow_service`, not in this model.

---

## 6. Owner KPI Models

### 6.1 OwnerKPI

Used by `/owners/kpis`.

```python
class OwnerKPI(BaseModel):
    owner: OwnerName
    activities_count: int
    projects_count: int
    estimated_value_sar: float
    moved_to_production_count: int
    overdue_deals_count: int
    stuck_deals_count: int
```

If you later want an LLM commentary per owner, that likely lives only in the UI or in a separate model, e.g.:

```python
class OwnerKPIWithComment(OwnerKPI):
    commentary: Optional[str] = None
```

---

## 7. Dashboard Models

### 7.1 DashboardItem

Returned by `/dashboard/today`.

```python
from typing import Literal

class DashboardItem(BaseModel):
    type: Literal["overdue", "stuck", "compliance", "cashflow"]
    pipeline: PipelineName
    priority: int               # lower = higher priority
    flag: str                   # e.g. "Overdue ≥7d", "Missing SDD", "Near invoice"
    deal: Optional[DealBase]    # may be None for pure cashflow rows
```

**Notes:**

- `DashboardScreen` will map `DashboardItem` → row in `#dashboard-table`.
- The `priority` field will define row ordering.

---

## 8. Email & Follow-Up Models

### 8.1 DealIssue

Represents a **single deal + its issue summary** for an email body.

```python
class DealIssue(BaseModel):
    deal_id: int
    title: str
    pipeline: PipelineName
    stage: StageName
    issue_summary: str           # “Overdue 10 days and missing survey checklist”
    next_action: Optional[str] = None
```

This is usually built from one of the specialized models + LLM output.

---

### 8.2 EmailDraft

Represents a **single email** to one salesperson, potentially mentioning multiple deals.

Used by:

- `POST /emails/followups/generate`
- `POST /emails/followups/send`

```python
class EmailDraft(BaseModel):
    salesperson: OwnerName
    to_email: str
    subject: str
    body: str
    deals: list[DealIssue]
```

---

## 9. Search Models (Optional)

### 9.1 SearchResult

You can reuse `DealBase` directly for `/deals/search`, or define a small wrapper:

```python
class DealSearchResult(DealBase):
    # currently no extra fields; defined for future extensions
    pass
```

---

## 10. DTO Models for Integrations (Implementation Detail)

In the **integration layer** (e.g. `pipedrive_client.py`), you may define DTOs that mirror Pipedrive responses.

LLM rule: **keep those separate** from domain models above.

Example:

```python
class PipedriveDealDTO(BaseModel):
    id: int
    title: str
    pipeline_id: int
    stage_id: int
    owner_id: int
    org_id: Optional[int] = None
    value: Optional[float] = None
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    # etc.
```

Service layer then maps `PipedriveDealDTO` → `DealBase` or specialized models.

---

## 11. Suggested Module Layout

These models should be placed in `backend/models/`:

- `deal_models.py`
  - `DealBase`, `OverdueDeal`, `StuckDeal`, `OrderReceivedAnalysis`, `ComplianceStatus`, `DealSummary`, `DealNote`, `DealSearchResult`
- `cashflow_models.py`
  - `CashflowBucket`
- `kpi_models.py`
  - `OwnerKPI`
- `dashboard_models.py`
  - `DashboardItem`
- `email_models.py`
  - `DealIssue`, `EmailDraft`

LLM: when generating imports, follow this structure unless the user specifies otherwise.

---

**End of Models_and_Schema.md**  
Use this as the reference for Pydantic models and data structures across the project.
