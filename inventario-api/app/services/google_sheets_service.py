"""
SERVICIO: IMPORTACIÓN DESDE GOOGLE SHEETS

Permite importar productos desde Google Sheets usando la API de Google.

SETUP REQUERIDO:
1. Crear proyecto en Google Cloud Console
2. Habilitar Google Sheets API
3. Crear credenciales OAuth 2.0
4. Descargar credentials.json

FORMATO DE SHEET:
    A        | B   | C            | D
    nombre   | sku | stock_actual | stock_minimo
    Producto1| SKU1| 100          | 10
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Product, User
from app.services.excel_import_service import ExcelImportResult


# ============================================
# CONFIGURACIÓN DE GOOGLE OAUTH
# ============================================

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'


def obtener_credenciales_google() -> Optional[Credentials]:
    """
    Obtiene credenciales de Google OAuth.
    
    Si ya existe un token guardado, lo usa.
    Si no, inicia el flujo de autenticación.
    
    Retorna:
        Credentials o None si no se pudo autenticar
    """
    creds = None
    
    # Verificar si hay un token guardado
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # Si no hay credenciales válidas, iniciar flujo de autenticación
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refrescar token expirado
            creds.refresh(Request())
        else:
            # Nuevo flujo de autenticación
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"No se encontró {CREDENTIALS_FILE}. "
                    "Descárgalo desde Google Cloud Console."
                )
            
            flow = Flow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            # Generar URL de autorización
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            print(f"\n🔐 Abre esta URL en tu navegador:\n{auth_url}\n")
            code = input("Ingresa el código de autorización: ")
            
            flow.fetch_token(code=code)
            creds = flow.credentials
        
        # Guardar credenciales
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds


def leer_google_sheet(
    spreadsheet_id: str,
    rango: str = "A1:Z1000"
) -> List[List[Any]]:
    """
    Lee datos de una Google Sheet.
    
    Args:
        spreadsheet_id: ID de la hoja (está en la URL)
            Ej: docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
        rango: Rango de celdas a leer (formato A1)
    
    Retorna:
        Lista de listas con los valores
    
    Raises:
        HTTPException: Si no se puede leer la hoja
    """
    try:
        creds = obtener_credenciales_google()
        service = build('sheets', 'v4', credentials=creds)
        
        # Leer hoja
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=rango
        ).execute()
        
        valores = result.get('values', [])
        
        if not valores:
            raise HTTPException(
                status_code=404,
                detail="La hoja está vacía o no se pudo leer"
            )
        
        return valores
    
    except HttpError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error de Google Sheets API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al leer Google Sheet: {str(e)}"
        )


def validar_columnas_sheet(valores: List[List[Any]]) -> tuple[bool, str]:
    """
    Valida que la sheet tenga las columnas necesarias.
    
    Args:
        valores: Datos de la sheet
    
    Retorna:
        Tuple[bool, str]: (es_valido, mensaje_error)
    """
    if len(valores) < 1:
        return False, "La hoja está vacía"
    
    # Primera fila = headers
    headers = [str(h).lower().strip() for h in valores[0]]
    
    columnas_requeridas = ['nombre', 'sku', 'stock_actual', 'stock_minimo']
    
    for columna in columnas_requeridas:
        if columna not in headers:
            return False, f"Falta la columna requerida: '{columna}'"
    
    return True, ""


def parsear_fila_sheet(
    fila: List[Any],
    headers: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Convierte una fila de Google Sheet a diccionario.
    
    Args:
        fila: Lista de valores de la fila
        headers: Lista de nombres de columnas
    
    Retorna:
        Dict con los datos o None si la fila está vacía
    """
    # Si la fila está vacía, ignorar
    if not fila or all(v == '' for v in fila):
        return None
    
    # Crear diccionario con valores por defecto
    datos = {}
    
    for i, header in enumerate(headers):
        valor = fila[i] if i < len(fila) else ''
        
        # Limpiar y convertir
        if header in ['nombre', 'sku']:
            datos[header] = str(valor).strip()
        elif header in ['stock_actual', 'stock_minimo']:
            try:
                datos[header] = int(valor) if valor != '' else 0
            except ValueError:
                datos[header] = 0
    
    return datos


