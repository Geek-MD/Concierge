"""
Tests para la funcionalidad de verificación SISS.
"""

import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add root directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from modules.servicios_sanitarios.src.core import ServiciosSanitarios
from modules.servicios_sanitarios.src.utils import (
    check_url_redirection, 
    save_json, 
    load_json,
    extract_url_by_text
)


class TestVerificarRedireccionURL:
    """Tests para la función check_url_redirection."""
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_verificar_redireccion_exitosa(self, mock_get):
        """Test: Verifica que se obtiene correctamente la URL de redirección."""
        # Simular respuesta con redirección
        mock_response = MagicMock()
        mock_response.url = "https://www.siss.gob.cl/pagina_final"
        mock_get.return_value = mock_response
        
        url_final = check_url_redirection("https://www.siss.gob.cl")
        
        assert url_final == "https://www.siss.gob.cl/pagina_final"
        mock_get.assert_called_once()
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_verificar_redireccion_sin_cambio(self, mock_get):
        """Test: URL que no redirecciona devuelve la misma URL."""
        mock_response = MagicMock()
        mock_response.url = "https://www.siss.gob.cl"
        mock_get.return_value = mock_response
        
        url_final = check_url_redirection("https://www.siss.gob.cl")
        
        assert url_final == "https://www.siss.gob.cl"
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_verificar_redireccion_error(self, mock_get):
        """Test: Manejo de errores en petición HTTP."""
        mock_get.side_effect = Exception("Error de conexión")
        
        url_final = check_url_redirection("https://www.siss.gob.cl")
        
        assert url_final is None


class TestGuardarCargarJSON:
    """Tests para las funciones de guardar y cargar JSON."""
    
    def test_save_json_exitoso(self, tmp_path):
        """Test: Guardar datos en JSON correctamente."""
        archivo = tmp_path / "test.json"
        datos = {"url": "https://example.com", "timestamp": "2024-01-01"}
        
        resultado = save_json(datos, str(archivo))
        
        assert resultado is True
        assert archivo.exists()
        
        # Verificar contenido
        with open(archivo, 'r') as f:
            contenido = json.load(f)
        assert contenido == datos
    
    def test_save_json_crea_directorios(self, tmp_path):
        """Test: Crear directorios automáticamente si no existen."""
        archivo = tmp_path / "subdir" / "subdir2" / "test.json"
        datos = {"test": "data"}
        
        resultado = save_json(datos, str(archivo))
        
        assert resultado is True
        assert archivo.exists()
    
    def test_load_json_exitoso(self, tmp_path):
        """Test: Cargar datos desde JSON correctamente."""
        archivo = tmp_path / "test.json"
        datos = {"url": "https://example.com"}
        
        with open(archivo, 'w') as f:
            json.dump(datos, f)
        
        resultado = load_json(str(archivo))
        
        assert resultado == datos
    
    def test_load_json_archivo_inexistente(self):
        """Test: Manejo de archivo JSON inexistente."""
        resultado = load_json("/ruta/inexistente/archivo.json")
        
        assert resultado is None


class TestExtraerURLPorTexto:
    """Tests para la función extract_url_by_text."""
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_extract_url_by_text_exitoso(self, mock_get):
        """Test: Extrae correctamente la URL de un enlace por texto."""
        mock_response = MagicMock()
        mock_response.content = b'''
        <html>
            <body>
                <a href="/tarifas">Tarifas vigentes</a>
            </body>
        </html>
        '''
        mock_response.url = "https://www.siss.gob.cl/589/w3-channel.html"
        mock_get.return_value = mock_response
        
        url = extract_url_by_text("https://www.siss.gob.cl/589/w3-channel.html", "Tarifas vigentes")
        
        assert url == "https://www.siss.gob.cl/tarifas"
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_extract_url_by_text_no_encontrado(self, mock_get):
        """Test: Retorna None si el texto no se encuentra."""
        mock_response = MagicMock()
        mock_response.content = b'<html><body><a href="/test">Otro enlace</a></body></html>'
        mock_get.return_value = mock_response
        
        url = extract_url_by_text("https://example.com", "Tarifas vigentes")
        
        assert url is None
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_extract_url_by_text_url_absoluta(self, mock_get):
        """Test: Maneja correctamente URLs absolutas."""
        mock_response = MagicMock()
        mock_response.content = b'''
        <html>
            <body>
                <a href="https://www.siss.gob.cl/tarifas/completo">Tarifas vigentes</a>
            </body>
        </html>
        '''
        mock_response.url = "https://www.siss.gob.cl"
        mock_get.return_value = mock_response
        
        url = extract_url_by_text("https://www.siss.gob.cl", "Tarifas vigentes")
        
        assert url == "https://www.siss.gob.cl/tarifas/completo"
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_extract_url_by_text_error(self, mock_get):
        """Test: Manejo de errores en petición HTTP."""
        mock_get.side_effect = Exception("Error de conexión")
        
        url = extract_url_by_text("https://example.com", "Tarifas vigentes")
        
        assert url is None


