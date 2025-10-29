import math
import requests

# Coordenadas Río Grande
LAT = -53.79
LON = -67.70

# 🔑 Clave fija de OpenWeatherMap
API_KEY = "befacab068306913251d9c19fc38a1e6"

def latlon_to_tile_xy(lat, lon, zoom):
    """Convierte lat/lon a tile x,y en esquema webmercator."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile


def fetch_owm_tile(layer="clouds_new", zoom=2):
    """
    Descarga la tile de OpenWeatherMap para la capa indicada y devuelve bytes (PNG).
    Zoom 2 → vista muy amplia, casi toda Tierra del Fuego visible.
    """
    x, y = latlon_to_tile_xy(LAT, LON, zoom)
    tile_url = f"https://tile.openweathermap.org/map/{layer}/{zoom}/{x}/{y}.png?appid={API_KEY}"

    resp = requests.get(tile_url, timeout=15)
    if resp.status_code == 200:
        return resp.content
    else:
        # Fallback: intentar con zoom menor (más amplio)
        if zoom > 0:
            return fetch_owm_tile(layer, zoom - 1)
        return None