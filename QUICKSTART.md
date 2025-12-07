# Quick Start Guide

## Project Created Successfully! ✅

Your Command Center project has been created with the following structure:

```
cmd_center/
├── app.py                         # Main TUI application
├── __init__.py
├── backend/
│   ├── main.py                   # FastAPI server
│   ├── api/                      # 7 API endpoint files
│   ├── models/                   # 5 Pydantic model files
│   ├── services/                 # 6 business logic services
│   └── integrations/             # 4 external client files
└── screens/                       # 6 Textual UI screens
```

## Next Steps

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials:
# - PIPEDRIVE_API_TOKEN
# - OPENROUTER_API_KEY
# - SMTP credentials (for email sending)
```

### 3. Start the Backend API

```bash
# Terminal 1: Run the FastAPI server
python -m cmd_center.backend.main

# The API will start at http://127.0.0.1:8000
# Visit http://127.0.0.1:8000/docs for API documentation
```

### 4. Start the TUI

```bash
# Terminal 2: Run the Textual UI
python -m cmd_center.app

# Use keyboard shortcuts:
# q - Quit
# d - Dashboard
# a - Aramco Pipeline
# c - Commercial Pipeline
# o - Owner KPIs
# e - Email Drafts
```

## Project Architecture

The project follows clean architecture principles:

1. **UI Layer** (`screens/`) - Textual TUI screens
2. **API Layer** (`backend/api/`) - FastAPI endpoints
3. **Service Layer** (`backend/services/`) - Business logic
4. **Integration Layer** (`backend/integrations/`) - External clients
5. **Models** (`backend/models/`) - Pydantic schemas

## Key Features Implemented

✅ Dashboard with priority items  
✅ Aramco pipeline with 5 modes (Overdue, Stuck, Order Received, Compliance, Cashflow)  
✅ Commercial pipeline with inactive deals and LLM summaries  
✅ Owner KPI tracking  
✅ Deal detail view with notes  
✅ Email draft generation and sending  
✅ Full API with 12+ endpoints  
✅ LLM integration via OpenRouter  
✅ Pipedrive integration  
✅ SMTP email sending  

## Testing the System

### 1. Test the API

```bash
# Health check
curl http://127.0.0.1:8000/health

# Get dashboard data
curl http://127.0.0.1:8000/dashboard/today

# Get Aramco overdue deals
curl http://127.0.0.1:8000/aramco/overdue
```

### 2. Test the TUI

1. Launch the app: `python -m cmd_center.app`
2. Press `d` for Dashboard
3. Press `a` for Aramco Pipeline
4. Use `1-5` to switch between modes
5. Press `r` to reload data

## Important Notes

⚠️ **Before Running:**
- You MUST configure `.env` with valid credentials
- Pipedrive API token is required for deal data
- OpenRouter API key is required for LLM features
- SMTP credentials are required for email sending

📝 **Development Mode:**
- FastAPI runs with auto-reload enabled
- Changes to backend code will auto-restart the server
- TUI changes require manual restart

## Troubleshooting

**API won't start?**
- Check that port 8000 is not in use
- Verify `.env` file exists and has valid values

**TUI shows errors?**
- Ensure the API is running first
- Check API_URL in the app (default: http://127.0.0.1:8000)

**No data showing?**
- Verify Pipedrive credentials
- Check that you have deals in your pipelines
- Review API logs for errors

## Documentation

- [`README.md`](README.md) - Full documentation
- [`Architecture.md`](Architecture.md) - System architecture
- [`models_schema.md`](models_schema.md) - Data models
- [`design_tui.md`](design_tui.md) - TUI design specification

## Support

For detailed information, see the documentation files mentioned above.

---

**Happy coding! 🚀**