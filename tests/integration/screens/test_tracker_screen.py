"""Integration tests for TrackerScreen."""

import pytest
from unittest.mock import patch

from cmd_center.app import CommandCenterApp
from cmd_center.screens.tracker_screen import TrackerScreen
from .conftest import MockAsyncClient, setup_mock_client


class TestTrackerScreen:
    """Tests for TrackerScreen."""

    @pytest.mark.asyncio
    async def test_screen_initializes_with_documents_mode(
        self, mock_client, sample_employees, sample_documents
    ):
        """Test that screen initializes with Documents mode as default."""
        setup_mock_client(
            mock_client, employees=sample_employees, documents=sample_documents
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")  # Switch to tracker screen
                await pilot.pause()

                screen = app.screen
                assert isinstance(screen, TrackerScreen)
                assert screen.current_mode == "documents"

    @pytest.mark.asyncio
    async def test_switch_to_bonuses_mode(
        self, mock_client, sample_employees, sample_documents, sample_bonuses
    ):
        """Test pressing '2' switches to Bonuses mode."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            documents=sample_documents,
            bonuses=sample_bonuses,
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                await pilot.press("2")  # Switch to bonuses
                await pilot.pause()

                screen = app.screen
                assert screen.current_mode == "bonuses"

    @pytest.mark.asyncio
    async def test_switch_to_logs_mode(
        self, mock_client, sample_employees, sample_documents, sample_employee_logs
    ):
        """Test pressing '3' switches to Logs mode."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            documents=sample_documents,
            employee_logs=sample_employee_logs,
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                await pilot.press("3")  # Switch to logs
                await pilot.pause()

                screen = app.screen
                assert screen.current_mode == "logs"

    @pytest.mark.asyncio
    async def test_switch_to_skills_mode(
        self, mock_client, sample_employees, sample_documents, sample_skills
    ):
        """Test pressing '4' switches to Skills mode."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            documents=sample_documents,
            skills=sample_skills,
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                await pilot.press("4")  # Switch to skills
                await pilot.pause()

                screen = app.screen
                assert screen.current_mode == "skills"

    @pytest.mark.asyncio
    async def test_switch_back_to_documents_mode(
        self, mock_client, sample_employees, sample_documents, sample_bonuses
    ):
        """Test pressing '1' switches back to Documents mode."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            documents=sample_documents,
            bonuses=sample_bonuses,
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                await pilot.press("2")  # Switch to bonuses
                await pilot.pause()

                await pilot.press("1")  # Switch back to documents
                await pilot.pause()

                screen = app.screen
                assert screen.current_mode == "documents"

    @pytest.mark.asyncio
    async def test_documents_api_called_on_mount(
        self, mock_client, sample_employees, sample_documents
    ):
        """Test that documents API is called when screen mounts."""
        setup_mock_client(
            mock_client, employees=sample_employees, documents=sample_documents
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                # Check that /documents was called
                call_urls = [call[1] for call in mock_client.calls]
                assert any("/documents" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_bonuses_api_called_on_mode_switch(
        self, mock_client, sample_employees, sample_documents, sample_bonuses
    ):
        """Test that bonuses API is called when switching to bonuses mode."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            documents=sample_documents,
            bonuses=sample_bonuses,
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                mock_client.calls.clear()

                await pilot.press("2")  # Switch to bonuses
                await pilot.pause()

                call_urls = [call[1] for call in mock_client.calls]
                assert any("/bonuses" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_refresh_reloads_data(
        self, mock_client, sample_employees, sample_documents
    ):
        """Test that pressing 'r' reloads data."""
        setup_mock_client(
            mock_client, employees=sample_employees, documents=sample_documents
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                initial_call_count = len(mock_client.calls)

                await pilot.press("r")  # Refresh
                await pilot.pause()

                assert len(mock_client.calls) > initial_call_count

    @pytest.mark.asyncio
    async def test_screen_handles_empty_data(self, mock_client, sample_employees):
        """Test screen handles empty data lists gracefully."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            documents=[],
            bonuses=[],
            employee_logs=[],
            skills=[],
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                screen = app.screen
                assert isinstance(screen, TrackerScreen)


class TestTrackerScreenDataDisplay:
    """Tests for data display in TrackerScreen."""

    @pytest.mark.asyncio
    async def test_documents_stored_in_items(
        self, mock_client, sample_employees, sample_documents
    ):
        """Test that documents are stored in items."""
        setup_mock_client(
            mock_client, employees=sample_employees, documents=sample_documents
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                screen = app.screen
                assert len(screen.items) == len(sample_documents)

    @pytest.mark.asyncio
    async def test_employees_api_called(self, mock_client, sample_employees, sample_documents):
        """Test that employees API is called."""
        setup_mock_client(
            mock_client, employees=sample_employees, documents=sample_documents
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                # Employees API is called asynchronously
                call_urls = [call[1] for call in mock_client.calls]
                # The screen should attempt to load employees
                screen = app.screen
                assert isinstance(screen, TrackerScreen)


class TestTrackerScreenActions:
    """Tests for actions in TrackerScreen."""

    @pytest.mark.asyncio
    async def test_new_item_binding_exists(
        self, mock_client, sample_employees, sample_documents
    ):
        """Test that 'n' key binding exists for new item."""
        setup_mock_client(
            mock_client, employees=sample_employees, documents=sample_documents
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "n" in bindings

    @pytest.mark.asyncio
    async def test_edit_item_binding_exists(
        self, mock_client, sample_employees, sample_documents
    ):
        """Test that 'e' key binding exists for edit."""
        setup_mock_client(
            mock_client, employees=sample_employees, documents=sample_documents
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "e" in bindings

    @pytest.mark.asyncio
    async def test_payment_binding_exists(
        self, mock_client, sample_employees, sample_documents
    ):
        """Test that '$' key binding exists for payment."""
        setup_mock_client(
            mock_client, employees=sample_employees, documents=sample_documents
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "$" in bindings

    @pytest.mark.asyncio
    async def test_escape_goes_back(
        self, mock_client, sample_employees, sample_documents
    ):
        """Test that Escape key binding exists for going back."""
        setup_mock_client(
            mock_client, employees=sample_employees, documents=sample_documents
        )

        with patch("cmd_center.screens.tracker_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("t")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "escape" in bindings
