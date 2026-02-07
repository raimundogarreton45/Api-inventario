"""
Paquete de modelos de base de datos.

Este archivo permite importar los modelos de forma más limpia:
En vez de: from app.models.user import User
Puedes hacer: from app.models import User
"""

from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale

# Exportar todos los modelos
__all__ = ["User", "Product", "Sale"]
