"""Verify pytest fixtures work correctly."""

import pytest
from sqlmodel import Session, select

from cmd_center.backend.db import Deal, Pipeline, Stage


class TestDatabaseFixtures:
    """Test that database fixtures provide proper isolation."""

    def test_engine_creates_tables(self, test_engine):
        """In-memory engine should have all tables created."""
        # Check tables exist by querying
        with Session(test_engine) as session:
            # This should not raise - tables exist
            result = session.exec(select(Pipeline)).all()
            assert result == []  # Empty, but queryable

    def test_session_is_isolated(self, test_session):
        """Each test gets a fresh session with empty tables."""
        # Insert a test pipeline
        pipeline = Pipeline(id=1, name="Test Pipeline", order_nr=1)
        test_session.add(pipeline)
        test_session.commit()

        # Verify it was inserted
        result = test_session.exec(select(Pipeline)).all()
        assert len(result) == 1
        assert result[0].name == "Test Pipeline"

    def test_session_isolation_between_tests(self, test_session):
        """This test should have empty tables (no data from previous test)."""
        result = test_session.exec(select(Pipeline)).all()
        assert len(result) == 0, "Database should be empty - fixture isolation failed"

    def test_override_db_patches_engine(self, override_db):
        """The override_db fixture should patch db.engine."""
        from cmd_center.backend import db

        # After override, db.engine should be our test engine
        assert db.engine is override_db
        assert "memory" in str(db.engine.url)


class TestSampleDataFixtures:
    """Test that sample data fixtures provide valid data."""

    def test_sample_employee_data(self, sample_employee_data):
        """Sample employee data should have required fields."""
        assert "full_name" in sample_employee_data
        assert "role_title" in sample_employee_data
        assert sample_employee_data["is_active"] is True

    def test_sample_task_data(self, sample_task_data):
        """Sample task data should have required fields."""
        assert "title" in sample_task_data
        assert "priority" in sample_task_data
        assert sample_task_data["target_type"] == "deal"

    def test_sample_reminder_data(self, sample_reminder_data):
        """Sample reminder data should have required fields."""
        assert "target_type" in sample_reminder_data
        assert "remind_at" in sample_reminder_data
        assert sample_reminder_data["channel"] == "email"
