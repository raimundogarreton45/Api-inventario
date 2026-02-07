"""
SCHEMAS: PRODUCTO

Define qué datos se aceptan al crear/actualizar productos
y qué datos se devuelven al cliente.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ============================================
# SCHEMA PARA CREAR PRODUCTOS
# ============================================

class ProductCreate(BaseModel):
    """
    Datos necesarios para crear un nuevo producto.
    """
    nombre: str = Field(..., min_length=2, max_length=200, description="Nombre del producto")
    sku: str = Field(..., min_length=1, max_length=50, description="Código SKU único del producto")
    stock_actual: int = Field(default=0, ge=0, description="Stock inicial (debe ser >= 0)")
    stock_minimo: int = Field(default=10, ge=0, description="Stock mínimo antes de alerta")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Camiseta Nike Negra Talla M",
                "sku": "CAM-NIKE-001",
                "stock_actual": 50,
                "stock_minimo": 10
            }
        }


# ============================================
# SCHEMA PARA ACTUALIZAR PRODUCTOS
# ============================================

class ProductUpdate(BaseModel):
    """
    Datos opcionales para actualizar un producto existente.
    
    Todos los campos son opcionales. Solo se actualizan los que se envíen.
    """
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    stock_actual: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_actual": 75,
                "stock_minimo": 15
            }
        }


# ============================================
# SCHEMA PARA ACTUALIZAR SOLO EL STOCK
# ============================================

class StockUpdate(BaseModel):
    """
    Para actualizar únicamente el stock de un producto.
    
    Esto se usa en el endpoint PUT /products/{id}/stock
    """
    stock_actual: int = Field(..., ge=0, description="Nuevo valor de stock")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_actual": 100
            }
        }


# ============================================
# SCHEMA PARA RESPUESTAS
# ============================================

class ProductResponse(BaseModel):
    """
    Datos que la API devuelve sobre un producto.
    """
    id: int
    nombre: str
    sku: str
    stock_actual: int
    stock_minimo: int
    usuario_id: int
    alerta_enviada: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "nombre": "Camiseta Nike Negra Talla M",
                "sku": "CAM-NIKE-001",
                "stock_actual": 50,
                "stock_minimo": 10,
                "usuario_id": 1,
                "alerta_enviada": False,
                "created_at": "2024-02-06T10:30:00",
                "updated_at": "2024-02-06T10:30:00"
            }
        }


# ============================================
# SCHEMA PARA LISTA DE PRODUCTOS
# ============================================

class ProductListResponse(BaseModel):
    """
    Respuesta cuando se listan múltiples productos.
    """
    total: int = Field(..., description="Número total de productos")
    products: list[ProductResponse] = Field(..., description="Lista de productos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "products": [
                    {
                        "id": 1,
                        "nombre": "Camiseta Nike Negra Talla M",
                        "sku": "CAM-NIKE-001",
                        "stock_actual": 50,
                        "stock_minimo": 10,
                        "usuario_id": 1,
                        "alerta_enviada": False,
                        "created_at": "2024-02-06T10:30:00",
                        "updated_at": "2024-02-06T10:30:00"
                    }
                ]
            }
        }