async def importar_desde_google_sheet(
    spreadsheet_id: str,
    db: Session,
    usuario: User,
    rango: str = "A1:Z1000",
    actualizar_existentes: bool = False
) -> Dict[str, Any]:
    """
    Importa productos desde Google Sheets.
    
    Args:
        spreadsheet_id: ID de la Google Sheet
        db: Sesión de base de datos
        usuario: Usuario que importa
        rango: Rango de celdas (default: toda la hoja)
        actualizar_existentes: Si True, actualiza productos existentes
    
    Retorna:
        Dict con resultados de la importación
    """
    # Leer datos de Google Sheet
    valores = leer_google_sheet(spreadsheet_id, rango)
    
    # Validar columnas
    es_valido, mensaje_error = validar_columnas_sheet(valores)
    if not es_valido:
        raise HTTPException(status_code=400, detail=mensaje_error)
    
    # Extraer headers y datos
    headers = [str(h).lower().strip() for h in valores[0]]
    filas_datos = valores[1:]
    
    # Inicializar resultado
    resultado = ExcelImportResult()
    resultado.total = len(filas_datos)
    
    # Procesar cada fila
    for index, fila in enumerate(filas_datos):
        fila_num = index + 2  # +2 porque Google Sheets empieza en 1 y tiene header
        
        try:
            # Parsear fila
            datos = parsear_fila_sheet(fila, headers)
            
            if not datos:
                continue  # Fila vacía
            
            # Validar datos
            if not datos.get('nombre'):
                resultado.agregar_error(fila_num, datos.get('sku', 'N/A'), "Nombre vacío")
                continue
            
            if not datos.get('sku'):
                resultado.agregar_error(fila_num, 'N/A', "SKU vacío")
                continue
            
            if datos['stock_actual'] < 0:
                resultado.agregar_error(fila_num, datos['sku'], "Stock actual no puede ser negativo")
                continue
            
            if datos['stock_minimo'] < 0:
                resultado.agregar_error(fila_num, datos['sku'], "Stock mínimo no puede ser negativo")
                continue
            
            # Verificar si el producto ya existe
            producto_existente = db.query(Product).filter(
                Product.sku == datos['sku'],
                Product.usuario_id == usuario.id
            ).first()
            
            if producto_existente:
                if actualizar_existentes:
                    # Actualizar
                    producto_existente.nombre = datos['nombre']
                    producto_existente.stock_actual = datos['stock_actual']
                    producto_existente.stock_minimo = datos['stock_minimo']
                    
                    if producto_existente.stock_actual > producto_existente.stock_minimo:
                        producto_existente.alerta_enviada = False
                    
                    db.commit()
                    resultado.agregar_exito(
                        fila_num,
                        datos['sku'],
                        "actualizado",
                        f"Stock: {producto_existente.stock_actual}"
                    )
                else:
                    resultado.agregar_error(
                        fila_num,
                        datos['sku'],
                        "SKU duplicado"
                    )
            else:
                # Crear nuevo
                nuevo_producto = Product(
                    nombre=datos['nombre'],
                    sku=datos['sku'],
                    stock_actual=datos['stock_actual'],
                    stock_minimo=datos['stock_minimo'],
                    usuario_id=usuario.id
                )
                
                db.add(nuevo_producto)
                db.commit()
                
                resultado.agregar_exito(fila_num, datos['sku'], "creado")
        
        except Exception as e:
            db.rollback()
            resultado.agregar_error(
                fila_num,
                datos.get('sku', 'N/A') if datos else 'N/A',
                f"Error: {str(e)}"
            )
    
    return resultado.to_dict()


def extraer_spreadsheet_id_de_url(url: str) -> str:
    """
    Extrae el ID de spreadsheet de una URL de Google Sheets.
    
    Args:
        url: URL completa de Google Sheets
            Ej: https://docs.google.com/spreadsheets/d/ABC123/edit
    
    Retorna:
        str: ID del spreadsheet
    
    Raises:
        ValueError: Si la URL no es válida
    """
    import re
    
    # Patrón para extraer ID
    patron = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
    match = re.search(patron, url)
    
    if match:
        return match.group(1)
    else:
        raise ValueError("URL de Google Sheets no válida")


# ============================================
# EJEMPLO DE USO
# ============================================
#
# @router.post("/products/import/google-sheets")
# async def importar_google_sheet(
#     spreadsheet_url: str,
#     actualizar: bool = False,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     # Extraer ID de la URL
#     spreadsheet_id = extraer_spreadsheet_id_de_url(spreadsheet_url)
#     
#     # Importar
#     resultado = await importar_desde_google_sheet(
#         spreadsheet_id, db, user, actualizar_existentes=actualizar
#     )
#     
#     return resultado
