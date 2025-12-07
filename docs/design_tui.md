# Design_Tui.md
Command Center TUI Design Specification (for LLMs)

> ⚠️ IMPORTANT FOR LLMS  
> - Treat this document as the **source of truth for the Textual UI design**.  
> - Do **not** change screen names, widget IDs, or global key bindings unless the user explicitly asks.  
> - When generating or modifying TUI code, keep the layout and navigation consistent with this document.

This project is a **keyboard-first command center** using **Textual** as the TUI framework and **FastAPI** as the backend API.

---

## 0. High-Level Overview

**Goal:**  
A fast, keyboard-driven Textual app that acts as a command center for:

- Pipedrive-based **sales & project management**
- Basic **cashflow projection**
- **Compliance checks** & follow-ups
- **Owner KPIs** (tables only, no charts)

**Main screens:**

1. `DashboardScreen` – Today’s focus  
2. `AramcoPipelineScreen` – Aramco pipeline deep-dive  
3. `CommercialPipelineScreen` – Commercial pipeline view  
4. `OwnerKPIScreen` – Per-salesperson KPI table  
5. `DealDetailScreen` – Deep dive on a single deal  
6. `EmailDraftsScreen` – Follow-up email review & send  
7. (Future / optional) Search deals screen (`/`)

---

## 1. Global UI Rules

### 1.1 Layout Pattern

All screens must follow the same structure:

- **Header** – App title, current screen name, clock.
- **Main row** – `Horizontal` with:
  - Left: **Sidebar** (`#sidebar`) – filters, mode toggles, actions.
  - Right: **Content** (`#content`) – tables, detail views, summaries.
- **Footer** – Textual `Footer` widget with keybinding hints.

ASCII layout:

```text
┌──────────────────────────────────────────────────────────────┐
│  [App Title] [Current Screen]                     [Clock]    │
├───────────────┬──────────────────────────────────────────────┤
│  Sidebar      │  Main content                               │
│               │                                             │
├───────────────┴──────────────────────────────────────────────┤
│  Footer with keyboard hints                                 │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Global Key Bindings

These should be defined in the main `App` class and work across screens:

- `q` → quit application
- `d` → switch to `DashboardScreen` (`"dashboard"`)
- `a` → switch to `AramcoPipelineScreen` (`"aramco"`)
- `c` → switch to `CommercialPipelineScreen` (`"commercial"`)
- `o` → switch to `OwnerKPIScreen` (`"owner_kpi"`)
- `e` → switch to `EmailDraftsScreen` (`"email_drafts"`)
- `/` → trigger deal search (future screen or dialog)

Example bindings:

```python
BINDINGS = [
    ("q", "quit", "Quit"),
    ("d", "switch_screen('dashboard')", "Dashboard"),
    ("a", "switch_screen('aramco')", "Aramco"),
    ("c", "switch_screen('commercial')", "Commercial"),
    ("o", "switch_screen('owner_kpi')", "Owner KPIs"),
    ("e", "switch_screen('email_drafts')", "Emails"),
    ("/", "search_deals", "Search deals"),
]
```

### 1.3 Common CSS/Layout Conventions

All screens share a consistent style:

```css
Screen {
    layout: vertical;
}

#main-row {
    height: 1fr;
}

#sidebar {
    width: 32;
    border: solid grey;
    padding: 1;
}

#content {
    border: solid grey;
    padding: 1;
}

#sidebar-title, #content-title {
    text-style: bold;
    margin-bottom: 1;
}
```

Additional specific IDs are defined per-screen below.

---

## 2. Screen: DashboardScreen

**Textual class name:** `DashboardScreen`  
**Route/name:** `"dashboard"`

### 2.1 Purpose

Provide a **“Today’s Focus”** overview:

- Deals overdue ≥ 7 days
- Deals stuck > 30 days
- Deals in `Order received` > 30 days
- Deals with missing SDD / survey / quality docs
- Deals near invoicing (cashflow-relevant)

### 2.2 Layout & Widgets

**Sidebar (`#sidebar`):**

- `Static` – `"Dashboard Filters"` (id: `#sidebar-title`)
- Period buttons:
  - `Button("Today", id="period-today")`
  - `Button("Last 7 days", id="period-7")`
  - `Button("Last 30 days", id="period-30")`
- Pipeline toggles:
  - `Button("Aramco ✓", id="pipe-aramco")`
  - `Button("Commercial ✓", id="pipe-commercial")`
- `Button("Refresh", id="btn-refresh")`

**Content (`#content`):**

- `Static("Today’s Focus", id="content-title")`
- `DataTable(id="dashboard-table")`

### 2.3 `dashboard-table` Columns

Columns (fixed):

1. `Type` – `"overdue" | "stuck" | "compliance" | "cashflow"`
2. `Pipeline` – `"Aramco"` / `"Commercial"`
3. `Deal` – deal title
4. `Owner` – salesperson name
5. `Stage` – Pipedrive stage
6. `Days` – overdue days or days in stage
7. `Flag` – short label, e.g. `Overdue ≥7d`, `Missing SDD`, `Ready to invoice`

