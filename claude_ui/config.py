from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Settings
    app_name: str = "Claude UI"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./claude_ui.db"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Claude Code Settings
    claude_code_path: str = "claude"
    max_instances: int = 5
    default_timeout: int = 120000  # 2 minutes in milliseconds
    
    # Session Settings
    session_cleanup_interval: int = 3600  # 1 hour
    max_session_age_days: int = 30
    
    # File Storage
    upload_dir: Path = Path("./uploads")
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    
    # Git Settings
    default_worktree_base: Path = Path("./worktrees")
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # MCP Settings
    mcp_config_path: Optional[Path] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.default_worktree_base.mkdir(parents=True, exist_ok=True)


# Create a singleton instance
settings = Settings()