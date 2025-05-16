from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    database_url: str | None = None

    # API configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # CORS configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]


settings = Settings()