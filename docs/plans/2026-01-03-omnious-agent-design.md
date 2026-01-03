# Omnious AI Agent Module Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a self-contained AI Agent module called Omnious - a friendly, witty assistant that queries company data, drafts communications, and manages operations with human confirmation for writes.

**Architecture:** ReAct loop with native OpenRouter/OpenAI tool calling. Agent imports existing services, uses streaming responses, and maintains conversation persistence in SQLite.

**Tech Stack:** Python, Textual (TUI), SQLModel, OpenRouter API (OpenAI-compatible), Pydantic

---

## 1. Overall Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentScreen (TUI)                       │
│  - Chat interface, streaming display, status indicators     │
│  - Global key: 'i' to open                                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   OmniousAgent (Core)                       │
│  - ReAct loop orchestration                                 │
│  - Tool dispatch via OpenRouter function calling            │
│  - Confirmation flow state machine for writes               │
└───────┬─────────────────┬─────────────────┬─────────────────┘
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│  ToolRegistry │ │ ConversationStore │ │  Metrics   │
│  - 25+ tools  │ │ - SQLModel tables │ │ - Tokens   │
│  - Schema gen │ │ - Message history │ │ - Cost     │
└───────┬───────┘ └─────────────────┘ └─────────────┘
        │
┌───────▼─────────────────────────────────────────────────────┐
│              Existing Services (imported)                   │
│  deal_health_service, task_service, employee_service, etc.  │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure

```
cmd_center/
├── agent/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py               # Main OmniousAgent class
│   │   ├── prompts.py             # System prompt, persona
│   │   └── context.py             # Conversation context management
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py            # Tool registration, schema generation
│   │   ├── base.py                # Base tool class, PendingAction
│   │   ├── pipeline_tools.py      # Deal/pipeline tools
│   │   ├── email_tools.py         # Email tools
│   │   ├── task_tools.py          # Task/note/reminder tools
│   │   ├── employee_tools.py      # Employee/HR tools
│   │   ├── financial_tools.py     # Cashflow/financial tools
│   │   └── knowledge_tools.py     # Knowledge base lookup
│   │
│   ├── knowledge/
│   │   ├── _index.md              # Navigation for agent
│   │   ├── company_overview.md
│   │   ├── company_structure.md
│   │   ├── employees_rolecard.md
│   │   ├── products_services.md
│   │   ├── procedures.md
│   │   ├── workflows.md
│   │   └── strategy.md
│   │
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── models.py              # AgentConversation, AgentMessage
│   │   └── conversation_store.py
│   │
│   └── observability/
│       ├── __init__.py
│       ├── logger.py              # File logging
│       └── metrics.py             # Token/cost tracking
│
├── screens/
│   └── agent_screen.py            # TUI chat interface
│
└── tests/
    └── agent/
        ├── __init__.py
        ├── test_agent_core.py
        ├── test_tools.py
        ├── test_persistence.py
        └── golden_tests.py
```

---

## 2. Agent Identity: Omnious

**Personality:**
- **Name:** Omnious
- **Self-reference:** "The all-knowing AI" (playful, not arrogant)
- **Tone:** Friendly, witty, professional
- **Style:** Concise but thorough, light humor when appropriate
- **Language:** English only

**Example Responses:**

```
User: "What's happening with our deals?"
Omnious: "Ah, you've come to the right place! The all-knowing Omnious has been
watching your pipeline. Here's what needs your attention today..."

User: "Thanks!"
Omnious: "Always happy to illuminate the path forward. Anything else
you'd like me to dig into?"
```

---

## 3. Core Agent Loop

### OmniousAgent Class

```python
class OmniousAgent:
    def __init__(self):
        self.llm = get_llm_client()
        self.tools = ToolRegistry()
        self.conversation = ConversationContext()
        self.metrics = MetricsTracker()
        self.pending_confirmation: Optional[PendingAction] = None
```

### Main Loop Flow

```
User Message
     │
     ▼
┌─────────────────────────────────────┐
│ 1. Check for pending confirmation   │──► If "yes" → Execute & respond
│    (from previous write request)    │──► If "no/adjust" → Handle
└─────────────────┬───────────────────┘
                  │ No pending action
                  ▼
┌─────────────────────────────────────┐
│ 2. Build messages array             │
│    - System prompt (Omnious persona)│
│    - Conversation history           │
│    - User's new message             │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│ 3. Call OpenRouter with tools       │◄──┐
│    (streaming response)             │   │
└─────────────────┬───────────────────┘   │
                  ▼                       │
┌─────────────────────────────────────┐   │
│ 4. Tool call requested?             │   │
│    YES → Execute tool, loop back ───────┘
│    NO  → Return final response      │
└─────────────────────────────────────┘
```

### Confirmation State Machine

```python
@dataclass
class PendingAction:
    tool_name: str           # "request_create_task"
    preview: str             # Formatted preview for user
    payload: dict            # Data to execute if confirmed
    created_at: datetime
```

Write tools return `PendingAction` instead of executing. User must say "yes" to confirm.

