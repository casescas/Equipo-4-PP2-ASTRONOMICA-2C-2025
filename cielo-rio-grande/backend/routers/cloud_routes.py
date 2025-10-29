from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, time
import sqlite3
from utils.time_utils import _parse_date
from typing import Optional

router = APIRouter()

try:
    from database import DB_FILE
except Exception:
    DB_FILE = "registros-octas.db"


@router.get("/octas")
def get_last_predict():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            f"""
            SELECT *
            FROM registro_historico
            ORDER BY fecha_captura ASC limit  1
            """,
        )
        item = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    return item[0]


@router.get("/historial")
def historial(
    desde: Optional[str] = Query(None, description="YYYY-MM-DD, ej: 2025-10-25"),
    hasta: Optional[str] = Query(None, description="YYYY-MM-DD, ej: 2025-10-27"),
):
    d1 = _parse_date(desde)
    d2 = _parse_date(hasta)
    if d1 and d2 and d2 < d1:
        raise HTTPException(status_code=400, detail="`hasta` debe ser >= `desde`")

    # Convertimos a límites de día
    where, params = [], []
    if d1:
        ini = datetime.combine(d1, time.min).isoformat()
        where.append("fecha_captura >= ?")
        params.append(ini)
    if d2:
        fin = datetime.combine(d2, time.max).isoformat()
        where.append("fecha_captura <= ?")
        params.append(fin)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
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
        "desde": d1.isoformat() if d1 else None,
        "hasta": d2.isoformat() if d2 else None,
        "items": items,
    }
