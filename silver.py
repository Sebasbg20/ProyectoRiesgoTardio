
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

# Nombres reales de las tablas en SQL Server
tablas = [
    "Sellers",
    "Productos",
    "nametranslation",
    "geolocation",
    "orders",
    "orderItems",
    "payments",
    "reviews"
]

# Diccionario para guardar los DataFrames
datos = {}

# Recorrer todas las tablas
for nombre in tablas:

    print("\n" + "=" * 50)
    print("DIAGNÓSTICO DE:", nombre)
    print("=" * 50)

    # Consultar SQL Server
    query = f"SELECT * FROM dbo.[{nombre}]"

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










