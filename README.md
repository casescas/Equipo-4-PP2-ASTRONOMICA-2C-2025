# ☁️🚀 Proyecto Cielo Río Grande – Equipo 4 · PP2 Astronómica 2C 2025

Proyecto de Ciencia de Datos e Inteligencia Artificial aplicado al análisis de la cobertura nubosa en Río Grande (Tierra del Fuego, Argentina).

Enlace para acceder a la documentación completa 🔗➡️ https://casescas.github.io/Equipo-4-PP2-ASTRONOMICA-2C-2025/

---

## 🛰️ Descripción general

Este repositorio contiene el desarrollo completo del proyecto **Cielo Río Grande**, una aplicación que utiliza técnicas de inteligencia artificial y visión por computadora para analizar imágenes capturadas por la **Estación Astronómica de Río Grande (EARG)**, clasificando automáticamente el nivel de nubosidad.

El proyecto forma parte de la materia **Prácticas Profesionalizantes II (Astronómica)** de la **Tecnicatura Superior de Ciencia de Datos e IA** del **Politécnico Malvinas Argentinas**, y busca aplicar de manera práctica los conocimientos adquiridos en la tecnicatura, desde el procesamiento de datos y entrenamiento del modelo hasta la evaluación de resultados y su visualización técnica.

---

## 👥 Equipo

- Carmueda, Pablo  
- Estrada, Diego  
- Isa, Facundo  
- González Sardi, Iara  
- Quinteros, Nicolás  

---

## 🎯 Objetivo General

Desarrollar una aplicación capaz de **clasificar automáticamente el tipo de cielo** (según el sistema **OCTAS**) a partir de imágenes capturadas por cámaras locales, utilizando un modelo de **aprendizaje profundo (EfficientNet-B0)** y desplegando los resultados en un **dashboard interactivo**.

---

## ⚙️ Componentes Principales

- **Backend (FastAPI):** gestiona el modelo de clasificación, expone endpoints y registra predicciones en una base de datos SQLite.  
- **Frontend (React + Recharts):** muestra el historial de predicciones, gráficos de evolución y permite exportar reportes en PDF.  
- **Modelo de IA:** red neuronal EfficientNet-B0 entrenada para clasificar imágenes según categorías de cobertura nubosa.  
- **Pipeline de datos:** procesos de backfill o ejecuciones en tiempo real y almacenamiento estructurado de resultados.  
- **Documentación:** sitio generado con MkDocs que centraliza manuales técnicos, guías y documentación del código.

---

## 📁 Estructura del Repositorio

```text
Equipo-4-PP2-ASTRONOMICA-2C-2025/
├── 01.Data/
├── 02.Notebooks/
├── 03.SRC/
├── 04.Reports/
├── 05.Models/
├── 06.Docs/
├── cielo-rio-grande/
│   ├── backend/
│   ├── frontend/
│   └── docs/
├── .gitignore
├── LICENSE
├── mkdocs.yml
├── README.md
└── requirements.txt
```

---

## 🧩 Requisitos

- **Python 3.12+**
- **Node.js 18+** y **npm**
- **Git**
- (Opcional) **CUDA/cuDNN** si se utiliza GPU para PyTorch

---

## 🔬 Modelo y Entrenamiento

El sistema utiliza **EfficientNet-B0**, seleccionado por su equilibrio entre precisión y eficiencia computacional.  
Fue entrenado en **PyTorch** con *fine-tuning completo* sobre imágenes clasificadas según la escala **OCTAS (0–8)**.

| Dataset | Accuracy | Loss |
|----------|-----------|------|
| Entrenamiento | 74.9 % | 0.135 |
| Validación | 67.6 % | 0.271 |

El entrenamiento se detuvo en la **época 80** mediante *Early Stopping*, mostrando ligera tendencia al sobreajuste pero desempeño estable en clases extremas (0 y 8).

---

## 🔁 Flujo de Datos y Backfill

El pipeline procesa imágenes capturadas por la **EARG** cada 10 minutos mediante un *scheduler APScheduler*.

Pasos principales:
1. Descarga de la imagen (`utils.image_utils`)
2. Clasificación con `predict_octas()`
3. Registro en **SQLite** (`data/registros-octas.db`)

Ejemplo de salida:

```bash
📊 Backfill → total = 864 | nuevos = 830 | duplicados = 28 | fallidos = 6
```

---

## 🌐 Endpoints API

| Endpoint | Método | Descripción |
|-----------|---------|-------------|
| `/octas` | GET | Última predicción registrada |
| `/historial` | GET | Registros históricos filtrables por fecha |
| `/imagen` | GET | Última imagen del cielo disponible |
| `/satellite` | GET | Imagen satelital de nubosidad (OpenWeatherMap) |
| `/clima` | GET | Datos meteorológicos actuales |

---

## 📈 Conclusiones

El proyecto **Cielo Río Grande** consolida un sistema completo para el análisis automatizado de la nubosidad local mediante técnicas de **inteligencia artificial** y **procesamiento de imágenes**.  
El modelo **EfficientNet-B0** alcanzó un rendimiento sólido, especialmente en los extremos de la escala **OCTAS**, confirmando la viabilidad de aplicar *deep learning* en entornos con recursos limitados.

La arquitectura implementada —**modelo de IA**, **backend FastAPI**, **frontend React** y **pipeline automatizado**— posibilita tanto el análisis histórico como la predicción en tiempo real, aportando valor a la observación astronómica local.

---


Desarrollado por el **Equipo 4 – PP2 Astronómica (2C 2025)**  
para la **Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial** del **Politécnico Malvinas Argentinas**,  
en colaboración con la **Estación Astronómica de Río Grande (EARG)**.

![alt text](./06.Docs/assets/footer_politecnico.png)
