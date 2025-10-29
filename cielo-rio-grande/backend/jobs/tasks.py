from datetime import datetime
from fastapi import Response
import requests

from utils.time_utils import bucket_10m_plus2
from utils.image_utils import image_url
from services.clouds_service import save_prediction, predict_octas

IMG_URL_BASE = "http://201.251.63.225/meteorologia/cielo/image/"


def predict_octas_task():
    ahora = datetime.now()
    print(ahora, "predict octas pipeline")

    ts_base, minuto_real = bucket_10m_plus2(ahora)
    url_imagen = image_url(IMG_URL_BASE, ts_base, minuto_real, with_year_dir=False)

    resp = requests.get(url_imagen, timeout=10)
    if resp.status_code != 200:
        return Response(
            content=f"No se pudo descargar la imagen: {resp.status_code}",
            status_code=resp.status_code,
        )

    pred = predict_octas(resp.content)

    data = {
        "octas_predichas": pred["octas_predichas"],
        "confianza": pred["confianza"],
        "categoria": pred["categoria"],
        "descripcion": pred["descripcion"],
        "imagen": url_imagen,
        "modelo_version": pred["modelo_version"],
    }

    save_prediction(data)
