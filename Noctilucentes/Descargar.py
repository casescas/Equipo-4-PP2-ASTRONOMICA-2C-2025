import os
import re
import sys
import time
import requests
from urllib.parse import urljoin

# ==== CONFIG ====
ANIO = "2024"  # <-- Cambiá este valor cuando quieras otro año
BASE_URL = f"http://201.251.63.225/meteorologia/cielo/image/{ANIO}/"
OUTPUT_DIR = f"imagenes_descargadas_{ANIO}"
TIMEOUT = 20
SLEEP_BETWEEN = 0.2  # segundos entre descargas

# ==== PREP ====
os.makedirs(OUTPUT_DIR, exist_ok=True)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

print(f"[INFO] Consultando listado: {BASE_URL}")
try:
    resp = requests.get(BASE_URL, headers=headers, timeout=TIMEOUT)
    print(f"[INFO] HTTP status: {resp.status_code}")
    if not resp.ok:
        print("[ERROR] La URL no devolvió 200 OK. Revisa la dirección o permisos.")
        sys.exit(1)
except requests.RequestException as e:
    print(f"[ERROR] No se pudo acceder a la URL: {e}")
    sys.exit(1)

# Guardar HTML para inspección
html_dump = os.path.join(OUTPUT_DIR, f"listado_{ANIO}.html")
with open(html_dump, "w", encoding="utf-8", errors="ignore") as f:
    f.write(resp.text)
print(f"[INFO] HTML del listado guardado en: {html_dump}")

# ==== EXTRACCIÓN DE NOMBRES ====
anchor_regex = re.compile(r'href=["\']([^"\']+\.jpg)["\']', re.IGNORECASE)
candidatos = anchor_regex.findall(resp.text)

if not candidatos:
    print("[WARN] No se encontraron <a href='...jpg'>. Probando extracción por patrón de texto.")
    texto_regex = re.compile(rf'({ANIO}-(?:01|12)\d{{6}}\.jpg)', re.IGNORECASE)
    candidatos = texto_regex.findall(resp.text)

# ==== FILTRO POR MESES ====
def es_enero_o_diciembre(name: str) -> bool:
    name = name.strip()
    return name.lower().endswith(".jpg") and (name.startswith(f"{ANIO}-01") or name.startswith(f"{ANIO}-12"))

limpios = []
for x in candidatos:
    x = x.split('?')[0].split('#')[0]
    x = x.strip('/').split('/')[-1]
    if es_enero_o_diciembre(x):
        limpios.append(x)

# Eliminar duplicados manteniendo orden
visto = set()
imagenes = []
for x in limpios:
    if x not in visto:
        visto.add(x)
        imagenes.append(x)

print(f"[INFO] Imágenes detectadas: {len(imagenes)}")
if not imagenes:
    print("[AYUDA] No se detectaron nombres. Revisa el archivo HTML guardado para ver cómo aparece el listado.")
    sys.exit(0)

# ==== DESCARGA ====
descargadas = 0
for i, img_name in enumerate(imagenes, 1):
    url = urljoin(BASE_URL, img_name)
    destino = os.path.join(OUTPUT_DIR, img_name)

    if os.path.exists(destino):
        print(f"[{i}/{len(imagenes)}] Ya existe, salto: {img_name}")
        continue

    try:
        with requests.get(url, headers=headers, stream=True, timeout=TIMEOUT) as r:
            if r.status_code == 404:
                print(f"[{i}/{len(imagenes)}] 404 No encontrado: {img_name}")
                continue
            r.raise_for_status()
            with open(destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        descargadas += 1
        print(f"[{i}/{len(imagenes)}] Descargada: {img_name}")
        time.sleep(SLEEP_BETWEEN)
    except requests.RequestException as e:
        print(f"[{i}/{len(imagenes)}] ERROR descargando {img_name}: {e}")

print(f"✅ Listo. Descargadas nuevas: {descargadas}. Guardadas en: {os.path.abspath(OUTPUT_DIR)}")