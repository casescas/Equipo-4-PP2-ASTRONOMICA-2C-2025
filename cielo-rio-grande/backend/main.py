from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
import requests
from datetime import datetime, timedelta
import os
import io
from fastapi.responses import JSONResponse
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import numpy as np
# 
from database import inicializar_db, intentar_registrar_prediccion
# 
from datetime import datetime, timedelta
#
from typing import Optional
from datetime import datetime, timedelta, date, time
from fastapi import Query, HTTPException
import sqlite3



# Cargar modelo al iniciar la app
modelo = load_model("models/600EPOC_modelo_octa.h5")
print("✅ Modelo de octas cargado correctamente.")

# ✅ Importamos la función desde tu módulo utils/satellite.py
from utils.satellite import fetch_owm_tile

app = FastAPI()

@app.on_event("startup")
def on_startup():
    """
    Función que se ejecuta una sola vez al iniciar el servidor FastAPI.

    """
    print("INFO: Iniciando servidor FastAPI...")
    inicializar_db()


# 🔒 Configuración de CORS (permite que React acceda al backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción conviene restringir al dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 Clave directa de OpenWeatherMap 
OWM_API_KEY = "befacab068306913251d9c19fc38a1e6"  
LAT, LON = -53.7877, -67.7093

@app.get("/clima")
def obtener_clima_owm():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&units=metric&lang=es&appid={OWM_API_KEY}"
    resp = requests.get(url, timeout=10)

    if resp.status_code == 200:
        data = resp.json()
        return {
            "temp": data["main"]["temp"],
            "humedad": data["main"]["humidity"],
            "viento": data["wind"]["speed"],
            "nubosidad_api": data["clouds"]["all"],
            "descripcion": data["weather"][0]["description"].capitalize()
        }
    else:
        return Response(
            content=f"No se pudo obtener el clima: {resp.status_code} {resp.text}",
            status_code=resp.status_code
        )

# ☁️ Endpoint para obtener la imagen actual del cielo
@app.get("/imagen")
def obtener_imagen(ts: int = 0):
    """
    Devuelve Redirect a la última imagen disponible en la secuencia:
    minutos: 02, 12, 22, 32, 42, 52
    Asegura que la imagen devuelta tenga minuto <= minuto_actual (es decir,
    la última ya subida).
    El parámetro ts solo sirve para evitar caché en el frontend.
    """
    url_base = "http://201.251.63.225/meteorologia/cielo/image/"

    ahora = datetime.now()

    # calcular el "bucket" de 10 minutos y el candidato con +2
    bucket = ahora.minute // 10
    candidato = bucket * 10 + 2

    # si el candidato está en el futuro (mayor que el minuto actual),
    # retroceder un bucket (posible ajuste de hora)
    if candidato > ahora.minute:
        bucket -= 1
        if bucket < 0:
            # retroceder una hora
            ahora = ahora - timedelta(hours=1)
            bucket = 5  # último bucket de la hora anterior (52 -> 5*10 + 2)
        candidato = bucket * 10 + 2

    minuto_real = candidato  # 02,12,22,32,42 o 52

    # Formato de nombre observado: 2025-10172322.jpg  (guion sólo después del año)
    # Construimos: YYYY- + MMDDHH + MMminuto
    nombre_imagen = f"{ahora.year}-{ahora.strftime('%m%d%H')}{minuto_real:02d}.jpg"
    url_imagen = f"{url_base}{nombre_imagen}"

    # debug en consola
    print(f"🔄 Redirigiendo a la última imagen disponible: {url_imagen}")

    return RedirectResponse(url_imagen)

##OWM_API_KEY = os.getenv("befacab068306913251d9c19fc38a1e6")  # tu API key de OpenWeatherMap

# 🛰️ Endpoint para la imagen satelital
@app.get("/satellite")
def obtener_satelite():
    """
    Devuelve una imagen satelital (tile) centrada en Río Grande
    obtenida desde OpenWeatherMap.
    """
    try:
        img_bytes = fetch_owm_tile(layer="clouds_new", zoom=4)
        if not img_bytes:
            return Response(content="No se pudo obtener la imagen satelital", status_code=404)

        return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")

    except Exception as e:
        return Response(content=f"Error interno: {e}", status_code=500)

IMG_URL_BASE = "http://201.251.63.225/meteorologia/cielo/image/"

