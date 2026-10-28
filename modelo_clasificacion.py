from pathlib import Path

import numpy as np
import pandas as pd

from gold import gold

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SEMILLA = 42
PORCENTAJE_DESARROLLO = 0.80
PORCENTAJE_ENTRENAMIENTO = 0.80
UMBRALES = np.arange(0.05, 0.96, 0.05)


def crear_preparacion(X):
    columnas_numericas = X.select_dtypes(include=["number"]).columns.tolist()
    columnas_categoricas = X.select_dtypes(
        include=["object", "category", "string"]
    ).columns.tolist()

    preparacion_numerica = Pipeline(steps=[
        ("faltantes", SimpleImputer(strategy="median")),
        ("escalado", StandardScaler()),
    ])
    preparacion_categorica = Pipeline(steps=[
        (
            "faltantes",
            SimpleImputer(strategy="constant", fill_value="Desconocido"),
        ),
        (
            "codificacion",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
        ),
    ])

    return ColumnTransformer(
        transformers=[
            ("numericas", preparacion_numerica, columnas_numericas),
            ("categoricas", preparacion_categorica, columnas_categoricas),
        ]
    )


def crear_modelos(X):
    return {
        "Regresion Logistica": Pipeline(steps=[
            ("preparacion", crear_preparacion(X)),
            (
                "clasificador",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=SEMILLA,
                ),
            ),
        ]),
        "Random Forest": Pipeline(steps=[
            ("preparacion", crear_preparacion(X)),
            (
                "clasificador",
                RandomForestClassifier(
                    n_estimators=100,
                    class_weight="balanced",
                    random_state=SEMILLA,
                    n_jobs=-1,
                ),
            ),
        ]),
        "HistGradientBoosting": Pipeline(steps=[
            ("preparacion", crear_preparacion(X)),
            (
                "clasificador",
                HistGradientBoostingClassifier(
                    max_iter=100,
                    learning_rate=0.1,
                    random_state=SEMILLA,
                ),
            ),
        ]),
    }


def probabilidades_positivas(modelo, X):
    indice_positivo = list(modelo.classes_).index(1)
    return modelo.predict_proba(X)[:, indice_positivo]


def calcular_metricas(y_real, probabilidades, umbral):
    predicciones = (probabilidades >= umbral).astype(int)
    matriz = confusion_matrix(y_real, predicciones, labels=[0, 1])
    return {
        "precision": precision_score(y_real, predicciones, zero_division=0),
        "recall": recall_score(y_real, predicciones, zero_division=0),
        "f1": f1_score(y_real, predicciones, zero_division=0),
        "accuracy": accuracy_score(y_real, predicciones),
        "roc_auc": roc_auc_score(y_real, probabilidades),
        "pr_auc": average_precision_score(y_real, probabilidades),
        "tn": int(matriz[0, 0]),
        "fp": int(matriz[0, 1]),
        "fn": int(matriz[1, 0]),
        "tp": int(matriz[1, 1]),
    }


