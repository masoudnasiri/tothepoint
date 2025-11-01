from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres123@localhost:5432/procurement_dss"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # CORS - Allow specific origins or use wildcard for development
    # In production, set ALLOWED_ORIGINS environment variable with comma-separated origins
    # Example: ALLOWED_ORIGINS=http://yourdomain.com,https://yourdomain.com
    # Set to "*" to allow all origins (for development only)
    allowed_origins: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def get_allowed_origins(self) -> List[str]:
        """Get list of allowed origins, handling wildcard and comma-separated values"""
        if self.allowed_origins:
            if self.allowed_origins == "*":
                return ["*"]  # Allow all origins
            # Parse comma-separated origins
            return [origin.strip() for origin in self.allowed_origins.split(",")]
        
        # Default based on environment
        if self.environment == "production":
            return ["http://localhost:3000"]
        else:
            # Development: allow all origins for flexibility (Docker, remote access, etc.)
            return ["*"]


settings = Settings()
