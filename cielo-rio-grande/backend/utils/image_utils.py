from datetime import datetime
import re
from datetime import datetime

_FILENAME_RE = re.compile(r"^(?P<year>\d{4})-(?P<rest>\d{8})\.jpg$")


def image_name(ts: datetime, minute_real: int) -> str:
    return f"{ts.year}-{ts.strftime('%m%d%H')}{minute_real:02d}.jpg"


def image_url(
    base: str, ts: datetime, minute_real: int, with_year_dir: bool = False
) -> str:
    """
    Construye URL con/sin carpeta del año (ambos casos los usás hoy).
    - job: with_year_dir=False  → http://.../image/{YYYY-MMDDHHmm}.jpg
    - backfill: with_year_dir=True → http://.../image/{YYYY}/{YYYY-MMDDHHmm}.jpg
    """
    name = image_name(ts, minute_real)
    if with_year_dir:
        return f"{base}{ts.year}/{name}"
    return f"{base}{name}"


def filename_from_url(url: str) -> str:
    """
    Extrae el nombre de archivo de una URL.
    Ej: http://.../2025/2025-10172322.jpg -> 2025-10172322.jpg
    """
    return url.rstrip("/").split("/")[-1]


def fecha_captura_from_filename(filename: str) -> datetime:
    """
    Convierte 'YYYY-MMDDHHmm.jpg' a datetime.
    Ej: '2025-10172322.jpg' -> 2025-10-17 23:22:00
    """
    m = _FILENAME_RE.match(filename)
    if not m:
        raise ValueError(f"Nombre inválido: {filename}")
    year = int(m.group("year"))
    rest = m.group("rest")  # MMDDHHmm
    dt_rest = datetime.strptime(rest, "%m%d%H%M")
    return dt_rest.replace(year=year)
