#!/usr/bin/env python3
"""
Ejemplo de uso de la funcionalidad de verificación SISS.

This script demonstrates how to verify the SISS redirection URL
and save it to a JSON file.
"""

import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.servicios_sanitarios.src import ServiciosSanitarios
from modules.servicios_sanitarios.src.utils import cargar_json


def main():
    """Main function of the example."""
    print("=" * 70)
    print("Concierge - Verificación SISS")
    print("=" * 70)
    print()
    
    # Create module instance
    print("1. Creando módulo de servicios sanitarios...")
    servicio = ServiciosSanitarios(nombre="Verificador SISS")
    print(f"   ✓ Módulo creado: {servicio.nombre}")
    print()
    
    # Verify SISS
    print("2. Verificando URL de SISS...")
    print("   URL a verificar: https://www.siss.gob.cl")
    print("   • Detectando redirección...")
    print("   • Extrayendo URL de 'Tarifas vigentes'...")
    print()
    
    resultado = servicio.verificar_siss(ruta_salida="data/siss_url.json")
    
    if resultado["exito"]:
        print("   ✓ Verificación exitosa!")
        print(f"   • URL Original: {resultado['url_original']}")
        print(f"   • URL Final: {resultado['url_final']}")
        print(f"   • URL Tarifas Vigentes: {resultado['url_tarifas_vigentes']}")
        print(f"   • Timestamp: {resultado['timestamp']}")
        print(f"   • Archivo: {resultado['archivo']}")
        print(f"   • Estado: {resultado['mensaje']}")
        if resultado['guardado']:
            print("   • ✓ Datos guardados exitosamente")
            if resultado['es_primera_vez']:
                print("   • Esta es la primera verificación")
            else:
                if resultado['cambios']['url_final']:
                    print("   • ⚠ La URL final cambió")
                if resultado['cambios']['url_tarifas_vigentes']:
                    print("   • ⚠ La URL de Tarifas vigentes cambió")
        else:
            print("   • ℹ No se guardaron cambios (URLs sin modificar)")
    else:
        print("   ✗ Error en la verificación")
        print(f"   • Error: {resultado.get('error', 'Desconocido')}")
    print()
    
    # Read the saved JSON file
    if resultado["exito"] and resultado["guardado"]:
        print("3. Leyendo datos guardados del archivo JSON...")
        datos = cargar_json("data/siss_url.json")
        if datos:
            print("   ✓ Archivo cargado correctamente:")
            print(f"   • URL Original: {datos['url_original']}")
            print(f"   • URL Final: {datos['url_final']}")
            print(f"   • URL Tarifas Vigentes: {datos['url_tarifas_vigentes']}")
            print(f"   • Timestamp: {datos['timestamp']}")
            print(f"   • Verificado: {datos['verificado']}")
            if 'historial' in datos and datos['historial']:
                print(f"   • Historial de cambios: {len(datos['historial'])} entrada(s)")
        else:
            print("   ✗ No se pudo leer el archivo")
        print()
    
    print("=" * 70)
    print("Demo completada")
    print("=" * 70)
    print()
    print("Nota: Ejecuta este script múltiples veces para ver cómo")
    print("      solo guarda cuando hay cambios en las URLs.")


if __name__ == "__main__":
    main()
