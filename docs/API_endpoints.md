# API_endpoints.md
Command Center API Endpoint Specification (for LLMs)

> ⚠️ IMPORTANT FOR LLMS  
> - Treat this file as the **source of truth for HTTP endpoints**.  
> - When generating backend or frontend code, keep these routes and shapes stable unless the user explicitly asks to change them.  
> - The TUI (Textual) must talk **only** to these endpoints, not directly to Pipedrive or the LLM.

Backend framework: **FastAPI**  
All endpoints are **JSON over HTTP**.

---

## 0. Global Conventions

### 0.1 Base URL

For local development:

- `BASE_URL = "http://localhost:8000"`

All examples assume this base.

### 0.2 Common Headers

- `Content-Type: application/json`
- Authentication header (to be implemented later, but reserve now):

```http
Authorization: Bearer <INTERNAL_API_TOKEN>
```

For now you can omit auth during development.

### 0.3 Error Format

On errors (4xx / 5xx), endpoints should return:

```json
{
  "detail": "Human readable message",
  "code": "OPTIONAL_ERROR_CODE"
}
```

FastAPI’s default `{"detail": "..."}` is acceptable.

### 0.4 Data Models (Conceptual Names)

These names refer to Pydantic models in `backend/models/`:

- `DealBase`
- `OverdueDeal`
- `StuckDeal`
- `OrderReceivedAnalysis`
- `ComplianceStatus`
- `DealSummary`
- `CashflowBucket`
- `OwnerKPI`
- `DealNote`
- `DashboardItem`
- `EmailDraft`
- `DealIssue`

LLMs: When generating code, import from `backend.models.*` according to these names.

---

## 1. Health

### 1.1 GET /health

**Purpose:** Basic liveness probe for the backend.

- **Method:** `GET`
- **Path:** `/health`
- **Query params:** _none_
- **Body:** _none_

**Response 200:**

```json
{
  "status": "ok"
}
```

Used by TUI (or external tools) to check if the API is running.

---

## 2. Dashboard (Today’s Focus)

### 2.1 GET /dashboard/today

**Purpose:** Return a unified list of “today’s focus” items, aggregated from overdue deals, stuck deals, compliance problems, and near-invoicing deals.

- **Method:** `GET`
- **Path:** `/dashboard/today`
- **Query params:**
  - `period` (optional, string): `"today" | "7d" | "30d"`.  
    - Default: `"7d"`.

**Response 200:**

Returns a JSON array of `DashboardItem`:

```jsonc
[
  {
    "type": "overdue",             // "overdue" | "stuck" | "compliance" | "cashflow"
    "pipeline": "Aramco",          // e.g. "Aramco" or "Commercial"
    "priority": 1,                 // lower number = higher priority
    "flag": "Overdue ≥7d",
    "deal": {
      "id": 123,
      "title": "Camp Toilets Phase 1",
      "pipeline": "Aramco Projects",
      "stage": "Proposal",
      "owner": "Faris",
      "org_name": "ABC Contracting",
      "value_sar": 450000,
      "add_time": "2025-11-01T10:00:00",
      "update_time": "2025-11-20T14:30:00",
      "last_activity_time": "2025-11-20T14:30:00"
    }
  }
]
```

TUI: `DashboardScreen` uses this to populate `#dashboard-table`.

---

## 3. Aramco Pipeline Endpoints

All these endpoints focus on the Pipedrive pipeline named `"Aramco Projects"`.

### 3.1 GET /aramco/overdue

**Purpose:** List deals that are overdue by at least a minimum number of days.

- **Method:** `GET`
- **Path:** `/aramco/overdue`
- **Query params:**
  - `min_days` (int, optional) – default `7`.

**Response 200:**

Array of `OverdueDeal`:

```jsonc
[
  {
    "id": 123,
    "title": "Camp Toilets Phase 1",
    "pipeline": "Aramco Projects",
    "stage": "Proposal",
    "owner": "Faris",
    "org_name": "ABC Contracting",
    "value_sar": 450000,
    "add_time": "2025-11-01T10:00:00",
    "update_time": "2025-11-20T14:30:00",
    "last_activity_time": "2025-11-20T14:30:00",
    "overdue_days": 10
  }
]
```

