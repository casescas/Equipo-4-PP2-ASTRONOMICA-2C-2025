import io
import numpy as np
from PIL import Image


def classify_octas(octas: int) -> tuple[str, str]:
    if octas == 0:
        return "SKC", "Cielo despejado"
    elif octas <= 2:
        return "FEW", "Pocas nubes"
    elif octas <= 4:
        return "SCT", "Nubes dispersas"
    elif octas <= 7:
        return "BKN", "Muy nublado"
    else:
        return "OVC", "Cubierto"


def preprocess_image_rgb224(img_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((224, 224))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)
