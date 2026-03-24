"""Configuração central (Fase 1: env simples; Fase 2: OAuth e secrets)."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TTV-Torneios API"
    database_url: str = "mysql+pymysql://ttv:ttv_secret@127.0.0.1:3306/ttv_torneios"
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_MVP_ONLY"
    access_token_expire_minutes: int = 60 * 24
    # OAuth (Fase 2)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    # Callback no backend (Google redireciona aqui)
    oauth_redirect_uri: str = "http://127.0.0.1:8000/auth/google/callback"
    frontend_url: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
