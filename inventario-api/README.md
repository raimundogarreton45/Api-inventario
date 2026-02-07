# 🏪 API de Inventario para PYME

Sistema de control de inventario diseñado para pequeñas empresas chilenas.

## 📋 Características

- ✅ **Gestión de Productos**: CRUD completo
- 💰 **Registro de Ventas**: Descuento automático de stock
- ⚠️ **Alertas por Email**: Notificaciones cuando el stock está bajo
- 🔐 **Autenticación Segura**: JWT + API Keys
- 👥 **Multi-usuario**: Cada usuario gestiona su propio inventario
- 📊 **Estadísticas**: Resumen de ventas y productos más vendidos

---

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.11+
- PostgreSQL (usaremos Supabase)
- Cuenta de SendGrid (para emails)

### 1. Clonar/Descargar el Proyecto

```bash
cd inventario-api
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copia el archivo de ejemplo y edítalo con tus datos:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus configuraciones:

```env
# Base de datos (ver sección "Conectar con Supabase")
DATABASE_URL=postgresql://postgres:TU_PASSWORD@db.TU_PROYECTO.supabase.co:5432/postgres

# Clave secreta (genera una nueva)
SECRET_KEY=tu_clave_secreta_aqui

# SendGrid (ver sección "Configurar SendGrid")
SENDGRID_API_KEY=SG.xxxxxxxxxx
SENDGRID_FROM_EMAIL=tu@email.cl
```

### 5. Generar Clave Secreta

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copia el resultado y úsalo como `SECRET_KEY` en tu archivo `.env`.

### 6. Correr la Aplicación

```bash
uvicorn app.main:app --reload
```

La API estará disponible en: **http://localhost:8000**

Documentación interactiva: **http://localhost:8000/docs**

---

## 🗄️ Conectar con Supabase

### Paso 1: Crear Proyecto en Supabase

1. Ve a [supabase.com](https://supabase.com)
2. Crea una cuenta (es gratis)
3. Click en "New Project"
4. Elige un nombre, contraseña y región (Santiago si está disponible)

### Paso 2: Obtener la URL de Conexión

1. En tu proyecto de Supabase, ve a **Settings** → **Database**
2. Busca la sección **Connection string**
3. Copia la URI de PostgreSQL (algo como):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijk.supabase.co:5432/postgres
   ```
4. Reemplaza `[YOUR-PASSWORD]` con la contraseña que configuraste
5. Pega esta URL en tu archivo `.env` como `DATABASE_URL`

### Paso 3: Verificar Conexión

Al iniciar la API, deberías ver:

```
✅ Tablas creadas exitosamente
```

Si ves un error de conexión:
- Verifica que la URL esté correcta
- Verifica que la contraseña sea correcta
- Asegúrate de no tener espacios al inicio/final de la URL

---

## 📧 Configurar SendGrid

### Paso 1: Crear Cuenta en SendGrid

1. Ve a [sendgrid.com](https://sendgrid.com)
2. Crea una cuenta gratuita (permite 100 emails/día)

### Paso 2: Verificar tu Email (Sender)

1. Ve a **Settings** → **Sender Authentication**
2. Click en **Verify a Single Sender**
3. Completa el formulario con tu email
4. Verifica tu email (revisa tu bandeja de entrada)

### Paso 3: Crear API Key

1. Ve a **Settings** → **API Keys**
2. Click en **Create API Key**
3. Nombre: "Inventario API"
4. Permisos: **Full Access**
5. Click en **Create & View**
6. **IMPORTANTE**: Copia la API Key (solo la verás una vez)

### Paso 4: Configurar en .env

```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=tu@email.cl  # El email que verificaste en Paso 2
```

### Paso 5: Probar Envío de Email

```bash
python -c "from app.services.alert_service import probar_envio_email; probar_envio_email('tu@email.cl')"
```

Deberías recibir un email de prueba.

---

## 📖 Uso de la API

### Flujo Básico

#### 1. Registrar Usuario

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "email": "juan@ejemplo.cl",
    "password": "mipassword123"
  }'
```

Respuesta:
```json
{
  "id": 1,
  "nombre": "Juan Pérez",
  "email": "juan@ejemplo.cl",
  "api_key": "sk_abc123xyz789",
  "created_at": "2024-02-06T10:30:00"
}
```

**Guarda tu API Key** - la necesitarás para autenticarte.

#### 2. Iniciar Sesión

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan@ejemplo.cl",
    "password": "mipassword123"
  }'
```

Respuesta:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { ... }
}
```

**Guarda tu access_token** - lo usarás en cada petición.

#### 3. Crear Producto

```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "nombre": "Camiseta Nike Negra Talla M",
    "sku": "CAM-NIKE-001",
    "stock_actual": 50,
    "stock_minimo": 10
  }'
```

#### 4. Registrar Venta

```bash
curl -X POST http://localhost:8000/sales \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "producto_id": 1,
    "cantidad": 5
  }'
```

**Esto automáticamente**:
- Descuenta 5 unidades del stock
- Si el stock queda ≤ stock_minimo, envía un email de alerta

#### 5. Listar Productos

```bash
curl -X GET http://localhost:8000/products \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

#### 6. Ver Productos con Stock Bajo

