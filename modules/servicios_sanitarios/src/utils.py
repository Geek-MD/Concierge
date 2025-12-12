"""
Utilidades y funciones auxiliares para el módulo de servicios sanitarios.
"""

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


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


def guardar_json(datos: dict[str, Any], ruta_archivo: str) -> bool:
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


def cargar_json(ruta_archivo: str) -> Optional[dict[str, Any]]:
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
) -> list[dict[str, Any]]:
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
        datos_extraidos: List[dict[str, Any]] = []
        
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


def extraer_empresas_agua(url: str, timeout: int = 10) -> list[dict[str, Any]]:
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
        empresas: List[dict[str, Any]] = []
        
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
            print("Error: El archivo descargado está vacío o no existe")
            return False
            
    except Exception as e:
        print(f"Error al descargar PDF desde {url}: {e}")
        return False


def parsear_estructura_tabla(tabla: list[list[Any]]) -> dict[str, Any]:
    """
    Parsea la estructura de una tabla identificando secciones y pares concepto-valor.
    
    Las tablas pueden contener:
    1. Encabezados de sección: filas con solo 1 columna con datos o texto destacado
    2. Pares concepto-valor: filas con 2 o más columnas (concepto + valor/precio)
    
    Args:
        tabla: Lista de filas, donde cada fila es una lista de celdas
        
    Returns:
        Dict con la estructura parseada:
        {
            "tipo": "simple" | "con_secciones",
            "secciones": [
                {
                    "nombre_seccion": str,
                    "datos": [{"concepto": str, "valor": str}, ...]
                },
                ...
            ],
            "datos_directos": [{"concepto": str, "valor": str}, ...],
            "total_filas": int,
            "total_conceptos": int
        }
    """
    if not tabla:
        return {
            "tipo": "vacia",
            "secciones": [],
            "datos_directos": [],
            "total_filas": 0,
            "total_conceptos": 0
        }
    
    secciones: list[dict[str, Any]] = []
    datos_directos: list[dict[str, Any]] = []
    seccion_actual: Optional[dict[str, Any]] = None
    total_conceptos = 0
    
    for fila in tabla:
        # Limpiar celdas
        celdas = [str(cell).strip() if cell else "" for cell in fila]
        celdas_no_vacias = [c for c in celdas if c]
        
        if not celdas_no_vacias:
            # Fila vacía, ignorar
            continue
        
        # Detectar si es encabezado de sección
        # Criterios: solo 1 celda con contenido, o todas las celdas menos la primera vacías
        if len(celdas_no_vacias) == 1:
            # Es un encabezado de sección
            nombre_seccion = celdas_no_vacias[0]
            
            # Guardar sección anterior si existe
            if seccion_actual is not None:
                secciones.append(seccion_actual)
            
            # Iniciar nueva sección
            seccion_actual = {
                "nombre_seccion": nombre_seccion,
                "datos": []
            }
        
        # Detectar si es un par concepto-valor
        elif len(celdas_no_vacias) >= 2:
            # Es un par concepto-valor (o múltiples valores)
            concepto = celdas_no_vacias[0]
            valores = celdas_no_vacias[1:]
            
            # Detectar si contiene números, precios o medidas
            es_dato_valor = any(
                _contiene_numero_o_precio(v) for v in valores
            )
            
            if es_dato_valor or len(valores) == 1:
                # Es un par concepto-valor válido
                par_datos: dict[str, Any] = {
                    "concepto": concepto,
                    "valor": valores[0] if len(valores) == 1 else valores,
                    "valores_adicionales": valores[1:] if len(valores) > 1 else []
                }
                
                if seccion_actual is not None:
                    seccion_actual["datos"].append(par_datos)
                else:
                    datos_directos.append(par_datos)
                
                total_conceptos += 1
            else:
                # Podría ser un encabezado de múltiples columnas
                # Tratarlo como sección
                nombre_seccion = " - ".join(celdas_no_vacias)
                
                if seccion_actual is not None:
                    secciones.append(seccion_actual)
                
                seccion_actual = {
                    "nombre_seccion": nombre_seccion,
                    "datos": []
                }
    
    # Guardar última sección si existe
    if seccion_actual is not None:
        secciones.append(seccion_actual)
    
    return {
        "tipo": "con_secciones" if secciones else "simple",
        "secciones": secciones,
        "datos_directos": datos_directos,
        "total_filas": len(tabla),
        "total_conceptos": total_conceptos
    }


