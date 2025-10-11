import cv2
import numpy as np
import os
import csv

#Ruta base en C:\
base_folder = r"C:\imagenes_oscuro_claro_nubes"
output_base = r"C:\imagenes_etiquetadas_nivel_octa"
folders = {
    "claro": "imagenes_claro",
    "oscuro": "imagenes_oscuro"
}
output_csv = os.path.join(output_base, "etiquetas_nubosidad.csv")

#Creamos estructura de carpetas en C:\
for tipo in ["imagenes_claras", "imagenes_oscuras"]:
    for i in range(9):
        carpeta = os.path.join(output_base, tipo, f"{tipo[:-1]}_octa_{i}")
        os.makedirs(carpeta, exist_ok=True)

#Leemos imágenes ya procesadas desde el CSV
imagenes_procesadas = set()
if os.path.exists(output_csv):
    with open(output_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Saltar encabezado
        for row in reader:
            if row:
                imagenes_procesadas.add(row[0])

#Damos Rangos HSV
lower_white_dia = np.array([0, 0, 120])
upper_white_dia = np.array([180, 70, 255])

lower_white_noche = np.array([0, 0, 30])
upper_white_noche = np.array([180, 140, 255])

#Metodo para calcular porcentaje de nubosidad y generar máscara
def porcentaje_nubosidad(img_path, noche=False):
    img = cv2.imread(img_path)
    if img is None:
        print(f"No se pudo leer la imagen: {img_path}")
        return 0, None

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

    nube_pixels = np.sum(mask > 0)
    total_pixels = mask.size
    porcentaje = nube_pixels / total_pixels * 100
    return porcentaje, img_resized

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

#Procesamos ambas carpetas
with open(output_csv, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if os.stat(output_csv).st_size == 0:
        writer.writerow(["imagen", "porcentaje_nubosidad", "octa", "clasificacion"])

    for clasificacion, folder_name in folders.items():
        folder_path = os.path.join(base_folder, folder_name)
        if not os.path.exists(folder_path):
            print(f"No existe la carpeta: {folder_path}")
            continue

        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith((".jpg", ".png", ".jpeg")) and filename not in imagenes_procesadas:
                path = os.path.join(folder_path, filename)
                noche = clasificacion == "oscuro"
                porcentaje, img_resized = porcentaje_nubosidad(path, noche)
                octa = porcentaje_a_octa(porcentaje)

                tipo_carpeta = "imagenes_oscuras" if noche else "imagenes_claras"
                carpeta_destino = os.path.join(output_base, tipo_carpeta, f"{tipo_carpeta[:-1]}_octa_{octa}")
                os.makedirs(carpeta_destino, exist_ok=True)

                destino_img = os.path.join(carpeta_destino, filename)

                if img_resized is not None:
                    guardado_exitoso = cv2.imwrite(destino_img, img_resized)
                    if guardado_exitoso:
                        writer.writerow([filename, round(porcentaje, 2), octa, clasificacion])
                        print(f"{filename}: {round(porcentaje, 2)}% → {octa} octas ({clasificacion}) → Guardada en {destino_img}")
                    else:
                        print(f"Error al guardar la imagen: {filename}")
                else:
                    print(f"No se pudo procesar la imagen: {filename}")

print("Proceso completado. Resultados actualizados en etiquetas_nubosidad.csv")