#!/usr/bin/env python3
"""
Ejemplo de uso de la funcionalidad de análisis de PDFs.

Este script demuestra cómo analizar PDFs de tarifas para extraer
su contenido de texto, tanto PDFs normales como PDFs escaneados usando OCR.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.servicios_sanitarios.src import ServiciosSanitarios


def main():
    """Función principal del ejemplo."""
    print("=" * 70)
    print("Concierge - Análisis de PDFs de Tarifas")
    print("=" * 70)
    print()
    
    # Crear instancia del módulo
    print("1. Creando módulo de servicios sanitarios...")
    servicio = ServiciosSanitarios(nombre="Analizador PDFs")
    print(f"   ✓ Módulo creado: {servicio.nombre}")
    print()
    
    # Analizar PDFs
    print("2. Analizando PDFs de tarifas...")
    print("   • Monitoreando carpeta de PDFs...")
    print("   • Detectando PDFs nuevos...")
    print("   • Extrayendo texto...")
    print()
    
    resultado = servicio.analizar_pdfs(
        ruta_pdfs="data/pdfs",
        ruta_registro="data/registro_analisis.json",
        usar_ocr=False,  # Cambiar a True para usar OCR en PDFs escaneados
        extraer_tablas=True,  # True para detectar tablas y bordes
        solo_nuevos=True
    )
    
    if resultado["exito"]:
        print("   ✓ Análisis completado!")
        print(f"   • Total de PDFs encontrados: {resultado['total_pdfs']}")
        print(f"   • PDFs analizados: {resultado['analizados']}")
        print(f"   • PDFs fallidos: {resultado['fallidos']}")
        print(f"   • Primera vez: {'Sí' if resultado['es_primera_vez'] else 'No'}")
        print(f"   • Usado OCR: {'Sí' if resultado['usado_ocr'] else 'No'}")
        print(f"   • Extracción de tablas: {'Sí' if resultado['extraer_tablas'] else 'No'}")
        print(f"   • Directorio PDFs: {resultado['ruta_pdfs']}")
        print(f"   • Registro: {resultado['ruta_registro']}")
        print(f"   • Timestamp: {resultado['timestamp']}")
        print(f"   • Estado: {resultado['mensaje']}")
        print()
        
        # Mostrar resumen de estructura jerárquica
        if 'estructura_jerarquica' in resultado:
            resumen = resultado['estructura_jerarquica']['resumen']
            print(f"   Estructura Jerárquica:")
            print(f"   • Total empresas: {resumen['total_empresas']}")
            print(f"   • Total localidades: {resumen['total_localidades']}")
            print(f"   • Total PDFs: {resumen['total_pdfs']}")
            print()
            
            # Mostrar primeras empresas
            empresas = resultado['estructura_jerarquica']['empresas']
            print(f"   Empresas organizadas:")
            for i, (empresa_key, empresa_data) in enumerate(list(empresas.items())[:3], 1):
                print(f"   {i}. {empresa_data['nombre_empresa']} ({empresa_data['total_pdfs']} PDFs)")
                
                # Mostrar primeras localidades
                for j, (loc_key, loc_data) in enumerate(list(empresa_data['localidades'].items())[:3], 1):
                    num_pdfs = len(loc_data['pdfs'])
                    print(f"      {j}. {loc_data['nombre_localidad']} - {num_pdfs} PDF(s)")
                    
                    # Mostrar info del primer PDF
                    if loc_data['pdfs']:
                        pdf_info = loc_data['pdfs'][0]['analisis']
                        print(f"         • Páginas: {pdf_info.get('total_paginas', 0)}, "
                              f"Tablas: {pdf_info.get('total_tablas', 0)}, "
                              f"Conceptos: {pdf_info.get('total_conceptos', 0)}")
                
                if len(empresa_data['localidades']) > 3:
                    print(f"      ... y {len(empresa_data['localidades']) - 3} localidades más")
            
            if len(empresas) > 3:
                print(f"   ... y {len(empresas) - 3} empresas más")
            print()
        
        if resultado['analizados'] > 0:
            print("   PDFs analizados exitosamente:")
            for i, pdf in enumerate(resultado['pdfs_analizados'][:3], 1):
                print(f"   {i}. {pdf['carpeta']}/{pdf['nombre_archivo']}")
                print(f"      Tamaño: {pdf['tamanio_kb']} KB")
                print(f"      Método: {pdf.get('metodo_extraccion', 'N/A')}")
                if 'total_tablas' in pdf:
                    print(f"      Páginas: {pdf['total_paginas']}, Tablas: {pdf['total_tablas']}")
                    if 'total_conceptos' in pdf:
                        print(f"      Conceptos extraídos: {pdf['total_conceptos']}, Secciones: {pdf['total_secciones']}")
                print(f"      Texto extraído: {pdf['longitud_texto']} caracteres")
                print(f"      Preview: {pdf['texto_extraido'][:100]}...")
                
                # Mostrar preview de tablas si existen
                if 'tablas' in pdf and pdf['tablas']:
                    print(f"      Tablas encontradas:")
                    for tabla in pdf['tablas'][:2]:  # Mostrar hasta 2 tablas
                        print(f"        - Página {tabla['pagina']}, Tabla {tabla['tabla_numero']}: {tabla['num_filas']} filas")
                        print(f"          Tipo: {tabla['tipo_estructura']}, Conceptos: {tabla['total_conceptos']}, Secciones: {tabla['total_secciones']}")
                        
                        # Mostrar secciones si existen
                        if 'secciones' in tabla and tabla['secciones']:
                            print(f"          Secciones detectadas:")
                            for sec in tabla['secciones'][:2]:
                                print(f"            • {sec['nombre']}: {sec['num_datos']} conceptos")
                                if sec['conceptos']:
                                    print(f"              Ejemplos: {', '.join(sec['conceptos'][:3])}")
                        
                        # Mostrar datos directos si existen
                        if 'datos_directos' in tabla and tabla['datos_directos']:
                            print(f"          Datos directos:")
                            for dato in tabla['datos_directos'][:2]:
                                print(f"            • {dato['concepto']}: {dato['valor']}")
                print()
            
            if len(resultado['pdfs_analizados']) > 3:
                print(f"   ... y {len(resultado['pdfs_analizados']) - 3} más")
        
        if resultado['fallidos'] > 0:
            print()
            print("   ⚠ PDFs que fallaron:")
            for i, pdf in enumerate(resultado['pdfs_fallidos'], 1):
                print(f"   {i}. {pdf['nombre_archivo']}")
                print(f"      Error: {pdf['error']}")
    else:
        print("   ✗ Error en el análisis")
        print(f"   • Error: {resultado.get('error', 'Desconocido')}")
    
    print()
    print("=" * 70)
    print("Demo completada")
    print("=" * 70)
    print()
    print("Notas importantes:")
    print()
    print("  • El análisis extrae texto de PDFs para su procesamiento")
    print("  • DETECTA TABLAS Y BORDES usando pdfplumber")
    print("  • Mantiene la estructura tabular preservando filas y columnas")
    print("  • PARSEA LA ESTRUCTURA DE LAS TABLAS identificando:")
    print("    1. Nombres de secciones (encabezados)")
    print("    2. Pares concepto-valor (nombre del concepto + precio/valor)")
    print("  • ORGANIZA JERÁRQUICAMENTE por empresa > localidad > análisis")
    print("  • Todos los análisis se guardan en un único JSON estructurado")
    print("  • Por defecto, solo analiza PDFs NUEVOS (no analizados antes)")
    print()
    print("  Estructura del JSON resultante:")
    print("  {")
    print("    \"estructura_jerarquica\": {")
    print("      \"empresas\": {")
    print("        \"Aguas_Andinas\": {")
    print("          \"localidades\": {")
    print("            \"Santiago\": {")
    print("              \"pdfs\": [{\"analisis\": {...}}]")
    print("            }")
    print("          }")
    print("        }")
    print("      }")
    print("    }")
    print("  }")
    print()
    print("  Estructura de datos extraídos:")
    print("  - Secciones: agrupan conceptos relacionados bajo un encabezado")
    print("  - Conceptos: pares de nombre-valor (ej: 'Cargo fijo' -> '$1,500')")
    print("  - Valores: pueden ser precios, cantidades, porcentajes, etc.")
    print()
    print("  Modos de extracción:")
    print("  - extraer_tablas=True (por defecto): usa pdfplumber para detectar tablas")
    print("  - extraer_tablas=False: usa pypdf para extracción simple de texto")
    print("  - usar_ocr=True: usa OCR para PDFs escaneados (requiere tesseract)")
    print()
    print("  Requisitos:")
    print("  - pip install pdfplumber (para detección de tablas)")
    print("  - pip install pypdf (alternativa simple)")
    print()
    print("  Requisitos para OCR (opcional):")
    print("  - pip install pytesseract pdf2image Pillow")
    print("  - Instalar tesseract-ocr en el sistema:")
    print("    * Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-spa")
    print("    * macOS: brew install tesseract tesseract-lang")
    print("    * Windows: descargar desde https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("  Uso recomendado:")
    print("  1. extraer_tablas=True, usar_ocr=False (por defecto, mejor para PDFs con tablas)")
    print("  2. Si falla, probar con usar_ocr=True para PDFs escaneados")
    print()


if __name__ == "__main__":
    main()
