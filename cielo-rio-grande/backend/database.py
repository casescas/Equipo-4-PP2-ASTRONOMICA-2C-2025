import os
import sqlite3
from utils.image_utils import filename_from_url, fecha_captura_from_filename

DB_FILE = "./data/registros-octas.db"


def inicializar_db() -> None:
    db_existe = os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    if not db_existe:
        print(f"INFO: Creando base en {DB_FILE}...")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS registro_historico (
                filename         TEXT PRIMARY KEY,
                url_imagen       TEXT NOT NULL,
                fecha_captura    TEXT NOT NULL,
                octas_predichas  INTEGER NOT NULL,
                confianza        REAL    NOT NULL,
                categoria        TEXT    NOT NULL,
                descripcion      TEXT,
                modelo_version   TEXT,
                created_at       TEXT    NOT NULL DEFAULT (CURRENT_TIMESTAMP)
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_historial_fecha ON registro_historico(fecha_captura);"
        )
        print("✅ Tabla 'registro_historico' creada (PK=filename).")
    else:
        print(f"INFO: Usando DB existente {DB_FILE}.")

    conn.commit()
    conn.close()


def guardar_prediccion(datos: dict) -> bool:
    """
    Inserta una predicción si no existe (idempotente).
    Espera:
      datos = {
        'octas_predichas': int,
        'confianza': float,
        'categoria': str,
        'descripcion': str | None,
        'imagen': str,              # URL completa
        'modelo_version': str | None
      }
    Retorna True si insertó, False si ya existía o hubo conflicto.
    """
    url = datos["imagen"]
    filename = filename_from_url(url)
    fecha_captura = fecha_captura_from_filename(filename).isoformat(timespec="minutes")

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO registro_historico
                (filename, url_imagen, fecha_captura,
                 octas_predichas, confianza, categoria, descripcion, modelo_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                url,
                fecha_captura,
                datos["octas_predichas"],
                datos["confianza"],
                datos["categoria"],
                datos.get("descripcion"),
                datos.get("modelo_version"),
            ),
        )
        conn.commit()

        if cur.rowcount == 0:
            print(f"ℹ{filename} ya existía, omitido.")
            return False

        print(f"{filename} guardado correctamente.")
        return True

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ ERROR al guardar {filename}: {e}")
        return False

    finally:
        if conn:
            conn.close()
