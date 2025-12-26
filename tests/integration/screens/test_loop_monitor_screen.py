"""Integration tests for LoopMonitorScreen."""

import pytest
from unittest.mock import patch

from cmd_center.app import CommandCenterApp
from cmd_center.screens.loop_monitor_screen import LoopMonitorScreen
from .conftest import MockAsyncClient, setup_mock_client


class TestLoopMonitorScreen:
    """Tests for LoopMonitorScreen."""

    @pytest.mark.asyncio
    async def test_screen_initializes_with_status_mode(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test that screen initializes with Status mode as default."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")  # Switch to loop monitor screen
                await pilot.pause()

                screen = app.screen
                assert isinstance(screen, LoopMonitorScreen)
                assert screen.current_mode == "status"

    @pytest.mark.asyncio
    async def test_switch_to_findings_mode(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test pressing '2' switches to Findings mode."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                await pilot.press("2")  # Switch to findings
                await pilot.pause()

                screen = app.screen
                assert screen.current_mode == "findings"

    @pytest.mark.asyncio
    async def test_switch_to_history_mode(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test pressing '3' switches to History mode."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                await pilot.press("3")  # Switch to history
                await pilot.pause()

                screen = app.screen
                assert screen.current_mode == "history"

    @pytest.mark.asyncio
    async def test_switch_back_to_status_mode(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test pressing '1' switches back to Status mode."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                await pilot.press("2")  # Switch to findings
                await pilot.pause()

                await pilot.press("1")  # Switch back to status
                await pilot.pause()

                screen = app.screen
                assert screen.current_mode == "status"

    @pytest.mark.asyncio
    async def test_loop_status_api_called_on_mount(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test that loop status API is called when screen mounts."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                call_urls = [call[1] for call in mock_client.calls]
                assert any("/loops/status" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_findings_api_called_on_mode_switch(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test that findings API is called when switching to findings mode."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                mock_client.calls.clear()

                await pilot.press("2")  # Switch to findings
                await pilot.pause()

                call_urls = [call[1] for call in mock_client.calls]
                assert any("/loops/findings" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_runs_api_called_on_history_mode(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test that runs API is called when switching to history mode."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                mock_client.calls.clear()

                await pilot.press("3")  # Switch to history
                await pilot.pause()

                call_urls = [call[1] for call in mock_client.calls]
                assert any("/loops/runs" in url for url in call_urls)

    @pytest.mark.asyncio
    async def test_refresh_reloads_data(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test that pressing 'r' reloads data."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                initial_call_count = len(mock_client.calls)

                await pilot.press("r")  # Refresh
                await pilot.pause()

                assert len(mock_client.calls) > initial_call_count

    @pytest.mark.asyncio
    async def test_screen_handles_empty_data(self, mock_client):
        """Test screen handles empty data lists gracefully."""
        setup_mock_client(
            mock_client,
            loop_status=[],
            findings=[],
            loop_runs=[],
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                screen = app.screen
                assert isinstance(screen, LoopMonitorScreen)


class TestLoopMonitorScreenDataDisplay:
    """Tests for data display in LoopMonitorScreen."""

    @pytest.mark.asyncio
    async def test_loop_status_stored_in_items(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test that loop status data is stored in items."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                screen = app.screen
                assert len(screen.items) == len(sample_loop_status)

    @pytest.mark.asyncio
    async def test_findings_stored_after_mode_switch(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test that findings are stored after switching to findings mode."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                await pilot.press("2")  # Switch to findings
                await pilot.pause()

                screen = app.screen
                assert len(screen.items) == len(sample_findings)


class TestLoopMonitorScreenActions:
    """Tests for actions in LoopMonitorScreen."""

    @pytest.mark.asyncio
    async def test_run_selected_binding_exists(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test that Enter key binding exists for running selected loop."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "enter" in bindings

    @pytest.mark.asyncio
    async def test_escape_goes_back(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test that Escape key binding exists for going back."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                screen = app.screen
                bindings = {b.key: b for b in screen.BINDINGS}
                assert "escape" in bindings

    @pytest.mark.asyncio
    async def test_default_filter_values(
        self, mock_client, sample_loop_status, sample_findings, sample_loop_runs
    ):
        """Test default filter values are set."""
        setup_mock_client(
            mock_client,
            loop_status=sample_loop_status,
            findings=sample_findings,
            loop_runs=sample_loop_runs,
        )

        with patch("cmd_center.screens.loop_monitor_screen.httpx.AsyncClient") as mock:
            mock.return_value = mock_client

            app = CommandCenterApp()
            async with app.run_test() as pilot:
                await pilot.press("l")
                await pilot.pause()

                screen = app.screen
                assert screen.finding_severity_filter == "all"
                assert screen.finding_target_filter == "all"
                assert screen.history_loop_filter == "all"
