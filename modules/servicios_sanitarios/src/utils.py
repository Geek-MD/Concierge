"""
Utilities and helper functions for the sanitary services module.
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
    Generate a unique ID to identify system elements.
    
    Returns:
        String with a unique UUID
    """
    return str(uuid.uuid4())


def format_timestamp(dt: datetime) -> str:
    """
    Format a timestamp in ISO 8601 format.
    
    Args:
        dt: Datetime object to format
        
    Returns:
        String with the formatted timestamp
    """
    return dt.isoformat()


def validar_prioridad(prioridad: str) -> bool:
    """
    Validate that a priority is valid.
    
    Args:
        prioridad: String with the priority to validate
        
    Returns:
        True if it's valid, False otherwise
    """
    return prioridad in ["baja", "media", "alta", "critica"]


def obtener_fecha_actual() -> datetime:
    """
    Get the current date and time.
    
    Returns:
        Datetime object with the current date/time
    """
    return datetime.now()


def formatear_duracion(inicio: datetime, fin: Optional[datetime] = None) -> str:
    """
    Calculate and format the duration between two dates.
    
    Args:
        inicio: Start date
        fin: End date (if not provided, uses current date)
        
    Returns:
        String with the formatted duration
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
    Check the URL to which a web page redirects.
    
    Args:
        url: Initial URL to check
        timeout: Maximum wait time in seconds
        
    Returns:
        String with the final URL after redirections, or None if there's an error
    """
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        return response.url
    except Exception as e:
        print(f"Error al verificar redirección: {e}")
        return None


def guardar_json(data: dict[str, Any], ruta_archivo: str) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Dictionary with the data to save
        ruta_archivo: Path to the file where to save the data
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        ruta = Path(ruta_archivo)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error al guardar JSON: {e}")
        return False


