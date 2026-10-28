

import sys
import subprocess
import importlib.util

bibliotecas = {
    "numpy": "numpy",
    "pandas": "pandas",
    "pyodbc": "pyodbc",
    "sklearn": "scikit-learn"
}

for modulo, paquete in bibliotecas.items():
    if importlib.util.find_spec(modulo) is None:
        print(f"Instalando {paquete}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", paquete
        ])

import pandas as pd

from gold import gold

datos_modelo = gold["order_delivery_risk_features"].copy()

print("\nDATOS PARA EL MODELO:")
print("Filas y columnas:", datos_modelo.shape)
print("\nPrimeros 5 pedidos:")
print(datos_modelo.head())


# Variable que queremos predecir
y = datos_modelo["late_delivery"]

# Variables que utilizaremos para predecir
X = datos_modelo.drop(
    columns=[
        "order_id",
        "order_purchase_timestamp",
        "late_delivery"
    ]
)

print("\nVARIABLES PREDICTORAS:")
print(X.columns.tolist())

print("\nDIMENSIONES:")
print("X:", X.shape)
print("y:", y.shape)


# Ordenar los pedidos por fecha de compra
orden = datos_modelo["order_purchase_timestamp"].sort_values().index

X = X.loc[orden]
y = y.loc[orden]

# Utilizar 80 % para entrenamiento y 20 % para prueba
punto_corte = int(len(X) * 0.80)

X_train = X.iloc[:punto_corte].copy()
X_test = X.iloc[punto_corte:].copy()

y_train = y.iloc[:punto_corte].copy()
y_test = y.iloc[punto_corte:].copy()

print("\nDIVISION TEMPORAL:")
print("Pedidos para entrenamiento:", len(X_train))
print("Pedidos para prueba:", len(X_test))


from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Identificar columnas numericas y categoricas
columnas_numericas = X.select_dtypes(
    include=["number"]
).columns.tolist()

columnas_categoricas = X.select_dtypes(
    include=["object", "category", "string"]
).columns.tolist()


# Preparar columnas numericas
preparacion_numerica = Pipeline(steps=[
    ("faltantes", SimpleImputer(strategy="median")),
    ("escalado", StandardScaler())
])



preparacion_categorica = Pipeline(steps=[
    ("faltantes", SimpleImputer(
        strategy="constant",
        fill_value="Desconocido"
    )),
    ("convertir", OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False
    ))
])

# Unir ambas preparaciones
preparacion = ColumnTransformer(
    transformers=[
        ("numericas", preparacion_numerica, columnas_numericas),
        ("categoricas", preparacion_categorica, columnas_categoricas)
    ]
)

print("\nPREPARACION DE DATOS CONFIGURADA")


# Importar el algoritmo de clasificacion
from sklearn.linear_model import LogisticRegression

# Crear el modelo con la preparacion de datos
modelo_logistico = Pipeline(steps=[
    ("preparacion", preparacion),
    ("clasificador", LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    ))
])

print("\nMODELO DE REGRESION LOGISTICA CONFIGURADO")


# Entrenar el modelo con los pedidos antiguos
print("\nINICIANDO ENTRENAMIENTO...")

modelo_logistico.fit(X_train, y_train)

print("MODELO ENTRENADO CORRECTAMENTE")


# Evaluar el modelo de clasificacion
from sklearn.metrics import (
    classification_report,
    confusion_matrix
)

# Predecir los pedidos de prueba
predicciones = modelo_logistico.predict(X_test)

# Mostrar los resultados
print("\nEVALUACION DEL MODELO LOGISTICO:")

print("\nMATRIZ DE CONFUSION:")
print(confusion_matrix(y_test, predicciones))

print("\nREPORTE DE CLASIFICACION:")
print(classification_report(
    y_test,
    predicciones,
    zero_division=0
))


# SEGUNDO MODELO: RANDOM FOREST
from sklearn.ensemble import RandomForestClassifier

modelo_forest = Pipeline(steps=[
    ("preparacion", preparacion),
    ("clasificador", RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    ))
])

print("\nMODELO RANDOM FOREST CONFIGURADO")


# Entrenar Random Forest
print("\nINICIANDO ENTRENAMIENTO RANDOM FOREST...")

modelo_forest.fit(X_train, y_train)

print("RANDOM FOREST ENTRENADO CORRECTAMENTE")

# Realizar predicciones
predicciones_forest = modelo_forest.predict(X_test)

# Evaluar los resultados
print("\nMATRIZ DE CONFUSION RANDOM FOREST:")
print(confusion_matrix(y_test, predicciones_forest))

print("\nREPORTE DE CLASIFICACION RANDOM FOREST:")
print(classification_report(
    y_test,
    predicciones_forest,
    zero_division=0
))


# TERCER MODELO: HISTGRADIENTBOOSTING
from sklearn.ensemble import HistGradientBoostingClassifier

modelo_hist = Pipeline(steps=[
    ("preparacion", preparacion),
    ("clasificador", HistGradientBoostingClassifier(
        max_iter=100,
        learning_rate=0.1,
        random_state=42
    ))
])

print("\nMODELO HISTGRADIENTBOOSTING CONFIGURADO")