TUI mapping: `AramcoPipelineScreen` mode=Overdue.

---

### 3.2 GET /aramco/stuck

**Purpose:** List deals that have been in the same stage longer than a threshold.

- **Method:** `GET`
- **Path:** `/aramco/stuck`
- **Query params:**
  - `min_days` (int, optional) – default `30`.

**Response 200:**

Array of `StuckDeal`:

```jsonc
[
  {
    "id": 234,
    "title": "Dorm Baffles",
    "pipeline": "Aramco Projects",
    "stage": "Design",
    "owner": "Ahmed",
    "org_name": "XYZ Dev",
    "value_sar": 300000,
    "add_time": "2025-10-01T10:00:00",
    "update_time": "2025-11-01T09:00:00",
    "last_activity_time": "2025-11-01T09:00:00",
    "days_in_stage": 42
  }
]
```

TUI mapping: `AramcoPipelineScreen` mode=Stuck.

---

### 3.3 GET /aramco/order_received

**Purpose:** Analyze deals in `"Order received"` stage that have been there longer than a threshold, with LLM fields about end user.

- **Method:** `GET`
- **Path:** `/aramco/order_received`
- **Query params:**
  - `min_days` (int, optional) – default `30`.

**Response 200:**

Array of `OrderReceivedAnalysis`:

```jsonc
[
  {
    "id": 345,
    "title": "Camp A PH2",
    "pipeline": "Aramco Projects",
    "stage": "Order received",
    "owner": "Faris",
    "org_name": "ABC Contracting",
    "value_sar": 800000,
    "add_time": "2025-10-10T10:00:00",
    "update_time": "2025-11-20T10:00:00",
    "last_activity_time": "2025-11-20T10:00:00",
    "days_in_stage": 37,
    "end_user_identified": true,
    "end_user_requests_count": 3
  }
]
```

TUI mapping: `AramcoPipelineScreen` mode=Order.

---

### 3.4 GET /aramco/compliance

**Purpose:** LLM-driven compliance check for survey checklists and quality inspection documents.

- **Method:** `GET`
- **Path:** `/aramco/compliance`
- **Query params:** none (for now; can add filters later).

**Response 200:**

Array of `ComplianceStatus`:

```jsonc
[
  {
    "id": 456,
    "title": "Camp A PH2",
    "pipeline": "Aramco Projects",
    "stage": "Execution",
    "owner": "Faris",
    "org_name": "ABC Contracting",
    "value_sar": 800000,
    "add_time": "2025-10-10T10:00:00",
    "update_time": "2025-11-22T10:00:00",
    "last_activity_time": "2025-11-22T10:00:00",
    "survey_checklist_present": true,
    "quality_docs_present": false,
    "comment": "Missing post-MDD quality inspection report."
  }
]
```

TUI mapping: `AramcoPipelineScreen` mode=Compliance.

---

### 3.5 GET /aramco/cashflow_projection

**Purpose:** Project expected invoice value by time bucket based on deal stages.

- **Method:** `GET`
- **Path:** `/aramco/cashflow_projection`
- **Query params:**
  - `bucket` (string, optional): `"week"` or `"month"`. Default `"week"`.

**Response 200:**

Array of `CashflowBucket`:

```jsonc
[
  {
    "period": "2026-W01",
    "expected_invoice_value_sar": 1200000,
    "deal_count": 3,
    "comment": "Mostly awaiting GR stage."
  },
  {
    "period": "2026-W02",
    "expected_invoice_value_sar": 750000,
    "deal_count": 2,
    "comment": "Two under progress deals."
  }
]
```

TUI mapping: `AramcoPipelineScreen` mode=Cashflow.

---

## 4. Commercial Pipeline Endpoints

All these endpoints work on the Pipedrive pipeline named `"pipeline"` (commercial deals).

### 4.1 GET /commercial/inactive

**Purpose:** Show commercial deals that have been inactive (same stage, no activity) for a long time.

- **Method:** `GET`
- **Path:** `/commercial/inactive`
- **Query params:**
  - `min_days` (int, optional) – default `60`.

