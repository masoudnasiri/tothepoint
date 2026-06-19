from pydantic_settings import BaseSettings
from typing import Optional, List
import os


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
    
    # Phase 3: Feature Flags for Package-Aware Procurement
    # Enable package-aware procurement operations (prefer package_id over project_item_id)
    enable_package_procurement: bool = os.getenv("ENABLE_PACKAGE_PROCUREMENT", "false").lower() == "true"
    
    # Allow legacy project_item_id/item_code operations when package_id not available
    legacy_project_item_fallback: bool = os.getenv("LEGACY_PROJECT_ITEM_FALLBACK", "true").lower() == "true"
    
    # Enforce supplier_id usage (block string-based supplier_name for new records)
    supplier_normalization_enforced: bool = os.getenv("SUPPLIER_NORMALIZATION_ENFORCED", "false").lower() == "true"
    
    # Enable package-based optimization (Phase 3 gradual rollout)
    enable_package_based_optimization: bool = os.getenv("ENABLE_PACKAGE_BASED_OPTIMIZATION", "false").lower() == "true"
    
    # Require package_id for new procurement options (stricter enforcement)
    require_package_id_for_new_options: bool = os.getenv("REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS", "false").lower() == "true"

    # Enforce full package/sub-item coverage before locking decisions
    enforce_package_coverage_on_lock: bool = os.getenv("ENFORCE_PACKAGE_COVERAGE_ON_LOCK", "false").lower() == "true"
    
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
