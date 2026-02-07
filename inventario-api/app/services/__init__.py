"""
Paquete de servicios (lógica de negocio).
"""

from app.services.product_service import (
    crear_producto,
    listar_productos,
    obtener_producto,
    actualizar_producto,
    actualizar_stock,
    eliminar_producto
)

from app.services.sale_service import (
    registrar_venta,
    listar_ventas,
    obtener_venta,
    obtener_estadisticas_ventas
)

from app.services.alert_service import (
    enviar_alerta_stock_bajo,
    probar_envio_email
)

__all__ = [
    # Product services
    "crear_producto",
    "listar_productos",
    "obtener_producto",
    "actualizar_producto",
    "actualizar_stock",
    "eliminar_producto",
    # Sale services
    "registrar_venta",
    "listar_ventas",
    "obtener_venta",
    "obtener_estadisticas_ventas",
    # Alert services
    "enviar_alerta_stock_bajo",
    "probar_envio_email",
]
