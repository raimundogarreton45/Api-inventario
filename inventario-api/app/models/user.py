"""
MODELO: USUARIO

Define cómo se ve un Usuario en la base de datos.

ANALOGÍA: Piensa en esto como un formulario que tiene campos específicos.
Cada usuario tiene: id, nombre, email, password, api_key
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    """
    Modelo de Usuario para la base de datos.
    
    Atributos:
        id: Identificador único del usuario (se genera automáticamente)
        nombre: Nombre completo del usuario
        email: Correo electrónico (único, no se pueden repetir)
        hashed_password: Contraseña encriptada (nunca guardamos la contraseña real)
        api_key: Clave única para autenticación (como un "carnet digital")
        created_at: Fecha de creación del usuario
    """
    
    # Nombre de la tabla en PostgreSQL
    __tablename__ = "users"
    
    # ============================================
    # COLUMNAS DE LA TABLA
    # ============================================
    
    # ID: Número único que identifica al usuario
    # primary_key=True significa que es el identificador principal
    # autoincrement=True significa que PostgreSQL lo genera automáticamente (1, 2, 3...)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Nombre del usuario
    # nullable=False significa que es obligatorio
    nombre = Column(String(100), nullable=False)
    
    # Email del usuario
    # unique=True significa que no pueden haber dos usuarios con el mismo email
    # index=True crea un índice para búsquedas rápidas
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Contraseña encriptada (NUNCA guardamos la contraseña en texto plano)
    hashed_password = Column(String(255), nullable=False)
    
    # API Key: Es como un "token de acceso" que el usuario usa para autenticarse
    # Se genera automáticamente cuando se crea el usuario
    api_key = Column(String(100), unique=True, nullable=False, index=True)
    
    # Fecha de creación
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
    # ============================================
    # RELACIONES
    # ============================================
    
    # Relación con productos: Un usuario puede tener muchos productos
    # relationship crea una "conexión virtual" entre User y Product
    # back_populates conecta esta relación con la relación inversa en Product
    products = relationship("Product", back_populates="owner")
    
    
    def __repr__(self):
        """
        Representación en texto del usuario (útil para debugging).
        
        Cuando hagas print(user), verás: <User: juan@ejemplo.cl>
        """
        return f"<User: {self.email}>"
