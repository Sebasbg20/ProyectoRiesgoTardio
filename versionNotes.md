# Notas de versión

**Proyecto:** ProyectoRiesgoTardio
**Responsable:** 
Maria José Arauz Retana 
Fiorella Paola Chavez Ordoñez 
Sebastian Barzuna Garza.

---

## Versión 0.1

**Fecha:** 2026-10-08
**Resumen:** Conexion SQL, Query Bronze

### Novedades
- (Bronze.sql)
- (connection.ipynb)

### Cambios
- (README.md) Se añade Readme y descripcion con integrantes

### Correcciones
- [Error corregido y cómo se manifestaba]

## Versión 0.2

**Fecha:** 2026-10-12
**Resumen:** Se añade capa silver y notas de versión.

### Novedades
- Se crea repositorio en github con los 3 colaboradores
- Se añade capa silver con datos limpios.


### Archivos incluidos
silver.py 

## Versión 0.3
### Diagnóstico de las tablas 
**Fecha:** 2026-10-13
**Resumen:** Se hace un Diagnóstico de todas las tablas de la base de datos de Olist.

### Novedades 
hacemos copia de todas las tablas para iniciar con la limpieza de datos.

## Versión 0.4
### Validación de calidad e integridad de datos OLIST
**Fecha:** 2026-10-15
**Resumen:** Se realizan controles de calidad, integridad referencial y conciliación de pagos como parte de la preparación de la capa Silver.

### Novedades
- Se revisan las tablas products, orders, orderitems, sellers, customers y payments.
- Se verifican valores faltantes, tipos de datos y registros duplicados según las claves correspondientes.
- Se comprueba la integridad referencial entre artículos, productos, vendedores, pedidos y clientes.
- Se conservan los 112.650 registros de orderitems y los 99.441 registros de customers.
- Se identifican 96.096 clientes únicos mediante customer_unique_id, de los cuales 2.997 tienen más de un registro.
- Se validan 3.095 vendedores sin valores faltantes ni IDs duplicados.
- Se conservan los 103.886 registros de payments y se revisan pagos de valor cero, tipos de pago y secuencias duplicadas.
- Se identifican 9 pagos de valor cero y 3 registros con tipo de pago not_defined; se conservan para no eliminar información sin justificación.
- Se realiza conciliación de productos, envíos y pagos por pedido.
- Se comparan 98.665 pedidos y se identifican 303 con diferencias superiores a 0,01 (aproximadamente 0,31 %).
- Se clasifica la magnitud de las diferencias y se revisan tipos de pago, vouchers y estados de los pedidos afectados.
- Se repite la conciliación mediante un cálculo independiente y se confirman los mismos 303 casos.
- Las diferencias se documentan como hallazgos pendientes de investigación, sin modificar ni eliminar registros.

### Archivos incluidos
- silver.py
- versionNotes.md

## Versión 0.5

### Validación e integración de datos geolocation, reviews y nametranslation

**Fecha:** 2026-10-19

**Resumen:** Se realizan validaciones de calidad de las tablas geolocation, reviews y nametranslation. Se integra el procesamiento geográfico al archivo principal silver.py como parte de la preparación de la capa Silver.

### Novedades

- Se analizan 1.000.163 registros de geolocation y se identifican 19.015 prefijos postales distintos.
- Se detectan 31 registros con coordenadas fuera del rango geográfico aproximado utilizado para Brasil.
- Se aplica una transformación que agrupa coordenadas por prefijo postal y calcula latitud y longitud promedio.
- Se obtienen 19.011 prefijos postales en Silver, sin duplicados.
- Se normalizan los prefijos postales a cinco caracteres.
- Se integra el procesamiento de geolocation en silver.py, evitando su carga completa mediante la lista general de tablas.
- Se analizan 99.224 registros de reviews y se identifican 789 identificadores review_id repetidos.
- Se comprueba que no existen combinaciones duplicadas de review_id y order_id.
- Se verifican valores nulos y puntuaciones de reviews, sin encontrar anomalías en los campos revisados.
- Se conservan los registros de reviews sin eliminar identificadores repetidos automáticamente.
- Se valida nametranslation con 71 registros, sin valores nulos ni filas completamente duplicadas.
- Se ejecuta silver.py sin errores visibles después de integrar geolocation.
- Se mantienen intactos los datos originales de Bronze.
- Queda pendiente completar la capa Silver y comprobar la compatibilidad de los datos geográficos resumidos con las siguientes etapas del proyecto.

