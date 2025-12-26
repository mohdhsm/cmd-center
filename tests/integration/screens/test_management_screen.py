"""Integration tests for ManagementScreen."""

import pytest
from unittest.mock import patch, AsyncMock

from cmd_center.app import CommandCenterApp
from cmd_center.screens.management_screen import ManagementScreen
from .conftest import MockAsyncClient, setup_mock_client


class TestManagementScreen:
    """Tests for ManagementScreen."""

    @pytest.mark.asyncio
    async def test_screen_initializes_with_tasks_mode(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that screen initializes with Tasks mode as default."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=sample_tasks)

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")  # Switch to management screen
                await pilot.pause()  # Wait for data loading

                screen = app.screen
                assert isinstance(screen, ManagementScreen)
                assert screen.current_mode == "tasks"

    @pytest.mark.asyncio
    async def test_switch_to_notes_mode(
        self, mock_client, sample_employees, sample_tasks, sample_notes
    ):
        """Test pressing '2' switches to Notes mode."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            tasks=sample_tasks,
            notes=sample_notes,
        )

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")  # Switch to management screen
                await pilot.pause()

                await pilot.press("2")  # Switch to notes mode
                await pilot.pause()

                screen = app.screen
                assert screen.current_mode == "notes"

    @pytest.mark.asyncio
    async def test_switch_back_to_tasks_mode(
        self, mock_client, sample_employees, sample_tasks, sample_notes
    ):
        """Test pressing '1' switches back to Tasks mode."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            tasks=sample_tasks,
            notes=sample_notes,
        )

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                await pilot.press("2")  # Switch to notes
                await pilot.pause()

                await pilot.press("1")  # Switch back to tasks
                await pilot.pause()

                screen = app.screen
                assert screen.current_mode == "tasks"

    @pytest.mark.asyncio
    async def test_tasks_api_called_on_mount(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that tasks API is called when screen mounts."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=sample_tasks)

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                # Check that /tasks and /employees were called
                call_urls = [call[1] for call in mock_client.calls]
                assert any("/tasks" in url for url in call_urls)
                assert any("/employees" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_notes_api_called_on_mode_switch(
        self, mock_client, sample_employees, sample_tasks, sample_notes
    ):
        """Test that notes API is called when switching to notes mode."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            tasks=sample_tasks,
            notes=sample_notes,
        )

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                # Clear previous calls
                mock_client.calls.clear()

                await pilot.press("2")  # Switch to notes
                await pilot.pause()

                # Check that /notes was called
                call_urls = [call[1] for call in mock_client.calls]
                assert any("/notes" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_refresh_reloads_data(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that pressing 'r' reloads data."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=sample_tasks)

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                # Clear previous calls
                initial_call_count = len(mock_client.calls)

                await pilot.press("r")  # Refresh
                await pilot.pause()

                # Should have made new API calls
                assert len(mock_client.calls) > initial_call_count

    @pytest.mark.asyncio
    async def test_screen_handles_empty_data(self, mock_client, sample_employees):
        """Test screen handles empty task/note lists gracefully."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=[], notes=[])

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                screen = app.screen
                assert isinstance(screen, ManagementScreen)
                # Should not crash with empty data

    @pytest.mark.asyncio
    async def test_employees_api_called(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that employees API is called for caching."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=sample_tasks)

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                # Check that employees API was called
                call_urls = [call[1] for call in mock_client.calls]
                assert any("/employees" in url for url in call_urls)


class TestManagementScreenDataDisplay:
    """Tests for data display in ManagementScreen."""

    @pytest.mark.asyncio
    async def test_tasks_api_called_for_data(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that tasks API is called for data display."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=sample_tasks)

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                # Check tasks API was called
                call_urls = [call[1] for call in mock_client.calls]
                assert any("/tasks" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_notes_api_called_for_data(
        self, mock_client, sample_employees, sample_tasks, sample_notes
    ):
        """Test that notes API is called when in notes mode."""
        setup_mock_client(
            mock_client,
            employees=sample_employees,
            tasks=sample_tasks,
            notes=sample_notes,
        )

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                await pilot.press("2")  # Switch to notes
                await pilot.pause()

                # Check notes API was called
                call_urls = [call[1] for call in mock_client.calls]
                assert any("/notes" in url for url in call_urls)


class TestManagementScreenActions:
    """Tests for actions in ManagementScreen."""

    @pytest.mark.asyncio
    async def test_new_task_action_exists(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that 'n' key triggers new item action."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=sample_tasks)

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                # The 'n' binding should exist
                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "n" in bindings

    @pytest.mark.asyncio
    async def test_complete_task_binding_exists(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that 'c' key binding exists for complete."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=sample_tasks)

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "c" in bindings

    @pytest.mark.asyncio
    async def test_delete_task_binding_exists(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that 'd' key binding exists for delete."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=sample_tasks)

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "d" in bindings

    @pytest.mark.asyncio
    async def test_edit_binding_exists(
        self, mock_client, sample_employees, sample_tasks
    ):
        """Test that 'e' key binding exists for edit."""
        setup_mock_client(mock_client, employees=sample_employees, tasks=sample_tasks)

        with patch("cmd_center.screens.management_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("m")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "e" in bindings
