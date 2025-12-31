"""
Tests para la funcionalidad de análisis de PDFs.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import shutil
import json
import sys
import os

# Agregar directorio raíz al path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from modules.servicios_sanitarios.src import ServiciosSanitarios
from modules.servicios_sanitarios.src.utils import (
    extract_pdf_text,
    extract_pdf_text_with_ocr,
    extract_pdf_tables,
    parse_table_structure,
    organize_hierarchical_analysis,
    get_pdfs_in_folder,
    get_new_pdfs
)


class TestOrganizeHierarchicalAnalysis(unittest.TestCase):
    """Tests para la función organizar_analisis_jerarquico."""
    
    def test_organizar_vacio(self):
        """Test con lista vacía."""
        estructura = organize_hierarchical_analysis([])
        
        self.assertEqual(estructura['summary']['total_companies'], 0)
        self.assertEqual(estructura['summary']['total_localities'], 0)
        self.assertEqual(estructura['summary']['total_pdfs'], 0)
        self.assertEqual(len(estructura['companies']), 0)
    
    def test_organizar_una_empresa_una_localidad(self):
        """Test con una empresa y una localidad."""
        pdfs = [
            {
                "nombre_archivo": "Santiago.pdf",
                "carpeta": "Aguas_Andinas",
                "ruta_pdf": "/path/Aguas_Andinas/Santiago.pdf",
                "size_kb": 150.5,
                "total_pages": 5,
                "total_tables": 2
            }
        ]
        
        estructura = organize_hierarchical_analysis(pdfs)
        
        self.assertEqual(estructura['summary']['total_companies'], 1)
        self.assertEqual(estructura['summary']['total_localities'], 1)
        self.assertEqual(estructura['summary']['total_pdfs'], 1)
        
        # Verificar empresa
        self.assertIn('Aguas_Andinas', estructura['companies'])
        empresa = estructura['companies']['Aguas_Andinas']
        self.assertEqual(empresa['company_name'], 'Aguas Andinas')
        self.assertEqual(empresa['total_localities'], 1)
        self.assertEqual(empresa['total_pdfs'], 1)
        
        # Verificar localidad
        self.assertIn('Santiago', empresa['localities'])
        localidad = empresa['localities']['Santiago']
        self.assertEqual(localidad['locality_name'], 'Santiago')
        self.assertEqual(len(localidad['pdfs']), 1)
    
    def test_organizar_una_empresa_multiples_localidades(self):
        """Test con una empresa y múltiples localidades."""
        pdfs = [
            {
                "nombre_archivo": "Santiago.pdf",
                "carpeta": "Aguas_Andinas",
                "ruta_pdf": "/path/Aguas_Andinas/Santiago.pdf"
            },
            {
                "nombre_archivo": "Maipu.pdf",
                "carpeta": "Aguas_Andinas",
                "ruta_pdf": "/path/Aguas_Andinas/Maipu.pdf"
            },
            {
                "nombre_archivo": "Providencia.pdf",
                "carpeta": "Aguas_Andinas",
                "ruta_pdf": "/path/Aguas_Andinas/Providencia.pdf"
            }
        ]
        
        estructura = organize_hierarchical_analysis(pdfs)
        
        self.assertEqual(estructura['summary']['total_companies'], 1)
        self.assertEqual(estructura['summary']['total_localities'], 3)
        self.assertEqual(estructura['summary']['total_pdfs'], 3)
        
        empresa = estructura['companies']['Aguas_Andinas']
        self.assertEqual(empresa['total_localities'], 3)
        self.assertEqual(len(empresa['localities']), 3)
    
    def test_organizar_multiples_empresas(self):
        """Test con múltiples empresas."""
        pdfs = [
            {
                "nombre_archivo": "Santiago.pdf",
                "carpeta": "Aguas_Andinas"
            },
            {
                "nombre_archivo": "Concepcion.pdf",
                "carpeta": "Essbio"
            },
            {
                "nombre_archivo": "Valparaiso.pdf",
                "carpeta": "Esval"
            }
        ]
        
        estructura = organize_hierarchical_analysis(pdfs)
        
        self.assertEqual(estructura['summary']['total_companies'], 3)
        self.assertEqual(estructura['summary']['total_localities'], 3)
        self.assertEqual(estructura['summary']['total_pdfs'], 3)
        
        # Verificar que todas las empresas existen
        self.assertIn('Aguas_Andinas', estructura['companies'])
        self.assertIn('Essbio', estructura['companies'])
        self.assertIn('Esval', estructura['companies'])
    
    def test_organizar_multiple_pdfs_misma_localidad(self):
        """Test con múltiples PDFs para la misma localidad."""
        pdfs = [
            {
                "nombre_archivo": "Santiago.pdf",
                "carpeta": "Aguas_Andinas",
                "timestamp": "2024-01-01"
            },
            {
                "nombre_archivo": "Santiago.pdf",
                "carpeta": "Aguas_Andinas",
                "timestamp": "2024-01-02"
            }
        ]
        
        estructura = organize_hierarchical_analysis(pdfs)
        
        # Debe haber 2 PDFs en la misma localidad
        localidad = estructura['companies']['Aguas_Andinas']['localities']['Santiago']
        self.assertEqual(len(localidad['pdfs']), 2)
    
    def test_organizar_preserva_datos_analisis(self):
        """Test que verifica que se preservan los datos del análisis."""
        pdfs = [
            {
                "nombre_archivo": "Santiago.pdf",
                "carpeta": "Aguas_Andinas",
                "ruta_pdf": "/path/Santiago.pdf",
                "size_kb": 150.5,
                "total_pages": 5,
                "total_tables": 2,
                "total_concepts": 10,
                "extraction_method": "pdfplumber",
                "timestamp": "2024-01-01"
            }
        ]
        
        estructura = organize_hierarchical_analysis(pdfs)
        
        pdf_analisis = estructura['companies']['Aguas_Andinas']['localities']['Santiago']['pdfs'][0]['analisis']
        
        self.assertEqual(pdf_analisis['tamanio_kb'], 150.5)
        self.assertEqual(pdf_analisis['total_paginas'], 5)
        self.assertEqual(pdf_analisis['total_tablas'], 2)
        self.assertEqual(pdf_analisis['total_concepts'], 10)
        self.assertEqual(pdf_analisis['metodo_extraccion'], 'pdfplumber')


class TestParseTableStructure(unittest.TestCase):
    """Tests para la función parsear_estructura_tabla."""
    
    def test_tabla_vacia(self):
        """Test con tabla vacía."""
        estructura = parse_table_structure([])
        
        self.assertEqual(estructura['type'], 'empty')
        self.assertEqual(len(estructura['secciones']), 0)
        self.assertEqual(len(estructura['direct_data']), 0)
    
    def test_tabla_simple_sin_secciones(self):
        """Test con tabla simple de pares concepto-valor."""
        tabla = [
            ['Cargo fijo', '$1,500'],
            ['Consumo', '$850 por m3'],
            ['Alcantarillado', '$450']
        ]
        
        estructura = parse_table_structure(tabla)
        
        self.assertEqual(estructura['type'], 'simple')
        self.assertEqual(len(estructura['direct_data']), 3)
        self.assertEqual(estructura['total_concepts'], 3)
        
        # Verificar primer concepto
        self.assertEqual(estructura['direct_data'][0]['concept'], 'Cargo fijo')
        self.assertEqual(estructura['direct_data'][0]['value'], '$1,500')
    
    def test_tabla_con_secciones(self):
        """Test con tabla que tiene secciones."""
        tabla = [
            ['AGUA POTABLE'],
            ['Cargo fijo', '$1,500'],
            ['Consumo', '$850 por m3'],
            ['ALCANTARILLADO'],
            ['Cargo fijo', '$900'],
            ['Servicio', '$600']
        ]
        
        estructura = parse_table_structure(tabla)
        
        self.assertEqual(estructura['type'], 'con_secciones')
        self.assertEqual(len(estructura['secciones']), 2)
        
        # Verificar primera sección
        self.assertEqual(estructura['secciones'][0]['section_name'], 'AGUA POTABLE')
        self.assertEqual(len(estructura['secciones'][0]['datos']), 2)
        
        # Verificar segunda sección
        self.assertEqual(estructura['secciones'][1]['section_name'], 'ALCANTARILLADO')
        self.assertEqual(len(estructura['secciones'][1]['datos']), 2)
        
        self.assertEqual(estructura['total_concepts'], 4)
    
    def test_tabla_con_filas_vacias(self):
        """Test con tabla que tiene filas vacías."""
        tabla = [
            ['Concepto', 'Valor'],
            ['', ''],
            ['Cargo fijo', '$1,500'],
            [None, None],
            ['Consumo', '$850']
        ]
        
        estructura = parse_table_structure(tabla)
        
        # Solo debe contar las filas con datos
        self.assertEqual(estructura['total_concepts'], 2)
    
    def test_tabla_con_multiples_columnas(self):
        """Test con tabla de múltiples columnas."""
        tabla = [
            ['Concepto', 'Residencial', 'Comercial', 'Industrial'],
            ['Cargo fijo', '$1,500', '$2,000', '$3,500'],
            ['Consumo m3', '$850', '$950', '$1,200']
        ]
        
        estructura = parse_table_structure(tabla)
        
        # Primera fila puede ser encabezado
        self.assertGreater(len(estructura['direct_data']) + 
                          sum(len(s['datos']) for s in estructura['secciones']), 0)


class TestExtractPdfTables(unittest.TestCase):
    """Tests para la función extraer_tablas_pdf."""
    
    def setUp(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Limpieza después de cada test."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_archivo_inexistente(self):
        """Test cuando el archivo no existe."""
        ruta_pdf = Path(self.temp_dir) / "noexiste.pdf"
        resultado = extract_pdf_tables(str(ruta_pdf))
        
        self.assertIsNone(resultado)
    
    @patch('modules.servicios_sanitarios.src.utils.pdfplumber')
    def test_extraer_tablas_exitoso(self, mock_pdfplumber):
        """Test de extracción exitosa con tablas."""
        # Mock de página con tabla
        mock_tabla = [
            ['Cargo fijo', '$1,500'],
            ['Consumo', '$850']
        ]
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Texto de prueba"
        mock_page.extract_tables.return_value = [mock_tabla]
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        
        mock_pdfplumber.open.return_value = mock_pdf
        
        # Crear archivo de prueba
        ruta_pdf = Path(self.temp_dir) / "test.pdf"
        ruta_pdf.touch()
        
        resultado = extract_pdf_tables(str(ruta_pdf))
        
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado['total_paginas'], 1)
        self.assertEqual(resultado['total_tablas'], 1)
        self.assertIn('estructura', resultado['tablas'][0])


class TestExtractPdfText(unittest.TestCase):
    """Tests para la función extraer_texto_pdf."""
    
    def setUp(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Limpieza después de cada test."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('modules.servicios_sanitarios.src.utils.PdfReader')
    def test_extraer_texto_exitoso(self, mock_pdf_reader):
        """Test de extracción exitosa de texto."""
        # Mock de PdfReader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Contenido del PDF"
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        # Crear archivo de prueba
        ruta_pdf = Path(self.temp_dir) / "test.pdf"
        ruta_pdf.touch()
        
        texto = extract_pdf_text(str(ruta_pdf))
        
        self.assertIsNotNone(texto)
        self.assertEqual(texto, "Contenido del PDF")
    
    @patch('modules.servicios_sanitarios.src.utils.PdfReader')
    def test_extraer_texto_multiples_paginas(self, mock_pdf_reader):
        """Test de extracción con múltiples páginas."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Página 1"
        
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Página 2"
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader
        
        ruta_pdf = Path(self.temp_dir) / "test.pdf"
        ruta_pdf.touch()
        
        texto = extract_pdf_text(str(ruta_pdf))
        
        self.assertIsNotNone(texto)
        self.assertIn("Página 1", texto)
        self.assertIn("Página 2", texto)
    
    def test_extraer_texto_archivo_inexistente(self):
        """Test cuando el archivo no existe."""
        ruta_pdf = Path(self.temp_dir) / "noexiste.pdf"
        texto = extract_pdf_text(str(ruta_pdf))
        
        self.assertIsNone(texto)
    
    @patch('modules.servicios_sanitarios.src.utils.PdfReader')
    def test_extraer_texto_vacio(self, mock_pdf_reader):
        """Test cuando el PDF no tiene texto."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        ruta_pdf = Path(self.temp_dir) / "test.pdf"
        ruta_pdf.touch()
        
        texto = extract_pdf_text(str(ruta_pdf), use_ocr=False)
        
        self.assertIsNone(texto)


class TestExtractPdfTextConOcr(unittest.TestCase):
    """Tests para la función extraer_texto_pdf_con_ocr."""
    
    def setUp(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Limpieza después de cada test."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('modules.servicios_sanitarios.src.utils.pytesseract')
    @patch('modules.servicios_sanitarios.src.utils.convert_from_path')
    def test_extraer_texto_con_ocr_exitoso(self, mock_convert, mock_pytesseract):
        """Test de extracción con OCR exitosa."""
        # Mock de convert_from_path
        mock_imagen = MagicMock()
        mock_convert.return_value = [mock_imagen]
        
        # Mock de pytesseract
        mock_pytesseract.image_to_string.return_value = "Texto OCR"
        
        ruta_pdf = Path(self.temp_dir) / "test.pdf"
        ruta_pdf.touch()
        
        texto = extract_pdf_text_with_ocr(str(ruta_pdf))
        
        self.assertIsNotNone(texto)
        self.assertIn("Texto OCR", texto)
        self.assertIn("Página 1", texto)
    
    def test_extraer_texto_con_ocr_archivo_inexistente(self):
        """Test cuando el archivo no existe."""
        ruta_pdf = Path(self.temp_dir) / "noexiste.pdf"
        texto = extract_pdf_text_with_ocr(str(ruta_pdf))
        
        self.assertIsNone(texto)


class TestGetPdfsInFolder(unittest.TestCase):
    """Tests para la función obtener_pdfs_en_carpeta."""
    
    def setUp(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Limpieza después de cada test."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_obtener_pdfs_carpeta_vacia(self):
        """Test en carpeta vacía."""
        pdfs = get_pdfs_in_folder(self.temp_dir)
        
        self.assertEqual(len(pdfs), 0)
    
    def test_obtener_pdfs_con_archivos(self):
        """Test con archivos PDF."""
        # Crear PDFs de prueba
        (Path(self.temp_dir) / "test1.pdf").touch()
        (Path(self.temp_dir) / "test2.pdf").touch()
        (Path(self.temp_dir) / "otro.txt").touch()  # No PDF
        
        pdfs = get_pdfs_in_folder(self.temp_dir, recursive=False)
        
        self.assertEqual(len(pdfs), 2)
        self.assertTrue(all(pdf.endswith('.pdf') for pdf in pdfs))
    
    def test_obtener_pdfs_recursivo(self):
        """Test con búsqueda recursiva."""
        # Crear estructura de carpetas
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        
        (Path(self.temp_dir) / "test1.pdf").touch()
        (subdir / "test2.pdf").touch()
        
        pdfs = get_pdfs_in_folder(self.temp_dir, recursive=True)
        
        self.assertEqual(len(pdfs), 2)
    
    def test_obtener_pdfs_no_recursivo(self):
        """Test sin búsqueda recursiva."""
        # Crear estructura de carpetas
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        
        (Path(self.temp_dir) / "test1.pdf").touch()
        (subdir / "test2.pdf").touch()
        
        pdfs = get_pdfs_in_folder(self.temp_dir, recursive=False)
        
        self.assertEqual(len(pdfs), 1)
    
    def test_obtener_pdfs_carpeta_inexistente(self):
        """Test cuando la carpeta no existe."""
        pdfs = get_pdfs_in_folder(str(Path(self.temp_dir) / "noexiste"))
        
        self.assertEqual(len(pdfs), 0)


class TestGetNewPdfs(unittest.TestCase):
    """Tests para la función get_new_pdfs."""
    
    def setUp(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.ruta_registro = Path(self.temp_dir) / "registro.json"
    
    def tearDown(self):
        """Limpieza después de cada test."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_get_new_pdfs_sin_registro(self):
        """Test cuando no existe registro previo."""
        # Crear PDFs
        (Path(self.temp_dir) / "test1.pdf").touch()
        (Path(self.temp_dir) / "test2.pdf").touch()
        
        pdfs_nuevos = get_new_pdfs(
            self.temp_dir,
            str(self.ruta_registro)
        )
        
        # Todos son nuevos si no hay registro
        self.assertEqual(len(pdfs_nuevos), 2)
    
    def test_get_new_pdfs_con_registro(self):
        """Test cuando existe registro previo."""
        # Crear PDFs
        pdf1 = Path(self.temp_dir) / "test1.pdf"
        pdf2 = Path(self.temp_dir) / "test2.pdf"
        pdf1.touch()
        pdf2.touch()
        
        # Crear registro con pdf1 ya analizado
        registro = {
            "pdfs_analizados": [
                {"ruta_pdf": str(pdf1)}
            ]
        }
        
        with open(self.ruta_registro, 'w', encoding='utf-8') as f:
            json.dump(registro, f)
        
        pdfs_nuevos = get_new_pdfs(
            self.temp_dir,
            str(self.ruta_registro)
        )
        
        # Solo pdf2 es nuevo
        self.assertEqual(len(pdfs_nuevos), 1)
        self.assertTrue(str(pdf2) in pdfs_nuevos)
    
    def test_get_new_pdfs_todos_analizados(self):
        """Test cuando todos los PDFs ya fueron analizados."""
        # Crear PDFs
        pdf1 = Path(self.temp_dir) / "test1.pdf"
        pdf1.touch()
        
        # Crear registro con todos analizados
        registro = {
            "pdfs_analizados": [
                {"ruta_pdf": str(pdf1)}
            ]
        }
        
        with open(self.ruta_registro, 'w', encoding='utf-8') as f:
            json.dump(registro, f)
        
        pdfs_nuevos = get_new_pdfs(
            self.temp_dir,
            str(self.ruta_registro)
        )
        
        self.assertEqual(len(pdfs_nuevos), 0)


