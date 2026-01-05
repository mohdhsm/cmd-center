"""API adapter contract tests for Pipedrive write operations.

Tests verify:
1. Request Format Contract - correct endpoints, methods, headers
2. Response Handling Contract - success/failure parsing
3. Parameter Mapping Contract - field transformations
4. Edge Cases - empty inputs, network errors, timeouts
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from cmd_center.backend.integrations.pipedrive_client import PipedriveClient


class TestPipedriveAdapterRequestFormat:
    """Tests for request format contract - endpoints, methods, payloads."""

    @pytest.fixture
    def client(self):
        """Create Pipedrive client with test credentials."""
        return PipedriveClient(
            api_token="test-api-token-123",
            api_url="https://api.pipedrive.com/v1",
            api_url_v2="https://api.pipedrive.com/v2"
        )

    @pytest.mark.asyncio
    async def test_update_deal_sends_put_to_correct_endpoint(self, client):
        """update_deal sends PUT request to deals/{deal_id} endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 456, "title": "Updated"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            await client.update_deal(456, title="Updated")

            mock_put.assert_called_once()
            call_args = mock_put.call_args
            # Verify URL contains the deal ID
            assert call_args[0][0] == "https://api.pipedrive.com/v1/deals/456"

    @pytest.mark.asyncio
    async def test_update_deal_passes_api_token_as_query_param(self, client):
        """update_deal passes api_token as query parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            await client.update_deal(123, title="Test")

            call_args = mock_put.call_args
            # Verify api_token is in params
            assert call_args[1]["params"] == {"api_token": "test-api-token-123"}

    @pytest.mark.asyncio
    async def test_update_deal_sends_json_body(self, client):
        """update_deal sends request body as JSON."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123, "title": "New Title", "status": "won"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            await client.update_deal(123, title="New Title", status="won")

            call_args = mock_put.call_args
            # Verify json keyword argument is used
            assert "json" in call_args[1]
            assert call_args[1]["json"] == {"title": "New Title", "status": "won"}

    @pytest.mark.asyncio
    async def test_add_deal_note_sends_post_to_notes_endpoint(self, client):
        """add_deal_note sends POST request to notes endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 789, "content": "Test note"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.add_deal_note(123, "Test note")

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            # Verify URL is the notes endpoint
            assert call_args[0][0] == "https://api.pipedrive.com/v1/notes"

    @pytest.mark.asyncio
    async def test_add_deal_note_passes_api_token_as_query_param(self, client):
        """add_deal_note passes api_token as query parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 789}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.add_deal_note(123, "Note content")

            call_args = mock_post.call_args
            assert call_args[1]["params"] == {"api_token": "test-api-token-123"}

    @pytest.mark.asyncio
    async def test_add_deal_note_sends_json_body(self, client):
        """add_deal_note sends request body as JSON with correct structure."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 789}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.add_deal_note(123, "Note content", pinned=True)

            call_args = mock_post.call_args
            assert "json" in call_args[1]
            payload = call_args[1]["json"]
            assert payload["deal_id"] == 123
            assert payload["content"] == "Note content"
            assert "pinned_to_deal_flag" in payload


class TestPipedriveAdapterResponseHandling:
    """Tests for response handling contract - success/failure parsing."""

    @pytest.fixture
    def client(self):
        """Create Pipedrive client with test credentials."""
        return PipedriveClient(
            api_token="test-token",
            api_url="https://api.pipedrive.com/v1",
            api_url_v2="https://api.pipedrive.com/v2"
        )

    @pytest.mark.asyncio
    async def test_update_deal_returns_data_on_success(self, client):
        """update_deal returns data dict when success=true."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123, "title": "Updated Deal", "status": "won"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            result = await client.update_deal(123, title="Updated Deal")

            assert result is not None
            assert result["id"] == 123
            assert result["title"] == "Updated Deal"

    @pytest.mark.asyncio
    async def test_update_deal_returns_none_on_failure(self, client):
        """update_deal returns None when success=false."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error": "Deal not found",
            "error_info": "Deal 999 does not exist"
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            result = await client.update_deal(999, title="Test")

            assert result is None

    @pytest.mark.asyncio
    async def test_update_deal_returns_none_on_missing_data(self, client):
        """update_deal returns None when success=true but data is missing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": None
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            result = await client.update_deal(123, title="Test")

            assert result is None

    @pytest.mark.asyncio
    async def test_add_deal_note_returns_data_on_success(self, client):
        """add_deal_note returns data dict when success=true."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 456, "content": "New note", "deal_id": 123}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.add_deal_note(123, "New note")

            assert result is not None
            assert result["id"] == 456
            assert result["content"] == "New note"

    @pytest.mark.asyncio
    async def test_add_deal_note_returns_none_on_failure(self, client):
        """add_deal_note returns None when success=false."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error": "Invalid deal_id"
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.add_deal_note(999, "Test note")

            assert result is None

    @pytest.mark.asyncio
    async def test_update_deal_raises_on_http_error(self, client):
        """update_deal propagates HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404)
        )

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await client.update_deal(123, title="Test")

    @pytest.mark.asyncio
    async def test_add_deal_note_raises_on_http_error(self, client):
        """add_deal_note propagates HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=MagicMock(status_code=500)
        )

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await client.add_deal_note(123, "Test note")


