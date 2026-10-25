
import pandas as pd
import pyodbc

# Conectar a SQL Server
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=olist;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

# Cargar la tabla customers
customers = pd.read_sql(
    "SELECT * FROM customers",
    conn
)

# Cerrar conexión después de cargar
conn.close()

# Revisar la tabla
print("Cantidad de filas y columnas:")
print(customers.shape)

print("\nTipos de datos:")
customers.info()

print("\nValores nulos por columna:")
print(customers.isna().sum())

print("\nFilas completamente duplicadas:")
print(customers.duplicated().sum())

print("\nCustomer ID duplicados:")
print(customers["customer_id"].duplicated().sum())







import pandas as pd
import pyodbc

# Conexión a SQL Server
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=olist;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

# Claves lógicas de Silver y nombres reales de las tablas en SQL Server
tablas = {
    "sellers": "sellers",
    "products": "products",
    "nametranslation": "nametranslation",
    "orders": "orders",
    "orderitems": "orderitems",
    "payments": "payments",
    "reviews": "reviews",
}

# Diccionario para guardar los DataFrames
datos = {}

# Recorrer todas las tablas
for nombre, tabla_sql in tablas.items():

    print("\n" + "=" * 50)
    print("DIAGNÓSTICO DE:", nombre)
    print("=" * 50)

    # Consultar SQL Server
    query = f"SELECT * FROM dbo.[{tabla_sql}]"

    df = pd.read_sql(query, conn)

    # Guardar tabla
    datos[nombre] = df

    # Cantidad de filas y columnas
    print("\nFilas y columnas:")
    print(df.shape)

    # Tipos de datos
    print("\nTipos de datos:")
    print(df.dtypes)

    # Valores nulos
    print("\nValores nulos por columna:")
    print(df.isna().sum())

    # Filas completamente duplicadas
    print("\nFilas duplicadas:")
    print(df.duplicated().sum())

    # Nombres de columnas
    print("\nColumnas disponibles:")
    print(df.columns.tolist())

    # ==========================================
# SILVER - GEOLOCATION
# ==========================================

print("\nPROCESANDO GEOLOCATION PARA SILVER")

consulta_geo = """
WITH coordenadas AS (
    SELECT
        geolocation_zip_code_prefix,
        TRY_CONVERT(FLOAT, geolocation_lat) AS lat,
        TRY_CONVERT(FLOAT, geolocation_lng) AS lng
    FROM dbo.geolocation
)
SELECT
    geolocation_zip_code_prefix,
    AVG(lat) AS latitud,
    AVG(lng) AS longitud,
    COUNT(*) AS cantidad
FROM coordenadas
WHERE lat BETWEEN -34 AND 6
  AND lng BETWEEN -74 AND -28
GROUP BY geolocation_zip_code_prefix
"""

geo_silver = pd.read_sql(consulta_geo, conn)

geo_silver["geolocation_zip_code_prefix"] = (
    geo_silver["geolocation_zip_code_prefix"]
    .astype(str)
    .str.zfill(5)
)

print("Codigos postales:", len(geo_silver))

print(
    "Duplicados:",
    geo_silver["geolocation_zip_code_prefix"].duplicated().sum()
)

# Incorporar al diccionario de datos
datos["geolocation"] = geo_silver

print("GEOLOCATION INCORPORADA CORRECTAMENTE")

# Cerrar conexión
conn.close()

print("\nDIAGNÓSTICO FINALIZADO")




# Crear copias para Silver
silver = {}

for nombre, df in datos.items():
    silver[nombre] = df.copy()

# Agregar customers, que cargaste por separado
silver["customers"] = customers.copy()

print("Tablas preparadas para Silver:")
print(list(silver.keys()))


# Preparar customers para la capa Silver

customers_silver = customers.copy()

# Convertir el código postal a texto de 5 dígitos
customers_silver["customer_zip_code_prefix"] = (
    customers_silver["customer_zip_code_prefix"]
    .astype(str)
    .str.zfill(5)
)

# Comprobar los resultados
print("DIAGNÓSTICO CUSTOMERS SILVER")
print(customers_silver.shape)

print("\nPrimeros 5 registros:")
print(customers_silver.head())

print("\nTipos de datos:")
print(customers_silver.dtypes)

silver["customers"] = customers_silver

print("Customers actualizado en Silver:")
print(silver["customers"]["customer_zip_code_prefix"].head())


