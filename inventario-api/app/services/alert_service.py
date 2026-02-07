"""
SERVICIO: ALERTAS POR EMAIL

Envía emails usando SendGrid cuando el stock está bajo.

IMPORTANTE: 
- Solo envía una alerta por producto hasta que el stock se recupere
- La bandera "alerta_enviada" evita spam de emails
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import get_settings
import logging

# Configurar logging para ver qué está pasando
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


def enviar_alerta_stock_bajo(
    email_destino: str,
    producto_nombre: str,
    sku: str,
    stock_actual: int,
    stock_minimo: int
) -> bool:
    """
    Envía un email de alerta cuando un producto tiene stock bajo.
    
    Args:
        email_destino: Email del usuario dueño del producto
        producto_nombre: Nombre del producto
        sku: SKU del producto
        stock_actual: Stock actual
        stock_minimo: Stock mínimo configurado
    
    Retorna:
        bool: True si se envió exitosamente, False si hubo error
    """
    
    # ============================================
    # CONSTRUIR EL CONTENIDO DEL EMAIL
    # ============================================
    
    asunto = f"⚠️ Alerta: Stock Bajo - {producto_nombre}"
    
    # Cuerpo del email en HTML (más bonito que texto plano)
    contenido_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #d9534f;">⚠️ Alerta de Stock Bajo</h2>
                
                <p>Hola,</p>
                
                <p>Tu producto ha alcanzado el stock mínimo:</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #d9534f; margin: 20px 0;">
                    <p><strong>Producto:</strong> {producto_nombre}</p>
                    <p><strong>SKU:</strong> {sku}</p>
                    <p><strong>Stock Actual:</strong> <span style="color: #d9534f; font-size: 18px;">{stock_actual}</span> unidades</p>
                    <p><strong>Stock Mínimo:</strong> {stock_minimo} unidades</p>
                </div>
                
                <p>Te recomendamos reabastecer este producto lo antes posible.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                
                <p style="font-size: 12px; color: #777;">
                    Este es un mensaje automático de tu sistema de inventario.<br>
                    No recibirás otra alerta hasta que el stock se recupere por encima del mínimo.
                </p>
            </div>
        </body>
    </html>
    """
    
    # Cuerpo en texto plano (por si el cliente de email no soporta HTML)
    contenido_texto = f"""
    ⚠️ ALERTA DE STOCK BAJO
    
    Producto: {producto_nombre}
    SKU: {sku}
    Stock Actual: {stock_actual} unidades
    Stock Mínimo: {stock_minimo} unidades
    
    Te recomendamos reabastecer este producto lo antes posible.
    
    ---
    Este es un mensaje automático de tu sistema de inventario.
    """
    
    
    # ============================================
    # ENVIAR EL EMAIL
    # ============================================
    
    try:
        # Crear el mensaje
        message = Mail(
            from_email=settings.sendgrid_from_email,
            to_emails=email_destino,
            subject=asunto,
            html_content=contenido_html,
            plain_text_content=contenido_texto
        )
        
        # Inicializar el cliente de SendGrid
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        
        # Enviar el email
        response = sg.send(message)
        
        # Verificar que se envió correctamente
        if response.status_code in [200, 201, 202]:
            logger.info(f"✅ Alerta enviada a {email_destino} para producto {sku}")
            return True
        else:
            logger.error(f"❌ Error al enviar alerta. Status: {response.status_code}")
            return False
    
    except Exception as e:
        # Si hay cualquier error, lo registramos pero no detenemos la ejecución
        logger.error(f"❌ Error al enviar email: {str(e)}")
        return False


# ============================================
# FUNCIÓN PARA PROBAR EL ENVÍO DE EMAILS
# ============================================

def probar_envio_email(email_destino: str) -> bool:
    """
    Función de prueba para verificar que SendGrid está configurado correctamente.
    
    Args:
        email_destino: Email donde se enviará el mensaje de prueba
    
    Retorna:
        bool: True si se envió, False si hubo error
    """
    try:
        message = Mail(
            from_email=settings.sendgrid_from_email,
            to_emails=email_destino,
            subject="Prueba de Sistema de Inventario",
            html_content="<p>Este es un email de prueba. Tu sistema está configurado correctamente.</p>",
            plain_text_content="Este es un email de prueba. Tu sistema está configurado correctamente."
        )
        
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"✅ Email de prueba enviado a {email_destino}")
            return True
        else:
            logger.error(f"❌ Error en prueba. Status: {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error en prueba: {str(e)}")
        return False


# ============================================
# PARA PROBAR DESDE LA TERMINAL
# ============================================
# 
# python -c "from app.services.alert_service import probar_envio_email; probar_envio_email('tu@email.cl')"
