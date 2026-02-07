# 📊 Configuración de Google Sheets API

Esta guía te enseña cómo configurar la integración con Google Sheets paso a paso.

## 🎯 ¿Para qué sirve?

Con esta integración puedes:
- Importar productos directamente desde Google Sheets
- Colaborar en tiempo real con tu equipo
- Mantener tu inventario sincronizado con una planilla en la nube

---

## 📝 Requisitos Previos

- Cuenta de Google (Gmail)
- 10-15 minutos para la configuración inicial

---

## 🔧 Paso 1: Crear Proyecto en Google Cloud

### 1.1. Ve a Google Cloud Console

Abre: https://console.cloud.google.com

### 1.2. Crear Nuevo Proyecto

1. Click en el menú desplegable de proyectos (arriba izquierda)
2. Click en "Nuevo Proyecto"
3. Nombre: `API Inventario`
4. Click en "Crear"

### 1.3. Seleccionar el Proyecto

Asegúrate de que "API Inventario" esté seleccionado en el menú superior.

---

## 📚 Paso 2: Habilitar Google Sheets API

### 2.1. Ir a APIs y Servicios

1. Menú ☰ → "APIs y servicios" → "Biblioteca"
2. Buscar: "Google Sheets API"
3. Click en "Google Sheets API"
4. Click en "HABILITAR"

---

## 🔐 Paso 3: Crear Credenciales OAuth

### 3.1. Configurar Pantalla de Consentimiento

1. Menú ☰ → "APIs y servicios" → "Pantalla de consentimiento de OAuth"
2. Seleccionar: **Externo**
3. Click en "Crear"

**Configuración:**
- Nombre de la aplicación: `API Inventario PYME`
- Correo de soporte: Tu email
- Dominios autorizados: Dejar vacío
- Correo del desarrollador: Tu email
- Click en "Guardar y continuar"

**Ámbitos:**
- Click en "Guardar y continuar" (sin agregar ámbitos)

**Usuarios de prueba:**
- Agregar tu email
- Click en "Guardar y continuar"

**Resumen:**
- Click en "Volver al panel"

### 3.2. Crear Credenciales

1. Menú ☰ → "APIs y servicios" → "Credenciales"
2. Click en "+ CREAR CREDENCIALES"
3. Seleccionar: "ID de cliente de OAuth"

**Configuración:**
- Tipo de aplicación: **Aplicación de escritorio**
- Nombre: `Cliente de escritorio Inventario`
- Click en "Crear"

### 3.3. Descargar Credenciales

1. Aparecerá un diálogo con tu ID de cliente
2. Click en "DESCARGAR JSON"
3. Renombrar el archivo descargado a: `credentials.json`
4. Mover `credentials.json` a la raíz de tu proyecto:
   ```
   inventario-api/
   ├── credentials.json  ← Aquí
   ├── app/
   ├── requirements.txt
   └── ...
   ```

---

## ✅ Paso 4: Verificar Instalación

### 4.1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4.2. Probar Conexión

Crea un archivo `test_google_sheets.py`:

```python
from app.services.google_sheets_service import obtener_credenciales_google

# Esto abrirá el flujo de autenticación
creds = obtener_credenciales_google()

if creds:
    print("✅ Autenticación exitosa!")
else:
    print("❌ Error en autenticación")
```

Ejecutar:
```bash
python test_google_sheets.py
```

**Esto hará:**
1. Abrirá tu navegador
2. Te pedirá autorizar la aplicación
3. Generará un archivo `token.pickle` (guarda esto, evita autenticar de nuevo)

---

## 📊 Paso 5: Crear Tu Google Sheet

### 5.1. Crear Nueva Hoja

1. Ve a https://sheets.google.com
2. Click en "+ En blanco"
3. Nombrar: "Inventario - [Tu Negocio]"

### 5.2. Configurar Columnas

En la primera fila, escribe estos headers (en orden):

```
A         | B   | C            | D
nombre    | sku | stock_actual | stock_minimo
```

### 5.3. Agregar Datos de Ejemplo

```
nombre          | sku      | stock_actual | stock_minimo
Coca Cola 1.5L  | BEB-001  | 100          | 20
Pan Hallulla    | PAN-001  | 200          | 50
Leche Entera 1L | LAC-001  | 50           | 10
```

### 5.4. Compartir la Hoja

