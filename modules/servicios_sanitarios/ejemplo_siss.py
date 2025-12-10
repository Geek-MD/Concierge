#!/usr/bin/env python3
"""
Ejemplo de uso de la funcionalidad de verificación SISS.

Este script demuestra cómo verificar la URL de redirección de SISS
y guardarla en un archivo JSON.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.servicios_sanitarios.src import ServiciosSanitarios
from modules.servicios_sanitarios.src.utils import cargar_json


def main():
    """Función principal del ejemplo."""
    print("=" * 60)
    print("Concierge - Verificación SISS")
    print("=" * 60)
    print()
    
    # Crear instancia del módulo
    print("1. Creando módulo de servicios sanitarios...")
    servicio = ServiciosSanitarios(nombre="Verificador SISS")
    print(f"   ✓ Módulo creado: {servicio.nombre}")
    print()
    
    # Verificar SISS
    print("2. Verificando URL de SISS...")
    print("   URL a verificar: https://www.siss.gob.cl")
    print("   Detectando redirección...")
    print()
    
    resultado = servicio.verificar_siss(ruta_salida="data/siss_url.json")
    
    if resultado["exito"]:
        print("   ✓ Verificación exitosa!")
        print(f"   • URL Original: {resultado['url_original']}")
        print(f"   • URL Final: {resultado['url_final']}")
        print(f"   • Timestamp: {resultado['timestamp']}")
        print(f"   • Archivo guardado: {resultado['archivo']}")
        print(f"   • Estado de guardado: {'✓ Exitoso' if resultado['guardado'] else '✗ Falló'}")
    else:
        print("   ✗ Error en la verificación")
        print(f"   • Error: {resultado.get('error', 'Desconocido')}")
    print()
    
    # Leer el archivo JSON guardado
    if resultado["exito"] and resultado["guardado"]:
        print("3. Leyendo datos guardados del archivo JSON...")
        datos = cargar_json("data/siss_url.json")
        if datos:
            print("   ✓ Archivo cargado correctamente:")
            print(f"   • URL Original: {datos['url_original']}")
            print(f"   • URL Final: {datos['url_final']}")
            print(f"   • Timestamp: {datos['timestamp']}")
            print(f"   • Verificado: {datos['verificado']}")
        else:
            print("   ✗ No se pudo leer el archivo")
        print()
    
    print("=" * 60)
    print("Demo completada")
    print("=" * 60)


if __name__ == "__main__":
    main()
