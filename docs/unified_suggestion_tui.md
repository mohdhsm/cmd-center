# Unified TUI Keyboard Navigation Suggestion

## Executive Summary

This document proposes a unified keyboard navigation system for all Command Center TUI screens. The goal is to create consistent, intuitive, and conflict-free keyboard shortcuts across all screens.

---

## Current State Analysis

### Global Key Bindings (app.py)
| Key | Screen | Route Name |
|-----|--------|------------|
| `q` | Quit | — |
| `d` | Dashboard | `dashboard` |
| `a` | Aramco Pipeline | `aramco` |
| `c` | Commercial Pipeline | `commercial` |
| `o` | Owner KPIs | `owner_kpi` |
| `e` | Email Drafts | `email_drafts` |
| `m` | Management (Tasks/Notes) | `management` |
| `t` | Tracker (Docs/Bonuses/Logs/Skills) | `tracker` |

### Per-Screen Bindings

| Screen | Keys Used | Purpose |
|--------|-----------|---------|
| DashboardScreen | `r` | Refresh |
| AramcoPipelineScreen | `1-5`, `r`, `t`, `s` | Modes, reload, focus table/sidebar |
| CommercialPipelineScreen | `1-2`, `r` | Modes, reload |
| OwnerKPIScreen | (none) | — |
| DealDetailScreen | `b`, `e` | Back, add to email |
| ManagementScreen | `1-2`, `n`, `e`, `c`, `d`, `r`, `Enter` | Modes, CRUD |
| TrackerScreen | `1-4`, `n`, `e`, `$`, `r`, `Escape` | Modes, CRUD, payment |

### Identified Conflicts

| Key | Global Use | Screen-Level Use | Severity |
|-----|------------|------------------|----------|
| `t` | Tracker screen | AramcoPipeline: Focus table | **High** |
| `e` | Email Drafts screen | Management: Edit item | **High** |
| `d` | Dashboard screen | Management: Delete item | **High** |
| `c` | Commercial screen | Management: Complete task | **High** |

---

## Proposed Solution

### Design Principles

1. **Reserved Keys**: Global navigation keys (`d`, `a`, `c`, `o`, `e`, `m`, `t`, `l`, `p`, `q`) should NEVER be used for screen-specific actions
2. **Numeric Modes**: `1-9` for mode/tab switching within a screen (already consistent)
3. **CRUD Convention**: Use function keys or modifiers for CRUD operations
4. **Escape**: Always goes back/dismisses
5. **Enter**: Always opens detail/selects

### Recommended Global Key Allocation

