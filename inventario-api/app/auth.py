"""
SISTEMA DE AUTENTICACIÓN

Maneja:
1. Encriptación de contraseñas (nunca guardamos contraseñas en texto plano)
2. Creación y validación de tokens JWT (como "carnets digitales temporales")
3. Generación de API Keys
4. Verificación de usuarios autenticados

CONCEPTOS:
- Hash: Proceso irreversible que convierte una contraseña en texto ilegible
- JWT: Token que contiene información del usuario y expira después de X tiempo
- API Key: Clave única por usuario para autenticación alternativa
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import secrets

from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import TokenData

# Configuración
settings = get_settings()

# ============================================
# CONFIGURACIÓN DE ENCRIPTACIÓN
# ============================================

# CryptContext maneja el "hash" de contraseñas con bcrypt
# bcrypt es un algoritmo muy seguro para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================
# FUNCIONES PARA CONTRASEÑAS
# ============================================

def hash_password(password: str) -> str:
    """
    Convierte una contraseña en texto plano a un hash seguro.
    
    IMPORTANTE: Esto es irreversible. No puedes obtener la contraseña original.
    
    Args:
        password: Contraseña en texto plano (ej: "mipassword123")
    
    Retorna:
        str: Contraseña hasheada (ej: "$2b$12$KIX...")
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash.
    
    Args:
        plain_password: Contraseña en texto plano que el usuario envió
        hashed_password: Hash guardado en la base de datos
    
    Retorna:
        bool: True si coinciden, False si no
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================
# FUNCIONES PARA API KEYS
# ============================================

def generate_api_key() -> str:
    """
    Genera una API Key única y segura.
    
    La API Key tiene el formato: sk_XXXXXXXXXXXX
    donde XXXX son caracteres aleatorios seguros.
    
    Retorna:
        str: API Key (ej: "sk_a1b2c3d4e5f6g7h8")
    """
    # secrets.token_urlsafe genera texto aleatorio seguro
    random_part = secrets.token_urlsafe(32)
    return f"sk_{random_part}"


# ============================================
# FUNCIONES PARA JWT (Tokens)
# ============================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT (JSON Web Token).
    
    Un JWT es como un "carnet digital temporal" que contiene:
    - ID del usuario
    - Email del usuario
    - Fecha de expiración
    
    El cliente debe enviar este token en cada petición para autenticarse.
    
    Args:
        data: Diccionario con datos a incluir en el token (user_id, email)
        expires_delta: Tiempo hasta que expire (opcional)
    
    Retorna:
        str: Token JWT codificado
    """
    to_encode = data.copy()
    
    # Calcular cuándo expira el token
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Por defecto, expira en 30 días
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    # Agregar la fecha de expiración al token
    to_encode.update({"exp": expire})
    
    # Codificar el token con nuestra clave secreta
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """
    Decodifica un token JWT y extrae la información del usuario.
    
    Args:
        token: Token JWT a decodificar
    
    Retorna:
        TokenData: Datos del usuario extraídos del token
    
    Raises:
        HTTPException: Si el token es inválido o expiró
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar el token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Extraer los datos
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            raise credentials_exception
        
        return TokenData(user_id=user_id, email=email)
    
    except JWTError:
        raise credentials_exception


# ============================================
# AUTENTICACIÓN DE USUARIOS
# ============================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Autentica a un usuario verificando su email y contraseña.
    
    Args:
        db: Sesión de base de datos
        email: Email del usuario
        password: Contraseña en texto plano
    
    Retorna:
        User: Usuario si las credenciales son correctas
        None: Si las credenciales son incorrectas
    """
    # Buscar usuario por email
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    # Verificar contraseña
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


# ============================================
# DEPENDENCIAS PARA RUTAS PROTEGIDAS
# ============================================

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Obtiene el usuario actual desde el token JWT o API Key.
    
    Esta función se usa como dependencia en las rutas protegidas:
    
    @app.get("/productos")
    def listar_productos(current_user: User = Depends(get_current_user)):
        # Solo usuarios autenticados pueden acceder aquí
        ...
    
    Soporta dos métodos de autenticación:
    1. Bearer Token (JWT): Authorization: Bearer eyJhbGc...
    2. API Key: Authorization: Bearer sk_abc123...
    
    Args:
        authorization: Header Authorization de la petición
        db: Sesión de base de datos
    
    Retorna:
        User: Usuario autenticado
    
    Raises:
        HTTPException: Si no está autenticado o el token/key es inválido
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not authorization:
        raise credentials_exception
    
    # El formato debe ser: "Bearer TOKEN_O_API_KEY"
    parts = authorization.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise credentials_exception
    
    token_or_key = parts[1]
    
    # Determinar si es un JWT o una API Key
    if token_or_key.startswith("sk_"):
        # Es una API Key
        user = db.query(User).filter(User.api_key == token_or_key).first()
        if not user:
            raise credentials_exception
        return user
    else:
        # Es un JWT
        token_data = decode_access_token(token_or_key)
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user:
            raise credentials_exception
        return user


# ============================================
# EJEMPLO DE USO EN UNA RUTA
# ============================================
#
# from fastapi import APIRouter, Depends
# from app.auth import get_current_user
# from app.models import User
#
# router = APIRouter()
#
# @router.get("/mi-perfil")
# def obtener_perfil(current_user: User = Depends(get_current_user)):
#     """Solo usuarios autenticados pueden ver su perfil."""
#     return {
#         "nombre": current_user.nombre,
#         "email": current_user.email
#     }
