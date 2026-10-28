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

## Versión 0.9 — Selección y evaluación temporal del modelo
**Fecha:** 27 de octubre de 2026

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
