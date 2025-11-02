# backfill_dir.py — Procesa todas las imágenes del disco y guarda resultados en SQL
from __future__ import annotations

import argparse
import asyncio
import io
import time
from pathlib import Path
from typing import Tuple, Optional

from PIL import Image, ImageFile

from services.clouds_service import save_prediction, predict_octas


# -----------------------------
# Utilidades
# -----------------------------
def _is_valid_image(image_bytes: bytes) -> bool:
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            im.verify()
        return True
    except Exception:
        return False


async def _read_file_bytes(path: Path) -> Optional[bytes]:
    try:
        return await asyncio.to_thread(path.read_bytes)
    except Exception:
        return None


# -----------------------------
# Procesamiento de una imagen
# -----------------------------
async def _process_one(sem: asyncio.Semaphore, fpath: Path) -> Tuple[int, int, int]:
    async with sem:
        t0 = time.time()

        # Leer bytes
        t_io0 = time.time()
        img = await _read_file_bytes(fpath)
        if not img or not _is_valid_image(img):
            print(f"❌ {fpath.name} — imagen inválida ({time.time()-t_io0:.2f}s lectura)")
            return (1, 0, 1)
        t_io = time.time() - t_io0

        # Predicción
        t_pred0 = time.time()
        pred = await asyncio.to_thread(predict_octas, img)
        t_pred = time.time() - t_pred0

        # Guardado en DB
        t_save0 = time.time()
        data = {
            "octas_predichas": pred["octas_predichas"],
            "confianza": pred["confianza"],
            "categoria": pred["categoria"],
            "descripcion": pred["descripcion"],
            "imagen": f"file://{fpath.as_posix()}",
            "modelo_version": pred["modelo_version"],
        }
        inserted = await asyncio.to_thread(save_prediction, data)
        t_save = time.time() - t_save0

        total = time.time() - t0
        print(
            f"✅ {fpath.name} → leer={t_io:.2f}s | pred={t_pred:.2f}s | save={t_save:.2f}s | total={total:.2f}s"
        )
        return (1, 1 if inserted else 0, 0)


# -----------------------------
# Backfill principal
# -----------------------------
async def backfill_async(base_dir: Path, concurrency: int = 64):
    if not base_dir.exists():
        raise SystemExit(f"❌ Carpeta no encontrada: {base_dir}")

    # Listado recursivo de imágenes
    all_images = [p for p in base_dir.rglob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    print(f"📂 Carpeta: {base_dir}")
    print(f"🧭 Encontradas {len(all_images)} imágenes para procesar")

    ok = miss = total = 0
    sem = asyncio.Semaphore(concurrency)

    tasks = [asyncio.create_task(_process_one(sem, p)) for p in all_images]
    done = 0
    for coro in asyncio.as_completed(tasks):
        try:
            t, ok_n, miss_n = await coro
        except Exception as e:
            print(f"⚠️ Task falló: {e}")
            t, ok_n, miss_n = 1, 0, 1
        total += t
        ok += ok_n
        miss += miss_n
        done += 1
        if done % 100 == 0:
            print(f"[{done}/{len(all_images)}] procesadas…")

    print(f"\n📊 Resultado → total={total} | nuevas={ok} | fallidas={miss}")


# -----------------------------
# CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Procesa todas las imágenes de una carpeta local y guarda predicciones en SQL."
    )
    parser.add_argument(
        "--base-dir",
        default=r"D:\PROYECTO ASTRONÓMICA\Equipo-4-PP2-ASTRONOMICA-2C-2025\01.Data\01.Raw\imagenes_nubes_2025_Original",
        help="Directorio donde están las imágenes.",
    )
    parser.add_argument("--concurrency", type=int, default=64, help="Concurrencia (default: 64)")
    args = parser.parse_args()

    asyncio.run(backfill_async(Path(args.base_dir), concurrency=args.concurrency))


if __name__ == "__main__":
    main()
