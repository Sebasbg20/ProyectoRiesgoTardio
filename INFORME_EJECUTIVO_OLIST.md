
# INFORME EJECUTIVO
## Clasificación del riesgo de entrega tardía en pedidos de OLIST

**Universidad Latina de Costa Rica**  
**Curso:** Minería de Datos  
**Profesor:** Jorge Bermúdez-Tellería  
**Integrantes:** María José Arauz Retana, Fiorella Paola Chávez Ordóñez y Sebastián Barzuna Garza  
**Fecha:** 29 de octubre de 2026

---

## 1. Resumen ejecutivo

El presente proyecto tiene como objetivo analizar los pedidos de OLIST para identificar cuáles presentan mayor riesgo de ser entregados después de la fecha estimada. La finalidad es aplicar técnicas de minería de datos que permitan apoyar el seguimiento de pedidos y mejorar la identificación de posibles atrasos.

Para desarrollar el proyecto trabajamos con información histórica de comercio electrónico de Brasil. Organizamos los datos en tres capas: Bronze, Silver y Gold. Posteriormente, utilizamos técnicas de clasificación supervisada para comparar diferentes modelos y seleccionar el que presentó mejores resultados durante la validación.

La tabla final contiene 96.476 pedidos, de los cuales 7.827 fueron clasificados como entregas tardías, equivalentes al 8,11 % del total. Se compararon cuatro modelos: DummyClassifier, Regresión Logística, Random Forest e HistGradientBoosting.

La Regresión Logística obtuvo el mejor PR-AUC durante la validación, con un resultado de 0,2076. En el conjunto de prueba alcanzó un Recall de 36,73 %, una Precision de 9,82 % y un ROC-AUC de 0,7127.

Los resultados muestran que el modelo permite identificar una parte de los pedidos que presentan atrasos. Sin embargo, también genera una cantidad considerable de alertas incorrectas. Por esta razón, consideramos que puede servir como base para futuras mejoras y evaluaciones antes de utilizarlo en un proceso operativo real.

## 2. Problema y objetivo del proyecto

### 2.1 Problema identificado

En el comercio electrónico, los atrasos en las entregas pueden afectar la satisfacción de los clientes y la organización de los procesos logísticos.

Cuando una empresa maneja numerosos pedidos, identificar anticipadamente cuáles podrían presentar problemas de entrega puede resultar complicado.

A partir de esta situación, nuestro proyecto busca responder la siguiente pregunta:

**¿Es posible identificar, desde la confirmación de una compra, cuáles pedidos presentan mayor riesgo de entregarse después de la fecha estimada?**

### 2.2 Objetivo general

Desarrollar y evaluar un modelo de clasificación supervisada que permita estimar el riesgo de entrega tardía de los pedidos de OLIST, utilizando información histórica y técnicas de preparación y análisis de datos.

### 2.3 Objetivos específicos

- Integrar las fuentes de información necesarias para analizar los pedidos.
- Aplicar procesos de limpieza y validación de datos.
- Construir una tabla analítica con una fila por pedido.
- Entrenar y comparar diferentes modelos de clasificación.
- Evaluar los resultados mediante métricas adecuadas para datos desbalanceados.
- Identificar las variables con mayor aporte predictivo.
- Proponer posibles aplicaciones y mejoras a partir de los resultados obtenidos.

## 3. Datos utilizados

Para el desarrollo del proyecto utilizamos el conjunto de datos público Brazilian E-Commerce Public Dataset by OLIST, que contiene información histórica de pedidos realizados en Brasil.

Las seis tablas principales utilizadas para construir la información analítica fueron:

| Tabla | Información |
|---|---|
| orders | Identificación de pedidos y fechas relacionadas con la compra y entrega. |
| order_items | Artículos incluidos en cada pedido, precios y costos de envío. |
| products | Características y categorías de los productos. |
| sellers | Información de los vendedores. |
| customers | Información de los clientes y su ubicación. |
| geolocation | Coordenadas geográficas asociadas a códigos postales. |

Estas tablas se relacionaron mediante identificadores para reunir la información necesaria de cada pedido.

