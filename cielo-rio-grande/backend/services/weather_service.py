import requests
from config.config import OWM_API_KEY, OWM_BASE_URL, LAT, LON
from utils.radiation_utils import get_radiation_data 


def get_weather() -> dict:
    
    # 1. Lógica para obtener datos de OpenWeatherMap (OWM)
    if not OWM_API_KEY:
        owm_data = {"error": "OWM_API_KEY not configured"} 
    else:
        url = (
            f"{OWM_BASE_URL}"
            f"?lat={LAT}&lon={LON}"
            f"&units=metric&lang=es&appid={OWM_API_KEY}"
        )

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            owm_data = { # Se guarda el resultado en 'owm_data'
                "temp": data["main"]["temp"],
                "sensacion_termica": data["main"]["feels_like"],
                "humedad": data["main"]["humidity"],
                "presion": data["main"]["pressure"],
                "viento_velocidad": data["wind"]["speed"],
                "viento_direccion": data["wind"].get("deg", None),
                "nubosidad_api": data["clouds"]["all"],
                "descripcion": data["weather"][0]["description"].capitalize(),
                "clima_fuente": "OpenWeatherMap"
            }

        except requests.RequestException as e:
            owm_data = {"error_clima": f"No se pudo obtener el clima OWM: {e}"} 
            
    # 2. OBTENER DATOS DE RADIACIÓN (NUEVO)
    radiation_data = get_radiation_data()
    
    # 3. COMBINAR AMBOS RESULTADOS (NUEVO)
    # Fusiona OWM y Radiación. Si usas Python < 3.9, reemplaza por {**owm_data, **radiation_data}
    combined_data = owm_data | radiation_data 

    # 4. RETORNAR EL RESULTADO COMBINADO
    return combined_data