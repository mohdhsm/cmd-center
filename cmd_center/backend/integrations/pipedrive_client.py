"""Pipedrive API client."""

import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .config import get_config


class PipedriveDealDTO(BaseModel):
    """DTO for Pipedrive deal response."""
    
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    
    id: int
    title: str
    pipeline_id: Optional[int] = None
    stage_id: Optional[int] = None
    # Pipedrive returns user/org/person as nested objects; normalize to IDs and keep names
    owner_id: Optional[int] = Field(default=None, alias="user_id")
    owner_name: Optional[str] = None
    creator_id: Optional[int] = Field(default=None, alias="creator_user_id")
    creator_name: Optional[str] = None
    org_id: Optional[int] = None
    org_name: Optional[str] = None
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    value: Optional[float] = None
    add_time: Optional[str] = None
    update_time: Optional[str] = None
    last_activity_date: Optional[str] = None
    status: Optional[str] = None

    @staticmethod
    def _extract_id(value: Any) -> Optional[int]:
        """Handle int or nested dict formats from Pipedrive API."""
        if isinstance(value, dict):
            return value.get("value") or value.get("id")
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value
    
    @staticmethod
    def _extract_name(value: Any) -> Optional[str]:
        if isinstance(value, dict):
            return value.get("name")
        return None

    @field_validator("owner_id", "org_id", "person_id", mode="before")
    @classmethod
    def normalize_nested_ids(cls, v):
        return cls._extract_id(v)
    
    @field_validator("owner_name", mode="before")
    @classmethod
    def normalize_owner_name(cls, v, info):
        raw_user = info.data.get("user_id") or info.data.get("owner_id")
        return v or cls._extract_name(raw_user)
    
    @field_validator("creator_id", mode="before")
    @classmethod
    def normalize_creator_id(cls, v):
        return cls._extract_id(v)
    
    @field_validator("creator_name", mode="before")
    @classmethod
    def normalize_creator_name(cls, v, info):
        raw_creator = info.data.get("creator_user_id") or info.data.get("creator_id")
        return v or cls._extract_name(raw_creator)
    
    @field_validator("org_name", mode="before")
    @classmethod
    def normalize_org_name(cls, v, info):
        raw_org = info.data.get("org_id")
        return v or cls._extract_name(raw_org)
    
    @field_validator("person_name", mode="before")
    @classmethod
    def normalize_person_name(cls, v, info):
        raw_person = info.data.get("person_id")
        return v or cls._extract_name(raw_person)


class PipedriveNoteDTO(BaseModel):
    """DTO for Pipedrive note response."""

    id: int
    content: str
    add_time: str
    user_id: Optional[int] = None


class PipedriveDealChangeDTO(BaseModel):
    """Single change event from flow API."""
    model_config = ConfigDict(extra="ignore")

    object: str  # "dealChange"
    timestamp: datetime
    data: Dict[str, Any]  # Contains id, field_key, old_value, new_value, log_time

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            # Handle Pipedrive format: "2025-09-14 11:31:17"
            from datetime import timezone
            return datetime.fromisoformat(v.replace(" ", "T")).replace(tzinfo=timezone.utc)
        return v


class PipedriveDealFlowDTO(BaseModel):
    """Response from /v1/deals/{id}/flow."""
    model_config = ConfigDict(extra="ignore")

    success: bool
    data: List[PipedriveDealChangeDTO] = []


