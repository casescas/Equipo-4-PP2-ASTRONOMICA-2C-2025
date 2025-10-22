from fastapi import FastAPI, Response
import requests

app = FastAPI()
OWM_API_KEY = "befacab068306913251d9c19fc38a1e6"

@app.get("/clima")
def obtener_clima_owm():
    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat=-53.7877&lon=-67.7093&units=metric&lang=es&appid={OWM_API_KEY}"
    )
    headers = {"User-Agent": "FastAPI-Client"}
    resp = requests.get(url, headers=headers, timeout=10)

    if resp.status_code == 200:
        data = resp.json()
        return {
            "temp": data["main"]["temp"],
            "viento": data["wind"]["speed"],
            "nubosidad_api": data["clouds"]["all"],
            "descripcion": data["weather"][0]["description"].capitalize(),
        }
    else:
        return Response(
            content=f"No se pudo obtener el clima: {resp.status_code} {resp.text}",
            status_code=resp.status_code
        )