def main():
    datos_modelo = gold["order_delivery_risk_features"].copy()
    datos_modelo["order_purchase_timestamp"] = pd.to_datetime(
        datos_modelo["order_purchase_timestamp"],
        errors="coerce",
    )
    datos_modelo = datos_modelo.dropna(
        subset=["order_purchase_timestamp", "late_delivery"]
    ).sort_values("order_purchase_timestamp", kind="mergesort")

    if datos_modelo.empty or datos_modelo["late_delivery"].nunique() != 2:
        raise ValueError(
            "Gold debe contener pedidos fechados y ambas clases de late_delivery."
        )

    X = datos_modelo.drop(
        columns=[
            "order_id",
            "order_purchase_timestamp",
            "late_delivery",
        ]
    )
    y = datos_modelo["late_delivery"].astype(int)
    order_ids = datos_modelo["order_id"]
    purchase_dates = datos_modelo["order_purchase_timestamp"]

    # El ultimo 20 % queda reservado y no participa en seleccion ni ajuste.
    corte_desarrollo = int(len(datos_modelo) * PORCENTAJE_DESARROLLO)
    X_desarrollo = X.iloc[:corte_desarrollo].copy()
    y_desarrollo = y.iloc[:corte_desarrollo].copy()

    # El desarrollo se separa cronologicamente en entrenamiento y validacion.
    corte_entrenamiento = int(len(X_desarrollo) * PORCENTAJE_ENTRENAMIENTO)
    X_train = X_desarrollo.iloc[:corte_entrenamiento].copy()
    y_train = y_desarrollo.iloc[:corte_entrenamiento].copy()
    X_validacion = X_desarrollo.iloc[corte_entrenamiento:].copy()
    y_validacion = y_desarrollo.iloc[corte_entrenamiento:].copy()
    X_test = X.iloc[corte_desarrollo:].copy()
    y_test = y.iloc[corte_desarrollo:].copy()

    if any(particion.nunique() != 2 for particion in (y_train, y_validacion, y_test)):
        raise ValueError(
            "Cada particion temporal debe contener pedidos retrasados y no retrasados."
        )

    ids_test = order_ids.iloc[corte_desarrollo:]
    fechas_test = purchase_dates.iloc[corte_desarrollo:]

    print("=" * 72)
    print("CLASIFICACION DE RIESGO DE ENTREGA TARDIA")
    print("=" * 72)
    print(f"Registros: {len(datos_modelo):,}")
    print(f"Variables predictoras: {X.shape[1]}")
    print(
        "Pedidos tardios: "
        f"{int(y.sum()):,} ({y.mean():.2%} del conjunto)"
    )
    print(
        "Division temporal (entrenamiento / validacion / prueba): "
        f"{len(X_train):,} / {len(X_validacion):,} / {len(X_test):,}"
    )
    print(
        "Fechas de prueba: "
        f"{fechas_test.min()} a {fechas_test.max()}"
    )

    # Baseline separado: siempre asigna la clase mayoritaria del entrenamiento.
    print("\n" + "-" * 72)
    print("BASELINE")
    print("-" * 72)
    baseline = DummyClassifier(strategy="prior")
    baseline.fit(X_train, y_train)
    prob_baseline_validacion = probabilidades_positivas(
        baseline,
        X_validacion,
    )
    metricas_baseline = calcular_metricas(
        y_validacion,
        prob_baseline_validacion,
        0.5,
    )
    print(
        "DummyClassifier (clase mayoritaria) | "
        f"Precision={metricas_baseline['precision']:.3f} | "
        f"Recall={metricas_baseline['recall']:.3f} | "
        f"F1={metricas_baseline['f1']:.3f} | "
        f"PR-AUC={metricas_baseline['pr_auc']:.3f} | "
        f"ROC-AUC={metricas_baseline['roc_auc']:.3f}"
    )

    print("\n" + "-" * 72)
    print("COMPARACION DE CANDIDATOS EN VALIDACION")
    print("-" * 72)
    candidatos = crear_modelos(X_train)
    probabilidades_validacion = {}
    metricas_validacion = {}

    for nombre, modelo in candidatos.items():
        print(f"Entrenando {nombre}...")
        modelo.fit(X_train, y_train)
        probabilidades = probabilidades_positivas(modelo, X_validacion)
        probabilidades_validacion[nombre] = probabilidades
        metricas_validacion[nombre] = calcular_metricas(
            y_validacion,
            probabilidades,
            0.5,
        )
        metricas = metricas_validacion[nombre]
        print(
            f"{nombre:24} | PR-AUC={metricas['pr_auc']:.4f} | "
            f"ROC-AUC={metricas['roc_auc']:.4f} | "
            f"F1@0.50={metricas['f1']:.4f}"
        )

    # PR-AUC es la regla de seleccion para el objetivo desbalanceado.
    modelo_elegido = max(
        metricas_validacion,
        key=lambda nombre: metricas_validacion[nombre]["pr_auc"],
    )
    probabilidades_elegido = probabilidades_validacion[modelo_elegido]

    tabla_umbrales = []
    for umbral in UMBRALES:
        metricas = calcular_metricas(
            y_validacion,
            probabilidades_elegido,
            float(umbral),
        )
        tabla_umbrales.append((float(umbral), metricas))

    umbral_seleccionado, metricas_umbral = max(
        tabla_umbrales,
        key=lambda fila: (fila[1]["f1"], fila[0]),
    )

    print("\n" + "-" * 72)
    print("SELECCION DEFINITIVA")
    print("-" * 72)
    print(f"Modelo seleccionado por PR-AUC de validacion: {modelo_elegido}")
    print(
        f"Umbral seleccionado por F1 de validacion: "
        f"{umbral_seleccionado:.2f}"
    )
    print(
        f"Validacion: Precision={metricas_umbral['precision']:.4f} | "
        f"Recall={metricas_umbral['recall']:.4f} | "
        f"F1={metricas_umbral['f1']:.4f}"
    )
    print("\nUmbrales del modelo seleccionado:")
    print("Umbral | Precision | Recall | F1")
    for umbral, metricas in tabla_umbrales:
        print(
            f"{umbral:6.2f} | {metricas['precision']:9.4f} | "
            f"{metricas['recall']:6.4f} | {metricas['f1']:.4f}"
        )

    modelo_final = candidatos[modelo_elegido]
    prob_test = probabilidades_positivas(modelo_final, X_test)
    metricas_test = calcular_metricas(
        y_test,
        prob_test,
        umbral_seleccionado,
    )
    metricas_test_050 = calcular_metricas(y_test, prob_test, 0.5)

    print("\n" + "-" * 72)
    print("RESULTADOS FINALES EN PRUEBA TEMPORAL")
    print("-" * 72)
    print(f"Modelo: {modelo_elegido}")
    print(f"Umbral elegido en validacion: {umbral_seleccionado:.2f}")
    print(
        f"Precision={metricas_test['precision']:.4f} | "
        f"Recall={metricas_test['recall']:.4f} | "
        f"F1={metricas_test['f1']:.4f} | "
        f"Accuracy={metricas_test['accuracy']:.4f}"
    )
    print(
        f"PR-AUC={metricas_test['pr_auc']:.4f} | "
        f"ROC-AUC={metricas_test['roc_auc']:.4f}"
    )
    print(
        "Matriz de confusion (TN, FP, FN, TP): "
        f"{metricas_test['tn']}, {metricas_test['fp']}, "
        f"{metricas_test['fn']}, {metricas_test['tp']}"
    )
    print(
        f"Comparacion F1 con umbral 0.50: "
        f"{metricas_test_050['f1']:.4f}"
    )

    print("\n" + "-" * 72)
    print("INTERPRETACION DE VARIABLES")
    print("-" * 72)
    cantidad_muestra = min(5000, len(X_test))
    muestra = X_test.sample(
        n=cantidad_muestra,
        random_state=SEMILLA,
    )
    importancia = permutation_importance(
        modelo_final,
        muestra,
        y_test.loc[muestra.index],
        scoring="average_precision",
        n_repeats=3,
        random_state=SEMILLA,
        n_jobs=-1,
    )
    importancias = pd.DataFrame({
        "variable": X.columns,
        "caida_pr_auc": importancia.importances_mean,
        "desviacion": importancia.importances_std,
    }).sort_values("caida_pr_auc", ascending=False)
    print(
        f"Importancia por permutacion en {cantidad_muestra:,} pedidos "
        "de prueba (caida media de PR-AUC):"
    )
    print(importancias.head(10).to_string(index=False, float_format="%.5f"))

    priorizados = pd.DataFrame({
        "order_id": ids_test.to_numpy(),
        "order_purchase_timestamp": fechas_test.to_numpy(),
        "probabilidad_retraso": prob_test,
    })
    priorizados["umbral_seleccionado"] = umbral_seleccionado
    priorizados["priorizar"] = (
        priorizados["probabilidad_retraso"] >= umbral_seleccionado
    )
    priorizados = priorizados.sort_values(
        "probabilidad_retraso",
        ascending=False,
    ).reset_index(drop=True)
    priorizados.insert(0, "prioridad", np.arange(1, len(priorizados) + 1))

    carpeta_salida = Path(__file__).resolve().parent / "outputs"
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    archivo_salida = carpeta_salida / "pedidos_priorizados.csv"
    priorizados.to_csv(archivo_salida, index=False, encoding="utf-8-sig")

    print("\n" + "-" * 72)
    print("EXPORTACION DE PEDIDOS PRIORIZADOS")
    print("-" * 72)
    print(f"Archivo: {archivo_salida}")
    print(f"Pedidos en el ranking: {len(priorizados):,}")
    print(f"Pedidos marcados para priorizar: {int(priorizados['priorizar'].sum()):,}")
    print("\nPrimeros 10 pedidos:")
    print(priorizados.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
