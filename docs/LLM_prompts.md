# LLM_Prompts.md
Command Center LLM Prompt Specification (for LLMs)

> ⚠️ IMPORTANT FOR LLMS  
> - This file defines **how to talk to the LLM provider (OpenRouter)**.  
> - Use these templates in `llm_analysis_service.py` and `email_service.py`.  
> - Always request **structured JSON** when a function returns data, and validate against the Pydantic models from `Models_and_Schema.md`.

The goals of these prompts:

1. Keep outputs **predictable and parseable**.
2. Minimize hallucinations by:
   - Repeating constraints clearly.
   - Asking for `"unknown"` / `null` when unsure.
3. Stay aligned with business context (Aramco projects, pipelines, sales workflow).

---

## 0. General Prompting Guidelines

### 0.1 Style

- System/intro text should:
  - Explain the domain briefly: Pipedrive deals, Aramco projects, commercial pipeline.
  - Ask for **short, factual answers**.
- Use **explicit JSON** format in the last instruction.
- For analysis tasks, we always pass:
  - Deal notes as text.
  - Optional metadata (stage, pipeline, etc.).

### 0.2 JSON Output Rule

For JSON-based functions:

- End your prompt with something like:

> Return ONLY a valid JSON object with this exact schema:  
> ```json
> { ... }
> ```

- Do **not** include commentary, explanations, or markdown code fences in the LLM response.

In `llm_client.complete_json`, we enforce this by:

1. Extracting JSON.
2. Validating with Pydantic schema.
3. Retrying or raising errors.

---

## 1. detect_sdd_requested(notes) → bool

### 1.1 Purpose

Determine if the **SDD (Statistical Delivery Date)** has been requested in the deal’s notes.

### 1.2 Schema

Return a JSON object like:

```json
{
  "sdd_requested": true
}
```

### 1.3 Prompt Template (pseudo-code)

```text
You are an assistant analyzing sales notes for construction/fitout projects.

The notes below come from a CRM (Pipedrive) for a single deal.
Your job is to determine if the salesperson has requested an SDD (Statistical Delivery Date) from the client or any stakeholder.

Consider that:
- SDD might be referred to explicitly as "SDD".
- It might also be described as "requested delivery date", "promised delivery schedule", "official delivery date from client", etc.

If you are not sure, treat it as NOT requested.

NOTES (chronological, most recent last):
---
{{NOTES_TEXT}}
---

Return ONLY a JSON object with this exact schema:

{
  "sdd_requested": true or false
}
```

In code, `{{NOTES_TEXT}}` is built by concatenating `DealNote` entries:

```text
[2025-11-10] Faris: Asked client for SDD for the materials.
[2025-11-15] Faris: Waiting for confirmation on delivery date.
```

---

## 2. analyze_order_received(notes) → (end_user_identified, end_user_requests_count)

### 2.1 Purpose

For deals in **"Order received"** stage, answer:

1. Has the **end user** been identified?
2. How many times has the salesperson requested the end user?

### 2.2 Schema

```json
{
  "end_user_identified": true,
  "end_user_requests_count": 3
}
```

Where:

- `end_user_identified` is `true`, `false`, or `null` (if unclear).
- `end_user_requests_count` is an integer OR `null` if you cannot estimate.

### 2.3 Prompt Template

```text
You are analyzing sales notes for industrial projects that supply and install products for Aramco and commercial clients.

The "end user" refers to the person or department at the final client (e.g. Aramco engineer, facility manager) who will approve or coordinate the actual work.

Your tasks:

1. Decide if the end user has been identified.
   - Examples of YES:
     - "We got the Aramco end user name and phone."
     - "End user is Eng. Ahmed from Aramco."
   - Examples of NO:
     - "Still trying to reach end user."
     - "Waiting for end user contact from contractor."
   - If it's impossible to tell, use null.

2. Estimate how many times the salesperson requested the end user contact.
   - Count explicit attempts like:
     - "asked contractor to share end user contact"
     - "followed up for end user details"
     - "requested end user information again"

Provide your best estimate based on the notes.

NOTES (chronological, most recent last):
---
{{NOTES_TEXT}}
---

Return ONLY a JSON object with this exact schema:

{
  "end_user_identified": true or false or null,
  "end_user_requests_count": integer or null
}
```

---

## 3. check_compliance(notes, stage) → ComplianceStatus

