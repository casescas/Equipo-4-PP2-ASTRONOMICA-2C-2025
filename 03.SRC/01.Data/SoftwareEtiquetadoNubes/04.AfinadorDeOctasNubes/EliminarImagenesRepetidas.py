import os
from collections import defaultdict

#Ruta base para inspeccionar
base_path = "C:\\Imagen procesada"

#Diccionario para rastrear nombres de archivos y sus ubicaciones
file_locations = defaultdict(list)

#Recorremos todas las carpetas y archivos
for root, dirs, files in os.walk(base_path):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
            file_locations[file].append(os.path.join(root, file))

#Eliminamos duplicados por nombre (mantener solo una copia)
eliminadas = []
for filename, paths in file_locations.items():
    if len(paths) > 1:
        # Mantener la primera y eliminar las demás
        for duplicate_path in paths[1:]:
            os.remove(duplicate_path)
            eliminadas.append(duplicate_path)

#Mostramos resultados
print(f"Total de imágenes eliminadas por nombre duplicado: {len(eliminadas)}")
if eliminadas:
    print("Imágenes eliminadas:")
    for path in eliminadas:
        print(path)