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
- Silver: limpieza, tipificación, validación de calidad y consistencia; los duplicados se detectan y se conservan para no modificar datos fuente sin justificación.
- Gold: tabla analítica nivel orden, lista para modelado.

> **Conclusión vigente:** el modelo no está listo para uso operativo. El umbral
> 0,15 se eligió maximizando F1 en validación, pero en prueba temporal el
> Recall fue 2,75 %: detectó 28 de 1.020 atrasos y generó 155 alertas. El
> ranking es retrospectivo; no debe interpretarse como una lista de pedidos
> activos ni usarse para automatizar acciones.

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
- `Data/Curated/`: nueve tablas Silver/Curated y su manifiesto
- `bronze_carga_completa.py`: carga completa de archivos raw a Bronze
- `silver.py`: limpieza, validaciones y preparación de la capa Silver
- `gold.py`: construcción de la tabla Gold `order_delivery_risk_features`
- `modelo_clasificacion.py`: entrenamiento, validación y exportación del ranking de riesgo
- `reporte_riesgo.py`: creación del reporte visual HTML y propuesta operativa
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
En esta etapa se generan las tablas Silver en memoria, se ejecutan las reglas de
calidad y se persisten los CSV curados y su manifiesto en `Data/Curated/`.

### Tratamiento Silver de tipos, nulos y duplicados

| Caso | Tratamiento aplicado | Motivo / efecto |
|---|---|---|
| Valores vacíos en columnas físicas de productos | Se convierten a nulos y luego a tipo numérico (`errors="coerce"`). | Evita tratar cadenas vacías como mediciones; las filas se conservan y se marca `datos_fisicos_incompletos`. |
| Categoría de producto faltante | Se conserva `product_category_name` nulo, se marca `categoria_faltante` y se crea `categoria_analisis` con el valor `Sin categoría`. | La variable original sigue disponible; la categoría derivada permite agrupar y modelar esos productos. |
| Fechas vacías o inválidas de órdenes | Se convierten a `NaT`; se conservan los pedidos y se calculan indicadores para anomalías temporales. | No se inventan fechas. Para Gold supervisado se excluyen únicamente los pedidos que no tienen fecha real de entrega o fecha estimada, porque no es posible etiquetar `late_delivery`. |
| Valores numéricos vacíos o no convertibles en ítems/pagos | Se convierten a nulos al tipificar. | Los registros no se eliminan; las validaciones cuantifican valores faltantes y anómalos. |
| Prefijos postales sin coincidencia en geolocation | Se conservan; los joins de Gold son `left` y las coordenadas/distancia quedan nulas cuando no hay coincidencia. | Se evita descartar pedidos y no se imputan coordenadas desconocidas. |
| Duplicados en claves | No se eliminan automáticamente. Se verifican claves simples y compuestas y el proceso falla si las claves que deben ser únicas presentan duplicados. | Preserva trazabilidad y evita escoger arbitrariamente una fila. |
| `review_id` repetidos | Se conservan las filas; se valida la combinación `(review_id, order_id)`, que es la clave útil para identificar duplicados de reseña dentro de un pedido. | Hay identificadores `review_id` repetidos en el origen, pero no se deben borrar sin determinar primero si son registros distintos. Las reseñas no se unen a Gold. |
| Geolocation | Se excluyen del agregado las coordenadas fuera del rango geográfico configurado para Brasil; las restantes se promedian por prefijo postal y se guarda el número de coordenadas agregadas. | Produce una fila por prefijo, utilizable como dimensión geográfica; el CSV raw original permanece intacto en Bronze. |

Silver normaliza los códigos postales a cinco caracteres, tipifica precios,
envíos, pagos, dimensiones y fechas, y agrega indicadores sin eliminar los
registros de las tablas fuente. Las validaciones automatizadas comprueban
conservación de filas, unicidad, integridad referencial, rangos, conversiones y
consistencia. Una regla que detecta anomalías de origen las reporta; no implica
que se corrijan o eliminen automáticamente.

### Joins y granularidad de Gold

Gold parte de `orders`, cuya clave `order_id` debe ser única; su granularidad
final es **una fila por pedido**. Los joins son `left` para conservar pedidos
aun si una dimensión no tiene coincidencia, y declaran `validate="many_to_one"`
para impedir que una llave no única multiplique las filas.

