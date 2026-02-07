# 🛒 Guía de Integraciones con Marketplaces

## Estrategia Modular de Integraciones

Esta guía explica cómo agregar integraciones con plataformas de venta online según las necesidades de cada cliente.

---

## 🎯 Filosofía de Integración

### Modelo "Cliente Decide"

Cada integración es un **módulo opcional** que se activa según necesidad:

```
Sistema Base (Incluido)
    ↓
¿Cliente vende en Mercado Libre? → Módulo ML ($10.000/mes)
¿Cliente vende en Instagram? → Módulo Social ($5.000/mes)
¿Cliente vende en Falabella? → Módulo Marketplace ($15.000/mes)
```

**Ventajas:**
- Cliente solo paga por lo que usa
- Implementación gradual
- Escalable según crecimiento

---

## 📊 Priorización de Integraciones

### Tier 1: Esenciales para PYME (Implementar Primero)

#### 1. Mercado Libre 🥇
**Por qué:**
- 70% de minimarkets chilenos venden aquí
- API bien documentada
- Alto volumen de transacciones

**Complejidad:** Media
**Tiempo desarrollo:** 2-3 semanas
**Valor para cliente:** Alto

#### 2. Instagram Shopping 🥈
**Por qué:**
- 85% de PYME tiene Instagram
- Fácil de implementar
- Bajo costo

**Complejidad:** Baja
**Tiempo desarrollo:** 1 semana
**Valor para cliente:** Medio-Alto

#### 3. WhatsApp Business API 🥉
**Por qué:**
- 95% de clientes usa WhatsApp
- Permite automatización
- Muy valorado por dueños

**Complejidad:** Media
**Tiempo desarrollo:** 2 semanas
**Valor para cliente:** Muy Alto

### Tier 2: Marketplaces Mayores (Según Demanda)

#### 4. Falabella Marketplace
**Por qué:**
- Mercado premium
- Clientes con mayor ticket promedio
- Permite expansión

**Complejidad:** Alta
**Tiempo desarrollo:** 4-6 semanas
**Valor para cliente:** Medio (para PYME)

#### 5. Linio
**Similar a Falabella**

#### 6. Yapo.cl
**Para productos usados/especiales**

### Tier 3: Especializadas (Nicho)

- Shopify (si tienen tienda online)
- WooCommerce (WordPress)
- Plataformas específicas por rubro

---

## 🔧 Implementación Técnica por Plataforma

### 1. Mercado Libre

#### Arquitectura

```python
app/
├── services/
│   └── integrations/
│       └── mercadolibre/
│           ├── __init__.py
│           ├── auth.py          # OAuth de ML
│           ├── products.py      # Sincronizar productos
│           ├── orders.py        # Procesar pedidos
│           ├── stock.py         # Actualizar stock
│           └── webhooks.py      # Notificaciones de ML
```

#### Flujo de Integración

```
1. Autenticación OAuth
   ↓
2. Cliente autoriza app en ML
   ↓
3. Sistema obtiene access token
   ↓
4. Sincronización inicial:
   - Lista productos de ML
   - Matchea con SKU interno
   - Sincroniza stock
   ↓
5. Operación continua:
   - Venta en ML → Webhook → Descuenta stock
   - Venta local → Actualiza ML
   - Stock bajo → No publicar en ML
```

#### Código Base (Ejemplo)

```python
# app/services/integrations/mercadolibre/client.py

import requests
from typing import Dict, List
from app.config import get_settings

settings = get_settings()

class MercadoLibreClient:
    """Cliente para interactuar con API de Mercado Libre."""
    
    BASE_URL = "https://api.mercadolibre.com"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def obtener_publicaciones(self, user_id: str) -> List[Dict]:
        """Obtiene todas las publicaciones activas del usuario."""
        url = f"{self.BASE_URL}/users/{user_id}/items/search"
        params = {"status": "active"}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()["results"]
    
    def actualizar_stock(self, item_id: str, cantidad: int) -> bool:
        """Actualiza el stock de una publicación."""
        url = f"{self.BASE_URL}/items/{item_id}"
        data = {"available_quantity": cantidad}
        
        response = requests.put(url, headers=self.headers, json=data)
        
        return response.status_code == 200
    
    def pausar_publicacion(self, item_id: str) -> bool:
        """Pausa una publicación (cuando stock = 0)."""
        url = f"{self.BASE_URL}/items/{item_id}"
        data = {"status": "paused"}
        
        response = requests.put(url, headers=self.headers, json=data)
        
        return response.status_code == 200
```

#### Modelo de Base de Datos

