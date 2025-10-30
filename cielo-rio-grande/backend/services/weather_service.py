import requests
from config.config import OWM_API_KEY, OWM_BASE_URL, LAT, LON


def get_weather() -> dict:
    if not OWM_API_KEY:
        return {"error": "OWM_API_KEY not configured"}

    url = (
        f"{OWM_BASE_URL}"
        f"?lat={LAT}&lon={LON}"
        f"&units=metric&lang=es&appid={OWM_API_KEY}"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        return {
            "temp": data["main"]["temp"],
            "sensacion_termica": data["main"]["feels_like"],
            "humedad": data["main"]["humidity"],
            "presion": data["main"]["pressure"],
            "viento_velocidad": data["wind"]["speed"],
            "viento_direccion": data["wind"].get("deg", None),
            "nubosidad_api": data["clouds"]["all"],
            "descripcion": data["weather"][0]["description"].capitalize(),
        }

    except requests.RequestException as e:
        return {"error": f"No se pudo obtener el clima: {e}"}
