# backfill.py — Backfill ultrarrápido (asyncio + aiohttp) con hedged requests y tiempos por imagen
from __future__ import annotations

import argparse
import asyncio
import io
import time
from datetime import datetime, timedelta
from typing import Iterable, List, Tuple, Optional, Set

import aiohttp
from aiohttp import ClientSession, TCPConnector, ClientTimeout
from PIL import Image, ImageFile

from utils.image_utils import image_url, filename_from_url
from services.clouds_service import (
    save_prediction,
    predict_octas,
    get_existing_filenames,
)
from config.config import IMG_URL_BASE

MINUTOS_VALIDOS = [2, 12, 22, 32, 42, 52]


def _iter_timestamps(desde: datetime, hasta: datetime) -> Iterable[datetime]:
    start_hour = desde.replace(minute=0, second=0, microsecond=0)
    end_hour = hasta.replace(minute=0, second=0, microsecond=0)
    ts = start_hour
    while ts <= end_hour:
        mins = MINUTOS_VALIDOS
        if ts == start_hour:
            mins = [m for m in mins if ts.replace(minute=m) >= desde]
        if ts == end_hour:
            mins = [m for m in mins if ts.replace(minute=m) <= hasta]
        for m in mins:
            yield ts.replace(minute=m, second=0, microsecond=0)
        ts += timedelta(hours=1)


# -----------------------------
# Hedged requests (latencia baja)
# -----------------------------
async def _fetch_once(session: ClientSession, url: str) -> Optional[bytes]:
    try:
        async with session.get(
            url,
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
            if not data:
                return None
            cl = resp.headers.get("Content-Length")
            if cl is not None and len(data) < int(cl):
                return None
            return data
    except Exception:
        return None


async def _fetch_bytes(
    session: ClientSession,
    url: str,
    *,
    retries: int = 2,
    hedge_delay: float = 0.8,
) -> Optional[bytes]:
    """
    Dispara 2 GET casi en paralelo y toma el primero válido (hedged requests).
    Repite 'retries' rondas si ninguna da resultado.
    """
    attempt = 0
    while attempt <= retries:
        t1 = asyncio.create_task(_fetch_once(session, url))
        await asyncio.sleep(hedge_delay)
        t2 = asyncio.create_task(_fetch_once(session, url))

        done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)

        result = None
        for d in done:
            try:
                result = d.result()
            except Exception:
                result = None

        if result:
            for p in pending:
                p.cancel()
            return result

        # si el primero que terminó no sirvió, esperá al otro por si trae algo
        still = [p for p in pending if not p.cancelled()]
        if still:
            done2, _ = await asyncio.wait(set(still), return_when=asyncio.ALL_COMPLETED)
            for d in done2:
                try:
                    result = d.result()
                except Exception:
                    result = None
                if result:
                    return result

        attempt += 1
        await asyncio.sleep(0.3 * attempt)  # backoff corto entre rondas

    return None


def _is_valid_image(image_bytes: bytes) -> bool:
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            im.verify()
        return True
    except Exception:
        return False


async def _process_one(
    sem: asyncio.Semaphore,
    session: ClientSession,
    ts: datetime,
) -> Tuple[int, int, int]:
    async with sem:
        url = image_url(IMG_URL_BASE, ts, ts.minute, with_year_dir=True)
        t0 = time.time()

        # Descarga (hedged)
        t_dl0 = time.time()
        img = await _fetch_bytes(session, url)
        if not img or not _is_valid_image(img):
            # segunda oportunidad (otra ronda de hedged)
            img = await _fetch_bytes(session, url)
            if not img or not _is_valid_image(img):
                print(f"❌ {url} — imagen inválida ({time.time()-t_dl0:.2f}s descarga)")
                return (1, 0, 1)
        t_dl = time.time() - t_dl0

        # Predicción
        t_pred0 = time.time()
        pred = await asyncio.to_thread(predict_octas, img)
        t_pred = time.time() - t_pred0

        # Guardado
        t_save0 = time.time()
        data = {
            "octas_predichas": pred["octas_predichas"],
            "confianza": pred["confianza"],
            "categoria": pred["categoria"],
            "descripcion": pred["descripcion"],
            "imagen": url,
            "modelo_version": pred["modelo_version"],
        }
        inserted = await asyncio.to_thread(save_prediction, data)
        t_save = time.time() - t_save0

        total = time.time() - t0
        print(
            f"✅ {url.split('/')[-1]} → descarga={t_dl:.2f}s | pred={t_pred:.2f}s | "
            f"save={t_save:.2f}s | total={total:.2f}s"
        )
        return (1, 1 if inserted else 0, 0)


