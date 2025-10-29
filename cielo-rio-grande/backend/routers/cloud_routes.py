from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from utils.time_utils import _parse_date

from services.clouds_service import (
    get_last_predict_service,
    get_historial_service,
)

router = APIRouter()


@router.get("/octas")
def get_last_predict():
    return get_last_predict_service()


@router.get("/historial")
def historial(
    desde: Optional[str] = Query(None, description="YYYY-MM-DD, ej: 2025-10-25"),
    hasta: Optional[str] = Query(None, description="YYYY-MM-DD, ej: 2025-10-27"),
):
    d1 = _parse_date(desde)
    d2 = _parse_date(hasta)

    if d1 and d2 and d2 < d1:
        raise HTTPException(status_code=400, detail="`hasta` debe ser >= `desde`")

    return get_historial_service(d1, d2)
