
from pathlib import Path
import csv
import re
import pyodbc

BASE = Path(__file__).resolve().parent
RAW = BASE / "Data" / "Raw"

CONEXION = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=olist;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

ARCHIVOS = {
    "olist_customers_dataset.csv": "customers_raw",
    "olist_geolocation_dataset.csv": "geolocation_raw",
    "olist_order_items_dataset.csv": "order_items_raw",
    "olist_order_payments_dataset.csv": "payments_raw",
    "olist_order_reviews_dataset.csv": "reviews_raw",
    "olist_orders_dataset.csv": "orders_raw",
    "olist_products_dataset.csv": "products_raw",
    "olist_sellers_dataset.csv": "sellers_raw",
    "product_category_name_translation.csv": "nametranslation_raw",
}

def cargar_archivo(conexion, nombre_archivo, tabla):
    archivo = RAW / nombre_archivo

    if not archivo.is_file():
        raise FileNotFoundError(archivo)

    with archivo.open("r", encoding="utf-8-sig", newline="") as f:
        lector = csv.reader(f)
        columnas = next(lector, None)

        if not columnas or len(set(columnas)) != len(columnas):
            raise ValueError("Encabezados inválidos")

        for columna in columnas:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", columna):
                raise ValueError(f"Columna inválida: {columna}")

        cursor = conexion.cursor()
        destino = f"bronze.{tabla}"

        # No modificar tablas que ya existan
        cursor.execute(
            "SELECT OBJECT_ID(?, 'U')",
            destino
        )

        if cursor.fetchone()[0] is not None:
            print(f"OMITIDA: {destino} ya existe")
            return

        columnas_sql = ", ".join(
            f"[{c}] NVARCHAR(MAX) NULL" for c in columnas
        )

        cursor.execute(
            f"CREATE TABLE bronze.[{tabla}] ({columnas_sql})"
        )

        marcadores = ", ".join("?" for _ in columnas)
        nombres = ", ".join(f"[{c}]" for c in columnas)

        sql = (
            f"INSERT INTO bronze.[{tabla}] ({nombres}) "
            f"VALUES ({marcadores})"
        )

        total = 0
        lote = []

        for fila in lector:
            if len(fila) != len(columnas):
                raise ValueError("Fila con número incorrecto de columnas")

            lote.append(tuple(fila))

            if len(lote) >= 1000:
                cursor.executemany(sql, lote)
                total += len(lote)
                lote.clear()

        if lote:
            cursor.executemany(sql, lote)
            total += len(lote)

        cursor.execute(
            f"SELECT COUNT(*) FROM bronze.[{tabla}]"
        )
        cargados = cursor.fetchone()[0]

        if total != cargados:
            raise ValueError("No coinciden las cantidades")

        cursor.execute("""
            INSERT INTO dbo.bronze_load_log
            (source_file, target_table,
             source_row_count, loaded_row_count,
             load_status, notes)
            VALUES (?, ?, ?, ?, 'SUCCESS', ?)
        """, nombre_archivo, destino, total, cargados,
             "Carga reproducible por lotes")

        conexion.commit()

        print(f"OK: {destino} - {cargados} registros")


def preparar_base_datos(conexion):
    cursor = conexion.cursor()
    cursor.execute("""
        IF SCHEMA_ID(N'bronze') IS NULL
            EXEC(N'CREATE SCHEMA bronze');

        IF OBJECT_ID(N'dbo.bronze_load_log', N'U') IS NULL
        BEGIN
            CREATE TABLE dbo.bronze_load_log (
                load_id BIGINT IDENTITY(1, 1) PRIMARY KEY,
                source_file NVARCHAR(255) NOT NULL,
                target_table NVARCHAR(255) NOT NULL,
                source_row_count BIGINT NOT NULL,
                loaded_row_count BIGINT NOT NULL,
                load_status NVARCHAR(20) NOT NULL,
                notes NVARCHAR(MAX) NULL,
                loaded_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
            )
        END
    """)
    conexion.commit()


def main():
    conexion = pyodbc.connect(CONEXION)
    conexion.autocommit = False

    try:
        preparar_base_datos(conexion)
        for archivo, tabla in ARCHIVOS.items():
            try:
                cargar_archivo(conexion, archivo, tabla)
            except Exception:
                conexion.rollback()
                print(f"ERROR cargando {archivo}")
                raise
    finally:
        conexion.close()


if __name__ == "__main__":
    main()

