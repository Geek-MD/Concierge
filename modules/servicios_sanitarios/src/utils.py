"""
Utilidades y funciones auxiliares para el módulo de servicios sanitarios.
"""

import uuid
from datetime import datetime
from typing import Optional


def generate_id() -> str:
    """
    Genera un ID único para identificar elementos del sistema.
    
    Returns:
        String con un UUID único
    """
    return str(uuid.uuid4())


def format_timestamp(dt: datetime) -> str:
    """
    Formatea un timestamp en formato ISO 8601.
    
    Args:
        dt: Objeto datetime a formatear
        
    Returns:
        String con el timestamp formateado
    """
    return dt.isoformat()


def validar_prioridad(prioridad: str) -> bool:
    """
    Valida que una prioridad sea válida.
    
    Args:
        prioridad: String con la prioridad a validar
        
    Returns:
        True si es válida, False en caso contrario
    """
    return prioridad in ["baja", "media", "alta", "critica"]


def obtener_fecha_actual() -> datetime:
    """
    Obtiene la fecha y hora actuales.
    
    Returns:
        Objeto datetime con la fecha/hora actual
    """
    return datetime.now()


def formatear_duracion(inicio: datetime, fin: Optional[datetime] = None) -> str:
    """
    Calcula y formatea la duración entre dos fechas.
    
    Args:
        inicio: Fecha de inicio
        fin: Fecha de fin (si no se provee, usa la fecha actual)
        
    Returns:
        String con la duración formateada
    """
    if fin is None:
        fin = datetime.now()
    
    duracion = fin - inicio
    
    dias = duracion.days
    segundos = duracion.seconds
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    
    partes = []
    if dias > 0:
        partes.append(f"{dias}d")
    if horas > 0:
        partes.append(f"{horas}h")
    if minutos > 0:
        partes.append(f"{minutos}m")
    if segs > 0 or not partes:
        partes.append(f"{segs}s")
    
    return " ".join(partes)
