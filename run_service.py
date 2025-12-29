#!/usr/bin/env python3
"""
Script to run the Concierge service transiently.

This script executes the complete service workflow:
1. Verifies SISS URL and extracts the current tariffs URL
2. Monitors current tariffs for all water companies
3. Downloads tariff PDFs (only new ones)
4. Analyzes downloaded PDFs (only new ones)

The script runs once and exits when all tasks are completed.
It does not remain as a daemon or background process.
"""

import sys
import os
from pathlib import Path

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from modules.servicios_sanitarios.src import ServiciosSanitarios


def print_header(titulo: str) -> None:
    """Print a formatted header."""
    print()
    print("=" * 80)
    print(f"  {titulo}")
    print("=" * 80)
    print()


def print_section(numero: int, titulo: str) -> None:
    """Print a section header."""
    print()
    print(f"{numero}. {titulo}")
    print("-" * 80)


def print_success(mensaje: str, indent: int = 3) -> None:
    """Print a success message."""
    print(" " * indent + f"✓ {mensaje}")


def print_info(mensaje: str, indent: int = 3) -> None:
    """Print an informational message."""
    print(" " * indent + f"• {mensaje}")


def print_warning(mensaje: str, indent: int = 3) -> None:
    """Print a warning message."""
    print(" " * indent + f"⚠ {mensaje}")


def print_error(mensaje: str, indent: int = 3) -> None:
    """Print an error message."""
    print(" " * indent + f"✗ {mensaje}")