silver["customers"] = customers_silver
print("Customers actualizado en el diccionario Silver")


print("Total de clientes en Silver:", len(silver["customers"]))
print("Codigos postales de ejemplo:")
print(silver["customers"]["customer_zip_code_prefix"].head())

# Validar correspondencia de codigos postales entre customers y geolocation

codigos_geo = set(
    silver["geolocation"]["geolocation_zip_code_prefix"]
)

clientes_con_geo = silver["customers"][
    "customer_zip_code_prefix"
].isin(codigos_geo)

print("\nVALIDACION GEOGRAFICA DE CLIENTES")
print("Total de clientes:", len(silver["customers"]))
print("Clientes con codigo postal encontrado:", clientes_con_geo.sum())
print("Clientes sin codigo postal encontrado:", (~clientes_con_geo).sum())

# Preparar vendedores para la capa Silver
sellers_silver = silver["sellers"].copy()

# Convertir el codigo postal a texto de 5 digitos
sellers_silver["seller_zip_code_prefix"] = (
    sellers_silver["seller_zip_code_prefix"]
    .astype(str)
    .str.zfill(5)
)

# Actualizar el diccionario Silver
silver["sellers"] = sellers_silver

# Comprobar resultados
print("VENDEDORES EN SILVER")
print("Total:", len(silver["sellers"]))
print("Codigos postales:")
print(silver["sellers"]["seller_zip_code_prefix"].head())


# Validar correspondencia de codigos postales entre sellers y geolocation

vendedores_con_geo = silver["sellers"][
    "seller_zip_code_prefix"
].isin(codigos_geo)

print("\nVALIDACION GEOGRAFICA DE VENDEDORES")
print("Total de vendedores:", len(silver["sellers"]))
print("Vendedores con codigo postal encontrado:", vendedores_con_geo.sum())
print("Vendedores sin codigo postal encontrado:", (~vendedores_con_geo).sum())

# Revisar productos antes de limpiar
products_silver = silver["products"].copy()

print("\nREVISION DE PRODUCTS")
print("Total de productos:", len(products_silver))

print("\nValores faltantes por columna:")
print(products_silver.isnull().sum())

print("\nProductos con al menos un dato faltante:")
print(products_silver.isnull().any(axis=1).sum())


# Revisar productos con peso o dimensiones faltantes

columnas_fisicas = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm"
]

productos_incompletos = products_silver[
    products_silver[columnas_fisicas].isnull().any(axis=1)
]

print("\nPRODUCTOS CON DATOS FISICOS FALTANTES")
print(productos_incompletos[
    ["product_id", "product_category_name"] + columnas_fisicas
].to_string(index=False))


# Verificar si los productos incompletos tienen ventas

productos_con_ventas = productos_incompletos[
    "product_id"
].isin(silver["orderitems"]["product_id"])

print("\nPRODUCTOS INCOMPLETOS CON VENTAS:")
print(productos_con_ventas.value_counts())

# Revisar productos sin categoría que aparecen en ventas

sin_categoria = products_silver[
    products_silver["product_category_name"].isnull()
]

tienen_ventas = sin_categoria["product_id"].isin(
    silver["orderitems"]["product_id"]
)

print("\nPRODUCTOS SIN CATEGORIA:")
print("Total:", len(sin_categoria))

print("\nRELACION CON VENTAS:")
print(tienen_ventas.value_counts())

print("\nCOLUMNAS DE NAMETRANSLATION:")
print(silver["nametranslation"].columns.tolist())

print("\nPRIMEROS 5 REGISTROS:")
print(silver["nametranslation"].head())

# Identificar productos sin categoría
products_silver["categoria_faltante"] = (
    products_silver["product_category_name"].isna()
)

# Actualizar la tabla dentro del diccionario Silver
silver["products"] = products_silver.copy()

# Comprobar resultados
print("\nCONTROL DE CATEGORIAS EN SILVER:")
print(products_silver["categoria_faltante"].value_counts())

print("\nTOTAL DE PRODUCTOS:")
print(len(silver["products"]))

# Verificar identificadores duplicados en products

print("\nCONTROL DE DUPLICADOS EN PRODUCTS:")

print("Total de productos:", len(silver["products"]))

print(
    "IDs duplicados:",
    silver["products"]["product_id"].duplicated().sum()
)