class TestPipedriveAdapterParameterMapping:
    """Tests for parameter mapping contract - field transformations."""

    @pytest.fixture
    def client(self):
        """Create Pipedrive client with test credentials."""
        return PipedriveClient(
            api_token="test-token",
            api_url="https://api.pipedrive.com/v1",
            api_url_v2="https://api.pipedrive.com/v2"
        )

    @pytest.mark.asyncio
    async def test_update_deal_maps_owner_id_to_user_id(self, client):
        """update_deal maps owner_id parameter to user_id in payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123, "user_id": 456}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            await client.update_deal(123, owner_id=456)

            call_args = mock_put.call_args
            payload = call_args[1]["json"]
            # owner_id should be mapped to user_id
            assert "user_id" in payload
            assert payload["user_id"] == 456
            # owner_id should NOT be in payload
            assert "owner_id" not in payload

    @pytest.mark.asyncio
    async def test_add_deal_note_uses_integer_for_pinned_flag(self, client):
        """add_deal_note uses pinned_to_deal_flag with 1/0 (not bool)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 789}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Test with pinned=True
            await client.add_deal_note(123, "Pinned note", pinned=True)
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["pinned_to_deal_flag"] == 1
            assert payload["pinned_to_deal_flag"] is not True  # Must be int, not bool

    @pytest.mark.asyncio
    async def test_add_deal_note_uses_zero_for_unpinned(self, client):
        """add_deal_note uses 0 (not False) for unpinned notes."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 789}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Test with pinned=False (default)
            await client.add_deal_note(123, "Regular note", pinned=False)
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["pinned_to_deal_flag"] == 0
            assert payload["pinned_to_deal_flag"] is not False  # Must be int, not bool

    @pytest.mark.asyncio
    async def test_update_deal_includes_only_provided_fields(self, client):
        """update_deal only includes fields that were explicitly provided."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            # Only provide title, not status/stage_id/owner_id/value
            await client.update_deal(123, title="Only Title")

            call_args = mock_put.call_args
            payload = call_args[1]["json"]
            assert payload == {"title": "Only Title"}
            assert "status" not in payload
            assert "stage_id" not in payload
            assert "user_id" not in payload
            assert "value" not in payload

    @pytest.mark.asyncio
    async def test_update_deal_includes_multiple_provided_fields(self, client):
        """update_deal includes all fields that were provided."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            await client.update_deal(
                123,
                title="New Title",
                status="won",
                stage_id=5,
                owner_id=10,
                value=50000.0
            )

            call_args = mock_put.call_args
            payload = call_args[1]["json"]
            assert payload == {
                "title": "New Title",
                "status": "won",
                "stage_id": 5,
                "user_id": 10,  # owner_id mapped to user_id
                "value": 50000.0
            }

    @pytest.mark.asyncio
    async def test_add_deal_note_payload_structure(self, client):
        """add_deal_note includes all required fields in payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 789}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await client.add_deal_note(123, "Note content", pinned=True)

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload == {
                "deal_id": 123,
                "content": "Note content",
                "pinned_to_deal_flag": 1
            }


