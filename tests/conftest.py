"""Shared pytest fixtures for CEO Dashboard tests.

This module provides:
- In-memory SQLite database fixtures for test isolation
- Database session management
- FastAPI test client with database override
- Helper fixtures for creating test data
"""

import pytest
import pytest_asyncio
from typing import Generator, AsyncGenerator
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_engine():
    """Create an in-memory SQLite engine for test isolation.

    Each test function gets a fresh database with all tables created.
    The engine is disposed after the test completes.
    """
    # Import all models to ensure they're registered with SQLModel.metadata
    # before creating tables. This must happen before create_all().
    from cmd_center.backend import db  # noqa: F401 - imports all models

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Required for in-memory SQLite with multiple connections
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine) -> Generator[Session, None, None]:
    """Provide a database session for unit tests.

    The session is bound to the in-memory test engine and is
    automatically closed after the test completes.
    """
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="function")
def override_db(test_engine):
    """Override the production db.engine with test engine.

    This fixture patches cmd_center.backend.db.engine so that
    all services and queries use the in-memory test database.

    Usage:
        def test_something(override_db):
            # All database operations now use in-memory SQLite
            service = get_employee_service()
            result = service.create_employee(...)
    """
    from cmd_center.backend import db
    original_engine = db.engine
    db.engine = test_engine
    yield test_engine
    db.engine = original_engine


# ============================================================================
# API Test Client Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def test_client(override_db) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for API integration tests.

    Uses httpx with ASGI transport to make in-process requests
    to the FastAPI application. The database is already overridden
    via the override_db dependency.

    Usage:
        @pytest.mark.asyncio
        async def test_create_employee(test_client):
            response = await test_client.post("/employees", json={...})
            assert response.status_code == 201
    """
    from cmd_center.backend.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================================
# Helper Fixtures for Test Data
# ============================================================================

@pytest.fixture
def sample_employee_data():
    """Sample employee data for testing."""
    return {
        "full_name": "John Doe",
        "role_title": "Software Engineer",
        "department": "Engineering",
        "email": "john.doe@example.com",
        "phone": "+966501234567",
        "is_active": True,
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    from datetime import datetime, timedelta
    return {
        "title": "Follow up with client",
        "description": "Review proposal and schedule meeting",
        "priority": "high",
        "due_at": (datetime.utcnow() + timedelta(days=3)).isoformat(),
        "target_type": "deal",
        "target_id": 123,
    }


@pytest.fixture
def sample_note_data():
    """Sample internal note data for testing."""
    return {
        "content": "Important note about this deal",
        "target_type": "deal",
        "target_id": 123,
        "pinned": False,
        "tags": "important,followup",
    }


@pytest.fixture
def sample_reminder_data():
    """Sample reminder data for testing."""
    from datetime import datetime, timedelta
    return {
        "target_type": "task",
        "target_id": 1,
        "remind_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "channel": "email",
        "message": "Task due tomorrow",
    }


@pytest.fixture
def sample_document_data():
    """Sample legal document data for testing."""
    from datetime import datetime, timedelta
    return {
        "title": "Commercial Registration",
        "document_type": "CR",
        "issue_date": datetime.utcnow().isoformat(),
        "expiry_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "status": "active",
        "reference_number": "CR-2024-001",
    }


# ============================================================================
# Service Reset Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_service_singletons():
    """Reset service singletons between tests.

    This ensures each test gets fresh service instances,
    preventing state leakage between tests.
    """
    yield

    # Reset any service singletons here after test completes
    # Example (add actual service modules as they're created):
    # from cmd_center.backend.services import employee_service
    # employee_service._employee_service = None


# ============================================================================
# Async Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for async tests."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