## Versión 0.6

### Construcción de la capa Gold

**Fecha:** 2026-10-20

**Resumen:** Se construye la tabla analítica Gold order_delivery_risk_features con una fila por order_id.

### Novedades

- Se integran orders, orderitems, products, sellers, customers y geolocation en una sola tabla.
- Se resumen los artículos por pedido y se toma como artículo principal el de mayor precio para definir la categoría y el vendedor.
- Se construye la variable objetivo late_delivery (1 si order_delivered_customer_date es posterior a order_estimated_delivery_date). Los pedidos sin fecha de entrega quedan fuera de la tabla Gold.
- Se crean las variables: cantidad de ítems, cantidad de vendedores, valor total, freight_value, peso y volumen totales, categoría principal, estado de origen y destino, distancia vendedor-cliente, día de la semana y mes de compra, días estimados de entrega y mismo estado.
- Se excluyen order_status y las fechas de entrega para evitar fuga de datos.
- Se conserva order_purchase_timestamp solo para dividir los datos por tiempo.
- Se agregan controles de filas en cada unión, order_id duplicados, valores faltantes y distribución de late_delivery.
- Se modifica la conexión de la base de datos en silver.py para transcribir la tabla [products] a [productos]

### Archivos incluidos
- gold_order_delivery_risk_features.py
- versionNotes.md

### Versión 0.7 — Validación de archivos originales de Bronze
**Fecha:** 26 de octubre de 2026

**Actividad realizada:**

Se creó el archivo `bronze.py` para verificar los archivos CSV originales del dataset Olist.

Se comprobaron los nombres de los archivos, la cantidad de registros y el número de columnas.

**Resultados:**
- Se identificaron nueve archivos CSV.
- Ocho archivos presentan la misma cantidad de registros que sus respectivas tablas en SQL Server.
- Se detectó una diferencia en `nametranslation`: el CSV contiene 71 registros y SQL Server contiene 72.
- Mediante una consulta SQL se confirmó que la fila adicional corresponde a los encabezados del archivo CSV, importados como datos.

**Decisión tomada:**

Se conservará la tabla original de Bronze sin modificaciones. La fila correspondiente a los encabezados se excluirá durante la preparación de Silver.

**Estado:** Validación inicial completada. Pendiente automatizar la carga reproducible y registrar la trazabilidad.

## Versión 0.8 — Verificación de resultados reales y consistencia de Silver
**Fecha:** 27 de octubre de 2026

**Ejecución:** `python silver.py` contra la base SQL Server local `olist`. La ejecución terminó correctamente y las reglas automatizadas de consistencia finalizaron sin errores.

### Reglas medibles y resultados