Rows are typically aggregated from multiple service calls (deal health, compliance, cashflow).

---

## 3. Screen: AramcoPipelineScreen

**Textual class name:** `AramcoPipelineScreen`  
**Route/name:** `"aramco"`

### 3.1 Purpose

View and manage the **“Aramco Projects”** pipeline with different modes:

1. Overdue deals
2. Stuck deals
3. `Order received` ageing (LLM analysis)
4. Compliance (survey / quality docs)
5. Cashflow projection

### 3.2 Layout & Widgets

**Sidebar (`#sidebar`):**

- `Static("Aramco Filters", id="sidebar-title")`
- Mode section (`Static("Mode:")`) with buttons:
  - `Button("1 Overdue", id="mode-overdue")`
  - `Button("2 Stuck", id="mode-stuck")`
  - `Button("3 Order received", id="mode-order")`
  - `Button("4 Compliance", id="mode-compliance")`
  - `Button("5 Cashflow proj.", id="mode-cashflow")`
- Stage filter:
  - `Static("Min days in stage:")`
  - `Input(value="30", id="min-days")`
- Owner filter:
  - `Static("Owner filter:")`
  - `Input(id="owner-filter")`
- `Button("Reload (R)", id="btn-reload")`

**Content (`#content`):**

- `Static("Aramco Pipeline", id="content-title")`
- `Static("[1] Overdue  [2] Stuck  [3] Order  [4] Compliance  [5] Cashflow", id="tab-hints")`
- `DataTable(id="aramco-table")`

### 3.3 `aramco-table` Modes & Columns

The columns of `#aramco-table` change depending on the current mode.

#### Mode 1: Overdue

Columns:

1. `ID`
2. `Title`
3. `Owner`
4. `Stage`
5. `Overdue days`
6. `Value SAR`

#### Mode 2: Stuck

Columns:

1. `ID`
2. `Title`
3. `Owner`
4. `Stage`
5. `Days in stage`
6. `Last activity`

#### Mode 3: Order Received (LLM-assisted)

Columns:

1. `ID`
2. `Title`
3. `Owner`
4. `Days in stage`
5. `End user identified?` (yes/no/unknown)
6. `# end-user requests` (int or `None`)

#### Mode 4: Compliance (LLM-assisted)

Columns:

1. `ID`
2. `Title`
3. `Stage`
4. `Survey checklist?` (yes/no/unclear)
5. `Quality docs?` (yes/no/unclear)
6. `Comment` (short text from LLM)

#### Mode 5: Cashflow Projection

Columns:

1. `Period` – e.g. `"2026-W01"` or `"2026-01"`
2. `Expected invoice value SAR`
3. `# deals`
4. `Comment` (optional)

### 3.4 Behavior

- Mode switch (buttons `#mode-*`) changes columns and reloads data from backend.
- `#btn-reload` reloads data with current filters (min days, owner).
- Selecting a row and pressing `Enter` may open `DealDetailScreen` for that deal.

---

## 4. Screen: CommercialPipelineScreen

**Textual class name:** `CommercialPipelineScreen`  
**Route/name:** `"commercial"`

### 4.1 Purpose

Manage the **commercial pipeline** (`"pipeline"` in Pipedrive):

- Show inactive deals (no movement for ≥ 60 days).
- Show LLM summaries of recently active deals.

### 4.2 Layout & Widgets

**Sidebar (`#sidebar`):**

- `Static("Commercial Filters", id="sidebar-title")`
- Mode section:
  - `Static("Mode:")`
  - `Button("1 Inactive (60+ days)", id="mode-inactive")`
  - `Button("2 Recent summary", id="mode-summary")`
- Owner filter:
  - `Static("Owner filter:")`
  - `Input(id="owner-filter")`
- `Button("Reload", id="btn-reload")`

**Content (`#content`):**

- `Static("Commercial Pipeline", id="content-title")`
- `Static("[1] Inactive  [2] Recent summary", id="tab-hints")`
- `DataTable(id="commercial-table")`

### 4.3 `commercial-table` Modes & Columns

#### Mode 1: Inactive (60+ days)

Columns:

1. `ID`
2. `Title`
3. `Owner`
4. `Stage`
5. `Days in stage`
6. `Last activity`

#### Mode 2: Recent Summary (LLM-assisted)

Columns:

1. `ID`
2. `Title`
3. `Owner`
4. `Org`
5. `Last activity`
6. `LLM summary` – concise status & next action

---

## 5. Screen: OwnerKPIScreen

**Textual class name:** `OwnerKPIScreen`  
**Route/name:** `"owner_kpi"`

### 5.1 Purpose

Show KPIs per salesperson:

- Number of activities
- Number of projects (deals)
- Estimated sales value (SAR)
- Number of projects moved to Production
- Number of overdue deals
- Number of stuck deals

### 5.2 Layout & Widgets

**Sidebar (`#sidebar`):**

- `Static("Owner KPI Filters", id="sidebar-title")`
- Period:
  - `Static("Period:")`
  - `Button("This week", id="period-week")`
  - `Button("This month", id="period-month")`
  - `Button("Last 60 days", id="period-60")`
