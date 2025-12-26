"""Integration tests for TeamScreen."""

import pytest
from unittest.mock import patch

from cmd_center.app import CommandCenterApp
from cmd_center.screens.team_screen import TeamScreen
from .conftest import MockAsyncClient, setup_mock_client


class TestTeamScreen:
    """Tests for TeamScreen."""

    @pytest.mark.asyncio
    async def test_screen_initializes_and_loads_employees(
        self, mock_client, sample_employees
    ):
        """Test that screen initializes and loads employee data."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")  # Switch to team screen
                await pilot.pause()

                screen = app.screen
                assert isinstance(screen, TeamScreen)

    @pytest.mark.asyncio
    async def test_employees_api_called_on_mount(self, mock_client, sample_employees):
        """Test that employees API is called when screen mounts."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                call_urls = [call[1] for call in mock_client.calls]
                assert any("/employees" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_employees_stored_in_list(self, mock_client, sample_employees):
        """Test that employees are stored in the employees list."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                screen = app.screen
                assert len(screen.employees) == len(sample_employees)

    @pytest.mark.asyncio
    async def test_refresh_reloads_data(self, mock_client, sample_employees):
        """Test that pressing 'r' reloads data."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                initial_call_count = len(mock_client.calls)

                await pilot.press("r")  # Refresh
                await pilot.pause()

                assert len(mock_client.calls) > initial_call_count

    @pytest.mark.asyncio
    async def test_screen_handles_empty_employees(self, mock_client):
        """Test screen handles empty employee list gracefully."""
        setup_mock_client(mock_client, employees=[], tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                screen = app.screen
                assert isinstance(screen, TeamScreen)
                assert len(screen.employees) == 0

    @pytest.mark.asyncio
    async def test_default_filters(self, mock_client, sample_employees):
        """Test default filter values."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                screen = app.screen
                assert screen.department_filter == "all"
                assert screen.active_filter is True


class TestTeamScreenActions:
    """Tests for actions in TeamScreen."""

    @pytest.mark.asyncio
    async def test_new_employee_binding_exists(self, mock_client, sample_employees):
        """Test that 'n' key binding exists for new employee."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "n" in bindings

    @pytest.mark.asyncio
    async def test_edit_employee_binding_exists(self, mock_client, sample_employees):
        """Test that 'F2' key binding exists for edit."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "f2" in bindings or "F2" in bindings

    @pytest.mark.asyncio
    async def test_view_skills_binding_exists(self, mock_client, sample_employees):
        """Test that 's' key binding exists for viewing skills."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "s" in bindings

    @pytest.mark.asyncio
    async def test_view_logs_binding_exists(self, mock_client, sample_employees):
        """Test that 'g' key binding exists for viewing logs."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "g" in bindings

    @pytest.mark.asyncio
    async def test_escape_goes_back(self, mock_client, sample_employees):
        """Test that Escape key binding exists for going back."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], employee_logs=[])

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "escape" in bindings


class TestTeamScreenEnrichment:
    """Tests for employee data enrichment."""

    @pytest.mark.asyncio
    async def test_tasks_api_called_for_enrichment(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that tasks API is called to enrich employee data."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            tasks=sample_tasks,
            employee_logs=[],
        )

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                # Check that tasks endpoint was called (for enrichment)
                call_urls = [call[1] for call in mock_client.calls]
                assert any("/tasks" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_employee_logs_api_called_for_enrichment(
        self, mock_client, sample_employees, sample_employee_logs
    ):
        """Test that employee-logs API is called to enrich employee data."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            tasks=[],
            employee_logs=sample_employee_logs,
        )

        with patch("cmd_center.screens.team_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("p")
                await pilot.pause()

                # Check that employee-logs endpoint was called
                call_urls = [call[1] for call in mock_client.calls]
                assert any("/employee-logs" in url for url in call_urls)