print(
    "IDs faltantes:",
    silver["products"]["product_id"].isnull().sum()
)

# Crear categoría para análisis sin alterar la original

products_silver["categoria_analisis"] = (
    products_silver["product_category_name"]
    .fillna("Sin categoría")
)

# Actualizar el diccionario Silver
silver["products"] = products_silver.copy()

# Verificar el resultado
print("\nCONTROL FINAL DE CATEGORIAS:")
print(
    silver["products"]["categoria_analisis"]
    .value_counts()
    .head(10)
)

print("\nPRODUCTOS SIN CATEGORIA ORIGINAL:")
print(
    silver["products"]["categoria_faltante"].sum()
)

# Revisar pesos y dimensiones de productos

columnas_fisicas = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm"
]

print("\nCONTROL DE VALORES FISICOS:")

for columna in columnas_fisicas:
    valores = products_silver[columna]

    print("\nColumna:", columna)
    print("Valores negativos:", (valores < 0).sum())
    print("Valores iguales a cero:", (valores == 0).sum())
    print("Valores faltantes:", valores.isna().sum())

    # Identificar productos con problemas de peso o dimensiones

productos_revisar = products_silver[
    (products_silver["product_weight_g"] == 0)
    | (products_silver[columnas_fisicas].isna().any(axis=1))
]

print("\nPRODUCTOS PARA REVISION:")
print(
    productos_revisar[
        ["product_id", "product_category_name"]
        + columnas_fisicas
    ].to_string(index=False)
)

print("\nTOTAL DE PRODUCTOS PARA REVISION:")
print(len(productos_revisar))


# Identificar productos sin información física completa
products_silver["datos_fisicos_incompletos"] = (
    products_silver[columnas_fisicas]
    .isna()
    .any(axis=1)
)

# Identificar productos con peso igual a cero
products_silver["peso_cero"] = (
    products_silver["product_weight_g"] == 0
)

# Actualizar el diccionario Silver
silver["products"] = products_silver.copy()

# Comprobar los resultados
print("\nCONTROL DE CALIDAD PRODUCTS SILVER:")

print("Total de productos:", len(silver["products"]))

print(
    "Productos con datos físicos incompletos:",
    silver["products"]["datos_fisicos_incompletos"].sum()
)

print(
    "Productos con peso cero:",
    silver["products"]["peso_cero"].sum()
)


print("\nCOLUMNAS FINALES DE PRODUCTS:")
print(silver["products"].columns.tolist())

print("\nDIMENSIONES DE PRODUCTS:")
print(silver["products"].shape)

print("\nCONTROL DE INDICADORES:")
print(
    silver["products"][
        ["datos_fisicos_incompletos", "peso_cero"]
    ].value_counts()
)


print("\nTIPOS DE DATOS FINALES DE PRODUCTS:")
print(silver["products"].dtypes)


# Convertir cantidad de fotografías a número
products_silver["product_photos_qty"] = pd.to_numeric(
    products_silver["product_photos_qty"],
    errors="coerce"
)

# Actualizar la tabla en Silver
silver["products"] = products_silver.copy()

# Verificar el resultado
print("\nREVISION DE FOTOGRAFIAS:")

print(
    "Tipo de dato:",
    silver["products"]["product_photos_qty"].dtype
)

print(
    "Valores faltantes:",
    silver["products"]["product_photos_qty"].isna().sum()
)

print(
    "Total de productos:",
    len(silver["products"])
)


print("\nRELACION ENTRE CATEGORIA Y FOTOGRAFIAS:")

print(
    pd.crosstab(
        silver["products"]["categoria_faltante"],
        silver["products"]["product_photos_qty"].isna()
    )
)


print("\nINTEGRIDAD REFERENCIAL PRODUCTS - ORDERITEMS:")

productos_validos = set(silver["products"]["product_id"])

ventas_sin_producto = silver["orderitems"][
    ~silver["orderitems"]["product_id"].isin(productos_validos)
]

print("Total de registros de ventas:",
      len(silver["orderitems"]))

print("Ventas con producto inexistente:",
      len(ventas_sin_producto))


print("\nCONTROL FINAL DE PRODUCTS:")

print("Productos en Bronze:",
      len(datos["products"]))

print("Productos en Silver:",
      len(silver["products"]))

print("IDs únicos en Silver:",
      silver["products"]["product_id"].nunique())


