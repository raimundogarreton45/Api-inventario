"""
RUTAS: VENTAS

Define todos los endpoints relacionados con ventas.

ENDPOINTS:
- POST /sales       → Registrar una venta (descuenta stock automáticamente)
- GET /sales        → Listar ventas
- GET /sales/{id}   → Obtener una venta específica
- GET /sales/stats  → Obtener estadísticas de ventas
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.schemas import (
    SaleCreate,
    SaleResponse,
    SaleConfirmation,
    SaleListResponse
)
from app.services import (
    registrar_venta,
    listar_ventas,
    obtener_venta,
    obtener_estadisticas_ventas
)

# Crear el router
router = APIRouter(
    prefix="/sales",
    tags=["Ventas"]
)


# ============================================
# REGISTRAR VENTA
# ============================================

@router.post(
    "",
    response_model=SaleConfirmation,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva venta",
    description="""
    Registra una venta y descuenta el stock automáticamente.
    
    **Flujo automático:**
    1. Verifica que el producto existe
    2. Verifica que hay stock suficiente
    3. Descuenta el stock
    4. Crea el registro de venta
    5. Si el stock queda bajo el mínimo, envía alerta por email
    
    **Campos requeridos:**
    - producto_id: ID del producto a vender
    - cantidad: Cantidad a vender
    
    **Requiere autenticación.**
    """
)
def registrar_nueva_venta(
    venta: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para registrar una venta.
    
    Descuenta automáticamente el stock y envía alertas si es necesario.
    """
    # Registrar la venta (el servicio maneja toda la lógica)
    venta_registrada, alerta_enviada = registrar_venta(db, venta, current_user)
    
    # Construir el mensaje de respuesta
    if alerta_enviada:
        mensaje = f"✅ Venta registrada. ⚠️ Stock bajo mínimo. Se envió alerta por email."
    else:
        mensaje = f"✅ Venta registrada exitosamente."
    
    # Preparar la respuesta con información enriquecida
    return {
        "venta": {
            "id": venta_registrada.id,
            "producto_id": venta_registrada.producto_id,
            "cantidad": venta_registrada.cantidad,
            "fecha": venta_registrada.fecha,
            "producto_nombre": venta_registrada.product.nombre,
            "producto_sku": venta_registrada.product.sku,
            "stock_restante": venta_registrada.product.stock_actual
        },
        "alerta_enviada": alerta_enviada,
        "mensaje": mensaje
    }


# ============================================
# LISTAR VENTAS
# ============================================

@router.get(
    "",
    response_model=SaleListResponse,
    summary="Listar ventas",
    description="""
    Lista todas las ventas del usuario autenticado.
    
    **Filtros disponibles:**
    - producto_id: Filtrar ventas de un producto específico
    
    **Paginación:**
    - skip: Número de ventas a saltar
    - limit: Máximo de ventas a devolver
    
    Las ventas se devuelven ordenadas por fecha (más recientes primero).
    
    **Requiere autenticación.**
    """
)
def listar_mis_ventas(
    producto_id: Optional[int] = Query(None, description="Filtrar por producto"),
    skip: int = Query(0, ge=0, description="Ventas a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de ventas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para listar ventas.
    
    Devuelve solo las ventas de productos del usuario autenticado.
    """
    ventas = listar_ventas(db, current_user, producto_id, skip, limit)
    
    # Enriquecer la respuesta con información del producto
    ventas_enriquecidas = []
    for venta in ventas:
        ventas_enriquecidas.append({
            "id": venta.id,
            "producto_id": venta.producto_id,
            "cantidad": venta.cantidad,
            "fecha": venta.fecha,
            "producto_nombre": venta.product.nombre,
            "producto_sku": venta.product.sku,
            "stock_restante": venta.product.stock_actual
        })
    
    return {
        "total": len(ventas_enriquecidas),
        "sales": ventas_enriquecidas
    }


# ============================================
# OBTENER UNA VENTA
# ============================================

@router.get(
    "/{venta_id}",
    response_model=SaleResponse,
    summary="Obtener una venta específica",
    description="""
    Obtiene los detalles de una venta por su ID.
    
    **Requiere autenticación.**
    Solo se pueden ver ventas de productos propios.
    """
)
def obtener_detalle_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obtener una venta específica.
    """
    venta = obtener_venta(db, venta_id, current_user)
    
    return {
        "id": venta.id,
        "producto_id": venta.producto_id,
        "cantidad": venta.cantidad,
        "fecha": venta.fecha,
        "producto_nombre": venta.product.nombre,
        "producto_sku": venta.product.sku,
        "stock_restante": venta.product.stock_actual
    }


# ============================================
# ESTADÍSTICAS DE VENTAS
# ============================================

@router.get(
    "/stats/summary",
    summary="Obtener estadísticas de ventas",
    description="""
    Obtiene un resumen de las estadísticas de ventas del usuario.
    
    **Incluye:**
    - Total de ventas realizadas
    - Total de unidades vendidas
    - Producto más vendido
    
    **Requiere autenticación.**
    """
)
def obtener_estadisticas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obtener estadísticas de ventas.
    """
    return obtener_estadisticas_ventas(db, current_user)