class TestAnalyzePdfs(unittest.TestCase):
    """Tests para el método analizar_pdfs."""
    
    def setUp(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.servicio = ServiciosSanitarios()
        
        self.ruta_pdfs = Path(self.temp_dir) / "pdfs"
        self.ruta_pdfs.mkdir()
        self.ruta_registro = Path(self.temp_dir) / "registro.json"
    
    def tearDown(self):
        """Limpieza después de cada test."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('modules.servicios_sanitarios.src.core.extraer_texto_pdf')
    def test_analizar_pdfs_primera_vez(self, mock_extraer):
        """Test de análisis primera vez."""
        # Crear PDFs de prueba
        (self.ruta_pdfs / "test1.pdf").touch()
        (self.ruta_pdfs / "test2.pdf").touch()
        
        # Mock de extracción
        mock_extraer.return_value = "Texto del PDF"
        
        resultado = self.servicio.analyze_pdfs(
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro),
            use_ocr=False,
            only_new=True
        )
        
        self.assertTrue(resultado['success'])
        self.assertTrue(resultado['is_first_time'])
        self.assertEqual(resultado['total_pdfs'], 2)
        self.assertEqual(resultado['analizados'], 2)
        self.assertEqual(resultado['failed'], 0)
    
    @patch('modules.servicios_sanitarios.src.core.extraer_texto_pdf')
    def test_analizar_pdfs_solo_nuevos(self, mock_extraer):
        """Test de análisis solo PDFs nuevos."""
        # Crear PDFs
        pdf1 = self.ruta_pdfs / "test1.pdf"
        pdf2 = self.ruta_pdfs / "test2.pdf"
        pdf1.touch()
        pdf2.touch()
        
        mock_extraer.return_value = "Texto del PDF"
        
        # Primera ejecución
        resultado1 = self.servicio.analyze_pdfs(
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertEqual(resultado1['analizados'], 2)
        
        # Agregar nuevo PDF
        pdf3 = self.ruta_pdfs / "test3.pdf"
        pdf3.touch()
        
        # Segunda ejecución - solo el nuevo
        resultado2 = self.servicio.analyze_pdfs(
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertTrue(resultado2['success'])
        self.assertFalse(resultado2['is_first_time'])
        self.assertEqual(resultado2['analizados'], 1)
    
    @patch('modules.servicios_sanitarios.src.core.extraer_texto_pdf')
    def test_analizar_pdfs_con_fallos(self, mock_extraer):
        """Test de análisis con algunos fallos."""
        # Crear PDFs
        (self.ruta_pdfs / "test1.pdf").touch()
        (self.ruta_pdfs / "test2.pdf").touch()
        
        # Simular que el segundo falla
        mock_extraer.side_effect = ["Texto PDF 1", None]
        
        resultado = self.servicio.analyze_pdfs(
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['analizados'], 1)
        self.assertEqual(resultado['failed'], 1)
    
    def test_analizar_pdfs_carpeta_vacia(self):
        """Test cuando no hay PDFs."""
        resultado = self.servicio.analyze_pdfs(
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['total_pdfs'], 0)
        self.assertEqual(resultado['analizados'], 0)
    
    @patch('modules.servicios_sanitarios.src.core.extraer_texto_pdf')
    def test_analizar_pdfs_con_ocr(self, mock_extraer):
        """Test de análisis con OCR habilitado."""
        (self.ruta_pdfs / "test1.pdf").touch()
        
        mock_extraer.return_value = "Texto extraído con OCR"
        
        resultado = self.servicio.analyze_pdfs(
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro),
            use_ocr=True
        )
        
        self.assertTrue(resultado['success'])
        self.assertTrue(resultado['usado_ocr'])
        self.assertEqual(resultado['analizados'], 1)
    
    @patch('modules.servicios_sanitarios.src.core.extraer_texto_pdf')
    def test_analizar_pdfs_guarda_metadatos(self, mock_extraer):
        """Test que verifica que se guardan los metadatos correctamente."""
        (self.ruta_pdfs / "test1.pdf").write_bytes(b"contenido de prueba")
        
        mock_extraer.return_value = "Texto del PDF de prueba"
        
        resultado = self.servicio.analyze_pdfs(
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['pdfs_analizados']), 1)
        
        pdf_analizado = resultado['pdfs_analizados'][0]
        self.assertIn('nombre_archivo', pdf_analizado)
        self.assertIn('carpeta', pdf_analizado)
        self.assertIn('tamanio_kb', pdf_analizado)
        self.assertIn('longitud_texto', pdf_analizado)
        self.assertIn('texto_extraido', pdf_analizado)
        self.assertIn('timestamp', pdf_analizado)
        
        self.assertEqual(pdf_analizado['nombre_archivo'], 'test1.pdf')
        self.assertGreater(pdf_analizado['tamanio_kb'], 0)
        self.assertEqual(pdf_analizado['longitud_texto'], len("Texto del PDF de prueba"))


if __name__ == '__main__':
    unittest.main()
