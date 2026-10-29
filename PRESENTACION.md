# Presentación breve: riesgo de entrega tardía en OLIST

## Diapositiva 1 — Problema y decisión
- ¿Podemos anticipar qué pedidos podrían llegar tarde?
- Se construyó y evaluó un clasificador con datos históricos de OLIST.
- **Decisión:** no implementar el modelo actual en operaciones; su Recall en
  prueba fue 2,75 %.

## Diapositiva 2 — Arquitectura de datos
- **Bronze:** conserva los CSV originales y su trazabilidad.
- **Silver:** tipifica, limpia y valida; no elimina anomalías sin justificación.
- **Gold:** integra los datos a nivel de pedido, una fila por `order_id`.
- Resultado: 96.476 pedidos etiquetados y 18 columnas.

## Diapositiva 3 — Controles de calidad
- Unicidad, integridad referencial, conservación de filas y controles de
  conversiones y fechas.
- Se informan anomalías de origen, no se ocultan: 303 diferencias de
  conciliación y 61 entregas anteriores a la aprobación.
- Los controles respaldan la trazabilidad; no garantizan predicciones útiles.

## Diapositiva 4 — Predictores y separación temporal
- El momento de referencia es `order_approved_at`; se usa para ordenar y
  dividir, no como predictor.
- Se usaron seis predictores: cantidad de ítems, valor total, flete, día y mes
  de compra y días estimados de entrega.
- División: 61.735 entrenamiento, 15.434 validación y 19.293 prueba.
- La disponibilidad de precio, flete e información de entrega al aprobar es
  una suposición que el conjunto OLIST no permite verificar por completo.

## Diapositiva 5 — Comparación y selección
- Se compararon DummyClassifier, Regresión Logística, Random Forest e
  HistGradientBoosting.
- PR-AUC de validación: 0,0810; 0,1165; 0,1167; **0,1289**.
- Se eligió HistGradientBoosting; el umbral 0,15 maximizó F1 en validación
  (0,1935). La prueba se reservó para la evaluación final.

## Diapositiva 6 — Prueba y limitación principal
- Precision: **18,06 %** · Recall: **2,75 %** · F1: **0,0477**.
- PR-AUC: **0,1251** · ROC-AUC: **0,7500**.
- Detectó **28 de 1.020** atrasos y emitió **155 alertas**; 992 atrasos no se
  detectaron.
- **Conclusión central:** el rendimiento cayó en prueba y no justifica uso
  operativo, aunque el umbral se seleccionó en validación sin consultar prueba.

## Diapositiva 7 — Próximo paso: piloto humano, solo tras revalidar
- Primero investigar la variación temporal y mejorar la sensibilidad del
  modelo en una prueba temporal nueva.
- Si una versión posterior demuestra utilidad, empezar con revisión humana y
  sin decisiones ni comunicaciones automáticas.
- Medir alertas correctas, falsas alarmas, atrasos no detectados, capacidad,
  tiempos y costos; definir criterios de avance antes del piloto.

## Nota para la exposición

La evidencia reproducible es la ejecución secuencial de los scripts Bronze,
Silver, Gold, modelo y reporte. El notebook es complementario y no se debe
presentar como completamente ejecutado.
