"""
Tests para la funcionalidad de verificación SISS.
"""

import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Agregar el directorio raíz al path para importar el módulo
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from modules.servicios_sanitarios.src.core import ServiciosSanitarios
from modules.servicios_sanitarios.src.utils import verificar_redireccion_url, guardar_json, cargar_json


class TestVerificarRedireccionURL:
    """Tests para la función verificar_redireccion_url."""
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_verificar_redireccion_exitosa(self, mock_get):
        """Test: Verifica que se obtiene correctamente la URL de redirección."""
        # Simular respuesta con redirección
        mock_response = MagicMock()
        mock_response.url = "https://www.siss.gob.cl/pagina_final"
        mock_get.return_value = mock_response
        
        url_final = verificar_redireccion_url("https://www.siss.gob.cl")
        
        assert url_final == "https://www.siss.gob.cl/pagina_final"
        mock_get.assert_called_once()
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_verificar_redireccion_sin_cambio(self, mock_get):
        """Test: URL que no redirecciona devuelve la misma URL."""
        mock_response = MagicMock()
        mock_response.url = "https://www.siss.gob.cl"
        mock_get.return_value = mock_response
        
        url_final = verificar_redireccion_url("https://www.siss.gob.cl")
        
        assert url_final == "https://www.siss.gob.cl"
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_verificar_redireccion_error(self, mock_get):
        """Test: Manejo de errores en petición HTTP."""
        mock_get.side_effect = Exception("Error de conexión")
        
        url_final = verificar_redireccion_url("https://www.siss.gob.cl")
        
        assert url_final is None


class TestGuardarCargarJSON:
    """Tests para las funciones de guardar y cargar JSON."""
    
    def test_guardar_json_exitoso(self, tmp_path):
        """Test: Guardar datos en JSON correctamente."""
        archivo = tmp_path / "test.json"
        datos = {"url": "https://example.com", "timestamp": "2024-01-01"}
        
        resultado = guardar_json(datos, str(archivo))
        
        assert resultado is True
        assert archivo.exists()
        
        # Verificar contenido
        with open(archivo, 'r') as f:
            contenido = json.load(f)
        assert contenido == datos
    
    def test_guardar_json_crea_directorios(self, tmp_path):
        """Test: Crear directorios automáticamente si no existen."""
        archivo = tmp_path / "subdir" / "subdir2" / "test.json"
        datos = {"test": "data"}
        
        resultado = guardar_json(datos, str(archivo))
        
        assert resultado is True
        assert archivo.exists()
    
    def test_cargar_json_exitoso(self, tmp_path):
        """Test: Cargar datos desde JSON correctamente."""
        archivo = tmp_path / "test.json"
        datos = {"url": "https://example.com"}
        
        with open(archivo, 'w') as f:
            json.dump(datos, f)
        
        resultado = cargar_json(str(archivo))
        
        assert resultado == datos
    
    def test_cargar_json_archivo_inexistente(self):
        """Test: Manejo de archivo JSON inexistente."""
        resultado = cargar_json("/ruta/inexistente/archivo.json")
        
        assert resultado is None


class TestVerificarSISS:
    """Tests para el método verificar_siss."""
    
    @patch('modules.servicios_sanitarios.src.core.verificar_redireccion_url')
    @patch('modules.servicios_sanitarios.src.core.guardar_json')
    def test_verificar_siss_exitoso(self, mock_guardar, mock_verificar, tmp_path):
        """Test: Verificación SISS exitosa."""
        # Configurar mocks
        mock_verificar.return_value = "https://www.siss.gob.cl/589/w3-channel.html"
        mock_guardar.return_value = True
        
        servicio = ServiciosSanitarios()
        archivo_salida = str(tmp_path / "siss_test.json")
        
        resultado = servicio.verificar_siss(ruta_salida=archivo_salida)
        
        assert resultado["exito"] is True
        assert resultado["url_original"] == "https://www.siss.gob.cl"
        assert resultado["url_final"] == "https://www.siss.gob.cl/589/w3-channel.html"
        assert resultado["guardado"] is True
        assert "timestamp" in resultado
        mock_verificar.assert_called_once_with("https://www.siss.gob.cl")
    
    @patch('modules.servicios_sanitarios.src.core.verificar_redireccion_url')
    def test_verificar_siss_error_conexion(self, mock_verificar):
        """Test: Manejo de error en la verificación SISS."""
        mock_verificar.return_value = None
        
        servicio = ServiciosSanitarios()
        resultado = servicio.verificar_siss()
        
        assert resultado["exito"] is False
        assert resultado["url_final"] is None
        assert "error" in resultado
    
    @patch('modules.servicios_sanitarios.src.core.verificar_redireccion_url')
    @patch('modules.servicios_sanitarios.src.core.guardar_json')
    def test_verificar_siss_guarda_datos_correctos(self, mock_guardar, mock_verificar):
        """Test: Los datos guardados contienen la información esperada."""
        mock_verificar.return_value = "https://www.siss.gob.cl/final"
        mock_guardar.return_value = True
        
        servicio = ServiciosSanitarios()
        servicio.verificar_siss()
        
        # Verificar que se llamó a guardar_json con los datos correctos
        assert mock_guardar.called
        datos_guardados = mock_guardar.call_args[0][0]
        
        assert datos_guardados["url_original"] == "https://www.siss.gob.cl"
        assert datos_guardados["url_final"] == "https://www.siss.gob.cl/final"
        assert datos_guardados["verificado"] is True
        assert "timestamp" in datos_guardados


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