**Response 200:**

Array of `StuckDeal`:

```jsonc
[
  {
    "id": 789,
    "title": "Office Fitout Tower B",
    "pipeline": "pipeline",
    "stage": "Design",
    "owner": "Arshad",
    "org_name": "Real Estate Holdings",
    "value_sar": 600000,
    "add_time": "2025-09-01T10:00:00",
    "update_time": "2025-10-01T10:00:00",
    "last_activity_time": "2025-10-01T10:00:00",
    "days_in_stage": 75
  }
]
```

TUI mapping: `CommercialPipelineScreen` mode=Inactive.

---

### 4.2 GET /commercial/recent_summary

**Purpose:** Summarize recently active commercial deals using LLM.

- **Method:** `GET`
- **Path:** `/commercial/recent_summary`
- **Query params:**
  - `days` (int, optional) – default `60`.

**Response 200:**

Array of `DealSummary`:

```jsonc
[
  {
    "id": 901,
    "title": "Mall Toilets",
    "pipeline": "pipeline",
    "stage": "Proposal",
    "owner": "Faris",
    "org_name": "ABC Real Estate",
    "value_sar": 500000,
    "add_time": "2025-11-01T10:00:00",
    "update_time": "2025-11-28T12:00:00",
    "last_activity_time": "2025-11-28T12:00:00",
    "last_activity_date": "2025-11-28T12:00:00",
    "llm_summary": "Client reviewing revised quote; follow up this week.",
    "next_action": "Call client to confirm decision by Thursday."
  }
]
```

TUI mapping: `CommercialPipelineScreen` mode=Summary.

---

## 5. Owner KPI Endpoints

### 5.1 GET /owners/kpis

**Purpose:** Get aggregated KPIs per salesperson.

- **Method:** `GET`
- **Path:** `/owners/kpis`
- **Query params:**
  - `period` (string, optional):
    - `"this_week" | "this_month" | "last_60d"`
    - Default: `"this_month"`.
  - `pipelines` (string, optional):
    - Comma-separated list, e.g. `"aramco,commercial"`.
    - Default: `"aramco,commercial"`.

**Response 200:**

Array of `OwnerKPI`:

```jsonc
[
  {
    "owner": "Faris",
    "activities_count": 25,
    "projects_count": 12,
    "estimated_value_sar": 3200000,
    "moved_to_production_count": 2,
    "overdue_deals_count": 3,
    "stuck_deals_count": 1
  },
  {
    "owner": "Arshad",
    "activities_count": 18,
    "projects_count": 9,
    "estimated_value_sar": 1900000,
    "moved_to_production_count": 1,
    "overdue_deals_count": 1,
    "stuck_deals_count": 0
  }
]
```

TUI mapping: `OwnerKPIScreen` table.

---

## 6. Deal Detail Endpoint

### 6.1 GET /deals/{deal_id}/detail

**Purpose:** Provide a deep-dive view for a single deal, including notes and LLM insights.

- **Method:** `GET`
- **Path:** `/deals/{deal_id}/detail`
- **Path params:**
  - `deal_id` (int) – Pipedrive deal ID.

**Response 200:**

```jsonc
{
  "deal": {
    "id": 123,
    "title": "Camp Toilets Phase 1",
    "pipeline": "Aramco Projects",
    "stage": "Order received",
    "owner": "Faris",
    "org_name": "ABC Contracting",
    "value_sar": 450000,
    "add_time": "2025-11-01T10:00:00",
    "update_time": "2025-11-20T14:30:00",
    "last_activity_time": "2025-11-20T14:30:00"
  },
  "notes": [
    {
      "id": 1,
      "date": "2025-11-10T09:00:00",
      "author": "Faris",
      "content": "SDD requested from client, waiting for response."
    },
    {
      "id": 2,
      "date": "2025-11-18T15:00:00",
      "author": "Faris",
      "content": "Client requested updated BOQ, sent."
    }
  ],
  "compliance": {
    "id": 123,
    "title": "Camp Toilets Phase 1",
    "pipeline": "Aramco Projects",
    "stage": "Execution",
    "owner": "Faris",
    "org_name": "ABC Contracting",
    "value_sar": 450000,
    "add_time": "2025-11-01T10:00:00",
    "update_time": "2025-11-20T14:30:00",
    "last_activity_time": "2025-11-20T14:30:00",
    "survey_checklist_present": false,
    "quality_docs_present": false,
    "comment": "Survey checklist missing; quality docs not yet created."
  },
  "sdd_requested": true,
  "end_user_identified": true
}
```

