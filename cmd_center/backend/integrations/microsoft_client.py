"""Microsoft Graph API client for SharePoint, OneDrive, and Email integration."""

import httpx
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import msal

from .config import get_config

logger = logging.getLogger(__name__)


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


# ==================== Email DTOs ====================


class EmailAddress(BaseModel):
    """Email address from Graph API."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    address: str
    name: Optional[str] = None


class EmailRecipient(BaseModel):
    """Email recipient wrapper (Graph API format)."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    email_address: EmailAddress = Field(alias="emailAddress")


class EmailBody(BaseModel):
    """Email body from Graph API."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    content_type: str = Field(default="html", alias="contentType")
    content: str = ""


class EmailAttachmentDTO(BaseModel):
    """Email attachment metadata from Graph API."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    name: str
    content_type: str = Field(default="application/octet-stream", alias="contentType")
    size: int = 0
    is_inline: bool = Field(default=False, alias="isInline")


class EmailMessageDTO(BaseModel):
    """Email message from Graph API."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    subject: Optional[str] = None
    body_preview: str = Field(default="", alias="bodyPreview")
    body: Optional[EmailBody] = None
    from_recipient: Optional[EmailRecipient] = Field(default=None, alias="from")
    to_recipients: List[EmailRecipient] = Field(default_factory=list, alias="toRecipients")
    cc_recipients: List[EmailRecipient] = Field(default_factory=list, alias="ccRecipients")
    bcc_recipients: List[EmailRecipient] = Field(default_factory=list, alias="bccRecipients")
    received_datetime: Optional[str] = Field(default=None, alias="receivedDateTime")
    sent_datetime: Optional[str] = Field(default=None, alias="sentDateTime")
    is_read: bool = Field(default=False, alias="isRead")
    has_attachments: bool = Field(default=False, alias="hasAttachments")
    importance: str = "normal"
    parent_folder_id: Optional[str] = Field(default=None, alias="parentFolderId")
    conversation_id: Optional[str] = Field(default=None, alias="conversationId")
    web_link: Optional[str] = Field(default=None, alias="webLink")
    is_draft: bool = Field(default=False, alias="isDraft")


class MailFolderDTO(BaseModel):
    """Mail folder from Graph API."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    display_name: str = Field(alias="displayName")
    parent_folder_id: Optional[str] = Field(default=None, alias="parentFolderId")
    child_folder_count: int = Field(default=0, alias="childFolderCount")
    unread_item_count: int = Field(default=0, alias="unreadItemCount")
    total_item_count: int = Field(default=0, alias="totalItemCount")


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

    async def _post_no_response(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Make POST request that returns no content (202 Accepted)."""
        headers = await self._get_headers()
        url = f"{self.base_url}/{endpoint}"

        response = await self.http_client.post(url, headers=headers, json=data, params=params)

        # Token might have expired, retry once with new token
        if response.status_code == 401:
            self._access_token = None
            headers = await self._get_headers()
            response = await self.http_client.post(url, headers=headers, json=data, params=params)

        response.raise_for_status()
        return response.status_code in (200, 202, 204)

    async def _patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make PATCH request to Microsoft Graph API."""
        headers = await self._get_headers()
        url = f"{self.base_url}/{endpoint}"

        response = await self.http_client.patch(url, headers=headers, json=data)

        # Token might have expired, retry once with new token
        if response.status_code == 401:
            self._access_token = None
            headers = await self._get_headers()
            response = await self.http_client.patch(url, headers=headers, json=data)

        response.raise_for_status()
        # PATCH may return empty response
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    async def _delete(self, endpoint: str) -> bool:
        """Make DELETE request to Microsoft Graph API."""
        headers = await self._get_headers()
        url = f"{self.base_url}/{endpoint}"

        response = await self.http_client.delete(url, headers=headers)

        # Token might have expired, retry once with new token
        if response.status_code == 401:
            self._access_token = None
            headers = await self._get_headers()
            response = await self.http_client.delete(url, headers=headers)

        response.raise_for_status()
        return response.status_code in (200, 204)

    async def _get_binary(self, endpoint: str) -> bytes:
        """Make GET request and return binary content."""
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

    # ==================== Email Methods ====================

    async def get_mail_folders(
        self,
        mailbox: str,
        include_hidden: bool = False,
    ) -> List[MailFolderDTO]:
        """
        Get mail folders for a mailbox.

        Args:
            mailbox: Email address of the mailbox (e.g., "user@domain.com")
            include_hidden: Whether to include hidden folders

        Returns:
            List of mail folders
        """
        endpoint = f"users/{mailbox}/mailFolders"
        params = {"$top": 100}
        if include_hidden:
            params["includeHiddenFolders"] = "true"

        data = await self._get(endpoint, params=params)

        folders = []
        for item in data.get("value", []):
            try:
                folders.append(MailFolderDTO.model_validate(item))
            except Exception as e:
                logger.warning(f"Error parsing mail folder: {e}")

        return folders

    async def get_mail_folder_by_name(
        self,
        mailbox: str,
        folder_name: str,
    ) -> Optional[MailFolderDTO]:
        """
        Get a mail folder by display name.

        Args:
            mailbox: Email address of the mailbox
            folder_name: Display name of the folder (e.g., "Inbox", "Sent Items")

        Returns:
            Mail folder or None if not found
        """
        # Well-known folder names map to IDs
        well_known = {
            "inbox": "inbox",
            "drafts": "drafts",
            "sentitems": "sentitems",
            "sent items": "sentitems",
            "deleteditems": "deleteditems",
            "deleted items": "deleteditems",
            "junkemail": "junkemail",
            "junk email": "junkemail",
            "archive": "archive",
        }

        folder_key = folder_name.lower()
        if folder_key in well_known:
            endpoint = f"users/{mailbox}/mailFolders/{well_known[folder_key]}"
            try:
                data = await self._get(endpoint)
                return MailFolderDTO.model_validate(data)
            except Exception:
                return None

        # Search by display name
        folders = await self.get_mail_folders(mailbox)
        for folder in folders:
            if folder.display_name.lower() == folder_name.lower():
                return folder

        return None

    async def create_mail_folder(
        self,
        mailbox: str,
        display_name: str,
        parent_folder_id: Optional[str] = None,
    ) -> MailFolderDTO:
        """
        Create a new mail folder.

        Args:
            mailbox: Email address of the mailbox
            display_name: Display name for the new folder
            parent_folder_id: Optional parent folder ID (creates subfolder)

        Returns:
            Created mail folder
        """
        if parent_folder_id:
            endpoint = f"users/{mailbox}/mailFolders/{parent_folder_id}/childFolders"
        else:
            endpoint = f"users/{mailbox}/mailFolders"

        data = {"displayName": display_name}
        result = await self._post(endpoint, data=data)
        return MailFolderDTO.model_validate(result)

    async def get_messages(
        self,
        mailbox: str,
        folder_id: str = "inbox",
        top: int = 50,
        skip: int = 0,
        filter_query: Optional[str] = None,
        search_query: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        order_by: str = "receivedDateTime desc",
    ) -> List[EmailMessageDTO]:
        """
        Get messages from a mailbox folder.

        Args:
            mailbox: Email address of the mailbox
            folder_id: Folder ID or well-known name (inbox, sentitems, etc.)
            top: Maximum number of messages to return
            skip: Number of messages to skip (for pagination)
            filter_query: OData filter query
            search_query: Search query string
            select_fields: Fields to include in response
            order_by: Sort order

        Returns:
            List of email messages
        """
        endpoint = f"users/{mailbox}/mailFolders/{folder_id}/messages"

        params: Dict[str, Any] = {
            "$top": top,
            "$skip": skip,
            "$orderby": order_by,
        }

        if filter_query:
            params["$filter"] = filter_query
        if search_query:
            params["$search"] = f'"{search_query}"'
        if select_fields:
            params["$select"] = ",".join(select_fields)

        data = await self._get(endpoint, params=params)

        messages = []
        for item in data.get("value", []):
            try:
                messages.append(EmailMessageDTO.model_validate(item))
            except Exception as e:
                logger.warning(f"Error parsing email message: {e}")

        return messages

    async def get_message_by_id(
        self,
        mailbox: str,
        message_id: str,
        include_body: bool = True,
    ) -> Optional[EmailMessageDTO]:
        """
        Get a single message by ID.

        Args:
            mailbox: Email address of the mailbox
            message_id: Message ID
            include_body: Whether to include full body content

        Returns:
            Email message or None if not found
        """
        endpoint = f"users/{mailbox}/messages/{message_id}"

        params = {}
        if include_body:
            params["$select"] = (
                "id,subject,bodyPreview,body,from,toRecipients,ccRecipients,"
                "receivedDateTime,sentDateTime,isRead,hasAttachments,importance,"
                "parentFolderId,conversationId,webLink,isDraft"
            )

        try:
            data = await self._get(endpoint, params=params if params else None)
            return EmailMessageDTO.model_validate(data)
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None

    async def send_mail(
        self,
        mailbox: str,
        subject: str,
        body: str,
        to_recipients: List[str],
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        body_type: str = "html",
        save_to_sent: bool = True,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Send an email from a mailbox.

        Args:
            mailbox: Email address to send from
            subject: Email subject
            body: Email body content
            to_recipients: List of recipient email addresses
            cc_recipients: List of CC email addresses
            bcc_recipients: List of BCC email addresses
            body_type: Body content type ("text" or "html")
            save_to_sent: Whether to save to Sent Items
            attachments: List of attachment dicts with keys:
                - name: filename
                - contentType: MIME type
                - contentBytes: base64-encoded content

        Returns:
            True if sent successfully
        """
        endpoint = f"users/{mailbox}/sendMail"

        def make_recipient(email: str) -> Dict[str, Any]:
            return {"emailAddress": {"address": email}}

        message: Dict[str, Any] = {
            "subject": subject,
            "body": {
                "contentType": body_type.capitalize(),
                "content": body,
            },
            "toRecipients": [make_recipient(e) for e in to_recipients],
        }

        if cc_recipients:
            message["ccRecipients"] = [make_recipient(e) for e in cc_recipients]
        if bcc_recipients:
            message["bccRecipients"] = [make_recipient(e) for e in bcc_recipients]
        if attachments:
            message["attachments"] = attachments

        data = {
            "message": message,
            "saveToSentItems": save_to_sent,
        }

        return await self._post_no_response(endpoint, data=data)

    async def reply_to_message(
        self,
        mailbox: str,
        message_id: str,
        comment: str,
        reply_all: bool = False,
    ) -> bool:
        """
        Reply to a message.

        Args:
            mailbox: Email address of the mailbox
            message_id: ID of the message to reply to
            comment: Reply comment/body
            reply_all: Whether to reply to all recipients

        Returns:
            True if successful
        """
        action = "replyAll" if reply_all else "reply"
        endpoint = f"users/{mailbox}/messages/{message_id}/{action}"

        data = {"comment": comment}
        return await self._post_no_response(endpoint, data=data)

    async def forward_message(
        self,
        mailbox: str,
        message_id: str,
        to_recipients: List[str],
        comment: Optional[str] = None,
    ) -> bool:
        """
        Forward a message.

        Args:
            mailbox: Email address of the mailbox
            message_id: ID of the message to forward
            to_recipients: List of recipient email addresses
            comment: Optional comment to add

        Returns:
            True if successful
        """
        endpoint = f"users/{mailbox}/messages/{message_id}/forward"

        data: Dict[str, Any] = {
            "toRecipients": [
                {"emailAddress": {"address": e}} for e in to_recipients
            ],
        }
        if comment:
            data["comment"] = comment

        return await self._post_no_response(endpoint, data=data)

    async def move_message(
        self,
        mailbox: str,
        message_id: str,
        destination_folder_id: str,
    ) -> Optional[EmailMessageDTO]:
        """
        Move a message to a different folder.

        Args:
            mailbox: Email address of the mailbox
            message_id: ID of the message to move
            destination_folder_id: ID of the destination folder

        Returns:
            Updated message or None if failed
        """
        endpoint = f"users/{mailbox}/messages/{message_id}/move"
        data = {"destinationId": destination_folder_id}

        try:
            result = await self._post(endpoint, data=data)
            return EmailMessageDTO.model_validate(result)
        except Exception as e:
            logger.error(f"Error moving message {message_id}: {e}")
            return None

    async def update_message(
        self,
        mailbox: str,
        message_id: str,
        is_read: Optional[bool] = None,
        categories: Optional[List[str]] = None,
    ) -> bool:
        """
        Update message properties (e.g., mark as read/unread).

        Args:
            mailbox: Email address of the mailbox
            message_id: ID of the message to update
            is_read: Set read/unread status
            categories: Set categories

        Returns:
            True if successful
        """
        endpoint = f"users/{mailbox}/messages/{message_id}"

        data: Dict[str, Any] = {}
        if is_read is not None:
            data["isRead"] = is_read
        if categories is not None:
            data["categories"] = categories

        if not data:
            return True  # Nothing to update

        try:
            await self._patch(endpoint, data=data)
            return True
        except Exception as e:
            logger.error(f"Error updating message {message_id}: {e}")
            return False

    async def get_message_attachments(
        self,
        mailbox: str,
        message_id: str,
    ) -> List[EmailAttachmentDTO]:
        """
        Get attachments for a message.

        Args:
            mailbox: Email address of the mailbox
            message_id: ID of the message

        Returns:
            List of attachment metadata
        """
        endpoint = f"users/{mailbox}/messages/{message_id}/attachments"

        data = await self._get(endpoint)

        attachments = []
        for item in data.get("value", []):
            try:
                attachments.append(EmailAttachmentDTO.model_validate(item))
            except Exception as e:
                logger.warning(f"Error parsing attachment: {e}")

        return attachments

    async def download_attachment(
        self,
        mailbox: str,
        message_id: str,
        attachment_id: str,
    ) -> bytes:
        """
        Download an attachment.

        Args:
            mailbox: Email address of the mailbox
            message_id: ID of the message
            attachment_id: ID of the attachment

        Returns:
            Attachment content as bytes
        """
        endpoint = f"users/{mailbox}/messages/{message_id}/attachments/{attachment_id}/$value"
        return await self._get_binary(endpoint)

    async def delete_message(
        self,
        mailbox: str,
        message_id: str,
    ) -> bool:
        """
        Delete a message (moves to Deleted Items).

        Args:
            mailbox: Email address of the mailbox
            message_id: ID of the message to delete

        Returns:
            True if successful
        """
        endpoint = f"users/{mailbox}/messages/{message_id}"
        return await self._delete(endpoint)


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
