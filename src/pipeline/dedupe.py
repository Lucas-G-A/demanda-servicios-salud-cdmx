import geopandas as gpd
import pandas as pd
from scipy.spatial import cKDTree
import numpy as np

DIST_THRESHOLD_DEG = 0.001  # ~100m


def _filtrar_geometrias_validas(gdf: gpd.GeoDataFrame, nombre: str) -> gpd.GeoDataFrame:
    n_antes = len(gdf)
    valido = (
        gdf.geometry.notna()
        & gdf.geometry.is_valid
        & gdf.geometry.x.notna()
        & gdf.geometry.y.notna()
        & np.isfinite(gdf.geometry.x)
        & np.isfinite(gdf.geometry.y)
    )
    gdf_limpio = gdf[valido].copy()
    n_despues = len(gdf_limpio)
    if n_despues < n_antes:
        print(f"  {nombre}: descartados {n_antes - n_despues} de {n_antes} por coordenadas inválidas")
    return gdf_limpio


def unify_salud_supply(
    establecimientos: gpd.GeoDataFrame,
    hospitales: gpd.GeoDataFrame,
    centros_salud: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Une las 3 fuentes puntuales de oferta de salud, evitando doble conteo."""

    establecimientos = _filtrar_geometrias_validas(establecimientos, "establecimientos_salud")
    hospitales = _filtrar_geometrias_validas(hospitales, "hospitales")
    centros_salud = _filtrar_geometrias_validas(centros_salud, "centros_salud")

    # 1. establecimientos_salud + hospitales: merge exacto por CLUES
    ids_establecimientos = set(establecimientos["CLUES"])
    hospitales_nuevos = hospitales[~hospitales["CLUES"].isin(ids_establecimientos)]

    base = pd.concat(
        [establecimientos[["CLUES", "geometry"]], hospitales_nuevos[["CLUES", "geometry"]]],
        ignore_index=True,
    )
    base = gpd.GeoDataFrame(base, geometry="geometry", crs=establecimientos.crs)

    # 2. centros_salud: dedup espacial por proximidad
    coords_base = np.array([(g.y, g.x) for g in base.geometry])
    coords_centros = np.array([(g.y, g.x) for g in centros_salud.geometry])
    tree = cKDTree(coords_base)
    dist, _ = tree.query(coords_centros, k=1)

    centros_nuevos = centros_salud[dist > DIST_THRESHOLD_DEG]

    salud_unificada = pd.concat(
        [base, centros_nuevos[["geometry"]]], ignore_index=True
    )
    return gpd.GeoDataFrame(salud_unificada, geometry="geometry", crs=base.crs)