
# INFORME EJECUTIVO
## Clasificación del riesgo de entrega tardía en pedidos de OLIST

**Universidad Latina de Costa Rica**  
**Curso:** Minería de Datos  
**Profesor:** Jorge Bermúdez-Tellería  
**Integrantes:** María José Arauz Retana, Fiorella Paola Chávez Ordóñez y Sebastián Barzuna Garza  
**Fecha:** 28 de octubre de 2026

---

## 1. Resumen ejecutivo

El presente proyecto tiene como objetivo analizar los pedidos de OLIST para identificar cuáles presentan mayor riesgo de ser entregados después de la fecha estimada. La finalidad es aplicar técnicas de minería de datos que permitan apoyar el seguimiento de pedidos y mejorar la identificación de posibles atrasos.

Para desarrollar el proyecto trabajamos con información histórica de comercio electrónico de Brasil. Organizamos los datos en tres capas: Bronze, Silver y Gold. Posteriormente, utilizamos técnicas de clasificación supervisada para comparar diferentes modelos y seleccionar el que presentó mejores resultados durante la validación.

La tabla Gold contiene 96.476 pedidos con etiqueta y 18 columnas. Para el modelo conservador se usaron 96.462 pedidos con fecha de aprobación disponible y seis predictores explícitos; se compararon DummyClassifier, Regresión Logística, Random Forest e HistGradientBoosting.

HistGradientBoosting obtuvo el mejor PR-AUC de validación (0,1289). En prueba temporal, con umbral 0,15, alcanzó PR-AUC de 0,1251, ROC-AUC de 0,7500, Precision de 18,06 % y Recall de 2,75 %.

El modelo detectó 28 de los 1.020 atrasos en prueba y generó 155 alertas. El bajo Recall indica que no debe utilizarse operativamente con este umbral; el resultado es una evaluación académica y requiere mejoras.

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

El resultado final fue una tabla denominada `order_delivery_risk_features`, con 96.476 registros y 18 columnas. Catorce pedidos con etiqueta no tenían fecha de aprobación y se excluyeron del modelado temporal.

El modelo conservador usa seis predictores: cantidad de ítems, valor total, flete, día y mes de compra y días estimados de entrega. `order_approved_at` se conserva solo para ordenar temporalmente y se excluye de los predictores.

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

La tabla final contiene 96.476 pedidos únicos. El modelado retiene 96.462 pedidos con fecha de aprobación disponible.

## 5. Metodología de clasificación

Nuestro problema corresponde a una clasificación binaria porque buscamos distinguir entre dos posibles resultados: entrega tardía y entrega no tardía.

Antes de entrenar los modelos, se organizaron los registros cronológicamente utilizando `order_approved_at`, que define el momento de predicción. Esta columna se usa solo para ordenar y dividir, no como predictor.

Los datos se dividieron de la siguiente manera:

| Conjunto | Cantidad de pedidos | Propósito |
|---|---:|---|
| Entrenamiento | 61.735 | Entrenar los modelos. |
| Validación | 15.434 | Comparar modelos y seleccionar el umbral. |
| Prueba | 19.293 | Evaluar el resultado final. |

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

También se consideró el desbalance de clases: 7.827 de los pedidos Gold (8,11 %) corresponden a entregas tardías.

## 6. Comparación de modelos

Para seleccionar el modelo se utilizó principalmente la métrica PR-AUC en el conjunto de validación.

Esta métrica resulta útil cuando una de las clases es considerablemente menos frecuente que la otra.

Los resultados obtenidos fueron:

| Modelo | PR-AUC en validación |
|---|---:|
| DummyClassifier | 0,0810 |
| Regresión Logística | 0,1165 |
| Random Forest | 0,1167 |
| HistGradientBoosting | **0,1289** |

HistGradientBoosting presentó el mejor resultado entre los modelos evaluados.

Por este motivo fue seleccionado para la evaluación final.

El umbral de clasificación seleccionado fue 0,15, al maximizar F1 en validación.

## 7. Resultados finales

El modelo seleccionado se evaluó con 19.293 pedidos correspondientes al conjunto de prueba temporal por fecha de aprobación.

Los resultados fueron los siguientes:

| Métrica | Resultado |
|---|---:|
| Precision | 18,06 % |
| Recall | 2,75 % |
| F1-score | 0,0477 |
| Accuracy | 94,20 % |
| ROC-AUC | 0,7500 |
| PR-AUC | 0,1251 |
| Umbral de clasificación | 0,15 |

### 7.1 Interpretación de resultados

La **Precision de 18,06 %** significa que, entre los pedidos identificados como posibles atrasos, alrededor de 18 de cada 100 presentaron realmente una entrega tardía.