El resultado final fue una tabla denominada `order_delivery_risk_features`, con 96.476 registros y 17 columnas.

De esas columnas, 14 se utilizaron como variables predictoras. Las restantes corresponden al identificador del pedido, la fecha de compra y la variable objetivo.

### 3.1 Variable objetivo

La variable que buscamos predecir se denomina `late_delivery`.

Su valor se define de la siguiente manera:

- **1:** el pedido fue entregado después de la fecha estimada.
- **0:** el pedido no fue entregado después de la fecha estimada.

Para calcularla se comparó la fecha real de entrega con la fecha estimada.

Es importante aclarar que la fecha real de entrega se utilizó únicamente para conocer el resultado histórico y construir la variable objetivo. No se incluyó como variable predictora.

## 4. Preparación de datos: Bronze, Silver y Gold

Para organizar el procesamiento de la información trabajamos con una arquitectura dividida en tres capas.

### 4.1 Bronze: datos originales

En Bronze se conservaron los archivos originales del conjunto de datos OLIST y se realizó su carga a SQL Server.

Esta capa permite mantener los datos de origen como referencia y facilita verificar los registros utilizados durante el proyecto.

### 4.2 Silver: limpieza y validación

En Silver se realizaron procesos de preparación de datos, entre ellos:

- Revisión de valores faltantes.
- Validación de identificadores.
- Comprobación de relaciones entre tablas.
- Conversión de tipos de datos.
- Normalización de códigos postales.
- Revisión de fechas y valores numéricos.
- Preparación de la información geográfica.

Durante esta etapa se aplicaron ocho controles de calidad, los cuales finalizaron correctamente según los resultados registrados.

Esto no significa que los datos originales estuvieran libres de problemas. Por ejemplo, se identificaron 303 diferencias en la conciliación de pagos y 61 registros con situaciones cronológicas que requieren revisión.

Estos hallazgos fueron documentados para mantener la trazabilidad del proceso.

### 4.3 Gold: tabla para el análisis

En Gold se integró la información preparada para obtener una sola fila por pedido.

Se calcularon variables relacionadas con:

- Cantidad de artículos.
- Cantidad de vendedores.
- Valor total del pedido.
- Costo del envío.
- Peso y volumen de los productos.
- Categoría principal.
- Estado de origen y destino.
- Distancia geográfica aproximada.
- Día y mes de la compra.
- Días disponibles hasta la fecha estimada de entrega.

La tabla final contiene 96.476 pedidos únicos y constituye la base utilizada para el entrenamiento y evaluación de los modelos.

## 5. Metodología de clasificación

Nuestro problema corresponde a una clasificación binaria porque buscamos distinguir entre dos posibles resultados: entrega tardía y entrega no tardía.

Antes de entrenar los modelos, se organizaron los registros cronológicamente utilizando la fecha de compra.

Los datos se dividieron de la siguiente manera:

| Conjunto | Cantidad de pedidos | Propósito |
|---|---:|---|
| Entrenamiento | 61.744 | Entrenar los modelos. |
| Validación | 15.436 | Comparar modelos y seleccionar el umbral. |
| Prueba | 19.296 | Evaluar el resultado final. |

La separación temporal permite evaluar el modelo con pedidos posteriores a los utilizados durante el entrenamiento.

### 5.1 Modelos utilizados

Se compararon cuatro alternativas:

**DummyClassifier:** se utilizó como modelo de referencia para contar con un punto de comparación.

**Regresión Logística:** modelo de clasificación que permite estimar la probabilidad de pertenecer a una de las dos clases.

**Random Forest:** modelo basado en un conjunto de árboles de decisión.

**HistGradientBoosting:** modelo que combina árboles de manera progresiva para mejorar las predicciones.

### 5.2 Preparación de variables

Para entrenar los modelos fue necesario preparar las variables numéricas y categóricas.

Se aplicaron procedimientos como imputación de valores faltantes, escalado de variables numéricas y codificación de categorías.

También se consideró el desbalance de clases, ya que solamente el 8,11 % de los pedidos del conjunto Gold correspondía a entregas tardías.