@app.get("/octas")
def predecir_octas(ts: int = 0):
    """
    Descarga la última imagen del cielo, la procesa y predice el nivel de octas
    usando el modelo 600EPOC_modelo_octa.h5.
    Devuelve también la categoría FEW/SCT/BKN/OVC y su descripción.
    """
    from datetime import datetime, timedelta
    ahora = datetime.now()
    bucket = ahora.minute // 10
    candidato = bucket * 10 + 2
    if candidato > ahora.minute:
        bucket -= 1
        if bucket < 0:
            ahora -= timedelta(hours=1)
            bucket = 5
        candidato = bucket * 10 + 2
    minuto_real = candidato
    nombre_imagen = f"{ahora.year}-{ahora.strftime('%m%d%H')}{minuto_real:02d}.jpg"
    url_imagen = f"{IMG_URL_BASE}{nombre_imagen}"

    # Descargar la imagen
    resp = requests.get(url_imagen, timeout=10)
    if resp.status_code != 200:
        return Response(
            content=f"No se pudo descargar la imagen: {resp.status_code}",
            status_code=resp.status_code
        )

    # Cargar y preprocesar imagen
    img = Image.open(io.BytesIO(resp.content)).convert('RGB')
    img = img.resize((224, 224))
    img_array = image.img_to_array(img)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0).astype('float32')

    # Predicción con el modelo
    prediccion = modelo.predict(img_array)
    print(prediccion)
    clase_predicha = int(np.argmax(prediccion))  # octas 0–8
    probabilidad = float(prediccion[0][clase_predicha])  # confianza

    # Clasificación según rango
    if clase_predicha == 0: 
        codigo, descripcion = "SKC", "Cielo despejado"
    elif clase_predicha <= 2:
        codigo, descripcion = "FEW", "Pocas nubes"
    elif clase_predicha <= 4:
        codigo, descripcion = "SCT", "Nubes dispersas"
    elif clase_predicha <= 7:
        codigo, descripcion = "BKN", "Muy nublado"
    else:
        codigo, descripcion = "OVC", "Cubierto"

    # --- INICIO BLOQUE NUEVO PARA REGISTRO DB ---
    
    # 1. Empaquetar los datos de la predicción en un diccionario
    datos_para_registrar = {
        "octas_predichas": clase_predicha,
        "confianza": round(probabilidad, 4),
        "categoria": codigo,
        "descripcion": descripcion,
        "imagen": url_imagen
    }
    
    # 2. Intentar el registro (la función interna maneja la lógica de 1 hora)
    #    Pasamos 'ahora', que es el datetime que capturamos al inicio de la función.
    intentar_registrar_prediccion(datos_para_registrar, ahora)
    
    # 3. Devolver la respuesta al usuario (igual que antes)
    return JSONResponse(datos_para_registrar)

# ---- HISTORIAL  ----------------------------------------


try:
    from database import DB_FILE
except Exception:
    DB_FILE = "registros-octas.db"

def _parse_date(s: Optional[str]) -> Optional[date]:
    if s is None:
        return None
    try:
        return date.fromisoformat(s)  # espera YYYY-MM-DD
    except Exception:
        raise HTTPException(status_code=400, detail=f"Fecha inválida (usa YYYY-MM-DD): {s}")

@app.get("/historial")
def historial(
    desde: Optional[str] = Query(None, description="YYYY-MM-DD, ej: 2025-10-25"),
    hasta: Optional[str] = Query(None, description="YYYY-MM-DD, ej: 2025-10-27"),
):
    """
    Devuelve el histórico sin paginación, filtrando solo por fecha (sin horas).
    """
    d1 = _parse_date(desde)
    d2 = _parse_date(hasta)
    if d1 and d2 and d2 < d1:
        raise HTTPException(status_code=400, detail="`hasta` debe ser >= `desde`")

    # Convertimos a límites de día
    where, params = [], []
    if d1:
        ini = datetime.combine(d1, time.min).isoformat()
        where.append("fecha_hora_prediccion >= ?")
        params.append(ini)
    if d2:
        fin = datetime.combine(d2, time.max).isoformat()
        where.append("fecha_hora_prediccion <= ?")
        params.append(fin)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            f"""
            SELECT id, fecha_hora_prediccion, octas_predichas, confianza, categoria, descripcion, url_imagen
            FROM registro_historico
            {where_sql}
            ORDER BY datetime(fecha_hora_prediccion) ASC
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
# ---- FIN HISTORIAL ----------------------------------------------------------


# 🧭 Endpoint raíz (opcional, para verificar que el servidor corre)
@app.get("/")
def home():
    return {"mensaje": "Servidor de nubosidad Río Grande activo 🚀"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
