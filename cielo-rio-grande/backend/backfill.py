# backfill.py — Backfill fijo (6 imágenes por hora)
import argparse
from datetime import datetime, timedelta
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from utils.image_utils import image_url
from services.clouds_service import save_prediction, predict_octas
from config.config import IMG_URL_BASE

MINUTOS_VALIDOS = [2, 12, 22, 32, 42, 52]


def _new_session():
    s = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=(408, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=2, pool_maxsize=2)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


def backfill(desde: datetime, hasta: datetime):
    if hasta < desde:
        raise SystemExit("`--hasta` debe ser >= `--desde`.")

    session = _new_session()
    total = ok = dup = miss = 0

    ts = desde.replace(minute=0, second=0, microsecond=0)
    hasta_real = hasta.replace(minute=0, second=0, microsecond=0)

    while ts <= hasta_real:
        for minuto in MINUTOS_VALIDOS:
            intento = ts.replace(minute=minuto)
            url_imagen = image_url(IMG_URL_BASE, intento, minuto, with_year_dir=True)

            try:
                resp = session.get(url_imagen, timeout=10)
            except Exception:
                miss += 1
                continue

            if resp.status_code != 200 or not resp.content:
                miss += 1
                continue

            pred = predict_octas(resp.content)

            data = {
                "octas_predichas": pred["octas_predichas"],
                "confianza": pred["confianza"],
                "categoria": pred["categoria"],
                "descripcion": pred["descripcion"],
                "imagen": url_imagen,
                "modelo_version": pred["modelo_version"],
            }

            inserted = save_prediction(data)
            if inserted:
                ok += 1
            else:
                dup += 1

            total += 1

        ts += timedelta(hours=1)

    print(
        f"\n📊 Backfill → total={total} | nuevos={ok} | duplicados={dup} | fallidos={miss}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill de nubosidad.")
    parser.add_argument("--desde", required=True, help="ISO: 2025-01-01T00:00")
    parser.add_argument("--hasta", required=True, help="ISO: 2025-10-29T00:00")
    args = parser.parse_args()

    d1 = datetime.fromisoformat(args.desde)
    d2 = datetime.fromisoformat(args.hasta)
    backfill(d1, d2)
