from fastapi import APIRouter, Response
from services.weather_service import get_weather

router = APIRouter()


@router.get("/clima")
def obtener_clima_owm():
    try:
        return get_weather()
    except Exception as e:
        return Response(content=f"No se pudo obtener el clima: {e}", status_code=502)
