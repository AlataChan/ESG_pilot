import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, field_validator, ValidationInfo, Field, computed_field, SecretStr
from typing import Optional, Dict, Any

# Determine the environment and load the appropriate .env file
env_state = os.getenv("ENV_STATE", "development")
env_file_path = ".env"  # Default

if env_state == "test":
    # For tests, we expect .env.test to be in the same directory as config.py
    env_file_path = os.path.join(os.path.dirname(__file__), ".env.test")
    if not os.path.exists(env_file_path):
        # Fallback to the root .env if .env.test is not found in the core dir
        env_file_path = ".env" 
elif env_state == "docker":
    # In a docker container, we expect the .env file at the root
    env_file_path = "/app/.env"

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables and .env files.
    """
    # Environment state: 'docker', 'local', 'test'
    ENV_STATE: str = "docker"

    # Core project settings
    PROJECT_NAME: str = "ESG-Copilot"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS settings - 支持常用的前端开发端口
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "http://localhost:5173",  # Vite默认端口
        "http://127.0.0.1:5173"
    ]

    # Pydantic automatically reads from environment variables.
    # It will also automatically load from a .env file in the same directory.
    # For more robust loading, we explicitly specify the .env file.
    model_config = SettingsConfigDict(env_file=env_file_path, extra="ignore", env_file_encoding='utf-8')

    # --- Database Settings ---
    # These are now dynamic based on the environment
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_NAME: Optional[str] = None
    
    # For local development with SQLite
    SQLITE_DB_PATH: str = "esg_copilot_dev.db"

    # Dynamic Database DSN (Data Source Name)
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        
        env_state = info.data.get("ENV_STATE", "development")
        
        if env_state in ["local", "test"]:
            # Use SQLite for local development and testing
            db_path = info.data.get("SQLITE_DB_PATH", "default.db")
            return f"sqlite+pysqlite:///{db_path}"
        
        # For Docker/production, only build if DB_HOST is provided
        if not info.data.get("DB_HOST"):
            return None # Avoid validation error during test collection

        return str(PostgresDsn.build(
            scheme="postgresql+psycopg2",
            username=info.data.get("DB_USER"),
            password=info.data.get("DB_PASSWORD"),
            host=info.data.get("DB_HOST"),
            port=info.data.get("DB_PORT"),
            path=f"/{info.data.get('DB_NAME') or ''}",
        ))
    
    @property
    def DATABASE_URL(self) -> Optional[str]:
        """兼容现有代码的DATABASE_URL属性"""
        return self.SQLALCHEMY_DATABASE_URI

    # DeepSeek Settings
    DEEPSEEK_API_KEY: Optional[SecretStr] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-reasoner"
    
    # 保持OpenAI兼容性，用于embedding
    OPENAI_API_KEY: Optional[SecretStr] = None
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-large"
    EMBEDDING_DIM: int = 3072

    # --- Vector Store Settings (ChromaDB) ---
    CHROMA_DB_HOST: Optional[str] = None
    CHROMA_DB_PORT: Optional[int] = None
    CHROMA_DB_PATH: str = "chroma_db_data"  # Default for local/test persistent storage
    CHROMA_COLLECTION_NAME: str = "esg_collection"

    def build_connection_string(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql",
                username=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT,
                path=f"/{self.DB_NAME}"
            )
        )

settings = Settings() 