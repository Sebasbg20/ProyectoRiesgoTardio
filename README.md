# ProyectoRiesgoTardio
Proyecto Final - Riesgo tardío por orden

Integrantes:
- Maria José Arauz Retana
- Fiorella Paola Chavez Ordoñez
- Sebastian Barzuna Garza

## 1. Descripción general
Este proyecto integra ingeniería de datos y minería de datos para resolver un problema de negocio con el dataset público OLIST de comercio electrónico en Brasil. El objetivo es construir primero una base analítica confiable y luego desarrollar un modelo de clasificación para estimar el riesgo de entrega tardía por orden.

El flujo del proyecto se estructura en tres capas principales:
- Bronze: carga reproducible de los archivos raw originales.
- Silver: limpieza, tipificación, validación de calidad, deduplicación y consistencia.
- Gold: tabla analítica nivel orden, lista para modelado.

## 2. Objetivo del negocio
Identificar, al momento de confirmar una orden, qué pedidos presentan alto riesgo de entregarse después de la fecha estimada. Este resultado permite priorizar intervención operativa, mejorar la experiencia del cliente y reducir la tasa de entregas tardías.

## 3. Requisitos
Antes de ejecutar el proyecto, se requieren los siguientes elementos:

- Python 3.10 o superior
- pandas
- numpy
- scikit-learn
- pyodbc
- SQL Server local
- ODBC Driver 17 for SQL Server
- Base de datos llamada `olist`

## 4. Estructura del repositorio
- `Data/Raw/`: archivos CSV originales del dataset OLIST
- `Data/control/`: trazabilidad y manifiesto de Bronze
- `bronze_carga_completa.py`: carga completa de archivos raw a Bronze
- `silver.py`: limpieza, validaciones y preparación de la capa Silver
- `gold.py`: construcción de la tabla Gold `order_delivery_risk_features`
- `modelo_clasificacion.py`: entrenamiento, validación y exportación del ranking de riesgo
- `outputs/`: resultados generados por el proyecto

## 5. Configuración previa
1. Crear la base de datos `olist` en SQL Server.
2. Confirmar que el driver ODBC instalado en el sistema es:
   `ODBC Driver 17 for SQL Server`
3. Verificar que cada script apunta a la conexión correcta:
   - `SERVER=localhost`
   - `DATABASE=olist`
   - `Trusted_Connection=yes`
   - `TrustServerCertificate=yes`

## 6. Orden de ejecución
El proyecto debe ejecutarse en este orden:

### Paso 1: Carga a Bronze
```bash
python bronze_carga_completa.py
```
Este paso carga los archivos raw a la base de datos en la capa Bronze y crea el log de trazabilidad.

### Paso 2: Preparación de Silver
```bash
python silver.py
```
En esta etapa se realizan:
- limpieza de tipos de datos,
- tratamiento de nulos,
- normalización de identificadores,
- validaciones de unicidad,
- integridad referencial,
- conversiones de fecha,
- controles de calidad y consistencia.

### Paso 3: Construcción de Gold
```bash
python gold.py
```
Se genera la tabla analítica `order_delivery_risk_features` con una fila por `order_id` y las variables disponibles antes o durante el despacho.

### Paso 4: Modelado y priorización
```bash
python modelo_clasificacion.py
```
Este script:
- separa los datos en entrenamiento, validación y prueba por temporalidad,
- compara modelos base y candidatos,
- selecciona el mejor modelo por PR-AUC,
- ajusta un umbral operativo por F1,
- exporta los pedidos priorizados a `outputs/pedidos_priorizados.csv`.

## 7. Salidas esperadas
Al ejecutar el pipeline completo, se deben generar las siguientes salidas:

- `Data/control/bronze_manifest.csv`
- `outputs/gold_order_delivery_risk_features.csv`
- `outputs/pedidos_priorizados.csv`

## 8. Reglas de calidad de datos
El proyecto incorpora validaciones medibles sobre la base de datos, incluyendo al menos las siguientes reglas:

- completitud: ausencia de valores faltantes críticos
- unicidad: claves no duplicadas
- consistencia: conversiones y valores coherentes
- integridad referencial: joins entre tablas sin referencias huérfanas
- validación temporal: no se usan variables posteriores al evento predictivo
- rangos y dominio: valores numéricos y geográficos dentro de límites razonables

## 9. Consideraciones de modelado
- La variable objetivo es `late_delivery`
- Se define como 1 cuando la fecha de entrega real supera la fecha estimada
- Se excluyen variables posteriores a la entrega o que revelen directamente el target
- La separación de datos se hace por tiempo para evitar fuga de información
- El modelo debe evaluarse con métricas técnicas: precision, recall, F1, ROC-AUC y PR-AUC

## 10. Resultado operativo esperado
La salida del modelo no es solo una métrica técnica, sino una priorización de órdenes con mayor riesgo de retraso. Esto permite a una operación logística:
- revisar pedidos de alto riesgo antes del despacho,
- coordinar acciones preventivas con vendedores o logística,
- reducir devoluciones operativas y mejorar la experiencia del cliente.

## 11. Limitaciones
- El modelo se entrena sobre datos históricos y no reemplaza la decisión humana.
- La priorización se basa en probabilidades estimadas, no en certeza absoluta.
- El uso en producción requiere revalidar la estabilidad de los patrones y mantener la calidad del dato.

## 12. Instalación rápida
Para instalar las dependencias necesarias, puede ejecutarse:

```bash
pip install pandas numpy scikit-learn pyodbc
```

## 13. Verificación rápida de conexión a SQL Server
Antes de ejecutar el pipeline, puede comprobarse la conexión con el siguiente ejemplo:

```python
import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=olist;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

print("Conexión OK")
conn.close()
```

## 14. Flujo reproducible del proyecto
El pipeline completo se ejecuta según este orden:

`Bronze → Silver → Gold → Modelado`

Este orden garantiza que la capa analítica se construya sobre datos validados y no sobre joins improvisados sin control de calidad.




