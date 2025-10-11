import os
import requests
import csv
from bs4 import BeautifulSoup
from tqdm import tqdm

#URL base del sitio
base_url = "http://201.251.63.225/meteorologia/cielo/image/2024/"

#Carpeta de salida
output_dir = "imagenes_nubes_2024"
os.makedirs(output_dir, exist_ok=True)

#Archivo CSV para registrar nombres de imágenes descargadas
csv_file = "imagenes_descargadas.csv"

#Leemos última imagen descargada del CSV
ultima_imagen = None
if os.path.exists(csv_file):
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # saltar encabezado
        filas = list(reader)
        if filas:
            ultima_imagen = filas[-1][0]

#Obtenemos el HTML de la página
response = requests.get(base_url)
soup = BeautifulSoup(response.text, 'html.parser')

# Extraer enlaces a imágenes .jpg que comienzan con '2025'
image_links = [a['href'] for a in soup.find_all('a', href=True)
               if a['href'].lower().endswith('.jpg') and a['href'].startswith('2024')]

#Ordenamos los enlaces para asegurar orden cronológico
image_links.sort()

#Filtramos imágenes posteriores a la última descargada
if ultima_imagen:
    image_links = [link for link in image_links if link > ultima_imagen]

#Descargamos imágenes con barra de progreso y registrar en CSV
for link in tqdm(image_links, desc="Descargando nuevas imágenes 2024"):
    nombre_archivo = link.split('/')[-1]
    url_completa = base_url + link
    ruta_local = os.path.join(output_dir, nombre_archivo)

    try:
        img_data = requests.get(url_completa).content
        with open(ruta_local, 'wb') as handler:
            handler.write(img_data)

        #Registramos en CSV
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([nombre_archivo])

    except Exception as e:
        print(f"Error al descargar {nombre_archivo}: {e}")

#EL registro es importante para saber donde quedo por algun problema. Para que continue desde la ultima descarga.
print(f"Se descargaron {len(image_links)} nuevas imágenes en la carpeta '{output_dir}' y se registraron en '{csv_file}'.")