## 6. Comparación de modelos

Para seleccionar el modelo se utilizó principalmente la métrica PR-AUC en el conjunto de validación.

Esta métrica resulta útil cuando una de las clases es considerablemente menos frecuente que la otra.

Los resultados obtenidos fueron:

| Modelo | PR-AUC en validación |
|---|---:|
| DummyClassifier | 0,0810 |
| Regresión Logística | **0,2076** |
| Random Forest | 0,1781 |
| HistGradientBoosting | 0,1860 |

La Regresión Logística presentó el mejor resultado entre los modelos evaluados.

Por este motivo fue seleccionada para la evaluación final.

Posteriormente se determinó un umbral de clasificación de 0,65, seleccionado a partir de los resultados de F1 en validación.

## 7. Resultados finales

El modelo seleccionado se evaluó con 19.296 pedidos correspondientes al conjunto de prueba temporal.

Los resultados fueron los siguientes:

| Métrica | Resultado |
|---|---:|
| Precision | 9,82 % |
| Recall | 36,73 % |
| F1-score | 0,1550 |
| Accuracy | 78,80 % |
| ROC-AUC | 0,7127 |
| PR-AUC | 0,1054 |
| Umbral de clasificación | 0,65 |

### 7.1 Interpretación de resultados

La **Precision de 9,82 %** significa que, entre los pedidos identificados como posibles atrasos, aproximadamente uno de cada diez presentó realmente una entrega tardía.

El **Recall de 36,73 %** indica que el modelo identificó aproximadamente el 37 % de los atrasos reales del conjunto de prueba.

El **ROC-AUC de 0,7127** muestra que el modelo tiene cierta capacidad para diferenciar entre pedidos tardíos y no tardíos.

Estos resultados deben analizarse en conjunto, ya que una sola métrica no permite determinar completamente el desempeño del modelo.

### 7.2 Matriz de confusión

La matriz de confusión permitió identificar la cantidad de predicciones correctas e incorrectas.

| Resultado real | Predicción sin atraso | Predicción con atraso |
|---|---:|---:|
| Sin atraso | 14.831 | 3.444 |
| Con atraso | 646 | 375 |

De acuerdo con estos resultados:

- Se identificaron correctamente 375 pedidos que presentaron atraso.
- Se generaron 3.444 alertas de pedidos que finalmente no se atrasaron.
- No se detectaron 646 pedidos que sí presentaron atraso.
- Se clasificaron correctamente 14.831 pedidos sin atraso.

En total, el modelo generó 3.819 alertas de posible entrega tardía.

Esto demuestra que, aunque el modelo logra identificar algunos pedidos de riesgo, todavía presenta dificultades para distinguir correctamente entre pedidos tardíos y no tardíos.

### 7.3 Comparación de umbrales

También se analizaron los resultados con umbrales de 0,50 y 0,65.

| Indicador | Umbral 0,50 | Umbral 0,65 |
|---|---:|---:|
| Precision | 8,78 % | 9,82 % |
| Recall | 81,68 % | 36,73 % |
| F1 | 0,1585 | 0,1550 |
| Alertas generadas | 9.500 | 3.819 |

Con el umbral de 0,50 se identificaron más atrasos, pero también aumentó considerablemente la cantidad de alertas.

El umbral de 0,65 redujo el volumen de alertas, aunque dejó más atrasos sin detectar.

El umbral seleccionado durante la validación fue 0,65. Sin embargo, para una aplicación real sería necesario considerar la capacidad de revisión de pedidos y las consecuencias de las predicciones incorrectas.

## 8. Variables con mayor importancia

Para conocer cuáles variables aportaron más al desempeño del modelo se realizó un análisis de importancia por permutación.

Los cinco factores principales fueron:

| Variable | Importancia registrada |
|---|---:|
| Días estimados de entrega | 0,05851 |
| Estado de destino | 0,00369 |
| Valor total del pedido | 0,00363 |
| Cantidad de artículos | 0,00333 |
| Cantidad de vendedores | 0,00249 |

