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
    ANALYSIS_MODE: Literal["simulated", "real", "both"] = "both"
    
    # Onionoo API Configuration
    ONIONOO_CACHE_TTL_SECONDS: int = 3600  # 1 hour
    ONIONOO_BANDWIDTH_ENDPOINT: str = "https://onionoo.torproject.org/bandwidth"
    ONIONOO_WEIGHTS_ENDPOINT: str = "https://onionoo.torproject.org/weights"
    ONIONOO_REQUEST_TIMEOUT: int = 30
    ONIONOO_MAX_RETRIES: int = 3
    ENABLE_RELAY_CACHE: bool = True
    CACHE_CLEANUP_INTERVAL_HOURS: int = 24
    
    # Real Traffic Analysis
    TRAFFIC_LOG_UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    REAL_TRAFFIC_AUTO_ANALYZE: bool = True
    EXPECTED_REAL_ACCURACY: float = 0.25  # 25% expected for real Tor traffic
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
