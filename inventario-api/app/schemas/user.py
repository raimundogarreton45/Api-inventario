"""
SCHEMAS: USUARIO

Los schemas definen QUÉ DATOS pueden entrar y salir de la API.

DIFERENCIA CON MODELS:
- Models (SQLAlchemy): Cómo se guardan los datos en la BD
- Schemas (Pydantic): Qué datos acepta/devuelve la API

EJEMPLO:
- Cuando creas un usuario, envías UserCreate (con contraseña)
- La API te devuelve UserResponse (sin contraseña, con api_key)
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# ============================================
# SCHEMA PARA CREAR USUARIOS
# ============================================

class UserCreate(BaseModel):
    """
    Datos necesarios para crear un nuevo usuario.
    
    Esto es lo que el cliente envía cuando quiere registrarse.
    """
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo del usuario")
    email: EmailStr = Field(..., description="Email único del usuario")
    password: str = Field(..., min_length=6, description="Contraseña (mínimo 6 caracteres)")
    
    class Config:
        # Ejemplo que aparece en la documentación automática
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "email": "juan@ejemplo.cl",
                "password": "mipassword123"
            }
        }


# ============================================
# SCHEMA PARA LOGIN
# ============================================

class UserLogin(BaseModel):
    """
    Datos para iniciar sesión.
    """
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "juan@ejemplo.cl",
                "password": "mipassword123"
            }
        }


# ============================================
# SCHEMA PARA RESPUESTAS
# ============================================

class UserResponse(BaseModel):
    """
    Datos que la API devuelve sobre un usuario.
    
    IMPORTANTE: Nunca devolvemos la contraseña por seguridad.
    """
    id: int
    nombre: str
    email: str
    api_key: str
    created_at: datetime
    
    class Config:
        # Permite que Pydantic lea datos de modelos SQLAlchemy
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "nombre": "Juan Pérez",
                "email": "juan@ejemplo.cl",
                "api_key": "sk_abc123xyz789",
                "created_at": "2024-02-06T10:30:00"
            }
        }


# ============================================
# SCHEMA PARA TOKEN DE AUTENTICACIÓN
# ============================================

class Token(BaseModel):
    """
    Respuesta después de login exitoso.
    
    El access_token es como un "pase temporal" que el cliente
    debe enviar en cada petición para autenticarse.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "nombre": "Juan Pérez",
                    "email": "juan@ejemplo.cl",
                    "api_key": "sk_abc123xyz789",
                    "created_at": "2024-02-06T10:30:00"
                }
            }
        }


# ============================================
# SCHEMA PARA DATOS DEL TOKEN (Interno)
# ============================================

class TokenData(BaseModel):
    """
    Datos que se guardan dentro del token JWT.
    
    Esto es interno, el cliente no lo ve directamente.
    """
    user_id: Optional[int] = None
    email: Optional[str] = None