| Integración | Claves y granularidad antes del join | Cardinalidad | Transformación / resultado |
|---|---|---|---|
| `orderitems` + `products` | Muchos ítems por `product_id`; una fila por producto | Muchos-a-uno | Añade categoría y atributos físicos del producto al nivel de ítem. |
| Resultado + `sellers` | Muchos ítems por `seller_id`; una fila por vendedor | Muchos-a-uno | Añade prefijo postal y estado del vendedor al nivel de ítem. |
| Ítems enriquecidos → resumen | Una fila por ítem, con `order_id` repetido | Agrupación por `order_id` | Calcula cantidad de ítems y vendedores, suma precio/envío, peso y volumen por orden. |
| Ítems enriquecidos → ítem principal | Puede haber varios ítems por `order_id` | Se selecciona un ítem por pedido | Se toma el de mayor precio; los empates se resuelven por `order_item_id` ascendente. Su categoría, vendedor y estado representan el pedido. |
| `orders` + `customers` | Una fila por pedido; un registro por `customer_id` | Muchos-a-uno | Añade estado destino y prefijo postal del cliente. |
| Pedidos + resumen e ítem principal | Una fila por pedido en cada agregado | Muchos-a-uno | Añade features agregadas y representativas al pedido. |
| Pedidos + `geolocation` (vendedor y cliente) | Un prefijo postal por pedido y una fila por prefijo en Silver | Muchos-a-uno, dos joins | Añade coordenadas promedio; calcula distancia Haversine cuando ambos extremos tienen coordenadas. |

En cada etapa se comprueba que el número de pedidos no cambie y que `order_id`
no se duplique. `payments` y `reviews` se curan y se validan en Silver, pero no
se integran en Gold porque no se requieren para las variables definidas.
Además, pueden tener varias filas por pedido; para incorporarlas habría que
definir primero una agregación por `order_id`. Las reseñas son posteriores a la
compra y no se usan como predictores del riesgo estimado al confirmar la orden.

### Paso 3: Construcción de Gold
```bash
python gold.py
```
Se genera la tabla analítica `order_delivery_risk_features` con una fila por
`order_id`. Incluye `order_approved_at` únicamente como referencia temporal
para ordenar y dividir los datos; no se usa como predictor. En este proyecto
la aprobación se usa como aproximación al momento de confirmación, ya que el
dataset no define por sí mismo ese evento operativo.

### Paso 4: Modelado y priorización
```bash
python modelo_clasificacion.py
```
Este script:
- usa una lista explícita y conservadora de predictores,
- separa los datos cronológicamente por `order_approved_at`, que no entra al
  clasificador,
- compara modelos base y candidatos,
- selecciona el mejor modelo por PR-AUC,
- selecciona un umbral de clasificación por F1 en validación,
- exporta los pedidos priorizados a `outputs/pedidos_priorizados.csv`.

Los predictores autorizados son `cantidad_items`, `valor_total`,
`freight_value`, `dia_semana_compra`, `mes_compra` y
`dias_estimados_entrega`. Se excluyen del clasificador las variables de
vendedor, cliente, catálogo y geolocalización que no tienen historial temporal
para demostrar que su valor era conocido al aprobar la orden. El uso del
contenido/precio/flete del pedido y de la fecha estimada supone que esos datos
ya estaban disponibles en ese momento; OLIST no permite verificarlo campo por
campo, por lo que la suposición debe declararse como limitación.

### Paso 5: Reporte visual y propuesta de acción
```bash
python reporte_riesgo.py
```
Genera `outputs/reporte_riesgo_entrega.html`, un reporte autocontenido con
métricas del conjunto temporal de prueba, matriz de confusión, riesgo por estado
destino, categoría y mes, y los pedidos con mayor probabilidad. El reporte
contrasta la tasa real de atraso con la probabilidad media estimada y filtra
grupos con menos de 100 pedidos para evitar conclusiones basadas en muestras
muy pequeñas.

El ranking se construye con el conjunto histórico de prueba y sus etiquetas se
usan solo para evaluación retrospectiva. No es una lista de pedidos activos.
Como propuesta preventiva, operaciones revisa manualmente las alertas en orden
de probabilidad, verifica primero el estado con vendedor o transportista y solo
actúa o comunica al cliente cuando confirme una señal logística. Antes de
desplegarlo, el equipo debe establecer su capacidad de revisión y medir en un
piloto alertas correctas, falsas alarmas, atrasos no detectados, tiempos y
costos. No se automatizan decisiones ni se promete que una alerta sea un atraso.

