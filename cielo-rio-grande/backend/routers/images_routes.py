from fastapi import APIRouter
from datetime import datetime, timedelta
from fastapi.responses import RedirectResponse, StreamingResponse, Response
import io
from services.images_service import latest_image_url, try_head
from utils.satellite_utils import fetch_owm_tile

router = APIRouter()


@router.get("/imagen")
def obtener_imagen(ts: int = 0):
    url = latest_image_url(datetime.now())

    if not try_head(url):
        url = latest_image_url(
            datetime.now().replace(minute=(datetime.now().minute // 10) * 10)
            - timedelta(minutes=10)
        )
    return RedirectResponse(url)


@router.get("/satellite")
def obtener_satelite():
    try:
        img_bytes = fetch_owm_tile(layer="clouds_new", zoom=4)
        if not img_bytes:
            return Response(
                content="No se pudo obtener la imagen satelital", status_code=404
            )

        return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")

    except Exception as e:
        return Response(content=f"Error interno: {e}", status_code=500)


IMG_URL_BASE = "http://201.251.63.225/meteorologia/cielo/image/"