---

## 4. Tool System (OpenRouter/OpenAI Format)

### Tool Schema Format

```python
class ToolRegistry:
    def get_tools_schema(self) -> list[dict]:
        """Convert tools to OpenAI/OpenRouter format"""
        return [{
            "type": "function",
            "function": {
                "name": "get_overdue_deals",
                "description": "Get deals with no recent activity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pipeline": {
                            "type": "string",
                            "description": "Pipeline: 'aramco' or 'commercial'",
                            "enum": ["aramco", "commercial"]
                        },
                        "min_days": {
                            "type": "integer",
                            "description": "Minimum days without activity",
                            "default": 7
                        }
                    },
                    "required": []
                }
            }
        }]
```

### LLM Request/Response

```python
# Request to OpenRouter
{
    "model": "anthropic/claude-sonnet-4",
    "messages": [...],
    "tools": self.tools.get_tools_schema(),
    "tool_choice": "auto"
}

# Response with tool call
{
    "choices": [{
        "message": {
            "role": "assistant",
            "content": null,
            "tool_calls": [{
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "get_overdue_deals",
                    "arguments": "{\"pipeline\": \"aramco\"}"
                }
            }]
        }
    }]
}

# Tool result back to model
messages.append({
    "role": "tool",
    "tool_call_id": "call_abc123",
    "content": json.dumps(tool_result)
})
```

### Pydantic to OpenAI Schema

```python
def pydantic_to_openai_schema(model: type[BaseModel]) -> dict:
    """Convert Pydantic model to OpenAI function parameters"""
    json_schema = model.model_json_schema()
    return {
        "type": "object",
        "properties": json_schema.get("properties", {}),
        "required": json_schema.get("required", [])
    }
```

### Read Tools (Direct Execution)

| Tool Name | Purpose | Source |
|-----------|---------|--------|
| `get_overdue_deals` | Deals with no recent activity | `deal_health_service` |
| `get_stuck_deals` | Deals stuck 30+ days | `deal_health_service` |
| `get_deal_details` | Full deal details | `deal_health_service` |
| `get_deal_notes` | Notes for a deal | `deal_health_service` |
| `search_deals` | Search by keyword | `db_queries` |
| `get_pipeline_summary` | Pipeline status | `ceo_dashboard_service` |
| `get_cashflow_projection` | Revenue forecast | `cashflow_prediction_service` |
| `get_ceo_dashboard` | Executive metrics | `ceo_dashboard_service` |
| `get_employees` | Employee directory | `employee_service` |
| `get_employee_details` | Single employee | `employee_service` |
| `get_employee_skills` | Skill ratings | `skill_service` |
| `get_tasks` | Tasks with filters | `task_service` |
| `get_overdue_tasks` | Past due tasks | `task_service` |
| `get_notes` | Internal notes | `note_service` |
| `get_pending_reminders` | Upcoming reminders | `reminder_service` |
| `get_expiring_documents` | Expiring docs | `document_service` |
| `get_unpaid_bonuses` | Pending bonuses | `bonus_service` |
| `search_emails` | Search emails | `msgraph_email_service` |
| `get_emails` | Get emails | `msgraph_email_service` |
| `get_owner_kpis` | Sales metrics | `owner_kpi_service` |
| `read_knowledge` | Knowledge base | Local markdown files |

### Write Tools (Require Confirmation)

| Tool Name | Purpose |
|-----------|---------|
| `draft_email` | Create email draft (no confirmation) |
| `request_send_email` | Send email (confirmation required) |
| `request_create_task` | Create task (confirmation required) |
| `request_create_note` | Create note (confirmation required) |
| `request_create_reminder` | Create reminder (confirmation required) |
| `request_update_deal` | Update Pipedrive deal (confirmation required) |
| `request_add_deal_note` | Add Pipedrive note (confirmation required) |

---

## 5. TUI Chat Screen

### Screen Structure

```python
class AgentScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("ctrl+l", "clear_chat", "Clear"),
        ("ctrl+s", "save_chat", "Save"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(id="agent-header")           # Token count, cost
        yield ConversationView(id="chat-view")    # Scrollable messages
        yield StatusBar(id="status-bar")          # Ready/Thinking/etc
        yield InputBox(id="input-box")            # User input
```

### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔮 Omnious                                          Tokens: 12,450 │ $0.23 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ You (10:30 AM) ───────────────────────────────────────────────────────┐ │
│  │ What deals need attention today?                                        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ 🔮 Omnious (10:30 AM) ────────────────────────────────── [3 tools] ───┐ │
│  │ Greetings! The all-knowing Omnious has scanned your pipeline...        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ✓ Ready                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  > _                                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Enter Send │ Ctrl+L Clear │ Ctrl+S Save │ Escape Back                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Status Indicators

- `✓ Ready` - Waiting for input
- `🔍 Searching...` - Querying tools
- `🤔 Thinking...` - LLM processing
- `⏳ Waiting for confirmation` - Write pending
- `⚠️ Error (retry 1/3)` - Tool failed
- `❌ Error: [details]` - Failed after retries

