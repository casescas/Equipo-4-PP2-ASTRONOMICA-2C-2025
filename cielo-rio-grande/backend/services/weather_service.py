import os, requests

OWM_API_KEY = os.getenv("OWM_API_KEY") or "befacab068306913251d9c19fc38a1e6"
LAT = float(os.getenv("LAT", "-53.7877"))
LON = float(os.getenv("LON", "-67.7093"))


def get_weather():
    if not OWM_API_KEY:
        return {"error": "OWM_API_KEY not configured"}
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}&units=metric&lang=es&appid={OWM_API_KEY}"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "temp": data["main"]["temp"],
        "humedad": data["main"]["humidity"],
        "viento": data["wind"]["speed"],
        "nubosidad_api": data["clouds"]["all"],
        "descripcion": data["weather"][0]["description"].capitalize(),
    }
