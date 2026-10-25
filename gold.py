import numpy as np
import pandas as pd

from silver import silver

print("\nINTEGRACION DE ORDERITEMS, PRODUCTS Y SELLERS:")

items = silver["orderitems"].merge(
    silver["products"][
        [
            "product_id",
            "categoria_analisis",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm"
        ]
    ],
    on="product_id",
    how="left"
)

items = items.merge(
    silver["sellers"][
        [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_state"
        ]
    ],
    on="seller_id",
    how="left"
)

# Volumen de cada articulo en cm3
items["volumen_cm3"] = (
    items["product_length_cm"]
    * items["product_height_cm"]
    * items["product_width_cm"]
)

print("Articulos en Silver:", len(silver["orderitems"]))
print("Articulos despues de integrar:", len(items))



# Resumen de articulos por pedido
grupo = items.groupby("order_id")

resumen_items = pd.DataFrame({
    "cantidad_items": grupo["order_item_id"].count(),
    "cantidad_vendedores": grupo["seller_id"].nunique(),
    "valor_total": grupo["price"].sum(),
    "freight_value": grupo["freight_value"].sum(),
    "peso_total_g": grupo["product_weight_g"].sum(min_count=1),
    "volumen_total_cm3": grupo["volumen_cm3"].sum(min_count=1)
})

# El articulo principal es el de mayor precio dentro del pedido
item_principal = (
    items.sort_values(
        ["order_id", "price", "order_item_id"],
        ascending=[True, False, True]
    )
    .drop_duplicates(subset="order_id")
    .set_index("order_id")[
        [
            "categoria_analisis",
            "seller_id",
            "seller_zip_code_prefix",
            "seller_state"
        ]
    ]
    .rename(columns={
        "categoria_analisis": "categoria_principal",
        "seller_id": "vendedor_principal",
        "seller_zip_code_prefix": "zip_vendedor",
        "seller_state": "estado_origen"
    })
)



print("\nINTEGRACION DE ORDERS, CUSTOMERS Y ARTICULOS:")

base = silver["orders"][
    [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_estimated_delivery_date",
        "order_delivered_customer_date"
    ]
].copy()

base = base.merge(
    silver["customers"][
        [
            "customer_id",
            "customer_zip_code_prefix",
            "customer_state"
        ]
    ].rename(columns={
        "customer_zip_code_prefix": "zip_cliente",
        "customer_state": "estado_destino"
    }),
    on="customer_id",
    how="left"
)

base = base.merge(
    resumen_items,
    left_on="order_id",
    right_index=True,
    how="left"
)

base = base.merge(
    item_principal,
    left_on="order_id",
    right_index=True,
    how="left"
)

print("Pedidos en Silver:", len(silver["orders"]))
print("Pedidos despues de integrar:", len(base))



print("\nINTEGRACION DE GEOLOCATION:")

geo = silver["geolocation"][
    [
        "geolocation_zip_code_prefix",
        "latitud",
        "longitud"
    ]
]

base = base.merge(
    geo.rename(columns={
        "geolocation_zip_code_prefix": "zip_vendedor",
        "latitud": "lat_vendedor",
        "longitud": "lng_vendedor"
    }),
    on="zip_vendedor",
    how="left"
)

base = base.merge(
    geo.rename(columns={
        "geolocation_zip_code_prefix": "zip_cliente",
        "latitud": "lat_cliente",
        "longitud": "lng_cliente"
    }),
    on="zip_cliente",
    how="left"
)

print("Pedidos despues de integrar geolocation:", len(base))

# Distancia aproximada en kilometros (formula de Haversine)
lat_v = np.radians(base["lat_vendedor"])
lng_v = np.radians(base["lng_vendedor"])
lat_c = np.radians(base["lat_cliente"])
lng_c = np.radians(base["lng_cliente"])

