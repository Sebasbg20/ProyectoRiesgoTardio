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
