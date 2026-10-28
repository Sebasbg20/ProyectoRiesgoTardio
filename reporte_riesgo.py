from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


BASE = Path(__file__).resolve().parent
SALIDA = BASE / "outputs"
ARCHIVO_GOLD = SALIDA / "gold_order_delivery_risk_features.csv"
ARCHIVO_RANKING = SALIDA / "pedidos_priorizados.csv"
ARCHIVO_REPORTE = SALIDA / "reporte_riesgo_entrega.html"
MINIMO_POR_GRUPO = 100


def formato_porcentaje(valor):
    return f"{valor:.1%}".replace(".", ",")


def grafico_barras(titulo, resumen, etiqueta):
    ancho = 920
    margen_izquierdo = 190
    margen_derecho = 90
    alto_fila = 48
    alto = 92 + len(resumen) * alto_fila
    ancho_grafico = ancho - margen_izquierdo - margen_derecho
    valores = resumen[["tasa_real", "probabilidad_media"]].to_numpy().ravel()
    maximo = float(np.nanmax(valores)) if len(valores) else 0
    escala = min(1.0, max(0.1, np.ceil(maximo * 20) / 20))

    elementos = [
        f'<svg viewBox="0 0 {ancho} {alto}" role="img" '
        f'aria-label="{escape(titulo)}">',
        '<line x1="190" y1="62" x2="830" y2="62" stroke="#dbe4ee"/>',
    ]

    for indice, fila in resumen.reset_index(drop=True).iterrows():
        y = 86 + indice * alto_fila
        nombre = escape(str(fila[etiqueta]))
        if len(nombre) > 25:
            nombre = nombre[:22] + "..."
        elementos.append(
            f'<text x="178" y="{y + 5}" text-anchor="end" '
            f'class="chart-label">{nombre}</text>'
        )
        for desplazamiento, campo, color in (
            (0, "tasa_real", "#e08a42"),
            (17, "probabilidad_media", "#287a78"),
        ):
            valor = float(fila[campo])
            largo = ancho_grafico * valor / escala
            elementos.append(
                f'<rect x="{margen_izquierdo}" y="{y + desplazamiento}" '
                f'width="{max(0, largo):.1f}" height="12" rx="4" '
                f'fill="{color}"/>'
            )
            elementos.append(
                f'<text x="{margen_izquierdo + largo + 7:.1f}" '
                f'y="{y + desplazamiento + 10}" class="chart-value">'
                f'{formato_porcentaje(valor)}</text>'
            )
        elementos.append(
            f'<text x="840" y="{y + 13}" class="chart-count">'
            f'n={int(fila["pedidos"]):,}</text>'
        )

    y_leyenda = alto - 12
    elementos.extend([
        f'<rect x="260" y="{y_leyenda - 11}" width="12" height="12" '
        'rx="3" fill="#e08a42"/>',
        f'<text x="278" y="{y_leyenda}" class="chart-legend">'
        "Atraso observado</text>",
        f'<rect x="440" y="{y_leyenda - 11}" width="12" height="12" '
        'rx="3" fill="#287a78"/>',
        f'<text x="458" y="{y_leyenda}" class="chart-legend">'
        "Probabilidad media predicha</text>",
        "</svg>",
    ])
    return "".join(elementos)


def resumir_por_grupo(datos, columna, etiqueta):
    resumen = (
        datos.assign(
            grupo=datos[columna].fillna("Sin dato").astype(str),
        )
        .groupby("grupo", as_index=False)
        .agg(
            pedidos=("late_delivery", "size"),
            tasa_real=("late_delivery", "mean"),
            probabilidad_media=("probabilidad_retraso", "mean"),
        )
    )
    resumen = resumen[resumen["pedidos"] >= MINIMO_POR_GRUPO]
    resumen = resumen.sort_values(
        ["tasa_real", "pedidos"],
        ascending=[False, False],
    ).head(10)
    return resumen.rename(columns={"grupo": etiqueta})


