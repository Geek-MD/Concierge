"""
Tests para la funcionalidad de monitoreo de tarifas vigentes.
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
    extraer_nombre_empresa,
    extraer_datos_tabla_tarifas,
    extraer_empresas_agua
)


class TestExtraerNombreEmpresa:
    """Tests para la función extraer_nombre_empresa."""
    
    def test_extraer_nombre_con_guion(self):
        """Test: Extrae correctamente el nombre antes del guión."""
        texto = "Aguas Andinas - Tarifas vigentes"
        resultado = extraer_nombre_empresa(texto)
        assert resultado == "Aguas Andinas"
    
    def test_extraer_nombre_sin_guion(self):
        """Test: Devuelve el texto completo si no hay guión."""
        texto = "Aguas Andinas"
        resultado = extraer_nombre_empresa(texto)
        assert resultado == "Aguas Andinas"
    
    def test_extraer_nombre_vacio(self):
        """Test: Retorna None para texto vacío."""
        assert extraer_nombre_empresa("") is None
        assert extraer_nombre_empresa(None) is None
    
    def test_extraer_nombre_con_espacios(self):
        """Test: Maneja correctamente espacios adicionales."""
        texto = "  Aguas Andinas  -  Tarifas vigentes  "
        resultado = extraer_nombre_empresa(texto)
        assert resultado == "Aguas Andinas"
    
    def test_extraer_nombre_multiples_guiones(self):
        """Test: Usa solo el primer guión."""
        texto = "Aguas Andinas - Tarifas vigentes - Región Metropolitana"
        resultado = extraer_nombre_empresa(texto)
        assert resultado == "Aguas Andinas"


class TestExtraerDatosTablaTarifas:
    """Tests para la función extraer_datos_tabla_tarifas."""
    
    def test_extraer_datos_tabla_simple(self):
        """Test: Extrae datos de una tabla HTML simple."""
        html = """
        <table>
            <tr>
                <th>Localidades</th>
                <th>Tarifa vigente</th>
            </tr>
            <tr>
                <td>Santiago</td>
                <td><a href="/tarifa_santiago.pdf">Ver PDF</a></td>
            </tr>
            <tr>
                <td>Providencia</td>
                <td><a href="/tarifa_providencia.pdf">Ver PDF</a></td>
            </tr>
        </table>
        """
        base_url = "https://www.siss.gob.cl"
        
        resultado = extraer_datos_tabla_tarifas(html, base_url)
        
        assert len(resultado) == 2
        assert resultado[0]["localidad"] == "Santiago"
        assert resultado[0]["url_pdf"] == "https://www.siss.gob.cl/tarifa_santiago.pdf"
        assert resultado[1]["localidad"] == "Providencia"
        assert resultado[1]["url_pdf"] == "https://www.siss.gob.cl/tarifa_providencia.pdf"
    
    def test_extraer_datos_tabla_url_absoluta(self):
        """Test: Maneja correctamente URLs absolutas."""
        html = """
        <table>
            <tr>
                <th>Localidades</th>
                <th>Tarifa vigente</th>
            </tr>
            <tr>
                <td>Santiago</td>
                <td><a href="https://ejemplo.com/tarifa.pdf">Ver PDF</a></td>
            </tr>
        </table>
        """
        base_url = "https://www.siss.gob.cl"
        
        resultado = extraer_datos_tabla_tarifas(html, base_url)
        
        assert len(resultado) == 1
        assert resultado[0]["url_pdf"] == "https://ejemplo.com/tarifa.pdf"
    
    def test_extraer_datos_tabla_sin_datos(self):
        """Test: Retorna lista vacía para tabla sin datos válidos."""
        html = """
        <table>
            <tr>
                <th>Otra Columna</th>
                <th>Otra Columna 2</th>
            </tr>
            <tr>
                <td>Dato</td>
                <td>Dato 2</td>
            </tr>
        </table>
        """
        base_url = "https://www.siss.gob.cl"
        
        resultado = extraer_datos_tabla_tarifas(html, base_url)
        
        assert len(resultado) == 0
    
    def test_extraer_datos_tabla_fila_incompleta(self):
        """Test: Ignora filas sin localidad o sin enlace PDF."""
        html = """
        <table>
            <tr>
                <th>Localidades</th>
                <th>Tarifa vigente</th>
            </tr>
            <tr>
                <td>Santiago</td>
                <td><a href="/tarifa.pdf">Ver PDF</a></td>
            </tr>
            <tr>
                <td></td>
                <td><a href="/tarifa2.pdf">Ver PDF</a></td>
            </tr>
            <tr>
                <td>Providencia</td>
                <td>Sin enlace</td>
            </tr>
        </table>
        """
        base_url = "https://www.siss.gob.cl"
        
        resultado = extraer_datos_tabla_tarifas(html, base_url)
        
        # Solo debe retornar la primera fila válida
        assert len(resultado) == 1
        assert resultado[0]["localidad"] == "Santiago"
    
    def test_extraer_datos_tabla_multiples_columnas(self):
        """Test: Funciona con tablas que tienen columnas adicionales."""
        html = """
        <table>
            <tr>
                <th>Código</th>
                <th>Localidades</th>
                <th>Tarifa vigente</th>
                <th>Observaciones</th>
            </tr>
            <tr>
                <td>001</td>
                <td>Santiago</td>
                <td><a href="/tarifa.pdf">Ver PDF</a></td>
                <td>Vigente</td>
            </tr>
        </table>
        """
        base_url = "https://www.siss.gob.cl"
        
        resultado = extraer_datos_tabla_tarifas(html, base_url)
        
        assert len(resultado) == 1
        assert resultado[0]["localidad"] == "Santiago"


class TestExtraerEmpresasAgua:
    """Tests para la función extraer_empresas_agua."""
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_extraer_empresas_exitoso(self, mock_get):
        """Test: Extrae correctamente empresas y sus datos."""
        mock_response = MagicMock()
        html_content = """
        <html>
            <body>
                <h2>Aguas Andinas - Tarifas vigentes</h2>
                <table>
                    <tr>
                        <th>Localidades</th>
                        <th>Tarifa vigente</th>
                    </tr>
                    <tr>
                        <td>Santiago</td>
                        <td><a href="/tarifa1.pdf">Ver PDF</a></td>
                    </tr>
                </table>
                
                <h2>Esval - Tarifas vigentes</h2>
                <table>
                    <tr>
                        <th>Localidades</th>
                        <th>Tarifa vigente</th>
                    </tr>
                    <tr>
                        <td>Valparaiso</td>
                        <td><a href="/tarifa2.pdf">Ver PDF</a></td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mock_response.content = html_content.encode('utf-8')
        mock_response.url = "https://www.siss.gob.cl/tarifas"
        mock_get.return_value = mock_response
        
        resultado = extraer_empresas_agua("https://www.siss.gob.cl/tarifas")
        
        assert len(resultado) == 2
        assert resultado[0]["empresa"] == "Aguas Andinas"
        assert len(resultado[0]["tarifas"]) == 1
        assert resultado[0]["tarifas"][0]["localidad"] == "Santiago"
        assert resultado[1]["empresa"] == "Esval"
        assert len(resultado[1]["tarifas"]) == 1
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_extraer_empresas_sin_tabla(self, mock_get):
        """Test: No extrae empresas sin tabla de datos."""
        mock_response = MagicMock()
        html_content = """
        <html>
            <body>
                <h2>Aguas Andinas - Tarifas vigentes</h2>
                <p>Sin tabla de datos</p>
            </body>
        </html>
        """
        mock_response.content = html_content.encode('utf-8')
        mock_response.url = "https://www.siss.gob.cl/tarifas"
        mock_get.return_value = mock_response
        
        resultado = extraer_empresas_agua("https://www.siss.gob.cl/tarifas")
        
        assert len(resultado) == 0
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_extraer_empresas_error_conexion(self, mock_get):
        """Test: Manejo de error de conexion."""
        mock_get.side_effect = Exception("Error de conexion")
        
        resultado = extraer_empresas_agua("https://www.siss.gob.cl/tarifas")
        
        assert resultado == []
    
    @patch('modules.servicios_sanitarios.src.utils.requests.get')
    def test_extraer_empresas_diferentes_encabezados(self, mock_get):
        """Test: Funciona con diferentes tipos de encabezados HTML."""
        mock_response = MagicMock()
        html_content = """
        <html>
            <body>
                <h3>Aguas Andinas - Tarifas vigentes</h3>
                <table>
                    <tr>
                        <th>Localidades</th>
                        <th>Tarifa vigente</th>
                    </tr>
                    <tr>
                        <td>Santiago</td>
                        <td><a href="/tarifa.pdf">Ver PDF</a></td>
                    </tr>
                </table>
                
                <strong>Esval - Tarifas vigentes</strong>
                <table>
                    <tr>
                        <th>Localidades</th>
                        <th>Tarifa vigente</th>
                    </tr>
                    <tr>
                        <td>Valparaiso</td>
                        <td><a href="/tarifa2.pdf">Ver PDF</a></td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mock_response.content = html_content.encode('utf-8')
        mock_response.url = "https://www.siss.gob.cl/tarifas"
        mock_get.return_value = mock_response
        
        resultado = extraer_empresas_agua("https://www.siss.gob.cl/tarifas")
        
        assert len(resultado) == 2


class TestMonitorearTarifasVigentes:
    """Tests para el método monitorear_tarifas_vigentes."""
    
    @patch('modules.servicios_sanitarios.src.utils.cargar_json')
    @patch('modules.servicios_sanitarios.src.core.extraer_empresas_agua')
    @patch('modules.servicios_sanitarios.src.core.guardar_json')
    def test_monitorear_primera_vez(self, mock_guardar, mock_extraer, mock_cargar, tmp_path):
        """Test: Primera vez guarda correctamente."""
        # Configurar mocks
        mock_cargar.return_value = None
        mock_extraer.return_value = [
            {
                "empresa": "Aguas Andinas",
                "tarifas": [
                    {"localidad": "Santiago", "url_pdf": "https://example.com/tarifa.pdf"}
                ]
            }
        ]
        mock_guardar.return_value = True
        
        servicio = ServiciosSanitarios()
        archivo_salida = str(tmp_path / "tarifas_test.json")
        
        resultado = servicio.monitorear_tarifas_vigentes(
            url_tarifas="https://www.siss.gob.cl/tarifas",
            ruta_salida=archivo_salida
        )
        
        assert resultado["exito"] is True
        assert resultado["guardado"] is True
        assert resultado["es_primera_vez"] is True
        assert resultado["total_empresas"] == 1
        assert resultado["mensaje"] == "Primera verificación guardada"
        assert len(resultado["empresas"]) == 1
    
    @patch('modules.servicios_sanitarios.src.core.cargar_json')
    @patch('modules.servicios_sanitarios.src.core.extraer_empresas_agua')
    @patch('modules.servicios_sanitarios.src.core.guardar_json')
    def test_monitorear_sin_cambios(self, mock_guardar, mock_extraer, mock_cargar):
        """Test: Sin cambios no guarda de nuevo."""
        empresas_data = [
            {
                "empresa": "Aguas Andinas",
                "tarifas": [
                    {"localidad": "Santiago", "url_pdf": "https://example.com/tarifa.pdf"}
                ]
            }
        ]
        
        # Configurar mocks
        datos_previos = {
            "empresas": empresas_data,
            "total_empresas": 1,
            "timestamp": "2024-01-01T00:00:00",
            "historial": []
        }
        mock_cargar.return_value = datos_previos
        mock_extraer.return_value = empresas_data
        
        servicio = ServiciosSanitarios()
        resultado = servicio.monitorear_tarifas_vigentes(
            url_tarifas="https://www.siss.gob.cl/tarifas"
        )
        
        assert resultado["exito"] is True
        assert resultado["guardado"] is False
        assert resultado["es_primera_vez"] is False
        assert resultado["cambios_detectados"] is False
        assert resultado["mensaje"] == "Sin cambios, no se guardó"
        mock_guardar.assert_not_called()
    
    @patch('modules.servicios_sanitarios.src.core.cargar_json')
    @patch('modules.servicios_sanitarios.src.core.extraer_empresas_agua')
    @patch('modules.servicios_sanitarios.src.core.guardar_json')
    def test_monitorear_con_cambios(self, mock_guardar, mock_extraer, mock_cargar):
        """Test: Cambios detectados se guardan con historial."""
        # Configurar mocks
        datos_previos = {
            "empresas": [
                {
                    "empresa": "Aguas Andinas",
                    "tarifas": [
                        {"localidad": "Santiago", "url_pdf": "https://example.com/vieja.pdf"}
                    ]
                }
            ],
            "total_empresas": 1,
            "timestamp": "2024-01-01T00:00:00",
            "historial": []
        }
        
        nuevos_datos = [
            {
                "empresa": "Aguas Andinas",
                "tarifas": [
                    {"localidad": "Santiago", "url_pdf": "https://example.com/nueva.pdf"}
                ]
            }
        ]
        
        mock_cargar.return_value = datos_previos
        mock_extraer.return_value = nuevos_datos
        mock_guardar.return_value = True
        
        servicio = ServiciosSanitarios()
        resultado = servicio.monitorear_tarifas_vigentes(
            url_tarifas="https://www.siss.gob.cl/tarifas"
        )
        
        assert resultado["exito"] is True
        assert resultado["guardado"] is True
        assert resultado["es_primera_vez"] is False
        assert resultado["cambios_detectados"] is True
        assert resultado["mensaje"] == "Cambios detectados y guardados"
        
        # Verificar que se guardó con historial
        assert mock_guardar.called
        datos_guardados = mock_guardar.call_args[0][0]
        assert "historial" in datos_guardados
        assert len(datos_guardados["historial"]) == 1
    
    @patch('modules.servicios_sanitarios.src.core.extraer_empresas_agua')
    def test_monitorear_sin_empresas(self, mock_extraer):
        """Test: Manejo cuando no se extraen empresas."""
        mock_extraer.return_value = []
        
        servicio = ServiciosSanitarios()
        resultado = servicio.monitorear_tarifas_vigentes(
            url_tarifas="https://www.siss.gob.cl/tarifas"
        )
        
        assert resultado["exito"] is False
        assert "error" in resultado
        assert resultado["empresas"] == []
    
    @patch('modules.servicios_sanitarios.src.core.ServiciosSanitarios.verificar_siss')
    @patch('modules.servicios_sanitarios.src.core.extraer_empresas_agua')
    @patch('modules.servicios_sanitarios.src.utils.cargar_json')
    @patch('modules.servicios_sanitarios.src.core.guardar_json')
    def test_monitorear_sin_url_usa_verificar_siss(
        self, mock_guardar, mock_cargar, mock_extraer, mock_verificar
    ):
        """Test: Si no se provee URL, la obtiene con verificar_siss."""
        # Configurar mocks
        mock_verificar.return_value = {
            "exito": True,
            "url_tarifas_vigentes": "https://www.siss.gob.cl/tarifas"
        }
        mock_cargar.return_value = None
        mock_extraer.return_value = [
            {
                "empresa": "Aguas Andinas",
                "tarifas": [
                    {"localidad": "Santiago", "url_pdf": "https://example.com/tarifa.pdf"}
                ]
            }
        ]
        mock_guardar.return_value = True
        
        servicio = ServiciosSanitarios()
        resultado = servicio.monitorear_tarifas_vigentes()
        
        assert resultado["exito"] is True
        mock_verificar.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
