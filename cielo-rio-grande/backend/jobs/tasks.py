from datetime import datetime, timedelta
from database import guardar_prediccion
from fastapi import Response
import requests
from pytz import timezone
from tensorflow.keras.models import load_model
import numpy as np

from utils.time_utils import bucket_10m_plus2
from utils.image_utils import image_url
from utils.clouds_utils import classify_octas, preprocess_image_rgb224

IMG_URL_BASE = "http://201.251.63.225/meteorologia/cielo/image/"
modelo = load_model("models/600EPOC_modelo_octa.h5")
print("✅ Modelo de octas cargado correctamente.")
TZ = timezone("America/Argentina/Buenos_Aires")


def predict_octas():
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

    img_array = preprocess_image_rgb224(resp.content)

    prediccion = modelo.predict(img_array)
    clase_predicha = int(np.argmax(prediccion))
    probabilidad = float(prediccion[0][clase_predicha])

    codigo, descripcion = classify_octas(clase_predicha)

    datos_para_registrar = {
        "octas_predichas": clase_predicha,
        "confianza": round(probabilidad, 4),
        "categoria": codigo,
        "descripcion": descripcion,
        "imagen": url_imagen,
        "modelo_version": "600EPOC_modelo_octa.h5",
    }

    guardar_prediccion(datos_para_registrar)