class TestVerificarSISS:
    """Tests para el método verificar_siss."""
    
    @patch('modules.servicios_sanitarios.src.utils.load_json')
    @patch('modules.servicios_sanitarios.src.core.extract_url_by_text')
    @patch('modules.servicios_sanitarios.src.core.check_url_redirection')
    @patch('modules.servicios_sanitarios.src.core.save_json')
    def test_verificar_siss_primera_vez(self, mock_guardar, mock_verificar, mock_extraer, mock_cargar, tmp_path):
        """Test: Primera verificación SISS guarda correctamente."""
        # Configurar mocks
        mock_cargar.return_value = None  # No existe archivo previo
        mock_verificar.return_value = "https://www.siss.gob.cl/589/w3-channel.html"
        mock_extraer.return_value = "https://www.siss.gob.cl/tarifas"
        mock_guardar.return_value = True
        
        servicio = ServiciosSanitarios()
        archivo_salida = str(tmp_path / "siss_test.json")
        
        resultado = servicio.verificar_siss(ruta_salida=archivo_salida)
        
        assert resultado["success"] is True
        assert resultado["url_original"] == "https://www.siss.gob.cl"
        assert resultado["url_final"] == "https://www.siss.gob.cl/589/w3-channel.html"
        assert resultado["url_tarifas_vigentes"] == "https://www.siss.gob.cl/tarifas"
        assert resultado["guardado"] is True
        assert resultado["is_first_time"] is True
        assert resultado["message"] == "Primera verificación guardada"
    
    @patch('modules.servicios_sanitarios.src.core.load_json')
    @patch('modules.servicios_sanitarios.src.core.extract_url_by_text')
    @patch('modules.servicios_sanitarios.src.core.check_url_redirection')
    @patch('modules.servicios_sanitarios.src.core.save_json')
    def test_verificar_siss_sin_cambios(self, mock_guardar, mock_verificar, mock_extraer, mock_cargar):
        """Test: Sin cambios no guarda de nuevo."""
        # Configurar mocks
        datos_previos = {
            "url_final": "https://www.siss.gob.cl/589/w3-channel.html",
            "url_tarifas_vigentes": "https://www.siss.gob.cl/tarifas",
            "timestamp": "2024-01-01T00:00:00",
            "historial": []
        }
        mock_cargar.return_value = datos_previos
        mock_verificar.return_value = "https://www.siss.gob.cl/589/w3-channel.html"
        mock_extraer.return_value = "https://www.siss.gob.cl/tarifas"
        
        servicio = ServiciosSanitarios()
        resultado = servicio.verificar_siss()
        
        assert resultado["success"] is True
        assert resultado["guardado"] is False
        assert resultado["is_first_time"] is False
        assert resultado["message"] == "Sin cambios, no se guardó"
        mock_guardar.assert_not_called()
    
    @patch('modules.servicios_sanitarios.src.core.load_json')
    @patch('modules.servicios_sanitarios.src.core.extract_url_by_text')
    @patch('modules.servicios_sanitarios.src.core.check_url_redirection')
    @patch('modules.servicios_sanitarios.src.core.save_json')
    def test_verificar_siss_con_cambio_url_final(self, mock_guardar, mock_verificar, mock_extraer, mock_cargar):
        """Test: Cambio en URL final se guarda con historial."""
        # Configurar mocks
        datos_previos = {
            "url_final": "https://www.siss.gob.cl/viejo",
            "url_tarifas_vigentes": "https://www.siss.gob.cl/tarifas",
            "timestamp": "2024-01-01T00:00:00",
            "historial": []
        }
        mock_cargar.return_value = datos_previos
        mock_verificar.return_value = "https://www.siss.gob.cl/nuevo"
        mock_extraer.return_value = "https://www.siss.gob.cl/tarifas"
        mock_guardar.return_value = True
        
        servicio = ServiciosSanitarios()
        resultado = servicio.verificar_siss()
        
        assert resultado["success"] is True
        assert resultado["guardado"] is True
        assert resultado["is_first_time"] is False
        assert resultado["cambios"]["url_final"] is True
        assert resultado["message"] == "Cambios detectados y guardados"
        
        # Verificar que se guardó con historial
        assert mock_guardar.called
        datos_guardados = mock_guardar.call_args[0][0]
        assert "historial" in datos_guardados
        assert len(datos_guardados["historial"]) == 1
        assert datos_guardados["historial"][0]["url_final"] == "https://www.siss.gob.cl/viejo"
    
    @patch('modules.servicios_sanitarios.src.core.load_json')
    @patch('modules.servicios_sanitarios.src.core.extract_url_by_text')
    @patch('modules.servicios_sanitarios.src.core.check_url_redirection')
    @patch('modules.servicios_sanitarios.src.core.save_json')
    def test_verificar_siss_con_cambio_tarifas(self, mock_guardar, mock_verificar, mock_extraer, mock_cargar):
        """Test: Cambio en URL de tarifas se guarda."""
        # Configurar mocks
        datos_previos = {
            "url_final": "https://www.siss.gob.cl/589/w3-channel.html",
            "url_tarifas_vigentes": "https://www.siss.gob.cl/tarifas_viejas",
            "timestamp": "2024-01-01T00:00:00",
            "historial": []
        }
        mock_cargar.return_value = datos_previos
        mock_verificar.return_value = "https://www.siss.gob.cl/589/w3-channel.html"
        mock_extraer.return_value = "https://www.siss.gob.cl/tarifas_nuevas"
        mock_guardar.return_value = True
        
        servicio = ServiciosSanitarios()
        resultado = servicio.verificar_siss()
        
        assert resultado["success"] is True
        assert resultado["guardado"] is True
        assert resultado["cambios"]["url_tarifas_vigentes"] is True
        assert resultado["message"] == "Cambios detectados y guardados"
    
    @patch('modules.servicios_sanitarios.src.core.check_url_redirection')
    def test_verificar_siss_error_conexion(self, mock_verificar):
        """Test: Manejo de error en la verificación SISS."""
        mock_verificar.return_value = None
        
        servicio = ServiciosSanitarios()
        resultado = servicio.verificar_siss()
        
        assert resultado["success"] is False
        assert resultado["url_final"] is None
        assert "error" in resultado


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
