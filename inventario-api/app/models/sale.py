"""
MODELO: VENTA

Define cómo se ve una Venta en la base de datos.

IMPORTANTE: Cuando registras una venta, el stock del producto se descuenta automáticamente.
Esto lo hace el servicio de ventas (sale_service.py).
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Sale(Base):
    """
    Modelo de Venta para la base de datos.
    
    Una venta registra que se vendieron X unidades de un producto en una fecha.
    
    Atributos:
        id: Identificador único de la venta
        producto_id: ID del producto que se vendió
        cantidad: Cuántas unidades se vendieron
        fecha: Fecha y hora de la venta
    """
    
    __tablename__ = "sales"
    
    # ============================================
    # COLUMNAS
    # ============================================
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # ForeignKey: Esta venta pertenece a un producto específico
    producto_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Cantidad vendida (debe ser un número positivo)
    cantidad = Column(Integer, nullable=False)
    
    # Fecha de la venta
    # Por defecto usa la fecha/hora actual cuando se crea el registro
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    
    # ============================================
    # RELACIONES
    # ============================================
    
    # Relación con el producto vendido
    # Puedes hacer: venta.product.nombre para obtener el nombre del producto
    product = relationship("Product", back_populates="sales")
    
    
    def __repr__(self):
        """Representación en texto de la venta."""
        return f"<Sale: {self.cantidad} unidades del producto {self.producto_id}>"


# ============================================
# EJEMPLO DE USO
# ============================================
# 
# Crear una venta:
# nueva_venta = Sale(
#     producto_id=1,
#     cantidad=5,
#     fecha=datetime.utcnow()
# )
# db.add(nueva_venta)
# db.commit()
#
# El descuento de stock lo hace el servicio, NO el modelo
