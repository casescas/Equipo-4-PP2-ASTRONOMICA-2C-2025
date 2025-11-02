import os
import cv2
import easyocr
import csv
import shutil
import re

#Ruta de entrada fija
input_directory = r"C:\imagenes_nubes_2025"

#Ruta de salida en el mismo directorio donde se ejecuta el script
base_dir = os.path.dirname(os.path.abspath(__file__))
output_directory = os.path.join(base_dir, "imagenes_oscuro_claro_nubes")
oscuro_dir = os.path.join(output_directory, "imagenes_oscuro")
claro_dir = os.path.join(output_directory, "imagenes_claro")
omitidas_dir = os.path.join(output_directory, "imagenes_omitidas")
csv_path = os.path.join(output_directory, "clasificacion_imagenes.csv")

#Creamos carpetas de salida si no existen
os.makedirs(oscuro_dir, exist_ok=True)
os.makedirs(claro_dir, exist_ok=True)
os.makedirs(omitidas_dir, exist_ok=True)

#Inicializamos OCR
reader = easyocr.Reader(['es'])

#Leemos imágenes ya procesadas si el CSV existe
imagenes_procesadas = set()
if os.path.exists(csv_path):
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader_csv = csv.reader(file)
        next(reader_csv)  # Saltar encabezado
        for row in reader_csv:
            if row:
                imagenes_procesadas.add(row[0])

#Listamos para guardar nuevos resultados
resultados = []

#Obtenemos lista de imágenes no procesadas
imagenes = [f for f in os.listdir(input_directory)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")) and f not in imagenes_procesadas]

#Procesamos cada imagen secuencialmente
for filename in imagenes:
    image_path = os.path.join(input_directory, filename)
    image = cv2.imread(image_path)

    if image is None:
        print(f"[ERROR] No se pudo cargar la imagen: {filename}")
        continue

    #Recortamos esquina inferior derecha
    height, width, _ = image.shape
    x_start = int(width * 0.70)
    y_start = int(height * 0.97)
    cropped = image[y_start:height, x_start:width]

    #Extraemos texto con OCR
    results = reader.readtext(cropped)
    texto_extraido = " ".join([res[1] for res in results]).strip()

    print(f"\nProcesando: {filename}")
    print(f"Texto extraído: {texto_extraido}")

    #Clasificamos basada en contenido
    clasificacion = "omitida"
    destino = omitidas_dir

    #Buscamos patrón "Sol" o "So1" seguido de ":" con posibles espacios
    match = re.search(r"(Sol|So1)\s*:\s*([=\-]|\d+)", texto_extraido)
    if match:
        simbolo_o_valor = match.group(2)
        if simbolo_o_valor in ["=", "-", "~"]:
            clasificacion = "oscuro"
            destino = oscuro_dir
        else:
            clasificacion = "claro"
            destino = claro_dir

    #Copiamos imagen original completa
    output_path = os.path.join(destino, filename)
    try:
        shutil.copy(image_path, output_path)
        print(f"[OK] Imagen copiada a: {destino}")
    except Exception as e:
        print(f"[ERROR] al copiar {filename}: {e}")
        continue

    #Guardamos resultado
    resultados.append([filename, clasificacion, texto_extraido])

#Guardamos o actualizamos CSV
modo_csv = 'a' if os.path.exists(csv_path) else 'w'
with open(csv_path, mode=modo_csv, newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    if modo_csv == 'w':
        writer.writerow(["Nombre de Imagen", "Clasificación", "Texto Extraído"])
    writer.writerows(resultados)

print(f"\n[FINALIZADO] Se procesaron {len(resultados)} nuevas imágenes. Resultados guardados en: {csv_path}")