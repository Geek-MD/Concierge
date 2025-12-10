"""
Core functionality for Servicios Sanitarios module.

Este archivo contiene la lógica principal del módulo de servicios sanitarios.
"""

from typing import Dict, List, Optional
from datetime import datetime
from .utils import generate_id, format_timestamp


class ServiciosSanitarios:
    """
    Clase principal para el manejo de servicios sanitarios.
    
    Esta clase proporciona la funcionalidad core del módulo, permitiendo
    gestionar tareas relacionadas con servicios sanitarios de manera
    automatizada y eficiente.
    """
    
    def __init__(self, nombre: str = "ServiciosSanitarios"):
        """
        Inicializa el módulo de servicios sanitarios.
        
        Args:
            nombre: Nombre identificador del módulo
        """
        self.nombre = nombre
        self.id = generate_id()
        self.fecha_creacion = datetime.now()
        self.tareas = []
        self._activo = True
        
    def agregar_tarea(self, 
                      descripcion: str, 
                      prioridad: str = "media",
                      metadata: Optional[Dict] = None) -> Dict:
        """
        Agrega una nueva tarea al sistema.
        
        Args:
            descripcion: Descripción de la tarea a realizar
            prioridad: Nivel de prioridad (baja, media, alta, critica)
            metadata: Información adicional sobre la tarea
            
        Returns:
            Dict con la información de la tarea creada
            
        Raises:
            ValueError: Si la prioridad no es válida
        """
        prioridades_validas = ["baja", "media", "alta", "critica"]
        if prioridad not in prioridades_validas:
            raise ValueError(f"Prioridad debe ser una de: {prioridades_validas}")
        
        tarea = {
            "id": generate_id(),
            "descripcion": descripcion,
            "prioridad": prioridad,
            "estado": "pendiente",
            "fecha_creacion": datetime.now(),
            "fecha_completado": None,
            "metadata": metadata or {}
        }
        
        self.tareas.append(tarea)
        return tarea
    
    def listar_tareas(self, 
                      filtro_estado: Optional[str] = None,
                      filtro_prioridad: Optional[str] = None) -> List[Dict]:
        """
        Lista las tareas registradas, opcionalmente filtradas.
        
        Args:
            filtro_estado: Filtrar por estado (pendiente, completado)
            filtro_prioridad: Filtrar por prioridad
            
        Returns:
            Lista de tareas que cumplen los filtros
        """
        tareas_filtradas = self.tareas
        
        if filtro_estado:
            tareas_filtradas = [t for t in tareas_filtradas 
                               if t["estado"] == filtro_estado]
        
        if filtro_prioridad:
            tareas_filtradas = [t for t in tareas_filtradas 
                               if t["prioridad"] == filtro_prioridad]
        
        return tareas_filtradas
    
    def completar_tarea(self, tarea_id: str) -> bool:
        """
        Marca una tarea como completada.
        
        Args:
            tarea_id: ID de la tarea a completar
            
        Returns:
            True si la tarea fue completada exitosamente, False en caso contrario
        """
        for tarea in self.tareas:
            if tarea["id"] == tarea_id:
                tarea["estado"] = "completado"
                tarea["fecha_completado"] = datetime.now()
                return True
        return False
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas sobre las tareas del módulo.
        
        Returns:
            Dict con estadísticas: total, pendientes, completadas, por prioridad
        """
        total = len(self.tareas)
        pendientes = len([t for t in self.tareas if t["estado"] == "pendiente"])
        completadas = len([t for t in self.tareas if t["estado"] == "completado"])
        
        por_prioridad = {
            "baja": len([t for t in self.tareas if t["prioridad"] == "baja"]),
            "media": len([t for t in self.tareas if t["prioridad"] == "media"]),
            "alta": len([t for t in self.tareas if t["prioridad"] == "alta"]),
            "critica": len([t for t in self.tareas if t["prioridad"] == "critica"])
        }
        
        return {
            "total": total,
            "pendientes": pendientes,
            "completadas": completadas,
            "por_prioridad": por_prioridad,
            "modulo_activo": self._activo,
            "fecha_creacion_modulo": format_timestamp(self.fecha_creacion)
        }
    
    def obtener_info(self) -> Dict:
        """
        Obtiene información general del módulo.
        
        Returns:
            Dict con información del módulo
        """
        return {
            "nombre": self.nombre,
            "id": self.id,
            "fecha_creacion": format_timestamp(self.fecha_creacion),
            "activo": self._activo,
            "total_tareas": len(self.tareas)
        }
    
    def activar(self) -> None:
        """Activa el módulo."""
        self._activo = True
    
    def desactivar(self) -> None:
        """Desactiva el módulo."""
        self._activo = False
    
    def esta_activo(self) -> bool:
        """
        Verifica si el módulo está activo.
        
        Returns:
            True si el módulo está activo, False en caso contrario
        """
        return self._activo
