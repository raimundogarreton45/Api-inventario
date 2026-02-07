"""
APLICACIÓN PRINCIPAL - API DE INVENTARIO PYME

Este es el archivo principal que:
1. Crea la aplicación FastAPI
2. Configura CORS (para permitir peticiones desde navegadores)
3. Registra todas las rutas
4. Inicializa la base de datos
5. Configura la documentación automática

Para correr la aplicación:
    uvicorn app.main:app --reload

La documentación estará disponible en:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.routes import auth, products, sales

settings = get_settings()


# ============================================
# CONFIGURACIÓN DE INICIO Y CIERRE
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Función que se ejecuta al iniciar y cerrar la aplicación.
    
    Startup: Inicializa las tablas de la base de datos
    Shutdown: Limpia recursos si es necesario
    """
    # STARTUP: Se ejecuta al iniciar
    print("🚀 Iniciando API de Inventario...")
    print(f"📝 Entorno: {settings.environment}")
    
    # Crear tablas en la base de datos
    init_db()
    
    print("✅ API lista para recibir peticiones")
    print("📖 Documentación disponible en: http://localhost:8000/docs")
    
    yield  # La aplicación corre aquí
    
    # SHUTDOWN: Se ejecuta al cerrar
    print("👋 Cerrando API de Inventario...")


# ============================================
# CREAR LA APLICACIÓN FASTAPI
# ============================================

app = FastAPI(
    title="API de Inventario para PYME",
    description="""
    ## 🏪 Sistema de Control de Inventario
    
    API REST para gestión de inventario diseñada para pequeñas empresas chilenas.
    
    ### Características principales:
    
    * 📦 **Gestión de Productos**: Crear, listar, actualizar y eliminar productos
    * 💰 **Registro de Ventas**: Las ventas descuentan el stock automáticamente
    * ⚠️ **Alertas Automáticas**: Recibe emails cuando el stock está bajo
    * 🔐 **Autenticación Segura**: JWT tokens y API Keys
    * 👤 **Multi-usuario**: Cada usuario solo ve sus propios productos
    
    ### Cómo empezar:
    
    1. **Registrarse**: `POST /auth/register`
    2. **Iniciar sesión**: `POST /auth/login` (obtienes un token)
    3. **Crear productos**: `POST /products`
    4. **Registrar ventas**: `POST /sales`
    
    ### Autenticación:
    
    Todas las rutas (excepto registro y login) requieren autenticación.
    
    **Opción 1: JWT Token** (recomendado)
    ```
    Authorization: Bearer {token_obtenido_en_login}
    ```
    
    **Opción 2: API Key**
    ```
    Authorization: Bearer {tu_api_key}
    ```
    
    La API Key se obtiene al registrarse y no expira.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Documentación interactiva (Swagger)
    redoc_url="/redoc"  # Documentación alternativa (ReDoc)
)


# ============================================
# CONFIGURAR CORS
# ============================================
# CORS permite que navegadores web puedan hacer peticiones a esta API

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React/Next.js en desarrollo
        "http://localhost:5173",  # Vite en desarrollo
        "https://tu-dominio.cl",  # Tu dominio en producción
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Permite todos los headers
)


# ============================================
# REGISTRAR RUTAS
# ============================================

# Rutas de autenticación
app.include_router(auth.router)

# Rutas de productos
app.include_router(products.router)

# Rutas de ventas
app.include_router(sales.router)


# ============================================
# RUTA RAÍZ (HEALTH CHECK)
# ============================================

@app.get("/", tags=["Health"])
def root():
    """
    Endpoint raíz para verificar que la API está funcionando.
    
    Útil para:
    - Health checks
    - Monitoreo
    - Verificar que el servidor responde
    """
    return {
        "mensaje": "🏪 API de Inventario para PYME",
        "version": "1.0.0",
        "status": "✅ Funcionando",
        "documentacion": "/docs",
        "entorno": settings.environment
    }


# ============================================
# MANEJO DE ERRORES GLOBAL
# ============================================

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Maneja errores de validación de datos.
    
    Se ejecuta cuando el cliente envía datos con formato incorrecto.
    """
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Error de validación",
            "errors": exc.errors()
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Maneja errores de base de datos.
    
    Se ejecuta cuando hay un error en la comunicación con PostgreSQL.
    """
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error de base de datos",
            "mensaje": "Ocurrió un error al procesar tu petición. Por favor intenta de nuevo."
        }
    )


# ============================================
# PARA DESARROLLO LOCAL
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    # Correr el servidor
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload cuando cambies código (solo en desarrollo)
    )
