from typing import Optional
from datetime import date
from fastapi import HTTPException

from datetime import datetime, timedelta


def bucket_10m_plus2(ts: datetime) -> tuple[datetime, int]:
    """
    - bucket = minuto//10
    - candidato = bucket*10 + 2
    - si candidato > minuto_actual => retrocede 10'
    Devuelve (ts_posiblemente_ajustado, minuto_real)
    """
    base = ts
    bucket = base.minute // 10
    candidato = bucket * 10 + 2

    if candidato > base.minute:
        bucket -= 1
        if bucket < 0:
            base = base - timedelta(hours=1)
            bucket = 5
        candidato = bucket * 10 + 2

    return base, candidato


def _parse_date(s: Optional[str]) -> Optional[date]:
    if s is None:
        return None
    try:
        return date.fromisoformat(s)  # espera YYYY-MM-DD
    except Exception:
        raise HTTPException(
            status_code=400, detail=f"Fecha inválida (usa YYYY-MM-DD): {s}"
        )