```python
# app/models/integrations.py

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from app.database import Base

class IntegracionMercadoLibre(Base):
    """Configuración de integración con Mercado Libre."""
    
    __tablename__ = "integracion_mercadolibre"
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("users.id"))
    
    # Credenciales OAuth
    ml_user_id = Column(String(50))
    access_token = Column(String(500))
    refresh_token = Column(String(500))
    
    # Configuración
    activo = Column(Boolean, default=True)
    auto_sincronizar = Column(Boolean, default=True)


class ProductoMercadoLibre(Base):
    """Mapeo entre productos locales y ML."""
    
    __tablename__ = "productos_mercadolibre"
    
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("products.id"))
    
    # ID en Mercado Libre
    ml_item_id = Column(String(50), unique=True)
    
    # Configuración
    sincronizar_stock = Column(Boolean, default=True)
    precio_ml = Column(Integer)  # Puede ser diferente al local
```

#### Webhook Handler

```python
# app/routes/webhooks/mercadolibre.py

from fastapi import APIRouter, Request
from app.services.integrations.mercadolibre import procesar_notificacion

router = APIRouter(prefix="/webhooks/mercadolibre")

@router.post("/notifications")
async def webhook_ml(request: Request):
    """
    Recibe notificaciones de Mercado Libre.
    
    Tipos de notificaciones:
    - orders: Nueva orden
    - items: Cambio en publicación
    - questions: Nueva pregunta
    """
    data = await request.json()
    
    # Procesar según tipo
    if data["topic"] == "orders":
        await procesar_orden_ml(data)
    elif data["topic"] == "items":
        await procesar_cambio_item(data)
    
    return {"status": "ok"}
```

---

### 2. Instagram Shopping

#### Arquitectura Simplificada

```python
app/
├── services/
│   └── integrations/
│       └── instagram/
│           ├── catalog.py      # Catálogo de productos
│           ├── sync.py         # Sincronización
│           └── webhook.py      # Eventos de IG
```

#### Flujo

```
1. Conectar cuenta Instagram Business
   ↓
2. Crear catálogo de productos (Facebook)
   ↓
3. Sincronizar productos:
   - Foto del producto
   - Nombre, precio
   - Stock (in_stock / out_of_stock)
   ↓
4. Instagram muestra productos
   ↓
5. Venta local → Actualizar catálogo
```

#### Código Base

```python
# app/services/integrations/instagram/catalog.py

import requests
from typing import Dict

class InstagramCatalog:
    """Gestión del catálogo de Instagram Shopping."""
    
    GRAPH_API = "https://graph.facebook.com/v18.0"
    
    def __init__(self, access_token: str, catalog_id: str):
        self.access_token = access_token
        self.catalog_id = catalog_id
    
    def crear_producto(self, producto: Dict) -> str:
        """Crea un producto en el catálogo."""
        url = f"{self.GRAPH_API}/{self.catalog_id}/products"
        
        data = {
            "retailer_id": producto["sku"],
            "name": producto["nombre"],
            "description": producto.get("descripcion", ""),
            "price": producto["precio"] * 100,  # En centavos
            "currency": "CLP",
            "availability": "in stock" if producto["stock"] > 0 else "out of stock",
            "url": f"https://tu-tienda.cl/productos/{producto['sku']}"
        }
        
        response = requests.post(
            url,
            params={"access_token": self.access_token},
            json=data
        )
        
        return response.json()["id"]
    
    def actualizar_disponibilidad(self, sku: str, en_stock: bool):
        """Actualiza si un producto está disponible."""
        url = f"{self.GRAPH_API}/{self.catalog_id}/products"
        
        data = {
            "retailer_id": sku,
            "availability": "in stock" if en_stock else "out of stock"
        }
        
        response = requests.post(
            url,
            params={
                "access_token": self.access_token,
                "update_only": True
            },
            json=data
        )
        
        return response.status_code == 200
```

---

### 3. WhatsApp Business API

#### Casos de Uso

1. **Alertas Automáticas**
   - Cliente: "¿Tienes Coca Cola?"
   - Bot: "Sí, tenemos 15 unidades en stock. ¿Cuántas necesitas?"

2. **Confirmación de Pedidos**
   - Cliente hace pedido
   - Bot confirma disponibilidad
   - Descuenta stock automáticamente

3. **Catálogo Interactivo**
   - Cliente: "Quiero ver bebidas"
   - Bot: *Envía catálogo con fotos y precios*

#### Código Base

