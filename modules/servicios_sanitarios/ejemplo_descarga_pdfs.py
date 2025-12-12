#!/usr/bin/env python3
"""
Ejemplo de uso de la funcionalidad de descarga de PDFs.

Este script demuestra cómo descargar PDFs de tarifas desde las URLs
almacenadas en el archivo JSON.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.servicios_sanitarios.src import ServiciosSanitarios


def main():
    """Función principal del ejemplo."""
    print("=" * 70)
    print("Concierge - Descarga de PDFs de Tarifas")
    print("=" * 70)
    print()
    
    # Crear instancia del módulo
    print("1. Creando módulo de servicios sanitarios...")
    servicio = ServiciosSanitarios(nombre="Descargador PDFs")
    print(f"   ✓ Módulo creado: {servicio.nombre}")
    print()
    
    # Descargar PDFs
    print("2. Descargando PDFs de tarifas...")
    print("   • Leyendo archivo JSON con URLs...")
    print("   • Verificando PDFs ya descargados...")
    print("   • Descargando PDFs...")
    print()
    
    resultado = servicio.descargar_pdfs(
        ruta_json="data/tarifas_empresas.json",
        ruta_pdfs="data/pdfs",
        ruta_registro="data/registro_descargas.json"
    )
    
    if resultado["exito"]:
        print("   ✓ Descarga completada!")
        print(f"   • Total de PDFs en JSON: {resultado['total_pdfs']}")
        print(f"   • PDFs descargados: {resultado['descargados']}")
        print(f"   • PDFs fallidos: {resultado['fallidos']}")
        print(f"   • Primera vez: {'Sí' if resultado['es_primera_vez'] else 'No'}")
        print(f"   • Directorio PDFs: {resultado['ruta_pdfs']}")
        print(f"   • Registro: {resultado['ruta_registro']}")
        print(f"   • Timestamp: {resultado['timestamp']}")
        print(f"   • Estado: {resultado['mensaje']}")
        print()
        
        if resultado['descargados'] > 0:
            print("   PDFs descargados exitosamente:")
            for i, pdf in enumerate(resultado['pdfs_descargados'][:5], 1):
                print(f"   {i}. {pdf['empresa']} - {pdf['localidad']}")
                print(f"      URL: {pdf['url_pdf']}")
                print(f"      Archivo: {pdf['ruta_local']}")
            
            if len(resultado['pdfs_descargados']) > 5:
                print(f"   ... y {len(resultado['pdfs_descargados']) - 5} más")
        
        if resultado['fallidos'] > 0:
            print()
            print("   ⚠ PDFs que fallaron:")
            for i, pdf in enumerate(resultado['pdfs_fallidos'], 1):
                print(f"   {i}. {pdf['empresa']} - {pdf['localidad']}")
                print(f"      URL: {pdf['url_pdf']}")
                print(f"      Error: {pdf['error']}")
    else:
        print("   ✗ Error en la descarga")
        print(f"   • Error: {resultado.get('error', 'Desconocido')}")
    
    print()
    print("=" * 70)
    print("Demo completada")
    print("=" * 70)
    print()
    print("Nota: Los PDFs se organizan en carpetas por empresa:")
    print("      data/pdfs/Aguas_Andinas/Santiago.pdf")
    print("      data/pdfs/Aguas_Andinas/Maipú.pdf")
    print("      data/pdfs/Essbio/Concepción.pdf")
    print()
    print("      Si ejecutas este script múltiples veces:")
    print("      • Primera vez: descarga TODOS los PDFs")
    print("      • Siguientes veces: descarga solo PDFs NUEVOS")
    print()


if __name__ == "__main__":
    main()