print("\nREVISION DE ORDERS:")
print("Total de pedidos:", len(silver["orders"]))

print("\nColumnas:")
print(silver["orders"].columns.tolist())

print("\nValores faltantes:")
print(silver["orders"].isnull().sum())

print("\nPedidos duplicados:")
print(silver["orders"]["order_id"].duplicated().sum())


print("\nESTADOS DE LOS PEDIDOS:")
print(silver["orders"]["order_status"].value_counts())

print("\nFECHAS FALTANTES SEGUN ESTADO:")
print(
    silver["orders"]
    .groupby("order_status")[
        [
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date"
        ]
    ]
    .agg(lambda columna: columna.isna().sum())
)


print("\nPEDIDOS ENTREGADOS SIN FECHA DE APROBACION:")

print(
    silver["orders"].loc[
        (silver["orders"]["order_status"] == "delivered")
        & (silver["orders"]["order_approved_at"].isna()),
        [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_customer_date"
        ]
    ].to_string(index=False)
)


# Identificar pedidos entregados sin fecha de aprobación
silver["orders"]["entregado_sin_aprobacion"] = (
    (silver["orders"]["order_status"] == "delivered")
    & (silver["orders"]["order_approved_at"].isna())
)

# Verificar el resultado
print("\nCONTROL DE PEDIDOS ENTREGADOS SIN APROBACION:")

print(
    silver["orders"]["entregado_sin_aprobacion"].value_counts()
)

print("\nTOTAL DE PEDIDOS EN SILVER:")
print(len(silver["orders"]))


print("\nCONTROL CRONOLOGICO DE PEDIDOS:")

orders = silver["orders"]

fechas_validas = (
    orders["order_purchase_timestamp"].notna()
    & orders["order_delivered_customer_date"].notna()
)

fechas_incorrectas = (
    fechas_validas
    & (
        orders["order_delivered_customer_date"]
        < orders["order_purchase_timestamp"]
    )
)

print("Pedidos con fechas comparables:", fechas_validas.sum())

print("Pedidos entregados antes de la compra:",
      fechas_incorrectas.sum())


print("\nCONTROL DE FECHAS DE APROBACION:")

orders = silver["orders"]

fechas_comparables = (
    orders["order_purchase_timestamp"].notna()
    & orders["order_approved_at"].notna()
)

aprobaciones_anteriores = (
    fechas_comparables
    & (
        orders["order_approved_at"]
        < orders["order_purchase_timestamp"]
    )
)

print(
    "Pedidos con fechas comparables:",
    fechas_comparables.sum()
)

print(
    "Aprobaciones anteriores a la compra:",
    aprobaciones_anteriores.sum()
)


print("\nCONTROL DE APROBACION Y ENTREGA:")

orders = silver["orders"]

fechas_comparables = (
    orders["order_approved_at"].notna()
    & orders["order_delivered_customer_date"].notna()
)

entregas_antes_aprobacion = (
    fechas_comparables
    & (
        orders["order_delivered_customer_date"]
        < orders["order_approved_at"]
    )
)

print(
    "Pedidos con ambas fechas:",
    fechas_comparables.sum()
)

print(
    "Entregas anteriores a la aprobacion:",
    entregas_antes_aprobacion.sum()
)


print("\nREVISION DE ENTREGAS ANTES DE APROBACION:")

pedidos_anomalos = orders.loc[
    entregas_antes_aprobacion,
    [
        "order_id",
        "order_status",
        "order_approved_at",
        "order_delivered_customer_date"
    ]
].copy()

pedidos_anomalos["diferencia_horas"] = (
    pedidos_anomalos["order_approved_at"]
    - pedidos_anomalos["order_delivered_customer_date"]
).dt.total_seconds() / 3600

print("Total de pedidos:", len(pedidos_anomalos))

print("\nDiferencias en horas:")
print(pedidos_anomalos["diferencia_horas"].describe())

print("\nPrimeros 10 pedidos:")
print(pedidos_anomalos.head(10).to_string(index=False))


print("\nESTADOS DE LOS 61 PEDIDOS:")
print(pedidos_anomalos["order_status"].value_counts())

print("\nCASOS CON MAYOR DIFERENCIA:")
print(
    pedidos_anomalos.sort_values(
        "diferencia_horas",
        ascending=False
    ).head(5).to_string(index=False)
)



# Identificar pedidos entregados antes de su aprobación
orders = silver["orders"]

