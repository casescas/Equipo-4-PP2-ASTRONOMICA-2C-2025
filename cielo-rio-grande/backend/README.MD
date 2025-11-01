# 🌥️ Flujo y Backfill — Guía de Uso

Este documento describe el funcionamiento general del sistema de clasificación automática de nubes y explica cómo ejecutar el proceso de backfill histórico.

El sistema obtiene imágenes públicas del cielo desde un servidor meteorológico, las procesa con un modelo de IA y almacena los resultados en una base de datos local.

# ⚙️ Flujo general

El sistema procesa imágenes del cielo capturadas periódicamente por la cámara instalada en el observatorio.

Cada imagen pasa por un pipeline automatizado que se ejecuta cada 10 minutos y realiza tres tareas principales:

1. Obtiene la nueva imagen desde la fuente configurada (IMG_URL_BASE).

2. Procesa la imagen con el modelo de clasificación de nubes (predict_octas).

3. Almacena el resultado en la base de datos local (registros-octas.db): 


El scheduler (`jobs/scheduler.py`) utiliza APScheduler para ejecutar este flujo de forma continua, garantizando la actualización de datos en tiempo real y alimentando el dashboard analítico.

# 🧩 Modos de funcionamiento

El sistema opera en dos modos complementarios:

| Modo                     | Descripción                                                                                                   | Frecuencia              |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- | ----------------------- |
| **Trigger (automático)** | Obtiene la última imagen disponible cada 10 minutos, la procesa con el modelo y guarda el resultado.          | Permanente              |
| **Backfill (histórico)** | Recorre un rango de fechas pasado y obtiene las imágenes correspondientes para generar el registro histórico. | Eventual / bajo demanda |

# 🧠 Backfill (backfill.py)

El backfill es un proceso independiente del trigger automático.

Su finalidad es reconstruir el historial de predicciones sobre un rango de fechas determinado, utilizando la misma lógica del pipeline principal.

# Funcionamiento

El backfill recorre el rango [--desde, --hasta] en pasos horarios.

Dentro de cada hora obtiene 6 imágenes fijas, correspondientes a los minutos válidos:

`MINUTOS_VALIDOS = [2, 12, 22, 32, 42, 52]`


Para cada intento:

- Construye la URL con `image_url`(`IMG_URL_BASE`, `intento`, `minuto`, `with_year_dir=True`).

- Obtiene la imagen desde el servidor público.

- La procesa con predict_octas(resp.content).

- Guarda el resultado con save_prediction(data).

El script muestra al finalizar un resumen con la cantidad total de imágenes procesadas, duplicadas y fallidas.

## Ejemplo de ejecución
``` bash
python -m backfill --desde "2025-01-01T00:00" --hasta "2025-01-31T23:59"
```

Salida esperada:
``` bash
📊 Backfill → total=864 | nuevos=830 | duplicados=28 | fallidos=6
```
## Validaciones y tolerancia a fallos

- Si --hasta es menor que --desde, el proceso finaliza con error.

- Los errores de red o imágenes ausentes se contabilizan como fallidos (miss).

- El proceso es idempotente: no repite registros ya existentes.

- Implementa reintentos automáticos (Retry(total=2)) ante errores HTTP (408, 500, 502, 503, 504).

## 🗂️ Estructura del servidor de imágenes

El servidor organiza las imágenes por año.

El backfill usa el `flag with_year_dir=True` para incluir la carpeta del año correspondiente.

/meteorologia/cielo/image/<AÑO>/<YYYY>-<MMDDHH><mm>.jpg


**Ejemplo:**

/meteorologia/cielo/image/2025/2025-01010002.jpg


Las ejecuciones del pipeline continuo no requieren esta estructura, ya que operan sobre el año actual (`with_year_dir=False`).

##  Ejemplos de ejecución
🔹 **Backfill del año actual (2025)**

En este caso las imágenes se encuentran en la raíz del servidor (sin carpeta por año).

```bash
python -m backfill --desde "2025-01-01T00:00" --hasta "2025-01-31T23:59"
```

Salida esperada:
```bash
📊 Backfill → total=864 | nuevos=830 | duplicados=28 | fallidos=6
```
🔹 **Backfill de un año anterior (2024)**

Para años anteriores las imágenes están dentro de una carpeta con el año correspondiente, por lo que el script usa `with_year_dir=True` automáticamente.
```bash
python -m backfill --desde "2024-01-01T00:00" --hasta "2024-12-31T23:59"
```

**Ejemplo de ruta accedida:**

http://201.251.63.225/meteorologia/cielo/image/2024/2024-01010002.jpg

🔹 **Backfill desde enero 2024 hasta hoy**

Combina ambos casos: empieza en la carpeta de 2024 y continúa con imágenes del año actual.
```bash
python -m backfill --desde "2024-01-01T00:00" --hasta "$(date +%Y-%m-%dT%H:%M)"
```
## 🧯 Solución de problemas

| Situación                              | Causa                                      | Solución                                               |
| -------------------------------------- | ------------------------------------------ | ------------------------------------------------------ |
| `ValueError: Invalid isoformat string` | Formato de fecha incorrecto                | Usar `"YYYY-MM-DDTHH:MM"`                              |
| 404 en todas las imágenes              | Carpeta de año omitida                     | Verificar que el backfill incluya `with_year_dir=True` |
| La base no se actualiza                | Imágenes ya procesadas                     | Es comportamiento esperado                             |
| Muchas fallidas                        | Rango de fechas muy grande o red inestable | Ejecutar por períodos más cortos                       |

## 🧪 Atajos y comandos rápidos

### Activar entorno virtual
```bash
source .venv/bin/activate          # Linux/macOS
.venv\Scripts\Activate.ps1         # Windows PowerShell
```
### Instalar dependencias
```bash
pip install -r requirements.txt
```

