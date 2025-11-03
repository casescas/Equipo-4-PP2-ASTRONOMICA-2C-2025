# 🚀 Guía de Uso — Cielo Río Grande

Esta guía explica cómo **obtener, instalar y ejecutar** el proyecto **Cielo Río Grande**, levantar la API y acceder al dashboard de visualización.

---

## 🧩 1️⃣ Clonar el Repositorio

Cloná el repositorio desde GitHub y entrá al directorio raíz del proyecto:

```bash
git clone https://github.com/<usuario>/Equipo-4-PP2-ASTRONOMICA-2C-2025.git
cd Equipo-4-PP2-ASTRONOMICA-2C-2025
```

Si ya clonaste el repo antes, actualizalo con:

```bash
git pull
```

---

## ⚙️ 2️⃣ Backend (FastAPI)

💡 El backend gestiona la lógica de predicción, los endpoints y la base de datos local.

### 🔹 1. Crear y activar un entorno virtual *(recomendado)*

Primero, creá el entorno virtual con **venv** y activalo según tu sistema operativo 👇

```bash
# Crear entorno virtual
python -m venv venv

# 🐧 Linux / macOS
source venv/bin/activate

# 🪟 Windows
venv\Scripts\activate

# 💡 Tip (PowerShell)
# Si aparece un error de permisos al activar el entorno,
# ejecutá este comando para permitir scripts temporariamente:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

 ```
### 🔹 2. Instalar dependencias y ejecutar la API **sin hot reload**

```bash
# Ir al directorio del backend
cd cielo-rio-grande/backend
 
# Instalar dependencias del proyecto
pip install -r requirements.txt
 
# Ejecutar la API sin hot reload
uvicorn main:app --host 0.0.0.0 --port 8000

# 💡 Tip:
# Si querés habilitar el modo automático de recarga (hot reload),
# agregá la opción --reload al final del comando:
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
 ```

### 3. Abrí la documentación interactiva (Swagger UI):  
   👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 💻 3️⃣ Frontend (React)

💡 El frontend muestra las predicciones, gráficos y reportes generados por el modelo.

1. 🚀 Levantar frontend del proyecto


Paso previo: instalación de Node.js y npm

Antes de continuar, asegurate de tener instalados **Node.js** (versión 16 o superior) y **npm**.  
Podés verificarlo ejecutando:

```bash
node -v
npm -v
```
Pasos

```bash
# Entrar al directorio del frontend
cd ../frontend          
```
```bash
# Instalar dependencias 
 npm install   
```
```bash
# Iniciar el servidor de desarrollo
npm run start           
```

1. Abrilo en tu navegador:  
   👉 [http://localhost:3000](http://localhost:3000)

2. Desde ahí podrás:  
      - 📊 Visualizar la evolución de nubosidad  
      - 📅 Filtrar por rango de fechas  
      - 🧾 Exportar reportes en PDF

---

## 🔁 4️⃣ Backfill (Procesamiento Histórico)

💡 El proceso de **backfill** reconstruye el historial de predicciones a partir de imágenes antiguas capturadas por la **Estación Astronómica de Río Grande (EARG)**.  
Su propósito es generar un registro completo de nubosidad clasificada, abarcando días o meses anteriores para análisis temporal y entrenamiento adicional del modelo.

### 🧠 Descripción general

El script `backfill.py` ejecuta un flujo automatizado que:

1. 🗓️ Calcula el rango temporal solicitado (`--desde` y `--hasta` en formato ISO).  
2. ☁️ Consulta imágenes históricas alojadas en el servidor EARG.  
3. 🧠 Aplica el modelo **EfficientNet-B0** para predecir el nivel de nubosidad (0–8).  
4. 💾 Guarda los resultados en `data/registros-octas.db`, evitando duplicados.  
5. 🧾 Registra logs detallados con progreso, errores y tiempos de ejecución.

### ⚙️ Ejemplo de ejecución

Procesar todas las imágenes del mes de enero de 2025:

```bash
cd cielo-rio-grande/backend
python -m backfill --desde 2025-01-01T00:00 --hasta 2025-01-31T23:59
```

La salida mostrará un resumen como:

```
[2025-01-31 23:59] ✅ Backfill completado:
total = 864 | nuevos = 830 | duplicados = 28 | fallidos = 6
```

### 🧩 Características técnicas

- ⚡ **Asincronía controlada:** usa `asyncio` para manejar solicitudes HTTP en paralelo.  
- 🔁 **Reintentos automáticos:** gestiona errores 408, 502, 503 y 504 con `Retry`.  
- 🧱 **Logging estructurado:** cada paso se registra en `logs/backfill.log`.  
- 🧮 **Idempotencia:** evita reprocesar imágenes ya almacenadas.  
- 🧵 **Concurrencia:** límite recomendado de 3–6 workers en entornos locales.

### 📦 Resultado final

- Base de datos actualizada: `data/registros-octas.db`  
- Registros ordenados por timestamp (`fecha_prediccion`)  
- Logs detallados: `logs/backfill.log`  
- Visualización disponible desde el dashboard React

El **backfill** es clave para mantener una base de datos completa y coherente con las predicciones en tiempo real.

---

## 📊 5️⃣ Visualización de Resultados

El **dashboard React** permite:

- 📈 Consultar el historial de predicciones  
- 📆 Visualizar gráficos de nubosidad por fecha  
- 📤 Exportar reportes en PDF  
- 🧮 Analizar tendencias mediante indicadores dinámicos

---

## 🧠 6️⃣ Endpoints Principales

| Endpoint | Método | Descripción |
|-----------|---------|-------------|
| `/octas` | GET | Retorna la última predicción generada |
| `/historial` | GET | Devuelve registros históricos filtrables por fecha |
| `/imagen` | GET | Obtiene la última imagen procesada |
| `/satellite` | GET | Muestra imagen satelital de nubosidad |
| `/clima` | GET | Proporciona datos meteorológicos actuales |

---

## ✅ 7️⃣ Verificación Final

- 🟢 La API muestra `Application startup complete` en consola.  
- 🟢 El dashboard carga correctamente en [http://localhost:3000](http://localhost:3000).  
- 🟢 La base `registros-octas.db` se actualiza tras ejecutar el backfill.  

Si todo esto sucede, tu entorno está listo 🚀

---

## ✨ Créditos

Desarrollado por el **Equipo 4 – PP2 Astronómica (2C 2025)**  
para la **Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial**  
del **Politécnico Malvinas Argentinas**, en colaboración con la **Estación Astronómica de Río Grande (EARG)**.

![alt text](./assets/footer_politecnico.png)
