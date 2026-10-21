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