1. **Conservación de registros:** las tablas sin agregación conservaron la cantidad de filas entre Bronze y Silver: customers 99.441, sellers 3.095, products 32.951, nametranslation 71, orders 99.441, orderitems 112.650, payments 103.886 y reviews 99.224. Geolocation se resume por prefijo postal: de 1.000.163 filas Bronze, 1.000.132 coordenadas válidas quedaron contabilizadas en 19.011 prefijos Silver.
2. **Unicidad de claves:** cero duplicados en `order_id`, `customer_id`, `product_id`, `seller_id`, la clave compuesta `(order_id, order_item_id)` de orderitems y `(order_id, payment_sequential)` de payments.
3. **Integridad referencial:** cero referencias huérfanas en orderitems hacia products, orders y sellers, en orders hacia customers y en payments hacia orders.
4. **Normalización y cobertura postal:** los 99.441 códigos postales de customers, los 3.095 de sellers y los 19.011 de geolocation tienen cinco caracteres. Geolocation no tiene prefijos duplicados y sus 1.000.132 coordenadas válidas en Bronze coinciden con la suma de registros agregados en Silver. Se encontraron coincidencias para 99.162 customers y 3.088 sellers.
5. **Conversiones numéricas e indicadores de productos:** 9 de 9 comprobaciones de conversiones e indicadores coincidieron con el recálculo desde Bronze. Se mantienen identificados 4 productos con peso cero.
6. **Calidad monetaria:** cero precios o envíos negativos, cero importes faltantes y cero pagos negativos o faltantes. Se conservaron y contabilizaron 9 pagos en cero, 3 pagos `not_defined` y 383 envíos en cero, sin eliminarlos.
7. **Fechas e indicadores cronológicos:** las cinco conversiones de fecha y los dos indicadores se verificaron (7 de 7). No hay entregas anteriores a la compra ni aprobaciones anteriores a la compra. Se detectaron 61 entregas anteriores a la aprobación; se conservan como anomalías de origen, correctamente reflejadas por el indicador.
8. **Conciliación independiente de pagos:** se compararon 98.665 pedidos. Los dos cálculos independientes produjeron resultados idénticos y detectaron 303 diferencias superiores a 0,01; son excepciones observadas, no se modificaron importes ni registros.

### Cambios
- `silver.py` ahora ejecuta estas reglas al finalizar, imprime los valores observados y detiene la ejecución con error si una transformación o una restricción de consistencia falla.
- Las anomalías de origen (por ejemplo, fechas cronológicas y diferencias de conciliación) se informan como resultados medibles, sin confundirse con errores de transformación ni eliminarse automáticamente.

## Versión 0.9 — Selección y evaluación temporal del modelo (histórica)
**Fecha:** 27 de octubre de 2026

> **Registro histórico, no vigente.** Esta ejecución seleccionó Regresión
> Logística y umbral 0,65. Sus resultados se conservan como trazabilidad y
> fueron supersedidos por la versión 1.4; no deben citarse como resultado
> final del proyecto.

### Cambios
- Se añadió un baseline separado `DummyClassifier` y se comparan regresión logística, Random Forest e HistGradientBoosting usando una partición cronológica de entrenamiento, validación y prueba.
- El modelo se selecciona por PR-AUC en validación, apropiada para comparar clases desbalanceadas. El umbral operativo se selecciona por F1 en validación; la prueba temporal queda reservada para la evaluación final.
- Se informa la importancia por permutación de las variables sobre una muestra de prueba, sin interpretarla como causalidad.
- Se exporta el ranking de pedidos de prueba a `outputs/pedidos_priorizados.csv`, con probabilidad, umbral y bandera de priorización; no se incluye la etiqueta real.

### Resultados de la ejecución
- Gold aportó 96.476 pedidos y 17 columnas. La división temporal produjo 61.744 pedidos de entrenamiento, 15.436 de validación y 19.296 de prueba.
- En validación, el baseline tuvo PR-AUC 0,081 y ROC-AUC 0,500. La regresión logística obtuvo PR-AUC 0,2076, Random Forest 0,1781 e HistGradientBoosting 0,1860. Se seleccionó regresión logística.
- El umbral que maximizó F1 en validación fue 0,65 (precision 0,2165; recall 0,4513; F1 0,2926).
- En la prueba temporal, con ese umbral, se obtuvo precision 0,0982, recall 0,3673, F1 0,1550, PR-AUC 0,1053 y ROC-AUC 0,7127. Con umbral 0,50, F1 fue 0,1585; por tanto, el umbral escogido en validación no mejoró F1 en la prueba y el resultado debe interpretarse como evidencia de generalización limitada.
- En la interpretación por permutación, `dias_estimados_entrega` mostró la mayor caída media de PR-AUC (0,05851) en 5.000 pedidos de prueba.
- El CSV contiene 19.296 pedidos ordenados por probabilidad; 3.819 superan el umbral de 0,65.

