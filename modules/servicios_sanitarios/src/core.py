"""
Core functionality for Servicios Sanitarios module.

Este archivo contiene la lógica principal del módulo de servicios sanitarios.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from .utils import (
    generate_id, 
    format_timestamp, 
    verificar_redireccion_url, 
    guardar_json,
    extraer_url_por_texto,
    extraer_empresas_agua,
    cargar_json,
    descargar_pdf
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
    
    def descargar_pdfs(
        self,
        ruta_json: str = "data/tarifas_empresas.json",
        ruta_pdfs: str = "data/pdfs",
        ruta_registro: str = "data/registro_descargas.json"
    ) -> Dict[str, Any]:
        """
        Descarga PDFs de tarifas desde las URLs almacenadas en el archivo JSON.
        
        Este método monitorea el archivo JSON con las URLs de PDFs y:
        - Si es la primera vez (no existe registro), descarga TODOS los PDFs
        - Si ya existe registro, descarga solo los PDFs NUEVOS
        
        Los PDFs se organizan en carpetas por empresa:
        data/pdfs/Empresa_Nombre/localidad_nombre.pdf
        
        Args:
            ruta_json: Ruta del archivo JSON con las URLs de PDFs
            ruta_pdfs: Directorio base donde guardar los PDFs
            ruta_registro: Ruta del archivo JSON para registrar descargas
            
        Returns:
            Dict con información del resultado:
            - exito: True si la operación fue exitosa
            - total_pdfs: Total de PDFs en el JSON
            - descargados: Cantidad de PDFs descargados
            - fallidos: Cantidad de PDFs que fallaron
            - es_primera_vez: True si es la primera descarga
            - pdfs_descargados: Lista de PDFs descargados exitosamente
            - pdfs_fallidos: Lista de PDFs que fallaron
            - timestamp: Momento de la operación
            - mensaje: Descripción del resultado
        """
        timestamp = datetime.now()
        
        # Cargar datos de URLs desde JSON
        datos_urls = cargar_json(ruta_json)
        if not datos_urls:
            return {
                "exito": False,
                "error": f"No se pudo cargar el archivo JSON: {ruta_json}",
                "timestamp": format_timestamp(timestamp)
            }
        
        # Obtener empresas y sus tarifas
        empresas = datos_urls.get("empresas", [])
        if not empresas:
            return {
                "exito": False,
                "error": "No se encontraron empresas en el archivo JSON",
                "timestamp": format_timestamp(timestamp)
            }
        
        # Cargar registro de descargas previas
        registro_previo = cargar_json(ruta_registro)
        es_primera_vez = registro_previo is None
        
        # Obtener PDFs ya descargados (si existen)
        pdfs_previos = set()
        if not es_primera_vez and registro_previo:
            for pdf_info in registro_previo.get("pdfs_descargados", []):
                pdfs_previos.add(pdf_info["url_pdf"])
        
        # Procesar descargas
        total_pdfs = 0
        pdfs_descargados: List[Dict[str, str]] = []
        pdfs_fallidos: List[Dict[str, str]] = []
        
        for empresa_data in empresas:
            empresa = empresa_data["empresa"]
            # Normalizar nombre de empresa para usar como directorio
            empresa_dir = empresa.replace(" ", "_").replace("/", "_")
            
            for tarifa in empresa_data.get("tarifas", []):
                localidad = tarifa["localidad"]
                url_pdf = tarifa["url_pdf"]
                total_pdfs += 1
                
                # Si no es primera vez, verificar si ya fue descargado
                if not es_primera_vez and url_pdf in pdfs_previos:
                    continue
                
                # Normalizar nombre de localidad para archivo
                localidad_file = localidad.replace(" ", "_").replace("/", "_")
                # PDF va directo en carpeta de empresa: empresa/localidad.pdf
                ruta_pdf = Path(ruta_pdfs) / empresa_dir / f"{localidad_file}.pdf"
                
                # Intentar descargar
                if descargar_pdf(url_pdf, str(ruta_pdf)):
                    pdfs_descargados.append({
                        "empresa": empresa,
                        "localidad": localidad,
                        "url_pdf": url_pdf,
                        "ruta_local": str(ruta_pdf),
                        "timestamp": format_timestamp(timestamp)
                    })
                else:
                    pdfs_fallidos.append({
                        "empresa": empresa,
                        "localidad": localidad,
                        "url_pdf": url_pdf,
                        "error": "Fallo en descarga"
                    })
        
        # Preparar registro actualizado
        pdfs_totales_descargados = []
        if not es_primera_vez and registro_previo:
            # Mantener registros previos
            pdfs_totales_descargados = registro_previo.get("pdfs_descargados", [])
        
        # Agregar nuevos
        pdfs_totales_descargados.extend(pdfs_descargados)
        
        # Guardar registro actualizado
        registro = {
            "ultima_actualizacion": format_timestamp(timestamp),
            "total_pdfs_descargados": len(pdfs_totales_descargados),
            "pdfs_descargados": pdfs_totales_descargados,
            "historial_descargas": [
                {
                    "timestamp": format_timestamp(timestamp),
                    "descargados": len(pdfs_descargados),
                    "fallidos": len(pdfs_fallidos),
                    "es_primera_vez": es_primera_vez
                }
            ] if es_primera_vez else registro_previo.get("historial_descargas", []) + [{
                "timestamp": format_timestamp(timestamp),
                "descargados": len(pdfs_descargados),
                "fallidos": len(pdfs_fallidos),
                "es_primera_vez": False
            }]
        }
        
        guardado = guardar_json(registro, ruta_registro)
        
        return {
            "exito": True,
            "total_pdfs": total_pdfs,
            "descargados": len(pdfs_descargados),
            "fallidos": len(pdfs_fallidos),
            "es_primera_vez": es_primera_vez,
            "pdfs_descargados": pdfs_descargados,
            "pdfs_fallidos": pdfs_fallidos,
            "ruta_pdfs": ruta_pdfs,
            "ruta_registro": ruta_registro,
            "registro_guardado": guardado,
            "timestamp": format_timestamp(timestamp),
            "mensaje": (
                f"Primera descarga: {len(pdfs_descargados)} PDFs descargados" if es_primera_vez else
                f"Descargados {len(pdfs_descargados)} PDFs nuevos" if len(pdfs_descargados) > 0 else
                "No hay PDFs nuevos para descargar"
            )
        }
