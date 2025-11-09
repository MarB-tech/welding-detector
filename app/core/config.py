from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Klasa konfiguracyjna ładująca zmienne środowiskowe z pliku .env
    """
    # Konfiguracja kamery
    CAMERA_INDEX: int = 0
    
    # Konfiguracja aplikacji
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_TITLE: str = "Welding Detector API"
    APP_VERSION: str = "1.0.0"
    
    # Dodatkowe ustawienia (opcjonalne)
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton - jedna instancja dla całej aplikacji
settings = Settings()
