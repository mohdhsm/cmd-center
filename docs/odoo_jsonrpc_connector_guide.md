# Odoo 17 (Odoo.sh) JSON-RPC Connector Guide

This guide is written so an LLM (or a developer) can implement an **Odoo JSON-RPC** connector (Odoo 17, Odoo.sh) in an application (e.g., FastAPI).
It focuses on:

- How Odoo JSON-RPC works (`/jsonrpc`)
- How to authenticate and call model methods
- Where to put **domain filters**, **fields**, and pagination parameters
- What the **response schema** looks like (success + error)
- Practical patterns (search, read, create, write, unlink)

The odoo information are all in enviroment variables as follow:
1. ODOO_URL
2. ODOO_Db
3. ODOO_USER
4. ODOO_SECRET


## 1) Endpoint and Transport

- **Endpoint:** `POST https://<your-odoo-host>/jsonrpc`
- **Content-Type:** `application/json`
- **Protocol:** JSON-RPC 2.0

All operations (login + model calls) are JSON POSTs to the same endpoint.

---

## 2) JSON-RPC Envelope (Top-Level Schema)

Every request body has this shape:

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": { ... },
  "id": 1
}
```

### Response (Success)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": <any>
}
```

### Response (Error)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": 200,
    "message": "Odoo Server Error",
    "data": {
      "name": "<ExceptionClass>",
      "message": "<Human readable>",
      "debug": "<stack trace>",
      "arguments": ["..."],
      "context": { }
    }
  }
}
```

**Connector rule:** If `error` exists, treat it as failure and surface a clean message (log `debug` internally only).

---

## 3) Authentication (Get `uid`)

Odoo’s JSON-RPC uses the **“common”** service for authentication.

### 3.1 Login call

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "common",
    "method": "login",
    "args": ["<DB_NAME>", "<USERNAME>", "<PASSWORD_OR_API_KEY>"]
  },
  "id": 1
}
```

- `result` is an integer **uid**.
- If login fails, `result` can be `false` (or an error).

**API key usage:** For RPC, an API key works like a password — pass it in the password slot.

### 3.2 Suggested connector state

Store:

- `db` (string)
- `uid` (int)
- `secret` (API key/password string)
- `base_url` (host)
- optional: `last_login_ts`

---

## 4) Model Calls (ORM via `object.execute`)

Odoo exposes its ORM through the **“object”** service using `execute`.

