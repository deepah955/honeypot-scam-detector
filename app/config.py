"""
Application configuration using Pydantic Settings
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: str | None = Field(default=None, env="REDIS_PASSWORD")
    
    # API Security
    api_keys: str = Field(default="", env="API_KEYS")
    
    # Application Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Memory Settings
    memory_ttl_seconds: int = Field(default=86400, env="MEMORY_TTL_SECONDS")
    use_redis_fallback: bool = Field(default=True, env="USE_REDIS_FALLBACK")
    
    @property
    def api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys into list"""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