El **Recall de 2,75 %** indica que el modelo identificó 28 de los 1.020 atrasos reales del conjunto de prueba. A este umbral, el modelo deja sin detectar la mayoría de los pedidos tardíos.

El **ROC-AUC de 0,7500** sugiere capacidad para ordenar pedidos por riesgo, pero las métricas de clasificación al umbral elegido muestran que aún no resulta adecuado como alerta operativa.

Estos resultados deben analizarse en conjunto, ya que una sola métrica no permite determinar completamente el desempeño del modelo.

### 7.2 Matriz de confusión

La matriz de confusión permitió identificar la cantidad de predicciones correctas e incorrectas.

| Resultado real | Predicción sin atraso | Predicción con atraso |
|---|---:|---:|
| Sin atraso | 18.146 | 127 |
| Con atraso | 992 | 28 |

De acuerdo con estos resultados:

- Se identificaron correctamente 28 pedidos que presentaron atraso.
- Se generaron 127 alertas de pedidos que finalmente no se atrasaron.
- No se detectaron 992 pedidos que sí presentaron atraso.
- Se clasificaron correctamente 18.146 pedidos sin atraso.

En total, el modelo generó 155 alertas de posible entrega tardía.

Esto demuestra que, aunque el modelo logra identificar algunos pedidos de riesgo, todavía presenta dificultades para distinguir correctamente entre pedidos tardíos y no tardíos.

### 7.3 Comparación de umbrales

Se comparó el umbral seleccionado de 0,15 con 0,05, que permite recuperar más atrasos, y con 0,50.

| Indicador | Umbral 0,05 | Umbral 0,15 | Umbral 0,50 |
|---|---:|---:|---:|
| Precision | 9,44 % | 18,06 % | 0,00 % |
| Recall | 80,88 % | 2,75 % | 0,00 % |
| F1 | 0,1690 | 0,0477 | 0,0000 |
| Alertas generadas | 8.744 | 155 | 0 |

Con el umbral 0,05 se recuperan más atrasos, pero se generan 8.744 alertas, lo que puede ser inviable operativamente.

El umbral 0,15 reduce las alertas a 155, pero deja sin detectar 992 de los 1.020 atrasos. En prueba, el umbral 0,50 no produce alertas.

El umbral se eligió en validación, sin consultar prueba. La caída de Recall en prueba señala una diferencia temporal de desempeño y la necesidad de investigar estabilidad y utilidad antes de cualquier uso operativo.

## 8. Variables con mayor importancia

Para conocer cuáles variables aportaron más al desempeño del modelo se realizó un análisis de importancia por permutación.

Los cinco factores principales fueron:

| Variable | Importancia registrada |
|---|---:|
| Días estimados de entrega | 0,07636 |
| Costo del envío | 0,01697 |
| Valor total del pedido | 0,01603 |
| Cantidad de artículos | 0,00814 |
| Día de semana de compra | 0,00311 |

La variable con mayor importancia fue `dias_estimados_entrega`, que representa el tiempo entre la compra y la fecha estimada de entrega.

Los resultados corresponden únicamente a los seis predictores autorizados del modelo conservador. La importancia negativa de `mes_compra` indica que no mejoró el PR-AUC en esta permutación.

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

Se aproximó el instante de predicción con la aprobación de la orden y se excluyeron como predictores vendedor, cliente, catálogo y geolocalización cuya disponibilidad histórica no puede verificarse. Se asume que ítems, precio, flete y fecha estimada ya se conocen al aprobarla. OLIST no incluye marcas de tiempo por campo, así que esta disponibilidad sigue siendo una limitación; la ausencia total de fuga no puede demostrarse con estos datos.

Finalmente, el proyecto se evaluó con datos históricos. No se realizó una implementación en producción ni se comprobó una reducción real de atrasos mediante acciones preventivas.

Estas limitaciones permiten identificar oportunidades de mejora para futuras etapas del proyecto.

## 11. Conclusiones

El desarrollo de este proyecto nos permitió aplicar diferentes conocimientos adquiridos durante el curso de Minería de Datos, desde la preparación de información hasta la evaluación de modelos predictivos.

Mediante las capas Bronze, Silver y Gold organizamos los datos de OLIST y construimos una tabla analítica de 96.476 pedidos. Para modelar se usaron 96.462 pedidos con fecha de aprobación disponible y seis predictores explícitos.

La comparación de modelos permitió identificar que HistGradientBoosting obtuvo el mejor PR-AUC de validación, con 0,1289.

En prueba, con umbral 0,15, el modelo alcanzó Recall de 2,75 % y Precision de 18,06 %. Recuperó pocos atrasos; por tanto, el resultado no sustenta un despliegue operativo.

El análisis de permutación mostró que los días estimados de entrega fueron el factor con mayor aporte predictivo entre los seis predictores autorizados.

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
