# 🚀 Escalamiento del Proyecto *Cielo Río Grande*

## 🎯 Objetivo del Escalamiento

El **objetivo principal** del escalamiento del sistema de monitoreo atmosférico automatizado desarrollado en el marco del proyecto **Cielo Río Grande** es ampliar sus capacidades técnicas, operativas y territoriales, consolidando una plataforma **robusta, modular y replicable** para la **clasificación de nubosidad**, **detección de nubes noctilucentes (NLCs)** y **análisis meteorológico en tiempo real**.

Este escalamiento busca:

- **Mejorar la precisión del modelo** de clasificación de nubosidad, especialmente en los niveles intermedios de octas (4, 5 y 6), mediante el enriquecimiento del dataset, la incorporación de arquitecturas alternativas y el ajuste de técnicas de entrenamiento que permitan una mejor generalización.
- **Integrar nuevas funcionalidades de análisis atmosférico**, como la detección automática de NLCs y la correlación con variables meteorológicas (vapor de agua GNSS, radiación solar, temperatura superficial).
- **Expandir el sistema a otras estaciones astronómicas o meteorológicas**, replicando la arquitectura modular de captura, procesamiento y visualización, y promoviendo la interoperabilidad entre observatorios.
- **Fortalecer la trazabilidad y confiabilidad de los datos**, mejorando el pipeline automático, el backfill histórico y la validación cruzada de registros.
- **Abrir el sistema a la comunidad científica y educativa**, publicando una API REST documentada y dashboards interactivos, promoviendo el desarrollo de proyectos innovadores basados en los datos recolectados.

> 🛰️ En síntesis, el escalamiento del proyecto apunta a consolidar una **solución integral, escalable y replicable** para el monitoreo inteligente del cielo, combinando **visión artificial, ciencia de datos y meteorología aplicada**.

---

## ⚙️ Estrategias de Escalamiento

A continuación se detallan las acciones propuestas en cada eje estratégico:

### A. Técnicas de Mejora de Modelos

- **Clasificación ordinal:** reemplazar la clasificación categórica por un enfoque ordinal que reconozca la progresión continua entre niveles de octas, reduciendo la confusión entre clases vecinas.  
- **Exploración de arquitecturas alternativas:** evaluar modelos más avanzados como **ConvNeXt** o **Swin Transformers**, capaces de capturar mejor las características visuales en imágenes astronómicas.

---

### B. Expansión del Dataset

- **Recolección activa de imágenes intermedias:** campañas de captura focalizadas en niveles de nubosidad poco representados (octas 4, 5 y 6), tanto en condiciones claras como oscuras.  
- **Generación sintética con GANs:** uso de redes generativas adversarias para crear imágenes artificiales que refuercen clases minoritarias, manteniendo coherencia visual con el dominio astronómico.  
- **Etiquetado colaborativo y revisión cruzada:** sistema distribuido de validación manual entre múltiples observadores, con revisión cruzada y enlaces a imágenes de otras estaciones astronómicas o meteorológicas, promoviendo la **estandarización del etiquetado** y la **mejora continua del modelo**.

---

### C. Integración de Nuevas Funcionalidades

- **Módulo de detección de NLCs:** entrenamiento de una red neuronal específica para identificar **nubes noctilucentes**, centrada en imágenes con ángulo solar entre -7° y -10.5° durante diciembre y enero.  
- **Correlación con datos GNSS y radiación solar:** incorporación de variables meteorológicas como vapor de agua GNSS, radiación solar y temperatura superficial, para generar **modelos híbridos** que combinen visión artificial con datos numéricos.  
- **Dashboard avanzado con alertas y capas satelitales:** integración de datos satelitales (OpenWeatherMap, GOES) y alertas automáticas ante cambios de nubosidad o detección de NLCs.  
- **Análisis temporal y predicción futura:** uso de modelos de series temporales (**LSTM**, **Prophet**) para predecir la evolución de la nubosidad y anticipar ventanas de cielo despejado.  
- **Comparación con imágenes de otras estaciones:** galería de referencia y consulta cruzada con cámaras de Ezeiza, Bariloche, Ushuaia u otras estaciones.

---

### D. Escalamiento Territorial e Institucional

- **Replicación del sistema:** adaptación de la arquitectura modular para su implementación en nuevos observatorios astronómicos o meteorológicos, manteniendo compatibilidad con el pipeline actual.  
- **Convenios institucionales:** acuerdos con universidades, institutos técnicos y organismos meteorológicos para compartir datos, validar modelos y ampliar cobertura territorial.  
- **Publicación abierta de la API REST:** acceso libre y documentado a predicciones, imágenes procesadas y datos meteorológicos, fomentando la colaboración educativa, científica y tecnológica.

---

## 🧭 Conclusión

El **escalamiento del proyecto Cielo Río Grande** representa una oportunidad estratégica para consolidar un sistema inteligente de monitoreo atmosférico que combina **visión artificial, ciencia de datos y meteorología aplicada**.

A través de la mejora de modelos, la expansión del dataset, la integración de nuevas funcionalidades y la apertura institucional, se busca fortalecer la **precisión**, la **interoperabilidad** y el **impacto del sistema** tanto a nivel local como regional.

La incorporación de tecnologías avanzadas —como arquitecturas modernas, clasificación ordinal, análisis temporal y correlación con datos GNSS— permitirá abordar los desafíos actuales en la clasificación de nubosidad y enriquecer el análisis atmosférico.

> 🌠 Este plan estratégico apunta a transformar **Cielo Río Grande** en una **plataforma de referencia** para la observación automatizada del cielo, con potencial de replicación en otras estaciones y aplicaciones en ámbitos científicos, técnicos y educativos.
