# backfill.py
import argparse
import time
from datetime import datetime, timedelta
import sqlite3
import io
import requests
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

from database import intentar_registrar_prediccion, DB_FILE

IMG_URL_BASE = "http://201.251.63.225/meteorologia/cielo/image/"
MODEL_PATH = "models/600EPOC_modelo_octa.h5"

# ↓ Ajustá este sleep si querés acelerar (0.5 es razonable)
REQUEST_SLEEP_SECONDS = 0.25

modelo = load_model(MODEL_PATH)
print("✅ Modelo cargado para backfill.")


def preparar_db(conn: sqlite3.Connection):
    """Garantiza índice único para evitar duplicados exactos."""
    cur = conn.cursor()
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_registro_historico_fecha
        ON registro_historico(fecha_hora_prediccion)
    """)
    conn.commit()


def url_imagen_para(ts: datetime):
    """
    Construye la URL respetando la estructura del servidor:
    /meteorologia/cielo/image/<AÑO>/<YYYY>-<MMDDHH><mm>.jpg
    donde mm = bucket*10 + 2 (00, 02, 12, 22, 32, 42, 52)
    """
    bucket = ts.minute // 10
    candidato = bucket * 10 + 2
    if candidato > ts.minute:
        bucket -= 1
        if bucket < 0:
            ts -= timedelta(hours=1)
            bucket = 5
        candidato = bucket * 10 + 2

    nombre = f"{ts.year}-{ts.strftime('%m%d%H')}{candidato:02d}.jpg"
    url = f"{IMG_URL_BASE}{ts.year}/{nombre}"  # ← carpeta del año
    return ts, url


def clasificar(octas: int):
    if octas == 0:
        return "SKC", "Cielo despejado"
    elif octas <= 2:
        return "FEW", "Pocas nubes"
    elif octas <= 4:
        return "SCT", "Nubes dispersas"
    elif octas <= 7:
        return "BKN", "Muy nublado"
    else:
        return "OVC", "Cubierto"


def procesar_timestamp(ts_objetivo: datetime, modo: str, conn: sqlite3.Connection):
    """
    Intenta la imagen del timestamp o hasta 6 buckets atrás (1h).
    Usa la URL con carpeta por año y nombre YYYY-MMDDHHmm.jpg (mm = bucket*10 + 2).
    """
    respuesta = None
    url_valida = None
    ts_usado = None

    for retro in range(0, 6):  # 0,10,20,30,40,50 minutos hacia atrás
        ts_cand = ts_objetivo - timedelta(minutes=retro * 10)
        ts_aj, url = url_imagen_para(ts_cand)
        time.sleep(REQUEST_SLEEP_SECONDS)  # anti-ban
        try:
            resp = requests.get(url, timeout=10)
        except Exception as e:
            print(f"⚠️  {ts_aj} | error de red: {e}")
            continue
        if resp.status_code == 200:
            respuesta = resp
            url_valida = url
            ts_usado = ts_aj
            break

    if respuesta is None:
        print(f"⏭️ {ts_objetivo} | sin imagen en ±1h (404).")
        return False

    # Preprocesado y predicción
    img = Image.open(io.BytesIO(respuesta.content)).convert("RGB").resize((224, 224))
    arr = image.img_to_array(img) / 255.0
    arr = np.expand_dims(arr, axis=0).astype("float32")

    pred = modelo.predict(arr, verbose=0)
    clase = int(np.argmax(pred))
    conf = float(pred[0][clase])
    codigo, descripcion = clasificar(clase)

    ts_norm = ts_usado.replace(second=0, microsecond=0)

    datos = {
        "octas_predichas": clase,
        "confianza": round(conf, 4),
        "categoria": codigo,
        "descripcion": descripcion,
        "imagen": url_valida,  # URL válida encontrada
    }

    if modo == "respetar_hora":
        return intentar_registrar_prediccion(datos, ts_norm)

    # modo forzar → UPSERT para evitar duplicados
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO registro_historico
              (fecha_hora_prediccion, octas_predichas, confianza, categoria, descripcion, url_imagen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(fecha_hora_prediccion) DO UPDATE SET
              octas_predichas = excluded.octas_predichas,
              confianza       = excluded.confianza,
              categoria       = excluded.categoria,
              descripcion     = excluded.descripcion,
              url_imagen      = excluded.url_imagen
            """,
            (
                ts_norm.isoformat(timespec="minutes"),
                datos["octas_predichas"],
                datos["confianza"],
                datos["categoria"],
                datos["descripcion"],
                datos["imagen"],
            ),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error SQLite en {ts_norm}: {e}")
        return False


def backfill(desde: datetime, hasta: datetime, step_min: int, modo: str):
    if hasta < desde:
        raise SystemExit("`--hasta` debe ser >= `--desde`.")
    hasta_real = min(hasta, datetime.now())  # no pedir futuro

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    preparar_db(conn)

    ts = desde
    total = ok = 0
    consecutivos_sin = 0

    while ts <= hasta_real:
        exito = procesar_timestamp(ts, modo, conn)
        if exito:
            ok += 1
            consecutivos_sin = 0
            print(f"✅ {ts} → guardado ({modo})")
        else:
            consecutivos_sin += 1

        total += 1
        if consecutivos_sin >= 30:
            print("⚠️  30 intentos seguidos sin imagen. Corto (probable rango sin archivos).")
            break

        ts += timedelta(minutes=step_min)

    conn.close()
    print(f"\n📊 Backfill: {ok}/{total} registros.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Backfill de /octas con rango explícito.")
    p.add_argument("--desde", required=True, help="ISO: 2025-01-01T00:00")
    p.add_argument("--hasta", required=True, help="ISO: 2025-01-31T23:59")
    p.add_argument("--step-min", type=int, default=10, help="Paso en minutos (10 por defecto)")
    p.add_argument("--modo", choices=["forzar", "respetar_hora"], default="forzar")
    args = p.parse_args()

    d1 = datetime.fromisoformat(args.desde)
    d2 = datetime.fromisoformat(args.hasta)
    backfill(d1, d2, args.step_min, args.modo)
