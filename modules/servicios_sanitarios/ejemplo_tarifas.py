#!/usr/bin/env python3
"""
Ejemplo de uso de la funcionalidad de monitoreo de tarifas vigentes.

Este script demuestra cómo monitorear la URL de tarifas vigentes,
extraer información de empresas de agua y guardarla en JSON.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.servicios_sanitarios.src import ServiciosSanitarios
from modules.servicios_sanitarios.src.utils import cargar_json


def main():
    """Función principal del ejemplo."""
    print("=" * 70)
    print("Concierge - Monitoreo de Tarifas Vigentes")
    print("=" * 70)
    print()
    
    # Crear instancia del módulo
    print("1. Creando módulo de servicios sanitarios...")
    servicio = ServiciosSanitarios(nombre="Monitor Tarifas")
    print(f"   ✓ Módulo creado: {servicio.nombre}")
    print()
    
    # Monitorear tarifas vigentes
    print("2. Monitoreando tarifas vigentes de empresas de agua...")
    print("   • Obteniendo URL de tarifas vigentes...")
    print("   • Extrayendo datos de empresas...")
    print("   • Procesando tablas de localidades y PDFs...")
    print()
    
    resultado = servicio.monitorear_tarifas_vigentes(
        ruta_salida="data/tarifas_empresas.json"
    )
    
    if resultado["exito"]:
        print("   ✓ Monitoreo exitoso!")
        print(f"   • URL Tarifas: {resultado['url_tarifas']}")
        print(f"   • Total de empresas: {resultado['total_empresas']}")
        print(f"   • Timestamp: {resultado['timestamp']}")
        print(f"   • Archivo: {resultado['archivo']}")
        print(f"   • Estado: {resultado['mensaje']}")
        
        if resultado['guardado']:
            print("   • ✓ Datos guardados exitosamente")
            if resultado['es_primera_vez']:
                print("   • Esta es la primera verificación")
            elif resultado['cambios_detectados']:
                print("   • ⚠ Se detectaron cambios en las tarifas")
        else:
            print("   • ℹ No se guardaron cambios (datos sin modificar)")
        
        print()
        print("   Empresas encontradas:")
        for i, empresa in enumerate(resultado['empresas'], 1):
            print(f"   {i}. {empresa['empresa']}")
            print(f"      • Localidades con tarifas: {len(empresa['tarifas'])}")
            if empresa['tarifas']:
                print(f"      • Ejemplos:")
                for j, tarifa in enumerate(empresa['tarifas'][:3], 1):
                    print(f"        {j}. {tarifa['localidad']}")
                    print(f"           PDF: {tarifa['url_pdf']}")
                if len(empresa['tarifas']) > 3:
                    print(f"        ... y {len(empresa['tarifas']) - 3} más")
    else:
        print("   ✗ Error en el monitoreo")
        print(f"   • Error: {resultado.get('error', 'Desconocido')}")
    print()
    
    # Leer el archivo JSON guardado
    if resultado["exito"] and resultado["guardado"]:
        print("3. Leyendo datos guardados del archivo JSON...")
        datos = cargar_json("data/tarifas_empresas.json")
        if datos:
            print("   ✓ Archivo cargado correctamente:")
            print(f"   • URL Tarifas: {datos['url_tarifas']}")
            print(f"   • Total de empresas: {datos['total_empresas']}")
            print(f"   • Timestamp: {datos['timestamp']}")
            print(f"   • Verificado: {datos['verificado']}")
            if 'historial' in datos and datos['historial']:
                print(f"   • Historial de cambios: {len(datos['historial'])} entrada(s)")
            
            print()
            print("   Detalle por empresa:")
            for empresa in datos['empresas']:
                print(f"   • {empresa['empresa']}: {len(empresa['tarifas'])} localidad(es)")
        else:
            print("   ✗ No se pudo leer el archivo")
        print()
    
    print("=" * 70)
    print("Demo completada")
    print("=" * 70)
    print()
    print("Nota: Ejecuta este script múltiples veces para ver cómo")
    print("      solo guarda cuando hay cambios en los datos de tarifas.")
    print()
    print("Los datos se guardan en formato JSON con la siguiente estructura:")
    print("  {")
    print("    'url_tarifas': '...',")
    print("    'empresas': [")
    print("      {")
    print("        'empresa': 'Nombre Empresa',")
    print("        'tarifas': [")
    print("          {")
    print("            'localidad': 'Nombre Localidad',")
    print("            'url_pdf': 'https://...'")
    print("          }")
    print("        ]")
    print("      }")
    print("    ],")
    print("    'total_empresas': N,")
    print("    'timestamp': '...',")
    print("    'verificado': true,")
    print("    'historial': [...]")
    print("  }")


if __name__ == "__main__":
    main()
