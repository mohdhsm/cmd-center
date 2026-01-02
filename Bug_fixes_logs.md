# Bug Fixes Log

This document summarizes all bugs fixed in the TUI screens during the integration testing phase.

---

## 1. Team Screen - Employee List Not Displaying

**Error:** `'str' object does not support item assignment`

**Root Cause:** The API returns paginated responses wrapped in an `items` key (e.g., `{"items": [...], "total": 3}`), but the frontend code was treating the response as a direct list. When iterating over a dict, Python returns the keys as strings, causing the error.

**Files Affected:**
- `cmd_center/screens/team_screen.py`
- `cmd_center/screens/tracker_screen.py`
- `cmd_center/screens/management_screen.py`
- `cmd_center/screens/loop_monitor_screen.py`

**Fix:** Extract `items` from the paginated response:
```python
# Before
self.employees = response.json()

# After
data = response.json()
self.employees = data.get("items", [])
```

---

## 2. TaskCreateModal Crash on Open

**Error:** `AttributeError: property 'task' of 'TaskCreateModal' object has no setter`

**Root Cause:** Textual's `ModalScreen` class has a built-in `task` property that conflicts with using `self.task` as an instance variable.

**File Affected:** `cmd_center/screens/ceo_modals.py`

**Fix:** Renamed the instance variable to avoid the conflict:
```python
# Before
self.task = task

# After
self._task_data = task
```

---

## 3. DateTime Timezone Mismatch

**Error:** `can't subtract offset-naive and offset-aware datetimes`

**Root Cause:** The code was mixing timezone-aware datetimes (from `datetime.now(timezone.utc)`) with timezone-naive datetimes (parsed from API responses without timezone info).

**File Affected:** `cmd_center/screens/management_screen.py`

**Fix:** Ensure parsed datetimes have timezone info:
```python
due_dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
if due_dt.tzinfo is None:
    due_dt = due_dt.replace(tzinfo=timezone.utc)
```

---

## 4. NoteCreateModal Buttons Partially Hidden

**Error:** Modal buttons were cut off at the bottom of the screen.

**Root Cause:** The modal's `max-height` CSS property was set too low (35) for the content.

**File Affected:** `cmd_center/screens/ceo_modals.py`

**Fix:** Increased the modal max-height:
```css
/* Before */
max-height: 35;

/* After */
max-height: 45;
```

---

## 5. LogCreateModal Crash on Open

**Error:** `AttributeError: property 'log' of 'LogCreateModal' object has no setter`

**Root Cause:** Same issue as TaskCreateModal - Textual's `ModalScreen` has a built-in `log` property that conflicts with `self.log`.

**File Affected:** `cmd_center/screens/tracker_screen.py`

**Fix:** Renamed the instance variable:
```python
# Before
self.log = log

# After
self._log_data = log
```

---

## 6. Empty Employee Select Crash

**Error:** `InvalidSelectValueError: Illegal select value ''`

**Root Cause:** When the employees list was empty (not yet loaded from API), the Select widget was initialized with an empty string value, which is invalid.

**File Affected:** `cmd_center/screens/tracker_screen.py`

**Fix:** Added a placeholder option and async employee loading:
```python
emp_options = [(name, str(id)) for id, name in self.employees.items()]
if not emp_options:
    emp_options = [("Loading...", "0")]
```

---

## 7. Log Creation Not Saving

**Error:** Clicking "Save" did nothing - no API call made or silent failure.

**Root Cause:** Multiple field name mismatches between frontend and API:
- Frontend sent `summary`/`details`, API expected `title`/`content`
- Frontend used invalid category `"performance_review"` (API accepts: achievement, issue, feedback, milestone, other)
- Frontend used invalid severity `"critical"` (API accepts: low, medium, high)

**File Affected:** `cmd_center/screens/tracker_screen.py`

**Fix:** Corrected field names and valid options:
```python
# Before
data = {
    "summary": summary,
    "details": details,
    "category": category,  # included "performance_review"
    "severity": severity,  # included "critical"
}

# After
data = {
    "title": title,
    "content": content,
    "category": category,  # milestone, other instead of performance_review
    "severity": severity,  # low, medium, high only
}
```

