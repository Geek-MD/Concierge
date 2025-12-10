"""
Utilidades y funciones auxiliares para el módulo de servicios sanitarios.
"""

import uuid
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path
from urllib.parse import urljoin


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


def verificar_redireccion_url(url: str, timeout: int = 10) -> Optional[str]:
    """
    Verifica la URL a la que redirecciona una página web.
    
    Args:
        url: URL inicial a verificar
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        String con la URL final tras las redirecciones, o None si hay error
    """
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        return response.url
    except Exception as e:
        print(f"Error al verificar redirección: {e}")
        return None


def guardar_json(datos: Dict, ruta_archivo: str) -> bool:
    """
    Guarda datos en un archivo JSON.
    
    Args:
        datos: Diccionario con los datos a guardar
        ruta_archivo: Ruta del archivo donde guardar los datos
        
    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    try:
        ruta = Path(ruta_archivo)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error al guardar JSON: {e}")
        return False


def cargar_json(ruta_archivo: str) -> Optional[Dict]:
    """
    Carga datos desde un archivo JSON.
    
    Args:
        ruta_archivo: Ruta del archivo JSON a cargar
        
    Returns:
        Diccionario con los datos cargados, o None si hay error
    """
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar JSON: {e}")
        return None


def extraer_url_por_texto(url: str, texto_buscar: str, timeout: int = 10) -> Optional[str]:
    """
    Extrae la URL de un enlace en una página HTML buscando por el texto del enlace.
    
    Args:
        url: URL de la página a analizar
        texto_buscar: Texto del enlace a buscar
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        String con la URL absoluta del enlace encontrado, o None si no se encuentra
    """
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar el enlace por texto
        link = soup.find('a', string=lambda text: text and texto_buscar.lower() in text.lower())
        
        if link and hasattr(link, 'get'):
            # Convertir a URL absoluta si es relativa
            href = link.get('href')
            if href and isinstance(href, str):
                url_absoluta = urljoin(url, href)
                return url_absoluta
        
        return None
    except Exception as e:
        print(f"Error al extraer URL por texto: {e}")
        return None