### 3.1 Purpose

Check if **survey checklists** and **quality inspection documents** exist, depending on the stage:

- After materials are purchased → Survey checklist should exist.
- After MDD (Material Delivery Document) is signed → Quality inspection docs should exist.

The LLM only infers from notes; it does **not** access files.

### 3.2 Schema

```json
{
  "survey_checklist_present": true,
  "quality_docs_present": false,
  "comment": "Missing quality inspection docs after MDD signed."
}
```

Values can be `true`, `false`, or `null` if unclear.

### 3.3 Prompt Template

```text
You are checking compliance for Aramco-related projects based on CRM notes.

The deal is currently in stage: "{{STAGE}}".

We care about two items:
1. Survey checklist (site survey, inspection checklist)
2. Quality inspection documents (post-installation or post-MDD quality forms, inspection reports)

Rules of thumb:
- After materials are purchased or delivered, there should be a survey checklist.
- After MDD (Material Delivery Document) is signed or GR is expected, there should be quality inspection documents.

From the notes, decide:
- Does it clearly indicate that a survey checklist exists?
- Does it clearly indicate that quality inspection docs exist?
- If you're not sure, return null for that field.

NOTES:
---
{{NOTES_TEXT}}
---

Return ONLY a JSON object with this exact schema:

{
  "survey_checklist_present": true or false or null,
  "quality_docs_present": true or false or null,
  "comment": "short explanation, mention what's missing or unclear"
}
```

---

## 4. summarize_recent_activity(notes) → (summary, next_action)

### 4.1 Purpose

For recent commercial deals, produce:

- A concise status summary.
- A clear recommended next action.

### 4.2 Schema

```json
{
  "summary": "Client reviewing revised quotation; they want a discount on accessories.",
  "next_action": "Call client this week to confirm decision and push for closing."
}
```

### 4.3 Prompt Template

```text
You are summarizing the status of a sales deal based on CRM notes.

Write:
1. A short, clear summary (1–2 sentences) of the current status.
2. A concrete next action for the salesperson (1 sentence).

Avoid long history. Focus on:
- Where things stand now.
- What should happen next.

NOTES (most recent last):
---
{{NOTES_TEXT}}
---

Return ONLY a JSON object with this exact schema:

{
  "summary": "one or two sentences about the current status",
  "next_action": "one sentence with a clear recommended next step, or null if not applicable"
}
```

If truly no next action can be inferred, set `"next_action": null`.

---

## 5. build_email_body_for_owner(owner, issues) → str

### 5.1 Purpose

Generate a **professional follow-up email** for a salesperson, summarizing their deals and what they should do next.

Each `DealIssue` contains:

- `title`
- `pipeline`
- `stage`
- `issue_summary`
- `next_action` (optional)

### 5.2 Output Style

- E-mail body as **plain text** (or very simple markdown).
- Friendly but direct.
- Bullet list per deal with:
  - Deal name
  - Key issue
  - Next action

No JSON needed here.

### 5.3 Prompt Template

```text
You are an assistant helping a sales manager write follow-up emails to salespeople.

The email is sent FROM the manager TO the salesperson.

Write an email to the following salesperson:

Salesperson: {{OWNER_NAME}}

Purpose:
- Remind them about important deals that need action.
- Be clear, respectful, and action-oriented.
- The manager wants to keep it short and to the point.

For each deal, include:
- Deal title
- Pipeline (e.g. Aramco Projects, Commercial)
- Stage
- The key issue summary
- The recommended next action

Tone:
- Professional but friendly.
- No blame, just clear expectations.
- Encourage quick follow-up.

Deal issues:
---
{{DEAL_ISSUES_LIST}}
---

Where each issue line looks like:
- Title: ...
  Pipeline: ...
  Stage: ...
  Issue: ...
  Next action: ...

Write the email body ONLY (no subject, no greeting metadata).
Include:
- Greeting (e.g. "Dear Faris,")
- Short intro sentence.
- Bullet list of deals with issues and actions.
- Short closing (e.g. "Thanks" or "Let me know if you need support.").

Do NOT return JSON. Return plain text only.
```

The `email_service` will handle subject lines and wrapping, this function focuses on the **body** only.

---

## 6. Optional: summarize_deal_for_dashboard

### 6.1 Purpose