async def backfill_async(
    desde: datetime,
    hasta: datetime,
    concurrency: int = 96,
    connect_timeout: float = 3.0,   # quedan por compatibilidad, pero no imponemos total
    read_timeout: float = 10.0,     # idem
    user_agent: str = "CieloRioGrande-BackfillAsync/1.0",
):
    if hasta < desde:
        raise SystemExit("`--hasta` debe ser >= `--desde`.")

    all_ts = list(_iter_timestamps(desde, hasta))
    print(f"🕒 Generados {len(all_ts)} timestamps para procesar")

    existing: Set[str] = get_existing_filenames(desde, hasta)
    remaining_ts: List[datetime] = []
    pre_skipped = total = 0

    for ts in all_ts:
        url = image_url(IMG_URL_BASE, ts, ts.minute, with_year_dir=True)
        fname = filename_from_url(url)
        if fname in existing:
            pre_skipped += 1
            total += 1
        else:
            remaining_ts.append(ts)

    print(f"🚀 A procesar {len(remaining_ts)} imágenes nuevas (saltadas {pre_skipped})")

    ok = miss = 0
    if remaining_ts:
        # Sin límite total de tiempo; usamos keep-alive y cache DNS
        timeout = ClientTimeout(total=None)
        connector = TCPConnector(
            limit=0,
            limit_per_host=concurrency,
            enable_cleanup_closed=True,
            ttl_dns_cache=300,
            keepalive_timeout=30,
        )
        headers = {"User-Agent": user_agent, "Connection": "keep-alive"}

        sem = asyncio.Semaphore(concurrency)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector, headers=headers) as session:
            tasks = [asyncio.create_task(_process_one(sem, session, ts)) for ts in remaining_ts]
            done = 0
            for coro in asyncio.as_completed(tasks):
                try:
                    t, ok_n, miss_n = await coro
                except Exception as e:
                    print(f"⚠️  Task falló: {e}")
                    t, ok_n, miss_n = 1, 0, 1
                total += t
                ok += ok_n
                miss += miss_n
                done += 1
                if done % 200 == 0:
                    print(f"[{done}/{len(remaining_ts)}] procesadas…")

    print(
        f"\n📊 Backfill (async) → total={total} | nuevos={ok} | fallidos_req={miss} | "
        f"saltados_preDB={pre_skipped}"
    )


def main():
    parser = argparse.ArgumentParser(description="Backfill de nubosidad (async, hedged requests, tiempos detallados).")
    parser.add_argument("--desde", required=True, help="ISO: 2025-01-01T00:00")
    parser.add_argument("--hasta", required=True, help="ISO: 2025-11-02T23:59")
    parser.add_argument("--concurrency", type=int, default=96, help="Concurrencia (default: 96)")
    parser.add_argument("--connect-timeout", type=float, default=3.0, help="Timeout de conexión (s)")  # keep for compat
    parser.add_argument("--read-timeout", type=float, default=10.0, help="Timeout de lectura (s)")      # keep for compat
    args = parser.parse_args()

    d1 = datetime.fromisoformat(args.desde)
    d2 = datetime.fromisoformat(args.hasta)

    asyncio.run(
        backfill_async(
            d1,
            d2,
            concurrency=args.concurrency,
            connect_timeout=args.connect_timeout,
            read_timeout=args.read_timeout,
        )
    )


if __name__ == "__main__":
    main()
