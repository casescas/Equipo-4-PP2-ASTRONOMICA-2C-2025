import requests
import numpy as np
import cv2
from datetime import datetime

def obtener_imagen_actual():
    now = datetime.now()
    minutes = (now.minute // 10) * 10
##    url_timestamp = now.strftime(f"%Y-%m%d%H") + f"{minutes:02d}"
    url = f"http://201.251.63.225/meteorologia/cielo/image/2025-10172042.jpg"
    headers = {'User-Agent': 'Mozilla/5.0'}

    resp = requests.get(url, headers=headers, stream=True)
    if resp.status_code == 200:
        return resp.content  # retornamos bytes
    return None
