#!/usr/bin/env python
"""
Script para iniciar el servidor de desarrollo.

Uso:
    python start_server.py
"""

import os
import sys
import subprocess

def check_env_file():
    """Verifica que exista el archivo .env"""
    if not os.path.exists('.env'):
        print("❌ Error: No se encontró el archivo .env")
        print("📝 Copia .env.example a .env y configura tus variables:")
        print("   cp .env.example .env")
        return False
    return True


def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        return True
    except ImportError:
        print("❌ Error: Faltan dependencias")
        print("📦 Instala las dependencias con:")
        print("   pip install -r requirements.txt")
        return False


def start_server():
    """Inicia el servidor de desarrollo"""
    print("🚀 Iniciando servidor de desarrollo...")
    print("📖 Documentación: http://localhost:8000/docs")
    print("🔄 Auto-reload activado")
    print("\n" + "="*60 + "\n")
    
    try:
        subprocess.run([
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido")


def main():
    """Función principal"""
    print("\n" + "="*60)
    print("🏪 API de Inventario para PYME - Servidor de Desarrollo")
    print("="*60 + "\n")
    
    # Verificar requisitos
    if not check_env_file():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Iniciar servidor
    start_server()


if __name__ == "__main__":
    main()
