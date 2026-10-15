from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Cloud-Based AI-Powered Data Analyst Platform"
    environment: str = "local"
    max_upload_mb: int = 20
    database_url: str = "sqlite:///./data/app.db"
    azure_storage_connection_string: str | None = None
    azure_storage_container: str = "datasets"
    azure_sql_connection_string: str | None = None
    azure_key_vault_url: str | None = None
    llm_provider: str = "none"
    llm_api_key: str | None = None
    llm_model: str | None = None
    applicationinsights_connection_string: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings=Settings()