silver["orders"]["entrega_antes_aprobacion"] = (
    orders["order_approved_at"].notna()
    & orders["order_delivered_customer_date"].notna()
    & (
        orders["order_delivered_customer_date"]
        < orders["order_approved_at"]
    )
)

print("\nVALIDACION DEL INDICADOR:")
print(
    silver["orders"]["entrega_antes_aprobacion"].value_counts()
)

print("\nTOTAL DE PEDIDOS:")
print(len(silver["orders"]))



print("\nCOLUMNAS FINALES DE ORDERS:")
print(silver["orders"].columns.tolist())

print("\nDIMENSIONES DE ORDERS:")
print(silver["orders"].shape)

print("\nTIPOS DE DATOS DE ORDERS:")
print(silver["orders"].dtypes)

# Validar fechas estimadas de entrega
orders = silver["orders"]

sin_fecha_estimada = orders["order_estimated_delivery_date"].isna().sum()

fecha_estimada_anterior_compra = (
    orders["order_estimated_delivery_date"].notna()
    & orders["order_purchase_timestamp"].notna()
    & (
        orders["order_estimated_delivery_date"]
        < orders["order_purchase_timestamp"]
    )
).sum()

print("\nVALIDACION DE FECHA ESTIMADA")
print("Pedidos sin fecha estimada:", sin_fecha_estimada)
print("Fecha estimada anterior a la compra:", fecha_estimada_anterior_compra)

print("\nREVISION DE ORDERITEMS:")

print("Total de registros:")
print(len(silver["orderitems"]))

print("\nColumnas:")
print(silver["orderitems"].columns.tolist())

print("\nValores faltantes:")
print(silver["orderitems"].isna().sum())

print("\nTipos de datos:")
print(silver["orderitems"].dtypes)



print("\nCONTROL DE CALIDAD DE ORDERITEMS:")

items = silver["orderitems"]

print("Total de registros:", len(items))

print("Articulos duplicados por pedido:",
      items.duplicated(
          subset=["order_id", "order_item_id"]
      ).sum())

print("Precios negativos:",
      (items["price"] < 0).sum())

print("Precios iguales a cero:",
      (items["price"] == 0).sum())

print("Costos de envio negativos:",
      (items["freight_value"] < 0).sum())

print("Envios gratuitos:",
      (items["freight_value"] == 0).sum())



print("\nINTEGRIDAD REFERENCIAL DE ORDERITEMS:")

items = silver["orderitems"]

productos_validos = set(
    silver["products"]["product_id"]
)

pedidos_validos = set(
    silver["orders"]["order_id"]
)

print("Articulos con producto inexistente:",
      (~items["product_id"].isin(productos_validos)).sum())

print("Articulos con pedido inexistente:",
      (~items["order_id"].isin(pedidos_validos)).sum())

print("Total de articulos conservados:",
      len(items))



print("\nVALIDACION DE VENDEDORES:")

vendedores_validos = set(
    silver["sellers"]["seller_id"]
)

vendedores_inexistentes = (
    ~silver["orderitems"]["seller_id"].isin(vendedores_validos)
).sum()

print("Articulos con vendedor inexistente:",
      vendedores_inexistentes)

print("Total de vendedores:",
      len(silver["sellers"]))

print("Total de articulos conservados:",
      len(silver["orderitems"]))



print("\nREVISION DE SELLERS:")

vendedores = silver["sellers"]

print("Total de vendedores:", len(vendedores))

print("\nColumnas:")
print(vendedores.columns.tolist())

print("\nValores faltantes:")
print(vendedores.isna().sum())

print("\nVendedores duplicados por ID:")
print(vendedores["seller_id"].duplicated().sum())

print("\nTipos de datos:")
print(vendedores.dtypes)



print("\nREVISION DE CUSTOMERS:")

clientes = silver["customers"]

print("Total de clientes:", len(clientes))

print("\nColumnas:")
print(clientes.columns.tolist())

print("\nValores faltantes:")
print(clientes.isna().sum())

print("\nClientes duplicados por ID:")
print(clientes["customer_id"].duplicated().sum())

print("\nTipos de datos:")
print(clientes.dtypes)



print("\nANALISIS DE CLIENTES UNICOS:")

print("Total de registros:",
      len(silver["customers"]))

print("Clientes unicos:",
      silver["customers"]["customer_unique_id"].nunique())

