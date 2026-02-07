# 🏗️ ARQUITECTURA DEL SISTEMA - EXPLICACIÓN COMPLETA

## 📚 Índice
1. [Visión General](#visión-general)
2. [Flujo de una Petición](#flujo-de-una-petición)
3. [Componentes Principales](#componentes-principales)
4. [Cómo Funciona una Venta](#cómo-funciona-una-venta)
5. [Sistema de Alertas](#sistema-de-alertas)
6. [Seguridad](#seguridad)

---

## Visión General

### ¿Qué hace este sistema?

Imagina que tienes una tienda y necesitas:
1. **Llevar un registro** de tus productos
2. **Saber cuánto stock tienes** de cada producto
3. **Recibir alertas** cuando se te está acabando algo
4. **Ver un historial** de tus ventas

Este sistema hace exactamente eso, pero de forma automática.

### Arquitectura de Capas

El sistema está organizado en **capas** (como un edificio):

```
┌─────────────────────────────────┐
│     CLIENTE (Tu App/Web)        │  ← Aquí es donde el usuario interactúa
└─────────────────────────────────┘
              ↕ HTTP
┌─────────────────────────────────┐
│    RUTAS (routes/)              │  ← Recibe peticiones HTTP
└─────────────────────────────────┘
              ↕
┌─────────────────────────────────┐
│    SERVICIOS (services/)        │  ← Lógica de negocio (las reglas)
└─────────────────────────────────┘
              ↕
┌─────────────────────────────────┐
│    MODELOS (models/)            │  ← Estructura de datos
└─────────────────────────────────┘
              ↕
┌─────────────────────────────────┐
│    BASE DE DATOS (PostgreSQL)   │  ← Donde se guarda todo
└─────────────────────────────────┘
```

**¿Por qué esta organización?**

Cada capa tiene una responsabilidad específica. Es como en una empresa:
- **Rutas** = Recepcionista (recibe peticiones)
- **Servicios** = Gerente (toma decisiones)
- **Modelos** = Archivador (organiza datos)
- **Base de datos** = Bodega (guarda todo)

---

## Flujo de una Petición

### Ejemplo: Registrar una venta

Veamos paso a paso qué pasa cuando alguien registra una venta:

```
1. CLIENTE envía petición:
   POST /sales
   {
     "producto_id": 1,
     "cantidad": 5
   }
   
   ↓

2. FASTAPI recibe la petición en app/main.py
   - Verifica que el formato JSON sea correcto
   
   ↓

3. RUTA (routes/sales.py) se activa
   - Función: registrar_nueva_venta()
   - Verifica que el usuario esté autenticado
   - Valida los datos con Pydantic (schemas)
   
   ↓

4. SERVICIO (services/sale_service.py) ejecuta la lógica
   - Función: registrar_venta()
   - Busca el producto en la base de datos
   - Verifica que hay stock suficiente
   - Descuenta el stock
   - Crea el registro de venta
   - Verifica si necesita enviar alerta
   
   ↓

5. Si necesita alerta → SERVICIO DE ALERTAS (services/alert_service.py)
   - Función: enviar_alerta_stock_bajo()
   - Construye el email
   - Envía vía SendGrid
   
   ↓

6. BASE DE DATOS guarda los cambios
   - Actualiza el stock del producto
   - Guarda el registro de venta
   - Actualiza la bandera de alerta
   
   ↓

7. RESPUESTA vuelve al cliente
   {
     "venta": {...},
     "alerta_enviada": true,
     "mensaje": "Venta registrada. Stock bajo..."
   }
```

---

## Componentes Principales

### 1. app/main.py - El Corazón

**¿Qué hace?**
- Crea la aplicación FastAPI
- Registra todas las rutas
- Configura CORS (para que navegadores puedan acceder)
- Inicializa la base de datos

**Analogía:** Es como el gerente general que coordina todo.

```python
# Simplificado:
app = FastAPI()  # Crear la aplicación

# Registrar rutas
app.include_router(auth.router)      # /auth/*
app.include_router(products.router)  # /products/*
app.include_router(sales.router)     # /sales/*
```

---

### 2. app/database.py - Conexión a BD

**¿Qué hace?**
- Conecta con PostgreSQL/Supabase
- Crea sesiones de base de datos
- Define la clase base para modelos

**Analogía:** Es el puente entre tu código y la base de datos.

**Conceptos clave:**

```python
# Engine = Motor que se conecta a PostgreSQL
engine = create_engine(database_url)

# SessionLocal = Fabricante de "sesiones"
# Una sesión es como una "conversación" con la BD
SessionLocal = sessionmaker(bind=engine)

# get_db() = Función que "presta" una sesión
# Garantiza que siempre se cierre al terminar
def get_db():
    db = SessionLocal()
    try:
        yield db  # "Prestar" la sesión
    finally:
        db.close()  # Cerrar cuando termine
```

---

### 3. models/ - Estructura de Datos

**¿Qué hace?**
Define cómo se ven los datos en la base de datos.

**Ejemplo: Product**

```python
class Product(Base):
    __tablename__ = "products"  # Nombre de la tabla
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(200))
    sku = Column(String(50), unique=True)
    stock_actual = Column(Integer)
    stock_minimo = Column(Integer)
    usuario_id = Column(Integer, ForeignKey("users.id"))
```

**Esto crea una tabla en PostgreSQL:**

```
products
├── id (número único)
├── nombre (texto)
├── sku (texto único)
├── stock_actual (número)
├── stock_minimo (número)
└── usuario_id (referencia a users)
```

---

### 4. schemas/ - Validación

**¿Qué hace?**
Define qué datos son válidos para entrar/salir de la API.

**Diferencia con Models:**
- **Models** → Cómo se guarda en BD
- **Schemas** → Qué acepta/devuelve la API

**Ejemplo:**

```python
# Schema para CREAR producto
class ProductCreate(BaseModel):
    nombre: str
    sku: str
    stock_actual: int
    stock_minimo: int

# Schema para RESPUESTA
class ProductResponse(BaseModel):
    id: int
    nombre: str
    sku: str
    stock_actual: int
    stock_minimo: int
    usuario_id: int
    created_at: datetime
```

**¿Por qué separar?**

Cuando CREAS un producto:
- No envías el ID (se genera automático)
- No envías created_at (se genera automático)

Cuando RECIBES un producto:
- Sí incluye ID y created_at

---

### 5. services/ - Lógica de Negocio

**¿Qué hace?**
Aquí vive la "inteligencia" del sistema.

**Ejemplo: Servicio de Ventas**

```python
def registrar_venta(db, venta_data, usuario):
    # 1. Buscar producto
    producto = db.query(Product).filter(...).first()
    
    # 2. Verificar stock
    if producto.stock_actual < venta_data.cantidad:
        raise HTTPException("Stock insuficiente")
    
    # 3. Descontar stock
    producto.stock_actual -= venta_data.cantidad
    
    # 4. Crear venta
    venta = Sale(...)
    db.add(venta)
    
    # 5. ¿Enviar alerta?
    if producto.stock_actual <= producto.stock_minimo:
        enviar_alerta(...)
    
    # 6. Guardar
    db.commit()
    
    return venta
```

**¿Por qué no poner esto en las rutas?**

Separación de responsabilidades:
- **Rutas** → Maneja HTTP
- **Servicios** → Maneja lógica

Esto permite:
- Reutilizar lógica
- Probar más fácil
- Código más limpio

---

### 6. routes/ - Endpoints HTTP

**¿Qué hace?**
Define los endpoints (URLs) de la API.

**Ejemplo:**

```python
@router.post("/sales")
def registrar_nueva_venta(
    venta: SaleCreate,              # ← Valida datos
    db: Session = Depends(get_db),  # ← Obtiene BD
    user: User = Depends(get_current_user)  # ← Autenticación
):
    # Llamar al servicio
    resultado = registrar_venta(db, venta, user)
    
    # Devolver respuesta
    return resultado
```

**Depends() = Inyección de Dependencias**

FastAPI "inyecta" automáticamente:
- `db` → Sesión de base de datos
- `user` → Usuario autenticado

---

## Cómo Funciona una Venta

### Paso a Paso Detallado

```python
# 1. Cliente envía:
POST /sales
{
  "producto_id": 1,
  "cantidad": 5
}

# 2. FastAPI valida con SaleCreate:
class SaleCreate(BaseModel):
    producto_id: int  # Debe ser número entero
    cantidad: int     # Debe ser número > 0

# 3. Ruta llama al servicio:
registrar_venta(db, venta_data, current_user)

# 4. Servicio ejecuta:

# Buscar producto
producto = db.query(Product).filter(
    Product.id == venta_data.producto_id
).first()

# ¿Existe?
if not producto:
    raise HTTPException(404, "Producto no encontrado")

# ¿Es del usuario?
if producto.usuario_id != current_user.id:
    raise HTTPException(403, "No es tu producto")

# ¿Hay stock?
if producto.stock_actual < venta_data.cantidad:
    raise HTTPException(400, "Stock insuficiente")

# Descontar stock
stock_anterior = producto.stock_actual  # 100
producto.stock_actual -= venta_data.cantidad  # 100 - 5 = 95

# Crear registro de venta
nueva_venta = Sale(
    producto_id=producto.id,
    cantidad=venta_data.cantidad
)
db.add(nueva_venta)

# ¿Stock bajo?
if producto.stock_actual <= producto.stock_minimo:
    if not producto.alerta_enviada:
        # Enviar email
        enviar_alerta_stock_bajo(...)
        producto.alerta_enviada = True

# Guardar todo
db.commit()

# 5. Responder al cliente:
{
  "venta": {
    "id": 1,
    "producto_id": 1,
    "cantidad": 5,
    "stock_restante": 95
  },
  "alerta_enviada": false,
  "mensaje": "Venta registrada"
}
```

---

## Sistema de Alertas

### ¿Cómo funciona?

```python
# Bandera: alerta_enviada
# - False: No se ha enviado alerta
# - True: Ya se envió, no enviar de nuevo

# Función en Product model:
def necesita_alerta(self):
    return (
        self.stock_actual <= self.stock_minimo  # Stock está bajo
        and not self.alerta_enviada             # No se ha enviado
    )

# Al registrar venta:
if producto.necesita_alerta():
    enviar_alerta(...)
    producto.alerta_enviada = True

# Al aumentar stock:
if producto.stock_actual > producto.stock_minimo:
    producto.alerta_enviada = False  # Resetear bandera
```

### Email de Alerta

```python
def enviar_alerta_stock_bajo(...):
    # Construir email
    mensaje = Mail(
        from_email="alertas@tuempresa.cl",
        to_emails=usuario.email,
        subject="⚠️ Stock Bajo",
        html_content="<html>...</html>"
    )
    
    # Enviar con SendGrid
    sg = SendGridAPIClient(api_key)
    sg.send(mensaje)
```

---

## Seguridad

### Autenticación: JWT vs API Key

**JWT (JSON Web Token)**
- Se genera al hacer login
- Expira en 30 días
- Contiene: user_id, email, fecha_expiración

**API Key**
- Se genera al registrarse
- No expira nunca
- Formato: `sk_abc123xyz789`

### ¿Cómo se verifica?

```python
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    # Extraer token del header
    # Authorization: Bearer TOKEN_O_KEY
    
    token = authorization.split()[1]
    
    if token.startswith("sk_"):
        # Es API Key
        user = db.query(User).filter(
            User.api_key == token
        ).first()
    else:
        # Es JWT
        payload = jwt.decode(token, secret_key)
        user = db.query(User).filter(
            User.id == payload['user_id']
        ).first()
    
    if not user:
        raise HTTPException(401, "No autenticado")
    
    return user
```

### Protección de Contraseñas

```python
# NUNCA guardar contraseñas en texto plano
# Usar hash (encriptación irreversible)

# Al registrarse:
hashed = hash_password("mipassword123")
# Resultado: "$2b$12$KIX..."

# Al hacer login:
verify_password("mipassword123", hashed)
# Retorna True si coincide
```

---

## Diagrama de Flujo Completo

```
CLIENTE
  │
  │ POST /sales { producto_id: 1, cantidad: 5 }
  │
  ▼
FASTAPI (main.py)
  │
  │ Verificar JSON válido
  │
  ▼
RUTA (routes/sales.py)
  │
  │ ¿Usuario autenticado?
  │ ¿Datos válidos?
  │
  ▼
SERVICIO (services/sale_service.py)
  │
  ├─► ¿Producto existe?
  ├─► ¿Es del usuario?
  ├─► ¿Hay stock?
  │
  ├─► Descontar stock
  ├─► Crear venta
  │
  ├─► ¿Stock bajo?
  │   └─► SÍ → Enviar email (alert_service.py)
  │
  ▼
BASE DE DATOS
  │
  │ UPDATE products SET stock_actual = 95
  │ INSERT INTO sales (...)
  │ COMMIT
  │
  ▼
RESPUESTA AL CLIENTE
  │
  │ { venta: {...}, alerta_enviada: true }
  │
  ▼
CLIENTE recibe respuesta
```

---

## Resumen para No Programadores

**El sistema es como una tienda física:**

1. **Base de datos** = Tu bodega donde guardas productos
2. **Modelos** = Las etiquetas en cada producto (nombre, SKU, cantidad)
3. **Rutas** = La caja registradora donde vendes
4. **Servicios** = El encargado que verifica stock y hace pedidos
5. **Alertas** = El sistema de alarma que te avisa cuando algo se acaba

**Cuando vendes algo:**

1. Cliente dice: "Quiero comprar 5 camisetas"
2. Caja (ruta) recibe la orden
3. Encargado (servicio) va a la bodega (BD)
4. Verifica que hay 5 camisetas
5. Las saca de la bodega (descuenta stock)
6. Registra la venta
7. Si quedan pocas, activa la alarma (email)
8. Te da un recibo (respuesta)

**Seguridad:**

- Solo el dueño puede ver su inventario
- Necesitas una "llave" (token/API key) para entrar
- Tu contraseña está encriptada (nadie la puede ver)

---

**¿Preguntas frecuentes?**

**P: ¿Por qué tantos archivos?**
R: Cada archivo tiene una responsabilidad. Es más fácil encontrar y arreglar cosas.

**P: ¿Qué es SQLAlchemy?**
R: Es como un traductor entre Python y PostgreSQL. Escribes Python y él lo convierte a SQL.

**P: ¿Qué es Pydantic?**
R: Es un validador. Verifica que los datos que entran sean correctos.

**P: ¿Por qué usar servicios?**
R: Para separar la lógica. Las rutas manejan HTTP, los servicios manejan reglas de negocio.

**P: ¿Cómo se comunica con Supabase?**
R: Supabase es PostgreSQL. SQLAlchemy se conecta igual que a cualquier PostgreSQL.