```
┌─────────────────────────────────────────────────────────────┐
│                  GLOBAL NAVIGATION KEYS                      │
├─────────────────────────────────────────────────────────────┤
│  Pipeline/Sales Screens:                                     │
│    d → Dashboard (Today's Focus)                             │
│    a → Aramco Pipeline                                       │
│    c → Commercial Pipeline                                   │
│    o → Owner KPIs                                           │
│    e → Email Drafts                                         │
│                                                              │
│  CEO Management Screens:                                     │
│    m → Management (Tasks & Notes)                            │
│    t → Tracker (Documents, Bonuses, Logs, Skills)            │
│    p → People/Team (Employee directory)                      │
│    l → Loop Monitor (Automation status)                      │
│                                                              │
│  Utility:                                                    │
│    / → Search (future)                                       │
│    ? → Help                                                  │
│    q → Quit                                                  │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Screen-Level Key Convention

For **ALL** screens that support CRUD operations:

| Key | Action | Mnemonic |
|-----|--------|----------|
| `n` | New/Create | **N**ew |
| `F2` or `Shift+E` | Edit | (avoids `e` conflict) |
| `x` or `Del` | Delete/Archive | e**X**ecute removal |
| `Space` | Toggle/Complete | Select/action |
| `r` | Refresh/Reload | **R**efresh |
| `Enter` | View Detail | Open |
| `Escape` | Back/Cancel | Exit |

For **multi-mode** screens:

| Key | Action |
|-----|--------|
| `1-9` | Switch to mode 1-9 |
| `Tab` | Cycle modes (optional) |

For **modal dialogs**:

| Key | Action |
|-----|--------|
| `Escape` | Cancel/Close |
| `Ctrl+Enter` | Save/Submit |
| `y` | Confirm (in confirmation dialogs) |
| `n` | Cancel (in confirmation dialogs) |

### Per-Screen Recommended Bindings

#### DashboardScreen
```python
BINDINGS = [
    ("r", "refresh", "Refresh"),
    ("enter", "view_detail", "View Deal"),
]
```

#### AramcoPipelineScreen
```python
BINDINGS = [
    ("1", "mode_overdue", "Overdue"),
    ("2", "mode_stuck", "Stuck"),
    ("3", "mode_order", "Order Received"),
    ("4", "mode_compliance", "Compliance"),
    ("5", "mode_cashflow", "Cashflow"),
    ("r", "reload", "Reload"),
    ("enter", "view_deal", "View Deal"),
    # REMOVE: ("t", "focus_table") - conflicts with global
    # REMOVE: ("s", "focus_sidebar") - not essential
]
```

#### CommercialPipelineScreen
```python
BINDINGS = [
    ("1", "mode_inactive", "Inactive"),
    ("2", "mode_summary", "Summary"),
    ("r", "reload", "Reload"),
    ("enter", "view_deal", "View Deal"),
]
```

#### ManagementScreen (Tasks & Notes)
```python
BINDINGS = [
    ("1", "mode_tasks", "Tasks"),
    ("2", "mode_notes", "Notes"),
    ("n", "new_item", "New"),
    ("F2", "edit_item", "Edit"),       # Changed from 'e'
    ("space", "complete_task", "Complete"),  # Changed from 'c'
    ("x", "delete_item", "Delete"),    # Changed from 'd'
    ("r", "refresh", "Refresh"),
    ("enter", "view_detail", "View"),
]
```

#### TrackerScreen (Documents, Bonuses, Logs, Skills)
```python
BINDINGS = [
    ("1", "mode_documents", "Docs"),
    ("2", "mode_bonuses", "Bonuses"),
    ("3", "mode_logs", "Logs"),
    ("4", "mode_skills", "Skills"),
    ("n", "new_item", "New"),
    ("F2", "edit_item", "Edit"),
    ("$", "record_payment", "Payment"),  # Specific to bonuses
    ("r", "refresh", "Refresh"),
    ("enter", "view_detail", "View"),
    ("escape", "go_back", "Back"),
]
```

#### TeamScreen (Future)
```python
BINDINGS = [
    ("n", "new_employee", "New"),
    ("F2", "edit_employee", "Edit"),
    ("s", "view_skills", "Skills"),     # Safe: not global
    ("r", "refresh", "Refresh"),
    ("enter", "view_detail", "View"),
]
```

#### LoopMonitorScreen (Future)
```python
BINDINGS = [
    ("1", "mode_status", "Status"),
    ("2", "mode_findings", "Findings"),
    ("3", "mode_history", "History"),
    ("enter", "run_selected", "Run Loop"),
    ("r", "refresh", "Refresh"),
]
```

---

## Navigation Flow Diagram

```
                    ┌──────────────────────────────────────────────┐
                    │             COMMAND CENTER                    │
                    │                 (App)                         │
                    └──────────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────┐
        │                               │                           │
        ▼                               ▼                           ▼
