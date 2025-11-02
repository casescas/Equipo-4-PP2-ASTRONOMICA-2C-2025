# 🧠 Reportes de Modelos de Clasificación de Nubosidad

Esta sección reúne los **informes técnicos de los modelos EfficientNet-B0 y EfficientNet-B3**, desarrollados en el marco del proyecto **Cielo Río Grande**.  
Cada reporte documenta el proceso de entrenamiento, validación y evaluación de los modelos de clasificación de nubosidad en imágenes astronómicas capturadas por la **Estación Astronómica de Río Grande (EARG)**.

---

##  **Propósito**
El objetivo general de estos reportes es **analizar el desempeño de las arquitecturas EfficientNet** en la estimación del nivel de nubosidad medido en *octas* (0 a 8).  
Los modelos buscan automatizar la identificación del estado del cielo para optimizar las observaciones astronómicas y fortalecer el monitoreo atmosférico de la estación.

---

## 📘 **Contenido de los reportes**
- **Reporte EfficientNet-B0:** describe el modelo base, su configuración de entrenamiento, balanceo de clases, métricas globales y análisis de errores.  
  Presenta una precisión del **67,6 % en validación**, con buen desempeño en cielos despejados o totalmente cubiertos, y dificultades en niveles intermedios de nubosidad:contentReference[oaicite:0]{index=0}.  
- **Reporte EfficientNet-B3:** detalla la versión ampliada del modelo con *fine-tuning* completo, técnicas de normalización, aumento de datos y Early Stopping.  
  Obtiene una precisión global del **70,3 %**, mostrando mejor capacidad de discriminación en clases extremas y un leve sobreajuste en las intermedias:contentReference[oaicite:1]{index=1}.

---

## ⚙️ **Alcance**
Los reportes incluyen:
- Descripción del **dataset** y su estructura por niveles de octas.  
- Estrategias de **balanceo y aumento de datos**.  
- Configuración de **entrenamiento y validación**.  
- **Métricas de desempeño** (accuracy, precision, recall, F1-score).  
- **Análisis de errores** y observaciones sobre la generalización del modelo.  
- Visualizaciones de aprendizaje, curvas de pérdida y precisión.

---

> 🔍 *Estos documentos constituyen la base de evaluación comparativa de los modelos de IA del proyecto, y sirven como insumo para futuras iteraciones orientadas a mejorar la precisión en la clasificación de nubosidad.*

![alt text](./assets/footer_politecnico.png)
