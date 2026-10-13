
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
