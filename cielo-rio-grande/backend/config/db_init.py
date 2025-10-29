import os
import sqlite3

DB_FILE = "./data/registros-octas.db"


def init_database() -> None:
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
                fecha_captura    DATETIME NOT NULL,
                octas_predichas  INTEGER NOT NULL,
                confianza        REAL    NOT NULL,
                categoria        TEXT    NOT NULL,
                descripcion      TEXT,
                modelo_version   TEXT,
                created_at       DATETIME NOT NULL
            );
            """
        )

        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_historial_fecha ON registro_historico(fecha_captura);"
        )

        print("✅ Tabla 'registro_historico' creada (PK = filename).")

    else:
        print(f"INFO: Usando DB existente {DB_FILE}.")

    conn.commit()
    conn.close()