---

## 8. Edit Functionality Not Saving

**Error:** Edit modal saves appeared to work but changes weren't persisted.

**Root Cause:** The frontend used HTTP `PATCH` method, but the API endpoints only accept `PUT` for updates.

**Files Affected:** `cmd_center/screens/tracker_screen.py`
- `DocumentCreateModal._save_document()`
- `BonusCreateModal._save_bonus()`
- `SkillCreateModal._save_skill()`

**Fix:** Changed HTTP method from PATCH to PUT:
```python
# Before
response = await client.patch(f"{self.api_url}/documents/{id}", json=data)

# After
response = await client.put(f"{self.api_url}/documents/{id}", json=data)
```

**Note:** LogCreateModal edit was disabled since employee logs are immutable (no update endpoint exists).

---

## 9. Log Table Showing Wrong Field

**Error:** Log table "Summary" column was empty or showing incorrect data.

**Root Cause:** The render function referenced `log.get("summary")` but the API returns `title`.

**File Affected:** `cmd_center/screens/tracker_screen.py`

**Fix:** Updated field reference and column header:
```python
# Before
table.add_columns(..., "Summary")
summary = log.get("summary", "")[:40]

# After
table.add_columns(..., "Title")
title = log.get("title", "")[:40]
```

---

## 10. Log Date Field Not Displaying

**Error:** Log dates showed as "—" even when data existed.

**Root Cause:** The code looked for `logged_at` but the API returns `occurred_at`.

**File Affected:** `cmd_center/screens/tracker_screen.py`

**Fix:** Updated field reference:
```python
# Before
if log.get("logged_at"):
    logged = datetime.fromisoformat(log["logged_at"].replace("Z", ""))

# After
if log.get("occurred_at"):
    occurred = datetime.fromisoformat(log["occurred_at"].replace("Z", ""))
```

---

## 11. Invalid Log Category Filter Option

**Error:** Filtering by "Performance" category returned no results or API error.

**Root Cause:** The filter dropdown included `"performance_review"` which is not a valid API category. Valid categories are: achievement, issue, feedback, milestone, other.

**File Affected:** `cmd_center/screens/tracker_screen.py`

**Fix:** Updated filter options to match API:
```python
# Before
[("Performance", "performance_review")]

# After
[("Milestone", "milestone"), ("Other", "other")]
```

---

## 12. Bonus Creation Not Saving

**Error:** Creating a new bonus did nothing - modal closed but no bonus created.

**Root Cause:** The API's `BonusCreate` schema requires a `promised_date` field, but the frontend wasn't sending it. The API returned a 422 validation error.

**File Affected:** `cmd_center/screens/tracker_screen.py`

**Fix:** Added required fields to the bonus modal:
1. Added `Bonus Type` dropdown (performance, project, annual, other)
2. Added `Promised Date` input field (defaults to today)
3. Updated `_save_bonus()` to include these fields in the API request:
```python
data = {
    "title": title,
    "employee_id": employee_id,
    "amount": amount,
    "currency": currency,
    "bonus_type": bonus_type,      # Added
    "promised_date": promised_date, # Added (required)
}
```

---

## Summary

| Bug | Category | Root Cause |
|-----|----------|------------|
| Team screen empty | API Response Parsing | Paginated response wrapper not handled |
| TaskCreateModal crash | Naming Conflict | Textual built-in `task` property |
| DateTime error | Type Mismatch | Mixing timezone-aware and naive datetimes |
| NoteModal buttons cut off | CSS Sizing | Modal max-height too small |
| LogCreateModal crash | Naming Conflict | Textual built-in `log` property |
| Empty Select crash | Validation Error | Empty Select value invalid |
| Log not saving | Field Mismatch | Wrong field names sent to API |
| Edit not saving | HTTP Method | PATCH vs PUT |
| Log table empty | Field Mismatch | Wrong field name referenced |
| Log dates empty | Field Mismatch | Wrong date field name |
| Log filter broken | Invalid Value | Non-existent category option |
| Bonus not saving | Missing Field | Required `promised_date` not sent |

---

*Last updated: 2025-12-26*