## Versión 1.0 — Persistencia y control de granularidad de Gold
**Fecha:** 27 de octubre de 2026

### Cambios
- `gold.py` conserva la tabla analítica en memoria y además la exporta como CSV reutilizable a `outputs/gold_order_delivery_risk_features.csv`.
- Las uniones con products, sellers, customers y geolocation ahora declaran cardinalidad muchos-a-uno. Se comprueba que no aumenten las filas de orders ni dupliquen `order_id`.
- Antes y después de exportar se verifica que haya exactamente una fila por `order_id`; el CSV se vuelve a leer para comprobar que conserva los identificadores, su orden y cantidad.

### Resultados de la ejecución
- Gold generó 96.476 filas y 17 columnas, con 96.476 `order_id` únicos, cero nulos y cero duplicados.
- La lectura de comprobación del CSV confirmó los 96.476 identificadores únicos y el mismo orden del DataFrame Gold.

## Versión 1.1 — Persistencia de Silver en Curated
**Fecha:** 28 de octubre de 2026

### Cambios
- `silver.py` exporta las nueve tablas curadas a `Data/Curated/` una vez que terminan correctamente las validaciones automáticas.
- Se genera `silver_manifest.csv` con fecha de generación, filas, columnas y hash SHA-256 de cada archivo.
- Se leen de vuelta los CSV y se verifican cantidad de filas, columnas y conservación de prefijos postales de cinco caracteres antes de actualizar la salida.
- El diccionario `silver` queda cargado desde los CSV persistidos para que `gold.py` consuma la capa Curated.
- Bronze permanece como fuente original y no se modifica.

## Versión 1.2 — Documentación de tratamientos Silver y joins Gold
**Fecha:** 28 de octubre de 2026

### Cambios
- El README describe los tratamientos de valores faltantes, conversiones, duplicados y anomalías, y aclara que no se eliminan registros automáticamente.
- Se documentan las cardinalidades, claves, agregaciones y decisiones de granularidad de los joins de Gold.
- Se explica la exclusión de pedidos sin fechas suficientes para formar la etiqueta supervisada y el uso de left joins para preservar pedidos sin coincidencia geográfica.
- Se corrige la descripción de Silver: valida duplicados en lugar de aplicar una deduplicación indiscriminada.

## Versión 1.3 — Reporte de riesgo y propuesta preventiva
**Fecha:** 28 de octubre de 2026

### Cambios
- Se añade `reporte_riesgo.py` para generar un reporte HTML autocontenido con métricas, matriz de confusión y agregados de riesgo por estado destino, categoría y mes.
- El reporte valida unicidad de `order_id`, cobertura del ranking contra Gold, etiquetas binarias y probabilidades dentro de rango antes de presentar resultados.
- Se documenta una propuesta de revisión humana y piloto operativo que reconoce el bajo precision y que el ranking corresponde a pedidos históricos del conjunto de prueba.
- Se documenta la capacidad de revisión como parámetro que operaciones debe definir; no se supone un límite operativo no proporcionado.


---

## Avances del 28 de octubre de 2026 — registro histórico supersedido

### Revisión y actualización del informe ejecutivo

> **Este resumen corresponde a una versión anterior.** La selección de
> Regresión Logística, umbral 0,65 y sus métricas ya no describen el modelo
> vigente. La referencia actual está en la versión 1.4.

Se revisó el informe ejecutivo del Proyecto 1 de OLIST, enfocado en la clasificación del riesgo de entrega tardía.

Se realizó una nueva redacción para presentar de forma más clara el trabajo desarrollado durante el curso, manteniendo los resultados obtenidos en el proyecto.

El informe incluye:

