from datetime import datetime
import math
import requests
from utils.time_utils import bucket_10m_plus2
from utils.image_utils import image_url
from config.config import IMG_URL_BASE, LAT, LON, OWM_TILES_BASE_URL, OWM_API_KEY


def latest_image_url(now: datetime | None = None) -> str:
    ahora = now or datetime.now()
    ts_base, minuto_real = bucket_10m_plus2(ahora)
    return image_url(IMG_URL_BASE, ts_base, minuto_real, with_year_dir=False)


def try_head(url: str, timeout=(3, 5)) -> bool:
    """
    Hace una solicitud HEAD y devuelve True si el recurso existe.
    """
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code < 400
    except requests.RequestException:
        return False


def latlon_to_tile_xy(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """
    Convierte lat/lon a coordenadas de tile X,Y en esquema WebMercator.
    """
    lat_rad = math.radians(lat)
    n = 2.0**zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int(
        (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi)
        / 2.0
        * n
    )
    return xtile, ytile


def fetch_owm_tile(layer="clouds_new", zoom=2):
    x, y = latlon_to_tile_xy(LAT, LON, zoom)
    tile_url = f"{OWM_TILES_BASE_URL}{layer}/{zoom}/{x}/{y}.png?appid={OWM_API_KEY}"

    try:
        resp = requests.get(tile_url, timeout=15)
        if resp.status_code == 200:
            return resp.content
        if zoom > 0:
            # si falla, intenta con un zoom menor
            return fetch_owm_tile(layer, zoom - 1)
        return None
    except requests.RequestException:
        if zoom > 0:
            return fetch_owm_tile(layer, zoom - 1)
        return None
