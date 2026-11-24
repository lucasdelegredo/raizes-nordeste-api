"""Configurações da aplicação, lidas do ambiente / arquivo .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "API Raízes do Nordeste"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"

    DATABASE_URL: str = "postgresql+psycopg://raizes:raizes123@localhost:5432/raizes_nordeste"

    JWT_SECRET: str = "troque-este-segredo"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
