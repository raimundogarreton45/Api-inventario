"""
RUTAS: IMPORTACIÓN DE PRODUCTOS

Endpoints para importar productos desde Excel y Google Sheets.

ENDPOINTS:
- POST /import/excel         → Importar desde Excel
- GET /import/excel/template → Descargar plantilla Excel
- POST /import/google-sheets → Importar desde Google Sheets
"""

from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.services.excel_import_service import (
    importar_desde_excel,
    generar_plantilla_excel
)
from app.services.google_sheets_service import (
    importar_desde_google_sheet,
    extraer_spreadsheet_id_de_url
)

# Crear el router
router = APIRouter(
    prefix="/import",
    tags=["Importación de Productos"]
)


# ============================================
# IMPORTAR DESDE EXCEL
# ============================================

@router.post(
    "/excel",
    summary="Importar productos desde Excel",
    description="""
    Importa productos masivamente desde un archivo Excel (.xlsx, .xls, .csv).
    
    **Formato requerido:**
    
    El archivo debe tener estas columnas (en cualquier orden):
    - nombre: Nombre del producto
    - sku: Código SKU único
    - stock_actual: Cantidad en inventario
    - stock_minimo: Cantidad mínima antes de alerta
    
    **Ejemplo de Excel:**
    ```
    nombre          | sku        | stock_actual | stock_minimo
    Coca Cola 1.5L  | BEB-001    | 100          | 20
    Pan Hallulla    | PAN-001    | 200          | 50
    ```
    
    **Modos de importación:**
    - actualizar=false (default): Solo crea productos nuevos, rechaza duplicados
    - actualizar=true: Actualiza productos existentes por SKU
    
    **Respuesta:**
    Devuelve un reporte detallado con:
    - Total de filas procesadas
    - Productos creados
    - Productos actualizados
    - Errores encontrados
    - Detalle fila por fila
    
    **Requiere autenticación.**
    """
)
async def importar_productos_desde_excel(
    archivo: UploadFile = File(..., description="Archivo Excel (.xlsx, .xls, .csv)"),
    actualizar: bool = Query(
        False, 
        description="Si es True, actualiza productos existentes. Si es False, rechaza duplicados."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para importar productos desde Excel.
    
    Procesa el archivo y retorna un reporte detallado.
    """
    resultado = await importar_desde_excel(
        archivo=archivo,
        db=db,
        usuario=current_user,
        actualizar_existentes=actualizar
    )
    
    return resultado


# ============================================
# DESCARGAR PLANTILLA EXCEL
# ============================================

@router.get(
    "/excel/template",
    summary="Descargar plantilla Excel",
    description="""
    Descarga una plantilla de Excel con el formato correcto y datos de ejemplo.
    
    La plantilla incluye:
    - Columnas con los nombres correctos
    - 4 productos de ejemplo
    - Formato listo para usar
    
    **Uso:**
    1. Descarga esta plantilla
    2. Reemplaza los datos de ejemplo con tus productos
    3. Importa el archivo usando POST /import/excel
    
    **No requiere autenticación.**
    """
)
def descargar_plantilla_excel():
    """
    Endpoint para descargar plantilla de Excel.
    
    Retorna un archivo Excel con formato de ejemplo.
    """
    # Generar plantilla
    contenido_excel = generar_plantilla_excel()
    
    # Crear respuesta como archivo descargable
    return StreamingResponse(
        io.BytesIO(contenido_excel),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=plantilla_productos.xlsx"
        }
    )


# ============================================
# IMPORTAR DESDE GOOGLE SHEETS
# ============================================

@router.post(
    "/google-sheets",
    summary="Importar productos desde Google Sheets",
    description="""
    Importa productos desde una Google Sheet compartida.
    
    **Requisitos previos:**
    1. Configurar credenciales de Google Cloud (ver documentación)
    2. Compartir la Google Sheet con "Cualquiera con el enlace"
    
    **Formato de la Google Sheet:**
    
    La hoja debe tener estas columnas en la primera fila:
    - nombre
    - sku
    - stock_actual
    - stock_minimo
    
    **Ejemplo:**
    ```
    A              | B        | C            | D
    nombre         | sku      | stock_actual | stock_minimo
    Coca Cola 1.5L | BEB-001  | 100          | 20
    Pan Hallulla   | PAN-001  | 200          | 50
    ```
    
    **URL de Google Sheets:**
    Puede ser la URL completa:
    ```
    https://docs.google.com/spreadsheets/d/ABC123XYZ/edit
    ```
    O solo el ID:
    ```
    ABC123XYZ
    ```
    
    **Parámetros:**
    - spreadsheet_url: URL o ID de la Google Sheet
    - rango: Rango de celdas (default: A1:Z1000, lee toda la hoja)
    - actualizar: Si True, actualiza productos existentes
    
    **Requiere autenticación.**
    """
)
async def importar_productos_desde_google_sheets(
    spreadsheet_url: str = Query(..., description="URL o ID de Google Sheets"),
    rango: str = Query("A1:Z1000", description="Rango de celdas (formato A1)"),
    actualizar: bool = Query(False, description="Actualizar productos existentes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para importar productos desde Google Sheets.
    
    Requiere configuración previa de credenciales de Google.
    """
    # Extraer ID si es una URL completa
    try:
        if 'docs.google.com' in spreadsheet_url:
            spreadsheet_id = extraer_spreadsheet_id_de_url(spreadsheet_url)
        else:
            spreadsheet_id = spreadsheet_url
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Importar
    resultado = await importar_desde_google_sheet(
        spreadsheet_id=spreadsheet_id,
        db=db,
        usuario=current_user,
        rango=rango,
        actualizar_existentes=actualizar
    )
    
    return resultado


# ============================================
# ENDPOINT INFORMATIVO
# ============================================

@router.get(
    "/info",
    summary="Información sobre importación",
    description="Devuelve información sobre cómo usar las funciones de importación."
)
def obtener_info_importacion():
    """
    Endpoint informativo sobre las opciones de importación.
    """
    return {
        "metodos_disponibles": [
            {
                "metodo": "Excel/CSV",
                "endpoint": "POST /import/excel",
                "formatos": [".xlsx", ".xls", ".csv"],
                "plantilla": "GET /import/excel/template",
                "ventajas": [
                    "Fácil de usar",
                    "No requiere configuración adicional",
                    "Funciona offline"
                ]
            },
            {
                "metodo": "Google Sheets",
                "endpoint": "POST /import/google-sheets",
                "requisitos": [
                    "Credenciales de Google Cloud",
                    "Hoja compartida públicamente"
                ],
                "ventajas": [
                    "Colaboración en tiempo real",
                    "Se actualiza automáticamente",
                    "Accesible desde cualquier dispositivo"
                ]
            }
        ],
        "formato_requerido": {
            "columnas": [
                {"nombre": "nombre", "tipo": "texto", "requerido": True},
                {"nombre": "sku", "tipo": "texto", "requerido": True, "unico": True},
                {"nombre": "stock_actual", "tipo": "numero", "requerido": True},
                {"nombre": "stock_minimo", "tipo": "numero", "requerido": True}
            ]
        },
        "ejemplos": {
            "excel": "Descarga plantilla en GET /import/excel/template",
            "google_sheets": "Crea una hoja con las columnas: nombre, sku, stock_actual, stock_minimo"
        }
    }