- Descripción del problema y objetivos.
- Tablas utilizadas del conjunto de datos OLIST.
- Procesamiento de información mediante las capas Bronze, Silver y Gold.
- Validaciones de calidad de los datos.
- Preparación de variables para la clasificación.
- Comparación de los modelos utilizados.
- Resultados de validación y prueba.
- Matriz de confusión.
- Análisis de variables importantes.
- Limitaciones y conclusiones del proyecto.

Se mantuvieron los resultados registrados durante el desarrollo del modelo, sin realizar nuevos entrenamientos.

### Resultados documentados

La tabla Gold contiene 96.476 pedidos, de los cuales 7.827 corresponden a entregas tardías.

Se compararon cuatro modelos:

1. DummyClassifier.
2. Regresión Logística.
3. Random Forest.
4. HistGradientBoosting.

La Regresión Logística presentó el mejor PR-AUC en validación, con un resultado de 0,2076.

En la evaluación final, utilizando un umbral de 0,65, se obtuvieron los siguientes resultados:

- Precision: 9,82 %.
- Recall: 36,73 %.
- F1-score: 0,1550.
- ROC-AUC: 0,7127.
- PR-AUC: 0,1054.

Estos resultados fueron incorporados al informe junto con su interpretación.

### Actualización del repositorio en GitHub

Se revisaron los cambios pendientes del proyecto en Visual Studio Code.

Se prepararon 12 archivos relacionados con la documentación, los modelos y los resultados obtenidos.

Se realizó el siguiente commit en la rama `main`:

`cb16151 - Agregar informe ejecutivo y resultados finales OLIST`


### Estado del proyecto

Al finalizar aquella revisión, los archivos principales seleccionados quedaron actualizados en GitHub. Este estado no representa los resultados vigentes.

## Versión 1.4 — Ejecución integral y resultados vigentes
**Fecha:** 28 de octubre de 2026

### Ejecución reproducible
- Se ejecutó el flujo completo en orden: `bronze_carga_completa.py`,
  `silver.py`, `gold.py`, `modelo_clasificacion.py` y `reporte_riesgo.py`.
- La conexión local a SQL Server `olist` respondió correctamente. Bronze
  omitió las nueve tablas raw que ya existían.
- Silver finalizó sus controles y persistió los CSV curados; Gold, el modelo,
  el ranking y el reporte se generaron sin errores.
- Gold contiene 96.476 pedidos etiquetados; el modelado temporal utilizó
  96.462 pedidos con fecha de aprobación y produjo 61.735 registros de
  entrenamiento, 15.434 de validación y 19.293 de prueba.
- Los archivos Gold, ranking y reporte HTML se regeneraron en esta misma
  ejecución. El reporte validó la unicidad y cobertura del ranking contra Gold.

### Resultados vigentes
- HistGradientBoosting obtuvo el mejor PR-AUC en validación: 0,1289. Se
  seleccionó el umbral 0,15 maximizando F1 en validación (F1 0,1935).
- En prueba temporal: Recall 2,75 %, Precision 18,06 %, F1 0,0477,
  PR-AUC 0,1251 y ROC-AUC 0,7500.
- De los 1.020 atrasos reales en prueba, se detectaron 28; se emitieron
  155 alertas, 127 de ellas falsas alarmas.
- **Conclusión:** el umbral fue seleccionado sin consultar prueba, pero la
  caída de Recall en la evaluación temporal significa que el modelo no
  justifica una implementación operativa. Los resultados son retrospectivos;
  no son pedidos activos y no autorizan automatizar acciones.
- El script guarda el artefacto del modelo en
  `outputs/modelo_clasificacion_v1.joblib`. `resultados_modelo.txt` no se
  genera en el flujo actual y no debe usarse como registro de esta ejecución.
- El notebook `OLIST_Analisis_y_Modelado.ipynb` no se ejecutó por completo; la
  secuencia de scripts es la evidencia reproducible del proyecto.

