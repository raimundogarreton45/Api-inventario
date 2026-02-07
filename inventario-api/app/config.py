"""
CONFIGURACIÓN DE LA APLICACIÓN

Este archivo lee todas las variables de entorno del archivo .env
y las hace disponibles para el resto de la aplicación.

Piensa en esto como el "panel de control" de tu API.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configuración de la aplicación.
    
    Pydantic lee automáticamente las variables del archivo .env
    y las convierte a los tipos correctos (str, int, bool, etc.)
    """
    
    # Nombre de la aplicación
    app_name: str = "API Inventario PYME"
    
    # Base de datos - URL de conexión a PostgreSQL/Supabase
    database_url: str
    
    # Seguridad - Para crear tokens JWT (como "carnets digitales")
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 días por defecto
    
    # SendGrid - Para enviar emails
    sendgrid_api_key: str
    sendgrid_from_email: str
    
    # Entorno (development o production)
    environment: str = "development"
    
    class Config:
        # Le dice a Pydantic dónde buscar las variables
        env_file = ".env"
        # Permite mayúsculas y minúsculas
        case_sensitive = False


# Decorador @lru_cache hace que esto se ejecute solo una vez
# Así no leemos el archivo .env cada vez que necesitamos la configuración
@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la configuración de la aplicación.
    
    Retorna:
        Settings: Objeto con toda la configuración
    """
    return Settings()


# Para usar en otros archivos:
# from app.config import get_settings
# settings = get_settings()
# print(settings.database_url)
