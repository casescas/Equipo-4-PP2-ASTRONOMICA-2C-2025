# app/services/clouds_service.py
from __future__ import annotations
import sqlite3
import time
from datetime import date, datetime, time as dtime
from typing import Any, Dict, List, Optional, Tuple, Set
from pytz import timezone
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from torchvision.models import efficientnet_b0
import torch.nn as nn
from utils.image_utils import filename_from_url, fecha_captura_from_filename
from utils.clouds_utils import classify_octas
from config.config import OCTAS_MODEL_PATH, DB_FILE, TZ
import os
import io

# --- Carga del modelo PyTorch ---
_model = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _get_model():
    """
    Carga el modelo EfficientNet_B0 + pesos personalizados.
    """
    global _model
    if _model is None:
        print(f"🧠 Cargando modelo PyTorch desde: {OCTAS_MODEL_PATH}")

        # 1) reconstruir arquitectura EXACTA
        model = efficientnet_b0(weights=None)

        # 2) reemplazar la capa final (ajustar si tu modelo usa otro número)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, 9)

        # 3) cargar pesos entrenados
        state_dict = torch.load(OCTAS_MODEL_PATH, map_location=_device)

        # si los pesos vienen de un modelo con DataParallel
        if "module." in list(state_dict.keys())[0]:
            state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}

        model.load_state_dict(state_dict, strict=False)

        # 4) mover a device y poner en eval
        _model = model.to(_device)
        _model.eval()

        print("✅ Modelo cargado correctamente.")

    return _model


# --- Conexión a la base de datos (robusta para alta concurrencia) ---
def _conn():
    # timeout: cuánto esperar si la DB está ocupada
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Mejoras de concurrencia y rendimiento
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")  # 5s de espera en locks
    return conn


TZ = timezone(TZ)


def _now_local_iso_minutes() -> str:
    return datetime.now(TZ).isoformat(timespec="minutes")


def _day_bounds(d: date) -> Tuple[str, str]:
    start = datetime.combine(d, dtime.min).isoformat()
    end = datetime.combine(d, dtime.max).isoformat()
    return start, end


# --- Servicios de consulta ---
def get_last_predict_service() -> List[Dict[str, Any]]:
    conn = _conn()
    try:
        cur = conn.execute(
            """
            SELECT *
            FROM registro_historico
            ORDER BY datetime(fecha_captura) DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        return row
    finally:
        conn.close()


def get_historial_service(
    desde: Optional[date], hasta: Optional[date]
) -> Dict[str, Any]:
    where, params = [], []
    if desde:
        ini, _ = _day_bounds(desde)
        where.append("fecha_captura >= ?")
        params.append(ini)
    if hasta:
        _, fin = _day_bounds(hasta)
        where.append("fecha_captura <= ?")
        params.append(fin)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    conn = _conn()
    try:
        cur = conn.execute(
            f"""
            SELECT *
            FROM registro_historico
            {where_sql}
            ORDER BY datetime(fecha_captura) ASC
            """,
            params,
        )
        items = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    return {
        "desde": desde.isoformat() if desde else None,
        "hasta": hasta.isoformat() if hasta else None,
        "items": items,
    }


# --- Guardado de predicción (con retry si la DB está bloqueada) ---
def save_prediction(datos: Dict[str, Any]) -> bool:
    url = datos["imagen"]
    filename = filename_from_url(url)
    fecha_local = fecha_captura_from_filename(filename)
    fecha_captura = fecha_local.isoformat(timespec="minutes")

    conn = None
    try:
        conn = _conn()
        for attempt in range(6):  # pequeños reintentos (≈ 0.9s total máx)
            try:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO registro_historico
                        (filename, url_imagen, fecha_captura,
                         octas_predichas, confianza, categoria, descripcion, modelo_version, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        filename,
                        url,
                        fecha_captura,
                        int(datos["octas_predichas"]),
                        float(datos["confianza"]),
                        str(datos["categoria"]),
                        datos.get("descripcion"),
                        datos.get("modelo_version"),
                        _now_local_iso_minutes(),
                    ),
                )
                conn.commit()
                break
            except sqlite3.OperationalError as e:
                # Manejo de locks (database is locked)
                if "locked" in str(e).lower():
                    time.sleep(0.05 * (attempt + 1))  # 50ms, 100ms, ...
                    continue
                raise

        if cur.rowcount == 0:
            print(f"{filename} ya existía, omitido.")
            return False

        print(f"{filename} guardado correctamente.")
        return True

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ERROR al guardar {filename}: {e}")
        return False

    finally:
        if conn:
            conn.close()


# --- Predicción con PyTorch ---
def predict_octas(image_bytes: bytes) -> Dict[str, Any]:
    # Permite cargar imágenes parcialmente truncadas sin romper el flujo
    from PIL import ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    # Preprocesamiento de imagen
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    try:
        # Cargar imagen en memoria y convertir a RGB
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        print(f"⚠️  Imagen inválida/truncada no recuperable: {e}")
        raise

    # Transformar la imagen para el modelo
    img_tensor = transform(image).unsqueeze(0).to(_device)

    # Obtener el modelo cargado (en memoria global)
    model = _get_model()

    # Inferencia sin gradientes
    with torch.no_grad():
        outputs = model(img_tensor)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        clase = int(torch.argmax(probs, dim=1).item())
        conf = float(torch.max(probs).item())

    # Interpretar resultado según sistema OCTAS
    codigo, descripcion = classify_octas(clase)

    return {
        "octas_predichas": clase,
        "confianza": round(conf, 4),
        "categoria": codigo,
        "descripcion": descripcion,
        "modelo_version": os.path.basename(OCTAS_MODEL_PATH),
    }


def exists_record_by_filename(filename: str) -> bool:
    conn = _conn()
    try:
        cur = conn.execute(
            "SELECT 1 FROM registro_historico WHERE filename = ? LIMIT 1",
            (filename,),
        )
        print("Skipeando prediccion, ya existe")
        return cur.fetchone() is not None
    finally:
        conn.close()


# --- Pre-skip masivo para backfill ---
def get_existing_filenames(desde: datetime, hasta: datetime) -> Set[str]:
    """
    Devuelve un set con todos los filenames existentes entre 'desde' y 'hasta'.
    Mejora el rendimiento del backfill al evitar consultas una por una.
    """
    conn = _conn()
    try:
        cur = conn.execute(
            """
            SELECT filename
            FROM registro_historico
            WHERE fecha_captura BETWEEN ? AND ?
            """,
            (desde.isoformat(), hasta.isoformat()),
        )
        rows = cur.fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()
