from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Private Security Lab"
    database_url: str
    session_secret: str
    encryption_key: str
    fingerprint_key: str
    bootstrap_token: str = ""
    environment: str = "development"
    cookie_secure: bool = True
    login_window_seconds: int = 900
    login_max_failures: int = 8
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