class PipedriveClient:
    """Client for Pipedrive API operations."""
    
    def __init__(self, api_token: str, api_url: str,api_url_v2: str):
        self.api_token = api_token
        self.api_url = api_url
        self.api_url_v2 = api_url_v2
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to Pipedrive API."""
        if params is None:
            params = {}
        params["api_token"] = self.api_token
        
        url = f"{self.api_url}/{endpoint}"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def _get_v2(self,endpoint:str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to Pipedrive API v2."""
        if params is None:
            params = {}
        params["api_token"] = self.api_token

        url = f"{self.api_url_v2}/{endpoint}"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

  # General deal methodd 
    async def get_deals(
        self,
        pipeline_id: Optional[int] = None,
        stage_id: Optional[int] = None,
        owner_id: Optional[int] = None,
        status: str = "all_not_deleted",
        limit: int = 500,
    ) -> List[PipedriveDealDTO]:
        """Get deals from Pipedrive."""
        params = {
            "status": status,
            "limit": limit,
        }

        if pipeline_id:
            params["pipeline_id"] = pipeline_id
        if stage_id:
            params["stage_id"] = stage_id
        if owner_id:
            params["owner_id"] = owner_id
        if status:
            params["status"] = status
        
        data = await self._get_v2("deals", params)
        
        deals = []
        if data.get("success") and data.get("data"):
            for item in data["data"]:
                try:
                    deals.append(PipedriveDealDTO(**item))
                except Exception as e:
                    print(f"Error parsing deal {item.get('id')}: {e}")
        
        return deals

   # Get single deal by ID 
    async def get_deal(self, deal_id: int) -> Optional[PipedriveDealDTO]:
        """Get a single deal by ID."""
        data = await self._get(f"deals/{deal_id}")
        
        if data.get("success") and data.get("data"):
            try:
                return PipedriveDealDTO(**data["data"])
            except Exception as e:
                print(f"Error parsing deal {deal_id}: {e}")
        
        return None
    
    async def get_deal_notes(self, deal_id: int) -> List[PipedriveNoteDTO]:
        """Get notes for a deal."""
        data = await self._get(f"deals/{deal_id}/notes")

        notes = []
        if data.get("success") and data.get("data"):
            for item in data["data"]:
                try:
                    notes.append(PipedriveNoteDTO(**item))
                except Exception as e:
                    print(f"Error parsing note: {e}")

        return notes

    async def get_deal_flow(
        self,
        deal_id: int,
        start: int = 0,
        all_changes: bool = True,
        items: str = "dealChange"
    ) -> Optional[PipedriveDealFlowDTO]:
        """Get deal flow/history from Pipedrive.

        Args:
            deal_id: Deal ID
            start: Pagination offset
            all_changes: Include all changes (not just important ones)
            items: Filter by item type (default: dealChange)
        """
        try:
            data = await self._get(
                f"deals/{deal_id}/flow",
                params={
                    "start": start,
                    "all_changes": 1 if all_changes else 0,
                    "items": items
                }
            )

            if data.get("success"):
                return PipedriveDealFlowDTO(**data)
            return None
        except Exception as e:
            print(f"Error fetching flow for deal {deal_id}: {e}")
            return None

    async def get_pipelines(self) -> List[Dict[str, Any]]:
        """Get all pipelines."""
        data = await self._get("pipelines")
        
        if data.get("success") and data.get("data"):
            return data["data"]
        
        return []

    async def get_stages(self, pipeline_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get stages, optionally filtered by pipeline."""
        params: Dict[str, Any] = {}
        if pipeline_id:
            params["pipeline_id"] = pipeline_id

        data = await self._get("stages", params)

        if data.get("success") and data.get("data"):
            return data["data"]

        return []
    
    async def get_pipeline_id(self, pipeline_name: str) -> Optional[int]:
        """Get pipeline ID by name."""
        pipelines = await self.get_pipelines()
        
        for pipeline in pipelines:
            if pipeline.get("name") == pipeline_name:
                return pipeline.get("id")
        
        return None
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        data = await self._get("users")
        
        if data.get("success") and data.get("data"):
            return data["data"]
        
        return []
# Utilitt function to convert date to RFC 3339 format



# Global client instance
_pipedrive_client: Optional[PipedriveClient] = None


def get_pipedrive_client() -> PipedriveClient:
    """Get or create Pipedrive client singleton."""
    global _pipedrive_client
    if _pipedrive_client is None:
        config = get_config()
        _pipedrive_client = PipedriveClient(
            api_token=config.pipedrive_api_token,
            api_url=config.pipedrive_api_url,
            api_url_v2=config.pipedrive_api_urlv2,
        )
    return _pipedrive_client

# TODO: Add method for from pipedrive v2 api for getting pipeline ID and mapping to name.
# TODO: add method from using pipedrive api v2, for getting stage id, and mapping it to its name.
# TODO: refix the dynamic methods so they can get the stage name from the pipeline ID.
# TODO: Refix the dynamic method to call the deals, based on pipeline id, and stage id, or owner
