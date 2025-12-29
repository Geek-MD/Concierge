"""
Tests para el módulo core de servicios sanitarios.
"""

import pytest
from datetime import datetime
import sys
import os

# Add root directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from modules.servicios_sanitarios.src.core import ServiciosSanitarios


class TestServiciosSanitarios:
    """Tests for the ServiciosSanitarios class."""
    
    def test_inicializacion(self):
        """Test: The module initializes correctly."""
        servicio = ServiciosSanitarios()
        
        assert servicio.nombre == "ServiciosSanitarios"
        assert servicio.id is not None
        assert isinstance(servicio.fecha_creacion, datetime)
        assert servicio.tareas == []
        assert servicio.esta_activo() is True
    
    def test_inicializacion_con_nombre(self):
        """Test: The module can be initialized with a custom name."""
        nombre_custom = "MiServicio"
        servicio = ServiciosSanitarios(nombre=nombre_custom)
        
        assert servicio.nombre == nombre_custom
    
    def test_agregar_tarea_basica(self):
        """Test: A basic task can be added."""
        servicio = ServiciosSanitarios()
        tarea = servicio.agregar_tarea("Limpiar área común")
        
        assert tarea["descripcion"] == "Limpiar área común"
        assert tarea["prioridad"] == "media"
        assert tarea["estado"] == "pendiente"
        assert tarea["id"] is not None
        assert len(servicio.tareas) == 1
    
    def test_agregar_tarea_con_prioridad(self):
        """Test: A task can be added with specific priority."""
        servicio = ServiciosSanitarios()
        tarea = servicio.agregar_tarea("Emergencia sanitaria", prioridad="critica")
        
        assert tarea["prioridad"] == "critica"
    
    def test_agregar_tarea_prioridad_invalida(self):
        """Test: Agregar tarea con prioridad inválida genera error."""
        servicio = ServiciosSanitarios()
        
        with pytest.raises(ValueError):
            servicio.agregar_tarea("Tarea", prioridad="urgentisima")
    
    def test_agregar_tarea_con_metadata(self):
        """Test: Metadata can be added to a task."""
        servicio = ServiciosSanitarios()
        metadata = {"ubicacion": "Piso 3", "responsable": "Juan"}
        tarea = servicio.agregar_tarea("Revisar sanitarios", metadata=metadata)
        
        assert tarea["metadata"] == metadata
    
    def test_listar_tareas(self):
        """Test: All tasks can be listed."""
        servicio = ServiciosSanitarios()
        servicio.agregar_tarea("Tarea 1")
        servicio.agregar_tarea("Tarea 2")
        servicio.agregar_tarea("Tarea 3")
        
        tareas = servicio.listar_tareas()
        assert len(tareas) == 3
    
    def test_listar_tareas_por_estado(self):
        """Test: Tasks can be filtered by state."""
        servicio = ServiciosSanitarios()
        tarea1 = servicio.agregar_tarea("Tarea 1")
        servicio.agregar_tarea("Tarea 2")
        servicio.completar_tarea(tarea1["id"])
        
        pendientes = servicio.listar_tareas(filtro_estado="pendiente")
        completadas = servicio.listar_tareas(filtro_estado="completado")
        
        assert len(pendientes) == 1
        assert len(completadas) == 1
    
    def test_listar_tareas_por_prioridad(self):
        """Test: Tasks can be filtered by priority."""
        servicio = ServiciosSanitarios()
        servicio.agregar_tarea("Tarea baja", prioridad="baja")
        servicio.agregar_tarea("Tarea alta", prioridad="alta")
        servicio.agregar_tarea("Tarea alta 2", prioridad="alta")
        
        altas = servicio.listar_tareas(filtro_prioridad="alta")
        bajas = servicio.listar_tareas(filtro_prioridad="baja")
        
        assert len(altas) == 2
        assert len(bajas) == 1
    
    def test_completar_tarea(self):
        """Test: A task can be completed."""
        servicio = ServiciosSanitarios()
        tarea = servicio.agregar_tarea("Tarea a completar")
        
        resultado = servicio.completar_tarea(tarea["id"])
        
        assert resultado is True
        assert tarea["estado"] == "completado"
        assert tarea["fecha_completado"] is not None
    
    def test_completar_tarea_inexistente(self):
        """Test: Intentar completar tarea inexistente retorna False."""
        servicio = ServiciosSanitarios()
        
        resultado = servicio.completar_tarea("id-inexistente")
        
        assert resultado is False
    
    def test_obtener_estadisticas(self):
        """Test: Module statistics can be obtained."""
        servicio = ServiciosSanitarios()
        servicio.agregar_tarea("Tarea 1", prioridad="alta")
        servicio.agregar_tarea("Tarea 2", prioridad="baja")
        tarea3 = servicio.agregar_tarea("Tarea 3", prioridad="alta")
        servicio.completar_tarea(tarea3["id"])
        
        stats = servicio.obtener_estadisticas()
        
        assert stats["total"] == 3
        assert stats["pendientes"] == 2
        assert stats["completadas"] == 1
        assert stats["por_prioridad"]["alta"] == 2
        assert stats["por_prioridad"]["baja"] == 1
        assert stats["modulo_activo"] is True
    
    def test_obtener_info(self):
        """Test: Module information can be obtained."""
        servicio = ServiciosSanitarios(nombre="TestServicio")
        servicio.agregar_tarea("Tarea 1")
        
        info = servicio.obtener_info()
        
        assert info["nombre"] == "TestServicio"
        assert info["id"] is not None
        assert info["activo"] is True
        assert info["total_tareas"] == 1
    
    def test_activar_desactivar(self):
        """Test: The module can be activated and deactivated."""
        servicio = ServiciosSanitarios()
        
        assert servicio.esta_activo() is True
        
        servicio.desactivar()
        assert servicio.esta_activo() is False
        
        servicio.activar()
        assert servicio.esta_activo() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
