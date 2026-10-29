# Diccionario de datos Gold

## Identificacion y alcance

- **Tabla logica:** `order_delivery_risk_features`
- **Archivo:** `outputs/gold_order_delivery_risk_features.csv`
- **Granularidad:** una fila por `order_id`, validada en `gold.py`.
- **Alcance:** pedidos con fecha real y estimada de entrega para construir `late_delivery`.
- **Columnas:** 18.
- **Predictores autorizados:** 6; el modelo los selecciona mediante una lista explicita.

Gold se guarda como CSV, por lo que los tipos se infieren al leerlo. Las marcas
de tiempo se almacenan como texto y se convierten a datetime en el modelo.

## Diccionario de columnas

| Columna | Origen y transformacion | Uso en el proyecto |
|---|---|---|
| `order_id` | `orders.order_id`; llave de la orden, unica en Gold. | Identificador; excluido de los predictores. |
| `order_purchase_timestamp` | `orders.order_purchase_timestamp`; se conserva para derivar calendario y mostrar fechas. | Auxiliar; no entra directamente al modelo ni define la particion. |
| `order_approved_at` | `orders.order_approved_at`; fecha de aprobacion conservada para el orden cronologico. | Referencia del momento de prediccion y particion; no entra al modelo. |
| `cantidad_items` | Conteo de `order_item_id` por pedido. | Predictor autorizado; se asume que el contenido de la orden esta definido al aprobarla. |
| `cantidad_vendedores` | Conteo de vendedores distintos por pedido. | Excluido: no hay marca temporal de asignacion de vendedores. |
| `valor_total` | Suma de `order_items.price` por pedido. | Predictor autorizado bajo la suposicion de que el precio esta definido al aprobar la orden. |
| `freight_value` | Suma de `order_items.freight_value` por pedido. | Predictor autorizado bajo la suposicion de que el costo de envio ya se conoce al aprobarla. |
| `peso_total_g` | Suma del peso de productos asociados a los items. | Excluido: el catalogo no tiene historial de versiones. |
| `volumen_total_cm3` | Suma de largo por alto por ancho de los productos asociados. | Excluido: el catalogo no tiene historial de versiones. |
| `categoria_principal` | Categoria del item de mayor precio; desempate por `order_item_id` ascendente. | Excluida: no existe historial temporal del catalogo. |
| `estado_origen` | Estado del vendedor del item de mayor precio. | Excluido: la asignacion del vendedor no tiene marca temporal. |
| `estado_destino` | Estado del cliente unido por `customer_id`. | Excluido: no hay una instantanea temporal del registro del cliente. |
| `distancia_km` | Distancia Haversine entre coordenadas medias por prefijo postal, derivadas de geolocation. | Excluida: las coordenadas se agregan sobre todo el periodo, sin vigencia por fecha. |
| `mismo_estado` | Comparacion de los estados de origen y destino, codificada como 0/1. | Excluido porque depende de estados y asignaciones sin instantaneas temporales. |
| `dia_semana_compra` | Dia de semana derivado de `order_purchase_timestamp` (lunes=0). | Predictor autorizado, derivado de la fecha de compra. |
| `mes_compra` | Mes derivado de `order_purchase_timestamp` (1-12). | Predictor autorizado, derivado de la fecha de compra. |
| `dias_estimados_entrega` | Diferencia en dias entre la fecha estimada y la fecha de compra. | Predictor autorizado bajo la suposicion de que la promesa estimada ya se conoce al aprobar la orden. |
| `late_delivery` | `1` si `order_delivered_customer_date > order_estimated_delivery_date`; `0` en otro caso. | Etiqueta objetivo; nunca predictor. |

## Control de fuga temporal

El momento de prediccion se fija en la aprobacion de la orden
(`order_approved_at`). Esta fecha solo ordena los datos para separar
cronologicamente entrenamiento, validacion y prueba. El modelo usa exactamente
estos seis predictores:

`cantidad_items`, `valor_total`, `freight_value`, `dia_semana_compra`,
`mes_compra` y `dias_estimados_entrega`.

La fecha real de entrega solo construye la etiqueta. Se excluyen del modelo las
variables de vendedor, cliente, catalogo y geolocalizacion porque OLIST no
guarda su historial de asignacion, vigencia o actualizacion. La lista permitida
en `modelo_clasificacion.py` evita que columnas nuevas de Gold entren
automaticamente al modelo.

Se asume que el contenido, el precio, el flete y la fecha estimada de la orden
ya se conocen al aprobarla. El dataset no contiene marcas de tiempo por campo
para demostrar esa disponibilidad historica; por eso el proyecto mitiga la
fuga directa y reduce el riesgo temporal, pero no puede garantizar su ausencia
completa. Para validarlo en produccion harian falta instantaneas o bitacoras de
disponibilidad de los datos.

## Fuentes

- `gold.py`: joins, agregaciones, objetivo y granularidad Gold.
- `modelo_clasificacion.py`: lista permitida de predictores y particion por fecha de aprobacion.
- `outputs/gold_order_delivery_risk_features.csv`: estructura y valores de Gold.
