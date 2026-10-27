import pandas as pd
import pyodbc

conexion = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=olist;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

tablas = [
    "customers_raw",
    "geolocation_raw",
    "nametranslation_raw",
    "order_items_raw",
    "orders_raw",
    "payments_raw",
    "products_raw",
    "reviews_raw",
    "sellers_raw",
]

for tabla in tablas:
    consulta = f"SELECT COUNT(*) FROM bronze.[{tabla}]"
    cursor = conexion.cursor()
    cursor.execute(consulta)
    cantidad = cursor.fetchone()[0]

    print(f"{tabla}: {cantidad} registros")

conexion.close()

print("\nVerificación de Bronze finalizada.")