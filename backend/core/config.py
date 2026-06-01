from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # теперь указывает на backend/

class Settings(BaseSettings):
    DATABASE_URL: str

    model_config = {"env_file": str(BASE_DIR / ".env")}

settings = Settings()