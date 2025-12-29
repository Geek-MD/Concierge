"""
Core functionality for Servicios Sanitarios module.

This file contains the main logic of the sanitary services module.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .logger import get_logger
from .utils import (
    cargar_json,
    descargar_pdf,
    extraer_empresas_agua,
    extract_pdf_tables,
    extract_pdf_text,
    extract_pdf_text_with_ocr,
    extraer_url_por_texto,
    format_timestamp,
    generate_id,
    guardar_json,
    get_pdfs_in_folder,
    get_new_pdfs,
    organize_hierarchical_analysis,
    verificar_redireccion_url,
)


class ServiciosSanitarios:
    """
    Main class for managing sanitary services.
    
    This class provides the core functionality of the module, allowing
    automated and efficient management of tasks related to sanitary services.
    """
    
    def __init__(self, nombre: str = "ServiciosSanitarios"):
        """
        Initialize the sanitary services module.
        
        Args:
            nombre: Module identifier name
        """
        self.nombre = nombre
        self.id = generate_id()
        self.fecha_creacion = datetime.now()
        self.tareas: list[dict[str, Any]] = []
        self._activo = True
        self.logger = get_logger('concierge.servicios_sanitarios')
        
        self.logger.info(f"Initialized module: {nombre} (ID: {self.id})")
        
    def agregar_tarea(self, 
                      descripcion: str, 
                      prioridad: str = "media",
                      metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Add a new task to the system.
        
        Args:
            descripcion: Description of the task to be performed
            prioridad: Priority level (baja, media, alta, critica)
            metadata: Additional information about the task
            
        Returns:
            dict[str, Any] with the created task information
            
        Raises:
            ValueError: If the priority is not valid
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
                      filtro_prioridad: Optional[str] = None) -> list[dict[str, Any]]:
        """
        List registered tasks, optionally filtered.
        
        Args:
            filtro_estado: Filter by state (pendiente, completado)
            filtro_prioridad: Filter by priority
            
        Returns:
            List of tasks that meet the filters
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
        Mark a task as completed.
        
        Args:
            tarea_id: ID of the task to complete
            
        Returns:
            True if the task was completed successfully, False otherwise
        """
        for tarea in self.tareas:
            if tarea["id"] == tarea_id:
                tarea["estado"] = "completado"
                tarea["fecha_completado"] = datetime.now()
                return True
        return False
    
    def obtener_estadisticas(self) -> dict[str, Any]:
        """
        Get statistics about the module's tasks.
        
        Returns:
            dict[str, Any] with statistics: total, pending, completed, by priority
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
    
    def obtener_info(self) -> dict[str, Any]:
        """
        Get general module information.
        
        Returns:
            dict[str, Any] with module information
        """
        return {
            "nombre": self.nombre,
            "id": self.id,
            "fecha_creacion": format_timestamp(self.fecha_creacion),
            "activo": self._activo,
            "total_tareas": len(self.tareas)
        }
    
    def activar(self) -> None:
        """Activate the module."""
        self._activo = True
    
    def desactivar(self) -> None:
        """Deactivate the module."""
        self._activo = False
    
    def esta_activo(self) -> bool:
        """
        Check if the module is active.
        
        Returns:
            True if the module is active, False otherwise
        """
        return self._activo
    
    def verificar_siss(self, ruta_salida: str = "data/siss_url.json") -> dict[str, Any]:
        """
        Verify the redirection URL of the SISS website and save it to JSON.
        
        This method accesses https://www.siss.gob.cl, detects which URL it
        redirects to, extracts the URL of the "Tarifas vigentes" link and saves
        this information in a JSON file with timestamp only if it's the
        first time or if any URL has changed.
        
        Args:
            ruta_salida: Path to the JSON file where to save the URL
            
        Returns:
            dict[str, Any] with result information (url, timestamp, saved, changes)
        """
        self.logger.info("Starting SISS verification")
        url_siss = "https://www.siss.gob.cl"
        timestamp = datetime.now()
        
        # Check redirection
        url_final = verificar_redireccion_url(url_siss)
        
        if url_final is None:
            self.logger.error("Failed to get SISS redirection URL")
            return {
                "success": False,
                "url_original": url_siss,
                "url_final": None,
                "url_tarifas_vigentes": None,
                "timestamp": format_timestamp(timestamp),
                "error": "No se pudo obtener la URL de redirección"
            }
        
        # Extract URL of "Tarifas vigentes"
        url_tarifas = extraer_url_por_texto(url_final, "Tarifas vigentes")
        
        # Load previous data if they exist
        datos_previos = cargar_json(ruta_salida)
        
        # Check if there are changes
        is_first_time = datos_previos is None
        url_final_cambio = False
        url_tarifas_cambio = False
        
        if datos_previos:
            url_final_previa = datos_previos.get("url_final")
            url_tarifas_previa = datos_previos.get("url_tarifas_vigentes")
            
            url_final_cambio = url_final_previa != url_final
            url_tarifas_cambio = url_tarifas_previa != url_tarifas
        
        hay_cambios = is_first_time or url_final_cambio or url_tarifas_cambio
        
        # Only save if there are changes
        guardado = False
        if hay_cambios:
            # Prepare history
            historial = []
            if datos_previos and "historial" in datos_previos:
                historial = datos_previos["historial"]
            
            # Add current entry to history if not the first time
            if not is_first_time and datos_previos:
                entrada_historial = {
                    "url_final": datos_previos.get("url_final"),
                    "url_tarifas_vigentes": datos_previos.get("url_tarifas_vigentes"),
                    "timestamp": datos_previos.get("timestamp")
                }
                historial.append(entrada_historial)
            
            # Prepare data to save
            datos = {
                "url_original": url_siss,
                "url_final": url_final,
                "url_tarifas_vigentes": url_tarifas,
                "timestamp": format_timestamp(timestamp),
                "verificado": True,
                "historial": historial
            }
            
            # Save to JSON
            guardado = guardar_json(datos, ruta_salida)
            if guardado:
                if is_first_time:
                    self.logger.info(f"First SISS verification saved to {ruta_salida}")
                else:
                    self.logger.info(f"SISS changes detected and saved to {ruta_salida}")
        else:
            self.logger.debug("No changes detected in SISS URLs")
        
        self.logger.info(f"SISS verification completed: {url_final}")
        return {
            "success": True,
            "url_original": url_siss,
            "url_final": url_final,
            "url_tarifas_vigentes": url_tarifas,
            "timestamp": format_timestamp(timestamp),
            "archivo": ruta_salida,
            "guardado": guardado,
            "is_first_time": is_first_time,
            "cambios": {
                "url_final": url_final_cambio,
                "url_tarifas_vigentes": url_tarifas_cambio
            },
            "message": (
                "Primera verificación guardada" if is_first_time else
                "Cambios detectados y guardados" if hay_cambios else
                "Sin cambios, no se guardó"
            )
        }
    
    def monitorear_tarifas_vigentes(
        self, 
        url_tarifas: Optional[str] = None,
        ruta_salida: str = "data/tarifas_empresas.json"
    ) -> dict[str, Any]:
        """
        Monitor the "Tarifas vigentes" URL and extract water companies data.
        
        This method accesses the current tariffs URL, extracts information from each
        water company (name, localities, PDF URLs) and saves the data to JSON
        only if it's the first time or if changes are detected.
        
        Args:
            url_tarifas: URL of the current tariffs page. If not provided,
                        it is automatically obtained using verificar_siss()
            ruta_salida: Path to the JSON file where to save the data
            
        Returns:
            dict[str, Any] with result information:
            - success: True if operation was successful
            - url_tarifas: URL of the current tariffs page
            - empresas: List of companies and their data
            - timestamp: Moment of verification
            - archivo: Output file path
            - guardado: True if changes were saved
            - is_first_time: True if it's the first execution
            - cambios_detectados: True if there were changes since last verification
            - message: Description of the result
        """
        timestamp = datetime.now()
        
        # If URL is not provided, obtain it from verificar_siss
        if url_tarifas is None:
            resultado_siss = self.verificar_siss()
            if not resultado_siss["success"]:
                return {
                    "success": False,
                    "url_tarifas": None,
                    "empresas": [],
                    "timestamp": format_timestamp(timestamp),
                    "error": "No se pudo obtener URL de tarifas vigentes"
                }
            url_tarifas = resultado_siss["url_tarifas_vigentes"]
            
            if not url_tarifas:
                return {
                    "success": False,
                    "url_tarifas": None,
                    "empresas": [],
                    "timestamp": format_timestamp(timestamp),
                    "error": "URL de tarifas vigentes no disponible"
                }
        
        # Extract water companies data
        empresas = extraer_empresas_agua(url_tarifas)
        
        if not empresas:
            return {
                "success": False,
                "url_tarifas": url_tarifas,
                "empresas": [],
                "timestamp": format_timestamp(timestamp),
                "error": "No se pudieron extraer datos de empresas"
            }
        
        # Load previous data if they exist
        datos_previos = cargar_json(ruta_salida)
        
        # Check if there are changes
        is_first_time = datos_previos is None
        cambios_detectados = False
        
        if not is_first_time and datos_previos is not None:
            # Compare current data with previous ones
            empresas_previas = datos_previos.get("empresas", [])
            
            # Convert to comparable format (serializable)
            empresas_str_actual = str(sorted(
                [(e["empresa"], sorted(str(t) for t in e["tarifas"])) 
                 for e in empresas]
            ))
            empresas_str_previa = str(sorted(
                [(e["empresa"], sorted(str(t) for t in e["tarifas"])) 
                 for e in empresas_previas]
            ))
            
            cambios_detectados = empresas_str_actual != empresas_str_previa
        
        hay_cambios = is_first_time or cambios_detectados
        
        # Only save if there are changes
        guardado = False
        if hay_cambios:
            # Prepare history
            historial: list[dict[str, Any]] = []
            if datos_previos and "historial" in datos_previos:
                historial = datos_previos["historial"]
            
            # Add current entry to history if not the first time
            if not is_first_time and datos_previos:
                entrada_historial = {
                    "empresas": datos_previos.get("empresas", []),
                    "timestamp": datos_previos.get("timestamp"),
                    "total_companies": datos_previos.get("total_companies", 0)
                }
                historial.append(entrada_historial)
            
            # Prepare data to save
            datos = {
                "url_tarifas": url_tarifas,
                "empresas": empresas,
                "total_companies": len(empresas),
                "timestamp": format_timestamp(timestamp),
                "verificado": True,
                "historial": historial
            }
            
            # Save to JSON
            guardado = guardar_json(datos, ruta_salida)
        
        return {
            "success": True,
            "url_tarifas": url_tarifas,
            "empresas": empresas,
            "total_companies": len(empresas),
            "timestamp": format_timestamp(timestamp),
            "archivo": ruta_salida,
            "guardado": guardado,
            "is_first_time": is_first_time,
            "cambios_detectados": cambios_detectados,
            "message": (
                "Primera verificación guardada" if is_first_time else
                "Cambios detectados y guardados" if cambios_detectados else
                "Sin cambios, no se guardó"
            )
        }
    
    def descargar_pdfs(
        self,
        ruta_json: str = "data/tarifas_empresas.json",
        pdfs_path: str = "data/pdfs",
        registry_path: str = "data/registro_descargas.json"
    ) -> dict[str, Any]:
        """
        Download tariff PDFs from URLs stored in the JSON file.
        
        This method monitors the JSON file with PDF URLs and:
        - If it's the first time (no registry exists), downloads ALL PDFs
        - If a registry already exists, downloads only NEW PDFs
        
        PDFs are organized in folders by company:
        data/pdfs/Company_Name/locality_name.pdf
        
        Args:
            ruta_json: Path to the JSON file with PDF URLs
            pdfs_path: Base directory where to save PDFs
            registry_path: Path to the JSON file to register downloads
            
        Returns:
            dict[str, Any] with result information:
            - success: True if operation was successful
            - total_pdfs: Total PDFs in the JSON
            - descargados: Number of PDFs downloaded
            - failed: Number of PDFs that failed
            - is_first_time: True if it's the first download
            - pdfs_descargados: List of successfully downloaded PDFs
            - failed_pdfs: List of PDFs that failed
            - timestamp: Moment of the operation
            - message: Description of the result
        """
        self.logger.info("Starting PDF downloads")
        timestamp = datetime.now()
        
        # Load URL data from JSON
        datos_urls = cargar_json(ruta_json)
        if not datos_urls:
            return {
                "success": False,
                "error": f"No se pudo cargar el archivo JSON: {ruta_json}",
                "timestamp": format_timestamp(timestamp)
            }
        
        # Get companies and their tariffs
        empresas = datos_urls.get("empresas", [])
        if not empresas:
            return {
                "success": False,
                "error": "No se encontraron empresas en el archivo JSON",
                "timestamp": format_timestamp(timestamp)
            }
        
        # Load previous download registry
        registro_previo = cargar_json(registry_path)
        is_first_time = registro_previo is None
        
        # Get already downloaded PDFs (if they exist)
        pdfs_previos = set()
        if not is_first_time and registro_previo:
            for pdf_info in registro_previo.get("pdfs_descargados", []):
                pdfs_previos.add(pdf_info["url_pdf"])
        
        # Process downloads
        total_pdfs = 0
        pdfs_descargados: list[dict[str, str]] = []
        failed_pdfs: list[dict[str, str]] = []
        
        for empresa_data in empresas:
            empresa = empresa_data["empresa"]
            # Normalize company name to use as directory
            empresa_dir = empresa.replace(" ", "_").replace("/", "_")
            
            for tarifa in empresa_data.get("tarifas", []):
                localidad = tarifa["localidad"]
                url_pdf = tarifa["url_pdf"]
                total_pdfs += 1
                
                # If not first time, check if already downloaded
                if not is_first_time and url_pdf in pdfs_previos:
                    continue
                
                # Normalize locality name for file
                localidad_file = localidad.replace(" ", "_").replace("/", "_")
                # PDF goes directly in company folder: company/locality.pdf
                ruta_pdf = Path(pdfs_path) / empresa_dir / f"{localidad_file}.pdf"
                
                # Try to download
                if descargar_pdf(url_pdf, str(ruta_pdf)):
                    pdfs_descargados.append({
                        "empresa": empresa,
                        "localidad": localidad,
                        "url_pdf": url_pdf,
                        "ruta_local": str(ruta_pdf),
                        "timestamp": format_timestamp(timestamp)
                    })
                else:
                    failed_pdfs.append({
                        "empresa": empresa,
                        "localidad": localidad,
                        "url_pdf": url_pdf,
                        "error": "Fallo en descarga"
                    })
        
        # Prepare updated registry
        pdfs_totales_descargados = []
        if not is_first_time and registro_previo:
            # Keep previous records
            pdfs_totales_descargados = registro_previo.get("pdfs_descargados", [])
        
        # Add new ones
        pdfs_totales_descargados.extend(pdfs_descargados)
        
        # Save updated registry
        registro = {
            "ultima_actualizacion": format_timestamp(timestamp),
            "total_pdfs_descargados": len(pdfs_totales_descargados),
            "pdfs_descargados": pdfs_totales_descargados,
            "historial_descargas": [
                {
                    "timestamp": format_timestamp(timestamp),
                    "descargados": len(pdfs_descargados),
                    "failed": len(failed_pdfs),
                    "is_first_time": is_first_time
                }
            ] if is_first_time else registro_previo.get("historial_descargas", []) + [{
                "timestamp": format_timestamp(timestamp),
                "descargados": len(pdfs_descargados),
                "failed": len(failed_pdfs),
                "is_first_time": False
            }]
        }
        
        guardado = guardar_json(registro, registry_path)
        
        return {
            "success": True,
            "total_pdfs": total_pdfs,
            "descargados": len(pdfs_descargados),
            "failed": len(failed_pdfs),
            "is_first_time": is_first_time,
            "pdfs_descargados": pdfs_descargados,
            "failed_pdfs": failed_pdfs,
            "pdfs_path": pdfs_path,
            "registry_path": registry_path,
            "registry_saved": guardado,
            "timestamp": format_timestamp(timestamp),
            "message": (
                f"Primera descarga: {len(pdfs_descargados)} PDFs descargados" if is_first_time else
                f"Descargados {len(pdfs_descargados)} PDFs nuevos" if len(pdfs_descargados) > 0 else
                "No hay PDFs nuevos para descargar"
            )
        }
    
    def analyze_pdfs(
        self,
        pdfs_path: str = "data/pdfs",
        registry_path: str = "data/registro_analisis.json",
        use_ocr: bool = False,
        extract_tables: bool = True,
        only_new: bool = True
    ) -> dict[str, Any]:
        """
        Analyze tariff PDFs extracting their text content and tables.
        
        This method monitors the PDFs folder and:
        - If only_new=True (default), analyzes only new PDFs
        - If only_new=False, analyzes all PDFs
        - If extract_tables=True (default), detects and extracts tables with borders
        - Can use OCR for scanned PDFs if use_ocr=True
        
        Args:
            pdfs_path: Directory where PDFs are located
            registry_path: Path to JSON file to register analyses
            use_ocr: If True, tries OCR for scanned PDFs
            extract_tables: If True, extracts tables detecting borders and structure
            only_new: If True, only analyzes non-analyzed PDFs
            
        Returns:
            dict[str, Any] with result information:
            - success: True if operation was successful
            - total_pdfs: Total PDFs found
            - analyzed: Number of PDFs analyzed
            - failed: Number of PDFs that failed
            - is_first_time: True if it is the first analysis
            - analyzed_pdfs: List of analyzed PDFs with their content
            - failed_pdfs: List of PDFs that failed
            - timestamp: Moment of the operation
            - message: Description of the result
        """
        self.logger.info("Starting PDF analysis")
        timestamp = datetime.now()
        
        # Get list of PDFs to analyze
        if only_new:
            pdfs_to_analyze = get_new_pdfs(pdfs_path, registry_path, recursivo=True)
        else:
            pdfs_to_analyze = get_pdfs_in_folder(pdfs_path, recursivo=True)
        
        if not pdfs_to_analyze:
            return {
                "success": True,
                "total_pdfs": 0,
                "analyzed": 0,
                "failed": 0,
                "is_first_time": False,
                "analyzed_pdfs": [],
                "failed_pdfs": [],
                "timestamp": format_timestamp(timestamp),
                "message": "No hay PDFs para analizar"
            }
        
        # Load previous registry
        registro_previo = cargar_json(registry_path)
        is_first_time = registro_previo is None
        
        # Process analysis
        analyzed_pdfs: list[dict[str, Any]] = []
        failed_pdfs: list[dict[str, str]] = []
        
        for ruta_pdf in pdfs_to_analyze:
            # Get file information
            pdf_file_path = Path(ruta_pdf)
            size_kb = pdf_file_path.stat().st_size / 1024
            
            # Decide extraction method
            if extract_tables:
                # Use pdfplumber to detect tables and borders
                extraction_result = extract_pdf_tables(ruta_pdf)
                
                if extraction_result:
                    texto = extraction_result["texto"]
                    tablas = extraction_result["tablas"]
                    
                    # Process table structure
                    processed_tables = []
                    total_conceptos = 0
                    total_secciones = 0
                    
                    for t in tablas:
                        estructura = t.get("estructura", {})
                        total_conceptos += estructura.get("total_concepts", 0)
                        total_secciones += len(estructura.get("sections", []))
                        
                        table_info = {
                            "page": t["page"],
                            "table_number": t["table_number"],
                            "num_rows": len(t["filas"]),
                            "structure_type": estructura.get("tipo", "desconocida"),
                            "total_concepts": estructura.get("total_concepts", 0),
                            "total_sections": len(estructura.get("sections", [])),
                            "preview": t["texto_formateado"][:200] + "..." if len(t["texto_formateado"]) > 200 else t["texto_formateado"]
                        }
                        
                        # Add sections if they exist
                        if estructura.get("sections"):
                            table_info["sections"] = [
                                {
                                    "name": sec["nombre_seccion"],
                                    "num_data": len(sec["datos"]),
                                    "concepts": [d["concept"] for d in sec["datos"][:3]]  # First 3
                                }
                                for sec in estructura.get("sections", [])
                            ]
                        
                        # Add direct data if they exist
                        if estructura.get("direct_data"):
                            table_info["direct_data"] = [
                                {
                                    "concept": d["concept"],
                                    "value": d["value"]
                                }
                                for d in estructura.get("direct_data", [])[:5]  # First 5
                            ]
                        
                        processed_tables.append(table_info)
                    
                    analyzed_pdfs.append({
                        "ruta_pdf": ruta_pdf,
                        "filename": pdf_file_path.name,
                        "folder": pdf_file_path.parent.name,
                        "size_kb": round(size_kb, 2),
                        "total_paginas": extraction_result["total_paginas"],
                        "total_tablas": extraction_result["total_tablas"],
                        "total_concepts": total_conceptos,
                        "total_sections": total_secciones,
                        "longitud_texto": len(texto),
                        "texto_extraido": texto[:1000] + "..." if len(texto) > 1000 else texto,
                        "full_text_available": True,
                        "extracted_tables": len(tablas),
                        "tablas": processed_tables,
                        "metodo_extraccion": "pdfplumber (con detección de tablas y estructura)",
                        "used_ocr": False,
                        "timestamp": format_timestamp(timestamp)
                    })
                elif use_ocr:
                    # If pdfplumber fails, try OCR
                    texto = extract_pdf_text_with_ocr(ruta_pdf)
                    if texto:
                        analyzed_pdfs.append({
                            "ruta_pdf": ruta_pdf,
                            "filename": pdf_file_path.name,
                            "folder": pdf_file_path.parent.name,
                            "size_kb": round(size_kb, 2),
                            "longitud_texto": len(texto),
                            "texto_extraido": texto[:1000] + "..." if len(texto) > 1000 else texto,
                            "full_text_available": True,
                            "metodo_extraccion": "OCR (pytesseract)",
                            "used_ocr": True,
                            "timestamp": format_timestamp(timestamp)
                        })
                    else:
                        failed_pdfs.append({
                            "ruta_pdf": ruta_pdf,
                            "filename": pdf_file_path.name,
                            "error": "No se pudo extraer texto (ni con pdfplumber ni con OCR)"
                        })
                else:
                    failed_pdfs.append({
                        "ruta_pdf": ruta_pdf,
                        "filename": pdf_file_path.name,
                        "error": "No se pudo extraer texto con pdfplumber"
                    })
            else:
                # Use pypdf for simple extraction
                texto = extract_pdf_text(ruta_pdf, use_ocr=use_ocr)
                
                if texto:
                    analyzed_pdfs.append({
                        "ruta_pdf": ruta_pdf,
                        "filename": pdf_file_path.name,
                        "folder": pdf_file_path.parent.name,
                        "size_kb": round(size_kb, 2),
                        "longitud_texto": len(texto),
                        "texto_extraido": texto[:1000] + "..." if len(texto) > 1000 else texto,
                        "full_text_available": True,
                        "metodo_extraccion": "pypdf (sin detección de tablas)",
                        "used_ocr": use_ocr,
                        "timestamp": format_timestamp(timestamp)
                    })
                else:
                    failed_pdfs.append({
                        "ruta_pdf": ruta_pdf,
                        "filename": pdf_file_path.name,
                        "error": "No se pudo extraer texto"
                    })
        
        # Prepare updated registry with hierarchical structure
        total_analyzed_pdfs = []
        if not is_first_time and registro_previo:
            # Keep previous records
            total_analyzed_pdfs = registro_previo.get("analyzed_pdfs", [])
        
        # Add new ones
        total_analyzed_pdfs.extend(analyzed_pdfs)
        
        # Organize in hierarchical structure by company and locality
        hierarchical_structure = organize_hierarchical_analysis(total_analyzed_pdfs)
        
        # Save registry with hierarchical structure
        registro = {
            "ultima_actualizacion": format_timestamp(timestamp),
            "total_analyzed_pdfs": len(total_analyzed_pdfs),
            "hierarchical_structure": hierarchical_structure,
            "configuration": {
                "use_ocr": use_ocr,
                "extract_tables": extract_tables,
                "only_new": only_new
            },
            "analysis_history": [
                {
                    "timestamp": format_timestamp(timestamp),
                    "analyzed": len(analyzed_pdfs),
                    "failed": len(failed_pdfs),
                    "is_first_time": is_first_time,
                    "used_ocr": use_ocr,
                    "extract_tables": extract_tables
                }
            ] if is_first_time else registro_previo.get("analysis_history", []) + [{
                "timestamp": format_timestamp(timestamp),
                "analyzed": len(analyzed_pdfs),
                "failed": len(failed_pdfs),
                "is_first_time": False,
                "used_ocr": use_ocr,
                "extract_tables": extract_tables
            }],
            # Keep flat list for compatibility
            "analyzed_pdfs": total_analyzed_pdfs
        }
        
        guardado = guardar_json(registro, registry_path)
        
        return {
            "success": True,
            "total_pdfs": len(pdfs_to_analyze),
            "analyzed": len(analyzed_pdfs),
            "failed": len(failed_pdfs),
            "is_first_time": is_first_time,
            "analyzed_pdfs": analyzed_pdfs,
            "failed_pdfs": failed_pdfs,
            "hierarchical_structure": hierarchical_structure,
            "pdfs_path": pdfs_path,
            "registry_path": registry_path,
            "registry_saved": guardado,
            "used_ocr": use_ocr,
            "extract_tables": extract_tables,
            "timestamp": format_timestamp(timestamp),
            "message": (
                f"Primer análisis: {len(analyzed_pdfs)} PDFs analyzed" if is_first_time else
                f"Analizados {len(analyzed_pdfs)} PDFs nuevos" if len(analyzed_pdfs) > 0 else
                "No hay PDFs nuevos para analizar"
            )
        }