a = (
    np.sin((lat_c - lat_v) / 2) ** 2
    + np.cos(lat_v) * np.cos(lat_c)
    * np.sin((lng_c - lng_v) / 2) ** 2
)

base["distancia_km"] = 2 * 6371 * np.arcsin(np.sqrt(a))

print("Pedidos sin distancia:", base["distancia_km"].isna().sum())



# Variables de fecha
base["order_purchase_timestamp"] = pd.to_datetime(
    base["order_purchase_timestamp"], errors="coerce"
)

base["order_estimated_delivery_date"] = pd.to_datetime(
    base["order_estimated_delivery_date"], errors="coerce"
)

base["order_delivered_customer_date"] = pd.to_datetime(
    base["order_delivered_customer_date"], errors="coerce"
)

# Dia de la semana (0 = lunes) y mes de la compra
base["dia_semana_compra"] = base["order_purchase_timestamp"].dt.dayofweek
base["mes_compra"] = base["order_purchase_timestamp"].dt.month

# Dias prometidos al cliente al momento de la compra
base["dias_estimados_entrega"] = (
    base["order_estimated_delivery_date"]
    - base["order_purchase_timestamp"]
).dt.total_seconds() / 86400

# Vendedor y cliente en el mismo estado
base["mismo_estado"] = (
    base["estado_origen"] == base["estado_destino"]
).astype(int)



print("\nVARIABLE OBJETIVO LATE_DELIVERY:")

# Solo se puede calcular en pedidos con fecha de entrega
fechas_comparables = (
    base["order_delivered_customer_date"].notna()
    & base["order_estimated_delivery_date"].notna()
)

base["late_delivery"] = (
    (
        base["order_delivered_customer_date"]
        > base["order_estimated_delivery_date"]
    )
    .astype(int)
    .where(fechas_comparables)
)

print("Pedidos sin fecha de entrega (fuera de Gold):",
      (~fechas_comparables).sum())



print("\nTABLA GOLD ORDER_DELIVERY_RISK_FEATURES:")

# Se excluyen variables posteriores a la entrega:
# order_delivered_customer_date, order_status y reviews.
# order_purchase_timestamp se conserva solo para dividir por tiempo.
columnas_gold = [
    "order_id",
    "order_purchase_timestamp",
    "cantidad_items",
    "cantidad_vendedores",
    "valor_total",
    "freight_value",
    "peso_total_g",
    "volumen_total_cm3",
    "categoria_principal",
    "estado_origen",
    "estado_destino",
    "distancia_km",
    "mismo_estado",
    "dia_semana_compra",
    "mes_compra",
    "dias_estimados_entrega",
    "late_delivery"
]

gold = {}

gold["order_delivery_risk_features"] = (
    base.loc[base["late_delivery"].notna(), columnas_gold]
    .copy()
)

gold["order_delivery_risk_features"]["late_delivery"] = (
    gold["order_delivery_risk_features"]["late_delivery"].astype(int)
)

print("Filas y columnas:")
print(gold["order_delivery_risk_features"].shape)

print("\nGranularidad: order_id duplicados:")
print(gold["order_delivery_risk_features"]["order_id"].duplicated().sum())

print("\nValores faltantes:")
print(gold["order_delivery_risk_features"].isna().sum())

print("\nDistribucion de late_delivery:")
print(
    gold["order_delivery_risk_features"]["late_delivery"]
    .value_counts()
)

print("\nProporcion de late_delivery:")
print(
    gold["order_delivery_risk_features"]["late_delivery"]
    .value_counts(normalize=True)
    .round(4)
)

print("\nPrimera y ultima compra:")
print(
    gold["order_delivery_risk_features"]["order_purchase_timestamp"].min(),
    "-",
    gold["order_delivery_risk_features"]["order_purchase_timestamp"].max()
)

print("\nCOLUMNAS DISPONIBLES PARA EL MODELO:")
print(gold["order_delivery_risk_features"].columns.tolist()) 