# Command Center

A keyboard-driven TUI (Text User Interface) command center for sales and project management, built with FastAPI and Textual.

## Architecture

This project follows a clean architecture pattern with clear separation of concerns:

- **UI Layer**: Textual-based TUI (`cmd_center/screens/`)
- **API Layer**: FastAPI REST endpoints (`cmd_center/backend/api/`)
- **Service Layer**: Business logic (`cmd_center/backend/services/`)
- **Integration Layer**: External service clients (`cmd_center/backend/integrations/`)
- **Models**: Pydantic data models (`cmd_center/backend/models/`)

## Features

### Pipelines
- **Aramco Projects**: Specialized tracking for Aramco deals
- **Commercial Pipeline**: General commercial opportunities

### Screens
1. **Dashboard** - Today's focus with priority items
2. **Aramco Pipeline** - Multi-mode analysis (Overdue, Stuck, Order Received, Compliance, Cashflow)
3. **Commercial Pipeline** - Inactive deals and LLM summaries
4. **Owner KPIs** - Salesperson performance metrics
5. **Deal Detail** - Deep dive into individual deals
6. **Email Drafts** - LLM-generated follow-up emails

### Key Capabilities
- Real-time deal health monitoring
- LLM-powered analysis (via OpenRouter)
- Cashflow projection
- Owner/salesperson KPI tracking
- Automated follow-up email generation
- Compliance checking

## Installation

1. Clone the repository:
```bash
cd command_center
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

## Configuration

Edit `.env` file with your credentials:

- **Pipedrive**: API token from Pipedrive settings
- **OpenRouter**: API key for LLM access
- **SMTP**: Email server credentials for sending follow-ups

## Usage

### Running the Backend API

Start the FastAPI server:

```bash
python -m cmd_center.backend.main
```

Or using uvicorn directly:

```bash
uvicorn cmd_center.backend.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### Running the TUI

In a separate terminal, start the Textual UI:

```bash
python -m cmd_center.app
```

Or:

```bash
python cmd_center/app.py
```

## Keyboard Shortcuts

### Global (available in all screens)
- `q` - Quit application
- `d` - Dashboard screen
- `a` - Aramco pipeline screen
- `c` - Commercial pipeline screen
- `o` - Owner KPIs screen
- `e` - Email drafts screen

### Screen-specific
- **Aramco Pipeline**: `1-5` - Switch modes, `r` - Reload
- **Commercial Pipeline**: `1-2` - Switch modes, `r` - Reload
- **Deal Detail**: `b` - Back, `e` - Add to email
- **Email Drafts**: `s` - Send, `r` - Regenerate, `b` - Back

## Project Structure

```
cmd_center/
├── app.py                    # Main TUI application
├── __init__.py
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── api/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── dashboard.py
│   │   ├── aramco.py
│   │   ├── commercial.py
│   │   ├── owners.py
│   │   ├── deals.py
│   │   └── emails.py
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   ├── deal_models.py
│   │   ├── cashflow_models.py
│   │   ├── kpi_models.py
│   │   ├── dashboard_models.py
│   │   └── email_models.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── deal_health_service.py
│   │   ├── llm_analysis_service.py
│   │   ├── cashflow_service.py
│   │   ├── owner_kpi_service.py
│   │   ├── email_service.py
│   │   └── dashboard_service.py
│   └── integrations/        # External clients
│       ├── __init__.py
│       ├── config.py
│       ├── pipedrive_client.py
│       ├── llm_client.py
│       └── email_client.py
└── screens/                 # Textual UI screens
    ├── __init__.py
    ├── dashboard_screen.py
    ├── aramco_screen.py
    ├── commercial_screen.py
    ├── owner_kpi_screen.py
    ├── deal_detail_screen.py
    └── email_drafts_screen.py
```

## API Endpoints

- `GET /health` - Health check
- `GET /dashboard/today` - Today's dashboard items
- `GET /aramco/overdue` - Overdue Aramco deals
- `GET /aramco/stuck` - Stuck Aramco deals
- `GET /aramco/order_received` - Order received analysis
- `GET /aramco/compliance` - Compliance status
- `GET /aramco/cashflow_projection` - Cashflow projection
- `GET /commercial/inactive` - Inactive commercial deals
- `GET /commercial/recent_summary` - Recent deal summaries
- `GET /owners/kpis` - Owner KPIs
- `GET /deals/{id}/detail` - Deal details
- `GET /deals/{id}/notes` - Deal notes
- `POST /emails/followups/generate` - Generate follow-up emails
- `POST /emails/followups/send` - Send follow-up emails

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines. Use `black` for formatting:

```bash
black cmd_center/
```

## Documentation

For detailed documentation, see:
- [`Architecture.md`](Architecture.md) - System architecture
- [`models_schema.md`](models_schema.md) - Data models
- [`design_tui.md`](design_tui.md) - TUI design specification

## Tech Stack

- **Python 3.10+**
- **FastAPI** - Modern web framework for APIs
- **Textual** - TUI framework
- **Pydantic** - Data validation
- **httpx** - Async HTTP client
- **Pipedrive API** - CRM integration
- **OpenRouter** - LLM access

## License

[Your License Here]

## Contributing

[Contributing guidelines here]

## Support

For issues and questions, please open an issue on GitHub.