# Entrenar HistGradientBoosting
print("\nINICIANDO ENTRENAMIENTO HISTGRADIENTBOOSTING...")

modelo_hist.fit(X_train, y_train)

print("HISTGRADIENTBOOSTING ENTRENADO CORRECTAMENTE")

# Realizar predicciones
predicciones_hist = modelo_hist.predict(X_test)

# Evaluar los resultados
print("\nMATRIZ DE CONFUSION HISTGRADIENTBOOSTING:")
print(confusion_matrix(y_test, predicciones_hist))

print("\nREPORTE DE CLASIFICACION HISTGRADIENTBOOSTING:")
print(classification_report(
    y_test,
    predicciones_hist,
    zero_division=0
))


# METRICAS ROC-AUC Y PR-AUC
from sklearn.metrics import roc_auc_score, average_precision_score

modelos = {
    "Regresion Logistica": modelo_logistico,
    "Random Forest": modelo_forest,
    "HistGradientBoosting": modelo_hist
}

print("\nCOMPARACION ROC-AUC Y PR-AUC:")

for nombre, modelo in modelos.items():
    probabilidades = modelo.predict_proba(X_test)[:, 1]

    roc_auc = roc_auc_score(y_test, probabilidades)
    pr_auc = average_precision_score(y_test, probabilidades)

    print(f"\n{nombre}")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"PR-AUC: {pr_auc:.4f}")


# VALIDACION TEMPORAL
# Reservar el 20 % final del entrenamiento para validar

corte_validacion = int(len(X_train) * 0.80)

X_entrenamiento = X_train.iloc[:corte_validacion].copy()
X_validacion = X_train.iloc[corte_validacion:].copy()

y_entrenamiento = y_train.iloc[:corte_validacion].copy()
y_validacion = y_train.iloc[corte_validacion:].copy()

print("\nVALIDACION TEMPORAL:")
print("Pedidos para entrenar:", len(X_entrenamiento))
print("Pedidos para validar:", len(X_validacion))
print("Pedidos reservados para prueba:", len(X_test))


# ENTRENAMIENTO PARA VALIDACION TEMPORAL
from sklearn.base import clone

modelos_validacion = {
    "Regresion Logistica": clone(modelo_logistico),
    "Random Forest": clone(modelo_forest),
    "HistGradientBoosting": clone(modelo_hist)
}

print("\nENTRENAMIENTO PARA VALIDACION TEMPORAL")

for nombre, modelo in modelos_validacion.items():
    print(f"\nEntrenando: {nombre}")

    modelo.fit(X_entrenamiento, y_entrenamiento)

    print(f"{nombre}: entrenamiento completado")


# COMPARACION DE UMBRALES EN VALIDACION
from sklearn.metrics import precision_score, recall_score, f1_score

umbrales = [0.10, 0.20, 0.30, 0.40, 0.50]

print("\nCOMPARACION DE UMBRALES EN VALIDACION")

for nombre, modelo in modelos_validacion.items():

    probabilidades = modelo.predict_proba(X_validacion)[:, 1]

    print(f"\nMODELO: {nombre}")

    for umbral in umbrales:
        predicciones_val = (probabilidades >= umbral).astype(int)

        precision = precision_score(
            y_validacion, predicciones_val, zero_division=0
        )
        recall = recall_score(
            y_validacion, predicciones_val, zero_division=0
        )
        f1 = f1_score(
            y_validacion, predicciones_val, zero_division=0
        )

        print(
            f"Umbral: {umbral:.2f} | "
            f"Precision: {precision:.3f} | "
            f"Recall: {recall:.3f} | "
            f"F1: {f1:.3f}"
        )
# COMPARACION DE LOS 100 PEDIDOS CON MAYOR RIESGO
print("\nCOMPARACION DE LOS 100 PEDIDOS CON MAYOR RIESGO")

for nombre, modelo in modelos_validacion.items():

    probabilidades = modelo.predict_proba(X_validacion)[:, 1]

    comparacion = pd.DataFrame({
        "probabilidad": probabilidades,
        "retraso_real": y_validacion.to_numpy()
    })

    top_100 = comparacion.nlargest(100, "probabilidad")

    retrasos_detectados = int(top_100["retraso_real"].sum())

    print(f"\nModelo: {nombre}")
    print(f"Retrasos reales entre los 100 pedidos: {retrasos_detectados}")
    print(f"Alertas incorrectas: {100 - retrasos_detectados}")

    # COMPARACION DE LOS 500 PEDIDOS CON MAYOR RIESGO

print("\nCOMPARACION DE LOS 500 PEDIDOS CON MAYOR RIESGO")

for nombre, modelo in modelos_validacion.items():

    probabilidades = modelo.predict_proba(X_validacion)[:, 1]

    comparacion = pd.DataFrame({
        "probabilidad": probabilidades,
        "retraso_real": y_validacion.to_numpy()
    })

    top_500 = comparacion.nlargest(500, "probabilidad")

    retrasos_detectados = int(top_500["retraso_real"].sum())

    print(f"\nModelo: {nombre}")
    print(f"Retrasos reales entre los 500 pedidos: {retrasos_detectados}")
    print(f"Alertas incorrectas: {500 - retrasos_detectados}")
    print(f"Precision en Top 500: {retrasos_detectados / 500:.2%}")