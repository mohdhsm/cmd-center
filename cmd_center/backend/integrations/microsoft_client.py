"""Microsoft Graph API client for SharePoint and OneDrive integration."""

import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import msal

from .config import get_config


class SharePointListItem(BaseModel):
    """DTO for SharePoint list item."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    fields: Dict[str, Any] = Field(default_factory=dict)
    created_datetime: Optional[str] = Field(default=None, alias="createdDateTime")
    last_modified_datetime: Optional[str] = Field(default=None, alias="lastModifiedDateTime")


class OneDriveFile(BaseModel):
    """DTO for OneDrive file metadata."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    name: str
    size: Optional[int] = None
    web_url: Optional[str] = Field(default=None, alias="webUrl")
    created_datetime: Optional[str] = Field(default=None, alias="createdDateTime")
    last_modified_datetime: Optional[str] = Field(default=None, alias="lastModifiedDateTime")
    download_url: Optional[str] = Field(default=None, alias="@microsoft.graph.downloadUrl")


class MicrosoftClient:
    """Client for Microsoft Graph API operations (SharePoint and OneDrive)."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        scope: str = "https://graph.microsoft.com/.default",
        timeout: float = 30.0,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.scope = scope
        self.timeout = timeout
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.http_client = httpx.AsyncClient(timeout=timeout)
        self._access_token: Optional[str] = None

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    def _get_access_token(self) -> str:
        """
        Get Microsoft Graph access token using client credentials flow.

        Returns:
            Access token string

        Raises:
            Exception: If authentication fails
        """
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret,
        )

        # Request token for Microsoft Graph
        scopes = [self.scope]
        result = app.acquire_token_for_client(scopes=scopes)

        if "access_token" in result:
            self._access_token = result["access_token"]
            return self._access_token
        else:
            error = result.get("error")
            error_desc = result.get("error_description")
            raise Exception(f"Failed to acquire token: {error} - {error_desc}")

    async def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers with fresh token."""
        if not self._access_token:
            self._get_access_token()

        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to Microsoft Graph API."""
        headers = await self._get_headers()
        url = f"{self.base_url}/{endpoint}"

        response = await self.http_client.get(url, headers=headers, params=params)

        # Token might have expired, retry once with new token
        if response.status_code == 401:
            self._access_token = None
            headers = await self._get_headers()
            response = await self.http_client.get(url, headers=headers, params=params)

        response.raise_for_status()
        return response.json()

    async def _post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make POST request to Microsoft Graph API."""
        headers = await self._get_headers()
        url = f"{self.base_url}/{endpoint}"

        response = await self.http_client.post(url, headers=headers, json=data, params=params)

        # Token might have expired, retry once with new token
        if response.status_code == 401:
            self._access_token = None
            headers = await self._get_headers()
            response = await self.http_client.post(url, headers=headers, json=data, params=params)

        response.raise_for_status()
        return response.json()

    # ==================== SharePoint Methods ====================

    async def get_sharepoint_sites(self, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get SharePoint sites.

        Args:
            search_query: Optional search query to filter sites

        Returns:
            List of SharePoint sites
        """
        if search_query:
            endpoint = f"sites?search={search_query}"
        else:
            endpoint = "sites"

        data = await self._get(endpoint)
        return data.get("value", [])

    async def get_sharepoint_site_by_path(self, hostname: str, site_path: str) -> Dict[str, Any]:
        """
        Get a SharePoint site by hostname and path.

        Args:
            hostname: SharePoint hostname (e.g., "contoso.sharepoint.com")
            site_path: Site path (e.g., "/sites/teamsite")

        Returns:
            SharePoint site information
        """
        endpoint = f"sites/{hostname}:{site_path}"
        return await self._get(endpoint)

    async def get_sharepoint_lists(self, site_id: str) -> List[Dict[str, Any]]:
        """
        Get all lists in a SharePoint site.

        Args:
            site_id: SharePoint site ID

        Returns:
            List of SharePoint lists
        """
        endpoint = f"sites/{site_id}/lists"
        data = await self._get(endpoint)
        return data.get("value", [])

    async def get_sharepoint_list_items(
        self,
        site_id: str,
        list_id: str,
        expand_fields: bool = True,
        filter_query: Optional[str] = None,
        top: int = 100,
    ) -> List[SharePointListItem]:
        """
        Get items from a SharePoint list.

        Args:
            site_id: SharePoint site ID
            list_id: SharePoint list ID or display name
            expand_fields: Whether to expand all fields
            filter_query: Optional OData filter query
            top: Maximum number of items to return (default 100)

        Returns:
            List of SharePoint list items
        """
        endpoint = f"sites/{site_id}/lists/{list_id}/items"

        params: Dict[str, Any] = {"$top": top}
        if expand_fields:
            params["$expand"] = "fields"
        if filter_query:
            params["$filter"] = filter_query

        data = await self._get(endpoint, params=params)

        items = []
        if data.get("value"):
            for item in data["value"]:
                try:
                    items.append(SharePointListItem(**item))
                except Exception as e:
                    print(f"Error parsing SharePoint list item: {e}")

        return items

    async def create_sharepoint_list_item(
        self,
        site_id: str,
        list_id: str,
        fields: Dict[str, Any],
    ) -> SharePointListItem:
        """
        Create a new item in a SharePoint list.

        Args:
            site_id: SharePoint site ID
            list_id: SharePoint list ID or display name
            fields: Dictionary of field names and values

        Returns:
            Created SharePoint list item
        """
        endpoint = f"sites/{site_id}/lists/{list_id}/items"
        data = {"fields": fields}

        result = await self._post(endpoint, data=data)
        return SharePointListItem(**result)

    # ==================== OneDrive Methods ====================

    async def get_onedrive_file_metadata(
        self,
        file_id: Optional[str] = None,
        file_path: Optional[str] = None,
        user_id: Optional[str] = None,
        drive_id: Optional[str] = None,
    ) -> OneDriveFile:
        """
        Get metadata for a OneDrive file.

        Args:
            file_id: OneDrive file ID
            file_path: File path relative to drive root (e.g., "/Documents/file.xlsx")
            user_id: User ID (for user-specific drives)
            drive_id: Drive ID (for specific drives)

        Returns:
            OneDrive file metadata

        Raises:
            ValueError: If neither file_id nor file_path is provided
        """
        endpoint = self._build_onedrive_endpoint(
            file_id=file_id,
            file_path=file_path,
            user_id=user_id,
            drive_id=drive_id,
            include_content=False,
        )

        data = await self._get(endpoint)
        return OneDriveFile(**data)

    async def download_onedrive_file(
        self,
        file_id: Optional[str] = None,
        file_path: Optional[str] = None,
        user_id: Optional[str] = None,
        drive_id: Optional[str] = None,
    ) -> bytes:
        """
        Download a file from OneDrive.

        Args:
            file_id: OneDrive file ID
            file_path: File path relative to drive root (e.g., "/Documents/file.xlsx")
            user_id: User ID (for user-specific drives)
            drive_id: Drive ID (for specific drives)

        Returns:
            File content as bytes
        """
        endpoint = self._build_onedrive_endpoint(
            file_id=file_id,
            file_path=file_path,
            user_id=user_id,
            drive_id=drive_id,
            include_content=True,
        )

        headers = await self._get_headers()
        url = f"{self.base_url}/{endpoint}"

        response = await self.http_client.get(url, headers=headers)

        # Token might have expired, retry once with new token
        if response.status_code == 401:
            self._access_token = None
            headers = await self._get_headers()
            response = await self.http_client.get(url, headers=headers)

        response.raise_for_status()
        return response.content

    async def list_onedrive_folder(
        self,
        folder_id: Optional[str] = None,
        folder_path: Optional[str] = None,
        user_id: Optional[str] = None,
        drive_id: Optional[str] = None,
    ) -> List[OneDriveFile]:
        """
        List files in a OneDrive folder.

        Args:
            folder_id: OneDrive folder ID
            folder_path: Folder path relative to drive root (e.g., "/Documents")
            user_id: User ID (for user-specific drives)
            drive_id: Drive ID (for specific drives)

        Returns:
            List of files in the folder
        """
        if folder_id:
            if drive_id:
                endpoint = f"drives/{drive_id}/items/{folder_id}/children"
            elif user_id:
                endpoint = f"users/{user_id}/drive/items/{folder_id}/children"
            else:
                endpoint = f"me/drive/items/{folder_id}/children"
        elif folder_path:
            if drive_id:
                endpoint = f"drives/{drive_id}/root:{folder_path}:/children"
            elif user_id:
                endpoint = f"users/{user_id}/drive/root:{folder_path}:/children"
            else:
                endpoint = f"me/drive/root:{folder_path}:/children"
        else:
            # List root folder
            if drive_id:
                endpoint = f"drives/{drive_id}/root/children"
            elif user_id:
                endpoint = f"users/{user_id}/drive/root/children"
            else:
                endpoint = "me/drive/root/children"

        data = await self._get(endpoint)

        files = []
        if data.get("value"):
            for item in data["value"]:
                try:
                    files.append(OneDriveFile(**item))
                except Exception as e:
                    print(f"Error parsing OneDrive file: {e}")

        return files

    def _build_onedrive_endpoint(
        self,
        file_id: Optional[str],
        file_path: Optional[str],
        user_id: Optional[str],
        drive_id: Optional[str],
        include_content: bool,
    ) -> str:
        """Build the appropriate OneDrive endpoint based on parameters."""
        if not file_id and not file_path:
            raise ValueError("Either file_id or file_path must be provided")

        content_suffix = "/content" if include_content else ""

        # Priority: drive_id > user_id > me
        if drive_id and file_id:
            return f"drives/{drive_id}/items/{file_id}{content_suffix}"
        elif drive_id and file_path:
            return f"drives/{drive_id}/root:{file_path}:{content_suffix}"
        elif user_id and file_id:
            return f"users/{user_id}/drive/items/{file_id}{content_suffix}"
        elif user_id and file_path:
            return f"users/{user_id}/drive/root:{file_path}:{content_suffix}"
        elif file_id:
            return f"me/drive/items/{file_id}{content_suffix}"
        elif file_path:
            return f"me/drive/root:{file_path}:{content_suffix}"
        else:
            raise ValueError("Invalid combination of parameters")


# Global client instance
_microsoft_client: Optional[MicrosoftClient] = None


def get_microsoft_client() -> MicrosoftClient:
    """Get or create Microsoft client singleton."""
    global _microsoft_client
    if _microsoft_client is None:
        config = get_config()
        _microsoft_client = MicrosoftClient(
            client_id=config.client_id,
            client_secret=config.client_secret,
            tenant_id=config.tenant_id,
            scope=config.microsoft_scope,
        )
    return _microsoft_client
