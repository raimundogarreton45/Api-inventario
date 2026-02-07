"""
Paquete de schemas de validación.

Facilita las importaciones de los schemas Pydantic.
"""

from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, TokenData
from app.schemas.product import ProductCreate, ProductUpdate, StockUpdate, ProductResponse, ProductListResponse
from app.schemas.sale import SaleCreate, SaleResponse, SaleConfirmation, SaleListResponse

__all__ = [
    # User schemas
    "UserCreate",
    "UserLogin", 
    "UserResponse",
    "Token",
    "TokenData",
    # Product schemas
    "ProductCreate",
    "ProductUpdate",
    "StockUpdate",
    "ProductResponse",
    "ProductListResponse",
    # Sale schemas
    "SaleCreate",
    "SaleResponse",
    "SaleConfirmation",
    "SaleListResponse",
]