### 4.1 Generic call template

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "<DB_NAME>",
      <UID>,
      "<PASSWORD_OR_API_KEY>",
      "<model.name>",
      "<method_name>",
      ...method_args
    ]
  },
  "id": 2
}
```

- `model.name` examples: `account.move`, `purchase.order`, `stock.picking`, `sale.order`
- `method_name` examples: `search`, `read`, `search_read`, `create`, `write`, `unlink`, `fields_get`

---

## 5) Domains (Filtering / WHERE clause)

Odoo uses a **domain** list to filter records.

### 5.1 Domain schema

A domain is a list of **tokens**. Most commonly, it is a list of triplets:

```json
[
  ["field", "operator", "value"],
  ["other_field", "operator", "value"]
]
```

Examples:

- Equals: `["state", "=", "posted"]`
- Not equals: `["state", "!=", "cancel"]`
- In list: `["state", "in", ["sale", "done"]]`
- Contains (case-insensitive for text): `["name", "ilike", "INV/2025"]`
- Comparisons: `["invoice_date", ">=", "2025-01-01"]`

### 5.2 AND / OR / NOT

- **AND** is implicit when you provide multiple triplets in a list.
- **OR** uses the prefix operator `"|"`:
  ```json
  ["|", ["state","=","draft"], ["state","=","sent"]]
  ```
- **NOT** uses `"!"`:
  ```json
  ["!", ["state","=","cancel"]]
  ```

### 5.3 Common domain mistakes (causes server IndexError)

- ✅ Correct: `[["field","=","x"]]`
- ❌ Wrong (extra nesting): `[[["field","=","x"]]]`

If you see errors like `tuple index out of range`, inspect domain brackets first.

---

## 6) Fields (Selecting Columns)

Many methods accept a **fields list** which controls which columns are returned.

Example fields list:

```json
["id", "name", "invoice_date", "amount_total"]
```

### 6.1 Where fields go?

There are two common patterns:

#### Pattern A: `search_read(domain, fields, offset, limit, order)`
In JSON-RPC with `object.execute`, `fields` is typically **the next positional argument after domain**:

```json
"args": [
  "DB", UID, "SECRET",
  "account.move", "search_read",
  [["move_type","=","out_invoice"]],
  ["id","name","amount_total"],
  0,
  20,
  "invoice_date desc"
]
```

#### Pattern B: `read(ids, fields)`
```json
"args": [
  "DB", UID, "SECRET",
  "sale.order", "read",
  [[123, 124]],
  ["id","name","partner_id","amount_total"]
]
```

**Connector rule:** Use the positional-argument style first. It is consistent and avoids confusion.

---

## 7) Pagination and Ordering

Most list methods accept:

- `offset` (int) — start index
- `limit` (int) — page size
- `order` (string) — e.g., `"date desc"` or `"name asc"`

Example:

```json
...,
["id","name"],
0,
50,
"date desc"
```

### 7.1 Recommended pagination loop (pseudo)

- Start `offset = 0`
- Fetch `limit = 200` (or your safe size)
- Stop when returned list length `< limit`
- Increment `offset += limit`

---

## 8) What Comes Back (Record Schemas)

### 8.1 `search_read` result shape

`result` is a list of dicts:

```json
{
  "result": [
    {
      "id": 10,
      "name": "INV/2025/0012",
      "partner_id": [7, "ACME Co."],
      "amount_total": 1500.0
    }
  ]
}
```

### 8.2 Common field types in responses

- **primitive:** `string`, `number`, `boolean`
- **date/datetime:** ISO-ish strings like `"2025-12-26"` or `"2025-12-26 14:30:00"` (timezone depends on server/user)
- **many2one:** typically `[id, display_name]`
  - example: `"partner_id": [7, "ACME Co."]`
- **one2many / many2many:** typically a list of integer IDs (unless you explicitly read related fields)
  - example: `"invoice_line_ids": [101, 102, 103]`

### 8.3 `search` result shape
`result` is a list of IDs:
```json
{ "result": [10, 11, 12] }
```

---

## 9) Core Method Recipes (Copy/Paste JSON Bodies)

Below bodies assume Postman env vars or templating:
- `{{odoo_db}}`, `{{odoo_uid}}`, `{{odoo_secret}}`

### 9.1 Accounts: Customer invoices (posted)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "account.move",
      "search_read",
      [["move_type","=","out_invoice"],["state","=","posted"]],
      ["id","name","invoice_date","partner_id","amount_total","amount_residual","payment_state"],
      0,
      20,
      "invoice_date desc"
    ]
  },
  "id": 101
}
```

### 9.2 Accounts: Vendor bills (posted)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "account.move",
      "search_read",
      [["move_type","=","in_invoice"],["state","=","posted"]],
      ["id","name","invoice_date","partner_id","amount_total","amount_residual","payment_state"],
      0,
      20,
      "invoice_date desc"
    ]
  },
  "id": 102
}
```

### 9.3 Sales: Sales orders

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "sale.order",
      "search_read",
      [["state","in",["sale","done"]]],
      ["id","name","partner_id","date_order","amount_total","invoice_status","user_id"],
      0,
      20,
      "date_order desc"
    ]
  },
  "id": 201
}
```

### 9.4 Purchasing: Purchase orders

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "purchase.order",
      "search_read",
      [["state","in",["purchase","done"]]],
      ["id","name","partner_id","date_order","amount_total","invoice_status","user_id"],
      0,
      20,
      "date_order desc"
    ]
  },
  "id": 301
}
```

### 9.5 Inventory: Pickings (outgoing)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "stock.picking",
      "search_read",
      [["picking_type_code","=","outgoing"]],
      ["id","name","origin","state","scheduled_date","date_done","partner_id"],
      0,
      20,
      "scheduled_date desc"
    ]
  },
  "id": 401
}
```

