"""
RUTAS: PRODUCTOS

Define todos los endpoints relacionados con productos.

ENDPOINTS:
- POST /products          → Crear producto
- GET /products           → Listar productos
- GET /products/{id}      → Obtener un producto
- PUT /products/{id}      → Actualizar producto
- PUT /products/{id}/stock → Actualizar solo el stock
- DELETE /products/{id}   → Eliminar producto
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.schemas import (
    ProductCreate, 
    ProductUpdate, 
    StockUpdate,
    ProductResponse, 
    ProductListResponse
)
from app.services import (
    crear_producto,
    listar_productos,
    obtener_producto,
    actualizar_producto,
    actualizar_stock,
    eliminar_producto
)

# Crear el router
router = APIRouter(
    prefix="/products",
    tags=["Productos"]
)


# ============================================
# CREAR PRODUCTO
# ============================================

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo producto",
    description="""
    Crea un nuevo producto en el inventario.
    
    **Campos requeridos:**
    - nombre: Nombre descriptivo del producto
    - sku: Código único del producto (no se puede repetir)
    - stock_actual: Cantidad inicial en inventario
    - stock_minimo: Cantidad mínima antes de enviar alerta
    
    **Requiere autenticación.**
    """
)
def crear_nuevo_producto(
    producto: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para crear un producto.
    
    El producto se asocia automáticamente al usuario autenticado.
    """
    return crear_producto(db, producto, current_user)


# ============================================
# LISTAR PRODUCTOS
# ============================================

@router.get(
    "",
    response_model=ProductListResponse,
    summary="Listar productos",
    description="""
    Lista todos los productos del usuario autenticado.
    
    **Filtros disponibles:**
    - stock_bajo: Si es true, solo muestra productos con stock bajo el mínimo
    
    **Paginación:**
    - skip: Número de productos a saltar
    - limit: Máximo de productos a devolver
    
    **Requiere autenticación.**
    """
)
def listar_mis_productos(
    skip: int = Query(0, ge=0, description="Productos a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de productos"),
    stock_bajo: Optional[bool] = Query(None, description="Filtrar por stock bajo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para listar productos.
    
    Devuelve solo los productos del usuario autenticado.
    """
    productos = listar_productos(db, current_user, skip, limit, stock_bajo)
    
    return {
        "total": len(productos),
        "products": productos
    }


# ============================================
# OBTENER UN PRODUCTO
# ============================================

@router.get(
    "/{producto_id}",
    response_model=ProductResponse,
    summary="Obtener un producto específico",
    description="""
    Obtiene los detalles de un producto por su ID.
    
    **Requiere autenticación.**
    Solo se puede ver productos propios.
    """
)
def obtener_detalle_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obtener un producto específico.
    """
    return obtener_producto(db, producto_id, current_user)


# ============================================
# ACTUALIZAR PRODUCTO (COMPLETO)
# ============================================

@router.put(
    "/{producto_id}",
    response_model=ProductResponse,
    summary="Actualizar un producto",
    description="""
    Actualiza los datos de un producto existente.
    
    Puedes actualizar cualquiera de estos campos:
    - nombre
    - sku
    - stock_actual
    - stock_minimo
    
    **Requiere autenticación.**
    Solo puedes actualizar tus propios productos.
    """
)
def actualizar_datos_producto(
    producto_id: int,
    producto: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para actualizar un producto.
    """
    return actualizar_producto(db, producto_id, producto, current_user)


# ============================================
# ACTUALIZAR SOLO EL STOCK
# ============================================

@router.put(
    "/{producto_id}/stock",
    response_model=ProductResponse,
    summary="Actualizar el stock de un producto",
    description="""
    Actualiza únicamente el stock de un producto.
    
    Este endpoint es útil cuando recibes mercancía nueva
    y quieres aumentar el stock manualmente.
    
    **Nota:** El stock también se descuenta automáticamente
    al registrar ventas usando POST /sales
    
    **Requiere autenticación.**
    """
)
def actualizar_stock_producto(
    producto_id: int,
    stock: StockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para actualizar solo el stock.
    
    Si el nuevo stock está por encima del mínimo,
    se resetea la bandera de alerta.
    
    Si el nuevo stock está bajo el mínimo Y no se ha enviado alerta,
    se envía un email automáticamente.
    """
    return actualizar_stock(db, producto_id, stock, current_user)


# ============================================
# ELIMINAR PRODUCTO
# ============================================

@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un producto",
    description="""
    Elimina un producto del inventario.
    
    ⚠️ **ADVERTENCIA:** Esta acción no se puede deshacer.
    
    **Requiere autenticación.**
    Solo puedes eliminar tus propios productos.
    """
)
def eliminar_producto_endpoint(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para eliminar un producto.
    """
    eliminar_producto(db, producto_id, current_user)
    return None  # 204 No Content no devuelve body
