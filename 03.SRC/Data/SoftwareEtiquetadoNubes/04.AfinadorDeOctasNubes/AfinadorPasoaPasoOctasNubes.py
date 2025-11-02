import cv2
import numpy as np
import os
import csv
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
from tqdm import tqdm

# **********CONFIGURACIÓN MANUAL**********
nivel_octa_actual = 8              #Aca cambiamo el nivel buscad entre 0 y 8
tipo_iluminacion = "oscura"      #Aca si queremos que sea "clara" o "oscura"
mostrar_preview = False        #Aca para visualizar la transformacion con True/False

#Rutas
input_base = r"C:\octas_dataset"
output_base = r"C:\imagenes_etiquetadas_nivel_octa"
output_csv = os.path.join(output_base, "etiquetas_nubosidad.csv")
error_csv = os.path.join(output_base, "errores_procesamiento.csv")
carpetas_csv = os.path.join(output_base, "carpetas_procesadas.csv")

#Creamos carpeta destino fija según configuración
carpeta_destino_fija = os.path.join(output_base, f"imagenes_{tipo_iluminacion}_octa_{nivel_octa_actual}")
os.makedirs(carpeta_destino_fija, exist_ok=True)

#Leemos imágenes ya procesadas
imagenes_procesadas = set()
if os.path.exists(output_csv):
    with open(output_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row:
                imagenes_procesadas.add(row[0])

#Leemos carpetas ya procesadas
carpetas_procesadas = set()
if os.path.exists(carpetas_csv):
    with open(carpetas_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row:
                carpetas_procesadas.add(row[0])

#Rangos HSV etiqueta 0
#lower_white_dia = np.array([0, 8, 80])
#upper_white_dia = np.array([180, 30, 137])

#Rangos HSV para octa 1 y 2(muy poca nubosidad)
lower_white_dia = np.array([90, 30, 40])
upper_white_dia = np.array([150, 255, 255])

##lower_white_dia = np.array([85, 20, 40])
##upper_white_dia = np.array([150, 255, 255])


lower_white_noche = np.array([0, 0, 80])
upper_white_noche = np.array([180, 120, 255])


#Metodo para calcular porcentaje de nubosidad y devolver también la máscara
def porcentaje_nubosidad(img_path, noche=False):
    img = cv2.imread(img_path)
    if img is None:
        return 0, None, None

    height, width = img.shape[:2]
    new_width = 640
    scale = new_width / width
    new_height = int(height * scale)
    img_resized = cv2.resize(img, (new_width, new_height))

    exclude_height = int(new_height * 0.2)
    img_cropped = img_resized[:new_height - exclude_height, :]

    hsv = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2HSV)
    lower_white = lower_white_noche if noche else lower_white_dia
    upper_white = upper_white_noche if noche else upper_white_dia
    mask = cv2.inRange(hsv, lower_white, upper_white)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    nube_pixels = np.sum(mask > 0)
    total_pixels = mask.size
    porcentaje = nube_pixels / total_pixels * 100
    return porcentaje, img_resized, mask

#Conversión de porcentaje a octas
def porcentaje_a_octa(p):
    if p <= 0: return 0
    elif p <= 12: return 1
    elif p <= 25: return 2
    elif p <= 38: return 3
    elif p <= 50: return 4
    elif p <= 63: return 5
    elif p <= 75: return 6
    elif p <= 88: return 7
    else: return 8

#Mostramos imagen original y máscara HSV con matplotlib
def mostrar_imagenes(img_original, mask, titulo="Vista previa"):
    mask_resized = cv2.resize(mask, (img_original.shape[1], img_original.shape[0]))
    mask_color = cv2.cvtColor(mask_resized, cv2.COLOR_GRAY2BGR)
    concatenada = np.hstack((img_original, mask_color))
    plt.figure(figsize=(12, 6))
    plt.imshow(cv2.cvtColor(concatenada, cv2.COLOR_BGR2RGB))
    plt.title(titulo)
    plt.axis('off')
    plt.show()

#Inicializamo el archivo CSV
with open(output_csv, 'a', newline='', encoding='utf-8') as f_out, \
     open(error_csv, 'a', newline='', encoding='utf-8') as f_err, \
     open(carpetas_csv, 'a', newline='', encoding='utf-8') as f_carpetas:

    writer = csv.writer(f_out)
    error_writer = csv.writer(f_err)
    carpeta_writer = csv.writer(f_carpetas)

    if os.stat(output_csv).st_size == 0:
        writer.writerow(["imagen", "porcentaje_nubosidad", "octa_original", "octa_reclasificada", "clasificacion", "timestamp"])

    if os.stat(error_csv).st_size == 0:
        error_writer.writerow(["imagen", "error", "timestamp"])

    if os.stat(carpetas_csv).st_size == 0:
        carpeta_writer.writerow(["carpeta", "timestamp"])

    carpeta_origen = os.path.join(input_base, f"imagenes_{tipo_iluminacion}_octa_{nivel_octa_actual}")
    if not os.path.exists(carpeta_origen):
        error_writer.writerow([f"carpeta_{tipo_iluminacion}_octa_{nivel_octa_actual}", "Carpeta no encontrada", datetime.now()])
    else:
        if f"imagenes_{tipo_iluminacion}_octa_{nivel_octa_actual}" not in carpetas_procesadas:
            archivos = sorted(os.listdir(carpeta_origen))
            imagenes_validas = [f for f in archivos if f.lower().endswith((".jpg", ".png", ".jpeg")) and f not in imagenes_procesadas]

            for filename in tqdm(imagenes_validas, desc=f"Procesando {tipo_iluminacion}_octa_{nivel_octa_actual}", unit="img"):
                path = os.path.join(carpeta_origen, filename)
                noche = tipo_iluminacion == "oscura"
                porcentaje, img_resized, mask = porcentaje_nubosidad(path, noche)
                octa_nueva = porcentaje_a_octa(porcentaje)

                if img_resized is not None:
                    destino_img = os.path.join(carpeta_destino_fija, filename)
                    guardado_exitoso = cv2.imwrite(destino_img, img_resized)

                    if guardado_exitoso:
                        writer.writerow([filename, round(porcentaje, 2), nivel_octa_actual, octa_nueva, tipo_iluminacion, datetime.now()])
                    else:
                        error_writer.writerow([filename, f"Error al guardar la imagen en {destino_img}", datetime.now()])
                else:
                    error_writer.writerow([filename, "No se pudo leer la imagen", datetime.now()])

                if mostrar_preview and img_resized is not None and mask is not None:
                    mostrar_imagenes(img_resized, mask)

            carpeta_writer.writerow([f"imagenes_{tipo_iluminacion}_octa_{nivel_octa_actual}", datetime.now()])

#Generamosr gráfico comparativo para ver si estas validando bien.
originales = []
reclasificadas = []

with open(output_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        originales.append(int(row['octa_original']))
        reclasificadas.append(int(row['octa_reclasificada']))

conteo_original = Counter(originales)
conteo_reclasificada = Counter(reclasificadas)

octas = list(range(9))
valores_original = [conteo_original.get(i, 0) for i in octas]
valores_reclasificada = [conteo_reclasificada.get(i, 0) for i in octas]

plt.figure(figsize=(10, 6))
plt.plot(octas, valores_original, marker='o', label='Octa Original')
plt.plot(octas, valores_reclasificada, marker='s', label='Octa Reclasificada')
plt.xlabel('Nivel de Octa')
plt.ylabel('Cantidad de Imágenes')
plt.title('Comparación entre Octa Original y Reclasificada')
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(output_base, "grafico_comparacion.png"))
plt.close()

print("Proceso completado: imágenes clasificadas en carpeta fija, carpeta registrada y gráfico generado.")