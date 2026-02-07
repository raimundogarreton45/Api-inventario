"""
MODELO: PRODUCTO

Define cómo se ve un Producto en la base de datos.

CONCEPTOS:
- Cada producto pertenece a un usuario (usuario_id es la "llave foránea")
- Tiene stock actual y stock mínimo para alertas
- Tiene un SKU (código único del producto)
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Product(Base):
    """
    Modelo de Producto para la base de datos.
    
    Atributos:
        id: Identificador único del producto
        nombre: Nombre descriptivo del producto
        sku: Código único del producto (ej: "CAM-001" para camiseta)
        stock_actual: Cantidad actual en inventario
        stock_minimo: Cantidad mínima antes de enviar alerta
        usuario_id: ID del usuario dueño del producto
        alerta_enviada: Indica si ya se envió alerta de stock bajo
        created_at: Fecha de creación
        updated_at: Fecha de última modificación
    """
    
    __tablename__ = "products"
    
    # ============================================
    # COLUMNAS BÁSICAS
    # ============================================
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Nombre del producto (ej: "Camiseta Nike Negra Talla M")
    nombre = Column(String(200), nullable=False)
    
    # SKU: Código único del producto
    # Puede ser algo como "CAM-NIKE-001" o "PROD-12345"
    # unique=True asegura que no haya dos productos con el mismo SKU
    sku = Column(String(50), unique=True, nullable=False, index=True)
    
    # Stock actual: Cuántas unidades hay ahora
    # default=0 significa que si no especificas, empieza en 0
    stock_actual = Column(Integer, nullable=False, default=0)
    
    # Stock mínimo: Cuando llegue a este número o menos, se envía alerta
    # Por ejemplo: si stock_minimo=5 y stock_actual=4, se envía email
    stock_minimo = Column(Integer, nullable=False, default=10)
    
    # ============================================
    # RELACIÓN CON USUARIO (Dueño del producto)
    # ============================================
    
    # ForeignKey es una "llave foránea" que apunta a la tabla users
    # Esto significa: "Este producto pertenece a un usuario específico"
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    
    # ============================================
    # CONTROL DE ALERTAS
    # ============================================
    
    # Esta bandera evita enviar la misma alerta múltiples veces
    # Se pone en True cuando se envía la alerta
    # Se pone en False cuando el stock vuelve a estar OK
    alerta_enviada = Column(Boolean, default=False, nullable=False)
    
    
    # ============================================
    # FECHAS
    # ============================================
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # updated_at se actualiza cada vez que modificas el producto
    # onupdate=datetime.utcnow hace que se actualice automáticamente
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    # ============================================
    # RELACIONES
    # ============================================
    
    # Relación inversa con User: Para acceder al dueño del producto
    # Puedes hacer: producto.owner.email para obtener el email del dueño
    owner = relationship("User", back_populates="products")
    
    # Relación con ventas: Un producto puede tener muchas ventas
    sales = relationship("Sale", back_populates="product")
    
    
    def __repr__(self):
        """Representación en texto del producto."""
        return f"<Product: {self.sku} - {self.nombre}>"
    
    
    def necesita_alerta(self) -> bool:
        """
        Determina si este producto necesita enviar una alerta.
        
        Retorna True si:
        - El stock actual es menor o igual al stock mínimo
        - Y aún no se ha enviado la alerta
        
        Retorna:
            bool: True si necesita alerta, False si no
        """
        return self.stock_actual <= self.stock_minimo and not self.alerta_enviada
    
    
    def puede_vender(self, cantidad: int) -> bool:
        """
        Verifica si hay suficiente stock para vender.
        
        Args:
            cantidad: Cantidad que se quiere vender
        
        Retorna:
            bool: True si hay stock suficiente, False si no
        """
        return self.stock_actual >= cantidad