print("IDs unicos de pedidos-clientes:",
      silver["customers"]["customer_id"].nunique())

print("Clientes con mas de un registro:",
      (silver["customers"]["customer_unique_id"]
       .value_counts() > 1).sum())



print("\nRELACION ENTRE CUSTOMERS Y ORDERS:")

clientes_validos = set(
    silver["customers"]["customer_id"]
)

pedidos_sin_cliente = silver["orders"][
    ~silver["orders"]["customer_id"].isin(clientes_validos)
]

print("Total de pedidos:",
      len(silver["orders"]))

print("Pedidos con cliente inexistente:",
      len(pedidos_sin_cliente))

print("Total de clientes conservados:",
      len(silver["customers"]))



print("\nREVISION DE PAYMENTS:")

pagos = silver["payments"]

print("Total de registros:", len(pagos))

print("\nColumnas:")
print(pagos.columns.tolist())

print("\nValores faltantes:")
print(pagos.isna().sum())

print("\nTipos de datos:")
print(pagos.dtypes)

print("\nTipos de pago:")
print(pagos["payment_type"].value_counts())



print("\nCONTROL DE CALIDAD DE PAYMENTS:")

pagos = silver["payments"]

pedidos_validos = set(silver["orders"]["order_id"])

print("Pagos con pedido inexistente:",
      (~pagos["order_id"].isin(pedidos_validos)).sum())

print("Pagos negativos:",
      (pagos["payment_value"] < 0).sum())

print("Pagos iguales a cero:",
      (pagos["payment_value"] == 0).sum())

print("Secuencias duplicadas por pedido:",
      pagos.duplicated(
          subset=["order_id", "payment_sequential"]
      ).sum())

print("Pagos no definidos:",
      (pagos["payment_type"] == "not_defined").sum())



print("\nREVISION DE PAGOS ESPECIALES:")

pagos = silver["payments"]

especiales = pagos[
    (pagos["payment_value"] == 0) |
    (pagos["payment_type"] == "not_defined")
]

print(especiales.to_string(index=False))

print("\nRESUMEN DE COINCIDENCIAS:")

print("Pagos en ambas condiciones:",
      ((pagos["payment_value"] == 0) &
       (pagos["payment_type"] == "not_defined")).sum())

print("Total de registros especiales:", len(especiales))



print("\nANALISIS DE MONTOS DE PAYMENTS:")

pagos = silver["payments"]

print(pagos["payment_value"].describe())

print("\nLOS 10 PAGOS MAS ALTOS:")

print(
    pagos.nlargest(10, "payment_value")[
        ["order_id", "payment_type", "payment_value"]
    ].to_string(index=False)
)



print("\nREVISION DEL PAGO MAS ALTO:")

pagos = silver["payments"]
items = silver["orderitems"]

pago_maximo = pagos.loc[
    pagos["payment_value"].idxmax()
]

pedido_id = pago_maximo["order_id"]

print("\nPago encontrado:")
print(pago_maximo.to_string())

articulos = items[
    items["order_id"] == pedido_id
]

print("\nArticulos del pedido:")
print(articulos.to_string(index=False))

print("\nTotal de productos:",
      articulos["price"].sum())

print("Total de envio:",
      articulos["freight_value"].sum())

print("Total de productos mas envio:",
      (articulos["price"] +
       articulos["freight_value"]).sum())

print("Total de pagos del pedido:",
      pagos.loc[
          pagos["order_id"] == pedido_id,
          "payment_value"
      ].sum())



print("\nCONCILIACION GENERAL DE PAGOS:")

pagos = silver["payments"]
items = silver["orderitems"]

total_items = items.assign(
    total_item=items["price"] + items["freight_value"]
).groupby("order_id")["total_item"].sum()

total_pagos = pagos.groupby("order_id")[
    "payment_value"
].sum()

comparacion = total_items.to_frame(
    "total_productos_envio"
).join(
    total_pagos.rename("total_pagado"),
    how="inner"
)

comparacion["diferencia"] = (
    comparacion["total_pagado"] -
    comparacion["total_productos_envio"]
).round(2)

print("Pedidos comparados:", len(comparacion))

print("Pedidos con diferencia mayor a 0.01:",
      (comparacion["diferencia"].abs() > 0.01).sum())