def cargar_json(ruta_archivo: str) -> Optional[dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        ruta_archivo: Path to the JSON file to load
        
    Returns:
        Dictionary with the loaded data, or None if there's an error
    """
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar JSON: {e}")
        return None


def extraer_url_por_texto(url: str, texto_buscar: str, timeout: int = 10) -> Optional[str]:
    """
    Extract the URL of a link in an HTML page by searching for the link text.
    
    Args:
        url: URL of the page to analyze
        texto_buscar: Text of the link to search for
        timeout: Maximum wait time in seconds
        
    Returns:
        String with the absolute URL of the found link, or None if not found
    """
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Search for the link by text
        link = soup.find('a', string=lambda text: text and texto_buscar.lower() in text.lower())
        
        if link and hasattr(link, 'get'):
            # Convert to absolute URL if relative
            href = link.get('href')
            if href and isinstance(href, str):
                url_absoluta = urljoin(url, href)
                return url_absoluta
        
        return None
    except Exception as e:
        print(f"Error al extraer URL por text: {e}")
        return None


def extraer_nombre_empresa(text: str) -> Optional[str]:
    """
    Extract the water company name from text with format "Company - Text".
    
    Args:
        text: Text containing the company name and description
        
    Returns:
        String with the company name (before the dash), or None if not found
        
    Examples:
        >>> extraer_nombre_empresa("Aguas Andinas - Tarifas vigentes")
        "Aguas Andinas"
    """
    try:
        if not text or not isinstance(text, str):
            return None
        
        # Search for the dash and extract text before it
        if " - " in text:
            nombre = text.split(" - ")[0].strip()
            return nombre if nombre else None
        
        # If there's no dash, return the complete clean text
        return text.strip() if text.strip() else None
    except Exception as e:
        print(f"Error al extraer nombre de company: {e}")
        return None


def extraer_datos_tabla_tarifas(
    html_content: str, 
    base_url: str
) -> list[dict[str, Any]]:
    """
    Extract data from an HTML table of water tariffs.
    
    Searches for tables with "Localidades" and "Tarifa vigente" columns, and extracts
    rows that have data in both columns. From the "Tarifa vigente" column,
    it extracts the PDF file URL.
    
    Args:
        html_content: HTML content of the page
        base_url: Base URL to resolve relative URLs
        
    Returns:
        List of dictionaries with the extracted data, each with:
        - localidad: Name of the locality
        - url_pdf: Absolute URL of the tariff PDF file
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        datos_extraidos: list[dict[str, Any]] = []
        
        # Search for all tables
        tables = soup.find_all('table')
        
        for table in tables:
            # Search for table headers
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Check if it has the required columns
            if not headers:
                continue
                
            # Search for column indices (case-insensitive)
            idx_localidades = -1
            idx_tarifa = -1
            
            for i, header in enumerate(headers):
                header_lower = header.lower()
                if 'localidad' in header_lower:
                    idx_localidades = i
                if 'tarifa' in header_lower and 'vigente' in header_lower:
                    idx_tarifa = i
            
            # If both columns are not found, try with the next table
            if idx_localidades == -1 or idx_tarifa == -1:
                continue
            
            # Extract data rows
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                # Check that there are enough cells
                if len(cells) <= max(idx_localidades, idx_tarifa):
                    continue
                
                # Extract locality
                localidad = cells[idx_localidades].get_text(strip=True)
                
                # Extract PDF URL from the current tariff cell
                celda_tarifa = cells[idx_tarifa]
                enlace_pdf = celda_tarifa.find('a')
                
                # Only add if both data exist
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
        print(f"Error al extraer data de table de tarifas: {e}")
        return []


def extraer_empresas_agua(url: str, timeout: int = 10) -> list[dict[str, Any]]:
    """
    Extract information from all water companies from the current tariffs page.
    
    For each company found, it extracts:
    - Company name
    - List of localities with their respective tariff PDF URLs
    
    Args:
        url: URL of the current tariffs page
        timeout: Maximum wait time in seconds
        
    Returns:
        List of dictionaries, one per company, with:
        - empresa: Name of the water company
        - tarifas: List of dictionaries with localidad and url_pdf
    """
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        empresas: list[dict[str, Any]] = []
        
        # Search for elements containing company names
        # Typically they will be headers (h2, h3, h4) or elements with format "Company - Current Tariffs"
        posibles_empresas = soup.find_all(['h2', 'h3', 'h4', 'strong', 'b'])
        
        for elemento in posibles_empresas:
            text = elemento.get_text(strip=True)
            
            # Check if the text contains "Tarifas vigentes" or similar
            if 'tarifa' not in text.lower():
                continue
            
            # Extract company name
            nombre_empresa = extraer_nombre_empresa(text)
            if not nombre_empresa:
                continue
            
            # Search for the table following the company header
            tabla_siguiente = elemento.find_next('table')
            if not tabla_siguiente:
                continue
            
            # Extract data from the table
            tabla_html = str(tabla_siguiente)
            datos_tarifas = extraer_datos_tabla_tarifas(
                tabla_html,
                response.url
            )
            
            # Only add if there is tariff data
            if datos_tarifas:
                empresas.append({
                    'empresa': nombre_empresa,
                    'tarifas': datos_tarifas
                })
        
        return empresas
    except Exception as e:
        print(f"Error al extraer companies de agua: {e}")
        return []


def descargar_pdf(url: str, ruta_destino: str, timeout: int = 30) -> bool:
    """
    Download a PDF file from a URL and save it to disk.
    
    Args:
        url: URL of the PDF to download
        ruta_destino: Path where to save the PDF
        timeout: Maximum wait time in seconds
        
    Returns:
        True if the download was successful, False otherwise
    """
    try:
        # Create directories if they don't exist
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        
        # Download the PDF
        response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
        response.raise_for_status()
        
        # Check that the content is PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
            print(f"Advertencia: El contenido no parece ser un PDF (content-type: {content_type})")
        
        # Save the file
        with open(ruta, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify that the file was saved and has content
        if ruta.exists() and ruta.stat().st_size > 0:
            return True
        else:
            print("Error: El archivo descargado está vacío o no existe")
            return False
            
    except Exception as e:
        print(f"Error al descargar PDF desde {url}: {e}")
        return False


def parse_table_structure(table: list[list[Any]]) -> dict[str, Any]:
    """
    Parse the structure of a table identifying sections and concept-value pairs.
    
    Tables can contain:
    1. Section headers: rows with only 1 column with data or highlighted text
    2. Concept-value pairs: rows with 2 or more columns (concept + value/price)
    
    Args:
        table: List of rows, where each row is a list of cells
        
    Returns:
        Dict with parsed structure:
        {
            "type": "simple" | "with_sections",
            "sections": [
                {
                    "section_name": str,
                    "data": [{"concept": str, "value": str}, ...]
                },
                ...
            ],
            "direct_data": [{"concept": str, "value": str}, ...],
            "total_rows": int,
            "total_concepts": int
        }
    """
    if not table:
        return {
            "type": "empty",
            "sections": [],
            "direct_data": [],
            "total_rows": 0,
            "total_concepts": 0
        }
    
    sections: list[dict[str, Any]] = []
    direct_data: list[dict[str, Any]] = []
    current_section: Optional[dict[str, Any]] = None
    total_concepts = 0
    
    for row in table:
        # Clean cells
        cells = [str(cell).strip() if cell else "" for cell in row]
        non_empty_cells = [c for c in cells if c]
        
        if not non_empty_cells:
            # Empty row, ignore
            continue
        
        # Detect if it is a section header
        # Criteria: only 1 cell with content, or all cells except the first are empty
        if len(non_empty_cells) == 1:
            # It is a section header
            section_name = non_empty_cells[0]
            
            # Save previous section if exists
            if current_section is not None:
                sections.append(current_section)
            
            # Initialize new section
            current_section = {
                "section_name": section_name,
                "data": []
            }
        
        # Detect if it is a concept-value pair
        elif len(non_empty_cells) >= 2:
            # It is a concept-value pair (or multiple values)
            concept = non_empty_cells[0]
            values = non_empty_cells[1:]
            
            # Detect if contains numbers, prices or measures
            es_dato_valor = any(
                _contains_number_or_price(v) for v in values
            )
            
            if es_dato_valor or len(values) == 1:
                # It is a valid concept-value pair
                par_datos: dict[str, Any] = {
                    "concept": concept,
                    "value": values[0] if len(values) == 1 else values,
                    "additional_values": values[1:] if len(values) > 1 else []
                }
                
                if current_section is not None:
                    current_section["data"].append(par_datos)
                else:
                    direct_data.append(par_datos)
                
                total_concepts += 1
            else:
                # Could be a multi-column header
                # Treat it as section
                section_name = " - ".join(non_empty_cells)
                
                if current_section is not None:
                    sections.append(current_section)
                
                current_section = {
                    "section_name": section_name,
                    "data": []
                }
    
    # Save last section if exists
    if current_section is not None:
        sections.append(current_section)
    
    return {
        "type": "with_sections" if sections else "simple",
        "sections": sections,
        "direct_data": direct_data,
        "total_rows": len(table),
        "total_concepts": total_concepts
    }


def _contains_number_or_price(text: str) -> bool:
    """
    Check if a text contains numbers, prices or values.
    
    Args:
        text: Text to analyze
        
    Returns:
        True if it contains numbers, prices or values
    """
    # Common patterns for prices and values
    patterns = [
        r'\d+',  # Numbers
        r'\$\s*\d+',  # Price with $
        r'\d+\s*,\s*\d+',  # Numbers with commas (thousands)
        r'\d+\.\d+',  # Decimal numbers
        r'\d+\s*%',  # Percentages
        r'\d+\s*(m3|m²|km|kg|lt|uf)',  # Units of measure
        r'(SI|NO|si|no)',  # Boolean values
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def extract_pdf_text(pdf_path: str, use_ocr: bool = False) -> Optional[str]:
    """
    Extracts text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        use_ocr: If True, uses OCR for scanned PDFs
        
    Returns:
        String with extracted text or None if error
    """
    try:
        from pypdf import PdfReader
        
        ruta = Path(pdf_path)
        if not ruta.exists():
            print(f"Error: El archivo {pdf_path} no existe")
            return None
        
        # Try to extract text directly from PDF
        reader = PdfReader(str(ruta))
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # If text is empty or very short, may be a scanned PDF
        if use_ocr and (not text.strip() or len(text.strip()) < 50):
            print("Texto extraído muy corto, intentando con OCR...")
            return extract_pdf_text_with_ocr(pdf_path)
        
        return text.strip() if text.strip() else None
        
    except Exception as e:
        print(f"Error al extraer text del PDF {pdf_path}: {e}")
        return None


def extract_pdf_tables(pdf_path: str) -> Optional[dict[str, Any]]:
    """
    Extracts tables from a PDF file detecting borders and structure.
    
    Uses pdfplumber which can detect tables, borders and 
    maintain the structure of tabular data.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dict with text and extracted tables, or None if error.
        Structure:
        {
            "texto": "complete text from PDF",
            "tables": [
                {
                    "page": 1,
                    "table_number": 1,
                    "filas": [[cell1, cell2, ...], ...],
                    "texto_formateado": "text representation"
                },
                ...
            ],
            "total_paginas": N,
            "total_tablas": M
        }
    """
    try:
        import pdfplumber
        
        ruta = Path(pdf_path)
        if not ruta.exists():
            print(f"Error: El archivo {pdf_path} no existe")
            return None
        
        result = {
            "text": "",
            "tables": [],
            "total_pages": 0,
            "total_tables": 0
        }
        
        with pdfplumber.open(str(ruta)) as pdf:
            result["total_pages"] = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text from page
                page_text = page.extract_text()
                if page_text:
                    result["text"] += f"\n--- Página {page_num} ---\n"
                    result["text"] += page_text + "\n"
                
                # Extract tables from page
                tablas_pagina = page.extract_tables()
                
                for table_num, table in enumerate(tablas_pagina, 1):
                    if table:
                        # Parse table structure
                        structure = parse_table_structure(table)
                        
                        # Format table as text
                        table_text = f"\n=== Tabla {result['total_tablas'] + 1} (Página {page_num}) ===\n"
                        
                        # Add table rows
                        for row in table:
                            # Clean None and extra spaces
                            fila_limpia = [str(cell).strip() if cell else "" for cell in row]
                            table_text += " | ".join(fila_limpia) + "\n"
                        
                        result["tables"].append({
                            "page": page_num,
                            "tabla_numero": table_num,
                            "rows": table,
                            "texto_formateado": table_text,
                            "structure": structure
                        })
                        
                        result["total_tables"] += 1
                        
                        # Add table to general text
                        result["text"] += table_text
        
        return result if result["text"].strip() else None
        
    except ImportError as e:
        print(f"Error: pdfplumber no está instalado: {e}")
        print("Instala: pip install pdfplumber")
        return None
    except Exception as e:
        print(f"Error al extraer tables del PDF {pdf_path}: {e}")
        return None


def extract_pdf_text_with_ocr(pdf_path: str) -> Optional[str]:
    """
    Extracts text from a scanned PDF using OCR.
    
    Requires:
        - pytesseract
        - pdf2image
        - tesseract-ocr installed on the system
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        String with extracted text or None if error
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
        
        ruta = Path(pdf_path)
        if not ruta.exists():
            print(f"Error: El archivo {pdf_path} no existe")
            return None
        
        # Convert PDF to images
        images = convert_from_path(str(ruta))
        
        # Apply OCR to each page
        full_text = ""
        for i, image in enumerate(images, 1):
            page_text = pytesseract.image_to_string(image, lang='spa')
            full_text += f"\n--- Página {i} ---\n"
            full_text += page_text + "\n"
        
        return full_text.strip() if full_text.strip() else None
        
    except ImportError as e:
        print(f"Error: Librerías necesarias no instaladas: {e}")
        print("Instala: pip install pytesseract pdf2image")
        print("Además necesitas instalar tesseract-ocr en el sistema")
        return None
    except Exception as e:
        print(f"Error al aplicar OCR al PDF {pdf_path}: {e}")
        return None


def get_pdfs_in_folder(folder_path: str, recursive: bool = True) -> list[str]:
    """
    Get the list of PDF files in a folder.
    
    Args:
        folder_path: Path to the folder
        recursive: If True, searches in subfolders
        
    Returns:
        List with complete paths of found PDF files
    """
    try:
        folder = Path(folder_path)
        if not folder.exists():
            print(f"Error: La folder {folder_path} no existe")
            return []
        
        if recursive:
            pdfs = list(folder.rglob("*.pdf"))
        else:
            pdfs = list(folder.glob("*.pdf"))
        
        return [str(pdf) for pdf in sorted(pdfs)]
        
    except Exception as e:
        print(f"Error al listar PDFs en {folder_path}: {e}")
        return []


def organize_hierarchical_analysis(analyzed_pdfs: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Organize PDF analyses in a hierarchical structure by company and locality.
    
    Resulting structure:
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
        analyzed_pdfs: List of analyzed PDFs with their information
        
    Returns:
        Dict with hierarchical structure organized by company and locality
    """
    structure = {
        "companies": {},
        "summary": {
            "total_companies": 0,
            "total_localities": 0,
            "total_pdfs": 0
        }
    }
    
    for pdf_data in analyzed_pdfs:
        # Get company (parent folder)
        company = pdf_data.get("folder", "Sin_Empresa")
        
        # Get locality (filename without extension)
        filename = pdf_data.get("filename", "")
        locality = filename.replace(".pdf", "").replace(".PDF", "")
        
        # Create company entry if it does not exist
        if company not in structure["companies"]:
            # Convert normalized name to readable name
            readable_company_name = company.replace("_", " ")
            
            structure["companies"][company] = {
                "company_name": readable_company_name,
                "normalized_name": company,
                "localities": {},
                "total_localities": 0,
                "total_pdfs": 0
            }
            structure["summary"]["total_companies"] += 1
        
        # Create locality entry if it does not exist
        if locality not in structure["companies"][company]["localities"]:
            readable_locality_name = locality.replace("_", " ")
            
            structure["companies"][company]["localities"][locality] = {
                "locality_name": readable_locality_name,
                "normalized_name": locality,
                "pdfs": []
            }
            structure["companies"][company]["total_localities"] += 1
            structure["summary"]["total_localities"] += 1
        
        # Add PDF analysis to locality
        structure["companies"][company]["localities"][locality]["pdfs"].append({
            "pdf_file": filename,
            "full_path": pdf_data.get("pdf_path", ""),
            "analysis": {
                "size_kb": pdf_data.get("size_kb", 0),
                "total_pages": pdf_data.get("total_pages", 0),
                "total_tables": pdf_data.get("total_tables", 0),
                "total_concepts": pdf_data.get("total_concepts", 0),
                "total_sections": pdf_data.get("total_sections", 0),
                "text_length": pdf_data.get("text_length", 0),
                "extraction_method": pdf_data.get("extraction_method", ""),
                "used_ocr": pdf_data.get("used_ocr", False),
                "timestamp": pdf_data.get("timestamp", ""),
                "extracted_text": pdf_data.get("extracted_text", ""),
                "tables": pdf_data.get("tables", [])
            }
        })
        
        structure["companies"][company]["total_pdfs"] += 1
        structure["summary"]["total_pdfs"] += 1
    
    return structure


def get_new_pdfs(
    folder_path: str, 
    registry_path: str,
    recursive: bool = True
) -> list[str]:
    """
    Get the list of new PDFs that have not been analyzed.
    
    Args:
        folder_path: Path to the folder with PDFs
        registry_path: Path to the JSON file with registry of analyzed PDFs
        recursive: If True, searches in subfolders
        
    Returns:
        List with paths of new PDFs (not analyzed)
    """
    try:
        # Get all PDFs in folder
        all_pdfs = get_pdfs_in_folder(folder_path, recursive)
        
        # Load registry of analyzed PDFs
        registry = cargar_json(registry_path)
        
        # If there's no registry, all are new
        if not registry:
            return all_pdfs
        
        # Get set of already analyzed PDFs
        analyzed_pdfs = set()
        for pdf_info in registry.get("analyzed_pdfs", []):
            analyzed_pdfs.add(pdf_info.get("pdf_path"))
        
        # Filter only new ones
        new_pdfs = [pdf for pdf in all_pdfs if pdf not in analyzed_pdfs]
        
        return new_pdfs
        
    except Exception as e:
        print(f"Error al obtener PDFs nuevos: {e}")
        return []
