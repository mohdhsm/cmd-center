"""Tests for Pipedrive write operations."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from cmd_center.backend.integrations.pipedrive_client import PipedriveClient


class TestPipedriveWriteOperations:
    """Tests for Pipedrive write methods."""

    @pytest.fixture
    def client(self):
        """Create Pipedrive client."""
        return PipedriveClient(
            api_token="test-token",
            api_url="https://api.pipedrive.com/v1",
            api_url_v2="https://api.pipedrive.com/v2"
        )

    @pytest.mark.asyncio
    async def test_update_deal(self, client):
        """update_deal sends PUT request with correct payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123, "title": "Updated Deal"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            result = await client.update_deal(123, title="Updated Deal", status="won")

            assert result is not None
            assert result["id"] == 123
            mock_put.assert_called_once()
            # Verify payload contents
            call_args = mock_put.call_args
            assert call_args[1]["json"] == {"title": "Updated Deal", "status": "won"}

    @pytest.mark.asyncio
    async def test_update_deal_owner_id_mapping(self, client):
        """update_deal maps owner_id to user_id in API payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123, "user_id": 456}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            result = await client.update_deal(123, owner_id=456)

            assert result is not None
            mock_put.assert_called_once()
            # Verify owner_id is mapped to user_id
            call_args = mock_put.call_args
            assert call_args[1]["json"] == {"user_id": 456}

    @pytest.mark.asyncio
    async def test_add_deal_note(self, client):
        """add_deal_note sends POST request with correct payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 456, "content": "Test note"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.add_deal_note(123, "Test note")

            assert result is not None
            assert result["content"] == "Test note"
            mock_post.assert_called_once()
            # Verify payload contents
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["deal_id"] == 123
            assert payload["content"] == "Test note"
            assert payload["pinned_to_deal_flag"] == 0  # Default is not pinned

    @pytest.mark.asyncio
    async def test_add_deal_note_pinned(self, client):
        """add_deal_note uses pinned_to_deal_flag with 1/0."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 456, "content": "Pinned note"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.add_deal_note(123, "Pinned note", pinned=True)

            assert result is not None
            mock_post.assert_called_once()
            # Verify pinned_to_deal_flag is 1 (not True)
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["pinned_to_deal_flag"] == 1
