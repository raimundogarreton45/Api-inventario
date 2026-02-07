"""
SERVICIO: IMPORTACIÓN DESDE EXCEL

Permite importar productos desde archivos Excel (.xlsx, .xls).

FORMATO ESPERADO:
    nombre | sku | stock_actual | stock_minimo
    -------|-----|--------------|-------------
    Prod 1 | SKU1| 100          | 10
    Prod 2 | SKU2| 50           | 5

CARACTERÍSTICAS:
- Valida datos antes de importar
- Detecta productos duplicados
- Actualiza productos existentes
- Genera reporte de resultados
"""

import pandas as pd
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import UploadFile, HTTPException
import io

from app.models import Product, User
from app.schemas import ProductCreate


class ExcelImportResult:
    """
    Resultado de una importación desde Excel.
    
    Atributos:
        total: Total de filas procesadas
        exitosos: Número de productos creados/actualizados
        errores: Número de errores
        detalles: Lista de mensajes detallados
    """
    def __init__(self):
        self.total = 0
        self.exitosos = 0
        self.errores = 0
        self.creados = 0
        self.actualizados = 0
        self.detalles: List[Dict[str, Any]] = []
    
    def agregar_exito(self, fila: int, sku: str, accion: str, mensaje: str = ""):
        """Registra un producto importado exitosamente."""
        self.exitosos += 1
        if accion == "creado":
            self.creados += 1
        elif accion == "actualizado":
            self.actualizados += 1
        
        self.detalles.append({
            "fila": fila,
            "sku": sku,
            "estado": "exitoso",
            "accion": accion,
            "mensaje": mensaje or f"Producto {accion} correctamente"
        })
    
    def agregar_error(self, fila: int, sku: str, error: str):
        """Registra un error en la importación."""
        self.errores += 1
        self.detalles.append({
            "fila": fila,
            "sku": sku,
            "estado": "error",
            "mensaje": error
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            "resumen": {
                "total_filas": self.total,
                "exitosos": self.exitosos,
                "creados": self.creados,
                "actualizados": self.actualizados,
                "errores": self.errores,
                "tasa_exito": f"{(self.exitosos/self.total*100):.1f}%" if self.total > 0 else "0%"
            },
            "detalles": self.detalles
        }


def validar_columnas_excel(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Valida que el Excel tenga las columnas necesarias.
    
    Args:
        df: DataFrame de pandas
    
    Retorna:
        Tuple[bool, str]: (es_valido, mensaje_error)
    """
    columnas_requeridas = ['nombre', 'sku', 'stock_actual', 'stock_minimo']
    columnas_excel = [col.lower().strip() for col in df.columns]
    
    for columna in columnas_requeridas:
        if columna not in columnas_excel:
            return False, f"Falta la columna requerida: '{columna}'"
    
    return True, ""


def limpiar_datos_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y normaliza los datos del Excel.
    
    Args:
        df: DataFrame original
    
    Retorna:
        DataFrame limpio
    """
    # Normalizar nombres de columnas (minúsculas, sin espacios extra)
    df.columns = [col.lower().strip() for col in df.columns]
    
    # Eliminar filas completamente vacías
    df = df.dropna(how='all')
    
    # Limpiar espacios en strings
    for col in ['nombre', 'sku']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Convertir números a int (manejando valores vacíos)
    for col in ['stock_actual', 'stock_minimo']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    return df


async def importar_desde_excel(
    archivo: UploadFile,
    db: Session,
    usuario: User,
    actualizar_existentes: bool = False
) -> Dict[str, Any]:
    """
    Importa productos desde un archivo Excel.
    
    Args:
        archivo: Archivo Excel subido
        db: Sesión de base de datos
        usuario: Usuario que importa
        actualizar_existentes: Si True, actualiza productos existentes por SKU
    
    Retorna:
        Dict con resultados de la importación
    
    Raises:
        HTTPException: Si el archivo no es válido
    """
    # Verificar extensión
    if not archivo.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=400,
            detail="Formato no válido. Use .xlsx, .xls o .csv"
        )
    
    # Leer archivo
    try:
        contenido = await archivo.read()
        
        if archivo.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contenido))
        else:
            df = pd.read_excel(io.BytesIO(contenido))
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al leer archivo: {str(e)}"
        )
    
    # Validar columnas
    es_valido, mensaje_error = validar_columnas_excel(df)
    if not es_valido:
        raise HTTPException(
            status_code=400,
            detail=mensaje_error
        )
    
    # Limpiar datos
    df = limpiar_datos_excel(df)
    
    # Inicializar resultado
    resultado = ExcelImportResult()
    resultado.total = len(df)
    
    # Procesar cada fila
    for index, fila in df.iterrows():
        fila_num = index + 2  # +2 porque Excel empieza en 1 y tiene header
        
        try:
            # Validar datos de la fila
            if pd.isna(fila['nombre']) or fila['nombre'] == '':
                resultado.agregar_error(fila_num, fila.get('sku', 'N/A'), "Nombre vacío")
                continue
            
            if pd.isna(fila['sku']) or fila['sku'] == '':
                resultado.agregar_error(fila_num, 'N/A', "SKU vacío")
                continue
            
            if fila['stock_actual'] < 0:
                resultado.agregar_error(fila_num, fila['sku'], "Stock actual no puede ser negativo")
                continue
            
            if fila['stock_minimo'] < 0:
                resultado.agregar_error(fila_num, fila['sku'], "Stock mínimo no puede ser negativo")
                continue
            
            # Verificar si el producto ya existe
            producto_existente = db.query(Product).filter(
                Product.sku == fila['sku'],
                Product.usuario_id == usuario.id
            ).first()
            
            if producto_existente:
                if actualizar_existentes:
                    # Actualizar producto existente
                    producto_existente.nombre = fila['nombre']
                    producto_existente.stock_actual = int(fila['stock_actual'])
                    producto_existente.stock_minimo = int(fila['stock_minimo'])
                    
                    # Resetear alerta si el stock subió
                    if producto_existente.stock_actual > producto_existente.stock_minimo:
                        producto_existente.alerta_enviada = False
                    
                    db.commit()
                    resultado.agregar_exito(
                        fila_num, 
                        fila['sku'], 
                        "actualizado",
                        f"Stock actualizado: {producto_existente.stock_actual}"
                    )
                else:
                    resultado.agregar_error(
                        fila_num, 
                        fila['sku'], 
                        "SKU duplicado (use modo actualización para sobrescribir)"
                    )
            else:
                # Crear nuevo producto
                nuevo_producto = Product(
                    nombre=fila['nombre'],
                    sku=fila['sku'],
                    stock_actual=int(fila['stock_actual']),
                    stock_minimo=int(fila['stock_minimo']),
                    usuario_id=usuario.id
                )
                
                db.add(nuevo_producto)
                db.commit()
                
                resultado.agregar_exito(fila_num, fila['sku'], "creado")
        
        except IntegrityError as e:
            db.rollback()
            resultado.agregar_error(
                fila_num, 
                fila.get('sku', 'N/A'), 
                "Error de base de datos (posible SKU duplicado)"
            )
        
        except Exception as e:
            db.rollback()
            resultado.agregar_error(
                fila_num, 
                fila.get('sku', 'N/A'), 
                f"Error inesperado: {str(e)}"
            )
    
    return resultado.to_dict()


def generar_plantilla_excel() -> bytes:
    """
    Genera un archivo Excel de plantilla con ejemplos.
    
    Retorna:
        bytes: Contenido del archivo Excel
    """
    # Datos de ejemplo
    datos_ejemplo = {
        'nombre': [
            'Coca Cola 1.5L',
            'Pan Hallulla',
            'Leche Entera 1L',
            'Arroz 1kg'
        ],
        'sku': [
            'BEB-COCA-001',
            'PAN-HAL-001',
            'LAC-ENT-001',
            'ARR-BLA-001'
        ],
        'stock_actual': [100, 200, 50, 80],
        'stock_minimo': [20, 50, 10, 15]
    }
    
    df = pd.DataFrame(datos_ejemplo)
    
    # Crear Excel en memoria
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Productos')
        
        # Ajustar ancho de columnas
        worksheet = writer.sheets['Productos']
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
    
    output.seek(0)
    return output.getvalue()


# ============================================
# EJEMPLO DE USO
# ============================================
#
# from fastapi import UploadFile
# 
# @router.post("/products/import/excel")
# async def importar_excel(
#     archivo: UploadFile,
#     actualizar: bool = False,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     resultado = await importar_desde_excel(archivo, db, user, actualizar)
#     return resultado
