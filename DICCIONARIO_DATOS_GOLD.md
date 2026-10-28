# Diccionario de datos Gold

## Identificación y alcance

- **Tabla lógica:** `order_delivery_risk_features`
- **Archivo:** `outputs/gold_order_delivery_risk_features.csv`
- **Granularidad:** una fila por `order_id`. `gold.py` construye la base desde `orders`, valida que `order_id` no esté duplicado y comprueba que las uniones no alteren la cantidad de pedidos.
- **Alcance de las filas:** pedidos con fecha real de entrega y fecha estimada disponibles para calcular `late_delivery`. Los pedidos sin ambas fechas comparables quedan fuera de Gold.
- **Columnas:** 17.
- **Predictoras del modelo:** 14.
- **Columnas excluidas del entrenamiento:** `order_id`, `order_purchase_timestamp` y `late_delivery`.

### Tipos de datos de la tabla Gold

La tabla Gold `order_delivery_risk_features` se almacena en formato CSV, el cual no conserva información explícita sobre los tipos de datos.

Los tipos indicados en este diccionario se determinaron a partir de la estructura de las variables, las transformaciones implementadas en `gold.py` y la representación de los valores en el archivo generado.

Se distinguen variables numéricas (`float64`, `int64`), categóricas (`object`) y temporales. La fecha de compra se almacena como texto en el CSV y posteriormente se convierte a formato de fecha para el análisis.

Los tipos presentados son inferidos y están sujetos a verificación mediante la lectura completa del archivo con pandas.

## Diccionario de columnas