┌───────────────┐             ┌───────────────┐             ┌───────────────┐
│   PIPELINE    │             │   CEO MGMT    │             │   UTILITY     │
│   SCREENS     │             │   SCREENS     │             │               │
├───────────────┤             ├───────────────┤             ├───────────────┤
│ d Dashboard   │             │ m Management  │             │ / Search      │
│ a Aramco      │             │ t Tracker     │             │ ? Help        │
│ c Commercial  │             │ p Team        │             │ q Quit        │
│ o Owner KPIs  │             │ l Loops       │             │               │
│ e Emails      │             │               │             │               │
└───────┬───────┘             └───────┬───────┘             └───────────────┘
        │                             │
        ▼                             ▼
┌───────────────┐             ┌───────────────┐
│ Deal Detail   │◄───Enter────│ Item Detail   │
│   (Modal)     │             │   (Modal)     │
│               │             │               │
│  b Back       │             │  Escape Back  │
│  e Add Email  │             │  F2 Edit      │
└───────────────┘             └───────────────┘
```

---

## Implementation Checklist

### Phase 1: Resolve Conflicts (Required)
- [ ] Remove `t` binding from AramcoPipelineScreen (focus_table)
- [ ] Remove `s` binding from AramcoPipelineScreen (focus_sidebar)
- [ ] Change ManagementScreen `e` to `F2` for edit
- [ ] Change ManagementScreen `d` to `x` for delete
- [ ] Change ManagementScreen `c` to `Space` for complete
- [ ] Update TrackerScreen to use same conventions

### Phase 2: Add Missing Bindings
- [ ] Add `r` (refresh) to OwnerKPIScreen
- [ ] Add `enter` (view detail) to all list screens
- [ ] Add `escape` (go back) where missing

### Phase 3: Footer Consistency
- [ ] Ensure all screens show consistent footer hints
- [ ] Format: `key Action` (e.g., `n New  F2 Edit  x Delete  r Refresh`)
- [ ] Group by category: modes | actions | navigation

### Phase 4: Help System
- [ ] Add `?` global binding for help overlay
- [ ] Create help modal showing all available keys for current screen

---

## Alternative Key Mapping (If F-keys Are Problematic)

If function keys don't work well in some terminals:

| Current | Alternative | Action |
|---------|-------------|--------|
| `F2` (edit) | `Shift+E` or `Ctrl+E` | Edit |
| `Del` (delete) | `x` | Delete |
| `Space` (complete) | `` ` `` (backtick) | Complete |

---

## Screen Switching Methods

### Method 1: Direct Key Press (Current)
Press the screen key directly from any screen:
- From Dashboard, press `m` → Management screen
- From Management, press `d` → Dashboard screen

### Method 2: Escape to Dashboard First
Always escape back to Dashboard, then navigate:
- Not recommended (extra keystrokes)

### Method 3: Command Palette (Future Enhancement)
Press `Ctrl+P` or `:` to open command palette:
```
: management
: tracker bonuses
: aramco stuck
```

---

## Recommended Footer Format

```
┌──────────────────────────────────────────────────────────────────────────┐
│  1 Tasks  2 Notes │ n New  F2 Edit  x Del │ r Refresh  Enter View  q Quit│
└──────────────────────────────────────────────────────────────────────────┘
```

Structure:
1. **Modes** (if applicable): `1 Mode1  2 Mode2  ...`
2. **CRUD Actions**: `n New  F2 Edit  x Delete`
3. **Navigation**: `r Refresh  Enter View  Esc Back  q Quit`

---

## Summary

The key changes needed:
1. **Never use global screen navigation keys (d, a, c, o, e, m, t, p, l) for screen-local actions**
2. **Use `F2` or `Shift+E` for Edit** (instead of conflicting `e`)
3. **Use `x` for Delete** (instead of conflicting `d`)
4. **Use `Space` for Complete/Toggle** (instead of conflicting `c`)
5. **Standardize `1-9` for modes, `r` for refresh, `Enter` for detail, `Escape` for back**

This creates a predictable, muscle-memory-friendly interface where users know:
- Letters navigate between screens
- Numbers switch modes within a screen
- `n`/`F2`/`x`/`Space` are CRUD operations
- `Enter` opens, `Escape` closes