- Pipelines:
  - `Static("Pipelines:")`
  - `Button("Aramco ✓", id="pipe-aramco")`
  - `Button("Commercial ✓", id="pipe-commercial")`
- `Button("Refresh", id="btn-refresh")`

**Content (`#content`):**

- `Static("Owner KPIs", id="content-title")`
- `DataTable(id="owner-table")`
- `Static("LLM commentary will appear here…", id="owner-commentary")`

### 5.3 `owner-table` Columns

Columns:

1. `Owner`
2. `# Activities`
3. `# Projects`
4. `Est. value SAR`
5. `# to Production`
6. `# Overdue`
7. `# Stuck`

`#owner-commentary` is updated when a row is selected, showing a short LLM-generated interpretation.

---

## 6. Screen: DealDetailScreen

**Textual class name:** `DealDetailScreen`  
**Route/name:** `"deal_detail"`

### 6.1 Purpose

Deep dive on a single deal:

- Show key Pipedrive fields.
- Show notes.
- Show LLM summary and compliance flags.

### 6.2 Layout & Widgets

Container: `Vertical(id="deal-main")`

**Header & Summary:**

- `Static("Deal Detail", id="deal-header")`
- `Horizontal(id="deal-summary-row")`
  - `Static("Summary", id="deal-summary")`  
    (text includes pipeline, stage, owner, value, age, last activity)

**Body:**

- `Horizontal(id="deal-body")`

Left side: `Vertical(id="deal-notes")`

- `Static("Notes", id="notes-title")`
- `DataTable(id="notes-table")`
  - Columns:
    1. `Date`
    2. `Author`
    3. `Note (short)`

Right side: `Vertical(id="deal-llm")`

- `Static("AI Summary", id="llm-title")`
- `Static(id="llm-summary")` – status, blockers, next steps
- `Static("Compliance checks:", id="llm-compliance-title")` (optional id)
- `Static(id="llm-compliance")` – SDD?, end user?, survey?, quality docs?

**Footer:**

- `Static("[B] Back   [E] Add to follow-up email", id="deal-footer")`

### 6.3 Key Bindings

- `B` – navigate back to previous screen.
- `E` – mark this deal to be included in follow-up emails (state stored in frontend or backend).

---

## 7. Screen: EmailDraftsScreen

**Textual class name:** `EmailDraftsScreen`  
**Route/name:** `"email_drafts"`

### 7.1 Purpose

Manage **LLM-generated follow-up emails** to salespeople:

- Group deals by salesperson.
- For each salesperson, display the draft email.
- Allow sending or regenerating.

### 7.2 Layout & Widgets

`Horizontal(id="main-row")`

**Sidebar (`#sidebar`):**

- `Static("Salespeople", id="sidebar-title")`
- `ListView(id="sales-list")`
  - Each `ListItem` shows e.g. `"Faris (3)"` for 3 deals in his email.

**Content (`#content`):**

- `Static("Email Draft", id="content-title")`
- `Static("To: <email>", id="email-to")`
- `Static("Subject: <subject>", id="email-subject")`
- `Static("Email body preview here…", id="email-body")`
- `Static("[S] Send   [R] Regenerate   [B] Back", id="email-footer")`

### 7.3 Behavior

- Selecting an item in `#sales-list` loads the corresponding `EmailDraft` (from backend).
- `S` – send the email.
- `R` – regenerate the draft via LLM.
- `B` – go back or deselect currently focused salesperson.

---

## 8. Future: Search Deals Screen (Optional)

Triggered by key `/`.

**Goal:** Quick deal search by title/org/person.

Recommended behavior:

- Show input at top: search query.
- Show table of results: `ID`, `Title`, `Pipeline`, `Owner`, `Stage`, `Last activity`.
- `Enter` opens `DealDetailScreen` for selected deal.

Layout pattern should follow the same sidebar/content structure:

- Sidebar: Filter presets (e.g., pipelines, owner).
- Content: Search box + results table.

---

## 9. Guidance for LLM When Generating UI Code

1. **Do not rename IDs** (`#dashboard-table`, `#aramco-table`, etc.) or class names unless explicitly requested.
2. Use `DataTable` for all tables; do not replace with other widgets.
3. For multi-mode tables (Aramco, Commercial):
   - Change columns when mode changes.
   - Clear and repopulate rows on reload.
4. Textual app should:
   - Mount `Header(show_clock=True)` at top.
   - Mount `Footer()` at bottom.
   - Use `install_screen` and `switch_screen` to navigate between screens.
5. Backend API:
   - All data and status come from FastAPI endpoints.
   - TUI should not directly call Pipedrive or the LLM.
6. Error handling:
   - If an HTTP call fails, display a simple error row or message in the content area instead of crashing.
7. When adding new features:
   - Reuse sidebar + content pattern.
   - Prefer adding new columns or new modes instead of entirely new layout types.

---

**End of Design_Tui.md**  
This file defines the Textual UI contract. All TUI code should stay aligned with this specification unless the user clearly requests a change.
