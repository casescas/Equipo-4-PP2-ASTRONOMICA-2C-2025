from datetime import datetime, timedelta
import os, requests
import math
import requests

IMG_URL_BASE = os.getenv(
    "IMG_URL_BASE", "http://201.251.63.225/meteorologia/cielo/image/"
)


def _build_filename(ts: datetime) -> str:
    return f"{ts.year}-{ts.strftime('%m%d%H')}{ts.strftime('%M')}" + ".jpg"


def _bucket_minute_10m_plus2(now: datetime) -> datetime:
    base = now.replace(second=0, microsecond=0)
    minute_bucket = (base.minute // 10) * 10
    candidate = base.replace(minute=minute_bucket) + timedelta(minutes=2)
    if candidate > now:
        candidate = candidate - timedelta(minutes=10)
    return candidate


def latest_image_url(now: datetime | None = None) -> str:
    now = now or datetime.now()
    ts = _bucket_minute_10m_plus2(now)
    return f"{IMG_URL_BASE}{_build_filename(ts)}"


def try_head(url: str, timeout=(3, 5)) -> bool:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code < 400
    except requests.RequestException:
        return False


LAT = -53.79
LON = -67.70

API_KEY = "befacab068306913251d9c19fc38a1e6"


def latlon_to_tile_xy(lat, lon, zoom):
    """Convierte lat/lon a tile x,y en esquema webmercator."""
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
    tile_url = f"https://tile.openweathermap.org/map/{layer}/{zoom}/{x}/{y}.png?appid={API_KEY}"

    resp = requests.get(tile_url, timeout=15)
    if resp.status_code == 200:
        return resp.content
    else:
        if zoom > 0:
            return fetch_owm_tile(layer, zoom - 1)
        return None