| Nombre exacto | Tipo observado/inferido en el CSV | Significado | Tabla y columna(s) de origen | Transformación aplicada en Gold | Función dentro del proyecto |
|---|---|---|---|---|---|
| `order_id` | Texto; identificador alfanumérico (`object` esperado) | Identificador único de la orden. | `orders.order_id` | Se conserva como llave al integrar tablas. Se comprueba que sea único después de las uniones y en Gold. | Identificador y llave de granularidad; no es predictor. |
| `order_purchase_timestamp` | Texto con fecha y hora (`object` esperado en CSV); se convierte a `datetime` en `modelo_clasificacion.py` | Fecha y hora de compra de la orden. | `orders.order_purchase_timestamp` | Se tipifica como fecha con `pd.to_datetime(errors="coerce")`. Se conserva para ordenar temporalmente y dividir los datos. | Columna auxiliar temporal; excluida de `X` y no es predictor. |
| `cantidad_items` | Numérico decimal (`float64` inferido; el CSV muestra valores como `1.0`) | Cantidad de ítems asociados a la orden. | `order_items.order_item_id` | Agrupación por `order_id`; conteo de `order_item_id`. Se integra al pedido mediante unión izquierda. | Predictora. |
| `cantidad_vendedores` | Numérico decimal (`float64` inferido; el CSV muestra valores como `1.0`) | Cantidad de vendedores distintos que participan en la orden. | `order_items.seller_id` | Agrupación por `order_id`; conteo de vendedores únicos con `nunique()`. Se integra mediante unión izquierda. | Predictora. |
| `valor_total` | Numérico decimal (`float64` inferido) | Suma del precio de los ítems de la orden; no incluye el flete en esta columna. | `order_items.price` | Suma por `order_id` (`sum`). | Predictora. |
| `freight_value` | Numérico decimal (`float64` inferido) | Suma de los valores de flete de los ítems de la orden. | `order_items.freight_value` | Suma por `order_id` (`sum`). | Predictora. |
| `peso_total_g` | Numérico decimal (`float64` inferido) | Peso agregado de los productos de la orden, expresado en gramos. | `products.product_weight_g`, asociada a los ítems por `product_id`; `order_items.order_id` para agrupar | Unión izquierda de ítems con productos; suma por `order_id` con `sum(min_count=1)`, de modo que un grupo sin ningún peso conocido puede permanecer nulo. | Predictora. |
| `volumen_total_cm3` | Numérico decimal (`float64` inferido) | Suma del volumen calculado de los productos de la orden, en centímetros cúbicos. | `products.product_length_cm`, `product_height_cm` y `product_width_cm`, asociadas por `product_id`; `order_items.order_id` para agrupar | Por ítem calcula `longitud × altura × anchura`; después suma por `order_id` con `sum(min_count=1)`. | Predictora. |
| `categoria_principal` | Texto (`object` esperado) | Categoría del ítem principal seleccionado para representar la orden; no es una lista de todas las categorías del pedido. | `products.product_category_name` (mediante `products.categoria_analisis`), relacionada con `order_items.product_id` | Silver define `categoria_analisis` como `product_category_name.fillna("Sin categoría")`. Gold selecciona por orden el ítem de mayor `price`; los empates se resuelven por `order_item_id` ascendente. | Predictora categórica. |
| `estado_origen` | Texto/código de estado (`object` esperado) | Estado brasileño del vendedor del ítem principal elegido para representar el pedido. | `sellers.seller_state`, relacionado con `order_items.seller_id` | Se toma del vendedor del ítem de mayor precio; desempate por `order_item_id` ascendente. | Predictora categórica. |
| `estado_destino` | Texto/código de estado (`object` esperado) | Estado brasileño del cliente que recibe la orden. | `customers.customer_state`, relacionado con `orders.customer_id` | Renombrado a `estado_destino` en la unión de customers con orders. | Predictora categórica. |
| `distancia_km` | Numérico decimal (`float64` inferido) | Distancia geográfica aproximada entre el prefijo postal del vendedor principal y el del cliente, en kilómetros; no representa necesariamente la ruta de transporte. | `sellers.seller_zip_code_prefix`, `customers.customer_zip_code_prefix` y `geolocation.geolocation_zip_code_prefix`, `latitud`, `longitud` | Se promedian coordenadas por prefijo en Silver; Gold hace uniones izquierdas para vendedor y cliente y aplica la fórmula de Haversine con radio terrestre de 6.371 km. Puede quedar nula si faltan coordenadas. | Predictora numérica. |
| `mismo_estado` | Entero (`int64` inferido; valores 0/1) | Indicador de si los estados del vendedor principal y del cliente coinciden. | `sellers.seller_state` y `customers.customer_state` | Comparación de igualdad entre `estado_origen` y `estado_destino`, convertida a entero (`True` → 1; `False` → 0). | Predictora binaria. |
| `dia_semana_compra` | Entero (`int64` inferido; lunes = 0) | Día de la semana de la compra, según la convención de pandas: lunes 0 a domingo 6. | `orders.order_purchase_timestamp` | Se extrae con `.dt.dayofweek` después de convertir la fecha a datetime. | Predictora temporal derivada. |
| `mes_compra` | Entero (`int64` inferido; 1–12) | Mes calendario de la compra. | `orders.order_purchase_timestamp` | Se extrae con `.dt.month` después de convertir la fecha a datetime. | Predictora temporal derivada. |
| `dias_estimados_entrega` | Numérico decimal (`float64` inferido) | Tiempo entre la compra y la fecha estimada de entrega, expresado en días; puede incluir fracciones de día. | `orders.order_purchase_timestamp` y `orders.order_estimated_delivery_date` | Diferencia entre fecha estimada y fecha de compra; el intervalo se convierte a segundos y se divide entre 86.400. | Predictora numérica. |
| `late_delivery` | Entero (`int64` inferido; valores 0/1) | Etiqueta binaria: `1` si `order_delivered_customer_date > order_estimated_delivery_date`; `0` en caso contrario. Si falta cualquiera de las dos fechas comparables, la etiqueta queda nula y la fila se excluye de Gold. | `orders.order_delivered_customer_date` y `orders.order_estimated_delivery_date` | Comparación estricta `>`; el resultado se conserva solo cuando ambas fechas no son nulas y se convierte a entero en Gold. | Variable objetivo; nunca debe incluirse como predictor. |

## Separación de variables para el modelo

### 14 predictoras

