# Claude Code Project Configuration

## Python Environment

**IMPORTANT:** Always activate the virtual environment before running Python commands:

```bash
source venv/bin/activate
```

This applies to:
- Running tests: `source venv/bin/activate && pytest tests/`
- Running the app: `source venv/bin/activate && python -m cmd_center.main`
- Any Python script execution

## Project Structure

- `cmd_center/` - Main application code
- `tests/` - Test files
- `venv/` - Virtual environment (activate before running Python)

## Common Commands

```bash
# Activate venv first
source venv/bin/activate

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/agent/test_metrics.py -v

# Run the TUI app
python -m cmd_center.main
```
