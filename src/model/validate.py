import numpy as np
import pandas as pd
from scipy import stats


def validar_leave_last_out(df: pd.DataFrame, cols_por_año: dict, tolerancia: float = 1.0) -> dict:
    """Entrena la pendiente con todos los cortes menos el último, predice el último, compara contra el real."""
    años = sorted(cols_por_año.keys())
    año_prueba = años[-1]
    años_entrenamiento = años[:-1]

    cols_train = [cols_por_año[a] for a in años_entrenamiento]
    col_real = cols_por_año[año_prueba]
    col_penultimo = cols_por_año[años_entrenamiento[-1]]

    def proyectar(row):
        y = row[cols_train].values.astype(float)
        if np.all(y == y[0]):
            return y[-1]
        pendiente = stats.linregress(años_entrenamiento, y).slope
        return max(0, y[-1] + pendiente * (año_prueba - años_entrenamiento[-1]))

    pred = df.apply(proyectar, axis=1)
    real = df[col_real]
    penultimo = df[col_penultimo]

    def clasificar(cambio):
        return np.where(cambio > tolerancia, 1, np.where(cambio < -tolerancia, -1, 0))

    cambio_real = clasificar(real - penultimo)
    cambio_pred = clasificar(pred - penultimo)
    cambio_baseline = clasificar(pd.Series(0, index=df.index))  # baseline: "no cambia nada"

    return {
        "correlacion_spearman": stats.spearmanr(real, pred)[0],
        "acierto_modelo": (cambio_real == cambio_pred).mean(),
        "acierto_baseline": (cambio_real == cambio_baseline).mean(),
        "año_prueba": año_prueba,
        "años_entrenamiento": años_entrenamiento,
    }