La variable con mayor importancia fue `dias_estimados_entrega`, que representa el tiempo entre la compra y la fecha estimada de entrega.

También se identificó un aporte predictivo de la ubicación de destino y de algunas características del pedido.

Estos resultados permiten conocer qué información utiliza el modelo para diferenciar los pedidos, pero no demuestran que estas variables sean la causa directa de los atrasos.

## 9. Aplicación de los resultados

A partir del trabajo realizado, consideramos que el modelo podría utilizarse como una herramienta de apoyo para identificar pedidos que requieren mayor seguimiento logístico.

Una posible aplicación sería ordenar los pedidos según su riesgo estimado y revisar primero aquellos que presentan probabilidades más altas.

Sin embargo, debido a la cantidad de falsas alarmas observadas, no sería conveniente utilizar las predicciones como única base para tomar decisiones.

Antes de implementar el modelo, sería necesario realizar una prueba piloto, verificar las alertas generadas y analizar si el seguimiento preventivo produce beneficios reales.

También sería importante evaluar periódicamente el desempeño del modelo y ajustar los procedimientos según los resultados obtenidos.

## 10. Limitaciones del proyecto

Durante el desarrollo del proyecto identificamos algunas limitaciones que deben considerarse al interpretar los resultados.

En primer lugar, los datos utilizados corresponden a pedidos históricos realizados entre 2016 y 2018. Por lo tanto, los resultados no garantizan que el modelo tenga el mismo desempeño con pedidos actuales.

Otra limitación es el desbalance de clases, debido a que las entregas tardías representan una proporción pequeña del total.

Además, aunque se excluyeron las fechas reales de entrega de las variables predictoras, todavía sería necesario confirmar que todas las variables utilizadas estén disponibles exactamente en el momento de confirmar una compra. Esta verificación es importante para evitar el uso de información que solo se conoce posteriormente.

Finalmente, el proyecto se evaluó con datos históricos. No se realizó una implementación en producción ni se comprobó una reducción real de atrasos mediante acciones preventivas.

Estas limitaciones permiten identificar oportunidades de mejora para futuras etapas del proyecto.

## 11. Conclusiones

El desarrollo de este proyecto nos permitió aplicar diferentes conocimientos adquiridos durante el curso de Minería de Datos, desde la preparación de información hasta la evaluación de modelos predictivos.

Mediante las capas Bronze, Silver y Gold logramos organizar los datos de OLIST y construir una tabla analítica de 96.476 pedidos, con las variables necesarias para realizar la clasificación.

La comparación de modelos permitió identificar que la Regresión Logística obtuvo el mejor PR-AUC durante la validación, con un resultado de 0,2076.

En la evaluación final, el modelo alcanzó un Recall de 36,73 % y una Precision de 9,82 %. Esto indica que existe capacidad para detectar parte de los atrasos, pero también una cantidad importante de predicciones incorrectas.

El análisis de variables mostró que los días estimados de entrega fueron el factor con mayor aporte predictivo entre los evaluados.

Consideramos que el proyecto cumple su propósito académico de construir, comparar y evaluar modelos de clasificación utilizando datos reales. Al mismo tiempo, los resultados muestran que se requieren mejoras y nuevas evaluaciones antes de considerar una implementación operativa.

Como aprendizaje principal, comprendimos que desarrollar un modelo predictivo no consiste únicamente en obtener predicciones, sino también en preparar correctamente los datos, seleccionar métricas adecuadas e interpretar los resultados para determinar si el modelo puede aportar valor.

## 12. Referencias y recursos del proyecto

- OLIST. Brazilian E-Commerce Public Dataset.
- Repositorio del equipo: `ProyectoRiesgoTardio`.
- Scripts de procesamiento: `bronze_carga_completa.py`, `silver.py` y `gold.py`.
- Script de clasificación: `modelo_clasificacion.py`.
- Notebook de análisis: `OLIST_Analisis_y_Modelado.ipynb`.
- Diccionario de datos: `DICCIONARIO_DATOS_GOLD.md`.
- Resultados y visualizaciones generados durante el proyecto.
