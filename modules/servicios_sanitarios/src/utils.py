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

from .logger import get_logger

# Initialize logger for utilities
logger = get_logger('concierge.servicios_sanitarios.utils')


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


def validate_priority(priority: str) -> bool:
    """
    Validate that a priority is valid.
    
    Args:
        priority: String with the priority to validate
        
    Returns:
        True if it's valid, False otherwise
    """
    return priority in ["baja", "media", "alta", "critica"]


def get_current_date() -> datetime:
    """
    Get the current date and time.
    
    Returns:
        Datetime object with the current date/time
    """
    return datetime.now()


def format_duration(start: datetime, end: Optional[datetime] = None) -> str:
    """
    Calculate and format the duration between two dates.
    
    Args:
        start: Start date
        end: End date (if not provided, uses current date)
        
    Returns:
        String with the formatted duration
    """
    if end is None:
        end = datetime.now()
    
    duration = end - start
    
    days = duration.days
    seconds = duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def check_url_redirection(url: str, timeout: int = 10) -> Optional[str]:
    """
    Check the URL to which a web page redirects.
    
    Args:
        url: Initial URL to check
        timeout: Maximum wait time in seconds
        
    Returns:
        String with the final URL after redirections, or None if there's an error
    """
    try:
        logger.debug(f"Checking redirection for URL: {url}")
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        final_url = response.url
        logger.debug(f"Redirection check successful: {url} -> {final_url}")
        return final_url
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error when checking redirection for {url}: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error when checking redirection for {url}: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error when checking redirection for {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error when checking redirection for {url}: {e}", exc_info=True)
        return None


def save_json(data: dict[str, Any], file_path: str) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Dictionary with the data to save
        file_path: Path to the file where to save the data
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Successfully saved JSON to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}", exc_info=True)
        return False


def load_json(file_path: str) -> Optional[dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file to load
        
    Returns:
        Dictionary with the loaded data, or None if there's an error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully loaded JSON from {file_path}")
        return data
    except FileNotFoundError:
        logger.debug(f"JSON file not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}", exc_info=True)
        return None


def extract_url_by_text(url: str, search_text: str, timeout: int = 10) -> Optional[str]:
    """
    Extract the URL of a link in an HTML page by searching for the link text.
    
    Args:
        url: URL of the page to analyze
        search_text: Text of the link to search for
        timeout: Maximum wait time in seconds
        
    Returns:
        String with the absolute URL of the found link, or None if not found
    """
    try:
        logger.debug(f"Extracting URL by text '{search_text}' from {url}")
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Search for the link by text
        link = soup.find('a', string=lambda text: text and search_text.lower() in text.lower())
        
        if link and hasattr(link, 'get'):
            # Convert to absolute URL if relative
            href = link.get('href')
            if href and isinstance(href, str):
                absolute_url = urljoin(url, href)
                logger.debug(f"Found link for '{search_text}': {absolute_url}")
                return absolute_url
        
        logger.warning(f"Link with text '{search_text}' not found on page {url}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error when extracting URL by text from {url}: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error when extracting URL by text from {url}: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error when extracting URL by text from {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error when extracting URL by text from {url}: {e}", exc_info=True)
        return None


def extract_company_name(text: str) -> Optional[str]:
    """
    Extract the water company name from text with format "Company - Text".
    
    Args:
        text: Text containing the company name and description
        
    Returns:
        String with the company name (before the dash), or None if not found
        
    Examples:
        >>> extract_company_name("Aguas Andinas - Tarifas vigentes")
        "Aguas Andinas"
    """
    try:
        if not text or not isinstance(text, str):
            return None
        
        # Search for the dash and extract text before it
        if " - " in text:
            name = text.split(" - ")[0].strip()
            return name if name else None
        
        # If there's no dash, return the complete clean text
        return text.strip() if text.strip() else None
    except Exception as e:
        logger.error(f"Error extracting company name: {e}")
        return None


def extract_tariff_table_data(
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
        extracted_data: list[dict[str, Any]] = []
        
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
            idx_localities = -1
            idx_tariff = -1
            
            for i, header in enumerate(headers):
                header_lower = header.lower()
                if 'localidad' in header_lower:
                    idx_localities = i
                if 'tarifa' in header_lower and 'vigente' in header_lower:
                    idx_tariff = i
            
            # If both columns are not found, try with the next table
            if idx_localities == -1 or idx_tariff == -1:
                continue
            
            # Extract data rows
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                # Check that there are enough cells
                if len(cells) <= max(idx_localities, idx_tariff):
                    continue
                
                # Extract locality
                locality = cells[idx_localities].get_text(strip=True)
                
                # Extract PDF URL from the current tariff cell
                tariff_cell = cells[idx_tariff]
                pdf_link = tariff_cell.find('a')
                
                # Only add if both data exist
                if locality and pdf_link:
                    href = pdf_link.get('href')
                    if href:
                        pdf_url = urljoin(base_url, href)
                        extracted_data.append({
                            'localidad': locality,
                            'url_pdf': pdf_url
                        })
        
        return extracted_data
    except Exception as e:
        logger.error(f"Error extracting tariff table data: {e}", exc_info=True)
        return []


def extract_water_companies(url: str, timeout: int = 10) -> list[dict[str, Any]]:
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
        companies: list[dict[str, Any]] = []
        
        # Search for elements containing company names
        # Typically they will be headers (h2, h3, h4) or elements with format "Company - Current Tariffs"
        possible_companies = soup.find_all(['h2', 'h3', 'h4', 'strong', 'b'])
        
        for element in possible_companies:
            text = element.get_text(strip=True)
            
            # Check if the text contains "Tarifas vigentes" or similar
            if 'tarifa' not in text.lower():
                continue
            
            # Extract company name
            company_name = extract_company_name(text)
            if not company_name:
                continue
            
            # Search for the table following the company header
            next_table = element.find_next('table')
            if not next_table:
                continue
            
            # Extract data from the table
            table_html = str(next_table)
            tariff_data = extract_tariff_table_data(
                table_html,
                response.url
            )
            
            # Only add if there is tariff data
            if tariff_data:
                companies.append({
                    'empresa': company_name,
                    'tarifas': tariff_data
                })
        
        return companies
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error when extracting water companies from {url}: {e}")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error when extracting water companies from {url}: {e}")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error when extracting water companies from {url}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error when extracting water companies from {url}: {e}", exc_info=True)
        return []


def download_pdf(url: str, dest_path: str, timeout: int = 30) -> bool:
    """
    Download a PDF file from a URL and save it to disk.
    
    Args:
        url: URL of the PDF to download
        dest_path: Path where to save the PDF
        timeout: Maximum wait time in seconds
        
    Returns:
        True if the download was successful, False otherwise
    """
    try:
        # Create directories if they don't exist
        path = Path(dest_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Downloading PDF from {url} to {dest_path}")
        
        # Download the PDF
        response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
        response.raise_for_status()
        
        # Check that the content is PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
            logger.warning(f"Content may not be a PDF (content-type: {content_type}) for URL: {url}")
        
        # Save the file
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify that the file was saved and has content
        if path.exists() and path.stat().st_size > 0:
            logger.debug(f"Successfully downloaded PDF to {dest_path} ({path.stat().st_size} bytes)")
            return True
        else:
            logger.error(f"Downloaded file is empty or does not exist: {dest_path}")
            return False
            
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error when downloading PDF from {url}: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error when downloading PDF from {url}: {e}")
        return False
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error when downloading PDF from {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error when downloading PDF from {url}: {e}", exc_info=True)
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