`cantidad_items`, `cantidad_vendedores`, `valor_total`, `freight_value`, `peso_total_g`, `volumen_total_cm3`, `categoria_principal`, `estado_origen`, `estado_destino`, `distancia_km`, `mismo_estado`, `dia_semana_compra`, `mes_compra` y `dias_estimados_entrega`.

### Tres columnas excluidas del entrenamiento

- `order_id`: identificador; se usa para trazabilidad, no como característica del modelo.
- `order_purchase_timestamp`: se utiliza para ordenamiento y partición temporal. El clasificador no la recibe como predictor.
- `late_delivery`: etiqueta objetivo; no puede usarse para predecir su propio valor.

El código de `modelo_clasificacion.py` crea `X` eliminando explícitamente esas tres columnas y usa `late_delivery` como `y`.

## Disponibilidad temporal y limitaciones

El objetivo del proyecto es estimar riesgo al confirmar una orden. El dataset OLIST contiene valores históricos, pero no conserva un registro de cuándo cada campo o dato de catálogo estuvo disponible para el sistema de predicción. Por ello, que una columna se derive de datos anteriores o asociados a una orden **no demuestra por sí solo** que estuviera disponible en el instante exacto de confirmación.

| Grupo de variables | Limitación que debe tenerse en cuenta |
|---|---|
| `cantidad_items`, `valor_total`, `freight_value` | Proceden de ítems y valores de precio/flete asociados a la orden. El dataset no proporciona un sello temporal que confirme cuándo quedaron fijados; disponibilidad exacta al confirmar: **pendiente de verificación**. |
| `cantidad_vendedores`, `estado_origen`, `categoria_principal` | Vendedor, estado y categoría se extraen de relaciones y catálogo históricos. No hay versionado temporal del catálogo ni evidencia de cuándo se asignó el vendedor respecto de la confirmación: disponibilidad exacta: **pendiente de verificación**. |
| `peso_total_g`, `volumen_total_cm3` | Se basan en atributos de producto de la tabla de productos, sin historial de cambios ni fecha de vigencia: disponibilidad histórica al momento de cada orden: **pendiente de verificación**. |
| `estado_destino` | Procede del estado del cliente relacionado con la orden. El proyecto no demuestra si el registro de cliente corresponde a una instantánea del momento de compra: **pendiente de verificación**. |
| `distancia_km` | Usa coordenadas promedio de geolocation por prefijo postal y ubicación del vendedor/cliente. No hay fecha de vigencia de esas coordenadas ni precisión de ruta; disponibilidad y exactitud operativa: **pendiente de verificación**. |
| `mismo_estado` | Se deriva de los estados de origen y destino, por lo que hereda las limitaciones temporales de ambos campos. |
| `dia_semana_compra`, `mes_compra` | Se derivan de la fecha de compra, por lo que son calculables una vez conocida esa fecha. El dataset no documenta el instante exacto en que el evento de “confirmación” se define en el proceso del proyecto. |
| `dias_estimados_entrega` | Se deriva de la fecha estimada de entrega y la fecha de compra. Aunque es una estimación destinada al cliente, el dataset no incluye un sello que pruebe cuándo se generó o comunicó respecto de la confirmación: disponibilidad exacta: **pendiente de verificación**. |
| `late_delivery` | Requiere la fecha real de entrega, que ocurre después del evento de predicción. Se utiliza únicamente para etiquetar pedidos históricos y entrenar/evaluar; no es una característica disponible para una orden nueva. |

Por estas limitaciones, antes de presentar el modelo como operativo al confirmar una orden, debe validarse con la definición del proceso de negocio qué significa “confirmar”, qué campos están realmente disponibles en ese instante y si los catálogos y ubicaciones históricos pueden reconstruirse sin información futura.

## Fuentes de este diccionario

- `gold.py`: selección de columnas, joins, agregaciones, características derivadas, objetivo y validación de granularidad.
- `silver.py`: limpieza, tipificación y tratamiento de fechas, categorías, dimensiones físicas y geolocalización.
- `outputs/gold_order_delivery_risk_features.csv`: nombres y valores representados en el CSV Gold.
- `modelo_clasificacion.py`: exclusión de las tres columnas de `X` y separación de `late_delivery` como objetivo.
