from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Private Security Lab"
    database_url: str
    session_secret: str
    encryption_key: str
    fingerprint_key: str
    environment: str = "development"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
