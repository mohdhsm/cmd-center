"""Configuration management for Command Center."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    """Application configuration from environment variables."""
    
    # Pipedrive - matching .env variable names
    pipedrive_api_token: str = Field(default="", alias="pipedrive_api_token")
    pipedrive_api_url: str = Field(default="https://api.pipedrive.com/v1", alias="pipedrive_base_url")
    pipedrive_api_urlv2: str = Field(default="https://api.pipedrive.com/api/v2", alias="pipedrive_base_url2")
    
    # OpenRouter / LLM - matching .env variable names
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_api_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = Field(default="anthropic/claude-3.5-sonnet", alias="OPENROUTER_MODEL")

    # microsoft onedrive configurtation
    onedrive_file_id: str = Field(default="", alias="ONEDRIVE_FILE_ID")
    onedrive_drive_id: str = Field(default="", alias="ONEDRIVE_DRIVE_ID")
    onedrive_user_id: str = Field(default="", alias="ONEDRIVE_USER_ID")

    # microsoft graph
    client_id: str = Field(default="", alias="CLIENT_ID")
    client_secret: str = Field(default="", alias="CLIENT_SECRET")
    tenant_id: str = Field(default="", alias="TENANT_ID")
    microsoft_scope: str = Field(default="https://graph.microsoft.com/.default", alias="MICROSODFT_SCOPE")
    # Email (SMTP)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # LLAMA cloud for ocr and other tasks
    llama_cloud_api_key: str = Field(default="", alias="Llama_cloud_api_key")



    # FastAPI
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    
    # Pipedrive configuration
    aramco_pipeline_name: str = "Aramco Projects"
    commercial_pipeline_name: str = "pipeline"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True  # Allow both field name and alias


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create config singleton."""
    global _config
    if _config is None:
        _config = Config()
    return _config