## 7. Salidas esperadas
Al ejecutar el pipeline completo, se deben generar las siguientes salidas:

- `Data/control/bronze_manifest.csv`
- `Data/Curated/silver_*.csv`
- `Data/Curated/silver_manifest.csv`
- `outputs/gold_order_delivery_risk_features.csv`
- `outputs/modelo_clasificacion_v1.joblib`
- `outputs/pedidos_priorizados.csv`
- `outputs/reporte_riesgo_entrega.html`

El script actual guarda el modelo como `modelo_clasificacion_v1.joblib`. Si
`modelo_riesgo_entrega_v1.joblib` permanece en `outputs/`, esta secuencia no
lo actualiza; no debe confundirse con el artefacto de la corrida vigente.

### Resultado vigente y decisión

La corrida completa del 28 de octubre de 2026 seleccionó HistGradientBoosting
por su PR-AUC de validación (0,1289) y eligió el umbral 0,15 maximizando F1 en
validación. En los 19.293 pedidos de prueba, el resultado fue:

| Métrica en prueba | Resultado |
|---|---:|
| Recall | 2,75 % |
| Precision | 18,06 % |
| F1 | 0,0477 |
| PR-AUC | 0,1251 |
| ROC-AUC | 0,7500 |

Con ese umbral se detectaron 28 de los 1.020 atrasos y se emitieron 155
alertas. La caída del Recall entre validación y prueba temporal no justifica
una implementación operativa. Se requiere investigar la estabilidad temporal
y mejorar el modelo antes de proponer un piloto; cualquier evaluación futura
debe mantener revisión humana y medir falsas alarmas y atrasos no detectados.

La corrida ejecutada regeneró Gold, el ranking y el reporte HTML en secuencia.
`reporte_riesgo.py` comprueba la unicidad y cobertura del ranking contra Gold
antes de producir el reporte. El archivo `resultados_modelo.txt` que pueda
existir en el repositorio no lo genera `modelo_clasificacion.py`; no se debe
usar como evidencia de la corrida vigente. Los resultados reproducibles se
obtienen en la salida de consola y en el reporte HTML.

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
- La fecha real de entrega solo se usa para formar la etiqueta; nunca es predictor
- El modelo usa una lista explícita de seis predictores y excluye variables de
  geolocalización agregada, vendedor, cliente y catálogo sin historial temporal
- La separación cronológica se hace por `order_approved_at`; esta marca se
  excluye de las variables predictoras
- Se asume que ítems, precio, flete y fecha estimada están disponibles al
  aprobar la orden; el dataset no permite comprobar completamente esta
  disponibilidad histórica
- El modelo debe evaluarse con métricas técnicas: precision, recall, F1, ROC-AUC y PR-AUC

## 10. Uso futuro sujeto a revalidación
La priorización podría apoyar una operación logística si una versión futura
demuestra utilidad en datos recientes. El resultado actual no justifica usar
las alertas en operaciones. Si el desempeño mejora y se autoriza un piloto, el
equipo podría:
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
python -m pip install pandas numpy scikit-learn pyodbc matplotlib ipykernel
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

`Bronze → Silver → Gold → Modelado → Reporte`

Este orden garantiza que la capa analítica se construya sobre datos validados y no sobre joins improvisados sin control de calidad.

Ejecute los cinco comandos desde la raíz del repositorio y en este orden:

```bash
python bronze_carga_completa.py
python silver.py
python gold.py
python modelo_clasificacion.py
python reporte_riesgo.py
```

La carga Bronze crea las tablas que falten y omite las existentes; el flujo
requiere SQL Server local, la base `olist` y el driver ODBC documentados arriba.
Compruebe que Gold, `pedidos_priorizados.csv` y el reporte HTML se regeneraron
en la misma corrida. El reporte se construye a partir del Gold y del ranking
recién generado y valida su correspondencia.

`OLIST_Analisis_y_Modelado.ipynb` es material complementario y no sustituye
esta secuencia como evidencia reproducible. No se debe presentar como notebook
completamente ejecutado hasta ejecutar y revisar todas sus celdas.
