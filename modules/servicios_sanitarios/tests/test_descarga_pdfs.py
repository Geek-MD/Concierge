"""
Tests para la funcionalidad de descarga de PDFs.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import shutil
import json

from modules.servicios_sanitarios.src import ServiciosSanitarios
from modules.servicios_sanitarios.src.utils import download_pdf


class TestDescargarPdf(unittest.TestCase):
    """Tests para la función download_pdf."""
    
    def setUp(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Limpieza después de cada test."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_download_pdf_exitoso(self, mock_get):
        """Test de descarga exitosa de PDF."""
        # Mock de respuesta HTTP
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'application/pdf'}
        mock_response.iter_content = lambda chunk_size: [b'PDF content']
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        ruta_pdf = Path(self.temp_dir) / "test.pdf"
        resultado = download_pdf("https://example.com/test.pdf", str(ruta_pdf))
        
        self.assertTrue(resultado)
        self.assertTrue(ruta_pdf.exists())
        self.assertGreater(ruta_pdf.stat().st_size, 0)
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_download_pdf_crea_directorios(self, mock_get):
        """Test que verifica que se crean los directorios necesarios."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'application/pdf'}
        mock_response.iter_content = lambda chunk_size: [b'PDF content']
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        ruta_pdf = Path(self.temp_dir) / "subdir1" / "subdir2" / "test.pdf"
        resultado = download_pdf("https://example.com/test.pdf", str(ruta_pdf))
        
        self.assertTrue(resultado)
        self.assertTrue(ruta_pdf.parent.exists())
        self.assertTrue(ruta_pdf.exists())
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_download_pdf_error_conexion(self, mock_get):
        """Test de manejo de error de conexión."""
        mock_get.side_effect = Exception("Error de conexión")
        
        ruta_pdf = Path(self.temp_dir) / "test.pdf"
        resultado = download_pdf("https://example.com/test.pdf", str(ruta_pdf))
        
        self.assertFalse(resultado)


class TestDescargarPdfs(unittest.TestCase):
    """Tests para el método download_pdfs."""
    
    def setUp(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.servicio = ServiciosSanitarios()
        
        # Crear JSON de prueba con URLs
        self.ruta_json = Path(self.temp_dir) / "tarifas_test.json"
        self.ruta_pdfs = Path(self.temp_dir) / "pdfs"
        self.ruta_registro = Path(self.temp_dir) / "registro.json"
        
        self.datos_test = {
            "url_tarifas": "https://test.com/tarifas",
            "empresas": [
                {
                    "empresa": "Aguas Andinas",
                    "tarifas": [
                        {
                            "localidad": "Santiago",
                            "url_pdf": "https://test.com/pdf1.pdf"
                        },
                        {
                            "localidad": "Maipú",
                            "url_pdf": "https://test.com/pdf2.pdf"
                        }
                    ]
                },
                {
                    "empresa": "Essbio",
                    "tarifas": [
                        {
                            "localidad": "Concepción",
                            "url_pdf": "https://test.com/pdf3.pdf"
                        }
                    ]
                }
            ],
            "total_empresas": 2
        }
        
        with open(self.ruta_json, 'w', encoding='utf-8') as f:
            json.dump(self.datos_test, f)
    
    def tearDown(self):
        """Limpieza después de cada test."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('modules.servicios_sanitarios.src.core.download_pdf')
    def test_download_pdfs_primera_vez(self, mock_descargar):
        """Test de descarga primera vez (todos los PDFs)."""
        mock_descargar.return_value = True
        
        resultado = self.servicio.download_pdfs(
            ruta_json=str(self.ruta_json),
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertTrue(resultado['success'])
        self.assertTrue(resultado['is_first_time'])
        self.assertEqual(resultado['total_pdfs'], 3)
        self.assertEqual(resultado['descargados'], 3)
        self.assertEqual(resultado['failed'], 0)
        self.assertEqual(mock_descargar.call_count, 3)
    
    @patch('modules.servicios_sanitarios.src.core.download_pdf')
    def test_download_pdfs_solo_nuevos(self, mock_descargar):
        """Test de descarga solo PDFs nuevos."""
        mock_descargar.return_value = True
        
        # Primera descarga
        resultado1 = self.servicio.download_pdfs(
            ruta_json=str(self.ruta_json),
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertEqual(resultado1['descargados'], 3)
        
        # Agregar nuevo PDF al JSON
        self.datos_test['empresas'][0]['tarifas'].append({
            "localidad": "Providencia",
            "url_pdf": "https://test.com/pdf4.pdf"
        })
        
        with open(self.ruta_json, 'w', encoding='utf-8') as f:
            json.dump(self.datos_test, f)
        
        # Segunda descarga - solo el nuevo
        mock_descargar.reset_mock()
        resultado2 = self.servicio.download_pdfs(
            ruta_json=str(self.ruta_json),
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertTrue(resultado2['success'])
        self.assertFalse(resultado2['is_first_time'])
        self.assertEqual(resultado2['descargados'], 1)  # Solo el nuevo
        self.assertEqual(mock_descargar.call_count, 1)
    
    @patch('modules.servicios_sanitarios.src.core.download_pdf')
    def test_download_pdfs_con_fallos(self, mock_descargar):
        """Test de descarga con algunos fallos."""
        # Simular que el segundo PDF falla
        mock_descargar.side_effect = [True, False, True]
        
        resultado = self.servicio.download_pdfs(
            ruta_json=str(self.ruta_json),
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['descargados'], 2)
        self.assertEqual(resultado['failed'], 1)
        self.assertEqual(len(resultado['failed_pdfs']), 1)
    
    def test_download_pdfs_json_no_existe(self):
        """Test cuando el archivo JSON no existe."""
        resultado = self.servicio.download_pdfs(
            ruta_json=str(Path(self.temp_dir) / "noexiste.json"),
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        self.assertFalse(resultado['success'])
        self.assertIn('error', resultado)
    
    @patch('modules.servicios_sanitarios.src.core.download_pdf')
    def test_estructura_carpetas_por_empresa(self, mock_descargar):
        """Test que verifica la estructura de carpetas por empresa."""
        mock_descargar.return_value = True
        
        resultado = self.servicio.download_pdfs(
            ruta_json=str(self.ruta_json),
            pdfs_path=str(self.ruta_pdfs),
            registry_path=str(self.ruta_registro)
        )
        
        # Verificar que se llamó con rutas que incluyen nombre de empresa
        calls = mock_descargar.call_args_list
        
        # Primer PDF de Aguas Andinas
        self.assertIn("Aguas_Andinas", calls[0][0][1])
        self.assertIn("Santiago.pdf", calls[0][0][1])
        
        # Segundo PDF de Aguas Andinas
        self.assertIn("Aguas_Andinas", calls[1][0][1])
        self.assertIn("Maipú.pdf", calls[1][0][1])
        
        # PDF de Essbio
        self.assertIn("Essbio", calls[2][0][1])
        self.assertIn("Concepción.pdf", calls[2][0][1])


if __name__ == '__main__':
    unittest.main()