Short one-line summary for dashboard flags (optional helper if needed).

### 6.2 Schema

```json
{
  "one_liner": "Overdue 10 days; waiting for client confirmation on revised BOQ."
}
```

### 6.3 Prompt Template

```text
You are creating a one-line comment for a CRM dashboard.

Goal:
- Summarize the main issue with this deal in ONE sentence.
- Focus on why it is on the dashboard (overdue, stuck, missing documents, etc.).
- Max 140 characters.

Deal context:
- Title: {{DEAL_TITLE}}
- Stage: {{STAGE}}
- Pipeline: {{PIPELINE}}
- Type: {{TYPE}}  (overdue | stuck | compliance | cashflow)

Relevant notes:
---
{{NOTES_TEXT}}
---

Return ONLY a JSON object with this exact schema:

{
  "one_liner": "short sentence describing the situation in max 140 characters"
}
```

---

## 7. predict_cashflow_dates(deals) → CashflowPredictionResult

### 7.1 Purpose

Predict invoice and payment dates for deals using comprehensive construction/interior design industry rules. This function powers the cashflow forecasting feature.

### 7.2 Schema

```json
{
  "predictions": [
    {
      "deal_id": 123,
      "deal_title": "ARAMCO - Baffle Ceiling Installation",
      "predicted_invoice_date": "2025-02-15",
      "predicted_payment_date": "2025-02-22",
      "confidence": 0.75,
      "assumptions": [
        "Project is 200 SQM baffle ceiling",
        "Production at 35 SQM/day with 1 team = 6 days",
        "Using realistic stage duration estimates"
      ],
      "missing_fields": ["exact SQM from deal notes"],
      "reasoning": "Deal at Under Progress stage with 5 days elapsed. Estimated 6 days production + 12 days post-production = 18 days to invoice."
    }
  ]
}
```

### 7.3 Comprehensive Prediction Rules

The LLM uses a detailed ruleset based on:

**Project Lifecycle Stages:**
1. Order Received (OR)
2. Approved (APR)
3. Awaiting Payment (AP)
4. Awaiting Site Readiness (ASR) / Everything Ready (ER)
5. Under Progress (UP)
6. Awaiting MDD
7. Awaiting GCC
8. Awaiting GR
9. Invoice Issued
10. Payment Received

**Stage Duration Reference (Realistic Estimates):**
| Stage | Days to Invoice |
|---|---|
| Order Received (< 100 SQM) | 36 days + production |
| Order Received (100-400 SQM) | 42 days + production |
| Order Received (> 400 SQM) | 50 days + production |
| Approved | 29 days + production |
| Awaiting Payment | 27 days + production |
| Awaiting Site Readiness | 22 days + production |
| Everything Ready | 17 days + production |
| Under Progress | 12 days + remaining production |
| Awaiting MDD | 12 days |
| Awaiting GCC | 10 days |
| Awaiting GR | 7 days |

**Production Capacity:**
- Baffle Ceiling: 35 SQM/day per 4-worker team
- Ceiling Tiles: 35 SQM/day per 3-worker team
- Carpet: 50 SQM/day per worker

**Payment Terms:**
- Aramco: Upon invoice
- Commercial: 30-60 days after invoice

### 7.4 Prompt Template Reference

See `prompt_registry.py` → `cashflow.predict_dates.v1` for the full prompt.

The system prompt includes:
- Company profile and workforce capacity
- Complete stage duration tables
- Production capacity formulas
- Risk factor adjustments
- Payment terms by client type

### 7.5 Implementation Notes

- Deterministic rules have been disabled in favor of LLM-based prediction
- The LLM applies the comprehensive ruleset directly
- Uses `model_tier="advanced"` for better reasoning
- Temperature set to 0.3 for consistency
- Max tokens: 4000 (to handle multiple deals)

---

## 8. Implementation Notes for Services

When implementing `llm_analysis_service.py` or `cashflow_prediction_service.py`:

- **Do not hardcode prompts everywhere.**  
  - Keep them as multiline strings or small helper functions that mirror the above templates.
- Always:
  - Pass **only the necessary text** (notes, stage, owner).
  - Validate structured responses with Pydantic models when expecting JSON.
- For any new LLM function:
  - Add a section to this file (`LLM_Prompts.md`) first.
  - Then implement the function using that spec.

---

End of LLM_Prompts.md
