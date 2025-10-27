# Backfill de Octas — Guía de Uso

Este documento explica cómo ejecutar el **backfill de datos de octas** a partir de las imágenes públicas del servidor meteorológico, utilizando el modelo de predicción y la base de datos local.

---

## 🧩 ¿Qué hace el backfill?

- Obtiene imágenes de cielo en intervalos de 10 minutos.
- Clasifica la cantidad de nubes usando un **modelo de IA** (`600EPOC_modelo_octa.h5`).
- Genera un registro histórico en **SQLite**, guardando:
  - `fecha_hora_prediccion`
  - `octas_predichas`
  - `confianza`
  - `categoria` (SKC, FEW, SCT, BKN, OVC)
  - `descripcion`
  - `url_imagen`

---

## 📁 Estructura esperada del proyecto

backend/
├─ backfill.py
├─ database.py
├─ registros-octas.db ← se crea automáticamente
└─ models/
└─ 600EPOC_modelo_octa.h5



# ⚙️ Configuración relevante en backfill.py
IMG_URL_BASE = "http://201.251.63.225/meteorologia/cielo/image/"
MODEL_PATH = "models/600EPOC_modelo_octa.h5"

# Pausa entre requests (anti-baneo)
REQUEST_SLEEP_SECONDS = 0.25
TIP:

  - 0.25 = rápido + estable
  -  0.5 = más seguro
  -  0 = máximo rendimiento, pero posible rate-limit
  
# 🧠 Bases del funcionamiento
Las imágenes están dentro de carpetas por año:

/meteorologia/cielo/image/<AÑO>/<YYYY>-<MMDDHH><mm>.jpg

Ejemplo real:

/meteorologia/cielo/image/2025/2025-01010002.jpg

# 🚀 Cómo ejecutar el Backfill

1) Rango definido
   
python backfill.py `
  --desde "2025-01-01T00:00" `
  --hasta "2025-01-31T23:59" `
  --step-min 10 `
  --modo forzar

2) Últimos 3 días automáticamente
python backfill.py `
  --desde "$( (Get-Date).AddDays(-3).ToString('yyyy-MM-ddTHH:mm') )" `
  --hasta "$(Get-Date -Format 'yyyy-MM-ddTHH:mm')" `
  --step-min 10 `
  --modo forzar

3) Desde enero de 2024 hasta ahora (lo más usado)

python backfill.py `
  --desde "2024-01-01T00:00" `
  --hasta "$(Get-Date -Format 'yyyy-MM-ddTHH:mm')" `
  --step-min 10 `
  --modo forzar

# 💾 Modos de escritura

| Modo            | Descripción                                                   |
| --------------- | ------------------------------------------------------------- |
| `forzar`        | **UPSERT** → actualiza valores si ya existen (recomendado)    |
| `respetar_hora` | Solo inserta si no existe el registro (no pisa datos previos) |


# ⏱️ Rendimiento

| Pausa (`REQUEST_SLEEP_SECONDS`) | Velocidad  | Riesgo                       |
| ------------------------------- | ---------- | ---------------------------- |
| `1.0`                           | lento      | muy seguro                   |
| `0.5`                           | estable    | seguro                       |
| `0.25`                          | rápido     | recomendado ✅                |
| `0.10`                          | muy rápido | riesgo moderado ⚠️           |
| `0.0`                           | máximo     | **riesgo alto de bloqueo** ❌ |


# 🧯 Solución de Problemas

| Error                                  | Causa                           | Solución                                    |
| -------------------------------------- | ------------------------------- | ------------------------------------------- |
| `ValueError: Invalid isoformat string` | Fecha mal formada               | Usar `"YYYY-MM-DDTHH:MM"`                   |
| 404 en todas las imágenes              | Falta carpeta de año            | Confirmar que la URL usa `/image/<AÑO>/...` |
| Muy lento                              | Pausa muy alta / conexión lenta | Reducir `REQUEST_SLEEP_SECONDS`             |
| Base no se actualiza                   | `DB_FILE` incorrecto            | Verificar `database.py`                     |

# 🗃️ Esquema de la Tabla

CREATE TABLE IF NOT EXISTS registro_historico (
  fecha_hora_prediccion TEXT PRIMARY KEY,
  octas_predichas INTEGER,
  confianza REAL,
  categoria TEXT,
  descripcion TEXT,
  url_imagen TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_registro_historico_fecha
  ON registro_historico(fecha_hora_prediccion);

🧪 Comandos rápidos (cheatsheet)

# Activar entorno
source .venv/bin/activate         # Linux/macOS
.venv\Scripts\Activate.ps1        # Windows PowerShell

# Actualizar repo y deps
git pull
pip install -r requirements.txt

# Correr backfill (ejemplo)
python backfill.py --desde "2025-01-01T00:00" --hasta "2025-01-07T23:59" --step-min 10 --modo forzar


