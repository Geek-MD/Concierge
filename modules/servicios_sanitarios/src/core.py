"""
Core functionality for Servicios Sanitarios module.

Este archivo contiene la lógica principal del módulo de servicios sanitarios.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .utils import (
    generate_id, 
    format_timestamp, 
    verificar_redireccion_url, 
    guardar_json,
    extraer_url_por_texto,
    extraer_empresas_agua,
    cargar_json
)


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
        self.tareas: List[Dict] = []
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
    
    def verificar_siss(self, ruta_salida: str = "data/siss_url.json") -> Dict:
        """
        Verifica la URL de redirección de la web de SISS y la guarda en JSON.
        
        Este método accede a https://www.siss.gob.cl, detecta a qué URL 
        redirecciona, extrae la URL del enlace "Tarifas vigentes" y guarda
        dicha información en un archivo JSON con timestamp solo si es la
        primera vez o si alguna URL ha cambiado.
        
        Args:
            ruta_salida: Ruta del archivo JSON donde guardar la URL
            
        Returns:
            Dict con información del resultado (url, timestamp, guardado, cambios)
        """
        url_siss = "https://www.siss.gob.cl"
        timestamp = datetime.now()
        
        # Verificar redirección
        url_final = verificar_redireccion_url(url_siss)
        
        if url_final is None:
            return {
                "exito": False,
                "url_original": url_siss,
                "url_final": None,
                "url_tarifas_vigentes": None,
                "timestamp": format_timestamp(timestamp),
                "error": "No se pudo obtener la URL de redirección"
            }
        
        # Extraer URL de "Tarifas vigentes"
        url_tarifas = extraer_url_por_texto(url_final, "Tarifas vigentes")
        
        # Cargar datos previos si existen
        datos_previos = cargar_json(ruta_salida)
        
        # Verificar si hay cambios
        es_primera_vez = datos_previos is None
        url_final_cambio = False
        url_tarifas_cambio = False
        
        if datos_previos:
            url_final_previa = datos_previos.get("url_final")
            url_tarifas_previa = datos_previos.get("url_tarifas_vigentes")
            
            url_final_cambio = url_final_previa != url_final
            url_tarifas_cambio = url_tarifas_previa != url_tarifas
        
        hay_cambios = es_primera_vez or url_final_cambio or url_tarifas_cambio
        
        # Solo guardar si hay cambios
        guardado = False
        if hay_cambios:
            # Preparar historial
            historial = []
            if datos_previos and "historial" in datos_previos:
                historial = datos_previos["historial"]
            
            # Agregar entrada actual al historial si no es la primera vez
            if not es_primera_vez and datos_previos:
                entrada_historial = {
                    "url_final": datos_previos.get("url_final"),
                    "url_tarifas_vigentes": datos_previos.get("url_tarifas_vigentes"),
                    "timestamp": datos_previos.get("timestamp")
                }
                historial.append(entrada_historial)
            
            # Preparar datos para guardar
            datos = {
                "url_original": url_siss,
                "url_final": url_final,
                "url_tarifas_vigentes": url_tarifas,
                "timestamp": format_timestamp(timestamp),
                "verificado": True,
                "historial": historial
            }
            
            # Guardar en JSON
            guardado = guardar_json(datos, ruta_salida)
        
        return {
            "exito": True,
            "url_original": url_siss,
            "url_final": url_final,
            "url_tarifas_vigentes": url_tarifas,
            "timestamp": format_timestamp(timestamp),
            "archivo": ruta_salida,
            "guardado": guardado,
            "es_primera_vez": es_primera_vez,
            "cambios": {
                "url_final": url_final_cambio,
                "url_tarifas_vigentes": url_tarifas_cambio
            },
            "mensaje": (
                "Primera verificación guardada" if es_primera_vez else
                "Cambios detectados y guardados" if hay_cambios else
                "Sin cambios, no se guardó"
            )
        }
    
    def monitorear_tarifas_vigentes(
        self, 
        url_tarifas: Optional[str] = None,
        ruta_salida: str = "data/tarifas_empresas.json"
    ) -> Dict[str, Any]:
        """
        Monitorea la URL de "Tarifas vigentes" y extrae datos de empresas de agua.
        
        Este método accede a la URL de tarifas vigentes, extrae información de cada
        empresa de agua (nombre, localidades, URLs de PDFs) y guarda los datos en JSON
        solo si es la primera vez o si hay cambios detectados.
        
        Args:
            url_tarifas: URL de la página de tarifas vigentes. Si no se provee,
                        se obtiene automáticamente usando verificar_siss()
            ruta_salida: Ruta del archivo JSON donde guardar los datos
            
        Returns:
            Dict con información del resultado:
            - exito: True si la operación fue exitosa
            - url_tarifas: URL de la página de tarifas vigentes
            - empresas: Lista de empresas y sus datos
            - timestamp: Momento de la verificación
            - archivo: Ruta del archivo de salida
            - guardado: True si se guardaron cambios
            - es_primera_vez: True si es la primera ejecución
            - cambios_detectados: True si hubo cambios desde última verificación
            - mensaje: Descripción del resultado
        """
        timestamp = datetime.now()
        
        # Si no se provee URL, obtenerla desde verificar_siss
        if url_tarifas is None:
            resultado_siss = self.verificar_siss()
            if not resultado_siss["exito"]:
                return {
                    "exito": False,
                    "url_tarifas": None,
                    "empresas": [],
                    "timestamp": format_timestamp(timestamp),
                    "error": "No se pudo obtener URL de tarifas vigentes"
                }
            url_tarifas = resultado_siss["url_tarifas_vigentes"]
            
            if not url_tarifas:
                return {
                    "exito": False,
                    "url_tarifas": None,
                    "empresas": [],
                    "timestamp": format_timestamp(timestamp),
                    "error": "URL de tarifas vigentes no disponible"
                }
        
        # Extraer datos de empresas de agua
        empresas = extraer_empresas_agua(url_tarifas)
        
        if not empresas:
            return {
                "exito": False,
                "url_tarifas": url_tarifas,
                "empresas": [],
                "timestamp": format_timestamp(timestamp),
                "error": "No se pudieron extraer datos de empresas"
            }
        
        # Cargar datos previos si existen
        datos_previos = cargar_json(ruta_salida)
        
        # Verificar si hay cambios
        es_primera_vez = datos_previos is None
        cambios_detectados = False
        
        if not es_primera_vez and datos_previos is not None:
            # Comparar datos actuales con previos
            empresas_previas = datos_previos.get("empresas", [])
            
            # Convertir a formato comparable (serializable)
            empresas_str_actual = str(sorted(
                [(e["empresa"], sorted(str(t) for t in e["tarifas"])) 
                 for e in empresas]
            ))
            empresas_str_previa = str(sorted(
                [(e["empresa"], sorted(str(t) for t in e["tarifas"])) 
                 for e in empresas_previas]
            ))
            
            cambios_detectados = empresas_str_actual != empresas_str_previa
        
        hay_cambios = es_primera_vez or cambios_detectados
        
        # Solo guardar si hay cambios
        guardado = False
        if hay_cambios:
            # Preparar historial
            historial: List[Dict[str, Any]] = []
            if datos_previos and "historial" in datos_previos:
                historial = datos_previos["historial"]
            
            # Agregar entrada actual al historial si no es la primera vez
            if not es_primera_vez and datos_previos:
                entrada_historial = {
                    "empresas": datos_previos.get("empresas", []),
                    "timestamp": datos_previos.get("timestamp"),
                    "total_empresas": datos_previos.get("total_empresas", 0)
                }
                historial.append(entrada_historial)
            
            # Preparar datos para guardar
            datos = {
                "url_tarifas": url_tarifas,
                "empresas": empresas,
                "total_empresas": len(empresas),
                "timestamp": format_timestamp(timestamp),
                "verificado": True,
                "historial": historial
            }
            
            # Guardar en JSON
            guardado = guardar_json(datos, ruta_salida)
        
        return {
            "exito": True,
            "url_tarifas": url_tarifas,
            "empresas": empresas,
            "total_empresas": len(empresas),
            "timestamp": format_timestamp(timestamp),
            "archivo": ruta_salida,
            "guardado": guardado,
            "es_primera_vez": es_primera_vez,
            "cambios_detectados": cambios_detectados,
            "mensaje": (
                "Primera verificación guardada" if es_primera_vez else
                "Cambios detectados y guardados" if cambios_detectados else
                "Sin cambios, no se guardó"
            )
        }