### 9.6 Inventory: On-hand (quants)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "stock.quant",
      "search_read",
      [["quantity",">",0]],
      ["id","product_id","location_id","quantity","reserved_quantity"],
      0,
      50,
      "quantity desc"
    ]
  },
  "id": 402
}
```

---

## 10) Introspection (Discover Models and Fields)

### 10.1 List field metadata (`fields_get`)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "account.move",
      "fields_get",
      [],
      {"attributes":["string","type","required","readonly","relation"]}
    ]
  },
  "id": 900
}
```

This returns a dict keyed by field name. Each field contains metadata (label, type, relation, etc.).
Use this to help an LLM auto-generate typed models or validate fields.

---

## 11) Write Operations

### 11.1 Create a record
Example: create a partner (minimal fields vary by config)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "res.partner",
      "create",
      [{"name":"Test Partner","email":"test@example.com"}]
    ]
  },
  "id": 1001
}
```

**Result:** new record ID (int).

### 11.2 Write (update)
Example: update partner 7

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "res.partner",
      "write",
      [[7], {"phone":"+966500000000"}]
    ]
  },
  "id": 1002
}
```

**Result:** boolean `true/false`.

### 11.3 Unlink (delete)
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "{{odoo_db}}",
      {{odoo_uid}},
      "{{odoo_secret}}",
      "res.partner",
      "unlink",
      [[7]]
    ]
  },
  "id": 1003
}
```

---

## 12) Connector Implementation Notes (FastAPI / Python)

### 12.1 Recommended API surface (LLM-friendly)

Implement these core functions:

- `login() -> uid`
- `call(service, method, args) -> result`
- `execute(model, method, *method_args) -> result`
- Convenience:
  - `search(model, domain, offset=0, limit=100, order=None) -> list[int]`
  - `read(model, ids, fields=None) -> list[dict]`
  - `search_read(model, domain, fields, offset=0, limit=100, order=None) -> list[dict]`
  - `create(model, values) -> int`
  - `write(model, ids, values) -> bool`

### 12.2 HTTP client behavior

- Use a persistent HTTP session (keep-alive).
- Add timeouts (connect + read).
- Retry on transient network errors and 502/503/504 (with backoff).
- Do **not** retry on permission errors / validation errors.

### 12.3 Error normalization

From the JSON-RPC error payload:

- `error.message`: coarse message ("Odoo Server Error")
- `error.data.name`: exception type (`AccessError`, `ValidationError`, etc.)
- `error.data.message`: better human message
- `error.data.debug`: stack trace (log only)

Return a normalized error object in your app.

---

## 13) Typical “Exploration” Workflow

1) `common.login` to get `uid`
2) `fields_get` on a model to discover fields
3) `search_read` with a simple domain to verify permissions + shape
4) Add filters (`domain`) and fields incrementally
5) Implement pagination for big models

---

## 14) Minimal Postman Environment Variables

- `odoo_base_url`: `https://<your-host>`
- `odoo_db`: your DB name
- `odoo_username`: user login/email
- `odoo_secret`: API key or password
- `odoo_uid`: set after login

---

## 15) Quick Reference: Common Models

- **Accounting**
  - `account.move` (invoices/bills)
  - `account.move.line` (journal items)
- **Sales**
  - `sale.order`, `sale.order.line`
- **Purchasing**
  - `purchase.order`, `purchase.order.line`
- **Inventory**
  - `stock.picking`, `stock.move`, `stock.move.line`, `stock.quant`

---

## 16) Schema Summary (for an LLM)

### Request
- JSON-RPC envelope with:
  - `jsonrpc="2.0"`
  - `method="call"`
  - `params={service, method, args}`
  - `id=<int>`

### Login
- `params.service="common"`
- `params.method="login"`
- `params.args=[db, username, secret]`
- `result=<uid:int>`

### Model execute
- `params.service="object"`
- `params.method="execute"`
- `params.args=[db, uid, secret, model, method, ...method_args]`

### `search_read`
- `method_args = [domain, fields, offset?, limit?, order?]`
- `domain = [[field, op, value], ...]`
- `fields = ["id", "..."]`
- `result = [ {field: value, ...}, ... ]`

### Errors
- `error.code`, `error.message`, `error.data.{name,message,debug,arguments,context}`

---

If you want, I can also generate:
- a **typed Pydantic schema** for common return shapes (many2one, date/datetime, etc.)
- a **FastAPI-ready Python connector module** with retries, timeouts, and methods above.
