from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/barghouth"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)


settings = Settings()
