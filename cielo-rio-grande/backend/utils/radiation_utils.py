import requests
from bs4 import BeautifulSoup
import re 
from typing import Dict, Any

# **URL ORIGINAL, donde están los números**
RADIATION_URL = "http://201.251.63.225/meteorologia/vp2s1/vantalhb.htm"

def extract_numeric_value(text: str) -> float | None:
    """Extrae el primer valor numérico (entero o flotante) de una cadena de texto."""
    match = re.search(r"([\d\.]+)", text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return float(match.group(1))
    return None

def get_radiation_data() -> Dict[str, Any]:
    """
    Realiza web scraping iterando sobre todas las tablas hasta encontrar la de Radiación.
    """
    try:
        # 1. Obtener y Parsear el HTML
        headers = {"User-Agent": "Cielo-Rio-Grande-Scraper"}
        resp = requests.get(RADIATION_URL, headers=headers, timeout=20) 
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser') 
        
        # 2. Localizar la tabla de Radiación por contenido (MÉTODO DEFINITIVO)
        
        radiation_table = None
        
        # Buscamos TODAS las etiquetas TABLE/table en la página
        all_tables = soup.find_all(['TABLE', 'table'])
        
        for table in all_tables:
            # Normalizamos el texto de la tabla para buscar 'radiacion solar'
            table_text = re.sub(r'\s+', ' ', table.get_text(strip=True).lower())
            
            if 'radiacion solar' in table_text and 'uv' in table_text:
                # Encontramos la tabla de radiación
                radiation_table = table
                break
        
        if not radiation_table:
            return {"error_radiacion": "FALLA FINAL: No se encontró la tabla de datos de radiación por iteración."}

        # 3. Extraer los datos de las celdas (TD)
        cells = radiation_table.find_all(['TD', 'td']) 
        
        if len(cells) < 3:
            return {"error_radiacion": f"FALLA FINAL: Se esperaban 3 celdas, se encontraron {len(cells)}."}

        # CELDA 1: Radiacion Solar
        rs_text = cells[0].get_text(strip=True)
        radiacion_solar = extract_numeric_value(rs_text)

        # CELDA 2: Maxima radiacion
        max_text = cells[1].get_text(strip=True)
        max_radiacion = extract_numeric_value(max_text)
        
        # Extracción de la hora: Busca un patrón de hora (HH:MM) seguido de 'hs'
        match_hora = re.search(r"(\d{1,2}:\d{2})\s*hs", max_text)
        max_radiacion_hora = match_hora.group(1).strip() if match_hora else None

        # CELDA 3: UV Index
        uv_text = cells[2].get_text(strip=True)
        uv_index = extract_numeric_value(uv_text)
        
        # 4. Retorno Exitoso
        return {
            "radiacion_solar_w_m2": radiacion_solar,
            "max_radiacion_w_m2": max_radiacion,
            "max_radiacion_hora": max_radiacion_hora,
            "uv_index": uv_index,
            "radiacion_fuente": "Estacion Local (vantalhb.htm)"
        }
        
    except Exception as e:
        print(f"Error al procesar datos de radiación: {e}")
        return {
            "error_radiacion": f"Error interno de parsing: {e}",
            "radiacion_solar_w_m2": None,
            "max_radiacion_w_m2": None,
            "max_radiacion_hora": None,
            "uv_index": None,
        }
        