class TestPipedriveAdapterEdgeCases:
    """Tests for edge cases - empty inputs, network errors."""

    @pytest.fixture
    def client(self):
        """Create Pipedrive client with test credentials."""
        return PipedriveClient(
            api_token="test-token",
            api_url="https://api.pipedrive.com/v1",
            api_url_v2="https://api.pipedrive.com/v2"
        )

    @pytest.mark.asyncio
    async def test_update_deal_with_no_fields_returns_none(self, client):
        """update_deal returns None when no fields are provided."""
        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            result = await client.update_deal(123)

            # Should not make any API call
            mock_put.assert_not_called()
            assert result is None

    @pytest.mark.asyncio
    async def test_update_deal_with_empty_string_title(self, client):
        """update_deal includes empty string as a valid value."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123, "title": ""}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            # Empty string is a valid value (different from None)
            result = await client.update_deal(123, title="")

            mock_put.assert_called_once()
            call_args = mock_put.call_args
            payload = call_args[1]["json"]
            assert payload == {"title": ""}

    @pytest.mark.asyncio
    async def test_update_deal_with_zero_value(self, client):
        """update_deal includes zero as a valid value."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123, "value": 0}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            # Zero is a valid value (different from None)
            result = await client.update_deal(123, value=0.0)

            mock_put.assert_called_once()
            call_args = mock_put.call_args
            payload = call_args[1]["json"]
            assert payload == {"value": 0.0}

    @pytest.mark.asyncio
    async def test_add_deal_note_with_empty_content(self, client):
        """add_deal_note sends request even with empty content."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 789, "content": ""}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.add_deal_note(123, "")

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["content"] == ""

    @pytest.mark.asyncio
    async def test_update_deal_handles_network_timeout(self, client):
        """update_deal propagates timeout errors."""
        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.side_effect = httpx.TimeoutException("Connection timed out")

            with pytest.raises(httpx.TimeoutException):
                await client.update_deal(123, title="Test")

    @pytest.mark.asyncio
    async def test_add_deal_note_handles_network_timeout(self, client):
        """add_deal_note propagates timeout errors."""
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Connection timed out")

            with pytest.raises(httpx.TimeoutException):
                await client.add_deal_note(123, "Test note")

    @pytest.mark.asyncio
    async def test_update_deal_handles_connection_error(self, client):
        """update_deal propagates connection errors."""
        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(httpx.ConnectError):
                await client.update_deal(123, title="Test")

    @pytest.mark.asyncio
    async def test_add_deal_note_handles_connection_error(self, client):
        """add_deal_note propagates connection errors."""
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(httpx.ConnectError):
                await client.add_deal_note(123, "Test note")

    @pytest.mark.asyncio
    async def test_update_deal_with_special_characters_in_title(self, client):
        """update_deal handles special characters in title."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            special_title = "Deal with 'quotes' and \"double quotes\" & <special> chars"
            await client.update_deal(123, title=special_title)

            call_args = mock_put.call_args
            payload = call_args[1]["json"]
            assert payload["title"] == special_title

    @pytest.mark.asyncio
    async def test_add_deal_note_with_multiline_content(self, client):
        """add_deal_note handles multiline content."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 789}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            multiline_content = "Line 1\nLine 2\nLine 3"
            await client.add_deal_note(123, multiline_content)

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["content"] == multiline_content

    @pytest.mark.asyncio
    async def test_add_deal_note_with_unicode_content(self, client):
        """add_deal_note handles unicode content."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 789}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            unicode_content = "Arabic: \u0645\u0631\u062d\u0628\u0627, Chinese: \u4f60\u597d"
            await client.add_deal_note(123, unicode_content)

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["content"] == unicode_content
