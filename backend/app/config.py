from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # Database
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_NAME: str = "tor_unveil"
    DB_USER: str = "tor_user"
    DB_PASSWORD: str = "tor_password"
    
    # Backend
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG: bool = True
    
    # Data Source
    DATA_SOURCE: Literal["sample", "live", "both"] = "sample"
    
    # Tor API
    TOR_ONIONOO_API: str = "https://onionoo.torproject.org"
    
    # Analysis
    DEFAULT_TOP_N: int = 10
    DEFAULT_SIMULATION_COUNT: int = 100
    DEFAULT_RANDOM_SEED: int = 42
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