def _contiene_numero_o_precio(texto: str) -> bool:
    """
    Detecta si un texto contiene números, precios o valores.
    
    Args:
        texto: Texto a analizar
        
    Returns:
        True si contiene números, precios o valores
    """
    # Patrones comunes de precios y valores
    patrones = [
        r'\d+',  # Números
        r'\$\s*\d+',  # Precio con $
        r'\d+\s*,\s*\d+',  # Números con comas (miles)
        r'\d+\.\d+',  # Números decimales
        r'\d+\s*%',  # Porcentajes
        r'\d+\s*(m3|m²|km|kg|lt|uf)',  # Unidades de medida
        r'(SI|NO|si|no)',  # Valores booleanos
    ]
    
    for patron in patrones:
        if re.search(patron, texto, re.IGNORECASE):
            return True
    
    return False


def extraer_texto_pdf(ruta_pdf: str, usar_ocr: bool = False) -> Optional[str]:
    """
    Extrae texto de un archivo PDF.
    
    Args:
        ruta_pdf: Ruta al archivo PDF
        usar_ocr: Si es True, usa OCR para PDFs escaneados
        
    Returns:
        String con el texto extraído o None si hay error
    """
    try:
        from pypdf import PdfReader
        
        ruta = Path(ruta_pdf)
        if not ruta.exists():
            print(f"Error: El archivo {ruta_pdf} no existe")
            return None
        
        # Intentar extraer texto directamente del PDF
        reader = PdfReader(str(ruta))
        texto = ""
        
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        
        # Si el texto está vacío o muy corto, puede ser un PDF escaneado
        if usar_ocr and (not texto.strip() or len(texto.strip()) < 50):
            print("Texto extraído muy corto, intentando con OCR...")
            return extraer_texto_pdf_con_ocr(ruta_pdf)
        
        return texto.strip() if texto.strip() else None
        
    except Exception as e:
        print(f"Error al extraer texto del PDF {ruta_pdf}: {e}")
        return None


def extraer_tablas_pdf(ruta_pdf: str) -> Optional[dict[str, Any]]:
    """
    Extrae tablas de un archivo PDF detectando bordes y estructura.
    
    Usa pdfplumber que es capaz de detectar tablas, bordes y 
    mantener la estructura de los datos tabulares.
    
    Args:
        ruta_pdf: Ruta al archivo PDF
        
    Returns:
        Dict con texto y tablas extraídas, o None si hay error.
        Estructura:
        {
            "texto": "texto completo del PDF",
            "tablas": [
                {
                    "pagina": 1,
                    "tabla_numero": 1,
                    "filas": [[cell1, cell2, ...], ...],
                    "texto_formateado": "representación en texto"
                },
                ...
            ],
            "total_paginas": N,
            "total_tablas": M
        }
    """
    try:
        import pdfplumber
        
        ruta = Path(ruta_pdf)
        if not ruta.exists():
            print(f"Error: El archivo {ruta_pdf} no existe")
            return None
        
        resultado = {
            "texto": "",
            "tablas": [],
            "total_paginas": 0,
            "total_tablas": 0
        }
        
        with pdfplumber.open(str(ruta)) as pdf:
            resultado["total_paginas"] = len(pdf.pages)
            
            for num_pagina, page in enumerate(pdf.pages, 1):
                # Extraer texto de la página
                texto_pagina = page.extract_text()
                if texto_pagina:
                    resultado["texto"] += f"\n--- Página {num_pagina} ---\n"
                    resultado["texto"] += texto_pagina + "\n"
                
                # Extraer tablas de la página
                tablas_pagina = page.extract_tables()
                
                for num_tabla, tabla in enumerate(tablas_pagina, 1):
                    if tabla:
                        # Parsear estructura de tabla
                        estructura = parsear_estructura_tabla(tabla)
                        
                        # Formatear tabla como texto
                        texto_tabla = f"\n=== Tabla {resultado['total_tablas'] + 1} (Página {num_pagina}) ===\n"
                        
                        # Agregar filas de la tabla
                        for fila in tabla:
                            # Limpiar None y espacios extras
                            fila_limpia = [str(cell).strip() if cell else "" for cell in fila]
                            texto_tabla += " | ".join(fila_limpia) + "\n"
                        
                        resultado["tablas"].append({
                            "pagina": num_pagina,
                            "tabla_numero": num_tabla,
                            "filas": tabla,
                            "texto_formateado": texto_tabla,
                            "estructura": estructura
                        })
                        
                        resultado["total_tablas"] += 1
                        
                        # Agregar tabla al texto general
                        resultado["texto"] += texto_tabla
        
        return resultado if resultado["texto"].strip() else None
        
    except ImportError as e:
        print(f"Error: pdfplumber no está instalado: {e}")
        print("Instala: pip install pdfplumber")
        return None
    except Exception as e:
        print(f"Error al extraer tablas del PDF {ruta_pdf}: {e}")
        return None


