
<<<<<<< HEAD

=======
>>>>>>> 7e8f4d63893ecaaef01227769471c05d82238fcd
from pathlib import Path
import csv

# Ubicación de los archivos CSV
carpeta_raw = Path(__file__).resolve().parent / "Data" / "Raw"

# Buscar los archivos CSV
archivos_csv = sorted(carpeta_raw.glob("*.csv"))

print("VERIFICACIÓN DE ARCHIVOS BRONZE")
print("-" * 40)

if not archivos_csv:
    print("No se encontraron archivos CSV.")
else:
    for archivo in archivos_csv:
        with archivo.open("r", encoding="utf-8-sig", newline="") as f:
            lector = csv.reader(f)
            encabezado = next(lector, None)
            cantidad = sum(1 for fila in lector)

        print("Archivo:", archivo.name)
        print("Registros:", cantidad)
        print("Columnas:", len(encabezado) if encabezado else 0)
        print("-" * 40)

print("Verificación finalizada.")



from datetime import datetime
import hashlib

# Carpeta donde guardaremos los controles de Bronze
carpeta_control = Path(__file__).resolve().parent / "Data" / "control"
carpeta_control.mkdir(parents=True, exist_ok=True)

# Archivo de trazabilidad
archivo_control = carpeta_control / "bronze_manifest.csv"

# Fecha real de esta verificación
fecha_verificacion = datetime.now().astimezone().isoformat()

with archivo_control.open("w", newline="", encoding="utf-8") as salida:
    escritor = csv.writer(salida)

    escritor.writerow([
        "archivo_origen",
        "fecha_verificacion",
        "cantidad_registros",
        "hash_sha256",
        "estado"
    ])

    for archivo in archivos_csv:
        # Calcular huella digital del archivo original
        hash_archivo = hashlib.sha256()

        with archivo.open("rb") as f:
            for bloque in iter(lambda: f.read(1024 * 1024), b""):
                hash_archivo.update(bloque)

        # Contar los registros
        with archivo.open("r", encoding="utf-8-sig", newline="") as f:
            lector = csv.reader(f)
            next(lector, None)
            cantidad = sum(1 for fila in lector)

        escritor.writerow([
            archivo.name,
            fecha_verificacion,
            cantidad,
            hash_archivo.hexdigest(),
            "VERIFICADO"
        ])

print("\nManifiesto Bronze generado correctamente:")
print(archivo_control)



# CONEXIÓN DE BRONZE A SQL SERVER

import pyodbc

try:
    conexion = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=olist;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    cursor = conexion.cursor()

    # Verificar que la tabla de trazabilidad existe
    cursor.execute("""
        SELECT COUNT(*)
        FROM dbo.bronze_load_log
    """)

    cantidad = cursor.fetchone()[0]

    print("\nConexión a SQL Server exitosa.")
    print("Registros actuales en bronze_load_log:", cantidad)

    conexion.close()

except pyodbc.Error as error:
    print("\nError al conectar con SQL Server:")
    print(error)



# PRIMERA CARGA REAL DE BRONZE

archivo_csv = carpeta_raw / "product_category_name_translation.csv"

conexion = None

try:
    conexion = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=olist;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    cursor = conexion.cursor()

    # Leer el CSV original
    with archivo_csv.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        lector = csv.reader(f)
        encabezados = next(lector)
        registros = list(lector)

    # Comprobar que tiene las columnas esperadas
    assert encabezados == [
        "product_category_name",
        "product_category_name_english"
    ], "Los encabezados del CSV no coinciden."

    # Evitar duplicar datos al volver a ejecutar
    cursor.execute("""
        SELECT COUNT(*)
        FROM bronze.nametranslation_raw
    """)

    existentes = cursor.fetchone()[0]

    if existentes > 0:
        print("La tabla ya contiene registros.")
        print("Se omite la carga para evitar duplicados.")

    else:
        # Insertar los datos originales
        cursor.executemany("""
            INSERT INTO bronze.nametranslation_raw
            (product_category_name,
             product_category_name_english)
            VALUES (?, ?)
        """, registros)

        # Comprobar la cantidad insertada
        cursor.execute("""
            SELECT COUNT(*)
            FROM bronze.nametranslation_raw
        """)

        cargados = cursor.fetchone()[0]

        if cargados != len(registros):
            raise ValueError(
                "La cantidad cargada no coincide con el CSV."
            )

        # Registrar la carga real en la bitácora
        cursor.execute("""
            INSERT INTO dbo.bronze_load_log
            (source_file, target_table,
             source_row_count, loaded_row_count,
             load_status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            archivo_csv.name,
            "bronze.nametranslation_raw",
            len(registros),
            cargados,
            "SUCCESS",
            "Carga inicial desde CSV original"
        )

        conexion.commit()

        print("Carga Bronze completada.")
        print("Registros originales:", len(registros))
        print("Registros cargados:", cargados)
        print("Bitácora actualizada correctamente.")

except (pyodbc.Error, ValueError, AssertionError, OSError) as error:
    if conexion is not None:
        conexion.rollback()
    print("Error durante la carga:", error)

finally:
    if conexion is not None:
        conexion.close()
