"""
Utilidades y funciones auxiliares para el módulo de servicios sanitarios.
"""

import uuid
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, Dict, List, Any
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


def extraer_nombre_empresa(texto: str) -> Optional[str]:
    """
    Extrae el nombre de la empresa de agua desde un texto con formato "Empresa - Texto".
    
    Args:
        texto: Texto que contiene el nombre de la empresa y descripción
        
    Returns:
        String con el nombre de la empresa (antes del guión), o None si no se encuentra
        
    Examples:
        >>> extraer_nombre_empresa("Aguas Andinas - Tarifas vigentes")
        "Aguas Andinas"
    """
    try:
        if not texto or not isinstance(texto, str):
            return None
        
        # Buscar el guión y extraer texto antes de él
        if " - " in texto:
            nombre = texto.split(" - ")[0].strip()
            return nombre if nombre else None
        
        # Si no hay guión, devolver el texto completo limpio
        return texto.strip() if texto.strip() else None
    except Exception as e:
        print(f"Error al extraer nombre de empresa: {e}")
        return None


def extraer_datos_tabla_tarifas(
    html_content: str, 
    base_url: str
) -> List[Dict[str, Any]]:
    """
    Extrae datos de una tabla HTML de tarifas de agua.
    
    Busca tablas con columnas "Localidades" y "Tarifa vigente", y extrae
    las filas que tienen datos en ambas columnas. De la columna "Tarifa vigente"
    extrae la URL del archivo PDF.
    
    Args:
        html_content: Contenido HTML de la página
        base_url: URL base para resolver URLs relativas
        
    Returns:
        Lista de diccionarios con los datos extraídos, cada uno con:
        - localidad: Nombre de la localidad
        - url_pdf: URL absoluta del archivo PDF de la tarifa
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        datos_extraidos: List[Dict[str, Any]] = []
        
        # Buscar todas las tablas
        tablas = soup.find_all('table')
        
        for tabla in tablas:
            # Buscar encabezados de la tabla
            headers = []
            header_row = tabla.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Verificar si tiene las columnas requeridas
            if not headers:
                continue
                
            # Buscar índices de las columnas (case-insensitive)
            idx_localidades = -1
            idx_tarifa = -1
            
            for i, header in enumerate(headers):
                header_lower = header.lower()
                if 'localidad' in header_lower:
                    idx_localidades = i
                if 'tarifa' in header_lower and 'vigente' in header_lower:
                    idx_tarifa = i
            
            # Si no se encuentran ambas columnas, probar con la siguiente tabla
            if idx_localidades == -1 or idx_tarifa == -1:
                continue
            
            # Extraer filas de datos
            filas = tabla.find_all('tr')[1:]  # Saltar encabezado
            
            for fila in filas:
                celdas = fila.find_all(['td', 'th'])
                
                # Verificar que haya suficientes celdas
                if len(celdas) <= max(idx_localidades, idx_tarifa):
                    continue
                
                # Extraer localidad
                localidad = celdas[idx_localidades].get_text(strip=True)
                
                # Extraer URL del PDF desde la celda de tarifa vigente
                celda_tarifa = celdas[idx_tarifa]
                enlace_pdf = celda_tarifa.find('a')
                
                # Solo agregar si ambos datos existen
                if localidad and enlace_pdf:
                    href = enlace_pdf.get('href')
                    if href:
                        url_pdf = urljoin(base_url, href)
                        datos_extraidos.append({
                            'localidad': localidad,
                            'url_pdf': url_pdf
                        })
        
        return datos_extraidos
    except Exception as e:
        print(f"Error al extraer datos de tabla de tarifas: {e}")
        return []


def extraer_empresas_agua(url: str, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Extrae información de todas las empresas de agua desde la página de tarifas vigentes.
    
    Para cada empresa encontrada, extrae:
    - Nombre de la empresa
    - Lista de localidades con sus respectivas URLs de PDF de tarifas
    
    Args:
        url: URL de la página de tarifas vigentes
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        Lista de diccionarios, uno por empresa, con:
        - empresa: Nombre de la empresa de agua
        - tarifas: Lista de diccionarios con localidad y url_pdf
    """
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        empresas: List[Dict[str, Any]] = []
        
        # Buscar elementos que contengan nombres de empresas
        # Típicamente serán encabezados (h2, h3, h4) o elementos con formato "Empresa - Tarifas vigentes"
        posibles_empresas = soup.find_all(['h2', 'h3', 'h4', 'strong', 'b'])
        
        for elemento in posibles_empresas:
            texto = elemento.get_text(strip=True)
            
            # Verificar si el texto contiene "Tarifas vigentes" o similar
            if 'tarifa' not in texto.lower():
                continue
            
            # Extraer nombre de empresa
            nombre_empresa = extraer_nombre_empresa(texto)
            if not nombre_empresa:
                continue
            
            # Buscar la tabla siguiente al encabezado de la empresa
            tabla_siguiente = elemento.find_next('table')
            if not tabla_siguiente:
                continue
            
            # Extraer datos de la tabla
            tabla_html = str(tabla_siguiente)
            datos_tarifas = extraer_datos_tabla_tarifas(
                tabla_html,
                response.url
            )
            
            # Solo agregar si hay datos de tarifas
            if datos_tarifas:
                empresas.append({
                    'empresa': nombre_empresa,
                    'tarifas': datos_tarifas
                })
        
        return empresas
    except Exception as e:
        print(f"Error al extraer empresas de agua: {e}")
        return []


def descargar_pdf(url: str, ruta_destino: str, timeout: int = 30) -> bool:
    """
    Descarga un archivo PDF desde una URL y lo guarda en disco.
    
    Args:
        url: URL del PDF a descargar
        ruta_destino: Ruta donde guardar el PDF
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        True si la descarga fue exitosa, False en caso contrario
    """
    try:
        # Crear directorios si no existen
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        
        # Descargar el PDF
        response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
        response.raise_for_status()
        
        # Verificar que el contenido sea PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
            print(f"Advertencia: El contenido no parece ser un PDF (content-type: {content_type})")
        
        # Guardar el archivo
        with open(ruta, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verificar que el archivo se guardó y tiene contenido
        if ruta.exists() and ruta.stat().st_size > 0:
            return True
        else:
            print(f"Error: El archivo descargado está vacío o no existe")
            return False
            
    except Exception as e:
        print(f"Error al descargar PDF desde {url}: {e}")
        return False
