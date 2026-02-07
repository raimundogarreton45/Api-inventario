"""
RUTAS: AUTENTICACIÓN Y USUARIOS

Define los endpoints para registro, login y gestión de usuarios.

ENDPOINTS:
- POST /auth/register  → Registrar nuevo usuario
- POST /auth/login     → Iniciar sesión
- GET /auth/me         → Obtener perfil del usuario actual
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.auth import (
    hash_password, 
    generate_api_key, 
    authenticate_user,
    create_access_token,
    get_current_user
)
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse, Token

# Crear el router
router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)


# ============================================
# REGISTRAR NUEVO USUARIO
# ============================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="""
    Crea una nueva cuenta de usuario.
    
    **Campos requeridos:**
    - nombre: Nombre completo
    - email: Email único (no puede repetirse)
    - password: Contraseña (mínimo 6 caracteres)
    
    **Respuesta:**
    - Devuelve los datos del usuario creado
    - Incluye la API Key que puede usarse para autenticación
    
    **Nota:** La contraseña se guarda encriptada, nunca en texto plano.
    """
)
def registrar_usuario(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Endpoint para registrar un nuevo usuario.
    
    Crea un usuario con:
    - Contraseña hasheada (encriptada)
    - API Key única generada automáticamente
    """
    try:
        # Crear el usuario
        nuevo_usuario = User(
            nombre=user_data.nombre,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            api_key=generate_api_key()
        )
        
        # Guardar en la base de datos
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        
        return nuevo_usuario
    
    except IntegrityError:
        db.rollback()
        # IntegrityError ocurre si el email ya existe
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El email '{user_data.email}' ya está registrado"
        )


# ============================================
# INICIAR SESIÓN
# ============================================

@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
    description="""
    Autentica a un usuario y devuelve un token de acceso.
    
    **Campos requeridos:**
    - email: Email registrado
    - password: Contraseña
    
    **Respuesta:**
    - access_token: Token JWT para usar en peticiones posteriores
    - token_type: Siempre es "bearer"
    - user: Datos del usuario autenticado
    
    **Uso del token:**
    Incluye el token en el header Authorization de tus peticiones:
    ```
    Authorization: Bearer {access_token}
    ```
    
    **Alternativa: Usar API Key**
    También puedes autenticarte con tu API Key:
    ```
    Authorization: Bearer {api_key}
    ```
    """
)
def iniciar_sesion(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Endpoint para iniciar sesión.
    
    Verifica las credenciales y devuelve un token JWT.
    """
    # Autenticar usuario
    usuario = authenticate_user(db, credentials.email, credentials.password)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token JWT
    access_token = create_access_token(
        data={
            "user_id": usuario.id,
            "email": usuario.email
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": usuario
    }


# ============================================
# OBTENER PERFIL DEL USUARIO ACTUAL
# ============================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener perfil del usuario actual",
    description="""
    Devuelve la información del usuario autenticado.
    
    **Requiere autenticación.**
    
    Este endpoint es útil para:
    - Verificar que el token es válido
    - Obtener datos actualizados del usuario
    - Mostrar información del perfil en tu app
    """
)
def obtener_mi_perfil(
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obtener el perfil del usuario actual.
    
    El usuario se obtiene automáticamente del token JWT o API Key.
    """
    return current_user


# ============================================
# ENDPOINT DE PRUEBA (solo para development)
# ============================================

@router.get(
    "/test",
    summary="Endpoint de prueba",
    description="Endpoint público para verificar que la API está funcionando."
)
def test_endpoint():
    """
    Endpoint simple para verificar que la API responde.
    
    No requiere autenticación.
    """
    return {
        "mensaje": "✅ API de Inventario funcionando correctamente",
        "version": "1.0.0",
        "docs": "/docs"
    }