def create_directories() -> None:
    """Create necessary directories for the service."""
    directories = [
        "data",
        "data/pdfs",
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def main():
    """Main function of the script."""
    print_header("CONCIERGE - Servicio de Monitoreo de Tarifas Sanitarias")
    
    print("Iniciando servicio...")
    print_info("Este script ejecutará el flujo completo y terminará al finalizar", 0)
    print_info("No quedará como daemon ni proceso en background", 0)
    
    # Crear directorios necesarios
    crear_directorios()
    
    # Crear instancia del servicio
    print_section(1, "Inicializando Módulo")
    servicio = ServiciosSanitarios(nombre="Concierge Runner")
    print_success(f"Módulo creado: {servicio.nombre}")
    print_info(f"ID: {servicio.id}")
    
    # ============================================================================
    # PASO 1: Verificar SISS
    # ============================================================================
    print_section(2, "Verificando URL de SISS")
    print_info("Accediendo a https://www.siss.gob.cl...")
    print_info("Detectando redirecciones...")
    print_info("Extrayendo URL de 'Tarifas vigentes'...")
    
    resultado_siss = servicio.verificar_siss(ruta_salida="data/siss_url.json")
    
    if not resultado_siss.get("success"):
        print_error("No se pudo verificar SISS")
        print_error(f"Error: {resultado_siss.get('error', 'Desconocido')}")
        print()
        print("Abortando ejecución...")
        return 1
    
    print_success("Verificación exitosa")
    print_info(f"URL Original: {resultado_siss['url_original']}")
    print_info(f"URL Final: {resultado_siss['url_final']}")
    print_info(f"URL Tarifas Vigentes: {resultado_siss['url_tarifas_vigentes']}")
    print_info(f"Timestamp: {resultado_siss['timestamp']}")
    
    if resultado_siss['guardado']:
        if resultado_siss['is_first_time']:
            print_info("Primera verificación - Datos guardados")
        elif resultado_siss['cambios']['url_final'] or resultado_siss['cambios']['url_tarifas_vigentes']:
            print_warning("Cambios detectados - Datos guardados")
    else:
        print_info("Sin cambios - No se guardó")
    
    # ============================================================================
    # PASO 2: Monitorear Tarifas Vigentes
    # ============================================================================
    print_section(3, "Monitoreando Tarifas Vigentes")
    print_info("Accediendo a página de tarifas vigentes...")
    print_info("Extrayendo datos de empresas de agua...")
    print_info("Procesando tablas de localidades y PDFs...")
    
    resultado_tarifas = servicio.monitorear_tarifas_vigentes(
        ruta_salida="data/tarifas_empresas.json"
    )
    
    if not resultado_tarifas.get("success"):
        print_error("No se pudo monitorear tarifas")
        print_error(f"Error: {resultado_tarifas.get('error', 'Desconocido')}")
        print()
        print("Abortando ejecución...")
        return 1
    
    print_success("Monitoreo exitoso")
    print_info(f"Total de empresas: {resultado_tarifas['total_companies']}")
    print_info(f"Timestamp: {resultado_tarifas['timestamp']}")
    
    if resultado_tarifas['guardado']:
        if resultado_tarifas['is_first_time']:
            print_info("Primera verificación - Datos guardados")
        elif resultado_tarifas['cambios_detectados']:
            print_warning("Cambios detectados - Datos guardados")
    else:
        print_info("Sin cambios - No se guardó")
    
    # Mostrar algunas empresas
    if resultado_tarifas['empresas']:
        print()
        print_info("Primeras empresas detectadas:")
        for i, empresa in enumerate(resultado_tarifas['empresas'][:5], 1):
            num_tarifas = len(empresa.get('tarifas', []))
            print(f"      {i}. {empresa['empresa']} ({num_tarifas} localidades)")
    
    # ============================================================================
    # PASO 3: Descargar PDFs
    # ============================================================================
    print_section(4, "Descargando PDFs de Tarifas")
    print_info("Leyendo archivo JSON con URLs...")
    print_info("Verificando PDFs ya descargados...")
    print_info("Descargando PDFs nuevos...")
    
    resultado_descarga = servicio.descargar_pdfs(
        ruta_json="data/tarifas_empresas.json",
        pdfs_path="data/pdfs",
        registry_path="data/registro_descargas.json"
    )
    
    if not resultado_descarga.get("success"):
        print_error("No se pudo descargar PDFs")
        print_error(f"Error: {resultado_descarga.get('error', 'Desconocido')}")
        print()
        print("Continuando con el siguiente paso...")
    else:
        print_success("Descarga completada")
        print_info(f"Total de PDFs en JSON: {resultado_descarga['total_pdfs']}")
        print_info(f"PDFs descargados: {resultado_descarga['descargados']}")
        print_info(f"PDFs fallidos: {resultado_descarga['failed']}")
        print_info(f"Primera vez: {'Sí' if resultado_descarga['is_first_time'] else 'No'}")
        print_info(f"Timestamp: {resultado_descarga['timestamp']}")
        
        if resultado_descarga['descargados'] > 0:
            print()
            print_info("Algunos PDFs descargados:")
            for i, pdf in enumerate(resultado_descarga['pdfs_descargados'][:5], 1):
                print(f"      {i}. {pdf['empresa']} - {pdf['localidad']}")
        elif resultado_descarga['is_first_time']:
            print_warning("Primera vez pero no se descargaron PDFs")
        else:
            print_info("No hay PDFs nuevos para descargar")
        
        if resultado_descarga['failed'] > 0:
            print()
            print_warning(f"{resultado_descarga['failed']} PDFs fallaron en la descarga")
    
    # ============================================================================
    # PASO 4: Analizar PDFs
    # ============================================================================
    print_section(5, "Analizando PDFs de Tarifas")
    print_info("Monitoreando carpeta de PDFs...")
    print_info("Detectando PDFs nuevos...")
    print_info("Extrayendo texto y tablas...")
    print_info("Identificando estructura de tarifas...")
    
    resultado_analisis = servicio.analyze_pdfs(
        pdfs_path="data/pdfs",
        registry_path="data/registro_analisis.json",
        use_ocr=False,
        extract_tables=True,
        only_new=True
    )
    
    if not resultado_analisis.get("success"):
        print_error("No se pudo analizar PDFs")
        print_error(f"Error: {resultado_analisis.get('error', 'Desconocido')}")
    else:
        print_success("Análisis completado")
        print_info(f"Total de PDFs encontrados: {resultado_analisis['total_pdfs']}")
        print_info(f"PDFs analizados: {resultado_analisis['analyzed']}")
        print_info(f"PDFs fallidos: {resultado_analisis['failed']}")
        print_info(f"Primera vez: {'Sí' if resultado_analisis['is_first_time'] else 'No'}")
        print_info(f"Extracción de tablas: {'Sí' if resultado_analisis['extract_tables'] else 'No'}")
        print_info(f"Timestamp: {resultado_analisis['timestamp']}")
        
        if resultado_analisis['analyzed'] > 0:
            print()
            print_info("Algunos PDFs analizados:")
            for i, pdf in enumerate(resultado_analisis['analyzed_pdfs'][:5], 1):
                print(f"      {i}. {pdf['folder']}/{pdf['filename']}")
                if 'total_tablas' in pdf:
                    print(f"         Páginas: {pdf.get('total_paginas', 0)}, "
                          f"Tablas: {pdf.get('total_tablas', 0)}, "
                          f"Conceptos: {pdf.get('total_concepts', 0)}")
                else:
                    print(f"         Texto extraído: {pdf.get('longitud_texto', 0)} caracteres")
        elif resultado_analisis['is_first_time']:
            print_warning("Primera vez pero no hay PDFs para analizar")
        else:
            print_info("No hay PDFs nuevos para analizar")
        
        if resultado_analisis['failed'] > 0:
            print()
            print_warning(f"{resultado_analisis['failed']} PDFs fallaron en el análisis")
        
        # Mostrar estructura jerárquica si está disponible
        if 'hierarchical_structure' in resultado_analisis:
            estructura = resultado_analisis['hierarchical_structure']
            resumen = estructura.get('resumen', {})
            print()
            print_info("Estructura Jerárquica:")
            print(f"         Total empresas: {resumen.get('total_empresas', 0)}")
            print(f"         Total localidades: {resumen.get('total_localidades', 0)}")
            print(f"         Total PDFs: {resumen.get('total_pdfs', 0)}")
    
    # ============================================================================
    # RESUMEN FINAL
    # ============================================================================
    print_section(6, "Resumen de Ejecución")
    
    print_info("Verificación SISS:", 0)
    if resultado_siss.get("success"):
        print_success(f"Exitosa - {resultado_siss['message']}")
    else:
        print_error("Fallida")
    
    print()
    print_info("Monitoreo Tarifas:", 0)
    if resultado_tarifas.get("success"):
        print_success(f"Exitoso - {resultado_tarifas['total_companies']} empresas")
    else:
        print_error("Fallido")
    
    print()
    print_info("Descarga PDFs:", 0)
    if resultado_descarga.get("success"):
        print_success(f"Exitosa - {resultado_descarga['descargados']} descargados")
    else:
        print_error("Fallida")
    
    print()
    print_info("Análisis PDFs:", 0)
    if resultado_analisis.get("success"):
        print_success(f"Exitoso - {resultado_analisis['analyzed']} analizados")
    else:
        print_error("Fallido")
    
    print_header("SERVICIO FINALIZADO")
    print_info("El servicio completó su ejecución y terminó correctamente", 0)
    print_info("No quedan procesos en background", 0)
    print()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 80)
        print("  EJECUCIÓN INTERRUMPIDA POR USUARIO")
        print("=" * 80)
        print()
        sys.exit(130)
    except Exception as e:
        print()
        print()
        print("=" * 80)
        print("  ERROR INESPERADO")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        sys.exit(1)