```bash
curl -X GET "http://localhost:8000/products?stock_bajo=true" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

---

## 🔐 Autenticación

Hay dos formas de autenticarse:

### Opción 1: JWT Token (recomendado)

1. Haz login y obtén el `access_token`
2. Úsalo en cada petición:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
3. El token expira en 30 días

### Opción 2: API Key

1. Obtén tu API Key al registrarte
2. Úsala directamente:
   ```
   Authorization: Bearer sk_abc123xyz789
   ```
3. La API Key no expira

---

## 🌐 Deploy en Render (Free Tier)

### Paso 1: Preparar el Proyecto

Crear archivo `render.yaml` en la raíz del proyecto:

```yaml
services:
  - type: web
    name: inventario-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: SECRET_KEY
        sync: false
      - key: SENDGRID_API_KEY
        sync: false
      - key: SENDGRID_FROM_EMAIL
        sync: false
      - key: ENVIRONMENT
        value: production
```

### Paso 2: Subir a GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/tu-usuario/inventario-api.git
git push -u origin main
```

### Paso 3: Deploy en Render

1. Ve a [render.com](https://render.com)
2. Crea una cuenta y conecta tu GitHub
3. Click en **New** → **Web Service**
4. Selecciona tu repositorio `inventario-api`
5. Configuración:
   - **Name**: inventario-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Click en **Advanced** y agrega las variables de entorno:
   - `DATABASE_URL`: Tu URL de Supabase
   - `SECRET_KEY`: Tu clave secreta
   - `SENDGRID_API_KEY`: Tu API key de SendGrid
   - `SENDGRID_FROM_EMAIL`: Tu email verificado
   - `ENVIRONMENT`: production
7. Click en **Create Web Service**

### Paso 4: Verificar

Tu API estará disponible en:
```
https://inventario-api.onrender.com
```

Documentación:
```
https://inventario-api.onrender.com/docs
```

---

## 🧪 Probar la API

### Usando Swagger UI

1. Ve a http://localhost:8000/docs
2. Click en **Authorize** 🔓
3. Ingresa: `Bearer TU_TOKEN_O_API_KEY`
4. Ahora puedes probar todos los endpoints directamente desde el navegador

### Usando Postman

1. Importa la colección (puedes crear una desde la documentación)
2. En cada request, agrega el header:
   ```
   Authorization: Bearer TU_TOKEN
   ```

### Usando Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/auth/login",
    json={
        "email": "juan@ejemplo.cl",
        "password": "mipassword123"
    }
)

token = response.json()["access_token"]

# Crear producto
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://localhost:8000/products",
    json={
        "nombre": "Producto de Prueba",
        "sku": "PROD-001",
        "stock_actual": 100,
        "stock_minimo": 20
    },
    headers=headers
)

print(response.json())
```

---

## 📁 Estructura del Proyecto

```
inventario-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicación principal
│   ├── config.py            # Configuración
│   ├── database.py          # Conexión a BD
│   ├── auth.py              # Autenticación
│   │
│   ├── models/              # Modelos de BD
│   │   ├── user.py
│   │   ├── product.py
│   │   └── sale.py
│   │
│   ├── schemas/             # Validación de datos
│   │   ├── user.py
│   │   ├── product.py
│   │   └── sale.py
│   │
│   ├── routes/              # Endpoints
│   │   ├── auth.py
│   │   ├── products.py
│   │   └── sales.py
│   │
│   └── services/            # Lógica de negocio
│       ├── product_service.py
│       ├── sale_service.py
│       └── alert_service.py
│
├── .env                     # Variables de entorno (NO SUBIR A GIT)
├── .env.example             # Ejemplo de variables
├── requirements.txt         # Dependencias
└── README.md               # Este archivo
```

---

## ❓ Preguntas Frecuentes

### ¿Cómo resetear la bandera de alerta?

Cuando aumentes el stock por encima del mínimo, la bandera se resetea automáticamente.

### ¿Puedo cambiar el mínimo de stock?

Sí, usa `PUT /products/{id}` y actualiza `stock_minimo`.

### ¿Cómo eliminar un producto?

```bash
curl -X DELETE http://localhost:8000/products/1 \
  -H "Authorization: Bearer TU_TOKEN"
```

### ¿Cómo ver mis estadísticas de ventas?

```bash
curl -X GET http://localhost:8000/sales/stats/summary \
  -H "Authorization: Bearer TU_TOKEN"
```

---

## 🐛 Solución de Problemas

### Error: "Could not connect to database"

- Verifica que tu `DATABASE_URL` en `.env` sea correcta
- Verifica que Supabase esté activo
- Verifica que la contraseña no tenga caracteres especiales sin escapar

### Error: "SendGrid API error"

- Verifica que tu `SENDGRID_API_KEY` sea correcta
- Verifica que el email de origen esté verificado en SendGrid
- Revisa los logs para ver el error específico

### Error: "Could not validate credentials"

- Verifica que estés enviando el header `Authorization` correctamente
- Verifica que el token no haya expirado (30 días)
- Usa tu API Key como alternativa

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs de la aplicación
2. Verifica que todas las variables de entorno estén configuradas
3. Prueba los endpoints desde `/docs` (Swagger UI)

---

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

**¡Éxito con tu inventario! 🚀**