```python
# app/services/integrations/whatsapp/bot.py

from twilio.rest import Client
from app.models import Product
from sqlalchemy.orm import Session

class WhatsAppBot:
    """Bot de WhatsApp para consultas de stock."""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
    
    def consultar_stock(self, db: Session, producto_nombre: str, usuario_id: int) -> str:
        """Busca un producto y retorna disponibilidad."""
        producto = db.query(Product).filter(
            Product.nombre.ilike(f"%{producto_nombre}%"),
            Product.usuario_id == usuario_id
        ).first()
        
        if not producto:
            return f"❌ No encontré '{producto_nombre}' en el inventario."
        
        if producto.stock_actual > 0:
            return f"✅ {producto.nombre}\n📦 Stock: {producto.stock_actual} unidades\n💰 Precio: ${producto.precio:,.0f}"
        else:
            return f"❌ {producto.nombre} está agotado"
    
    def enviar_mensaje(self, to_number: str, mensaje: str):
        """Envía un mensaje de WhatsApp."""
        self.client.messages.create(
            from_=f"whatsapp:{self.from_number}",
            to=f"whatsapp:{to_number}",
            body=mensaje
        )
```

---

## 💰 Modelo de Precios por Integración

| Integración | Setup | Mensual | Incluye |
|-------------|-------|---------|---------|
| Mercado Libre | $30.000 | $10.000 | Sincronización automática, webhooks |
| Instagram Shopping | $20.000 | $5.000 | Catálogo, actualización stock |
| WhatsApp Business | $25.000 | $8.000 | Bot básico, 1000 mensajes/mes |
| Falabella Marketplace | $50.000 | $15.000 | Sincronización, reportes |
| Combo ML + IG + WA | $60.000 | $20.000 | ⭐ Ahorro $15.000 |

---

## 📋 Checklist de Implementación

### Antes de Ofrecer una Integración

- [ ] API documentada y estable
- [ ] Cuenta de pruebas disponible
- [ ] Webhooks configurables
- [ ] OAuth o API Key funcional
- [ ] Límites de rate conocidos
- [ ] Costos asociados claros

### Antes de Activar para Cliente

- [ ] Cliente tiene cuenta activa en plataforma
- [ ] Cliente entiende el flujo
- [ ] Credenciales configuradas
- [ ] Prueba de sincronización exitosa
- [ ] Cliente capacitado
- [ ] Documentación entregada

---

## 🎯 Estrategia Comercial

### Pitch por Integración

#### Mercado Libre
> "¿Vendes en Mercado Libre? Imagina que cada venta se descuenta automáticamente de tu stock. Nunca más venderás algo que no tienes."

#### Instagram
> "Tienes Instagram? Convierte tus fotos en un catálogo de compras. Tus seguidores ven stock en tiempo real."

#### WhatsApp
> "¿Tus clientes te preguntan por WhatsApp si tienes X producto? Deja que un bot responda por ti, 24/7."

### Upselling Natural

```
Cliente empieza → Plan Básico ($0)
    ↓
Crece, vende en ML → Agrega integración ML (+$10.000)
    ↓
Quiere más canales → Agrega Instagram (+$5.000)
    ↓
Muchas consultas → Agrega WhatsApp Bot (+$8.000)
    ↓
Total: $23.000/mes (vs $35.000 Plan Empresarial)
```

---

## 🔒 Consideraciones de Seguridad

### Tokens y Credenciales

```python
# Nunca en código:
ML_TOKEN = "ABC123"  # ❌

# Siempre en base de datos encriptado:
from cryptography.fernet import Fernet

class EncryptedToken:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
    
    def encrypt(self, token: str) -> str:
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt(self, encrypted_token: str) -> str:
        return self.cipher.decrypt(encrypted_token.encode()).decode()
```

### Validación de Webhooks

```python
import hmac
import hashlib

def validar_webhook_ml(data: dict, signature: str, secret: str) -> bool:
    """Valida que el webhook venga realmente de ML."""
    expected = hmac.new(
        secret.encode(),
        json.dumps(data).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

---

## 📊 Métricas de Éxito

### KPIs por Integración

**Mercado Libre:**
- % de productos sincronizados
- Tiempo de actualización de stock
- Ventas ML vs total

**Instagram:**
- CTR en productos
- Conversión catálogo
- Engagement

**WhatsApp:**
- Mensajes respondidos automáticamente
- Tiempo de respuesta promedio
- Satisfacción del cliente

---

## 🚀 Roadmap Sugerido

### Mes 1-2: Base
- [ ] Implementar Mercado Libre
- [ ] Testear con 3 clientes beta
- [ ] Ajustar flujo

### Mes 3-4: Expansión
- [ ] Implementar Instagram Shopping
- [ ] Implementar WhatsApp básico
- [ ] Crear combo

### Mes 5-6: Escalamiento
- [ ] Falabella Marketplace (si hay demanda)
- [ ] Mejoras en automatización
- [ ] Dashboard unificado

---

**Siguiente:** Empezar con Mercado Libre (70% del mercado)
