# backfill.py — Backfill concurrente (descargas paralelas, predict+DB secuencial)
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import sqlite3
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tensorflow.keras.models import load_model

from database import guardar_prediccion, DB_FILE
from utils.time_utils import bucket_10m_plus2
from utils.image_utils import image_url, filename_from_url
from utils.clouds_utils import classify_octas, preprocess_image_rgb224

IMG_URL_BASE = "http://201.251.63.225/meteorologia/cielo/image/"
MODEL_PATH = "models/600EPOC_modelo_octa.h5"

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = load_model(MODEL_PATH)
        print("✅ Modelo de octas cargado (backfill).")
    return _model


def _new_session():
    s = requests.Session()
    retry = Retry(
        total=1,
        backoff_factor=0.4,
        status_forcelist=(408, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=4)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


def _exists_filename(conn: sqlite3.Connection, filename: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM registro_historico WHERE filename = ? LIMIT 1", (filename,)
    )
    return cur.fetchone() is not None


def _make_url_for_ts(ts: datetime, use_year_dir: bool):
    ts_base, minute_real = bucket_10m_plus2(ts)
    return ts_base, image_url(
        IMG_URL_BASE, ts_base, minute_real, with_year_dir=use_year_dir
    )


def _download_one(ts: datetime, *, use_year_dir: bool) -> dict:
    """
    Descarga bytes para un timestamp. No levanta excepciones.
    Devuelve dict con ts_base, url, filename, content (o None) y reason si falló.
    """
    session = _new_session()
    ts_base, url = _make_url_for_ts(ts, use_year_dir)
    filename = filename_from_url(url)
    try:
        r = session.get(url, timeout=(2.5, 4.0), stream=False)
        if r.status_code == 200:
            return {
                "ok": True,
                "ts": ts_base,
                "url": url,
                "filename": filename,
                "content": r.content,
            }
        return {
            "ok": False,
            "ts": ts_base,
            "url": url,
            "filename": filename,
            "content": None,
            "reason": f"http_{r.status_code}",
        }
    except Exception as e:
        return {
            "ok": False,
            "ts": ts_base,
            "url": url,
            "filename": filename,
            "content": None,
            "reason": f"net:{e}",
        }


def _predict_and_insert(img_bytes: bytes, url: str, ts_base: datetime) -> dict:
    arr = preprocess_image_rgb224(img_bytes)
    model = _get_model()
    pred = model.predict(arr, verbose=0)
    clase = int(np.argmax(pred))
    conf = float(pred[0][clase])
    codigo, descripcion = classify_octas(clase)

    datos = {
        "octas_predichas": clase,
        "confianza": round(conf, 4),
        "categoria": codigo,
        "descripcion": descripcion,
        "imagen": url,
        "modelo_version": "600EPOC_modelo_octa.h5",
    }
    inserted = guardar_prediccion(datos)
    return {
        "ok": inserted,
        "duplicated": not inserted,
        "ts": ts_base.isoformat(),
        "url": url,
        "octas": clase,
        "confianza": round(conf, 4),
        "categoria": codigo,
    }


def backfill(desde: datetime, hasta: datetime, step_min: int, workers: int):
    if hasta < desde:
        raise SystemExit("`--hasta` debe ser >= `--desde`.")
    hasta_real = min(hasta, datetime.now())

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA cache_size=-20000;")
    except Exception:
        pass

    timestamps = []
    ts = desde
    skipped_dups = 0
    while ts <= hasta_real:
        ts_base, url = _make_url_for_ts(ts, use_year_dir=True)
        filename = filename_from_url(url)
        if not _exists_filename(conn, filename):
            timestamps.append(ts)
        else:
            skipped_dups += 1
        ts += timedelta(minutes=step_min)

    conn.close()

    total = len(timestamps)
    ok = dup = miss = 0

    if total == 0:
        print(
            f"\n📊 Backfill → no hay trabajo pendiente (duplicados saltados={skipped_dups})."
        )
        return

    futures = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for t in timestamps:
            futures.append(ex.submit(_download_one, t, use_year_dir=True))

        for fut in as_completed(futures):
            res = fut.result()
            if not res["ok"] or not res["content"]:
                miss += 1
                continue

            out = _predict_and_insert(res["content"], res["url"], res["ts"])
            if out["ok"]:
                ok += 1
            elif out.get("duplicated"):
                dup += 1
            else:
                miss += 1

    print(
        f"\n📊 Backfill → candidatos={total + skipped_dups} | saltados_por_PK={skipped_dups} | descargados+procesados={total} | nuevos={ok} | duplicados={dup} | fallidos={miss}"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Backfill de nubosidad (con descargas paralelas)."
    )
    p.add_argument("--desde", required=True, help="ISO: 2024-01-01T00:00")
    p.add_argument("--hasta", required=True, help="ISO: 2025-10-28T23:59")
    p.add_argument(
        "--step-min", type=int, default=10, help="Paso en minutos (10 por defecto)"
    )
    p.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Hilos de descarga paralela (3 por defecto)",
    )
    args = p.parse_args()

    d1 = datetime.fromisoformat(args.desde)
    d2 = datetime.fromisoformat(args.hasta)
    backfill(d1, d2, args.step_min, args.workers)