def crear_reporte():
    if not ARCHIVO_GOLD.is_file() or not ARCHIVO_RANKING.is_file():
        raise FileNotFoundError(
            "Faltan las salidas requeridas. Ejecute primero gold.py y "
            "modelo_clasificacion.py."
        )

    gold = pd.read_csv(
        ARCHIVO_GOLD,
        usecols=[
            "order_id",
            "order_purchase_timestamp",
            "estado_destino",
            "categoria_principal",
            "late_delivery",
        ],
        dtype={
            "order_id": "string",
            "estado_destino": object,
            "categoria_principal": object,
        },
        low_memory=False,
    )
    ranking = pd.read_csv(
        ARCHIVO_RANKING,
        dtype={"order_id": "string"},
        low_memory=False,
    )

    if gold["order_id"].isna().any() or gold["order_id"].duplicated().any():
        raise ValueError("Gold debe tener order_id único y no nulo.")
    if ranking["order_id"].isna().any() or ranking["order_id"].duplicated().any():
        raise ValueError("El ranking debe tener order_id único y no nulo.")

    ranking["probabilidad_retraso"] = pd.to_numeric(
        ranking["probabilidad_retraso"],
        errors="coerce",
    )
    if (
        ranking["probabilidad_retraso"].isna().any()
        or not ranking["probabilidad_retraso"].between(0, 1).all()
    ):
        raise ValueError("El ranking contiene probabilidades inválidas.")

    umbrales = ranking["umbral_seleccionado"].dropna().unique()
    if len(umbrales) != 1:
        raise ValueError(
            "Se esperaba exactamente un umbral operativo en el ranking."
        )
    umbral = float(umbrales[0])

    prueba = ranking.merge(
        gold,
        on="order_id",
        how="left",
        validate="one_to_one",
        suffixes=("_ranking", "_gold"),
        indicator=True,
    )
    if not prueba["_merge"].eq("both").all():
        raise ValueError("Hay pedidos del ranking que no aparecen en Gold.")
    prueba = prueba.drop(columns="_merge")
    prueba["late_delivery"] = pd.to_numeric(
        prueba["late_delivery"],
        errors="coerce",
    )
    if prueba["late_delivery"].isna().any():
        raise ValueError("La etiqueta real falta en parte del ranking.")
    if not prueba["late_delivery"].isin([0, 1]).all():
        raise ValueError("La etiqueta late_delivery debe ser binaria.")

    prueba["order_purchase_timestamp_gold"] = pd.to_datetime(
        prueba["order_purchase_timestamp_gold"],
        errors="coerce",
    )
    if prueba["order_purchase_timestamp_gold"].isna().any():
        raise ValueError("El conjunto de prueba tiene fechas de compra inválidas.")

    y_real = prueba["late_delivery"].astype(int)
    probabilidades = prueba["probabilidad_retraso"]
    predicciones = probabilidades.ge(umbral)
    precision = precision_score(y_real, predicciones, zero_division=0)
    recall = recall_score(y_real, predicciones, zero_division=0)
    f1 = f1_score(y_real, predicciones, zero_division=0)
    pr_auc = average_precision_score(y_real, probabilidades)
    roc_auc = roc_auc_score(y_real, probabilidades)

    tp = int(((y_real == 1) & predicciones).sum())
    fp = int(((y_real == 0) & predicciones).sum())
    fn = int(((y_real == 1) & ~predicciones).sum())
    tn = int(((y_real == 0) & ~predicciones).sum())
    tasa_base = float(y_real.mean())
    alertas = int(predicciones.sum())

    por_estado = resumir_por_grupo(
        prueba,
        "estado_destino",
        "estado",
    )
    por_categoria = resumir_por_grupo(
        prueba,
        "categoria_principal",
        "categoría",
    )
    prueba["mes_compra"] = (
        prueba["order_purchase_timestamp_gold"].dt.to_period("M").astype(str)
    )
    por_mes = resumir_por_grupo(prueba, "mes_compra", "mes")
    por_mes = por_mes.sort_values("mes")

    def tabla_resumen(resumen, columna_nombre):
        if resumen.empty:
            return (
                f'<p class="note">No hay grupos con al menos '
                f"{MINIMO_POR_GRUPO} pedidos en el conjunto de prueba.</p>"
            )
        filas = []
        for _, fila in resumen.iterrows():
            filas.append(
                "<tr>"
                f"<td>{escape(str(fila[columna_nombre]))}</td>"
                f"<td>{int(fila['pedidos']):,}</td>"
                f"<td>{formato_porcentaje(fila['tasa_real'])}</td>"
                f"<td>{formato_porcentaje(fila['probabilidad_media'])}</td>"
                "</tr>"
            )
        return (
            "<table><thead><tr><th>Grupo</th><th>Pedidos</th>"
            "<th>Atraso observado</th><th>Prob. media</th></tr></thead>"
            f"<tbody>{''.join(filas)}</tbody></table>"
        )

    top_pedidos = prueba.sort_values(
        "probabilidad_retraso",
        ascending=False,
    ).head(10)
    filas_pedidos = "".join(
        "<tr>"
        f"<td>{int(fila.prioridad)}</td>"
        f"<td><code>{escape(str(fila.order_id))}</code></td>"
        f"<td>{formato_porcentaje(fila.probabilidad_retraso)}</td>"
        f"<td>{escape(str(fila.estado_destino) if pd.notna(fila.estado_destino) else 'Sin dato')}</td>"
        "</tr>"
        for fila in top_pedidos.itertuples(index=False)
    )

    matriz = (
        "<table class=\"matrix\"><thead><tr><th></th>"
        "<th>Predijo sin atraso</th><th>Predijo atraso</th></tr></thead>"
        "<tbody>"
        f"<tr><th>Sin atraso real</th><td>{tn:,} (TN)</td>"
        f"<td>{fp:,} (FP)</td></tr>"
        f"<tr><th>Atraso real</th><td>{fn:,} (FN)</td>"
        f"<td>{tp:,} (TP)</td></tr></tbody></table>"
    )

    fecha_inicio = prueba["order_purchase_timestamp_gold"].min().strftime("%Y-%m-%d")
    fecha_fin = prueba["order_purchase_timestamp_gold"].max().strftime("%Y-%m-%d")
    tasa_alerta = alertas / len(prueba)

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reporte de riesgo de entrega tardía — OLIST</title>
<style>
:root {{ color-scheme: light; --ink:#172b3a; --muted:#607384; --line:#dce5eb; --bg:#f4f7f9; --teal:#287a78; --orange:#e08a42; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.55 "Segoe UI",Arial,sans-serif; }}
main {{ max-width:1180px; margin:0 auto; padding:32px 22px 56px; }}
header {{ background:#173b50; color:white; padding:32px; border-radius:18px; }}
h1 {{ margin:0 0 8px; font-size:clamp(26px,4vw,38px); line-height:1.15; }}
h2 {{ margin:0 0 14px; font-size:21px; }}
h3 {{ margin:20px 0 8px; font-size:17px; }}
p {{ margin:8px 0 12px; }}
.subtitle,.muted {{ color:var(--muted); }}
header .subtitle {{ color:#d5e5eb; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin:18px 0; }}
.card,.panel {{ background:white; border:1px solid var(--line); border-radius:14px; padding:18px; }}
.card span {{ display:block; color:var(--muted); font-size:13px; }}
.card strong {{ display:block; margin-top:5px; font-size:25px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,480px),1fr)); gap:16px; margin:16px 0; }}
.panel {{ margin:16px 0; overflow-x:auto; }}
.note {{ color:var(--muted); font-size:13px; }}
.warning {{ border-left:5px solid var(--orange); background:#fff8ef; padding:14px 16px; border-radius:8px; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:9px 10px; white-space:nowrap; }}
th {{ color:var(--muted); font-weight:600; }}
.matrix td {{ text-align:center; font-weight:650; }}
svg {{ width:100%; height:auto; overflow:visible; }}
.chart-label {{ fill:var(--ink); font-size:13px; }}
.chart-value,.chart-count {{ fill:var(--muted); font-size:12px; }}
.chart-legend {{ fill:var(--muted); font-size:12px; }}
ol {{ padding-left:22px; }}
li {{ margin:8px 0; }}
footer {{ color:var(--muted); font-size:12px; margin-top:24px; }}
@media print {{ body {{ background:white; }} main {{ max-width:none; }} .panel,.card,header {{ break-inside:avoid; }} }}
</style>
</head>
<body><main>
<header>
<h1>Riesgo de entrega tardía</h1>
<p class="subtitle">Brazilian E-Commerce Public Dataset by OLIST · evaluación temporal del conjunto de prueba</p>
<p class="subtitle">Pedidos del {fecha_inicio} al {fecha_fin} · {len(prueba):,} pedidos evaluados</p>
</header>

<section class="cards">
<div class="card"><span>Precision</span><strong>{formato_porcentaje(precision)}</strong></div>
<div class="card"><span>Recall</span><strong>{formato_porcentaje(recall)}</strong></div>
<div class="card"><span>F1</span><strong>{formato_porcentaje(f1)}</strong></div>
<div class="card"><span>PR-AUC</span><strong>{pr_auc:.3f}</strong></div>
<div class="card"><span>ROC-AUC</span><strong>{roc_auc:.3f}</strong></div>
<div class="card"><span>Umbral / alertas</span><strong>{umbral:.2f} / {alertas:,}</strong></div>
</section>

<section class="panel">
<h2>Lectura ejecutiva</h2>
<p>El atraso observado en este conjunto fue <strong>{formato_porcentaje(tasa_base)}</strong>. Con el umbral seleccionado en validación ({umbral:.2f}), el modelo marcó {alertas:,} pedidos ({formato_porcentaje(tasa_alerta)}) para revisión; de ellos, {tp:,} fueron atrasos y {fp:,} no lo fueron.</p>
<div class="warning"><strong>Uso recomendado:</strong> tratar la salida como una cola de revisión y no como una decisión automática. La precision de {formato_porcentaje(precision)} implica que muchas alertas no terminan en atraso; validar capacidad y costo operativo antes de escalar.</div>
<p class="note">Este ranking corresponde a pedidos históricos del conjunto de prueba con etiquetas ya conocidas; sirve para evaluar el modelo y no representa pedidos activos listos para intervención.</p>
</section>

<div class="grid">
<section class="panel"><h2>Atrasos por estado destino</h2>
<p class="note">Se muestran hasta 10 estados con mayor tasa observada; mínimo {MINIMO_POR_GRUPO} pedidos.</p>
{grafico_barras("Riesgo por estado destino", por_estado, "estado")}
{tabla_resumen(por_estado, "estado")}
</section>
<section class="panel"><h2>Atrasos por categoría</h2>
<p class="note">Se muestran hasta 10 categorías con mayor tasa observada; mínimo {MINIMO_POR_GRUPO} pedidos.</p>
{grafico_barras("Riesgo por categoría", por_categoria, "categoría")}
{tabla_resumen(por_categoria, "categoría")}
</section>
</div>
<section class="panel"><h2>Evolución mensual en prueba</h2>
<p class="note">Compara la tasa real de atraso con la probabilidad media estimada por el modelo.</p>
{grafico_barras("Riesgo por mes", por_mes, "mes")}
{tabla_resumen(por_mes, "mes")}
</section>

<section class="panel"><h2>Matriz de confusión</h2>
<p class="note">Con el umbral {umbral:.2f}; positivos significan pedidos priorizados por el modelo.</p>
{matriz}
</section>

<section class="panel"><h2>Propuesta de acción preventiva</h2>
<ol>
<li><strong>Revisión humana:</strong> el equipo de operaciones revisa primero la cola ordenada por probabilidad, comenzando por el mayor riesgo; el umbral actual sirve para marcar candidatos, no para prometer atraso.</li>
<li><strong>Validación del pedido:</strong> confirmar el estado del despacho y la información disponible con vendedor o transportista antes de contactar al cliente o cambiar la operación.</li>
<li><strong>Acción proporcional:</strong> si se confirma una señal logística accionable, solicitar actualización/plan al transportista o vendedor y comunicar al cliente solo cuando exista información verificada.</li>
<li><strong>Piloto controlado:</strong> definir con operaciones una capacidad diaria de revisión y registrar alertas revisadas, atrasos confirmados, falsos positivos, tiempo de respuesta y acciones tomadas. La capacidad no se fija en este reporte porque no se proporcionó un límite operativo.</li>
<li><strong>Reevaluación:</strong> comparar resultados del piloto y costos de falsos positivos y falsos negativos antes de cambiar el umbral; recalibrar o reentrenar si cambia el desempeño o la población de pedidos.</li>
</ol>
</section>

<section class="panel"><h2>Diez pedidos con mayor probabilidad</h2>
<p class="note">Muestra histórica del conjunto de prueba; no usar como cola operativa vigente.</p>
<table><thead><tr><th>Prioridad</th><th>Order ID</th><th>Probabilidad</th><th>Estado destino</th></tr></thead>
<tbody>{filas_pedidos}</tbody></table>
</section>
<footer>Generado a partir de outputs/gold_order_delivery_risk_features.csv y outputs/pedidos_priorizados.csv. Los agregados por grupo se calculan sobre el conjunto temporal de prueba y muestran atraso observado y probabilidad media, no relaciones causales.</footer>
</main></body></html>
"""

    ARCHIVO_REPORTE.write_text(html, encoding="utf-8")
    print(f"Reporte generado: {ARCHIVO_REPORTE}")
    print(
        f"Pedidos evaluados: {len(prueba):,}; "
        f"precision={precision:.4f}; recall={recall:.4f}; "
        f"F1={f1:.4f}; PR-AUC={pr_auc:.4f}; ROC-AUC={roc_auc:.4f}"
    )
    return ARCHIVO_REPORTE


if __name__ == "__main__":
    crear_reporte()
