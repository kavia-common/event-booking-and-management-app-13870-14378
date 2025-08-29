import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    APP_NAME: str = Field(default="Event Service")
    APP_DESCRIPTION: str = Field(default="Event lifecycle management, discovery, and analytics.")
    APP_VERSION: str = Field(default="0.1.0")

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = Field(default_factory=lambda: os.getenv("CORS_ALLOW_ORIGINS", "*").split(","))
    CORS_ALLOW_CREDENTIALS: bool = Field(default=(os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"))
    CORS_ALLOW_METHODS: List[str] = Field(default_factory=lambda: os.getenv("CORS_ALLOW_METHODS", "*").split(","))
    CORS_ALLOW_HEADERS: List[str] = Field(default_factory=lambda: os.getenv("CORS_ALLOW_HEADERS", "*").split(","))

    # Security
    API_KEY_HEADER_NAME: str = Field(default=os.getenv("API_KEY_HEADER_NAME", "x-api-key"))
    INTERNAL_API_KEY: Optional[str] = Field(default=os.getenv("INTERNAL_API_KEY"))

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = Field(default=int(os.getenv("DEFAULT_PAGE_SIZE", "20")))
    MAX_PAGE_SIZE: int = Field(default=int(os.getenv("MAX_PAGE_SIZE", "100")))

    # Feature flags
    ENABLE_ADMIN_ANALYTICS: bool = Field(default=(os.getenv("ENABLE_ADMIN_ANALYTICS", "true").lower() == "true"))

    # External service placeholders (UserService integration, etc.)
    USER_SERVICE_BASE_URL: Optional[str] = Field(default=os.getenv("USER_SERVICE_BASE_URL"))
    BOOKING_SERVICE_BASE_URL: Optional[str] = Field(default=os.getenv("BOOKING_SERVICE_BASE_URL"))


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