def extraer_texto_pdf_con_ocr(ruta_pdf: str) -> Optional[str]:
    """
    Extrae texto de un PDF escaneado usando OCR.
    
    Requiere:
        - pytesseract
        - pdf2image
        - tesseract-ocr instalado en el sistema
    
    Args:
        ruta_pdf: Ruta al archivo PDF
        
    Returns:
        String con el texto extraído o None si hay error
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
        
        ruta = Path(ruta_pdf)
        if not ruta.exists():
            print(f"Error: El archivo {ruta_pdf} no existe")
            return None
        
        # Convertir PDF a imágenes
        imagenes = convert_from_path(str(ruta))
        
        # Aplicar OCR a cada página
        texto_completo = ""
        for i, imagen in enumerate(imagenes, 1):
            texto_pagina = pytesseract.image_to_string(imagen, lang='spa')
            texto_completo += f"\n--- Página {i} ---\n"
            texto_completo += texto_pagina + "\n"
        
        return texto_completo.strip() if texto_completo.strip() else None
        
    except ImportError as e:
        print(f"Error: Librerías necesarias no instaladas: {e}")
        print("Instala: pip install pytesseract pdf2image")
        print("Además necesitas instalar tesseract-ocr en el sistema")
        return None
    except Exception as e:
        print(f"Error al aplicar OCR al PDF {ruta_pdf}: {e}")
        return None


def obtener_pdfs_en_carpeta(ruta_carpeta: str, recursivo: bool = True) -> list[str]:
    """
    Obtiene la lista de archivos PDF en una carpeta.
    
    Args:
        ruta_carpeta: Ruta a la carpeta
        recursivo: Si es True, busca en subcarpetas
        
    Returns:
        Lista con las rutas completas de los archivos PDF encontrados
    """
    try:
        carpeta = Path(ruta_carpeta)
        if not carpeta.exists():
            print(f"Error: La carpeta {ruta_carpeta} no existe")
            return []
        
        if recursivo:
            pdfs = list(carpeta.rglob("*.pdf"))
        else:
            pdfs = list(carpeta.glob("*.pdf"))
        
        return [str(pdf) for pdf in sorted(pdfs)]
        
    except Exception as e:
        print(f"Error al listar PDFs en {ruta_carpeta}: {e}")
        return []


def organizar_analisis_jerarquico(pdfs_analizados: List[dict[str, Any]]) -> dict[str, Any]:
    """
    Organiza los análisis de PDFs en una estructura jerárquica por compañía y localidad.
    
    Estructura resultante:
    {
        "empresas": {
            "Aguas_Andinas": {
                "nombre_empresa": "Aguas Andinas",
                "localidades": {
                    "Santiago": {
                        "nombre_localidad": "Santiago",
                        "archivo_pdf": "Santiago.pdf",
                        "analisis": {...}
                    },
                    "Maipu": {...}
                }
            },
            "Essbio": {...}
        },
        "resumen": {
            "total_empresas": N,
            "total_localidades": M,
            "total_pdfs": K
        }
    }
    
    Args:
        pdfs_analizados: Lista de PDFs analizados con su información
        
    Returns:
        Dict con estructura jerárquica organizada por empresa y localidad
    """
    estructura = {
        "empresas": {},
        "resumen": {
            "total_empresas": 0,
            "total_localidades": 0,
            "total_pdfs": 0
        }
    }
    
    for pdf_data in pdfs_analizados:
        # Obtener empresa (carpeta padre)
        empresa = pdf_data.get("carpeta", "Sin_Empresa")
        
        # Obtener localidad (nombre del archivo sin extensión)
        nombre_archivo = pdf_data.get("nombre_archivo", "")
        localidad = nombre_archivo.replace(".pdf", "").replace(".PDF", "")
        
        # Crear entrada de empresa si no existe
        if empresa not in estructura["empresas"]:
            # Convertir nombre normalizado a nombre legible
            nombre_empresa_legible = empresa.replace("_", " ")
            
            estructura["empresas"][empresa] = {
                "nombre_empresa": nombre_empresa_legible,
                "nombre_normalizado": empresa,
                "localidades": {},
                "total_localidades": 0,
                "total_pdfs": 0
            }
            estructura["resumen"]["total_empresas"] += 1
        
        # Crear entrada de localidad si no existe
        if localidad not in estructura["empresas"][empresa]["localidades"]:
            nombre_localidad_legible = localidad.replace("_", " ")
            
            estructura["empresas"][empresa]["localidades"][localidad] = {
                "nombre_localidad": nombre_localidad_legible,
                "nombre_normalizado": localidad,
                "pdfs": []
            }
            estructura["empresas"][empresa]["total_localidades"] += 1
            estructura["resumen"]["total_localidades"] += 1
        
        # Agregar análisis del PDF a la localidad
        estructura["empresas"][empresa]["localidades"][localidad]["pdfs"].append({
            "archivo_pdf": nombre_archivo,
            "ruta_completa": pdf_data.get("ruta_pdf", ""),
            "analisis": {
                "tamanio_kb": pdf_data.get("tamanio_kb", 0),
                "total_paginas": pdf_data.get("total_paginas", 0),
                "total_tablas": pdf_data.get("total_tablas", 0),
                "total_conceptos": pdf_data.get("total_conceptos", 0),
                "total_secciones": pdf_data.get("total_secciones", 0),
                "longitud_texto": pdf_data.get("longitud_texto", 0),
                "metodo_extraccion": pdf_data.get("metodo_extraccion", ""),
                "usado_ocr": pdf_data.get("usado_ocr", False),
                "timestamp": pdf_data.get("timestamp", ""),
                "texto_extraido": pdf_data.get("texto_extraido", ""),
                "tablas": pdf_data.get("tablas", [])
            }
        })
        
        estructura["empresas"][empresa]["total_pdfs"] += 1
        estructura["resumen"]["total_pdfs"] += 1
    
    return estructura


def obtener_pdfs_nuevos(
    ruta_carpeta: str, 
    ruta_registro: str,
    recursivo: bool = True
) -> list[str]:
    """
    Obtiene la lista de PDFs nuevos que no han sido analizados.
    
    Args:
        ruta_carpeta: Ruta a la carpeta con PDFs
        ruta_registro: Ruta al archivo JSON con registro de PDFs analizados
        recursivo: Si es True, busca en subcarpetas
        
    Returns:
        Lista con las rutas de PDFs nuevos (no analizados)
    """
    try:
        # Obtener todos los PDFs en la carpeta
        todos_pdfs = obtener_pdfs_en_carpeta(ruta_carpeta, recursivo)
        
        # Cargar registro de PDFs analizados
        registro = cargar_json(ruta_registro)
        
        # Si no hay registro, todos son nuevos
        if not registro:
            return todos_pdfs
        
        # Obtener conjunto de PDFs ya analizados
        pdfs_analizados = set()
        for pdf_info in registro.get("pdfs_analizados", []):
            pdfs_analizados.add(pdf_info.get("ruta_pdf"))
        
        # Filtrar solo los nuevos
        pdfs_nuevos = [pdf for pdf in todos_pdfs if pdf not in pdfs_analizados]
        
        return pdfs_nuevos
        
    except Exception as e:
        print(f"Error al obtener PDFs nuevos: {e}")
        return []