### Streaming Implementation

```python
async def send_message(self, user_input: str):
    self.set_status("🤔 Thinking...")

    message_widget = self.add_assistant_message("")

    async for chunk in self.agent.chat_stream(user_input):
        if chunk.type == "text":
            message_widget.append_text(chunk.content)
        elif chunk.type == "tool_call":
            self.set_status(f"🔍 Using {chunk.tool_name}...")
        elif chunk.type == "confirmation_needed":
            self.set_status("⏳ Waiting for confirmation")

    self.set_status("✓ Ready")
```

---

## 6. Persistence & Observability

### Database Tables

```python
class AgentConversation(SQLModel, table=True):
    __tablename__ = "agent_conversation"

    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_message_at: datetime
    title: str = Field(max_length=100)
    total_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    is_archived: bool = Field(default=False)


class AgentMessage(SQLModel, table=True):
    __tablename__ = "agent_message"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="agent_conversation.id", index=True)
    role: str  # "user" | "assistant" | "tool"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tokens_used: int = Field(default=0)
    tools_used: Optional[str] = None  # JSON array
    metadata: Optional[str] = None    # JSON
```

### Metrics Tracking

```python
class MetricsTracker:
    PRICING = {
        "anthropic/claude-sonnet-4": {"input": 3.00, "output": 15.00}  # per 1M tokens
    }

    def track(self, input_tokens: int, output_tokens: int):
        self.session_tokens += input_tokens + output_tokens
        self.session_cost += self._calculate_cost(input_tokens, output_tokens)
```

### Intervention Logging

```python
log_action(
    actor="omnious",
    object_type="agent_tool",
    object_id=0,
    action_type="agent_tool_call",
    summary=f"Called {tool_name}({params})",
    details={"tool": tool_name, "params": params, "result_count": len(result)}
)
```

### File Logging

```
logs/omnious/conversations_2026-01-03.jsonl
```

---

## 7. Scope Boundaries

### Omnious MUST REFUSE:

1. **Delete anything** - No deletions
2. **Make financial commitments** - No approving payments/bonuses
3. **Send emails without confirmation** - Always draft first
4. **Modify data without confirmation** - Always preview first
5. **Access outside defined tools** - No arbitrary execution
6. **Make up information** - Must use tools or knowledge base

### Refusal Style

```
User: "Delete all overdue tasks"
Omnious: "I appreciate the spring cleaning energy, but I'm not authorized to
delete anything. I can help you review the overdue tasks and mark them as
complete one by one if you'd like. Want me to show you the list?"
```

---

## 8. Phased Implementation

### Phase 1: Core Foundation (MVP)

| Component | Files |
|-----------|-------|
| Agent Core | `agent/core/agent.py` |
| Prompts | `agent/core/prompts.py` |
| Tool Base | `agent/tools/base.py`, `registry.py` |
| 6 Read Tools | `get_overdue_deals`, `get_stuck_deals`, `get_deal_details`, `get_deal_notes`, `get_tasks`, `get_employees` |
| Basic TUI | `screens/agent_screen.py` |
| Metrics | `agent/observability/metrics.py` |

**Deliverable:** Chat with Omnious, query deals/tasks, streaming responses.

### Phase 2: Expand Read Capabilities

| Component | Adds |
|-----------|------|
| More tools | Cashflow, emails, skills, KPIs, documents, bonuses |
| Knowledge base | `agent/knowledge/*.md` + `read_knowledge` tool |
| Persistence | DB tables + ConversationStore |

**Deliverable:** Full read access, conversations persist.

### Phase 3: Write Operations

| Component | Adds |
|-----------|------|
| Confirmation flow | PendingAction state machine |
| Write tools | Tasks, notes, emails, deal updates |
| Intervention logging | All confirmed writes logged |

**Deliverable:** Create tasks/notes, send emails with confirmation.

### Phase 4: Polish

| Component | Adds |
|-----------|------|
| File logging | JSONL conversation logs |
| Error handling | Retry logic, graceful failures |
| Context limits | Token counting, soft limit warnings |
| Golden tests | Full Q&A test suite |

---

## 9. Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Orchestration | Native tool use | More reliable than text-based ReAct |
| LLM Provider | OpenRouter | Already configured in codebase |
| Tool format | OpenAI-compatible | Required by OpenRouter |
| Streaming | Yes | Better UX for longer responses |
| Phasing | 4 phases | De-risks, validates architecture early |

---

## 10. Success Criteria

1. ✅ Press `i` opens Omnious chat
2. ✅ Natural language queries get data-backed answers
3. ✅ Agent selects appropriate tools
4. ✅ Write operations require confirmation
5. ✅ Refuses deletions and financial commitments
6. ✅ Conversations persist across restarts
7. ✅ Token/cost displayed in header
8. ✅ Tool calls logged to intervention table
9. ✅ Conversations logged to file
10. ✅ Context resolves pronouns correctly
11. ✅ Errors handled with retries
12. ✅ All tests pass