print("\nDIFERENCIAS MAS GRANDES:")
print(
    comparacion.reindex(
        comparacion["diferencia"].abs()
        .sort_values(ascending=False).index
    ).head(10).to_string()
)



print("\nANALISIS DE DIFERENCIAS DE PAGOS:")

diferencias = comparacion[
    comparacion["diferencia"].abs() > 0.01
]

print("Total de pedidos con diferencias:",
      len(diferencias))

print("Pagos mayores al valor del pedido:",
      (diferencias["diferencia"] > 0).sum())

print("Pagos menores al valor del pedido:",
      (diferencias["diferencia"] < 0).sum())

print("\nESTADISTICAS DE LAS DIFERENCIAS:")
print(diferencias["diferencia"].describe())



print("\nTIPOS DE PAGO EN PEDIDOS CON DIFERENCIAS:")

pagos = silver["payments"]

pedidos_diferentes = diferencias.index

pagos_diferentes = pagos[
    pagos["order_id"].isin(pedidos_diferentes)
]

print("\nCantidad de pagos por tipo:")
print(pagos_diferentes["payment_type"].value_counts())

print("\nPedidos con diferencias que usan voucher:")
pedidos_voucher = set(
    pagos_diferentes.loc[
        pagos_diferentes["payment_type"] == "voucher",
        "order_id"
    ]
)

print(len(pedidos_voucher))

print("\nPedidos con diferencias sin voucher:")
print(len(pedidos_diferentes.difference(
    pedidos_voucher
)))



print("\nESTADOS DE PEDIDOS CON DIFERENCIAS:")

pedidos_con_diferencias = silver["orders"][
    silver["orders"]["order_id"].isin(
        diferencias.index
    )
]

print("\nCantidad por estado:")
print(
    pedidos_con_diferencias["order_status"].value_counts()
)

print("\nTotal de pedidos encontrados:")
print(len(pedidos_con_diferencias))

print("\nPedidos con diferencias no entregados:")
print(
    (pedidos_con_diferencias["order_status"] != "delivered").sum()
)



print("\nANALISIS DE DIFERENCIAS Y ENVIOS:")

envios = (
    silver["orderitems"]
    .groupby("order_id")["freight_value"]
    .sum()
)

revision_envios = diferencias.join(
    envios.rename("total_envio")
)

print("\nPedidos cuya diferencia coincide con el envio:")
print(
    (
        (revision_envios["diferencia"].abs() -
         revision_envios["total_envio"]).abs() <= 0.01
    ).sum()
)

print("\nPrimeros 10 pedidos para revisar:")
print(
    revision_envios[
        ["diferencia", "total_envio"]
    ].head(10).to_string()
)



print("\nCLASIFICACION DE DIFERENCIAS:")

magnitud = diferencias["diferencia"].abs()

print("Entre 0.01 y 0.10:",
      ((magnitud > 0.01) & (magnitud <= 0.10)).sum())

print("Mayores a 0.10 y hasta 1:",
      ((magnitud > 0.10) & (magnitud <= 1)).sum())

print("Mayores a 1 y hasta 10:",
      ((magnitud > 1) & (magnitud <= 10)).sum())

print("Mayores a 10:",
      (magnitud > 10).sum())

print("\nTOTAL DE CASOS:")
print(len(diferencias))



print("\nVERIFICACION INDEPENDIENTE DE PAGOS:")

items = silver["orderitems"]
pagos = silver["payments"]

# Sumar productos y envios por pedido
total_articulos = (
    items.assign(
        total_linea=items["price"] + items["freight_value"]
    )
    .groupby("order_id")["total_linea"]
    .sum()
    .round(2)
)

# Sumar todos los pagos por pedido
total_pagos = (
    pagos.groupby("order_id")["payment_value"]
    .sum()
    .round(2)
)

# Comparar sin duplicar registros
verificacion = total_articulos.to_frame(
    "total_articulos"
).join(
    total_pagos.rename("total_pagos"),
    how="inner"
)

verificacion["diferencia"] = (
    verificacion["total_pagos"]
    - verificacion["total_articulos"]
).round(2)

print("Pedidos comparados:", len(verificacion))

print("Pedidos con diferencias mayores a 0.01:",
      (verificacion["diferencia"].abs() > 0.01).sum())

print("Diferencia maxima:",
      verificacion["diferencia"].max())

print("Diferencia minima:",
      verificacion["diferencia"].min())
