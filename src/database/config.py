# src/database/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
import os 
from dotenv import load_dotenv
load_dotenv()
class Settings(BaseSettings):
    database_url: str | None = None

    @property
    def DATABASE_URL(self) -> str:
        return os.environ.get("DATABASE_URL")

settings = Settings()
print(os.environ.get("DATABASE_URL"))