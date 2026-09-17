# src/model/trend.py
import numpy as np
import pandas as pd
from scipy import stats


def compute_trend_generico(df: pd.DataFrame, cols_por_año: dict[int, str]) -> pd.DataFrame:
    """Pendiente + R² sobre cualquier número de cortes temporales."""
    años = np.array(sorted(cols_por_año.keys()))
    cols = [cols_por_año[a] for a in años]

    def slope_r2(row):
        y = row[cols].values.astype(float)
        if np.all(y == y[0]):
            return pd.Series({"tendencia_pendiente": 0.0, "tendencia_r2": 0.0})
        res = stats.linregress(años, y)
        return pd.Series({"tendencia_pendiente": res.slope, "tendencia_r2": res.rvalue**2})

    df = df.copy()
    df[["tendencia_pendiente", "tendencia_r2"]] = df.apply(slope_r2, axis=1)
    return df


def compute_saturacion(df: pd.DataFrame) -> pd.DataFrame:
    """Oferta actual por cada 1,000 habitantes -- señal negativa para el score."""
    df = df.copy()
    oferta_total = df["n_salud_denue_2026"].fillna(0) + df["n_salud_publica"].fillna(0)
    df["saturacion_por_mil"] = np.where(
        df["POB_TOTAL"] > 0,
        oferta_total / df["POB_TOTAL"] * 1000,
        np.nan,
    )
    return df


def _normalizar(serie: pd.Series) -> pd.Series:
    """Normalización por percentil (rank), robusta a outliers como torres médicas."""
    return serie.rank(pct=True, na_option="keep")


def compute_opportunity_score(
    df: pd.DataFrame,
    w_demanda: float = 0.65,
    w_tendencia: float = 0.0,
    w_saturacion: float = 0.35,
) -> pd.DataFrame:
    df = compute_saturacion(df)

    demanda_norm = _normalizar(df["PSDSS"].fillna(df["PSDSS"].median()))
    tendencia_norm = _normalizar(df["tendencia_pendiente"])
    saturacion_norm = _normalizar(df["saturacion_por_mil"].fillna(df["saturacion_por_mil"].median()))

    df["score_oportunidad"] = (
        w_demanda * demanda_norm
        + w_tendencia * tendencia_norm
        - w_saturacion * saturacion_norm
    )

    df["confianza"] = np.where(
        df["PSDSS"].isna(),
        0.3,
        0.5 + 0.5 * df["tendencia_r2"].fillna(0),
    )

    return df


def compute_factibilidad_flag(df: pd.DataFrame, min_predios: int = 20, percentil: float = 0.75) -> pd.DataFrame:
    df = df.copy()
    mask_muestra_suficiente = df["n_predios_total"] >= min_predios
    umbral = df.loc[mask_muestra_suficiente, "pct_uso_equipamiento"].quantile(percentil)

    df["tiene_factibilidad_uso_suelo"] = (
        mask_muestra_suficiente & (df["pct_uso_equipamiento"] >= umbral)
    )
    return df


def compute_tipo_zona(df: pd.DataFrame) -> pd.DataFrame:
    """Clasifica cada AGEB por su uso de suelo dominante -- filtro real, no placeholder."""
    df = df.copy()
    n_otro = df["n_predios_total"] - df["n_equipamiento"] - df["n_mixto"]

    condiciones = [
        df["n_equipamiento"] >= df[["n_mixto"]].join(n_otro.rename("n_otro")).max(axis=1),
        df["n_mixto"] >= n_otro,
    ]
    opciones = ["Equipamiento/Institucional", "Mixto/Comercial"]
    df["tipo_zona"] = np.select(condiciones, opciones, default="Habitacional")
    df.loc[df["n_predios_total"].isna() | (df["n_predios_total"] == 0), "tipo_zona"] = "Sin dato"
    return df