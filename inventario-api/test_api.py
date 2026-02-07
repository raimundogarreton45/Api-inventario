"""
SCRIPT DE PRUEBA - API DE INVENTARIO

Este script demuestra cómo usar todos los endpoints de la API.

Para ejecutarlo:
    python test_api.py

IMPORTANTE: Asegúrate de que la API esté corriendo en http://localhost:8000
"""

import requests
import json
from datetime import datetime

# URL base de la API
BASE_URL = "http://localhost:8000"

# Colores para la consola
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(message):
    """Imprime mensaje de éxito en verde."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message):
    """Imprime mensaje de error en rojo."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_info(message):
    """Imprime mensaje informativo en azul."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")


def print_warning(message):
    """Imprime mensaje de advertencia en amarillo."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_json(data):
    """Imprime JSON formateado."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def test_health_check():
    """Prueba que la API esté funcionando."""
    print_info("Probando Health Check...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        
        if response.status_code == 200:
            print_success("API está funcionando")
            print_json(response.json())
            return True
        else:
            print_error(f"API respondió con código {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print_error("No se pudo conectar a la API. ¿Está corriendo en http://localhost:8000?")
        return False


def test_register_user():
    """Prueba el registro de usuario."""
    print_info("Probando registro de usuario...")
    
    # Generar email único para evitar conflictos
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    user_data = {
        "nombre": "Usuario de Prueba",
        "email": f"prueba_{timestamp}@ejemplo.cl",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    
    if response.status_code == 201:
        print_success("Usuario registrado exitosamente")
        user = response.json()
        print_json(user)
        return user
    else:
        print_error("Error al registrar usuario")
        print_json(response.json())
        return None


def test_login(email, password):
    """Prueba el login de usuario."""
    print_info("Probando login...")
    
    credentials = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=credentials)
    
    if response.status_code == 200:
        print_success("Login exitoso")
        data = response.json()
        print_info(f"Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print_error("Error en login")
        print_json(response.json())
        return None


def test_get_profile(token):
    """Prueba obtener perfil del usuario."""
    print_info("Probando obtener perfil...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        print_success("Perfil obtenido")
        print_json(response.json())
        return True
    else:
        print_error("Error al obtener perfil")
        return False


def test_create_product(token):
    """Prueba crear un producto."""
    print_info("Probando crear producto...")
    
    product_data = {
        "nombre": "Producto de Prueba",
        "sku": f"PROD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "stock_actual": 100,
        "stock_minimo": 20
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/products", json=product_data, headers=headers)
    
    if response.status_code == 201:
        print_success("Producto creado")
        product = response.json()
        print_json(product)
        return product
    else:
        print_error("Error al crear producto")
        print_json(response.json())
        return None


def test_list_products(token):
    """Prueba listar productos."""
    print_info("Probando listar productos...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/products", headers=headers)
    
    if response.status_code == 200:
        print_success("Productos listados")
        data = response.json()
        print_info(f"Total de productos: {data['total']}")
        print_json(data)
        return True
    else:
        print_error("Error al listar productos")
        return False


def test_update_stock(token, product_id):
    """Prueba actualizar el stock de un producto."""
    print_info(f"Probando actualizar stock del producto {product_id}...")
    
    stock_data = {
        "stock_actual": 150
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{BASE_URL}/products/{product_id}/stock",
        json=stock_data,
        headers=headers
    )
    
    if response.status_code == 200:
        print_success("Stock actualizado")
        print_json(response.json())
        return True
    else:
        print_error("Error al actualizar stock")
        return False


def test_create_sale(token, product_id):
    """Prueba registrar una venta."""
    print_info(f"Probando registrar venta del producto {product_id}...")
    
    sale_data = {
        "producto_id": product_id,
        "cantidad": 145  # Esto dejará el stock en 5, bajo el mínimo de 20
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/sales", json=sale_data, headers=headers)
    
    if response.status_code == 201:
        print_success("Venta registrada")
        data = response.json()
        
        if data['alerta_enviada']:
            print_warning("Se envió alerta de stock bajo")
        
        print_json(data)
        return data['venta']
    else:
        print_error("Error al registrar venta")
        print_json(response.json())
        return None


def test_list_sales(token):
    """Prueba listar ventas."""
    print_info("Probando listar ventas...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/sales", headers=headers)
    
    if response.status_code == 200:
        print_success("Ventas listadas")
        data = response.json()
        print_info(f"Total de ventas: {data['total']}")
        print_json(data)
        return True
    else:
        print_error("Error al listar ventas")
        return False


def test_sales_stats(token):
    """Prueba obtener estadísticas de ventas."""
    print_info("Probando obtener estadísticas...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/sales/stats/summary", headers=headers)
    
    if response.status_code == 200:
        print_success("Estadísticas obtenidas")
        print_json(response.json())
        return True
    else:
        print_error("Error al obtener estadísticas")
        return False


def main():
    """Función principal que ejecuta todas las pruebas."""
    print("\n" + "="*60)
    print("🧪 PRUEBA COMPLETA DE LA API DE INVENTARIO")
    print("="*60 + "\n")
    
    # 1. Health Check
    if not test_health_check():
        print_error("La API no está disponible. Abortando pruebas.")
        return
    
    print("\n" + "-"*60 + "\n")
    
    # 2. Registro
    user = test_register_user()
    if not user:
        print_error("No se pudo registrar usuario. Abortando pruebas.")
        return
    
    print("\n" + "-"*60 + "\n")
    
    # 3. Login
    token = test_login(user['email'], "password123")
    if not token:
        print_error("No se pudo hacer login. Abortando pruebas.")
        return
    
    print("\n" + "-"*60 + "\n")
    
    # 4. Obtener Perfil
    test_get_profile(token)
    
    print("\n" + "-"*60 + "\n")
    
    # 5. Crear Producto
    product = test_create_product(token)
    if not product:
        print_error("No se pudo crear producto. Abortando pruebas.")
        return
    
    print("\n" + "-"*60 + "\n")
    
    # 6. Listar Productos
    test_list_products(token)
    
    print("\n" + "-"*60 + "\n")
    
    # 7. Actualizar Stock
    test_update_stock(token, product['id'])
    
    print("\n" + "-"*60 + "\n")
    
    # 8. Registrar Venta
    sale = test_create_sale(token, product['id'])
    
    print("\n" + "-"*60 + "\n")
    
    # 9. Listar Ventas
    test_list_sales(token)
    
    print("\n" + "-"*60 + "\n")
    
    # 10. Estadísticas
    test_sales_stats(token)
    
    print("\n" + "="*60)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS")
    print("="*60 + "\n")
    
    print_info("Datos de prueba creados:")
    print(f"  • Email: {user['email']}")
    print(f"  • API Key: {user['api_key']}")
    print(f"  • Producto ID: {product['id']}")
    print(f"  • SKU: {product['sku']}")


if __name__ == "__main__":
    main()