TUI mapping: `DealDetailScreen`.

---

## 7. Email Draft Endpoints

### 7.1 POST /emails/followups/generate

**Purpose:** Generate follow-up email drafts per salesperson, based on filtered deals.

- **Method:** `POST`
- **Path:** `/emails/followups/generate`
- **Body (JSON):**

```jsonc
{
  "conditions": {
    "include_overdue": true,
    "include_stuck": true,
    "include_missing_compliance": true,
    "min_overdue_days": 7,
    "min_stuck_days": 30
  },
  "pipelines": ["Aramco Projects", "pipeline"]
}
```

Fields can be extended later; LLM should preserve shape when adding options.

**Response 200:**

Array of `EmailDraft`:

```jsonc
[
  {
    "salesperson": "Faris",
    "to_email": "faris@example.com",
    "subject": "Follow up on your active Aramco & commercial deals",
    "body": "Dear Faris, ...",
    "deals": [
      {
        "deal_id": 123,
        "title": "Camp Toilets Phase 1",
        "pipeline": "Aramco Projects",
        "stage": "Order received",
        "issue_summary": "Overdue 10 days and missing survey checklist.",
        "next_action": "Contact end user to schedule survey this week."
      }
    ]
  }
]
```

TUI mapping: `EmailDraftsScreen` loads these and displays by salesperson.

---

### 7.2 POST /emails/followups/send

**Purpose:** Send follow-up emails generated by the previous endpoint.

- **Method:** `POST`
- **Path:** `/emails/followups/send`
- **Body (JSON):**

Option 1 (send full drafts):

```jsonc
{
  "drafts": [
    {
      "salesperson": "Faris",
      "to_email": "faris@example.com",
      "subject": "Follow up on your active Aramco & commercial deals",
      "body": "Dear Faris, ...",
      "deals": [
        {
          "deal_id": 123,
          "title": "Camp Toilets Phase 1",
          "pipeline": "Aramco Projects",
          "stage": "Order received",
          "issue_summary": "Overdue 10 days and missing survey checklist.",
          "next_action": "Contact end user to schedule survey this week."
        }
      ]
    }
  ]
}
```

Option 2 (if you later introduce server-side draft IDs):

```jsonc
{
  "draft_ids": [1, 2, 3]
}
```

**Response 200:**

```json
{
  "status": "sent",
  "sent_to": ["faris@example.com"]
}
```

TUI mapping: `EmailDraftsScreen`’s `S` key calls this endpoint.

---

## 8. Optional: Search Endpoint

(Planned for `/` shortcut, not required for MVP, but reserved.)

### 8.1 GET /deals/search

**Purpose:** Search deals by title, org, owner, etc.

- **Method:** `GET`
- **Path:** `/deals/search`
- **Query params:**
  - `q` (string, required) – search query
  - `pipeline` (string, optional) – limit to one pipeline
  - `owner` (string, optional)

**Response 200:**

Array of `DealBase`:

```jsonc
[
  {
    "id": 777,
    "title": "Camp A Showers",
    "pipeline": "Aramco Projects",
    "stage": "Proposal",
    "owner": "Faris",
    "org_name": "ABC Contracting",
    "value_sar": 250000,
    "add_time": "2025-11-02T10:00:00",
    "update_time": "2025-11-25T14:30:00",
    "last_activity_time": "2025-11-25T14:30:00"
  }
]
```

TUI mapping: future `SearchScreen` or dialog; `Enter` opens `DealDetailScreen`.

---

**End of API_endpoints.md**  
Use this file as the reference when implementing FastAPI routes and when wiring the TUI to the backend.