1. Click en "Compartir" (arriba derecha)
2. En "Acceso general", seleccionar: **Cualquiera con el enlace**
3. Permiso: **Lector**
4. Click en "Copiar enlace"

**Guardar este enlace**, lo usarás para importar.

---

## 🚀 Paso 6: Usar la Importación

### 6.1. Desde la API

```bash
curl -X POST "http://localhost:8000/import/google-sheets" \
  -H "Authorization: Bearer TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/ABC123/edit",
    "actualizar": false
  }'
```

### 6.2. Desde Python

```python
import requests

headers = {"Authorization": "Bearer TU_TOKEN"}
data = {
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/ABC123/edit",
    "actualizar": False
}

response = requests.post(
    "http://localhost:8000/import/google-sheets",
    json=data,
    headers=headers
)

print(response.json())
```

---

## 🔒 Seguridad

### Archivos Sensibles

**NUNCA subas estos archivos a Git:**
- `credentials.json` (credenciales de Google)
- `token.pickle` (token de autenticación)

Estos archivos YA están en `.gitignore`.

### Permisos

La aplicación solo necesita permisos de **lectura** de Google Sheets.

---

## ❓ Solución de Problemas

### Error: "credentials.json not found"

**Solución:**
- Asegúrate de que `credentials.json` esté en la raíz del proyecto
- Verifica que el nombre sea exactamente `credentials.json`

### Error: "Access denied"

**Solución:**
- Verifica que la Google Sheet esté compartida públicamente
- Asegúrate de haber autorizado la aplicación

### Error: "Invalid scope"

**Solución:**
- Borra el archivo `token.pickle`
- Vuelve a ejecutar la autenticación

### La importación no encuentra datos

**Solución:**
- Verifica que los headers estén en la primera fila
- Verifica que las columnas se llamen exactamente: `nombre`, `sku`, `stock_actual`, `stock_minimo`
- Asegúrate de que la hoja no esté vacía

---

## 📊 Formato Avanzado

### Usar Rangos Específicos

Puedes especificar qué rango leer:

```python
# Solo leer filas 1-100
spreadsheet_url = "..."
rango = "A1:D100"

# Solo leer una hoja específica
rango = "Hoja1!A1:D100"

# Leer múltiples columnas
rango = "A1:Z1000"
```

### Múltiples Hojas

Si tu Google Sheet tiene múltiples pestañas:

```python
# Leer la pestaña "Productos"
rango = "Productos!A1:D1000"

# Leer la pestaña "Inventario"
rango = "Inventario!A1:D1000"
```

---

## 🎯 Mejores Prácticas

### 1. Mantén una Hoja Maestra

- Usa una Google Sheet como "fuente de verdad"
- Importa regularmente para mantener sincronizado

### 2. Usa Validación de Datos

En Google Sheets:
1. Selecciona la columna `stock_actual`
2. Datos → Validación de datos
3. Criterios: Número → Mayor o igual a → 0

### 3. Código de Colores

- Verde: Stock alto
- Amarillo: Stock cercano al mínimo
- Rojo: Stock bajo el mínimo

---

## 🚀 Automatización (Avanzado)

### Sincronización Automática

Puedes crear un script que importe automáticamente cada hora:

```python
import schedule
import time
from app.services.google_sheets_service import importar_desde_google_sheet

def sincronizar():
    print("🔄 Sincronizando con Google Sheets...")
    # Tu código de importación aquí
    print("✅ Sincronización completa")

# Ejecutar cada hora
schedule.every().hour.do(sincronizar)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 📚 Recursos Adicionales

- **Documentación Google Sheets API**: https://developers.google.com/sheets/api
- **Google Cloud Console**: https://console.cloud.google.com
- **Límites de la API**: 60 solicitudes/minuto (suficiente para PYME)

---

## ✅ Checklist de Configuración

- [ ] Proyecto creado en Google Cloud
- [ ] Google Sheets API habilitada
- [ ] Credenciales OAuth creadas
- [ ] Archivo `credentials.json` descargado
- [ ] Archivo movido a la raíz del proyecto
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Autenticación exitosa (generó `token.pickle`)
- [ ] Google Sheet creada con formato correcto
- [ ] Hoja compartida públicamente
- [ ] Primera importación exitosa

---

**¡Listo! Ahora puedes importar productos desde Google Sheets. 🎉**
