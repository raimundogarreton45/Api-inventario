"""
SCHEMAS: VENTA

Define qué datos se necesitan para registrar una venta
y qué datos se devuelven.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ============================================
# SCHEMA PARA CREAR VENTAS
# ============================================

class SaleCreate(BaseModel):
    """
    Datos necesarios para registrar una venta.
    
    IMPORTANTE: Al crear una venta, automáticamente se descuenta el stock.
    """
    producto_id: int = Field(..., gt=0, description="ID del producto a vender")
    cantidad: int = Field(..., gt=0, description="Cantidad a vender (debe ser > 0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": 1,
                "cantidad": 5
            }
        }


# ============================================
# SCHEMA PARA RESPUESTAS
# ============================================

class SaleResponse(BaseModel):
    """
    Datos que la API devuelve sobre una venta.
    """
    id: int
    producto_id: int
    cantidad: int
    fecha: datetime
    # Información adicional del producto (para comodidad)
    producto_nombre: Optional[str] = None
    producto_sku: Optional[str] = None
    stock_restante: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "producto_id": 1,
                "cantidad": 5,
                "fecha": "2024-02-06T14:30:00",
                "producto_nombre": "Camiseta Nike Negra Talla M",
                "producto_sku": "CAM-NIKE-001",
                "stock_restante": 45
            }
        }


# ============================================
# SCHEMA PARA CONFIRMACIÓN DE VENTA
# ============================================

class SaleConfirmation(BaseModel):
    """
    Respuesta completa después de registrar una venta.
    
    Incluye información de la venta Y si se envió una alerta.
    """
    venta: SaleResponse
    alerta_enviada: bool = Field(..., description="True si se envió alerta de stock bajo")
    mensaje: str = Field(..., description="Mensaje informativo sobre la venta")
    
    class Config:
        json_schema_extra = {
            "example": {
                "venta": {
                    "id": 1,
                    "producto_id": 1,
                    "cantidad": 5,
                    "fecha": "2024-02-06T14:30:00",
                    "producto_nombre": "Camiseta Nike Negra Talla M",
                    "producto_sku": "CAM-NIKE-001",
                    "stock_restante": 8
                },
                "alerta_enviada": True,
                "mensaje": "Venta registrada. ⚠️ Stock bajo mínimo. Se envió alerta por email."
            }
        }


# ============================================
# SCHEMA PARA LISTA DE VENTAS
# ============================================

class SaleListResponse(BaseModel):
    """
    Respuesta cuando se listan múltiples ventas.
    """
    total: int = Field(..., description="Número total de ventas")
    sales: list[SaleResponse] = Field(..., description="Lista de ventas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "sales": [
                    {
                        "id": 1,
                        "producto_id": 1,
                        "cantidad": 5,
                        "fecha": "2024-02-06T14:30:00",
                        "producto_nombre": "Camiseta Nike Negra Talla M",
                        "producto_sku": "CAM-NIKE-001",
                        "stock_restante": 45
                    }
                ]
            }
        }
