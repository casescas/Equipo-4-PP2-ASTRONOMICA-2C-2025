import os
import re
import shutil  # Para mover archivos
import cv2  # OpenCV
import pytesseract
import numpy as np

# --- 1. CONFIGURACIÓN PRINCIPAL ---
CARPETAS_ORIGEN = ["Enero", "Diciembre"]

# Carpeta para imágenes que coinciden
CARPETA_DESTINO = "_CLASIFICADAS"

# ¡NUEVO! Carpeta para imágenes que fallan
CARPETA_ERRORES = "_ERRORES"

# Límites del ángulo del sol
MIN_ANGULO = -9.5
MAX_ANGULO = -8.0

# --- 2. FUNCIÓN DE PROCESAMIENTO (AHORA DEVUELVE CÓDIGOS) ---
def procesar_imagen(ruta_imagen):
    """
    Procesa una sola imagen.
    Devuelve:
    - "CLASIFICAR" (si el ángulo coincide)
    - "DESCARTAR" (si el ángulo no coincide)
    - "ERROR" (si no puede leer "Sol:" o hay un error técnico)
    """
    try:
        # 1. Abrir y Recortar (Ultra-preciso)
        imagen = cv2.imread(ruta_imagen)
        if imagen is None:
            print(f"  -> Error: No se pudo leer la imagen {ruta_imagen}")
            return "ERROR"
            
        (altura, anchura) = imagen.shape[:2]
        inicio_y = int(altura * 0.90) 
        inicio_x = int(anchura * 0.50) 
        region_interes = imagen[inicio_y:altura, inicio_x:anchura]
        
        # 3. PRE-PROCESAMIENTO
        gris = cv2.cvtColor(region_interes, cv2.COLOR_BGR2GRAY)
        factor_escala = 3
        (h, w) = gris.shape
        gris_grande = cv2.resize(
            gris, (w * factor_escala, h * factor_escala), interpolation=cv2.INTER_CUBIC
        )
        mascara_binaria = cv2.inRange(gris_grande, 150, 255)
        franja_preparada = cv2.bitwise_not(mascara_binaria)
        
        # (Quitamos el "engrosar" - dilate)

        # 7. Usar Tesseract 
        config_ocr = '--psm 6 -l spa+eng'
        texto_leido = pytesseract.image_to_string(franja_preparada, config=config_ocr)
        
        # 8. Encontrar el valor del Sol
        match = re.search(r"Sol\s*:\s*(-?\d+[,.]\d+)", texto_leido, re.IGNORECASE)

        if match:
            valor_str = match.group(1)
            valor_str_limpio = valor_str.replace(",", ".")
            valor_sol = float(valor_str_limpio)
            
            # 9. Clasificar
            if MIN_ANGULO <= valor_sol <= MAX_ANGULO:
                print(f"  -> ¡COINCIDENCIA! Valor del Sol: {valor_sol}")
                return "CLASIFICAR"
            else:
                print(f"  -> Descartado. (Sol: {valor_sol})")
                return "DESCARTAR"
        else:
            # ¡CAMBIO! Si no encuentra "Sol:", es un error
            print(f"  -> ERROR OCR: No se encontró 'Sol:'. Texto leído: [{texto_leido.strip()}]")
            return "ERROR"

    except Exception as e:
        print(f"  -> ERROR TÉCNICO procesando {ruta_imagen}: {e}")
        return "ERROR"

# --- 3. SCRIPT PRINCIPAL (El 'recorrido') ---
def main():
    print(f"Iniciando clasificación...")
    print(f"Buscando imágenes con ángulo de Sol entre {MIN_ANGULO} y {MAX_ANGULO}.")
    
    # Crear AMBAS carpetas de destino
    os.makedirs(CARPETA_DESTINO, exist_ok=True)
    os.makedirs(CARPETA_ERRORES, exist_ok=True) # ¡NUEVO!
    
    print(f"Imágenes clasificadas se moverán a: '{CARPETA_DESTINO}'")
    print(f"Imágenes con error se moverán a:   '{CARPETA_ERRORES}'\n")
    
    total_movidas_ok = 0
    total_movidas_error = 0
    total_procesadas = 0

    for nombre_carpeta in CARPETAS_ORIGEN:
        if not os.path.isdir(nombre_carpeta):
            print(f"Advertencia: La carpeta '{nombre_carpeta}' no existe. Saltando...")
            continue
            
        print(f"--- Procesando carpeta: {nombre_carpeta} ---")
        
        for nombre_archivo in os.listdir(nombre_carpeta):
            if nombre_archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                ruta_completa = os.path.join(nombre_carpeta, nombre_archivo)
                
                print(f"Procesando: {nombre_archivo}...")
                total_procesadas += 1
                
                # Llamar a nuestra función de OCR
                resultado = procesar_imagen(ruta_completa)
                
                # --- LÓGICA DE MOVIMIENTO ACTUALIZADA ---
                try:
                    if resultado == "CLASIFICAR":
                        ruta_destino = os.path.join(CARPETA_DESTINO, nombre_archivo)
                        shutil.move(ruta_completa, ruta_destino)
                        print(f"  -> ¡MOVIMOS! Archivo movido a '{CARPETA_DESTINO}'")
                        total_movidas_ok += 1
                        
                    elif resultado == "ERROR":
                        # ¡NUEVO! Mover a la carpeta de errores
                        ruta_destino_error = os.path.join(CARPETA_ERRORES, nombre_archivo)
                        shutil.move(ruta_completa, ruta_destino_error)
                        print(f"  -> ¡ERROR! Archivo movido a '{CARPETA_ERRORES}'")
                        total_movidas_error += 1
                        
                    elif resultado == "DESCARTAR":
                        # No hacemos nada, el archivo se queda donde está
                        pass
                        
                except Exception as e:
                    print(f"  -> !! ERROR CRÍTICO AL MOVER !!: {e}")
    
    print("\n--- ¡Proceso completado! ---")
    print(f"Imágenes totales procesadas: {total_procesadas}")
    print(f"Imágenes clasificadas (movidas a '{CARPETA_DESTINO}'): {total_movidas_ok}")
    print(f"Imágenes con error (movidas a '{CARPETA_ERRORES}'):   {total_movidas_error}")

# Ejecutar el script
if __name__ == "__main__":
    main()