import os

APP_ENV = os.getenv("APP_ENV", "dev")
TZ = os.getenv("TZ", "America/Argentina/Buenos_Aires")
DB_FILE = os.getenv("DB_FILE", "./data/registros-octas.db")
OCTAS_MODEL_PATH = os.getenv("OCTAS_MODEL_PATH", "models/600EPOC_modelo_octa.h5")

IMG_URL_BASE = os.getenv(
    "IMG_URL_BASE", "http://201.251.63.225/meteorologia/cielo/image/"
)
OWM_API_KEY = os.getenv("OWM_API_KEY", "befacab068306913251d9c19fc38a1e6")
OWM_BASE_URL = os.getenv(
    "OWM_BASE_URL", "https://api.openweathermap.org/data/2.5/weather"
)
OWM_TILES_BASE_URL = os.getenv(
    "OWM_TILES_BASE_URL", "https://tile.openweathermap.org/map/"
)

LAT = float(os.getenv("LAT", "-53.7877"))
LON = float(os.getenv("LON", "-67.7093"))
