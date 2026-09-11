import pandas as pd
import geopandas as gpd
from src.pipeline.config import PATHS, CRS_STANDARD, SCIAN_SALUD_PREFIX


def load_denue(path) -> gpd.GeoDataFrame:
    df = pd.read_csv(path, encoding="latin-1", dtype={"cod_postal": str}, low_memory=False)
    df = df[df["codigo_act"].astype(str).str.startswith(SCIAN_SALUD_PREFIX)].copy()

    # marca establecimientos que comparten dirección exacta (torres médicas, no error de dato)
    df["coord"] = df["latitud"].round(5).astype(str) + "_" + df["longitud"].round(5).astype(str)
    conteo_por_coord = df["coord"].value_counts()
    df["n_en_misma_direccion"] = df["coord"].map(conteo_por_coord)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitud"], df["latitud"]),
        crs=CRS_STANDARD,
    )

    return gdf


def load_ageb_geom() -> gpd.GeoDataFrame:
    urb = gpd.read_file(PATHS["ageb_urbana"]).to_crs(CRS_STANDARD)
    rur = gpd.read_file(PATHS["ageb_rural"]).to_crs(CRS_STANDARD)
    ageb = pd.concat([urb, rur], ignore_index=True)
    ageb = gpd.GeoDataFrame(ageb, geometry="geometry", crs=CRS_STANDARD)

    # CVEGEO es la clave completa (ENT+MUN+LOC+AGEB) — la que hace match con el xls de marginación
    ageb["CVE_AGEB"] = ageb["CVEGEO"].astype(str)
    return ageb


def load_marginacion() -> pd.DataFrame:
    df = pd.read_excel(
        PATHS["marginacion_ageb"],
        sheet_name="IMU_2020",
        dtype={"CVE_AGEB": str, "ENT": str, "MUN": str, "LOC": str},
    )
    return df[df["NOM_ENT"] == "Ciudad de México"].copy()


def load_centros_salud() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(PATHS["centros_salud"])
    return gdf.to_crs(CRS_STANDARD)


def load_hospitales() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(PATHS["hospitales"])
    return gdf.to_crs(CRS_STANDARD)


def load_establecimientos_salud() -> gpd.GeoDataFrame:
    df = pd.read_excel(PATHS["establecimientos_salud"], sheet_name="CLUES_202607")
    # ajusta los nombres exactos de columna de lat/lon una vez que los confirmes
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["LONGITUD"], df["LATITUD"]),
        crs=CRS_STANDARD,
    )
    return gdf


def load_equipamiento_basico() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(PATHS["equipamiento_basico"], encoding="utf-8-sig")
    return gdf.to_crs(CRS_STANDARD)

def load_cartografia_colonia() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(PATHS["cartografia_colonia"])  # agrega esta ruta a config.py si no está
    return gdf.to_crs(CRS_STANDARD)

def arreglar_mojibake(serie: pd.Series) -> pd.Series:
    """Repara texto UTF-8 guardado incorrectamente como Latin-1 en el archivo origen (ej. afluencia_metro.csv)."""
    def fix(x):
        if pd.isna(x):
            return x
        try:
            return x.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            return x
    return serie.apply(fix)


def normalizar_texto(serie: pd.Series) -> pd.Series:
    """Mayúsculas, sin acentos, sin espacios extra -- para cruzar nombres de estación entre fuentes."""
    import unicodedata
    import re

    def limpiar(x):
        if pd.isna(x):
            return x
        x = str(x).upper().strip()
        x = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode("utf-8")
        x = re.sub(r"\s+", " ", x)
        return x
    return serie.apply(limpiar)


# src/pipeline/clean.py — reemplaza load_estaciones_con_afluencia() completa por esto

def load_estaciones_con_afluencia() -> gpd.GeoDataFrame:
    afluencia = pd.read_csv(PATHS["afluencia_metro"], encoding="utf-8-sig")
    afluencia["estacion"] = arreglar_mojibake(afluencia["estacion"])
    afluencia["estacion_norm"] = normalizar_texto(afluencia["estacion"])
    afluencia["linea_norm"] = normalizar_texto(afluencia["linea"]).str.extract(r"(\d+)")  # "Linea 1" -> "1"

    afluencia_total = (
        afluencia.groupby(["estacion_norm", "linea_norm"])["afluencia"]
        .sum()
        .reset_index()
        .rename(columns={"afluencia": "afluencia_total_historica"})
    )

    estaciones = gpd.read_file(PATHS["estaciones_metro"]).to_crs(CRS_STANDARD)
    estaciones["estacion_norm"] = normalizar_texto(estaciones["NOMBRE"])
    estaciones["linea_norm"] = estaciones["LINEA"].astype(str).str.lstrip("0")  # "01" -> "1"

    estaciones_con_afluencia = estaciones.merge(
        afluencia_total, on=["estacion_norm", "linea_norm"], how="left"
    )

    n_sin_match = estaciones_con_afluencia["afluencia_total_historica"].isna().sum()
    print(f"  Estaciones Metro sin match de afluencia: {n_sin_match} de {len(estaciones_con_afluencia)}")

    return estaciones_con_afluencia